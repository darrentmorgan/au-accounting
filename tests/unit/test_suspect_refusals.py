"""GOAL gate 1: every 2026-27 figure that is still unpublished (SUSPECT, value null, with checked_at and the URL that was
checked) makes any calculator that needs it refuse with a code and never return a number, also in draft mode.

The keys are the ones named in the gate: the Medicare levy low-income thresholds, the home office fixed rate, and the
GIC and SIC rates for January to March 2027 and April to June 2027 (plus the 2027-28 years that are unpublished in the
same way). The ASIC fees are now VERIFIED (ASIC INFO 30) and the router uses them.
"""

import datetime as dt

import pytest

from au_tax.figures import FigureError, Figures, load_year
from au_tax.registry import run

MEDICARE_LOW_INCOME_KEYS = [
    "medicare.low_income_single_lower", "medicare.low_income_single_upper",
    "medicare.low_income_sapto_single_lower", "medicare.low_income_sapto_single_upper",
    "medicare.low_income_family_lower", "medicare.low_income_family_upper",
    "medicare.low_income_sapto_family_lower", "medicare.low_income_sapto_family_upper",
    "medicare.low_income_per_child_lower_add", "medicare.low_income_per_child_upper_add",
]
GIC_SIC_2027_KEYS = [
    "penalties_interest.gic_jan_mar_2027", "penalties_interest.gic_apr_jun_2027",
    "penalties_interest.sic_jan_mar_2027", "penalties_interest.sic_apr_jun_2027",
]
OTHER_UNPUBLISHED_2026_27 = ["car_home.home_office_fixed_rate_per_hour", "medicare.phi_rebate_from_2027_04_01"]


def raw(year, key):
    dom, name = key.split(".", 1)
    return load_year(year)[dom][name]


# ---------------------------------------------------------------- the figures themselves

@pytest.mark.parametrize("key", MEDICARE_LOW_INCOME_KEYS + GIC_SIC_2027_KEYS + OTHER_UNPUBLISHED_2026_27)
def test_2026_27_gate_1_figures_are_null_suspect_and_checked(key):
    fig = raw("2026-27", key)
    assert fig["value"] is None and fig["status"] == "SUSPECT"
    assert isinstance(fig["checked_at"], dt.date)          # the date the source URL was checked and found not to publish it
    assert fig["source"].startswith("https://")
    assert fig["notes"]


@pytest.mark.parametrize("key", MEDICARE_LOW_INCOME_KEYS + GIC_SIC_2027_KEYS + OTHER_UNPUBLISHED_2026_27)
@pytest.mark.parametrize("allow_draft", [False, True])
def test_reading_an_unpublished_figure_refuses_even_in_draft_mode(key, allow_draft):
    with pytest.raises(FigureError) as e:
        Figures("2026-27", allow_draft=allow_draft).get(key)
    assert e.value.code == "AU-GEN-003"       # no published value: a draft cannot help


# ---------------------------------------------------------------- calculators that need them

def refuses(tool, year, payload, allow_draft, code, needle):
    rc, out = run(tool, year, payload, allow_draft=allow_draft)
    assert rc in (3, 4), out
    assert out["refusal"]["code"] == code, out
    assert needle in out["refusal"]["detail"], out
    # never a number alongside the refusal
    for k in ("total_liability", "medicare_levy", "interest", "deduction", "gross_tax", "amount"):
        assert k not in out, (k, out)
    return out


@pytest.mark.parametrize("allow_draft", [False, True])
@pytest.mark.parametrize("payload", [
    {"taxable_income": 30000},                                                    # single, inside the possible low-income range
    {"taxable_income": 43000},                                                    # just under the current-law upper limit range
    {"taxable_income": 50000, "has_spouse": True, "spouse_taxable_income": 10000},        # family income 60,000: inside the range
    {"taxable_income": 30000, "has_spouse": True, "dependent_children": 2},               # family with children
])
def test_individual_tax_refuses_when_the_medicare_thresholds_decide_the_answer(payload, allow_draft):
    refuses("individual_income_tax", "2026-27", {**payload, "private_hospital_cover": True}, allow_draft,
            "AU-GEN-003", "medicare.low_income_single_lower")


def test_individual_tax_gives_a_number_only_where_current_law_shows_the_reduction_cannot_apply():
    # Income 60,000 is above the current-law upper limit (Medicare Levy Act as in force 1 Jul 2026) scaled by the phase-in
    # ratio 0.1 / (0.1 - 0.02) = 1.25: 35,013 x 1.25 = 43,766.25. So no low-income reduction can apply and the plain levy,
    # 2% x 60,000 = 1,200, is stated, with the assumption written out and every figure used VERIFIED.
    rc, out = run("individual_income_tax", "2026-27", {"taxable_income": 60000, "private_hospital_cover": True})
    assert rc == 0 and out["medicare_levy"] == 1200 and out["draft"] is False
    assert any("not yet set" in a for a in out["assumptions"])
    assert all(f["status"] == "VERIFIED" for f in out["figures_used"])
    assert not any(f["key"].startswith("medicare.low_income_single") for f in out["figures_used"])


