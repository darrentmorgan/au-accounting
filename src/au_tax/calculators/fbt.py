"""Fringe benefits tax (FBT): car benefits (statutory formula and operating cost), FBT payable and due
dates, reportable fringe benefits amount, loan benefits, electric car exemption, work vehicle
exemption, car parking, meal entertainment and minor benefit screening.

Law: Fringe Benefits Tax Assessment Act 1986 (FBTAA) ss 5B (gross-up), 7-10 (car benefits), 8(2) (work
vehicles), 8A (electric cars), 39A (car parking), 58P (minor benefits), 135P (reportable amount),
Div 9A (meal entertainment); Fringe Benefits Tax (Rates) Act; Practical Compliance Guidelines PCG 2018/3
and PCG 2024/2. Every rate, threshold and date comes from data/rates/<income-year>.yaml (fbt group) and its
overlay via Figures. The income year argument selects the FBT year that ENDS inside it: 2026-27 means the
FBT year 1 Apr 2026 to 31 Mar 2027 (FBT2027).
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from au_tax.figures import FigureError, Figures
from au_tax.holidays import COMMONWEALTH, roll_due_date, roll_due_date_or_statutory
from au_tax.registry import Refusal, calculator

EmployerType = Literal["standard", "rebatable_nfp", "pbi_or_health_promotion", "hospital_or_ambulance", "government"]
SpecialCircumstance = Literal[
    "lafha",
    "housing",
    "remote_area_housing",
    "recreation_entertainment",
    "entertainment_facility_leasing",
    "salary_packaged_meal_entertainment",
    "pre_2011_commitment_car",
    "employee_status_doubtful",
]
_SPECIAL_CODES = {
    "lafha": "AU-FBT-002",
    "housing": "AU-FBT-003",
    "remote_area_housing": "AU-FBT-003",
    "recreation_entertainment": "AU-FBT-004",
    "entertainment_facility_leasing": "AU-FBT-004",
    "salary_packaged_meal_entertainment": "AU-FBT-004",
    "pre_2011_commitment_car": "AU-FBT-005",
    "employee_status_doubtful": "AU-FBT-006",
}
REVIEW = "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use."


# ---------------------------------------------------------------- helpers

def _r(x: float) -> float:
    return round(x + 0.0, 2)


def _d(n: int | float) -> date:
    """Figures store dates as integer yyyymmdd (the rates schema allows numbers only)."""
    n = int(n)
    return date(n // 10000, (n // 100) % 100, n % 100)


def _fbt_year(figures: Figures) -> tuple[date, date, int]:
    """(start, end, days) of the FBT year whose 31 March falls in this income year."""
    end = figures.data["meta"].get("fbt_year_ending")
    if not isinstance(end, date):
        raise FigureError(f"no fbt_year_ending in the {figures.income_year} rates file")
    start = date(end.year - 1, 4, 1)
    return start, end, (end - start).days + 1


def _label(end: date) -> str:
    return f"FBT{end.year}"


def _roll(figures: Figures, d: date, warnings: list[str], strict: bool = True):
    """First business day on or after d (TAA 1953 s 8AAZMB and Sch 1 s 388-52): not a Saturday, Sunday or a public holiday
    for the whole of any State, the ACT or the NT. Holiday data: data/holidays/au.yaml. strict=False (a due date that is
    secondary to the amount) returns the unrolled date with an AU-GEN-004 note when the date is after the holiday data."""
    r = (roll_due_date if strict else roll_due_date_or_statutory)(d, COMMONWEALTH, figures)
    warnings.extend(w for w in r.warnings if w not in warnings)
    return r


def _gross_up(figures: Figures, kind: int | None) -> float | None:
    if kind is None:
        return None
    return figures.get("fbt.gross_up_type1" if kind == 1 else "fbt.gross_up_type2")


def _check_special(items: list[str]) -> None:
    for s in items:
        raise Refusal(_SPECIAL_CODES[s], s)


def _check_employer(employer_type: str) -> None:
    if employer_type != "standard":
        raise Refusal("AU-FBT-001", f"employer type {employer_type}")


def _gross_up_block(figures: Figures, taxable_value: float, kind: int | None) -> dict:
    if kind is None:
        return {}
    gu = _gross_up(figures, kind)
    grossed = taxable_value * gu
    return {"gross_up_type": kind, "gross_up_rate": gu, "grossed_up_taxable_value": _r(grossed),
            "fbt_rate": figures.get("fbt.rate"), "fbt_on_this_benefit": _r(grossed * figures.get("fbt.rate"))}


def _year_header(figures: Figures) -> dict:
    s, e, n = _fbt_year(figures)
    return {"fbt_year": _label(e), "fbt_year_start": s.isoformat(), "fbt_year_end": e.isoformat(), "days_in_fbt_year": n}


# ---------------------------------------------------------------- car: statutory formula

class CarStatutoryInput(BaseModel):
    """Statutory formula car fringe benefit for one car and one employee for one FBT year."""

    base_value: float = Field(gt=0, description="Base value of the car: cost price to the provider including GST, luxury car tax, "
                              "dealer delivery and non-business accessories, less trade-in or cash paid by the employee; "
                              "excluding registration and stamp duty.")
    days_available: int | None = Field(None, ge=0, le=366, description="Days in the FBT year the car was used or available for private use. "
                                       "Default: the whole FBT year.")
    employee_contributions: float = Field(0, ge=0, description="Recipient's payments: after-tax amounts paid to the employer for the car and "
                                          "car expenses (fuel, rego, insurance, repairs) the employee paid and was not reimbursed for.")
    gross_up_type: Literal[1, 2] | None = Field(None, description="1 if the provider is entitled to a GST credit on the car, 2 if not. "
                                                "Optional: when given, the grossed-up value and FBT are returned too.")
    pre_existing_commitment: bool = Field(False, description="Car provided under a commitment made before 7.30pm AEST 10 May 2011 (refuses AU-FBT-005).")
    ev_exempt: bool = Field(False, description="The car benefit is exempt under the electric car exemption (use ev_exemption_check first). "
                            "Taxable value is then nil but the calculated value is still reportable.")


@calculator("car_fringe_benefit_statutory", CarStatutoryInput)
def car_fringe_benefit_statutory(figures: Figures, inp: CarStatutoryInput) -> dict:
    """Taxable value of a car fringe benefit under the statutory formula method (FBTAA s 9): base value x flat
    statutory rate x days available / days in the FBT year, less employee contributions (not below nil). The
    income year argument picks the FBT year ending in it (2026-27 = FBT year 1 Apr 2026 to 31 Mar 2027). Use for
    "FBT on a company car", "taxable value of a car benefit", "novated lease car FBT" when no logbook is kept or
    to compare with the operating cost method. Optionally grosses up (type 1 or 2) and applies 47% FBT. Refuses
    AU-FBT-005 for pre-May-2011 commitments; for an exempt electric car pass ev_exempt true (taxable value nil,
    reportable value still returned). Returns taxable_value, taxable_value_for_rfba, assumptions and warnings."""
    if inp.pre_existing_commitment:
        raise Refusal("AU-FBT-005", "pre-existing commitment before 10 May 2011")
    hdr = _year_header(figures)
    total_days = hdr["days_in_fbt_year"]
    warnings: list[str] = []
    days = total_days if inp.days_available is None else inp.days_available
    if days > total_days:
        warnings.append(f"days_available {days} exceeds the {total_days} days in the FBT year; capped.")
        days = total_days
    rate = figures.get("fbt.car_statutory_rate")
    gross = inp.base_value * rate * days / total_days
    tv = max(0.0, gross - inp.employee_contributions)
    if inp.employee_contributions > gross:
        warnings.append("Employee contributions exceed the gross taxable value: taxable value is nil; the excess cannot reduce other benefits.")
    assumptions = [
        "Flat statutory rate applies (no pre-existing commitment before 10 May 2011).",
        "Base value includes GST and luxury car tax; the employer may need to confirm the cost price basis and any trade-in.",
        "One car, one employee; associates are treated as the employee.",
    ]
    out = {**hdr, "method": "statutory_formula", "statutory_rate": rate, "days_available": days,
           "gross_taxable_value": _r(gross), "employee_contributions": _r(inp.employee_contributions),
           "taxable_value": _r(0.0 if inp.ev_exempt else tv), "taxable_value_for_rfba": _r(tv),
           "exempt_ev": inp.ev_exempt, "assumptions": assumptions, "warnings": warnings}
    out.update(_gross_up_block(figures, out["taxable_value"], inp.gross_up_type))
    if inp.ev_exempt:
        warnings.append("Exempt electric car benefit: nil FBT but the calculated taxable value still counts towards the employee's reportable fringe benefits amount (FBTAA s 135P(3)).")
    return out


# ---------------------------------------------------------------- car: operating cost method

class CarOperatingCostInput(BaseModel):
    """Operating cost method car fringe benefit for one car and one employee for one FBT year."""

    ownership: Literal["owned", "leased"] = Field(description="owned includes hire purchase; leased means the provider leases the car.")
    running_costs: float = Field(ge=0, description="Running costs for the period held, GST-inclusive: fuel or electricity, oil, repairs, servicing, tyres, "
                                 "registration, insurance, roadside assistance, and costs the employee paid. Exclude lease payments and depreciation.")
    lease_costs: float = Field(0, ge=0, description="Leased cars only: lease payments for the period held, in place of depreciation and interest.")
    cost_price: float | None = Field(None, gt=0, description="Owned cars: cost price including GST, luxury car tax and delivery, less trade-in and deposits.")
    years_owned_before_fbt_year: int = Field(0, ge=0, le=30, description="Owned cars: whole FBT years already held before this one (0 if acquired in this FBT year); "
                                             "depreciated value = cost price x (1 - deemed rate) for each of these years.")
    days_held: int | None = Field(None, ge=1, le=366, description="Days in the FBT year the car was held to provide benefits; default whole year. Apportions depreciation and interest.")
    business_use_percentage: float = Field(0, ge=0, le=100, description="Business use % from the logbook (logbook year) or the "
                                           "averaged prior logbook (non-logbook year). Private use is the rest.")
    logbook_records_adequate: bool = Field(True, description="False if the required logbook and odometer records were not kept: business use is then treated as nil.")
    employee_contributions: float = Field(0, ge=0, description="Recipient's payments (after tax) towards the car or its expenses.")
    gross_up_type: Literal[1, 2] | None = Field(None, description="Optional gross-up type for the resulting taxable value.")
    pre_existing_commitment: bool = Field(False, description="Pre-10-May-2011 commitment: refuses AU-FBT-005.")
    ev_exempt: bool = Field(False, description="Exempt electric car benefit: taxable value nil, calculated value reportable.")

    @model_validator(mode="after")
    def _consistent(self):
        if self.ownership == "owned" and self.cost_price is None:
            raise ValueError("cost_price is required for an owned car")
        if self.ownership == "leased" and self.cost_price is not None:
            raise ValueError("cost_price is not used for a leased car; give lease_costs")
        return self


@calculator("car_fringe_benefit_operating_cost", CarOperatingCostInput)
def car_fringe_benefit_operating_cost(figures: Figures, inp: CarOperatingCostInput) -> dict:
    """Taxable value of a car fringe benefit under the operating cost method (FBTAA s 10): total operating
    costs (running costs plus deemed depreciation at the diminishing-value rate and deemed interest at the
    benchmark rate on the depreciated value, or lease payments for a leased car) x private use %, less employee
    contributions (not below nil). Private use % = 100 less the logbook business use %. Use when the employer
    elects the operating cost method and keeps a logbook; the election must be made by the FBT return due date.
    Without adequate records business use is treated as nil. The income year argument picks the FBT year ending in it.
    Returns operating cost components, taxable_value and the statutory-method comparison note."""
    if inp.pre_existing_commitment:
        raise Refusal("AU-FBT-005", "pre-existing commitment before 10 May 2011")
    hdr = _year_header(figures)
    total_days = hdr["days_in_fbt_year"]
    days = total_days if inp.days_held is None else min(inp.days_held, total_days)
    frac = days / total_days
    warnings: list[str] = []
    assumptions = ["Operating costs are GST-inclusive and cover the period the car was held to provide the benefit.",
                   "Deemed depreciation and interest are used, not income tax depreciation or actual interest.",
                   "Non-business accessories fitted after purchase are not modelled separately."]
    dep = interest = 0.0
    depreciated = None
    dep_rate = interest_rate = None
    if inp.ownership == "owned":
        dep_rate = figures.get("fbt.car_operating_cost_depreciation_rate")
        interest_rate = figures.get("fbt.benchmark_interest_rate")
        depreciated = inp.cost_price * (1 - dep_rate) ** inp.years_owned_before_fbt_year
        dep = depreciated * dep_rate * frac
        interest = depreciated * interest_rate * frac
        costs = inp.running_costs + dep + interest
    else:
        costs = inp.running_costs + inp.lease_costs
    business = inp.business_use_percentage
    if not inp.logbook_records_adequate:
        if business:
            warnings.append("Logbook or odometer records not adequate: business use of "
                            f"{business}% ignored; the car is treated as 100% private use.")
        business = 0.0
    private = 100.0 - business
    gross = costs * private / 100.0
    tv = max(0.0, gross - inp.employee_contributions)
    warnings.append("The operating cost method must be elected by the FBT return due date (or 21 May if no return); "
                    "compare with the statutory formula method and use the lower taxable value.")
    out = {**hdr, "method": "operating_cost", "days_held": days, "running_costs": _r(inp.running_costs),
           "lease_costs": _r(inp.lease_costs), "depreciated_value_at_start": None if depreciated is None else _r(depreciated),
           "deemed_depreciation": _r(dep), "deemed_interest": _r(interest), "total_operating_costs": _r(costs),
           "business_use_percentage": business, "private_use_percentage": private,
           "gross_taxable_value": _r(gross), "employee_contributions": _r(inp.employee_contributions),
           "taxable_value": _r(0.0 if inp.ev_exempt else tv), "taxable_value_for_rfba": _r(tv),
           "exempt_ev": inp.ev_exempt, "assumptions": assumptions, "warnings": warnings}
    out.update(_gross_up_block(figures, out["taxable_value"], inp.gross_up_type))
    return out


# ---------------------------------------------------------------- FBT payable

class BenefitLine(BaseModel):
    description: str = ""
    taxable_value: float = Field(ge=0, description="Taxable value after reductions and employee contributions, before gross-up.")
    gross_up_type: Literal[1, 2]


class FbtPayableInput(BaseModel):
    """Employer FBT for one FBT year from aggregate taxable values."""

    type1_taxable_value: float = Field(0, ge=0, description="Total taxable value of type 1 benefits (provider entitled to GST credits), before gross-up.")
    type2_taxable_value: float = Field(0, ge=0, description="Total taxable value of type 2 benefits (no GST credits), before gross-up.")
    benefits: list[BenefitLine] = Field(default_factory=list, description="Optional itemised benefits added to the totals above.")
    employer_type: EmployerType = "standard"
    special_circumstances: list[SpecialCircumstance] = Field(default_factory=list, description="Any special regime present; each stops the calculation.")
    instalments_paid: float = Field(0, ge=0, description="FBT instalments already paid through activity statements for the year.")
    prior_year_fbt: float | None = Field(None, ge=0, description="FBT payable for the prior FBT year, to say whether quarterly instalments apply this year.")
    lodgment: Literal["self", "tax_agent_electronic"] = Field("self", description="Who lodges the FBT return; agent electronic lodgment generally gets the June date.")


@calculator("fbt_payable", FbtPayableInput)
def fbt_payable(figures: Figures, inp: FbtPayableInput) -> dict:
    """Employer FBT payable for one FBT year: (type 1 taxable value x type 1 gross-up + type 2 taxable value x
    type 2 gross-up) x FBT rate, less instalments paid, plus the return lodgment and payment due date (21 May, or
    generally 25 June via a tax agent, moved to the first business day after if a Saturday, Sunday or public holiday, TAA 1953 s 8AAZMB) and whether quarterly
    instalments apply. Give taxable values before gross-up; use the car, loan, parking and meal entertainment
    tools to get each taxable value first. The income year argument picks the FBT year ending in it (2026-27 =
    FBT2027, 1 Apr 2026 to 31 Mar 2027). Refuses AU-FBT-001 for PBI, hospital and rebatable NFP employers and
    for salary packaging caps, AU-FBT-002 living-away-from-home, AU-FBT-003 housing, AU-FBT-004 entertainment
    beyond the simple methods, AU-FBT-005 pre-2011 car commitments, AU-FBT-006 doubtful employee status."""
    _check_employer(inp.employer_type)
    _check_special(inp.special_circumstances)
    hdr = _year_header(figures)
    t1 = inp.type1_taxable_value + sum(b.taxable_value for b in inp.benefits if b.gross_up_type == 1)
    t2 = inp.type2_taxable_value + sum(b.taxable_value for b in inp.benefits if b.gross_up_type == 2)
    g1, g2 = figures.get("fbt.gross_up_type1"), figures.get("fbt.gross_up_type2")
    rate = figures.get("fbt.rate")
    gu1, gu2 = t1 * g1, t2 * g2
    fbt = (gu1 + gu2) * rate
    warnings: list[str] = []
    return_roll = _roll(figures, _d(figures.get("fbt.return_due_date")), warnings, strict=False)
    agent_roll = _roll(figures, _d(figures.get("fbt.return_due_date_agent_electronic")), warnings, strict=False)
    field_refusals = [{"field": f, **r.out_of_range} for f, r in (("return_and_payment_due_self_lodged", return_roll),
                                                                     ("return_and_payment_due_agent_electronic", agent_roll)) if r.out_of_range]
    return_due, agent_due = return_roll.due, agent_roll.due
    due = agent_due if inp.lodgment == "tax_agent_electronic" else return_due
    due_roll = agent_roll if inp.lodgment == "tax_agent_electronic" else return_roll
    threshold = figures.get("fbt.instalment_prior_year_fbt_min")
    instal = None
    if inp.prior_year_fbt is not None:
        instal = inp.prior_year_fbt >= threshold
    warnings.append("The agent date applies only if the employer was on the agent's FBT client list by 21 May.")
    if not (t1 or t2):
        warnings.append("No taxable value given: FBT is nil.")
    out = {**hdr, "type1_taxable_value": _r(t1), "type2_taxable_value": _r(t2),
           "type1_grossed_up": _r(gu1), "type2_grossed_up": _r(gu2), "total_grossed_up_taxable_value": _r(gu1 + gu2),
           "gross_up_type1": g1, "gross_up_type2": g2, "fbt_rate": rate, "fbt_payable": _r(fbt),
           "instalments_paid": _r(inp.instalments_paid), "balance_payable_or_refund": _r(fbt - inp.instalments_paid),
           "return_and_payment_due": due.isoformat(), "return_and_payment_due_self_lodged": return_due.isoformat(),
           "return_and_payment_due_agent_electronic": agent_due.isoformat(),
           "business_day_roll": due_roll.as_dict(), "field_refusals": field_refusals,
           "quarterly_instalments_apply_this_year": instal, "instalment_threshold": threshold,
           "assumptions": ["Taxable values are already net of employee contributions and reductions; standard (non-exempt, non-rebatable) employer.",
                           "FBT is a flat rate on the grossed-up taxable value; no rebate or cap applies."],
           "warnings": warnings}
    return out


# ---------------------------------------------------------------- reportable fringe benefits amount

class RfbaInput(BaseModel):
    """One employee's reportable fringe benefits amount for one FBT year."""

    type1_taxable_value: float = Field(0, ge=0, description="Employee's reportable type 1 benefits, taxable value before gross-up.")
    type2_taxable_value: float = Field(0, ge=0, description="Employee's reportable type 2 benefits, taxable value before gross-up.")
    exempt_ev_taxable_value: float = Field(0, ge=0, description="Notional taxable value of exempt electric car benefits (they are still reportable).")
    employer_type: EmployerType = "standard"


