"""Companies and Division 7A: company tax rate and tax payable, maximum franking credits and gross-up,
the corporate loss carry back tax offset, and Division 7A complying-loan minimum yearly repayments and
amortisation schedules.

Law: Income Tax Rates Act 1986 s23AA (base rate entity rate); ITAA 1997 s202-60 (maximum franking
credit), s995-1 (corporate tax rate for imputation purposes, corporate tax gross-up rate), Div 205
(franking account, franking deficit tax), Div 160 as substituted by the Treasury Laws Amendment
(Tax Reform No. 2) Act 2026 (No. 71 of 2026) Sch 1 (loss carry back); ITAA 1936 Pt III Div 7A
(ss109C-109F payments, loans, forgiveness; s109E minimum yearly repayment; s109N complying loans;
s109Y distributable surplus). Every rate and threshold comes from data/rates/<year>.yaml and its
overlays via Figures.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from au_tax.figures import Figures
from au_tax.registry import Refusal, calculator

# ITAA 1997 s160-5(1)(a) (Act 71 of 2026 Sch 1; application item 11): loss year must start on/after this date.
LOSS_CARRY_BACK_START = date(2026, 7, 1)

SpecialCompany = Literal[
    "life_insurer", "rsa_provider", "pooled_development_fund", "credit_union", "non_profit",
    "strata_title_body", "non_resident", "in_liquidation",
]


def _r(x: float) -> float:
    return round(x + 0.0, 2)


def _year_start(label: str) -> date:
    return date(int(label[:4]), 7, 1)


def _year_label(start_year: int) -> str:
    return f"{start_year}-{(start_year + 1) % 100:02d}"


def _year_index(label: str) -> int:
    if len(label) != 7 or label[4] != "-" or not label[:4].isdigit():
        raise ValueError(f"income year must look like 2026-27, got {label!r}")
    y = int(label[:4])
    if int(label[5:]) != (y + 1) % 100:
        raise ValueError(f"income year {label!r} is not two consecutive years")
    return y


# ---------------------------------------------------------------- shared rate logic

def bre_test(figures: Figures, aggregated_turnover: float, passive_share: float) -> tuple[bool, list[str]]:
    """Base rate entity test (ITRA 1986 s23AA): aggregated turnover below the threshold AND base rate
    entity passive income no more than the maximum share of assessable income."""
    threshold = figures.get("company.bre_aggregated_turnover_threshold")
    max_share = figures.get("company.bre_passive_income_max_share")
    reasons = []
    ok_turnover = aggregated_turnover < threshold
    ok_passive = passive_share <= max_share
    reasons.append(f"aggregated turnover {'below' if ok_turnover else 'not below'} the base rate entity threshold")
    reasons.append(f"base rate entity passive income {'within' if ok_passive else 'above'} the maximum share of assessable income")
    return ok_turnover and ok_passive, reasons


def _rate(figures: Figures, bre: bool) -> float:
    return figures.get("company.rate_base_rate_entity" if bre else "company.rate_other")


def _passive_share(share: float | None, passive: float | None, assessable: float | None) -> float | None:
    if share is not None:
        return share
    if passive is not None and assessable is not None:
        if assessable <= 0:
            return 0.0 if passive <= 0 else 1.0
        return passive / assessable
    return None


def imputation_rate(figures: Figures, existed_prior_year: bool, prior_turnover: float | None,
                    prior_passive_share: float | None) -> tuple[float, str]:
    """Corporate tax rate for imputation purposes (ITAA 1997 s995-1; LCR 2019/5): apply this year's
    base rate entity test assuming aggregated turnover, BRE passive income and assessable income are the
    same as the previous income year. A company that did not exist last year uses the lower rate."""
    if not existed_prior_year:
        return _rate(figures, True), "did not exist in the previous income year: lower rate"
    if prior_turnover is None or prior_passive_share is None:
        raise ValueError("prior-year aggregated turnover and passive income share are needed for the imputation rate")
    bre, _ = bre_test(figures, prior_turnover, prior_passive_share)
    return _rate(figures, bre), ("previous-year facts pass the base rate entity test" if bre
                                 else "previous-year facts fail the base rate entity test")


# ---------------------------------------------------------------- company_tax

class CompanyTaxInput(BaseModel):
    """One company, one income year. Amounts in AUD."""

    taxable_income: float = Field(ge=0, description="Taxable income after any prior-year losses deducted.")
    aggregated_turnover: float = Field(ge=0, description="Aggregated turnover for THIS income year (company plus connected entities and affiliates).")
    passive_income_share: float | None = Field(
        None, ge=0, le=1, description="Base rate entity passive income as a share of assessable income this year (0-1). "
        "Passive income = dividends and franking credits, interest, rent, royalties, net capital gains, and trust or partnership "
        "distributions traceable to those. Or give base_rate_entity_passive_income and assessable_income.")
    base_rate_entity_passive_income: float | None = Field(None, ge=0)
    assessable_income: float | None = Field(None, ge=0)
    existed_prior_year: bool = Field(True, description="False if the company did not exist in the previous income year (imputation rate).")
    prior_year_aggregated_turnover: float | None = Field(None, ge=0, description="Previous year's aggregated turnover, for the rate used to frank distributions this year.")
    prior_year_passive_income_share: float | None = Field(None, ge=0, le=1, description="Previous year's BRE passive income share of assessable income.")
    franking_credits_received: float = Field(0, ge=0, description="Franking credits on dividends received (non-refundable franking tax offset for a company).")
    payg_instalments_paid: float | None = Field(None, ge=0, description="PAYG instalments already paid for the year.")
    prior_losses_deducted: float = Field(0, ge=0, description="Carried-forward tax losses deducted in arriving at taxable income.")
    ownership_or_control_changed: bool | None = Field(
        None, description="True if more than half the ownership or control changed since the loss years (loss recoupment tests).")
    consolidated_group: bool = Field(False, description="Head or member of a consolidated or MEC group.")
    special_company_type: SpecialCompany | None = Field(None, description="Company type with its own rates or rules (refused).")

    @model_validator(mode="after")
    def _need_passive(self):
        if _passive_share(self.passive_income_share, self.base_rate_entity_passive_income, self.assessable_income) is None:
            raise ValueError("give passive_income_share, or base_rate_entity_passive_income and assessable_income")
        return self


@calculator("company_tax", CompanyTaxInput)
def company_tax(figures: Figures, inp: CompanyTaxInput) -> dict:
    """Australian company income tax for one income year (2025-26 or 2026-27): applies the base rate entity
    test (aggregated turnover below the threshold and base rate entity passive income no more than the
    maximum share of assessable income) to choose the lower base rate entity rate or the general company
    rate, then tax on taxable income, less the non-refundable franking tax offset for franked dividends
    received (excess converted to a tax loss), less PAYG instalments. Also returns the corporate tax rate
    for imputation purposes (the rate for franking this year's distributions, from LAST year's turnover and
    passive income) when prior-year facts are given, which can differ from this year's tax rate.
    Use for "what rate does my company pay", "company tax on $X", "is my company a base rate entity",
    "bucket company tax rate", "25% or 30%". Refuses AU-COMP-001 (consolidated groups), AU-COMP-002
    (prior losses deducted after an ownership or control change), AU-COMP-008 (special company types)."""
    if inp.consolidated_group:
        raise Refusal("AU-COMP-001", "consolidated or MEC group")
    if inp.special_company_type:
        raise Refusal("AU-COMP-008", inp.special_company_type)
    if inp.prior_losses_deducted and inp.ownership_or_control_changed:
        raise Refusal("AU-COMP-002", "prior-year losses deducted after a change in ownership or control")

    assumptions: list[str] = []
    warnings: list[str] = []
    share = _passive_share(inp.passive_income_share, inp.base_rate_entity_passive_income, inp.assessable_income)
    bre, reasons = bre_test(figures, inp.aggregated_turnover, share)
    rate = _rate(figures, bre)
    gross = rate * inp.taxable_income
    offset_used = min(inp.franking_credits_received, gross)
    excess = inp.franking_credits_received - offset_used
    net = gross - offset_used
    out: dict = {
        "base_rate_entity": bre,
        "base_rate_entity_reasons": reasons,
        "passive_income_share": round(share, 4),
        "company_tax_rate": rate,
        "taxable_income": _r(inp.taxable_income),
        "gross_tax": _r(gross),
        "franking_tax_offset_used": _r(offset_used),
        "net_tax_payable": _r(net),
    }
    if excess > 0:
        out["excess_franking_offset"] = _r(excess)
        out["excess_franking_offset_as_tax_loss"] = _r(excess / rate)
        warnings.append("Excess franking offset is not refunded to a company; it converts to a tax loss (ITAA 1997 s36-55), "
                        "computed here as excess / company tax rate. Confirm the loss calculation with a registered tax agent.")
    if inp.payg_instalments_paid is not None:
        out["payg_instalments_paid"] = _r(inp.payg_instalments_paid)
        out["balance_payable_or_refund"] = _r(net - inp.payg_instalments_paid)
    if inp.existed_prior_year and (inp.prior_year_aggregated_turnover is None or inp.prior_year_passive_income_share is None):
        out["corporate_tax_rate_for_imputation"] = None
        assumptions.append("Rate for franking distributions this year not worked out: needs the previous year's aggregated "
                           "turnover and passive income share (it is based on last year's facts, not this year's).")
    else:
        irate, basis = imputation_rate(figures, inp.existed_prior_year, inp.prior_year_aggregated_turnover,
                                       inp.prior_year_passive_income_share)
        out["corporate_tax_rate_for_imputation"] = irate
        out["imputation_rate_basis"] = basis
        if irate != rate:
            warnings.append("The rate for franking distributions this year differs from this year's company tax rate; "
                            "frank at the imputation rate.")
    if inp.prior_losses_deducted and inp.ownership_or_control_changed is None:
        warnings.append("Prior-year losses were deducted: confirm the continuity of ownership test (or business continuity "
                        "test) is passed; if ownership or control changed, the deduction needs review (AU-COMP-002).")
    assumptions.append("Taxable income is as given; aggregated turnover includes connected entities and affiliates.")
    assumptions.append("Resident company, not a consolidated group; tax offsets other than franking offsets and the loss "
                       "carry back offset are not modelled.")
    out["franking_credit_on_paying_tax"] = _r(net)
    assumptions.append("Paying the income tax (instalments or balance) credits the franking account by the amount paid; "
                       "a tax refund debits it.")
    out["assumptions"] = assumptions
    out["warnings"] = warnings
    return out


# ---------------------------------------------------------------- max_franking_credit

class FrankingInput(BaseModel):
    """One frankable distribution by a corporate tax entity."""

    frankable_distribution: float = Field(gt=0, description="Frankable part of the dividend or distribution (AUD).")
    corporate_tax_rate_for_imputation: float | None = Field(
        None, description="If already known: the entity's corporate tax rate for imputation purposes for the year of the "
        "distribution (must be the base rate entity rate or the general rate). Otherwise give the prior-year facts.")
    existed_prior_year: bool = Field(True, description="False if the entity did not exist in the previous income year.")
    prior_year_aggregated_turnover: float | None = Field(None, ge=0, description="Aggregated turnover for the previous income year.")
    prior_year_passive_income_share: float | None = Field(None, ge=0, le=1, description="Previous year's BRE passive income share of assessable income.")
    franking_percentage: float = Field(1.0, ge=0, description="Share of the maximum franking credit allocated (1 = fully franked).")
    franking_account_balance: float | None = Field(None, description="Franking account balance just before the distribution.")
    benchmark_franking_percentage: float | None = Field(
        None, ge=0, le=1, description="Franking percentage of the first frankable distribution in the franking period, if an "
        "earlier distribution was made this period (benchmark rule).")


@calculator("max_franking_credit", FrankingInput)
def max_franking_credit(figures: Figures, inp: FrankingInput) -> dict:
    """Maximum franking credit on a frankable distribution (ITAA 1997 s202-60): distribution x 1 / corporate
    tax gross-up rate, where the gross-up rate = (1 - imputation rate) / imputation rate. The corporate tax
    rate for imputation purposes is worked out from the PREVIOUS income year's aggregated turnover and
    passive income (or is the lower rate for a company that did not exist last year), so it can differ from
    the company's tax rate this year. Returns the maximum credit, the credit allocated at the chosen franking
    percentage (capped at the maximum), the grossed-up dividend and franking tax offset for the shareholder,
    franking account effect and any franking deficit. Use for "how much franking credit on a $X dividend",
    "fully franked dividend gross-up", "can I frank at 30%", "franking credits for shareholders"."""
    assumptions: list[str] = []
    warnings: list[str] = []
    escalations: list[dict] = []
    lower, general = figures.get("company.rate_base_rate_entity"), figures.get("company.rate_other")
    if inp.corporate_tax_rate_for_imputation is not None:
        irate = inp.corporate_tax_rate_for_imputation
        if irate not in (lower, general):
            raise ValueError("corporate_tax_rate_for_imputation must be the base rate entity rate or the general company rate")
        basis = "given"
    else:
        irate, basis = imputation_rate(figures, inp.existed_prior_year, inp.prior_year_aggregated_turnover,
                                       inp.prior_year_passive_income_share)
    gross_up_rate = (1 - irate) / irate
    maximum = inp.frankable_distribution / gross_up_rate
    pct = inp.franking_percentage
    if pct > 1:
        warnings.append("Franking percentage above 100%: the franking credit on the distribution is limited to the maximum "
                        "franking credit (s202-60(1)); the excess allocation is ignored and over-franking consequences need review.")
        escalations.append({"code": "AU-COMP-009", "reason": "over-franked distribution"})
        pct = 1.0
    credit = maximum * pct
    out: dict = {
        "corporate_tax_rate_for_imputation": irate,
        "imputation_rate_basis": basis,
        "corporate_tax_gross_up_rate": round(gross_up_rate, 6),
        "frankable_distribution": _r(inp.frankable_distribution),
        "maximum_franking_credit": _r(maximum),
        "franking_percentage": pct,
        "franking_credit_allocated": _r(credit),
        "shareholder": {
            "grossed_up_dividend": _r(inp.frankable_distribution + credit),
            "franking_tax_offset": _r(credit),
        },
        "franking_debit": _r(credit),
    }
    if inp.franking_account_balance is not None:
        after = inp.franking_account_balance - credit
        out["franking_account_balance_after"] = _r(after)
        if after < 0:
            warnings.append("The franking account would be in deficit. If it is still in deficit at the end of the income year "
                            "(or on ceasing to be a franking entity), the company pays franking deficit tax equal to the deficit "
                            "(ITAA 1997 Div 205), which can generate a franking deficit tax offset.")
    if inp.benchmark_franking_percentage is not None and abs(inp.benchmark_franking_percentage - pct) > 1e-9:
        warnings.append("Franking percentage differs from the benchmark franking percentage for the franking period (for a "
                        "private company, the income year): the benchmark rule may impose over-franking tax or an "
                        "under-franking debit (ITAA 1997 Div 203).")
        escalations.append({"code": "AU-COMP-009", "reason": "benchmark rule departure"})
    assumptions.append("Individual shareholders include the grossed-up dividend in assessable income and receive a franking "
                       "tax offset equal to the credit (refundable for eligible individuals; non-refundable for companies). "
                       "Holding period and related payments rules assumed satisfied.")
    assumptions.append("A Division 7A deemed dividend is unfranked; this tool is for actual frankable distributions.")
    out.update({"assumptions": assumptions, "warnings": warnings, "escalations": escalations})
    return out


# ---------------------------------------------------------------- Division 7A

def minimum_yearly_repayment(balance: float, rate: float, remaining_term: int) -> float:
    """ITAA 1936 s109E(6): balance x rate / (1 - (1 / (1 + rate)) ** remaining_term)."""
    if remaining_term <= 0:
        raise ValueError("remaining term must be at least 1 year")
    if balance <= 0:
        return 0.0
    if rate == 0:
        return balance / remaining_term
    return balance * rate / (1 - (1 / (1 + rate)) ** remaining_term)


def _max_term(figures: Figures, secured: bool) -> int:
    return int(figures.get("div7a.max_term_secured_years" if secured else "div7a.max_term_unsecured_years"))


def _check_term(figures: Figures, term: int, secured: bool, security_ratio: float | None) -> tuple[bool, list[str]]:
    reasons = []
    ok = True
    if secured:
        if security_ratio is not None and security_ratio < figures.get("div7a.secured_loan_min_security_ratio"):
            ok = False
            reasons.append("security value (after prior-ranking debts) below the minimum multiple of the loan: only the "
                           "unsecured maximum term is available (s109N(3)(a)(ii))")
            term_max = figures.get("div7a.max_term_unsecured_years")
        else:
            term_max = _max_term(figures, True)
    else:
        term_max = _max_term(figures, False)
    if term > term_max:
        ok = False
        reasons.append("loan term exceeds the maximum term for this kind of loan (s109N(3)); the agreement is not complying")
    return ok, reasons


class Div7AMyrInput(BaseModel):
    """One amalgamated loan under a written complying loan agreement, for the income year of the call."""

    opening_balance: float = Field(
        ge=0, description="Amount of the amalgamated loan not repaid by the end of the previous income year. First year after "
        "the loan year: loan amount less repayments made before the company's lodgment day. Later years: previous closing "
        "balance (principal plus benchmark interest less repayments).")
    repayments_before_lodgment_day: float = Field(
        0, ge=0, description="First year only: repayments made after 30 June of the loan year but before lodgment day that are "
        "NOT already deducted from opening_balance. They reduce the balance used for the MYR and also count as repayments "
        "made in the current year.")
    loan_income_year: str | None = Field(None, description="Income year the loan was made, e.g. 2025-26.")
    years_elapsed: int | None = Field(
        None, ge=0, description="Alternative to loan_income_year: years between the end of the loan year and the end of the "
        "previous income year (0 in the first year after the loan year).")
    loan_term_years: int = Field(ge=1, description="Term in the written agreement (longest constituent loan).")
    secured: bool = Field(False, description="100% secured by a registered mortgage over real property.")
    security_value_ratio: float | None = Field(
        None, ge=0, description="Market value of the mortgaged property less prior-ranking debts, divided by the loan, when "
        "the loan was first made (secured loans).")
    repayments_in_year: float = Field(
        0, ge=0, description="Total paid on the loan during the current income year (principal and interest), including any "
        "paid before the lodgment day for the loan year that fall in this income year.")
    written_agreement_before_lodgment_day: bool = Field(True, description="Complying written agreement made before the lodgment day for the loan year.")
    distributable_surplus: float | None = Field(None, description="Company's distributable surplus for the year (caps the deemed dividend, s109Y), if known.")
    reborrowed_or_interposed: bool = Field(False, description="Repayment funded by a new loan from the company or an interposed entity, or made by journal only (s109R/s109T).")

    @model_validator(mode="after")
    def _one_of(self):
        if self.loan_income_year is None and self.years_elapsed is None:
            raise ValueError("give loan_income_year or years_elapsed")
        if self.loan_income_year is not None:
            _year_index(self.loan_income_year)
        return self


@calculator("div7a_minimum_repayment", Div7AMyrInput)
def div7a_minimum_repayment(figures: Figures, inp: Div7AMyrInput) -> dict:
    """Division 7A minimum yearly repayment (ITAA 1936 s109E) on a private company loan to a shareholder or
    associate under a complying written agreement (s109N), for the income year of the call, using that
    year's benchmark interest rate: MYR = balance x rate / (1 - (1 + rate) ** -remaining term). Remaining
    term = agreement term less whole years from the end of the loan year to the end of the previous year.
    Compares repayments made in the year and returns any shortfall, which is an unfranked deemed dividend at
    30 June (capped at distributable surplus, s109Y). Also checks the term against the maximum (7 years
    unsecured, 25 years secured by a registered mortgage). Use for "Div 7A minimum repayment", "MYR on my
    director loan", "how much must I repay my company this year", "Div 7A shortfall". For a full
    year-by-year amortisation use div7a_loan_schedule. Refuses AU-COMP-006 (repay-and-redraw or interposed
    entity repayments) and AU-COMP-007 (loan past its term, special cases)."""
    if inp.reborrowed_or_interposed:
        raise Refusal("AU-COMP-006", "repayment funded by reborrowing, an interposed entity or journal entry")
    assumptions: list[str] = []
    warnings: list[str] = []
    cur = _year_index(figures.income_year)
    if inp.loan_income_year is not None:
        elapsed = cur - _year_index(inp.loan_income_year) - 1
        if elapsed < 0:
            if elapsed == -1:
                return {
                    "complying": None, "minimum_yearly_repayment": 0.0, "loan_year": True,
                    "note": "No minimum yearly repayment is due in the income year the loan is made. Before the company's "
                            "lodgment day for this year, repay the loan or put it under a complying written agreement; "
                            "otherwise the unpaid amount is a deemed dividend at 30 June of this year (s109D), subject to "
                            "distributable surplus. The first MYR falls due by 30 June of the next income year.",
                    "assumptions": assumptions, "warnings": warnings}
            raise ValueError("loan_income_year is after the income year of the call")
    else:
        elapsed = inp.years_elapsed or 0
    complying, reasons = _check_term(figures, inp.loan_term_years, inp.secured, inp.security_value_ratio)
    if not inp.written_agreement_before_lodgment_day:
        complying = False
        reasons.append("no complying written agreement before the lodgment day for the loan year")
    if not complying:
        return {"complying": False, "reasons": reasons, "minimum_yearly_repayment": None,
                "note": "Not a complying loan: the amount not repaid before the lodgment day for the loan year is treated as "
                        "an unfranked dividend at the end of the loan year (s109D), subject to distributable surplus "
                        "(s109Y). MYR rules do not apply.",
                "assumptions": assumptions, "warnings": warnings}
    remaining = inp.loan_term_years - elapsed
    if remaining <= 0:
        raise Refusal("AU-COMP-007", "loan is past its maximum term")
    rate = figures.get("div7a.benchmark_interest_rate")
    balance = max(0.0, inp.opening_balance - inp.repayments_before_lodgment_day)
    myr = minimum_yearly_repayment(balance, rate, remaining)
    paid = inp.repayments_in_year + (inp.repayments_before_lodgment_day if elapsed == 0 else 0.0)
    if inp.repayments_before_lodgment_day and elapsed != 0:
        warnings.append("repayments_before_lodgment_day only applies in the first year after the loan year; ignored.")
    shortfall = max(0.0, myr - paid)
    deemed = shortfall
    if inp.distributable_surplus is not None:
        deemed = max(0.0, min(shortfall, inp.distributable_surplus))
    out = {
        "complying": True,
        "benchmark_interest_rate": rate,
        "years_elapsed": elapsed,
        "remaining_term_years": remaining,
        "balance_for_myr": _r(balance),
        "minimum_yearly_repayment": _r(myr),
        "repayments_counted": _r(paid),
        "shortfall": _r(shortfall),
        "deemed_dividend": _r(deemed),
        "deemed_dividend_capped_by_distributable_surplus": inp.distributable_surplus is not None and deemed < shortfall,
        "interest_if_repaid_on_30_june": _r(balance * rate),
    }
    if shortfall:
        assumptions.append("The shortfall is an unfranked dividend paid to the borrower at the end of the income year "
                           "(s109E(2)), subject to the company's distributable surplus (s109Y), unless the Commissioner "
                           "exercises a discretion (s109Q, s109RB): seek a registered tax agent (AU-COMP-007) if relying on it.")
        if inp.distributable_surplus is None:
            warnings.append("Distributable surplus not given: the deemed dividend shown is uncapped (s109Y).")
    assumptions.append("Benchmark interest rate for the income year of the call; standard 1 July to 30 June income year.")
    assumptions.append("Repayments must be real payments (or valid set-off of dividends or salary under an agreement) made by "
                       "30 June; accrued or journalled interest is not a repayment.")
    return {**out, "assumptions": assumptions, "warnings": warnings}


class Repayment(BaseModel):
    date: date
    amount: float = Field(gt=0)


class Div7AScheduleInput(BaseModel):
    """A complying Div 7A loan from the loan year to the end of its term."""

    loan_income_year: str = Field(description="Income year the loan was made, e.g. 2025-26.")
    loan_amount: float = Field(gt=0, description="Amalgamated loan outstanding at 30 June of the loan year (net of repayments made in the loan year).")
    loan_term_years: int = Field(ge=1, description="Term in the written agreement.")
    secured: bool = False
    security_value_ratio: float | None = Field(None, ge=0)
    lodgment_day: date | None = Field(
        None, description="Company's lodgment day for the loan year (earlier of due date and actual lodgment). Repayments "
        "after 30 June and on or before this day reduce the balance used for the first MYR.")
    repayments: list[Repayment] = Field(
        default_factory=list, description="Actual repayments with dates after the loan year. Years with no repayment listed "
        "are assumed to pay exactly the MYR on 30 June.")
    benchmark_rate_overrides: dict[str, float] = Field(
        default_factory=dict, description="Benchmark rates for years the rates file does not cover, e.g. {\"2027-28\": 0.085}.")

    @model_validator(mode="after")
    def _years(self):
        _year_index(self.loan_income_year)
        for k in self.benchmark_rate_overrides:
            _year_index(k)
        return self


def _interest_daily(opening: float, rate: float, start: date, end: date, pays: list[Repayment]) -> tuple[float, float]:
    """Interest on the daily balance (s109E(7)); a repayment reduces the balance from its own date.
    Returns (interest, total repaid)."""
    days_in_year = (end - start).days + 1
    bal, cursor, interest, paid = opening, start, 0.0, 0.0
    for p in sorted(pays, key=lambda x: x.date):
        interest += bal * rate * (p.date - cursor).days / days_in_year
        bal -= p.amount
        paid += p.amount
        cursor = p.date
    interest += bal * rate * ((end - cursor).days + 1) / days_in_year
    return interest, paid


@calculator("div7a_loan_schedule", Div7AScheduleInput)
def div7a_loan_schedule(figures: Figures, inp: Div7AScheduleInput) -> dict:
    """Year-by-year Division 7A amortisation schedule for a complying loan (ITAA 1936 s109E, s109N): for each
    income year after the loan year, the opening balance, benchmark interest rate, remaining term, minimum
    yearly repayment, repayments, interest on the daily balance at the benchmark rate (s109E(7)), closing
    balance and any shortfall (deemed dividend, before the distributable surplus cap). Uses verified
    benchmark rates where published; later years use benchmark_rate_overrides or are projected at the
    latest published rate and marked projected. Years with no listed repayment assume exactly the MYR is
    paid on 30 June. Use for "Div 7A loan schedule", "repayment plan for a 7-year Div 7A loan", "amortise my
    shareholder loan", "what will I owe each year". Refuses AU-COMP-007 for loans past their term."""
    assumptions: list[str] = []
    warnings: list[str] = []
    complying, reasons = _check_term(figures, inp.loan_term_years, inp.secured, inp.security_value_ratio)
    if not complying:
        return {"complying": False, "reasons": reasons, "schedule": [],
                "note": "Not a complying loan: the amount not repaid before the lodgment day for the loan year is a deemed "
                        "dividend at the end of the loan year (s109D), subject to distributable surplus.",
                "assumptions": assumptions, "warnings": warnings}
    history = {str(r["from"].year): r["rate"] for r in figures.get("div7a.benchmark_interest_rate_history")}
    latest_start = max(int(k) for k in history)
    loan_y = _year_index(inp.loan_income_year)
    loan_end = date(loan_y + 1, 6, 30)
    known_dates = {r.date for r in inp.repayments}
    for r in inp.repayments:
        if r.date <= loan_end:
            raise ValueError("repayments must be dated after 30 June of the loan year; net loan-year repayments into loan_amount")
    rows = []
    balance = inp.loan_amount
    projected_any = False
    for k in range(1, inp.loan_term_years + 1):
        y = loan_y + k
        label = _year_label(y)
        start, end = date(y, 7, 1), date(y + 1, 6, 30)
        if label in inp.benchmark_rate_overrides:
            rate, source = inp.benchmark_rate_overrides[label], "override"
        elif str(y) in history:
            rate, source = history[str(y)], "published"
        else:
            rate, source = history[str(latest_start)], "projected"
            projected_any = True
        pays = [r for r in inp.repayments if start <= r.date <= end]
        pre_lodge = sum(r.amount for r in pays if k == 1 and inp.lodgment_day and r.date <= inp.lodgment_day)
        base = max(0.0, balance - pre_lodge)
        remaining = inp.loan_term_years - (k - 1)
        myr = minimum_yearly_repayment(base, rate, remaining)
        assumed = False
        if not pays:
            assumed = True
            # MYR treated as paid at the close of 30 June: a full year's interest on the opening balance,
            # which is the annual-payment basis the s109E(6) annuity formula assumes.
            interest = balance * rate
            pays_total = min(myr, balance + interest)
        else:
            interest, pays_total = _interest_daily(balance, rate, start, end, pays)
        closing = balance + interest - pays_total
        shortfall = max(0.0, myr - pays_total)
        rows.append({
            "income_year": label, "opening_balance": _r(balance), "balance_for_myr": _r(base),
            "benchmark_rate": rate, "rate_source": source, "remaining_term_years": remaining,
            "minimum_yearly_repayment": _r(myr), "repayments": _r(pays_total), "repayment_assumed": assumed,
            "interest": _r(interest), "principal_repaid": _r(pays_total - interest), "closing_balance": _r(max(closing, 0.0)),
            "shortfall_deemed_dividend": _r(shortfall),
        })
        balance = closing
        if balance <= 0.005:
            break
    if balance > 0.005:
        warnings.append("Loan not fully repaid by the end of its term on these repayments; any balance past the term needs "
                        "review (AU-COMP-007).")
    if projected_any:
        warnings.append("Years marked projected use the latest published benchmark rate as a placeholder; the real MYR for "
                        "each year uses that year's benchmark rate, published before the year starts.")
    if any(r["repayment_assumed"] for r in rows):
        assumptions.append("Years with no listed repayment assume exactly the minimum yearly repayment is paid at the close of "
                           "30 June (a full year's interest on the opening balance).")
    if inp.lodgment_day and any(d <= inp.lodgment_day for d in known_dates):
        assumptions.append("Repayments on or before the lodgment day for the loan year reduce the balance used for the first "
                           "MYR and also count towards the first year's repayments (ATO worked example).")
    assumptions.append("Interest accrues on the daily balance at the benchmark rate, a repayment reducing the balance from its "
                       "own date, over the actual days in the income year.")
    assumptions.append("Shortfalls are shown before the distributable surplus cap (s109Y).")
    return {"complying": True, "loan_income_year": inp.loan_income_year, "loan_amount": _r(inp.loan_amount),
            "loan_term_years": inp.loan_term_years, "schedule": rows,
            "total_repayments": _r(sum(r["repayments"] for r in rows)),
            "total_interest": _r(sum(r["interest"] for r in rows)),
            "assumptions": assumptions, "warnings": warnings}


