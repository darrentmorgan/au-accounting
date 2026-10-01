"""Superannuation contributions, the individual member's view: concessional cap position (with
five-year carry forward and excess concessional contributions), non-concessional cap and bring
forward, Division 293 tax, Division 296 tax on large balances (from 2026-27), government
co-contribution, low income super tax offset (LISTO), spouse contribution offset and downsizer
contribution limits.

Law: ITAA 1997 Subdiv 290-C (s290-170 notice of intent), Subdiv 290-D (ss290-230, 290-235),
Div 291 (s291-15, s291-20), Div 292 (ss292-85, 292-90, 292-102), Div 293 (ss293-20 to 293-30),
Div 296 (ss296-15 to 296-55, inserted by Act No. 8 of 2026) with the Superannuation (Building a
Stronger and Fairer Super System) Imposition Act 2026 (No. 9) s5; Superannuation (Government
Co-contribution for Low Income Earners) Act 2003 ss6-11, 12C, 12E. Every rate and threshold comes
from data/rates/<year>.yaml and its overlays via Figures. Employer SG obligations belong to payroll.
"""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from au_tax.figures import FigureError, Figures
from au_tax.registry import Refusal, calculator

# ---------------------------------------------------------------- helpers


def _r(x: float) -> float:
    return round(x + 0.0, 2)


def _start(year: str) -> int:
    return int(year[:4])


def _label(start: int) -> str:
    return f"{start}-{str(start + 1)[-2:]}"


def _hist_key(name: str, year: str) -> str:
    return f"super.{name}_{year.replace('-', '_')}"


def _cap_for(figures: Figures, name: str, year: str) -> float:
    """Current-year cap from the base key, earlier years from the overlay history keys."""
    if year == figures.income_year:
        return figures.get(f"super.{name}")
    return figures.get(_hist_key(name, year))


def _year_field(v: str) -> str:
    if len(v) != 7 or v[4] != "-" or not v[:4].isdigit() or int(v[5:]) != (int(v[:4]) + 1) % 100:
        raise ValueError(f"income year must look like 2025-26, got {v!r}")
    return v


# ---------------------------------------------------------------- refusals shared by several tools

class _Scope(BaseModel):
    has_defined_benefit_interest: bool = Field(
        False, description="Member has a defined benefit interest (including untaxed or constitutionally "
        "protected funds). Caps, Div 293 and Div 296 use special valuation rules: refused (AU-SUPER-001).")
    special_contributions: list[Literal[
        "foreign_super_transfer", "personal_injury_structured_settlement", "cgt_cap_small_business",
        "fhss_recontribution", "covid_recontribution", "family_law_split"]] = Field(
        default_factory=list, description="Special contribution types present; each is outside this tool (AU-SUPER-006).")


def _scope_check(inp: _Scope) -> None:
    if inp.has_defined_benefit_interest:
        raise Refusal("AU-SUPER-001", "defined benefit interest")
    if inp.special_contributions:
        raise Refusal("AU-SUPER-006", ", ".join(inp.special_contributions))


# ================================================================ concessional cap position

class PriorYear(BaseModel):
    income_year: str = Field(description="Earlier income year, e.g. 2023-24.")
    concessional_contributions: float = Field(ge=0, description="Total concessional contributions counted for that year.")
    tsb_prior_30_june: float | None = Field(
        None, ge=0, description="Total super balance at 30 June before that year. Needed only if that year's "
        "contributions exceeded its general cap (to know whether carry forward was used).")

    _y = field_validator("income_year")(classmethod(lambda cls, v: _year_field(v)))


class UnappliedAmount(BaseModel):
    income_year: str = Field(description="Year the unused cap arose, e.g. 2022-23.")
    amount: float = Field(ge=0, description="Unapplied unused concessional cap still available for that year "
                          "(as shown in ATO online services, Super > Carry-forward concessional contributions).")

    _y = field_validator("income_year")(classmethod(lambda cls, v: _year_field(v)))


class ConcessionalInput(_Scope):
    """One member, one income year. Amounts in AUD received by the fund(s) in the year."""

    employer_contributions: float = Field(0, ge=0, description="Employer contributions: SG and any other employer amounts, excluding salary sacrifice.")
    salary_sacrifice: float = Field(0, ge=0, description="Salary sacrifice contributions.")
    personal_deductible: float = Field(0, ge=0, description="Personal contributions for which a deduction is claimed (or intended).")
    other_concessional: float = Field(0, ge=0, description="Other concessional amounts (e.g. fund reserve allocations, notional employer amounts for non-DB).")
    noi_acknowledged: bool | None = Field(
        None, description="True if a valid notice of intent to deduct was given and acknowledged by the fund in time "
        "(ITAA 1997 s290-170). False = the personal contributions stay non-concessional. None = not stated.")
    tsb_prior_30_june: float | None = Field(None, ge=0, description="Total super balance at 30 June before this income year (carry-forward test).")
    unapplied_unused: list[UnappliedAmount] | None = Field(
        None, description="Unapplied unused cap amounts by year, if known (ATO online services). Use this OR prior_years.")
    prior_years: list[PriorYear] | None = Field(
        None, description="Concessional contributions for consecutive earlier years ending with the previous year "
        "(ideally all years from 2018-19, at least the last five). The tool replays carry forward earliest first.")
    age_at_contribution: int | None = Field(None, ge=0, le=120, description="Age when personal contributions were made (deductibility age tests).")
    taxable_income_excluding_excess: float | None = Field(
        None, ge=0, description="Taxable income before adding any excess concessional contributions; if given, the extra "
        "income tax and Medicare levy on the excess is estimated (resident, no other offsets).")
    release_excess: bool = Field(False, description="True if the member elects to release up to 85% of the excess (TAA 1953 Sch 1 Div 131).")

    @model_validator(mode="after")
    def _one_history(self):
        if self.unapplied_unused is not None and self.prior_years is not None:
            raise ValueError("give either unapplied_unused or prior_years, not both")
        return self


