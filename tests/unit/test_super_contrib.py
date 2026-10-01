"""super-contributions calculators. Expected values come from ATO worked examples (cited) or hand
computation from the statute shown step by step. None were produced by running the calculators."""

import pytest

from au_tax.figures import Figures
from au_tax.registry import load_all, run

TOOLS = ["concessional_cap_position", "bring_forward_nonconcessional", "div293_tax", "div296_tax",
         "co_contribution", "low_income_super_tax_offset", "spouse_offset", "downsizer_contribution"]


def calc(name, year, **kw):
    code, out = run(name, year, kw)
    assert code == 0, out
    return out


def refused(name, year, **kw):
    code, out = run(name, year, kw)
    assert code == 3, out
    return out["refusal"]["code"]


def approx(x):
    return pytest.approx(x, abs=0.01)


def test_all_registered():
    assert set(TOOLS) <= set(load_all())


def test_all_figures_verified_both_years():
    # every figure in this domain's overlay must be VERIFIED (no draft outputs in normal use)
    import yaml

    from au_tax.figures import RATES_DIR
    for y in ("2025-26", "2026-27"):
        figs = yaml.safe_load((RATES_DIR / f"{y}.d" / "super_contributions.yaml").read_text())["super"]
        assert figs and all(v["status"] == "VERIFIED" for v in figs.values()), y


# ================================================================ Division 296 (ATO worked examples)
# Source: ATO "How Division 296 tax is calculated" (last updated 29 Jun 2026).

def test_div296_ato_jordan():
    # TSB 30 Jun 2027 $4m, earnings $100,000: (4m-3m)/4m = 25%; TSE 25,000; tax 25,000 x 15% = 3,750
    out = calc("div296_tax", "2026-27", tsb_end_of_year=4_000_000, total_super_earnings=100_000)
    assert out["pct_over_lsbt"] == 25.0
    assert out["taxable_super_earnings"] == approx(25_000)
    assert out["div296_tax"] == approx(3_750)


def test_div296_ato_kelly_over_vlsbt():
    # TSB $12m, earnings $500,000: 75% -> 375,000 x 15% = 56,250; (12m-10m)/12m = 16.67% -> 83,350 x 10% = 8,335
    # total 64,585
    out = calc("div296_tax", "2026-27", tsb_end_of_year=12_000_000, total_super_earnings=500_000)
    assert out["pct_over_vlsbt"] == 16.67
    assert out["very_large_balance_earnings_component"] == approx(83_350)
    assert out["div296_tax"] == approx(64_585)


def test_div296_ato_leanne_three_funds():
    # earnings 20,000 + 5,000 + 3,500 = 28,500 (ATO example uses a DB fund; here all given as fund-reported,
    # non-DB, to test summing). TSB 3.5m: 14.29%; TSE 28,500 x 14.29% = 4,072.65; tax x 15% = 610.8975 -> 610.90
    out = calc("div296_tax", "2026-27", tsb_end_of_year=3_500_000, interests=[
        {"fund": "SMSF", "relevant_earnings": 20_000}, {"fund": "B", "relevant_earnings": 5_000},
        {"fund": "C", "relevant_earnings": 3_500}])
    assert out["total_super_earnings"] == approx(28_500)
    assert out["pct_over_lsbt"] == 14.29
    assert out["taxable_super_earnings"] == approx(4_072.65)
    assert out["div296_tax"] == approx(610.90)


def test_div296_ato_george_excluded_interest():
    # Judges' pension interest $9m (excluded, earnings nil) + accumulation $2m earning $130,000; TSB 11m.
    # 8/11 = 72.727 -> 72.73%; 1/11 = 9.0909 -> 9.09%. TSE 130,000 x 72.73% = 94,549; VLSB 130,000 x 9.09% = 11,817
    # tax 94,549 x 15% = 14,182.35 + 11,817 x 10% = 1,181.70 = 15,364.05
    out = calc("div296_tax", "2026-27", tsb_end_of_year=11_000_000, interests=[
        {"fund": "Judges", "relevant_earnings": 400_000, "excluded": True},
        {"fund": "Accumulation", "relevant_earnings": 130_000}])
    assert out["taxable_super_earnings"] == approx(94_549)
    assert out["very_large_balance_earnings_component"] == approx(11_817)
    assert out["div296_tax"] == approx(15_364.05)


