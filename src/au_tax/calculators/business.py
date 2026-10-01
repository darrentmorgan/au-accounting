"""Sole trader business: small business income tax offset, simplified depreciation (instant asset
write-off and the general small business pool), car cents-per-km v logbook, home office fixed rate,
non-commercial loss tests and personal services income (PSI) tests.

Law: ITAA 1997 Subdiv 328-F (SBITO), Subdiv 328-D (simplified depreciation, as amended by the
Treasury Laws Amendment (Tax Reform No. 2) Act 2026 Sch 2), Div 28 (car expenses), Div 35
(non-commercial losses), Pt 2-42 Divs 84-87 (PSI); PCG 2023/1 (home office). Every rate and
threshold comes from data/rates/<year>.yaml and its overlays via Figures.
"""

from __future__ import annotations

import math
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from au_tax.calculators.individual import _apply
from au_tax.figures import Figures
from au_tax.registry import Refusal, calculator


def _r(x: float) -> float:
    return round(x + 0.0, 2)


def _year_bounds(figures: Figures) -> tuple[date, date]:
    meta = figures.data.get("meta", {})
    return meta["start"], meta["end"]


# ================================================================ small business income tax offset

class SbitoInput(BaseModel):
    """Inputs for the small business income tax offset (SBITO) for one individual and one income year."""

    aggregated_turnover: float = Field(ge=0, description="Aggregated annual turnover of the sole trader business (own turnover plus connected entities and affiliates).")
    net_small_business_income: float = Field(
        ge=0, description="Sole trader net small business income: assessable business income less deductions attributable to it. "
        "Exclude net capital gains, PSI (unless a personal services business), salary, unrelated interest and dividends, "
        "and add back any deferred non-commercial loss. A loss is entered as 0.")
    taxable_income: float = Field(ge=0, description="Taxable income for the year.")
    partnership_or_trust_net_small_business_income: float = Field(
        0, ge=0, description="Share of net small business income from a partnership or trust that is itself a small business entity "
        "(turnover below the offset threshold). One cap applies across all sources.")
    residency: Literal["resident", "foreign"] = Field("resident", description="Selects the rate scale for the basic income tax liability when it is not supplied.")
    basic_income_tax_liability: float | None = Field(
        None, ge=0, description="Income tax on taxable income before offsets and excluding Medicare levy. If omitted it is computed from the "
        "resident (or foreign resident) rate scale, which ignores special rules such as income averaging or minors.")


@calculator("small_business_income_tax_offset", SbitoInput)
def small_business_income_tax_offset(figures: Figures, inp: SbitoInput) -> dict:
    """Small business income tax offset (ITAA 1997 Subdiv 328-F) for a sole trader (plus any small business
    partnership or trust share): offset = rate x basic income tax liability x (total net small business income /
    taxable income), capped per individual. Needs aggregated turnover (below the offset threshold, which is lower than
    the small business entity threshold), net small business income, taxable income. Computes basic income tax liability
    from the rate scale if not supplied. Non-refundable. Use for "how much small business tax offset do I get".
    Returns eligible=false with a reason (not a refusal) when turnover is at or above the threshold."""
    threshold = figures.get("business.sbito_turnover_threshold")
    warnings: list[str] = []
    assumptions: list[str] = []
    if inp.aggregated_turnover >= threshold:
        return {"eligible": False, "reason": "aggregated turnover is not below the small business income tax offset threshold",
                "offset": 0.0, "assumptions": assumptions, "warnings": warnings}
    rate, cap = figures.get("business.sbito_rate"), figures.get("business.sbito_cap")
    ti = inp.taxable_income
    total_nsbi = inp.net_small_business_income + inp.partnership_or_trust_net_small_business_income
    bitl = inp.basic_income_tax_liability
    if bitl is None:
        key = "individual.resident_rates" if inp.residency == "resident" else "individual.foreign_resident_rates"
        bitl = _apply(figures.get(key), ti)
        assumptions.append("Basic income tax liability computed as tax on taxable income at the "
                           f"{inp.residency} rate scale, before offsets and excluding Medicare levy.")
    share = min(total_nsbi, ti) / ti if ti > 0 else 0.0
    uncapped = rate * bitl * share
    offset = min(uncapped, cap)
    assumptions.append("Offset is non-refundable and cannot be carried forward; it can only reduce tax payable.")
    if inp.partnership_or_trust_net_small_business_income:
        warnings.append("Partnership or trust share counts only if that entity is itself a small business entity below the offset turnover threshold and carried on its own business.")
    return {"eligible": True, "net_small_business_income_total": _r(total_nsbi), "taxable_income": _r(ti),
            "business_share_of_taxable_income": round(share, 6), "basic_income_tax_liability": _r(bitl),
            "offset_before_cap": _r(uncapped), "cap_applied": uncapped > cap, "offset": _r(offset),
            "assumptions": assumptions, "warnings": warnings}


