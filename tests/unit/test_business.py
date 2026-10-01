"""sole-trader-business calculators. Expected values come from ATO/legislation worked examples (cited) or
hand computations shown step by step. None were produced by running the calculators."""

import pytest

from au_tax.registry import load_all, run


def ok(name, year, **kw):
    code, out = run(name, year, kw)
    assert code == 0, out
    return out


def refused(name, year, **kw):
    code, out = run(name, year, kw)
    return code, out


def approx(x):
    return pytest.approx(x, abs=0.01)


def test_registered():
    reg = load_all()
    for n in ("small_business_income_tax_offset", "simplified_depreciation", "car_expense_cents_per_km",
              "home_office_fixed_rate", "non_commercial_loss_test", "psi_tests"):
        assert n in reg


# ---------------------------------------------------------------- SBITO

def test_sbito_capped_at_1000():
    # 2026-27 resident rates: tax at 80,000 = 4,020 + 0.30 x (80,000 - 45,000) = 14,520
    # all income is small business income: share 1; 16% x 14,520 = 2,323.20 -> cap 1,000
    out = ok("small_business_income_tax_offset", "2026-27", aggregated_turnover=400000,
             net_small_business_income=80000, taxable_income=80000)
    assert out["basic_income_tax_liability"] == approx(14520)
    assert out["offset_before_cap"] == approx(2323.20)
    assert out["offset"] == 1000 and out["cap_applied"] is True


def test_sbito_low_income_uncapped():
    # tax at 30,000 = 0.15 x (30,000 - 18,200) = 1,770; 16% x 1,770 = 283.20
    out = ok("small_business_income_tax_offset", "2026-27", aggregated_turnover=100000,
             net_small_business_income=30000, taxable_income=30000)
    assert out["offset"] == approx(283.20)


def test_sbito_proportion_of_taxable_income():
    # tax at 60,000 = 4,020 + 0.30 x 15,000 = 8,520; business share 30,000/60,000 = 0.5 -> 4,260
    # 16% x 4,260 = 681.60
    out = ok("small_business_income_tax_offset", "2026-27", aggregated_turnover=100000,
             net_small_business_income=30000, taxable_income=60000)
    assert out["business_share_of_taxable_income"] == pytest.approx(0.5)
    assert out["offset"] == approx(681.60)


def test_sbito_2025_26_rate_scale():
    # 2025-26: 16% over 18,200; tax at 30,000 = 0.16 x 11,800 = 1,888; 16% x 1,888 = 302.08
    out = ok("small_business_income_tax_offset", "2025-26", aggregated_turnover=100000,
             net_small_business_income=30000, taxable_income=30000)
    assert out["offset"] == approx(302.08)


def test_sbito_business_income_above_taxable_income_share_capped_at_one():
    # NSBI 50,000 > TI 30,000 (deductions elsewhere): share 1 -> same as full basic liability: 283.20
    out = ok("small_business_income_tax_offset", "2026-27", aggregated_turnover=100000,
             net_small_business_income=50000, taxable_income=30000)
    assert out["offset"] == approx(283.20)


def test_sbito_turnover_threshold_is_five_million_not_ten():
    # ATO: aggregated turnover must be below 5m (SBE threshold 10m does not apply)
    below = ok("small_business_income_tax_offset", "2026-27", aggregated_turnover=4999999,
               net_small_business_income=30000, taxable_income=30000)
    at = ok("small_business_income_tax_offset", "2026-27", aggregated_turnover=5000000,
            net_small_business_income=30000, taxable_income=30000)
    six_m = ok("small_business_income_tax_offset", "2026-27", aggregated_turnover=6000000,
               net_small_business_income=30000, taxable_income=30000)
    assert below["eligible"] and below["offset"] > 0
    assert not at["eligible"] and at["offset"] == 0
    assert not six_m["eligible"]


