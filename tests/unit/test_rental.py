"""rental_property_result and capital_works_deduction. Expected values come from ATO worked examples (cited),
the worked example in the Act (s 26-155 Henrietta example) or hand computation shown step by step.
None were produced by running the calculator."""

import pytest

from au_tax.calculators.rental import quarantine_step
from au_tax.registry import load_all, run


def rent(year="2025-26", **kw):
    code, out = run("rental_property_result", year, kw)
    assert code == 0, out
    return out


def cw(year="2025-26", **kw):
    code, out = run("capital_works_deduction", year, kw)
    assert code == 0, out
    return out


def refused(tool, year="2025-26", **kw):
    code, out = run(tool, year, kw)
    assert code == 3, out
    return out["refusal"]["code"]


def approx(x, tol=0.01):
    return pytest.approx(x, abs=tol)


# ---------------------------------------------------------------- registration

def test_registered():
    assert {"rental_property_result", "capital_works_deduction"} <= set(load_all())


# ---------------------------------------------------------------- capital works (Div 43)

def test_capital_works_ato_example_meg():
    # ATO capital works page, Meg: cost 500,000, construction began Feb 2005 (after 15 Sep 1987) -> 2.5%.
    # Full year = 500,000 x 2.5% = 12,500. Income-producing 122 days of 365 -> 12,500 x 122 / 365 = 4,178.08 (ATO: $4,178).
    out = cw(construction_cost=500000, construction_start_date="2005-02-01", construction_completion_date="2005-11-30",
             days_income_producing=122)
    assert out["rate"] == 0.025
    assert out["annual_full_year_amount"] == approx(12500)
    assert out["capital_works_deduction"] == approx(4178.08)


def test_capital_works_full_year_general_rate():
    # 300,000 x 2.5% = 7,500 for 365 of 365 days
    assert cw(construction_cost=300000, construction_start_date="2010-05-01")["capital_works_deduction"] == approx(7500)


def test_capital_works_4_percent_window_1985_1987():
    # begun 1 Mar 1986 (18 Jul 1985 to 15 Sep 1987) -> 4%; 250,000 x 4% = 10,000
    out = cw(construction_cost=250000, construction_start_date="1986-03-01")
    assert out["rate"] == 0.04
    assert out["capital_works_deduction"] == approx(10000)


def test_capital_works_before_18_jul_1985_nil():
    out = cw(construction_cost=250000, construction_start_date="1985-07-17")
    assert out["capital_works_deduction"] == 0
    assert out["warnings"]


def test_capital_works_16_sep_1987_boundary_is_2_5():
    out = cw(construction_cost=100000, construction_start_date="1987-09-16")
    assert out["rate"] == 0.025
    assert out["capital_works_deduction"] == approx(2500)


def test_capital_works_traveller_10_units_4_percent():
    # apartment building, 12 units owned, begun 1995 (after 26 Feb 1992) -> 4%; 2,000,000 x 4% = 80,000
    out = cw(construction_cost=2000000, construction_start_date="1995-01-01", use_type="traveller_accommodation",
             units_or_bedrooms_held=12)
    assert out["rate"] == 0.04
    assert out["capital_works_deduction"] == approx(80000)
    assert out["claim_period_years"] == 25


def test_capital_works_traveller_9_units_falls_back_to_2_5():
    # 9 units is below the minimum of 10 -> residential 2.5%; 2,000,000 x 2.5% = 50,000
    out = cw(construction_cost=2000000, construction_start_date="1995-01-01", use_type="traveller_accommodation",
             units_or_bedrooms_held=9)
    assert out["rate"] == 0.025
    assert out["capital_works_deduction"] == approx(50000)


def test_capital_works_traveller_dates():
    # 10 bedrooms, ATO table: 16 Sep 1987 to 26 Feb 1992 -> 2.5%; 22 Aug 1984 to 15 Sep 1987 -> 4%; 27 Feb 1992 -> 4%
    def rate(d):
        return cw(construction_cost=100000, construction_start_date=d, use_type="traveller_accommodation",
                  units_or_bedrooms_held=10)["rate"]
    assert rate("1990-06-01") == 0.025
    assert rate("1986-06-01") == 0.04
    assert rate("1992-02-27") == 0.04
    assert rate("1992-02-26") == 0.025


