"""FBT calculators. Expected values come from ATO worked examples (cited) or hand computation shown step by
step. None were produced by running the calculators. The income year argument selects the FBT year ending
in it: 2026-27 = FBT2027 (1 Apr 2026 to 31 Mar 2027, 365 days), 2025-26 = FBT2026 (365 days).

Rates used (ATO FBT rates and thresholds page, read 2026-09-29): FBT rate 47%; type 1 gross-up 2.0802; type 2
gross-up 1.8868; statutory rate 20%; deemed depreciation 25%; benchmark interest 8.27% (FBT2027) and 8.62%
(FBT2026); RFBA threshold 2,000; car parking threshold 11.48 (FBT2027).
"""

from datetime import date

import pytest

from au_tax.calculators.fbt import _d
from au_tax.registry import load_all, run

Y27 = "2026-27"
Y26 = "2025-26"


def call(name, year=Y27, **kw):
    code, out = run(name, year, kw)
    assert code == 0, out
    return out


def approx(x):
    return pytest.approx(x, abs=0.01)


def test_tools_registered():
    tools = set(load_all())
    assert {"car_fringe_benefit_statutory", "car_fringe_benefit_operating_cost", "fbt_payable",
            "reportable_fringe_benefits_amount", "loan_fringe_benefit", "ev_exemption_check",
            "work_vehicle_exemption_check", "car_parking_fringe_benefit", "meal_entertainment_taxable_value",
            "minor_benefit_screen"} <= tools


def test_fbt_year_labels():
    out = call("car_fringe_benefit_statutory", base_value=1000)
    assert out["fbt_year"] == "FBT2027"
    assert out["fbt_year_start"] == "2026-04-01" and out["fbt_year_end"] == "2027-03-31"
    assert out["days_in_fbt_year"] == 365
    assert call("car_fringe_benefit_statutory", Y26, base_value=1000)["fbt_year"] == "FBT2026"


# ---------------------------------------------------------------- statutory formula

def test_statutory_ato_example_28():
    # ATO FBT guide Example 28: base 60,000, available 182 days, employee pays fuel 1,000.
    # 60,000 x 0.2 = 12,000; x 182 = 2,184,000; / 365 = 5,983.56 (ATO shows 5,983); less 1,000 = 4,983.56 (ATO 4,983).
    out = call("car_fringe_benefit_statutory", Y26, base_value=60000, days_available=182, employee_contributions=1000)
    assert out["gross_taxable_value"] == approx(5983.56)
    assert out["taxable_value"] == approx(4983.56)


def test_statutory_ato_item23_example_6():
    # ATO FBT return instructions Example 6: 32,000 x 20% x 274 / 365 = 6,400 x 274 / 365 = 1,753,600 / 365 = 4,804.38 (ATO 4,804).
    out = call("car_fringe_benefit_statutory", base_value=32000, days_available=274)
    assert out["taxable_value"] == approx(4804.38)


def test_statutory_full_year_default_and_gross_up():
    # 50,000 x 0.2 = 10,000 for the full year. Type 1: 10,000 x 2.0802 = 20,802; x 0.47 = 9,776.94.
    out = call("car_fringe_benefit_statutory", base_value=50000, gross_up_type=1)
    assert out["taxable_value"] == approx(10000)
    assert out["grossed_up_taxable_value"] == approx(20802)
    assert out["fbt_on_this_benefit"] == approx(9776.94)
    # Type 2: 10,000 x 1.8868 = 18,868; x 0.47 = 8,867.96.
    out2 = call("car_fringe_benefit_statutory", base_value=50000, gross_up_type=2)
    assert out2["grossed_up_taxable_value"] == approx(18868)
    assert out2["fbt_on_this_benefit"] == approx(8867.96)


def test_statutory_contributions_cannot_go_negative():
    # 10,000 gross less 12,000 contributions floors at nil.
    out = call("car_fringe_benefit_statutory", base_value=50000, employee_contributions=12000)
    assert out["taxable_value"] == 0
    assert any("exceed" in w for w in out["warnings"])


def test_statutory_days_capped_at_year():
    out = call("car_fringe_benefit_statutory", base_value=50000, days_available=366)
    assert out["days_available"] == 365 and out["taxable_value"] == approx(10000)
    assert out["warnings"]


