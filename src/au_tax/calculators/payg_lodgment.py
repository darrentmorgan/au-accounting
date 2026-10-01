"""PAYG instalments, lodgment due dates, failure to lodge penalty and interest charges.

Law: Taxation Administration Act 1953 (TAA) Sch 1 Div 45 (PAYG instalments; Subdiv 45-G GIC on
excessive variations), Subdiv 286-C (failure to lodge on time penalty, s 286-80), Div 284 (shortfall
penalties, awareness only), ss 8AAB and 8AAD (general interest charge) and s 280-105 (shortfall
interest charge). Every rate, threshold and date comes from data/rates/<year>.yaml and its overlays
via Figures; nothing here hard-codes a figure that changes over time.
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from au_tax.figures import Figure, FigureError, Figures
from au_tax.holidays import COMMONWEALTH, Roll, roll_due_date, roll_due_date_or_statutory
from au_tax.registry import Refusal, calculator

EntityType = Literal["individual", "trust", "company", "super_fund"]
SpecialCircumstance = Literal[
    "consolidated_head_company",
    "monthly_instalment_payer",
    "gst_instalment_combined",
    "substituted_accounting_period_nonstandard_quarters",
    "dynamic_accounting_software_method",
]

REVIEW = "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use."


# ---------------------------------------------------------------- helpers

def _r(x: float) -> float:
    return round(x + 0.0, 2)


def _roll(figures: Figures, d: date, warnings: list[str] | None = None, strict: bool = True) -> Roll:
    """Move a due date that is not a business day to the first business day after: Saturday, Sunday or a public holiday
    for the whole of any State, the ACT or the NT (TAA 1953 s 8AAZMB, Sch 1 s 388-52). Holiday data: data/holidays/au.yaml.
    strict=False (a due date secondary to the amount) returns the unrolled date with an AU-GEN-004 note when the date is
    after the holiday data, instead of refusing."""
    r = (roll_due_date if strict else roll_due_date_or_statutory)(d, COMMONWEALTH, figures)
    if warnings is not None:
        warnings.extend(w for w in r.warnings if w not in warnings)
    return r


def _year_start(income_year: str) -> int:
    return int(income_year[:4])


def _quarter_due_date(figures: Figures, start_year: int, quarter: int) -> date:
    """Unrolled due date of an instalment or BAS quarter in the income year starting 1 July start_year."""
    month = int(figures.get(f"lodgment.quarterly_due_month_q{quarter}"))
    day = int(figures.get("lodgment.quarterly_due_day"))
    year = start_year if quarter == 1 else start_year + 1  # Q1 due in October; Q2 to Q4 fall after 1 January
    return date(year, month, day)


def _reject_specials(specials: list[str]) -> None:
    if specials:
        raise Refusal("AU-PAYG-001", ", ".join(specials))


def _merge_used(figures: Figures, other: Figures, suffix: str) -> None:
    """Record figures read from another income year's file, keyed with the year so keys do not clash."""
    for k, f in other.used.items():
        figures.used[f"{k}@{suffix}"] = Figure(f"{k}@{suffix}", f.value, f.unit, f.status, f.source, f.as_at)


# ---------------------------------------------------------------- interest engine

_PENDING_LABELS = {"jan_mar_2027": (date(2027, 1, 1), date(2027, 3, 31)),
                   "apr_jun_2027": (date(2027, 4, 1), date(2027, 6, 30)),
                   "jan_mar_2028": (date(2028, 1, 1), date(2028, 3, 31)),
                   "apr_jun_2028": (date(2028, 4, 1), date(2028, 6, 30))}
INTEREST_YEARS = ("2025-26", "2026-27", "2027-28")


def _interest_periods(figures: Figures, charge: str) -> tuple[list[dict], dict[str, tuple[date, date]]]:
    """All published quarterly rate rows for the charge from the loaded year files, plus the date ranges that are
    known but unpublished (figure key -> (from, to)): a named quarter with a null value, or a whole income year whose
    quarterly series is null (2027-28 today). Rows are sorted and may span years."""
    prefix = "gic" if charge == "gic" else "sic"
    rows: list[dict] = []
    pending: dict[str, tuple[date, date]] = {}
    for year in INTEREST_YEARS:
        src = figures if year == figures.income_year else Figures(year, allow_draft=figures.allow_draft)
        block = src.data.get("penalties_interest", {})
        series = block.get(f"{prefix}_quarterly", {})
        if isinstance(series, dict) and series.get("value") is None and year > "2026-27":
            meta = src.data["meta"]  # no quarter of that year is published: the whole year is pending
            pending[f"{prefix}_quarterly@{year}"] = (meta["start"], meta["end"])
        else:
            for r in src.get(f"penalties_interest.{prefix}_quarterly"):
                rows.append({**r, "_year": year})
            if src is not figures:
                _merge_used(figures, src, year)
        for key, node in block.items():
            if key.startswith(f"{prefix}_") and key != f"{prefix}_quarterly" and isinstance(node, dict) \
                    and node.get("value") is None:
                for label, rng in _PENDING_LABELS.items():
                    if key.endswith(label):
                        pending[key] = rng
    rows.sort(key=lambda r: r["from"])
    return rows, pending