def test_capital_works_structural_improvement():
    # fence begun 2000 -> 2.5%; 20,000 x 2.5% = 500
    out = cw(construction_cost=20000, construction_start_date="2000-01-01", use_type="structural_improvement")
    assert out["capital_works_deduction"] == approx(500)
    # begun 26 Feb 1992: not eligible
    assert cw(construction_cost=20000, construction_start_date="1992-02-26", use_type="structural_improvement")["capital_works_deduction"] == 0


def test_capital_works_completion_part_year():
    # completed 1 Jan 2026; claim 1 Jan to 30 Jun 2026 = 31+28+31+30+31+30 = 181 days.
    # 200,000 x 2.5% = 5,000 x 181 / 365 = 2,479.45
    out = cw(construction_cost=200000, construction_start_date="2025-03-01", construction_completion_date="2026-01-01")
    assert out["days_claimed"] == 181
    assert out["capital_works_deduction"] == approx(2479.45)


def test_capital_works_not_complete_by_year_end():
    out = cw(construction_cost=200000, construction_start_date="2026-03-01", construction_completion_date="2026-09-01")
    assert out["capital_works_deduction"] == 0


def test_capital_works_cap_at_undeducted_balance():
    # full year 7,500 but only 1,000 undeducted remains
    out = cw(construction_cost=300000, construction_start_date="1990-05-01", previously_deducted_or_undeducted=1000)
    assert out["capital_works_deduction"] == approx(1000)
    assert out["capped_at_undeducted_balance"] is True


def test_capital_works_half_owner():
    # 300,000 x 2.5% = 7,500 x 50% = 3,750
    assert cw(construction_cost=300000, construction_start_date="2010-05-01", ownership_percent=50)["capital_works_deduction"] == approx(3750)


def test_capital_works_holiday_home_denied():
    out = cw(construction_cost=300000, construction_start_date="2010-05-01", holiday_home_denied_s26_50=True)
    assert out["capital_works_deduction"] == 0
    assert out["denied_by_s26_50"] is True


def test_capital_works_refusals():
    assert refused("capital_works_deduction", construction_cost=1, construction_start_date="2000-01-01", use_type="non_residential") == "AU-RENT-001"
    assert refused("capital_works_deduction", construction_cost=1, construction_start_date="1988-01-01", pre_16_sep_1987_contract=True) == "AU-RENT-004"
    assert refused("capital_works_deduction", construction_cost=1, construction_start_date="2000-01-01", use_type="traveller_accommodation") == "AU-RENT-004"


def test_capital_works_2026_27_same_rate():
    assert cw("2026-27", construction_cost=300000, construction_start_date="2010-05-01")["capital_works_deduction"] == approx(7500)


# ---------------------------------------------------------------- apportionment (PCG 2026/2 examples)

def test_pcg_example_3_time_based_private_use_30_days():
    # Gail and Craig: 30 private days of 365. Agent and advertising 1,828 fully deductible.
    # Other expenses 34,801 x (365 - 30) / 365 = 34,801 x 335 / 365 = 11,658,335 / 365 = 31,940.64
    # deductions = 1,828 + 31,940.64 = 33,768.64; net = 40,000 - 33,768.64 = 6,231.36
    out = rent(gross_rent=40000, expenses={"agent_fees": 1828, "interest": 34801}, days_rented=300, days_available_commercial_terms=35)
    assert out["apportionment"]["time_factor"] == pytest.approx(335 / 365)
    assert out["deductions"]["total"] == approx(33768.64)
    assert out["net_rental_result"] == approx(6231.36)


def test_pcg_example_5_area_based_kim():
    # A = 45 (tenant floor), B = 35 (gardens, shared), C = 45 + 55 + 35 = 135.
    # (45 + 35/2) / 135 = 62.5 / 135 = 0.462963 (ATO: 46.3%). 10,000 x 0.462963 = 4,629.63
    out = rent(gross_rent=15000, expenses={"council_rates": 10000}, area_exclusive_to_tenant=45, area_shared_common=35, area_total=135)
    assert out["apportionment"]["area_factor"] == pytest.approx(0.462963, abs=1e-5)
    assert out["deductions"]["total"] == approx(4629.63)


def test_pcg_example_6_combined_area_and_time_leanne():
    # A = 10, B = 50, C = 80 -> (10 + 25) / 80 = 43.75%. Days let 100 of 365 (part of home: available days nil).
    # 43.75% x 100 / 365 = 0.4375 x 0.273973 = 0.119863 (ATO: 11.99%).
    # Ownership 20,000 x 0.119863 = 2,397.26 (= 875,000 / 365); platform fees 500 fully deductible -> 2,897.26
    out = rent(gross_rent=6000, expenses={"interest": 20000, "platform_fees": 500}, days_rented=100, days_available_commercial_terms=50,
               part_of_home=True, area_exclusive_to_tenant=10, area_shared_common=50, area_total=80)
    assert out["apportionment"]["combined_factor"] == pytest.approx(0.119863, abs=1e-5)
    assert out["deductions"]["total"] == approx(2897.26)
    assert any("part of your home" in w.lower() for w in out["warnings"])