def test_statutory_ev_exempt_nil_but_reportable():
    # 60,000 x 0.2 = 12,000 full year; exempt taxable value nil, RFBA value stays 12,000.
    out = call("car_fringe_benefit_statutory", base_value=60000, ev_exempt=True)
    assert out["taxable_value"] == 0 and out["taxable_value_for_rfba"] == approx(12000)


def test_statutory_pre_existing_commitment_refused():
    code, out = run("car_fringe_benefit_statutory", Y27, {"base_value": 50000, "pre_existing_commitment": True})
    assert code == 3 and out["refusal"]["code"] == "AU-FBT-005"


# ---------------------------------------------------------------- operating cost method

def test_operating_cost_ato_example_7():
    # ATO FBT return instructions Example 7: total operating costs 10,000, private use 30% -> 3,000.
    # Modelled as a leased car with running costs 10,000, no lease costs, business use 70%.
    out = call("car_fringe_benefit_operating_cost", Y26, ownership="leased", running_costs=10000, business_use_percentage=70)
    assert out["total_operating_costs"] == approx(10000)
    assert out["taxable_value"] == approx(3000)


def test_operating_cost_owned_new_car():
    # Cost 40,000, acquired this FBT year, held whole year. Depreciation 40,000 x 25% = 10,000.
    # Interest 40,000 x 8.27% = 3,308. Costs = 4,000 + 10,000 + 3,308 = 17,308. Private 40% -> 6,923.20; less 500 -> 6,423.20.
    out = call("car_fringe_benefit_operating_cost", ownership="owned", cost_price=40000, running_costs=4000,
               business_use_percentage=60, employee_contributions=500)
    assert out["deemed_depreciation"] == approx(10000)
    assert out["deemed_interest"] == approx(3308)
    assert out["total_operating_costs"] == approx(17308)
    assert out["taxable_value"] == approx(6423.20)


def test_operating_cost_second_year_depreciated_value():
    # Held one full prior FBT year: depreciated value 40,000 x 0.75 = 30,000. Dep 7,500. Interest 30,000 x 8.27% = 2,481.
    # Costs 4,000 + 7,500 + 2,481 = 13,981. Private 40% = 5,592.40.
    out = call("car_fringe_benefit_operating_cost", ownership="owned", cost_price=40000, years_owned_before_fbt_year=1,
               running_costs=4000, business_use_percentage=60)
    assert out["depreciated_value_at_start"] == approx(30000)
    assert out["taxable_value"] == approx(5592.40)


def test_operating_cost_part_year_apportions_depreciation_and_interest():
    # 182 of 365 days. Dep 10,000 x 182/365 = 4,986.30. Interest 3,308 x 182/365 = 602,056/365 = 1,649.47.
    # Costs 2,000 + 4,986.30 + 1,649.47 = 8,635.77. Private 40% = 3,454.31.
    out = call("car_fringe_benefit_operating_cost", ownership="owned", cost_price=40000, days_held=182, running_costs=2000,
               business_use_percentage=60)
    assert out["deemed_depreciation"] == approx(4986.30)
    assert out["deemed_interest"] == approx(1649.47)
    assert out["taxable_value"] == approx(3454.31)


def test_operating_cost_no_logbook_means_all_private():
    # Business use 70% is ignored without records: private 100% of 10,000.
    out = call("car_fringe_benefit_operating_cost", ownership="leased", running_costs=10000, business_use_percentage=70,
               logbook_records_adequate=False)
    assert out["taxable_value"] == approx(10000) and out["private_use_percentage"] == 100
    assert any("not adequate" in w for w in out["warnings"])


def test_operating_cost_leased_uses_lease_payments():
    # Running 3,000 + lease 12,000 = 15,000; business 20% -> private 80% = 12,000.
    out = call("car_fringe_benefit_operating_cost", ownership="leased", running_costs=3000, lease_costs=12000, business_use_percentage=20)
    assert out["deemed_depreciation"] == 0 and out["taxable_value"] == approx(12000)