def _replay(figures: Figures, rows: list[PriorYear], first_unused: int, window: int,
            limit: float, assumptions: list[str]) -> dict[str, float]:
    """Replay earlier years (consecutive, ending the year before) and return unapplied unused cap by year."""
    cur = _start(figures.income_year)
    rows = sorted(rows, key=lambda r: _start(r.income_year))
    starts = [_start(r.income_year) for r in rows]
    if starts[-1] != cur - 1 or starts != list(range(starts[0], cur)):
        raise Refusal("AU-SUPER-008", f"prior_years must be consecutive and end with {_label(cur - 1)}")
    bank: dict[str, float] = {}
    for r in rows:
        y = r.income_year
        ys = _start(y)
        if ys < first_unused:
            continue
        cap = _cap_for(figures, "concessional_cap", y)
        for k in [k for k in bank if _start(k) < ys - window]:
            del bank[k]  # expired: more than 5 years earlier
        if r.concessional_contributions < cap:
            bank[y] = cap - r.concessional_contributions
        elif r.concessional_contributions > cap and bank:
            if r.tsb_prior_30_june is None:
                raise Refusal("AU-SUPER-008", f"tsb_prior_30_june is needed for {y}: contributions exceeded that year's cap")
            if r.tsb_prior_30_june < limit:
                need = r.concessional_contributions - cap
                for k in sorted(bank, key=_start):
                    use = min(need, bank[k])
                    bank[k] -= use
                    need -= use
                bank = {k: v for k, v in bank.items() if v > 0}
    if starts[0] > first_unused:
        assumptions.append(f"Years before {rows[0].income_year} were not given: assumed they left no unapplied unused cap "
                           "that was later drawn on. Give earlier years (from 2018-19) if carry forward was used before.")
    return {k: v for k, v in bank.items() if _start(k) >= cur - window}


@calculator("concessional_cap_position", ConcessionalInput)
def concessional_cap_position(figures: Figures, inp: ConcessionalInput) -> dict:
    """Concessional contributions cap position for one member for one income year (2025-26 or
    2026-27): totals concessional contributions (employer/SG, salary sacrifice, personal deductible
    with a valid notice of intent, other), applies the five-year carry forward of unused cap when total
    super balance at the prior 30 June is below the carry-forward limit (earliest year first), and
    returns the available cap, any excess concessional contributions (included in assessable income
    with a 15% non-refundable offset; counts towards the non-concessional cap unless released), the
    optional extra tax on the excess, and the unused amounts carried to next year. Use for "how much
    can I contribute", "catch-up contributions", "carry-forward concessional", "did I exceed my
    concessional cap", "salary sacrifice limit". Refuses AU-SUPER-001 (defined benefit) and
    AU-SUPER-006 (special contribution types)."""
    _scope_check(inp)
    assumptions: list[str] = []
    warnings: list[str] = []
    escalations: list[str] = []
    year = figures.income_year
    cur = _start(year)
    cap = figures.get("super.concessional_cap")
    limit = figures.get("super.carry_forward_tsb_limit")
    window = figures.get("super.carry_forward_years")
    first_unused = figures.get("super.carry_forward_first_unused_year_start")

    personal = inp.personal_deductible
    reclassified = 0.0
    if personal:
        if inp.noi_acknowledged is False:
            reclassified, personal = personal, 0.0
            warnings.append("No valid acknowledged notice of intent (ITAA 1997 s290-170): the personal contributions are "
                            "not deductible and count as non-concessional contributions instead.")
        elif inp.noi_acknowledged is None:
            assumptions.append("Assumed a valid notice of intent will be given and acknowledged before the earlier of lodging "
                               f"the {year} return and 30 June {cur + 2} (ITAA 1997 s290-170(1)).")
        if inp.age_at_contribution is not None and inp.age_at_contribution >= 67:
            warnings.append("Aged 67 or over: a personal deduction needs the work test (40 hours in 30 consecutive days) or the "
                            "work test exemption (ITAA 1997 s290-165(1A)); no deduction after 28 days past the month of turning 75.")
    total = inp.employer_contributions + inp.salary_sacrifice + personal + inp.other_concessional

    # unapplied unused amounts from the previous 5 years
    bank: dict[str, float] = {}
    if inp.unapplied_unused is not None:
        for u in inp.unapplied_unused:
            s = _start(u.income_year)
            if s >= cur:
                raise Refusal("AU-SUPER-008", "unapplied_unused years must be earlier than the income year")
            if s < max(cur - window, first_unused):
                warnings.append(f"Unused amount for {u.income_year} has expired or never existed and was ignored.")
                continue
            bank[u.income_year] = bank.get(u.income_year, 0.0) + u.amount
        history_basis = "unapplied amounts supplied"
    elif inp.prior_years:
        bank = _replay(figures, inp.prior_years, first_unused, window, limit, assumptions)
        history_basis = "replayed from prior-year contributions"
    else:
        history_basis = "none supplied"
        if total > cap:
            assumptions.append("No earlier-year history given: no unused cap amounts assumed. Supply prior years to test carry forward.")

    tsb = inp.tsb_prior_30_june
    eligible = tsb is not None and tsb < limit
    if tsb is None and bank and total > cap:
        warnings.append("Total super balance at the prior 30 June not given: carry forward cannot be confirmed and was not applied.")
    available_unused = _r(sum(bank.values())) if eligible else 0.0

    applied: dict[str, float] = {}
    if total > cap and eligible:
        need = total - cap
        for k in sorted(bank, key=_start):  # s291-20(5): earliest first
            use = min(need, bank[k])
            if use > 0:
                applied[k] = _r(use)
                bank[k] -= use
                need -= use
    increased_cap = cap + sum(applied.values())
    excess = max(0.0, total - increased_cap)

    carried: dict[str, float] = {k: _r(v) for k, v in bank.items() if _start(k) > cur - window and v > 0}
    if total < cap and cur >= first_unused:
        carried[year] = _r(cap - total)
    expiring = {k: _r(v) for k, v in bank.items() if _start(k) == cur - window and v > 0}

    out: dict = {
        "general_cap": cap,
        "concessional_contributions": {
            "employer": _r(inp.employer_contributions), "salary_sacrifice": _r(inp.salary_sacrifice),
            "personal_deductible": _r(personal), "other": _r(inp.other_concessional), "total": _r(total)},
        "personal_reclassified_as_non_concessional": _r(reclassified),
        "carry_forward": {
            "tsb_prior_30_june": tsb, "tsb_limit": limit, "eligible": eligible,
            "history_basis": history_basis, "unapplied_unused_by_year": {k: _r(v) for k, v in
                                                                            sorted(((k, v + applied.get(k, 0)) for k, v in bank.items()), key=lambda kv: _start(kv[0]))},
            "available_unused_total": available_unused, "applied_by_year": applied,
            "expiring_after_this_year": expiring},
        "available_cap": _r(cap + available_unused),
        "cap_after_carry_forward": _r(increased_cap),
        "remaining_room": _r(max(0.0, cap + available_unused - total)),
        "excess_concessional_contributions": _r(excess),
        "unused_carried_to_next_year": carried,
    }
    if excess:
        rate = figures.get("super.excess_concessional_offset_rate")
        offset = rate * excess
        div = figures.get("super.excess_concessional_release_divisor")
        release_max = div * excess
        out["excess_treatment"] = {
            "included_in_assessable_income": _r(excess),
            "non_refundable_offset": _r(offset),
            "max_release_amount": _r(release_max),
            "counts_towards_non_concessional_cap": 0.0 if inp.release_excess else _r(excess),
        }
        assumptions.append("Excess concessional contributions are included in assessable income and attract a 15% non-refundable "
                           "offset (ITAA 1997 s291-15). No excess concessional contributions charge applies from 2021-22.")
        if inp.release_excess:
            assumptions.append("Release elected: amounts released (divided by 85%) reduce the excess counted as non-concessional "
                               "contributions (ITAA 1997 s292-90(1A)); assumed the full 85% is released.")
        else:
            warnings.append("Unreleased excess concessional contributions count towards the non-concessional cap (ITAA 1997 "
                            "s292-90(1)(b)); check the non-concessional position with bring_forward_nonconcessional.")
        if inp.taxable_income_excluding_excess is not None:
            extra = _extra_tax(figures, inp.taxable_income_excluding_excess, excess, warnings)
            if extra is not None:
                out["excess_treatment"]["extra_tax_and_levy_before_offset"] = _r(extra)
                out["excess_treatment"]["net_extra_tax"] = _r(max(0.0, extra - offset))
                assumptions.append("Extra tax estimated as the change in resident income tax (after LITO) plus Medicare levy from "
                                   "adding the excess to taxable income; other offsets, MLS and HELP ignored.")
    if total > cap and not eligible and tsb is not None:
        warnings.append("Total super balance at the prior 30 June is at or above the carry-forward limit: no unused cap can be used this year.")
    out.update({"assumptions": assumptions, "warnings": warnings, "escalations": escalations})
    return out