def test_pcg_example_4_change_of_use_sachin():
    # Rented until 28 Feb (Jul 31 + Aug 31 + Sep 30 + Oct 31 + Nov 30 + Dec 31 + Jan 31 + Feb 28 = 243 days of 365).
    # Interest 28,000 x 243 / 365 = 6,804,000 / 365 = 18,641.10
    out = rent(gross_rent=20000, expenses={"interest": 28000}, days_rented=243)
    assert out["deductions"]["total"] == approx(18641.10)


def test_pcg_example_7_non_arms_length_capped_at_rent():
    # Jana: rent 10,000 from her mother; deductions would be 15,000 -> limited to rent received: net nil.
    out = rent(gross_rent=10000, expenses={"interest": 12000, "council_rates": 3000}, non_arms_length_rent=True)
    assert out["deductions"]["total"] == approx(10000)
    assert out["net_rental_result"] == 0
    assert out["deductions"]["capped_at_rent_received"] is True


def test_non_arms_length_below_rent_not_capped():
    out = rent(gross_rent=10000, expenses={"interest": 4000}, non_arms_length_rent=True)
    assert out["deductions"]["total"] == approx(4000)
    assert out["net_rental_result"] == approx(6000)


def test_days_exceed_period_is_invalid():
    code, _ = run("rental_property_result", "2025-26", {"days_rented": 300, "days_available_commercial_terms": 100})
    assert code == 2


def test_tenant_area_exceeds_total_is_invalid():
    code, _ = run("rental_property_result", "2025-26", {"area_exclusive_to_tenant": 90, "area_total": 80})
    assert code == 2


# ---------------------------------------------------------------- expense categories

def test_interest_purpose_share_removed_first():
    # interest 10,000, 20% for a private redraw -> 8,000 deductible
    out = rent(gross_rent=20000, expenses={"interest": 10000, "interest_non_rental_share": 0.2})
    assert out["deductions"]["total"] == approx(8000)


def test_travel_denied():
    out = rent(gross_rent=20000, expenses={"travel": 800, "council_rates": 1000})
    assert out["deductions"]["total"] == approx(1000)
    assert out["denied_amounts"][0]["amount"] == approx(800)


def test_capital_items_not_deducted():
    out = rent(gross_rent=20000, expenses={"initial_repairs": 2000, "capital_improvements": 5000, "purchase_and_sale_costs": 9000, "repairs_maintenance": 300})
    assert out["deductions"]["total"] == approx(300)
    assert {i["item"] for i in out["capital_not_deductible_now"]} == {"initial_repairs", "capital_improvements", "purchase_and_sale_costs"}


def test_vacant_land_holding_costs_denied():
    out = rent(gross_rent=0, expenses={"interest": 5000, "council_rates": 900, "land_tax": 600}, vacant_land=True)
    assert out["deductions"]["total"] == 0
    assert out["net_rental_result"] == 0
    assert out["denied_amounts"][0]["amount"] == approx(6500)


def test_ownership_percent_splits_income_and_expenses():
    # 50% legal title: income 10,000 x 50% = 5,000; direct 2,000 x 50% = 1,000; interest 4,000 x 50% = 2,000; net = 5,000 - 3,000 = 2,000
    out = rent(gross_rent=10000, ownership_percent=50, expenses={"agent_fees": 2000, "interest": 4000})
    assert out["assessable_income"]["total"] == approx(5000)
    assert out["deductions"]["total"] == approx(3000)
    assert out["net_rental_result"] == approx(2000)


# ---------------------------------------------------------------- holiday homes (s 26-50)

def test_holiday_home_not_mainly_rent_denies_ownership_costs():
    # Only the platform fees (2,000) and cleaning (500) remain; interest, rates, depreciation, capital works denied.
    out = rent(gross_rent=20000, holiday_home=True, holiday_home_mainly_for_rent="no",
               expenses={"platform_fees": 2000, "guest_cleaning_and_linen": 500, "interest": 15000, "council_rates": 3000},
               depreciating_assets=[{"description": "oven", "cost": 2000, "effective_life_years": 10}],
               capital_works=[{"construction_cost": 200000, "construction_start_date": "2005-01-01"}])
    assert out["deductions"]["total"] == approx(2500)
    assert out["net_rental_result"] == approx(17500)
    assert out["denied_amounts"]