def test_operating_cost_uses_year_benchmark_rate():
    # FBT2026 benchmark 8.62%: interest 40,000 x 8.62% = 3,448; dep 10,000; no running costs; business 0 -> 13,448.
    out = call("car_fringe_benefit_operating_cost", Y26, ownership="owned", cost_price=40000, running_costs=0)
    assert out["taxable_value"] == approx(13448)


def test_operating_cost_owned_requires_cost_price():
    code, out = run("car_fringe_benefit_operating_cost", Y27, {"ownership": "owned", "running_costs": 100})
    assert code == 2


# ---------------------------------------------------------------- FBT payable

def test_fbt_payable_two_types():
    # Type 1 10,000 x 2.0802 = 20,802; type 2 5,000 x 1.8868 = 9,434; total 30,236; x 0.47 = 14,210.92.
    out = call("fbt_payable", type1_taxable_value=10000, type2_taxable_value=5000)
    assert out["type1_grossed_up"] == approx(20802) and out["type2_grossed_up"] == approx(9434)
    assert out["fbt_payable"] == approx(14210.92)


def test_fbt_payable_itemised_benefits_and_instalments():
    # Items: type 1 4,000 + 6,000 = 10,000; type 2 5,000 -> same 14,210.92; less instalments 4,000 = 10,210.92.
    out = call("fbt_payable", benefits=[{"taxable_value": 4000, "gross_up_type": 1}, {"taxable_value": 6000, "gross_up_type": 1},
                                        {"taxable_value": 5000, "gross_up_type": 2}], instalments_paid=4000)
    assert out["fbt_payable"] == approx(14210.92)
    assert out["balance_payable_or_refund"] == approx(10210.92)


def test_fbt_payable_due_dates():
    # ATO: return and payment 21 May (Friday in 2027); tax agent electronic generally 25 June (Friday in 2027).
    out = call("fbt_payable", type2_taxable_value=1000)
    assert out["return_and_payment_due"] == "2027-05-21"
    out2 = call("fbt_payable", type2_taxable_value=1000, lodgment="tax_agent_electronic")
    assert out2["return_and_payment_due"] == "2027-06-25"
    # FBT2026: 21 May 2026 and 25 June 2026 are both Thursdays.
    out3 = call("fbt_payable", Y26, type2_taxable_value=1000)
    assert out3["return_and_payment_due"] == "2026-05-21" and out3["fbt_year"] == "FBT2026"


def test_due_date_business_day_roll_block():
    # 21 May 2027 (Fri) and 25 Jun 2027 (Fri) are business days: no roll. The roll block cites TAA 1953 s 8AAZMB.
    out = call("fbt_payable", type2_taxable_value=1000)
    roll = out["business_day_roll"]
    assert roll["original_date"] == "2027-05-21" and roll["due_date"] == "2027-05-21" and roll["rolled"] is False
    assert "8AAZMB" in roll["rule"] and out["draft"] is False
    assert not any("public holidays" in w for w in out["warnings"])
    assert _d(20270521) == date(2027, 5, 21)


def test_instalment_threshold_is_3000_or_more():
    # ATO: FBT liability of 3,000 or more last year means quarterly instalments.
    assert call("fbt_payable", prior_year_fbt=3000)["quarterly_instalments_apply_this_year"] is True
    assert call("fbt_payable", prior_year_fbt=2999.99)["quarterly_instalments_apply_this_year"] is False
    assert call("fbt_payable")["quarterly_instalments_apply_this_year"] is None


@pytest.mark.parametrize("kw,code", [
    ({"employer_type": "pbi_or_health_promotion"}, "AU-FBT-001"),
    ({"employer_type": "hospital_or_ambulance"}, "AU-FBT-001"),
    ({"employer_type": "rebatable_nfp"}, "AU-FBT-001"),
    ({"special_circumstances": ["lafha"]}, "AU-FBT-002"),
    ({"special_circumstances": ["remote_area_housing"]}, "AU-FBT-003"),
    ({"special_circumstances": ["housing"]}, "AU-FBT-003"),
    ({"special_circumstances": ["recreation_entertainment"]}, "AU-FBT-004"),
    ({"special_circumstances": ["pre_2011_commitment_car"]}, "AU-FBT-005"),
    ({"special_circumstances": ["employee_status_doubtful"]}, "AU-FBT-006"),
])
def test_fbt_payable_refusals(kw, code):
    c, out = run("fbt_payable", Y27, {"type1_taxable_value": 1000, **kw})
    assert c == 3 and out["refusal"]["code"] == code


