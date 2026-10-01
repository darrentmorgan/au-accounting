"""Short-stay accommodation (Airbnb-style letting by an individual owner) working-paper tools.

Covers only what rental.py and gst.py do not: night-by-night apportionment of mixed-use costs with the holiday home
(ITAA 1997 s 26-50) gate, a GST classification screen (residential premises v commercial residential premises, GSTA 1999
ss 40-35 and 195-1, GSTR 2012/6) that never decides the hotel-like question, Division 87 long-term accommodation
arithmetic for a confirmed commercial residential premises, the Sharing Economy Reporting Regime scope check (TAA 1953
Sch 1 s 396-55 table item 15; LI 2025/5) and the platform-statement reconciliation. Net rental result, deductions by
category, negative gearing and GST registration stay in rental_property_result and gst_registration_check: this module
hands off to them.

Figures come from data/rates/<year>.d/shortstay.yaml (SERR), gst.yaml (Division 87, GST rate) and rental.yaml
(s 26-50 compliance start).
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from au_tax.calculators.rental import OwnerType, _r, _year_bounds, _ymd, pcg_2026_2_factors
from au_tax.figures import Figures
from au_tax.holidays import COMMONWEALTH, roll_due_date_or_statutory
from au_tax.registry import InputError, Refusal, calculator


# ====================================================================== short_stay_apportionment

class CostLine(BaseModel):
    """One expense line for the whole property for the period, in AUD, excluding GST."""

    description: str = ""
    amount: float = Field(ge=0)


class ApportionmentInput(BaseModel):
    """Nights and costs for ONE short-stay property owned by an individual who is not in business."""

    owner_type: OwnerType = Field("individual", description="Anything other than individual is refused (AU-RENT-001).")
    property_location: Literal["australia", "overseas"] = Field("australia", description="Overseas is refused (AU-RENT-005).")
    carrying_on_rental_business: bool = Field(False, description="Business indicators (several properties run systematically, "
                                              "hotel-like services): refused (AU-RENT-001).")
    mixed_use_with_business: bool = Field(False, description="Also used for a business: refused (AU-RENT-001).")
    ownership_percent: float = Field(100, gt=0, le=100, description="Legal-title share; the result is your share.")

    days_owned: int | None = Field(None, ge=1, le=366, description="Days in the income year you owned the property (part-year "
                                   "ownership uses days owned). Omit for the whole income year, taken from the calendar "
                                   "(365 or 366).")
    nights_rented: int = Field(0, ge=0, description="Nights occupied by paying guests, plus nights paid for even if nobody stayed "
                               "(PCG 2026/2 para 14). Market-rate nights for relatives count here only with evidence of the rate.")
    nights_available_commercial_terms: int = Field(0, ge=0, description="Unoccupied nights genuinely available for rent on "
                                                   "commercial terms (broad advertising, comparable pricing, requests monitored). "
                                                   "For a room in your own home these count as private and are set to nil.")
    nights_owner_use: int = Field(0, ge=0, description="Nights the owner used it, or it was otherwise unused and private.")
    nights_family_friends_free_or_reduced: int = Field(0, ge=0, description="Nights family or friends stayed free or at a "
                                                       "reduced rate. Counted as private (assumption; PCG 2026/2 gives no "
                                                       "day-level method) and they make it a holiday home.")
    nights_blocked_unused: int = Field(0, ge=0, description="Nights blocked out or reserved (for the owner, family or friends) "
                                       "that no one used and that were not available to rent. Private.")
    nights_closed_repairs: int = Field(0, ge=0, description="Nights closed for repairs or renovation. Not settled by the sources "
                                       "read: refused (AU-SS-003) if above zero.")
    is_main_residence: bool = Field(False, description="The property is the owner's main residence (let while away). Owner nights "
                                    "are then ordinary living, not holiday use, so it is not a holiday home.")
    part_of_home: bool = Field(False, description="Only a room or part of the owner's home is let.")
    area_exclusive_to_tenant: float | None = Field(None, ge=0)
    area_shared_common: float | None = Field(None, ge=0)
    area_total: float | None = Field(None, gt=0)
    holiday_home_mainly_for_rent: Literal["yes", "no", "unresolved"] | None = Field(
        None, description="Only when the property is a holiday home (owner, family or friends use or reserve it for holidays): is it "
        "used or held mainly to produce rent at all times in the year (s 26-50(3)(b)(ii); PCG 2026/3 green = yes, red = no). "
        "Missing or unresolved is refused (AU-RENT-003).")

    gross_rent: float = Field(0, ge=0, description="Rent and platform income before fees and commissions, including cleaning and host fees charged to guests.")
    other_rental_income: float = Field(0, ge=0, description="Retained bonds, insurance payouts for lost rent, cancellation fees kept.")
    direct_costs: list[CostLine] = Field(default_factory=list, description="Bucket A, deductible in full: platform commissions, agent fees, "
                                         "advertising, cleaning and laundry after guest stays.")
    ownership_costs: list[CostLine] = Field(default_factory=list, description="Bucket B, apportioned (or denied by s 26-50): interest "
                                            "(after removing any private-purpose share), rates, water, land tax, body corporate, insurance, "
                                            "repairs, power and internet, depreciation, capital works.")

    @model_validator(mode="after")
    def _consistent(self):
        if self.area_total is not None:
            if (self.area_exclusive_to_tenant or 0) + (self.area_shared_common or 0) > self.area_total:
                raise ValueError("tenant and common areas exceed the total area")
        elif self.area_exclusive_to_tenant is not None or self.area_shared_common is not None:
            raise ValueError("area_total is required with the area fields")
        if self.part_of_home and self.area_total is None:
            raise ValueError("part_of_home needs the area fields (area_exclusive_to_tenant, area_shared_common, area_total)")
        if self.days_owned is not None and self._nights() != self.days_owned:
            raise ValueError(f"nights add up to {self._nights()} but days owned is {self.days_owned}: account for every night")
        return self

    def _nights(self) -> int:
        return (self.nights_rented + self.nights_available_commercial_terms + self.nights_owner_use
                + self.nights_family_friends_free_or_reduced + self.nights_blocked_unused + self.nights_closed_repairs)


@calculator("short_stay_apportionment", ApportionmentInput)
def short_stay_apportionment(figures: Figures, inp: ApportionmentInput) -> dict:
    """Night-by-night apportionment of a short-stay (Airbnb-style) property owned by an individual, for one income year
    (2025-26 or 2026-27), with the holiday home gate. Every night owned is classified (rented or paid for, available on
    commercial terms, owner use, family or friends free or reduced, blocked and unused); direct letting costs are
    deductible in full; ownership costs are multiplied by the time factor (nights rented plus nights available, over days
    owned; a room in your own home has no available nights) and, for part of a home, the area factor (exclusive area plus
    half the shared area, over total area), per PCG 2026/2. If owner, family or friends use or reserve the whole property
    for holidays it is a holiday home: with holiday_home_mainly_for_rent 'no' s 26-50 denies all ownership costs (no
    apportionment); 'yes' keeps them, apportioned for private use. Returns the deductions, net rental result and a ready
    handoff block for rental_property_result (which owns depreciation, borrowing costs, negative gearing and the wider
    rental rules). Use to work out the private-use split for Airbnb, Stayz and Booking.com hosts. Refuses AU-RENT-001
    (entity owner, business), AU-RENT-005 (overseas), AU-RENT-003 (holiday home test missing or unresolved) and AU-SS-003
    (nights closed for repairs, which the sources do not settle). Exit 2 if the nights do not add up to the days owned."""
    if inp.owner_type != "individual" or inp.carrying_on_rental_business or inp.mixed_use_with_business:
        raise Refusal("AU-RENT-001", f"owner {inp.owner_type}, business={inp.carrying_on_rental_business}, "
                      f"mixed_use={inp.mixed_use_with_business}")
    if inp.property_location == "overseas":
        raise Refusal("AU-RENT-005", "property outside Australia")
    if inp.nights_closed_repairs:
        raise Refusal("AU-SS-003", f"{inp.nights_closed_repairs} nights closed for repairs or renovation")

    ys, ye = _year_bounds(figures)
    diy = (ye - ys).days + 1
    days = inp.days_owned if inp.days_owned is not None else diy
    if days > diy:
        raise InputError(f"days owned {days} exceeds the {diy} days in the income year")
    if inp._nights() != days:
        raise InputError(f"nights add up to {inp._nights()} but days owned is {days} (the income year has {diy} days): "
                         "account for every night")

    assumptions: list[str] = []
    warnings: list[str] = []
    flags: list[str] = []

    time_f, area_f, notes = pcg_2026_2_factors(
        inp.nights_rented, inp.nights_available_commercial_terms, days, inp.part_of_home,
        inp.area_exclusive_to_tenant, inp.area_shared_common, inp.area_total)
    avail_used = 0 if inp.part_of_home else inp.nights_available_commercial_terms
    warnings += [n for n in notes if n.startswith("Part of your home")]
    factor = time_f * area_f
    if inp.part_of_home and inp.nights_available_commercial_terms:
        flags.append("short-stay-room-held-days")

    # ---- holiday home gate (s 26-50)
    reserved_private = (inp.nights_owner_use + inp.nights_family_friends_free_or_reduced + inp.nights_blocked_unused)
    holiday_home = (not inp.is_main_residence and not inp.part_of_home and reserved_private > 0)
    if inp.nights_family_friends_free_or_reduced:
        flags.append("short-stay-friends-family-reduced-rate")
        assumptions.append("Nights that family or friends stayed free or at a reduced rate are counted as private use and excluded from "
                           "the time factor. PCG 2026/2 gives no day-level method for occasional discounted stays, so this is the "
                           "preparer's conservative treatment, not an ATO-stated rule. Rent actually received is still assessable.")
    if inp.nights_blocked_unused:
        flags.append("short-stay-blocked-peak-periods")
    denied = False
    s2650: dict = {"holiday_home": holiday_home, "ownership_costs_denied": False}
    if holiday_home:
        if inp.holiday_home_mainly_for_rent in (None, "unresolved"):
            raise Refusal("AU-RENT-003", "holiday home 'mainly for rent' test unresolved or not answered")
        s2650["mainly_for_rent"] = inp.holiday_home_mainly_for_rent
        if inp.holiday_home_mainly_for_rent == "no":
            denied = True
            s2650["ownership_costs_denied"] = True
            flags.append("short-stay-blocked-peak-periods")
            if ys < _ymd(figures.get("rental.holiday_home_compliance_start")):
                warnings.append("Expenses incurred before 1 Jul 2026: the ATO will not devote compliance resources to s 26-50 for them "
                                "(PCG 2026/3 paras 12-13), but the law is unchanged and the claim must still be correct.")
        else:
            assumptions.append("Holiday home used or held mainly to produce rent all year (s 26-50(3)(b)(ii)): ownership costs stay deductible, "
                               "apportioned for private use. You must be able to show it objectively (PCG 2026/3 green zone).")
    elif inp.holiday_home_mainly_for_rent is not None:
        assumptions.append("holiday_home_mainly_for_rent was given but the property is not a holiday home on the nights supplied (no owner, "
                           "family or friends use or reservation of the whole property, or it is a room in the owner's home or the main residence); it was not used.")
    if inp.is_main_residence:
        assumptions.append("Main residence let while the owner is away: time-based apportionment only, direct letting costs in full "
                           "(ATO John and Mary example). Renting the home can reduce the main residence exemption: see the cgt skill.")

    # ---- amounts
    direct_total = sum(c.amount for c in inp.direct_costs)
    own_total = sum(c.amount for c in inp.ownership_costs)
    share = inp.ownership_percent / 100
    own_deductible = 0.0 if denied else own_total * factor
    private_portion = 0.0 if denied else own_total - own_deductible
    income = inp.gross_rent + inp.other_rental_income
    deductions = direct_total + own_deductible
    net = (income - deductions) * share
    if inp.ownership_percent < 100:
        flags.append("rental-co-ownership-title")
    if factor < 1 and not denied:
        flags.append("rental-private-use-apportionment")
    assumptions.append("Not a business, no GST in the amounts (residential rent is input taxed), depreciation and capital works entered "
                       "here as ownership cost lines are already for the period. Own travel (s 26-31) and second-hand depreciating assets "
                       "(s 40-27) are not deductible for an individual and are not in these lines.")

    line_detail = ([{"bucket": "direct", "description": c.description, "amount": _r(c.amount), "deductible": _r(c.amount)}
                    for c in inp.direct_costs]
                   + [{"bucket": "ownership", "description": c.description, "amount": _r(c.amount),
                       "deductible": 0.0 if denied else _r(c.amount * factor)} for c in inp.ownership_costs])
    handoff = {
        "short_stay": True,
        "days_in_period": days,
        "days_rented": inp.nights_rented,
        "days_available_commercial_terms": avail_used,
        "part_of_home": inp.part_of_home,
        "area_exclusive_to_tenant": inp.area_exclusive_to_tenant,
        "area_shared_common": inp.area_shared_common,
        "area_total": inp.area_total,
        "holiday_home": holiday_home,
        "holiday_home_mainly_for_rent": inp.holiday_home_mainly_for_rent if holiday_home else None,
        "ownership_percent": inp.ownership_percent,
    }
    return {
        "days_owned": days,
        "nights": {"rented_or_paid": inp.nights_rented, "available_commercial_terms": avail_used,
                   "owner_use_or_private": inp.nights_owner_use + (inp.nights_available_commercial_terms if inp.part_of_home else 0),
                   "family_friends_free_or_reduced": inp.nights_family_friends_free_or_reduced,
                   "blocked_unused": inp.nights_blocked_unused},
        "apportionment": {"time_factor": round(time_f, 6), "area_factor": round(area_f, 6), "combined_factor": round(factor, 6),
                          "days_owned": days, "days_in_income_year": diy},
        "section_26_50": s2650,
        "assessable_income": _r(income * share),
        "direct_costs_deductible": _r(direct_total),
        "ownership_costs_total": _r(own_total),
        "ownership_costs_deductible": _r(own_deductible),
        "private_portion_of_ownership_costs": _r(private_portion),
        "denied_ownership_costs": _r(own_total) if denied else 0.0,
        "total_deductions": _r(deductions),
        "net_rental_result": _r(net),
        "ownership_percent": inp.ownership_percent,
        "line_detail": line_detail,
        "rental_property_result_handoff": handoff,
        "risk_flag_ids": sorted(set(flags)),
        "assumptions": assumptions,
        "warnings": warnings,
    }


# ====================================================================== gst_short_stay_classification

class ClassificationInput(BaseModel):
    """Facts for the GST screen of a short-stay supply. The tool never decides the hotel-like question."""

    perspective: Literal["owner_letting_own_premises", "owner_leasing_to_operator", "operator_supplying_guests"] = Field(
        "owner_letting_own_premises",
        description="owner_letting_own_premises = the owner supplies the stay to guests, directly or through an agent or manager "
        "acting for the owner; owner_leasing_to_operator = the owner leases the premises to a separate operator; "
        "operator_supplying_guests = an operator holds head leases or licences and sells stays in its own name (refused).")
    premises_kind: Literal["house", "unit_or_apartment", "granny_flat", "rooms_in_owners_home",
                           "room_or_apartment_in_managed_complex", "hotel_motel_inn_hostel_or_boarding_house",
                           "caravan_park_or_camping_ground", "school_accommodation", "ship_or_marina_berth", "other"] = "house"
    daily_cleaning_or_housekeeping: bool = Field(False, description="The supplier provides daily or regular housekeeping during stays "
                                                 "(cleaning after the guest leaves and provision of linen are not indicators).")
    meals_or_communal_dining_provided: bool = Field(False, description="The supplier provides breakfast or other meals, or a communal dining room.")
    reception_or_front_desk_operated_by_supplier: bool = Field(False, description="The supplier (not an agent acting for an owner) runs a "
                                                               "reception or front desk or on-site guest services.")
    held_out_as_hotel_guesthouse_or_bnb: bool = Field(False, description="Marketed to the public as a hotel, motel, guest house, lodge or B&B business.")
    several_premises_supplied_centrally_in_own_right: bool = Field(False, description="The supplier takes bookings, allocates rooms and "
                                                                   "supplies stays for several premises as principal.")
    leased_together_with_whole_complex: bool = Field(False, description="For owner_leasing_to_operator: the owner leases the whole building "
                                                     "or many units together with common facilities, not one unit on its own.")
    annual_rent: float | None = Field(None, ge=0, description="Annual short-stay rent (GST exclusive), to hand to gst_registration_check "
                                      "as input taxed sales included.")
    asked_must_register_because_of_platform_income: bool = Field(False, description="The host asked whether they must register for GST "
                                                                 "because they earn through a platform.")


LISTED_CRP = {"hotel_motel_inn_hostel_or_boarding_house", "caravan_park_or_camping_ground", "school_accommodation", "ship_or_marina_berth"}


@calculator("gst_short_stay_classification", ClassificationInput)
def gst_short_stay_classification(figures: Figures, inp: ClassificationInput) -> dict:
    """GST screen for short-stay letting: is the supply of residential premises (input taxed, GSTA 1999 s 40-35: no GST on
    the rent, no input tax credits on related costs, rent excluded from GST turnover) or does it show features of commercial
    residential premises (taxable; s 195-1, GSTR 2012/6)? Length of stay never decides it. Returns input taxed only when
    there are no hotel-like indicators and no listed category (hotel, motel, inn, hostel, boarding house, caravan park,
    school accommodation, ship or marina); an owner leasing one unit to a hotel operator is input taxed for the owner. Any
    indicator, an operator supplying stays in its own right, or a whole-complex lease is refused AU-GST-002: the tool sets
    out the tests and never makes the determination. Also returns the handoff for gst_registration_check (rent excluded from
    turnover). Use for Airbnb, Stayz, serviced apartments and B&B questions."""
    indicators = {
        "daily cleaning or housekeeping": inp.daily_cleaning_or_housekeeping,
        "meals or communal dining": inp.meals_or_communal_dining_provided,
        "reception or front desk run by the supplier": inp.reception_or_front_desk_operated_by_supplier,
        "held out as a hotel, guest house or B&B": inp.held_out_as_hotel_guesthouse_or_bnb,
        "several premises supplied centrally in the supplier's own right": inp.several_premises_supplied_centrally_in_own_right,
    }
    present = [k for k, v in indicators.items() if v]
    if inp.premises_kind in LISTED_CRP:
        raise Refusal("AU-GST-002", f"premises described as {inp.premises_kind}, a listed commercial residential premises category (s 195-1)")
    if inp.perspective == "operator_supplying_guests":
        raise Refusal("AU-GST-002", "operator supplying stays in its own right (principal or head-lease model): the operator's supplies "
                      "may be commercial residential premises accommodation")
    if inp.perspective == "owner_leasing_to_operator" and inp.leased_together_with_whole_complex:
        raise Refusal("AU-GST-002", "lease of a whole complex or many units with common facilities can itself be commercial residential premises")
    if inp.perspective == "owner_letting_own_premises" and present:
        raise Refusal("AU-GST-002", "hotel-like features present: " + "; ".join(present))

    notes: list[str] = []
    warnings: list[str] = []
    if inp.perspective == "owner_leasing_to_operator":
        notes.append("This is the owner's lease of a unit on its own (GSTR 2012/6 paras 95-98). The operator's supplies to guests are a separate "
                     "question and can be taxable commercial residential premises accommodation; it needs the operator's facts and contracts (AU-GST-002).")
    elif inp.premises_kind == "room_or_apartment_in_managed_complex":
        notes.append("A manager who acts as agent for the owner does not make the supply of the accommodation: the owner does, and it is input taxed "
                     "(GSTR 2012/6 Example 12, paras 82-85). The manager's fee is a separate taxable supply to the owner for which the owner has no credit.")
    else:
        notes.append("Any agent, manager or platform fee is a cost to the owner with no input tax credit, because it relates to input taxed rent (s 11-15(2)(a)).")
    if inp.premises_kind == "rooms_in_owners_home":
        notes.append("Two furnished rooms in a home with linen only is the GSTR 2012/6 Example 3 pattern (paras 51-52): not commercial residential premises.")
    if inp.asked_must_register_because_of_platform_income:
        warnings.append("Registration: the rule is GSTA 1999 s 23-5 (enterprise plus GST turnover at or above the threshold), and input taxed rent is excluded "
                        "from GST turnover (s 188-15). The ATO Registering for GST page lists sharing economy or digital platform income as a case where you "
                        "must register, which cannot be reconciled with the Act for residential rent. Do not tell the host they must or must not register on "
                        "platform income alone (AU-SS-001).")
    return {
        "classification": "residential_premises_input_taxed",
        "authority": "GSTA 1999 s 40-35(1)(a) and (2)(a); s 195-1 'residential premises' applies regardless of the term of occupation; GSTR 2012/5, GSTR 2012/6",
        "gst_charged_on_rent": False,
        "input_tax_credits_on_related_costs": False,
        "counts_toward_gst_turnover": False,
        "division_87_applies": False,
        "registration_position": "Registration depends on other taxable turnover only (s 23-5, s 188-15); registration does not change the input taxed classification (s 9-30(2)).",
        "handoff_gst_registration_check": {"input_taxed_sales_included": inp.annual_rent if inp.annual_rent is not None else 0},
        "notes": notes,
        "assumptions": ["Individual or entity making the supply carries on the letting as an enterprise or not: irrelevant to the classification.",
                        "No hotel-like features beyond those answered false; the screen is a fact-based indication, not a ruling."],
        "warnings": warnings,
        "risk_flag_ids": ["GST-RF-002"] + (["short-stay-gst-registration-wording"] if inp.asked_must_register_because_of_platform_income else []),
    }


# ====================================================================== div87_stay_gst

class Div87Input(BaseModel):
    """One stay in commercial residential premises that a registered agent has confirmed are commercial residential premises."""

    crp_confirmed: bool = Field(description="A registered tax or BAS agent has confirmed the premises are commercial residential premises "
                                "(GSTR 2012/6) and the supplier is registered or required to be. False is refused (AU-GST-002).")
    nights: int | None = Field(None, ge=1, description="Continuous nights (arrival day counted, departure day not). Or give check_in and check_out.")
    check_in: date | None = None
    check_out: date | None = None
    nightly_price_gst_inclusive: float = Field(gt=0, description="Price per night including GST.")
    bookings_total_12m: int = Field(ge=1, description="Bookings of commercial accommodation in the premises in the last 12 months (actual) or the "
                                    "next 12 months (projected), GSTR 2012/7 paras 53-56.")
    bookings_28_nights_or_more_12m: int = Field(ge=0, description="Of those, bookings of 28 continuous days or more.")
    elected_not_to_apply_division_87: bool = Field(False, description="The supplier has chosen not to apply Division 87 (s 87-25).")

    @model_validator(mode="after")
    def _consistent(self):
        if self.check_in is not None or self.check_out is not None:
            if self.check_in is None or self.check_out is None:
                raise ValueError("give both check_in and check_out")
            n = (self.check_out - self.check_in).days
            if n < 1:
                raise ValueError("check_out must be after check_in")
            if self.nights is not None and self.nights != n:
                raise ValueError(f"nights {self.nights} does not match the dates ({n})")
            self.nights = n
        if self.nights is None:
            raise ValueError("give nights, or check_in and check_out")
        if self.bookings_28_nights_or_more_12m > self.bookings_total_12m:
            raise ValueError("long-term bookings exceed total bookings")
        return self


@calculator("div87_stay_gst", Div87Input)
def div87_stay_gst(figures: Figures, inp: Div87Input) -> dict:
    """GST on one stay in commercial residential premises under Division 87 (GSTA 1999 ss 87-5, 87-10, 87-20, 87-25;
    GSTR 2012/7). Only for premises a registered agent has confirmed are commercial residential premises: it does nothing
    for residential premises (already input taxed). Counts days with the arrival day in and the departure day out; 28 or
    more continuous days is long-term accommodation. If at least the predominance share of bookings are long-term, the
    value is half the GST-inclusive price from day one (GST 10% of that value); otherwise the first 27 days are valued
    normally (GST is 1/11 of the price) and the days after the first 27 are valued at half the price. If the supplier has
    elected not to apply Division 87 a long-term stay is input taxed (nil GST, no credits); a stay under 28 days stays
    taxable. Returns GST payable, the GST without Division 87 and the charged amount if the GST-exclusive rate is unchanged.
    Refuses AU-GST-002 when crp_confirmed is false."""
    if not inp.crp_confirmed:
        raise Refusal("AU-GST-002", "commercial residential premises status not confirmed; Division 87 does not apply to residential premises")
    long_days = int(figures.get("gst.div87_long_term_days"))
    share_min = figures.get("gst.div87_predominantly_long_term_share")
    value_share = figures.get("gst.div87_value_share")
    rate = figures.get("gst.rate")
    nights = int(inp.nights or 0)
    price = inp.nightly_price_gst_inclusive
    full_price = nights * price
    long_term = nights >= long_days
    predominantly = inp.bookings_28_nights_or_more_12m / inp.bookings_total_12m >= share_min
    first_days = long_days - 1
    assumptions = ["The guest is an individual provided with commercial accommodation; separately charged extras (meals, minibar, laundry, calls) "
                   "carry normal GST and are not in these amounts.",
                   "Price is the GST-inclusive price the supply would have without Division 87 (s 87-5 and s 87-10 apply to that price)."]
    gst_without = full_price * rate / (1 + rate)
    base = {"days_provided": nights, "long_term_accommodation": long_term, "predominantly_long_term": predominantly,
            "gst_without_division_87": _r(gst_without), "full_price_gst_inclusive": _r(full_price), "input_taxed": False}
    if long_term and inp.elected_not_to_apply_division_87:
        return {**base, "input_taxed": True, "gst_payable": 0.0,
                "basis": "Division 87 not applied by election (s 87-25): the long-term supply is input taxed; no GST and no credits on the costs of making it.",
                "assumptions": assumptions + ["The election covers all commercial accommodation the supplier provides and cannot be revoked within 12 months."],
                "warnings": [], "risk_flag_ids": ["short-stay-crp-drift"]}
    if not long_term:
        return {**base, "gst_payable": _r(gst_without), "basis": "Stay under the long-term period: fully taxable, GST is 1/11 of the price (s 9-70 and s 9-75).",
                "assumptions": assumptions, "warnings": [], "risk_flag_ids": ["short-stay-crp-drift"]}
    if predominantly:
        value = value_share * full_price
        gst = rate * value
        return {**base, "value_of_supply": _r(value), "gst_payable": _r(gst),
                "gst_per_night": _r(gst / nights),
                "basis": "Premises predominantly for long-term accommodation: value is the value share of the price from day one (s 87-5).",
                "total_charged_if_gst_exclusive_rate_unchanged": _r(nights * (price - price * rate / (1 + rate)) + gst),
                "assumptions": assumptions, "warnings": [], "risk_flag_ids": ["short-stay-crp-drift"]}
    first_price = first_days * price
    rest_nights = nights - first_days
    rest_price = rest_nights * price
    gst_first = first_price * rate / (1 + rate)
    value_rest = value_share * rest_price
    gst_rest = rate * value_rest
    exclusive_night = price - price * rate / (1 + rate)
    return {**base,
            "first_27_days_price": _r(first_price), "gst_first_27_days": _r(gst_first),
            "nights_after_first_27_days": rest_nights, "value_after_first_27_days": _r(value_rest),
            "gst_after_first_27_days": _r(gst_rest), "gst_per_night_after_first_27_days": _r(gst_rest / rest_nights),
            "gst_payable": _r(gst_first + gst_rest),
            "basis": "Premises not predominantly long-term: first 27 days valued normally, later days at the value share of the price (s 87-10).",
            "total_charged_if_gst_exclusive_rate_unchanged": _r(first_price + rest_nights * exclusive_night + gst_rest),
            "assumptions": assumptions + ["'Charged if the GST-exclusive rate is unchanged' assumes the operator keeps the GST-exclusive nightly amount and "
                                          "only the GST falls; the operator may price differently."],
            "warnings": [], "risk_flag_ids": ["short-stay-crp-drift"]}


# ====================================================================== serr_report_check

class SerrCheckInput(BaseModel):
    """Would an online platform report this short-stay booking under the Sharing Economy Reporting Regime?"""

    booking_entered_date: date = Field(description="Date the transaction was entered into (the regime applies to transactions entered into "
                                       "on or after the start date for short-term accommodation).")
    property_location: Literal["australia", "overseas"] = Field("australia", description="Overseas is refused (AU-SS-002).")
    platform_role: Literal["online_platform_operator", "agent_on_own_site_only"] = Field(
        "online_platform_operator", description="agent_on_own_site_only: the platform only acts as agent on its own site, so it is not an "
        "electronic distribution platform for the regime.")
    supplier_is_listed_entity_or_government: bool = False
    supplier_value_12m_gst_inclusive: float | None = Field(None, ge=0, description="Total value (GST inclusive) of supplies the supplier made "
                                                           "through that platform in the 12 months to the end of the reporting period.")
    days_supplier_active_on_platform_12m: int | None = Field(None, ge=1, le=365, description="Only for a supplier that started on the platform "
                                                             "in those 12 months: days supplies were available on the platform.")
    property_platform_transactions_12m: int | None = Field(None, ge=0, description="Transactions the platform facilitated for this property "
                                                           "in the 12 months to the end of the reporting period.")
    days_property_listed_12m: int | None = Field(None, ge=1, le=365, description="Only for a property first listed in those 12 months: days listed.")
    another_platform_reports_and_exemption_notified: bool = Field(False, description="Two platforms are in the chain, the other one reports, and the "
                                                                  "first has notified the ATO it is applying the exemption (LI 2025/5 s 6).")
    booking_has_no_price_and_no_platform_payment: bool = Field(False, description="Mere booking: no price at booking, payment not through the "
                                                               "platform, and no visibility of whether it happened (LI 2025/5 s 8(c)).")
    supplier_has_no_australian_link_on_all_four_tests: bool = Field(False, description="All four together: no Australian address given, service not "
                                                                    "provided in Australia, payment not to an Australian account, and no other sign "
                                                                    "of Australian residence (LI 2025/5 s 8(b)). Always false for an Australian property.")


REPORTED_FIELDS = [
    "platform identity and the seller's name, date of birth and contact details",
    "the seller's bank or payment account",
    "activity code (short-term accommodation) and property type",
    "gross income for the period including GST, fees and commissions, with refunds for cancellations through the platform netted off",
    "the GST amount and the number of bookings",
    "fees and commissions withheld by the platform (GST inclusive)",
    "for each property: street address, suburb, state, postcode, and nights booked and attended",
]


@calculator("serr_report_check", SerrCheckInput)
def serr_report_check(figures: Figures, inp: SerrCheckInput) -> dict:
    """Sharing Economy Reporting Regime (TAA 1953 Sch 1 Subdiv 396-B, s 396-55 table item 15; LI 2025/5) scope check for one
    short-stay booking: reportable, exempt (and which exemption: listed entity or government supplier, substantial supplier
    at the GST-inclusive value figure, substantial property at the transaction count figure, both prorated for a new supplier
    or listing, a two-platform chain, a mere booking, or a supplier with no Australian link on all four tests), or not in
    scope (before the start date, or a platform acting only as agent on its own site). It is a platform reporting duty: the
    host has no filing duty and the income is assessable whether or not it is reported. Returns what is reported and the
    platform's report due dates for the income year, each rolled to the next business day (TAA 1953 Sch 1 s 388-52) with the
    business_day_roll block; a date after the public holiday data range is returned unrolled with a field_refusals note (AU-GEN-004). There is no 90-day limit in the current instrument.
    Refuses AU-SS-002 for an Australian resident's overseas property, which the sources do not settle."""
    if inp.property_location == "overseas":
        raise Refusal("AU-SS-002", "overseas property let by an Australian resident: SERR scope not settled")
    start = figures.get("shortstay.serr_start_short_term_accommodation")
    supplier_cap = figures.get("shortstay.serr_substantial_supplier_value")
    property_cap = figures.get("shortstay.serr_substantial_property_transactions")
    ys, _ = _year_bounds(figures)
    y = ys.year
    due = {}
    warnings: list[str] = []
    field_refusals: list[dict] = []
    for label, p_start, p_end, dy, mkey, dkey in (
            ("period_1_jul_to_31_dec", date(y, 7, 1), date(y, 12, 31), y + 1, "shortstay.serr_due_month_period_jul_dec",
             "shortstay.serr_due_day_period_jul_dec"),
            ("period_1_jan_to_30_jun", date(y + 1, 1, 1), date(y + 1, 6, 30), y + 1, "shortstay.serr_due_month_period_jan_jun",
             "shortstay.serr_due_day_period_jan_jun")):
        d = date(dy, int(figures.get(mkey)), int(figures.get(dkey)))
        roll = roll_due_date_or_statutory(d, COMMONWEALTH, figures)
        due[label] = {"period_start": p_start.isoformat(), "period_end": p_end.isoformat(),
                      "statutory_due": d.isoformat(), "statutory_weekday": d.strftime("%A"), "falls_on_weekend": d.weekday() >= 5,
                      "due": roll.due.isoformat(), "weekday": roll.due.strftime("%A"), "business_day_roll": roll.as_dict()}
        warnings.extend(w for w in roll.warnings if w not in warnings)
        if roll.out_of_range:
            field_refusals.append({"field": f"platform_report_due_dates.{label}", **roll.out_of_range})

    reasons: list[str] = []
    exemptions: list[str] = []
    supplier_amount = property_amount = None
    if inp.booking_entered_date < start:
        status = "not_in_scope"
        reasons.append(f"Booking entered into before {start.isoformat()}, when the regime started for short-term accommodation.")
    elif inp.platform_role == "agent_on_own_site_only":
        status = "not_in_scope"
        reasons.append("A platform that acts only as agent on its own site is not an electronic distribution platform for the regime.")
    else:
        if inp.supplier_is_listed_entity_or_government:
            exemptions.append("supplier is a listed entity, its wholly owned subsidiary, or a government body (LI 2025/5 s 7(1))")
        if inp.supplier_value_12m_gst_inclusive is not None:
            supplier_amount = supplier_cap * (min(inp.days_supplier_active_on_platform_12m, 365) / 365
                                              if inp.days_supplier_active_on_platform_12m else 1)
            if inp.supplier_value_12m_gst_inclusive >= supplier_amount:
                exemptions.append("substantial supplier (LI 2025/5 ss 4 and 7(2))")
        else:
            warnings.append("Supplier value not given, so the substantial supplier exemption was not tested.")
        if inp.property_platform_transactions_12m is not None:
            property_amount = property_cap * (min(inp.days_property_listed_12m, 365) / 365 if inp.days_property_listed_12m else 1)
            if inp.property_platform_transactions_12m >= property_amount:
                exemptions.append("substantial property (LI 2025/5 ss 4 and 8(a)); the ATO describes this as a commercial residential property")
        else:
            warnings.append("Property transaction count not given, so the substantial property exemption was not tested.")
        if inp.another_platform_reports_and_exemption_notified:
            exemptions.append("another platform in the chain reports and the first platform notified the ATO (LI 2025/5 s 6)")
        if inp.booking_has_no_price_and_no_platform_payment:
            exemptions.append("mere booking with no price and no platform payment (LI 2025/5 s 8(c))")
        if inp.supplier_has_no_australian_link_on_all_four_tests:
            exemptions.append("supplier with no Australian link on all four tests (LI 2025/5 s 8(b))")
        if exemptions:
            status = "exempt"
            reasons.append("The platform need not report this transaction: " + "; ".join(exemptions) + ".")
        else:
            status = "reportable"
            reasons.append("Short-term accommodation booking connected with Australia through an electronic distribution platform, no exemption "
                           "shown on the facts given (s 396-55 table item 15).")
    reasons.append("No report does not mean no income: the rent is assessable and must be declared gross whether or not the platform reports it.")
    warnings.append("The report dates are the platform's, not the host's.")
    return {
        "status": status,
        "reasons": reasons,
        "exemptions_triggered": exemptions,
        "host_filing_duty": False,
        "applies_from": start.isoformat(),
        "substantial_supplier_amount_applied": _r(supplier_amount) if supplier_amount is not None else None,
        "substantial_property_amount_applied": _r(property_amount) if property_amount is not None else None,
        "what_is_reported": REPORTED_FIELDS if status == "reportable" else [],
        "platform_report_due_dates": due,
        "assumptions": ["The regime is a reporting duty only: no tax is withheld and no one is registered for GST by it.",
                        "Where a manager or agent holds the listing the reported seller may be the manager, not the owner.",
                        "A report due date that is not a business day moves to the first business day after (TAA 1953 Sch 1 s 388-52; "
                        "Saturday, Sunday or a public holiday for the whole of any State, the ACT or the NT), so `due` is the rolled date "
                        "and `statutory_due` is 31 January or 31 July as printed."],
        "warnings": warnings,
        "field_refusals": field_refusals,
        "risk_flag_ids": ["short-stay-gross-vs-net-platform-income", "short-stay-serr-manager-listing"],
    }


