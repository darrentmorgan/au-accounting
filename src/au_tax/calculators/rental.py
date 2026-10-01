"""Residential rental property for individuals who are not in business: rental income and deductions,
private-use apportionment (TR 2026/1, PCG 2026/2), holiday homes (ITAA 1997 s 26-50, PCG 2026/3),
borrowing expenses (s 25-25), depreciation (Div 40, incl. s 40-27), capital works (Div 43), the travel
and vacant land denials (ss 26-31, 26-102) and the residential dwelling loss quarantine (ss 26-155,
26-160) which applies from the 2027-28 income year.

Every rate, date and threshold comes from data/rates/<year>.d/rental.yaml via Figures.
"""

from __future__ import annotations

import calendar
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from au_tax.figures import Figures
from au_tax.registry import Refusal, calculator, refusal_catalogue


# ---------------------------------------------------------------- helpers

def _r(x: float) -> float:
    return round(x + 0.0, 2)


def _ymd(n: int | float) -> date:
    n = int(n)
    return date(n // 10000, (n // 100) % 100, n % 100)


def _year_bounds(figures: Figures) -> tuple[date, date]:
    meta = figures.data.get("meta", {})
    start, end = meta.get("start"), meta.get("end")
    if isinstance(start, date) and isinstance(end, date):
        return start, end
    y = int(figures.income_year[:4])
    return date(y, 7, 1), date(y + 1, 6, 30)


def _days_in_year(figures: Figures) -> int:
    s, e = _year_bounds(figures)
    return (e - s).days + 1


def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    y = d.year + m // 12
    m = m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def _series_rate(series: list[dict], on: date) -> float:
    """Rate whose (inclusive) date range contains `on`; 0 when the date is before the first range."""
    for item in series:
        if item["from"] <= on <= item["to"]:
            return float(item["rate"])
    return 0.0


def quarantine_step(deductions: float, income: float, brought_forward: float = 0.0,
                    other_exempt_net_income: float = 0.0) -> dict:
    """ITAA 1997 s 26-155(1) and (6): excess of (deductions plus amounts brought forward) over assessable
    income from quarantined residential dwellings, reduced by the net income of exempt dwellings
    (s 26-155(6)(a)). The excess is not deductible and is carried forward (s 26-155(1)(a) and (c);
    the method-statement offset against net capital gains is not modelled)."""
    total = deductions + brought_forward
    excess = max(0.0, total - income)
    excess = max(0.0, excess - max(0.0, other_exempt_net_income))
    return {"deductible": total - excess, "quarantined_carried_forward": excess}


def pcg_2026_2_factors(days_rented: int | None, days_available: int | None, period: int, part_of_home: bool,
                       area_exclusive: float | None, area_shared: float | None,
                       area_total: float | None) -> tuple[float, float, list[str]]:
    """PCG 2026/2 apportionment factors, shared with the short-stay skill so there is one implementation.
    Time factor = (days used to produce income + days held to produce income) / days in the period; a room or part of
    the home has no held days (para 15). Area factor = (area exclusive to the tenant + half the shared areas) / total area
    (paras 29-32). Returns (time_factor, area_factor, notes); notes starting "Part of your home" are warnings."""
    notes: list[str] = []
    avail = days_available
    if part_of_home and avail:
        notes.append("Part of your home is let, so unoccupied days count as private use: days available on commercial terms set to nil (PCG 2026/2 para 15).")
        avail = 0
    if days_rented is None and avail is None:
        time_f = 1.0
        notes.append("Rented or available on commercial terms for the whole period; no private use, so no time apportionment.")
    else:
        time_f = min(1.0, ((days_rented or 0) + (avail or 0)) / period)
    if area_total is not None:
        area_f = ((area_exclusive or 0) + (area_shared or 0) / 2) / area_total
    else:
        area_f = 1.0
    return time_f, area_f, notes


# ---------------------------------------------------------------- capital works (Div 43)

CapitalWorksUse = Literal["residential", "traveller_accommodation", "structural_improvement", "non_residential"]


class CapitalWorksInput(BaseModel):
    """One set of construction costs for Div 43 capital works in an income-producing property."""

    construction_cost: float = Field(gt=0, description="Construction cost (not the purchase price, insured or replacement cost). "
                                     "Owner-builder labour and notional profit are excluded.")
    construction_start_date: date = Field(description="Date construction began (ITAA 1997 s 43-80); sets the rate.")
    construction_completion_date: date | None = Field(
        None, description="Date construction was completed. Deductions start only once construction is complete.")
    use_type: CapitalWorksUse = Field(
        "residential", description="residential = building intended for residential use or to produce income; "
        "traveller_accommodation = short-term traveller accommodation (apartment building or hotel, motel, guest house); "
        "structural_improvement = fence, driveway, retaining wall etc; non_residential = shop or office (refused).")
    units_or_bedrooms_held: int | None = Field(
        None, ge=0, description="For traveller_accommodation: apartment units or flats you own or lease in the building, or "
        "bedrooms in the hotel, motel or guest house. Below the minimum, the residential rate applies.")
    days_income_producing: int | None = Field(
        None, ge=0, le=366, description="Days in the income year the property was used or held for income-producing purposes "
        "(and owned). Defaults to every day of the year from the later of 1 July and completion.")
    previously_deducted_or_undeducted: float | None = Field(
        None, ge=0, description="Undeducted construction expenditure remaining (cost less prior years' deductions); caps the claim "
        "(ITAA 1997 s 43-15(1)).")
    pre_16_sep_1987_contract: bool = Field(
        False, description="Construction relates to certain contracts entered into before 16 September 1987 (special 4% rate). "
        "Not modelled: refused with AU-RENT-004.")
    holiday_home_denied_s26_50: bool = Field(
        False, description="The property is a holiday home and s 26-50 denies ownership costs; capital works are then nil.")
    ownership_percent: float = Field(100, gt=0, le=100, description="Your legal ownership share (co-owners claim by title).")


def _capital_works(figures: Figures, inp: CapitalWorksInput, days: int | None, assumptions: list[str],
                   warnings: list[str]) -> dict:
    """Core Div 43 arithmetic for one item. `days` is the income-producing days already limited to the period owned."""
    if inp.use_type == "non_residential":
        raise Refusal("AU-RENT-001", "non-residential (commercial) building")
    if inp.pre_16_sep_1987_contract:
        raise Refusal("AU-RENT-004", "certain pre-16 September 1987 contracts change the rate; not modelled")
    ys, ye = _year_bounds(figures)
    diy = (ye - ys).days + 1
    start = inp.construction_start_date
    use = inp.use_type
    if use == "traveller_accommodation":
        need = figures.get("rental.capital_works_traveller_minimum_units")
        if inp.units_or_bedrooms_held is None:
            raise Refusal("AU-RENT-004", "units or bedrooms held not given for traveller accommodation")
        if inp.units_or_bedrooms_held >= need:
            rate = _series_rate(figures.get("rental.capital_works_rate_traveller_accommodation"), start)
            basis = "traveller accommodation (10 or more units or bedrooms)"
        else:
            rate = _series_rate(figures.get("rental.capital_works_rate_residential"), start)
            basis = "residential (below the traveller accommodation minimum of units or bedrooms)"
            assumptions.append("Fewer units or bedrooms than the traveller-accommodation minimum, so the residential rate applies; "
                               "a single short-stay dwelling is residential for Div 43.")
    elif use == "structural_improvement":
        rate = _series_rate(figures.get("rental.capital_works_rate_structural_improvement"), start)
        basis = "structural improvement"
    else:
        rate = _series_rate(figures.get("rental.capital_works_rate_residential"), start)
        basis = "residential or income-producing building"
    if rate == 0.0:
        warnings.append("Construction began before the earliest date for this type of work, so no capital works deduction is available.")
    # days available to claim
    avail = days if days is not None else diy
    comp = inp.construction_completion_date
    if comp is not None and comp > ys:
        if comp > ye:
            avail = 0
            warnings.append("Construction was not complete by the end of the income year; no deduction until completion.")
        else:
            avail = min(avail, (ye - comp).days + 1)
    full_year = inp.construction_cost * rate
    amount = full_year * avail / diy
    capped = False
    if inp.previously_deducted_or_undeducted is not None and amount > inp.previously_deducted_or_undeducted:
        amount, capped = inp.previously_deducted_or_undeducted, True
    return {"rate": rate, "basis": basis, "annual_full_year_amount": full_year, "days_claimed": avail,
            "days_in_income_year": diy, "amount": amount, "capped_at_undeducted": capped,
            "years_of_claim": (round(1 / rate) if rate else 0)}


@calculator("capital_works_deduction", CapitalWorksInput)
def capital_works_deduction(figures: Figures, inp: CapitalWorksInput) -> dict:
    """Division 43 capital works deduction (building, structural improvement or initial repairs treated as capital works)
    for one income year: construction cost x rate for the date construction began x days claimed / days in the income
    year. Rate is 2.5% for residential and income-producing buildings begun on or after 16 Sep 1987 (4% for 18 Jul 1985 to
    15 Sep 1987) and 4% only for short-term traveller accommodation in an apartment building or hotel, motel or guest
    house with 10 or more units or bedrooms owned or leased (works begun 27 Feb 1992 onward). Inputs: construction
    cost, start date, optional completion date, use type, units or bedrooms held, days income-producing, undeducted
    balance, s 26-50 denial flag and ownership percent. Use for capital works on a rental property, including short-stay
    stock; a single Airbnb-style house or unit is residential at the general rate. Refuses AU-RENT-001 for commercial
    buildings and AU-RENT-004 when the construction dates or contract history cannot be verified."""
    assumptions: list[str] = []
    warnings: list[str] = []
    res = _capital_works(figures, inp, inp.days_income_producing, assumptions, warnings)
    share = inp.ownership_percent / 100
    amount = res["amount"] * share
    denied = False
    if inp.holiday_home_denied_s26_50:
        denied, amount = True, 0.0
        warnings.append("s 26-50 denies capital works on a holiday home that is not used or held mainly to produce rent.")
    if share < 1:
        assumptions.append(f"Deduction is your {inp.ownership_percent:g} per cent legal-title share.")
    assumptions.append("Construction cost is the actual cost (or a quantity surveyor estimate), not the purchase price; "
                       "claimed amounts reduce the CGT cost base.")
    return {
        "capital_works_deduction": _r(amount),
        "rate": res["rate"],
        "rate_basis": res["basis"],
        "annual_full_year_amount": _r(res["annual_full_year_amount"] * share),
        "days_claimed": res["days_claimed"],
        "days_in_income_year": res["days_in_income_year"],
        "capped_at_undeducted_balance": res["capped_at_undeducted"],
        "denied_by_s26_50": denied,
        "claim_period_years": res["years_of_claim"],
        "assumptions": assumptions,
        "warnings": warnings,
    }


# ---------------------------------------------------------------- rental property result

class BorrowingExpense(BaseModel):
    """Borrowing expenses (loan establishment, mortgage stamp duty, valuation, LMI billed to you) for one loan."""

    description: str = ""
    amount: float = Field(gt=0, description="Total borrowing expenses incurred for the loan.")
    loan_start_date: date = Field(description="First day money was borrowed.")
    loan_term_months: int | None = Field(None, gt=0, description="Contract term in months; over 60 months is treated as 60.")
    loan_repaid_date: date | None = Field(None, description="Date the loan was repaid, if repaid early.")
    previously_deducted: float = Field(0, ge=0, description="Maximum amounts already worked out for earlier income years "
                                       "(before any private-purpose share).")
    rental_share_of_loan: float = Field(1.0, ge=0, le=1, description="Fraction of the borrowing used for the rental property.")


class DepreciatingAsset(BaseModel):
    """A depreciating asset (Div 40) in the rental property, such as carpet, an oven or a dishwasher."""

    description: str = ""
    cost: float = Field(gt=0)
    effective_life_years: float = Field(gt=0, description="Effective life: the Commissioner's determination (Income Tax "
                                        "(Effective Life of Depreciating Assets) Determination 2025) or your own estimate.")
    method: Literal["prime_cost", "diminishing_value"] = "prime_cost"
    days_held: int | None = Field(None, ge=0, le=366, description="Days held in the year, from when the asset was first used or installed "
                                  "ready for use. Defaults to the days in the ownership period.")
    opening_adjustable_value: float | None = Field(
        None, ge=0, description="Opening adjustable value for a later year (base value for diminishing value; caps prime cost). "
        "Omit in the first year, when the base is the cost.")
    second_hand: bool = Field(False, description="Not new when you started to hold it (was in the property when you bought it, "
                              "or was previously used, including in your own home).")
    acquired_date: date | None = Field(None, description="Date acquired (contract date), for second-hand assets.")
    installed_date: date | None = Field(None, description="Date first installed ready for use at the rental, for second-hand assets.")
    new_residential_premises_exception: bool = Field(
        False, description="Asset supplied as part of new residential premises and meeting s 40-27(4) or (5); you have confirmed this.")
    part_of_set_over_low_cost_limit: bool = Field(
        False, description="Part of a set, or one of identical assets, whose total cost exceeds the low-cost limit.")


class Expenses(BaseModel):
    """Expenses for the whole property for the period, in AUD. Leave unused fields at zero."""

    # direct letting expenses: deductible in full (PCG 2026/2 paras 10-12)
    agent_fees: float = Field(0, ge=0, description="Letting and management fees to an agent.")
    platform_fees: float = Field(0, ge=0, description="Sharing-economy platform commissions and service fees.")
    advertising: float = Field(0, ge=0, description="Advertising for tenants or guests.")
    guest_cleaning_and_linen: float = Field(0, ge=0, description="Cleaning and laundering relating to paying guest stays only.")
    other_direct_letting: float = Field(0, ge=0, description="Other costs that relate only to letting (tenant checks, lease preparation).")
    # ownership and use expenses: apportioned; denied for a holiday home outside the s 26-50 exception
    interest: float = Field(0, ge=0, description="Interest on loans, before removing any non-rental purpose share.")
    interest_non_rental_share: float = Field(0, ge=0, le=1, description="Fraction of the interest relating to money used for a "
                                             "non-rental purpose (private redraws, split loan private part); TR 2000/2.")
    council_rates: float = Field(0, ge=0)
    water_charges: float = Field(0, ge=0, description="Water charges you (not the tenant) bear.")
    land_tax: float = Field(0, ge=0)
    insurance: float = Field(0, ge=0, description="Landlord or building and contents insurance.")
    strata_body_corporate: float = Field(0, ge=0, description="Ordinary body corporate levies (administration and sinking fund for "
                                         "repairs). Capital-works levies are entered under capital_improvements.")
    repairs_maintenance: float = Field(0, ge=0, description="Repairs and maintenance for wear and tear or damage that happened "
                                       "while rented or available for rent (TR 97/23).")
    gardening_pest_control: float = Field(0, ge=0)
    bank_fees_other_ownership: float = Field(0, ge=0, description="Other ownership costs such as bank account fees and lease document costs.")
    # denied or capital items: reported, never deducted immediately
    travel: float = Field(0, ge=0, description="Travel to inspect, maintain or collect rent (denied, s 26-31).")
    initial_repairs: float = Field(0, ge=0, description="Repairs to damage or defects that existed when you acquired the property (capital).")
    capital_improvements: float = Field(0, ge=0, description="Improvements, renovations and replacements of an entirety (capital works or depreciating assets).")
    purchase_and_sale_costs: float = Field(0, ge=0, description="Stamp duty on the transfer, conveyancing and other acquisition or sale costs (CGT).")


OwnerType = Literal["individual", "company", "trust", "partnership", "smsf"]
DwellingKind = Literal["house_unit_apartment_or_similar", "caravan_or_mobile_home",
                       "hotel_motel_inn_hostel_boarding_house", "student_accommodation", "boat_or_vessel"]


class CapitalWorksItem(BaseModel):
    """Capital works item inside rental_property_result (days come from the ownership period)."""

    description: str = ""
    construction_cost: float = Field(gt=0)
    construction_start_date: date
    construction_completion_date: date | None = None
    use_type: CapitalWorksUse = "residential"
    units_or_bedrooms_held: int | None = Field(None, ge=0)
    undeducted_construction_expenditure: float | None = Field(None, ge=0)
    pre_16_sep_1987_contract: bool = False


class RentalInput(BaseModel):
    """One residential rental property (whole-property amounts for the period) owned by an individual who is not in business."""

    owner_type: OwnerType = Field("individual", description="Anything other than individual is refused (AU-RENT-001).")
    property_type: Literal["residential", "commercial"] = "residential"
    property_location: Literal["australia", "overseas"] = Field("australia", description="Overseas is refused (AU-RENT-005).")
    short_stay: bool = Field(False, description="Let mainly on a short-term (Airbnb-style) basis rather than long-term tenancies.")
    carrying_on_rental_business: bool = Field(
        False, description="Indicators of a rental business (large portfolio, substantial services, systematic activity): refused.")
    property_development_or_resale: bool = Field(False, description="Bought to renovate and sell, subdivide or develop: refused.")
    mixed_use_with_business: bool = Field(False, description="Used for a business as well (home office business, farm, shop and flat): refused.")
    ownership_percent: float = Field(100, gt=0, le=100, description="Your legal-title share; the result is your share (TR 2026/1 para 22).")

    gross_rent: float = Field(0, ge=0, description="Rent and platform income received or due, before agent and platform fees, excluding GST.")
    other_rental_income: float = Field(0, ge=0, description="Other rental-related income: retained bond, insurance payouts for lost rent, "
                                       "reimbursements of deductions.")
    expenses: Expenses = Field(default_factory=Expenses)
    borrowing_expenses: list[BorrowingExpense] = Field(default_factory=list)
    depreciating_assets: list[DepreciatingAsset] = Field(default_factory=list)
    capital_works: list[CapitalWorksItem] = Field(default_factory=list)
    capital_works_amount_from_schedule: float = Field(
        0, ge=0, description="Div 43 capital works deduction for the period already worked out, for example from a quantity surveyor's "
        "schedule. Use this when you have the annual amount but not the construction cost and start date; it is apportioned like other "
        "ownership costs. Do not also enter the same works under capital_works.")

    days_in_period: int | None = Field(None, ge=1, le=366, description="Days in the period being apportioned: the whole income year, or the "
                                       "period owned or since a clear change in use. Defaults to the income year.")
    days_rented: int | None = Field(None, ge=0, le=366, description="Days actually let (including days paid for but not occupied). "
                                    "Omit if let or available all period.")
    days_available_commercial_terms: int | None = Field(
        None, ge=0, le=366, description="Days unoccupied but genuinely available for rent on commercial terms (broad advertising, "
        "market rent, requests monitored). Not days blocked for private use or advertised only to friends.")
    part_of_home: bool = Field(False, description="Only a room or part of your home is let; unoccupied days then count as private (PCG 2026/2 para 15).")
    area_exclusive_to_tenant: float | None = Field(None, ge=0, description="Floor area solely occupied by the tenant.")
    area_shared_common: float | None = Field(None, ge=0, description="Floor area of common areas shared with the tenant.")
    area_total: float | None = Field(None, gt=0, description="Floor area of the whole property.")
    non_arms_length_rent: bool = Field(False, description="Rent charged to family or friends below market. Deductions are limited to the rent "
                                       "received (PCG 2026/2 para 44), giving no loss.")

    holiday_home: bool = Field(False, description="The property is used or held for use for your (or associates') holidays or recreation "
                               "at no rent or reduced rent, as well as being rented.")
    holiday_home_mainly_for_rent: Literal["yes", "no", "unresolved"] | None = Field(
        None, description="Only when holiday_home: is it, at all times in the year, used or held for use mainly to produce rent (s 26-50(3)(b)(ii); "
        "PCG 2026/3 green zone = yes, red zone = no). unresolved is refused (AU-RENT-003).")
    vacant_land: bool = Field(False, description="Land with no substantial and permanent building in use or available (or a newly built or renovated "
                              "dwelling not yet lawfully occupiable and let). Holding costs denied from 1 Jul 2019 (s 26-102).")

    dwelling_kind: DwellingKind = "house_unit_apartment_or_similar"
    acquisition_date: date | None = Field(None, description="Date you last acquired your ownership interest (contract date if bought under contract).")
    acquired_before_730pm_on_cutoff_day: bool | None = Field(
        None, description="Only if acquisition_date is the grandfathering cut-off day: acquired before 7.30 pm ACT time.")
    claims_new_residential_dwelling: bool = Field(False, description="You believe the dwelling is a new residential dwelling.")
    preview_quarantine_from_2027_28: bool = Field(
        False, description="Also show what the same result would mean under the loss quarantine that applies from 2027-28.")
    quarantined_brought_forward: float = Field(0, ge=0, description="Quarantined amount carried forward (previews only).")
    other_exempt_dwellings_net_income: float = Field(0, ge=0, description="Net rental income from your other exempt residential dwellings "
                                                     "(s 26-155(6)(a)); previews only.")

    @model_validator(mode="after")
    def _consistent(self):
        if self.area_total is not None:
            a = (self.area_exclusive_to_tenant or 0) + (self.area_shared_common or 0)
            if a > self.area_total:
                raise ValueError("tenant and common areas exceed the total area")
        elif self.area_exclusive_to_tenant is not None or self.area_shared_common is not None:
            raise ValueError("area_total is required with the area fields")
        if (self.days_rented or 0) + (self.days_available_commercial_terms or 0) > (self.days_in_period or 366):
            raise ValueError("days rented plus days available exceed days in period")
        if self.holiday_home and self.holiday_home_mainly_for_rent is None:
            raise ValueError("holiday_home_mainly_for_rent is required when holiday_home is true")
        return self


def _borrowing(figures: Figures, be: BorrowingExpense) -> dict:
    """ITAA 1997 s 25-25(4)-(6): remaining expenditure / remaining loan days x days of the period in the income year."""
    ys, ye = _year_bounds(figures)
    max_years = int(figures.get("rental.borrowing_expense_max_years"))
    months = min(be.loan_term_months or max_years * 12, max_years * 12)
    end = _add_months(be.loan_start_date, months) - timedelta(days=1)
    if be.loan_repaid_date is not None:
        end = min(end, be.loan_repaid_date)
    first = max(ys, be.loan_start_date)
    incurred_this_year = ys <= be.loan_start_date <= ye
    limit = figures.get("rental.borrowing_expense_immediate_limit")
    if incurred_this_year and be.amount <= limit:
        return {"maximum_for_year": be.amount, "deductible": be.amount * be.rental_share_of_loan,
                "method": "immediate (total not above the borrowing expense limit)"}
    remaining = max(0.0, be.amount - be.previously_deducted)
    last = min(ye, end)
    days_in_year_part = max(0, (last - first).days + 1)
    remaining_days = max(0, (end - first).days + 1)
    max_for_year = remaining * days_in_year_part / remaining_days if remaining_days else 0.0
    return {"maximum_for_year": max_for_year, "deductible": max_for_year * be.rental_share_of_loan,
            "period_ends": end.isoformat(), "days_in_year_part": days_in_year_part, "remaining_loan_days": remaining_days,
            "method": "spread over the loan period, at most 5 years"}


def _asset(figures: Figures, a: DepreciatingAsset, default_days: int, assumptions: list[str],
           warnings: list[str]) -> tuple[float, str]:
    """Decline in value before apportionment; returns (amount, note)."""
    ys, ye = _year_bounds(figures)
    diy = (ye - ys).days + 1
    if a.second_hand and not a.new_residential_premises_exception:
        acq_cut, inst_cut = _ymd(figures.get("rental.second_hand_asset_acquired_before")), _ymd(figures.get("rental.second_hand_asset_installed_before"))
        ok = (a.acquired_date is not None and a.installed_date is not None
              and a.acquired_date < acq_cut and a.installed_date < inst_cut)
        if not ok:
            if a.acquired_date is None or a.installed_date is None:
                warnings.append(f"Second-hand asset '{a.description}': dates not given, so treated as acquired at or after 7.30 pm on 9 May 2017; "
                                "give the acquisition and installation dates if it was earlier.")
            return 0.0, "denied: second-hand asset in residential rental (s 40-27)"
    low = figures.get("rental.low_cost_asset_immediate_deduction_limit")
    if a.opening_adjustable_value is None and a.cost <= low and not a.part_of_set_over_low_cost_limit:
        return a.cost, "immediate deduction (cost within the low-cost limit, s 40-80(2))"
    days = a.days_held if a.days_held is not None else default_days
    if a.method == "diminishing_value":
        base = a.opening_adjustable_value if a.opening_adjustable_value is not None else a.cost
        amt = min(base, base * days / diy * figures.get("rental.diminishing_value_factor") / a.effective_life_years)
        return amt, "diminishing value"
    amt = a.cost * days / diy / a.effective_life_years
    if a.opening_adjustable_value is not None:
        amt = min(amt, a.opening_adjustable_value)
    return amt, "prime cost"


def _negative_gearing(figures: Figures, inp: RentalInput, income: float, deductions: float,
                      warnings: list[str], assumptions: list[str]) -> tuple[dict, float | None]:
    """Returns (block for output, quarantined-adjusted net result or None when quarantine does not apply this year)."""
    first_year = int(figures.get("rental.negative_gearing_first_income_year"))
    cutoff = _ymd(figures.get("rental.negative_gearing_grandfather_date"))
    ys, _ = _year_bounds(figures)
    applies = ys.year >= first_year
    block: dict = {"applies_this_year": applies, "first_income_year_affected": f"{first_year}-{str(first_year + 1)[-2:]}",
                   "grandfather_cutoff": f"{cutoff.isoformat()} 7.30 pm ACT time"}
    if inp.dwelling_kind != "house_unit_apartment_or_similar":
        block["status"] = "not a residential dwelling (excluded kind, s 26-160(1))"
        return block, None
    # status
    if inp.claims_new_residential_dwelling:
        status = "new_residential_dwelling_claimed"
    elif inp.acquisition_date is None:
        status = "acquisition_date_not_given"
    elif inp.acquisition_date < cutoff:
        status = "grandfathered"
    elif inp.acquisition_date > cutoff:
        status = "subject_to_quarantine"
    elif inp.acquired_before_730pm_on_cutoff_day is None:
        status = "cutoff_day_time_not_given"
    else:
        status = "grandfathered" if inp.acquired_before_730pm_on_cutoff_day else "subject_to_quarantine"
    block["status"] = status
    block["new_residential_dwelling_instrument"] = ("not made: the exception under s 26-155(2)(b) cannot be assessed until the "
                                                    "Minister determines requirements under s 26-160(4)")
    needs_answer = applies or inp.preview_quarantine_from_2027_28
    if needs_answer and status in ("new_residential_dwelling_claimed", "acquisition_date_not_given", "cutoff_day_time_not_given"):
        if status == "new_residential_dwelling_claimed":
            raise Refusal("AU-RENT-002", "new residential dwelling exception depends on an instrument that has not been made")
        raise Refusal("AU-RENT-002", "acquisition date needed to decide whether the dwelling is grandfathered")
    if status == "new_residential_dwelling_claimed":
        warnings.append("New residential dwelling status cannot be assessed (ministerial instrument not made). No effect on this income year.")
    net_income = income - deductions
    if applies and status == "subject_to_quarantine":
        q = quarantine_step(deductions, income, inp.quarantined_brought_forward, inp.other_exempt_dwellings_net_income)
        block["quarantined_carried_forward"] = _r(q["quarantined_carried_forward"])
        return block, income - q["deductible"]
    if applies:
        return block, None
    # not applicable this year: note and optional preview
    if status == "subject_to_quarantine":
        block["note"] = ("No quarantine in this income year: the rule applies from the 2027-28 income year. From 2027-28 a loss on this dwelling "
                         "would not be deductible against other income and would carry forward against future residential rental income.")
    elif status == "grandfathered":
        block["note"] = "Acquired before the cut-off, so not quarantined in any year (s 26-155(2)(a))."
    if inp.preview_quarantine_from_2027_28 and status == "subject_to_quarantine":
        q = quarantine_step(deductions, income, inp.quarantined_brought_forward, inp.other_exempt_dwellings_net_income)
        block["preview_2027_28_if_same_result"] = {
            "deductible_against_rental_income": _r(q["deductible"]),
            "net_rental_result_after_quarantine": _r(income - q["deductible"]),
            "quarantined_carried_forward": _r(q["quarantined_carried_forward"]),
            "basis": "Illustrative: this property's result alone with the brought-forward and exempt-dwelling amounts given. Real quarantine works "
                     "across all your non-exempt residential dwellings together and can also be applied against residential capital gains.",
        }
    if inp.preview_quarantine_from_2027_28 and status == "grandfathered":
        block["preview_2027_28_if_same_result"] = {"quarantined_carried_forward": 0.0, "basis": "grandfathered: no quarantine"}
    return block, None


@calculator("rental_property_result", RentalInput)
def rental_property_result(figures: Figures, inp: RentalInput) -> dict:
    """Net rental result for ONE residential rental property owned by an individual who is not in business, for one
    income year (2025-26 or 2026-27): assessable rent (gross, before agent and platform fees), immediately deductible
    expenses (fees, advertising, guest cleaning in full; interest by purpose, rates, insurance, repairs, strata and other
    ownership costs apportioned), borrowing expenses spread over up to 5 years, depreciation on new (or grandfathered
    second-hand) assets, Div 43 capital works, and private-use apportionment by days (rented plus available on commercial
    terms over days in period) and by floor area ((exclusive area + half common area) / total area), per PCG 2026/2.
    Applies the denials for travel (s 26-31), vacant land (s 26-102) and holiday homes not used mainly for rent (s 26-50),
    caps non-arm's-length rent at the rent received, and splits by ownership percent. Shows capital items that are not
    immediately deductible. Reports the residential dwelling loss quarantine (applies from 2027-28 only, grandfathered for
    interests last acquired before 7.30 pm ACT time on 12 May 2026) and can preview it. Use for long-term rentals, spare
    rooms, holiday homes and Airbnb-style short stays. Refuses AU-RENT-001 (development or resale, commercial, company,
    trust, partnership or SMSF owner, rental business, business use), AU-RENT-002 (new residential dwelling exception or
    unknown acquisition date when quarantine is asked about), AU-RENT-003 (s 26-50 test unresolved), AU-RENT-004
    (capital works dates or contracts not verifiable) and AU-RENT-005 (overseas property)."""
    if inp.owner_type != "individual" or inp.property_type != "residential" or inp.carrying_on_rental_business \
            or inp.property_development_or_resale or inp.mixed_use_with_business:
        raise Refusal("AU-RENT-001", f"owner {inp.owner_type}, {inp.property_type}, business={inp.carrying_on_rental_business}, "
                      f"development={inp.property_development_or_resale}, mixed_use={inp.mixed_use_with_business}")
    if inp.property_location == "overseas":
        raise Refusal("AU-RENT-005", "property outside Australia; for rent and deductions the taxpayer states, use foreign_rental_net "
                      "(net foreign rent, assembly components and offset inputs) and carry on with the other skills")
    if inp.holiday_home and inp.holiday_home_mainly_for_rent == "unresolved":
        raise Refusal("AU-RENT-003", "holiday home 'mainly for rent' test unresolved")

    assumptions: list[str] = []
    warnings: list[str] = []
    flags: list[str] = []
    ys, ye = _year_bounds(figures)
    diy = (ye - ys).days + 1
    period = inp.days_in_period or diy
    share = inp.ownership_percent / 100
    e = inp.expenses

    # ---- apportionment factors (PCG 2026/2)
    time_f, area_f, factor_notes = pcg_2026_2_factors(
        inp.days_rented, inp.days_available_commercial_terms, period, inp.part_of_home,
        inp.area_exclusive_to_tenant, inp.area_shared_common, inp.area_total)
    warnings += [n for n in factor_notes if n.startswith("Part of your home")]
    assumptions += [n for n in factor_notes if not n.startswith("Part of your home")]
    factor = time_f * area_f
    if factor < 1:
        flags.append("rental-private-use-apportionment")
    if inp.non_arms_length_rent:
        flags.append("rental-non-arms-length-rent")
    if inp.ownership_percent < 100:
        flags.append("rental-co-ownership-title")
    if inp.short_stay:
        flags.append("rental-short-stay-data-matching")

    # ---- categories
    direct = {"agent_fees": e.agent_fees, "platform_fees": e.platform_fees, "advertising": e.advertising,
              "guest_cleaning_and_linen": e.guest_cleaning_and_linen, "other_direct_letting": e.other_direct_letting}
    interest_rental = e.interest * (1 - e.interest_non_rental_share)
    if e.interest_non_rental_share:
        flags.append("rental-interest-purpose")
        assumptions.append("Interest: the non-rental-purpose share was removed first (purpose test, TR 2000/2), then the result was apportioned.")
    ownership = {"interest": interest_rental, "council_rates": e.council_rates, "water_charges": e.water_charges,
                 "land_tax": e.land_tax, "insurance": e.insurance, "strata_body_corporate": e.strata_body_corporate,
                 "repairs_maintenance": e.repairs_maintenance, "gardening_pest_control": e.gardening_pest_control,
                 "bank_fees_other_ownership": e.bank_fees_other_ownership}

    bw = [_borrowing(figures, b) for b in inp.borrowing_expenses]
    borrowing = sum(x["deductible"] for x in bw)

    dep_lines = []
    dep_total = 0.0
    for a in inp.depreciating_assets:
        amt, note = _asset(figures, a, period, assumptions, warnings)
        dep_lines.append({"asset": a.description, "amount_before_apportionment": _r(amt), "basis": note})
        dep_total += amt
        if note.startswith("denied"):
            flags.append("rental-second-hand-assets")

    cw_lines = []
    cw_total = 0.0
    for c in inp.capital_works:
        item = CapitalWorksInput(construction_cost=c.construction_cost, construction_start_date=c.construction_start_date,
                                 construction_completion_date=c.construction_completion_date, use_type=c.use_type,
                                 units_or_bedrooms_held=c.units_or_bedrooms_held, days_income_producing=period,
                                 previously_deducted_or_undeducted=c.undeducted_construction_expenditure,
                                 pre_16_sep_1987_contract=c.pre_16_sep_1987_contract)
        r = _capital_works(figures, item, period, assumptions, warnings)
        cw_lines.append({"item": c.description, "rate": r["rate"], "amount_before_apportionment": _r(r["amount"]), "basis": r["basis"]})
        cw_total += r["amount"]
    if inp.capital_works_amount_from_schedule:
        cw_lines.append({"item": "amount taken from schedule", "amount_before_apportionment": _r(inp.capital_works_amount_from_schedule),
                         "basis": "as given; construction date and rate not checked"})
        cw_total += inp.capital_works_amount_from_schedule
        assumptions.append("Capital works amount taken as given from the schedule; check the construction start date, use type and rate against "
                           "Div 43 and confirm the schedule is for the period owned.")

    # ---- denials
    denied: list[dict] = []
    holiday_denied = inp.holiday_home and inp.holiday_home_mainly_for_rent == "no"
    if inp.holiday_home:
        flags.append("rental-holiday-home-s26-50")
    if holiday_denied:
        denied.append({"item": "ownership and use expenses, borrowing expenses, depreciation and capital works",
                       "amount": _r((sum(ownership.values()) + borrowing + dep_total + cw_total) * share),
                       "reason": "(before apportionment) Holiday home not used or held mainly to produce rent: s 26-50(1) denies costs of owning and using it, with no apportionment "
                                 "(TR 2026/1 paras 30-35, 86-95)."})
        ownership = {k: 0.0 for k in ownership}
        borrowing = dep_total = cw_total = 0.0
        if ys < _ymd(figures.get("rental.holiday_home_compliance_start")):
            warnings.append("Expenses incurred before 1 Jul 2026: the ATO will not devote compliance resources to s 26-50 for them (PCG 2026/3 paras 12-13), "
                            "but the law is unchanged and the claim must still be correct.")
    elif inp.holiday_home:
        assumptions.append("Holiday home used or held mainly to produce rent all year (s 26-50(3)(b)(ii)): ownership costs stay deductible, apportioned for private use. "
                           "You must be able to show it objectively (PCG 2026/3 green zone).")
    if inp.vacant_land:
        flags.append("rental-vacant-land")
        denied.append({"item": "holding costs of vacant land",
                       "amount": _r((sum(ownership.values()) + borrowing + dep_total + cw_total) * share),
                       "reason": "Holding costs (interest, rates, land tax, borrowing costs) of vacant land are not deductible (s 26-102; TR 2023/3). "
                                 "They may form part of the CGT cost base."})
        ownership = {k: 0.0 for k in ownership}
        borrowing = dep_total = cw_total = 0.0
    if e.travel:
        flags.append("rental-travel-denied")
        denied.append({"item": "travel", "amount": _r(e.travel * share),
                       "reason": "Travel relating to a residential rental property is not deductible for an individual not carrying on a rental business (s 26-31)."})
    capital_items = []
    for label, amt, note in (
            ("initial_repairs", e.initial_repairs, "Capital: repairs to damage or defects that existed at acquisition (TR 97/23). Claim as Div 43 capital works "
                                                   "(or Div 40 for depreciating assets), not as repairs."),
            ("capital_improvements", e.capital_improvements, "Capital: improvements and replacement of an entirety; Div 43 capital works or Div 40 depreciation."),
            ("purchase_and_sale_costs", e.purchase_and_sale_costs, "Capital: CGT cost base, not deductible now.")):
        if amt:
            capital_items.append({"item": label, "amount": _r(amt * share), "treatment": note})
            if label == "initial_repairs":
                flags.append("rental-initial-repairs")

    # ---- apportion and total
    direct_total = sum(direct.values())
    own_total = sum(ownership.values())
    apportioned = (own_total + borrowing + dep_total + cw_total) * factor
    # asset-based amounts were computed for the ownership period already; borrowing follows loan dates only
    deductions_all = direct_total + apportioned
    income_total = inp.gross_rent + inp.other_rental_income
    capped = False
    if inp.non_arms_length_rent and deductions_all > income_total:
        deductions_all, capped = income_total, True
        assumptions.append("Rent charged below market to family or friends: deductions limited to the rent received, so no net rental loss (PCG 2026/2 para 44).")
    deductions_all_share = deductions_all * share
    income_share = income_total * share

    ng_block, ng_net = _negative_gearing(figures, inp, income_share, deductions_all_share, warnings, assumptions)
    if ng_block.get("applies_this_year"):
        flags.append("rental-negative-gearing-2027-28")
    elif ng_block.get("status") == "subject_to_quarantine":
        flags.append("rental-negative-gearing-2027-28")
    net = income_share - deductions_all_share
    net_reported = ng_net if ng_net is not None else net

    if inp.short_stay:
        assumptions.append("Short-stay letting by an individual owner is treated as passive rental income, not a business. Hotel-like services, several properties "
                           "run systematically or GST questions are outside this tool (see AU-RENT-001 and the gst-bas skill).")
    assumptions.append("Amounts exclude GST. Rent for residential premises is input taxed; whether short-stay accommodation is commercial residential premises is a GST question.")
    if period != diy:
        assumptions.append(f"Period apportioned: {period} days. Depreciation and capital works were computed for the days in this period; loan costs use actual amounts.")

    return {
        "ownership_percent": inp.ownership_percent,
        "assessable_income": {"rent_and_platform_income": _r(inp.gross_rent * share), "other": _r(inp.other_rental_income * share),
                              "total": _r(income_share)},
        "deductions": {
            "direct_letting_expenses": _r(direct_total * share),
            "ownership_expenses_after_apportionment": _r(own_total * factor * share),
            "borrowing_expenses_after_apportionment": _r(borrowing * factor * share),
            "depreciation_after_apportionment": _r(dep_total * factor * share),
            "capital_works_after_apportionment": _r(cw_total * factor * share),
            "capped_at_rent_received": capped,
            "total": _r(deductions_all_share),
        },
        "apportionment": {"time_factor": round(time_f, 6), "area_factor": round(area_f, 6), "combined_factor": round(factor, 6),
                          "days_in_period": period, "days_in_income_year": diy},
        "net_rental_result": _r(net_reported),
        "net_rental_result_before_quarantine": _r(net),
        "negative_gearing": ng_block,
        "borrowing_expense_detail": [{**x, "maximum_for_year": _r(x["maximum_for_year"]), "deductible": _r(x["deductible"])} for x in bw],
        "depreciation_detail": dep_lines,
        "capital_works_detail": cw_lines,
        "denied_amounts": denied,
        "capital_not_deductible_now": capital_items,
        "risk_flag_ids": sorted(set(flags)),
        "assumptions": assumptions,
        "warnings": warnings,
    }


# ---------------------------------------------------------------- overseas rental from stated amounts

class ForeignRentalExpense(BaseModel):
    label: str = Field(description="What the cost is, for example 'platform commissions' or 'loan interest'.")
    amount_aud: float = Field(ge=0, description="Amount in AUD, converted from the foreign currency by the rules that apply (idr_to_aud for rupiah).")
    debt_deduction: bool = Field(False, description="True for interest, borrowing costs and other debt deductions: they stay in taxable "
                                 "income at step 2 of the foreign income tax offset limit (s 770-75(4)).")


class ForeignRentalInput(BaseModel):
    """Rent from residential property outside Australia and the costs the taxpayer states, all in AUD and the taxpayer's own share."""

    owner_type: OwnerType = Field("individual", description="Anything other than individual is refused (AU-RENT-001).")
    gross_rent_aud: float = Field(ge=0, description="Gross rent and platform income for the year before commissions and fees, in AUD.")
    expenses: list[ForeignRentalExpense] = Field(default_factory=list, description="Costs the taxpayer states, each in AUD; taken as given.")
    foreign_tax_paid_aud: float = Field(0, ge=0, description="Foreign income tax paid on the rent, in AUD, translated when paid (for the offset hand-off).")
    any_owner_or_family_use: bool = Field(False, description="True if the owner, family or friends used the property: private-use apportionment "
                                          "and any holiday home test for overseas property are not modelled (AU-RENT-005).")


@calculator("foreign_rental_net", ForeignRentalInput)
def foreign_rental_net(figures: Figures, inp: ForeignRentalInput) -> dict:
    """Net rental income from a residential property OUTSIDE Australia for an Australian resident individual, from the gross rent,
    the costs and the foreign tax paid that the taxpayer states (all in AUD, own share). It adds up the amounts as given: it does
    NOT decide whether each cost is deductible, and it does not compute depreciation, capital works, interest apportionment,
    private use or the holiday home test for foreign property (those stay AU-RENT-005 for a registered tax agent), so the result is
    a working figure resting on the stated deductions. It returns the components for assemble_taxable_income (gross rent as
    foreign_income, costs as other_deduction lines, debt deductions separate), the items for indonesia_treaty_fito (or the inputs
    for foreign_income_tax_offset) and the escalations. Use it instead of rental_property_result for Bali or other overseas rent
    so the rest of the return can still be worked out. Refuses a loss (AU-RENT-005), owner or family use (AU-RENT-005) and a
    non-individual owner (AU-RENT-001)."""
    if inp.owner_type != "individual":
        raise Refusal("AU-RENT-001", f"owner {inp.owner_type}")
    if inp.any_owner_or_family_use:
        raise Refusal("AU-RENT-005", "overseas property with owner or family use: private-use apportionment and any holiday home "
                      "test are not modelled for property outside Australia")
    direct = sum(e.amount_aud for e in inp.expenses if not e.debt_deduction)
    debt = sum(e.amount_aud for e in inp.expenses if e.debt_deduction)
    net = inp.gross_rent_aud - direct - debt
    if net < -1e-9:
        raise Refusal("AU-RENT-005", "the stated costs exceed the rent (an overseas rental loss): its treatment and the offset limit "
                      "with a foreign loss are not modelled")
    src = {"source_skill": "rental-property", "source_tool": "foreign_rental_net"}
    components = [{"kind": "foreign_income", "amount": _r(inp.gross_rent_aud), "label": "Foreign rental income (gross)", **src}]
    if direct:
        components.append({"kind": "other_deduction", "amount": _r(direct), "label": "Foreign rental deductions (as stated)", **src})
    if debt:
        components.append({"kind": "other_deduction", "amount": _r(debt), "label": "Foreign rental debt deductions (as stated)", **src})
    entry = refusal_catalogue()["AU-RENT-005"]
    return {
        "gross_rent_aud": _r(inp.gross_rent_aud), "direct_deductions_aud": _r(direct), "debt_deductions_aud": _r(debt),
        "net_foreign_rental_income_aud": _r(net), "foreign_tax_paid_aud": _r(inp.foreign_tax_paid_aud),
        "deductions": [{"label": e.label, "amount_aud": _r(e.amount_aud), "debt_deduction": e.debt_deduction} for e in inp.expenses],
        "assemble_taxable_income_components": components,
        "indonesia_treaty_fito_inputs": {
            "items": [{"kind": "rent_real_property", "gross_aud": _r(inp.gross_rent_aud),
                       "foreign_tax_paid_aud": _r(inp.foreign_tax_paid_aud), "label": "Foreign rental income"}],
            "related_deductions_aud": _r(direct)},
        "foreign_income_tax_offset_inputs": {"foreign_tax_paid": _r(inp.foreign_tax_paid_aud),
                                             "foreign_net_income": _r(inp.gross_rent_aud - direct)},
        "escalations": [{"code": "AU-RENT-005", "message": entry["message"], "route": entry.get("route"),
                         "scope": "Not checked by this tool: whether each stated cost is deductible for foreign property, "
                                  "depreciation and capital works, interest apportionment, private use and any holiday home test, "
                                  "return labels, and the foreign country's own tax. The result stands on the stated amounts."}],
        "risk_flag_ids": ["rental-foreign-property-stated-deductions"],
        "assumptions": ["The rent, costs and foreign tax are in AUD, already translated by the rules that apply (rupiah: idr_to_aud), and "
                        "are the taxpayer's own share.",
                        "The property was let on commercial terms with no owner or family use, and the costs relate to earning the rent."],
        "warnings": ["Deductibility of the stated costs for property outside Australia is not tested. Depreciation (Div 40), capital works "
                     "(Div 43), the travel and second-hand asset denials, interest apportionment and any holiday home rule are not "
                     "computed; a registered tax agent should confirm them (AU-RENT-005).",
                     "Debt deductions (interest, borrowing costs) are left inside taxable income at step 2 of the foreign income tax "
                     "offset limit; only the other costs are related deductions."],
    }