def _compound(amount: float, start: date, end: date, rows: list[dict],
              pending: dict[str, tuple[date, date]], charge: str) -> tuple[float, list[dict]]:
    """Daily-compounded interest from start (inclusive) to end (exclusive: interest runs for each day on which
    the amount is still unpaid at the end of the day, so the day of payment carries none).
    Returns (interest, per-quarter breakdown). Refuses if a day falls in an unpublished or unloaded quarter."""
    balance = amount
    breakdown: list[dict] = []
    d = start
    while d < end:
        row = next((r for r in rows if r["from"] <= d <= r["to"]), None)
        if row is None:
            for key, (lo, hi) in pending.items():
                if lo <= d <= hi:
                    raise Refusal("AU-PAYG-002", f"{charge.upper()} rate for {lo} to {hi} is not yet published "
                                  f"(figure {key} has no value)")
            raise Refusal("AU-PAYG-002", f"no {charge.upper()} rate loaded for {d.isoformat()}; loaded periods run "
                          f"{rows[0]['from']} to {rows[-1]['to']} (published quarters only)")
        seg_end = min(end, row["to"] + timedelta(days=1))
        n = (seg_end - d).days
        growth = (1 + row["daily_rate"]) ** n
        before = balance
        balance *= growth
        breakdown.append({"from": d.isoformat(), "to_exclusive": seg_end.isoformat(), "days": n,
                          "annual_rate": row["rate"], "daily_rate": row["daily_rate"],
                          "interest": _r(balance - before)})
        d = seg_end
    return balance - amount, breakdown


# ---------------------------------------------------------------- payg_entry_check

class PaygEntryInput(BaseModel):
    """Would the ATO automatically enter this taxpayer into PAYG instalments, or can they enter voluntarily?"""

    entity_type: EntityType = Field(description="individual (incl. sole trader), trust, company or super_fund.")
    instalment_income: float = Field(ge=0, description="Instalment income (gross business and investment income excluding GST and capital gains) in the latest tax return.")
    tax_payable_on_assessment: float = Field(0, ge=0, description="Tax payable on the latest notice of assessment (individuals and trusts).")
    notional_tax: float = Field(0, ge=0, description="Estimated (notional) tax worked out by the ATO from the latest return.")
    is_consolidated_head_company: bool = False


@calculator("payg_entry_check", PaygEntryInput)
def payg_entry_check(figures: Figures, inp: PaygEntryInput) -> dict:
    """Tests the automatic entry thresholds for PAYG instalments from the latest tax return. Individuals and
    trusts enter automatically only if ALL of: instalment income, tax payable on the latest assessment and
    notional tax are at or above their minimums. Companies and super funds enter if ANY of: instalment income at
    or above the company minimum, notional tax at or above the notional tax minimum, or head company of a
    consolidated group (as the ATO states it). Returns the test results and the figures used. Use for "do I
    need to pay PAYG instalments", "will I be put into instalments", "voluntary PAYG instalments". Below the
    thresholds the taxpayer may still enter voluntarily."""
    inc_min = figures.get("payg_instalments.entry_instalment_income_min")
    tax_min = figures.get("payg_instalments.entry_last_assessed_tax_min")
    notional_min = figures.get("payg_instalments.entry_notional_tax_min")
    tests: dict[str, bool]
    if inp.entity_type in ("individual", "trust"):
        tests = {
            "instalment_income_at_or_above_minimum": inp.instalment_income >= inc_min,
            "tax_payable_on_assessment_at_or_above_minimum": inp.tax_payable_on_assessment >= tax_min,
            "notional_tax_at_or_above_minimum": inp.notional_tax >= notional_min,
        }
        entered = all(tests.values())
        rule = "all three tests must be met"
    else:
        co_min = figures.get("payg_instalments.entry_company_instalment_income_min")
        tests = {
            "instalment_income_at_or_above_company_minimum": inp.instalment_income >= co_min,
            "notional_tax_at_or_above_minimum": inp.notional_tax >= notional_min,
            "head_company_of_consolidated_group": inp.is_consolidated_head_company,
        }
        entered = any(tests.values())
        rule = "any one test is enough"
    assumptions = ["Based on the latest tax return and notice of assessment; the ATO decides and notifies entry by letter or statement."]
    warnings = []
    if not entered:
        warnings.append("Below the automatic thresholds: voluntary entry is still possible (myGov, agent or the ATO).")
    if inp.entity_type in ("company", "super_fund"):
        warnings.append("Company and super fund entry follows the ATO's published test as stated; confirm against the ATO letter or activity statement.")
    return {"entity_type": inp.entity_type, "automatic_entry": entered, "rule": rule, "tests": tests,
            "assumptions": assumptions, "warnings": warnings, "review": REVIEW}


# ---------------------------------------------------------------- payg_instalment