def test_sbito_supplied_basic_liability_and_partnership_share():
    # supplied basic liability 5,000; TI 50,000; sole trader 15,000 + partnership share 10,000 = 25,000
    # share 0.5; 0.16 x 5,000 x 0.5 = 400
    out = ok("small_business_income_tax_offset", "2026-27", aggregated_turnover=1000000,
             net_small_business_income=15000, partnership_or_trust_net_small_business_income=10000,
             taxable_income=50000, basic_income_tax_liability=5000)
    assert out["offset"] == approx(400)


def test_sbito_foreign_resident_scale():
    # foreign resident 30% to 135,000: tax at 40,000 = 12,000; 16% = 1,920 -> cap 1,000
    out = ok("small_business_income_tax_offset", "2026-27", aggregated_turnover=100000,
             net_small_business_income=40000, taxable_income=40000, residency="foreign")
    assert out["basic_income_tax_liability"] == approx(12000)
    assert out["offset"] == 1000


def test_sbito_nil_taxable_income():
    out = ok("small_business_income_tax_offset", "2026-27", aggregated_turnover=1000,
             net_small_business_income=0, taxable_income=0)
    assert out["offset"] == 0


# ---------------------------------------------------------------- simplified depreciation

def asset(name, cost, d, pct=100, typ="general"):
    return {"name": name, "cost": cost, "first_used_date": d, "business_use_percent": pct, "asset_type": typ}


def dep(year, **kw):
    kw.setdefault("aggregated_turnover", 500000)
    return ok("simplified_depreciation", year, **kw)


def test_iawo_below_threshold_2026_27():
    # 19,999 < 20,000 threshold (Act 71 Sch 2), 100% business -> deduction 19,999, nothing pooled
    out = dep("2026-27", assets=[asset("laptop rig", 19999, "2026-07-01")])
    assert out["instant_asset_write_off_total"] == approx(19999)
    assert out["pool"]["closing_balance"] == 0
    assert out["total_depreciation_deduction"] == approx(19999)


def test_asset_at_threshold_goes_to_pool():
    # cost must be LESS than 20,000. 20,000 pooled: E = 20,000 (not below threshold) so pool is depreciated:
    # 15% x 20,000 = 3,000; closing 17,000
    out = dep("2026-27", assets=[asset("ute", 20000, "2026-08-01")])
    assert out["instant_asset_write_off_total"] == 0
    assert out["pool"]["deduction"] == approx(3000)
    assert out["pool"]["closing_balance"] == approx(17000)


def test_iawo_business_use_apportioned():
    # ATO Example 1 shape: 18,000 x 50% = 9,000 (asset cost below threshold, deduction is business portion)
    out = dep("2026-27", assets=[asset("car", 18000, "2026-09-01", pct=50)])
    assert out["instant_asset_write_off_total"] == approx(9000)


def test_pool_below_threshold_written_off_act_example():
    # Act 71 Sch 2 item 8 example (Cassidy): opening 28,500 + 21,000 x 80% = 16,800 - sold car 29,600 (100%)
    # = 15,700 < 20,000 -> deduct 15,700, closing 0. (Dates moved to 2026-27 for this test.)
    out = dep("2026-27", opening_pool_balance=28500,
              assets=[asset("mower", 21000, "2026-08-10", pct=80)],
              disposals=[{"name": "car", "termination_value": 29600, "business_use_percent": 100, "was_in_pool": True}])
    assert out["pool"]["balance_before_deduction"] == approx(15700)
    assert out["pool"]["deduction"] == approx(15700)
    assert out["pool"]["closing_balance"] == 0


