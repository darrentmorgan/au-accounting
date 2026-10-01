"""Tests for data/holidays/au.yaml and scripts/validate_holidays.py.

Expected values come from primary sources, not from this repo's code:
- the ATO table "Lodgment and payment dates on weekends or public holidays" (typed again below, independently of the data file);
- ATO Payday Super worked examples (payment-deadlines-for-payday-super page, updated 29 Sep 2026) and LCR 2026/3 paras 98, 99 and 167;
- RevenueSA's published payroll tax lodgement dates for 2026-27 (monthly-returns page).
"""
import copy
import datetime as dt
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_holidays as vh  # noqa: E402

DATA = ROOT / "data" / "holidays" / "au.yaml"
D = dt.date


def load():
    return yaml.safe_load(DATA.read_text())


def non_business(doc, regime):
    rows = doc["holidays"]
    if regime == "commonwealth":  # every listed day, part-day included (ATO table treats Christmas Eve and New Year's Eve as holidays)
        return {r["date"] for r in rows}
    if regime == "sa":  # Public Holidays Act 2023 (SA); part-day holidays excluded (LIA 2021 s 46, PHA 2023 s 8(3))
        return {r["date"] for r in rows if "SA" in vh.expand(r["jurisdictions"]) and not r.get("part_day")}
    raise ValueError(regime)


def roll(d, hol):
    while d.weekday() >= 5 or d in hol:
        d += dt.timedelta(days=1)
    return d


def business_days_after(start, n, hol):
    d, count = start, 0
    while count < n:
        d += dt.timedelta(days=1)
        if d.weekday() < 5 and d not in hol:
            count += 1
    return d


# ---------------------------------------------------------------- the real data file

def test_data_file_passes_validator():
    errs, counts, by_year = vh.validate(load())
    assert errs == []
    assert counts["VERIFIED"] > 0 and set(by_year) == {"2025-26", "2026-27", "2027-28"}


def test_unresolved_dates_are_not_listed_as_certain():
    doc = load()
    listed = {(r["date"], j) for r in doc["holidays"] for j in vh.expand(r["jurisdictions"])}
    assert {u["name"] for u in doc["unresolved"]} == {"Friday before the AFL Grand Final", "Labour Day", "Western Australia Day"}
    for u in doc["unresolved"]:
        assert u["date"] is None and u["status"] == "SUSPECT"
        for c in u.get("candidate_dates", []):
            assert all((c["date"], j) not in listed for j in u["jurisdictions"])


# ---------------------------------------------------------------- ATO table (typed independently from the ATO page)

ATO_TABLE = [
    (D(2026, 8, 3), D(2026, 8, 4)),
    (D(2026, 9, 25), D(2026, 9, 28)),
    (D(2026, 9, 28), D(2026, 9, 29)),
    (D(2026, 10, 5), D(2026, 10, 6)),
    (D(2026, 11, 3), D(2026, 11, 4)),
    (D(2026, 12, 24), D(2026, 12, 29)),
    (D(2026, 12, 25), D(2026, 12, 29)),
    (D(2026, 12, 28), D(2026, 12, 29)),
    (D(2026, 12, 31), D(2027, 1, 4)),
    (D(2027, 1, 1), D(2027, 1, 4)),
    (D(2027, 1, 26), D(2027, 1, 27)),
    (D(2027, 3, 1), D(2027, 3, 2)),
    (D(2027, 3, 8), D(2027, 3, 9)),
    (D(2027, 3, 26), D(2027, 3, 30)),
    (D(2027, 3, 29), D(2027, 3, 30)),
    (D(2027, 4, 26), D(2027, 4, 27)),
    (D(2027, 5, 3), D(2027, 5, 4)),
    (D(2027, 5, 31), D(2027, 6, 1)),
    (D(2027, 6, 7), D(2027, 6, 8)),
    (D(2027, 6, 14), D(2027, 6, 15)),
]


def test_ato_table_transcription_matches_second_transcription():
    rows = load()["ato_first_business_day_table"]["rows"]
    assert [(r["date"], r["first_business_day"]) for r in rows] == ATO_TABLE


def test_weekday_holidays_in_ato_window_are_exactly_the_ato_dates():
    hol = load()["holidays"]
    lo, hi = ATO_TABLE[0][0], ATO_TABLE[-1][0]
    ours = {r["date"] for r in hol if lo <= r["date"] <= hi and r["date"].weekday() < 5}
    assert ours == {d for d, _ in ATO_TABLE}