class PaygInstalmentInput(BaseModel):
    """One PAYG instalment for one quarter (or the annual or two-instalment equivalent)."""

    method: Literal["amount", "rate", "varied_amount", "varied_rate"] = Field(
        description="amount = pay the ATO instalment amount (GDP-adjusted notional tax, T7); rate = instalment income x "
        "instalment rate (T1 x T2 = T11); varied_amount = the T9 amount when varying the amount for a quarter; "
        "varied_rate = the new varied rate at T3 = estimated tax / estimated instalment income.")
    entity_type: EntityType = "individual"
    frequency: Literal["quarterly", "annual", "two_instalments"] = Field(
        "quarterly", description="Amount method only. annual = one payment (T5); two_instalments = primary producers and "
        "special professionals, April (quarter 3) and July (quarter 4).")
    quarter: int = Field(1, ge=1, le=4, description="Instalment quarter of the income year: 1 Jul-Sep, 2 Oct-Dec, 3 Jan-Mar, 4 Apr-Jun.")
    notional_tax: float | None = Field(None, ge=0, description="method=amount: estimated (notional) tax the ATO gave for the year (before the GDP adjustment).")
    instalment_income: float | None = Field(None, ge=0, description="method=rate: instalment income for the quarter (T1), excluding GST. method=varied_rate: ESTIMATED instalment income for the whole year.")
    instalment_rate_percent: float | None = Field(None, ge=0, description="method=rate: instalment rate at T2 (or T3 if varied) as a percentage, e.g. 11 for 11%.")
    estimated_tax: float | None = Field(None, ge=0, description="method=varied_amount or varied_rate: your estimate of the tax on instalment income for the whole income year (T8).")
    earlier_instalments_paid: float = Field(0, ge=0, description="method=varied_amount: total instalments (5A) already reported for earlier quarters of this income year.")
    credits_claimed_earlier: float = Field(0, ge=0, description="method=varied_amount: credits (5B) already claimed in earlier quarters.")
    sap_income_year_start: date | None = Field(None, description="Substituted accounting period taxpayers: the date the income year began. 1 Jan to 1 Mar 2026 starts keep the prior-year GDP adjustment in 2026-27.")
    special_circumstances: list[SpecialCircumstance] = Field(default_factory=list, description="Any listed regime present; each stops the calculation (AU-PAYG-001).")

    @model_validator(mode="after")
    def _needs(self):
        need = {"amount": ["notional_tax"], "rate": ["instalment_income", "instalment_rate_percent"],
                "varied_amount": ["estimated_tax"], "varied_rate": ["estimated_tax", "instalment_income"]}[self.method]
        missing = [n for n in need if getattr(self, n) is None]
        if missing:
            raise ValueError(f"method {self.method} needs {', '.join(missing)}")
        if self.frequency == "two_instalments" and self.quarter not in (3, 4):
            raise ValueError("two_instalments payers pay in quarter 3 (April) and quarter 4 (July)")
        return self


def _gdp_factor(figures: Figures, sap_start: date | None, warnings: list[str]) -> float:
    factor = figures.get("payg_instalments.gdp_adjustment")
    if sap_start is not None and figures.income_year == "2026-27" and date(2026, 1, 1) <= sap_start <= date(2026, 3, 1):
        prior = Figures("2025-26", allow_draft=figures.allow_draft)
        factor = prior.get("payg_instalments.gdp_adjustment")
        _merge_used(figures, prior, "2025-26")
        warnings.append("Substituted accounting period year that began 1 Jan to 1 Mar 2026: the prior-year GDP adjustment continues (ATO software developers page).")
    return factor


