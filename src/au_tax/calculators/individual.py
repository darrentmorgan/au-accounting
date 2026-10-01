"""Individual income tax: tax on taxable income, LITO, Medicare levy (with low-income and family
reductions), Medicare levy surcharge and compulsory study-loan (HELP) repayment.

Law: Income Tax Rates Act 1986 (ITRA) Sch 7 and ss18-20; ITAA 1997 Subdiv 61-D (LITO) and, from 2027-28,
Subdiv 61-E (working Australians tax offset, Act No. 49 of 2026 Sch 3);
Medicare Levy Act 1986 (MLA) ss6-9 and 8B-8D; ITAA 1936 s251U (prescribed persons);
Higher Education Support Act 2003 (repayment income and schedule). Every rate and threshold comes
from data/rates/<year>.yaml and its overlays via Figures.
"""

from __future__ import annotations

import math

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from au_tax.figures import FigureError, Figures
from au_tax.registry import Refusal, calculator

WATO_FIRST_YEAR = "2027-28"  # Act No. 49 of 2026 Sch 3 item 4: assessments for 2027-28 and later years

SpecialCircumstance = Literal[
    "deceased_estate",
    "trustee_assessed_income",
    "minor_unearned_income",
    "employment_termination_payment",
    "super_lump_sum",
    "lump_sum_in_arrears",
    "income_averaging",
    "first_home_super_saver_release",
]


class IndividualTaxInput(BaseModel):
    """Inputs for one individual for one income year. Amounts in AUD for the whole income year."""

    taxable_income: float = Field(ge=0, description="Taxable income (assessable income less deductions).")
    residency: Literal["resident", "foreign", "whm"] = Field(
        "resident",
        description="resident = Australian resident for tax purposes (full or part year); foreign = foreign "
        "resident all year; whm = working holiday maker (visa 417/462) who is a foreign resident and whose "
        "taxable income is all working holiday taxable income.")
    resident_months: int = Field(
        12, ge=1, le=12,
        description="Months resident in the year, counting the month residency started or ended. "
        "Less than 12 = part-year resident (reduced tax-free threshold).")
    has_spouse: bool = Field(False, description="Married or de facto on 30 June (Medicare family tests).")
    spouse_taxable_income: float = Field(0, ge=0, description="Spouse's taxable income (family Medicare reduction).")
    spouse_income_for_mls: float | None = Field(
        None, ge=0, description="Spouse's income for MLS purposes; defaults to spouse_taxable_income.")
    dependent_children: int = Field(0, ge=0, description="Dependent children or students (Medicare and MLS family thresholds).")
    private_hospital_cover: bool | None = Field(
        None, description="True if the person and all dependants held appropriate private patient hospital cover "
        "all year. None = not stated (MLS shown as a contingent amount only).")
    days_without_cover: int | None = Field(
        None, ge=0, le=366, description="Days in the year without appropriate hospital cover; defaults to the whole year "
        "when private_hospital_cover is false.")
    has_help_debt: bool = Field(False, description="Has a HELP, VSL, SFSS, SSL, ABSTUDY SSL or AASL debt.")
    help_debt_balance: float | None = Field(None, ge=0, description="Outstanding loan balance; caps the compulsory repayment.")
    reportable_fringe_benefits: float = Field(0, ge=0, description="Reportable fringe benefits amount.")
    net_investment_losses: float = Field(0, ge=0, description="Net financial investment loss plus net rental property loss.")
    reportable_super_contributions: float = Field(0, ge=0, description="Reportable employer super plus deductible personal contributions.")
    exempt_foreign_employment_income: float = Field(0, ge=0, description="Exempt foreign employment income.")
    medicare_full_exemption_days: int | None = Field(
        None, ge=0, le=366, description="Days in a full Medicare levy exemption category (e.g. foreign resident, "
        "not entitled to Medicare benefits). Part-year residents default to the non-resident months.")
    medicare_half_exemption_days: int = Field(0, ge=0, le=366, description="Days in a half exemption category.")
    net_labour_income: float | None = Field(
        None, ge=0, description="2027-28 and later years: net labour income for the working Australians tax offset "
        "(ITAA 1997 s 61-155(2): labour income, business income as an individual and personal services income, less the "
        "deductions for earning it). Leave out if not worked out; the offset is then not applied and the result says so.")
    sapto_eligible: bool = Field(False, description="Might qualify for the seniors and pensioners tax offset.")
    whm_tax_resident: bool = Field(False, description="Working holiday maker who is an Australian resident for tax purposes.")
    whm_other_income: bool = Field(False, description="Working holiday maker with income other than working holiday taxable income.")
    special_circumstances: list[SpecialCircumstance] = Field(
        default_factory=list, description="Any special regime present; each one stops the calculation (AU-IND-001).")
    tax_withheld: float | None = Field(None, ge=0, description="PAYG withheld, to estimate a refund or debt.")

    @model_validator(mode="after")
    def _consistent(self):
        if self.resident_months < 12 and self.residency != "resident":
            raise ValueError("resident_months below 12 is only valid with residency 'resident' (part-year resident)")
        if not self.has_spouse and (self.spouse_taxable_income or self.spouse_income_for_mls):
            raise ValueError("spouse income given but has_spouse is false")
        return self