def test_fbt_payable_unknown_year_is_general_refusal():
    c, out = run("fbt_payable", "2027-28", {"type1_taxable_value": 1000})
    assert c == 4 and out["refusal"]["code"] == "AU-GEN-003"


# ---------------------------------------------------------------- RFBA

def test_rfba_ato_example_just_over_threshold():
    # ATO rates page: taxable value 2,000.01 -> reportable 3,773 (2,000.01 x 1.8868 = 3,773.62, shown as 3,773).
    out = call("reportable_fringe_benefits_amount", Y26, type2_taxable_value=2000.01)
    assert out["reportable"] is True
    assert out["reportable_fringe_benefits_amount"] == approx(3773.62)
    assert out["reportable_fringe_benefits_amount_whole_dollars"] == 3773


def test_rfba_at_threshold_is_not_reportable():
    # The threshold is "more than" 2,000, so exactly 2,000 is nil.
    out = call("reportable_fringe_benefits_amount", type1_taxable_value=2000)
    assert out["reportable"] is False and out["reportable_fringe_benefits_amount"] == 0


def test_rfba_uses_type2_rate_for_type1_benefits():
    # Type 1 1,500 + type 2 1,000 = 2,500 > 2,000; grossed up at 1.8868 for both: 2,500 x 1.8868 = 4,717.
    out = call("reportable_fringe_benefits_amount", type1_taxable_value=1500, type2_taxable_value=1000)
    assert out["reportable_fringe_benefits_amount"] == approx(4717)
    assert out["income_year_reported_in"] == "2026-27"


def test_rfba_includes_exempt_ev_value():
    # Exempt EV benefit of 5,000 is reportable: 5,000 x 1.8868 = 9,434.
    out = call("reportable_fringe_benefits_amount", exempt_ev_taxable_value=5000)
    assert out["reportable_fringe_benefits_amount"] == approx(9434)


def test_rfba_refuses_pbi():
    c, out = run("reportable_fringe_benefits_amount", Y27, {"type1_taxable_value": 3000, "employer_type": "pbi_or_health_promotion"})
    assert c == 3 and out["refusal"]["code"] == "AU-FBT-001"


# ---------------------------------------------------------------- loans

def test_loan_ato_example_8():
    # ATO FBT return instructions Example 8: 20,000 interest free, 8.62% (FBT year ending 31 Mar 2026): 20,000 x 8.62% = 1,724.
    out = call("loan_fringe_benefit", Y26, loan_balance=20000)
    assert out["taxable_value"] == approx(1724)


def test_loan_2027_rate():
    # 20,000 x 8.27% = 1,654. Type 2 default: 1,654 x 1.8868 = 3,120.77; x 0.47 = 1,466.76.
    out = call("loan_fringe_benefit", loan_balance=20000)
    assert out["benchmark_interest_rate"] == 0.0827
    assert out["taxable_value"] == approx(1654)
    assert out["grossed_up_taxable_value"] == approx(3120.77) and out["fbt_on_this_benefit"] == approx(1466.76)


def test_loan_low_interest_reduces_by_interest_charged():
    # 50,000 x 8.27% = 4,135 notional; interest charged 2,500 -> 1,635 (same method as the ATO guide's 325 example).
    out = call("loan_fringe_benefit", loan_balance=50000, interest_charged=2500)
    assert out["taxable_value"] == approx(1635)


def test_loan_otherwise_deductible_rule():
    # ATO guide method (rate set without regard to use): before = 4,135 - 2,000 = 2,135; 60% income-producing:
    # value = 2,135 x (1 - 0.6) = 854. (ATO's own example: 825 -> 330 = 825 x 0.4.)
    out = call("loan_fringe_benefit", loan_balance=50000, interest_charged=2000, income_producing_use_percentage=60)
    assert out["taxable_value_before_otherwise_deductible"] == approx(2135)
    assert out["taxable_value"] == approx(854)