@calculator("reportable_fringe_benefits_amount", RfbaInput)
def reportable_fringe_benefits_amount(figures: Figures, inp: RfbaInput) -> dict:
    """Reportable fringe benefits amount (RFBA) for one employee for one FBT year. If the total taxable value of
    the employee's reportable fringe benefits (type 1 plus type 2 plus exempt electric car benefits) is MORE than
    the reporting threshold, the RFBA is that total grossed up at the LOWER (type 2) rate whatever the benefit type;
    otherwise nil. Reported on the income statement for the income year ending 30 June after the FBT year (FBT year
    ending 31 Mar 2027 goes on the 2026-27 income statement) and used in the individual's MLS, HELP and other tests
    (pass the result to individual_income_tax reportable_fringe_benefits). Refuses AU-FBT-001 for exempt or rebatable employers."""
    _check_employer(inp.employer_type)
    hdr = _year_header(figures)
    threshold = figures.get("fbt.rfba_reporting_threshold_taxable_value")
    g2 = figures.get("fbt.gross_up_type2")
    total = inp.type1_taxable_value + inp.type2_taxable_value + inp.exempt_ev_taxable_value
    reportable = total > threshold
    rfba = total * g2 if reportable else 0.0
    minimum = figures.get("fbt.rfba_min_grossed_up_value")
    return {**hdr, "total_taxable_value": _r(total), "reporting_threshold": threshold, "reportable": reportable,
            "gross_up_rate_used": g2, "reportable_fringe_benefits_amount": _r(rfba),
            "reportable_fringe_benefits_amount_whole_dollars": math.floor(rfba),
            "income_year_reported_in": figures.income_year,
            "minimum_grossed_up_value_when_reportable": minimum,
            "assumptions": ["Only benefits that count towards the reportable amount are included (exempt benefits other than exempt electric "
                            "cars, and meal entertainment valued by the 50:50 or 12-week methods, are excluded by the caller).",
                            "The ATO shows the grossed-up amount in whole dollars, ignoring cents."],
            "warnings": ["The threshold is on taxable value, not the grossed-up figure; exactly the threshold is not reportable."]}