def _extra_tax(figures: Figures, ti: float, excess: float, warnings: list[str]) -> float | None:
    from au_tax.calculators.individual import IndividualTaxInput, _core

    try:
        base = _core(figures, IndividualTaxInput(taxable_income=ti), ti, [], [])
        high = _core(figures, IndividualTaxInput(taxable_income=ti + excess), ti + excess, [], [])
    except FigureError as e:
        warnings.append(f"Extra tax on the excess not estimated: {e}")
        return None
    return (high["net"] + high["levy"]) - (base["net"] + base["levy"])


# ================================================================ non-concessional / bring forward

class PriorTrigger(BaseModel):
    trigger_year: str = Field(description="Income year in which a bring-forward period was triggered (one of the 2 previous years).")
    period_years: Literal[2, 3] = Field(description="Length of that bring-forward period (2 or 3 years), as shown in ATO online services.")
    ncc_since_trigger: float = Field(ge=0, description="Non-concessional contributions made in the period before this income year (including the trigger year).")

    _y = field_validator("trigger_year")(classmethod(lambda cls, v: _year_field(v)))


class NonConcessionalInput(_Scope):
    """One member, one income year."""

    age_at_1_july: int = Field(ge=0, le=120, description="Age on 1 July of the income year (bring forward needs age under 75 at any time in the year).")
    tsb_prior_30_june: float = Field(ge=0, description="Total super balance at 30 June before this income year.")
    prior_trigger: PriorTrigger | None = Field(None, description="Bring-forward period triggered in one of the 2 previous years, if any. None = no earlier trigger (confirm in ATO online services).")
    planned_ncc: float | None = Field(None, ge=0, description="Non-concessional contributions made or planned this year (include unreleased excess concessional contributions and personal contributions not deducted).")