def test_loan_periods_daily_balance():
    # Balance-days: 30,000 x 100 + 20,000 x 265 = 3,000,000 + 5,300,000 = 8,300,000. x 8.27% = 686,410; / 365 = 1,880.58.
    out = call("loan_fringe_benefit", periods=[{"balance": 30000, "days": 100}, {"balance": 20000, "days": 265}])
    assert out["taxable_value"] == approx(1880.58)


def test_loan_interest_above_benchmark_is_nil():
    out = call("loan_fringe_benefit", loan_balance=20000, interest_charged=2000)
    assert out["taxable_value"] == 0


def test_loan_needs_one_balance_source():
    assert run("loan_fringe_benefit", Y27, {})[0] == 2
    assert run("loan_fringe_benefit", Y27, {"loan_balance": 1, "periods": [{"balance": 1, "days": 1}]})[0] == 2


# ---------------------------------------------------------------- EV exemption

def ev(year=Y27, **kw):
    base = {"vehicle_type": "battery_electric"}
    base.update(kw)
    return call("ev_exemption_check", year, **base)


def test_ev_ato_example_held_before_used_after_start():
    # ATO example: first held 15 Jun 2022, first used 5 Jul 2022: first time held AND used is after 1 Jul 2022 -> exempt.
    out = ev(first_held_date="2022-06-15", first_used_date="2022-07-05", lct_payable=False)
    assert out["exempt"] is True


def test_ev_ato_example_first_used_before_start():
    # ATO example (Shelly): first held and used 1 Apr 2022 -> before 1 Jul 2022 -> not exempt.
    out = ev(first_held_date="2022-04-01", first_used_date="2022-04-01", lct_payable=False)
    assert out["exempt"] is False


def test_ev_held_30_june_used_1_july_is_exempt():
    # ATO example: held 30 Jun 2022, used 1 Jul 2022: both true first on 1 Jul 2022 -> eligible.
    assert ev(first_held_date="2022-06-30", first_used_date="2022-07-01", lct_payable=False)["exempt"] is True


def test_ev_lct_threshold_boundary_for_year_of_sale():
    # Fuel-efficient LCT threshold 2026-27 is 91,661 (ATO LCT page): value at threshold pays no LCT.
    common = dict(first_held_date="2026-08-01", first_used_date="2026-08-05", first_retail_sale_date="2026-08-01")
    assert ev(value_at_first_retail_sale=91661, **common)["exempt"] is True
    assert ev(value_at_first_retail_sale=91662, **common)["exempt"] is False


def test_ev_lct_uses_threshold_of_year_of_sale_not_current_year():
    # Sold 2024-25 when the threshold was 91,387: 91,500 is under today's 91,661 but LCT was payable then.
    kw = dict(first_held_date="2024-09-01", first_used_date="2024-09-01", first_retail_sale_date="2024-09-01")
    out = ev(value_at_first_retail_sale=91500, **kw)
    assert out["exempt"] is False and out["lct_threshold_used"] == 91387
    # 2022-23 threshold 84,916: 84,916 ok.
    kw2 = dict(first_held_date="2022-09-01", first_used_date="2022-09-01", first_retail_sale_date="2022-09-01")
    assert ev(value_at_first_retail_sale=84916, **kw2)["exempt"] is True


def test_ev_phev_grandfathering():
    # PHEV benefit in FBT2027 (from 1 Apr 2026): exempt only if exempt use before 1 Apr 2025 and binding commitment continues.
    kw = dict(vehicle_type="plug_in_hybrid", first_held_date="2024-08-01", first_used_date="2024-08-01", lct_payable=False)
    assert ev(**kw, phev_exempt_before_2025_04_01=True, phev_binding_commitment_continues=True)["exempt"] is True
    assert ev(**kw, phev_exempt_before_2025_04_01=True, phev_binding_commitment_continues=False)["exempt"] is False
    assert ev(**kw, phev_exempt_before_2025_04_01=False, phev_binding_commitment_continues=True)["exempt"] is False
    assert ev(**kw, phev_exempt_before_2025_04_01=True, phev_binding_commitment_continues=True,
              phev_commitment_changed_after_2025_04_01=True)["exempt"] is False
    assert ev(**kw)["exempt"] is None