# ================================================================ simplified depreciation

class Asset(BaseModel):
    """A depreciating asset first used, or installed ready for use, in the income year."""

    name: str = Field(description="Description of the asset.")
    cost: float = Field(gt=0, description="Cost of the asset for tax purposes: GST-exclusive if you claim GST credits, otherwise GST-inclusive. Before any trade-in credit is deducted.")
    first_used_date: date = Field(description="Date first used, or first installed ready for use, for a taxable purpose. This, not the purchase date, sets the threshold.")
    business_use_percent: float = Field(100, ge=0, le=100, description="Estimated taxable purpose (business) use, 0 to 100.")
    asset_type: Literal["general", "passenger_car", "excluded"] = Field(
        "general", description="passenger_car = car subject to the car limit; excluded = asset excluded from simplified depreciation "
        "(for example leased out on a long-term hire, horticultural plant, primary production item, capital works).")


class Disposal(BaseModel):
    """An asset sold, lost or permanently taken out of use in the year."""

    name: str
    termination_value: float = Field(ge=0, description="Sale proceeds, trade-in or insurance payout.")
    business_use_percent: float = Field(100, ge=0, le=100)
    was_in_pool: bool = Field(True, description="True if the asset sat in the small business pool; false if it was previously written off in full (instant asset write-off).")


class CostAddition(BaseModel):
    """Improvement or other second-element cost added to an existing asset this year."""

    name: str
    cost: float = Field(gt=0)
    business_use_percent: float = Field(100, ge=0, le=100, description="Same proportion as applies to the asset.")
    asset_previously_written_off: bool = Field(False, description="The asset itself was written off in full in an earlier year.")
    first_improvement: bool = Field(True, description="First improvement claimed for that asset since it was written off.")


class SimplifiedDepreciationInput(BaseModel):
    """Small business simplified depreciation for one income year."""

    aggregated_turnover: float = Field(ge=0, description="Aggregated annual turnover; must be below the small business entity threshold.")
    previously_opted_out: bool = Field(False, description="The business previously chose to stop using simplified depreciation (lock-out rule may apply).")
    assets: list[Asset] = Field(default_factory=list)
    opening_pool_balance: float = Field(0, ge=0, description="Closing pool balance from the prior year.")
    opening_pool_adjustment: float = Field(0, description="Adjustment to the opening balance for a change of more than 10 percentage points in business use (increase positive).")
    disposals: list[Disposal] = Field(default_factory=list)
    cost_additions: list[CostAddition] = Field(default_factory=list)


