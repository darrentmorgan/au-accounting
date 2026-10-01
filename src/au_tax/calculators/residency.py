"""Residency and cross-border: individual residency indicators, foreign income tax offset (Div 770),
Australia-Indonesia treaty checks, and a scope check that returns the verbatim escalation message.

Law: ITAA 1936 s 6(1) (resident) as explained in TR 2023/1; ITAA 1997 Div 770 (s 770-10 amount, s 770-75
offset limit); ITAA 1936 s 23AG; ITAA 1997 Subdiv 768-R; Australia-Indonesia double tax agreement Arts 4, 10-15.
Every threshold and treaty rate comes from data/rates/<year>.d/residency.yaml via Figures.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from au_tax.calculators.individual import IndividualTaxInput, _core, _mls, _r
from au_tax.figures import Figures
from au_tax.registry import Refusal, calculator, refusal_catalogue

Where = Literal["australia", "overseas", "both", "none"]
Intention = Literal["settle_australia", "return_to_australia_foreseen", "stay_overseas_indefinitely", "visit_only", "unsure"]


def _days_in_year(figures: Figures) -> int:
    meta = figures.data.get("meta", {})
    start, end = meta.get("start"), meta.get("end")
    if isinstance(start, date) and isinstance(end, date):
        return (end - start).days + 1
    return 365


def _escalation(code: str) -> dict:
    entry = refusal_catalogue()[code]
    return {"code": code, "message": entry["message"], "route": entry.get("route")}


# ======================================================================= foreign income tax offset

FitoComplication = Literal[
    "deferred_non_commercial_business_loss",
    "foreign_loss_component",
    "attribution_account_payment",
    "jpda_income",
    "foreign_tax_paid_in_different_year",
    "foreign_tax_refunded",
]


class FitoInput(BaseModel):
    """Foreign income tax offset for a resident individual for one income year. AUD, whole year, all foreign
    amounts already converted to AUD."""

    foreign_tax_paid: float = Field(ge=0, description="Total foreign income tax paid that counts towards the offset (s 770-10), in AUD.")
    taxable_income: float = Field(ge=0, description="Taxable income for the year (including the foreign income).")
    foreign_net_income: float = Field(
        0, ge=0, description="Step 2 amount: foreign-taxed income plus other non-Australian-source income, less "
        "deductions reasonably related to it (debt deductions only for an overseas permanent establishment). "
        "Taxable income is reduced by this to work out the limit. Not needed when foreign_tax_paid is at or below the "
        "default limit and claim_default_limit_only is not in play.")
    claim_default_limit_only: bool = Field(
        False, description="True if the taxpayer chooses to claim only the default limit rather than compute the limit "
        "(s 770-75 Note 1). The rest of the foreign tax is then lost.")
    resident_months: int = Field(12, ge=1, le=12, description="Months resident (part-year residents use the reduced tax-free threshold).")
    has_spouse: bool = False
    spouse_taxable_income: float = Field(0, ge=0)
    dependent_children: int = Field(0, ge=0)
    private_hospital_cover: bool | None = Field(None, description="None = not stated: MLS is left out of both steps and a warning is given.")
    days_without_cover: int | None = Field(None, ge=0, le=366)
    reportable_fringe_benefits: float = Field(0, ge=0)
    net_investment_losses: float = Field(0, ge=0)
    reportable_super_contributions: float = Field(0, ge=0)
    exempt_foreign_employment_income: float = Field(0, ge=0)
    complications: list[FitoComplication] = Field(
        default_factory=list, description="Any special rule present; each one stops the calculation (AU-RES-005).")

    @model_validator(mode="after")
    def _consistent(self):
        if self.foreign_net_income > self.taxable_income + 1e-9:
            raise ValueError("foreign_net_income cannot exceed taxable_income (it is part of taxable income)")
        if not self.has_spouse and self.spouse_taxable_income:
            raise ValueError("spouse income given but has_spouse is false")
        return self


def offset_limit_amount(default_limit: float, tax_with_foreign: float, tax_without_foreign: float) -> float:
    """s 770-75(2): the greater of the default limit and (tax payable less tax payable under the s 770-75(4) assumptions)."""
    return max(default_limit, tax_with_foreign - tax_without_foreign)


def _tax_before_offsets(figures: Figures, inp: FitoInput, ti: float, assumptions: list[str], warnings: list[str]) -> tuple[float, float]:
    """(income tax + Medicare levy + MLS disregarding offsets, income tax after LITO + levy + MLS)."""
    ind = IndividualTaxInput(
        taxable_income=ti, residency="resident", resident_months=inp.resident_months, has_spouse=inp.has_spouse,
        spouse_taxable_income=inp.spouse_taxable_income, dependent_children=inp.dependent_children,
        private_hospital_cover=inp.private_hospital_cover, days_without_cover=inp.days_without_cover,
        reportable_fringe_benefits=inp.reportable_fringe_benefits, net_investment_losses=inp.net_investment_losses,
        reportable_super_contributions=inp.reportable_super_contributions,
        exempt_foreign_employment_income=inp.exempt_foreign_employment_income)
    c = _core(figures, ind, ti, assumptions, warnings)
    mls, _ = _mls(figures, ind, ti, c["days"], assumptions, warnings)
    return c["gross"] + c["levy"] + mls, c["net"] + c["levy"] + mls


@calculator("foreign_income_tax_offset", FitoInput)
def foreign_income_tax_offset(figures: Figures, inp: FitoInput) -> dict:
    """Foreign income tax offset (ITAA 1997 Div 770) for an Australian resident individual: applies the offset
    limit in s 770-75. The limit is the greater of the default limit and the extra income tax (including Medicare
    levy and surcharge, disregarding offsets) caused by the foreign income. Inputs: foreign_tax_paid (AUD),
    taxable_income, foreign_net_income (foreign income less related deductions, the amount disregarded at step 2),
    plus Medicare family details. If foreign tax paid is at or below the default limit no limit calculation is
    needed and the whole amount is the offset. Returns offset_after_limit, the limit, the tax payable steps, and
    the amount usable against tax payable (the offset is non-refundable and cannot be carried forward; unused foreign
    tax is lost). Use for "how much foreign tax credit can I claim", "FITO limit", "foreign tax paid on overseas
    income". Refuses AU-RES-005 for deferred business losses, foreign loss components, attribution account payments,
    JPDA income, or foreign tax in a different year from the income. Residents only."""
    if inp.complications:
        raise Refusal("AU-RES-005", ", ".join(inp.complications))
    cap = figures.get("residency.fito_default_offset_limit")
    assumptions: list[str] = [
        "Foreign tax paid counts only to the extent it was paid on amounts included in assessable income (s 770-10); "
        "the caller must have removed tax on amounts that are not assessable (for example the discounted or losses-absorbed part of a foreign gain).",
        "All foreign amounts are already in AUD.",
    ]
    warnings: list[str] = []
    paid = inp.foreign_tax_paid
    out: dict = {"foreign_tax_paid": _r(paid), "default_offset_limit": cap}

    # tax payable after LITO (non-refundable offset ordering: FITO applied last)
    ti = inp.taxable_income
    tax1, tax1_after_lito = _tax_before_offsets(figures, inp, ti, assumptions, warnings)

    if paid <= cap:
        limit_method = "default limit: no computed limit needed (s 770-75(2) Note 1)"
        limit = cap
        out.update({"tax_payable_step1": _r(tax1), "tax_payable_step2": None, "computed_limit": None})
    elif inp.claim_default_limit_only:
        limit_method = "taxpayer claims the default limit only"
        limit = cap
        out.update({"tax_payable_step1": _r(tax1), "tax_payable_step2": None, "computed_limit": None})
        warnings.append("Only the default limit is claimed; the remaining foreign tax cannot be refunded or carried forward.")
    else:
        if inp.foreign_net_income <= 0:
            warnings.append("foreign_net_income is nil, so the computed limit is nil and the default limit applies. "
                            "If foreign income was included in taxable income, supply foreign_net_income.")
        ti2 = ti - inp.foreign_net_income
        tax2, _ = _tax_before_offsets(figures, inp, ti2, [], [])
        limit = offset_limit_amount(cap, tax1, tax2)
        computed = tax1 - tax2
        limit_method = "computed limit (s 770-75(2)(b)) applies" if computed > cap else "default limit is greater than the computed amount"
        out.update({"tax_payable_step1": _r(tax1), "tax_payable_step2": _r(tax2),
                    "taxable_income_step2": _r(ti2), "computed_limit": _r(computed)})

    before_tax_cap = min(paid, limit)
    usable = min(before_tax_cap, tax1_after_lito)  # non-refundable: cannot reduce tax payable below nil
    if usable < before_tax_cap - 0.005:
        warnings.append("Offset exceeds tax payable after other offsets; the excess is not refunded or carried forward.")
    if paid > limit + 0.005:
        warnings.append("Foreign tax paid exceeds the offset limit; the excess is lost (no refund, no carry-forward).")
    out.update({
        "limit_method": limit_method,
        "offset_limit": _r(limit),
        "offset_after_limit": _r(before_tax_cap),
        "tax_payable_after_lito_before_fito": _r(tax1_after_lito),
        "offset_usable_against_tax": _r(usable),
        "tax_payable_after_fito": _r(tax1_after_lito - usable),
        "foreign_tax_lost": _r(paid - usable),
        "assumptions": assumptions + ["Tax payable is income tax plus Medicare levy plus Medicare levy surcharge; HELP is not reduced by the offset. "
                                      "Other non-refundable offsets (LITO only is modelled) are applied before the foreign income tax offset."],
        "warnings": warnings,
    })
    return out


# ======================================================================= residency indicators

class ResidencyInput(BaseModel):
    """Facts about an individual for one income year. Leave a field out (null) if unknown: unknown facts are
    reported as questions and never guessed."""

    days_in_australia: int = Field(ge=0, le=366, description="Days physically present in Australia in the income year (continuously or intermittently).")
    prior_year_resident: bool | None = Field(None, description="Was an Australian resident for tax purposes in the previous income year.")
    movement: Literal["arriving", "departing", "none"] = Field("none", description="Arrived in or left Australia during the year (for the part-year note).")
    home: Where | None = Field(None, description="Where the person's home (dwelling available to live in) is: australia, overseas, both, or none.")
    family: Where | None = Field(None, description="Where spouse and dependent children live.")
    employment: Where | None = Field(None, description="Where the main employment or business is carried on.")
    assets: Where | None = Field(None, description="Where significant assets sit (home, bank accounts, vehicles, super, business).")
    intention: Intention | None = Field(None, description="The person's stated intention about living in Australia.")
    domicile: Literal["australia", "overseas", "unsure"] = Field("unsure", description="Domicile under common law and the Domicile Act 1982 (born in Australia and no domicile of choice elsewhere = australia).")
    planned_overseas_stay_months: float | None = Field(None, ge=0, description="For someone leaving or abroad: intended length of the stay overseas, if any is fixed.")
    usual_place_of_abode_overseas: bool | None = Field(None, description="For the 183-day exception: usual place of abode is outside Australia.")
    commonwealth_super_member: bool = Field(False, description="Active member of the PSS or CSS (or spouse, or child under 16, of one).")
    temporary_visa_holder: bool | None = Field(None, description="Holds a temporary visa under the Migration Act 1958.")
    spouse_australian_resident: bool | None = Field(None, description="Has a spouse who is an Australian resident (removes temporary resident status).")
    working_holiday_visa: bool = Field(False, description="Holds a working holiday (417) or work and holiday (462) visa.")


def _factor(score_au: int, score_os: int, where: str | None, weight: int) -> tuple[int, int]:
    if where == "australia":
        return score_au + weight, score_os
    if where == "overseas":
        return score_au, score_os + weight
    if where == "both":
        return score_au + weight, score_os + weight
    return score_au, score_os


@calculator("residency_indicators", ResidencyInput)
def residency_indicators(figures: Figures, inp: ResidencyInput) -> dict:
    """Structured Australian tax residency checklist for an individual (ITAA 1936 s 6(1); TR 2023/1). Inputs: days
    present in the income year, home, family, employment, assets, intention, domicile, planned time overseas,
    usual place of abode, Commonwealth super membership, visa status. Returns for each of the four tests (resides,
    domicile, 183-day, Commonwealth super) whether it is likely met, likely not met or uncertain, with the ruling
    paragraph references, plus an overall indication: likely_resident, likely_non_resident, or uncertain_escalate.
    It never gives a definitive conclusion: when indicators point both ways or facts are missing it returns
    uncertain_escalate with escalation AU-RES-004. Also flags temporary resident status (Subdiv 768-R), working
    holiday makers and part-year residency. Use for "am I an Australian resident for tax", "did I stop being a
    resident when I moved overseas", "183 days", "part-year resident". Not a determination: residency is a question
    of fact."""
    days_year = _days_in_year(figures)
    clamp_warning = None
    if inp.days_in_australia > days_year:
        clamp_warning = f"days_in_australia {inp.days_in_australia} exceeds the {days_year} days in the income year; treated as {days_year}."
        inp = inp.model_copy(update={"days_in_australia": days_year})
    threshold = days_year // 2 + 1  # "more than one-half of the year of income"
    substantial_months = figures.get("residency.permanent_abode_substantial_period_years") * 12
    visit_months = figures.get("residency.short_visit_months")

    au = os_ = 0
    factors: list[dict] = []
    # presence (weight 2 for the Australian side; weight 1 against for a short first-time stay)
    if inp.days_in_australia >= threshold:
        au += 2
        factors.append({"factor": "presence", "points_to": "australia", "note": f"{inp.days_in_australia} days is more than half of the {days_year}-day year (TR 2023/1 paras 26-30)"})
    elif inp.prior_year_resident is False:
        os_ += 1
        factors.append({"factor": "presence", "points_to": "overseas", "note": f"short stay for someone not previously resident; a visit under about {int(visit_months)} months rarely amounts to residing (para 29)"})
    else:
        factors.append({"factor": "presence", "points_to": "neutral", "note": "physical absence does not by itself end residency (para 25)"})
    for name, where, weight, para in (("home", inp.home, 2, "paras 46-54, 67"), ("family", inp.family, 2, "paras 46-50"),
                                      ("intention", None, 2, "paras 31-40"), ("employment", inp.employment, 1, "paras 47-49"),
                                      ("assets", inp.assets, 1, "paras 51-52")):
        if name == "intention":
            i = inp.intention
            where = "australia" if i in ("settle_australia", "return_to_australia_foreseen") else ("overseas" if i in ("stay_overseas_indefinitely", "visit_only") else None)
        a0, o0 = au, os_
        au, os_ = _factor(au, os_, where, weight)
        pts = "both" if (au > a0 and os_ > o0) else "australia" if au > a0 else "overseas" if os_ > o0 else "unknown/neutral"
        factors.append({"factor": name, "points_to": pts, "weight": weight, "ruling_paras": para})

    # Neither side dominates when both have real weight and the gap is under 4 points.
    conflict = au >= 3 and os_ >= 3 and abs(au - os_) < 4
    missing = [n for n, v in (("home", inp.home), ("family", inp.family), ("employment", inp.employment),
                              ("assets", inp.assets), ("intention", inp.intention), ("prior_year_resident", inp.prior_year_resident)) if v is None]

    # ---- ordinary concepts (resides) test
    # Leaving is harder than arriving (adhesive residency), so a wider margin is needed for a previous resident.
    os_margin = 3 if inp.prior_year_resident is False else 4
    if au >= 5 and au - os_ >= 4:
        resides = "likely_met"
    elif os_ >= 5 and os_ - au >= os_margin:
        resides = "likely_not_met"
    else:
        resides = "uncertain"

    # ---- domicile test (permanent place of abode overseas proviso)
    indefinite_or_long = (inp.intention == "stay_overseas_indefinitely"
                          or (inp.planned_overseas_stay_months is not None and inp.planned_overseas_stay_months >= substantial_months))
    moved_overseas = inp.home == "overseas" and inp.family in ("overseas", "none") and indefinite_or_long
    retained = inp.home in ("australia", "both") or inp.family == "australia"
    if inp.domicile == "overseas":
        domicile = "likely_not_met"
        dom_note = "domicile is not in Australia (paras 55-62)"
    elif inp.domicile == "unsure":
        domicile = "uncertain"
        dom_note = "domicile not established: ask about birth, domicile of choice and intention (paras 56-62)"
    elif moved_overseas:
        domicile = "likely_not_met"
        dom_note = ("Australian domicile, but a permanent place of abode overseas looks established: home and family overseas and the stay "
                    "is indefinite or long (paras 63-82). The Commissioner must be satisfied; not certain.")
    elif retained:
        domicile = "likely_met"
        dom_note = "Australian domicile and an Australian home or family retained, so a permanent place of abode overseas is unlikely (paras 67, 74-76)"
    else:
        domicile = "uncertain"
        dom_note = "Australian domicile but the permanent place of abode overseas question is unresolved (paras 63-82)"

    # ---- 183-day test
    if inp.days_in_australia < threshold:
        d183 = "likely_not_met"
        d183_note = f"present {inp.days_in_australia} days, fewer than the {threshold} needed in a {days_year}-day year (paras 83-91)"
    else:
        exception = inp.usual_place_of_abode_overseas is True and inp.intention in ("visit_only", "stay_overseas_indefinitely")
        no_exception = inp.usual_place_of_abode_overseas is False or inp.intention in ("settle_australia", "return_to_australia_foreseen")
        if exception:
            d183 = "likely_not_met"
            d183_note = "present for more than half the year, but usual place of abode is overseas and there is no intention to take up residence (paras 88-95)"
        elif no_exception:
            d183 = "likely_met"
            d183_note = "present for more than half the year and the overseas-abode exception does not look available (paras 88-95)"
        else:
            d183 = "uncertain"
            d183_note = "present for more than half the year; the exception turns on usual place of abode and intention, not yet known (paras 88-95)"

    # ---- Commonwealth superannuation test
    csf = "likely_met" if inp.commonwealth_super_member else "likely_not_met"

    tests = {
        "resides_ordinary_concepts": {"status": resides, "ruling_paras": "17-54", "score_australia": au, "score_overseas": os_},
        "domicile": {"status": domicile, "ruling_paras": "55-82", "note": dom_note},
        "days_183": {"status": d183, "ruling_paras": "83-95", "note": d183_note, "days_needed": threshold},
        "commonwealth_super": {"status": csf, "ruling_paras": "96-97"},
    }
    statuses = [t["status"] for t in tests.values()]
    if csf == "likely_met":
        overall = "likely_resident"
        leaning = "resident"
    elif conflict:
        overall, leaning = "uncertain_escalate", ("resident" if au > os_ else "non_resident" if os_ > au else None)
    elif "likely_met" in statuses:
        overall, leaning = "likely_resident", "resident"
    elif all(s == "likely_not_met" for s in statuses):
        overall, leaning = "likely_non_resident", "non_resident"
    else:
        overall, leaning = "uncertain_escalate", ("resident" if au > os_ else "non_resident" if os_ > au else None)

    notes: list[str] = []
    if conflict:
        notes.append("Indicators point both ways (ties to Australia and overseas at once): residency can be held in more than one country "
                     "(para 24) and the outcome is not decided by dominance. Do not conclude.")
    if inp.movement == "arriving":
        notes.append("Arriving: residency can start on arrival if behaviour is consistent with residing here, even when less than half the year "
                     "is spent in Australia (paras 27, 39, 45). Part-year: use months from the month residency starts (para 106) with individual_income_tax.")
    if inp.movement == "departing":
        notes.append("Departing: residency does not end on the departure date; it ends when a permanent place of abode overseas is established "
                     "(paras 25, 63, 74-76). Part-year: use months to the month residency ends (para 106).")
    temp = None
    if inp.temporary_visa_holder is not None:
        if inp.temporary_visa_holder and inp.spouse_australian_resident is False:
            temp = "likely_temporary_resident"
        elif inp.temporary_visa_holder and inp.spouse_australian_resident is None:
            temp = "unknown_spouse_status"
        else:
            temp = "not_temporary_resident"
    temp_note = None
    if temp in ("likely_temporary_resident", "unknown_spouse_status"):
        temp_note = ("If an Australian resident who holds a temporary visa (and has no Australian-resident spouse), foreign-source income other "
                     "than employment or services performed while a temporary resident is not assessable (ITAA 1997 s 768-910) and gains that "
                     "would be disregarded for a foreign resident are disregarded (s 768-915). Australian-source income is fully taxable. "
                     "Confirm visa subclass and spouse status against the definition in s 995-1.")
    if inp.working_holiday_visa:
        notes.append("Working holiday maker (visa 417 or 462): TR 2023/1 paras 102-104 and Examples 15, 16 and 18 usually treat a working holiday maker "
                     "as a non-resident when the stay is a visit, but a person who settles here can be resident. Rates and calculation belong to "
                     "individual-tax; a working holiday maker who is a resident or relies on a treaty is escalated there (AU-IND-004).")

    out = {
        "overall": overall,
        "leaning": leaning,
        "is_determination": False,
        "days_in_year": days_year,
        "days_needed_for_183_test": threshold,
        "tests": tests,
        "factors": factors,
        "conflicting_indicators": conflict,
        "missing_facts": missing,
        "temporary_resident": temp,
        "temporary_resident_note": temp_note,
        "notes": notes,
        "assumptions": ["Weights are a screening aid built from the TR 2023/1 factor lists, not a legal test. Residency is a question of fact "
                        "decided on all circumstances of the year and surrounding years (para 16).",
                        "Board of Taxation bright-line residency model is not law; the four tests in ITAA 1936 s 6(1) apply."],
        "warnings": [clamp_warning] if clamp_warning else [],
    }
    if overall == "uncertain_escalate":
        out["escalation"] = _escalation("AU-RES-004")
        out["warnings"].append("Uncertain: do not present a residency conclusion. Surface the escalation message.")
    return out


# ======================================================================= Australia-Indonesia treaty

class IndonesiaDtaInput(BaseModel):
    """One Australia-Indonesia treaty question. Set `article` and the fields it needs."""

    article: Literal["independent_services", "employment", "dividends", "interest", "royalties", "residence_tie_breaker"]
    treaty_country: str = Field("indonesia", description="Must be indonesia; any other treaty is escalated (AU-RES-001).")
    # Arts 14 and 15
    residence_state: Literal["australia", "indonesia"] | None = Field(None, description="Treaty residence state of the individual (Arts 14, 15).")
    days_in_other_state_12m: int | None = Field(None, ge=0, le=366, description="Maximum days present in the other state in any period of 12 months.")
    fixed_base_available: bool | None = Field(None, description="Art 14: a fixed base is regularly available in the other state.")
    employer_resident_in_work_state: bool | None = Field(None, description="Art 15: the employer is a resident of the state where the work is done.")
    remuneration_borne_by_pe_or_fixed_base: bool | None = Field(None, description="Art 15: remuneration is deductible in a PE or fixed base the employer has in the work state.")
    remuneration_taxed_in_residence_state: bool | None = Field(None, description="Art 15: the remuneration is or will be subject to tax in the residence state.")
    # Arts 10-12
    gross_amount: float | None = Field(None, ge=0, description="Gross dividend, interest or royalty (Arts 10-12).")
    royalty_type: Literal["equipment_or_know_how", "other"] | None = None
    # Art 4(3)
    resident_of_both_states_under_domestic_law: bool | None = Field(None, description="Art 4(3) applies only if the individual is a resident of both states under each state's domestic law.")
    permanent_home_australia: bool | None = None
    permanent_home_indonesia: bool | None = None
    habitual_abode: Literal["australia", "indonesia", "both", "neither"] | None = None
    closer_relations: Literal["australia", "indonesia", "unclear"] | None = None


@calculator("indonesia_dta_check", IndonesiaDtaInput)
def indonesia_dta_check(figures: Figures, inp: IndonesiaDtaInput) -> dict:
    """Australia-Indonesia double tax agreement (1992, as modified by the MLI) for one question. article =
    independent_services (Art 14: other state may tax if a fixed base is regularly available or presence exceeds 120
    days in any 12 months), employment (Art 15: taxable only in the residence state if all four conditions hold,
    including presence not above 120 days), dividends / interest / royalties (Arts 10-12: source-state tax limit and
    the amount at that limit), or residence_tie_breaker (Art 4(3): permanent home, then habitual abode, then closer
    personal and economic relations; no nationality step; the tie-breaker result is only ever an indication with missing facts
    and escalations, never a determination). Returns the treaty outcome and the paragraph. Treaty
    limits are ceilings, not the domestic rate. Any other country's treaty, or a tie-breaker with unclear facts, is
    refused with AU-RES-001. Use for Bali or Indonesia questions: 120 days, withholding tax on Indonesian
    dividends or royalties, dual residence."""
    if inp.treaty_country.strip().lower() != "indonesia":
        raise Refusal("AU-RES-001", f"treaty with {inp.treaty_country} is not modelled")
    days_limit = figures.get("residency.indonesia_dta_days_threshold")
    a = inp.article
    assumptions = ["Treaty text: Australia-Indonesia agreement of 22 April 1992 as modified by the MLI (ATO synthesised text). "
                   "The treaty allocates taxing rights; domestic law still decides what each country taxes and at what rate.",
                   "Australia keeps its right to tax its own residents; Indonesian tax is relieved by a credit under Art 24 and the foreign income tax offset (Div 770)."]
    out: dict = {"article": a, "assumptions": assumptions, "warnings": []}

    if a in ("independent_services", "employment"):
        if inp.residence_state is None:
            raise Refusal("AU-RES-001", "residence_state is required for Arts 14 and 15")
        other = "indonesia" if inp.residence_state == "australia" else "australia"
        out.update({"residence_state": inp.residence_state, "other_state": other, "days_threshold": days_limit})
        if a == "independent_services":
            if inp.fixed_base_available is None or inp.days_in_other_state_12m is None:
                out.update({"other_state_may_tax": None, "reason": "need fixed_base_available and days_in_other_state_12m"})
                out["warnings"].append("Missing facts; no outcome given.")
                return out
            over = inp.days_in_other_state_12m > days_limit
            may = inp.fixed_base_available or over
            out.update({
                "article_ref": "Art 14(1)",
                "other_state_may_tax": may,
                "fixed_base_test_met": inp.fixed_base_available,
                "days_test_met": over,
                "scope": ("only income attributable to the fixed base (Art 14(1)(a)) or derived from activities in the other state (Art 14(1)(b))"
                          if may else "taxable only in the residence state"),
            })
            out["warnings"].append("Presence is counted in any period of 12 months, rolling, not the income year. Art 14 applies to independent activities; "
                                   "business profits of a company or a permanent establishment are Arts 5 and 7.")
        else:
            conds = {
                "presence_not_above_threshold": None if inp.days_in_other_state_12m is None else inp.days_in_other_state_12m <= days_limit,
                "employer_not_resident_of_work_state": None if inp.employer_resident_in_work_state is None else not inp.employer_resident_in_work_state,
                "not_borne_by_pe_or_fixed_base": None if inp.remuneration_borne_by_pe_or_fixed_base is None else not inp.remuneration_borne_by_pe_or_fixed_base,
                "taxed_in_residence_state": inp.remuneration_taxed_in_residence_state,
            }
            out.update({"article_ref": "Art 15(2)", "conditions": conds})
            if any(v is False for v in conds.values()):
                out.update({"taxable_only_in_residence_state": False, "other_state_may_tax": True,
                            "scope": "remuneration derived from the employment exercised in the other state may be taxed there (Art 15(1))"})
            elif any(v is None for v in conds.values()):
                out.update({"taxable_only_in_residence_state": None, "other_state_may_tax": None})
                out["warnings"].append("Missing facts; all four Art 15(2) conditions must be shown to get the exemption.")
            else:
                out.update({"taxable_only_in_residence_state": True, "other_state_may_tax": False})
            out["warnings"].append("Art 15(1) is subject to Arts 16, 18, 19 and 20 (directors' fees, pensions, government service, students).")
        return out

    if a in ("dividends", "interest", "royalties"):
        if a == "dividends":
            key, ref = "residency.indonesia_dta_wht_dividends", "Art 10(2)"
        elif a == "interest":
            key, ref = "residency.indonesia_dta_wht_interest", "Art 11(2)"
        else:
            if inp.royalty_type is None:
                raise Refusal("AU-RES-001", "royalty_type is required (equipment_or_know_how or other)")
            key = ("residency.indonesia_dta_wht_royalties_equipment_know_how" if inp.royalty_type == "equipment_or_know_how"
                   else "residency.indonesia_dta_wht_royalties_other")
            ref = "Art 12(2)"
        rate = figures.get(key)
        out.update({"article_ref": ref, "source_state_tax_limit_rate": rate})
        if inp.gross_amount is not None:
            out["source_state_tax_limit_amount"] = _r(rate * inp.gross_amount)
        out["warnings"].append("Ceiling only: the source state's domestic rate may be lower. The limit does not apply where the income is effectively "
                               "connected with a permanent establishment or fixed base in the source state (Arts 7 or 14 apply instead).")
        out["warnings"].append("Treaty-limited foreign tax can support a foreign income tax offset; foreign tax above the treaty limit that could be "
                               "recovered from the foreign authority may not count. Confirm before claiming.")
        return out

    # Art 4(3) tie-breaker. The result is only ever an indication: the agreement's text and the OECD Commentary (an interpretive
    # aid the ATO treats as relevant, TR 2001/13) leave the availability of a home, habitual abode and closer relations as
    # questions of fact, and Indonesian domestic residence is an Indonesian-law question this plugin does not verify.
    escalations = [_escalation("AU-RES-001"), _escalation("AU-IDN-002")]
    domestic = ("Indonesian domestic residence: whether Indonesia treats the person as a resident under its own law is an Indonesian-law "
                "question that this plugin does not verify; obtain the view of an Indonesian tax adviser and any evidence")
    if inp.resident_of_both_states_under_domestic_law is not True:
        out.update({"applies": False, "reason": "Art 4(3) only applies when the individual is a resident of both states under each state's domestic law"})
        if inp.resident_of_both_states_under_domestic_law is None:
            out["warnings"].append("Dual residence under domestic law not confirmed.")
            out.update({"missing_facts": [domestic], "escalations": escalations})
        return out
    ph_au, ph_id = inp.permanent_home_australia, inp.permanent_home_indonesia
    steps: list[str] = []
    result: str | None = None
    if ph_au is None or ph_id is None:
        raise Refusal("AU-RES-001", "permanent home availability in each state is required")
    if ph_au != ph_id:
        result = "australia" if ph_au else "indonesia"
        steps.append("Art 4(3)(a): permanent home available in one state only")
    else:
        steps.append("Art 4(3)(a): permanent home available in both states or neither, so go to habitual abode" if ph_au else
                     "Art 4(3)(a): permanent home in neither state, so go to habitual abode")
        ha = inp.habitual_abode
        if ha is None:
            raise Refusal("AU-RES-001", "habitual_abode is required when permanent homes do not decide")
        if ha in ("australia", "indonesia"):
            result = ha
            steps.append("Art 4(3)(b): habitual abode in one state only")
        else:
            steps.append("Art 4(3)(b): habitual abode in both or neither, so go to closer personal and economic relations")
            cr = inp.closer_relations
            if cr in (None, "unclear"):
                raise Refusal("AU-RES-001", "closer personal and economic relations are unclear; a determination is needed")
            result = cr
            steps.append("Art 4(3)(c): closer personal and economic relations")
    missing = [domestic,
               "Whether each home is genuinely available to the person throughout the period (a home let to unrelated guests for most of the year "
               "may not be available; OECD Commentary Art 4 para 13, an interpretive aid, not treaty text)"]
    if ph_au == ph_id:
        missing.append("For habitual abode: the comparative length, frequency and regularity of stays in each state over a period long enough to compare "
                       "(OECD Commentary Art 4 paras 19 to 19.1, an interpretive aid), not a single year's day count")
    missing.append("Personal and economic relations in each state (family, business, assets, where affairs are administered), needed if the earlier "
                   "steps do not decide")
    out.update({"applies": True, "indication_only": True, "indicated_resident_state": result, "steps": steps,
                "missing_facts": missing, "escalations": escalations,
                "note": "This is an indication from the Art 4(3) steps on the facts supplied, not a determination of treaty residence. "
                        "No nationality step and no mutual agreement step for individuals in this agreement. "
                        "Indonesian domestic residency rules were not verified for this skill."})
    out["warnings"].append("Indication only: present it as where the steps point on the supplied facts, never as 'resident of X only'. List the missing "
                           "facts and quote both escalations (AU-RES-001 and AU-IDN-002) verbatim; a registered tax agent (or the competent authority "
                           "process) decides.")
    return out


# ======================================================================= scope check (verbatim escalation)

Situation = Literal[
    "controlled_foreign_company", "foreign_trust", "foreign_investment_fund_or_hybrid", "offshore_company_controlled",
    "foreign_super_transfer", "foreign_pension", "other_treaty_country", "dual_resident_conflicting_facts",
]


class ScopeInput(BaseModel):
    """Situations present in the matter."""

    situations: list[Situation] = Field(default_factory=list, description="Every out-of-scope cross-border situation that is present.")


@calculator("cross_border_scope_check", ScopeInput)
def cross_border_scope_check(figures: Figures, inp: ScopeInput) -> dict:
    """Checks whether a cross-border matter is inside the residency-cross-border skill. Pass situations such as
    controlled_foreign_company, foreign_trust, offshore_company_controlled (for example an Indonesian PT controlled by an
    Australian resident), foreign_super_transfer, foreign_pension, other_treaty_country, dual_resident_conflicting_facts.
    If any is present it refuses with the escalation code and fixed message to quote (AU-RES-001, AU-RES-002 or
    AU-RES-003); with none it returns in_scope true. Call it whenever the facts include offshore companies, trusts or
    super, a treaty other than Indonesia, or a dual resident with conflicting facts."""
    order = {
        "controlled_foreign_company": "AU-RES-002", "foreign_trust": "AU-RES-002", "foreign_investment_fund_or_hybrid": "AU-RES-002",
        "offshore_company_controlled": "AU-RES-002", "foreign_super_transfer": "AU-RES-003", "foreign_pension": "AU-RES-003",
        "other_treaty_country": "AU-RES-001", "dual_resident_conflicting_facts": "AU-RES-001",
    }
    if inp.situations:
        codes = sorted({order[s] for s in inp.situations})
        raise Refusal(codes[0], ", ".join(inp.situations) + (f" (also {', '.join(codes[1:])})" if len(codes) > 1 else ""))
    return {"in_scope": True, "assumptions": [], "warnings": []}