def test_holiday_home_mainly_rent_apportions():
    # rented 100 + available 150 = 250 of 365; interest 10,000 x 250 / 365 = 6,849.32
    out = rent(gross_rent=20000, holiday_home=True, holiday_home_mainly_for_rent="yes", days_rented=100,
               days_available_commercial_terms=150, expenses={"interest": 10000})
    assert out["deductions"]["total"] == approx(6849.32)


def test_holiday_home_unresolved_refused():
    assert refused("rental_property_result", gross_rent=1, holiday_home=True, holiday_home_mainly_for_rent="unresolved") == "AU-RENT-003"


def test_holiday_home_requires_mainly_answer():
    code, _ = run("rental_property_result", "2025-26", {"holiday_home": True})
    assert code == 2


# ---------------------------------------------------------------- borrowing expenses (s 25-25)

def test_borrowing_expenses_ato_example_peter():
    # Peter: expenses 1,600 (over 100); loan 3 Jul 2025, 25 years -> 5-year period 3 Jul 2025 to 2 Jul 2030 = 1,826 days
    # (one leap day, 29 Feb 2028). Year 1 days 3 Jul to 30 Jun = 363. 1,600 x 363 / 1,826 = 318.07 (ATO: $318.07)
    out = rent(gross_rent=1, borrowing_expenses=[{"amount": 1600, "loan_start_date": "2025-07-03", "loan_term_months": 300}])
    assert out["borrowing_expense_detail"][0]["deductible"] == approx(318.07)
    assert out["deductions"]["total"] == approx(318.07)


def test_borrowing_expenses_ato_example_fiona_max_years_1_and_2():
    # Fiona and Max: 1,670; loan 17 Jul 2025, 20 years; 170,000 of 209,000 borrowed for the rental.
    # Year 1: 1,670 x 349 / 1,826 = 319.18; x 170/209 = 259.62 (ATO)
    y1 = rent(gross_rent=1, borrowing_expenses=[{"amount": 1670, "loan_start_date": "2025-07-17", "loan_term_months": 240,
                                                 "rental_share_of_loan": 170000 / 209000}])
    assert y1["borrowing_expense_detail"][0]["maximum_for_year"] == approx(319.18)
    assert y1["borrowing_expense_detail"][0]["deductible"] == approx(259.62)
    # Year 2 (2026-27): remaining 1,670 - 319.18 = 1,350.82; x 365 / 1,477 = 333.82; x 170/209 = 271.53 (ATO)
    y2 = rent("2026-27", gross_rent=1, borrowing_expenses=[{"amount": 1670, "loan_start_date": "2025-07-17", "loan_term_months": 240,
                                                            "previously_deducted": 319.18, "rental_share_of_loan": 170000 / 209000}])
    assert y2["borrowing_expense_detail"][0]["maximum_for_year"] == approx(333.82)
    assert y2["borrowing_expense_detail"][0]["deductible"] == approx(271.53)


def test_borrowing_expenses_100_or_less_immediate():
    out = rent(gross_rent=1, borrowing_expenses=[{"amount": 90, "loan_start_date": "2025-09-01", "loan_term_months": 300}])
    assert out["borrowing_expense_detail"][0]["deductible"] == approx(90)


def test_borrowing_expenses_short_loan_repaid_early_all_in_year():
    # loan 1 Jul 2025 repaid 31 Dec 2025: period is 184 days, all inside 2025-26, so the whole 1,000 is deductible
    out = rent(gross_rent=1, borrowing_expenses=[{"amount": 1000, "loan_start_date": "2025-07-01", "loan_term_months": 300,
                                                  "loan_repaid_date": "2025-12-31"}])
    assert out["borrowing_expense_detail"][0]["deductible"] == approx(1000)


def test_borrowing_expenses_apportioned_for_private_use():
    # Peter's unrounded 1,600 x 363 / 1,826 = 318.0723; time factor (150 + 32) / 365 = 182 / 365
    out = rent(gross_rent=1, days_rented=150, days_available_commercial_terms=32,
               borrowing_expenses=[{"amount": 1600, "loan_start_date": "2025-07-03", "loan_term_months": 300}])
    assert out["deductions"]["total"] == approx(318.0723 * 182 / 365)