# ---------------------------------------------------------------- loss carry back

class CarryBackYear(BaseModel):
    income_year: str = Field(description="One of the 2 income years before the loss year, e.g. 2025-26.")
    income_tax_liability: float = Field(ge=0, description="Income tax liability for that year (tax assessed after non-refundable offsets).")
    net_exempt_income: float = Field(0, ge=0, description="Net exempt income for that year.")
    liability_already_used: float = Field(0, ge=0, description="Part of that liability already used by an earlier loss carry back offset.")
    corporate_tax_entity_throughout: bool = True
    loss_carried_back: float | None = Field(None, ge=0, description="Amount of the loss chosen to carry back to this year; omit to let the tool choose.")


class LossCarryBackInput(BaseModel):
    """Loss year = the income year of the call."""

    tax_loss: float = Field(gt=0, description="Tax loss for the loss year.")
    loss_year_start: date | None = Field(None, description="First day of the loss year if not 1 July (substituted accounting period).")
    base_rate_entity: bool | None = Field(None, description="Base rate entity in the loss year (sets the corporate tax rate). Or give turnover and passive share.")
    aggregated_turnover: float | None = Field(None, ge=0)
    passive_income_share: float | None = Field(None, ge=0, le=1)
    franking_account_balance: float = Field(description="Franking account balance at the END of the loss year.")
    carry_back_years: list[CarryBackYear] = Field(default_factory=list, max_length=2)
    corporate_tax_entity_throughout: bool = True
    significant_global_entity: bool = False
    lodgment_condition_met: bool = Field(True, description="Returns lodged (or not required, or assessed) for the loss year and the 5 years before.")
    consolidated_group_or_transferred_losses: bool = False
    change_of_control_scheme: bool = Field(False, description="Shares or control changed hands since the start of a carry back year in a deal priced by reference to the offset.")
    foreign_resident: bool = False
    loss_includes_excess_franking_offset: bool = False
    amending_earlier_choice: bool = False


