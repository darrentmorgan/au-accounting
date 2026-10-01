"""South Australian state taxes: payroll tax, land tax, and stamp duty on property transfers.

Law: Payroll Tax Act 2009 (SA) s 9 and Sch 1 (annual liability formula), Sch 2 (monthly formula, prescribed
amount); Land Tax Act 1936 (SA) s 5(10) (exemptions) and RevenueSA general and trust scales; Stamp Duties Act
1923 (SA) (conveyance scale, foreign ownership surcharge, qualifying land, s 71DD first home buyer relief).
Every rate, threshold and effective date comes from data/rates/<year>.yaml (base file, key state.sa) and the
overlay data/rates/<year>.d/state_sa.yaml via Figures. South Australia only: other states are refused
(AU-SA-001).
"""

from __future__ import annotations

import math
from datetime import date
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from au_tax.figures import FigureError, Figures
from au_tax.holidays import SA_STATE, roll_due_date, roll_due_date_or_statutory
from au_tax.registry import Refusal, calculator

_SA_NAMES = {"sa", "south australia", "s.a.", "south-australia"}


def _check_state(state: str) -> None:
    if state.strip().lower() not in _SA_NAMES:
        raise Refusal("AU-SA-001", f"requested jurisdiction: {state}")


def _d(x: float | int | str) -> Decimal:
    return Decimal(str(x))