@calculator("bring_forward_nonconcessional", NonConcessionalInput)
def bring_forward_nonconcessional(figures: Figures, inp: NonConcessionalInput) -> dict:
    """Non-concessional contributions cap for one member for one income year (2025-26 or 2026-27),
    including the bring-forward arrangement (ITAA 1997 s292-85): nil cap when total super balance at
    the prior 30 June is at or above the general transfer balance cap; a new 2- or 3-year period
    (first-year cap 2x or 3x the annual cap) set by the cap space below the transfer balance cap and
    age under 75; or the remaining cap in an existing period triggered in one of the two previous
    years (trigger-year cap, not indexed). With planned_ncc, reports whether it triggers a period and
    any excess (release or excess tax options: escalate the election, AU-SUPER-003). Use for "how
    much can I put in after tax", "bring forward", "non-concessional cap", "$X lump sum into super"."""
    _scope_check(inp)
    assumptions: list[str] = []
    warnings: list[str] = []
    escalations: list[str] = []
    year = figures.income_year
    cur = _start(year)
    annual = figures.get("super.non_concessional_cap")
    tbc = figures.get("super.transfer_balance_cap")
    age_limit = figures.get("super.bring_forward_age_limit")
    tsb = inp.tsb_prior_30_june
    out: dict = {"annual_cap": annual, "general_transfer_balance_cap": tbc, "tsb_prior_30_june": tsb}

    in_period = None
    if inp.prior_trigger is not None:
        t = inp.prior_trigger
        offset = cur - _start(t.trigger_year)
        if offset < 1 or offset > 2:
            raise Refusal("AU-SUPER-008", "prior_trigger.trigger_year must be one of the two previous income years")
        if offset < t.period_years:
            in_period = (t, offset)
        else:
            assumptions.append(f"The {t.period_years}-year period triggered in {t.trigger_year} has ended; a new period can start this year.")

    if in_period:
        t, offset = in_period
        trig_cap = figures.get(_hist_key("nonconcessional_cap", t.trigger_year))
        total_bf = t.period_years * trig_cap
        remaining = max(0.0, total_bf - t.ncc_since_trigger)
        nil = tsb >= tbc
        cap = 0.0 if nil else remaining
        out.update({
            "status": "within_existing_bring_forward_period",
            "period": {"trigger_year": t.trigger_year, "period_years": t.period_years, "year_of_period": offset + 1,
                       "trigger_year_annual_cap": trig_cap, "bring_forward_cap": _r(total_bf),
                       "used_before_this_year": _r(t.ncc_since_trigger), "remaining": _r(remaining)},
            "cap_this_year": _r(cap), "can_trigger_new_period": False,
        })
        assumptions.append("Within a bring-forward period the cap is the trigger-year amount (no indexation) less contributions "
                           "already made in the period (ITAA 1997 s292-85(6)-(7)).")
        if nil:
            warnings.append("Total super balance at the prior 30 June is at or above the general transfer balance cap: the "
                            "remaining bring-forward cap is nil this year (s292-85(6)(a)(i), (7)(a)(i)).")
    elif tsb >= tbc:
        out.update({"status": "nil_cap", "cap_this_year": 0.0, "can_trigger_new_period": False})
        warnings.append("Total super balance at the prior 30 June is at or above the general transfer balance cap: the "
                        "non-concessional cap is nil (ITAA 1997 s292-85(2)(b)); any non-concessional contribution is excess.")
    else:
        space = tbc - tsb
        young = inp.age_at_1_july < age_limit
        if not young:
            period, first = 1, annual
            reason = f"aged {age_limit} or over for the whole year: no bring forward (s292-85(3)(c))"
        elif space <= annual:
            period, first = 1, annual
            reason = "cap space below the transfer balance cap does not exceed the annual cap: no bring forward (s292-85(3)(e))"
        elif space <= 2 * annual:
            period, first = 2, 2 * annual
            reason = "cap space exceeds 1x but not 2x the annual cap: 2-year period (s292-85(4), (5)(a))"
        else:
            period, first = 3, 3 * annual
            reason = "cap space exceeds 2x the annual cap: 3-year period (s292-85(5)(b))"
        out.update({
            "status": "annual_cap_bring_forward_available" if period > 1 else "annual_cap_only",
            "cap_space": _r(space), "bring_forward_period_years": period if period > 1 else 0,
            "max_first_year_cap": _r(first), "cap_this_year": _r(annual), "can_trigger_new_period": period > 1,
            "basis": reason,
        })
        if period > 1:
            assumptions.append("Bring forward is triggered automatically only if this year's non-concessional contributions exceed the annual cap.")
        if young and inp.age_at_1_july >= 67:
            warnings.append("Funds may accept non-concessional contributions only until 28 days after the end of the month the "
                            "member turns 75; check fund acceptance timing.")

    if inp.planned_ncc is not None:
        p = inp.planned_ncc
        if out["status"] == "annual_cap_bring_forward_available" and p > annual:
            limit_ = out["max_first_year_cap"]
            out["triggers_bring_forward"] = True
            out["cap_this_year"] = _r(limit_)
            out["remaining_in_period_after_this_year"] = _r(max(0.0, limit_ - p))
        else:
            limit_ = out["cap_this_year"]
            out["triggers_bring_forward"] = False
        excess = max(0.0, p - limit_)
        best = out.get("max_first_year_cap", out["cap_this_year"]) if out["status"].startswith("annual_cap") else out["cap_this_year"]
        out["further_room_this_year_without_excess"] = _r(max(0.0, best - p))
        if out["status"] == "annual_cap_bring_forward_available" and p <= annual and best > annual:
            assumptions.append("Contributing more than the annual cap this year (up to the maximum first-year cap) automatically "
                               "triggers the bring-forward period; that is not excess.")
        out["planned_ncc"] = _r(p)
        out["excess_non_concessional_contributions"] = _r(excess)
        if excess:
            escalations.append("AU-SUPER-003")
            warnings.append("Excess non-concessional contributions: the ATO will issue a determination with a choice to release "
                            "the excess plus 85% of associated earnings, or leave it and pay excess non-concessional contributions "
                            "tax at the top marginal rate plus Medicare levy. The election is escalated (AU-SUPER-003).")
    out.update({"assumptions": assumptions, "warnings": warnings, "escalations": escalations})
    return out


# ================================================================ Division 293

class Div293Input(_Scope):
    taxable_income: float = Field(ge=0, description="Taxable income for the year (includes any excess concessional contributions; already net of salary sacrifice and personal super deductions).")
    reportable_fringe_benefits: float = Field(0, ge=0, description="Reportable fringe benefits total.")
    net_investment_loss: float = Field(0, ge=0, description="Total net investment loss (net financial investment loss plus net rental property loss).")
    concessional_contributions: float = Field(ge=0, description="Concessional contributions (low tax contributed amounts) for the year.")
    excess_concessional_contributions: float = Field(0, ge=0, description="Excess concessional contributions for the year (excluded from low tax contributions).")
    lump_sum_taxed_element_offset_amount: float = Field(0, ge=0, description="Amount under ITAA 1997 s301-20(3) (taxed element of a super lump sum within the low rate cap for a person aged 55-59), if any.")

    @model_validator(mode="after")
    def _ok(self):
        if self.excess_concessional_contributions > self.concessional_contributions:
            raise ValueError("excess_concessional_contributions cannot exceed concessional_contributions")
        return self