def test_div296_mary_transitional_closing_only():
    # ATO Mary: TSB 3.15m at 30 Jun 2026 but 2.95m at 30 Jun 2027 -> 2026-27 uses closing only -> no tax
    out = calc("div296_tax", "2026-27", tsb_start_of_year=3_150_000, tsb_end_of_year=2_950_000,
               total_super_earnings=80_000)
    assert out["applies"] is False and out["div296_tax"] == 0


def test_div296_death_in_2026_27_not_liable():
    # ATO Alex: dies 15 Feb 2027 -> never liable for 2026-27
    out = calc("div296_tax", "2026-27", tsb_end_of_year=4_200_000, total_super_earnings=150_000, died_in_year=True)
    assert out["div296_tax"] == 0


def test_div296_rounding_half_up():
    # TSB 6.4m: 3.4/6.4 = 53.125% -> rounds half up to 53.13 (s296-40(3)); earnings 100,000 -> TSE 53,130
    # tax = 53,130 x 15% = 7,969.50
    out = calc("div296_tax", "2026-27", tsb_end_of_year=6_400_000, total_super_earnings=100_000)
    assert out["pct_over_lsbt"] == 53.13
    assert out["div296_tax"] == approx(7_969.50)


def test_div296_negative_earnings_nil():
    out = calc("div296_tax", "2026-27", tsb_end_of_year=5_000_000, total_super_earnings=-20_000)
    assert out["div296_tax"] == 0


def test_div296_not_in_force_2025_26():
    out = calc("div296_tax", "2025-26", tsb_end_of_year=5_000_000, total_super_earnings=100_000)
    assert out["applies"] is False and out["div296_tax"] == 0


def test_div296_balance_movement_estimate_refused():
    assert refused("div296_tax", "2026-27", tsb_end_of_year=5_000_000,
                   earnings_estimate_from_balances=True) == "AU-SUPER-005"


def test_div296_valuation_dispute_and_db_refused():
    assert refused("div296_tax", "2026-27", tsb_end_of_year=5e6, total_super_earnings=1e5,
                   valuation_dispute=True) == "AU-SUPER-005"
    assert refused("div296_tax", "2026-27", tsb_end_of_year=5e6, total_super_earnings=1e5,
                   has_defined_benefit_interest=True) == "AU-SUPER-001"


def test_div296_child_recipient_exempt():
    out = calc("div296_tax", "2026-27", tsb_end_of_year=5e6, total_super_earnings=1e5, child_recipient_income_stream=True)
    assert out["div296_tax"] == 0


# ================================================================ concessional cap

def test_cc_under_cap_2026_27():
    # cap 32,500; SG 15,000 + SS 5,000 = 20,000 -> room 12,500; unused 12,500 carried from 2026-27
    out = calc("concessional_cap_position", "2026-27", employer_contributions=15_000, salary_sacrifice=5_000)
    assert out["general_cap"] == 32_500
    assert out["remaining_room"] == approx(12_500)
    assert out["excess_concessional_contributions"] == 0
    assert out["unused_carried_to_next_year"]["2026-27"] == approx(12_500)


