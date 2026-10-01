"""Bookkeeping and year-end close: trial balance check, GST control account reconciliation to the BAS,
prepayment deduction (12-month rule) and the large proprietary company size test.

Law: ITAA 1936 ss 82KZL-82KZMD (prepayments); Corporations Act 2001 ss 45A, 286, 292, 319 with
Corporations Regulations 2001 reg 1.0.02B (size thresholds). Every threshold and rate comes from
data/rates/<year>.yaml and its overlays via Figures; nothing legislated is hard-coded here.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from au_tax.figures import Figures
from au_tax.registry import Refusal, calculator


def _r(x: float) -> float:
    return round(x + 0.0, 2)


def _add_months(d: date, months: int) -> date:
    """Calendar month addition; a month-end date maps to the month-end of the target month."""
    y, m = divmod(d.month - 1 + months, 12)
    y, m = d.year + y, m + 1
    last = calendar.monthrange(y, m)[1]
    if d.day == calendar.monthrange(d.year, d.month)[1]:
        return date(y, m, last)
    return date(y, m, min(d.day, last))


def _months_later(d: date, months: int) -> date:
    """Same day-of-month `months` later; if that day does not exist, the first day of the following month."""
    y, m = divmod(d.month - 1 + months, 12)
    y, m = d.year + y, m + 1
    if d.day > calendar.monthrange(y, m)[1]:
        return date(y + (m == 12), m % 12 + 1, 1)
    return date(y, m, d.day)


def _anniversary(d: date, years: int) -> date:
    """Same calendar day `years` later; 29 Feb rolls to 1 Mar (the day after the last day of Feb)."""
    try:
        return d.replace(year=d.year + years)
    except ValueError:
        return date(d.year + years, 3, 1)


def _income_year_start(d: date) -> int:
    return d.year if d.month >= 7 else d.year - 1


def _label(start_year: int) -> str:
    return f"{start_year}-{(start_year + 1) % 100:02d}"


# ------------------------------------------------------------------ trial balance

AccountType = Literal["asset", "liability", "equity", "income", "cost_of_sales", "expense"]
_DEBIT_NORMAL = {"asset", "cost_of_sales", "expense"}
_SUSPENSE_WORDS = ("suspense", "ask my accountant", "uncategor", "unallocated", "unreconciled")


class TBAccount(BaseModel):
    name: str
    debit: float = Field(0, ge=0, description="Debit balance (positive number).")
    credit: float = Field(0, ge=0, description="Credit balance (positive number).")
    type: AccountType | None = Field(
        None, description="asset, liability, equity, income, cost_of_sales or expense. Needed for ratios.")
    current: bool | None = Field(
        None, description="For asset or liability accounts: true if current, false if non-current. Needed for the current ratio.")
    suspense: bool = Field(
        False, description="True for suspense, clearing or uncategorised accounts. Names containing 'suspense' or "
        "'uncategorised' are flagged automatically.")


class TrialBalanceInput(BaseModel):
    """Trial balance lines for one entity at one balance date. Amounts in AUD."""

    accounts: list[TBAccount] = Field(min_length=1)
    tolerance: float = Field(0.005, ge=0, description="Largest debit-credit difference treated as balanced.")


@calculator("trial_balance_check", TrialBalanceInput)
def trial_balance_check(figures: Figures, inp: TrialBalanceInput) -> dict:
    """Checks a trial balance: total debits vs credits, whether it balances, the difference with likely causes
    (transposition, one-sided or reversed entry), suspense or clearing balances, and basic ratios (gross margin,
    net profit margin, current ratio) when accounts carry a type. Inputs: accounts with name, debit, credit and
    optional type, current flag and suspense flag. Use at month end or year end before preparing tax or BAS working
    papers. Not an audit; it only tests arithmetic and flags obvious ledger problems."""
    warnings: list[str] = []
    assumptions = ["Debit and credit balances are as at the same balance date, after all adjusting journals."]
    td = _r(sum(a.debit for a in inp.accounts))
    tc = _r(sum(a.credit for a in inp.accounts))
    diff = _r(td - tc)
    balanced = abs(diff) <= inp.tolerance

    hints: list[str] = []
    if not balanced:
        cents = round(abs(diff) * 100)
        nets = [abs(a.debit - a.credit) for a in inp.accounts]
        if cents % 9 == 0:
            hints.append("The difference is divisible by 9: look for a transposed or slid digit.")
        if any(abs(n - abs(diff)) < 0.005 for n in nets):
            hints.append("An account balance equals the difference: an account may be omitted, or its opposite entry missing.")
        if any(abs(n - abs(diff) / 2) < 0.005 for n in nets if n):
            hints.append("Half the difference equals an account balance: an entry may be posted to the wrong side.")
        if not hints:
            hints.append("No pattern found; check for a one-sided journal, an unposted batch or a missing account.")

    suspense_accounts, suspense_bal = [], 0.0
    for a in inp.accounts:
        if a.suspense or any(w in a.name.lower() for w in _SUSPENSE_WORDS):
            bal = _r(a.debit - a.credit)
            if bal:
                suspense_accounts.append({"name": a.name, "balance_debit_positive": bal})
                suspense_bal += bal
    if suspense_accounts:
        warnings.append("Suspense or clearing balance is not nil: clear it to real accounts before year end reporting.")

    def bal(kind: str) -> float:
        tot = 0.0
        for a in inp.accounts:
            if a.type == kind:
                tot += (a.debit - a.credit) if kind in _DEBIT_NORMAL else (a.credit - a.debit)
        return tot

    typed = [a for a in inp.accounts if a.type]
    ratios: dict = {}
    if typed:
        income, cos, exp = bal("income"), bal("cost_of_sales"), bal("expense")
        net = income - cos - exp
        ratios["total_income"] = _r(income)
        ratios["cost_of_sales"] = _r(cos)
        ratios["expenses"] = _r(exp)
        ratios["net_profit"] = _r(net)
        ratios["gross_margin"] = round((income - cos) / income, 4) if income else None
        ratios["net_profit_margin"] = round(net / income, 4) if income else None
        ca = sum((a.debit - a.credit) for a in inp.accounts if a.type == "asset" and a.current is True)
        cl = sum((a.credit - a.debit) for a in inp.accounts if a.type == "liability" and a.current is True)
        if any(a.current is not None for a in typed):
            ratios["current_assets"] = _r(ca)
            ratios["current_liabilities"] = _r(cl)
            ratios["current_ratio"] = round(ca / cl, 4) if cl else None
        else:
            ratios["current_ratio"] = None
            assumptions.append("Current ratio not calculated: no account has a current flag.")
        if any(a.type is None for a in inp.accounts):
            warnings.append("Some accounts have no type; ratios exclude them.")
    else:
        assumptions.append("No account types given, so ratios were not calculated.")

    return {
        "total_debits": td, "total_credits": tc, "difference": diff, "balanced": balanced,
        "hints": hints, "suspense": {"accounts": suspense_accounts, "net_debit_balance": _r(suspense_bal)},
        "ratios": ratios, "assumptions": assumptions, "warnings": warnings,
    }


# ------------------------------------------------------------------ GST control

class GstReconInput(BaseModel):
    """GST control account versus the BAS lodged, one period. Amounts in AUD, GST amounts only."""

    period: str = Field("", description="Label such as 'Q4 2026-27' or 'June 2027'.")
    ledger_gst_collected: float = Field(ge=0, description="GST on sales per the ledger for the period (credit side of the GST control account).")
    ledger_gst_paid: float = Field(ge=0, description="GST credits on purchases per the ledger (debit side).")
    bas_1a: float = Field(ge=0, description="GST on sales reported at label 1A on the BAS lodged.")
    bas_1b: float = Field(ge=0, description="GST on purchases reported at label 1B on the BAS lodged.")
    ledger_taxable_sales_ex_gst: float | None = Field(
        None, ge=0, description="Optional: ledger sales coded as GST on income (GST-exclusive), to test the GST charged.")
    ledger_creditable_purchases_ex_gst: float | None = Field(
        None, ge=0, description="Optional: ledger purchases coded with GST credits (GST-exclusive), to test the credits.")
    opening_balance_payable: float | None = Field(
        None, description="Optional roll-forward: GST control opening balance, positive = payable to the ATO.")
    payments_to_ato: float = Field(0, ge=0, description="Roll-forward: payments to the ATO in the period.")
    refunds_from_ato: float = Field(0, ge=0, description="Roll-forward: refunds received from the ATO in the period.")
    closing_balance_payable: float | None = Field(
        None, description="Optional roll-forward: GST control closing balance per ledger, positive = payable.")
    tolerance: float = Field(1.0, ge=0, description="Largest variance treated as rounding.")


@calculator("gst_control_reconciliation", GstReconInput)
def gst_control_reconciliation(figures: Figures, inp: GstReconInput) -> dict:
    """Reconciles the GST control account to the BAS lodged for a period. Inputs: GST collected and GST paid per the
    ledger, BAS labels 1A and 1B, optionally GST-exclusive sales and purchases (to test the ledger GST against the
    GST rate), and an opening/closing roll-forward with ATO payments and refunds. Returns variances on 1A, 1B and net
    GST, the GST-inclusive size of a transaction that would explain each variance, and reconciling hints. Use at BAS
    time and at year end when the GST control account does not clear to nil after lodgment."""
    rate = figures.get("gst.rate")
    inclusive_factor = (1 + rate) / rate  # GST-inclusive value of a transaction whose GST is the variance
    warnings: list[str] = []
    hints: list[str] = []

    v1a = _r(inp.ledger_gst_collected - inp.bas_1a)
    v1b = _r(inp.ledger_gst_paid - inp.bas_1b)
    net_ledger = _r(inp.ledger_gst_collected - inp.ledger_gst_paid)
    net_bas = _r(inp.bas_1a - inp.bas_1b)
    net_var = _r(net_ledger - net_bas)
    tol = inp.tolerance

    def status(v: float) -> str:
        return "agrees" if abs(v) <= tol else "variance"

    def explain(label: str, v: float, side: str) -> None:
        if abs(v) <= tol:
            return
        direction = "more" if v > 0 else "less"
        hints.append(
            f"Ledger {side} is {direction} than {label} by {abs(v):.2f}: a GST-inclusive transaction of about "
            f"{abs(v) * inclusive_factor:.2f} miscoded, omitted or dated in another period would explain it.")

    explain("1A", v1a, "GST collected")
    explain("1B", v1b, "GST paid")
    if abs(net_var) > tol:
        warnings.append("Ledger GST does not agree to the BAS lodged: identify the transactions and decide whether an "
                        "adjustment goes in the next BAS or a revised BAS is needed.")

    checks: dict = {}
    if inp.ledger_taxable_sales_ex_gst is not None:
        exp = _r(inp.ledger_taxable_sales_ex_gst * rate)
        checks["expected_gst_on_sales"] = exp
        checks["gst_on_sales_vs_expected"] = _r(inp.ledger_gst_collected - exp)
        if abs(checks["gst_on_sales_vs_expected"]) > tol:
            hints.append("GST collected differs from the GST rate applied to GST-coded sales: check GST-free, input-taxed "
                         "or margin scheme sales coded as taxable, rounding on invoices, or sales coded as taxable with no GST.")
    if inp.ledger_creditable_purchases_ex_gst is not None:
        exp = _r(inp.ledger_creditable_purchases_ex_gst * rate)
        checks["expected_gst_on_purchases"] = exp
        checks["gst_on_purchases_vs_expected"] = _r(inp.ledger_gst_paid - exp)
        if abs(checks["gst_on_purchases_vs_expected"]) > tol:
            hints.append("GST paid differs from the GST rate applied to GST-coded purchases: check input-taxed, private or "
                         "capital acquisitions, purchases without a valid tax invoice, or partial credit apportionment.")

    roll: dict = {}
    if inp.opening_balance_payable is not None:
        expected_close = _r(inp.opening_balance_payable + net_ledger - inp.payments_to_ato + inp.refunds_from_ato)
        roll["expected_closing_balance_payable"] = expected_close
        if inp.closing_balance_payable is not None:
            u = _r(inp.closing_balance_payable - expected_close)
            roll["closing_balance_per_ledger"] = _r(inp.closing_balance_payable)
            roll["unexplained_difference"] = u
            if abs(u) > tol:
                hints.append("The control account roll-forward does not agree: look for manual journals to the GST account, "
                             "ATO payments coded elsewhere, or GST posted to it from non-GST accounts.")
    else:
        roll = {"note": "No opening balance given, so no roll-forward was done."}

    return {
        "period": inp.period,
        "gst_rate_used": rate,
        "label_1a": {"ledger": _r(inp.ledger_gst_collected), "bas": _r(inp.bas_1a), "variance": v1a, "status": status(v1a)},
        "label_1b": {"ledger": _r(inp.ledger_gst_paid), "bas": _r(inp.bas_1b), "variance": v1b, "status": status(v1b)},
        "net_gst": {"ledger": net_ledger, "bas": net_bas, "variance": net_var, "status": status(net_var)},
        "reconciled": abs(v1a) <= tol and abs(v1b) <= tol,
        "rate_checks": checks,
        "roll_forward": roll,
        "hints": hints,
        "assumptions": ["Amounts are GST only. Variances are ledger minus BAS lodged; positive means the ledger is higher."],
        "warnings": warnings,
    }


# ------------------------------------------------------------------ prepayments

class PrepaymentInput(BaseModel):
    """One prepaid expense. Amount in AUD is the deductible amount excluding any GST credit."""

    amount: float = Field(gt=0, description="Prepaid amount, excluding input tax credits (GST credits reduce the amount).")
    payment_date: date
    service_start: date = Field(description="First day the goods or services are provided.")
    service_end: date = Field(description="Last day the goods or services are provided.")
    taxpayer: Literal["small_business", "individual_non_business", "other_business", "other_non_business"] = Field(
        description="small_business = small business entity, or would be one if the aggregated turnover threshold were the "
        "medium-entity ceiling; individual_non_business = individual with deductible non-business expenditure; "
        "other_business = larger business (apportion); other_non_business = company, trust or partnership with non-business "
        "expenditure (apportion).")
    aggregated_turnover: float | None = Field(
        None, ge=0, description="Optional. If given for small_business and at or above the medium-entity ceiling, the 12-month "
        "rule is not applied.")
    tax_shelter_arrangement: bool = Field(False, description="Prepayment is under a tax shelter arrangement.")
    excluded_expenditure: Literal["none", "required_by_law", "salary_or_wages", "capital_private_domestic"] = Field(
        "none", description="Excluded expenditure category; excluded amounts are deductible in the year incurred.")
    claim_immediate_if_eligible: bool = Field(
        True, description="The 12-month rule is a concession the taxpayer chooses; false forces apportionment.")

    @model_validator(mode="after")
    def _dates(self):
        if self.service_end < self.service_start:
            raise ValueError("service_end is before service_start")
        return self


@calculator("prepayment_deduction", PrepaymentInput)
def prepayment_deduction(figures: Figures, inp: PrepaymentInput) -> dict:
    """Works out the deduction for a prepaid expense under the prepayment rules (ITAA 1936 Subdiv H of Div 3): immediate
    deduction in the year of payment if the expenditure is excluded (below the excluded amount, required by law, wages,
    capital or private) or satisfies the 12-month rule (small business entity, would-be small business entity, or
    individual non-business expenditure; service period of 12 months or less ending by the last day of the next income
    year); otherwise apportions by days over the eligible service period (capped at 10 years). Inputs: amount excluding
    GST credits, payment date, service start and end, taxpayer type. Returns the year-by-year schedule and the amount
    for the income year requested. Use at year end for insurance, subscriptions, rent, advertising and similar prepayments."""
    max_months = figures.get("bookkeeping.prepayment_max_service_months")
    max_years = figures.get("bookkeeping.prepayment_max_apportion_years")
    excluded_amt = figures.get("bookkeeping.prepayment_excluded_amount")
    ceiling = figures.get("bookkeeping.medium_entity_turnover_ceiling")

    if inp.tax_shelter_arrangement:
        raise Refusal("AU-BKP-002", "prepayment under a tax shelter arrangement")

    assumptions = [
        "The expense would otherwise be deductible in full in the year incurred (nexus to income, not capital or private).",
        "Expenditure is incurred on the payment date.",
        "Eligible service period starts on the later of the payment date and the first day the services are provided.",
    ]
    warnings: list[str] = []
    pay_year = _income_year_start(inp.payment_date)
    start = max(inp.service_start, inp.payment_date)
    end = inp.service_end
    if end < start:
        raise Refusal("AU-BKP-002", "service ends before the expenditure is incurred; not a prepayment")
    cap_end = _anniversary(start, max_years) - timedelta(days=1)
    capped = end > cap_end
    if capped:
        end = cap_end
        warnings.append("Eligible service period capped at the maximum apportionment period.")
    days = (end - start).days + 1

    rule_eligible_taxpayer = inp.taxpayer in ("small_business", "individual_non_business")
    if inp.taxpayer == "small_business" and inp.aggregated_turnover is not None and inp.aggregated_turnover >= ceiling:
        rule_eligible_taxpayer = False
        warnings.append("Aggregated turnover is at or above the medium-entity ceiling: 12-month rule not available.")

    within_months = (end + timedelta(days=1)) <= _months_later(start, max_months)
    ends_by = date(pay_year + 2, 6, 30)  # last day of the income year after the payment year
    ends_in_time = end <= ends_by
    twelve_month_rule = within_months and ends_in_time

    treatment: str
    reason: str
    if inp.excluded_expenditure != "none":
        treatment, reason = "immediate", f"Excluded expenditure ({inp.excluded_expenditure}): prepayment rules do not apply."
    elif inp.amount < excluded_amt:
        treatment, reason = "immediate", "Prepaid amount is below the excluded amount: prepayment rules do not apply."
    elif rule_eligible_taxpayer and twelve_month_rule and inp.claim_immediate_if_eligible:
        treatment, reason = "immediate", "12-month rule satisfied."
    else:
        treatment = "apportioned"
        if not rule_eligible_taxpayer:
            reason = "Taxpayer is not eligible for the 12-month rule."
        elif not within_months:
            reason = "Eligible service period is longer than 12 months."
        elif not ends_in_time:
            reason = "Eligible service period ends after the last day of the next income year."
        else:
            reason = "12-month rule available but the taxpayer chose not to use it."

    schedule: list[dict] = []
    if treatment == "immediate":
        schedule.append({"income_year": _label(pay_year), "days": None, "deduction": _r(inp.amount)})
    else:
        first, last = _income_year_start(start), _income_year_start(end)
        rows = []
        for y in range(min(pay_year, first), last + 1):
            ys, ye = date(y, 7, 1), date(y + 1, 6, 30)
            lo, hi = max(start, ys), min(end, ye)
            d = max(0, (hi - lo).days + 1)
            rows.append([y, d])
        last_idx = max(i for i, rr in enumerate(rows) if rr[1] > 0)
        allocated = 0.0
        for i, (y, d) in enumerate(rows):
            amt = 0.0
            if d:
                amt = _r(inp.amount - allocated) if i == last_idx else _r(inp.amount * d / days)
                allocated += amt
            schedule.append({"income_year": _label(y), "days": d, "deduction": amt})

    this_year = next((s["deduction"] for s in schedule if s["income_year"] == figures.income_year), 0.0)
    if _label(pay_year) != figures.income_year and treatment == "immediate":
        warnings.append(f"Payment falls in {_label(pay_year)}, not the income year requested; the immediate deduction belongs to {_label(pay_year)}.")

    return {
        "treatment": treatment,
        "reason": reason,
        "twelve_month_rule": {"service_period_within_12_months": within_months,
                              "ends_by_last_day_of_next_income_year": ends_in_time,
                              "satisfied": twelve_month_rule},
        "eligible_service_period": {"start": start.isoformat(), "end": end.isoformat(), "days": days},
        "payment_income_year": _label(pay_year),
        "schedule": schedule,
        "deduction_in_requested_income_year": this_year,
        "assumptions": assumptions,
        "warnings": warnings,
    }


# ------------------------------------------------------------------ large proprietary test

class EntityFigures(BaseModel):
    name: str = ""
    revenue: float = Field(0, ge=0, description="Revenue for the financial year (AUD, accounting-standard basis).")
    gross_assets: float = Field(0, ge=0, description="Gross assets at year end (AUD, total assets, not net).")
    employees: float = Field(0, ge=0, description="Employees at year end, part-time counted as a fraction of full-time equivalent.")


class LargeProprietaryInput(BaseModel):
    """Size test for one proprietary company and the entities it controls, one financial year."""

    entity: EntityFigures = Field(description="The company itself.")
    controlled_entities: list[EntityFigures] = Field(default_factory=list, description="Each entity the company controls (AASB 10).")
    intra_group_revenue_eliminations: float = Field(0, ge=0, description="Revenue between group entities to eliminate on consolidation.")
    intra_group_asset_eliminations: float = Field(0, ge=0, description="Intra-group balances and investments to eliminate from consolidated gross assets.")
    company_type: Literal["proprietary", "public", "disclosing_entity", "other_non_proprietary"] = "proprietary"
    control_uncertain: bool = Field(False, description="True if whether the company controls another entity is unclear (AASB 10 judgement).")
    foreign_controlled: bool = False
    crowd_sourced_funding_shareholders: bool = False
    asic_direction: bool = Field(False, description="ASIC has directed the company to prepare a report.")
    shareholder_direction: bool = Field(False, description="Qualifying shareholders have directed the company to prepare a report.")
    financial_year_end: date | None = Field(None, description="Balance date, to give the ASIC lodgment date.")


@calculator("large_proprietary_test", LargeProprietaryInput)
def large_proprietary_test(figures: Figures, inp: LargeProprietaryInput) -> dict:
    """Corporations Act s 45A size test for a proprietary company: consolidated revenue, consolidated gross assets and
    employees (full-time equivalent) of the company plus the entities it controls, against the prescribed thresholds. Large
    if at least 2 of 3 are met, otherwise small. Returns each test, the classification, whether a financial report is
    required (large, or small with a trigger such as foreign control, crowd-sourced funding, ASIC or shareholder direction)
    and the ASIC lodgment date. Use for 'do we need audited financial statements', 'are we a large proprietary company'.
    Refuses for entities that are not proprietary companies and where control of another entity is uncertain."""
    if inp.company_type != "proprietary":
        raise Refusal("AU-BKP-003", f"company type {inp.company_type}")
    if inp.control_uncertain:
        raise Refusal("AU-BKP-001", "whether the company controls another entity is a consolidation judgement")

    t_rev = figures.get("asic.large_proprietary_revenue")
    t_assets = figures.get("asic.large_proprietary_gross_assets")
    t_emp = figures.get("asic.large_proprietary_employees")
    lodge_months = int(figures.get("bookkeeping.financial_report_lodgement_months"))

    group = [inp.entity, *inp.controlled_entities]
    revenue = _r(sum(e.revenue for e in group) - inp.intra_group_revenue_eliminations)
    assets = _r(sum(e.gross_assets for e in group) - inp.intra_group_asset_eliminations)
    employees = round(sum(e.employees for e in group), 2)

    tests = {
        "revenue": {"value": revenue, "threshold": t_rev, "meets_large_test": revenue >= t_rev},
        "gross_assets": {"value": assets, "threshold": t_assets, "meets_large_test": assets >= t_assets},
        "employees": {"value": employees, "threshold": t_emp, "meets_large_test": employees >= t_emp},
    }
    large_count = sum(1 for t in tests.values() if t["meets_large_test"])
    large = large_count >= 2

    triggers = [k for k, v in (("foreign_controlled", inp.foreign_controlled),
                               ("crowd_sourced_funding_shareholders", inp.crowd_sourced_funding_shareholders),
                               ("asic_direction", inp.asic_direction),
                               ("shareholder_direction", inp.shareholder_direction)) if v]
    required = large or bool(triggers)
    notes: list[str] = []
    if large:
        notes.append("Large proprietary company: must prepare an annual financial report and directors' report, have it audited, "
                     "send it to members and lodge it with ASIC (Corporations Act ss 292, 301, 314-319), unless ASIC relief applies.")
    elif triggers:
        notes.append("Small proprietary company with a reporting trigger: the report is required for this year; audit and lodgment "
                     "depend on the trigger and any ASIC relief. Confirm which applies.")
    else:
        notes.append("Small proprietary company: no annual financial report to ASIC unless later directed. Tax and financial "
                     "records must still be kept.")
    lodge_by = None
    if large and inp.financial_year_end:
        lodge_by = _add_months(inp.financial_year_end, lodge_months).isoformat()

    warnings = ["Consolidated revenue and gross assets follow the accounting standards; control is decided under AASB 10.",
                "Employee count is at year end, part-time employees as a fraction of full-time equivalent (s 45A(5))."]
    if inp.controlled_entities and not (inp.intra_group_revenue_eliminations or inp.intra_group_asset_eliminations):
        warnings.append("Controlled entities included with no intra-group eliminations: confirm figures are already consolidated.")

    return {
        "classification": "large" if large else "small",
        "tests_met_for_large": large_count,
        "tests": tests,
        "consolidated_entities": len(group),
        "financial_report_required": required,
        "reporting_triggers": triggers,
        "lodgment_due_by": lodge_by,
        "reporting_notes": notes,
        "assumptions": ["The company is a proprietary company and a full financial year is being tested.",
                        "Thresholds are those prescribed by Corporations Regulations 2001 reg 1.0.02B."],
        "warnings": warnings,
    }