# ---------------------------------------------------------------- loan fringe benefit

class LoanPeriod(BaseModel):
    balance: float = Field(ge=0)
    days: int = Field(ge=0, le=366)


class LoanInput(BaseModel):
    """Low-interest or interest-free employee loan for one FBT year."""

    loan_balance: float | None = Field(None, ge=0, description="Constant outstanding balance; use periods if it changed.")
    days_outstanding: int | None = Field(None, ge=0, le=366, description="Days the loan_balance was outstanding; default whole FBT year.")
    periods: list[LoanPeriod] = Field(default_factory=list, description="Alternative to loan_balance: outstanding balance and days for each period.")
    interest_charged: float = Field(0, ge=0, description="Interest actually paid or payable by the employee for the FBT year.")
    income_producing_use_percentage: float = Field(0, ge=0, le=100, description="Percentage of the loan used for income-producing purposes "
                                                   "(otherwise deductible rule). Assumes the interest rate was set without regard to the use.")
    gross_up_type: Literal[1, 2] | None = Field(2, description="Loans are normally type 2 (no GST credit on a financial supply); override if needed.")

    @model_validator(mode="after")
    def _one_source(self):
        if (self.loan_balance is None) == (not self.periods):
            raise ValueError("give either loan_balance or periods, not both or neither")
        return self