@calculator("simplified_depreciation", SimplifiedDepreciationInput)
def simplified_depreciation(figures: Figures, inp: SimplifiedDepreciationInput) -> dict:
    """Small business simplified depreciation (ITAA 1997 Subdiv 328-D) for one income year: assets with their cost and
    first-use date, business use, disposals, cost additions and the opening pool balance in; instant asset write-off
    deductions, pool deduction (first-year rate on additions, later-year rate on the opening balance), balance write-off
    when the pool is below the threshold, assessable income from disposals, and the closing pool balance out. The
    per-asset write-off threshold is decided by the first-use date (new $20,000 rule for assets first used from
    1 July 2026). Cars are capped at the car limit when pooled. Use for "instant asset write-off", "small business pool",
    "depreciation for my sole trader business". Refuses AU-BUS-003 if not a small business entity, previously opted out
    or an excluded asset; AU-BUS-005 if an asset's first-use date is outside the income year."""
    if inp.aggregated_turnover >= figures.get("business.sbe_turnover_threshold"):
        raise Refusal("AU-BUS-003", "aggregated turnover is not below the small business entity threshold")
    if inp.previously_opted_out:
        raise Refusal("AU-BUS-003", "previously opted out of simplified depreciation; lock-out status must be checked")
    start, end = _year_bounds(figures)
    thr = figures.get("business.iawo_threshold")
    lo_rate, hi_rate = figures.get("business.pool_first_year_rate"), figures.get("business.pool_later_year_rate")
    car_limit: float | None = None
    warnings: list[str] = []
    assumptions: list[str] = []

    iawo_lines, pooled_lines = [], []
    for a in inp.assets:
        if a.asset_type == "excluded":
            raise Refusal("AU-BUS-003", f"{a.name}: asset excluded from simplified depreciation")
        if not (start <= a.first_used_date <= end):
            raise Refusal("AU-BUS-005", f"{a.name}: first used {a.first_used_date} is outside {figures.income_year}")
        b = a.business_use_percent / 100
        if a.cost < thr:
            iawo_lines.append({"asset": a.name, "cost": _r(a.cost), "business_use_percent": a.business_use_percent, "deduction": _r(a.cost * b)})
        else:
            base = a.cost
            if a.asset_type == "passenger_car":
                if car_limit is None:
                    car_limit = figures.get("car_home.car_limit")
                if a.cost > car_limit:
                    base = car_limit
            pooled_lines.append({"asset": a.name, "cost": _r(a.cost), "pooled_amount": _r(base * b),
                                 "reason": "cost at or above threshold" + ("; capped at car limit" if base != a.cost else "")})
    iawo_total = sum(x["deduction"] for x in iawo_lines)

    immediate_additions, pool_additions = [], 0.0
    for c in inp.cost_additions:
        b = c.business_use_percent / 100
        if c.asset_previously_written_off and c.first_improvement and c.cost < thr:
            immediate_additions.append({"addition": c.name, "deduction": _r(c.cost * b)})
        else:
            pool_additions += c.cost * b
    immediate_total = sum(x["deduction"] for x in immediate_additions)

    a_open = inp.opening_pool_balance + inp.opening_pool_adjustment
    b_new = sum(x["pooled_amount"] for x in pooled_lines)
    d_disp = sum(d.termination_value * d.business_use_percent / 100 for d in inp.disposals if d.was_in_pool)
    assessable = sum(d.termination_value * d.business_use_percent / 100 for d in inp.disposals if not d.was_in_pool)
    e = a_open + b_new + pool_additions - d_disp

    if e < 0:
        pool_deduction, closing, pool_assessable = 0.0, 0.0, -e
        basis = "pool balance negative after disposals: shortfall included in assessable income, closing balance nil"
    elif e < thr:
        pool_deduction, closing, pool_assessable = e, 0.0, 0.0
        basis = "pool balance below the write-off threshold: whole balance deducted, closing balance nil"
    else:
        ded_open = hi_rate * a_open
        ded_new = lo_rate * (b_new + pool_additions)
        pool_deduction = ded_open + ded_new
        closing = e - pool_deduction
        pool_assessable = 0.0
        basis = "pool depreciated: later-year rate on the opening balance, first-year rate on additions"
    total_ded = iawo_total + immediate_total + pool_deduction
    total_assessable = assessable + pool_assessable
    assumptions.append("Amounts are the business (taxable purpose) portion; cost basis is GST-exclusive if GST credits are claimed.")
    assumptions.append("Business use for pooled assets must be reviewed for the first 3 years after pooling; a change of more than 10 percentage points adjusts the opening balance.")
    if car_limit is not None:
        assumptions.append("Cars costing more than the car limit are pooled at the limit (ITAA 1997 Subdiv 40-C).")
    if e >= thr:
        warnings.append("Closing pool balance carries forward as next year's opening balance.")
    return {
        "instant_asset_write_off_threshold": thr,
        "instant_asset_write_offs": iawo_lines,
        "instant_asset_write_off_total": _r(iawo_total),
        "cost_addition_immediate_deductions": immediate_additions,
        "pool": {"opening_balance_after_adjustment": _r(a_open), "added_this_year": _r(b_new), "cost_additions": _r(pool_additions),
                 "disposals_reduction": _r(d_disp), "balance_before_deduction": _r(e), "deduction": _r(pool_deduction),
                 "closing_balance": _r(closing), "basis": basis, "pooled_assets": pooled_lines},
        "total_depreciation_deduction": _r(total_ded),
        "assessable_income_from_disposals": _r(total_assessable),
        "assumptions": assumptions, "warnings": warnings,
    }