def test_first_business_day_from_holiday_rows_matches_ato_table_except_one_row():
    hol = non_business(load(), "commonwealth")
    for d, printed in ATO_TABLE:
        got = roll(d + dt.timedelta(days=1), hol)
        if d == D(2026, 9, 25):
            # The ATO prints Mon 28 Sep, but 28 Sep 2026 is WA's King's Birthday (a row of the same ATO table), so the
            # statutory definition (TAA 1953 s 8AAZMB(2)) gives Tue 29 Sep. Reported to the orchestrator.
            assert printed == D(2026, 9, 28) and got == D(2026, 9, 29)
        else:
            assert got == printed, d


# ---------------------------------------------------------------- scenarios the due-date calculators must pass

def test_easter_and_christmas_new_year_roll_forward_commonwealth():
    hol = non_business(load(), "commonwealth")
    # Easter 2027: Good Friday 26 Mar, Easter Monday 29 Mar; a due date on Good Friday, Saturday, Sunday or Monday is Tue 30 Mar (ATO table).
    for due in (D(2027, 3, 26), D(2027, 3, 27), D(2027, 3, 28), D(2027, 3, 29)):
        assert roll(due, hol) == D(2027, 3, 30)
    # Christmas and New Year 2026-27 (ATO table): 24, 25, 28 Dec -> 29 Dec; 31 Dec and 1 Jan -> Mon 4 Jan.
    for due in (D(2026, 12, 24), D(2026, 12, 25), D(2026, 12, 26), D(2026, 12, 28)):
        assert roll(due, hol) == D(2026, 12, 29)
    for due in (D(2026, 12, 31), D(2027, 1, 1), D(2027, 1, 2)):
        assert roll(due, hol) == D(2027, 1, 4)
    # Easter 2028 (state and territory lists): Good Friday 14 Apr to Easter Monday 17 Apr; next business day Tue 18 Apr.
    assert roll(D(2028, 4, 14), hol) == D(2028, 4, 18)
    # Christmas 2027 falls on a Saturday: 24 Dec (part-day), 25 to 28 Dec are all non-business days, so Wed 29 Dec.
    assert roll(D(2027, 12, 24), hol) == D(2027, 12, 29)
    # New Year 2028: Saturday 1 Jan, additional Monday 3 Jan -> Tue 4 Jan.
    assert roll(D(2027, 12, 31), hol) == D(2028, 1, 4)


# RevenueSA published dates (payroll tax monthly returns and payment, 2026-27; annual reconciliation 2025-26 and 2026-27).
# December 2026 is left out: RevenueSA published Thu 14 Jan 2027, an extension over Christmas and New Year, not the 7th rolled.
REVENUESA = [
    (D(2026, 8, 7), D(2026, 8, 7)),
    (D(2026, 9, 7), D(2026, 9, 7)),
    (D(2026, 10, 7), D(2026, 10, 7)),
    (D(2026, 11, 7), D(2026, 11, 9)),
    (D(2026, 12, 7), D(2026, 12, 7)),
    (D(2027, 2, 7), D(2027, 2, 8)),
    (D(2027, 3, 7), D(2027, 3, 9)),
    (D(2027, 4, 7), D(2027, 4, 7)),
    (D(2027, 5, 7), D(2027, 5, 7)),
    (D(2027, 6, 7), D(2027, 6, 7)),
    (D(2026, 7, 28), D(2026, 7, 28)),
    (D(2027, 7, 28), D(2027, 7, 28)),
]


def test_sa_regime_reproduces_revenuesa_published_payroll_tax_dates():
    hol = non_business(load(), "sa")
    for nominal, published in REVENUESA:
        assert roll(nominal, hol) == published, nominal
    # Adelaide Cup Day (SA, Mon 8 Mar 2027) is the SA holiday that moves the February return: Sun 7 Mar -> Mon 8 Mar is a holiday -> Tue 9 Mar.
    assert D(2027, 3, 8) in hol
    # December 2026: the standard roll is Thu 7 Jan 2027; RevenueSA's published 14 Jan 2027 is a discretionary extension.
    assert roll(D(2027, 1, 7), hol) == D(2027, 1, 7)