@calculator("loan_fringe_benefit", LoanInput)
def loan_fringe_benefit(figures: Figures, inp: LoanInput) -> dict:
    """Taxable value of a loan fringe benefit (interest-free or low-interest employee loan): notional interest at
    the FBT benchmark (statutory) interest rate on the daily outstanding balance, less interest actually charged,
    reduced under the otherwise deductible rule for the income-producing share of the loan. The benchmark rate is
    set by FBT year (the rate for the FBT year ending in the income year argument). Use for "employee loan at 0%",
    "FBT on a loan to a director-employee". Type 2 gross-up by default. Returns notional interest, taxable value
    before and after the otherwise deductible rule, and optionally FBT."""
    hdr = _year_header(figures)
    total_days = hdr["days_in_fbt_year"]
    rate = figures.get("fbt.benchmark_interest_rate")
    if inp.periods:
        balance_days = sum(p.balance * p.days for p in inp.periods)
    else:
        d = total_days if inp.days_outstanding is None else inp.days_outstanding
        balance_days = inp.loan_balance * d
    notional = balance_days / total_days * rate
    before = max(0.0, notional - inp.interest_charged)
    p = inp.income_producing_use_percentage / 100.0
    after = before * (1 - p)
    out = {**hdr, "benchmark_interest_rate": rate, "notional_interest": _r(notional), "interest_charged": _r(inp.interest_charged),
           "taxable_value_before_otherwise_deductible": _r(before), "otherwise_deductible_reduction": _r(before - after),
           "taxable_value": _r(after),
           "assumptions": ["Interest accrues on the daily balance; the benchmark rate for the FBT year applies to the whole year.",
                           "Otherwise deductible rule assumes the interest rate was set without regard to how the employee uses the loan; "
                           "the employee declaration must be held by the return due date."],
           "warnings": []}
    if inp.income_producing_use_percentage and not before:
        out["warnings"].append("No taxable value before the otherwise deductible rule.")
    out.update(_gross_up_block(figures, out["taxable_value"], inp.gross_up_type))
    return out


# ---------------------------------------------------------------- electric car exemption

class EvInput(BaseModel):
    """Facts needed to test the electric car exemption (FBTAA s 8A)."""

    vehicle_type: Literal["battery_electric", "hydrogen_fuel_cell", "plug_in_hybrid", "hybrid_non_plug_in", "petrol_or_diesel"]
    is_car: bool = Field(True, description="False for a vehicle that is not a 'car' (load one tonne or more, 9 or more passengers, motorcycle).")
    first_held_date: date | None = Field(None, description="Date the car was first held (owned or leased) by anyone, ISO yyyy-mm-dd.")
    first_used_date: date | None = Field(None, description="Date the car was first used or available for use by anyone, ISO yyyy-mm-dd.")
    benefit_date: date | None = Field(None, description="Date (or start of the period) the private use is provided; default the start of the FBT year.")
    recipient: Literal["current_employee", "associate_of_current_employee", "former_or_future_employee", "other"] = "current_employee"
    lct_payable: bool | None = Field(None, description="True if luxury car tax was ever payable on the sale or importation. If unknown give the value and date below.")
    value_at_first_retail_sale: float | None = Field(None, ge=0, description="LCT value (GST-inclusive, excluding LCT) at first retail sale or import.")
    first_retail_sale_date: date | None = Field(None, description="Date of first retail sale or importation, ISO yyyy-mm-dd.")
    phev_exempt_before_2025_04_01: bool | None = Field(None, description="Plug-in hybrid only: the car was used or available for use and the benefit was exempt before 1 Apr 2025.")
    phev_binding_commitment_continues: bool | None = Field(None, description="Plug-in hybrid only: a financially binding commitment to keep providing the car on and after 1 Apr 2025 (an optional extension is not binding).")
    phev_commitment_changed_after_2025_04_01: bool = Field(False, description="Plug-in hybrid only: the commitment was changed or replaced on or after 1 Apr 2025.")