def test_cc_carry_forward_replay_2026_27():
    # Window for 2026-27: 2021-22 to 2025-26. Caps (ATO Table 1.1): 27,500 x3, 30,000 x2.
    # 2021-22: 10,000 -> unused 17,500; 2022-23, 2023-24: 27,500 -> nil; 2024-25: 20,000 -> 10,000; 2025-26: 30,000 -> nil
    # 2026-27: 60,000 contributed, cap 32,500, excess before carry forward 27,500; TSB 300,000 < 500,000
    # apply earliest first: 2021-22 17,500 then 2024-25 10,000 -> no excess
    out = calc("concessional_cap_position", "2026-27", employer_contributions=20_000, salary_sacrifice=40_000,
               tsb_prior_30_june=300_000, prior_years=[
                   {"income_year": "2021-22", "concessional_contributions": 10_000},
                   {"income_year": "2022-23", "concessional_contributions": 27_500},
                   {"income_year": "2023-24", "concessional_contributions": 27_500},
                   {"income_year": "2024-25", "concessional_contributions": 20_000},
                   {"income_year": "2025-26", "concessional_contributions": 30_000}])
    assert out["carry_forward"]["available_unused_total"] == approx(27_500)
    assert out["carry_forward"]["applied_by_year"] == {"2021-22": 17_500, "2024-25": 10_000}
    assert out["available_cap"] == approx(60_000)
    assert out["excess_concessional_contributions"] == 0


def test_cc_carry_forward_blocked_by_tsb():
    # same facts, TSB 500,000 (not less than the limit) -> excess 27,500
    out = calc("concessional_cap_position", "2026-27", employer_contributions=20_000, salary_sacrifice=40_000,
               tsb_prior_30_june=500_000, unapplied_unused=[{"income_year": "2021-22", "amount": 17_500},
                                                           {"income_year": "2024-25", "amount": 10_000}])
    assert out["carry_forward"]["eligible"] is False
    assert out["excess_concessional_contributions"] == approx(27_500)
    # offset 15% x 27,500 = 4,125; max release 85% x 27,500 = 23,375
    assert out["excess_treatment"]["non_refundable_offset"] == approx(4_125)
    assert out["excess_treatment"]["max_release_amount"] == approx(23_375)


def test_cc_expired_year_ignored_2026_27():
    # 2020-21 unused amounts expired at the end of 2025-26 (5 years): ignored for 2026-27
    out = calc("concessional_cap_position", "2026-27", employer_contributions=40_000, tsb_prior_30_june=100_000,
               unapplied_unused=[{"income_year": "2020-21", "amount": 25_000}, {"income_year": "2023-24", "amount": 5_000}])
    # excess 7,500 before carry forward; only 2023-24 5,000 available -> excess 2,500
    assert out["carry_forward"]["available_unused_total"] == approx(5_000)
    assert out["excess_concessional_contributions"] == approx(2_500)


def test_cc_replay_with_mid_period_carry_forward_2025_26():
    # 2025-26 window 2020-21..2024-25. Caps: 2020-21 25,000; 2021-22..2023-24 27,500; 2024-25 30,000.
    # 2020-21: 5,000 -> unused 20,000
    # 2021-22: 7,500 -> unused 20,000
    # 2022-23: 47,500 (TSB 200k) -> excess 20,000 met from 2020-21 (earliest) -> 2020-21 left 0
    # 2023-24: 27,500 -> nil; 2024-25: 25,000 -> unused 5,000
    # 2025-26: cap 30,000, contributions 50,000 -> need 20,000: 2021-22 20,000 -> no excess, 2024-25 5,000 left
    out = calc("concessional_cap_position", "2025-26", employer_contributions=50_000, tsb_prior_30_june=250_000,
               prior_years=[
                   {"income_year": "2020-21", "concessional_contributions": 5_000},
                   {"income_year": "2021-22", "concessional_contributions": 7_500},
                   {"income_year": "2022-23", "concessional_contributions": 47_500, "tsb_prior_30_june": 200_000},
                   {"income_year": "2023-24", "concessional_contributions": 27_500},
                   {"income_year": "2024-25", "concessional_contributions": 25_000}])
    assert out["carry_forward"]["applied_by_year"] == {"2021-22": 20_000}
    assert out["excess_concessional_contributions"] == 0
    assert out["unused_carried_to_next_year"] == {"2024-25": 5_000}