def _money(x: Decimal | float) -> float:
    return float(_d(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _days_in_year(figures: Figures) -> int:
    meta = figures.data.get("meta", {})
    start, end = meta.get("start"), meta.get("end")
    if isinstance(start, date) and isinstance(end, date):
        return (end - start).days + 1
    return 365


def _date_fig(figures: Figures, key: str) -> date:
    n = int(figures.get(key))
    return date(n // 10000, (n // 100) % 100, n % 100)


def sa_monthly_return_due(figures: Figures, wages_year: int, wages_month: int, strict: bool = True) -> dict:
    """Due date of the RevenueSA monthly payroll tax return and payment for wages paid in the given month.
    The 7th of the following month (Payroll Tax Act 2009 (SA) s 9(1)(a)), moved to the next business day under the
    sa_state_tax regime (SA public holidays only; RevenueSA monthly returns page). RevenueSA's published extension for
    the December return, where the rates file has one, replaces the ordinary date (then rolled if needed).
    strict (default) refuses AU-GEN-004 for a date after the holiday data; strict=False returns the unrolled date with a
    warning and the note in business_day_roll["refusal"] (for callers where the date is not the main result)."""
    day = int(figures.get("state.sa.payroll_tax_monthly_due_day"))
    ny, nm = (wages_year + 1, 1) if wages_month == 12 else (wages_year, wages_month + 1)
    ordinary = date(ny, nm, day)
    original, extension, warnings = ordinary, False, []
    if wages_month == 12:
        try:
            original, extension = _date_fig(figures, "state.sa.payroll_tax_december_return_due_yyyymmdd"), True
        except FigureError:
            warnings.append("RevenueSA may extend the December return over the Christmas and New Year period; it has published no "
                            "extension date for this year, so the ordinary due date is used. Check RevenueSA's monthly returns page.")
    roll = (roll_due_date if strict else roll_due_date_or_statutory)(original, SA_STATE, figures)
    warnings.extend(roll.warnings)
    return {"wages_month": f"{wages_year}-{wages_month:02d}", "ordinary_due_date": ordinary.isoformat(),
            "published_extension": extension, "original_date": original.isoformat(), "due_date": roll.due.isoformat(),
            "business_day_roll": roll.as_dict(), "warnings": warnings}


def sa_reconciliation_due(figures: Figures, financial_year_end: date, strict: bool = True) -> dict:
    """Due date of the annual payroll tax reconciliation (28 July after the financial year, RevenueSA), next business day rule.
    strict as sa_monthly_return_due."""
    orig = date(financial_year_end.year, 7, int(figures.get("state.sa.payroll_tax_annual_reconciliation_due_day_july")))
    roll = (roll_due_date if strict else roll_due_date_or_statutory)(orig, SA_STATE, figures)
    return {"original_date": orig.isoformat(), "due_date": roll.due.isoformat(), "business_day_roll": roll.as_dict(),
            "warnings": roll.warnings}


def _per_100_scale(brackets: list[dict], value: float) -> Decimal:
    """RevenueSA scale: base + (rate per $100) x number of $100 units, or part, above 'from'.
    Bracket is the last one whose 'from' is below the value (bands are 'exceeds from, up to and including to')."""
    v = _d(value)
    if v <= 0:
        return Decimal(0)
    chosen = brackets[0]
    for b in brackets:
        if v > _d(b["from"]):
            chosen = b
    units = math.ceil((v - _d(chosen["from"])) / Decimal(100))
    return _d(chosen["base"]) + _d(chosen["rate"]) * 100 * units


# ====================================================================== payroll tax

class SAPayrollTaxInput(BaseModel):
    """One employer for one period. Amounts in AUD."""

    state: str = Field("SA", description="Jurisdiction. Only SA is supported; anything else is refused (AU-SA-001).")
    period: Literal["annual", "monthly"] = Field(
        "annual", description="annual = full-year (or part-year) liability or reconciliation; monthly = one monthly return.")
    sa_taxable_wages: float = Field(
        ge=0, description="This employer's SA taxable wages in the period (the year for annual, the month for monthly).")
    annual_sa_taxable_wages: float | None = Field(
        None, ge=0, description="This employer's SA taxable wages for the whole financial year (actual, or the estimate declared "
        "for monthly returns). Defaults to sa_taxable_wages when period is annual; required when period is monthly.")
    annual_interstate_wages: float = Field(
        0, ge=0, description="Wages taxable in other states or territories for the year (interstate wages). Counts toward the "
        "threshold and rate, reduces the SA deduction.")
    days_employing: int | None = Field(
        None, ge=1, le=366, description="Days in the financial year on which the employer (or, for a group, any member) paid or "
        "was liable to pay taxable or interstate wages. Defaults to the whole year. Set for part-year employers.")
    group_status: Literal["none", "designated_group_employer", "group_member"] = Field(
        "none", description="none = not in a group; designated_group_employer = the DGE (claims the group's deduction); "
        "group_member = another member (no deduction, pays the rate on its own SA wages).")
    group_annual_sa_taxable_wages: float | None = Field(
        None, ge=0, description="Total SA taxable wages of ALL group members for the year. Required for group members and the DGE.")
    group_annual_interstate_wages: float = Field(
        0, ge=0, description="Total interstate wages of all group members for the year.")
    indicative_rate_2dp: bool = Field(
        False, description="False (default) = statutory exact rate. True = truncate the variable rate to 2 decimal places of a "
        "percent, as RevenueSA's worked examples for monthly returns do. The annual reconciliation uses the exact formula.")
    wages_month: str | None = Field(
        None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$", description="period monthly only: the month the wages were paid, as YYYY-MM "
        "(for example 2027-02). Gives the return and payment due date for that month; leave out to skip it.")
    special_circumstances: list[Literal["grouping_disputed", "contractor_determination_needed"]] = Field(
        default_factory=list, description="Any of these stops the calculation (AU-SA-002).")

    @model_validator(mode="after")
    def _consistent(self):
        if self.wages_month and self.period != "monthly":
            raise ValueError("wages_month only applies when period is monthly")
        if self.period == "monthly" and self.annual_sa_taxable_wages is None:
            raise ValueError("period monthly needs annual_sa_taxable_wages (declared or estimated annual SA wages)")
        if self.group_status != "none" and self.group_annual_sa_taxable_wages is None:
            raise ValueError("group_status needs group_annual_sa_taxable_wages")
        if self.group_status == "none" and (self.group_annual_sa_taxable_wages or self.group_annual_interstate_wages):
            raise ValueError("group wages given but group_status is none")
        own = self.annual_sa_taxable_wages if self.annual_sa_taxable_wages is not None else self.sa_taxable_wages
        if self.group_annual_sa_taxable_wages is not None and own > self.group_annual_sa_taxable_wages:
            raise ValueError("this employer's annual SA wages cannot exceed the group's SA wages")
        return self


@calculator("sa_payroll_tax", SAPayrollTaxInput)
def sa_payroll_tax(figures: Figures, inp: SAPayrollTaxInput) -> dict:
    """South Australian payroll tax for one employer, for a whole financial year (annual liability or annual
    reconciliation) or for one monthly return. Applies the Payroll Tax Act 2009 (SA) formulas: nil while annualised
    Australian taxable wages (SA plus interstate, or the group's) are at or below the threshold, a variable rate
    between the threshold and the top of the band, the top rate above it, applied to SA taxable wages less a flat
    deduction (reduced for part-year employing, interstate wages and group membership; only the designated group
    employer claims a group's deduction). Inputs: SA taxable wages for the period, annual SA estimate (monthly),
    interstate wages, days employing, group status and group wages. Returns the rate, deduction, tax and the
    return due dates (annual reconciliation always; the monthly return for wages_month), rolled over weekends and SA public holidays;
    a due date after the public holiday data range is returned unrolled with a warning and a field_refusals entry (AU-GEN-004) and the tax is still given. Use for "how much SA payroll tax", "do I owe payroll tax in SA", "monthly payroll tax return",
    "payroll tax with interstate wages or a group". Refuses other states (AU-SA-001) and grouping or contractor
    determinations (AU-SA-002); it does not decide what counts as wages."""
    _check_state(inp.state)
    if inp.special_circumstances:
        raise Refusal("AU-SA-002", ", ".join(inp.special_circumstances))

    ta = _d(figures.get("state.sa.payroll_tax_threshold_annual"))
    top_rate = _d(figures.get("state.sa.payroll_tax_rate"))
    band_top = _d(figures.get("state.sa.payroll_tax_variable_band_top"))
    width = _d(figures.get("state.sa.payroll_tax_variable_band_width"))
    ea = _d(figures.get("state.sa.payroll_tax_max_deduction_annual"))
    monthly_due = int(figures.get("state.sa.payroll_tax_monthly_due_day"))
    recon_day = int(figures.get("state.sa.payroll_tax_annual_reconciliation_due_day_july"))
    june_day = int(figures.get("state.sa.payroll_tax_june_payment_due_day_act"))

    fy = _d(_days_in_year(figures))
    c = _d(inp.days_employing) if inp.days_employing else fy
    assumptions: list[str] = []
    warnings: list[str] = []

    tw = _d(inp.annual_sa_taxable_wages if inp.annual_sa_taxable_wages is not None else inp.sa_taxable_wages)
    iw = _d(inp.annual_interstate_wages)
    grouped = inp.group_status != "none"
    if grouped:
        base_tw = _d(inp.group_annual_sa_taxable_wages)
        base_iw = _d(inp.group_annual_interstate_wages)
    else:
        base_tw, base_iw = tw, iw

    total = base_tw + base_iw                      # SA taxable plus interstate wages (group or employer)
    threshold_amount = ta * c / fy                 # Sch 1 cl 4 / cl 8: C/FY x TA
    tarw = (total * fy / c) if c else Decimal(0)   # total annualised relevant wages

    if total <= threshold_amount:
        band, rate = "nil", Decimal(0)
    elif tarw > band_top:
        band, rate = "top", top_rate
    else:
        band = "variable"
        rate = top_rate * (tarw - ta) / width
    if inp.indicative_rate_2dp and band == "variable":
        rate = rate.quantize(Decimal("0.0001"), rounding=ROUND_DOWN)
        assumptions.append("Variable rate truncated to 2 decimal places of a percent (RevenueSA indicative rate); the annual "
                           "reconciliation uses the exact statutory formula, so a small difference can arise.")

    # deduction: EA x SA share of Australian wages x C/FY (Sch 1 cl 5(1) and cl 9(2); monthly D = EA/12 in Sch 2 cl 6(3))
    share = (base_tw / total) if total else Decimal(0)
    annual_deduction = ea * share * c / fy
    entitled = inp.group_status != "group_member"
    wages_in_period = _d(inp.sa_taxable_wages)
    if inp.period == "annual":
        deduction = annual_deduction if entitled else Decimal(0)
    else:
        deduction = (annual_deduction / 12) if entitled else Decimal(0)

    if band == "nil":
        tax = Decimal(0)
        net = Decimal(0)
    else:
        net = max(Decimal(0), wages_in_period - deduction)
        tax = net * rate
    unused_deduction = max(Decimal(0), deduction - wages_in_period) if band != "nil" else Decimal(0)

    if grouped:
        assumptions.append(
            "Group: the threshold and rate are tested on the group's total Australian taxable wages; only the designated "
            "group employer claims the deduction; other members pay the rate on their own SA taxable wages.")
        if unused_deduction > 0 and inp.group_status == "designated_group_employer":
            warnings.append("The designated group employer's deduction exceeds its own wages; the unused part can be allocated "
                            "to other group members at the annual reconciliation (RevenueSA).")
    if inp.days_employing:
        assumptions.append("Part-year: the threshold and the deduction are pro-rated by days employing / days in the year, and "
                           "the rate is set on annualised wages.")
    if iw or base_iw:
        assumptions.append("Interstate wages count toward the threshold and rate but the deduction is scaled by the SA share of "
                           "Australian wages.")
    if inp.period == "monthly":
        assumptions.append("Monthly return: rate and deduction are based on the annual SA and interstate wages declared or "
                           "estimated for the year; differences are settled at the annual reconciliation (Payroll Tax Act 2009 (SA) s 83).")
    warnings.append("This tool takes taxable wages as an input. It does not decide what is wages (including contractor payments "
                    "under relevant contracts, superannuation, fringe benefits, allowances, employment agents) or where wages are "
                    "taxable (nexus, s 11).")
    warnings.append("Payroll Tax Act 2009 (SA) Sch 2 cl 21: cents are disregarded when amounts in a formula are calculated; RevenueSA "
                    "Online produces the assessed amount. Treat cents here as indicative.")

    fy_end = figures.data["meta"]["end"]
    # The due dates are secondary to the tax amount: a date after the holiday data is returned unrolled with a field refusal
    # (AU-GEN-004), not by refusing the tax (sa_payroll_tax for 2027-28 always has the 28 Jul 2028 reconciliation date).
    due_dates: dict = {"annual_reconciliation": sa_reconciliation_due(figures, fy_end, strict=False)}
    if inp.wages_month:
        wy, wm = int(inp.wages_month[:4]), int(inp.wages_month[5:7])
        if not figures.data["meta"]["start"] <= date(wy, wm, 1) <= fy_end:
            warnings.append(f"Wages month {inp.wages_month} is outside the {figures.income_year} financial year; the rates and "
                            "figures used are for that year, so check the year.")
        due_dates["monthly_return"] = sa_monthly_return_due(figures, wy, wm, strict=False)
    field_refusals: list[dict] = []
    for name, dd in due_dates.items():
        warnings.extend(w for w in dd.pop("warnings") if w not in warnings)
        if "refusal" in dd["business_day_roll"]:
            field_refusals.append({"field": f"due_dates.{name}", **dd["business_day_roll"]["refusal"]})
    assumptions.append("Due dates use the SA business-day rule (Saturday, Sunday or an SA public holiday, Public Holidays Act 2023 (SA) s 8; "
                       "RevenueSA accepts lodgement and payment on the next business day). Other States' holidays do not move an SA state tax date.")

    return {
        "state": "SA",
        "period": inp.period,
        "days_in_year": int(fy),
        "days_employing": int(c),
        "group_status": inp.group_status,
        "threshold_amount_for_period_of_employing": _money(threshold_amount),
        "australian_taxable_wages_tested": _money(total),
        "annualised_wages_for_rate": _money(tarw),
        "rate_band": band,
        "rate_applied": float(rate),
        "rate_applied_percent": float((rate * 100).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)),
        "wages_in_period": _money(wages_in_period),
        "deduction_applied": _money(deduction),
        "unused_deduction": _money(unused_deduction),
        "wages_after_deduction": _money(net),
        "payroll_tax": _money(tax),
        "due": {
            "monthly_return_and_payment": f"day {monthly_due} of the month after the wages month (next business day if a weekend or SA public holiday)",
            "annual_reconciliation_revenuesa": f"{recon_day} July after the financial year (RevenueSA published date; next business day if a weekend or SA public holiday)",
            "june_tax_payable_under_act_s9_1_b": f"within {june_day} days after the end of June (statute); RevenueSA administers June through the annual reconciliation",
        },
        "due_dates": due_dates,
        "field_refusals": field_refusals,
        "assumptions": assumptions,
        "warnings": warnings,
    }


# ====================================================================== land tax

class Parcel(BaseModel):
    """One parcel of land held by the same owner at midnight on 30 June before the financial year."""

    site_value: float = Field(ge=0, description="Site value (unimproved value) set by the Valuer-General, not capital value.")
    exemption: Literal["none", "principal_place_of_residence", "primary_production"] = Field(
        "none", description="Exemption the owner qualifies for on the facts (stated, not decided here).")
    business_floor_area_percent: float = Field(
        0, ge=0, le=100, description="Principal place of residence only: share of total building floor area used for business "
        "or commercial purposes (other than primary production).")


class SALandTaxInput(BaseModel):
    """Land tax for one ownership for one financial year. Amounts in AUD."""

    state: str = Field("SA", description="Jurisdiction. Only SA is supported (AU-SA-001 otherwise).")
    ownership_type: Literal["general", "trust"] = Field(
        "general", description="general = individuals, companies and trusts assessed at general rates; trust = trusts that do not "
        "meet the general-rate criteria (for example discretionary trust land acquired after 16 October 2019).")
    parcels: list[Parcel] = Field(default_factory=list, description="Each parcel with its site value and exemption.")
    total_site_value: float | None = Field(
        None, ge=0, description="Shortcut: combined site value of all taxable land, no exemptions. Use instead of parcels.")
    foreign_owner: bool = Field(False, description="Owner is a foreign person. SA has no land tax surcharge; noted in the output.")
    assessment_due_date: date | None = Field(
        None, description="The payment due date printed on the land tax assessment notice. Gives the payment date; if it is not a "
        "business day in SA the rolled date is shown as a labelled assumption.")
    special_circumstances: list[Literal[
        "exemption_disputed", "corporate_reconstruction", "trust_designated_beneficiary", "corporate_group_aggregation",
        "deceased_estate", "unit_trust_or_landholder"]] = Field(
        default_factory=list, description="Any of these stops the calculation (AU-SA-003 or AU-SA-004).")

    @model_validator(mode="after")
    def _one_source(self):
        if bool(self.parcels) == (self.total_site_value is not None):
            raise ValueError("give either parcels or total_site_value, not both and not neither")
        return self


@calculator("sa_land_tax", SALandTaxInput)
def sa_land_tax(figures: Figures, inp: SALandTaxInput) -> dict:
    """South Australian land tax for one ownership for the financial year of the income_year given (2025-26 or
    2026-27), assessed on the total taxable site value of all land the owner holds at midnight on 30 June before that
    year. Applies the general scale or the trust scale (per $100 or part of $100), the principal place of residence
    exemption (full below the business-use limit, stepped partial exemption up to the upper limit), the primary
    production exemption as stated by the owner, and the minimum assessment rule (no assessment where tax is under
    the minimum). Use for "how much land tax on SA property", "land tax on my investment properties in Adelaide",
    "trust land tax rates". Notes that SA has no foreign owner land tax surcharge. With assessment_due_date it shows the
    payment date and, as a labelled assumption only (RevenueSA states no rule), the next business day under Public Holidays Act 2023 (SA) s 8(2). Refuses other states (AU-SA-001),
    disputed exemptions and reconstructions (AU-SA-003), and trust, group, estate and landholder complexities
    (AU-SA-004)."""
    _check_state(inp.state)
    sc = set(inp.special_circumstances)
    if sc & {"exemption_disputed", "corporate_reconstruction"}:
        raise Refusal("AU-SA-003", ", ".join(sorted(sc)))
    if sc:
        raise Refusal("AU-SA-004", ", ".join(sorted(sc)))

    if inp.ownership_type == "general":
        scale = figures.get("state.sa.land_tax_general_scale")
        threshold = figures.get("state.sa.land_tax_general_threshold")
    else:
        scale = figures.get("state.sa.land_tax_trust_scale")
        threshold = figures.get("state.sa.land_tax_trust_threshold")
    minimum = _d(figures.get("state.sa.land_tax_minimum_assessment"))
    assumptions: list[str] = []
    warnings: list[str] = []

    parcels = inp.parcels or [Parcel(site_value=inp.total_site_value or 0)]
    detail, total, taxable = [], Decimal(0), Decimal(0)
    n_ppr = sum(1 for p in parcels if p.exemption == "principal_place_of_residence")
    for p in parcels:
        sv = _d(p.site_value)
        total += sv
        frac = Decimal(1)
        if p.exemption == "principal_place_of_residence":
            full_below = _d(figures.get("state.sa.land_tax_ppr_full_exemption_business_area_below_pct"))
            upper = _d(figures.get("state.sa.land_tax_ppr_partial_max_business_area_pct"))
            step = _d(figures.get("state.sa.land_tax_ppr_partial_step_pct"))
            u = _d(p.business_floor_area_percent)
            if u < full_below:
                frac = Decimal(0)
            elif u <= upper:
                frac = (step * (u // step)) / 100          # taxable share; reduction = 100 - step x floor(u/step)
            else:
                frac = Decimal(1)
                warnings.append("Business use above the upper limit: no principal place of residence exemption for that parcel.")
        elif p.exemption == "primary_production":
            frac = Decimal(0)
        t = sv * frac
        taxable += t
        detail.append({"site_value": _money(sv), "exemption": p.exemption, "taxable_site_value": _money(t)})
    if n_ppr > 1:
        warnings.append("More than one parcel is marked principal place of residence; a person can have only one principal place of "
                        "residence (RevenueSA), so check the exemption applies to each.")
    if any(p.exemption == "primary_production" for p in parcels):
        assumptions.append("Primary production exemption taken as stated: land of at least the minimum area used wholly or mainly for "
                           "the business of primary production; inside the defined rural area extra owner conditions apply "
                           "(Land Tax Act 1936 (SA) s 5(10)(g)).")
    if any(p.exemption == "principal_place_of_residence" for p in parcels):
        assumptions.append("Principal place of residence exemption taken as stated: owned and occupied by a natural person on an "
                           "ongoing basis at midnight on 30 June, buildings predominantly residential.")

    tax = _per_100_scale(scale, float(taxable)) if taxable > 0 else Decimal(0)
    raw = tax
    assessed = True
    if taxable > _d(threshold) and tax < minimum:
        tax, assessed = Decimal(0), False
        warnings.append("Calculated land tax is under the minimum assessment amount, so no assessment is issued.")
    elif tax == 0:
        assessed = False

    if inp.ownership_type == "trust":
        assumptions.append("Trust scale applied: the user states the land is held on trust and does not qualify for general rates. "
                           "Fixed and unit trusts with notified beneficiaries or unitholders, and pre-17 October 2019 discretionary "
                           "trusts with a designated beneficiary, use the general scale.")
    if inp.foreign_owner:
        warnings.append("SA has no foreign owner land tax surcharge (none in the Land Tax Act 1936 or on RevenueSA pages); the SA "
                        "foreign ownership surcharge applies to stamp duty only. Some relief, such as the off-the-plan land tax "
                        "relief for 2017-18 contracts, is not extended to foreign purchasers.")
    assumptions.append("Site values are the Valuer-General's values at midnight on 30 June before the financial year; land held under "
                       "the same ownership is aggregated. Related corporations are aggregated as a group (not modelled).")

    payment_due = None
    if inp.assessment_due_date:
        roll = roll_due_date_or_statutory(inp.assessment_due_date, SA_STATE, figures)
        payment_due = {"assessment_due_date": inp.assessment_due_date.isoformat(), "assumed_due_date": roll.due.isoformat(),
                       "assumed_roll_applied": roll.rolled, "business_day_roll": roll.as_dict()}
        warnings.extend(roll.warnings)
        assumptions.append(
            "ASSUMPTION (not a RevenueSA statement): the payment due date is the date on the assessment. RevenueSA's payment pages say "
            "to pay by that date and say nothing about weekends or public holidays, and neither the Land Tax Act 1936 (SA) nor the "
            "Taxation Administration Act 1996 (SA) has a roll provision. Public Holidays Act 2023 (SA) s 8(2) probably moves an "
            "obligation to pay on a Saturday, Sunday or public holiday to the next day that is not one"
            + (f", which would make it {roll.due.isoformat()}" if roll.rolled else
               " (cannot be checked here: the assessment date is after the public holiday data)" if roll.out_of_range else
               " (not needed here: the assessment date is a business day)")
            + ". Pay by the assessment date to be safe, or confirm with RevenueSA.")

    return {
        "state": "SA",
        "financial_year": figures.income_year,
        "ownership_type": inp.ownership_type,
        "scale": "trust" if inp.ownership_type == "trust" else "general",
        "threshold": threshold,
        "total_site_value": _money(total),
        "exempt_site_value": _money(total - taxable),
        "taxable_site_value": _money(taxable),
        "land_tax_before_minimum": _money(raw),
        "assessment_issued": assessed,
        "land_tax": _money(tax),
        "parcels": detail,
        "payment_due": payment_due,
        "field_refusals": ([{"field": "payment_due", **roll.out_of_range}] if payment_due and roll.out_of_range else []),
        "assumptions": assumptions,
        "warnings": warnings,
    }


# ====================================================================== stamp duty

class SAStampDutyInput(BaseModel):
    """One SA property transfer. Amounts in AUD."""

    state: str = Field("SA", description="Jurisdiction. Only SA is supported (AU-SA-001 otherwise).")
    dutiable_value: float = Field(
        ge=0, description="Dutiable value: the greater of the consideration (including GST) and the market value of the land "
        "and improvements. For a part interest, the value of the interest transferred.")
    property_type: Literal["residential", "primary_production", "qualifying_non_residential"] = Field(
        "residential", description="residential (includes vacant land zoned residential) and primary_production are dutiable; "
        "qualifying_non_residential (commercial, industrial, hotel, motel and similar land use codes) has no duty for "
        "instruments from 1 July 2018.")
    contract_date: date = Field(description="Date the contract was entered into (controls first home buyer relief).")
    first_home_buyer_new_home: bool = Field(
        False, description="True only if the purchasers meet every first home buyer relief condition for a new home, off-the-plan "
        "apartment or vacant land to build on (no prior relevant interest in residential property for spouses either, "
        "residence requirement, citizen or permanent resident). Relief does not apply to established homes.")
    foreign_person: bool = Field(False, description="A purchaser is a foreign person, corporation or foreign trust.")
    foreign_interest_percent: float = Field(
        100, gt=0, le=100, description="Percentage of the dutiable value acquired by foreign persons (surcharge base).")
    seniors_downsizing_relief_claimed: bool = Field(False, description="Seniors downsizing relief is being claimed (refused).")
    special_circumstances: list[Literal[
        "landholder", "unit_trust", "trust_acquisition", "partnership_transfer", "corporate_reconstruction",
        "family_or_estate_transfer", "deceased_estate"]] = Field(
        default_factory=list, description="Any of these stops the calculation (AU-SA-004).")


@calculator("sa_stamp_duty_transfer", SAStampDutyInput)
def sa_stamp_duty_transfer(figures: Figures, inp: SAStampDutyInput) -> dict:
    """South Australian stamp duty (conveyance duty) on a property transfer: the general scale on the dutiable
    value (per $100 or part of $100), nil duty on qualifying non-residential land for instruments from 1 July 2018,
    full first home buyer relief for a new home, off-the-plan apartment or vacant land (contracts from 13 February
    2025, which does not reduce the foreign ownership surcharge), and the 7% foreign ownership surcharge on
    residential land acquired by foreign persons. Inputs: dutiable value, property type, contract date, first home
    buyer new-home flag, foreign person flag and interest share. Returns duty before relief, relief, duty payable,
    surcharge and total. Use for "stamp duty on an Adelaide purchase", "first home buyer relief in SA", "foreign buyer
    surcharge SA", "duty on a commercial property in SA". Refuses other states (AU-SA-001), downsizer relief
    (AU-SA-005), dates outside the supported range (AU-SA-006), trusts, landholder and reconstruction transfers
    (AU-SA-004). Does not include Land Services SA registration or transfer fees."""
    _check_state(inp.state)
    if inp.seniors_downsizing_relief_claimed:
        raise Refusal("AU-SA-005", "seniors downsizing stamp duty relief")
    if inp.special_circumstances:
        raise Refusal("AU-SA-004", ", ".join(inp.special_circumstances))

    qual_from = _date_fig(figures, "state.sa.stamp_duty_qualifying_land_nil_duty_from")
    fhb_from = _date_fig(figures, "state.sa.stamp_duty_fhb_full_relief_contracts_from")
    fos_from = _date_fig(figures, "state.sa.stamp_duty_foreign_surcharge_from")
    if inp.contract_date < qual_from:
        raise Refusal("AU-SA-006", f"contract dated {inp.contract_date.isoformat()}, before {qual_from.isoformat()}")
    if inp.first_home_buyer_new_home and inp.contract_date < fhb_from:
        raise Refusal("AU-SA-006", f"first home buyer relief claimed on a contract dated {inp.contract_date.isoformat()}, before {fhb_from.isoformat()}")

    assumptions: list[str] = []
    warnings: list[str] = []
    v = _d(inp.dutiable_value)

    if inp.property_type == "qualifying_non_residential":
        duty = Decimal(0)
        assumptions.append("Qualifying land (non-residential, non-primary-production): no duty on a conveyance or transfer executed "
                           "on or after 1 July 2018 arising from a contract entered into on or after that date (RevenueSA real "
                           "property page). RevenueSA relies on Valuer-General land use codes; mixed-use or residential-coded land "
                           "(including land used for short-term letting) may be dutiable.")
    else:
        duty = _per_100_scale(figures.get("state.sa.stamp_duty_conveyance_scale"), inp.dutiable_value)

    relief = Decimal(0)
    if inp.first_home_buyer_new_home:
        if inp.property_type == "qualifying_non_residential":
            warnings.append("First home buyer relief is irrelevant to qualifying non-residential land: no duty applies anyway.")
        else:
            relief = duty
            assumptions.append("First home buyer relief applied in full (contract on or after the relief start date): eligibility "
                               "is as stated by the user (new home, off-the-plan apartment or vacant land to build on; no prior "
                               "relevant interest in residential property by purchasers or spouses; each purchaser to live there "
                               "6 continuous months within the required window). Relief is clawed back if conditions are not met.")
            if inp.foreign_person:
                warnings.append("At least one purchaser must be an Australian citizen or permanent resident for first home buyer "
                                "relief; confirm eligibility.")

    surcharge = Decimal(0)
    if inp.foreign_person:
        if inp.contract_date < fos_from:
            warnings.append("Foreign ownership surcharge applies only to instruments executed on or after its start date.")
        elif inp.property_type == "residential":
            rate = _d(figures.get("state.sa.stamp_duty_foreign_ownership_surcharge"))
            surcharge = v * _d(inp.foreign_interest_percent) / 100 * rate
            if inp.first_home_buyer_new_home:
                assumptions.append("First home buyer relief is not applied to the foreign ownership surcharge for contracts from the "
                                   "relief start date.")
        else:
            assumptions.append("The foreign ownership surcharge applies to residential land only; none charged for this property type.")

    payable = duty - relief
    return {
        "state": "SA",
        "property_type": inp.property_type,
        "contract_date": inp.contract_date.isoformat(),
        "dutiable_value": _money(v),
        "duty_before_relief": _money(duty),
        "first_home_buyer_relief": _money(relief),
        "duty_payable": _money(payable),
        "foreign_ownership_surcharge": _money(surcharge),
        "total_duty_and_surcharge": _money(payable + surcharge),
        "assumptions": assumptions,
        "warnings": warnings + [
            "Land Services SA registration and transfer fees are not included.",
            "Seniors downsizing relief is not modelled (start date and conditions unverified).",
        ],
    }