@calculator("ev_exemption_check", EvInput)
def ev_exemption_check(figures: Figures, inp: EvInput) -> dict:
    """Test whether private use of a car is exempt under the electric car exemption (FBTAA s 8A) with reasons.
    Conditions: a zero or low emissions car (battery electric, hydrogen fuel cell, and plug-in hybrid only if
    grandfathered), first held AND used on or after 1 Jul 2022 (the later of the two dates), provided to a current
    employee or associate, and no luxury car tax ever payable (value at first retail sale not above the fuel-efficient
    LCT threshold for the year of sale). Plug-in hybrids lose eligibility from 1 Apr 2025 unless their use was already
    exempt before then and a financially binding commitment continues unchanged. Date-effective: the announced change from 1 Apr
    2027 (a base value limit with a reduced statutory rate above it, then a discount for all eligible cars from 1 Apr 2029) is an
    exposure draft, NOT law, and is returned only as information; current law keeps the full exemption. Returns exempt
    (true, false or null if facts are missing), each condition, and reasons. Exempt benefits stay reportable."""
    hdr = _year_header(figures)
    fy_start = date.fromisoformat(hdr["fbt_year_start"])
    benefit = inp.benefit_date or fy_start
    ev_start = _d(figures.get("fbt.ev_exemption_start_date"))
    phev_cut = _d(figures.get("fbt.phev_cutoff_date"))
    reasons: list[str] = []
    warnings: list[str] = []
    conds: dict[str, bool | None] = {}

    # vehicle
    if not inp.is_car:
        conds["is_car"] = False
        reasons.append("Not a 'car' for FBT (load one tonne or more, 9 or more passengers, or motorcycle): the electric car exemption applies only to cars.")
    else:
        conds["is_car"] = True
    if inp.vehicle_type in ("hybrid_non_plug_in", "petrol_or_diesel"):
        conds["zero_or_low_emissions"] = False
        reasons.append(f"{inp.vehicle_type} is not a zero or low emissions vehicle (only battery electric, hydrogen fuel cell, and grandfathered plug-in hybrids).")
    elif inp.vehicle_type == "plug_in_hybrid":
        if benefit < phev_cut:
            conds["zero_or_low_emissions"] = True
            reasons.append(f"Plug-in hybrid counts as low emissions for benefits before {phev_cut.isoformat()}.")
        else:
            gf = (inp.phev_exempt_before_2025_04_01, inp.phev_binding_commitment_continues)
            if None in gf:
                conds["zero_or_low_emissions"] = None
                reasons.append("Plug-in hybrid from 1 Apr 2025: need whether use was exempt before that date and whether a binding commitment continues.")
            elif gf == (True, True) and not inp.phev_commitment_changed_after_2025_04_01:
                conds["zero_or_low_emissions"] = True
                reasons.append("Plug-in hybrid grandfathered: exempt use before 1 Apr 2025 and a financially binding commitment continues unchanged.")
            else:
                conds["zero_or_low_emissions"] = False
                if inp.phev_commitment_changed_after_2025_04_01:
                    reasons.append("Plug-in hybrid: the commitment was changed or replaced on or after 1 Apr 2025, so the exemption ends from that new commitment.")
                if not inp.phev_exempt_before_2025_04_01:
                    reasons.append("Plug-in hybrid was not in exempt use before 1 Apr 2025 (delivery delays do not extend the date).")
                if not inp.phev_binding_commitment_continues:
                    reasons.append("No financially binding commitment continues on and after 1 Apr 2025 (an optional extension is not binding).")
    else:
        conds["zero_or_low_emissions"] = True

    # held and used
    if inp.first_held_date is None or inp.first_used_date is None:
        conds["first_held_and_used_on_or_after_start"] = None
        reasons.append("Need the dates the car was first held and first used.")
    else:
        both = max(inp.first_held_date, inp.first_used_date)
        ok = both >= ev_start
        conds["first_held_and_used_on_or_after_start"] = ok
        reasons.append(f"First time both held and used: {both.isoformat()} "
                       f"({'on or after' if ok else 'before'} {ev_start.isoformat()}).")
    if benefit < ev_start:
        conds["benefit_on_or_after_start"] = False
        reasons.append(f"Benefit provided before {ev_start.isoformat()}: the exemption does not apply.")

    # recipient
    if inp.recipient in ("current_employee", "associate_of_current_employee"):
        conds["recipient_current_employee_or_associate"] = True
    else:
        conds["recipient_current_employee_or_associate"] = False
        reasons.append("Recipient must be a current employee or their associate; use by a former or future employee (not an associate of a current employee) is not exempt.")

    # LCT
    lct_series = figures.get("fbt.lct_threshold_fuel_efficient_by_year")
    lct_ok: bool | None = None
    threshold_used = None
    if inp.lct_payable is not None:
        lct_ok = not inp.lct_payable
        reasons.append("Luxury car tax was " + ("never payable." if lct_ok else "payable: not eligible."))
    elif inp.value_at_first_retail_sale is not None and inp.first_retail_sale_date is not None:
        for row in lct_series:
            if row["from"] <= inp.first_retail_sale_date <= row["to"]:
                threshold_used = row["rate"]
        if threshold_used is None:
            reasons.append("First retail sale date is outside the LCT threshold series held; confirm LCT status directly.")
        else:
            lct_ok = inp.value_at_first_retail_sale <= threshold_used
            reasons.append(f"Value at first retail sale {inp.value_at_first_retail_sale:,.2f} vs fuel-efficient LCT threshold "
                           f"{threshold_used:,.0f} for the year of sale: " + ("no LCT payable." if lct_ok else "LCT payable, not eligible."))
    else:
        reasons.append("Need lct_payable, or the value and date of first retail sale, to test luxury car tax.")
    conds["no_luxury_car_tax_payable"] = lct_ok

    vals = list(conds.values())
    exempt = False if any(v is False for v in vals) else (None if any(v is None for v in vals) else True)

    proposal = None
    try:
        proposal = {
            "status": "EXPOSURE DRAFT / ANNOUNCED - NOT LAW",
            "start_date": _d(figures.get("fbt.ev_proposal_start_date")).isoformat(),
            "base_value_limit": figures.get("fbt.ev_proposal_base_value_limit"),
            "discounted_statutory_rate_above_limit": figures.get("fbt.ev_proposal_discounted_statutory_rate"),
            "all_eligible_discounted_from": _d(figures.get("fbt.ev_proposal_full_discount_end_date")).isoformat(),
            "note": "Between the start date and the later date, cars at or under the base value limit would keep a nil statutory rate; "
                    "above it (below the LCT threshold) 15% would apply; existing arrangements would be grandfathered. Not enacted: current law "
                    "keeps the full exemption, so do not apply it to any FBT year.",
        }
        if benefit >= _d(figures.get("fbt.ev_proposal_start_date")):
            warnings.append("Benefit date is on or after the proposed 1 Apr 2027 change: current law still exempts an eligible car, but the "
                            "announced wind-back is not law and may change treatment (existing arrangements are proposed to be grandfathered).")
    except FigureError:
        pass
    if exempt:
        warnings.append("Exempt electric car benefits are still reportable: include the notional taxable value in the employee's reportable fringe benefits amount (FBTAA s 135P(3)).")
        warnings.append("Home charging cost can use the PCG 2024/2 cents per kilometre rate if eligible: "
                        f"{figures.get('fbt.ev_home_charging_rate_per_km')} per km for this FBT year.")
    return {**hdr, "exempt": exempt, "conditions": conds, "reasons": reasons, "benefit_date_tested": benefit.isoformat(),
            "lct_threshold_used": threshold_used, "law_status": "current law (FBTAA s 8A as in force)",
            "proposal_not_law": proposal,
            "assumptions": ["Tested against FBTAA s 8A as enacted; salary packaged benefits are included in the exemption."],
            "warnings": warnings}