# ---------------------------------------------------------------- helpers

def _bracket(brackets: list[dict], x: float) -> dict:
    """Bracket whose range contains x, 'from' exclusive and 'to' inclusive (ATO tables: '$45,001 - $135,000')."""
    for b in brackets:
        if x <= (b["to"] if b["to"] is not None else float("inf")) and (x > b["from"] or b["from"] == 0):
            return b
    return brackets[-1]


def _apply(brackets: list[dict], x: float) -> float:
    """base + rate x (x - from), or rate x whole x where whole_income is set."""
    b = _bracket(brackets, x)
    if b.get("whole_income"):
        return b["rate"] * x
    return b["base"] + b["rate"] * (x - b["from"])


def _marginal_sum(brackets: list[dict], x: float, first_from: float | None = None) -> float:
    """Sum of rate x slice for each bracket; first_from replaces the lower edge of the first taxed bracket
    (used for the part-year tax-free threshold, ITRA s20)."""
    total, replaced = 0.0, False
    for b in brackets:
        lo, hi = b["from"], b["to"] if b["to"] is not None else float("inf")
        if b["rate"] > 0 and not replaced and first_from is not None:
            lo, replaced = first_from, True
        if x > lo:
            total += b["rate"] * (min(x, hi) - lo)
    return total


def _r(x: float) -> float:
    return round(x + 0.0, 2)


def _days_in_year(figures: Figures) -> int:
    meta = figures.data.get("meta", {})
    start, end = meta.get("start"), meta.get("end")
    if isinstance(start, date) and isinstance(end, date):
        return (end - start).days + 1
    return 365


def family_reduction(levy: float, ti: float, fi: float, fit: float, levy_rate: float, shade_rate: float,
                     spouse_liable: bool) -> float:
    """MLA s8(2)-(3): reduction = levy_rate x FIT - (shade_rate - levy_rate) x (FI - FIT), apportioned by
    TI / FI when the spouse would also pay levy. Returns the levy after the reduction (not below nil)."""
    if fi <= fit:
        return 0.0
    red = levy_rate * fit - (shade_rate - levy_rate) * (fi - fit)
    if red <= 0:
        return levy
    if spouse_liable and fi > 0:
        red *= ti / fi
    return max(0.0, levy - red)


def _full_exemption_days(inp: IndividualTaxInput, days: int) -> int:
    """Full Medicare exemption days: as given, else the non-resident part of a part-year resident's year."""
    d = inp.medicare_full_exemption_days
    if d is None:
        d = round(days * (12 - inp.resident_months) / 12) if inp.resident_months < 12 else 0
    return min(d, days)


def _screen_above_low_income(figures: Figures, ti: float, family: bool, fi: float, children: int) -> bool:
    """For a year whose low-income thresholds are not yet set: True only if income is above the
    current-law upper limits by a further phase-in ratio margin, so the reduction cannot apply."""
    levy_rate = figures.get("medicare.levy_rate")
    shade = figures.get("medicare.low_income_shade_in_rate")
    ratio = shade / (shade - levy_rate)  # upper limit = lower threshold x this ratio (MLA s7(2))
    if ti <= figures.get("medicare.low_income_current_law_single_upper") * ratio:
        return False
    if family:
        fit = (figures.get("medicare.low_income_current_law_family_lower")
               + figures.get("medicare.low_income_current_law_per_child_lower_add") * children)
        if fi <= fit * ratio * ratio:
            return False
    return True


# ---------------------------------------------------------------- components