def test_pool_ato_loretta_worked_example():
    # ATO pool calculations Example 2: opening 100,000; new 28,000 (pooled); sold 8,000; plus 15,000 trailer written off
    # E = 100,000 + 28,000 - 8,000 = 120,000 (>= threshold)
    # pool deduction = 30% x 100,000 + 15% x 28,000 = 30,000 + 4,200 = 34,200; closing 120,000 - 34,200 = 85,800
    # total = 15,000 + 34,200 = 49,200
    out = dep("2026-27", opening_pool_balance=100000,
              assets=[asset("trailer 1", 15000, "2026-12-01"), asset("trailer 2", 28000, "2027-02-02")],
              disposals=[{"name": "old trailer", "termination_value": 8000}])
    assert out["pool"]["deduction"] == approx(34200)
    assert out["pool"]["closing_balance"] == approx(85800)
    assert out["total_depreciation_deduction"] == approx(49200)


def test_pool_ato_worksheet_with_cost_additions():
    # ATO worksheet shape: opening 30,200; new pooled 29,930; cost additions 350; disposals 8,000
    # E = 30,200 + 29,930 + 350 - 8,000 = 52,480
    # F = 30% x 30,200 = 9,060; G+H = 15% x (29,930 + 350) = 15% x 30,280 = 4,542; total 13,602
    # closing = 52,480 - 13,602 = 38,878
    out = dep("2026-27", opening_pool_balance=30200,
              assets=[asset("machine", 29930, "2026-10-01")],
              cost_additions=[{"name": "upgrade", "cost": 350}],
              disposals=[{"name": "old", "termination_value": 8000}])
    assert out["pool"]["balance_before_deduction"] == approx(52480)
    assert out["pool"]["deduction"] == approx(13602)
    assert out["pool"]["closing_balance"] == approx(38878)


def test_car_over_limit_pooled_at_car_limit():
    # 2026-27 car limit 69,883 (ATO); car cost 80,000 > threshold; business use 75%
    # pooled = 69,883 x 0.75 = 52,412.25; 15% = 7,861.8375; closing = 52,412.25 - 7,861.8375 = 44,550.4125
    out = dep("2026-27", assets=[asset("car", 80000, "2026-09-15", pct=75, typ="passenger_car")])
    assert out["pool"]["added_this_year"] == approx(52412.25)
    assert out["pool"]["deduction"] == approx(7861.84)
    assert out["pool"]["closing_balance"] == approx(44550.41)


def test_car_under_threshold_uses_cost_not_limit():
    # cost 19,000 < threshold: IAWO on full cost x 100%
    out = dep("2026-27", assets=[asset("small car", 19000, "2026-09-15", typ="passenger_car")])
    assert out["instant_asset_write_off_total"] == approx(19000)


def test_opening_pool_exactly_at_threshold_is_depreciated():
    # E = 20,000 not below the threshold -> 30% x 20,000 = 6,000; closing 14,000
    out = dep("2026-27", opening_pool_balance=20000)
    assert out["pool"]["deduction"] == approx(6000)
    assert out["pool"]["closing_balance"] == approx(14000)


def test_opening_pool_below_threshold_fully_deducted():
    out = dep("2026-27", opening_pool_balance=15000)
    assert out["pool"]["deduction"] == approx(15000)
    assert out["pool"]["closing_balance"] == 0


def test_negative_pool_becomes_assessable_income():
    # opening 5,000 - disposal 8,000 = -3,000 -> assessable 3,000; closing nil (ATO pool page)
    out = dep("2026-27", opening_pool_balance=5000,
              disposals=[{"name": "van", "termination_value": 8000}])
    assert out["assessable_income_from_disposals"] == approx(3000)
    assert out["pool"]["closing_balance"] == 0 and out["pool"]["deduction"] == 0


def test_disposal_of_written_off_asset_is_assessable():
    # ATO: previously fully written off asset sold for 4,000 at 60% business use -> 2,400 assessable
    out = dep("2026-27", disposals=[{"name": "tool", "termination_value": 4000, "business_use_percent": 60, "was_in_pool": False}])
    assert out["assessable_income_from_disposals"] == approx(2400)


