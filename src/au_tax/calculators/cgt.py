"""Capital gains tax: single-event capital gain (discount, frozen indexation and the 1 July 2027 regime),
net capital gain with loss ordering, the main residence exemption, and a small business concession screen.

Law (ITAA 1997 compilation in force 1 Jul 2026, which incorporates Act No. 49 of 2026):
- Events and timing: s104-10 (A1 at contract date; pre-CGT assets s104-10(5)), s104-160/165 (I1).
- Cost base and reduced cost base: s110-25, s110-55; capital works deductions excluded s110-45(1B).
- Discount: Div 115 (s115-25 12 months; s115-25(3) excluded events; s115-100 percentages; s115-105/115
  foreign and temporary residents after 8 May 2012; s115-102 new residential dwellings from 1 Jul 2027).
- Frozen indexation: s110-36(1), s114-10, s960-275(2),(5) (Sep 1999 CPI; factor to 3 decimal places).
- 1 July 2027 regime (Act No. 49 of 2026 Sch 1): indexation s110-36(1A), s114-25, s960-275(1B); deemed sale
  and reacquisition at market value just before 1 Jul 2027 (s112-155, s112-160, s112-175); new loss and gain
  ordering (s102-5, s102-6); Div 119 minimum tax on capital gains (with ITRA s12AA).
- Losses: s102-5, s102-10, s102-15, s108-10 (collectables), s108-20 (personal use), s118-10.
- Main residence: s118-110, s118-140, s118-145, s118-185, s118-190, s118-192.
- Foreign residents: s855-10 (taxable Australian property only); FRCGW TAA 1953 Sch 1 Subdiv 14-D.
- Small business: s152-10, s152-15, s152-35, s152-205(2) (50% active asset reduction gate from 2027-28).
Rates and dollar thresholds come from data/rates via Figures, read from the rates file of the income year of the
CGT event (its contract date), never from the year the tool happened to be called with: an event on or after
1 Jul 2027 uses 2027-28 or later figures (figures_for_income_year) and refuses when that year has no rates file or
a needed figure has no value (the post-2027 CPI index numbers, cgt.indexation_cpi_from_2027, are null until
published, so the indexed post-1 Jul 2027 part is refused AU-GEN-003, at field level when a deferred component exists). Statutory dates (20 Sep 1985, 21 Sep 1999,
8 May 2012, 20 Aug 1996, 1 Jul 2027) and periods (12 months, 6 years, 6 months) are fixed in the Act.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from au_tax.figures import UNPUBLISHED, FigureError, Figures
from au_tax.registry import InputError, Refusal, calculator, figure_refusal, refusal_catalogue

PRE_CGT_CUTOFF = date(1985, 9, 20)       # acquired before this day = pre-CGT (s104-10(5))
FROZEN_INDEXATION_LAST = date(1999, 9, 21)  # acquired at or before 11.45 am 21 Sep 1999 (s110-36(1))
FOREIGN_DISCOUNT_DATE = date(2012, 5, 8)  # s115-105, s115-115
REFORM_DATE = date(2027, 7, 1)            # Act No. 49 of 2026 Sch 1
REFORM_YEAR = "2027-28"                   # first income year with a CGT event on or after REFORM_DATE
FIRST_INCOME_USE_CUTOFF = date(1996, 8, 20)  # s118-192(1)(aa)

EntityType = Literal["individual", "trust", "complying_super_fund", "company"]
Residency = Literal["resident", "foreign", "temporary_resident"]
AssetType = Literal["shares_or_units", "real_property", "crypto", "collectable", "personal_use_asset", "other"]
CgtEvent = Literal["A1", "C1", "C2", "D1", "D2", "D3", "E", "F", "H2", "I1", "K6", "K", "other"]
Special = Literal[
    "small_business_concession_application", "rollover", "marriage_breakdown_rollover", "trust_streaming",
    "earnout", "defi_or_crypto_lending", "crypto_wrapping_or_bridging", "airdrop_in_business",
    "crypto_trading_business", "non_widely_held_entity_interest", "deceased_estate_asset",
]
NO_DISCOUNT_EVENTS = {"D1", "D2", "D3", "F", "H2"}  # s115-25(3)
MODELLED_EVENTS = {"A1", "C1", "C2", "D1", "H2", "I1"}

SPECIAL_CODES = {
    "small_business_concession_application": "AU-CGT-001",
    "rollover": "AU-CGT-002",
    "marriage_breakdown_rollover": "AU-CGT-002",
    "trust_streaming": "AU-CGT-003",
    "earnout": "AU-CGT-004",
    "non_widely_held_entity_interest": "AU-CGT-004",
    "defi_or_crypto_lending": "AU-CGT-005",
    "crypto_wrapping_or_bridging": "AU-CGT-005",
    "airdrop_in_business": "AU-CGT-005",
    "crypto_trading_business": "AU-CGT-005",
    "deceased_estate_asset": "AU-CGT-008",
}


# ---------------------------------------------------------------- shared helpers

def _r(x: float) -> float:
    return round(x + 0.0, 2)


def add_months(d: date, n: int) -> date:
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def held_12_months(acquired: date, event: date) -> bool:
    """s115-25(1) / s114-10(1): acquired at least 12 months before the event. The ATO excludes the day of
    acquisition and the day of the event, so the earliest qualifying event is 12 months and 1 day later."""
    return event >= add_months(acquired, 12) + timedelta(days=1)


def days_incl(a: date, b: date) -> int:
    return max(0, (b - a).days + 1)


def income_year_of(d: date) -> str:
    start = d.year if d.month >= 7 else d.year - 1
    return f"{start}-{str(start + 1)[-2:]}"


def round_factor(x: float) -> float:
    """s960-275(5): three decimal places, rounding up if the fourth is 5 or more."""
    return float(Decimal(str(x)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))


def _escalation(code: str, detail: str = "") -> dict:
    entry = refusal_catalogue().get(code, {})
    return {"code": code, "message": entry.get("message"), "route": entry.get("route"), "detail": detail}


def figures_for_income_year(figures: Figures, year: str, warnings: list[str]) -> Figures:
    """Figures from the rates file of an income year, for a rule that is date-effective (CONVENTIONS section 3).
    The CGT regime changes on 1 Jul 2027, so from 2027-28 the figures must come from that year's file and never from
    an earlier one: a year with no rates file refuses (AU-GEN-003). Before 2027-28 the CGT figures read here (discount
    rates, thresholds, the frozen CPI table) are statutory and the same in every year, so a year with no file (an
    older event) falls back to the file the tool was called with, unless that file is itself post-reform."""
    try:
        chosen = figures.for_year(year)
    except FigureError:
        if year >= REFORM_YEAR:
            raise FigureError(f"no rates file for {year}: CGT events on or after 1 Jul 2027 use the figures of their own "
                              "income year and nothing is carried forward from an earlier one", UNPUBLISHED)
        if figures.income_year >= REFORM_YEAR:
            raise FigureError(f"no rates file for {year}, and the {figures.income_year} file holds the figures for the "
                              "regime that starts 1 Jul 2027 (no discount for individuals), so it cannot stand in for an "
                              "earlier year", UNPUBLISHED)
        warnings.append(f"No rates file for {year}; the CGT figures read here are statutory and the same in every year "
                        f"before 2027-28, so the {figures.income_year} file was used.")
        return figures
    if chosen.income_year != figures.income_year:
        warnings.append(f"The tool was called for {figures.income_year}, but the CGT event falls in {year}: figures were "
                        f"read from the {year} rates file (reported in figures_used as key@{year}).")
    return chosen


def event_figures(figures: Figures, event: date, warnings: list[str]) -> Figures:
    """Figures for the income year of a CGT event (contract date, s104-10(3))."""
    return figures_for_income_year(figures, income_year_of(event), warnings)


def discount_rate_for(figures: Figures, entity: EntityType) -> float:
    if entity in ("individual", "trust"):
        return figures.get("cgt.discount_individual_trust")
    if entity == "complying_super_fund":
        return figures.get("cgt.discount_complying_super_fund")
    return figures.get("cgt.discount_company")


def _tax_on(brackets: list[dict], x: float) -> float:
    total = 0.0
    for b in brackets:
        lo, hi = b["from"], b["to"] if b["to"] is not None else float("inf")
        if x > lo:
            total += b["rate"] * (min(x, hi) - lo)
    return total


def minimum_tax_gap(figures: Figures, taxable_income: float, mtcg: float) -> dict:
    """ITAA 1997 s119-10(2) method statement. `figures` must be the 2027-28 (or later) rates: Division 119 applies to
    CGT events on or after 1 Jul 2027, and the resident rates that step 2 and step 3 use are that year's table (ITRA
    Sch 7 Pt I cl 1 table for 2027-28 or a later year), read from the same file."""
    if figures.income_year < REFORM_YEAR:
        raise ValueError(f"Division 119 minimum tax applies from {REFORM_YEAR}; got figures for {figures.income_year}")
    rate = figures.get("cgt.minimum_tax_rate_from_2027_28")
    brackets = figures.get("individual.resident_rates")
    step1 = rate * mtcg
    step2 = _tax_on(brackets, taxable_income)
    step3 = _tax_on(brackets, max(0.0, taxable_income - mtcg))
    step4 = step2 - step3
    gap = int(max(0.0, step1 - step4))  # step 6 rounds down to whole dollars
    return {"minimum_tax_capital_gain": _r(mtcg), "step1_minimum_tax": _r(step1),
            "step2_basic_tax_on_taxable_income": _r(step2), "step3_basic_tax_without_gain": _r(step3),
            "step4_tax_attributable_to_gain": _r(step4), "minimum_tax_gap_amount": gap}


# ---------------------------------------------------------------- capital_gain

class CostItem(BaseModel):
    """One amount in the cost base. Dates matter for indexation and for the 1 July 2027 split."""

    element: Literal[1, 2, 3, 4, 5] = Field(description="1 acquisition price, 2 incidental costs, 3 costs of ownership "
                                            "(interest, rates, insurance, repairs not deducted), 4 capital improvements, "
                                            "5 costs of defending title.")
    amount: float = Field(ge=0)
    date_incurred: date | None = Field(None, description="Date incurred (contract date for the purchase price).")
    disposal_cost: bool = Field(False, description="True for incidental costs of the sale itself (agent, legal).")


class CapitalGainInput(BaseModel):
    """One CGT event happening to one asset. Amounts in AUD."""

    entity_type: EntityType = Field("individual", description="Who made the gain.")
    cgt_event: CgtEvent = Field("A1", description="A1 disposal (sale, swap of crypto); C1 loss or destruction; "
                                "C2 cancellation or expiry of intangible (options, wrapping per draft TD 2026/D2); "
                                "D1 creating contractual rights; H2 receipt for an event relating to a CGT asset; "
                                "I1 ceasing to be an Australian resident. Others are escalated.")
    asset_type: AssetType = Field("other")
    acquisition_date: date = Field(description="Contract date of acquisition (or date acquired if no contract).")
    event_date: date = Field(description="Contract date of the disposal (s104-10(3)), not settlement.")
    capital_proceeds: float = Field(ge=0, description="Sale price or market value received (I1: market value).")
    first_element: float = Field(0, ge=0, description="Purchase price (element 1).")
    incidental_costs_acquisition: float = Field(0, ge=0, description="Stamp duty, legal, buyer's agent (element 2).")
    incidental_costs_disposal: float = Field(0, ge=0, description="Agent commission, legal costs on sale (element 2).")
    ownership_costs: float = Field(0, ge=0, description="Non-deductible holding costs (element 3), e.g. interest, rates "
                                   "on land never income producing. Never include amounts already deducted.")
    capital_improvements: float = Field(0, ge=0, description="Capital expenditure increasing value (element 4).")
    title_costs: float = Field(0, ge=0, description="Costs to establish or defend title (element 5).")
    cost_base_items: list[CostItem] = Field(default_factory=list, description="Dated cost base items, used instead of "
                                            "or as well as the scalar fields when dates matter.")
    capital_works_deductions: float = Field(0, ge=0, description="Division 43 deductions claimed; they reduce the cost "
                                            "base and reduced cost base.")
    residency: Residency = Field("resident", description="Residency of the individual at the time of the event.")
    foreign_or_temporary_days_after_8_may_2012: int | None = Field(
        None, ge=0, description="Days after 8 May 2012 within the ownership period when the individual was a foreign "
        "or temporary resident. Default: none if resident at the event, all such days if not.")
    foreign_or_temporary_on_8_may_2012: bool = Field(False)
    choose_market_value_method_8_may_2012: bool = Field(False, description="s115-115(4) choice.")
    market_value_8_may_2012: float | None = Field(None, ge=0)
    taxable_australian_property: bool | None = Field(
        None, description="Foreign or temporary residents only: is the asset taxable Australian property? "
        "Defaults to true for real property and false otherwise.")
    indirect_real_property_interest: bool = Field(False, description="Interest in an entity whose TAP status depends "
                                                  "on the principal asset test (escalated).")
    frcgw_clearance_certificate: bool | None = Field(None, description="Real property: vendor gave the purchaser a "
                                                     "clearance certificate.")
    new_residential_dwelling: bool = Field(False, description="Taxpayer asserts the dwelling is a new residential "
                                           "dwelling (s115-102). Relevant only to events from 1 July 2027.")
    residential_dwelling: bool | None = Field(None, description="Asset is (or was) a residential dwelling "
                                              "(s26-160). Defaults to true for real_property.")
    choose_indexation_for_new_dwelling: bool = Field(False, description="s115-102(5) choice of indexation instead.")
    method_choice: Literal["best", "discount", "indexation"] = Field(
        "best", description="Assets acquired before 21 Sep 1999: frozen indexation or discount.")
    market_value_30_june_2027: float | None = Field(
        None, ge=0, description="Market value just before 1 July 2027; required for events on or after 1 July 2027 "
        "on assets held on 30 June 2027.")
    capital_losses_available: float = Field(0, ge=0, description="Current-year capital losses plus unapplied net "
                                            "capital losses from earlier years (not collectable or personal use), "
                                            "applied before the discount.")
    i1_choose_to_disregard: bool = Field(False, description="s104-165 choice to disregard I1 gains and losses.")
    taxable_income_including_gain: float | None = Field(
        None, ge=0, description="Events from 1 July 2027, resident individuals: taxable income for the year including "
        "this net gain, to test the minimum tax (Div 119).")
    receives_minimum_tax_exempt_payment: bool = Field(False, description="Received a payment listed in s119-15 (age "
                                                      "pension, JobSeeker, family tax benefit and others) in the year.")
    personal_use_crypto_claim: bool = Field(False, description="Crypto claimed as a personal use asset.")
    special_circumstances: list[Special] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check(self):
        if self.event_date < self.acquisition_date:
            raise ValueError("event_date is before acquisition_date")
        return self


def _items(inp: CapitalGainInput) -> list[CostItem]:
    items = list(inp.cost_base_items)
    for amt, el, dt, disp in (
        (inp.first_element, 1, inp.acquisition_date, False),
        (inp.incidental_costs_acquisition, 2, inp.acquisition_date, False),
        (inp.ownership_costs, 3, None, False),
        (inp.capital_improvements, 4, None, False),
        (inp.title_costs, 5, None, False),
        (inp.incidental_costs_disposal, 2, inp.event_date, True),
    ):
        if amt:
            items.append(CostItem(element=el, amount=amt, date_incurred=dt, disposal_cost=disp))
    return items


def _item_date(it: CostItem, inp: CapitalGainInput) -> date | None:
    if it.date_incurred is not None:
        return it.date_incurred
    if it.disposal_cost:
        return inp.event_date
    if it.element in (1, 2):
        return inp.acquisition_date
    return None


def _cpi_lookup(table: list[dict], d: date) -> float | None:
    for row in table:
        if row["from"] <= d <= row["to"]:
            return row["rate"]
    return None


def _frozen_indexed_cost_base(figures: Figures, inp: CapitalGainInput, items: list[CostItem],
                              warnings: list[str]) -> tuple[float, list[dict]]:
    """s110-36(1), s960-275(2),(5): index elements 1, 2, 4, 5 incurred by 21 Sep 1999 to the Sep 1999 quarter."""
    table = figures.get("cgt.frozen_indexation_cpi")
    sep99 = _cpi_lookup(table, date(1999, 9, 30))
    total, detail = 0.0, []
    for it in items:
        d = _item_date(it, inp)
        factor = 1.0
        if it.element != 3 and not it.disposal_cost and d is not None and d <= FROZEN_INDEXATION_LAST:
            cpi = _cpi_lookup(table, d)
            if cpi:
                factor = round_factor(sep99 / cpi)
        elif it.element in (4, 5) and d is None:
            warnings.append(f"Element {it.element} amount {it.amount} has no date, so it was not indexed.")
        total += it.amount * factor
        detail.append({"element": it.element, "amount": it.amount, "date": d.isoformat() if d else None,
                       "indexation_factor": factor, "indexed_amount": _r(it.amount * factor)})
    return total, detail


def _foreign_discount_pct(inp: CapitalGainInput, gain: float, cost_base_8_may: float,
                          assumptions: list[str]) -> float:
    """s115-115 percentage for an individual to whom s115-105 applies (pre-reform headline rate 50%)."""
    start, end = inp.acquisition_date, inp.event_date
    total = days_incl(start, end)
    after = days_incl(max(start, FOREIGN_DISCOUNT_DATE + timedelta(days=1)), end)
    fdays = inp.foreign_or_temporary_days_after_8_may_2012
    if fdays is None:
        fdays = after
        assumptions.append("Foreign or temporary resident for every day after 8 May 2012 in the ownership period "
                           "(days not given).")
    fdays = min(fdays, after)
    if start > FOREIGN_DISCOUNT_DATE:  # s115-115(2)
        return (total - fdays) / (2 * total)
    if not inp.foreign_or_temporary_on_8_may_2012:  # s115-115(3)
        return (total - fdays) / (2 * total)
    if inp.choose_market_value_method_8_may_2012 and inp.market_value_8_may_2012 is not None:  # s115-115(4)-(5)
        excess = inp.market_value_8_may_2012 - cost_base_8_may
        if excess > 0:
            if excess >= gain:
                return 0.5
            shortfall = gain - excess
            return (excess + shortfall * (after - fdays) / after) / (2 * gain)
    return (after - fdays) / (2 * total)  # s115-115(6)


def _screen_refusals(inp: CapitalGainInput) -> None:
    for s in inp.special_circumstances:
        raise Refusal(SPECIAL_CODES[s], f"special circumstance: {s}")
    if inp.cgt_event == "E" or (inp.entity_type == "trust" and "trust_streaming" in inp.special_circumstances):
        raise Refusal("AU-CGT-003", "trust CGT event (E-series)")
    if inp.cgt_event not in MODELLED_EVENTS:
        raise Refusal("AU-CGT-004", f"CGT event {inp.cgt_event} not modelled")
    if inp.indirect_real_property_interest:
        raise Refusal("AU-CGT-009", "indirect Australian real property interest")


@calculator("capital_gain", CapitalGainInput)
def capital_gain(figures: Figures, inp: CapitalGainInput) -> dict:
    """Capital gain or loss for ONE CGT event on ONE asset (Australia), applying the law in force on the event's
    contract date: cost base (5 elements) and reduced cost base; pre-CGT exemption; collectable and personal use
    asset rules; 50% discount (individuals, trusts), one-third (complying super funds), none (companies), 12-month
    rule; apportioned discount for foreign and temporary residents after 8 May 2012; frozen indexation for assets
    acquired before 21 Sep 1999; foreign residents only taxed on taxable Australian property; FRCGW amount.
    For events on or after 1 July 2027 (Act No. 49 of 2026): individuals' deemed sale at market value just before
    1 July 2027 (discounted deferred gain) plus an indexed post-1 July 2027 gain, the retained 50% discount for new
    residential dwellings, the pre-CGT reset, and the 30% minimum tax gap (Div 119) when taxable income is given.
    Index numbers for the post-2027 indexation are read from the rates file only (never typed in): until they are
    published, an event that would be indexed on an asset held on 30 June 2027 still returns the deferred component
    (`deferred_component`: deemed sale notional gain, discount, discounted amount) with a field-level refusal
    (`field_refusals`, AU-GEN-003) for the post-1 July 2027 part and no net capital gain; an asset acquired on or after
    1 July 2027 has no deferred component and the whole event refuses AU-GEN-003. Rates come from the income year of the
    event. Optional capital_losses_available are applied before the discount. Use for any 'how much CGT / capital gain on
    selling shares, property, crypto' question; use net_capital_gain for several gains and losses in a year and
    main_residence_exemption for a home."""
    _screen_refusals(inp)
    assumptions: list[str] = []
    warnings: list[str] = []
    escalations: list[dict] = []
    figures = event_figures(figures, inp.event_date, warnings)  # date-effective: the income year of the event
    event, acq = inp.event_date, inp.acquisition_date
    post_reform = event >= REFORM_DATE
    regime = "from_1_july_2027" if post_reform else "before_1_july_2027"
    items = _items(inp)
    out: dict = {"event_income_year": income_year_of(event), "rates_year_used": figures.income_year,
                 "law_regime": regime, "cgt_event": inp.cgt_event, "capital_proceeds": _r(inp.capital_proceeds)}

    if inp.personal_use_crypto_claim:
        warnings.append("Crypto is a personal use asset only in narrow cases (acquired and used mainly to buy items "
                        "for personal use or consumption, usually held briefly). Investment holdings never qualify.")
    if inp.asset_type in ("personal_use_asset", "collectable"):
        items = [it for it in items if it.element != 3]  # s108-17, s108-30: no third element
    if inp.cgt_event == "I1":
        assumptions.append("CGT event I1: capital proceeds are the asset's market value when residency ceased "
                           "(s104-160(4)); taxable Australian property is not subject to I1.")
        if inp.entity_type != "individual" and inp.i1_choose_to_disregard:
            raise ValueError("only individuals can choose under s104-165")
    if inp.cgt_event == "D1":
        assumptions.append("CGT event D1: cost base is only the incidental costs of creating the right (s104-35); "
                           "no discount (s115-25(3)).")

    # --- foreign or temporary residents: taxable Australian property only (s855-10, s768-915)
    foreign = inp.entity_type == "individual" and inp.residency != "resident"
    if foreign or inp.entity_type != "individual" and inp.residency != "resident":
        tap = inp.taxable_australian_property
        if tap is None:
            tap = inp.asset_type == "real_property"
            assumptions.append(f"Taxable Australian property assumed {'yes (direct Australian real property)' if tap else 'no'}"
                               " - confirm.")
        if not tap:
            out.update(_zero_result("Gain or loss disregarded: foreign or temporary resident and the asset is not "
                                    "taxable Australian property (s855-10, s768-915)."))
            return {**out, "assumptions": assumptions, "warnings": warnings, "escalations": escalations}
    if inp.asset_type == "real_property" and inp.cgt_event == "A1":
        rate = figures.get("cgt.frcgw_rate")
        applies = foreign or inp.frcgw_clearance_certificate is False
        out["frcgw"] = {"rate": rate, "withholding_if_no_clearance": _r(rate * inp.capital_proceeds),
                        "applies": applies,
                        "note": "Purchaser withholds from the purchase price unless the vendor gives a clearance "
                                "certificate (residents) or a variation; the amount is a credit against the vendor's "
                                "tax, not the tax itself."}

    if inp.cgt_event == "I1" and inp.i1_choose_to_disregard:
        out.update(_zero_result("s104-165 choice made: I1 gain or loss disregarded; the assets are taxable Australian "
                                "property until sold or residency resumes."))
        return {**out, "assumptions": assumptions, "warnings": warnings, "escalations": escalations}

    if post_reform:
        body = _post_reform(figures, inp, items, assumptions, warnings)
    else:
        body = _pre_reform(figures, inp, items, assumptions, warnings)
    out.update(body)
    if post_reform and inp.new_residential_dwelling:
        warnings.append("New residential dwelling is defined by a Ministerial legislative instrument (s26-160(4)) "
                        "not made as at 29 Sep 2026; the retained discount assumes the dwelling will qualify.")
    return {**out, "assumptions": assumptions, "warnings": warnings, "escalations": escalations}


def _zero_result(reason: str) -> dict:
    return {"method": "disregarded", "reason": reason, "cost_base": None, "reduced_cost_base": None,
            "gross_capital_gain": 0.0, "capital_loss": 0.0, "discount_percentage": 0.0, "discount_amount": 0.0,
            "net_capital_gain": 0.0, "components": []}


def _cost_bases(items: list[CostItem], cw: float) -> tuple[float, float]:
    cb = sum(it.amount for it in items) - cw
    rcb = sum(it.amount for it in items if it.element != 3) - cw
    return max(0.0, cb), max(0.0, rcb)


def _exempt_small_assets(figures: Figures, inp: CapitalGainInput, items: list[CostItem]) -> str | None:
    first = sum(it.amount for it in items if it.element == 1)
    if inp.asset_type == "collectable" and first <= figures.get("cgt.collectable_exempt_max_cost"):
        return "Collectable with a first element of cost base at or below the collectables threshold: gain or loss " \
               "disregarded (s118-10(1))."
    if inp.asset_type == "personal_use_asset" and first <= figures.get("individual.personal_use_asset_cgt_exempt_max_cost"):
        return "Personal use asset with a first element of cost base at or below the personal use threshold: gain " \
               "disregarded (s118-10(3)); losses are always disregarded (s108-20(1))."
    return None


def _discount_eligible(inp: CapitalGainInput, acquired: date) -> tuple[bool, str]:
    if inp.entity_type == "company":
        return False, "companies cannot make discount capital gains (s115-10)"
    if inp.cgt_event in NO_DISCOUNT_EVENTS:
        return False, f"CGT event {inp.cgt_event} gains are not discount capital gains (s115-25(3))"
    if not held_12_months(acquired, inp.event_date):
        return False, "asset not held for at least 12 months, excluding the days of acquisition and the event (s115-25)"
    return True, ""


def _pre_reform(figures: Figures, inp: CapitalGainInput, items: list[CostItem], assumptions: list[str],
                warnings: list[str]) -> dict:
    acq, event = inp.acquisition_date, inp.event_date
    if acq < PRE_CGT_CUTOFF:
        return _zero_result("Pre-CGT asset (acquired before 20 September 1985): gain or loss disregarded "
                            "(s104-10(5)). Shares and trust interests may still trigger CGT event K6 (escalate).")
    small = _exempt_small_assets(figures, inp, items)
    cb, rcb = _cost_bases(items, inp.capital_works_deductions)
    if small:
        r = _zero_result(small)
        r.update(cost_base=_r(cb), reduced_cost_base=_r(rcb))
        return r
    proceeds = inp.capital_proceeds
    gain = max(0.0, proceeds - cb)
    loss = max(0.0, rcb - proceeds) if proceeds < rcb else 0.0
    if inp.asset_type == "personal_use_asset" and loss:
        loss = 0.0
        assumptions.append("Capital loss on a personal use asset disregarded (s108-20(1)).")
    res: dict = {"cost_base": _r(cb), "reduced_cost_base": _r(rcb), "gross_capital_gain": _r(gain),
                 "capital_loss": _r(loss)}
    if gain <= 0:
        res.update(method="loss" if loss else "nil", discount_percentage=0.0, discount_amount=0.0,
                   net_capital_gain=0.0, components=[] if not loss else [
                       {"category": "pre_2027", "capital_loss": _r(loss),
                        "collectable": inp.asset_type == "collectable"}])
        if loss:
            res["net_capital_loss_note"] = "A capital loss cannot be deducted from other income; it offsets capital " \
                                           "gains now or is carried forward (s102-10)."
        return res

    eligible, why = _discount_eligible(inp, acq)
    pct = 0.0
    if eligible:
        pct = discount_rate_for(figures, inp.entity_type)
        if inp.entity_type == "individual":
            has_foreign = inp.residency != "resident" or (inp.foreign_or_temporary_days_after_8_may_2012 or 0) > 0
            if has_foreign and event > FOREIGN_DISCOUNT_DATE:
                cb_8may = sum(it.amount for it in items
                              if (_item_date(it, inp) or acq) <= FOREIGN_DISCOUNT_DATE and it.element != 3)
                pct = _foreign_discount_pct(inp, gain, cb_8may, assumptions)
                res["foreign_resident_apportionment"] = "s115-115 applied"
        elif inp.entity_type == "trust" and inp.residency != "resident":
            raise Refusal("AU-CGT-003", "foreign trust discount (s115-120)")
    else:
        assumptions.append(f"No discount: {why}.")

    losses = inp.capital_losses_available
    disc_net = max(0.0, gain - losses) * (1 - pct)
    method, idx_detail = "discount" if pct else "no_discount", None
    net, used_gain = disc_net, gain
    if acq <= FROZEN_INDEXATION_LAST and held_12_months(acq, event):
        icb, idx_detail = _frozen_indexed_cost_base(figures, inp, items, warnings)
        icb -= inp.capital_works_deductions
        igain = max(0.0, proceeds - icb)
        idx_net = max(0.0, igain - losses)
        choose_index = (inp.method_choice == "indexation" or inp.entity_type == "company"
                        or (inp.method_choice == "best" and idx_net < disc_net))
        res["indexation_alternative"] = {"indexed_cost_base": _r(icb), "indexed_gain": _r(igain),
                                         "net_after_losses": _r(idx_net), "items": idx_detail}
        res["discount_alternative"] = {"gain": _r(gain), "discount_percentage": pct, "net_after_losses": _r(disc_net)}
        if choose_index:
            method, net, used_gain, pct = "frozen_indexation", idx_net, igain, 0.0
            res["cost_base_indexed"] = _r(icb)
    applied = min(losses, used_gain)
    res.update(method=method, discount_percentage=round(pct, 6), capital_losses_applied=_r(applied),
               capital_losses_remaining=_r(losses - applied),
               discount_amount=_r(max(0.0, used_gain - applied) * pct),
               net_capital_gain=_r(net),
               components=[{"category": "pre_2027", "gain": _r(used_gain), "discount_eligible": pct > 0,
                            "discount_percentage": round(pct, 6), "collectable": inp.asset_type == "collectable"}])
    return res


def _post_reform(figures: Figures, inp: CapitalGainInput, items: list[CostItem], assumptions: list[str],
                 warnings: list[str]) -> dict:
    """Events on or after 1 July 2027 (Act No. 49 of 2026 Sch 1)."""
    acq, event = inp.acquisition_date, inp.event_date
    if inp.entity_type in ("trust", "complying_super_fund"):
        raise Refusal("AU-CGT-003", "trust or super fund gain from a CGT event on or after 1 July 2027")
    if inp.entity_type == "company":
        return _pre_reform(figures, inp, items, assumptions, warnings)  # companies: no change
    small = _exempt_small_assets(figures, inp, items)
    if small:
        cb, rcb = _cost_bases(items, inp.capital_works_deductions)
        r = _zero_result(small)
        r.update(cost_base=_r(cb), reduced_cost_base=_r(rcb))
        return r
    residential = inp.residential_dwelling if inp.residential_dwelling is not None else inp.asset_type == "real_property"
    cat = "residential" if residential else "non_residential"
    foreign_history = inp.residency != "resident" or (inp.foreign_or_temporary_days_after_8_may_2012 or 0) > 0
    if foreign_history and inp.residency == "resident":
        raise Refusal("AU-CGT-007", "foreign or temporary residency after 8 May 2012 but resident at the event")
    resident_now = not foreign_history
    new_dwelling = inp.new_residential_dwelling and not inp.choose_indexation_for_new_dwelling and resident_now
    proceeds = inp.capital_proceeds
    if acq < PRE_CGT_CUTOFF and foreign_history:
        raise Refusal("AU-CGT-007", "pre-CGT asset of a foreign or temporary resident sold on or after 1 July 2027")

    # ---- no deemed sale: foreign residents (s112-155(1)(d)) and new dwellings (s112-155(1)(e))
    if acq >= PRE_CGT_CUTOFF and (foreign_history or new_dwelling or (acq >= REFORM_DATE and not _indexable(inp, acq))):
        cb, rcb = _cost_bases(items, inp.capital_works_deductions)
        gain = max(0.0, proceeds - cb)
        loss = max(0.0, rcb - proceeds)
        pct = 0.0
        eligible, why = _discount_eligible(inp, acq)
        if gain and eligible and new_dwelling:
            pct = figures.get("cgt.discount_new_residential_dwelling")  # s115-100(a), s115-102
            method = "new_dwelling_discount"
        elif gain and eligible and foreign_history:
            cb_8may = sum(it.amount for it in items if (_item_date(it, inp) or acq) <= FOREIGN_DISCOUNT_DATE)
            pct = _foreign_discount_pct(inp, gain, cb_8may, assumptions)  # s115-100(c)
            method = "foreign_resident_apportioned_discount"
            warnings.append("For events from 1 July 2027 the apportioned foreign resident discount follows the text of "
                            "s115-100(c), which Act 49 did not limit to earlier events; no ATO guidance yet.")
        else:
            method = "no_discount_no_indexation"
            if gain and not eligible:
                assumptions.append(f"No discount: {why}.")
        applied = min(inp.capital_losses_available, gain)
        net = (gain - applied) * (1 - pct)
        comp_cat = cat
        res = {"cost_base": _r(cb), "reduced_cost_base": _r(rcb), "gross_capital_gain": _r(gain),
               "capital_loss": _r(loss), "method": method, "discount_percentage": round(pct, 6),
               "discount_amount": _r((gain - applied) * pct), "capital_losses_applied": _r(applied),
               "capital_losses_remaining": _r(inp.capital_losses_available - applied), "net_capital_gain": _r(net),
               "components": [{"category": comp_cat, "gain": _r(gain), "capital_loss": _r(loss),
                               "discount_eligible": pct > 0, "discount_percentage": round(pct, 6),
                               "minimum_tax_applies": resident_now and not (new_dwelling and pct > 0)}]}
        mt = resident_now and not (new_dwelling and pct > 0)
        _min_tax(figures, inp, res, (gain - applied) * (1 - pct) if mt else 0.0, warnings)
        return res

    # ---- resident individual: acquired on or after 1 July 2027 -> indexation only
    if acq >= REFORM_DATE:
        return _indexed_only(figures, inp, items, cat, assumptions, warnings)

    # ---- resident individual holding the asset on 30 June 2027: deemed sale and reacquisition
    mv = inp.market_value_30_june_2027
    if mv is None:
        raise Refusal("AU-CGT-006", "market value just before 1 July 2027 not provided")
    pre_cgt = acq < PRE_CGT_CUTOFF
    pre_items, post_items = [], []
    undated_split = False
    for it in items:
        d = _item_date(it, inp)
        if d is None:
            undated_split = True
            pre_items.append(it)
        elif d < REFORM_DATE and not it.disposal_cost:
            pre_items.append(it)
        else:
            post_items.append(it)
    if undated_split:
        assumptions.append("Undated cost base amounts (elements 3 to 5) treated as incurred before 1 July 2027.")
    components: list[dict] = []
    deferred_gain = deferred_loss = 0.0
    cb_pre = rcb_pre = 0.0
    if pre_cgt:
        assumptions.append("Pre-CGT asset: deemed sold and reacquired at market value just before 1 July 2027; the "
                           "gain or loss on that deemed sale is disregarded (s112-175).")
    else:
        cb_pre, rcb_pre = _cost_bases(pre_items, inp.capital_works_deductions)
        deferred_gain = max(0.0, mv - cb_pre)  # s112-155(2), s112-160(3)
        deferred_loss = max(0.0, rcb_pre - mv)
        eligible, why = _discount_eligible(inp, acq)  # 12 months tested to the realisation event (s112-160(3)(c))
        dpct = figures.get("cgt.discount_individual_trust_deferred_gain") if (eligible and deferred_gain) else 0.0  # s112-160(3)
        if deferred_gain and not eligible:
            assumptions.append(f"Deferred gain not discounted: {why}.")
        components.append({"category": f"deferred_{cat}", "gain": _r(deferred_gain), "capital_loss": _r(deferred_loss),
                           "discount_eligible": dpct > 0, "discount_percentage": dpct,
                           "note": "deemed sale just before 1 July 2027 (s112-155, s112-160)"})
    # post-1 July 2027 part: reacquired on 1 July 2027 for mv
    first = CostItem(element=1, amount=mv, date_incurred=REFORM_DATE)  # counts as September 2027 quarter expenditure
    post_all = [first] + post_items
    cb_post_plain, rcb_post = _cost_bases(post_all, 0.0)
    indexable = held_12_months(acq, event)  # s114-10(9): disregard the deemed reacquisition
    try:
        icb, idx_detail, indexed = _index_post(figures, inp, post_all, indexable, warnings)
    except FigureError as e:
        # Only the post-1 July 2027 part needs the unpublished index numbers. The deferred component (deemed sale gain or
        # loss, its discount) does not, so it is returned and the post-July part is refused at field level.
        return _deferred_only(inp, components, deferred_gain, deferred_loss, cb_pre, rcb_pre, mv, e, warnings)
    post_gain = max(0.0, proceeds - icb)
    post_loss = max(0.0, rcb_post - proceeds)
    components.append({"category": cat, "gain": _r(post_gain), "capital_loss": _r(post_loss),
                       "discount_eligible": False, "discount_percentage": 0.0, "indexed": indexed,
                       "minimum_tax_applies": True, "note": "period from 1 July 2027 (s110-36(1A))"})
    net = _net_components(components, inp.capital_losses_available)
    mtcg = net["remaining_by_category"].get(cat, 0.0)
    res = {"cost_base_to_30_june_2027": _r(cb_pre), "reduced_cost_base_to_30_june_2027": _r(rcb_pre),
           "market_value_30_june_2027": _r(mv), "cost_base_from_1_july_2027_indexed": _r(icb),
           "cost_base_from_1_july_2027_unindexed": _r(cb_post_plain), "indexation_items": idx_detail,
           "gross_capital_gain": _r(deferred_gain + post_gain),
           "capital_loss": _r(deferred_loss + post_loss), "method": "deemed_sale_split_at_1_july_2027",
           "discount_amount": net["discount_amount"], "capital_losses_applied": net["losses_applied"],
           "capital_losses_remaining": net["losses_remaining"], "net_capital_gain": net["net_capital_gain"],
           "net_capital_loss_carried_forward": net["net_capital_loss"], "components": components}
    _min_tax(figures, inp, res, mtcg, warnings)
    return res


def _deferred_only(inp: CapitalGainInput, components: list[dict], deferred_gain: float, deferred_loss: float,
                   cb_pre: float, rcb_pre: float, mv: float, err: FigureError, warnings: list[str]) -> dict:
    """Partial result for a deemed-sale disposal whose post-1 July 2027 part cannot be worked out because a figure it needs
    (the index numbers, cgt.indexation_cpi_from_2027) is unpublished: the deferred component is returned with its discount;
    the post-July gain, the net capital gain and the minimum tax test are withheld, with a field-level refusal. Nothing is
    estimated, and no bound is shown for the withheld part."""
    net = _net_components(components, inp.capital_losses_available)
    comp = components[0] if components else None
    deferred = {
        "category": comp["category"] if comp else None,
        "notional_gain": _r(deferred_gain), "notional_loss": _r(deferred_loss),
        "cost_base_to_30_june_2027": _r(cb_pre), "market_value_30_june_2027": _r(mv),
        "discount_eligible": bool(comp and comp["discount_eligible"]),
        "discount_percentage": comp["discount_percentage"] if comp else 0.0,
        "losses_applied": net["losses_applied"], "losses_remaining_for_post_1_july_2027_part": net["losses_remaining"],
        "discount_amount": net["discount_amount"], "gain_after_discount": net["net_capital_gain"],
        "note": ("Pre-CGT asset: reacquired at market value just before 1 July 2027 and the deemed sale gain or loss is "
                 "disregarded (s112-175)." if inp.acquisition_date < PRE_CGT_CUTOFF else
                 "Deemed sale just before 1 July 2027 (s112-155); the gain or loss is deferred to this event and discounted "
                 "only if the asset was held 12 months to the event, ignoring the deemed reacquisition (s112-160(3))."),
    }
    refusal = figure_refusal(err)
    warnings.append(
        f"The post-1 July 2027 part is not computed: {refusal['code']} ({err}). The deferred component above stands on its "
        "own; no post-July gain, upper bound, net capital gain or minimum tax figure is shown and none is estimated. Losses "
        "shown as remaining are not yet applied to the post-July part.")
    return {
        "partial": True, "method": "deemed_sale_split_at_1_july_2027",
        "market_value_30_june_2027": _r(mv), "cost_base_to_30_june_2027": _r(cb_pre),
        "reduced_cost_base_to_30_june_2027": _r(rcb_pre),
        "deferred_component": deferred,
        "post_1_july_2027_part": {"status": "refused", "gain": None, "capital_loss": None, "refusal_code": refusal["code"]},
        "gross_capital_gain": None, "capital_loss": None, "discount_amount": None, "net_capital_gain": None,
        "components": [dict(c, partial_result=True) for c in components],
        "field_refusals": [{"field": "post_1_july_2027_part", **refusal}],
    }


def _indexable(inp: CapitalGainInput, acq: date) -> bool:
    return held_12_months(acq, inp.event_date)


def _index_number(table: list[dict], d: date, what: str) -> float:
    """Index number for the quarter containing d, from cgt.indexation_cpi_from_2027 (rows shaped like the frozen table:
    from, to, rate = index number). A quarter the table does not hold is unpublished: refuse AU-GEN-003."""
    value = _cpi_lookup(table, d)
    if value is None:
        raise FigureError(f"cgt.indexation_cpi_from_2027 has no index number for the quarter containing {d.isoformat()} "
                          f"({what}); nothing is estimated or carried forward", UNPUBLISHED)
    return value


def _index_post(figures: Figures, inp: CapitalGainInput, items: list[CostItem], indexable: bool,
                warnings: list[str]) -> tuple[float, list[dict], bool]:
    """s110-36(1A), s960-275(1B),(5): factor = index number for the event quarter over the index number for the
    quarter the expenditure was incurred, 3 decimal places. Third element never indexed; disposal costs are not
    indexed. The index numbers come only from the rates file (cgt.indexation_cpi_from_2027): while that figure has no
    published value this refuses AU-GEN-003, so no indexed gain is ever shown from an index number the file does not
    hold. Nothing is read (and nothing refuses) when no item is indexable, for example under 12 months (s114-10)."""
    total, detail, any_indexed = 0.0, [], False
    dated = {id(it): _item_date(it, inp) for it in items}
    to_index = [it for it in items if indexable and it.element != 3 and not it.disposal_cost and dated[id(it)] is not None]
    table = figures.get("cgt.indexation_cpi_from_2027") if to_index else None
    ev = _index_number(table, inp.event_date, "CGT event") if to_index else None
    for it in items:
        factor = 1.0
        d = dated[id(it)]
        if indexable and it.element != 3 and not it.disposal_cost:
            if d is None:
                warnings.append(f"Element {it.element} amount {_r(it.amount)} has no date, so it was not indexed.")
            else:
                factor = round_factor(ev / _index_number(table, d, f"element {it.element} incurred {d.isoformat()}"))
                any_indexed = True
        total += it.amount * factor
        detail.append({"element": it.element, "amount": _r(it.amount), "indexation_factor": factor,
                       "indexed_amount": _r(it.amount * factor)})
    if not indexable:
        warnings.append("No indexation: asset not held for at least 12 months (s114-10).")
    return total, detail, any_indexed


def _indexed_only(figures: Figures, inp: CapitalGainInput, items: list[CostItem], cat: str,
                  assumptions: list[str], warnings: list[str]) -> dict:
    cb, rcb = _cost_bases(items, inp.capital_works_deductions)
    icb, detail, indexed = _index_post(figures, inp, items, held_12_months(inp.acquisition_date, inp.event_date), warnings)
    icb -= inp.capital_works_deductions
    gain = max(0.0, inp.capital_proceeds - icb)
    loss = max(0.0, rcb - inp.capital_proceeds)
    comp = [{"category": cat, "gain": _r(gain), "capital_loss": _r(loss), "discount_eligible": False,
             "discount_percentage": 0.0, "indexed": indexed, "minimum_tax_applies": True}]
    net = _net_components(comp, inp.capital_losses_available)
    res = {"cost_base": _r(cb), "cost_base_indexed": _r(icb), "reduced_cost_base": _r(rcb),
           "indexation_items": detail, "gross_capital_gain": _r(gain), "capital_loss": _r(loss),
           "method": "indexation_from_1_july_2027", "discount_percentage": 0.0, "discount_amount": 0.0,
           "capital_losses_applied": net["losses_applied"], "capital_losses_remaining": net["losses_remaining"],
           "net_capital_gain": net["net_capital_gain"], "components": comp}
    _min_tax(figures, inp, res, net["remaining_by_category"].get(cat, 0.0), warnings)
    return res


def _min_tax(figures: Figures, inp: CapitalGainInput, res: dict, mtcg: float, warnings: list[str]) -> None:
    res["minimum_tax_capital_gain"] = _r(mtcg)
    if mtcg <= 0 or inp.entity_type != "individual":
        return
    if inp.residency != "resident":
        res["minimum_tax_note"] = "Div 119 applies only to individuals who are Australian residents at some time in " \
                                  "the income year."
        return
    if inp.receives_minimum_tax_exempt_payment:
        res["minimum_tax_note"] = "No minimum tax: a payment listed in s119-15 was received in the income year."
        return
    res["minimum_tax_rate"] = figures.get("cgt.minimum_tax_rate_from_2027_28")
    if inp.taxable_income_including_gain is None:
        warnings.append("Minimum tax (Div 119) not tested: give taxable_income_including_gain for the year. Tax "
                        "deductible gifts reduce the minimum tax capital gain (s119-5(1)(b)) and are not modelled.")
        return
    res["minimum_tax"] = minimum_tax_gap(figures, inp.taxable_income_including_gain, mtcg)


CATEGORY_ORDER = ["deferred_non_residential", "deferred_residential", "pre_2027", "non_residential", "residential"]


def _net_components(components: list[dict], losses_available: float, quarantined: float = 0.0) -> dict:
    """s102-5(1) steps 1-5 for one taxpayer: losses (the component losses plus losses_available) reduce gains in
    category order, non-discount gains first within a category (the taxpayer may choose the order); the
    quarantined residential amount then reduces deferred residential and residential gains; then the discount."""
    gains = [dict(c, remaining=c.get("gain", 0.0)) for c in components if c.get("gain", 0.0) > 0]
    pool = losses_available + sum(c.get("capital_loss", 0.0) for c in components)
    start_pool = pool
    gains.sort(key=lambda g: (CATEGORY_ORDER.index(g["category"]), g.get("discount_percentage", 0.0)))
    for g in gains:
        use = min(pool, g["remaining"])
        g["remaining"] -= use
        pool -= use
    q = quarantined
    for catname in ("deferred_residential", "residential"):
        for g in gains:
            if g["category"] == catname:
                use = min(q, g["remaining"])
                g["remaining"] -= use
                q -= use
    disc = sum(g["remaining"] * g.get("discount_percentage", 0.0) for g in gains)
    by_cat: dict[str, float] = {}
    for g in gains:
        g["after_discount"] = g["remaining"] * (1 - g.get("discount_percentage", 0.0))
        by_cat[g["category"]] = by_cat.get(g["category"], 0.0) + g["after_discount"]
    net_loss = pool
    return {"losses_applied": _r(start_pool - pool), "losses_remaining": _r(pool), "discount_amount": _r(disc),
            "net_capital_gain": _r(sum(g["after_discount"] for g in gains)), "net_capital_loss": _r(net_loss),
            "remaining_by_category": {k: _r(v) for k, v in by_cat.items()}, "quarantined_unused": _r(q),
            "gains": gains}


# ---------------------------------------------------------------- net_capital_gain

class GainItem(BaseModel):
    amount: float = Field(gt=0, description="Capital gain before losses and discount (after any indexation).")
    discount_eligible: bool = Field(False, description="Discount capital gain (12 months, eligible entity and event).")
    discount_percentage: float | None = Field(None, ge=0, le=0.6, description="Override, e.g. an apportioned foreign "
                                              "resident percentage from capital_gain. Default: entity rate.")
    category: Literal["pre_2027", "deferred_non_residential", "deferred_residential", "non_residential",
                      "residential"] = Field("pre_2027", description="pre_2027 for CGT events before 1 July 2027; "
                                             "later events use the s102-6 categories from capital_gain.")
    collectable: bool = False
    new_residential_dwelling: bool = Field(False, description="Post-1 July 2027 gain to which s115-102 applies.")
    label: str = ""


class LossItem(BaseModel):
    amount: float = Field(gt=0)
    collectable: bool = False
    personal_use_asset: bool = False
    label: str = ""


class NetCapitalGainInput(BaseModel):
    """All CGT events of one taxpayer for one income year."""

    entity_type: EntityType = "individual"
    gains: list[GainItem] = Field(default_factory=list)
    losses: list[LossItem] = Field(default_factory=list, description="Current-year capital losses.")
    prior_year_net_capital_losses: float = Field(0, ge=0, description="Unapplied net capital losses from earlier years "
                                                 "(other than collectables).")
    prior_year_collectable_losses: float = Field(0, ge=0)
    quarantined_residential_amount: float = Field(0, ge=0, description="From 2027-28: quarantined residential "
                                                  "property amount (s26-155(1)(b)).")


@calculator("net_capital_gain", NetCapitalGainInput)
def net_capital_gain(figures: Figures, inp: NetCapitalGainInput) -> dict:
    """Net capital gain or net capital loss for one taxpayer and one income year (ITAA 1997 s102-5, s102-10),
    from a list of capital gains and capital losses: personal use asset losses disregarded; collectable losses
    only against collectable gains (current then carried forward); other current-year losses, then prior-year net
    capital losses, applied BEFORE the discount, to non-discount gains first (and, from 2027-28, in the s102-5
    category order: deferred non-residential, deferred residential, non-residential, residential); quarantined
    residential amounts; then the discount, at the rate in the rates file of the income year given (before 2027-28:
    individuals and trusts, one-third super funds, none companies; from 2027-28 individuals and trusts discount only
    deferred gains and new residential dwelling gains, and post-2027 gain categories are refused in earlier years).
    Returns the net capital gain and the losses carried forward. Use whenever a year has more than one gain or loss,
    or carried-forward losses."""
    assumptions: list[str] = []
    warnings: list[str] = []
    default = discount_rate_for(figures, inp.entity_type)
    post_year = figures.income_year >= REFORM_YEAR
    gains = []
    for g in inp.gains:
        post_cat = g.category != "pre_2027"
        if post_cat and not post_year:
            raise InputError(f"gain '{g.label}' has category {g.category}, which exists only for CGT events on or after "
                             f"1 July 2027 (income year {REFORM_YEAR} or later); the income year given is {figures.income_year}. "
                             f"Run this tool for the income year of those events.")
        if not post_cat and post_year and inp.entity_type != "company":
            raise InputError(f"gain '{g.label}' has category pre_2027 but the income year is {figures.income_year}: a CGT "
                             "event before 1 July 2027 falls in an earlier income year. Run that year separately.")
        pct = 0.0
        if g.discount_eligible:
            if inp.entity_type == "company":
                pct = 0.0
                warnings.append(f"Gain '{g.label}': companies get no discount.")
            elif g.discount_percentage is not None:
                pct = g.discount_percentage
            elif inp.entity_type == "complying_super_fund" or not post_cat:
                pct = default
            elif g.category in ("deferred_non_residential", "deferred_residential"):
                pct = figures.get("cgt.discount_individual_trust_deferred_gain")  # s112-160(3), s115-100(aa), (ab)
            elif g.new_residential_dwelling:
                pct = figures.get("cgt.discount_new_residential_dwelling")  # s115-100(a), s115-102
            else:
                pct = default  # s115-100 residual rate for events on or after 1 July 2027
            if post_cat and pct == 0.0 and inp.entity_type in ("individual", "trust") and g.discount_percentage is None \
                    and g.category in ("non_residential", "residential"):
                warnings.append(f"Gain '{g.label}': from 1 July 2027 individuals and trusts only discount deferred "
                                "gains and new residential dwelling gains (s115-100); discount removed.")
        gains.append({"label": g.label, "gain": g.amount, "category": g.category, "discount_percentage": pct,
                      "collectable": g.collectable})
    disregarded = sum(l.amount for l in inp.losses if l.personal_use_asset)
    if disregarded:
        assumptions.append("Personal use asset losses disregarded (s108-20(1)).")
    coll_losses = sum(l.amount for l in inp.losses if l.collectable and not l.personal_use_asset)
    other_losses = sum(l.amount for l in inp.losses if not l.collectable and not l.personal_use_asset)

    # collectables first (s108-10): current-year then prior-year collectable losses against collectable gains
    coll_pool_cur, coll_pool_prior = coll_losses, inp.prior_year_collectable_losses
    order = sorted(gains, key=lambda g: (CATEGORY_ORDER.index(g["category"]), g["discount_percentage"]))
    for g in order:
        g["remaining"] = g["gain"]
    for pool_name in ("cur", "prior"):
        for g in order:
            if not g["collectable"]:
                continue
            pool = coll_pool_cur if pool_name == "cur" else coll_pool_prior
            use = min(pool, g["remaining"])
            g["remaining"] -= use
            if pool_name == "cur":
                coll_pool_cur -= use
            else:
                coll_pool_prior -= use
    # step 1: current-year losses; step 2: prior-year net capital losses
    cur, prior = other_losses, inp.prior_year_net_capital_losses
    for g in order:
        use = min(cur, g["remaining"])
        g["remaining"] -= use
        cur -= use
    for g in order:
        use = min(prior, g["remaining"])
        g["remaining"] -= use
        prior -= use
    q = inp.quarantined_residential_amount
    for catname in ("deferred_residential", "residential"):
        for g in order:
            if g["category"] == catname:
                use = min(q, g["remaining"])
                g["remaining"] -= use
                q -= use
    disc = 0.0
    for g in order:
        g["discount"] = g["remaining"] * g["discount_percentage"]
        disc += g["discount"]
        g["net"] = g["remaining"] - g["discount"]
    net = sum(g["net"] for g in order)
    total_gains = sum(g["gain"] for g in order)
    # s102-10: net capital loss = losses exceeding gains for the year (current year), plus unused prior losses
    net_loss_current = max(0.0, other_losses + coll_losses - total_gains) if net == 0 else 0.0
    carried = cur + prior
    mtcg = sum(g["net"] for g in order if g["category"] in ("non_residential", "residential"))
    return {"net_capital_gain": _r(net), "total_capital_gains": _r(total_gains),
            "current_year_losses_applied": _r(other_losses - cur + coll_losses - coll_pool_cur),
            "prior_year_losses_applied": _r(inp.prior_year_net_capital_losses - prior
                                            + inp.prior_year_collectable_losses - coll_pool_prior),
            "discount_amount": _r(disc),
            "net_capital_loss_carried_forward": _r(carried),
            "collectable_losses_carried_forward": _r(coll_pool_cur + coll_pool_prior),
            "personal_use_losses_disregarded": _r(disregarded),
            "quarantined_amount_unused": _r(q),
            "net_capital_loss_this_year": _r(net_loss_current),
            "minimum_tax_capital_gain_before_gifts": _r(mtcg),
            "gains": [{k: (_r(v) if isinstance(v, float) else v) for k, v in g.items()} for g in order],
            "assumptions": assumptions + ["Losses are applied to gains with the lowest discount first, which gives "
                                          "the lowest net capital gain (the taxpayer chooses the order)."],
            "warnings": warnings}


# ---------------------------------------------------------------- main residence

class Period(BaseModel):
    start: date
    end: date
    floor_area_fraction: float = Field(1.0, gt=0, le=1, description="Income-use periods only: share of floor area.")


class MainResidenceInput(BaseModel):
    """One dwelling owned by an individual. Dates are settlement dates of purchase and sale for the ownership
    period (s118-130); event_date is the sale contract date."""

    capital_proceeds: float = Field(ge=0)
    cost_base: float = Field(ge=0, description="Full cost base including purchase costs, capital improvements and "
                             "selling costs.")
    ownership_start: date = Field(description="Settlement of purchase.")
    ownership_end: date = Field(description="Settlement of sale.")
    event_date: date | None = Field(None, description="Sale contract date (for the income year and the discount); "
                                    "defaults to ownership_end.")
    acquisition_contract_date: date | None = Field(None, description="Purchase contract date (12-month test); defaults "
                                                   "to ownership_start.")
    lived_in_periods: list[Period] = Field(description="Periods the dwelling was actually the main residence.")
    income_use_periods: list[Period] = Field(default_factory=list, description="Periods it was rented or used for "
                                             "business (whole or part, with floor_area_fraction).")
    choose_absence_rule: bool = Field(True, description="s118-145 choice to keep treating it as the main residence "
                                      "after moving out (no other main residence claimed for that time).")
    changing_residence_overlap: bool = Field(False, description="Bought a new home before selling this one: up to 6 "
                                             "months before settlement of sale treated as main residence (s118-140).")
    market_value_at_first_income_use: float | None = Field(None, ge=0)
    selling_costs_after_first_income_use: float = Field(0, ge=0, description="Costs incurred after first income use "
                                                        "(added to the market value cost base under s118-192).")
    residency_at_event: Residency = "resident"
    foreign_residency_years_at_event: float | None = Field(None, ge=0)
    life_events_test_met: bool = False
    capital_losses_available: float = Field(0, ge=0)
    special_circumstances: list[Literal["deceased_estate", "land_over_2_hectares", "construction_or_renovation",
                                        "destroyed_dwelling", "adjacent_land_only", "spouse_different_main_residence",
                                        "income_use_before_moving_out_with_absence"]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check(self):
        if self.ownership_end < self.ownership_start:
            raise ValueError("ownership_end before ownership_start")
        return self


def _daymap(start: date, end: date, periods: list[Period]) -> dict[int, float]:
    out: dict[int, float] = {}
    for p in periods:
        a, b = max(p.start, start), min(p.end, end)
        d = a
        while d <= b:
            out[d.toordinal()] = max(out.get(d.toordinal(), 0.0), p.floor_area_fraction)
            d += timedelta(days=1)
    return out


def _day_weights(inp: MainResidenceInput) -> tuple[dict[int, float], list[str]]:
    """Taxable weight (0 = main residence, 1 = not, fraction = part income use) for each day of ownership."""
    start, end = inp.ownership_start, inp.ownership_end
    notes: list[str] = []
    lived = _daymap(start, end, [Period(start=p.start, end=p.end) for p in inp.lived_in_periods])
    income = _daymap(start, end, inp.income_use_periods)
    overlap_from = None
    if inp.changing_residence_overlap:
        # s118-140: both homes are main residences for up to 6 months ending when ownership ends
        last12 = add_months(end, -12).toordinal()
        recent = sorted(d for d in lived if d > last12)
        longest, run, prev = 0, 0, None
        for d in recent:
            run = run + 1 if prev is not None and d == prev + 1 else 1
            longest, prev = max(longest, run), d
        income_not_mr = any(d > last12 and d not in lived for d in income)
        if longest >= days_incl(add_months(end, -3), end) - 1 and not income_not_mr:
            overlap_from = (add_months(end, -6) + timedelta(days=1)).toordinal()
            notes.append("s118-140: up to 6 months before the end of ownership treated as main residence.")
        else:
            notes.append("s118-140 not applied: needs 3 continuous months as main residence in the last 12 months "
                         "and no income use in that period while not the main residence.")
    weights: dict[int, float] = {}
    seen_lived = False
    abs_income_days = 0
    abs_cap = 0
    for o in range(start.toordinal(), end.toordinal() + 1):
        if o in lived:
            weights[o] = income.get(o, 0.0)  # part of the home used to produce income (s118-190)
            seen_lived, abs_income_days, abs_cap = True, 0, 0  # each new absence gets a fresh 6 years
        elif overlap_from is not None and o >= overlap_from:
            weights[o] = 0.0
        elif inp.choose_absence_rule and seen_lived:
            if o in income:  # s118-145(2): 6 years of income use per absence
                if abs_cap == 0:
                    first = date.fromordinal(o)
                    abs_cap = days_incl(first, add_months(first, 72))
                abs_income_days += 1
                weights[o] = 0.0 if abs_income_days <= abs_cap else 1.0
            else:
                weights[o] = 0.0  # s118-145(3): unlimited if not income producing
        else:
            weights[o] = 1.0
    return weights, notes


@calculator("main_residence_exemption", MainResidenceInput)
def main_residence_exemption(figures: Figures, inp: MainResidenceInput) -> dict:
    """Main residence exemption for an individual's dwelling (ITAA 1997 Subdiv 118-B): full exemption, or the
    days-based partial exemption (s118-185: gain x non-main-residence days / ownership days), income use of part
    of the home by floor area (s118-190), the 6-year absence rule for rented former homes (s118-145; unlimited if
    not income producing; a fresh 6 years each time you move back in), the 6-month overlap when changing homes
    (s118-140), the 'home first used to produce income' market value rule (s118-192), and the foreign resident
    exclusion (s118-110(3), life events test). Then applies losses and the discount to the taxable part. Days are
    counted inclusively from settlement to settlement. Use for any question about selling a home, a former home
    that was rented out, Airbnb in part of a home, or the 6-year rule. Events on or after 1 July 2027 with a
    partial exemption are escalated."""
    for s in inp.special_circumstances:
        raise Refusal("AU-CGT-008", f"special circumstance: {s}")
    event = inp.event_date or inp.ownership_end
    acq_contract = inp.acquisition_contract_date or inp.ownership_start
    assumptions: list[str] = ["Ownership period counted from settlement of purchase to settlement of sale, inclusive."]
    warnings: list[str] = []
    figures = event_figures(figures, event, warnings)  # date-effective: the income year of the sale contract
    out: dict = {"event_income_year": income_year_of(event), "rates_year_used": figures.income_year}
    gain_full = max(0.0, inp.capital_proceeds - inp.cost_base)
    if inp.residency_at_event != "resident":
        yrs = inp.foreign_residency_years_at_event
        if not (inp.life_events_test_met and yrs is not None and yrs <= 6):
            out.update(exemption="none", exempt_fraction=0.0, taxable_capital_gain=_r(gain_full),
                       reason="Foreign resident at the time of the CGT event without meeting the life events test "
                              "(s118-110(3), s118-185(3)): no main residence exemption.")
            return _finish(figures, inp, out, gain_full, acq_contract, event, assumptions, warnings)
        assumptions.append("Foreign resident for 6 years or less who meets the life events test (s118-110(5)).")
    if acq_contract < PRE_CGT_CUTOFF:
        out.update(exemption="pre_cgt", taxable_capital_gain=0.0, exempt_fraction=1.0,
                   reason="Acquired before 20 September 1985: no CGT (s104-10(5)).")
        return {**out, "net_capital_gain": 0.0, "assumptions": assumptions, "warnings": warnings}

    start, end = inp.ownership_start, inp.ownership_end
    weights, notes = _day_weights(inp)
    assumptions += notes
    gain, cost_base = gain_full, inp.cost_base
    rule_192 = False
    count_from = start
    if any(weights.values()) and inp.income_use_periods:
        first_income = max(start, min(p.start for p in inp.income_use_periods))
        before = [weights[o] for o in range(start.toordinal(), first_income.toordinal())]
        if first_income > FIRST_INCOME_USE_CUTOFF and before and not any(before):
            if inp.market_value_at_first_income_use is None:
                raise Refusal("AU-CGT-006", "market value when the home was first used to produce income is needed "
                                            "(s118-192)")
            rule_192 = True
            cost_base = inp.market_value_at_first_income_use + inp.selling_costs_after_first_income_use
            gain = max(0.0, inp.capital_proceeds - cost_base)
            count_from = first_income
            acq_contract = first_income
            assumptions.append("s118-192: taken to have acquired the dwelling when first used to produce income, for "
                               "its market value then; days counted from that date.")
    days = [weights[o] for o in range(count_from.toordinal(), end.toordinal() + 1)]
    taxable_days, total_days = sum(days), len(days)
    if event >= REFORM_DATE and taxable_days > 0:
        raise Refusal("AU-CGT-007", "partial main residence exemption for a CGT event on or after 1 July 2027")
    frac_taxable = taxable_days / total_days if total_days else 0.0
    taxable_gain = gain * frac_taxable
    out.update(exemption="full" if taxable_days == 0 else "partial", home_first_used_to_produce_income_rule=rule_192,
               capital_gain_before_exemption=_r(gain), cost_base_used=_r(cost_base),
               ownership_days=total_days, non_main_residence_days=round(taxable_days, 4),
               exempt_fraction=round(1 - frac_taxable, 6), taxable_capital_gain=_r(taxable_gain))
    if gain_full == 0 and inp.capital_proceeds < inp.cost_base:
        warnings.append("A capital loss arises; the same exemption fraction applies to the loss (s118-185).")
    return _finish(figures, inp, out, taxable_gain, acq_contract, event, assumptions, warnings)


def _finish(figures: Figures, inp: MainResidenceInput, out: dict, taxable_gain: float, acquired: date, event: date,
            assumptions: list[str], warnings: list[str]) -> dict:
    pct = 0.0
    if taxable_gain > 0:
        if held_12_months(acquired, event):
            pct = figures.get("cgt.discount_individual_trust")
            if event >= REFORM_DATE:
                pct = 0.0
                warnings.append("Event from 1 July 2027: discount and indexation follow capital_gain rules.")
            if inp.residency_at_event != "resident":
                pct = 0.0
                warnings.append("Foreign resident: discount apportioned under s115-115; rerun capital_gain for the "
                                "percentage (shown here without discount).")
        else:
            assumptions.append("No discount: held less than 12 months from the (deemed) acquisition.")
    applied = min(inp.capital_losses_available, taxable_gain)
    net = (taxable_gain - applied) * (1 - pct)
    out.update(discount_percentage=pct, capital_losses_applied=_r(applied), net_capital_gain=_r(net))
    return {**out, "assumptions": assumptions, "warnings": warnings}


# ---------------------------------------------------------------- small business screen

class SmallBusinessScreenInput(BaseModel):
    event_date: date
    aggregated_turnover: float | None = Field(None, ge=0, description="Aggregated turnover for the income year "
                                              "(including affiliates and connected entities).")
    net_asset_value: float | None = Field(None, ge=0, description="Net value of CGT assets of you, connected entities "
                                          "and affiliates just before the event (excluding personal use assets, "
                                          "main residence and super).")
    carries_on_business: bool = True
    asset_acquired: date
    active_asset_years: float = Field(ge=0, description="Years the asset was an active asset (used in a business; "
                                      "not mainly to derive rent).")
    asset_is_share_or_trust_interest: bool = False
    asset_mainly_used_to_derive_rent: bool = False


@calculator("small_business_cgt_screen", SmallBusinessScreenInput)
def small_business_cgt_screen(figures: Figures, inp: SmallBusinessScreenInput) -> dict:
    """Eligibility SCREEN ONLY for the small business CGT concessions (ITAA 1997 Div 152): basic conditions -
    CGT small business entity (aggregated turnover under the $2m threshold) or maximum net asset value test (not
    more than $6m), and the active asset test (active for at least half the ownership period, or 7.5 years if owned
    more than 15 years). From the income year that includes 1 July 2027, the 50% active asset reduction alone is
    available to small business entities with turnover under the $10m threshold (s152-205(2)). Always returns an
    escalation (AU-CGT-001): applying the concessions needs a registered tax agent."""
    warnings: list[str] = []
    figures = event_figures(figures, inp.event_date, warnings)  # date-effective: the income year of the event
    turnover_2m = figures.get("cgt.small_business_aggregated_turnover")
    mnav = figures.get("cgt.small_business_max_net_asset_value")
    iy = income_year_of(inp.event_date)
    from_2027_28 = inp.event_date >= REFORM_DATE
    sbe = inp.carries_on_business and inp.aggregated_turnover is not None and inp.aggregated_turnover < turnover_2m
    nav = inp.net_asset_value is not None and inp.net_asset_value <= mnav
    owned_years = (inp.event_date - inp.asset_acquired).days / 365.25
    if owned_years > 15:
        active_ok = inp.active_asset_years >= 7.5
    else:
        active_ok = inp.active_asset_years >= owned_years / 2
    if inp.asset_mainly_used_to_derive_rent:
        active_ok = False
    basic = (sbe or nav) and active_ok
    gate10 = None
    reduction_ok = basic
    if from_2027_28:
        gate10 = figures.get("cgt.active_asset_reduction_turnover_gate_from_2027_28")
        sbe10 = inp.carries_on_business and inp.aggregated_turnover is not None and inp.aggregated_turnover < gate10
        reduction_ok = (sbe10 or nav) and active_ok
    notes = ["Screen only: connected entities, affiliates, CGT concession stakeholders and the extra conditions for "
             "each concession are not tested."]
    if inp.asset_mainly_used_to_derive_rent:
        notes.append("An asset whose main use is to derive rent is not an active asset (s152-40(4)(e)).")
    if inp.asset_is_share_or_trust_interest:
        notes.append("Shares and trust interests need the additional basic conditions in s152-10(2).")
    return {"event_income_year": iy, "rates_year_used": figures.income_year, "cgt_small_business_entity": sbe, "max_net_asset_value_test": nav,
            "active_asset_test": active_ok, "owned_years": round(owned_years, 2), "basic_conditions_screen": basic,
            "active_asset_50_percent_reduction_screen": reduction_ok,
            "reduction_turnover_gate_applied": gate10 if from_2027_28 else turnover_2m,
            "concessions_possibly_available": {
                "15_year_exemption": basic and owned_years >= 15,
                "active_asset_50_percent_reduction": reduction_ok,
                "retirement_exemption": basic, "rollover": basic},
            "escalations": [_escalation("AU-CGT-001", "detailed application of Div 152")],
            "assumptions": notes, "warnings": warnings}