# ---------------------------------------------------------------- depreciation (Div 40)

def test_depreciation_prime_cost_full_year():
    # 1,200 x 365/365 x 100%/10 = 120
    out = rent(gross_rent=1, depreciating_assets=[{"cost": 1200, "effective_life_years": 10}])
    assert out["deductions"]["total"] == approx(120)


def test_depreciation_diminishing_value_years_1_and_2():
    # 2,000 x 200%/8 = 500; next year base 1,500 x 200%/8 = 375
    y1 = rent(gross_rent=1, depreciating_assets=[{"cost": 2000, "effective_life_years": 8, "method": "diminishing_value"}])
    assert y1["deductions"]["total"] == approx(500)
    y2 = rent("2026-27", gross_rent=1, depreciating_assets=[{"cost": 2000, "effective_life_years": 8, "method": "diminishing_value",
                                                             "opening_adjustable_value": 1500}])
    assert y2["deductions"]["total"] == approx(375)


def test_depreciation_part_year_days_held():
    # 1,825 x 100/365 x 1/5 = 100
    out = rent(gross_rent=1, depreciating_assets=[{"cost": 1825, "effective_life_years": 5, "days_held": 100}])
    assert out["deductions"]["total"] == approx(100)


def test_depreciation_low_cost_immediate_and_over_limit():
    # cost 250 within 300 -> 250 in full; cost 350 over the limit -> prime cost 350 / 5 = 70
    assert rent(gross_rent=1, depreciating_assets=[{"cost": 250, "effective_life_years": 5}])["deductions"]["total"] == approx(250)
    assert rent(gross_rent=1, depreciating_assets=[{"cost": 350, "effective_life_years": 5}])["deductions"]["total"] == approx(70)


def test_depreciation_second_hand_denied_after_2017():
    out = rent(gross_rent=1, depreciating_assets=[{"cost": 3000, "effective_life_years": 10, "second_hand": True,
                                                   "acquired_date": "2020-01-01", "installed_date": "2020-01-15"}])
    assert out["deductions"]["total"] == 0
    assert "rental-second-hand-assets" in out["risk_flag_ids"]


def test_depreciation_second_hand_dates_unknown_denied_with_warning():
    out = rent(gross_rent=1, depreciating_assets=[{"cost": 3000, "effective_life_years": 10, "second_hand": True}])
    assert out["deductions"]["total"] == 0
    assert out["warnings"]


def test_depreciation_second_hand_grandfathered():
    # acquired 1 Jan 2016, installed 1 Mar 2016: both before the 9 May 2017 / 1 Jul 2017 cut-offs -> 3,000/10 = 300
    out = rent(gross_rent=1, depreciating_assets=[{"cost": 3000, "effective_life_years": 10, "second_hand": True,
                                                   "acquired_date": "2016-01-01", "installed_date": "2016-03-01",
                                                   "opening_adjustable_value": 1200}])
    assert out["deductions"]["total"] == approx(300)


def test_depreciation_new_asset_apportioned():
    # period 200 days, rented 100 of them: time factor 0.5; asset held the 200 days of the period
    out = rent(gross_rent=1, days_in_period=200, days_rented=100, depreciating_assets=[{"cost": 1200, "effective_life_years": 10}])
    # 1,200 x 200/365 / 10 = 65.753; x 0.5 = 32.877
    assert out["deductions"]["total"] == approx(1200 * 200 / 365 / 10 * 0.5)


# ---------------------------------------------------------------- capital works inside the result

def test_result_includes_capital_works_and_apportions():
    # 400,000 x 2.5% = 10,000; time factor (rented 150 + available 32)/365 applied: 10,000 x 182/365 = 4,986.30
    out = rent(gross_rent=1, days_rented=150, days_available_commercial_terms=32,
               capital_works=[{"construction_cost": 400000, "construction_start_date": "2016-01-01"}])
    assert out["deductions"]["total"] == approx(10000 * 182 / 365)


def test_result_part_year_ownership_capital_works():
    # bought 1 Mar 2026: 122 days (1 Mar to 30 Jun). 400,000 x 2.5% x 122/365 = 3,342.47
    out = rent(gross_rent=1, days_in_period=122, capital_works=[{"construction_cost": 400000, "construction_start_date": "2016-01-01"}])
    assert out["deductions"]["total"] == approx(3342.47)