def test_ev_phev_delivered_after_cutoff_not_exempt():
    # ATO example (Sonia): novated lease signed, delivered 1 May 2025 -> not in exempt use before 1 Apr 2025 -> not exempt.
    out = ev(vehicle_type="plug_in_hybrid", first_held_date="2025-04-15", first_used_date="2025-05-01", lct_payable=False,
             phev_exempt_before_2025_04_01=False, phev_binding_commitment_continues=True)
    assert out["exempt"] is False


def test_ev_phev_before_cutoff_still_low_emissions():
    # A benefit provided on 31 Mar 2025 (before the PHEV cut-off) is exempt if the other conditions are met (FBT2025 year, income year 2024-25 has no file, use 2025-26).
    out = ev(Y26, vehicle_type="plug_in_hybrid", first_held_date="2024-08-01", first_used_date="2024-08-01", lct_payable=False,
             benefit_date="2025-03-31")
    assert out["exempt"] is True


@pytest.mark.parametrize("vt", ["hybrid_non_plug_in", "petrol_or_diesel"])
def test_ev_non_plug_hybrid_and_ice_not_eligible(vt):
    assert ev(vehicle_type=vt, first_held_date="2023-01-01", first_used_date="2023-01-01", lct_payable=False)["exempt"] is False


def test_ev_recipient_and_car_conditions():
    kw = dict(first_held_date="2023-01-01", first_used_date="2023-01-01", lct_payable=False)
    assert ev(recipient="former_or_future_employee", **kw)["exempt"] is False
    assert ev(recipient="associate_of_current_employee", **kw)["exempt"] is True
    assert ev(is_car=False, **kw)["exempt"] is False


def test_ev_benefit_before_start_and_missing_facts():
    out = ev(Y26, first_held_date="2022-01-01", first_used_date="2022-01-01", lct_payable=False, benefit_date="2022-05-01")
    assert out["exempt"] is False
    assert ev(lct_payable=False)["exempt"] is None
    assert ev(first_held_date="2023-01-01", first_used_date="2023-01-01")["exempt"] is None


def test_ev_proposal_is_information_not_law():
    # Exposure draft (ATO page 14 May 2026): from 1 Apr 2027 limit 75,000, 15% above it, 25% discount for all from 1 Apr 2029. NOT LAW.
    out = ev(first_held_date="2023-01-01", first_used_date="2023-01-01", lct_payable=False, benefit_date="2027-04-01")
    assert out["exempt"] is True
    p = out["proposal_not_law"]
    assert "NOT LAW" in p["status"] and p["base_value_limit"] == 75000 and p["discounted_statutory_rate_above_limit"] == 0.15
    assert p["start_date"] == "2027-04-01"
    assert any("not law" in w.lower() for w in out["warnings"])
    # The 2025-26 file has no proposal figures.
    assert ev(Y26, first_held_date="2023-01-01", first_used_date="2023-01-01", lct_payable=False)["proposal_not_law"] is None


def test_ev_exempt_stays_reportable_warning():
    out = ev(first_held_date="2023-01-01", first_used_date="2023-01-01", lct_payable=False)
    assert any("reportable" in w for w in out["warnings"])


# ---------------------------------------------------------------- work vehicle exemption

def wv(**kw):
    return call("work_vehicle_exemption_check", **kw)


def test_ute_home_to_work_only_is_exempt():
    out = wv(vehicle_kind="single_cab_ute")
    assert out["eligible_vehicle"] is True and out["exempt"] is True


def test_ute_regular_private_use_not_exempt():
    # ATO Example 16 (Rose): regular weekend shopping and football trips are not minor, infrequent and irregular.
    out = wv(vehicle_kind="single_cab_ute", other_private_use="more_than_minor")
    assert out["exempt"] is False and "car fringe benefit" in out["if_not_exempt"]


def test_ute_minor_infrequent_use_still_exempt():
    # ATO Example 15: one furniture move a year.
    assert wv(vehicle_kind="panel_van", other_private_use="minor_infrequent_irregular")["exempt"] is True


def test_ute_associate_on_home_work_trips_loses_exemption():
    assert wv(vehicle_kind="single_cab_ute", associate_travelled_home_to_work=True)["exempt"] is False


