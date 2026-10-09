"""Router: lodgment and obligations calendar for one entity and one income year.

Builds a dated list of lodge-and-pay obligations from facts about the entity (type, registrations, employer
status, state) by reusing the due-date logic and verified figures already owned by the domain calculators:
BAS and activity statements (gst.bas_* figures and `bas_due_date`), the FBT return (fbt.return_due_date*),
SA payroll tax (state.sa.payroll_tax_* figures), Payday Super (super.payday_super_* figures) and the
payg-instalments-lodgment tool `lodgment_due_dates` (lodgment.* figures: self-lodged individual return, PAYG
instalment quarters, TPAR, STP finalisation). It never invents a date: an obligation whose date is not in the
rates files (agent lodgment program, company and trust returns) is listed under `not_computed` with the skill
that owns it. A figure that is not VERIFIED is skipped (listed under `unverified`) unless allow_draft.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from au_tax.calculators.gst import DueDateInput, bas_due_date
from au_tax.calculators.payg_lodgment import DueDatesInput, lodgment_due_dates
from au_tax.calculators.state_sa import sa_monthly_return_due, sa_reconciliation_due
from au_tax.figures import FigureError, Figures
from au_tax.holidays import COMMONWEALTH, roll_due_date
from au_tax.registry import Refusal, calculator, refusal_catalogue

EntityType = Literal["individual", "sole_trader", "partnership", "company", "trust"]

ASIC_ANNUAL_REVIEW = "https://asic.gov.au/for-business/payments-fees-and-invoices/asic-fees/fees-for-commonly-lodged-documents/annual-review"


def _keys_for(obligation: str, quarter: int | None) -> list[str]:
    """Figure keys lodgment_due_dates reads for an obligation (lodgment.* overlay, payg-instalments-lodgment)."""
    if obligation == "payg_instalment_quarter":
        return ["lodgment.quarterly_due_day", f"lodgment.quarterly_due_month_q{quarter}"]
    if obligation == "individual_return_self_lodged":
        return ["lodgment.individual_return_due_month", "lodgment.individual_return_due_day"]
    if obligation == "tpar":
        return ["lodgment.tpar_due_month", "lodgment.tpar_due_day"]
    return ["lodgment.stp_finalisation_due_month", "lodgment.stp_finalisation_due_day"]


class ObligationsInput(BaseModel):
    """Facts about one entity for one income year. Leave a registration false if the entity is not registered."""

    entity_type: EntityType = Field(description="individual (no business), sole_trader, partnership, company or trust.")
    gst_registered: bool = False
    gst_cycle: Literal["quarterly", "monthly", "annual"] = Field(
        "quarterly", description="GST reporting cycle when registered. Annual only for voluntary registrants below the threshold.")
    gst_turnover: float | None = Field(None, ge=0, description="GST turnover; at or above the monthly threshold means monthly BAS and no online concession.")
    lodgment: Literal["online_self", "registered_agent", "paper"] = Field(
        "online_self", description="How activity statements and the FBT return are lodged.")
    payg_withholding_registered: bool = Field(False, description="Registered for PAYG withholding (employer, or withholding from suppliers).")
    has_employees: bool = False
    provides_fringe_benefits: bool = Field(False, description="Provides fringe benefits so an FBT return is required for the FBT year.")
    sa_payroll_tax_registered: bool = Field(False, description="Registered for payroll tax with RevenueSA.")
    sa_payroll_tax_cycle: Literal["monthly"] = Field("monthly", description="Only monthly SA returns are modelled.")
    payg_instalments: bool = Field(False, description="Entered in the PAYG instalment system.")
    lodges_income_tax_return: bool = True
    tpar_industry: bool = Field(False, description="Business in a TPAR industry (building, cleaning, courier, road freight, IT, security, etc.).")
    gst_registered_from: date | None = Field(None, description="GST registration start date if it began during the year: earlier periods are left out.")
    employing_from: date | None = Field(None, description="Date of the first wage payment if it falls during the year: PAYG withholding periods ending earlier are left out.")
    employment_start: date | None = Field(None, description="Date the first SA worker starts work (ReturnToWorkSA registration runs from this date). Defaults to employing_from if not given.")
    company_registration_date: date | None = Field(None, description="Company only: ASIC registration date, for the annual review date.")
    employs_in_sa: bool = Field(False, description="Has workers who usually work in or are based in South Australia (ReturnToWorkSA registration).")
    expected_annual_wages: float | None = Field(None, ge=0, description="Total remuneration expected to be paid to workers for the financial year.")
    other_states: list[str] = Field(default_factory=list, description="Other states or territories with payroll tax or land tax registration (not modelled).")

    @model_validator(mode="after")
    def _consistent(self):
        if self.entity_type == "individual" and self.gst_registered:
            raise ValueError("an individual with GST registration carries on an enterprise: use entity_type sole_trader")
        return self


def _roll(figures: Figures, d: date, warnings: list[str]) -> tuple[date, dict]:
    """Commonwealth business-day roll (TAA 1953 s 8AAZMB, Sch 1 s 388-52) with holiday data; returns the date and the roll block."""
    r = roll_due_date(d, COMMONWEALTH, figures)
    warnings.extend(w for w in r.warnings if w not in warnings)
    return r.due, r.as_dict()


def _ymd(n: int) -> date:
    n = int(n)
    return date(n // 10000, (n // 100) % 100, n % 100)


def _item(obligation: str, period: str, original: date | None, due: date | None, rule: str, keys: list[str],
          skill: str, figures: Figures, roll: dict | None = None) -> dict:
    sources = sorted({figures.used[k].source for k in keys if k in figures.used} | ({roll["rule_source"]} if roll else set()))
    item = {
        "obligation": obligation,
        "period": period,
        "original_due_date": original.isoformat() if original else None,
        "due_date": due.isoformat() if due else None,
        "due_date_weekday": due.strftime("%A") if due else None,
        "rule": rule,
        "figure_keys": keys,
        "sources": sources,
        "owner_skill": skill,
    }
    if roll:
        item["business_day_roll"] = roll
    return item


@calculator("obligations_calendar", ObligationsInput)
def obligations_calendar(figures: Figures, inp: ObligationsInput) -> dict:
    """Lodgment and payment calendar for one entity for one income year, sorted by date: BAS or activity
    statements (quarterly with the online or registered agent concession, monthly with the December concession,
    or the annual GST return), PAYG withholding reported on the activity statement, the FBT return for the FBT
    year ending in the income year, SA payroll tax monthly returns and annual reconciliation, and the Payday Super
    contribution window (2026-27 on), STP finalisation, TPAR, PAYG instalment quarters, the self-lodged individual
    return and payment date, and the ASIC annual review date (from company_registration_date). Each item carries its
    rule, figure keys and primary sources. Dates not in the verified rates files (agent lodgment program, company and
    trust returns) are listed in not_computed with the skill that owns them; never fill those in from memory. Use in the
    router skill for "what do I need to lodge", "year-end calendar", "what's due this year" for a client."""
    start, end = figures.data["meta"]["start"], figures.data["meta"]["end"]
    y0, y1 = start.year, start.year + 1
    items: list[dict] = []
    rules: list[dict] = []
    unverified: list[dict] = []
    not_computed: list[dict] = []
    assumptions: list[str] = []
    warnings: list[str] = []
    assumptions.append("A due date that is not a business day moves to the first business day after. ATO-administered dates use the "
                       "Commonwealth rule (TAA 1953 s 8AAZMB, Sch 1 s 388-52): not a Saturday, Sunday or a public holiday for the whole of "
                       "any State, the ACT or the NT. SA state tax dates use SA public holidays only (Public Holidays Act 2023 (SA)). "
                       "Holiday data: data/holidays/au.yaml.")

    def skip(obligation: str, err: FigureError | Refusal, skill: str):
        """List one obligation that cannot be dated, with the refusal code, instead of refusing the whole calendar. AU-GEN-004 (a
        due date after the public holiday data) carries the statutory date before any roll: it is shown for reference only and
        is not a checked due date."""
        if isinstance(err, Refusal):
            if err.code != "AU-GEN-004":
                raise err
            row = {"obligation": obligation, "reason": f"{refusal_catalogue()[err.code]['message']} ({err.detail})",
                   "refusal_code": err.code, "owner_skill": skill}
            sd = getattr(err, "statutory_date", None)
            if sd:
                row["statutory_due_date"] = sd.isoformat()
            unverified.append(row)
            return
        unverified.append({"obligation": obligation, "reason": str(err), "refusal_code": err.code, "owner_skill": skill})

    # ---- activity statements: GST, and PAYG withholding reported on the same statement
    reports_as = inp.gst_registered or inp.payg_withholding_registered
    if reports_as:
        what = []
        if inp.gst_registered:
            what.append("GST")
        if inp.payg_withholding_registered:
            what.append("PAYG withholding (W1, W2)")
        label = "BAS: " + " and ".join(what)

        def active(period_end: date, quarterly_w_only: bool = False) -> list[str]:
            out = []
            if inp.gst_registered and not quarterly_w_only and (inp.gst_registered_from is None or inp.gst_registered_from <= period_end):
                out.append("GST")
            if inp.payg_withholding_registered and (inp.employing_from is None or inp.employing_from <= period_end):
                out.append("PAYG withholding (W1, W2)")
            return out

        if inp.gst_registered_from and inp.gst_registered_from > start:
            assumptions.append(f"GST registration from {inp.gst_registered_from.isoformat()}: earlier GST periods are not listed; "
                               "the first BAS covers the period in which registration starts.")
        if inp.employing_from and inp.employing_from > start:
            assumptions.append(f"First wages {inp.employing_from.isoformat()}: PAYG withholding reporting starts in that period.")
        cycle = inp.gst_cycle if inp.gst_registered else "quarterly"
        if not inp.gst_registered:
            assumptions.append("PAYG withholding without GST: treated as a small withholder reporting quarterly on an "
                               "activity statement. Medium and large withholders report monthly or more often; confirm.")
        if inp.gst_registered and inp.gst_cycle == "annual" and inp.payg_withholding_registered:
            assumptions.append("Annual GST reporting: PAYG withholding is still reported on quarterly activity statements "
                               "(listed separately below).")
            cycle = "annual_plus_quarterly_w"
        if cycle in ("quarterly", "annual_plus_quarterly_w"):
            name = label if cycle == "quarterly" else "Activity statement: PAYG withholding (W1, W2)"
            qend = {1: date(y0, 9, 30), 2: date(y0, 12, 31), 3: date(y1, 3, 31), 4: date(y1, 6, 30)}
            for q in (1, 2, 3, 4):
                act = active(qend[q], quarterly_w_only=(cycle == "annual_plus_quarterly_w"))
                if not act:
                    continue
                if cycle == "quarterly":
                    name = "BAS: " + " and ".join(act)
                try:
                    r = bas_due_date(figures, DueDateInput(cycle="quarterly", quarter=q, lodgment=inp.lodgment,
                                                           gst_turnover=inp.gst_turnover))
                except (FigureError, Refusal) as e:
                    skip(f"{name} Q{q}", e, "gst-bas")
                    continue
                keys = ["gst.bas_quarterly_due_day"]
                if q != 2 and inp.lodgment == "online_self":
                    keys.append("gst.bas_online_concession_days")
                if q != 2 and inp.lodgment == "registered_agent":
                    keys.append(f"gst.bas_agent_q{q}_due_yyyymmdd")
                warnings.extend(w for w in r["warnings"] if w not in warnings)
                items.append(_item(f"{name} Q{q}", r["period"], date.fromisoformat(r["original_due_date"]),
                                   date.fromisoformat(r["due_date"]), " ".join(r["notes"]) or "Quarterly activity statement.",
                                   keys, "gst-bas", figures, r["business_day_roll"]))
        if cycle == "monthly":
            for m in (7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6):
                yr = y0 if m >= 7 else y1
                mend = (date(yr + (m == 12), m % 12 + 1, 1) - timedelta(days=1))
                act = active(mend)
                if not act:
                    continue
                label = "BAS: " + " and ".join(act)
                try:
                    r = bas_due_date(figures, DueDateInput(cycle="monthly", month=m, lodgment=inp.lodgment,
                                                           gst_turnover=inp.gst_turnover))
                except (FigureError, Refusal) as e:
                    skip(f"{label} month {m}", e, "gst-bas")
                    continue
                keys = ["gst.bas_monthly_due_day"]
                if r["due_date"][5:7] == "02" and m == 12:
                    keys.append("gst.bas_monthly_december_concession_day_february")
                warnings.extend(w for w in r["warnings"] if w not in warnings)
                items.append(_item(label, r["period"], date.fromisoformat(r["original_due_date"]),
                                   date.fromisoformat(r["due_date"]), " ".join(r["notes"]), keys, "gst-bas", figures,
                                   r["business_day_roll"]))
        if inp.gst_registered and inp.gst_cycle == "annual":
            try:
                day = int(figures.get("gst.bas_annual_gst_return_due_day_october"))
                orig = date(y1, 10, day)
                due_a, roll_a = _roll(figures, orig, warnings)
                items.append(_item("Annual GST return", f"{figures.income_year}", orig, due_a,
                                   "Annual GST return: 31 October after the year if an income tax return is required; "
                                   "28 February if no income tax return is required. Payment is due on the same date.",
                                   ["gst.bas_annual_gst_return_due_day_october"], "gst-bas", figures, roll_a))
            except (FigureError, Refusal) as e:
                skip("Annual GST return", e, "gst-bas")

    # ---- FBT return for the FBT year ending in this income year
    if inp.provides_fringe_benefits:
        fbt_end = figures.data["meta"].get("fbt_year_ending")
        key = "fbt.return_due_date_agent_electronic" if inp.lodgment == "registered_agent" else "fbt.return_due_date"
        try:
            orig = _ymd(figures.get(key))
            label = f"FBT{fbt_end.year}" if isinstance(fbt_end, date) else "FBT year"
            rule = ("FBT return lodge and pay: 21 May after the FBT year" if key == "fbt.return_due_date" else
                    "FBT return via a tax agent lodging electronically, if the employer was on the agent's FBT client list by 21 May")
            due_f, roll_f = _roll(figures, orig, warnings)
            items.append(_item("FBT return and payment", label, orig, due_f, rule, [key], "fbt", figures, roll_f))
        except (FigureError, Refusal) as e:
            skip("FBT return and payment", e, "fbt")

    # ---- SA payroll tax: monthly returns July to May, June in the annual reconciliation
    if inp.sa_payroll_tax_registered:
        try:
            figures.get("state.sa.payroll_tax_monthly_due_day")
            for m in (7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5):
                yr = y0 if m >= 7 else y1
                try:
                    r = sa_monthly_return_due(figures, yr, m)
                except Refusal as e:  # a month whose date is after the holiday data: listed, the other months still are
                    skip(f"SA payroll tax monthly return {date(yr, m, 1).strftime('%B %Y')}", e, "state-taxes-sa")
                    continue
                warnings.extend(w for w in r["warnings"] if w not in warnings)
                keys = ["state.sa.payroll_tax_monthly_due_day"]
                rule = "Due by the 7th of the month after the wages month, next business day if not one under SA public holidays (June wages go in the annual reconciliation)."
                if r["published_extension"]:
                    keys.append("state.sa.payroll_tax_december_return_due_yyyymmdd")
                    rule = "RevenueSA's published extension over the Christmas and New Year period replaces the ordinary 7th."
                items.append(_item("SA payroll tax monthly return and payment", date(yr, m, 1).strftime("%B %Y"),
                                   date.fromisoformat(r["ordinary_due_date"]), date.fromisoformat(r["due_date"]), rule,
                                   keys, "state-taxes-sa", figures, r["business_day_roll"]))
        except FigureError as e:
            skip("SA payroll tax monthly returns", e, "state-taxes-sa")
        try:
            rr = sa_reconciliation_due(figures, end)
            warnings.extend(w for w in rr["warnings"] if w not in warnings)
            items.append(_item("SA payroll tax annual reconciliation (includes June)", figures.income_year,
                               date.fromisoformat(rr["original_date"]), date.fromisoformat(rr["due_date"]),
                               "RevenueSA published reconciliation date; the Act's June payment date is earlier (see state-taxes-sa).",
                               ["state.sa.payroll_tax_annual_reconciliation_due_day_july"], "state-taxes-sa", figures,
                               rr["business_day_roll"]))
        except (FigureError, Refusal) as e:
            skip("SA payroll tax annual reconciliation", e, "state-taxes-sa")
    for st in inp.other_states:
        not_computed.append({"obligation": f"{st} state tax obligations", "why": "Only South Australia is modelled (AU-SA-001).",
                             "owner_skill": "state-taxes-sa"})

    # ---- ReturnToWorkSA registration (state work injury insurance; not a tax)
    if inp.has_employees and inp.employs_in_sa:
        try:
            days = int(figures.get("employer_sa.return_to_work_registration_days"))
            keys = ["employer_sa.return_to_work_registration_days"]
            required = None
            if inp.expected_annual_wages is not None:
                minimum = figures.get("employer_sa.return_to_work_registration_remuneration_min")
                keys.append("employer_sa.return_to_work_registration_remuneration_min")
                required = inp.expected_annual_wages >= minimum
            if required is False:
                rules.append({"obligation": "ReturnToWorkSA registration", "recurs": "once",
                              "rule": f"Not required: expected remuneration {inp.expected_annual_wages:.2f} is below the "
                                      f"registration minimum {minimum}. If a worker is injured, report, register and pay the minimum premium.",
                              "figure_keys": keys, "owner_skill": "router", "tool": None})
            elif inp.employment_start or inp.employing_from:
                start_emp = inp.employment_start or inp.employing_from
                if not inp.employment_start:
                    warnings.append("ReturnToWorkSA: employment start date not given; counted from the first wage payment. "
                                    "The 14 days run from when the worker starts, so the real deadline may be earlier.")
                due = start_emp + timedelta(days=days)
                items.append(_item("ReturnToWorkSA work injury insurance registration", "on employing", due, due,
                                   f"Register within {days} days of employing" + (" (expected remuneration is at or above the "
                                   "registration minimum)." if required else "; confirm expected remuneration against the minimum."),
                                   keys, "router", figures))
            else:
                rules.append({"obligation": "ReturnToWorkSA registration", "recurs": "once",
                              "rule": f"Register within {days} days of first employing a worker in SA (unless remuneration for the "
                                      "year will be below the registration minimum).", "figure_keys": keys, "owner_skill": "router", "tool": None})
        except FigureError as e:
            skip("ReturnToWorkSA registration", e, "router")

    # ---- super guarantee and STP (recurring, per pay run)
    if inp.has_employees:
        if start >= date(2026, 7, 1):
            try:
                n = figures.get("super.payday_super_usual_period_business_days")
                n_first = figures.get("super.payday_super_first_contribution_business_days")
                rules.append({"obligation": "Super guarantee (Payday Super)", "recurs": "each payday (QE day)",
                              "rule": f"Contribution must reach the fund within {n} business days after each QE day "
                                      f"({n_first} for a new employee's first contribution or a new fund).",
                              "figure_keys": ["super.payday_super_usual_period_business_days",
                                              "super.payday_super_first_contribution_business_days"],
                              "owner_skill": "payroll-sg", "tool": "super_guarantee"})
            except FigureError as e:
                skip("Super guarantee (Payday Super)", e, "payroll-sg")
        else:
            rules.append({"obligation": "Super guarantee (quarterly regime)", "recurs": "each quarter",
                          "rule": "Quarterly SG for quarters to 30 Jun 2026: get each quarter's due date from the super_guarantee tool.",
                          "figure_keys": [], "owner_skill": "payroll-sg", "tool": "super_guarantee"})
        rules.append({"obligation": "Single Touch Payroll pay event", "recurs": "each payday",
                      "rule": "Report salary, wages and super information to the ATO through STP on or before each payday.",
                      "figure_keys": [], "owner_skill": "payroll-sg", "tool": None})

    # ---- annual and instalment obligations from the payg-instalments-lodgment tool (lodgment.* figures)
    def lodg(name: str, obligation: str, skill: str, rule: str, quarter: int | None = None):
        try:
            r = lodgment_due_dates(figures, DueDatesInput(obligation=obligation, quarter=quarter))
        except (FigureError, Refusal) as e:
            skip(name, e, skill)
            return None
        period = f"Q{quarter} {figures.income_year}" if quarter else figures.income_year
        warnings.extend(w for w in r["warnings"] if w.startswith(("DRAFT", "The ATO's table")) and w not in warnings)
        items.append(_item(name, period, date.fromisoformat(r["statutory_due_date"]), date.fromisoformat(r["due_date"]),
                           rule + (" " + " ".join(r["warnings"]) if r["warnings"] else ""),
                           _keys_for(obligation, quarter), skill, figures, r["business_day_roll"]))
        return r

    if inp.has_employees:
        lodg("STP finalisation declaration", "stp_finalisation", "payroll-sg",
             "Finalise STP for every employee for the income year.")
    if inp.tpar_industry:
        lodg("Taxable payments annual report (TPAR)", "tpar", "bookkeeping-year-end",
             "Report payments to contractors in the listed industries for the income year.")
    if inp.payg_instalments:
        if inp.gst_registered and inp.gst_cycle == "quarterly":
            rules.append({"obligation": "PAYG instalments", "recurs": "each quarter",
                          "rule": "Instalments are reported and paid on the quarterly BAS (T labels): the BAS due dates above apply.",
                          "figure_keys": [], "owner_skill": "payg-instalments-lodgment", "tool": "payg_instalment"})
        else:
            for q in (1, 2, 3, 4):
                lodg(f"PAYG instalment notice Q{q}", "payg_instalment_quarter", "payg-instalments-lodgment",
                     "Quarterly instalment (notice or activity statement); no online concession for instalment notices.", q)
    if inp.lodges_income_tax_return:
        if inp.entity_type in ("individual", "sole_trader") and inp.lodgment != "registered_agent":
            r = lodg("Individual income tax return (self-lodged)", "individual_return_self_lodged", "payg-instalments-lodgment",
                     "Return for this income year, lodged by the taxpayer.")
            if r:
                rules.append({"obligation": "Individual income tax payment", "recurs": "once",
                              "rule": f"For a return lodged on time, any tax bill is due the later of {r['payment_due_if_lodged_by_due_date']} and "
                                      "21 days after the assessment issues. Lodging late does not extend the standard November payment date; verify the assessment and any ATO deferral.",
                              "figure_keys": ["lodgment.individual_payment_due_month", "lodgment.individual_payment_due_day"],
                              "owner_skill": "payg-instalments-lodgment", "tool": "lodgment_due_dates"})
        else:
            why = ("Return lodged through a registered tax agent: the date comes from the ATO agent lodgment program "
                   "(published per year and client), not computed here." if inp.lodgment == "registered_agent" else
                   f"{inp.entity_type.replace('_', ' ').title()} return: the due date depends on the entity's lodgment history, size "
                   "and agent lodgment program; not computed here.")
            not_computed.append({"obligation": "income_tax_return", "why": why, "owner_skill": "payg-instalments-lodgment"})
    if inp.entity_type == "company":
        if inp.company_registration_date:
            rd = inp.company_registration_date
            review = None
            for yr in (y0, y1):
                try:
                    cand = date(yr, rd.month, rd.day)
                except ValueError:  # 29 February registration
                    cand = date(yr, 3, 1)
                if start <= cand <= end and cand > rd:
                    review = cand
            if review:
                fee_keys = ["asic.annual_review_proprietary", "asic.annual_review_special_purpose_proprietary"]
                fees: dict[str, float] | None = None
                try:
                    fees = {"proprietary": figures.get(fee_keys[0]), "special_purpose_proprietary": figures.get(fee_keys[1])}
                except FigureError as e:  # fee unpublished for the year (2027-28 today) or not verified: date still given
                    fee_keys = []
                    skip("ASIC annual review fee", e, "company-div7a")
                item = _item("ASIC annual review date (annual statement issued; pay the review fee)",
                             figures.income_year, review, review,
                             "The review date is the anniversary of registration. The review fee for the company type is in "
                             "fee_aud when the rates file has it for this year; the annual statement states the amount payable, "
                             "including any late fee.", fee_keys, "company-div7a", figures)
                item["sources"] = sorted(set(item["sources"]) | {ASIC_ANNUAL_REVIEW})
                if fees is not None:
                    item["fee_aud"] = fees
                items.append(item)
        else:
            not_computed.append({"obligation": "asic_annual_review",
                                 "why": "ASIC annual review falls on the anniversary of registration; give company_registration_date.",
                                 "owner_skill": "company-div7a"})

    items.sort(key=lambda i: (i["due_date"] or "9999", i["obligation"]))
    return {
        "entity_type": inp.entity_type,
        "income_year_start": start.isoformat(),
        "income_year_end": end.isoformat(),
        "calendar": items,
        "recurring_rules": rules,
        "not_computed": not_computed,
        "unverified": unverified,
        "assumptions": assumptions + [
            "Dates are lodge-and-pay dates for obligations arising from this income year; some fall after 30 June.",
            "Registered agent dates apply only to eligible clients on the agent's client list and lodged electronically.",
        ],
        "warnings": warnings,
    }


# ====================================================================== taxable income assembly

SKILLS = Literal["user", "residency-cross-border", "bookkeeping-year-end", "gst-bas", "payroll-sg", "fbt", "state-taxes-sa",
                 "company-div7a", "trusts-partnerships", "sole-trader-business", "rental-property", "short-stay-accommodation", "crypto", "au-indonesia-cross-border", "cgt",
                 "super-contributions", "individual-tax", "payg-instalments-lodgment"]
INCOME_KINDS = ("salary_wages", "employment_other", "interest", "dividends_unfranked", "dividends_franked", "franking_credit",
                "business_net", "partnership_share", "trust_ordinary_share", "trust_franked_distribution",
                "trust_total_assessed", "rental_net", "net_capital_gain", "foreign_income", "deemed_dividend",
                "other_income")
DEDUCTION_KINDS = ("work_related_deduction", "personal_super_deduction", "gift_deduction", "tax_affairs_deduction",
                   "other_deduction")
RAW_CGT_KINDS = ("capital_gain_gross", "capital_loss")
ComponentKind = Literal[INCOME_KINDS + DEDUCTION_KINDS + RAW_CGT_KINDS]  # type: ignore[valid-type]
SIGNED_KINDS = ("business_net", "partnership_share", "trust_ordinary_share", "trust_total_assessed", "rental_net", "other_income")


class IncomeComponent(BaseModel):
    kind: ComponentKind = Field(description="Income kinds are added, deduction kinds (…_deduction) are subtracted. Business, "
                                "partnership, trust and rental results are signed (a loss is negative); all others are positive.")
    amount: float = Field(description="Amount exactly as the source skill's tool returned it (AUD).")
    source_skill: SKILLS = Field(description="Skill whose tool produced the amount, or 'user' for figures the user gave (salary, interest).")
    source_tool: str | None = Field(None, description="Tool that returned the amount, e.g. net_capital_gain, rental_property_result.")
    label: str = ""
    gst_inclusive: bool | None = Field(None, description="True if the amount still includes GST (not allowed for a GST-registered "
                                       "taxpayer: GST is not assessable income, ITAA 1997 s 17-5).")
    net_of_foreign_tax: bool = Field(False, description="foreign_income only: true if foreign tax was already deducted (not allowed; "
                                     "include the gross amount and claim the foreign income tax offset).")
    capital_gain_part: float = Field(0, ge=0, description="trust_total_assessed or partnership_share: the part that is a capital gain "
                                     "(trust tool attributable_capital_gain).")
    deferred_non_commercial_loss: bool = Field(False, description="business_net loss deferred under Div 35 (non_commercial_loss_test "
                                               "deferred_loss): excluded.")
    quarantined: bool = Field(False, description="rental_net amount quarantined (not deductible this year): excluded.")
    confirmed_distinct: bool = Field(False, description="Set true when two components of the same kind and amount are genuinely separate.")


class AssembleInput(BaseModel):
    """Components of ONE individual's taxable income for one income year, each with the skill that produced it."""

    components: list[IncomeComponent] = Field(min_length=1)
    gst_registered: bool | None = Field(None, description="Whether the taxpayer's business is registered for GST.")
    prior_year_tax_losses: float = Field(0, ge=0, description="Unapplied tax losses (revenue, not capital) from earlier years.")


