"""Employer payroll obligations: PAYG withholding (Schedule 1 and Schedule 8 formulas, no-TFN and no-ABN
withholding), superannuation guarantee (quarterly regime to 30 Jun 2026, Payday Super from 1 Jul 2026),
SG charge estimates (both regimes) and employee-versus-contractor indicators.

Law: Taxation Administration Act 1953 (TAA) Sch 1 Div 12 (ss12-35, 12-190) and ss15-25/15-30 withholding
schedules (NAT 1004, NAT 3539); Superannuation Guarantee (Administration) Act 1992 (SGAA) as amended by the
Treasury Laws Amendment (Payday Superannuation) Act 2025 and the Superannuation Guarantee Charge Amendment
Act 2025 (qualifying earnings s10A, individual SG amount s17A, shortfall ss16B-20C); SG (Administration)
Regulations 2018 ss13-13D; LCR 2026/3; TR 2023/4 (who is an employee, incl. SGAA s12 in Appendix 2);
CFMMEU v Personnel Contracting Pty Ltd [2022] HCA 1; ZG Operations Australia Pty Ltd v Jamsek [2022] HCA 2;
Fair Work Act 2009 s15AA (from 26 Aug 2024). Every rate and threshold comes from data/rates via Figures.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from au_tax.figures import FigureError, Figures
from au_tax.holidays import COMMONWEALTH, business_days_after as business_days_after_checked, roll_due_date
from au_tax.registry import Refusal, calculator

PAYDAY_SUPER_START = date(2026, 7, 1)          # SGAA amendments apply to QE paid on or after this day
STSL_2025_26_SCHEDULE_FROM = date(2025, 9, 24)  # Schedule 8 (marginal system) for 2025-26 payments from this day
LATE_OFFSET_LAST_QUARTER_END = date(2026, 3, 31)  # late payment offset only for quarters to 31 Mar 2026


# ---------------------------------------------------------------- shared helpers

def _half_up(x: float) -> int:
    """Round to the nearest dollar, 50 cents up (Schedule 1 'Rounding of withholding amounts').
    A tiny epsilon absorbs binary noise so 12.5 exactly rounds up and 12.4999999 does not."""
    return int(math.floor(x + 0.5 + 1e-9))


def _cents(x: float) -> float:
    return round(x + 0.0, 2)


def _year_bounds(figures: Figures) -> tuple[date, date]:
    meta = figures.data.get("meta", {})
    return meta["start"], meta["end"]


def _coeff_row(rows: list[dict], x: float) -> dict:
    for r in rows:
        if r["to"] is None or x < r["to"]:
            return r
    return rows[-1]


def _apply_coeff(rows: list[dict], x: float) -> float:
    r = _coeff_row(rows, x)
    return max(0.0, r["rate"] * x - r["b"])


def _override_walk(start: date, n: int | None, holidays: set[date]) -> date:
    """Caller-supplied holidays: weekends and exactly these days are non-business days. n=None rolls start forward."""
    d, count = start, 0
    if n is None:
        while d.weekday() >= 5 or d in holidays:
            d += timedelta(days=1)
        return d
    while count < n:
        d += timedelta(days=1)
        if d.weekday() < 5 and d not in holidays:
            count += 1
    return d


def business_days_after(start: date, n: int, holidays: set[date] | None = None, figures: Figures | None = None,
                        notes: list | None = None) -> date:
    """The nth business day after start (start itself not counted). Business day: not Sat/Sun and not a
    public holiday for the whole of any state, the ACT or the NT (SGAA s6(1); LCR 2026/3 para 4). By default the
    public holidays come from data/holidays/au.yaml (commonwealth_tax regime; refuses outside the data range,
    AU-GEN-004). A caller-supplied `holidays` set overrides the data: only weekends and those days are skipped.
    `notes` (optional) collects warnings and the skipped days."""
    if holidays is not None:
        return _override_walk(start, n, holidays)
    r = business_days_after_checked(start, n, COMMONWEALTH, figures)
    if notes is not None:
        notes.extend(w for w in r.warnings if w not in notes)
    return r.due


def _next_business_day(d: date, holidays: set[date] | None = None, figures: Figures | None = None,
                       notes: list | None = None) -> date:
    """First business day on or after d (data default; caller-supplied holidays override), as business_days_after."""
    if holidays is not None:
        return _override_walk(d, None, holidays)
    r = roll_due_date(d, COMMONWEALTH, figures)
    if notes is not None:
        notes.extend(w for w in r.warnings if w not in notes)
    return r.due


# ---------------------------------------------------------------- PAYG withholding

PaygSpecial = Literal[
    "working_holiday_maker", "seniors_pensioner_offset", "horticulture_or_shearing", "entertainer",
    "daily_or_casual_table", "back_payment_bonus_or_commission_lump", "termination_payment",
    "medicare_levy_variation_family", "directors_fee_or_other_non_periodic", "super_income_stream_or_lump_sum",
    "extra_withholding_53_or_27_pays", "increased_withholding_agreement", "voluntary_agreement_contractor",
]


class PaygInput(BaseModel):
    """One regular payment to one payee."""

    gross_earnings: float = Field(ge=0, description="Gross earnings for this pay period including allowances subject to "
                                  "withholding (before salary sacrifice is NOT deducted here: give the taxable amount paid).")
    period: Literal["weekly", "fortnightly", "monthly", "quarterly"] = Field(description="Pay period.")
    tfn_provided: bool = Field(True, description="False if the payee has not quoted a TFN (and none of the TFN exemptions apply) -> scale 4.")
    residency: Literal["resident", "foreign"] = Field("resident", description="Tax residency declared on the TFN declaration.")
    tax_free_threshold_claimed: bool = Field(True, description="Tax-free threshold claimed with this payer (residents only).")
    medicare_exemption: Literal["none", "full", "half"] = Field(
        "none", description="Medicare levy variation declaration claiming a full (scale 5) or half (scale 6) exemption.")
    study_loan_debt: bool = Field(False, description="Payee has a HELP, VSL, FS, SSL or AASL debt (Schedule 8 component).")
    withholding_declaration_offsets: float = Field(
        0, ge=0, description="Annual total of tax offsets claimed on the Withholding declaration (scales 2, 5, 6 only).")
    payment_date: date | None = Field(None, description="Date the payment is made (needed for 2025-26 study loan component).")
    special_circumstances: list[PaygSpecial] = Field(
        default_factory=list, description="Any situation needing a different schedule or table; each one refuses (AU-PAY-006).")


def _weekly_x(gross: float, period: str) -> float:
    """Schedule 1 'Working out the weekly earnings': whole dollars of the weekly equivalent plus 99 cents."""
    if period == "weekly":
        w = gross
    elif period == "fortnightly":
        w = gross / 2
    elif period == "monthly":
        g = round(gross, 2)
        if round(g * 100) % 100 == 33:  # amounts ending in 33 cents: add one cent
            g += 0.01
        w = g * 3 / 13
    else:
        w = gross / 13
    return math.floor(w + 1e-9) + 0.99


def _to_period(weekly: int, period: str) -> int:
    if period == "weekly":
        return weekly
    if period == "fortnightly":
        return weekly * 2
    if period == "monthly":
        return _half_up(weekly * 13 / 3)
    return weekly * 13


@calculator("payg_withholding", PaygInput)
def payg_withholding(figures: Figures, inp: PaygInput) -> dict:
    """PAYG withholding from one regular weekly, fortnightly, monthly or quarterly payment to an employee (or
    other Schedule 1 payee) using the ATO Schedule 1 statement of formulas (NAT 1004) for the income year:
    scale 1 (no tax-free threshold), 2 (tax-free threshold), 3 (foreign resident), 4 (no TFN), 5 and 6
    (full or half Medicare exemption), tax offsets claimed on a Withholding declaration, and the Schedule 8
    study and training support loan (HELP etc.) component. Returns the weekly equivalent, scale, each
    component and the total to withhold in whole dollars. Use for "how much tax do I withhold from a $X
    fortnightly pay", "no TFN withholding", "withholding with HELP debt". Income year selects the schedule:
    2025-26 = payments 1 Jul 2025 to 30 Jun 2026; 2026-27 = payments from 1 Jul 2026. Refuses AU-PAY-006
    for payees needing other schedules (working holiday makers, seniors, daily/casual, bonuses and back pay,
    termination payments, Medicare levy family adjustments); AU-GEN-001 if coefficients are not verified.
    For payments to a supplier with no ABN use no_abn_withholding instead."""
    if inp.special_circumstances:
        raise Refusal("AU-PAY-006", ", ".join(inp.special_circumstances))
    start, end = _year_bounds(figures)
    assumptions: list[str] = []
    warnings: list[str] = []
    if inp.payment_date and not (start <= inp.payment_date <= end):
        raise Refusal("AU-PAY-008", f"payment date {inp.payment_date} is outside income year {figures.income_year}; "
                      "rerun with the income year in which the payment is made")
    if inp.residency == "foreign" and inp.medicare_exemption != "none":
        warnings.append("Medicare exemption ignored: foreign residents are withheld under scale 3, which has no Medicare levy.")
    period = inp.period
    gross = inp.gross_earnings
    out: dict = {"period": period, "gross_earnings": _cents(gross)}

    # Scale 4: no TFN
    if not inp.tfn_provided:
        key = "payroll.payg_scale4_no_tfn_resident_rate" if inp.residency == "resident" else "payroll.payg_scale4_no_tfn_foreign_rate"
        rate = figures.get(key)
        amount = math.floor(rate * math.floor(gross + 1e-9) + 1e-9)
        assumptions.append("No TFN quoted and no TFN exemption: scale 4 applies to the whole payment (cents ignored in earnings and result); "
                           "no tax-free threshold, offsets or study loan component.")
        if inp.study_loan_debt:
            warnings.append("Study loan component not added: Schedule 8 applies only where a TFN declaration was given.")
        out.update({"scale": "4", "weekly_equivalent_x": None, "withholding_before_offsets": amount,
                    "offsets_reduction": 0, "stsl_component": 0, "total_withholding": amount,
                    "assumptions": assumptions, "warnings": warnings})
        return out

    if inp.residency == "foreign":
        scale, key = "3", "payroll.payg_scale3_foreign"
    elif not inp.tax_free_threshold_claimed:
        if inp.medicare_exemption != "none":
            raise Refusal("AU-PAY-006", "Medicare levy exemption without the tax-free threshold: no Schedule 1 scale")
        scale, key = "1", "payroll.payg_scale1_no_tft"
    elif inp.medicare_exemption == "full":
        scale, key = "5", "payroll.payg_scale5_full_medicare_exemption"
    elif inp.medicare_exemption == "half":
        scale, key = "6", "payroll.payg_scale6_half_medicare_exemption"
    else:
        scale, key = "2", "payroll.payg_scale2_tft"

    x = _weekly_x(gross, period)
    weekly = _half_up(_apply_coeff(figures.get(key), x))
    before_offsets = _to_period(weekly, period)

    offsets = 0
    if inp.withholding_declaration_offsets:
        if scale in ("2", "5", "6"):
            factor = figures.get(f"payroll.payg_offset_factor_{period}")
            offsets = _half_up(factor * inp.withholding_declaration_offsets)
        else:
            warnings.append(f"Tax offsets on the Withholding declaration are not allowed under scale {scale}; ignored.")
    after_offsets = max(0, before_offsets - offsets)

    stsl = 0
    if inp.study_loan_debt:
        if figures.income_year == "2025-26" and (inp.payment_date is None or inp.payment_date < STSL_2025_26_SCHEDULE_FROM):
            raise Refusal("AU-PAY-006", "2025-26 study loan component: the Schedule 8 held here applies to payments from "
                          "24 Sep 2025; give payment_date on or after that day, or use the ATO tax withheld calculator")
        tkey = ("payroll.payg_stsl_component_tft_or_foreign" if (inp.residency == "foreign" or inp.tax_free_threshold_claimed)
                else "payroll.payg_stsl_component_no_tft")
        stsl = _to_period(_half_up(_apply_coeff(figures.get(tkey), x)), period)
        assumptions.append("Study loan component from Schedule 8 added to the Schedule 1 amount (payee has not claimed a "
                           "Medicare levy reduction for spouse or dependants).")

    total = after_offsets + stsl
    assumptions.append(f"Schedule 1 scale {scale}; weekly equivalent x = {x:.2f}; y = a x - b rounded to the nearest dollar, "
                       "then converted to the pay period.")
    if period in ("weekly", "fortnightly"):
        warnings.append("If the year has 53 weekly or 27 fortnightly pays, the payee may ask for extra withholding (Schedule 1 table); not added.")
    out.update({
        "scale": scale,
        "weekly_equivalent_x": x,
        "weekly_withholding": weekly,
        "withholding_before_offsets": before_offsets,
        "offsets_reduction": offsets,
        "stsl_component": stsl,
        "total_withholding": total,
        "assumptions": assumptions,
        "warnings": warnings,
    })
    return out


# ---------------------------------------------------------------- no-ABN withholding

class NoAbnInput(BaseModel):
    payment_ex_gst: float = Field(ge=0, description="Total payment for the supply, excluding GST.")
    abn_quoted: bool = Field(False, description="Supplier quoted a valid ABN (on invoice or other document).")
    exception: Literal["none", "not_carrying_on_enterprise", "hobby_or_private_statement", "wholly_input_taxed",
                       "under_18_not_over_350_per_week", "exempt_income", "not_entitled_to_abn"] = Field(
        "none", description="A no-ABN withholding exception evidenced by a Statement by a supplier or the facts.")
    worker_may_be_employee: bool = Field(False, description="True if the 'supplier' is an individual whose work may make "
                                         "them an employee (then PAYG and SG obligations may apply instead).")


@calculator("no_abn_withholding", NoAbnInput)
def no_abn_withholding(figures: Figures, inp: NoAbnInput) -> dict:
    """No-ABN withholding (TAA 1953 Sch 1 s12-190): amount a business must withhold from a payment to a supplier
    who has not quoted an ABN, at the top rate, unless the payment is at or below the small-payment threshold
    (excluding GST) or an exception applies. Use for "contractor has no ABN, what do I withhold". Report at
    BAS label W4. If the worker may really be an employee, run worker_status_indicators first."""
    threshold = figures.get("payroll.no_abn_payment_threshold")
    rate = figures.get("payroll.no_abn_withholding_rate")
    warnings: list[str] = []
    if inp.worker_may_be_employee:
        warnings.append("If the individual is an employee (or an SG employee under SGAA s12(3)), PAYG withholding under "
                        "Schedule 1, super guarantee and STP reporting apply instead of no-ABN withholding.")
    if inp.abn_quoted:
        reason, amount = "ABN quoted: no withholding", 0.0
    elif inp.payment_ex_gst <= threshold:
        reason, amount = "total payment for the supply at or below the threshold (excluding GST)", 0.0
    elif inp.exception != "none":
        reason, amount = f"exception applies: {inp.exception}", 0.0
    else:
        reason = "no ABN quoted, payment above threshold, no exception: withhold the top rate from the whole payment"
        amount = math.floor(rate * math.floor(inp.payment_ex_gst + 1e-9) + 1e-9)
    return {"payment_ex_gst": _cents(inp.payment_ex_gst), "withholding": amount, "reason": reason,
            "assumptions": ["Withholding applies to the whole payment; cents ignored as for scale 4. Report at W4 and give the "
                            "supplier a PAYG payment summary - withholding where ABN not quoted."],
            "warnings": warnings}


# ---------------------------------------------------------------- super guarantee

class SgPayment(BaseModel):
    pay_date: date = Field(description="Day the earnings leave the employer's account (QE day from 1 Jul 2026).")
    ordinary_time_earnings: float = Field(0, ge=0, description="Pay for ordinary hours incl. paid leave, casual loading, shift penalties, "
                                          "ordinary-hours allowances and bonuses, and commissions for ordinary hours.")
    commissions_outside_ordinary_hours: float = Field(0, ge=0, description="Commission solely for work entirely outside ordinary hours "
                                                      "(qualifying earnings from 1 Jul 2026; not OTE before).")
    salary_sacrificed_ote: float = Field(0, ge=0, description="Amounts sacrificed to super that would otherwise have been OTE "
                                         "(stay in the SG base: qualifying earnings, SGAA s10A; before 1 Jul 2026 the salary sacrifice rules added from 1 Jan 2020).")
    overtime: float = Field(0, ge=0, description="Overtime pay (not OTE and not qualifying earnings for an ordinary employee).")
    other_excluded: float = Field(0, ge=0, description="Other amounts outside the base (e.g. expense reimbursements, "
                                  "termination payments, paid parental leave from the government).")


class SgInput(BaseModel):
    payments: list[SgPayment] = Field(min_length=1, description="Payments of earnings to one employee in the income year.")
    ytd_base_before: float = Field(0, ge=0, description="Qualifying earnings already paid by this employer earlier in the "
                                   "2026-27 year (for the annual maximum contribution base). Ignored for 2025-26.")
    first_contribution_new_employee: bool = Field(False, description="First SG contribution for a new employee (20 business days).")
    first_contribution_new_fund: bool = Field(False, description="First SG contribution to a new fund for an existing employee.")
    public_holidays: list[date] | None = Field(None, description="Override only. Leave out to use the public holiday data "
                                               "(holidays for the whole of any state, the ACT or the NT, 1 Jul 2025 to 30 Jun 2028). If "
                                               "given, these days and weekends are the only non-business days and the data is not used.")
    employee_under_18_hours_over_30: bool | None = Field(None, description="Under 18: true if they worked more than 30 hours "
                                                         "in the week; false = no SG for that week. None = not under 18 / not stated.")
    domestic_or_private_hours_over_30: bool | None = Field(None, description="Private or domestic worker: true if more than 30 "
                                                           "hours in the week; false = no SG. None = not applicable.")


def _quarter(d: date) -> tuple[int, date, date]:
    q_start_month = ((d.month - 1) // 3) * 3 + 1
    qs = date(d.year, q_start_month, 1)
    qe = (date(d.year + (q_start_month + 3 > 12), (q_start_month + 3 - 1) % 12 + 1, 1) - timedelta(days=1))
    fy_q = {7: 1, 10: 2, 1: 3, 4: 4}[q_start_month]
    return fy_q, qs, qe


def _quarter_due(qe: date) -> date:
    """SG due date for a quarter to 30 Jun 2026: 28 days after the end of the quarter (28 Oct, 28 Jan, 28 Apr, 28 Jul)."""
    return qe + timedelta(days=28)


@calculator("super_guarantee", SgInput)
def super_guarantee(figures: Figures, inp: SgInput) -> dict:
    """Minimum super guarantee for one employee from a list of pay dates and earnings. 2026-27 (Payday Super,
    from 1 Jul 2026): 12% of qualifying earnings for each payday (QE day), capped by the annual maximum
    contribution base, due in the fund within 7 business days after payday (20 for a first contribution to a
    new employee or new fund). 2025-26 (quarterly regime): 12% of ordinary time earnings per quarter, capped
    by the quarterly maximum contribution base, due 28 days after quarter end. Overtime is excluded;
    salary-sacrificed ordinary pay stays in the base. Use for "how much super do I pay on this pay run",
    "when is super due", "super on overtime / commission / salary sacrifice". Business days exclude
    weekends and public holidays for the whole of any state, the ACT or the NT, read from the public holiday data
    (dates outside it are refused, AU-GEN-004); public_holidays, if given, overrides the data."""
    start, end = _year_bounds(figures)
    rate = figures.get("super.sg_rate")
    holidays = set(inp.public_holidays) if inp.public_holidays is not None else None
    assumptions: list[str] = []
    warnings: list[str] = []
    for p in inp.payments:
        if not (start <= p.pay_date <= end):
            raise Refusal("AU-PAY-008", f"pay date {p.pay_date} is outside income year {figures.income_year}; "
                          "split the payments by income year")
    if inp.employee_under_18_hours_over_30 is False or inp.domestic_or_private_hours_over_30 is False:
        assumptions.append("No SG required: worker under 18 (or private/domestic) who did not work more than 30 hours in the week (SGAA s12(11) for domestic work; under-18 part-time exclusion).")
        return {"regime": "n/a", "sg_total": 0.0, "lines": [], "assumptions": assumptions, "warnings": warnings}
    if holidays is not None:
        warnings.append("Caller-supplied public_holidays override the public holiday data: only weekends and the days you gave "
                        "are treated as non-business days.")
    else:
        assumptions.append("Business days exclude Saturdays, Sundays and any day that is a public holiday for the whole of any State, "
                           "the ACT or the NT, wherever the employer is (SGAA 1992 s 6(1); LCR 2026/3 para 4), read from data/holidays/au.yaml.")
    if any(p.overtime for p in inp.payments):
        assumptions.append("Overtime excluded from the SG base (not OTE and not qualifying earnings for an ordinary employee).")
    if any(p.salary_sacrificed_ote for p in inp.payments):
        assumptions.append("Salary-sacrificed amounts that would otherwise be OTE are added back to the base (qualifying earnings, SGAA s10A; salary sacrifice rules from 1 Jan 2020 before that); "
                           "sacrificed contributions do not count towards the employer's SG.")

    lines = []
    if start >= PAYDAY_SUPER_START:
        mcb = figures.get("super.max_contribution_base_annual")
        n7 = figures.get("super.payday_super_usual_period_business_days")
        n20 = figures.get("super.payday_super_first_contribution_business_days")
        ytd = inp.ytd_base_before
        longest_prev_end: date | None = None
        first = inp.first_contribution_new_employee or inp.first_contribution_new_fund
        for i, p in enumerate(sorted(inp.payments, key=lambda q: q.pay_date)):
            qe = p.ordinary_time_earnings + p.commissions_outside_ordinary_hours + p.salary_sacrificed_ote
            counted = max(0.0, min(qe, mcb - ytd))
            ytd += qe
            sg = _cents(rate * counted)
            usual = business_days_after(p.pay_date, n7, holidays, figures, warnings)
            due, basis = usual, "7 business days after the QE day"
            if first and i == 0:
                due, basis = business_days_after(p.pay_date, n20, holidays, figures, warnings), "first contribution: 20 business days after the QE day"
                longest_prev_end = due
            elif longest_prev_end and usual < longest_prev_end:
                due, basis = longest_prev_end, "extended to the earlier QE day's allowable longer period"
            lines.append({"qe_day": p.pay_date.isoformat(), "qualifying_earnings": _cents(qe),
                          "qualifying_earnings_counted": _cents(counted), "sg_amount": sg,
                          "due_date": due.isoformat(), "due_basis": basis})
            if counted < qe:
                warnings.append(f"Maximum contribution base reached on {p.pay_date}: SG not required on earnings above it for the rest of the year.")
        assumptions.append("Payday Super: the contribution must be received by the fund, allocable, by the due date; paying a "
                           "clearing house is not receipt by the fund.")
        regime = "payday_super"
    else:
        mcb_q = figures.get("super.max_contribution_base_per_quarter")
        by_q: dict[int, dict] = {}
        for p in inp.payments:
            q, qs, qend = _quarter(p.pay_date)
            b = by_q.setdefault(q, {"quarter": q, "quarter_start": qs, "quarter_end": qend, "ote": 0.0})
            b["ote"] += p.ordinary_time_earnings + p.salary_sacrificed_ote
            if p.commissions_outside_ordinary_hours:
                warnings.append("Commission solely for work outside ordinary hours is not OTE before 1 Jul 2026; excluded.")
        for q in sorted(by_q):
            b = by_q[q]
            counted = min(b["ote"], mcb_q)
            due = _next_business_day(_quarter_due(b["quarter_end"]), holidays, figures, warnings)
            lines.append({"quarter": q, "period": f"{b['quarter_start']} to {b['quarter_end']}", "ote": _cents(b["ote"]),
                          "ote_counted": _cents(counted), "sg_amount": _cents(rate * counted), "due_date": due.isoformat(),
                          "due_basis": "28 days after the end of the quarter (first business day after if not a business day)"})
            if counted < b["ote"]:
                warnings.append(f"Quarter {q}: OTE above the quarterly maximum contribution base; SG capped.")
        assumptions.append("Quarterly regime (quarters ending on or before 30 Jun 2026): SG is 12% of OTE for the quarter; "
                           "contributions for the June 2026 quarter received on or after 29 Jul 2026 go to Payday Super QE days instead.")
        regime = "quarterly"
    return {"regime": regime, "sg_rate": rate, "sg_total": _cents(sum(l["sg_amount"] for l in lines)), "lines": lines,
            "assumptions": assumptions, "warnings": warnings}


# ---------------------------------------------------------------- SG charge

class LateContribution(BaseModel):
    amount: float = Field(gt=0)
    received: date = Field(description="Day the fund received it (allocable).")


class SgcEmployee(BaseModel):
    name: str = "employee"
    qualifying_earnings: float = Field(0, ge=0, description="Payday Super: qualifying earnings paid on the QE day. "
                                       "Quarterly regime: salary or wages for the quarter (INCLUDING overtime).")
    on_time_contributions: float = Field(0, ge=0, description="Eligible contributions received within the on-time window.")
    late_contributions: list[LateContribution] = Field(default_factory=list)
    first_contribution_new_employee_or_fund: bool = False
    non_choice_compliant_contributions: float = Field(0, ge=0, description="Contributions that did not meet choice of fund rules.")
    prior_choice_loadings_in_notice_period: float = Field(0, ge=0)


class SgcInput(BaseModel):
    qe_day: date | None = Field(None, description="Payday Super: the QE day (payday) the shortfall relates to.")
    quarter_end: date | None = Field(None, description="Quarterly regime (2025-26): last day of the quarter, e.g. 2025-09-30.")
    employees: list[SgcEmployee] = Field(min_length=1)
    calculation_date: date = Field(description="Date the estimate is made. Notional earnings run to the day before assessment "
                                   "(or this date if no assessment date is given).")
    assessment_date: date | None = Field(None, description="Payday Super: day the ATO assessment is made, if known.")
    vds_lodged: date | None = Field(None, description="Payday Super: day a voluntary disclosure statement was lodged (before assessment).")
    commissioner_assessment_in_prior_24_months: bool = Field(
        False, description="Payday Super: an ATO-initiated SGC assessment or estimate in the 24 months ending on the QE day (from 1 Jul 2026).")
    sgc_statement_lodged: date | None = Field(None, description="Quarterly regime: day the SGC statement is lodged (default: calculation_date).")
    late_payments_elected_offset: float = Field(0, ge=0, description="Quarterly regime: late contributions elected as a late payment offset.")
    public_holidays: list[date] | None = Field(None, description="Override only: leave out to use the public holiday data; if given, "
                                               "these days and weekends are the only non-business days.")
    gic_annual_rate_override: float | None = Field(None, gt=0, lt=1, description="Assumed GIC rate for days whose GIC rate is not yet "
                                                   "published or for reproducing an ATO example; output is then an estimate only.")
    dispute_or_penalty: bool = Field(False, description="True if the question is about objecting to an assessment, remission, the "
                                     "late payment penalty, Part 7 penalty or a director penalty notice (refused, AU-PAY-007).")


def _gic_daily(figures: Figures, d: date, override: float | None) -> float:
    if override is not None:
        return override / 365
    for q in figures.get("penalties_interest.gic_quarterly"):
        if q["from"] <= d <= q["to"]:
            return q.get("daily_rate") or q["rate"] / 365
    raise FigureError(f"GIC rate for {d} not in the verified {figures.income_year} rates; give gic_annual_rate_override for an estimate")


def _sgc_payday(figures: Figures, inp: SgcInput, assumptions: list[str], warnings: list[str]) -> dict:
    qe_day = inp.qe_day
    if qe_day is None:
        raise Refusal("AU-PAY-008", "qe_day is required for Payday Super (QE days from 1 Jul 2026)")
    rate = figures.get("super.sg_rate")
    n7 = figures.get("super.payday_super_usual_period_business_days")
    n20 = figures.get("super.payday_super_first_contribution_business_days")
    holidays = set(inp.public_holidays) if inp.public_holidays is not None else None
    last_day = (inp.assessment_date - timedelta(days=1)) if inp.assessment_date else inp.calculation_date
    rows, tot_final, tot_ne, tot_choice = [], 0.0, 0.0, 0.0
    choice_rate = choice_limit = None
    any_base = False
    for e in inp.employees:
        sg = _cents(rate * e.qualifying_earnings)
        n = n20 if e.first_contribution_new_employee_or_fund else n7
        on_time_end = business_days_after(qe_day, n, holidays, figures, warnings)
        base = max(0.0, _cents(sg - e.on_time_contributions))
        late_sorted = sorted((c for c in e.late_contributions if c.received <= last_day), key=lambda c: c.received)
        ignored = [c for c in e.late_contributions if c.received > last_day]
        if ignored:
            warnings.append(f"{e.name}: late contributions received after the late period ended are ignored.")
        final, ne, ne_days, ne_end = base, 0.0, 0, None
        if base > 0:
            any_base = True
            paid, cleared = 0.0, None
            for c in late_sorted:
                if c.received <= on_time_end:
                    continue
                paid += c.amount
                if cleared is None and paid >= base - 1e-9:
                    cleared = c.received
            final = max(0.0, _cents(base - paid))
            ne_start = on_time_end + timedelta(days=1)
            ne_end = cleared or last_day
            if ne_end >= ne_start:
                amt, d = base, ne_start
                while d <= ne_end:
                    amt *= 1 + _gic_daily(figures, d, inp.gic_annual_rate_override)
                    d += timedelta(days=1)
                    ne_days += 1
                ne = _cents(amt - base)
        choice = 0.0
        if e.non_choice_compliant_contributions:
            choice_rate = choice_rate or figures.get("super.sgc_choice_loading_rate")
            choice_limit = choice_limit or figures.get("super.sgc_choice_loading_limit")
            choice = _cents(max(0.0, min(choice_rate * e.non_choice_compliant_contributions,
                                         choice_limit - e.prior_choice_loadings_in_notice_period)))
        tot_final += final
        tot_ne += ne
        tot_choice += choice
        rows.append({"name": e.name, "individual_sg_amount": sg, "on_time_deadline": on_time_end.isoformat(),
                     "individual_base_shortfall": base, "individual_final_shortfall": final,
                     "notional_earnings": ne, "notional_earnings_days": ne_days,
                     "notional_earnings_to": ne_end.isoformat() if ne_end and ne_days else None, "choice_loading": choice})
    pct, uplift = 0.0, 0.0
    if any_base:
        pct = figures.get("super.sgc_admin_uplift_default_rate")
        if not inp.commissioner_assessment_in_prior_24_months:
            pct -= figures.get("super.sgc_admin_uplift_compliance_history_reduction")
        if inp.vds_lodged:
            day_n = (inp.vds_lodged - qe_day).days + 1  # calendar days starting on the QE day
            k = ("30_days" if day_n <= 30 else "60_days" if day_n <= 60 else "120_days" if day_n <= 120 else "later")
            pct -= figures.get(f"super.sgc_admin_uplift_vds_reduction_{k}")
        pct = max(0.0, round(pct, 4))
        uplift = _cents(pct * (tot_final + tot_ne))
    total = _cents(tot_final + tot_ne + uplift + tot_choice)
    assessed = math.floor(total * 20 + 1e-6) / 20  # decreased to the nearest multiple of 5 cents
    assumptions.append("Payday Super SGC per LCR 2026/3: individual final shortfall + notional earnings (GIC compounded daily on "
                       "the base shortfall over calendar days in the late period) + administrative uplift + choice loading.")
    if inp.gic_annual_rate_override is not None:
        warnings.append(f"Notional earnings use an assumed GIC rate of {inp.gic_annual_rate_override:.4f}; estimate only.")
    if not inp.assessment_date:
        assumptions.append(f"No assessment date given: notional earnings accrue to {inp.calculation_date} and keep growing until the "
                           "shortfall is paid or the ATO assesses.")
    return {"regime": "payday_super", "qe_day": qe_day.isoformat(), "employees": rows,
            "total_individual_final_shortfall": _cents(tot_final), "total_notional_earnings": _cents(tot_ne),
            "admin_uplift_rate": pct, "admin_uplift_amount": uplift, "total_choice_loading": _cents(tot_choice),
            "sg_charge": total, "sg_charge_as_assessed": round(assessed, 2), "deductible": True}


def _sgc_quarterly(figures: Figures, inp: SgcInput, assumptions: list[str], warnings: list[str]) -> dict:
    qend = inp.quarter_end
    if qend is None:
        raise Refusal("AU-PAY-008", "quarter_end is required for quarters ending on or before 30 Jun 2026")
    ys, ye = _year_bounds(figures)
    if not ys <= qend <= ye:
        raise Refusal("AU-PAY-008", f"quarter ending {qend} is not in income year {figures.income_year}")
    _, qs, qe_calc = _quarter(qend)
    if qe_calc != qend:
        raise Refusal("AU-PAY-008", "quarter_end must be 30 Sep, 31 Dec, 31 Mar or 30 Jun")
    if any(e.on_time_contributions or e.non_choice_compliant_contributions for e in inp.employees):
        raise Refusal("AU-PAY-007", "partly paid quarter or choice liability under the pre-1 Jul 2026 SGC: reduction of the charge "
                      "percentage and choice liability need the ATO SGC statement and calculator tool")
    rate = figures.get("super.sg_rate")
    mcb_q = figures.get("super.max_contribution_base_per_quarter")
    ni_rate = figures.get("super.sgc_nominal_interest_rate")
    fee = figures.get("super.sgc_admin_fee_per_employee")
    # statement due date: 28th day of the second month after quarter end
    m = qend.month + 2
    due = date(qend.year + (m > 12), (m - 1) % 12 + 1, 28)
    lodged = inp.sgc_statement_lodged or inp.calculation_date
    lodgment_day = max(due, lodged)
    days = (lodgment_day - qs).days  # from the first day of the quarter up to but not including the lodgment day
    rows, total_short = [], 0.0
    for e in inp.employees:
        sw = min(e.qualifying_earnings, mcb_q)
        short = _cents(rate * sw)
        total_short += short
        rows.append({"name": e.name, "salary_or_wages": _cents(e.qualifying_earnings), "sg_shortfall": short})
        if e.qualifying_earnings > mcb_q:
            warnings.append(f"{e.name}: salary or wages capped at the quarterly maximum contribution base.")
    total_short = _cents(total_short)
    n_short = sum(1 for r in rows if r["sg_shortfall"] > 0)
    nominal = _cents(total_short * days / 365 * ni_rate)
    admin = _cents(fee * n_short)
    sgc = _cents(total_short + nominal + admin)
    offset = 0.0
    if inp.late_payments_elected_offset:
        if qend > LATE_OFFSET_LAST_QUARTER_END:
            warnings.append("Late payment offset is not available for the quarter ending 30 Jun 2026; late contributions go to QE days instead.")
        else:
            offset = min(inp.late_payments_elected_offset, total_short + nominal)
    assumptions.append("Pre-1 Jul 2026 SGC: shortfall on salary or wages (including overtime), nominal interest from the first day of "
                       "the quarter up to but not including the later of the statement due date and lodgment, plus an administration fee "
                       "per employee. Not deductible.")
    return {"regime": "quarterly", "quarter": f"{qs} to {qend}", "sgc_statement_due": due.isoformat(),
            "nominal_interest_days": days, "employees": rows, "total_sg_shortfall": total_short,
            "nominal_interest": nominal, "administration_fee": admin, "sg_charge": sgc,
            "late_payment_offset": _cents(offset), "sgc_payable_after_offset": _cents(sgc - offset), "deductible": False}


@calculator("sg_charge_estimate", SgcInput)
def sg_charge_estimate(figures: Figures, inp: SgcInput) -> dict:
    """Estimate the super guarantee charge for late or missed SG. Income year 2026-27 (Payday Super, QE days from
    1 Jul 2026): per QE day, individual final SG shortfall + notional earnings (GIC compounded daily from the day
    after the on-time deadline until paid or the day before assessment) + administrative uplift (default
    percentage reduced for clean compliance history and a voluntary disclosure) + choice loading; tax deductible,
    assessed by the ATO. Income year 2025-26 (quarters to 30 Jun 2026): shortfall on salary or wages + nominal
    interest + administration fee per employee, optional late payment offset; not deductible. Use for "I paid
    super late, what's the SGC", "missed super for a payday". Refuses AU-PAY-007 for disputes, penalties and
    partly paid pre-2026 quarters; AU-GEN-001 if a needed GIC rate is not yet published (or give
    gic_annual_rate_override for a labelled estimate)."""
    if inp.dispute_or_penalty:
        raise Refusal("AU-PAY-007", "objection, remission or penalty question")
    assumptions: list[str] = []
    warnings: list[str] = []
    start, end = _year_bounds(figures)
    if start >= PAYDAY_SUPER_START:
        if inp.quarter_end is not None or (inp.qe_day and not start <= inp.qe_day <= end):
            raise Refusal("AU-PAY-008", f"income year {figures.income_year} covers Payday Super QE days {start} to {end}; "
                          "for quarters to 30 Jun 2026 use income year 2025-26")
        body = _sgc_payday(figures, inp, assumptions, warnings)
    else:
        if inp.qe_day is not None:
            raise Refusal("AU-PAY-008", "QE days apply from 1 Jul 2026 (income year 2026-27); for 2025-26 give quarter_end")
        body = _sgc_quarterly(figures, inp, assumptions, warnings)
    return {**body, "assumptions": assumptions, "warnings": warnings}


# ---------------------------------------------------------------- employee vs contractor

Tri = Literal["yes", "no", "unknown"]


class WorkerStatusInput(BaseModel):
    """Facts about one engagement. 'yes' / 'no' / 'unknown' for each; answer from the contract terms first."""

    worker_is_individual: bool = Field(True, description="False if engaged through a company, trust or partnership.")
    written_contract_comprehensive: Tri = Field("unknown", description="Terms comprehensively committed to a written contract not "
                                                "challenged as a sham or varied.")
    right_to_control_how_work_done: Tri = Field("unknown", description="Engager has the contractual right to control how, where and when.")
    must_perform_personally: Tri = Field("unknown", description="Worker cannot delegate or subcontract the work.")
    paid_by_time: Tri = Field("unknown", description="Paid by hours or days worked rather than a quoted price for a result.")
    paid_for_result: Tri = Field("unknown", description="Paid a fixed price to produce a specified result.")
    provides_significant_tools_equipment: Tri = Field("unknown", description="Worker supplies substantial tools, equipment or vehicle at own cost.")
    bears_commercial_risk: Tri = Field("unknown", description="Worker bears risk of loss, rectifies defects at own cost, carries own insurance.")
    builds_own_goodwill: Tri = Field("unknown", description="Worker advertises and works for other clients; goodwill accrues to them.")
    presents_as_part_of_engager_business: Tri = Field("unknown", description="Wears uniform, uses engager branding, is integrated into its business.")
    contract_principally_for_labour: Tri = Field("unknown", description="More than half the contract value is for the person's labour "
                                                 "(not materials, equipment or a result).")
    has_abn: bool | None = Field(None, description="Worker quotes an ABN (not determinative).")
    labelled_contractor: bool | None = Field(None, description="Contract calls the worker a contractor (label not determinative).")
    dispute_or_sham_allegation: bool = Field(False, description="A dispute, claim or allegation of sham contracting exists (refused, AU-PAY-001).")


@calculator("worker_status_indicators", WorkerStatusInput)
def worker_status_indicators(figures: Figures, inp: WorkerStatusInput) -> dict:
    """Employee-versus-contractor indicators for one engagement, for PAYG withholding and super guarantee.
    Applies the multi-factor 'totality of the relationship' test as reframed by CFMMEU v Personnel Contracting
    [2022] HCA 1 and ZG Operations v Jamsek [2022] HCA 2 (legal rights in a comprehensive written contract
    govern), TR 2023/4 (tax and, in Appendix 2, SGAA s12), and the SG extended definition in SGAA s12(3)
    (individual under a contract wholly or principally for their labour is an employee for SG even if a
    contractor at common law). Returns indicators each way, a lean (never a conclusion where facts
    conflict), the s12(3) result and next steps. Use for "is my cleaner a contractor", "do I pay super for a
    subbie with an ABN". Refuses AU-PAY-001 where there is a dispute or sham contracting allegation."""
    if inp.dispute_or_sham_allegation:
        raise Refusal("AU-PAY-001", "worker status dispute or sham contracting allegation")
    emp, con, unknown = [], [], []

    def f(val: str, yes_emp: str, yes_con: str, name: str):
        if val == "yes" and yes_emp:
            emp.append(yes_emp)
        elif val == "yes" and yes_con:
            con.append(yes_con)
        elif val == "no" and yes_emp:
            con.append(f"not: {yes_emp}")
        elif val == "no" and yes_con:
            emp.append(f"not: {yes_con}")
        elif val == "unknown":
            unknown.append(name)

    f(inp.right_to_control_how_work_done, "engager has the right to control how the work is done", "", "control")
    f(inp.must_perform_personally, "must perform the work personally (no delegation)", "", "delegation")
    f(inp.paid_by_time, "paid for time worked", "", "basis of payment (time)")
    f(inp.paid_for_result, "", "paid a price for a specified result", "basis of payment (result)")
    f(inp.provides_significant_tools_equipment, "", "supplies significant tools or equipment at own cost", "tools and equipment")
    f(inp.bears_commercial_risk, "", "bears commercial risk and cost of rectifying defects", "commercial risk")
    f(inp.builds_own_goodwill, "", "works for others and builds own goodwill", "goodwill")
    f(inp.presents_as_part_of_engager_business, "presented as part of the engager's business", "", "integration/presentation")

    if not inp.worker_is_individual:
        lean = "contractor (engaged through an entity)"
    elif emp and not con:
        lean = "leans employee"
    elif con and not emp:
        lean = "leans contractor"
    elif not emp and not con:
        lean = "insufficient facts"
    else:
        lean = "mixed: facts conflict, no conclusion"

    # SGAA s12(3): individual, contract wholly or principally for labour (TR 2023/4 App 2: paid for labour not a result,
    # must perform personally, labour is the principal part of contract value)
    if not inp.worker_is_individual:
        s12_3 = "does not apply (worker engaged through a company, trust or partnership)"
    elif inp.contract_principally_for_labour == "yes" and inp.must_perform_personally != "no" and inp.paid_for_result != "yes":
        s12_3 = "likely applies: SG employee under SGAA s12(3) even if a contractor at common law"
    elif inp.contract_principally_for_labour == "no" or inp.paid_for_result == "yes" or inp.must_perform_personally == "no":
        s12_3 = "unlikely to apply"
    else:
        s12_3 = "uncertain: need the contract value split, payment basis and delegation right"

    notes = [
        "Tax (PAYG withholding) and SG: where the terms are comprehensively in a written contract that is not a sham or varied, "
        "the legal rights and obligations in the contract decide (Personnel Contracting; Jamsek; TR 2023/4 paras 7-13). Labels and an "
        "ABN are not determinative.",
        "Fair Work Act purposes differ: from 26 Aug 2024 FW Act s15AA looks at the real substance, practical reality and true nature of "
        "the relationship, including how the contract is performed. The answer can differ between the FW Act and tax/SG.",
        "Payroll tax has its own relevant-contract rules (state law): use the state-taxes-sa skill.",
        "Contractors paid for cleaning, courier, building and other TPAR services may need a Taxable payments annual report (AU-PAY-009).",
    ]
    if inp.labelled_contractor:
        notes.append("The 'contractor' label is not relevant to the characterisation (TR 2023/4 para 13).")
    if inp.has_abn:
        notes.append("Having an ABN does not prevent the worker being an employee (TR 2023/4 para 12).")
    if inp.written_contract_comprehensive != "yes":
        notes.append("Without a comprehensive written contract, the terms are found from conduct and communications, then characterised.")
    obligations = []
    if lean == "leans employee":
        obligations = ["PAYG withholding (payg_withholding)", "super guarantee (super_guarantee)", "STP reporting on or before payday",
                       "Fair Work entitlements (award/NES)"]
    elif s12_3.startswith("likely"):
        obligations = ["super guarantee under SGAA s12(3) (super_guarantee)", "no PAYG withholding if a genuine contractor with an ABN"]
    return {"lean": lean, "employee_indicators": emp, "contractor_indicators": con, "unknown_factors": unknown,
            "sg_extended_definition_s12_3": s12_3, "obligations_if_lean_holds": obligations, "notes": notes,
            "assumptions": ["Indicators only; weigh them as a whole, not as a checklist (TR 2023/4 para 11)."],
            "warnings": ["Not a ruling. Where facts conflict or the stakes are high, get advice or an ATO private ruling."]}