def test_first_improvement_to_written_off_asset_immediate():
    # ATO pool page Example 5: tow ball 300 on a car written off at 50% -> 150
    out = dep("2026-27", cost_additions=[{"name": "tow ball", "cost": 300, "business_use_percent": 50,
                                          "asset_previously_written_off": True, "first_improvement": True}])
    assert out["total_depreciation_deduction"] == approx(150)


def test_second_improvement_goes_to_pool():
    # second improvement 5,000 at 100%: pool E = 5,000 < 20,000 -> whole balance deducted = 5,000
    out = dep("2026-27", cost_additions=[{"name": "more", "cost": 5000, "asset_previously_written_off": True, "first_improvement": False}])
    assert out["pool"]["cost_additions"] == approx(5000)
    assert out["pool"]["deduction"] == approx(5000)


def test_2025_26_asset_first_used_before_1_july_2026():
    # ATO: assets first used 1 Jul 2025 - 30 Jun 2026 with cost below 20,000 are written off in 2025-26
    out = dep("2025-26", assets=[asset("drill", 19500, "2026-06-30")])
    assert out["instant_asset_write_off_total"] == approx(19500)


def test_first_use_date_outside_year_refused():
    code, out = refused("simplified_depreciation", "2026-27", aggregated_turnover=1000,
                        assets=[asset("bought early", 15000, "2026-06-30")])
    assert code == 3 and out["refusal"]["code"] == "AU-BUS-005"
    code, out = refused("simplified_depreciation", "2025-26", aggregated_turnover=1000,
                        assets=[asset("bought late", 15000, "2026-07-01")])
    assert code == 3 and out["refusal"]["code"] == "AU-BUS-005"


def test_depreciation_refusals():
    code, out = refused("simplified_depreciation", "2026-27", aggregated_turnover=10000000)
    assert code == 3 and out["refusal"]["code"] == "AU-BUS-003"
    code, out = refused("simplified_depreciation", "2026-27", aggregated_turnover=1000, previously_opted_out=True)
    assert code == 3 and out["refusal"]["code"] == "AU-BUS-003"
    code, out = refused("simplified_depreciation", "2026-27", aggregated_turnover=1000,
                        assets=[asset("orchard", 5000, "2026-08-01", typ="excluded")])
    assert code == 3 and out["refusal"]["code"] == "AU-BUS-003"


def test_sbe_threshold_boundary():
    ok("simplified_depreciation", "2026-27", aggregated_turnover=9999999)


# ---------------------------------------------------------------- car cents per km

def test_cents_per_km_2026_27():
    # 3,000 km x 0.91 = 2,730
    out = ok("car_expense_cents_per_km", "2026-27", business_km=3000)
    assert out["cents_per_km_deduction"] == approx(2730)


def test_cents_per_km_cap():
    # 6,000 km counts 5,000: 5,000 x 0.91 = 4,550
    out = ok("car_expense_cents_per_km", "2026-27", business_km=6000)
    assert out["cents_per_km_deduction"] == approx(4550)
    assert out["km_counted"] == 5000 and out["warnings"]


def test_cents_per_km_2025_26_ato_example():
    # ATO example (Johan): 2,514 km x 0.88 = 2,212.32 ("$2,212")
    out = ok("car_expense_cents_per_km", "2025-26", business_km=2514)
    assert out["cents_per_km_deduction"] == approx(2212.32)


def test_logbook_vs_cents():
    # logbook 12,000 x 40% = 4,800; cents 5,000 x 0.91 = 4,550 -> logbook better
    out = ok("car_expense_cents_per_km", "2026-27", business_km=9000,
             logbook_total_car_expenses=12000, logbook_business_use_percent=40)
    assert out["logbook_deduction"] == approx(4800)
    assert out["better_method"] == "logbook"
    out2 = ok("car_expense_cents_per_km", "2026-27", business_km=4000,
              logbook_total_car_expenses=6000, logbook_business_use_percent=30)
    # logbook 1,800; cents 4,000 x 0.91 = 3,640 -> cents better
    assert out2["better_method"] == "cents_per_km"