@calculator("payg_instalment", PaygInstalmentInput)
def payg_instalment(figures: Figures, inp: PaygInstalmentInput) -> dict:
    """Works out a PAYG instalment (TAA Sch 1 Div 45). method=amount: quarterly instalment = notional tax x
    (1 + GDP adjustment for the income year) / 4 (annual payers pay the notional tax at T5 with no GDP
    adjustment; two-instalment payers pay 75% then the rest). method=rate: instalment income (T1) x instalment
    rate (T2 or T3) = T11 / 5A, also returned in whole dollars as the ATO example enters it. method=varied_amount:
    the varied amount T9 for quarter q = estimated tax x q/4 less instalments already reported plus credits already
    claimed (a negative result is nil at T9 and a credit at 5B). method=varied_rate: new varied rate T3 = estimated
    tax / estimated instalment income. The GDP adjustment (higher for 2026-27 than 2025-26) is read from the rates
    file for the income year. Returns the amount, the GDP factor, the due date and the BAS labels. Use for "what is my
    quarterly PAYG instalment", "how do I vary my instalments". Refuses AU-PAYG-001 for consolidated groups, monthly
    payers, GST-combined instalments, substituted accounting periods with non-standard quarters and the dynamic
    software method."""
    _reject_specials(inp.special_circumstances)
    assumptions: list[str] = []
    warnings: list[str] = []
    res: dict = {"method": inp.method, "quarter": inp.quarter, "frequency": inp.frequency}
    start_year = _year_start(figures.income_year)
    quarters = int(figures.get("payg_instalments.quarters_per_year"))
    standard_year = inp.sap_income_year_start is None
    if inp.method == "amount":
        gdp = _gdp_factor(figures, inp.sap_income_year_start, warnings)
        adjusted = inp.notional_tax * (1 + gdp)
        if inp.frequency == "quarterly":
            amt = adjusted / quarters
            res["gdp_adjusted_notional_tax"] = _r(adjusted)
            res["labels"] = {"T7": _r(amt), "5A": _r(amt)}
            res["gdp_adjustment_applied"] = gdp
            assumptions.append("Quarterly instalment = GDP-adjusted notional tax divided by the number of quarters.")
        elif inp.frequency == "annual":
            amt = inp.notional_tax
            res["labels"] = {"T5": _r(amt)}
            assumptions.append("Annual payers: the ATO states the GDP adjustment does not affect annual instalments, so the notional tax is used unadjusted. Confirm against label T5 on the instalment notice.")
            warnings.append("Annual instalment eligibility needs notional tax below the annual option limit (figure payg_instalments.annual_option_notional_tax_max).")
            limit = figures.get("payg_instalments.annual_option_notional_tax_max")
            res["annual_option_eligible_on_notional_tax"] = inp.notional_tax < limit
        else:
            share = figures.get("payg_instalments.two_instalment_first_share")
            yearly = adjusted
            amt = yearly * share if inp.quarter == 3 else yearly * (1 - share)
            res["gdp_adjusted_notional_tax"] = _r(adjusted)
            res["gdp_adjustment_applied"] = gdp
            res["labels"] = {"T7": _r(amt), "5A": _r(amt)}
            assumptions.append("Two-instalment payers pay the first share of the yearly GDP-adjusted amount by 28 April and the rest by 28 July.")
        res["instalment_amount"] = _r(amt)
        res["instalment_amount_whole_dollars"] = math.floor(amt + 1e-9)
    elif inp.method == "rate":
        rate = inp.instalment_rate_percent / 100
        amt = inp.instalment_income * rate
        res["instalment_amount"] = _r(amt)
        res["instalment_amount_whole_dollars"] = math.floor(amt + 1e-9)
        res["labels"] = {"T1": _r(inp.instalment_income), "T2": inp.instalment_rate_percent, "T11": _r(amt), "5A": _r(amt)}
        assumptions.append("The GDP adjustment does not apply to the rate method. The ATO's worked example enters the whole-dollar amount (cents dropped).")
        reasonable = {"individual": "reasonable_rate_individual_trust", "trust": "reasonable_rate_individual_trust",
                      "super_fund": "reasonable_rate_super_fund", "company": "reasonable_rate_corporate"}[inp.entity_type]
        cap = figures.get(f"payg_instalments.{reasonable}")
        if rate > cap:
            warnings.append("The rate entered is above the reasonable instalment rate for this entity type; the ATO caps the rate it issues, so recheck T2.")
            res["reasonable_rate_percent"] = _r(cap * 100)
    elif inp.method == "varied_amount":
        target = inp.estimated_tax * inp.quarter / quarters
        t9_raw = target - inp.earlier_instalments_paid + inp.credits_claimed_earlier
        t9 = max(0.0, t9_raw)
        res["target_cumulative"] = _r(target)
        res["labels"] = {"T8": _r(inp.estimated_tax), "T9": _r(t9), "5A": _r(t9)}
        res["instalment_amount"] = _r(t9)
        if t9_raw < 0:
            res["credit_available_5B"] = _r(-t9_raw)
            res["labels"]["5B"] = _r(-t9_raw)
            assumptions.append("Negative varied amount: enter nil at T9 and claim the credit at 5B, or leave the credit to the tax return.")
        assumptions.append("Varying before the due date and before the tax return is lodged; a reason code is required at T4.")
        warnings.append("Underestimating can trigger GIC when the varied instalments fall below the safe harbour share of the benchmark tax; use payg_variation_check.")
    else:  # varied_rate
        if inp.instalment_income == 0:
            new_rate = 0.0
        else:
            new_rate = inp.estimated_tax / inp.instalment_income * 100
        truncated = math.floor(new_rate * 100 + 1e-9) / 100
        res["varied_rate_percent"] = truncated
        res["varied_rate_percent_exact"] = round(new_rate, 4)
        res["labels"] = {"T3": truncated}
        assumptions.append("Varied rate = estimated tax for the year / estimated instalment income for the year, as a percentage. Shown with the third decimal dropped, as in the ATO's worked example; the exact value is also returned.")
        if inp.instalment_rate_percent is not None:
            res["credit_note"] = "If the varied rate is below the rate used earlier, a credit for earlier quarters can be claimed at 5B (ATO credit table)."
    if inp.method in ("amount", "rate", "varied_amount") and standard_year and inp.frequency != "annual":
        due = _quarter_due_date(figures, start_year, inp.quarter)
        rolled = _roll(figures, due, warnings, strict=False)
        res["due_date"] = rolled.due.isoformat()
        res["due_date_statutory"] = due.isoformat()
        res["business_day_roll"] = rolled.as_dict()
        if rolled.out_of_range:
            res["field_refusals"] = [{"field": "due_date", **rolled.out_of_range}]
        assumptions.append("Due date is the standard quarter date moved to the first business day after if it is a Saturday, Sunday or a public holiday for the whole of any State, the ACT or the NT (TAA 1953 s 8AAZMB); the online or agent concessions are not applied (instalment notices get no concession).")
    if inp.frequency == "annual" and inp.method == "amount":
        warnings.append("Annual instalment due dates are on the instalment notice; agent clients pay by 21 October.")
    return {**res, "assumptions": assumptions, "warnings": warnings, "review": REVIEW}