def test_cc_replay_needs_tsb_for_excess_year():
    assert refused("concessional_cap_position", "2025-26", employer_contributions=10_000, prior_years=[
        {"income_year": "2023-24", "concessional_contributions": 5_000},
        {"income_year": "2024-25", "concessional_contributions": 40_000}]) == "AU-SUPER-008"


def test_cc_noi_missing_reclassifies_personal():
    # personal 10,000 without an acknowledged notice -> not concessional
    out = calc("concessional_cap_position", "2026-27", employer_contributions=20_000, personal_deductible=10_000,
               noi_acknowledged=False)
    assert out["concessional_contributions"]["total"] == approx(20_000)
    assert out["personal_reclassified_as_non_concessional"] == approx(10_000)


def test_cc_excess_extra_tax_2026_27():
    # TI 150,000 + excess 5,000: both in the 37% bracket (135,001-190,000) -> 1,850; Medicare 2% x 5,000 = 100
    # extra 1,950; offset 15% x 5,000 = 750; net 1,200
    out = calc("concessional_cap_position", "2026-27", employer_contributions=37_500, tsb_prior_30_june=900_000,
               taxable_income_excluding_excess=150_000)
    t = out["excess_treatment"]
    assert out["excess_concessional_contributions"] == approx(5_000)
    assert t["extra_tax_and_levy_before_offset"] == approx(1_950)
    assert t["net_extra_tax"] == approx(1_200)


def test_cc_defined_benefit_refused():
    assert refused("concessional_cap_position", "2026-27", employer_contributions=1,
                   has_defined_benefit_interest=True) == "AU-SUPER-001"


# ================================================================ non-concessional / bring forward
# ATO non-concessional contributions cap page: 2026-27 tiers <1.84m 390k/3y; 1.84m-<1.97m 260k/2y;
# 1.97m-<2.1m 130k, no bring forward; >=2.1m nil. 2025-26: <1.76m 360k; <1.88m 240k; <2m 120k; nil.

@pytest.mark.parametrize("tsb,first,years,status", [
    (0, 390_000, 3, "annual_cap_bring_forward_available"),
    (1_839_999, 390_000, 3, "annual_cap_bring_forward_available"),
    (1_840_000, 260_000, 2, "annual_cap_bring_forward_available"),
    (1_969_999, 260_000, 2, "annual_cap_bring_forward_available"),
    (1_970_000, 130_000, 0, "annual_cap_only"),
    (2_099_999, 130_000, 0, "annual_cap_only"),
])
def test_bf_tiers_2026_27(tsb, first, years, status):
    out = calc("bring_forward_nonconcessional", "2026-27", age_at_1_july=60, tsb_prior_30_june=tsb)
    assert out["status"] == status
    assert out["max_first_year_cap"] == first
    assert out["bring_forward_period_years"] == years


def test_bf_matches_rates_file_tiers_both_years():
    # the statutory cap-space rule must reproduce the ATO tier table stored in each base rates file
    for y in ("2025-26", "2026-27"):
        for t in Figures(y).get("super.bring_forward_tiers"):
            for tsb in (t["from"], (t["to"] or t["from"] + 1) - 1):
                out = calc("bring_forward_nonconcessional", y, age_at_1_july=50, tsb_prior_30_june=tsb)
                first = out.get("max_first_year_cap", out["cap_this_year"])
                assert first == t["cap_first_year"], (y, tsb)


def test_bf_nil_at_tbc():
    out = calc("bring_forward_nonconcessional", "2026-27", age_at_1_july=60, tsb_prior_30_june=2_100_000, planned_ncc=10_000)
    assert out["cap_this_year"] == 0
    assert out["excess_non_concessional_contributions"] == approx(10_000)
    assert "AU-SUPER-003" in out["escalations"]