def test_capital_works_amount_from_schedule_and_loss_example():
    # Rent 26,000. Deductions = interest 21,000 + rates 2,200 + insurance 1,300 + agent 2,080 + repairs 900
    # + capital works per QS schedule 3,000 = 30,480. Principal repayments (8,000) and the bond (2,000) are not in the inputs.
    # Net = 26,000 - 30,480 = -4,480.
    out = rent(gross_rent=26000, capital_works_amount_from_schedule=3000, acquisition_date="2020-03-01",
               expenses={"interest": 21000, "council_rates": 2200, "insurance": 1300, "agent_fees": 2080, "repairs_maintenance": 900})
    assert out["deductions"]["total"] == approx(30480)
    assert out["net_rental_result"] == approx(-4480)
    assert out["negative_gearing"]["status"] == "grandfathered"


def test_capital_works_amount_from_schedule_apportioned_and_denied():
    # 3,000 x (150 + 32)/365 = 1,495.89; holiday home not mainly for rent -> nil
    a = rent(gross_rent=1, days_rented=150, days_available_commercial_terms=32, capital_works_amount_from_schedule=3000)
    assert a["deductions"]["total"] == approx(3000 * 182 / 365)
    b = rent(gross_rent=1, capital_works_amount_from_schedule=3000, holiday_home=True, holiday_home_mainly_for_rent="no")
    assert b["deductions"]["total"] == 0


# ---------------------------------------------------------------- negative gearing (2026 law)

def test_quarantine_step_act_example_henrietta():
    # Act 49 of 2026 Sch 2, s 26-155 example.
    # 2028-29: deductions 65,000, income 50,000 -> deduct 50,000, carry 15,000.
    y1 = quarantine_step(65000, 50000)
    assert (y1["deductible"], y1["quarantined_carried_forward"]) == (50000, 15000)
    # 2029-30: 70,000 + 15,000 brought forward = 85,000 vs income 52,000 -> deduct 52,000, carry 33,000.
    y2 = quarantine_step(70000, 52000, 15000)
    assert (y2["deductible"], y2["quarantined_carried_forward"]) == (52000, 33000)
    # 2030-31: 20,000 + 33,000 = 53,000 vs income 72,000 -> all deductible, carry nil.
    y3 = quarantine_step(20000, 72000, 33000)
    assert (y3["deductible"], y3["quarantined_carried_forward"]) == (53000, 0)


def test_quarantine_step_exempt_dwelling_net_income_reduces_excess():
    # s 26-155(6)(a): excess 60,000 - 50,000 = 10,000 less exempt net income 4,000 = 6,000 carried; deductible 54,000
    q = quarantine_step(60000, 50000, 0, 4000)
    assert (q["deductible"], q["quarantined_carried_forward"]) == (54000, 6000)


def test_no_quarantine_in_2026_27_for_post_cutoff_purchase():
    # Deductions: interest 30,000; income 20,000 -> loss 10,000, fully deductible in 2026-27.
    out = rent("2026-27", gross_rent=20000, expenses={"interest": 30000}, acquisition_date="2026-06-01")
    assert out["net_rental_result"] == approx(-10000)
    assert out["negative_gearing"]["applies_this_year"] is False
    assert out["negative_gearing"]["first_income_year_affected"] == "2027-28"
    assert out["negative_gearing"]["status"] == "subject_to_quarantine"


def test_no_quarantine_in_2025_26_either():
    out = rent("2025-26", gross_rent=20000, expenses={"interest": 30000}, acquisition_date="2026-06-01")
    assert out["net_rental_result"] == approx(-10000)
    assert out["negative_gearing"]["applies_this_year"] is False


def test_preview_2027_28_quarantine_for_post_cutoff_purchase():
    # deductions 30,000 vs income 20,000: excess 10,000 would be quarantined and carried forward;
    # deductible 20,000; net rental result after quarantine 0.
    out = rent("2026-27", gross_rent=20000, expenses={"interest": 30000}, acquisition_date="2026-06-01",
               preview_quarantine_from_2027_28=True)
    p = out["negative_gearing"]["preview_2027_28_if_same_result"]
    assert p["quarantined_carried_forward"] == approx(10000)
    assert p["net_rental_result_after_quarantine"] == 0
    assert out["net_rental_result"] == approx(-10000)  # this year's actual result is unaffected


def test_grandfathered_by_acquisition_date():
    out = rent("2026-27", gross_rent=20000, expenses={"interest": 30000}, acquisition_date="2026-05-11",
               preview_quarantine_from_2027_28=True)
    assert out["negative_gearing"]["status"] == "grandfathered"
    assert out["negative_gearing"]["preview_2027_28_if_same_result"]["quarantined_carried_forward"] == 0