# ---------------------------------------------------------------- payg_variation_check

class VariationCheckInput(BaseModel):
    """Check a varied PAYG instalment against the safe harbour share of the benchmark tax and estimate GIC exposure."""

    method: Literal["amount", "rate"] = "amount"
    benchmark_tax: float | None = Field(None, ge=0, description="method=amount: the tax on instalment income for the whole income year (per the assessment, or a best estimate). This is the benchmark the varied estimate is tested against.")
    estimated_tax: float | None = Field(None, ge=0, description="method=amount: the estimated tax entered at T8 when varying.")
    instalments_paid: list[float] | None = Field(None, description="method=amount: instalments actually paid for each quarter, in order (up to four values).")
    varied_rate_percent: float | None = Field(None, ge=0, description="method=rate: the varied rate used at T3, as a percentage.")
    benchmark_rate_percent: float | None = Field(None, ge=0, description="method=rate: the actual rate for the year = tax / instalment income, as a percentage.")
    assessment_due_date: date | None = Field(None, description="Due date for payment of the income tax assessment; with it the tool estimates GIC from each quarter's due date. Omit to get the shortfall only.")
    special_circumstances: list[SpecialCircumstance] = Field(default_factory=list)

    @model_validator(mode="after")
    def _needs(self):
        if self.method == "amount":
            if self.benchmark_tax is None or self.estimated_tax is None or not self.instalments_paid:
                raise ValueError("method amount needs benchmark_tax, estimated_tax and instalments_paid")
            if len(self.instalments_paid) > 4:
                raise ValueError("instalments_paid holds at most four quarters")
        else:
            if self.varied_rate_percent is None or self.benchmark_rate_percent is None:
                raise ValueError("method rate needs varied_rate_percent and benchmark_rate_percent")
        return self


@calculator("payg_variation_check", VariationCheckInput)
def payg_variation_check(figures: Figures, inp: VariationCheckInput) -> dict:
    """Tests whether a varied PAYG instalment meets the 85% safe harbour (TAA Sch 1 Subdiv 45-G). method=amount:
    compares the estimated tax you entered at T8 and the instalments actually paid with the benchmark tax (the
    tax on instalment income for the year); reports whether each is at least 85% of the benchmark, the tax
    shortfall the assessment will collect, per-quarter instalment shortfalls against 25% of the benchmark each
    quarter, and, if assessment_due_date is given, indicative GIC on those shortfalls from each quarter's due date
    (daily compounding). method=rate: compares the varied rate with the benchmark rate (test only). The GIC applies only if the 85% test fails;
    the Commissioner may remit it (s 45-240) and must notify it (14 days to pay). Indicative only: the
    Commissioner's benchmark (Subdiv 45-K) and later-quarter top-up reductions (s 45-233) are not modelled.
    Use for "will I be charged interest if I vary my instalments", "did I vary too low"."""
    _reject_specials(inp.special_circumstances)
    ratio = figures.get("payg_instalments.variation_safe_harbour_ratio")
    assumptions = ["The benchmark you supply stands in for the Commissioner's benchmark tax or rate (TAA Sch 1 Subdiv 45-K). The ATO's own figure governs."]
    warnings: list[str] = ["GIC on a variation is notified by the ATO and payable within 14 days of notice; the Commissioner may remit it where special circumstances make that fair and reasonable (s 45-240). Remission requests go to a registered tax agent (AU-PAYG-003)."]
    res: dict = {"method": inp.method, "safe_harbour_ratio": ratio}
    if inp.method == "rate":
        threshold = inp.benchmark_rate_percent * ratio
        meets = inp.varied_rate_percent >= threshold - 1e-9
        res.update({"safe_harbour_rate_percent": _r(threshold), "meets_safe_harbour": meets,
                    "gic_applies": not meets})
        if not meets:
            warnings.append("GIC is charged on the shortfall in each quarter's instalment from its due date to the assessment due date (rate discrepancy x instalment income, plus a credit adjustment, s 45-230). The dollar amount is not modelled for the rate method.")
        return {**res, "assumptions": assumptions, "warnings": warnings, "review": REVIEW}

    bench = inp.benchmark_tax
    est_ok = inp.estimated_tax >= bench * ratio - 1e-9
    paid_total = sum(inp.instalments_paid)
    paid_ok = paid_total >= bench * ratio - 1e-9
    res.update({
        "benchmark_tax": _r(bench),
        "safe_harbour_amount": _r(bench * ratio),
        "estimated_tax_meets_safe_harbour": est_ok,
        "instalments_paid_total": _r(paid_total),
        "instalments_paid_meet_safe_harbour": paid_ok,
        "estimated_tax_share_of_benchmark": _r(inp.estimated_tax / bench) if bench else None,
        "instalments_paid_share_of_benchmark": _r(paid_total / bench) if bench else None,
        "tax_shortfall_at_assessment": _r(max(0.0, bench - paid_total)),
        "gic_applies": not est_ok or not paid_ok,
    })
    per_q = bench / int(figures.get("payg_instalments.quarters_per_year"))
    shortfalls = []
    for i, paid in enumerate(inp.instalments_paid, start=1):
        shortfalls.append({"quarter": i, "acceptable_instalment": _r(per_q), "paid": _r(paid),
                           "shortfall": _r(max(0.0, per_q - paid))})
    res["quarter_shortfalls"] = shortfalls
    if not res["gic_applies"]:
        res["indicative_gic"] = 0.0
        return {**res, "assumptions": assumptions, "warnings": warnings, "review": REVIEW}
    if inp.assessment_due_date is not None:
        rows, pending = _interest_periods(figures, "gic")
        start_year = _year_start(figures.income_year)
        total = 0.0
        detail = []
        for s in shortfalls:
            if s["shortfall"] <= 0:
                continue
            due = _quarter_due_date(figures, start_year, s["quarter"])
            if inp.assessment_due_date <= due:
                continue
            gic, _ = _compound(s["shortfall"], due, inp.assessment_due_date, rows, pending, "gic")
            total += gic
            detail.append({"quarter": s["quarter"], "from": due.isoformat(), "amount": s["shortfall"], "gic": _r(gic)})
        res["indicative_gic"] = _r(total)
        res["indicative_gic_detail"] = detail
        assumptions.append("Indicative GIC runs from each quarter's statutory due date to the assessment due date on that quarter's shortfall, daily compounding; later-quarter top-up reductions (s 45-233) would lower it, so treat as an upper bound.")
    else:
        warnings.append("Give assessment_due_date to get an indicative GIC figure.")
    if not est_ok:
        assumptions.append("The estimate used to vary was below the safe harbour share of the benchmark, which is the trigger for GIC under ss 45-232 and 45-235.")
    return {**res, "assumptions": assumptions, "warnings": warnings, "review": REVIEW}