def _income_tax(figures: Figures, inp: IndividualTaxInput, ti: float) -> tuple[float, float, float]:
    """Returns (gross tax, tax-free threshold applied, bracket rate at ti)."""
    if inp.residency == "resident":
        rates = figures.get("individual.resident_rates")
        tft = rates[0]["to"]
        if inp.resident_months < 12:
            tft = (figures.get("individual.part_year_tax_free_threshold_flat")
                   + figures.get("individual.part_year_tax_free_threshold_prorated") * inp.resident_months / 12)
            gross = _marginal_sum(rates, ti, first_from=tft)
            rate = 0.0 if ti <= tft else (_bracket(rates, ti)["rate"] or rates[1]["rate"])
            return gross, tft, rate
        return _apply(rates, ti), tft, _bracket(rates, ti)["rate"]
    key = "individual.foreign_resident_rates" if inp.residency == "foreign" else "individual.whm_rates"
    rates = figures.get(key)
    return _apply(rates, ti), 0.0, _bracket(rates, ti)["rate"]


def _lito(figures: Figures, inp: IndividualTaxInput, ti: float) -> float:
    if inp.residency != "resident":
        return 0.0
    return max(0.0, _apply(figures.get("individual.lito"), ti))


def _wato(figures: Figures, inp: IndividualTaxInput, assumptions: list[str], warnings: list[str]) -> tuple[float, dict]:
    """Working Australians tax offset, ITAA 1997 s 61-155 and s 61-160 (2027-28 and later years): for an Australian
    resident at any time in the year whose net labour income is above the tax-free threshold, the lesser of the maximum
    (individual.working_australians_tax_offset_max) and the basic income tax liability on a taxable income made up only
    of the net labour income. Non-refundable, no carry forward (s 63-10). Needs net_labour_income."""
    if inp.residency != "resident":
        return 0.0, {"applies": False, "reason": "not an Australian resident (s 61-155(1)(a))"}
    if figures.income_year < WATO_FIRST_YEAR:
        if inp.net_labour_income is not None:
            warnings.append(f"net_labour_income ignored: the working Australians tax offset starts with the 2027-28 income "
                            f"year (Act No. 49 of 2026 Sch 3 item 4), not {figures.income_year}.")
        return 0.0, {"applies": False, "reason": f"no such offset in {figures.income_year}"}
    if inp.net_labour_income is None:
        warnings.append("Working Australians tax offset (up to the maximum in individual.working_australians_tax_offset_max) "
                        "not applied: give net_labour_income to include it. Without it the tax is overstated by the offset.")
        return 0.0, {"applies": False, "reason": "net_labour_income not given"}
    cap = figures.get("individual.working_australians_tax_offset_max")
    nli = float(math.floor(inp.net_labour_income))
    threshold = figures.get("individual.resident_rates")[0]["to"]  # ITRA s 3(1) tax-free threshold, not the part-year one
    if nli <= threshold:
        return 0.0, {"applies": False, "net_labour_income": _r(nli),
                     "reason": "net labour income does not exceed the tax-free threshold (s 61-155(1)(b))"}
    liability_on_nli = _income_tax(figures, inp, nli)[0]
    amount = min(cap, liability_on_nli)
    assumptions.append("Working Australians tax offset applied on the net labour income given: the lesser of the maximum and "
                       "the basic income tax liability on that income alone (s 61-160); it reduces income tax but cannot "
                       "create a refund.")
    return amount, {"applies": True, "net_labour_income": _r(nli), "basic_income_tax_liability_on_net_labour_income": _r(liability_on_nli),
                    "maximum": cap}


