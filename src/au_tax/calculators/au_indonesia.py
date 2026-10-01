"""Australia-Indonesia treaty calculators that sit beside residency.py.

residency.py keeps the general residency tests, the generic foreign income tax offset (`foreign_income_tax_offset`)
and the four structured treaty articles (`indonesia_dta_check`: Arts 4(3), 10, 11, 12, 14, 15). This module adds what
those tools do not do: rolling 12 month presence counting, the service permanent establishment screen (Art 5(2)(j)),
allocation of other income types (Arts 6, 7, 13, 16, 17, 18, 22), treaty-capped foreign tax feeding the offset in one
step, Australian withholding on payments to an Indonesian resident, rupiah translation from ATO published rates, and
a scope check that returns the verbatim escalation for Indonesian domestic tax and structure questions.

Law: Australia-Indonesia agreement of 22 April 1992 (as modified by the MLI); ITAA 1953 s 17A(1); Income Tax
(Dividends, Interest and Royalties Withholding Tax) Act 1974 s 7; ITAA 1997 Div 770 and s 960-50. Treaty caps that
already live in the residency overlay are read from there (one fact, one key); new keys are in
data/rates/<year>.d/au_indonesia.yaml. Indonesian domestic tax is not modelled anywhere.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from au_tax.calculators.individual import _r
from au_tax.calculators.residency import FitoComplication, FitoInput, _escalation, foreign_income_tax_offset
from au_tax.figures import Figures
from au_tax.registry import Refusal, calculator

State = Literal["australia", "indonesia"]
MONTHS = ("jul", "aug", "sep", "oct", "nov", "dec", "jan", "feb", "mar", "apr", "may", "jun")
DAYS_KEY = "residency.indonesia_dta_days_threshold"
MAX_PERIOD_DAYS = 3660


# ----------------------------------------------------------------------------- day counting helpers

def _add_12_months(d: date) -> date:
    try:
        return d.replace(year=d.year + 1)
    except ValueError:  # 29 Feb: the same day next year does not exist
        return date(d.year + 1, 3, 1)


def _window_end(start: date) -> date:
    """Last day of the 12 month period that starts on `start` (1 Jan 2026 gives 31 Dec 2026)."""
    return _add_12_months(start) - timedelta(days=1)


def _expand(start: date, end: date) -> set[date]:
    return {start + timedelta(days=i) for i in range((end - start).days + 1)}


def _max_window(sorted_days: list[date]) -> tuple[int, date | None, date | None]:
    """Most days (a date may appear more than once: person days) inside any 12 month period. The best period can be
    taken to start on a day that appears in the list. Returns the count and the earliest such period."""
    best, best_start = 0, None
    for s in sorted(set(sorted_days)):
        n = bisect_right(sorted_days, _window_end(s)) - bisect_left(sorted_days, s)
        if n > best:
            best, best_start = n, s
    return best, best_start, (_window_end(best_start) if best_start else None)


def _income_year_label(d: date) -> str:
    y = d.year if d.month >= 7 else d.year - 1
    return f"{y}-{(y + 1) % 100:02d}"


class _Range(BaseModel):
    start: date
    end: date

    @model_validator(mode="after")
    def _ordered(self):
        if self.end < self.start:
            raise ValueError("end is before start")
        if (self.end - self.start).days > MAX_PERIOD_DAYS:
            raise ValueError("a single period longer than ten years is not accepted; split it or check the dates")
        return self


# ============================================================================= presence window

class Trip(_Range):
    """One visit to Indonesia: first and last day of physical presence, both inclusive (part days count as days)."""


class PresenceInput(BaseModel):
    """Days of physical presence in Indonesia (or Australia for an Indonesian resident), as date ranges."""

    trips: list[Trip] = Field(min_length=1, description="Each visit, first and last day inclusive. Overlaps are merged.")


@calculator("indonesia_presence_window", PresenceInput)
def indonesia_presence_window(figures: Figures, inp: PresenceInput) -> dict:
    """Counts days of physical presence in the other treaty state for Australia-Indonesia Art 14(1)(b) (independent
    services: present for periods exceeding the days limit in any 12 months) and Art 15(2)(a) (employment: present
    not exceeding it in aggregate in any 12 months). Input: trips, each a first and last day of presence, inclusive
    (part days, arrival and departure days, weekends and holidays all count; days in transit or wholly away do not).
    Returns the distinct days, the most days in ANY rolling period of 12 months (not the income year, not 183
    days) with the earliest such period, days per income year, whether the limit is exceeded, and the number to pass as
    days_in_other_state_12m to indonesia_dta_check. Use for "how many days in Bali", "120 days", "am I over the limit"."""
    limit = figures.get(DAYS_KEY)
    days = sorted(set().union(*(_expand(t.start, t.end) for t in inp.trips)))
    best, start, end = _max_window(days)
    per_year: dict[str, int] = {}
    for d in days:
        per_year[_income_year_label(d)] = per_year.get(_income_year_label(d), 0) + 1
    exceeds = best > limit
    return {
        "days_present_total": len(days),
        "max_days_in_any_12_months": best,
        "max_window_start": start.isoformat() if start else None,
        "max_window_end": end.isoformat() if end else None,
        "days_limit": limit,
        "exceeds_limit": exceeds,
        "art14_presence_test_met": exceeds,
        "art15_presence_condition_met": not exceeds,
        "by_income_year": [{"income_year": y, "days": n} for y, n in sorted(per_year.items())],
        "handoff": {"tool": "indonesia_dta_check", "days_in_other_state_12m": best},
        "assumptions": [
            "Physical presence: every calendar day on which the person was in the state for any part counts, including arrival and "
            "departure days, weekends, holidays and short breaks; days in transit between two points outside the state and days wholly "
            "away do not. The treaty does not define a day: this follows the OECD Commentary on Art 15 para 5 as an interpretive aid.",
            "Any period of 12 months is tested on a rolling basis (the period starting on 1 Jan ends on 31 Dec), not the income year.",
        ],
        "warnings": [
            "Days on which the person was already a resident of the state where the work was done are excluded under the OECD aid "
            "(Commentary on Art 15 para 5.1); remove them from the trips before calling if that applies.",
            "Presence over the limit does not by itself decide the outcome: Art 15 needs three more conditions (employer, permanent "
            "establishment cost, taxed at home) and a fixed base or directors' fees need no days at all (Arts 14(1)(a), 16).",
        ],
    }


# ============================================================================= service permanent establishment

class ServicePeriod(_Range):
    """A period during which a person furnished services in Indonesia, first and last day inclusive."""

    person: str = Field(min_length=1, description="Label for the employee or other personnel (any string).")


class ServicePeInput(BaseModel):
    """Services furnished in Indonesia by an Australian enterprise through employees or other personnel."""

    periods: list[ServicePeriod] = Field(min_length=1, description="Periods on which the person actually furnished services; split ranges around any gap days.")
    same_or_connected_project: bool = Field(description="True when every period is for the same project or a connected project. Days of unconnected projects "
                                                        "are not aggregated: run one call per project group. False refuses (AU-IDN-001).")


@calculator("indonesia_service_pe_screen", ServicePeInput)
def indonesia_service_pe_screen(figures: Figures, inp: ServicePeInput) -> dict:
    """Screens the service permanent establishment limb of Australia-Indonesia Art 5(2)(j): services (including
    consultancy) furnished through employees or other personnel for the same or a connected project for periods
    aggregating more than the days limit within any 12 month period, with no fixed place of business needed. The treaty
    does not say how days are counted, so this returns BOTH counts: enterprise days (each day on which at least one person
    served counts once) and person days (each person's days added), each as the maximum in any rolling 12 months. If both
    are under the limit no service PE is indicated; if both are over, one is indicated (attribution of profits under
    Art 7 is not computed); if they disagree it gives no conclusion and returns escalation AU-IDN-001. Screens this limb
    only: a fixed place of business, dependent agent, building site or installation limb needs a tax agent. Use for
    "staff working in Bali", "do we have a PE in Indonesia", "employees in Jakarta for a project"."""
    if not inp.same_or_connected_project:
        raise Refusal("AU-IDN-001", "days for unconnected projects are not aggregated; screen each project group separately and confirm connection")
    limit = figures.get("au_indonesia.dta_pe_services_days")
    by_person: dict[str, set[date]] = {}
    for p in inp.periods:
        by_person.setdefault(p.person, set()).update(_expand(p.start, p.end))
    enterprise_days = sorted(set().union(*by_person.values()))
    person_days = sorted(d for days in by_person.values() for d in days)
    e_max, e_start, e_end = _max_window(enterprise_days)
    p_max, p_start, p_end = _max_window(person_days)
    over_e, over_p = e_max > limit, p_max > limit
    out: dict = {
        "enterprise_days_total": len(enterprise_days),
        "enterprise_days_max_12m": e_max,
        "enterprise_days_window": [e_start.isoformat(), e_end.isoformat()] if e_start else None,
        "person_days_total": len(person_days),
        "person_days_max_12m": p_max,
        "person_days_window": [p_start.isoformat(), p_end.isoformat()] if p_start else None,
        "days_limit": limit,
        "exceeds_on_enterprise_days": over_e,
        "exceeds_on_person_days": over_p,
        "escalation": None,
    }
    if not over_e and not over_p:
        out.update({"screen_result": "below_limit_on_both_methods", "service_pe_indicated": False})
    elif over_e and over_p:
        out.update({"screen_result": "above_limit_on_both_methods", "service_pe_indicated": True,
                    "escalation": _escalation("AU-IDN-001")})
    else:
        out.update({"screen_result": "methods_disagree", "service_pe_indicated": None, "escalation": _escalation("AU-IDN-001")})
    out["assumptions"] = [
        "Each period is treated as days on which services were actually furnished; a day on which two people served counts once as an enterprise day "
        "and twice as person days.",
        "Enterprise days follow the OECD Commentary on Art 5 paras 160 to 163 (the comparable alternative services provision) as an interpretive aid; "
        "the Indonesian text is not identical and the treaty does not define the count. Person days is the other reading. Neither is settled.",
        "All periods are for the same project or a connected project (commercial coherence), as stated by the caller.",
    ]
    out["warnings"] = [
        "Screen of Art 5(2)(j) only. A fixed place of business (Art 5(1)-(2)), a dependent agent (Art 5(4)), a building site or installation "
        "(Art 5(2)(h), (i)) and a fixed base (Art 14(1)(a)) are not tested here.",
        "No conclusion is stated where the two counts disagree; give the tax agent both numbers.",
    ]
    return out


# ============================================================================= treaty allocation (other articles)

IncomeType = Literal[
    "real_property_income", "natural_resource_payments", "business_profits", "real_property_gain", "share_gain",
    "pe_business_property_gain", "directors_fees", "entertainer_athlete", "pension_annuity", "other_income",
    "independent_services", "employment", "dividend", "interest", "royalty",
]

_DELEGATE_ARTICLE = {"independent_services": "independent_services", "employment": "employment", "dividend": "dividends",
                     "interest": "interest", "royalty": "royalties"}


class AllocationInput(BaseModel):
    """Which country the Australia-Indonesia agreement lets tax one kind of income."""

    income_type: IncomeType
    residence_state: State = Field("australia", description="Treaty residence of the taxpayer.")
    source_state: State = Field("indonesia", description="State where the property is, the work is exercised, the paying company is resident or the "
                                                        "permanent establishment is.")
    pe_or_fixed_base_in_source_state: bool | None = Field(None, description="business_profits, pe_business_property_gain: the enterprise has a "
                                                                            "permanent establishment (or fixed base) there. None = unknown.")
    land_rich: bool | None = Field(None, description="share_gain: the company's assets consist wholly or principally of real property in the source state. None = unknown.")
    enterprise_is_company: bool = Field(False, description="business_profits: the enterprise is a company (adds the branch profits additional tax cap, Art 10(6)).")


def _base_row(article: str, may_tax, notes: list[str], **extra) -> dict:
    return {"article": article, "other_state_may_tax": may_tax, "notes": notes, **extra}


@calculator("indonesia_treaty_allocation", AllocationInput)
def indonesia_treaty_allocation(figures: Figures, inp: AllocationInput) -> dict:
    """Allocates taxing rights under the Australia-Indonesia agreement for one kind of income and says whether the OTHER
    state (not the taxpayer's residence state) may tax it, the article, any treaty ceiling and the relief. Covers real
    property income (Art 6), natural resource payments (Art 6(2)(b)), business profits (Art 7, needs the permanent
    establishment fact), gains on real property (Art 13(1)), shares (Art 13(4) land-rich; Art 13(5) left to domestic
    law), business property of a permanent establishment (Art 13(2)), directors' fees (Art 16, no days test), entertainers
    (Art 17), pensions and annuities (Art 18, ceiling from the overlay) and other income (Art 22). For employment,
    independent services, dividends, interest and royalties it names the tool that already models them. Treaty
    allocation never exempts a resident from tax in their own country; the relief is the credit (Art 24). Use for
    "can Indonesia tax my villa rent / directors fees / share sale", "which article applies"."""
    r, s = inp.residence_state, inp.source_state
    other = "australia" if r == "indonesia" else "indonesia"
    t = inp.income_type
    out: dict
    if t in _DELEGATE_ARTICLE:
        tool = "au_withholding_indonesian_payee" if (r == "indonesia" and t in ("dividend", "interest", "royalty")) else "indonesia_dta_check"
        return {"income_type": t, "residence_state": r, "source_state": s, "other_state": other, "cross_border": s != r,
                "article": {"independent_services": "Art 14", "employment": "Art 15", "dividend": "Art 10", "interest": "Art 11", "royalty": "Art 12"}[t],
                "other_state_may_tax": None, "treaty_limit_rate": None, "delegate_tool": tool,
                "delegate_article": _DELEGATE_ARTICLE[t], "escalation": None, "notes": [f"Already modelled: call {tool}."],
                "assumptions": [], "warnings": []}
    if s == r:
        return {"income_type": t, "residence_state": r, "source_state": s, "other_state": other, "cross_border": False,
                "article": None, "other_state_may_tax": False, "treaty_limit_rate": None, "escalation": None,
                "notes": ["The income arises in the taxpayer's own state of residence, so the treaty gives the other state no claim on these facts."],
                "assumptions": [], "warnings": []}
    esc = None
    limit = None
    pe = inp.pe_or_fixed_base_in_source_state
    if t == "real_property_income":
        row = _base_row("Art 6(1), (4)", True, ["Taxable where the real property is, including letting and any other use, with no permanent establishment "
                                                 "needed and no treaty ceiling. Real property has the local law meaning and includes leases of land."])
    elif t == "natural_resource_payments":
        row = _base_row("Art 6(2)(b)", True, ["Payments for exploiting or exploring for natural resources are real property income taxable where the resources are; "
                                               "no ceiling (not the royalty ceiling in Art 12)."])
    elif t in ("business_profits", "pe_business_property_gain"):
        art = "Art 7(1)" if t == "business_profits" else "Art 13(2)"
        if pe is None:
            row = _base_row(art, None, ["Whether the enterprise has a permanent establishment (or fixed base) in the source state decides this and has not been given."])
            esc = "AU-IDN-001"
        elif pe is False:
            row = _base_row(art, False, ["Without a permanent establishment the profits are taxable only in the enterprise's state (Art 7(1)); a gain on other property "
                                          "falls to Art 13(5) and domestic law."] if t == "business_profits" else
                            ["Not business property of a permanent establishment or fixed base: Art 13(2) does not apply (see Art 13(5))."])
        else:
            row = _base_row(art, True, ["The source state may tax the profits attributable to the permanent establishment plus profits from sales of the same or "
                                        "similar goods and activities of the same kind there (Art 7(1)(b), (c)). Attribution is not computed."] if t == "business_profits" else
                            ["The source state may tax gains on business property of the permanent establishment or fixed base, including on selling it."])
            esc = "AU-IDN-001"
            if t == "business_profits" and inp.enterprise_is_company:
                row["branch_profits_additional_tax_cap"] = figures.get("au_indonesia.dta_branch_profits_additional_tax_cap")
                row["notes"].append("Art 10(6) allows additional tax on the profits of a company's permanent establishment, capped at the branch profits key share "
                                    "of the profits after source state tax (Art 10(7) carves out Indonesian oil and gas production sharing).")
    elif t == "real_property_gain":
        row = _base_row("Art 13(1)", True, ["Gains from alienating real property in the other state may be taxed there, with no treaty ceiling."])
    elif t == "share_gain":
        if inp.land_rich is True:
            row = _base_row("Art 13(4)", True, ["Shares or comparable interests in an entity whose assets are wholly or principally real property in the source state "
                                                "may be taxed there (MLI Art 9 tests the value at any time in the look-back period and adds partnership and trust interests)."])
            esc = "AU-IDN-004"
        elif inp.land_rich is False:
            row = _base_row("Art 13(5)", None, ["Not a land-rich entity: the agreement does not restrict either state's domestic law on gains from other property, so "
                                                 "there is no treaty ceiling and no residence-only rule. What each country taxes is a domestic law question."])
        else:
            row = _base_row("Art 13(4) or (5)", None, ["Whether the entity is land-rich has not been given."])
            esc = "AU-IDN-004"
    elif t == "directors_fees":
        row = _base_row("Art 16", True, ["Directors' fees and similar payments from a company resident in the other state may be taxed there. No days test and no "
                                          "fixed base test applies."])
    elif t == "entertainer_athlete":
        row = _base_row("Art 17(1), (2)", True, ["The state where the performance takes place may tax, overriding Arts 14 and 15 (and Art 7 where the income accrues to "
                                                  "another person)."])
    elif t == "pension_annuity":
        limit = figures.get("au_indonesia.dta_wht_pensions_annuities")
        row = _base_row("Art 18(2)", True, ["Art 18(1) makes pensions and annuities taxable only in the recipient's state, but the source state may tax them up to the "
                                             "ceiling shown (a ceiling, not the rate charged)."])
    else:  # other_income
        row = _base_row("Art 22(1), (2)", True, ["Income not covered by another article is taxable in the residence state, and the state it comes from may also tax it. "
                                                  "Income effectively connected with a permanent establishment or fixed base goes to Art 7 or 14 instead (Art 22(3))."])
    if r == "australia":
        relief = ("Australia still taxes its resident on the income (MLI saving clause). Indonesian tax paid under Indonesian law and the agreement is relieved by "
                  "the credit in Art 24(1), applied through the foreign income tax offset (ITAA 1997 Div 770): use indonesia_treaty_fito.")
    else:
        relief = ("Indonesia gives a credit for Australian tax (Art 24(3), (4)). The Australian side is domestic law; withholding on dividends, interest and "
                  "royalties is au_withholding_indonesian_payee.")
    out = {"income_type": t, "residence_state": r, "source_state": s, "other_state": other, "cross_border": True, "treaty_limit_rate": limit,
           "relief": relief, "escalation": _escalation(esc) if esc else None,
           "assumptions": ["The agreement allocates taxing rights; the domestic law of each country decides what is taxed and at what rate. Indonesian domestic tax is not verified."],
           "warnings": [], **row}
    return out


# ============================================================================= treaty-capped foreign tax feeding FITO

ItemKind = Literal["dividend", "interest", "royalty_equipment_know_how", "royalty_other", "pension_annuity", "rent_real_property", "employment",
                   "independent_services", "directors_fees", "capital_gain", "other"]
CAP_KEYS = {
    "dividend": ("residency.indonesia_dta_wht_dividends", "Art 10(2)"),
    "interest": ("residency.indonesia_dta_wht_interest", "Art 11(2)"),
    "royalty_equipment_know_how": ("residency.indonesia_dta_wht_royalties_equipment_know_how", "Art 12(2)(a)"),
    "royalty_other": ("residency.indonesia_dta_wht_royalties_other", "Art 12(2)(b)"),
    "pension_annuity": ("au_indonesia.dta_wht_pensions_annuities", "Art 18(2)"),
}


class ForeignTaxItem(BaseModel):
    """One Indonesian income item with the Indonesian tax paid on it, all in AUD."""

    kind: ItemKind
    gross_aud: float = Field(ge=0, description="Gross amount before Indonesian withholding, in AUD (for a capital gain: the gain before any discount).")
    foreign_tax_paid_aud: float = Field(ge=0, description="Indonesian income tax paid (including tax withheld by a payer) on this item, in AUD, translated when paid.")
    assessable_aud: float | None = Field(None, ge=0, description="Amount included in assessable income. Default: gross_aud. REQUIRED for capital_gain: the net capital "
                                                                   "gain (after discount and losses) from the cgt skill that relates to this asset.")
    nane_dividend: bool = Field(False, description="dividend only: non-assessable non-exempt income under ITAA 1997 s 768-5 (Australian company with a participation interest).")
    label: str | None = None

    @model_validator(mode="after")
    def _checks(self):
        if self.kind == "capital_gain" and self.assessable_aud is None:
            raise ValueError("assessable_aud is required for capital_gain (the net capital gain relating to the asset, from the cgt skill)")
        if self.nane_dividend and self.kind != "dividend":
            raise ValueError("nane_dividend applies to a dividend only")
        if self.assessable_aud is not None and self.assessable_aud > self.gross_aud + 1e-9:
            raise ValueError("assessable_aud cannot exceed gross_aud")
        return self


def _assessable(item: ForeignTaxItem) -> float:
    if item.nane_dividend:
        return 0.0
    return item.gross_aud if item.assessable_aud is None else item.assessable_aud


class TreatyFitoInput(BaseModel):
    """Indonesian income items and tax paid, plus the taxpayer's position, for the foreign income tax offset of a resident individual."""

    items: list[ForeignTaxItem] = Field(min_length=1)
    taxable_income: float = Field(ge=0, description="Taxable income for the year, including the assessable Indonesian income and after all deductions "
                                                      "(debt deductions such as villa loan interest are already inside it).")
    related_deductions_aud: float = Field(0, ge=0, description="Deductions reasonably related to the Indonesian income, other than debt deductions (unless attributable "
                                                                 "to an overseas permanent establishment). Removed with the income at step 2 of the limit.")
    overseas_assets_max_value_aud: float | None = Field(None, ge=0, description="Optional: most the taxpayer's overseas assets were worth at any time in the year, to answer the return's overseas assets question.")
    resident_months: int = Field(12, ge=1, le=12)
    has_spouse: bool = False
    spouse_taxable_income: float = Field(0, ge=0)
    dependent_children: int = Field(0, ge=0)
    private_hospital_cover: bool | None = Field(None, description="None = not stated: Medicare levy surcharge is left out and a warning is given.")
    days_without_cover: int | None = Field(None, ge=0, le=366)
    reportable_fringe_benefits: float = Field(0, ge=0)
    net_investment_losses: float = Field(0, ge=0)
    reportable_super_contributions: float = Field(0, ge=0)
    exempt_foreign_employment_income: float = Field(0, ge=0)
    complications: list[FitoComplication] = Field(default_factory=list, description="Any special foreign income tax offset rule present; each stops the calculation (AU-RES-005).")

    def _raw_net_income(self) -> float:
        return sum(_assessable(i) for i in self.items) - self.related_deductions_aud

    def foreign_net_income(self) -> float:
        return max(0.0, self._raw_net_income())

    def to_fito(self, foreign_tax_paid: float) -> FitoInput:
        return FitoInput(
            foreign_tax_paid=foreign_tax_paid, taxable_income=self.taxable_income, foreign_net_income=self.foreign_net_income(),
            resident_months=self.resident_months, has_spouse=self.has_spouse, spouse_taxable_income=self.spouse_taxable_income,
            dependent_children=self.dependent_children, private_hospital_cover=self.private_hospital_cover,
            days_without_cover=self.days_without_cover, reportable_fringe_benefits=self.reportable_fringe_benefits,
            net_investment_losses=self.net_investment_losses, reportable_super_contributions=self.reportable_super_contributions,
            exempt_foreign_employment_income=self.exempt_foreign_employment_income, complications=self.complications)

    @model_validator(mode="after")
    def _consistent(self):
        if self._raw_net_income() < -1e-9:
            raise ValueError("related_deductions_aud exceed the assessable Indonesian income")
        self.to_fito(0.0)  # runs the offset tool's own input checks (foreign income within taxable income, spouse fields)
        return self


@calculator("indonesia_treaty_fito", TreatyFitoInput)
def indonesia_treaty_fito(figures: Figures, inp: TreatyFitoInput) -> dict:
    """Foreign income tax offset for Indonesian income of an Australian resident individual, in one step: applies the
    Australia-Indonesia treaty ceilings first (dividends Art 10(2), interest Art 11(2), royalties Art 12(2) in two tiers,
    pensions Art 18(2)), keeping only Indonesian tax correctly imposed within the ceiling as creditable and reporting the
    excess to be reclaimed from Indonesia (not FITO); apportions foreign tax on a discounted or loss-absorbed capital gain
    to the assessable part; gives no offset for a non-assessable non-exempt dividend (s 768-5); then runs the existing
    foreign_income_tax_offset tool (Div 770, offset limit s 770-75) on the total creditable tax. Items with no treaty
    ceiling (rent Art 6, employment, services, directors' fees, gains) are taken as the tax the taxpayer says was correctly
    imposed; whether Indonesian tax was correct under Indonesian law is NOT verified. Inputs: items (kind, gross_aud,
    foreign_tax_paid_aud, assessable_aud), taxable_income, related_deductions_aud, Medicare family details. Returns per-item
    outcomes, creditable_foreign_tax, excess_over_treaty_cap, and the offset result (fito). Refuses AU-RES-005 for the
    special cases the offset tool refuses. Use for "how much Indonesian tax can I claim as a credit", "treaty rate
    v withholding", "Bali rent foreign tax offset"."""
    rows, warnings = [], []
    total_creditable = 0.0
    total_excess = 0.0
    for it in inp.items:
        assessable = _assessable(it)
        row = {"label": it.label, "kind": it.kind, "gross_aud": _r(it.gross_aud), "foreign_tax_paid_aud": _r(it.foreign_tax_paid_aud),
               "assessable_aud": _r(assessable), "treaty_limit_rate": None, "treaty_limit_amount": None}
        if it.nane_dividend:
            row.update({"creditable_foreign_tax": 0.0, "excess_over_treaty_cap": 0.0, "not_creditable_non_assessable_part": _r(it.foreign_tax_paid_aud),
                        "note": "Non-assessable non-exempt dividend (ITAA 1997 s 768-5): no foreign income tax offset (ATO FITO guide Example 13)."})
            rows.append(row)
            continue
        after_cap = it.foreign_tax_paid_aud
        if it.kind in CAP_KEYS:
            key, ref = CAP_KEYS[it.kind]
            rate = figures.get(key)
            cap_amount = it.gross_aud * rate
            row.update({"treaty_limit_rate": rate, "treaty_limit_amount": _r(cap_amount), "treaty_limit_ref": ref})
            after_cap = min(it.foreign_tax_paid_aud, cap_amount)
        excess = it.foreign_tax_paid_aud - after_cap
        share = 1.0 if it.gross_aud == 0 else assessable / it.gross_aud
        creditable = after_cap * share
        row.update({"creditable_foreign_tax": _r(creditable), "excess_over_treaty_cap": _r(excess),
                    "not_creditable_non_assessable_part": _r(after_cap - creditable)})
        total_creditable += creditable
        total_excess += excess
        rows.append(row)
    if total_excess > 0.005:
        warnings.append("Indonesian tax above the treaty ceiling was not correctly imposed under the agreement: it is not creditable and should be "
                        "reclaimed from Indonesia (ITAA 1997 s 770-15). It is not carried forward or refunded by Australia.")
    if any(i.kind not in CAP_KEYS and not i.nane_dividend and i.foreign_tax_paid_aud > 0 for i in inp.items):
        warnings.append("Items with no treaty ceiling use the Indonesian tax stated as paid and correctly imposed under Indonesian law. Indonesian domestic "
                        "tax is not verified here; keep withholding slips or the assessment (AU-IDN-002 if asked to judge correctness).")
    warnings.append("Villa loan interest, borrowing costs and other debt deductions are not part of related_deductions_aud: they stay in taxable income at step 2 "
                    "unless attributable to an overseas permanent establishment (ITAA 1997 s 770-75(4)).")
    fi = foreign_income_tax_offset(figures, inp.to_fito(total_creditable))
    fito = {k: v for k, v in fi.items() if k not in ("assumptions", "warnings")}
    out = {
        "items": rows,
        "creditable_foreign_tax": _r(total_creditable),
        "excess_over_treaty_cap": _r(total_excess),
        "foreign_net_income_step2": _r(inp.foreign_net_income()),
        "fito": fito,
        "assumptions": fi["assumptions"] + ["Treaty ceilings apply to the gross amount before Indonesian withholding; a ceiling limits the tax, it is not the rate Indonesia charges.",
                                            "Indonesian tax is translated to AUD at the time it was paid (ITAA 1997 s 960-50); use idr_to_aud."],
        "warnings": warnings + fi["warnings"],
    }
    if inp.overseas_assets_max_value_aud is not None:
        threshold = figures.get("au_indonesia.foreign_assets_reporting_threshold")
        out["foreign_assets_label_p_yes"] = inp.overseas_assets_max_value_aud >= threshold
    return out


# ============================================================================= Australian withholding on an Indonesian payee

class WithholdingInput(BaseModel):
    """A payment by an Australian payer to a payee that may be an Indonesian resident."""

    payment_kind: Literal["dividend", "interest", "royalty_equipment_know_how", "royalty_other"]
    gross_amount: float | None = Field(None, ge=0, description="Interest or royalty, gross, in AUD.")
    unfranked_amount: float | None = Field(None, ge=0, description="Dividend: the unfranked part, in AUD.")
    franked_amount: float | None = Field(None, ge=0, description="Dividend: the franked part, in AUD.")
    payee_resident_of_indonesia: bool
    beneficially_entitled: bool = Field(description="The payee is the beneficial owner, not a conduit, agent or nominee.")
    connected_with_australian_pe: bool = Field(False, description="The payment is effectively connected with the payee's Australian permanent establishment (AU-IDN-001).")

    @model_validator(mode="after")
    def _shape(self):
        if self.payment_kind == "dividend":
            if self.gross_amount is not None:
                raise ValueError("for a dividend give unfranked_amount and franked_amount, not gross_amount")
            if self.unfranked_amount is None and self.franked_amount is None:
                raise ValueError("a dividend needs unfranked_amount and/or franked_amount")
        else:
            if self.gross_amount is None:
                raise ValueError("gross_amount is required for interest and royalties")
            if self.unfranked_amount is not None or self.franked_amount is not None:
                raise ValueError("unfranked_amount and franked_amount are for dividends only")
        return self


@calculator("au_withholding_indonesian_payee", WithholdingInput)
def au_withholding_indonesian_payee(figures: Figures, inp: WithholdingInput) -> dict:
    """Australian withholding tax an Australian payer withholds from a dividend, interest or royalty paid to a payee that is
    (or may be) a resident of Indonesia. Unfranked dividends and royalties are withheld at the lower of the domestic rate
    and the Australia-Indonesia treaty ceiling (Arts 10(2), 12(2); ITAA 1953 s 17A(1)); interest at the domestic rate, which
    equals the ceiling (Art 11(2)); franked dividends carry no withholding. The treaty rate needs an Indonesian resident payee
    who is beneficially entitled: a conduit or non-resident gets the domestic rate. A payment effectively connected with
    the payee's Australian permanent establishment is refused (AU-IDN-001). Inputs: payment_kind, gross_amount (interest,
    royalty) or unfranked_amount and franked_amount (dividend), payee_resident_of_indonesia, beneficially_entitled. Returns
    the rate applied, withholding, net paid and the treaty relief. Use for "withholding tax on a dividend to my Indonesian
    shareholder", "royalty paid to Jakarta", "interest to an Indonesian lender"."""
    if inp.connected_with_australian_pe:
        raise Refusal("AU-IDN-001", "payment effectively connected with an Australian permanent establishment of the payee")
    k = inp.payment_kind
    domestic_key = {"dividend": "au_indonesia.au_wht_unfranked_dividend_rate", "interest": "au_indonesia.au_wht_interest_rate"}.get(k, "au_indonesia.au_wht_royalty_rate")
    cap_key, cap_ref = {"dividend": ("residency.indonesia_dta_wht_dividends", "Art 10(2)"),
                        "interest": ("residency.indonesia_dta_wht_interest", "Art 11(2)")}.get(k, (
        "residency.indonesia_dta_wht_royalties_equipment_know_how" if k == "royalty_equipment_know_how" else "residency.indonesia_dta_wht_royalties_other", "Art 12(2)"))
    domestic = figures.get(domestic_key)
    cap = figures.get(cap_key)
    treaty = inp.payee_resident_of_indonesia and inp.beneficially_entitled
    applied = min(domestic, cap) if treaty else domestic
    base = (inp.unfranked_amount or 0.0) if k == "dividend" else inp.gross_amount
    withholding = base * applied
    total = ((inp.unfranked_amount or 0.0) + (inp.franked_amount or 0.0)) if k == "dividend" else inp.gross_amount
    warnings = []
    if inp.payee_resident_of_indonesia and not inp.beneficially_entitled:
        warnings.append("The payee is not beneficially entitled (conduit, agent or nominee): the treaty ceiling is not available and the domestic rate applies. "
                        "If the beneficial owner is an Indonesian resident behind the payee, or a principal purpose test issue arises, escalate (AU-IDN-005).")
    if not inp.payee_resident_of_indonesia:
        warnings.append("The payee is not an Indonesian resident, so the Australia-Indonesia agreement is not applied. The domestic rate is shown; another treaty may apply (AU-RES-001).")
    warnings.append("The reduced rate needs the payee to be a resident of Indonesia and beneficially entitled; the payer should hold the payee's current overseas address and "
                    "residency evidence. The MLI principal purpose test can deny a ceiling where obtaining it was a principal purpose of an arrangement.")
    out = {
        "payment_kind": k, "treaty_applied": treaty, "domestic_rate": domestic, "treaty_limit_rate": cap, "treaty_limit_ref": cap_ref, "applied_rate": applied,
        "withholding_base": _r(base), "withholding": _r(withholding), "net_paid": _r(total - withholding),
        "treaty_relief": _r(base * (domestic - applied)),
        "assumptions": ["Withholding is on the gross amount, in AUD, before any Australian tax offset the payee may later claim.",
                        "Rates: Income Tax (Dividends, Interest and Royalties Withholding Tax) Act 1974 s 7; the treaty ceiling reduces the liability through ITAA 1953 s 17A(1)."],
        "warnings": warnings,
    }
    if k == "dividend":
        out["franked_withholding"] = 0.0
        out["assumptions"].append("The franked part of a dividend carries no dividend withholding; withholding applies to the unfranked part only (ATO withholding pages; Explanatory Memorandum 1992, Art 10).")
    return out


# ============================================================================= rupiah translation

class IdrInput(BaseModel):
    """Translate a rupiah amount to AUD from a rate published by the ATO, or from a supplied rate with its source."""

    idr_amount: float
    translation_basis: Literal["annual_average", "monthly_average", "actual_30_jun", "supplied_rate"]
    nature: Literal["income_or_deduction_spread_over_year", "one_off_capital_event", "single_dated_item"] = Field(description=(
        "income_or_deduction_spread_over_year: regular income or expense across the year (rent, interest). one_off_capital_event: a sale or purchase "
        "of an asset (every cost base element has its own date). single_dated_item: one payment or receipt on a known date, such as Indonesian tax paid."))
    month: Literal["jul", "aug", "sep", "oct", "nov", "dec", "jan", "feb", "mar", "apr", "may", "jun"] | None = Field(None, description="monthly_average: the month of the income year.")
    event_date: date | None = Field(None, description="Date of the event or payment. Required for one_off_capital_event and single_dated_item with a supplied rate, and for actual_30_jun.")
    supplied_rate_idr_per_aud: float | None = Field(None, gt=0, description="supplied_rate: rupiah per A$1 for the date, for example the Reserve Bank of Australia daily rate.")
    supplied_rate_source: str | None = Field(None, description="supplied_rate: where the rate came from (kept as evidence).")

    @model_validator(mode="after")
    def _checks(self):
        b = self.translation_basis
        if b == "supplied_rate":
            if self.supplied_rate_idr_per_aud is None or not (self.supplied_rate_source or "").strip():
                raise ValueError("supplied_rate needs supplied_rate_idr_per_aud and supplied_rate_source")
            if self.nature != "income_or_deduction_spread_over_year" and self.event_date is None:
                raise ValueError("a supplied rate for a one-off event or dated item needs event_date")
        elif self.supplied_rate_idr_per_aud is not None or self.supplied_rate_source is not None:
            raise ValueError("supplied_rate_idr_per_aud and supplied_rate_source are only for translation_basis supplied_rate")
        if b == "monthly_average":
            if self.month is None and self.event_date is None:
                raise ValueError("monthly_average needs month or event_date")
            if self.month is not None and self.event_date is not None and MONTHS[(self.event_date.month - 7) % 12] != self.month:
                raise ValueError("month does not match event_date")
        return self


@calculator("idr_to_aud", IdrInput)
def idr_to_aud(figures: Figures, inp: IdrInput) -> dict:
    """Translates a rupiah (IDR) amount to Australian dollars using a rate the ATO has published for the income year:
    the annual average (year to 30 June), a monthly average, or the nearest actual rate at 30 June; or a rate you supply
    (for example the Reserve Bank daily rate) with its source. The ATO does publish rupiah rates. Rules (ITAA 1997 s 960-50;
    ATO translation rules): an average suits income or expenses spread over the period, not a one-off capital event, which
    needs the rate at the event (the 30 June rate only on 30 June); a year-end rate is not a substitute for income or tax that
    arose on other dates; Indonesian tax paid is translated when paid. Refuses AU-IDN-006 where the basis is not allowed, the
    date is outside the income year or no event rate is available, and AU-GEN-003 where the ATO figure is not yet published
    (for example most months of 2026-27). Inputs: idr_amount, translation_basis, nature, month or event_date, supplied rate
    and source. Use for "convert rupiah rent to AUD", "what rate do I use", "villa sale in IDR"."""
    b, nature, d = inp.translation_basis, inp.nature, inp.event_date
    meta = figures.data.get("meta", {})
    start, end = meta.get("start"), meta.get("end")
    if b != "supplied_rate" and d is not None and isinstance(start, date) and isinstance(end, date) and not (start <= d <= end):
        raise Refusal("AU-IDN-006", f"event date {d.isoformat()} is outside the {figures.income_year} income year whose rates are being used")
    assumptions = ["Amounts are translated to AUD at the time of the receipt, payment or event, or by an acceptable average where the income arises across the period "
                   "(ITAA 1997 s 960-50(6)); Indonesian tax paid is translated at the time it was paid."]
    warnings: list[str] = []
    if b == "supplied_rate":
        rate, basis_note = inp.supplied_rate_idr_per_aud, f"supplied rate, source: {inp.supplied_rate_source.strip()}"
        warnings.append("Keep the rate and its source with the records. The ATO accepts a rate from an Australian bank or another reliable external source where it "
                        "does not publish one; a rate from the taxpayer or an associate is not acceptable.")
    elif b == "actual_30_jun":
        if nature == "income_or_deduction_spread_over_year":
            raise Refusal("AU-IDN-006", "a year-end rate is not allowed for income or deductions spread across the year")
        if d is None or not (isinstance(end, date) and d == end):
            raise Refusal("AU-IDN-006", "the nearest actual 30 June rate is right only for a transaction on 30 June; supply the rate for the event date")
        rate, basis_note = figures.get("au_indonesia.fx_idr_per_aud_nearest_actual_30_jun"), "ATO annual table, nearest actual rate at 30 June"
    elif nature == "one_off_capital_event":
        raise Refusal("AU-IDN-006", "an average rate does not suit a one-off capital event; each cost base element uses the rate at its own time")
    elif b == "annual_average":
        rate, basis_note = figures.get("au_indonesia.fx_idr_per_aud_average_year_to_30_jun"), "ATO annual average, year ended 30 June"
        warnings.append("An average is acceptable only where it reasonably approximates the rates at the time of each receipt or payment.")
    else:
        month = inp.month or MONTHS[(d.month - 7) % 12]
        rate, basis_note = figures.get(f"au_indonesia.fx_idr_per_aud_monthly_average_{month}"), f"ATO monthly average, {month.capitalize()} of the income year"
        warnings.append("An average is acceptable only where it reasonably approximates the rates at the time of each receipt or payment.")
    if nature == "single_dated_item" and b in ("annual_average", "monthly_average"):
        warnings.append("Indonesian tax paid is translated at the time it was paid; an average is a fallback for an item on a known date.")
    return {"idr_amount": inp.idr_amount, "rate_used": rate, "rate_basis": basis_note, "aud_amount": _r(inp.idr_amount / rate),
            "nature": nature, "assumptions": assumptions, "warnings": warnings}


# ============================================================================= scope check

Situation = Literal[
    "pe_or_fixed_base_question", "dependent_agent", "building_site_or_installation", "indonesian_domestic_tax_question",
    "indonesian_domestic_residency", "indonesian_company_or_pt", "trust_or_partnership_with_indonesian_income", "related_party_charges",
    "land_rich_or_indirect_property_interest", "royalty_or_software_characterisation", "treaty_benefit_denial_or_conduit",
    "dual_resident_company", "other_treaty_country", "offshore_company_controlled", "foreign_pension_or_super",
]
_SCOPE_CODES = {
    "pe_or_fixed_base_question": "AU-IDN-001", "dependent_agent": "AU-IDN-001", "building_site_or_installation": "AU-IDN-001",
    "indonesian_domestic_tax_question": "AU-IDN-002", "indonesian_domestic_residency": "AU-IDN-002",
    "indonesian_company_or_pt": "AU-IDN-003", "trust_or_partnership_with_indonesian_income": "AU-IDN-003", "related_party_charges": "AU-IDN-003",
    "land_rich_or_indirect_property_interest": "AU-IDN-004",
    "royalty_or_software_characterisation": "AU-IDN-005", "treaty_benefit_denial_or_conduit": "AU-IDN-005",
    "dual_resident_company": "AU-RES-001", "other_treaty_country": "AU-RES-001",
    "offshore_company_controlled": "AU-RES-002", "foreign_pension_or_super": "AU-RES-003",
}


class ScopeInput(BaseModel):
    """Situations present in an Australia-Indonesia matter."""

    situations: list[Situation] = Field(default_factory=list, description="Every out-of-scope situation that is present.")


@calculator("indonesia_scope_check", ScopeInput)
def indonesia_scope_check(figures: Figures, inp: ScopeInput) -> dict:
    """Checks whether an Australia-Indonesia matter is inside the au-indonesia-cross-border skill. Pass situations such as
    pe_or_fixed_base_question, dependent_agent, building_site_or_installation, indonesian_domestic_tax_question,
    indonesian_domestic_residency, indonesian_company_or_pt, trust_or_partnership_with_indonesian_income, related_party_charges,
    land_rich_or_indirect_property_interest, royalty_or_software_characterisation, treaty_benefit_denial_or_conduit,
    dual_resident_company, other_treaty_country, offshore_company_controlled (an Australian resident controlling a PT),
    foreign_pension_or_super. If any is present it refuses with the escalation code and fixed message to quote (AU-IDN-001 to
    AU-IDN-005, or AU-RES-001 to AU-RES-003); with none it returns in_scope true. Call it whenever the facts involve a permanent
    establishment or fixed base, an Indonesian company, Indonesian domestic tax, land-rich shares or a royalty characterisation."""
    if inp.situations:
        codes = sorted({_SCOPE_CODES[s] for s in inp.situations})
        raise Refusal(codes[0], ", ".join(inp.situations) + (f" (also {', '.join(codes[1:])})" if len(codes) > 1 else ""))
    return {"in_scope": True, "assumptions": [], "warnings": []}