# ---------------------------------------------------------------- lodgment_due_dates

class DueDatesInput(BaseModel):
    """Due dates for the common recurring obligations in an income year."""

    obligation: Literal["bas_quarter", "payg_instalment_quarter", "individual_return_self_lodged", "tpar", "stp_finalisation"] = Field(
        description="bas_quarter = quarterly BAS (28th of the month after the quarter, Q2 28 February); "
        "payg_instalment_quarter = quarterly instalment notice; individual_return_self_lodged = tax return lodged by the taxpayer "
        "for the income year; tpar = taxable payments annual report; stp_finalisation = STP finalisation declaration.")
    quarter: int | None = Field(None, ge=1, le=4, description="Quarter 1 to 4 for the two quarterly obligations, within the income year in the envelope.")
    lodges_online_themselves: bool = Field(False, description="bas_quarter only: lodged online by the business itself (2 weeks extra for quarters 1, 3 and 4). Registered agent lodgment program dates are separate: see the skill reference.")

    @model_validator(mode="after")
    def _q(self):
        if self.obligation in ("bas_quarter", "payg_instalment_quarter") and self.quarter is None:
            raise ValueError("quarter is required for quarterly obligations")
        return self


@calculator("lodgment_due_dates", DueDatesInput)
def lodgment_due_dates(figures: Figures, inp: DueDatesInput) -> dict:
    """Gives the due date for a recurring lodgment obligation, moving a date that is a Saturday, Sunday or public holiday
    (whole of any State, the ACT or the NT) to the first business day after (TAA 1953 s 8AAZMB, Sch 1 s 388-52).
    For income_year Y: bas_quarter and payg_instalment_quarter give the due date of quarter 1 to 4 falling in Y (quarter 2
    is 28 February; the online concession adds 2 weeks for quarters 1, 3 and 4 of a BAS and never applies to quarter 2
    or instalment notices); individual_return_self_lodged gives the self-lodger due date for the RETURN FOR income
    year Y (31 October after year end) and the payment date if a tax bill results; tpar gives the 28 August after
    year Y; stp_finalisation gives 14 July after year Y. Tax agent lodgment program dates are not computed here
    (they are ATO-published per year); the skill points to them. Dates outside the holiday data range are refused (AU-GEN-004)."""
    start_year = _year_start(figures.income_year)
    assumptions = ["A due date that is not a business day moves to the first business day after (TAA 1953 s 8AAZMB for payments, Sch 1 s 388-52 for approved forms): "
                   "a Saturday, a Sunday, or a public holiday for the whole of any State, the ACT or the NT, wherever the taxpayer is."]
    warnings: list[str] = []
    res: dict = {"obligation": inp.obligation}
    if inp.obligation in ("bas_quarter", "payg_instalment_quarter"):
        due = _quarter_due_date(figures, start_year, inp.quarter)
        rolled = _roll(figures, due, warnings)
        res.update({"quarter": inp.quarter, "statutory_due_date": due.isoformat(), "due_date": rolled.due.isoformat(),
                    "business_day_roll": rolled.as_dict()})
        if inp.obligation == "bas_quarter" and inp.lodges_online_themselves:
            if inp.quarter == 2:
                res["concession_applies"] = False
                warnings.append("No online concession for quarter 2: its February due date already includes an extension.")
            else:
                days = int(figures.get("lodgment.online_concession_days"))
                extended = _roll(figures, due + timedelta(days=days), warnings)
                res["concession_applies"] = True
                res["due_date_with_online_concession"] = extended.due.isoformat()
                res["online_concession_business_day_roll"] = extended.as_dict()
                assumptions.append("Online concession taken as the statutory date plus the concession days, moved to a business day; the ATO wording is 'up to 2 weeks', so the date on the BAS itself governs.")
        if inp.obligation == "payg_instalment_quarter":
            warnings.append("Instalment notices (forms R, S and T) get no extra time; pay by the due date. Monthly GST reporters pay on the 21st.")
        if inp.obligation == "bas_quarter":
            warnings.append("Clients of a registered agent may have lodgment program dates; use the agent's date.")
    elif inp.obligation == "individual_return_self_lodged":
        due = date(start_year + 1, int(figures.get("lodgment.individual_return_due_month")),
                   int(figures.get("lodgment.individual_return_due_day")))
        pay = date(start_year + 1, int(figures.get("lodgment.individual_payment_due_month")),
                   int(figures.get("lodgment.individual_payment_due_day")))
        rolled, pay_rolled = _roll(figures, due, warnings), _roll(figures, pay, warnings)
        res.update({"return_income_year": figures.income_year, "statutory_due_date": due.isoformat(),
                    "due_date": rolled.due.isoformat(), "business_day_roll": rolled.as_dict(),
                    "payment_due_statutory": pay.isoformat(),
                    "payment_due_if_lodged_by_due_date": pay_rolled.due.isoformat(),
                    "payment_business_day_roll": pay_rolled.as_dict()})
        warnings.append("Registered tax agent clients may have a later lodgment program date if the agent is engaged before the self-lodger due date; taxpayers with earlier returns outstanding lose it.")
        warnings.append("If the assessment issues after the self-lodger due date, payment is due 21 days after the assessment issues.")
    elif inp.obligation == "tpar":
        due = date(start_year + 1, int(figures.get("lodgment.tpar_due_month")), int(figures.get("lodgment.tpar_due_day")))
        rolled = _roll(figures, due, warnings)
        res.update({"report_income_year": figures.income_year, "statutory_due_date": due.isoformat(), "due_date": rolled.due.isoformat(),
                    "business_day_roll": rolled.as_dict()})
    else:
        due = date(start_year + 1, int(figures.get("lodgment.stp_finalisation_due_month")),
                   int(figures.get("lodgment.stp_finalisation_due_day")))
        rolled = _roll(figures, due, warnings)
        res.update({"report_income_year": figures.income_year, "statutory_due_date": due.isoformat(), "due_date": rolled.due.isoformat(),
                    "business_day_roll": rolled.as_dict()})
        warnings.append("Closely held payees are finalised later (30 September, or the payee's return due date for small employers with only closely held payees).")
    return {**res, "assumptions": assumptions, "warnings": warnings, "review": REVIEW}