def test_cutoff_day_needs_time():
    out = rent("2026-27", gross_rent=1, acquisition_date="2026-05-12", acquired_before_730pm_on_cutoff_day=True)
    assert out["negative_gearing"]["status"] == "grandfathered"
    out2 = rent("2026-27", gross_rent=1, acquisition_date="2026-05-12", acquired_before_730pm_on_cutoff_day=False)
    assert out2["negative_gearing"]["status"] == "subject_to_quarantine"
    assert refused("rental_property_result", "2026-27", gross_rent=1, acquisition_date="2026-05-12",
                   preview_quarantine_from_2027_28=True) == "AU-RENT-002"


def test_new_dwelling_claim_refused_only_when_it_matters():
    assert refused("rental_property_result", "2026-27", gross_rent=1, claims_new_residential_dwelling=True,
                   preview_quarantine_from_2027_28=True) == "AU-RENT-002"
    out = rent("2026-27", gross_rent=1, claims_new_residential_dwelling=True)
    assert out["negative_gearing"]["status"] == "new_residential_dwelling_claimed"


def test_preview_needs_acquisition_date():
    assert refused("rental_property_result", "2026-27", gross_rent=1, preview_quarantine_from_2027_28=True) == "AU-RENT-002"


def test_excluded_dwelling_kind_not_residential_dwelling():
    out = rent("2026-27", gross_rent=1, dwelling_kind="caravan_or_mobile_home", acquisition_date="2026-06-01")
    assert "not a residential dwelling" in out["negative_gearing"]["status"]


def test_year_without_rates_file_refused():
    # A 2027-28 rates file now exists; 2028-29 does not, so it must be refused as unpublished.
    code, out = run("rental_property_result", "2028-29", {"gross_rent": 1})
    assert code == 4
    assert out["refusal"]["code"] == "AU-GEN-003"


# ---------------------------------------------------------------- refusals

@pytest.mark.parametrize("kw,code", [
    ({"owner_type": "company"}, "AU-RENT-001"),
    ({"owner_type": "trust"}, "AU-RENT-001"),
    ({"owner_type": "smsf"}, "AU-RENT-001"),
    ({"property_type": "commercial"}, "AU-RENT-001"),
    ({"property_development_or_resale": True}, "AU-RENT-001"),
    ({"carrying_on_rental_business": True}, "AU-RENT-001"),
    ({"mixed_use_with_business": True}, "AU-RENT-001"),
    ({"property_location": "overseas"}, "AU-RENT-005"),
])
def test_scope_refusals(kw, code):
    assert refused("rental_property_result", gross_rent=1, **kw) == code


# ---------------------------------------------------------------- envelope

def test_envelope_reports_figures_and_not_draft():
    out = rent(gross_rent=20000, expenses={"interest": 1000}, capital_works=[{"construction_cost": 100000, "construction_start_date": "2001-01-01"}],
               acquisition_date="2026-06-01")
    keys = {f["key"] for f in out["figures_used"]}
    assert "rental.capital_works_rate_residential" in keys
    assert "rental.negative_gearing_first_income_year" in keys
    assert out["draft"] is False
    assert all(f["status"] == "VERIFIED" for f in out["figures_used"])


# ---------------------------------------------------------------- overseas rental: foreign_rental_net (user-stated amounts)

def frn(year="2025-26", **kw):
    code, out = run("foreign_rental_net", year, kw)
    assert code == 0, out
    return out


def test_foreign_rental_net_registered():
    assert "foreign_rental_net" in set(load_all())