# ================================================================ car expenses

class CarInput(BaseModel):
    """One car, one income year."""

    business_km: float = Field(ge=0, description="Business kilometres travelled in the car in the year.")
    vehicle_type: Literal["car", "other"] = Field("car", description="car = designed to carry less than 1 tonne and fewer than 9 passengers; other = ute over 1 tonne, van, truck, motorbike etc.")
    claimant: Literal["sole_trader", "partnership_individual", "company_or_trust"] = Field("sole_trader")
    logbook_total_car_expenses: float | None = Field(None, ge=0, description="Total car running costs plus decline in value for the year (logbook method), before applying business use.")
    logbook_business_use_percent: float | None = Field(None, ge=0, le=100, description="Business-use percentage from a valid 12-week logbook.")


@calculator("car_expense_cents_per_km", CarInput)
def car_expense_cents_per_km(figures: Figures, inp: CarInput) -> dict:
    """Car expense deduction for one car by the cents per kilometre method (rate for the income year, business
    kilometres capped per car per year) and, if logbook figures are given, by the logbook method, with the better
    option and the km above which the cap bites. Use for "car deduction", "cents per km", "logbook vs cents per km".
    Only for a car claimed by a sole trader or a partnership with an individual partner; refuses AU-BUS-004
    otherwise. Logbook total must already respect the car limit on depreciation."""
    if inp.vehicle_type != "car" or inp.claimant == "company_or_trust":
        raise Refusal("AU-BUS-004", "cents per kilometre needs a car claimed by an individual or a partnership with an individual partner")
    rate = figures.get("car_home.car_cents_per_km")
    cap = figures.get("car_home.car_cents_per_km_max_km")
    counted = min(inp.business_km, cap)
    cents = counted * rate
    warnings, assumptions = [], []
    out = {"rate_per_km": rate, "km_cap": cap, "km_counted": _r(counted), "cents_per_km_deduction": _r(cents)}
    if inp.business_km > cap:
        warnings.append("Business kilometres exceed the cap; the excess earns nothing under this method. The logbook method must cover the whole claim if used.")
    if inp.logbook_total_car_expenses is not None and inp.logbook_business_use_percent is not None:
        lb = inp.logbook_total_car_expenses * inp.logbook_business_use_percent / 100
        out["logbook_deduction"] = _r(lb)
        out["better_method"] = "logbook" if lb > cents else "cents_per_km"
        out["better_method_amount"] = _r(max(lb, cents))
    elif inp.logbook_total_car_expenses is not None or inp.logbook_business_use_percent is not None:
        warnings.append("Both logbook_total_car_expenses and logbook_business_use_percent are needed to compare the logbook method.")
    assumptions.append("Cents per kilometre covers all car expenses including depreciation; no separate claim for fuel, registration, insurance or servicing. Keep a record of how business kilometres were worked out.")
    assumptions.append("Logbook method needs a continuous 12-week logbook (valid 5 years), odometer readings and receipts; business use is the logbook percentage.")
    out.update({"assumptions": assumptions, "warnings": warnings})
    return out


# ================================================================ home office

class HomeOfficeInput(BaseModel):
    """Home office running expenses for a sole trader working from home."""

    hours_worked_from_home: float = Field(ge=0, description="Total actual hours worked from home in the income year.")
    hours_record_kept: bool = Field(description="True only if a record of the ACTUAL hours worked from home for the whole income year exists (timesheet, roster, diary); an estimate does not qualify.")
    expense_records_held: bool = Field(True, description="At least one record (bill or receipt) held for each type of additional running expense the rate covers.")
    actual_running_costs_business_portion: float | None = Field(
        None, ge=0, description="Optional: business portion of actual additional running expenses (energy, internet, phone, stationery), to compare with the fixed rate.")