# ---------------------------------------------------------------- failure_to_lodge_penalty

class FtlInput(BaseModel):
    """Failure to lodge on time penalty for one overdue document."""

    days_late: int = Field(ge=0, description="Days the document is overdue (lodgment date or today minus the due date). 0 = on time.")
    due_date: date = Field(description="The date the document was due (the date of the failure). Sets the penalty unit and the entity size test date.")
    entity_size: Literal["small", "medium", "large", "sge"] = Field(
        "small", description="Size at the time the document was due. small = individuals and small withholders (base amount); "
        "medium = assessable income or GST turnover from 1m to under 20m, or medium withholder (x2); large = 20m or more or large "
        "withholder (x5); sge = significant global entity (x500).")
    lodgment_result: Literal["payable", "refund_or_nil", "unknown"] = Field("unknown", description="Outcome of the late document; the ATO generally does not penalise a late return or activity statement that results in a refund or nil, with exceptions.")
    agent_safe_harbour_possible: bool = Field(False, description="A registered tax or BAS agent was engaged and given all information in time (safe harbour).")


def _penalty_unit(figures: Figures, due: date) -> tuple[float, Figures]:
    """Penalty unit in force on the date of the failure, taken from the rates file of the income year the due date
    falls in (date-effective). A due date before 1 Jul 2025, or in a year with no rates file, refuses AU-PAYG-002: the
    unit is never taken from another year's file."""
    year = f"{due.year if due.month >= 7 else due.year - 1}-{str((due.year if due.month >= 7 else due.year - 1) + 1)[-2:]}"
    if due < date(2025, 7, 1):
        raise Refusal("AU-PAYG-002", f"penalty unit for {due.isoformat()} is not loaded (loaded from 1 Jul 2025)")
    try:
        src = figures if figures.income_year == year else Figures(year, allow_draft=figures.allow_draft)
    except FigureError as e:
        raise Refusal("AU-PAYG-002", f"penalty unit for {due.isoformat()} is not loaded: {e}") from e
    return src.get("penalties_interest.penalty_unit"), src