def test_dual_cab_eligibility():
    assert wv(vehicle_kind="dual_cab_ute", designed_principally_to_carry_passengers=True)["exempt"] is False
    assert wv(vehicle_kind="dual_cab_ute", designed_principally_to_carry_passengers=False)["exempt"] is True
    assert wv(vehicle_kind="dual_cab_ute", designed_load_tonnes=1.0)["exempt"] is True
    assert wv(vehicle_kind="dual_cab_ute")["exempt"] is None


def test_passenger_car_not_eligible():
    out = wv(vehicle_kind="passenger_car_or_other")
    assert out["eligible_vehicle"] is False and out["exempt"] is False


def test_pcg_2018_3_safe_harbour_boundaries():
    # PCG 2018/3: policy + assurance, wholly private km not more than 1,000, no return journey over 200 km, diversion not over 2 km.
    base = dict(vehicle_kind="single_cab_ute", policy_and_employee_assurance=True, wholly_private_km_total=1000,
                longest_private_return_trip_km=200, max_home_work_diversion_km=2)
    assert wv(**base)["pcg_2018_3_safe_harbour_met"] is True
    assert wv(**{**base, "wholly_private_km_total": 1001})["pcg_2018_3_safe_harbour_met"] is False
    assert wv(**{**base, "longest_private_return_trip_km": 201})["pcg_2018_3_safe_harbour_met"] is False
    assert wv(**{**base, "max_home_work_diversion_km": 2.5})["pcg_2018_3_safe_harbour_met"] is False
    assert wv(**{**base, "policy_and_employee_assurance": False})["pcg_2018_3_safe_harbour_met"] is False
    # Safe harbour met: exempt even if the taxpayer labels other use as more than minor.
    assert wv(**base, other_private_use="more_than_minor")["exempt"] is True
    assert wv(**{**base, "wholly_private_km_total": 1500}, other_private_use="more_than_minor")["exempt"] is False


# ---------------------------------------------------------------- car parking

def park(**kw):
    base = dict(days_parked=200, daily_value=20.0, commercial_station_within_1km=True, lowest_all_day_fee_first_day=25.0)
    base.update(kw)
    return call("car_parking_fringe_benefit", **base)


def test_car_parking_taxable_value():
    # 200 days x 20.00 = 4,000; less employee contribution 500 = 3,500.
    out = park(employee_contributions=500)
    assert out["benefit_arises"] is True and out["taxable_value"] == approx(3500)


def test_car_parking_threshold_must_be_exceeded():
    # FBT2027 threshold 11.48: 11.49 arises, 11.48 does not.
    assert park(lowest_all_day_fee_first_day=11.49)["benefit_arises"] is True
    assert park(lowest_all_day_fee_first_day=11.48)["benefit_arises"] is False
    # FBT2026 threshold 11.03.
    assert call("car_parking_fringe_benefit", Y26, days_parked=10, daily_value=10, commercial_station_within_1km=True,
                lowest_all_day_fee_first_day=11.04)["benefit_arises"] is True
    # Fee must exceed the threshold on the day of the benefit as well.
    assert park(lowest_all_day_fee_on_day=11.0)["benefit_arises"] is False


def test_car_parking_no_station_or_short_stay():
    assert park(commercial_station_within_1km=False)["taxable_value"] == 0
    assert park(parked_over_4_hours=False)["benefit_arises"] is False


def test_car_parking_small_business_exemption():
    out = park(prior_year_aggregated_turnover=40_000_000)
    assert out["exempt_reason"] == "small_business_exemption" and out["taxable_value"] == 0
    # Turnover exactly 50,000,000 and gross income exactly 10,000,000: both tests need "less than".
    out2 = park(prior_year_aggregated_turnover=50_000_000, prior_year_gross_total_income=10_000_000)
    assert out2["exempt_reason"] is None and out2["taxable_value"] == approx(4000)
    # A commercial car park or a listed company group blocks the exemption.
    assert park(prior_year_aggregated_turnover=1_000_000, parking_in_commercial_car_park=True)["exempt_reason"] is None
    assert park(prior_year_aggregated_turnover=1_000_000, government_or_listed_company_group=True)["exempt_reason"] is None


def test_car_parking_disability_and_refusal():
    assert park(employee_has_disability_permit=True)["taxable_value"] == 0
    c, out = run("car_parking_fringe_benefit", Y27, {"days_parked": 1, "daily_value": 1, "commercial_station_within_1km": True,
                                                    "employer_type": "hospital_or_ambulance"})
    assert c == 3 and out["refusal"]["code"] == "AU-FBT-001"