@calculator("assemble_taxable_income", AssembleInput)
def assemble_taxable_income(figures: Figures, inp: AssembleInput) -> dict:
    """Adds up one individual's taxable income from the results of other skills so the router never does arithmetic in
    prose: income components (salary, interest, dividends and franking credits, business net result from
    sole-trader-business, partnership and trust shares from trusts-partnerships, net rental result from
    rental-property, net capital gain from cgt, foreign income from residency-cross-border, deemed dividends from
    company-div7a) less deductions (work-related, personal super deduction from super-contributions, other), then
    prior-year tax losses. Blocks (taxable_income null, consistent false) on double counting (same kind and amount
    twice, more than one net capital gain, a trust capital gain counted both in a trust share and in the cgt net capital
    gain), raw capital gains or losses not netted through cgt, GST-inclusive amounts, and foreign income net of foreign
    tax. Excludes deferred non-commercial losses and quarantined rental losses. Returns the build-up table to show in
    the working paper, and passes taxable_income to individual_income_tax. Individuals only."""
    blocking: list[str] = []
    warnings: list[str] = []
    assumptions: list[str] = []
    lines: list[dict] = []
    c = inp.components
    seen: dict[tuple, int] = {}
    for i, comp in enumerate(c):
        k = (comp.kind, round(comp.amount, 2))
        if comp.amount and k in seen and not (comp.confirmed_distinct and c[seen[k]].confirmed_distinct):
            blocking.append(f"Possible double count: components {seen[k] + 1} and {i + 1} are both {comp.kind} of "
                            f"{comp.amount:.2f}. If they are genuinely separate, set confirmed_distinct on both.")
        seen.setdefault(k, i)
    ncg = [x for x in c if x.kind == "net_capital_gain"]
    if len(ncg) > 1:
        blocking.append("More than one net_capital_gain: a taxpayer has one net capital gain per year. Put every gain and "
                        "loss (including trust capital gains) into one cgt net_capital_gain call.")
    for x in ncg:
        if x.source_skill != "cgt":
            blocking.append(f"net_capital_gain must come from the cgt skill (net_capital_gain tool), not {x.source_skill}.")
        if x.amount < 0:
            blocking.append("A net capital gain cannot be negative: a net capital loss is carried forward, not deducted.")
    for x in c:
        if x.kind in RAW_CGT_KINDS:
            blocking.append(f"'{x.label or x.kind}': capital gains and losses are not added directly. Run them through the cgt "
                            "net_capital_gain tool and pass only its net_capital_gain.")
        if x.kind == "trust_total_assessed" and x.capital_gain_part > 0:
            if ncg:
                blocking.append(f"'{x.label or 'trust share'}' includes a capital gain part and a cgt net capital gain is also "
                                "present: double count. Pass the trust share without the capital gain part (trust_ordinary_share "
                                "plus franked parts) and include the grossed-up trust gain inside the cgt calculation.")
            else:
                warnings.append(f"'{x.label or 'trust share'}' includes a capital gain part. That is only right if the beneficiary "
                                "has no other capital gains or losses; otherwise run the grossed-up gain through cgt.")
        if x.gst_inclusive:
            blocking.append(f"'{x.label or x.kind}' includes GST. Use GST-exclusive amounts (GST is not assessable income or a "
                            "deduction for a registered entity, ITAA 1997 ss 17-5 and 27-5).")
        elif inp.gst_registered and x.kind in ("business_net", "rental_net", "partnership_share") and x.gst_inclusive is None:
            warnings.append(f"'{x.label or x.kind}': GST-registered, confirm the amount is GST-exclusive.")
        if x.kind == "foreign_income" and x.net_of_foreign_tax:
            blocking.append(f"'{x.label or 'foreign income'}' is net of foreign tax. Include the gross amount in AUD and claim "
                            "the foreign income tax offset (residency-cross-border).")
        if x.kind in DEDUCTION_KINDS and x.amount < 0:
            blocking.append(f"'{x.label or x.kind}': give deductions as positive amounts.")
        if x.kind not in SIGNED_KINDS and x.kind in INCOME_KINDS and x.amount < 0:
            blocking.append(f"'{x.label or x.kind}' cannot be negative.")
    if any(x.kind in ("dividends_franked", "trust_franked_distribution") for x in c) and not any(x.kind == "franking_credit" for x in c):
        warnings.append("Franked dividends without a franking_credit component: the franking credit is assessable (s 207-20) "
                        "and gives a matching offset. Add it unless the dividend was unfranked.")
    if any(x.kind == "salary_wages" for x in c) and not any(x.kind in DEDUCTION_KINDS for x in c):
        assumptions.append("No deductions were given.")

    income = deductions = 0.0
    for i, x in enumerate(c, 1):
        included, reason = True, ""
        if x.kind in RAW_CGT_KINDS:
            included, reason = False, "raw capital amount: goes through cgt"
        elif x.kind == "business_net" and x.amount < 0 and x.deferred_non_commercial_loss:
            included, reason = False, "non-commercial loss deferred (Div 35)"
        elif x.kind == "rental_net" and x.quarantined:
            included, reason = False, "rental loss quarantined, carried forward"
        sign = -1 if x.kind in DEDUCTION_KINDS else 1
        if included:
            if sign > 0:
                income += x.amount
            else:
                deductions += x.amount
        lines.append({"line": i, "kind": x.kind, "label": x.label, "amount": round(x.amount, 2),
                      "effect": ("subtract" if sign < 0 else "add") if included else "excluded",
                      "excluded_reason": reason or None, "source_skill": x.source_skill, "source_tool": x.source_tool})
    before_losses = income - deductions
    applied = min(inp.prior_year_tax_losses, max(0.0, before_losses))
    after = before_losses - applied
    if inp.prior_year_tax_losses:
        assumptions.append("Prior-year tax losses applied after deductions; net exempt income (which reduces losses first, "
                           "s 36-17) is taken as nil.")
    rental_losses = sum(-x.amount for x in c if x.kind == "rental_net" and x.amount < 0 and not x.quarantined)
    consistent = not blocking
    limitations = []
    if inp.prior_year_tax_losses:
        limitations.append({"id": "net_exempt_income_assumed_nil", "kind": "assumption",
                            "message": "Net exempt income reducing prior-year revenue losses is assumed nil (s 36-17).",
                            "affects": ["taxable_income", "tax_loss_carried_forward", "handoffs"]})
    # Each existing assembly warning identifies unresolved facts affecting the build-up.
    for index, message in enumerate(warnings, 1):
        limitations.append({"id": f"assembly_warning_{index}", "kind": "assumption",
                            "message": message, "affects": ["taxable_income", "handoffs"]})
    for index, message in enumerate(blocking, 1):
        limitations.append({"id": f"assembly_block_{index}", "kind": "exclusion",
                            "message": message, "affects": ["taxable_income", "handoffs"]})
    return {
        "limitations": limitations,
        "total_complete": consistent and not limitations,
        "total_status": "incomplete" if not consistent else "conditional" if limitations else "complete",
        "completeness_scope": "Supplied taxable-income components only; downstream totals inherit these limitations.",
        "consistent": consistent,
        "blocking_issues": blocking,
        "lines": lines,
        "income_components_net": round(income, 2),
        "deductions_included": round(deductions, 2),
        "prior_year_tax_losses_applied": round(applied, 2),
        "taxable_income": round(max(0.0, after), 2) if consistent else None,
        "tax_loss_carried_forward": round(max(0.0, -after) + (inp.prior_year_tax_losses - applied), 2) if consistent else None,
        "handoffs": {"individual_income_tax.taxable_income": round(max(0.0, after), 2) if consistent else None,
                     "net_rental_loss_for_net_investment_losses": round(rental_losses, 2)},
        "assumptions": assumptions,
        "warnings": warnings,
    }
