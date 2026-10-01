"""Shared business-day loader (au_tax.holidays). Expected values are the ATO's published first business days
(ATO, Lodgment and payment dates on weekends or public holidays, updated 1 Jul 2026), RevenueSA's published 2026-27
payroll tax lodgement dates, and the ATO Payday Super and LCR 2026/3 worked examples, typed here independently of the
data file. Rule: TAA 1953 s 8AAZMB and Sch 1 s 388-52 (Commonwealth); Public Holidays Act 2023 (SA) s 8 (SA)."""
from datetime import date

import pytest

from au_tax import holidays as h
from au_tax.figures import FigureError, Figures
from au_tax.registry import Refusal, refusal_catalogue

D = date
CW, SA = h.COMMONWEALTH, h.SA_STATE


def due(d, regime=CW):
    return h.roll_due_date(d, regime).due


# ---------------------------------------------------------------- Commonwealth: ATO table

@pytest.mark.parametrize("original,expected", [
    # Easter 2027: Good Friday 26 Mar, Easter Sat/Sun, Easter Monday 29 Mar -> Tue 30 Mar (ATO table, 26 Mar 2027 row)
    (D(2027, 3, 26), D(2027, 3, 30)),
    (D(2027, 3, 27), D(2027, 3, 30)),
    (D(2027, 3, 28), D(2027, 3, 30)),
    (D(2027, 3, 29), D(2027, 3, 30)),
    # Christmas 2026: Thu 24 Dec (Christmas Eve part-day in QLD, NT, SA, counted by the ATO), Fri 25, Sat 26, Sun 27, Mon 28
    (D(2026, 12, 24), D(2026, 12, 29)),
    (D(2026, 12, 25), D(2026, 12, 29)),
    (D(2026, 12, 26), D(2026, 12, 29)),
    (D(2026, 12, 27), D(2026, 12, 29)),
    (D(2026, 12, 28), D(2026, 12, 29)),
    # New Year 2027: Thu 31 Dec (New Year's Eve part-day NT, SA), Fri 1 Jan, Sat 2 Jan -> Mon 4 Jan
    (D(2026, 12, 31), D(2027, 1, 4)),
    (D(2027, 1, 1), D(2027, 1, 4)),
    (D(2027, 1, 2), D(2027, 1, 4)),
    # Other rows of the ATO table
    (D(2026, 8, 3), D(2026, 8, 4)),      # Picnic Day (NT)
    (D(2026, 9, 28), D(2026, 9, 29)),    # King's Birthday (WA)
    (D(2026, 10, 5), D(2026, 10, 6)),    # Labour Day and King's Birthday (QLD)
    (D(2026, 11, 3), D(2026, 11, 4)),    # Melbourne Cup (VIC)
    (D(2027, 1, 26), D(2027, 1, 27)),    # Australia Day
    (D(2027, 3, 1), D(2027, 3, 2)),      # Labour Day (WA)
    (D(2027, 3, 8), D(2027, 3, 9)),      # Adelaide Cup, Labour Day (VIC), Eight Hours Day (TAS), Canberra Day
    (D(2027, 6, 7), D(2027, 6, 8)),      # Western Australia Day
])
def test_commonwealth_roll_matches_ato_table(original, expected):
    r = h.roll_due_date(original)
    assert r.due == expected
    assert r.rolled
    assert r.reason and r.alternative is None and not r.draft


def test_business_day_is_not_rolled():
    r = h.roll_due_date(D(2027, 2, 26))  # Friday, no holiday
    assert r.due == D(2027, 2, 26) and not r.rolled and r.reason is None
    assert r.as_dict()["rolled"] is False


def test_january_28_and_february_28_bas_dates_2027():
    # 28 Jan 2027 is a Thursday and 28 Feb 2027 a Sunday (calendar): Sunday rolls to Mon 1 Mar 2027,
    # which is not a holiday (Labour Day WA is Mon 1 Mar 2027 -> Tue 2 Mar per the ATO table).
    assert due(D(2027, 1, 28)) == D(2027, 1, 28)
    r = h.roll_due_date(D(2027, 2, 28))
    assert r.due == D(2027, 3, 2)
    assert [d for d, _ in r.skipped] == [D(2027, 2, 28), D(2027, 3, 1)]
    assert "Sunday" in r.skipped[0][1] and "Labour Day" in r.skipped[1][1]


def test_reason_names_holiday_and_jurisdictions():
    r = h.roll_due_date(D(2027, 6, 7))
    assert "Western Australia Day" in r.reason and "WA" in r.reason
    assert r.as_dict()["regime"] == CW
    assert "8AAZMB" in r.as_dict()["rule"] and "388-52" in r.as_dict()["rule"]


def test_saturday_holiday_is_reported_as_saturday():
    r = h.roll_due_date(D(2026, 12, 26))  # Boxing Day on a Saturday
    assert r.skipped[0][1] == "Saturday"


# ---------------------------------------------------------------- SA regime and regime difference