# ---------------------------------------------------------------- meal entertainment

def test_meal_entertainment_50_50():
    # 20,000 x 50% = 10,000; type 2: 10,000 x 1.8868 = 18,868; x 0.47 = 8,867.96.
    out = call("meal_entertainment_taxable_value", method="50_50", total_meal_entertainment_expenditure=20000, gross_up_type=2)
    assert out["taxable_value"] == approx(10000)
    assert out["fbt_on_this_benefit"] == approx(8867.96)


def test_meal_entertainment_register():
    # Register 3,000 / 12,000 = 25%; 80,000 x 25% = 20,000.
    out = call("meal_entertainment_taxable_value", method="twelve_week_register", total_meal_entertainment_expenditure=80000,
               register_employee_and_associate_value=3000, register_total_value=12000)
    assert out["taxable_value"] == approx(20000)


def test_meal_entertainment_register_needs_register_values():
    assert run("meal_entertainment_taxable_value", Y27, {"method": "twelve_week_register", "total_meal_entertainment_expenditure": 1})[0] == 2


@pytest.mark.parametrize("sc", ["recreation_entertainment", "entertainment_facility_leasing", "salary_packaged_meal_entertainment"])
def test_meal_entertainment_refusals(sc):
    c, out = run("meal_entertainment_taxable_value", Y27, {"method": "50_50", "total_meal_entertainment_expenditure": 1000,
                                                          "special_circumstances": [sc]})
    assert c == 3 and out["refusal"]["code"] == "AU-FBT-004"


# ---------------------------------------------------------------- minor benefits

def test_minor_benefit_threshold_is_less_than():
    # s 58P(1)(e): notional taxable value must be less than 300.
    assert call("minor_benefit_screen", notional_taxable_value=299.99)["likely_exempt"] is True
    out = call("minor_benefit_screen", notional_taxable_value=300)
    assert out["likely_exempt"] is False and out["below_threshold"] is False


def test_minor_benefit_regular_lunch_not_exempt():
    # ATO example: 45 Friday lunch provided every week is not exempt even though under the threshold.
    out = call("minor_benefit_screen", notional_taxable_value=45, frequent_or_regular=True, similar_benefits_total_notional_value=2340)
    assert out["below_threshold"] is True and out["likely_exempt"] is False
    assert out["factors"]["frequency_and_regularity"] == "against"


def test_minor_benefit_occasional_gift_is_exempt():
    # ATO example: flowers or chocolates on a special occasion.
    assert call("minor_benefit_screen", notional_taxable_value=80)["likely_exempt"] is True


def test_minor_benefit_salary_packaged_not_exempt():
    assert call("minor_benefit_screen", notional_taxable_value=100, principally_remuneration=True)["likely_exempt"] is False


def test_minor_benefit_associated_total_counts():
    # Associated benefits of 300 or more in the same event count against.
    assert call("minor_benefit_screen", notional_taxable_value=100, associated_benefits_total_notional_value=350)["likely_exempt"] is False


# ---------------------------------------------------------------- figures and drafts

def test_all_fbt_figures_verified_so_not_draft():
    out = call("fbt_payable", type1_taxable_value=1000)
    assert out["draft"] is False
    assert {f["status"] for f in out["figures_used"]} == {"VERIFIED"}


def test_fbt_due_date_roll_after_the_holiday_data_is_flagged_not_refused():
    # fbt_payable's return date is secondary to the FBT amount: strict=False returns the unrolled date with an AU-GEN-004 note.
    from datetime import date

    from au_tax.calculators.fbt import _roll
    from au_tax.figures import Figures
    from au_tax.registry import Refusal

    warnings: list[str] = []
    r = _roll(Figures("2027-28"), date(2028, 7, 3), warnings, strict=False)
    assert r.due == date(2028, 7, 3) and not r.rolled and r.out_of_range["code"] == "AU-GEN-004" and warnings
    with pytest.raises(Refusal):
        _roll(Figures("2027-28"), date(2028, 7, 3), [])
    assert call("fbt_payable", type1_taxable_value=1000)["field_refusals"] == []