@calculator("div293_tax", Div293Input)
def div293_tax(figures: Figures, inp: Div293Input) -> dict:
    """Division 293 tax for one individual for one income year (2025-26 or 2026-27): income for
    Div 293 purposes (taxable income + reportable fringe benefits + total net investment loss, less any
    s301-20(3) amount, disregarding reportable super contributions) plus low tax contributions
    (concessional contributions less excess concessional contributions); if over the high income
    threshold, taxable contributions are the lesser of the low tax contributions and the excess, taxed
    at the Div 293 rate (ITAA 1997 ss293-20 to 293-30). Use for "extra 15% tax on super", "Div 293",
    "income over $250k super tax". Refuses AU-SUPER-001 for defined benefit interests."""
    _scope_check(inp)
    thr = figures.get("super.div293_threshold")
    rate = figures.get("super.div293_rate")
    income = max(0.0, inp.taxable_income + inp.reportable_fringe_benefits + inp.net_investment_loss
                 - inp.lump_sum_taxed_element_offset_amount)
    ltc = inp.concessional_contributions - inp.excess_concessional_contributions
    combined = income + ltc
    over = max(0.0, combined - thr)
    taxable = min(ltc, over) if ltc > 0 else 0.0
    tax = rate * taxable
    assumptions = ["Income for Div 293 purposes is income for surcharge purposes disregarding reportable super contributions "
                   "(ITAA 1997 s293-20(1)(a), s995-1); low tax contributions replace them (s293-25)."]
    warnings: list[str] = []
    if taxable:
        warnings.append("Div 293 tax is assessed separately by the ATO after fund reporting; it can be paid personally or "
                        "released from super using a release authority.")
    return {
        "income_for_div293": _r(income), "low_tax_contributions": _r(ltc), "combined": _r(combined),
        "threshold": thr, "excess_over_threshold": _r(over), "taxable_contributions": _r(taxable),
        "rate": rate, "div293_tax": _r(tax), "applies": taxable > 0,
        "assumptions": assumptions, "warnings": warnings, "escalations": [],
    }


# ================================================================ Division 296

class Div296Interest(BaseModel):
    fund: str = Field("", description="Fund name or label.")
    relevant_earnings: float = Field(description="Relevant super earnings for the interest as calculated and reported by the fund (may be negative).")
    excluded: bool = Field(False, description="Division 296 excluded interest (e.g. judges' pension scheme, certain constitutionally protected funds) or foreign fund: earnings taken as nil.")


class Div296Input(_Scope):
    tsb_end_of_year: float = Field(ge=0, description="Total super balance at the end of the income year (30 June), excluding LRBA amounts, all interests.")
    tsb_start_of_year: float | None = Field(None, ge=0, description="Total super balance just before the start of the year (prior 30 June). Ignored for 2026-27 (transitional); required from 2027-28.")
    total_super_earnings: float | None = Field(None, description="Total of relevant super earnings reported by all funds for the year. Use this or interests.")
    interests: list[Div296Interest] | None = Field(None, description="Per-interest relevant earnings reported by each fund.")
    died_in_year: bool = Field(False, description="Member died during the income year.")
    child_recipient_income_stream: bool = Field(False, description="Member was a child recipient of a super income stream at any time in the year (ITAA 1997 s296-20).")
    structured_settlement_contribution: bool = Field(False, description="A structured settlement contribution has ever been made for the member (s296-25).")
    earnings_estimate_from_balances: bool = Field(False, description="True if the only earnings information is a change in balance (opening/closing, contributions, withdrawals). Refused: Div 296 earnings are fund-calculated (AU-SUPER-005).")
    valuation_dispute: bool = Field(False, description="The member disputes a reported TSB value or fund earnings (AU-SUPER-005).")

    @model_validator(mode="after")
    def _one_source(self):
        if self.total_super_earnings is not None and self.interests is not None:
            raise ValueError("give total_super_earnings or interests, not both")
        return self