def test_cents_per_km_refusals():
    code, out = refused("car_expense_cents_per_km", "2026-27", business_km=100, vehicle_type="other")
    assert code == 3 and out["refusal"]["code"] == "AU-BUS-004"
    code, out = refused("car_expense_cents_per_km", "2026-27", business_km=100, claimant="company_or_trust")
    assert code == 3 and out["refusal"]["code"] == "AU-BUS-004"


# ---------------------------------------------------------------- home office

def test_home_office_2025_26_ato_examples():
    # Keisha: 843 h x 0.70 = 590.10 (ATO: $590); Yang: 567 h x 0.70 = 396.90
    out = ok("home_office_fixed_rate", "2025-26", hours_worked_from_home=843, hours_record_kept=True)
    assert out["fixed_rate_deduction"] == approx(590.10)
    assert out["fixed_rate_deduction_whole_dollars"] == 590
    out = ok("home_office_fixed_rate", "2025-26", hours_worked_from_home=567, hours_record_kept=True)
    assert out["fixed_rate_deduction"] == approx(396.90)
    assert out["fixed_rate_deduction_whole_dollars"] == 396


def test_home_office_actual_comparison():
    # 1,000 h x 0.70 = 700 vs actual 900 -> actual better
    out = ok("home_office_fixed_rate", "2025-26", hours_worked_from_home=1000, hours_record_kept=True,
             actual_running_costs_business_portion=900)
    assert out["better_method"] == "actual_cost"


def test_home_office_requires_actual_hours_record():
    code, out = refused("home_office_fixed_rate", "2025-26", hours_worked_from_home=500, hours_record_kept=False)
    assert code == 3 and out["refusal"]["code"] == "AU-BUS-004"


def test_home_office_2026_27_rate_unpublished():
    code, out = refused("home_office_fixed_rate", "2026-27", hours_worked_from_home=500, hours_record_kept=True)
    assert code == 4 and out["refusal"]["code"] == "AU-GEN-003"
    code, out = run("home_office_fixed_rate", "2026-27",
                    {"hours_worked_from_home": 500, "hours_record_kept": True}, allow_draft=True)
    assert code == 4  # no value even in draft mode


# ---------------------------------------------------------------- non-commercial losses

def ncl(**kw):
    kw.setdefault("business_loss", 12000)
    return ok("non_commercial_loss_test", "2026-27", **kw)


def test_ncl_ato_joe_income_requirement():
    # ATO example: 155,000 taxable income + 10,000 net investment loss = 165,000 < 250,000
    out = ncl(taxable_income_excluding_business_loss=155000, net_investment_loss=10000, assessable_income_from_activity=25000)
    assert out["income_for_requirement"] == approx(165000)
    assert out["income_requirement_met"] and out["loss_deductible_now"]
    assert out["deferred_loss"] == 0 and out["deductible_loss"] == approx(12000)


def test_ncl_income_requirement_boundary():
    # requirement is "under 250,000": 249,999 passes, 250,000 fails
    assert ncl(taxable_income_excluding_business_loss=249999, assessable_income_from_activity=30000)["loss_deductible_now"]
    out = ncl(taxable_income_excluding_business_loss=250000, assessable_income_from_activity=30000)
    assert not out["income_requirement_met"] and out["deferred_loss"] == approx(12000)
    assert out["commissioner_discretion_possible"]


def test_ncl_adds_fringe_benefits_and_super():
    # 200,000 + RFB 30,000 + reportable super 20,000 = 250,000 -> fails
    out = ncl(taxable_income_excluding_business_loss=200000, reportable_fringe_benefits=30000,
              reportable_super_contributions=20000, assessable_income_from_activity=50000)
    assert out["income_for_requirement"] == approx(250000) and not out["income_requirement_met"]


def test_ncl_no_test_passed_defers():
    out = ncl(taxable_income_excluding_business_loss=80000, assessable_income_from_activity=15000,
              profit_years_in_last_5=1, real_property_value=400000, other_assets_value=90000)
    assert out["tests_passed"] == [] and not out["loss_deductible_now"]
    assert out["deferred_loss"] == approx(12000)