# ---------------------------------------------------------------- work vehicle exemption (s 8(2))

class WorkVehicleInput(BaseModel):
    """Facts for the limited private use exemption for utes, vans and similar eligible vehicles."""

    vehicle_kind: Literal["single_cab_ute", "dual_cab_ute", "panel_van", "taxi", "four_wheel_drive",
                          "modified_vehicle", "other_load_1t_or_more_or_over_8_passengers", "passenger_car_or_other"]
    designed_load_tonnes: float | None = Field(None, ge=0, description="Designed load capacity (gross vehicle weight less kerb weight), tonnes.")
    designed_passengers_including_driver: int | None = Field(None, ge=1, description="Passengers the vehicle is designed to carry, including the driver.")
    designed_principally_to_carry_passengers: bool | None = Field(None, description="Dual cabs and four-wheel drives: True if designed principally to carry passengers (MT 2024, TD 94/19).")
    modification_permanently_changes_design: bool | None = Field(None, description="Modified vehicles: modification permanently affects the inherent design for the whole year.")
    other_private_use: Literal["none", "minor_infrequent_irregular", "more_than_minor"] = Field(
        "none", description="Private use other than home to work and incidental work travel.")
    associate_travelled_home_to_work: bool = Field(False, description="An associate of the employee travelled on the home to work trips (family school run).")
    policy_and_employee_assurance: bool | None = Field(None, description="PCG 2018/3: written private-use policy and an assurance from the employee.")
    wholly_private_km_total: float | None = Field(None, ge=0, description="PCG 2018/3: total kilometres of wholly private journeys in the FBT year (excluding home to work).")
    longest_private_return_trip_km: float | None = Field(None, ge=0, description="PCG 2018/3: longest wholly private return journey, km.")
    max_home_work_diversion_km: float | None = Field(None, ge=0, description="PCG 2018/3: longest diversion added to a home to work trip, km.")


@calculator("work_vehicle_exemption_check", WorkVehicleInput)
def work_vehicle_exemption_check(figures: Figures, inp: WorkVehicleInput) -> dict:
    """Test the ute and work vehicle exemption (FBTAA s 8(2) and s 47(6)): an eligible vehicle (single cab ute,
    panel van or goods van, taxi, dual cab or four-wheel drive not designed principally to carry passengers, or a
    vehicle designed for a load of one tonne or more or more than 8 passengers) is exempt only if private use
    is limited to home to work travel, incidental work travel and minor, infrequent and irregular use. Also checks the ATO's
    PCG 2018/3 safe harbour when its facts are given. Returns eligible, exempt, reasons, and what to do if not exempt
    (value as a car benefit with car_fringe_benefit_statutory or car_fringe_benefit_operating_cost, or as a residual
    benefit if the vehicle is not a car). Garaging at home counts as available for private use only if the vehicle is not eligible or the limits are breached."""
    km_cap = figures.get("fbt.pcg_2018_3_private_km_cap")
    trip_cap = figures.get("fbt.pcg_2018_3_single_trip_km_cap")
    div_cap = figures.get("fbt.pcg_2018_3_diversion_km_cap")
    reasons: list[str] = []
    k = inp.vehicle_kind
    load, pax = inp.designed_load_tonnes, inp.designed_passengers_including_driver
    eligible: bool | None
    if k in ("single_cab_ute", "panel_van", "taxi", "other_load_1t_or_more_or_over_8_passengers"):
        eligible = True
        reasons.append(f"{k} is an eligible vehicle type.")
    elif k in ("dual_cab_ute", "four_wheel_drive"):
        if (load is not None and load >= 1) or (pax is not None and pax > 8):
            eligible = True
            reasons.append("Designed for a load of one tonne or more or more than 8 passengers: eligible.")
        elif inp.designed_principally_to_carry_passengers is None:
            eligible = None
            reasons.append("Need whether the vehicle is designed principally to carry passengers (MT 2024, TD 94/19).")
        else:
            eligible = not inp.designed_principally_to_carry_passengers
            reasons.append("Designed principally to carry passengers: not eligible." if not eligible
                           else "Not designed principally to carry passengers: eligible.")
    elif k == "modified_vehicle":
        eligible = inp.modification_permanently_changes_design
        reasons.append("Modified vehicle: eligible only if the modification permanently affects the inherent design for the whole year (MT 2033)."
                       if eligible is None else ("Modification permanently changes design: eligible." if eligible
                                                  else "Modification does not permanently change design: not eligible."))
    else:
        eligible = False
        reasons.append("An ordinary passenger car or other vehicle is not an eligible vehicle: private use is a car fringe benefit.")

    pcg_facts = (inp.wholly_private_km_total, inp.longest_private_return_trip_km, inp.max_home_work_diversion_km)
    pcg_met: bool | None = None
    if inp.policy_and_employee_assurance is not None and None not in pcg_facts:
        pcg_met = (inp.policy_and_employee_assurance and inp.wholly_private_km_total <= km_cap
                   and inp.longest_private_return_trip_km <= trip_cap and inp.max_home_work_diversion_km <= div_cap)
        reasons.append("PCG 2018/3 safe harbour " + ("met." if pcg_met else "not met (policy and assurance, private kilometres, longest return trip and diversion limits)."))

    exempt: bool | None
    if eligible is False:
        exempt = False
    elif inp.associate_travelled_home_to_work:
        exempt = False
        reasons.append("An associate travelled on the home to work trips: the exemption is lost (current employee only).")
    elif inp.other_private_use == "more_than_minor" and not pcg_met:
        exempt = False
        reasons.append("Other private use is more than minor, infrequent and irregular (regular family use, school runs, weekend shopping).")
    elif eligible is None:
        exempt = None
    else:
        exempt = True
        reasons.append("Private use limited to home to work, incidental work travel and minor, infrequent and irregular use.")
    is_car = not (k == "other_load_1t_or_more_or_over_8_passengers" or (load is not None and load >= 1) or (pax is not None and pax >= 9))
    follow = None
    if exempt is False:
        follow = ("Value private use as a car fringe benefit (statutory formula or operating cost method)." if is_car
                  else "Not a 'car': value private use as a residual fringe benefit (FBT guide s 18.6); the exemption may still apply on the same limits.")
    return {**_year_header(figures), "eligible_vehicle": eligible, "exempt": exempt, "pcg_2018_3_safe_harbour_met": pcg_met,
            "pcg_limits": {"private_km_total": km_cap, "single_return_trip_km": trip_cap, "diversion_km": div_cap},
            "reasons": reasons, "if_not_exempt": follow,
            "assumptions": ["Use is by a current employee; the vehicle is registered and held by the employer."],
            "warnings": ["A car garaged at or near the employee's home is available for private use even if a policy forbids private use, so the exemption "
                         "depends on the actual use limits, not on policy alone."]}


