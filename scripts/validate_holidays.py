# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Validate data/holidays/*.yaml. Run: uv run scripts/validate_holidays.py [files...]

Checks: meta and regimes blocks, row schema, allowed statuses, source URLs, weekday and date-range checks,
calendar-rule checks for every named holiday (Easter, nth-weekday rules, substitute days), duplicate and ordering checks,
required-holiday coverage for every calendar year in range, the unresolved list (SUSPECT with a null date), and the
transcribed ATO first-business-day table against the holiday rows.
Prints counts by status and income year. Exit 1 on any error.
"""
from __future__ import annotations

import datetime as dt
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

STATUSES = {"VERIFIED", "SOURCE-CITED", "SUSPECT"}
JURIS = ["ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA"]
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
ROW_REQUIRED = ("date", "weekday", "name", "jurisdictions", "status", "source", "as_at")
ROW_ALLOWED = set(ROW_REQUIRED) | {"part_day", "part_day_from", "sources", "notes"}
UNRESOLVED_REQUIRED = ("name", "jurisdictions", "date", "status", "source", "as_at", "checked_at", "notes")
UNRESOLVED_ALLOWED = set(UNRESOLVED_REQUIRED) | {"expected_month", "candidate_dates", "sources"}
REGIME_KEYS = ("applies_to", "non_business_day", "jurisdictions", "part_day_holidays_count", "part_day_basis", "rule_source", "table_source")
HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
YEAR_MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


# ------------------------------------------------------------------ calendar helpers

def easter(y: int) -> dt.date:
    """Easter Sunday (anonymous Gregorian algorithm)."""
    a, b, c = y % 19, y // 100, y % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = (h + l - 7 * m + 114) % 31 + 1
    return dt.date(y, month, day)


def nth_weekday(y: int, m: int, weekday: int, n: int) -> dt.date:
    first = dt.date(y, m, 1)
    return first + dt.timedelta(days=(weekday - first.weekday()) % 7 + 7 * (n - 1))


def on_or_after(d: dt.date, weekday: int) -> dt.date:
    return d + dt.timedelta(days=(weekday - d.weekday()) % 7)


def income_year_label(start_year: int) -> str:
    return f"{start_year}-{(start_year + 1) % 100:02d}"


def income_year_of(d: dt.date) -> str:
    return income_year_label(d.year if d.month >= 7 else d.year - 1)


MON, TUE, FRI = 0, 1, 4


def _in(d: dt.date, month: int, days: tuple[int, ...]) -> bool:
    return d.month == month and d.day in days


# name, jurisdiction -> predicate(date). Names not listed in KNOWN_NAMES are rejected so every new holiday name needs a rule.
RULES: dict[tuple[str, str], callable] = {}


def _rule(name: str, juris: list[str], fn) -> None:
    for j in juris:
        RULES[(name, j)] = fn


def _build_rules() -> None:
    _rule("Canberra Day", ["ACT"], lambda d: d == nth_weekday(d.year, 3, MON, 2))
    _rule("Eight Hours Day", ["TAS"], lambda d: d == nth_weekday(d.year, 3, MON, 2))
    _rule("Labour Day", ["VIC"], lambda d: d == nth_weekday(d.year, 3, MON, 2))
    _rule("Adelaide Cup Day", ["SA"], lambda d: d == nth_weekday(d.year, 3, MON, 2))
    _rule("Labour Day", ["WA"], lambda d: d == on_or_after(dt.date(d.year, 3, 1), MON))
    _rule("Labour Day", ["QLD"], lambda d: d == nth_weekday(d.year, 5, MON, 1))
    _rule("May Day", ["NT"], lambda d: d == nth_weekday(d.year, 5, MON, 1))
    _rule("Labour Day", ["ACT", "NSW", "SA"], lambda d: d == nth_weekday(d.year, 10, MON, 1))
    _rule("King's Birthday", ["QLD"], lambda d: d == nth_weekday(d.year, 10, MON, 1))
    _rule("King's Birthday", ["ACT", "NSW", "NT", "SA", "TAS", "VIC"], lambda d: d == nth_weekday(d.year, 6, MON, 2))
    _rule("King's Birthday", ["WA"], lambda d: d.weekday() == MON and d.month in (9, 10))  # proclaimed each year
    _rule("Reconciliation Day", ["ACT"], lambda d: d == on_or_after(dt.date(d.year, 5, 27), MON))
    _rule("Western Australia Day", ["WA"], lambda d: d == on_or_after(dt.date(d.year, 6, 1), MON))
    _rule("Picnic Day", ["NT"], lambda d: d == nth_weekday(d.year, 8, MON, 1))
    _rule("Melbourne Cup", ["VIC"], lambda d: d == nth_weekday(d.year, 11, TUE, 1))
    _rule("Friday before the AFL Grand Final", ["VIC"], lambda d: d.weekday() == FRI and d.month == 9)


_build_rules()

# names whose rule does not depend on the jurisdiction
GENERIC_RULES = {
    "New Year's Day": lambda d: _in(d, 1, (1, 2, 3)),
    "Additional public holiday for New Year's Day": lambda d: _in(d, 1, (2, 3)) and d.weekday() == MON,
    "Australia Day": lambda d: _in(d, 1, (26,)) or (_in(d, 1, (27, 28)) and d.weekday() == MON),
    "Good Friday": lambda d: d == easter(d.year) - dt.timedelta(days=2),
    "Easter Saturday": lambda d: d == easter(d.year) - dt.timedelta(days=1),
    "Easter Sunday": lambda d: d == easter(d.year),
    "Easter Monday": lambda d: d == easter(d.year) + dt.timedelta(days=1),
    "Anzac Day": lambda d: _in(d, 4, (25,)) or (_in(d, 4, (26,)) and d.weekday() == MON and dt.date(d.year, 4, 25).weekday() == 6),
    "Additional public holiday for Anzac Day": lambda d: _in(d, 4, (26, 27)) and d.weekday() == MON and dt.date(d.year, 4, 25).weekday() >= 5,
    "Christmas Eve": lambda d: _in(d, 12, (24,)),
    "Christmas Day": lambda d: _in(d, 12, (25,)),
    "Additional public holiday for Christmas Day": lambda d: _in(d, 12, (26, 27)),
    "Boxing Day": lambda d: _in(d, 12, (26, 27, 28)),
    "Additional public holiday for Boxing Day": lambda d: _in(d, 12, (27, 28)),
    "Proclamation Day holiday": lambda d: _in(d, 12, (26,)),
    "Additional public holiday for Proclamation Day holiday": lambda d: _in(d, 12, (27, 28)),
    "New Year's Eve": lambda d: _in(d, 12, (31,)),
}
JURISDICTION_RULE_NAMES = {name for name, _ in RULES}
KNOWN_NAMES = set(GENERIC_RULES) | JURISDICTION_RULE_NAMES
PART_DAY_NAMES = {"Christmas Eve", "New Year's Eve"}  # part-day holidays only (NT and SA from 7pm, QLD from 6pm on Christmas Eve)


# ------------------------------------------------------------------ small validators

def is_url(x) -> bool:
    return isinstance(x, str) and x.startswith(("http://", "https://"))


def expand(j) -> list[str]:
    return list(JURIS) if j == ["ALL"] else list(j)


def check_juris(path: str, j, errs: list[str], allow_all: bool) -> bool:
    if j == ["ALL"]:
        if not allow_all:
            errs.append(f"{path}: ALL not allowed here")
            return False
        return True
    if not isinstance(j, list) or not j or not all(x in JURIS for x in j):
        errs.append(f"{path}: jurisdictions must be ALL or a non-empty list drawn from {JURIS} (got {j!r})")
        return False
    if len(set(j)) != len(j) or list(j) != sorted(j):
        errs.append(f"{path}: jurisdictions must be unique and sorted (got {j!r})")
        return False
    if len(j) == len(JURIS):
        errs.append(f"{path}: list every jurisdiction as ALL")
        return False
    return True


def check_sources(path: str, row: dict, errs: list[str]) -> None:
    if not is_url(row.get("source")):
        errs.append(f"{path}: source must be an http(s) URL")
    if "sources" in row:
        s = row["sources"]
        if not isinstance(s, list) or not s or not all(is_url(x) for x in s):
            errs.append(f"{path}: sources must be a non-empty list of http(s) URLs")
        elif len(set(s)) != len(s) or row.get("source") in s:
            errs.append(f"{path}: sources must not repeat source or each other")


def check_holiday(path: str, row, lo: dt.date, hi: dt.date, errs: list[str], counts: Counter) -> bool:
    if not isinstance(row, dict):
        errs.append(f"{path}: row must be a mapping")
        return False
    for k in ROW_REQUIRED:
        if k not in row:
            errs.append(f"{path}: missing '{k}'")
    extra = set(row) - ROW_ALLOWED
    if extra:
        errs.append(f"{path}: unexpected keys {sorted(extra)}")
    d = row.get("date")
    ok = isinstance(d, dt.date)
    if not ok:
        errs.append(f"{path}: date must be a YYYY-MM-DD date (a null date belongs in 'unresolved')")
    else:
        if not lo <= d <= hi:
            errs.append(f"{path}: date {d} outside range {lo} to {hi}")
        if row.get("weekday") != WEEKDAYS[d.weekday()]:
            errs.append(f"{path}: weekday {row.get('weekday')!r} is wrong for {d} ({WEEKDAYS[d.weekday()]})")
    name = row.get("name")
    if not isinstance(name, str) or not name.strip():
        errs.append(f"{path}: name must be a non-empty string")
    j = row.get("jurisdictions")
    if "jurisdictions" in row:
        check_juris(f"{path}.jurisdictions", j, errs, allow_all=True)
    st = row.get("status")
    if st not in STATUSES:
        errs.append(f"{path}: status {st!r} not in {sorted(STATUSES)}")
    else:
        counts[st] += 1
        if st == "SUSPECT" and not row.get("notes"):
            errs.append(f"{path}: SUSPECT requires a note")
    check_sources(path, row, errs)
    if not isinstance(row.get("as_at"), dt.date):
        errs.append(f"{path}: as_at must be a YYYY-MM-DD date")
    if "notes" in row and not (isinstance(row["notes"], str) and row["notes"].strip()):
        errs.append(f"{path}: notes must be a non-empty string")
    pd = row.get("part_day", False)
    if not isinstance(pd, bool):
        errs.append(f"{path}: part_day must be a boolean")
    elif pd:
        if not (isinstance(row.get("part_day_from"), str) and HHMM.match(row["part_day_from"])):
            errs.append(f"{path}: part_day true needs part_day_from as a quoted 'HH:MM' string")
    elif "part_day_from" in row or "part_day" in row:
        errs.append(f"{path}: omit part_day and part_day_from for a whole-day holiday")
    if isinstance(name, str) and (name in PART_DAY_NAMES) != (pd is True):
        errs.append(f"{path}: {name!r} {'must' if name in PART_DAY_NAMES else 'must not'} be marked part_day")
    # calendar rules
    if ok and isinstance(name, str) and isinstance(j, list):
        if name not in KNOWN_NAMES:
            errs.append(f"{path}: unknown holiday name {name!r}; add it (with its calendar rule) to validate_holidays.py")
        else:
            if name in GENERIC_RULES and not GENERIC_RULES[name](d):
                errs.append(f"{path}: {name} on {d} breaks its calendar rule")
            for jur in expand(j):
                rule = RULES.get((name, jur))
                if rule and not rule(d):
                    errs.append(f"{path}: {name} ({jur}) on {d} breaks its calendar rule")
            if name in JURISDICTION_RULE_NAMES and name not in GENERIC_RULES:
                if not any((name, jur) in RULES for jur in expand(j)):
                    errs.append(f"{path}: {name} is not a holiday in {j}")
    return ok


def check_regimes(reg, errs: list[str]) -> None:
    if not isinstance(reg, dict):
        errs.append("regimes: must be a mapping")
        return
    for name in ("commonwealth_tax", "sa_state_tax"):
        r = reg.get(name)
        if not isinstance(r, dict):
            errs.append(f"regimes.{name}: missing")
            continue
        for k in REGIME_KEYS:
            if k not in r:
                errs.append(f"regimes.{name}: missing '{k}'")
        if not isinstance(r.get("part_day_holidays_count"), bool):
            errs.append(f"regimes.{name}.part_day_holidays_count must be a boolean")
        for k in ("rule_source", "table_source"):
            if k in r and not is_url(r[k]):
                errs.append(f"regimes.{name}.{k} must be an http(s) URL")
        for k in ("applies_to", "non_business_day", "part_day_basis"):
            if k in r and not (isinstance(r[k], str) and r[k].strip()):
                errs.append(f"regimes.{name}.{k} must be a non-empty string")
    cth, sa = reg.get("commonwealth_tax") or {}, reg.get("sa_state_tax") or {}
    if cth.get("jurisdictions") != "ALL":
        errs.append("regimes.commonwealth_tax.jurisdictions must be ALL")
    if sa.get("jurisdictions") != ["SA"]:
        errs.append("regimes.sa_state_tax.jurisdictions must be [SA]")


def check_unresolved(rows, lo: dt.date, hi: dt.date, errs: list[str]) -> None:
    if not isinstance(rows, list):
        errs.append("unresolved: must be a list")
        return
    for i, row in enumerate(rows):
        path = f"unresolved[{i}]"
        if not isinstance(row, dict):
            errs.append(f"{path}: row must be a mapping")
            continue
        for k in UNRESOLVED_REQUIRED:
            if k not in row:
                errs.append(f"{path}: missing '{k}'")
        extra = set(row) - UNRESOLVED_ALLOWED
        if extra:
            errs.append(f"{path}: unexpected keys {sorted(extra)}")
        if row.get("date") is not None:
            errs.append(f"{path}: date must be null (a declared date belongs in 'holidays')")
        if row.get("status") != "SUSPECT":
            errs.append(f"{path}: status must be SUSPECT")
        if row.get("name") not in KNOWN_NAMES:
            errs.append(f"{path}: unknown holiday name {row.get('name')!r}")
        if "jurisdictions" in row:
            check_juris(f"{path}.jurisdictions", row["jurisdictions"], errs, allow_all=False)
        check_sources(path, row, errs)
        for k in ("as_at", "checked_at"):
            if not isinstance(row.get(k), dt.date):
                errs.append(f"{path}: {k} must be a YYYY-MM-DD date")
        if not (isinstance(row.get("notes"), str) and row["notes"].strip()):
            errs.append(f"{path}: notes must explain what is unresolved")
        em, cd = row.get("expected_month"), row.get("candidate_dates")
        if em is None and cd is None:
            errs.append(f"{path}: give expected_month or candidate_dates so calculators can flag the uncertainty")
        if em is not None:
            if not (isinstance(em, str) and YEAR_MONTH.match(em)):
                errs.append(f"{path}: expected_month must be a quoted YYYY-MM string")
            elif not lo <= dt.date(int(em[:4]), int(em[5:]), 1) <= hi:
                errs.append(f"{path}: expected_month {em} outside range")
        if cd is not None:
            if not isinstance(cd, list) or not cd:
                errs.append(f"{path}: candidate_dates must be a non-empty list")
            else:
                for n, c in enumerate(cd):
                    if not (isinstance(c, dict) and set(c) == {"date", "basis"} and isinstance(c["date"], dt.date)
                            and isinstance(c["basis"], str) and c["basis"].strip()):
                        errs.append(f"{path}.candidate_dates[{n}]: needs date and basis only")
                    elif not lo <= c["date"] <= hi:
                        errs.append(f"{path}.candidate_dates[{n}]: date outside range")
                    elif isinstance(row.get("name"), str) and row.get("jurisdictions") and row["name"] in KNOWN_NAMES:
                        for jur in expand(row["jurisdictions"]):
                            rule = RULES.get((row["name"], jur))
                            if rule and not rule(c["date"]):
                                errs.append(f"{path}.candidate_dates[{n}]: {row['name']} ({jur}) on {c['date']} breaks its calendar rule")


# ------------------------------------------------------------------ cross-section checks

def whole_or_part_day_dates(rows: list[dict]) -> set[dt.date]:
    """Commonwealth regime: every listed date counts (whole-day and part-day holidays, any State or Territory)."""
    return {r["date"] for r in rows if isinstance(r, dict) and isinstance(r.get("date"), dt.date)}


def next_business_day(d: dt.date, holidays: set[dt.date]) -> dt.date:
    d += dt.timedelta(days=1)
    while d.weekday() >= 5 or d in holidays:
        d += dt.timedelta(days=1)
    return d


def check_required_coverage(rows: list[dict], lo: dt.date, hi: dt.date, errs: list[str]) -> None:
    """The holidays every jurisdiction observes must be present for every calendar year in range. A holiday may move to a
    later day in one jurisdiction (for example Tasmania observes a Saturday New Year's Day on the Monday), so coverage is
    the union of jurisdictions over the canonical date and the three days after it."""
    listed: dict[str, list[tuple[dt.date, set[str]]]] = {}
    for r in rows:
        if isinstance(r, dict) and isinstance(r.get("date"), dt.date) and isinstance(r.get("name"), str) and isinstance(r.get("jurisdictions"), list):
            listed.setdefault(r["name"], []).append((r["date"], set(expand(r["jurisdictions"]))))
    for y in range(lo.year, hi.year + 1):
        e = easter(y)
        aus = dt.date(y, 1, 26)
        if aus.weekday() >= 5:
            aus = on_or_after(aus, MON)
        expected = {
            "New Year's Day": dt.date(y, 1, 1),
            "Australia Day": aus,
            "Good Friday": e - dt.timedelta(days=2),
            "Easter Monday": e + dt.timedelta(days=1),
            "Anzac Day": dt.date(y, 4, 25),
            "Christmas Day": dt.date(y, 12, 25),
        }
        for name, d in expected.items():
            if not lo <= d <= hi:
                continue
            covered: set[str] = set()
            for rd, js in listed.get(name, []):
                if d <= rd <= d + dt.timedelta(days=3):
                    covered |= js
            if covered != set(JURIS):
                errs.append(f"coverage: '{name}' near {d} is missing for {sorted(set(JURIS) - covered)}")
    years = [income_year_label(y) for y in range(lo.year, hi.year)]
    for jur in JURIS:
        seen = {income_year_of(r["date"]) for r in rows
                if isinstance(r, dict) and isinstance(r.get("date"), dt.date) and jur in expand(r.get("jurisdictions") or [])}
        for y in years:
            if y not in seen:
                errs.append(f"coverage: no holidays for {jur} in income year {y}")


def check_duplicates_and_order(rows: list[dict], errs: list[str]) -> None:
    seen: dict[tuple[dt.date, str, str], int] = {}
    prev = None
    for i, r in enumerate(rows):
        if not (isinstance(r, dict) and isinstance(r.get("date"), dt.date) and isinstance(r.get("name"), str)
                and isinstance(r.get("jurisdictions"), list)):
            continue
        if prev is not None and r["date"] < prev:
            errs.append(f"holidays[{i}]: not in date order")
        prev = r["date"]
        for jur in expand(r["jurisdictions"]):
            k = (r["date"], r["name"], jur)
            if k in seen:
                errs.append(f"holidays[{i}]: duplicate of holidays[{seen[k]}] ({r['name']} {r['date']} {jur})")
            seen[k] = i


def check_ato_table(doc, rows: list[dict], errs: list[str]) -> None:
    t = doc.get("ato_first_business_day_table")
    if not isinstance(t, dict):
        errs.append("ato_first_business_day_table: missing")
        return
    if not is_url(t.get("source")):
        errs.append("ato_first_business_day_table.source must be an http(s) URL")
    if t.get("status") != "VERIFIED":
        errs.append("ato_first_business_day_table.status must be VERIFIED")
    if not isinstance(t.get("as_at"), dt.date):
        errs.append("ato_first_business_day_table.as_at must be a date")
    trows = t.get("rows")
    if not isinstance(trows, list) or not trows:
        errs.append("ato_first_business_day_table.rows must be a non-empty list")
        return
    hol = whole_or_part_day_dates(rows)
    dates = []
    for i, r in enumerate(trows):
        path = f"ato_first_business_day_table.rows[{i}]"
        if not (isinstance(r, dict) and isinstance(r.get("date"), dt.date) and isinstance(r.get("first_business_day"), dt.date)):
            errs.append(f"{path}: needs date and first_business_day")
            continue
        extra = set(r) - {"date", "first_business_day", "discrepancy"}
        if extra:
            errs.append(f"{path}: unexpected keys {sorted(extra)}")
        d, fbd = r["date"], r["first_business_day"]
        dates.append(d)
        if d.weekday() >= 5:
            errs.append(f"{path}: {d} is a weekend; the ATO table lists weekday holidays only")
        if d not in hol:
            errs.append(f"{path}: {d} is not a holiday row in 'holidays'")
        if fbd.weekday() >= 5 or fbd <= d:
            errs.append(f"{path}: first_business_day {fbd} must be a later weekday")
        computed = next_business_day(d, hol)
        if "discrepancy" in r:
            if not (isinstance(r["discrepancy"], str) and r["discrepancy"].strip()):
                errs.append(f"{path}: discrepancy must be a non-empty string")
            if computed == fbd:
                errs.append(f"{path}: discrepancy note is stale ({fbd} agrees with the holiday rows)")
        elif computed != fbd:
            errs.append(f"{path}: ATO prints {fbd} but the holiday rows give {computed}; fix the data or record a discrepancy")
    if dates != sorted(dates):
        errs.append("ato_first_business_day_table.rows: not in date order")
    if dates:
        lo, hi = min(dates), max(dates)
        weekday_hols = {d for d in hol if lo <= d <= hi and d.weekday() < 5}
        if weekday_hols != set(dates):
            missing = sorted(weekday_hols - set(dates))
            extra = sorted(set(dates) - weekday_hols)
            errs.append(f"ato_first_business_day_table: weekday holiday dates in {lo}..{hi} differ from the holiday rows "
                        f"(only in rows: {[str(x) for x in missing]}; only in ATO table: {[str(x) for x in extra]})")


# ------------------------------------------------------------------ entry points

def validate(doc) -> tuple[list[str], Counter, Counter]:
    """Return (errors, status counts, counts by income year) for a parsed holidays document."""
    errs: list[str] = []
    counts: Counter = Counter()
    by_year: Counter = Counter()
    if not isinstance(doc, dict):
        return ["top level must be a mapping"], counts, by_year
    for k in ("meta", "regimes", "holidays", "unresolved", "ato_first_business_day_table"):
        if k not in doc:
            errs.append(f"missing top-level '{k}'")
    meta = doc.get("meta")
    lo = hi = None
    if not isinstance(meta, dict):
        errs.append("meta: missing")
    else:
        if meta.get("schema_version") != 1:
            errs.append("meta.schema_version must be 1")
        for k in ("range_start", "range_end", "compiled"):
            if not isinstance(meta.get(k), dt.date):
                errs.append(f"meta.{k}: must be a date")
        if isinstance(meta.get("range_start"), dt.date) and isinstance(meta.get("range_end"), dt.date):
            lo, hi = meta["range_start"], meta["range_end"]
            if lo >= hi:
                errs.append("meta: range_start must precede range_end")
            if (lo.month, lo.day) != (7, 1) or (hi.month, hi.day) != (6, 30):
                errs.append("meta: range must run from 1 July to 30 June (whole income years)")
            else:
                want = [income_year_label(y) for y in range(lo.year, hi.year)]
                if meta.get("income_years") != want:
                    errs.append(f"meta.income_years must be {want}")
        if meta.get("jurisdictions") != JURIS:
            errs.append(f"meta.jurisdictions must be {JURIS}")
    check_regimes(doc.get("regimes"), errs)
    rows = doc.get("holidays")
    if not isinstance(rows, list) or not rows:
        errs.append("holidays: must be a non-empty list")
        rows = []
    if lo and hi:
        for i, row in enumerate(rows):
            if check_holiday(f"holidays[{i}]", row, lo, hi, errs, counts):
                by_year[income_year_of(row["date"])] += 1
        check_duplicates_and_order(rows, errs)
        check_required_coverage(rows, lo, hi, errs)
        check_unresolved(doc.get("unresolved"), lo, hi, errs)
        check_ato_table(doc, rows, errs)
    return errs, counts, by_year


def main() -> int:
    root = Path(__file__).resolve().parent.parent / "data" / "holidays"
    files = [Path(a) for a in sys.argv[1:]] or sorted(root.glob("*.yaml"))
    if not files:
        print(f"no holiday files found in {root}")
        return 1
    bad = 0
    for f in files:
        try:
            doc = yaml.safe_load(f.read_text())
        except yaml.YAMLError as e:
            print(f"{f.name}: YAML parse error: {e}")
            bad += 1
            continue
        errs, counts, by_year = validate(doc)
        n = len(doc.get("holidays") or []) if isinstance(doc, dict) else 0
        pending = len(doc.get("unresolved") or []) if isinstance(doc, dict) else 0
        print(f"{f.name}: {n} holidays, {pending} unresolved | " + ", ".join(f"{s}={counts.get(s, 0)}" for s in sorted(STATUSES))
              + " | " + ", ".join(f"{y}={c}" for y, c in sorted(by_year.items())))
        for e in errs:
            print(f"  ERROR {e}")
        bad += len(errs)
    print("FAIL" if bad else "OK", f"({bad} errors)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