def _medicare_levy(figures: Figures, inp: IndividualTaxInput, ti: float, days: int,
                   assumptions: list[str], warnings: list[str]) -> tuple[float, dict]:
    if inp.residency != "resident":
        assumptions.append("Foreign resident all year: full Medicare levy exemption (prescribed person, ITAA 1936 s251U); no levy or surcharge.")
        return 0.0, {"basis": "exempt (foreign resident)"}
    levy_rate = figures.get("medicare.levy_rate")
    full = levy_rate * ti
    family = inp.has_spouse or inp.dependent_children > 0
    fi = ti + (inp.spouse_taxable_income if inp.has_spouse else 0.0)
    detail: dict = {"levy_before_reductions": _r(full), "family_income": _r(fi) if family else None}
    try:
        lower = figures.get("medicare.low_income_single_lower")
    except FigureError:
        try:
            clear = _screen_above_low_income(figures, ti, family, fi, inp.dependent_children)
        except FigureError:
            clear = False
        if not clear:
            raise
        assumptions.append(
            f"{figures.income_year} Medicare low-income thresholds are not yet set; income is well above the "
            "current-law thresholds (Medicare Levy Act as in force 1 Jul 2026), so no low-income reduction applies.")
        levy = full
        detail["low_income_reduction"] = "not applicable (screened against current-law thresholds)"
    else:
        levy = full
        if ti <= lower:
            levy = 0.0
            detail["low_income_reduction"] = "no levy: taxable income at or below the lower threshold (MLA s7(1))"
        else:
            shade = None
            if family or ti <= figures.get("medicare.low_income_single_upper"):
                shade = figures.get("medicare.low_income_shade_in_rate")
            if shade is not None and shade * (ti - lower) < full:
                levy = shade * (ti - lower)
                detail["low_income_reduction"] = "shade-in applies (MLA s7(2))"
            if family and levy > 0:
                fit = (figures.get("medicare.low_income_family_lower")
                       + figures.get("medicare.low_income_per_child_lower_add") * inp.dependent_children)
                spouse_liable = inp.has_spouse and inp.spouse_taxable_income > lower
                after = family_reduction(levy, ti, fi, fit, levy_rate, shade, spouse_liable)
                detail["family_income_threshold"] = _r(fit)
                if after < levy:
                    detail["family_reduction"] = _r(levy - after)
                    detail["low_income_reduction"] = "family income reduction applies (MLA s8)"
                    if spouse_liable and after == 0:
                        warnings.append("Family reduction may exceed your levy; any excess reduces your spouse's levy (MLA s8(4)), not modelled.")
                levy = after
                if not inp.has_spouse and inp.dependent_children:
                    assumptions.append("Sole parent: assumed family tax benefit was payable for each dependent child (MLA s8(6)).")
    full_days = _full_exemption_days(inp, days)
    if inp.medicare_full_exemption_days is None and full_days:
        assumptions.append(f"Part-year resident: {full_days} non-resident days treated as full Medicare levy exemption days "
                           "(estimated from months; give exact days if known).")
    half_days = min(inp.medicare_half_exemption_days, days - full_days)
    if full_days or half_days:
        levy *= 1 - (full_days + 0.5 * half_days) / days  # MLA s9; half exemption halves the levy for those days
        detail["exemption_days"] = {"full": full_days, "half": half_days, "days_in_year": days}
    return levy, detail