def test_jurisdiction_matters_wa_day_melbourne_cup_and_part_day_holidays():
    doc = load()
    cth, sa = non_business(doc, "commonwealth"), non_business(doc, "sa")
    # WA Day, Mon 7 Jun 2027: ATO table rolls to Tue 8 Jun; RevenueSA's published May-return date stays Mon 7 Jun.
    assert roll(D(2027, 6, 7), cth) == D(2027, 6, 8) and roll(D(2027, 6, 7), sa) == D(2027, 6, 7)
    # Melbourne Cup, Tue 3 Nov 2026: non-business for the ATO, ordinary day in SA.
    assert D(2026, 11, 3) in cth and D(2026, 11, 3) not in sa
    # Christmas Eve, Thu 24 Dec 2026, is a part-day holiday: the ATO table rolls it; the SA regime does not.
    assert roll(D(2026, 12, 24), cth) == D(2026, 12, 29) and roll(D(2026, 12, 24), sa) == D(2026, 12, 24)
    # New Year's Eve, Thu 31 Dec 2026 likewise.
    assert roll(D(2026, 12, 31), cth) == D(2027, 1, 4) and roll(D(2026, 12, 31), sa) == D(2026, 12, 31)


def test_no_sa_holiday_date_is_unique_to_sa():
    """Finding recorded for the due-date brief: every whole-day SA holiday in range is also observed elsewhere, so under the
    Commonwealth regime there is no SA-only date; the SA/other-state difference shows in the other direction (WA Day, Melbourne Cup)."""
    for r in load()["holidays"]:
        if "SA" in vh.expand(r["jurisdictions"]) and not r.get("part_day"):
            same_day_elsewhere = [x for x in load()["holidays"] if x["date"] == r["date"] and set(vh.expand(x["jurisdictions"])) - {"SA"}]
            assert same_day_elsewhere, r["date"]


# Payday Super business-day counts. Commonwealth regime: a holiday in ANY State, the ACT or the NT is not a business day.
PAYDAY_SUPER = [
    (D(2026, 7, 9), 20, D(2026, 8, 7)),    # ATO Payday page example 1 (3 Aug 2026 Picnic Day NT not counted)
    (D(2026, 7, 30), 7, D(2026, 8, 11)),   # same page
    (D(2026, 7, 23), 7, D(2026, 8, 4)),    # same page, bunching example
    (D(2026, 8, 7), 20, D(2026, 9, 4)),    # example 2
    (D(2026, 9, 4), 7, D(2026, 9, 15)),    # example 2
    (D(2026, 8, 8), 20, D(2026, 9, 4)),    # example 4 (exceptional circumstances)
    (D(2027, 6, 8), 7, D(2027, 6, 18)),    # LCR 2026/3 para 98 (14 Jun 2027 King's Birthday)
    (D(2027, 6, 29), 7, D(2027, 7, 8)),    # LCR 2026/3 para 99
    (D(2027, 7, 30), 7, D(2027, 8, 11)),   # LCR 2026/3 para 167 (2 Aug 2027 Picnic Day NT)
]


@pytest.mark.parametrize("start,n,expected", PAYDAY_SUPER)
def test_payday_super_business_day_examples(start, n, expected):
    assert business_days_after(start, n, non_business(load(), "commonwealth")) == expected


# ---------------------------------------------------------------- the validator rejects bad data

def errs_after(mutate):
    doc = copy.deepcopy(load())
    mutate(doc)
    return vh.validate(doc)[0]


def find(doc, name, year, juris=None):
    for i, r in enumerate(doc["holidays"]):
        if r["name"] == name and r["date"].year == year and (juris is None or "SA" in vh.expand(r["jurisdictions"])):
            return i
    raise AssertionError((name, year))


def test_validator_flags_wrong_weekday():
    assert any("weekday" in e for e in errs_after(lambda d: d["holidays"][0].update(weekday="Tue")))


def test_validator_flags_date_outside_range():
    def m(d):
        d["holidays"][0].update(date=D(2025, 6, 30), weekday="Mon")
    assert any("outside range" in e for e in errs_after(m))


def test_validator_flags_unknown_name_and_missing_source():
    assert any("unknown holiday name" in e for e in errs_after(lambda d: d["holidays"][0].update(name="Foo Day")))
    assert any("source must be an http" in e for e in errs_after(lambda d: d["holidays"][0].update(source="fairwork")))


def test_validator_flags_duplicates():
    def m(d):
        d["holidays"].insert(1, copy.deepcopy(d["holidays"][0]))
    assert any("duplicate" in e for e in errs_after(m))