@calculator("home_office_fixed_rate", HomeOfficeInput)
def home_office_fixed_rate(figures: Figures, inp: HomeOfficeInput) -> dict:
    """Home office running expense deduction by the fixed rate method (PCG 2023/1): actual hours worked from home x the
    rate for the income year. The rate covers energy, phone and internet, stationery and computer consumables; decline in
    value of equipment, repairs and cleaning are claimed separately. Optionally compares with actual costs. Refuses
    AU-BUS-004 without a record of actual hours for the whole year. If the income year's rate is not published or verified
    the call is refused with AU-GEN-001. Use for "working from home deduction", "fixed rate method", "home office"."""
    if not inp.hours_record_kept or not inp.expense_records_held:
        raise Refusal("AU-BUS-004", "fixed rate method needs a record of actual hours worked from home for the whole year and a record of each expense type")
    rate = figures.get("car_home.home_office_fixed_rate_per_hour")
    amount = inp.hours_worked_from_home * rate
    out = {"rate_per_hour": rate, "hours": inp.hours_worked_from_home, "fixed_rate_deduction": _r(amount),
           "fixed_rate_deduction_whole_dollars": math.floor(round(amount, 6))}
    if inp.actual_running_costs_business_portion is not None:
        out["actual_cost_deduction"] = _r(inp.actual_running_costs_business_portion)
        out["better_method"] = "actual_cost" if inp.actual_running_costs_business_portion > amount else "fixed_rate"
    out["assumptions"] = [
        "Fixed rate covers energy, phone, internet, stationery and computer consumables: no separate claim for those. Depreciating assets, repairs and cleaning are claimed separately.",
        "Occupancy expenses (rent, mortgage interest) are deductible only if an area has the character of a place of business; claiming them can affect the main residence CGT exemption.",
        "The final claim disregards cents (not rounded).",
    ]
    out["warnings"] = []
    return out


# ================================================================ non-commercial losses

class NclInput(BaseModel):
    """Div 35 non-commercial loss test for one individual sole trader activity in one income year."""

    business_loss: float = Field(gt=0, description="Current-year loss from the business activity.")
    taxable_income_excluding_business_loss: float = Field(
        description="Taxable income worked out as if this activity's loss (and any other non-commercial business loss) were not deducted; "
        "can be negative only if other losses exceed income, treat as 0 then.")
    reportable_fringe_benefits: float = Field(0, ge=0)
    reportable_super_contributions: float = Field(0, ge=0)
    net_investment_loss: float = Field(0, ge=0, description="Net financial investment loss plus net rental property loss.")
    assessable_income_from_activity: float = Field(0, ge=0, description="Assessable income from the business activity in the year (reasonable estimate for a part year).")
    profit_years_in_last_5: int = Field(0, ge=0, le=5, description="Income years, out of the current and preceding four, in which the activity made a taxable profit (assessable income exceeded deductions).")
    real_property_value: float = Field(0, ge=0, description="Value of real property (excluding a private dwelling) used on a continuing basis in the activity.")
    other_assets_value: float = Field(0, ge=0, description="Value of eligible other assets used on a continuing basis (excludes real property, cars and similar vehicles, and certain other assets).")
    activity_type: Literal["general", "primary_production_or_professional_arts", "partnership_share"] = Field("general")
    seeking_commissioner_discretion: bool = Field(False, description="The taxpayer wants, or may need, the Commissioner's discretion.")