def _mls(figures: Figures, inp: IndividualTaxInput, ti: float, days: int,
         assumptions: list[str], warnings: list[str]) -> tuple[float, dict]:
    if inp.residency != "resident":
        return 0.0, {"applies": False, "reason": "foreign resident"}
    own = (ti + inp.reportable_fringe_benefits + inp.net_investment_losses
           + inp.reportable_super_contributions + (inp.exempt_foreign_employment_income if ti >= 1 else 0.0))
    family = inp.has_spouse or inp.dependent_children > 0
    detail: dict = {"income_for_mls": _r(own)}
    try:
        figures.get("medicare.mls_family_tiers" if family else "medicare.mls_single_tiers")
    except FigureError as e:
        # Tiers not published for the year. The surcharge is nil, whatever the income, for a person (and dependants) with
        # appropriate hospital cover all year, so the figure is not needed then; and when cover is not stated the surcharge
        # is not in the total anyway. Otherwise the amount depends on the missing figure: refuse (AU-GEN-003 or -001).
        if inp.private_hospital_cover is True and inp.days_without_cover is None:
            detail.update({"applies": False, "reason": "appropriate hospital cover all year (surcharge thresholds not needed)"})
            return 0.0, detail
        if inp.private_hospital_cover is None:
            detail.update({"applies": False, "reason": f"hospital cover not stated and the {figures.income_year} surcharge "
                                                       "thresholds are not available, so no contingent amount is shown"})
            warnings.append(f"Hospital cover not stated and the {figures.income_year} Medicare levy surcharge thresholds are not "
                            "available: the surcharge is not included and no contingent amount can be shown. Total liability "
                            "excludes it.")
            return 0.0, detail
        raise e
    if family:
        spouse = inp.spouse_income_for_mls if inp.spouse_income_for_mls is not None else inp.spouse_taxable_income
        combined = own + (spouse if inp.has_spouse else 0.0)
        shift = figures.get("medicare.mls_family_per_child_after_first") * max(0, inp.dependent_children - 1)
        tiers = [{**t, "from": t["from"] + (shift if t["from"] else 0),
                  "to": (t["to"] + shift) if t["to"] is not None else None}
                 for t in figures.get("medicare.mls_family_tiers")]
        tier_income = combined
        detail.update({"family": True, "combined_income_for_mls": _r(combined), "family_tier1_threshold": tiers[0]["to"]})
    else:
        tiers = figures.get("medicare.mls_single_tiers")
        tier_income = own
        detail.update({"family": False, "singles_tier1_threshold": tiers[0]["to"]})
    b = _bracket(tiers, tier_income)
    tier = tiers.index(b)
    rate = b["rate"]
    if rate and inp.has_spouse:
        # MLA s8D(3)(c): own income for MLS must exceed the singles threshold amount
        try:
            own_ok = own > figures.get("medicare.low_income_single_lower")
        except FigureError:
            ratio = figures.get("medicare.low_income_shade_in_rate") / (
                figures.get("medicare.low_income_shade_in_rate") - figures.get("medicare.levy_rate"))
            if own <= figures.get("medicare.low_income_current_law_single_lower") * ratio:
                raise
            own_ok = True
        if not own_ok:
            rate, detail["reason"] = 0.0, "own income for MLS at or below the Medicare lower threshold (MLA s8D(3)(c))"
    if rate and not inp.has_spouse and inp.dependent_children and own <= tiers[0]["to"]:
        rate, detail["reason"] = 0.0, "sole parent: own income for MLS not above the family threshold (MLA s8C(3))"
    base = ti + inp.reportable_fringe_benefits
    full_exempt = _full_exemption_days(inp, days)
    uncovered = inp.days_without_cover if inp.days_without_cover is not None else days
    mls_days = max(0, min(uncovered, days - full_exempt))
    amount = rate * base * mls_days / days
    detail.update({"tier": tier, "rate": rate, "surcharge_base": _r(base), "days_without_cover": mls_days})
    if inp.private_hospital_cover is None:
        detail["applies"] = False
        detail["contingent_amount_if_no_cover"] = _r(amount)
        if amount:
            warnings.append("Hospital cover not stated: MLS not included in the total; it would add the contingent amount shown if the person (or a dependant) lacked appropriate cover.")
        return 0.0, detail
    if inp.private_hospital_cover and inp.days_without_cover is None:
        detail.update({"applies": False, "reason": "appropriate hospital cover all year"})
        return 0.0, detail
    detail["applies"] = amount > 0
    if tier and family:
        assumptions.append("MLS tier set on combined family income for MLS purposes; surcharge applied to own taxable income plus reportable fringe benefits.")
    return amount, detail


def _help(figures: Figures, inp: IndividualTaxInput, ti: float) -> tuple[float, dict]:
    if not inp.has_help_debt:
        return 0.0, {"applies": False}
    ri = (ti + inp.reportable_fringe_benefits + inp.net_investment_losses
          + inp.reportable_super_contributions + inp.exempt_foreign_employment_income)
    amount = _apply(figures.get("help.repayment_schedule"), ri)
    detail = {"applies": True, "repayment_income": _r(ri)}
    if inp.help_debt_balance is not None and amount > inp.help_debt_balance:
        detail["capped_at_balance"] = True
        amount = inp.help_debt_balance
    return amount, detail


def _core(figures: Figures, inp: IndividualTaxInput, ti: float, assumptions: list[str], warnings: list[str]) -> dict:
    days = _days_in_year(figures)
    gross, tft, bracket_rate = _income_tax(figures, inp, ti)
    lito = min(_lito(figures, inp, ti), gross)  # non-refundable
    wato, wato_detail = _wato(figures, inp, assumptions, warnings)
    wato = min(wato, gross - lito)  # both offsets are non-refundable: together they cannot exceed the tax
    levy, levy_detail = _medicare_levy(figures, inp, ti, days, assumptions, warnings)
    return {"gross": gross, "tft": tft, "bracket_rate": bracket_rate, "lito": lito, "wato": wato,
            "wato_detail": wato_detail, "net": gross - lito - wato, "levy": levy, "levy_detail": levy_detail, "days": days}