def test_sa_regime_feb_2027_payroll_return_adelaide_cup():
    # RevenueSA published date: February 2027 return, 7 Mar 2027 is a Sunday, Mon 8 Mar 2027 is Adelaide Cup Day -> Tue 9 Mar 2027.
    r = h.roll_due_date(D(2027, 3, 7), SA)
    assert r.due == D(2027, 3, 9)
    assert "Adelaide Cup" in r.reason and "SA" in r.reason


def test_sa_regime_nov_2026_saturday():
    # RevenueSA published date: 7 Nov 2026 (Saturday) -> Mon 9 Nov 2026.
    assert due(D(2026, 11, 7), SA) == D(2026, 11, 9)


def test_regime_difference_wa_day_2027():
    # WA Day Mon 7 Jun 2027: ATO rolls to Tue 8 Jun; RevenueSA's own published May 2027 due date stays Mon 7 Jun.
    assert due(D(2027, 6, 7), CW) == D(2027, 6, 8)
    assert due(D(2027, 6, 7), SA) == D(2027, 6, 7)


def test_regime_difference_melbourne_cup_2026():
    assert due(D(2026, 11, 3), CW) == D(2026, 11, 4)
    assert due(D(2026, 11, 3), SA) == D(2026, 11, 3)


def test_regime_difference_christmas_eve_part_day():
    # Thu 24 Dec 2026: the ATO table counts the part-day holiday (Tue 29 Dec); SA regime excludes it (PHA 2023 s 8(3)).
    assert due(D(2026, 12, 24), CW) == D(2026, 12, 29)
    assert due(D(2026, 12, 24), SA) == D(2026, 12, 24)


def test_sa_christmas_day_and_proclamation_day_roll():
    # Fri 25 Dec 2026 Christmas Day; Sat 26 Boxing Day; Sun 27; Mon 28 Dec Proclamation Day holiday -> Tue 29 Dec.
    assert due(D(2026, 12, 25), SA) == D(2026, 12, 29)


def test_unknown_regime_is_an_error():
    with pytest.raises(ValueError):
        h.roll_due_date(D(2027, 3, 1), "nsw_state_tax")


# ---------------------------------------------------------------- helpers

def test_is_business_day_and_first_business_day():
    assert not h.is_business_day(D(2027, 3, 26))
    assert h.is_business_day(D(2027, 3, 30))
    assert h.is_business_day(D(2027, 6, 7), SA)
    assert not h.is_business_day(D(2027, 6, 7), CW)
    assert h.first_business_day_on_or_after(D(2027, 3, 26)) == D(2027, 3, 30)
    assert h.next_business_day(D(2027, 3, 30)) == D(2027, 3, 30)


@pytest.mark.parametrize("start,n,expected", [
    (D(2026, 7, 9), 20, D(2026, 8, 7)),    # ATO Payday Super example (Hannah), includes Picnic Day Mon 3 Aug
    (D(2026, 7, 30), 7, D(2026, 8, 11)),   # ATO Payday Super example
    (D(2027, 6, 8), 7, D(2027, 6, 18)),    # LCR 2026/3 para 98
    (D(2027, 7, 30), 7, D(2027, 8, 11)),   # LCR 2026/3 para 167 (Mon 2 Aug 2027 Picnic Day)
])
def test_add_business_days_payday_super_examples(start, n, expected):
    assert h.add_business_days(start, n) == expected
    assert h.business_days_after(start, n).due == expected


# ---------------------------------------------------------------- range, unresolved, ATO discrepancy

def test_outside_data_range_refuses():
    with pytest.raises(Refusal) as e:
        h.roll_due_date(D(2028, 7, 1))
    assert e.value.code == "AU-GEN-004" and "2028-07-01" in e.value.detail
    with pytest.raises(Refusal):
        h.is_business_day(D(2025, 6, 30))
    with pytest.raises(Refusal):
        h.add_business_days(D(2028, 6, 28), 5)   # the count runs past 30 Jun 2028


def test_or_statutory_rolls_inside_the_range_exactly_like_roll_due_date():
    # 28 Feb 2027 is a Sunday; Mon 1 Mar 2027 is Labour Day (WA): Tue 2 Mar 2027 (ATO table).
    r = h.roll_due_date_or_statutory(D(2027, 2, 28))
    assert r.due == D(2027, 3, 2) and r.rolled and r.out_of_range is None
    assert r.as_dict() == h.roll_due_date(D(2027, 2, 28)).as_dict()
    assert "refusal" not in r.as_dict()


def test_or_statutory_outside_the_range_returns_the_statutory_date_with_a_note():
    # 28 Jul 2028 is a Friday (1 Jul 2028 is a Saturday, so 28 Jul is 27 days later: Friday). Data ends 30 Jun 2028.
    r = h.roll_due_date_or_statutory(D(2028, 7, 28))
    assert r.due == D(2028, 7, 28) and r.original == r.due and not r.rolled
    b = r.as_dict()
    assert b["rolled"] is False and b["due_date"] == "2028-07-28" and b["holiday_data_covers_date"] is False
    assert b["refusal"]["code"] == "AU-GEN-004" and b["refusal"]["message"] == refusal_catalogue()["AU-GEN-004"]["message"]
    assert "2028-07-28" in b["refusal"]["detail"]
    assert r.warnings and "AU-GEN-004" in r.warnings[0] and "2028-07-28" in r.warnings[0]