@pytest.mark.parametrize("field,value,test", [
    ("assessable_income_from_activity", 20000, "assessable_income"),
    ("profit_years_in_last_5", 3, "profit"),
    ("real_property_value", 500000, "real_property"),
    ("other_assets_value", 100000, "other_assets"),
])
def test_ncl_each_test_at_its_boundary(field, value, test):
    out = ncl(taxable_income_excluding_business_loss=80000, **{field: value})
    assert out["tests"][test] is True and out["loss_deductible_now"]


@pytest.mark.parametrize("field,value,test", [
    ("assessable_income_from_activity", 19999, "assessable_income"),
    ("profit_years_in_last_5", 2, "profit"),
    ("real_property_value", 499999, "real_property"),
    ("other_assets_value", 99999, "other_assets"),
])
def test_ncl_just_below_each_boundary(field, value, test):
    out = ncl(taxable_income_excluding_business_loss=80000, **{field: value})
    assert out["tests"][test] is False and not out["loss_deductible_now"]


def test_ncl_refusals():
    code, out = refused("non_commercial_loss_test", "2026-27", business_loss=5000, taxable_income_excluding_business_loss=300000,
                        seeking_commissioner_discretion=True)
    assert code == 3 and out["refusal"]["code"] == "AU-BUS-002"
    code, out = refused("non_commercial_loss_test", "2026-27", business_loss=5000, taxable_income_excluding_business_loss=50000,
                        activity_type="primary_production_or_professional_arts")
    assert code == 3 and out["refusal"]["code"] == "AU-BUS-002"


# ---------------------------------------------------------------- PSI

def psi(**kw):
    return run("psi_tests", "2026-27", kw)


def test_psi_results_test_pass():
    # 80% of PSI for a result (>= 75%), own tools, liable for defects -> results test passed; PSI rules do not apply
    code, out = psi(result_share_of_psi=0.8, supplies_own_tools_and_equipment=True, liable_to_fix_defects_at_own_cost=True)
    assert code == 0 and out["psi_rules_apply"] is False and out["outcome"] == "psb_self_assessed_results_test"


def test_psi_results_test_boundary_75_percent():
    code, out = psi(result_share_of_psi=0.75, supplies_own_tools_and_equipment=True, liable_to_fix_defects_at_own_cost=True)
    assert code == 0 and out["tests"]["results"] is True
    code, out = psi(result_share_of_psi=0.74, supplies_own_tools_and_equipment=True, liable_to_fix_defects_at_own_cost=True,
                    unrelated_clients_from_public_offers=0, principal_work_share_by_others=0, apprentice_months=0,
                    premises_used_mainly_for_psi=False)
    assert code == 0 and out["tests"]["results"] is False and out["psi_rules_apply"] is True


def test_psi_80_percent_rule_blocks_other_tests():
    # 85,000 of 100,000 from one client (85% >= 80%): unrelated clients test cannot be used; results fails -> PSI rules apply
    code, out = psi(total_psi=100000, largest_client_psi_including_associates=85000, result_share_of_psi=0.2,
                    supplies_own_tools_and_equipment=False, liable_to_fix_defects_at_own_cost=False,
                    unrelated_clients_from_public_offers=3, principal_work_share_by_others=0.5)
    assert code == 0 and out["psi_rules_apply"] is True
    assert out["tests"]["eighty_percent_rule_met"] is False and out["largest_client_share"] == pytest.approx(0.85)


def test_psi_80_percent_boundary_exactly_80_fails_rule():
    code, out = psi(total_psi=100000, largest_client_psi_including_associates=80000, result_share_of_psi=0.0,
                    unrelated_clients_from_public_offers=2)
    assert code == 0 and out["tests"]["eighty_percent_rule_met"] is False and out["psi_rules_apply"] is True