def test_foreign_rental_net_bali_villa_and_chain_to_taxable_income_and_fito():
    # Bali villa 2025-26, amounts already in AUD at the ATO annual average (IDR 11,446.3586 per A$1):
    # gross rent 572,317,930 / 11,446.3586 = 50,000; commissions 57,231,793 / 11,446.3586 = 5,000; housekeeping
    # 91,570,869 / 11,446.3586 = 8,000; Indonesian tax 57,231,793 / 11,446.3586 = 5,000 (eval hand computation).
    # Net foreign rent = 50,000 - 5,000 - 8,000 = 37,000; no loan, so no debt deductions.
    out = frn(gross_rent_aud=50000, expenses=[{"label": "platform commissions", "amount_aud": 5000},
                                             {"label": "housekeeping and property manager", "amount_aud": 8000}],
              foreign_tax_paid_aud=5000)
    assert out["net_foreign_rental_income_aud"] == approx(37000)
    assert out["direct_deductions_aud"] == approx(13000) and out["debt_deductions_aud"] == 0
    comps = out["assemble_taxable_income_components"]
    assert [(c["kind"], c["amount"]) for c in comps] == [("foreign_income", 50000), ("other_deduction", 13000)]
    assert out["indonesia_treaty_fito_inputs"] == {
        "items": [{"kind": "rent_real_property", "gross_aud": 50000, "foreign_tax_paid_aud": 5000,
                   "label": "Foreign rental income"}], "related_deductions_aud": 13000}
    # Chain (values from the integration eval's hand computation, ATO rates 2025-26):
    # taxable income = 85,000 salary + 37,000 net rent + 1,800 staking + 5,250 net capital gain = 129,050.
    code, asm = run("assemble_taxable_income", "2025-26", {"components": [
        {"kind": "salary_wages", "amount": 85000, "source_skill": "user"}, *comps,
        {"kind": "other_income", "amount": 1800, "source_skill": "user"},
        {"kind": "net_capital_gain", "amount": 5250, "source_skill": "cgt"}]})
    assert code == 0 and asm["consistent"] is True and asm["taxable_income"] == approx(129050)
    # Tax 4,288 + 0.30 x 84,050 = 29,503; Medicare 2% = 2,581; 32,084 before FITO. Step 2 (taxable 92,050): 18,403 + 1,841
    # = 20,244; limit 11,840; FITO = min(5,000, 11,840) = 5,000; payable 27,084.
    code, res = run("indonesia_treaty_fito", "2025-26", {**out["indonesia_treaty_fito_inputs"], "taxable_income": 129050,
                                                          "private_hospital_cover": True})
    assert code == 0, res
    assert res["fito"]["offset_limit"] == approx(11840) and res["fito"]["offset_after_limit"] == approx(5000)
    assert res["fito"]["tax_payable_after_fito"] == approx(27084)


def test_foreign_rental_net_debt_deductions_stay_out_of_the_fito_related_deductions():
    # Gross 50,000; direct 13,000; interest 4,000 (a debt deduction): net = 50,000 - 13,000 - 4,000 = 33,000.
    # The offset's step 2 removes the income less related non-debt deductions only: 50,000 - 13,000 = 37,000 (s 770-75(4)).
    out = frn(gross_rent_aud=50000, expenses=[{"label": "management", "amount_aud": 13000},
                                             {"label": "loan interest", "amount_aud": 4000, "debt_deduction": True}],
              foreign_tax_paid_aud=5000)
    assert out["net_foreign_rental_income_aud"] == approx(33000)
    assert out["direct_deductions_aud"] == approx(13000) and out["debt_deductions_aud"] == approx(4000)
    assert [(c["kind"], c["amount"]) for c in out["assemble_taxable_income_components"]] == [
        ("foreign_income", 50000), ("other_deduction", 13000), ("other_deduction", 4000)]
    assert out["indonesia_treaty_fito_inputs"]["related_deductions_aud"] == approx(13000)
    assert out["foreign_income_tax_offset_inputs"] == {"foreign_tax_paid": 5000, "foreign_net_income": 37000}


def test_foreign_rental_net_does_not_decide_deductibility_and_lists_what_is_not_checked():
    out = frn(gross_rent_aud=10000, expenses=[{"label": "management", "amount_aud": 1000}])
    assert any(e["code"] == "AU-RENT-005" for e in out["escalations"])
    assert any("depreciation" in w.lower() for w in out["warnings"])


@pytest.mark.parametrize("kw,code", [
    ({"gross_rent_aud": 10000, "expenses": [{"label": "repairs", "amount_aud": 12000}]}, "AU-RENT-005"),   # a loss
    ({"gross_rent_aud": 10000, "any_owner_or_family_use": True}, "AU-RENT-005"),                        # private use
    ({"gross_rent_aud": 10000, "owner_type": "company"}, "AU-RENT-001"),
])
def test_foreign_rental_net_refusals(kw, code):
    assert refused("foreign_rental_net", **kw) == code


def test_overseas_refusal_detail_points_to_foreign_rental_net():
    code, out = run("rental_property_result", "2025-26", {"property_location": "overseas", "gross_rent": 1})
    assert code == 3 and out["refusal"]["code"] == "AU-RENT-005"
    assert "foreign_rental_net" in out["refusal"]["detail"]