@calculator("failure_to_lodge_penalty", FtlInput)
def failure_to_lodge_penalty(figures: Figures, inp: FtlInput) -> dict:
    """Failure to lodge on time (FTL) penalty, TAA Sch 1 Subdiv 286-C s 286-80: one base penalty unit for each 28 days
    or part thereof the document is late, capped at 5 base units, multiplied by 2 (medium), 5 (large) or 500 (significant
    global entity). The penalty unit is the amount in force on the date the document was due (from 1 Jul 2026 it is
    higher than before), not the date it was lodged or assessed. Inputs: days_late, due_date, entity_size. Returns
    periods, base units, multiplier, penalty unit, penalty, and flags for the refund/nil practice, agent safe
    harbour and remission. Use for "what is the late lodgment penalty", "penalty for lodging my BAS 60 days late".
    Does not decide remission (AU-PAYG-003) or disputes (AU-PAYG-004)."""
    period_days = int(figures.get("penalties_interest.ftl_period_days"))
    max_units = int(figures.get("penalties_interest.ftl_max_base_units"))
    per_period = figures.get("penalties_interest.failure_to_lodge_units_per_28_days_small")
    mult = {"small": 1, "medium": figures.get("penalties_interest.ftl_multiplier_medium"),
            "large": figures.get("penalties_interest.ftl_multiplier_large"),
            "sge": figures.get("penalties_interest.ftl_multiplier_sge")}[inp.entity_size]
    unit, unit_src = _penalty_unit(figures, inp.due_date)
    if unit_src is not figures:
        _merge_used(figures, unit_src, unit_src.income_year)
    periods = math.ceil(inp.days_late / period_days) if inp.days_late > 0 else 0
    base_units = min(periods * per_period, max_units)
    total_units = base_units * mult
    penalty = total_units * unit
    warnings: list[str] = []
    assumptions = [f"Penalty unit is the amount in force on the due date ({inp.due_date.isoformat()}).",
                   "Entity size is the size at the time the document was due; the tool takes it as given."]
    if inp.lodgment_result == "refund_or_nil":
        warnings.append("The ATO generally does not issue an FTL penalty notice for a late return or activity statement that results in a refund or nil, unless a penalty was applied before lodgment, it is a third-party data report such as a TPAR, or the entity is a large withholder.")
    if inp.agent_safe_harbour_possible:
        warnings.append("Safe harbour may cancel the penalty if all information reached the registered agent in time and the agent was not reckless or intentionally disregarding the law.")
    if penalty > 0:
        warnings.append("The ATO can remit all or part of an FTL penalty on request once the document is lodged; a remission request with contested facts goes to a registered tax agent (AU-PAYG-003).")
    return {"days_late": inp.days_late, "due_date": inp.due_date.isoformat(), "entity_size": inp.entity_size,
            "periods_of_28_days": periods, "base_units": base_units, "multiplier": mult,
            "penalty_units": total_units, "penalty_unit_amount": unit, "penalty": _r(penalty),
            "assumptions": assumptions, "warnings": warnings, "review": REVIEW}


# ---------------------------------------------------------------- general_interest_charge

class GicInput(BaseModel):
    """Interest on an unpaid amount over a date range, daily compounding at the ATO quarterly rates."""

    amount: float = Field(gt=0, description="Unpaid tax or other amount in AUD at the start of the period.")
    from_date: date = Field(description="First day interest runs: the day the amount was due (the beginning of the due day). For SIC, the day the tax would have been due.")
    to_date: date = Field(description="Payment date (or the date to calculate to). Interest runs for each day the amount is unpaid at the end of the day, so this day carries none.")
    charge: Literal["gic", "sic"] = Field("gic", description="gic = general interest charge (late payment, underestimated instalments, late return); sic = shortfall interest charge (amended assessments).")

    @model_validator(mode="after")
    def _order(self):
        if self.to_date < self.from_date:
            raise ValueError("to_date must not be before from_date")
        return self


@calculator("general_interest_charge", GicInput)
def general_interest_charge(figures: Figures, inp: GicInput) -> dict:
    """General interest charge (TAA s 8AAB, s 8AAD) or shortfall interest charge (s 280-105) on an amount between two
    dates, compounded daily using each quarter's published ATO daily rate (loaded from 1 Jul 2025 to the last published
    quarter). The period runs from from_date (the due date) up to but not including to_date (the payment date). Returns
    days, interest, total and a per-quarter breakdown. Refuses AU-PAYG-002 if any day falls in a quarter whose rate is
    not yet published or not loaded, rather than guessing. GIC and SIC incurred from 1 Jul 2025 are not deductible. Use
    for "how much GIC on $X owed since <date>", "interest on my ATO debt", "GIC on the underpaid instalment"."""
    rows, pending = _interest_periods(figures, inp.charge)
    interest, breakdown = _compound(inp.amount, inp.from_date, inp.to_date, rows, pending, inp.charge)
    days = (inp.to_date - inp.from_date).days
    return {"charge": inp.charge, "amount": _r(inp.amount), "from_date": inp.from_date.isoformat(),
            "to_date": inp.to_date.isoformat(), "days": days, "interest": _r(interest),
            "total_with_interest": _r(inp.amount + interest), "breakdown": breakdown,
            "assumptions": ["Daily compounding on the unpaid balance including accrued interest, using each quarter's daily rate.",
                            "Interest counted for each day from the due date up to the day before payment; the ATO's own statement may differ by a day or by rounding.",
                            "GIC and SIC incurred from 1 Jul 2025 are not tax deductible."],
            "warnings": (["Interest continues to accrue daily until the amount is paid, including under a payment plan."]
                         if inp.charge == "gic" else []),
            "review": REVIEW}