def test_bf_age_75_no_bring_forward():
    # 75 on 1 July -> not under 75 at any time in the year -> annual cap only
    out = calc("bring_forward_nonconcessional", "2026-27", age_at_1_july=75, tsb_prior_30_june=500_000)
    assert out["bring_forward_period_years"] == 0 and out["cap_this_year"] == 130_000
    out = calc("bring_forward_nonconcessional", "2026-27", age_at_1_july=74, tsb_prior_30_june=500_000)
    assert out["bring_forward_period_years"] == 3


def test_bf_existing_period_not_indexed():
    # triggered 2025-26 (cap 120,000) 3-year period: 360,000 fixed; used 200,000 -> 160,000 left in 2026-27
    # (ATO: indexation to 130,000 does not apply to an existing period)
    out = calc("bring_forward_nonconcessional", "2026-27", age_at_1_july=60, tsb_prior_30_june=1_000_000,
               prior_trigger={"trigger_year": "2025-26", "period_years": 3, "ncc_since_trigger": 200_000},
               planned_ncc=170_000)
    assert out["status"] == "within_existing_bring_forward_period"
    assert out["period"]["bring_forward_cap"] == 360_000
    assert out["cap_this_year"] == approx(160_000)
    assert out["excess_non_concessional_contributions"] == approx(10_000)


def test_bf_existing_period_nil_when_tsb_at_tbc():
    out = calc("bring_forward_nonconcessional", "2026-27", age_at_1_july=60, tsb_prior_30_june=2_150_000,
               prior_trigger={"trigger_year": "2024-25", "period_years": 3, "ncc_since_trigger": 120_000})
    assert out["cap_this_year"] == 0


def test_bf_two_year_period_ended():
    # 2-year period triggered 2024-25 covers 2024-25 and 2025-26 -> 2026-27 is fresh
    out = calc("bring_forward_nonconcessional", "2026-27", age_at_1_july=60, tsb_prior_30_june=1_000_000,
               prior_trigger={"trigger_year": "2024-25", "period_years": 2, "ncc_since_trigger": 240_000},
               planned_ncc=390_000)
    assert out["triggers_bring_forward"] is True
    assert out["excess_non_concessional_contributions"] == 0


def test_bf_trigger_2026_27_planned_300k():
    # TSB 1.5m -> 3-year, 390,000; 300,000 contributed triggers; 90,000 left for the rest of the period
    out = calc("bring_forward_nonconcessional", "2026-27", age_at_1_july=60, tsb_prior_30_june=1_500_000, planned_ncc=300_000)
    assert out["triggers_bring_forward"] is True
    assert out["remaining_in_period_after_this_year"] == approx(90_000)


def test_bf_under_annual_cap_does_not_trigger():
    out = calc("bring_forward_nonconcessional", "2026-27", age_at_1_july=60, tsb_prior_30_june=1_500_000, planned_ncc=130_000)
    assert out["triggers_bring_forward"] is False and out["excess_non_concessional_contributions"] == 0


# ================================================================ Division 293 (hand computation, ss293-20 to 293-30)

def test_div293_excess_smaller():
    # TI 200,000 + RFB 30,000 + NFIL 10,000 = 240,000; + LTC 25,000 = 265,000; excess 15,000 < 25,000
    # tax 15% x 15,000 = 2,250
    out = calc("div293_tax", "2026-27", taxable_income=200_000, reportable_fringe_benefits=30_000,
               net_investment_loss=10_000, concessional_contributions=25_000)
    assert out["taxable_contributions"] == approx(15_000)
    assert out["div293_tax"] == approx(2_250)


def test_div293_contributions_smaller():
    # TI 290,000 + LTC 25,000 = 315,000; excess 65,000 > 25,000 -> 25,000 x 15% = 3,750
    out = calc("div293_tax", "2025-26", taxable_income=290_000, concessional_contributions=25_000)
    assert out["div293_tax"] == approx(3_750)


def test_div293_below_threshold():
    # 220,000 + 30,000 = 250,000, not over -> nil
    out = calc("div293_tax", "2026-27", taxable_income=220_000, concessional_contributions=30_000)
    assert out["div293_tax"] == 0 and out["applies"] is False