def test_psi_unrelated_clients_test_passes_with_rule_met():
    # 60% from one client (< 80%), 2 unrelated clients from public offers -> PSB via unrelated clients test
    code, out = psi(total_psi=100000, largest_client_psi_including_associates=60000, result_share_of_psi=0.1,
                    supplies_own_tools_and_equipment=False, liable_to_fix_defects_at_own_cost=False,
                    unrelated_clients_from_public_offers=2)
    assert code == 0 and out["psi_rules_apply"] is False and out["outcome"] == "psb_self_assessed_other_test"


def test_psi_one_unrelated_client_not_enough():
    code, out = psi(total_psi=100000, largest_client_psi_including_associates=60000, result_share_of_psi=0.1,
                    supplies_own_tools_and_equipment=False, liable_to_fix_defects_at_own_cost=False,
                    unrelated_clients_from_public_offers=1, principal_work_share_by_others=0.05, apprentice_months=0,
                    premises_used_mainly_for_psi=False)
    assert code == 0 and out["psi_rules_apply"] is True


def test_psi_employment_test_20_percent_and_apprentices():
    base = dict(total_psi=100000, largest_client_psi_including_associates=50000, result_share_of_psi=0.0,
                supplies_own_tools_and_equipment=False, unrelated_clients_from_public_offers=1,
                premises_used_mainly_for_psi=False)
    code, out = psi(principal_work_share_by_others=0.20, **base)
    assert code == 0 and out["tests"]["employment"] is True and out["psi_rules_apply"] is False
    code, out = psi(principal_work_share_by_others=0.19, apprentice_months=6, **base)
    assert code == 0 and out["tests"]["employment"] is True
    code, out = psi(principal_work_share_by_others=0.19, apprentice_months=5, **base)
    assert code == 0 and out["tests"]["employment"] is False and out["psi_rules_apply"] is True


def test_psi_business_premises_test():
    code, out = psi(total_psi=100000, largest_client_psi_including_associates=50000, result_share_of_psi=0.0,
                    supplies_own_tools_and_equipment=False, unrelated_clients_from_public_offers=0,
                    principal_work_share_by_others=0.0, apprentice_months=0,
                    premises_used_mainly_for_psi=True, premises_exclusive_use=True, premises_separate_from_private=True,
                    premises_separate_from_clients=True, premises_maintained_all_year=True)
    assert code == 0 and out["tests"]["business_premises"] is True and out["psi_rules_apply"] is False
    code, out = psi(total_psi=100000, largest_client_psi_including_associates=50000, result_share_of_psi=0.0,
                    supplies_own_tools_and_equipment=False, unrelated_clients_from_public_offers=0,
                    principal_work_share_by_others=0.0, apprentice_months=0,
                    premises_used_mainly_for_psi=True, premises_exclusive_use=True, premises_separate_from_private=True,
                    premises_separate_from_clients=False, premises_maintained_all_year=True)
    assert code == 0 and out["tests"]["business_premises"] is False and out["psi_rules_apply"] is True


def test_psi_uncertain_escalates():
    code, out = psi(total_psi=100000, largest_client_psi_including_associates=50000, result_share_of_psi=0.5)
    assert code == 3 and out["refusal"]["code"] == "AU-BUS-001"


def test_psi_determination_escalates():
    code, out = psi(seeking_psb_determination=True, income_mainly_reward_for_personal_effort=True)
    assert code == 3 and out["refusal"]["code"] == "AU-BUS-001"


def test_psi_not_psi():
    code, out = psi(income_mainly_reward_for_personal_effort=False)
    assert code == 0 and out["psi_rules_apply"] is False and out["outcome"] == "not_psi"


def test_psi_consequences_listed_when_applies():
    code, out = psi(total_psi=100000, largest_client_psi_including_associates=95000, result_share_of_psi=0.0)
    assert code == 0 and out["psi_rules_apply"] is True and out["consequences"]