@calculator("non_commercial_loss_test", NclInput)
def non_commercial_loss_test(figures: Figures, inp: NclInput) -> dict:
    """Div 35 non-commercial loss rules for a sole trader activity: the income requirement (taxable income before the
    loss plus reportable fringe benefits, reportable super and net investment losses, below the limit) and the four tests
    (assessable income, profit in 3 of the last 5 years, real property, other assets). Reports which tests pass, whether the
    loss can be offset against other income this year, and the amount deferred. Failing the income requirement returns
    loss_deductible_now=false and flags the Commissioner's discretion for escalation. Refuses AU-BUS-002 for the
    Commissioner's discretion, primary production / professional arts activities and partnership shares."""
    if inp.seeking_commissioner_discretion:
        raise Refusal("AU-BUS-002", "Commissioner's discretion")
    if inp.activity_type != "general":
        raise Refusal("AU-BUS-002", inp.activity_type)
    limit = figures.get("business.ncl_income_requirement")
    income_test = (max(inp.taxable_income_excluding_business_loss, 0) + inp.reportable_fringe_benefits
                   + inp.reportable_super_contributions + inp.net_investment_loss)
    income_req = income_test < limit
    tests = {
        "assessable_income": inp.assessable_income_from_activity >= figures.get("business.ncl_assessable_income_test"),
        "profit": inp.profit_years_in_last_5 >= figures.get("business.ncl_profit_test_years_required"),
        "real_property": inp.real_property_value >= figures.get("business.ncl_real_property_test"),
        "other_assets": inp.other_assets_value >= figures.get("business.ncl_other_assets_test"),
    }
    passed = [k for k, v in tests.items() if v]
    deductible = income_req and bool(passed)
    warnings, assumptions = [], []
    if not income_req:
        warnings.append("Income requirement not met: the loss is deferred. The Commissioner has a discretion in limited circumstances; escalate to a registered tax agent (AU-BUS-002) if that is being considered.")
    elif not passed:
        warnings.append("None of the four tests is passed: the loss is deferred to a later year in which the activity passes a test or makes a profit.")
    assumptions.append("Deferred losses are carried forward against later profits from the same activity; they are added back when working out net small business income for the offset.")
    assumptions.append("A part-year assessable income figure is a reasonable estimate for the full year. Each of the four tests is an alternative: one pass (plus the income requirement) is enough.")
    return {"income_for_requirement": _r(income_test), "income_requirement_limit": limit, "income_requirement_met": income_req,
            "tests": tests, "tests_passed": passed, "loss_deductible_now": deductible,
            "deductible_loss": _r(inp.business_loss if deductible else 0.0),
            "deferred_loss": _r(0.0 if deductible else inp.business_loss),
            "commissioner_discretion_possible": not income_req,
            "assumptions": assumptions, "warnings": warnings}


# ================================================================ personal services income

class PsiInput(BaseModel):
    """Structured facts for the personal services business (PSB) tests. Leave a field null if unknown."""

    income_mainly_reward_for_personal_effort: bool | None = Field(
        None, description="More than half of the income is a reward for the individual's personal efforts or skills (not from assets, "
        "goods or a business structure). False means the PSI rules do not apply at all.")
    total_psi: float | None = Field(None, gt=0, description="Total PSI for the year.")
    largest_client_psi_including_associates: float | None = Field(None, ge=0, description="PSI from the single largest client together with its associates.")
    result_share_of_psi: float | None = Field(None, ge=0, le=1, description="Share of PSI paid for producing a specified result (0 to 1).")
    supplies_own_tools_and_equipment: bool | None = Field(None, description="Results test: supplies any tools or equipment needed to do the work.")
    liable_to_fix_defects_at_own_cost: bool | None = Field(None, description="Results test: legally liable to rectify defects at own cost.")
    unrelated_clients_from_public_offers: int | None = Field(None, ge=0, description="Unrelated clients obtained as a direct result of offers to the public (advertising, website, tenders) in the year.")
    principal_work_share_by_others: float | None = Field(None, ge=0, le=1, description="Share of principal work by market value done by employees or contractors (not associates, not the individual).")
    apprentice_months: int | None = Field(None, ge=0, le=12, description="Months in the year one or more apprentices were employed.")
    premises_used_mainly_for_psi: bool | None = Field(None)
    premises_exclusive_use: bool | None = Field(None)
    premises_separate_from_private: bool | None = Field(None)
    premises_separate_from_clients: bool | None = Field(None)
    premises_maintained_all_year: bool | None = Field(None)
    seeking_psb_determination: bool = Field(False, description="A PSB determination from the Commissioner is being considered or requested.")


def _all(*vals: bool | None) -> bool | None:
    """Three-valued AND: False if any False, None if any unknown, else True."""
    if any(v is False for v in vals):
        return False
    if any(v is None for v in vals):
        return None
    return True


