"""Business days and public holidays: the one place every due-date calculator rolls a date.

Data: data/holidays/au.yaml (per-date holiday rows, two regimes, an unresolved list and the ATO's own
first-business-day table). Rule and jurisdiction analysis: docs/research/due-dates-public-holidays.md.

Two regimes (the `regimes:` block of the data file):
  commonwealth_tax  everything the ATO administers. Not a business day: Saturday, Sunday, or a day that is a
                    public holiday for the whole of ANY State, the ACT or the NT (all eight pooled; the
                    taxpayer's own location is irrelevant). Part-day holidays (Christmas Eve, New Year's Eve)
                    count, following the ATO table. Law: TAA 1953 s 8AAZMB (tax debts), Sch 1 s 388-52 (approved
                    forms), business day defined in s 8AAZMB(2), ITAA 1997 s 995-1(1), SGAA 1992 s 6(1).
  sa_state_tax      RevenueSA. Not a business day: Saturday, Sunday, or a public holiday under the Public
                    Holidays Act 2023 (SA). Part-day holidays do not count. Law: Legislation Interpretation Act
                    2021 (SA) s 44(2); Public Holidays Act 2023 (SA) s 8.

Behaviour the calculators rely on:
- A date outside the data range is refused (AU-GEN-004); the loader never falls back to weekends only. Refuse
  (roll_due_date) where the due date is the answer being asked for. Where the due date is a secondary output beside
  a main result (a tax amount, a scope check), roll_due_date_or_statutory returns the statutory date unrolled with
  rolled False, a warning and a per-field AU-GEN-004 note, so the main result is still given.
- A day the walk touches that may be a holiday but is not yet declared (the `unresolved` list) is refused like
  an unverified figure: AU-GEN-001 when candidate dates exist (a draft with allow_draft carries both dates),
  AU-GEN-003 when no date exists at all.
- Where the ATO's printed first business day differs from the definition (one row today), the statutory date is
  returned and a warning quotes the ATO's printed date.
- GIC is not rolled (s 8AAZMB(2)); only the tax debt due date is.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from functools import cache
from pathlib import Path

import yaml

from au_tax.figures import UNPUBLISHED, UNVERIFIED, Figure, FigureError, Figures
from au_tax.registry import Refusal, refusal_catalogue

HOLIDAYS_FILE = Path(__file__).resolve().parents[2] / "data" / "holidays" / "au.yaml"
COMMONWEALTH = "commonwealth_tax"
SA_STATE = "sa_state_tax"

RULE_TEXT = {
    COMMONWEALTH: ("TAA 1953 s 8AAZMB (tax debts) and Sch 1 s 388-52 (approved forms): a due date that is not a business day "
                   "moves to the first business day after; business day as defined in s 8AAZMB(2), ITAA 1997 s 995-1(1) and "
                   "SGAA 1992 s 6(1) (not a Saturday, Sunday or a public holiday for the whole of any State, the ACT or the NT)"),
    SA_STATE: ("Legislation Interpretation Act 2021 (SA) s 44(2) and Public Holidays Act 2023 (SA) s 8: a due date that is not a "
               "business day moves to the next business day (Saturday, Sunday or an SA public holiday; part-day holidays excluded); "
               "RevenueSA accepts lodgement and payment on the next business day"),
}
ALL_JURISDICTIONS = ("ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA")
_WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


@dataclass(frozen=True)
class Holiday:
    day: date
    name: str
    jurisdictions: tuple[str, ...]
    part_day: bool
    part_day_from: str | None
    status: str
    source: str


@dataclass(frozen=True)
class Unresolved:
    name: str
    jurisdictions: tuple[str, ...]
    candidate_dates: tuple[date, ...]
    expected_month: str | None
    weekday: int | None          # inferred from a name such as "Friday before the AFL Grand Final"
    source: str
    notes: str


@dataclass(frozen=True)
class Calendar:
    range_start: date
    range_end: date
    compiled: str
    regimes: dict
    by_date: dict[date, tuple[Holiday, ...]]
    unresolved: tuple[Unresolved, ...]
    ato_rows: dict[date, dict]


def _juris(v) -> tuple[str, ...]:
    return ALL_JURISDICTIONS if v == "ALL" or "ALL" in v else tuple(v)


@cache
def load_calendar(path: str | None = None) -> Calendar:
    doc = yaml.safe_load(Path(path or HOLIDAYS_FILE).read_text())
    meta = doc["meta"]
    by: dict[date, list[Holiday]] = {}
    for r in doc["holidays"]:
        h = Holiday(r["date"], r["name"], _juris(r["jurisdictions"]), bool(r.get("part_day")), r.get("part_day_from"),
                    r["status"], r["source"])
        by.setdefault(h.day, []).append(h)
    unresolved = []
    for u in doc.get("unresolved", []):
        first = u["name"].split()[0]
        wd = _WEEKDAYS.index(first) if first in _WEEKDAYS else None
        unresolved.append(Unresolved(u["name"], _juris(u["jurisdictions"]),
                                     tuple(c["date"] for c in u.get("candidate_dates", [])), u.get("expected_month"), wd,
                                     u["source"], u["notes"]))
    ato = {r["date"]: r for r in doc.get("ato_first_business_day_table", {}).get("rows", [])}
    return Calendar(meta["range_start"], meta["range_end"], str(meta["compiled"]), doc["regimes"],
                    {k: tuple(v) for k, v in by.items()}, tuple(unresolved), ato)


def _regime(regime: str) -> dict:
    cal = load_calendar()
    if regime not in cal.regimes:
        raise ValueError(f"unknown holiday regime {regime!r}; expected one of {sorted(cal.regimes)}")
    return cal.regimes[regime]


class HolidayDataRange(Refusal):
    """AU-GEN-004: a date the walk needs is outside the holiday data. `day` is the date that is outside; `statutory_date`
    (set by roll_due_date) is the due date being rolled, before any roll, for callers that list it beside the refusal."""

    def __init__(self, detail: str, day: date):
        super().__init__("AU-GEN-004", detail)
        self.day = day
        self.statutory_date: date | None = None


def _check_range(d: date) -> None:
    cal = load_calendar()
    if not cal.range_start <= d <= cal.range_end:
        raise HolidayDataRange(f"{d.isoformat()} is outside the public holiday data range "
                               f"{cal.range_start.isoformat()} to {cal.range_end.isoformat()}", d)


def _counts(h: Holiday, reg: dict) -> bool:
    if h.part_day and not reg["part_day_holidays_count"]:
        return False
    if reg["jurisdictions"] == "ALL":
        return True
    return bool(set(h.jurisdictions) & set(reg["jurisdictions"]))


def _juris_text(h: Holiday) -> str:
    j = "all States and Territories" if set(h.jurisdictions) == set(ALL_JURISDICTIONS) else ", ".join(h.jurisdictions)
    return f"{j}, part-day from {h.part_day_from}" if h.part_day else j


def _reason(d: date, regime: str, extra: frozenset[date] = frozenset()) -> str | None:
    """Why d is not a business day under the regime, or None if it is one. Range is not checked here."""
    if d.weekday() == 5:
        return "Saturday"
    if d.weekday() == 6:
        return "Sunday"
    reg = _regime(regime)
    hits = [h for h in load_calendar().by_date.get(d, ()) if _counts(h, reg)]
    if hits:
        return "; ".join(f"{h.name} ({_juris_text(h)})" for h in hits)
    if d in extra:
        return "an assumed holiday (candidate date)"
    return None


# ---------------------------------------------------------------- pure helpers

def non_business_reason(d: date, regime: str = COMMONWEALTH) -> str | None:
    """Reason d is not a business day (Saturday, Sunday, or the holiday name and jurisdictions); None if it is one.
    Refuses (AU-GEN-004) outside the data range."""
    _check_range(d)
    return _reason(d, regime)


def is_business_day(d: date, regime: str = COMMONWEALTH) -> bool:
    return non_business_reason(d, regime) is None


def first_business_day_on_or_after(d: date, regime: str = COMMONWEALTH) -> date:
    """d itself if it is a business day, otherwise the first business day after it. No uncertainty check: use
    roll_due_date in a calculator."""
    while non_business_reason(d, regime):
        d += timedelta(days=1)
    return d


next_business_day = first_business_day_on_or_after


def add_business_days(start: date, n: int, regime: str = COMMONWEALTH) -> date:
    """The nth business day after start (start itself is not counted; the count starts the day after)."""
    _check_range(start)
    d, count = start, 0
    while count < n:
        d += timedelta(days=1)
        if non_business_reason(d, regime) is None:
            count += 1
    return d


# ---------------------------------------------------------------- checked results for calculators

@dataclass
class Roll:
    """Result of moving a date to a business day, or of counting business days."""

    original: date
    due: date
    regime: str
    kind: str = "roll"                       # "roll" or "count"
    business_days: int | None = None         # kind == "count"
    skipped: list[tuple[date, str]] = field(default_factory=list)
    uncertain: list[dict] = field(default_factory=list)
    alternative: date | None = None
    warnings: list[str] = field(default_factory=list)
    out_of_range: dict | None = None         # set by roll_due_date_or_statutory: the AU-GEN-004 note for this date

    @property
    def rolled(self) -> bool:
        return self.due != self.original

    @property
    def draft(self) -> bool:
        return bool(self.uncertain)

    @property
    def reason(self) -> str | None:
        if not self.skipped:
            return None
        return "; ".join(f"{d.isoformat()} ({why})" if why == _WEEKDAYS[d.weekday()] else f"{d.isoformat()} ({_WEEKDAYS[d.weekday()]}): {why}"
                         for d, why in self.skipped)

    def as_dict(self) -> dict:
        reg = _regime(self.regime)
        out = {
            "kind": self.kind,
            "regime": self.regime,
            "original_date": self.original.isoformat(),
            "due_date": self.due.isoformat(),
            "due_date_weekday": _WEEKDAYS[self.due.weekday()],
            "rolled": self.rolled,
            "reason": self.reason,
            "rule": RULE_TEXT[self.regime],
            "rule_source": reg["rule_source"],
            "holiday_data": f"data/holidays/au.yaml (compiled {load_calendar().compiled})",
            "draft": self.draft,
        }
        if self.business_days is not None:
            out["business_days"] = self.business_days
        if self.out_of_range:
            out["holiday_data_covers_date"] = False
            out["refusal"] = dict(self.out_of_range)
            out["holiday_data"] = (f"data/holidays/au.yaml (compiled {load_calendar().compiled}) does not cover this date "
                                   f"(range {load_calendar().range_start.isoformat()} to {load_calendar().range_end.isoformat()})")
        if self.uncertain:
            out["alternative_due_date"] = self.alternative.isoformat() if self.alternative else None
            out["uncertain"] = self.uncertain
        return out


def _walk_roll(d: date, regime: str, extra: frozenset[date] = frozenset()) -> tuple[date, list[tuple[date, str]]]:
    skipped: list[tuple[date, str]] = []
    while True:
        _check_range(d)
        why = _reason(d, regime, extra)
        if why is None:
            return d, skipped
        skipped.append((d, why))
        d += timedelta(days=1)


def _walk_count(start: date, n: int, regime: str, extra: frozenset[date] = frozenset()) -> tuple[date, list[tuple[date, str]]]:
    _check_range(start)
    d, count, skipped = start, 0, []
    while count < n:
        d += timedelta(days=1)
        _check_range(d)
        why = _reason(d, regime, extra)
        if why is None:
            count += 1
        else:
            skipped.append((d, why))
    return d, skipped


def _touching(lo: date, hi: date, regime: str) -> list[dict]:
    """Unresolved holidays that could change a walk over lo..hi (inclusive) under the regime."""
    reg = _regime(regime)
    out = []
    for u in load_calendar().unresolved:
        if reg["jurisdictions"] != "ALL" and not set(u.jurisdictions) & set(reg["jurisdictions"]):
            continue
        cands = [c for c in u.candidate_dates if lo <= c <= hi]
        if cands:
            out.append({"name": u.name, "jurisdictions": list(u.jurisdictions), "candidate_date": cands[0].isoformat(),
                        "candidate_dates": [c.isoformat() for c in cands], "source": u.source, "notes": u.notes})
        elif not u.candidate_dates and u.expected_month:
            y, m = int(u.expected_month[:4]), int(u.expected_month[5:7])
            d = max(lo, date(y, m, 1))
            while d <= hi and (d.year, d.month) == (y, m):
                if u.weekday is None or d.weekday() == u.weekday:
                    out.append({"name": u.name, "jurisdictions": list(u.jurisdictions), "candidate_date": None,
                                "candidate_dates": [], "expected_month": u.expected_month, "source": u.source, "notes": u.notes})
                    break
                d += timedelta(days=1)
    return out


def _finish(res: Roll, redo, figures: Figures | None, allow_draft: bool | None) -> Roll:
    """Apply the unresolved-holiday policy, the ATO-table discrepancy warning and figure reporting."""
    cal = load_calendar()
    allow = figures.allow_draft if (allow_draft is None and figures is not None) else bool(allow_draft)
    res.uncertain = _touching(min(res.original, res.due), max(res.original, res.due), res.regime)
    if res.uncertain:
        names = "; ".join(f"{u['name']} ({'/'.join(u['jurisdictions'])}), " +
                          (f"candidate {u['candidate_date']}" if u["candidate_date"] else f"not yet declared for {u['expected_month']}")
                          for u in res.uncertain)
        span = f"{min(res.original, res.due).isoformat()} to {max(res.original, res.due).isoformat()}"
        if any(u["candidate_date"] is None for u in res.uncertain):
            raise FigureError(f"the business-day walk {span} touches a public holiday whose date is not yet declared ({names}); "
                              "no draft is possible", UNPUBLISHED)
        if not allow:
            raise FigureError(f"the business-day walk {span} touches a public holiday that is not yet confirmed ({names}); "
                              "rerun with --allow-draft for a draft that shows both dates", UNVERIFIED)
        extra = frozenset(date.fromisoformat(c) for u in res.uncertain for c in u["candidate_dates"])
        alt, _ = redo(extra)
        res.alternative = alt
        res.warnings.append(
            f"DRAFT: {names}. The date returned treats the candidate date as an ordinary business day; if it is a public holiday "
            f"the date is {alt.isoformat()}. Confirm against the ATO lodgment and payment dates page before relying on it.")
    if res.regime == COMMONWEALTH and res.kind == "roll":
        for d, _why in res.skipped:
            row = cal.ato_rows.get(d)
            if row and "discrepancy" in row and row["first_business_day"] != res.due:
                res.warnings.append(
                    f"The ATO's table (lodgment and payment dates on weekends or public holidays) prints "
                    f"{row['first_business_day'].isoformat()} ({_WEEKDAYS[row['first_business_day'].weekday()]}) as the first business day "
                    f"after {d.isoformat()}, but under the statutory definition the date is {res.due.isoformat()} "
                    f"({_WEEKDAYS[res.due.weekday()]}): {row['discrepancy']} The statutory date is returned; confirm with the ATO.")
    if figures is not None:
        record(figures, res)
    return res


def record(figures: Figures, res: Roll) -> None:
    """Report the rule and holiday data in figures_used; an unconfirmed candidate date marks the output draft."""
    reg = _regime(res.regime)
    key = f"holidays.{res.regime}"
    figures.used[key] = Figure(key, f"business-day rule and public holiday data compiled {load_calendar().compiled}", "rule",
                               "VERIFIED", reg["rule_source"], load_calendar().compiled)
    for u in res.uncertain:
        k = f"holidays.unresolved.{u['name']}"
        figures.used[k] = Figure(k, f"candidate {u['candidate_date']}", "date", "SUSPECT", u["source"], load_calendar().compiled)


def roll_due_date(d: date, regime: str = COMMONWEALTH, figures: Figures | None = None,
                  allow_draft: bool | None = None) -> Roll:
    """Move a due date that is not a business day to the first business day after (regime rule), with the reason,
    unresolved-holiday handling and figure reporting. Raises Refusal AU-GEN-004 outside the data range and
    FigureError (AU-GEN-001 or AU-GEN-003) when an unconfirmed holiday could change the answer."""
    try:
        due, skipped = _walk_roll(d, regime)
    except HolidayDataRange as e:
        e.statutory_date = d
        raise
    res = Roll(d, due, regime, "roll", skipped=skipped)
    return _finish(res, lambda extra: _walk_roll(d, regime, extra), figures, allow_draft)


def business_days_after(start: date, n: int, regime: str = COMMONWEALTH, figures: Figures | None = None,
                        allow_draft: bool | None = None) -> Roll:
    """The nth business day after start (start not counted), with the same checks as roll_due_date."""
    due, skipped = _walk_count(start, n, regime)
    res = Roll(start, due, regime, "count", business_days=n, skipped=skipped)
    return _finish(res, lambda extra: _walk_count(start, n, regime, extra), figures, allow_draft)


def roll_due_date_or_statutory(d: date, regime: str = COMMONWEALTH, figures: Figures | None = None,
                               allow_draft: bool | None = None) -> Roll:
    """roll_due_date for a due date that is secondary to the main result of a calculator. A date outside the holiday
    data range does not refuse: the statutory date is returned unrolled (rolled False) with a warning and the
    AU-GEN-004 code, message and detail in `Roll.out_of_range` (as_dict()["refusal"]), so the caller can report a
    per-field refusal and still return its main result. Nothing else changes: an unconfirmed holiday still raises
    FigureError, and a date inside the range is rolled exactly as roll_due_date does.

    Do not use this where the due date is the answer (bas_due_date, lodgment_due_dates): refuse there."""
    try:
        return roll_due_date(d, regime, figures, allow_draft)
    except Refusal as r:
        if r.code != "AU-GEN-004":
            raise
        entry = refusal_catalogue()["AU-GEN-004"]
        note = {"code": r.code, "message": entry["message"], "route": entry.get("route"), "detail": r.detail}
        res = Roll(d, d, regime, "roll", out_of_range=note)
        moves = (f" It is a {_WEEKDAYS[d.weekday()]}, so the real date is later, and I cannot say by how much."
                 if d.weekday() >= 5 else " If it is a public holiday the real date is later.")
        res.warnings.append(
            f"{d.isoformat()} is the statutory date, not moved for any non-business day: it is outside the public holiday data "
            f"({r.detail}).{moves} Check the ATO's lodgment and payment dates page (or RevenueSA for SA state taxes) before "
            "relying on it. AU-GEN-004 applies to this date only.")
        return res