@pytest.mark.parametrize("allow_draft", [False, True])
def test_seniors_offset_thresholds_unpublished_so_sapto_is_escalated_not_computed(allow_draft):
    rc, out = run("individual_income_tax", "2026-27", {"taxable_income": 30000, "sapto_eligible": True},
                  allow_draft=allow_draft)
    assert rc == 3 and out["refusal"]["code"] == "AU-IND-002"
    assert "total_liability" not in out


@pytest.mark.parametrize("year", ["2026-27", "2027-28"])
@pytest.mark.parametrize("allow_draft", [False, True])
def test_home_office_fixed_rate_refuses_while_the_rate_is_unpublished(year, allow_draft):
    # 500 hours would give a deduction of hours x rate; the rate has no published value, so there is no deduction.
    refuses("home_office_fixed_rate", year, {"hours_worked_from_home": 500, "hours_record_kept": True}, allow_draft,
            "AU-GEN-003", "car_home.home_office_fixed_rate_per_hour")


@pytest.mark.parametrize("charge", ["gic", "sic"])
@pytest.mark.parametrize("allow_draft", [False, True])
@pytest.mark.parametrize("from_date,to_date,quarter", [
    ("2027-01-05", "2027-01-20", "2027-01-01 to 2027-03-31"),      # January to March 2027
    ("2027-04-05", "2027-04-20", "2027-04-01 to 2027-06-30"),      # April to June 2027
    ("2026-12-20", "2027-01-10", "2027-01-01 to 2027-03-31"),      # spans a published quarter into an unpublished one
    ("2027-07-05", "2027-07-20", "2027-07-01 to 2028-06-30"),      # 2027-28: no quarter published
    ("2028-01-05", "2028-01-20", "2027-07-01 to 2028-06-30"),      # January to March 2028
    ("2028-04-05", "2028-04-20", "2027-07-01 to 2028-06-30"),      # April to June 2028
])
def test_gic_and_sic_refuse_in_quarters_with_no_published_rate(charge, allow_draft, from_date, to_date, quarter):
    rc, out = run("general_interest_charge", "2026-27", {"amount": 10000, "from_date": from_date, "to_date": to_date,
                                                         "charge": charge}, allow_draft=allow_draft)
    assert rc == 3 and out["refusal"]["code"] == "AU-PAYG-002", out
    assert "not yet published" in out["refusal"]["detail"], out
    assert "interest" not in out


def test_gic_still_computes_for_a_published_quarter_next_to_the_unpublished_ones():
    # Jul to Sep 2026 is published (VERIFIED): 1 day at the daily rate gives a number, so the refusals above come from the
    # missing rate and nothing else. 1,000 for 10 days at 0.000313150685 daily: 1,000 x (1.000313150685^10 - 1) = 3.14.
    rc, out = run("general_interest_charge", "2026-27", {"amount": 1000, "from_date": "2026-08-01", "to_date": "2026-08-11"})
    assert rc == 0 and out["interest"] == pytest.approx(3.14, abs=0.01)
    assert out["draft"] is False


# ---------------------------------------------------------------- ASIC fees are verified and the router uses them

@pytest.mark.parametrize("key,expected", [("asic.annual_review_proprietary", 342),
                                          ("asic.annual_review_special_purpose_proprietary", 70)])
def test_router_asic_fee_figures_are_verified_2026_27(key, expected):
    # ASIC INFO 30 (fees for commonly lodged documents), from 1 Jul 2026.
    assert Figures("2026-27").get(key) == expected


def test_router_lists_the_asic_review_fee_from_the_verified_figures():
    payload = {"entity_type": "company", "company_registration_date": "2015-03-15", "lodges_income_tax_return": False}
    rc, out = run("obligations_calendar", "2026-27", payload)
    assert rc == 0
    item = next(i for i in out["calendar"] if i["obligation"].startswith("ASIC annual review"))
    assert item["due_date"] == "2027-03-15"
    assert item["fee_aud"] == {"proprietary": 342, "special_purpose_proprietary": 70}
    assert item["figure_keys"] == ["asic.annual_review_proprietary", "asic.annual_review_special_purpose_proprietary"]
    assert "not verified" not in item["rule"]
    assert any("asic.gov.au" in s for s in item["sources"])
    assert not any(u["obligation"] == "ASIC annual review fee" for u in out["unverified"])


def test_router_asic_fee_unpublished_for_2027_28_gives_the_date_and_a_refusal_code_for_the_fee():
    payload = {"entity_type": "company", "company_registration_date": "2015-03-15", "lodges_income_tax_return": False}
    rc, out = run("obligations_calendar", "2027-28", payload)
    assert rc == 0
    item = next(i for i in out["calendar"] if i["obligation"].startswith("ASIC annual review"))
    assert item["due_date"] == "2028-03-15" and "fee_aud" not in item
    fee = next(u for u in out["unverified"] if u["obligation"] == "ASIC annual review fee")
    assert fee["refusal_code"] == "AU-GEN-003"