# ---------------------------------------------------------------- car parking

class CarParkingInput(BaseModel):
    """Car parking fringe benefit for one employee for one FBT year."""

    days_parked: int = Field(ge=0, le=366, description="Days the employee parked for more than 4 hours between 7am and 7pm.")
    daily_value: float = Field(ge=0, description="Value of one day's parking under the valuation method chosen (for example the lowest "
                               "representative all-day fee of the nearest commercial parking station), GST-inclusive.")
    commercial_station_within_1km: bool = Field(description="A commercial parking station is within 1 km (shortest practicable route) of the employer's car park.")
    lowest_all_day_fee_first_day: float | None = Field(None, ge=0, description="Lowest representative all-day fee within 1 km on the first day of the FBT year.")
    lowest_all_day_fee_on_day: float | None = Field(None, ge=0, description="Same on the day of the benefit; default: same as first day.")
    parked_over_4_hours: bool = True
    drove_home_work_at_least_once: bool = True
    employee_has_disability_permit: bool = False
    employee_contributions: float = Field(0, ge=0, description="Amount the employee paid towards the parking for the year.")
    employer_type: EmployerType = "standard"
    prior_year_aggregated_turnover: float | None = Field(None, ge=0, description="Aggregated turnover for the last income year before the FBT year (small business test).")
    prior_year_gross_total_income: float | None = Field(None, ge=0, description="Gross total income for the last income year before the FBT year.")
    parking_in_commercial_car_park: bool = Field(False, description="Employees are parked in a commercial car park (blocks the small business exemption).")
    government_or_listed_company_group: bool = Field(False, description="Employer is a government body, a listed public company or its subsidiary.")


@calculator("car_parking_fringe_benefit", CarParkingInput)
def car_parking_fringe_benefit(figures: Figures, inp: CarParkingInput) -> dict:
    """Test and value a car parking fringe benefit (FBTAA s 39A). A benefit arises only if the employee parked for more
    than 4 hours between 7am and 7pm, drove home to work at least once, and a commercial parking station within 1 km
    charged an all-day fee ABOVE the car parking threshold on both the first day of the FBT year and the day of the
    benefit. Not provided: employees with a disability permit, and the small business employer exemption (prior-year
    aggregated turnover below the small business threshold, or gross total income below the alternative threshold, not
    in a commercial car park, not government or a listed company group). Taxable value = days x daily value less
    employee contributions. The chosen valuation method (market value, cost, commercial station rate etc.) is an input
    via daily_value. Refuses AU-FBT-001 for exempt and rebatable employers."""
    _check_employer(inp.employer_type)
    threshold = figures.get("fbt.car_parking_threshold")
    reasons: list[str] = []
    first = inp.lowest_all_day_fee_first_day
    day = inp.lowest_all_day_fee_on_day if inp.lowest_all_day_fee_on_day is not None else first
    small: bool | None = None
    t_lim = figures.get("fbt.small_business_turnover_threshold")
    g_lim = figures.get("fbt.small_business_gross_income_threshold")
    if inp.prior_year_aggregated_turnover is not None or inp.prior_year_gross_total_income is not None:
        size_ok = ((inp.prior_year_aggregated_turnover is not None and inp.prior_year_aggregated_turnover < t_lim)
                   or (inp.prior_year_gross_total_income is not None and inp.prior_year_gross_total_income < g_lim))
        small = size_ok and not inp.parking_in_commercial_car_park and not inp.government_or_listed_company_group
        reasons.append("Small business car parking exemption " + ("applies." if small else "does not apply."))
    exempt_reason = None
    if inp.employee_has_disability_permit:
        exempt_reason = "employee_disability_permit"
    elif small:
        exempt_reason = "small_business_exemption"
    arises: bool | None
    if not inp.commercial_station_within_1km:
        arises = False
        reasons.append("No commercial parking station within 1 km: no car parking fringe benefit.")
    elif first is None:
        arises = None
        reasons.append("Need the lowest representative all-day fee within 1 km on the first day of the FBT year.")
    else:
        fee_ok = first > threshold and (day is None or day > threshold)
        arises = fee_ok and inp.parked_over_4_hours and inp.drove_home_work_at_least_once
        reasons.append(f"All-day fee {first:,.2f} vs car parking threshold {threshold}: " + ("above." if first > threshold else "not above."))
        if not inp.parked_over_4_hours:
            reasons.append("Car not parked for more than 4 hours: no benefit.")
        if not inp.drove_home_work_at_least_once:
            reasons.append("Employee did not drive between home and work at least once that day: no benefit.")
    gross = inp.days_parked * inp.daily_value
    tv = 0.0
    if arises and not exempt_reason:
        tv = max(0.0, gross - inp.employee_contributions)
    return {**_year_header(figures), "car_parking_threshold": threshold, "benefit_arises": arises, "exempt_reason": exempt_reason,
            "gross_value": _r(gross), "employee_contributions": _r(inp.employee_contributions), "taxable_value": _r(tv),
            "reasons": reasons,
            "assumptions": ["daily_value is the value of one day's parking under the valuation method chosen for the year; the taxable value method is elected annually."],
            "warnings": ["A small parking amount may also qualify as a minor benefit; the 5 valuation methods have their own record requirements."]}