def test_div293_excess_cc_excluded():
    # CC 40,000 incl. excess 7,500 -> LTC 32,500; TI 300,000 (includes the excess) -> lesser is 32,500 -> 4,875
    out = calc("div293_tax", "2026-27", taxable_income=300_000, concessional_contributions=40_000,
               excess_concessional_contributions=7_500)
    assert out["low_tax_contributions"] == approx(32_500)
    assert out["div293_tax"] == approx(4_875)


# ================================================================ co-contribution (Co-contribution Act ss6-11)

def test_cocontrib_ato_angelo_max():
    # ATO example: income 35,000, contributes 1,040 -> maximum 500
    out = calc("co_contribution", "2026-27", personal_nonconcessional_contributions=1_040, assessable_income=35_000,
               eligible_income=35_000, age_at_end_of_year=30, tsb_prior_30_june=50_000)
    assert out["co_contribution"] == 500


def test_cocontrib_taper_2026_27():
    # income 55,000: max = 500 - 0.03333 x (55,000 - 49,293) = 500 - 0.03333 x 5,707 = 500 - 190.21431 = 309.78569
    # matched 50% x 1,000 = 500 -> 309.78569 rounded up to 5 cents = 309.80
    out = calc("co_contribution", "2026-27", personal_nonconcessional_contributions=1_000, assessable_income=55_000,
               eligible_income=55_000, age_at_end_of_year=30, tsb_prior_30_june=50_000)
    assert out["co_contribution"] == approx(309.80)


def test_cocontrib_minimum_20_and_cutout():
    # 64,000: 500 - 0.03333 x 14,707 = 500 - 490.18431 = 9.81569 -> below 20 -> 20 (s11)
    out = calc("co_contribution", "2026-27", personal_nonconcessional_contributions=1_000, assessable_income=64_000,
               eligible_income=64_000, age_at_end_of_year=30, tsb_prior_30_june=50_000)
    assert out["co_contribution"] == 20
    out = calc("co_contribution", "2026-27", personal_nonconcessional_contributions=1_000, assessable_income=64_293,
               eligible_income=64_293, age_at_end_of_year=30, tsb_prior_30_june=50_000)
    assert out["eligible"] is False and out["co_contribution"] == 0


def test_cocontrib_2025_26_thresholds():
    # 2025-26 lower 47,488: income 50,000 -> 500 - 0.03333 x 2,512 = 500 - 83.72496 = 416.27504; contribution 600 -> 300
    out = calc("co_contribution", "2025-26", personal_nonconcessional_contributions=600, assessable_income=50_000,
               eligible_income=50_000, age_at_end_of_year=30, tsb_prior_30_june=50_000)
    assert out["co_contribution"] == 300


def test_cocontrib_ineligible_tests():
    base = dict(personal_nonconcessional_contributions=1_000, assessable_income=30_000, eligible_income=30_000,
                age_at_end_of_year=30, tsb_prior_30_june=50_000)
    assert calc("co_contribution", "2026-27", **{**base, "age_at_end_of_year": 71})["eligible"] is False
    assert calc("co_contribution", "2026-27", **{**base, "eligible_income": 2_000})["eligible"] is False
    assert calc("co_contribution", "2026-27", **{**base, "tsb_prior_30_june": 2_100_000})["eligible"] is False
    assert calc("co_contribution", "2026-27", **{**base, "temporary_visa_holder": True})["eligible"] is False


# ================================================================ LISTO (s12E)

@pytest.mark.parametrize("cc,expected", [(1_000, 150), (3_600, 500), (50, 10)])
def test_listo_amounts(cc, expected):
    # 15% x 1,000 = 150; 15% x 3,600 = 540 -> capped 500; 15% x 50 = 7.50 -> minimum 10
    out = calc("low_income_super_tax_offset", "2026-27", adjusted_taxable_income=30_000, concessional_contributions=cc,
               total_income=30_000, eligible_income=30_000)
    assert out["listo"] == expected