@calculator("psi_tests", PsiInput)
def psi_tests(figures: Figures, inp: PsiInput) -> dict:
    """Personal services income (ITAA 1997 Pt 2-42): from structured facts, decides which personal services business
    tests pass (results test; unrelated clients, employment and business premises tests, each only usable if the 80% rule
    is met) and whether the PSI rules apply to the individual for the year. When the facts are incomplete and could change
    the answer, or a PSB determination is being sought, it refuses AU-BUS-001 (escalate) and lists what is missing. When the
    PSI rules apply, notes the consequences (PSI attributed to the individual, limits on deductions). Passing a test does not
    remove Part IVA risk."""
    if inp.income_mainly_reward_for_personal_effort is False:
        return {"psi": False, "psi_rules_apply": False, "outcome": "not_psi",
                "reason": "income is not mainly a reward for personal effort or skills, so it is not personal services income",
                "assumptions": [], "warnings": []}
    if inp.seeking_psb_determination:
        raise Refusal("AU-BUS-001", "a personal services business determination is being considered")
    res_share = figures.get("business.psi_results_test_share")
    rule80 = figures.get("business.psi_80_rule_share")
    emp_share = figures.get("business.psi_employment_test_share")
    app_months = figures.get("business.psi_employment_test_apprentice_months")

    results = _all(
        None if inp.result_share_of_psi is None else inp.result_share_of_psi >= res_share,
        inp.supplies_own_tools_and_equipment, inp.liable_to_fix_defects_at_own_cost)
    if inp.total_psi is None or inp.largest_client_psi_including_associates is None:
        rule_ok, largest_share = None, None
    else:
        largest_share = inp.largest_client_psi_including_associates / inp.total_psi
        rule_ok = largest_share < rule80
    unrelated = None if inp.unrelated_clients_from_public_offers is None else inp.unrelated_clients_from_public_offers >= 2
    if inp.principal_work_share_by_others is None and inp.apprentice_months is None:
        employment = None
    else:
        a = None if inp.principal_work_share_by_others is None else inp.principal_work_share_by_others >= emp_share
        b = None if inp.apprentice_months is None else inp.apprentice_months >= app_months
        employment = True if (a or b) else (None if (a is None or b is None) else False)
    premises = _all(inp.premises_used_mainly_for_psi, inp.premises_exclusive_use, inp.premises_separate_from_private,
                    inp.premises_separate_from_clients, inp.premises_maintained_all_year)
    others = {"unrelated_clients": unrelated, "employment": employment, "business_premises": premises}
    tests = {"results": results, **others, "eighty_percent_rule_met": rule_ok}

    other_pass = any(v is True for v in others.values())
    other_unknown = any(v is None for v in others.values())
    warnings = ["Passing a personal services business test does not remove Part IVA exposure (PCG 2025/5); the arrangement must still be commercially genuine."]
    assumptions = ["Tests are applied to the individual for this income year only; each year stands alone."]

    if results is True:
        outcome, applies = "psb_self_assessed_results_test", False
    elif rule_ok is True and other_pass:
        outcome, applies = "psb_self_assessed_other_test", False
    elif rule_ok is False and results is False:
        outcome, applies = "psi_rules_apply", True
        warnings.append("80% or more of PSI is from one client and its associates and the results test fails: the other tests cannot be used. A PSB determination from the Commissioner is the only route to PSB status (AU-BUS-001).")
    elif results is False and all(v is False for v in others.values()):
        outcome, applies = "psi_rules_apply", True
    elif results is False and rule_ok is True and not other_unknown and not other_pass:
        outcome, applies = "psi_rules_apply", True
    else:
        missing = [k for k, v in tests.items() if v is None]
        raise Refusal("AU-BUS-001", "outcome depends on unanswered facts: " + ", ".join(missing))
    consequences = ([] if not applies else [
        "PSI is attributed to the individual (ITAA 1997 s 86-15) even if it is paid to a company, partnership or trust.",
        "Deductions against PSI are limited (Div 85): no rent, mortgage interest, rates or land tax for the home, no payments to associates for work that is not principally by them.",
        "PSI is excluded from net small business income for the small business income tax offset."])
    return {"psi": True, "psi_rules_apply": applies, "outcome": outcome, "tests": tests,
            "largest_client_share": None if largest_share is None else round(largest_share, 4),
            "consequences": consequences, "assumptions": assumptions, "warnings": warnings}