@calculator("loss_carry_back_offset", LossCarryBackInput)
def loss_carry_back_offset(figures: Figures, inp: LossCarryBackInput) -> dict:
    """Corporate loss carry back tax offset under new ITAA 1997 Div 160 (Treasury Laws Amendment (Tax Reform
    No. 2) Act 2026 Sch 1): a corporate tax entity that is not a significant global entity, with a tax loss
    for an income year starting on or after 1 July 2026, may carry the loss back to either or both of the
    2 previous income years in which it had an income tax liability. Each year's component = the lesser of
    that year's unused income tax liability and (loss carried back - that year's net exempt income) x the
    corporate tax rate for the LOSS year; the refundable offset = sum of components capped at the franking
    account balance at the end of the loss year. Checks eligibility (lodgment of the loss year and prior 5
    years, corporate tax entity throughout, not an SGE). If no split is given, chooses one that uses the
    older year first and carries back no more loss than the offset can use. Use for "can my company carry
    back a loss", "loss carry back refund", "tax loss 2026-27 refund of prior tax". Loss years starting
    before 1 July 2026 are ineligible. Refuses AU-COMP-001 (consolidated groups, transferred losses) and
    AU-COMP-003 (integrity rule, foreign residents, excess franking offset losses, amended choices,
    substituted accounting periods)."""
    if inp.consolidated_group_or_transferred_losses:
        raise Refusal("AU-COMP-001", "consolidated group or transferred losses (s160-25)")
    if inp.change_of_control_scheme:
        raise Refusal("AU-COMP-003", "integrity rule s160-30")
    if inp.foreign_resident:
        raise Refusal("AU-COMP-003", "foreign resident (s160-10(3))")
    if inp.loss_includes_excess_franking_offset:
        raise Refusal("AU-COMP-003", "loss increased by excess franking offsets (s160-25(1)(b))")
    if inp.amending_earlier_choice:
        raise Refusal("AU-COMP-003", "changing a loss carry back choice (s160-20)")
    if inp.loss_year_start is not None and inp.loss_year_start != _year_start(figures.income_year):
        raise Refusal("AU-COMP-003", "substituted accounting period")

    assumptions: list[str] = []
    warnings: list[str] = []
    start = inp.loss_year_start or _year_start(figures.income_year)
    reasons: list[str] = []
    if start < LOSS_CARRY_BACK_START:
        reasons.append("the loss year starts before 1 July 2026; Div 160 as substituted by Act 71 of 2026 applies only to "
                       "income years starting on or after that date (s160-5(1)(a)); the earlier temporary carry back ended "
                       "with 2022-23")
        return {"eligible": False, "reasons": reasons, "loss_carry_back_tax_offset": 0.0,
                "loss_to_carry_forward": _r(inp.tax_loss), "assumptions": assumptions, "warnings": warnings}
    window = int(figures.get("company.loss_carry_back_years"))
    lookback = int(figures.get("company.loss_carry_back_lodgment_lookback_years"))
    if not inp.corporate_tax_entity_throughout:
        reasons.append("not a corporate tax entity throughout the loss year (s160-5(1)(b))")
    if inp.significant_global_entity:
        reasons.append("significant global entity for the loss year (s160-5(1)(e))")
    if not inp.lodgment_condition_met:
        reasons.append(f"returns not lodged (or assessed) for the loss year and each of the {lookback} prior years (s160-5(1)(f))")

    if inp.base_rate_entity is not None:
        bre = inp.base_rate_entity
    elif inp.aggregated_turnover is not None and inp.passive_income_share is not None:
        bre, _ = bre_test(figures, inp.aggregated_turnover, inp.passive_income_share)
    else:
        raise ValueError("give base_rate_entity, or aggregated_turnover and passive_income_share for the loss year")
    rate = _rate(figures, bre)

    cur = _year_index(figures.income_year)
    allowed = {_year_label(cur - k) for k in range(1, window + 1)}
    years = sorted(inp.carry_back_years, key=lambda c: c.income_year)  # older first
    eligible_years = []
    for c in years:
        if c.income_year not in allowed:
            raise ValueError(f"{c.income_year} is not one of the {window} income years before {figures.income_year}")
        if c.income_tax_liability - c.liability_already_used <= 0 or c.income_tax_liability <= 0:
            warnings.append(f"{c.income_year}: no income tax liability left, so it is not an eligible carry back year.")
            continue
        if not c.corporate_tax_entity_throughout:
            warnings.append(f"{c.income_year}: not a corporate tax entity throughout, so not an eligible carry back year.")
            continue
        eligible_years.append(c)
    if not eligible_years:
        reasons.append("no eligible carry back year (s160-5(1)(d), (2)): needs an income tax liability in one of the "
                       f"{window} previous income years")
    if reasons:
        return {"eligible": False, "reasons": reasons, "corporate_tax_rate": rate, "loss_carry_back_tax_offset": 0.0,
                "loss_to_carry_forward": _r(inp.tax_loss), "assumptions": assumptions, "warnings": warnings}

    chosen_given = any(c.loss_carried_back is not None for c in eligible_years)
    loss_left = inp.tax_loss
    cap_left = max(0.0, inp.franking_account_balance)
    comps = []
    for c in eligible_years:
        room = c.income_tax_liability - c.liability_already_used
        if chosen_given:
            amt = c.loss_carried_back or 0.0
        else:
            useful = min(room, cap_left)
            amt = min(loss_left, useful / rate + c.net_exempt_income) if useful > 0 else 0.0
        if amt > loss_left + 1e-9:
            raise ValueError("loss carried back exceeds the tax loss")
        loss_left -= amt
        step2 = max(0.0, amt - c.net_exempt_income)
        comp = min(room, step2 * rate) if amt else 0.0
        cap_left = max(0.0, cap_left - comp)
        comps.append({"income_year": c.income_year, "loss_carried_back": _r(amt), "net_exempt_income": _r(c.net_exempt_income),
                      "liability_available": _r(room), "component": _r(comp)})
    total = sum(x["component"] for x in comps)
    offset = min(total, max(0.0, inp.franking_account_balance))
    carried = sum(x["loss_carried_back"] for x in comps)
    if total > offset:
        warnings.append("Offset limited to the franking account balance at the end of the loss year (s160-10(1)(b)); loss "
                        "carried back beyond what the offset can use is still consumed. Consider carrying back less.")
    for x in comps:
        if x["component"] < (max(0.0, x["loss_carried_back"] - x["net_exempt_income"]) * rate) - 0.005:
            warnings.append(f"{x['income_year']}: component limited to that year's unused income tax liability; the excess "
                            "loss carried back is wasted.")
    if not chosen_given:
        assumptions.append("Loss split chosen by the tool: older eligible year first, carrying back only as much loss as the "
                           "liability and franking cap can use. The company makes its own choice in the approved form.")
    assumptions.append("The choice must be made in the approved form by the day the loss year's return is lodged (or later "
                       "if the Commissioner allows) (s160-15(2)).")
    assumptions.append("Corporate tax rate for the loss year applied at step 3 (s160-10(2)).")
    warnings.append("The offset is refundable (s67-23). Franking account and loss-recoupment consequences of the choice are "
                    "not modelled; confirm with a registered tax agent.")
    return {"eligible": True, "corporate_tax_rate": rate, "base_rate_entity": bre, "components": comps,
            "sum_of_components": _r(total), "franking_account_cap": _r(inp.franking_account_balance),
            "loss_carry_back_tax_offset": _r(offset), "loss_carried_back": _r(carried),
            "loss_to_carry_forward": _r(inp.tax_loss - carried),
            "assumptions": assumptions, "warnings": warnings}