def test_validator_flags_all_written_as_a_list_and_unsorted_lists():
    assert any("as ALL" in e for e in errs_after(lambda d: d["holidays"][0].update(jurisdictions=list(vh.JURIS))))
    assert any("sorted" in e for e in errs_after(lambda d: d["holidays"][0].update(jurisdictions=["NT", "ACT"])))


def test_validator_flags_part_day_misuse():
    def whole_day_christmas(d):
        d["holidays"][find(d, "Christmas Day", 2025)].update(part_day=True, part_day_from="19:00")

    def christmas_eve_without_flag(d):
        i = find(d, "Christmas Eve", 2025)
        d["holidays"][i].pop("part_day")
        d["holidays"][i].pop("part_day_from")

    def bad_time(d):
        d["holidays"][find(d, "Christmas Eve", 2025)]["part_day_from"] = "7pm"

    assert any("must not be marked part_day" in e for e in errs_after(whole_day_christmas))
    assert any("must be marked part_day" in e for e in errs_after(christmas_eve_without_flag))
    assert any("HH:MM" in e for e in errs_after(bad_time))


def test_validator_flags_suspect_without_note():
    def m(d):
        r = d["holidays"][0]
        r.update(status="SUSPECT")
    assert any("SUSPECT requires a note" in e for e in errs_after(m))


def test_validator_flags_calendar_rule_breaks():
    def cup(d):  # third Monday instead of second
        d["holidays"][find(d, "Adelaide Cup Day", 2027, "SA")].update(date=D(2027, 3, 15), weekday="Mon")

    def easter_monday(d):
        d["holidays"][find(d, "Easter Monday", 2027)].update(date=D(2027, 3, 30), weekday="Tue")

    def wa_day(d):  # 1st Monday on or after 1 June 2027 is 7 June
        d["holidays"][find(d, "Western Australia Day", 2027)].update(date=D(2027, 6, 14), weekday="Mon")

    for m in (cup, easter_monday, wa_day):
        assert any("breaks its calendar rule" in e for e in errs_after(m))


def test_validator_flags_missing_required_holiday():
    def m(d):
        d["holidays"] = [r for r in d["holidays"] if not (r["name"] == "Good Friday" and r["date"].year == 2027)]
    assert any("coverage" in e and "Good Friday" in e for e in errs_after(m))


def test_validator_flags_unresolved_problems():
    def dated(d):
        d["unresolved"][0]["date"] = D(2027, 9, 24)

    def no_hint(d):
        d["unresolved"][0].pop("expected_month")

    def bad_candidate(d):  # WA Labour Day 2028 candidate on a Tuesday breaks the rule
        d["unresolved"][1]["candidate_dates"][0]["date"] = D(2028, 3, 7)

    assert any("date must be null" in e for e in errs_after(dated))
    assert any("expected_month or candidate_dates" in e for e in errs_after(no_hint))
    assert any("breaks its calendar rule" in e for e in errs_after(bad_candidate))


def test_validator_flags_ato_table_drift():
    def wrong_fbd(d):
        d["ato_first_business_day_table"]["rows"][0]["first_business_day"] = D(2026, 8, 5)

    def dropped_row(d):
        del d["ato_first_business_day_table"]["rows"][3]

    def stale_discrepancy(d):
        d["ato_first_business_day_table"]["rows"][0]["discrepancy"] = "not real"

    assert any("ATO prints" in e for e in errs_after(wrong_fbd))
    assert any("differ from the holiday rows" in e for e in errs_after(dropped_row))
    assert any("stale" in e for e in errs_after(stale_discrepancy))


def test_validator_flags_missing_blocks():
    assert any("regimes.sa_state_tax: missing" in e for e in errs_after(lambda d: d["regimes"].pop("sa_state_tax")))
    assert any("meta.jurisdictions" in e for e in errs_after(lambda d: d["meta"].update(jurisdictions=["ACT"])))
    assert any("missing top-level 'holidays'" in e for e in vh.validate({"meta": {}})[0])
    assert vh.validate([])[0] == ["top level must be a mapping"]


def test_easter_helper_matches_known_dates():
    # Easter Sunday: 5 Apr 2026, 28 Mar 2027, 16 Apr 2028 (dates on the Fair Work Ombudsman and state pages).
    assert (vh.easter(2026), vh.easter(2027), vh.easter(2028)) == (D(2026, 4, 5), D(2027, 3, 28), D(2028, 4, 16))