# ---------------------------------------------------------------- meal entertainment

class MealEntertainmentInput(BaseModel):
    """Meal entertainment valuation for one employer and FBT year (simple methods only)."""

    method: Literal["50_50", "twelve_week_register"]
    total_meal_entertainment_expenditure: float = Field(ge=0, description="Total GST-inclusive spend on meal entertainment for ALL people (employees, associates, clients) in the FBT year.")
    register_employee_and_associate_value: float | None = Field(None, ge=0, description="Register method: value of meal entertainment for employees and associates in the 12-week register.")
    register_total_value: float | None = Field(None, gt=0, description="Register method: value of all meal entertainment in the 12-week register.")
    special_circumstances: list[SpecialCircumstance] = Field(default_factory=list, description="recreation_entertainment, entertainment_facility_leasing or salary_packaged_meal_entertainment stop the calculation.")
    gross_up_type: Literal[1, 2] | None = None
    employer_type: EmployerType = "standard"

    @model_validator(mode="after")
    def _register_fields(self):
        if self.method == "twelve_week_register" and (self.register_employee_and_associate_value is None or self.register_total_value is None):
            raise ValueError("register_employee_and_associate_value and register_total_value are required for the 12-week register method")
        return self


@calculator("meal_entertainment_taxable_value", MealEntertainmentInput)
def meal_entertainment_taxable_value(figures: Figures, inp: MealEntertainmentInput) -> dict:
    """Taxable value of meal entertainment fringe benefits under the two simple elections: 50:50 split (50% of total
    meal entertainment spend on all people) or the 12-week register (register percentage = employee and associate
    value / total value in the register, applied to total spend). Both methods tax spend on clients and switch off the
    minor benefit and on-premises exemptions; the actual method (only what employees and associates received) is the
    alternative not computed here. Refuses AU-FBT-004 for recreation, entertainment facility leasing or salary-packaged
    meal entertainment, AU-FBT-001 for NFP employers with entertainment caps. Elections are made by the return due date."""
    _check_employer(inp.employer_type)
    _check_special(inp.special_circumstances)
    total = inp.total_meal_entertainment_expenditure
    if inp.method == "50_50":
        share = figures.get("fbt.meal_entertainment_split_rate")
        pct_note = "50:50 split method"
    else:
        a, b = inp.register_employee_and_associate_value, inp.register_total_value
        share = min(a / b, 1.0)
        pct_note = "12-week register method"
    tv = total * share
    out = {**_year_header(figures), "method": inp.method, "share_applied": round(share, 6), "taxable_value": _r(tv),
           "assumptions": [f"{pct_note}; spend includes amounts that would otherwise be exempt or not taxed.",
                           "The register must cover a continuous 12 weeks that is representative of the year.",
                           "Confirm the gross-up type: type 1 only where the employer is entitled to a GST credit on the entertainment."],
           "warnings": ["Compare with the actual method: it can be lower where much spend is on clients or exempt on-premises benefits."]}
    out.update(_gross_up_block(figures, out["taxable_value"], inp.gross_up_type))
    return out


# ---------------------------------------------------------------- minor benefit screen

class MinorBenefitInput(BaseModel):
    """Facts for the minor benefits exemption (FBTAA s 58P) for one benefit."""

    notional_taxable_value: float = Field(ge=0, description="Notional taxable value of this benefit in the FBT year (value if it were taxable; for a car, as if a residual benefit).")
    frequent_or_regular: bool = Field(False, description="Identical or similar or connected benefits are provided often or on a regular basis.")
    similar_benefits_total_notional_value: float | None = Field(None, ge=0, description="Sum of notional taxable values of this and identical or similar benefits, this and other years.")
    associated_benefits_total_notional_value: float = Field(0, ge=0, description="Sum of notional taxable values of other benefits provided in connection with this one.")
    principally_remuneration: bool = Field(False, description="Provided as a reward for services, under a salary packaging arrangement, or otherwise principally in the nature of pay.")
    unexpected_event: bool = Field(False, description="Provided because of an unexpected event (unplanned overtime, taxi after a cancelled flight).")
    hard_to_value_or_record: bool = Field(False, description="Practically difficult to determine value or keep records.")
    provided_to_associate: bool = Field(False, description="Benefit provided to an associate (their value is not counted against the employee threshold test).")


@calculator("minor_benefit_screen", MinorBenefitInput)
def minor_benefit_screen(figures: Figures, inp: MinorBenefitInput) -> dict:
    """Screen a benefit against the minor benefits exemption (FBTAA s 58P, TR 2007/12): (1) notional taxable value
    must be LESS than the minor benefit threshold, tested per benefit not as a total; (2) it must also be unreasonable
    to treat it as a fringe benefit, weighing frequency and regularity, total of similar benefits, associated
    benefits, practical difficulty and circumstances. Returns the threshold result, each factor, and likely_exempt
    (True only if the threshold is met and no factor points against it). This is a screen: the second limb is a
    judgement the employer must be able to support; regular or salary-packaged benefits usually fail."""
    thr = figures.get("fbt.minor_benefit_threshold")
    below = inp.notional_taxable_value < thr
    factors = {
        "frequency_and_regularity": "against" if inp.frequent_or_regular else "for",
        "similar_benefits_total": ("against" if (inp.similar_benefits_total_notional_value or 0) >= thr else "for"),
        "associated_benefits_total": ("against" if inp.associated_benefits_total_notional_value >= thr else "for"),
        "practical_difficulty": "for" if inp.hard_to_value_or_record else "neutral",
        "circumstances": "against" if inp.principally_remuneration else ("for" if inp.unexpected_event else "neutral"),
    }
    against = [k for k, v in factors.items() if v == "against"]
    likely = below and not against
    reasons = [f"Notional taxable value {inp.notional_taxable_value:,.2f} is " + ("below" if below else "not below") + f" the threshold {thr:,.0f}."]
    if against:
        reasons.append("Factors pointing to treating it as a fringe benefit: " + ", ".join(against) + ".")
    return {**_year_header(figures), "threshold": thr, "below_threshold": below, "factors": factors, "likely_exempt": likely,
            "judgement_required": below, "reasons": reasons,
            "assumptions": ["A benefit exactly at the threshold fails the first limb (it must be less than).",
                            "Each separate benefit is tested individually; the threshold is not a cap on the total minor benefits an employee can receive."],
            "warnings": ["Passing the screen is not a determination: the employer must be able to support the 'unreasonable to treat as a fringe benefit' conclusion."]}