@calculator("individual_income_tax", IndividualTaxInput)
def individual_income_tax(figures: Figures, inp: IndividualTaxInput) -> dict:
    """Australian individual income tax for one income year (2025-26, 2026-27 or 2027-28; each year reads its own
    rates file, so 2027-28 uses the 2027-28 resident rates): tax on taxable income
    (resident full or part year, foreign resident, or working holiday maker), low income tax offset,
    Medicare levy with low-income and family reductions and exemption days, Medicare levy surcharge
    (tier from income for MLS purposes, single or family thresholds), and compulsory HELP/study loan
    repayment on repayment income. Returns each component, total liability, effective rate, marginal
    rate on the next dollar (income tax and Medicare levy), and a refund/debt estimate if tax_withheld is
    given. Use for "how much tax on $X", "tax payable", "take-home", "Medicare levy surcharge", "HELP
    repayment". From 2027-28 also the working Australians tax offset when net_labour_income is given. Refuses
    (AU-IND-001..004) for special regimes, SAPTO cases, foreign-resident study loans
    and mixed WHM cases; refuses AU-GEN-001 when a needed figure for the year is not yet verified, or AU-GEN-003
    when it has no published value (no draft possible)."""
    if inp.special_circumstances:
        raise Refusal("AU-IND-001", ", ".join(inp.special_circumstances))
    if inp.sapto_eligible:
        raise Refusal("AU-IND-002", "seniors and pensioners tax offset eligibility")
    if inp.residency == "whm" and (inp.whm_tax_resident or inp.whm_other_income):
        raise Refusal("AU-IND-004", "working holiday maker with residency or other-income complications")
    if inp.has_help_debt and inp.residency != "resident":
        raise Refusal("AU-IND-003", "study loan debtor who is a foreign resident")

    assumptions: list[str] = []
    warnings: list[str] = []
    # ATO assessments use whole dollars: cents in taxable income are ignored before rates apply.
    ti = float(math.floor(inp.taxable_income))
    if ti != inp.taxable_income:
        assumptions.append(f"Taxable income {inp.taxable_income:,.2f} rounded down to whole dollars ({ti:,.0f}) "
                           "before applying rates, as the ATO does on assessment.")
    c = _core(figures, inp, ti, assumptions, warnings)
    mls, mls_detail = _mls(figures, inp, ti, c["days"], assumptions, warnings)
    help_amt, help_detail = _help(figures, inp, ti)

    # marginal rate on the next dollar: income tax after LITO plus Medicare levy (MLS/HELP cliffs excluded)
    try:
        nxt = _core(figures, inp, ti + 1, [], [])
        marginal = round((nxt["net"] + nxt["levy"]) - (c["net"] + c["levy"]), 4)
    except FigureError:
        marginal = None

    total = c["net"] + c["levy"] + mls + help_amt
    if inp.residency == "resident" and inp.resident_months < 12:
        assumptions.append(f"Part-year resident for {inp.resident_months} months: tax-free threshold pro-rated (ITRA s20); "
                           "resident rates apply to all taxable income; LITO available in full.")
    if inp.residency == "whm":
        assumptions.append("All taxable income treated as working holiday taxable income (ITRA s3A); no LITO; foreign resident for Medicare.")
    if inp.residency == "foreign":
        assumptions.append("Foreign resident: no tax-free threshold and no LITO.")
    if help_amt:
        assumptions.append("Study loan repayment is compulsory repayment on repayment income; tax offsets do not reduce it.")
    assumptions.append("Only LITO (and, from 2027-28, the working Australians tax offset when net_labour_income is given) is "
                       "applied as an offset; other offsets (franking credits, PHI rebate, SBITO, dependant or zone offsets) are not included.")

    out = {
        "residency": inp.residency,
        "resident_months": inp.resident_months,
        "taxable_income": _r(ti),
        "tax_free_threshold": _r(c["tft"]),
        "gross_tax": _r(c["gross"]),
        "offsets": {"lito": _r(c["lito"]), **({"working_australians_tax_offset": _r(c["wato"]),
                                               "working_australians_tax_offset_detail": c["wato_detail"]}
                                              if figures.income_year >= WATO_FIRST_YEAR else {})},
        "income_tax_after_offsets": _r(c["net"]),
        "medicare_levy": _r(c["levy"]),
        "medicare_levy_detail": c["levy_detail"],
        "medicare_levy_surcharge": _r(mls),
        "mls_detail": mls_detail,
        "help_repayment": _r(help_amt),
        "help_detail": help_detail,
        "total_liability": _r(total),
        "effective_rate": round(total / ti, 4) if ti else 0.0,
        "bracket_rate": c["bracket_rate"],
        "marginal_rate_tax_and_medicare": marginal,
        "assumptions": assumptions,
        "warnings": warnings,
    }
    if inp.tax_withheld is not None:
        out["tax_withheld"] = _r(inp.tax_withheld)
        out["estimated_refund"] = _r(inp.tax_withheld - total)
    return out