def test_or_statutory_outside_the_range_on_a_weekend_says_the_date_will_move():
    # 29 Jul 2028 is a Saturday.
    r = h.roll_due_date_or_statutory(D(2028, 7, 29))
    assert not r.rolled and "Saturday" in r.warnings[0] and "later" in r.warnings[0]


def test_or_statutory_still_refuses_before_the_range_start():
    r = h.roll_due_date_or_statutory(D(2025, 6, 30))
    assert r.out_of_range["code"] == "AU-GEN-004" and not r.rolled


def test_or_statutory_does_not_swallow_an_unconfirmed_holiday():
    # Mon 6 Mar 2028 is the WA Labour Day candidate date (unresolved, no draft allowed): FigureError, exactly as roll_due_date.
    with pytest.raises(FigureError):
        h.roll_due_date_or_statutory(D(2028, 3, 6))


def test_refusal_code_is_catalogued():
    assert "AU-GEN-004" in refusal_catalogue()


def test_ato_table_discrepancy_returns_statutory_date_and_warns():
    # Fri 25 Sep 2026 (VIC Friday before the AFL Grand Final): the ATO prints Mon 28 Sep, but 28 Sep 2026 is
    # King's Birthday (WA), so TAA 1953 s 8AAZMB(2) gives Tue 29 Sep 2026 (brief, section 5).
    r = h.roll_due_date(D(2026, 9, 25))
    assert r.due == D(2026, 9, 29)
    assert len(r.warnings) == 1 and "2026-09-28" in r.warnings[0] and "2026-09-29" in r.warnings[0]
    assert "King's Birthday" in r.warnings[0]
    # Sat 26 Sep 2026 rolls to the same statutory date, no ATO row for it, so no warning
    assert h.roll_due_date(D(2026, 9, 26)).warnings == []


def test_candidate_date_needs_draft_flag_wa_labour_day_2028():
    # Mon 6 Mar 2028 is a WA holiday under current law but the pending Bill would move it (data: unresolved, SUSPECT).
    with pytest.raises(FigureError) as e:
        h.roll_due_date(D(2028, 3, 6))
    assert e.value.code == "AU-GEN-001"
    f = Figures("2026-27", allow_draft=True)
    r = h.roll_due_date(D(2028, 3, 6), CW, f)
    assert r.due == D(2028, 3, 6) and r.alternative == D(2028, 3, 7) and r.draft
    assert f.draft is True
    assert any(k.startswith("holidays.unresolved.") for k in f.used)
    assert r.as_dict()["alternative_due_date"] == "2028-03-07" and r.warnings and "DRAFT" in r.warnings[0]


def test_candidate_date_on_a_walk_start_saturday():
    # Sat 4 Mar 2028 rolls onto Mon 6 Mar 2028, the candidate date: uncertain.
    with pytest.raises(FigureError) as e:
        h.roll_due_date(D(2028, 3, 4))
    assert e.value.code == "AU-GEN-001"
    r = h.roll_due_date(D(2028, 3, 4), CW, allow_draft=True)
    assert r.due == D(2028, 3, 6) and r.alternative == D(2028, 3, 7)


def test_candidate_date_does_not_touch_sa_regime_or_other_days():
    assert h.roll_due_date(D(2028, 3, 6), SA).due == D(2028, 3, 6)      # WA holiday is irrelevant to RevenueSA
    assert h.roll_due_date(D(2028, 3, 3)).due == D(2028, 3, 3)          # Friday before, not touched
    with pytest.raises(FigureError):
        h.roll_due_date(D(2028, 6, 5))                                  # WA Day candidate


def test_undeclared_afl_friday_2027_has_no_draft():
    # Fridays in Sep 2027 may be the VIC Friday before the AFL Grand Final; no date exists, so AU-GEN-003 even with allow_draft.
    for allow in (False, True):
        with pytest.raises(FigureError) as e:
            h.roll_due_date(D(2027, 9, 24), CW, allow_draft=allow)
        assert e.value.code == "AU-GEN-003"
    assert h.roll_due_date(D(2027, 9, 23)).due == D(2027, 9, 23)        # a Thursday is not affected
    assert h.roll_due_date(D(2027, 9, 24), SA).due == D(2027, 9, 24)    # VIC day is irrelevant to RevenueSA
    with pytest.raises(FigureError):
        h.business_days_after(D(2027, 9, 20), 5)                        # the count passes over Fri 24 Sep 2027


def test_record_reports_rule_source_in_figures_used():
    f = Figures("2026-27")
    h.roll_due_date(D(2027, 3, 26), CW, f)
    h.roll_due_date(D(2027, 3, 7), SA, f)
    used = {u["key"]: u for u in f.report()}
    assert used["holidays.commonwealth_tax"]["status"] == "VERIFIED"
    assert used["holidays.commonwealth_tax"]["source"].startswith("https://www.legislation.gov.au/")
    assert used["holidays.sa_state_tax"]["source"].startswith("https://www.legislation.sa.gov.au/")
    assert f.draft is False