def test_listo_over_limit():
    out = calc("low_income_super_tax_offset", "2026-27", adjusted_taxable_income=37_001, concessional_contributions=4_000,
               total_income=37_001, eligible_income=37_001)
    assert out["listo"] == 0


# ================================================================ spouse offset (ss290-230, 290-235)

def test_spouse_offset_full():
    # spouse income 30,000 < 37,000 -> base 3,000; contributions 3,000 -> 18% x 3,000 = 540
    out = calc("spouse_offset", "2026-27", contributions_for_spouse=3_000, spouse_assessable_income=30_000,
               spouse_tsb_prior_30_june=100_000)
    assert out["spouse_offset"] == 540


def test_spouse_offset_reduced():
    # spouse income 38,500: base 3,000 - 1,500 = 1,500; contributions 3,000 -> 18% x 1,500 = 270
    out = calc("spouse_offset", "2026-27", contributions_for_spouse=3_000, spouse_assessable_income=36_000,
               spouse_reportable_employer_super=2_500, spouse_tsb_prior_30_june=100_000)
    assert out["spouse_income"] == approx(38_500)
    assert out["spouse_offset"] == approx(270)


def test_spouse_offset_small_contribution_and_cutout():
    # 1,000 contributed, income 20,000 -> 18% x 1,000 = 180
    out = calc("spouse_offset", "2025-26", contributions_for_spouse=1_000, spouse_assessable_income=20_000,
               spouse_tsb_prior_30_june=100_000)
    assert out["spouse_offset"] == approx(180)
    out = calc("spouse_offset", "2025-26", contributions_for_spouse=3_000, spouse_assessable_income=40_000,
               spouse_tsb_prior_30_june=100_000)
    assert out["eligible"] is False


def test_spouse_offset_tsb_blocks():
    # spouse TSB at the prior 30 June >= general TBC (2.0m in 2025-26) -> no offset
    out = calc("spouse_offset", "2025-26", contributions_for_spouse=3_000, spouse_assessable_income=10_000,
               spouse_tsb_prior_30_june=2_000_000)
    assert out["spouse_offset"] == 0


# ================================================================ downsizer (s292-102)

def test_downsizer_limits():
    # proceeds 1,000,000, age 60, 20 years -> min(300,000, 1,000,000) = 300,000
    out = calc("downsizer_contribution", "2026-27", age_at_contribution=60, ownership_years=20, days_after_settlement=30,
               capital_proceeds=1_000_000)
    assert out["maximum_downsizer_contribution"] == 300_000
    # proceeds 400,000 with spouse already contributing 250,000 from the same sale -> 150,000
    out = calc("downsizer_contribution", "2026-27", age_at_contribution=60, ownership_years=20, days_after_settlement=30,
               capital_proceeds=400_000, other_downsizer_from_this_sale=250_000, planned_contribution=200_000)
    assert out["maximum_downsizer_contribution"] == 150_000
    assert out["not_covered_counts_as_non_concessional"] == approx(50_000)


def test_downsizer_ineligible():
    out = calc("downsizer_contribution", "2026-27", age_at_contribution=54, ownership_years=20, days_after_settlement=30,
               capital_proceeds=500_000)
    assert out["eligible"] is False
    out = calc("downsizer_contribution", "2026-27", age_at_contribution=60, ownership_years=9, days_after_settlement=91,
               capital_proceeds=500_000)
    assert len(out["reasons_not_eligible"]) == 2


def test_bf_room_after_small_contribution_2026_27():
    # TSB 1.9m -> cap space 200,000: > 130,000 but not > 260,000 -> 2-year period, first-year cap 260,000.
    # 50,000 already contributed (not yet a trigger) -> further 210,000 possible without excess
    out = calc("bring_forward_nonconcessional", "2026-27", age_at_1_july=58, tsb_prior_30_june=1_900_000, planned_ncc=50_000)
    assert out["further_room_this_year_without_excess"] == approx(210_000)
    assert out["excess_non_concessional_contributions"] == 0