# ====================================================================== serr_income_reconciliation

class PlatformStatement(BaseModel):
    """One platform's figures for the period (all AUD)."""

    platform: str = ""
    guest_payments: float = Field(ge=0, description="Total paid by guests through the platform, including cleaning and host fees charged to guests.")
    cancellation_refunds: float = Field(0, ge=0, description="Refunds for cancellations made through the platform.")
    fees_and_commissions_withheld: float = Field(0, ge=0, description="Platform fees and commissions withheld (GST inclusive).")
    payout_received: float | None = Field(None, ge=0, description="What actually reached the host's account for these bookings.")
    gross_reported_by_platform: float | None = Field(None, ge=0, description="Gross income shown on the platform's annual or half-year statement.")


class ReconciliationInput(BaseModel):
    """Platform statements for a property or host for one income year, and what was declared."""

    statements: list[PlatformStatement] = Field(min_length=1)
    income_declared: float | None = Field(None, ge=0, description="Rental income the client recorded or declared for these bookings.")


@calculator("serr_income_reconciliation", ReconciliationInput)
def serr_income_reconciliation(figures: Figures, inp: ReconciliationInput) -> dict:
    """Reconcile platform statements to the income that must be declared for short-stay letting. Gross income to declare =
    guest payments (including cleaning and host fees charged to guests) less refunds for cancellations through the platform;
    platform fees and commissions are a separate deduction, never netted off income. Also checks the payout (gross less fees)
    against what the host received, the platform's own gross figure against ours, and any declared income against gross
    (the ATO receives gross income, fees, refunds and nights from platforms). Sums several platforms. Use when a host
    declared the net payout or a statement does not tie to the return. Any unexplained difference returns escalation code
    AU-SS-004; it does not decide whether an earlier return needs amending."""
    rows = []
    gross_total = fees_total = payout_total = 0.0
    payout_given_total = 0.0
    all_payouts = True
    any_platform_gross = False
    gross_agrees = True
    for s in inp.statements:
        gross = s.guest_payments - s.cancellation_refunds
        if gross < 0:
            raise InputError(f"refunds exceed guest payments on statement '{s.platform}'")
        expected = gross - s.fees_and_commissions_withheld
        row = {"platform": s.platform, "gross_income": _r(gross), "fees_deduction": _r(s.fees_and_commissions_withheld),
               "expected_payout": _r(expected)}
        if s.payout_received is not None:
            row["payout_difference"] = _r(s.payout_received - expected)
            payout_given_total += s.payout_received
        else:
            all_payouts = False
        if s.gross_reported_by_platform is not None:
            any_platform_gross = True
            row["platform_gross_difference"] = _r(gross - s.gross_reported_by_platform)
            if abs(gross - s.gross_reported_by_platform) > 0.005:
                gross_agrees = False
        rows.append(row)
        gross_total += gross
        fees_total += s.fees_and_commissions_withheld
        payout_total += expected
    warnings: list[str] = []
    flags = ["short-stay-gross-vs-net-platform-income"]
    escalate = False
    out: dict = {"by_platform": rows, "gross_income_to_declare": _r(gross_total), "platform_fees_deduction": _r(fees_total),
                 "expected_payout": _r(payout_total)}
    if all_payouts:
        out["payout_difference"] = _r(payout_given_total - payout_total)
        if abs(payout_given_total - payout_total) > 0.005:
            escalate = True
            warnings.append("The payouts received do not equal gross less fees: check held funds, chargebacks, currency conversion, missing statements or "
                            "fees taken from another account.")
    else:
        out["payout_difference"] = None
    out["platform_gross_agrees"] = gross_agrees if any_platform_gross else None
    if any_platform_gross and not gross_agrees:
        escalate = True
        warnings.append("Our gross (guest payments less refunds) differs from the gross the platform reports for the same period.")
    if inp.income_declared is not None:
        diff = gross_total - inp.income_declared
        out["income_declared"] = _r(inp.income_declared)
        out["income_understated_by"] = _r(diff)
        if abs(diff) > 0.005:
            escalate = True
        if diff > 0.005:
            warnings.append("Declared income is below gross platform income. Declare gross before fees and claim the fees as a deduction; the ATO holds the gross figure.")
        elif diff < -0.005:
            warnings.append("Declared income is more than gross platform income: check for direct bookings, retained bonds or another source before treating it as an error.")
    else:
        out["income_declared"] = None
        out["income_understated_by"] = None
    out["escalation_code"] = "AU-SS-004" if escalate else None
    out.update({"assumptions": ["Amounts are as printed on the statements, in AUD, for the same income year. Cash receipt timing at 30 June for payouts held "
                                "over the year end is not settled here (AU-SS-003)."],
                "warnings": warnings, "risk_flag_ids": flags})
    return out