def _pct(tsb: float, threshold: float) -> Decimal:
    """(TSB - threshold) / TSB as a percentage, rounded to 2 dp half up (ss296-40(3), 296-45(3))."""
    if tsb <= threshold:
        return Decimal(0)
    return (Decimal(str(tsb - threshold)) / Decimal(str(tsb)) * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@calculator("div296_tax", Div296Input)
def div296_tax(figures: Figures, inp: Div296Input) -> dict:
    """Division 296 tax on earnings for large super balances (ITAA 1997 Div 296, Act No. 8 of 2026;
    rates in the Imposition Act No. 9 of 2026 s5), date-effective from 2026-27. Total super earnings
    are the relevant earnings each fund calculates and reports (realised, taxable-income based), NOT
    the change in balance. TSB reference amount: 2026-27 = TSB at 30 June 2027 only (transitional);
    later years = greater of opening and closing TSB. Percentage over the large and very large balance
    thresholds (rounded to 2 dp) times total earnings gives taxable super earnings (taxed at the lower
    Div 296 rate) and the very large balance earnings component (additional rate). For 2025-26 or
    earlier returns nil (not yet in force). Use for "$3 million super tax", "Div 296", "tax on super
    over $3m/$10m". Refuses AU-SUPER-005 when earnings would have to be estimated from balances or a
    valuation is disputed, AU-SUPER-001 for defined benefit interests."""
    _scope_check(inp)
    year = figures.income_year
    cur = _start(year)
    assumptions: list[str] = []
    warnings: list[str] = []
    if cur < 2026:
        return {"applies": False, "div296_tax": 0.0,
                "reason": "Division 296 first applies to the 2026-27 income year (Act No. 8 of 2026).",
                "assumptions": assumptions, "warnings": warnings, "escalations": []}
    if inp.valuation_dispute:
        raise Refusal("AU-SUPER-005", "disputed total super balance value or fund-reported earnings")
    if inp.total_super_earnings is None and inp.interests is None:
        if inp.earnings_estimate_from_balances:
            raise Refusal("AU-SUPER-005", "earnings would have to be estimated from balance movements")
        raise Refusal("AU-SUPER-008", "give total_super_earnings or interests (fund-reported relevant super earnings)")

    lsbt = figures.get("super.div296_large_balance_threshold")
    vlsbt = figures.get("super.div296_very_large_balance_threshold")
    r1 = figures.get("super.div296_rate_over_lsbt")
    r2 = figures.get("super.div296_additional_rate_over_vlsbt")

    if inp.interests is not None:
        earnings = sum(0.0 if i.excluded else i.relevant_earnings for i in inp.interests)
        if any(i.excluded for i in inp.interests):
            assumptions.append("Earnings of excluded interests are taken as nil, but their value still counts in the TSB (s296-55(2)-(3)).")
    else:
        earnings = inp.total_super_earnings or 0.0

    base = {"lsbt": lsbt, "vlsbt": vlsbt, "total_super_earnings": _r(earnings)}
    if inp.child_recipient_income_stream or inp.structured_settlement_contribution:
        why = "child recipient of a super income stream (s296-20)" if inp.child_recipient_income_stream \
            else "structured settlement contribution (s296-25)"
        return {**base, "applies": False, "div296_tax": 0.0, "reason": f"Exempt: {why}.",
                "assumptions": assumptions, "warnings": warnings, "escalations": []}
    if cur == 2026:
        if inp.died_in_year:
            return {**base, "applies": False, "div296_tax": 0.0,
                    "reason": "Transitional rule: a member who dies in 2026-27 is not liable for Division 296 tax for that year.",
                    "assumptions": assumptions, "warnings": warnings, "escalations": []}
        ref = inp.tsb_end_of_year
        assumptions.append("2026-27 transitional rule: only the TSB at 30 June 2027 is tested and used as the reference amount.")
    else:
        if inp.tsb_start_of_year is None:
            raise Refusal("AU-SUPER-008", "tsb_start_of_year is required from 2027-28")
        end = 0.0 if inp.died_in_year else inp.tsb_end_of_year  # s296-50: TSB nil after death
        ref = max(inp.tsb_start_of_year, end)
        assumptions.append("Reference amount is the greater of the TSB just before the start of the year and at the end (s296-40(2)).")
    assumptions.append("TSB for Division 296 excludes limited recourse borrowing arrangement amounts.")

    p1 = _pct(ref, lsbt)
    p2 = _pct(ref, vlsbt)
    out = {**base, "tsb_reference_amount": _r(ref), "pct_over_lsbt": float(p1), "pct_over_vlsbt": float(p2)}
    if ref <= lsbt or earnings <= 0:
        reason = "TSB reference amount not above the large balance threshold" if ref <= lsbt else \
            "total super earnings are nil or negative, so there are no taxable super earnings (s296-40(1)(b))"
        out.update({"applies": False, "taxable_super_earnings": 0.0, "very_large_balance_earnings_component": 0.0,
                    "div296_tax": 0.0, "reason": reason})
    else:
        tse = earnings * float(p1) / 100
        vlc = earnings * float(p2) / 100 if ref > vlsbt else 0.0
        t1, t2 = r1 * tse, r2 * vlc
        out.update({"applies": True, "taxable_super_earnings": _r(tse), "very_large_balance_earnings_component": _r(vlc),
                    "tax_on_taxable_super_earnings": _r(t1), "additional_tax_on_vlsb_component": _r(t2),
                    "div296_tax": _r(t1 + t2)})
        warnings.append("Division 296 tax is assessed on the individual after funds report; it cannot be deducted "
                        "(ITAA 1997 s26-99A) and may be paid personally or deferred/released from super.")
    out.update({"assumptions": assumptions, "warnings": warnings, "escalations": []})
    return out


# ================================================================ co-contribution and LISTO

class CoContributionInput(BaseModel):
    personal_nonconcessional_contributions: float = Field(ge=0, description="Eligible personal contributions not claimed as a deduction, received by the fund in the year.")
    assessable_income: float = Field(ge=0, description="Assessable income (excluding any assessable FHSS released amount).")
    reportable_fringe_benefits: float = Field(0, ge=0, description="Reportable fringe benefits total.")
    reportable_employer_super_contributions: float = Field(0, ge=0, description="Reportable employer super contributions (salary sacrifice etc.).")
    excess_concessional_contributions: float = Field(0, ge=0, description="Excess concessional contributions included in assessable income (reduces RESC for the income test).")
    business_deductions: float = Field(0, ge=0, description="Deductions from carrying on a business (reduce total income, but not for the 10% test).")
    eligible_income: float = Field(ge=0, description="Income from employment (SG-type activities) and carrying on a business, for the 10% test.")
    age_at_end_of_year: int = Field(ge=0, le=120, description="Age at 30 June of the income year.")
    temporary_visa_holder: bool = Field(False, description="Held a temporary visa at any time in the year (NZ citizens and prescribed visas excepted).")
    tsb_prior_30_june: float = Field(ge=0, description="Total super balance at 30 June before the year.")
    exceeded_ncc_cap: bool = Field(False, description="Non-concessional contributions for the year exceed the non-concessional cap.")
    lodges_return: bool = Field(True, description="An income tax return for the year is (or will be) lodged.")


def _round_up_5c(x: float) -> float:
    return math.ceil(round(x * 20, 6)) / 20


@calculator("co_contribution", CoContributionInput)
def co_contribution(figures: Figures, inp: CoContributionInput) -> dict:
    """Government super co-contribution for one income year (2025-26 or 2026-27), per the
    Superannuation (Government Co-contribution for Low Income Earners) Act 2003: eligibility tests
    (s6: total income below the higher threshold, 10% eligible income test, under 71 at year end, no
    temporary visa, TSB below the general transfer balance cap at the prior 30 June, NCC cap not
    exceeded, return lodged), then 50% of eligible personal contributions, capped at the maximum less
    3.333 cents per dollar of total income above the lower threshold, minimum $20, rounded up to 5
    cents. Use for "government co-contribution", "if I put $1,000 in after tax will the government
    add $500"."""
    lower = figures.get("super.co_contribution_lower_threshold")
    higher = figures.get("super.co_contribution_higher_threshold")
    mx = figures.get("super.co_contribution_max")
    match = figures.get("super.co_contribution_match_rate")
    taper = figures.get("super.co_contribution_taper_per_dollar")
    minimum = figures.get("super.co_contribution_minimum")
    ratio = figures.get("super.co_contribution_eligible_income_ratio")
    age_limit = figures.get("super.co_contribution_age_limit")
    tbc = figures.get("super.transfer_balance_cap")

    resc = max(0.0, inp.reportable_employer_super_contributions - inp.excess_concessional_contributions)
    gross = inp.assessable_income + inp.reportable_fringe_benefits + resc
    total = gross - inp.business_deductions
    fails: list[str] = []
    if inp.personal_nonconcessional_contributions <= 0:
        fails.append("no eligible personal contributions (s6(1)(a))")
    if gross <= 0 or inp.eligible_income < ratio * gross:
        fails.append("less than 10% of total income from employment or business (s6(1)(b))")
    if total >= higher:
        fails.append("total income not below the higher income threshold (s6(1)(c))")
    if not inp.lodges_return:
        fails.append("no income tax return lodged (s6(1)(d))")
    if inp.exceeded_ncc_cap:
        fails.append("non-concessional contributions exceed the cap (s6(1)(da))")
    if inp.tsb_prior_30_june >= tbc:
        fails.append("total super balance at the prior 30 June not below the general transfer balance cap (s6(1)(db))")
    if inp.age_at_end_of_year >= age_limit:
        fails.append("not under 71 at the end of the income year (s6(1)(e))")
    if inp.temporary_visa_holder:
        fails.append("held a temporary visa during the year (s6(1)(f))")
    out: dict = {"total_income": _r(total), "lower_threshold": lower, "higher_threshold": higher, "eligible": not fails}
    if fails:
        out.update({"co_contribution": 0.0, "reasons_not_eligible": fails})
    else:
        cap = mx if total <= lower else max(0.0, mx - taper * (total - lower))
        amount = min(match * inp.personal_nonconcessional_contributions, cap)
        amount = max(amount, minimum)
        out.update({"maximum_after_taper": _r(cap), "matched_amount": _r(match * inp.personal_nonconcessional_contributions),
                    "co_contribution": _round_up_5c(amount),
                    "contribution_needed_for_maximum": _r(cap / match)})
    out.update({"assumptions": ["Paid by the ATO to the fund after the return is lodged; not taxable and preserved."],
                "warnings": [], "escalations": []})
    return out


class ListoInput(BaseModel):
    adjusted_taxable_income: float = Field(ge=0, description="Adjusted taxable income (taxable income + RFB + total net investment loss + tax-free pensions + reportable super contributions + target foreign income - child support paid).")
    concessional_contributions: float = Field(ge=0, description="Concessional contributions for the year (employer, salary sacrifice, deductible personal).")
    total_income: float = Field(ge=0, description="Total income for the 10% test (assessable income + RFB + RESC, no business deductions).")
    eligible_income: float = Field(ge=0, description="Income from employment and carrying on a business.")
    temporary_visa_holder: bool = Field(False, description="Held a temporary visa at any time in the year (NZ citizens and prescribed visas excepted).")


@calculator("low_income_super_tax_offset", ListoInput)
def low_income_super_tax_offset(figures: Figures, inp: ListoInput) -> dict:
    """Low income super tax offset (LISTO) for one income year (2025-26 or 2026-27), per the
    Co-contribution Act ss12C and 12E: eligible if adjusted taxable income does not exceed the LISTO
    income limit, at least 10% of total income is from employment or business, and no temporary visa;
    amount is 15% of concessional contributions, capped at the LISTO maximum, minimum $10. Paid to the
    fund. The higher threshold and maximum legislated in Act No. 8 of 2026 Sch 4 start 1 Jul 2027 and do
    not apply to these years. Use for "LISTO", "low income super tax offset", "tax refund into super"."""
    limit = figures.get("super.listo_ati_limit")
    mx = figures.get("super.listo_max")
    rate = figures.get("super.listo_rate")
    minimum = figures.get("super.listo_minimum")
    ratio = figures.get("super.co_contribution_eligible_income_ratio")
    fails = []
    if inp.concessional_contributions <= 0:
        fails.append("no concessional contributions")
    if inp.adjusted_taxable_income > limit:
        fails.append("adjusted taxable income above the LISTO limit (s12C(1)(b))")
    if inp.total_income <= 0 or inp.eligible_income < ratio * inp.total_income:
        fails.append("less than 10% of total income from employment or business (s12C(1)(c))")
    if inp.temporary_visa_holder:
        fails.append("held a temporary visa during the year (s12C(1)(d))")
    out: dict = {"ati_limit": limit, "eligible": not fails}
    if fails:
        out.update({"listo": 0.0, "reasons_not_eligible": fails})
    else:
        raw = rate * inp.concessional_contributions
        out.update({"fifteen_percent_of_contributions": _r(raw), "listo": _r(min(mx, max(minimum, raw)))})
    out.update({"assumptions": ["LISTO is paid by the ATO into the fund, not to the person."], "warnings": [], "escalations": []})
    return out


# ================================================================ spouse contribution offset

class SpouseOffsetInput(BaseModel):
    contributions_for_spouse: float = Field(ge=0, description="Non-concessional contributions you made to your spouse's fund in the year.")
    spouse_assessable_income: float = Field(ge=0, description="Spouse's assessable income (excluding assessable FHSS released amount).")
    spouse_reportable_fringe_benefits: float = Field(0, ge=0, description="Spouse's reportable fringe benefits total.")
    spouse_reportable_employer_super: float = Field(0, ge=0, description="Spouse's reportable employer super contributions.")
    spouse_excess_concessional: float = Field(0, ge=0, description="Spouse's excess concessional contributions for the year (reduces RESC).")
    both_australian_residents: bool = Field(True, description="Both you and your spouse were Australian residents when the contribution was made.")
    living_apart_permanently: bool = Field(False, description="Living separately and apart on a permanent basis when contributing.")
    spouse_tsb_prior_30_june: float = Field(ge=0, description="Spouse's total super balance at 30 June before the year.")
    spouse_exceeded_ncc_cap: bool = Field(False, description="Spouse's non-concessional contributions exceed their cap for the year.")
    contributions_deductible_as_employer: bool = Field(False, description="You can deduct the contribution as an employer contribution (s290-60): no offset.")


@calculator("spouse_offset", SpouseOffsetInput)
def spouse_offset(figures: Figures, inp: SpouseOffsetInput) -> dict:
    """Spouse super contribution tax offset for one income year (2025-26 or 2026-27), ITAA 1997
    ss290-230 and 290-235: spouse income (assessable income + reportable fringe benefits + reportable
    employer super, less spouse's excess concessional contributions) must be below the cut-out; offset
    = 18% of the lesser of (the maximum contribution base reduced dollar for dollar by spouse income
    above the reduction threshold) and the contributions made, capped at the maximum offset. Denied if
    spouse's TSB at the prior 30 June is at or above the general transfer balance cap, spouse exceeded
    the NCC cap, either is non-resident, or living apart permanently. Use for "spouse contribution tax
    offset", "super for my partner"."""
    rate = figures.get("super.spouse_offset_rate")
    base_amt = figures.get("super.spouse_offset_max_contributions")
    thr = figures.get("super.spouse_offset_income_threshold")
    cut = figures.get("super.spouse_offset_income_cutout")
    mx = figures.get("super.spouse_offset_max")
    tbc = figures.get("super.transfer_balance_cap")
    income = (inp.spouse_assessable_income + inp.spouse_reportable_fringe_benefits
              + max(0.0, inp.spouse_reportable_employer_super - inp.spouse_excess_concessional))
    fails = []
    if inp.contributions_for_spouse <= 0:
        fails.append("no contributions made for the spouse")
    if income >= cut:
        fails.append("spouse income not below the cut-out (s290-230(2)(c))")
    if not inp.both_australian_residents:
        fails.append("both spouses must be Australian residents (s290-230(2)(b))")
    if inp.living_apart_permanently:
        fails.append("living separately and apart on a permanent basis (s290-230(3))")
    if inp.spouse_exceeded_ncc_cap:
        fails.append("spouse exceeded the non-concessional cap (s290-230(4A)(a))")
    if inp.spouse_tsb_prior_30_june >= tbc:
        fails.append("spouse TSB at the prior 30 June at or above the general transfer balance cap (s290-230(4A)(b))")
    if inp.contributions_deductible_as_employer:
        fails.append("contribution deductible as an employer contribution (s290-230(2)(d))")
    out: dict = {"spouse_income": _r(income), "eligible": not fails}
    if fails:
        out.update({"spouse_offset": 0.0, "reasons_not_eligible": fails})
    else:
        reduced = max(0.0, base_amt - max(0.0, income - thr))
        amount = min(mx, rate * min(reduced, inp.contributions_for_spouse))
        out.update({"reduced_contribution_base": _r(reduced), "spouse_offset": _r(amount),
                    "contribution_needed_for_this_maximum": _r(reduced)})
    out.update({"assumptions": ["The offset is non-refundable. Contributions count as the spouse's non-concessional contributions."],
                "warnings": [], "escalations": []})
    return out


# ================================================================ downsizer

class DownsizerInput(BaseModel):
    age_at_contribution: int = Field(ge=0, le=120, description="Age when the contribution is made.")
    ownership_years: float = Field(ge=0, description="Years the dwelling (or land) was held by you, your spouse or former spouse, ending just before disposal.")
    days_after_settlement: int = Field(ge=0, description="Days from change of ownership (usually settlement) to the contribution.")
    capital_proceeds: float = Field(ge=0, description="Capital proceeds from the sale (your interest plus any related spousal interest in the same contract).")
    other_downsizer_from_this_sale: float = Field(0, ge=0, description="Downsizer contributions already made from this sale for you or your spouse.")
    previous_downsizer_contributions: float = Field(0, ge=0, description="Your earlier downsizer contributions (any sale).")
    main_residence_exemption_available: bool = Field(True, description="Gain would be wholly or partly disregarded under the main residence exemption (Subdiv 118-B).")
    dwelling_in_australia_not_mobile: bool = Field(True, description="Dwelling in Australia and not a caravan, houseboat or other mobile home.")
    earlier_downsizer_from_other_dwelling: bool = Field(False, description="You already made a downsizer contribution from the sale of a different home (only one sale per person).")
    planned_contribution: float | None = Field(None, ge=0, description="Amount you plan to contribute as a downsizer contribution.")
    commissioner_extension: bool = Field(False, description="ATO allowed a longer period than 90 days.")


@calculator("downsizer_contribution", DownsizerInput)
def downsizer_contribution(figures: Figures, inp: DownsizerInput) -> dict:
    """Downsizer contribution eligibility and limit (ITAA 1997 s292-102) for 2025-26 or 2026-27:
    age at least the downsizer minimum age, 10-year ownership, main residence exemption at least
    partly available, dwelling in Australia, contribution within 90 days of change of ownership (or an
    ATO extension), one sale per person; limit is the lesser of the per-person downsizer cap (less
    earlier downsizer contributions) and the capital proceeds (less other downsizer contributions from
    the same sale). Downsizer contributions do not count towards the contribution caps and are not
    blocked by total super balance, but they do raise the TSB. Use for "downsizer contribution", "sold
    my home, put money into super"."""
    cap = figures.get("super.downsizer_cap")
    min_age = figures.get("super.downsizer_min_age")
    yrs = figures.get("super.downsizer_ownership_years")
    days = figures.get("super.downsizer_contribution_days")
    fails = []
    if inp.age_at_contribution < min_age:
        fails.append("under the minimum age when contributing (s292-102(1)(a))")
    if inp.ownership_years < yrs:
        fails.append("10-year ownership condition not met (s292-102(2))")
    if not inp.main_residence_exemption_available:
        fails.append("main residence exemption not available even in part (s292-102(1)(d))")
    if not inp.dwelling_in_australia_not_mobile:
        fails.append("dwelling outside Australia or a mobile home (s292-102(1)(f))")
    if inp.days_after_settlement > days and not inp.commissioner_extension:
        fails.append("contribution more than 90 days after change of ownership without an ATO extension (s292-102(1)(g))")
    if inp.earlier_downsizer_from_other_dwelling:
        fails.append("already made a downsizer contribution from another dwelling's sale (s292-102(1)(i))")
    limit = max(0.0, min(cap - inp.previous_downsizer_contributions,
                         inp.capital_proceeds - inp.other_downsizer_from_this_sale))
    out: dict = {"eligible": not fails, "per_person_cap": cap, "maximum_downsizer_contribution": _r(limit) if not fails else 0.0}
    if fails:
        out["reasons_not_eligible"] = fails
    if inp.planned_contribution is not None:
        allowed = min(inp.planned_contribution, out["maximum_downsizer_contribution"])
        out["planned_contribution"] = _r(inp.planned_contribution)
        out["covered_as_downsizer"] = _r(allowed)
        out["not_covered_counts_as_non_concessional"] = _r(inp.planned_contribution - allowed)
    out.update({"assumptions": ["The downsizer election form must be given to the fund at or before the time of contribution.",
                                "Downsizer contributions are not deductible and count towards total super balance afterwards."],
                "warnings": [], "escalations": []})
    return out
