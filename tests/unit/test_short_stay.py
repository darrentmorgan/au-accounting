"""Short-stay accommodation tools: short_stay_apportionment, gst_short_stay_classification, div87_stay_gst,
serr_report_check, serr_income_reconciliation.

Expected values come from the primary-source brief (docs/research/short-stay-accommodation.md section 10, which
worked each example by hand from PCG 2026/2, TR 2026/1, GSTA 1999 Div 87, LI 2025/5 and the ATO SERR pages) or are
hand computations shown step by step here. None were produced by running the calculators."""

import pytest

from au_tax.mcp_server import build
from au_tax.registry import load_all, run


def ok(tool, year="2026-27", **kw):
    code, out = run(tool, year, kw)
    assert code == 0, out
    return out


def refused(tool, year="2026-27", **kw):
    code, out = run(tool, year, kw)
    assert code == 3, out
    return out["refusal"]["code"]


def approx(x, tol=0.01):
    return pytest.approx(x, abs=tol)


def test_registered():
    assert {"short_stay_apportionment", "gst_short_stay_classification", "div87_stay_gst", "serr_report_check",
            "serr_income_reconciliation"} <= set(load_all())


# ------------------------------------------------------------ short_stay_apportionment: brief Example A

EX_A = dict(
    days_owned=365, nights_rented=225, nights_available_commercial_terms=119, nights_owner_use=14,
    nights_family_friends_free_or_reduced=7,
    gross_rent=54000,
    direct_costs=[{"description": "platform commission", "amount": 6480}, {"description": "guest cleaning", "amount": 9000}],
    ownership_costs=[{"description": "interest", "amount": 21600}, {"description": "council rates", "amount": 2400},
                     {"description": "water", "amount": 1100}, {"description": "insurance", "amount": 1900},
                     {"description": "repairs", "amount": 1000}, {"description": "capital works", "amount": 6000}],
)


def test_example_a_green_zone_holiday_home_apportioned():
    # Brief Example A. 225 + 119 + 14 + 7 = 365 nights, all accounted for.
    # Holiday home (owner and friends stay free) and mainly for rent (green zone facts): s 26-50 exception applies.
    # Direct costs 6,480 + 9,000 = 15,480 in full.
    # Time share = (225 + 119) / 365 = 344/365 = 0.942466. Ownership costs 34,000 x 344/365 = 32,043.84.
    # Deductions 32,043.84 + 15,480 = 47,523.84. Net rental income 54,000 - 47,523.84 = 6,476.16.
    out = ok("short_stay_apportionment", holiday_home_mainly_for_rent="yes", **EX_A)
    assert out["apportionment"]["time_factor"] == pytest.approx(344 / 365, abs=1e-6)
    assert out["apportionment"]["area_factor"] == 1.0
    assert out["direct_costs_deductible"] == approx(15480)
    assert out["ownership_costs_total"] == approx(34000)
    assert out["ownership_costs_deductible"] == approx(32043.84)
    assert out["private_portion_of_ownership_costs"] == approx(1956.16)
    assert out["total_deductions"] == approx(47523.84)
    assert out["net_rental_result"] == approx(6476.16)
    assert out["section_26_50"]["holiday_home"] is True
    assert out["section_26_50"]["ownership_costs_denied"] is False
    assert "short-stay-friends-family-reduced-rate" in out["risk_flag_ids"]


def test_example_a_matches_rental_property_result_when_handed_off():
    # The handoff block must run through rental_property_result to the same net result (6,476.16 by hand above).
    out = ok("short_stay_apportionment", holiday_home_mainly_for_rent="yes", **EX_A)
    h = out["rental_property_result_handoff"]
    code, r = run("rental_property_result", "2026-27", {
        **h, "gross_rent": 54000,
        "expenses": {"platform_fees": 6480, "guest_cleaning_and_linen": 9000, "interest": 21600, "council_rates": 2400,
                     "water_charges": 1100, "insurance": 1900, "repairs_maintenance": 1000},
        "capital_works_amount_from_schedule": 6000})
    assert code == 0, r
    assert r["net_rental_result"] == approx(6476.16)


def test_example_a_step8_red_zone_ownership_costs_denied():
    # Brief Example A step 8. Rented 60 nights, gross 60 x 240 = 14,400; commission 1,728 and cleaning 2,400 are direct.
    # Christmas, Easter and school holidays blocked (305 other nights unused and not available).
    # s 26-50(1) denies all 34,000 of ownership costs (no apportionment). Deductions 1,728 + 2,400 = 4,128.
    # Net rental income 14,400 - 4,128 = 10,272.
    out = ok("short_stay_apportionment", days_owned=365, nights_rented=60, nights_blocked_unused=305,
             holiday_home_mainly_for_rent="no", gross_rent=14400,
             direct_costs=[{"description": "commission", "amount": 1728}, {"description": "cleaning", "amount": 2400}],
             ownership_costs=EX_A["ownership_costs"])
    assert out["ownership_costs_deductible"] == 0
    assert out["denied_ownership_costs"] == approx(34000)
    assert out["total_deductions"] == approx(4128)
    assert out["net_rental_result"] == approx(10272)
    assert out["section_26_50"]["ownership_costs_denied"] is True
    assert "short-stay-blocked-peak-periods" in out["risk_flag_ids"]


def test_2025_26_denial_notes_ato_compliance_start_not_a_change_in_law():
    # Same red facts in 2025-26: the law denies; the ATO only stops reviewing s 26-50 for expenses before 1 Jul 2026.
    out = ok("short_stay_apportionment", year="2025-26", days_owned=365, nights_rented=60, nights_blocked_unused=305,
             holiday_home_mainly_for_rent="no", gross_rent=14400, ownership_costs=[{"amount": 34000}])
    assert out["section_26_50"]["ownership_costs_denied"] is True
    assert any("1 Jul 2026" in w or "compliance" in w for w in out["warnings"])


# ------------------------------------------------------------ brief Example B: room in the owner's home

def test_example_b_room_in_home_area_and_time():
    # Brief Example B. Area share = (14 + 46/2) / 120 = 37/120 = 0.308333.
    # A room in the home has no held days: 128 rented of 365 = 0.350685 (the 237 unoccupied nights are private
    # even though the listing stayed live).
    # Combined = 37/120 x 128/365 = 4,736/43,800 = 0.108128. Ownership 22,000 x 0.108128 = 2,378.81.
    # Direct 1,050 + 1,280 = 2,330. Total 4,708.81. Net 23,040 - 4,708.81 = 18,331.19.
    out = ok("short_stay_apportionment", days_owned=365, nights_rented=128, nights_available_commercial_terms=237,
             part_of_home=True, area_exclusive_to_tenant=14, area_shared_common=46, area_total=120, gross_rent=23040,
             direct_costs=[{"description": "commission", "amount": 1050}, {"description": "laundry", "amount": 1280}],
             ownership_costs=[{"description": "interest", "amount": 15200}, {"description": "rates", "amount": 2100},
                              {"description": "insurance", "amount": 1300}, {"description": "power water internet", "amount": 3400}])
    a = out["apportionment"]
    assert a["area_factor"] == pytest.approx(37 / 120, abs=1e-6)
    assert a["time_factor"] == pytest.approx(128 / 365, abs=1e-6)
    assert a["combined_factor"] == pytest.approx(4736 / 43800, abs=1e-6)
    assert out["ownership_costs_deductible"] == approx(2378.81)
    assert out["direct_costs_deductible"] == approx(2330)
    assert out["total_deductions"] == approx(4708.81)
    assert out["net_rental_result"] == approx(18331.19)
    assert out["section_26_50"]["holiday_home"] is False  # a room in the owner's own home is not a holiday home
    assert "short-stay-room-held-days" in out["risk_flag_ids"]
    assert out["rental_property_result_handoff"]["days_available_commercial_terms"] == 0


def test_example_b_matches_rental_property_result():
    out = ok("short_stay_apportionment", days_owned=365, nights_rented=128, nights_available_commercial_terms=237,
             part_of_home=True, area_exclusive_to_tenant=14, area_shared_common=46, area_total=120, gross_rent=23040,
             direct_costs=[{"amount": 2330}], ownership_costs=[{"amount": 22000}])
    code, r = run("rental_property_result", "2026-27", {
        **out["rental_property_result_handoff"], "gross_rent": 23040,
        "expenses": {"platform_fees": 1050, "guest_cleaning_and_linen": 1280, "interest": 15200, "council_rates": 2100,
                     "insurance": 1300, "bank_fees_other_ownership": 3400}})
    assert code == 0, r
    assert r["net_rental_result"] == approx(18331.19)


def test_main_residence_let_while_away_is_time_based_only():
    # Main residence, whole home, owner away for the bookings: time-based only (PCG 2026/2), on nights let.
    # 40 nights let of 365: 40/365 = 0.109589; ownership 10,000 x 40/365 = 1,095.89; direct 100% (500).
    # Owner lives there the other 325 nights: private, and not a holiday home (it is the main residence).
    out = ok("short_stay_apportionment", days_owned=365, nights_rented=40, nights_owner_use=325, is_main_residence=True,
             gross_rent=6000, direct_costs=[{"amount": 500}], ownership_costs=[{"amount": 10000}])
    assert out["section_26_50"]["holiday_home"] is False
    assert out["ownership_costs_deductible"] == approx(1095.89)
    assert out["total_deductions"] == approx(1595.89)
    assert out["net_rental_result"] == approx(4404.11)


def test_part_year_ownership_uses_days_owned():
    # Owned 200 days; 150 rented and 50 available: (150 + 50) / 200 = 1. Full ownership costs of 2,000 deductible.
    out = ok("short_stay_apportionment", days_owned=200, nights_rented=150, nights_available_commercial_terms=50,
             gross_rent=9000, ownership_costs=[{"amount": 2000}])
    assert out["apportionment"]["time_factor"] == 1.0
    assert out["ownership_costs_deductible"] == approx(2000)


def test_ownership_percent_splits_by_title():
    # 50% co-owner: whole-property amounts, result is half. Rent 10,000, ownership 4,000 all rented: net (10,000-4,000)/2 = 3,000.
    out = ok("short_stay_apportionment", days_owned=365, nights_rented=100, nights_available_commercial_terms=265,
             ownership_percent=50, gross_rent=10000, ownership_costs=[{"amount": 4000}])
    assert out["net_rental_result"] == approx(3000)
    assert "rental-co-ownership-title" in out["risk_flag_ids"]


def test_default_days_owned_is_calendar_year():
    out = ok("short_stay_apportionment", nights_rented=100, nights_available_commercial_terms=265, gross_rent=1000)
    assert out["apportionment"]["days_owned"] == 365


# ------------------------------------------------------------ apportionment refusals and input errors

def test_holiday_home_test_unresolved_refuses_rent_003():
    assert refused("short_stay_apportionment", days_owned=365, nights_rented=200, nights_available_commercial_terms=100,
                   nights_owner_use=65, holiday_home_mainly_for_rent="unresolved") == "AU-RENT-003"


def test_holiday_home_answer_missing_refuses_rent_003():
    assert refused("short_stay_apportionment", days_owned=365, nights_rented=200, nights_available_commercial_terms=100,
                   nights_family_friends_free_or_reduced=65) == "AU-RENT-003"


def test_nights_closed_for_repairs_refuses_ss_003():
    # Day treatment of nights closed for repairs is not settled (brief open question O8).
    assert refused("short_stay_apportionment", days_owned=365, nights_rented=200, nights_available_commercial_terms=100,
                   nights_closed_repairs=65) == "AU-SS-003"


def test_company_owner_refuses_rent_001():
    assert refused("short_stay_apportionment", owner_type="company", days_owned=365, nights_rented=365) == "AU-RENT-001"


def test_business_of_letting_refuses_rent_001():
    assert refused("short_stay_apportionment", carrying_on_rental_business=True, days_owned=365, nights_rented=365) == "AU-RENT-001"


def test_overseas_property_refuses_rent_005():
    assert refused("short_stay_apportionment", property_location="overseas", days_owned=365, nights_rented=365) == "AU-RENT-005"


def test_nights_must_account_for_every_day_owned():
    code, out = run("short_stay_apportionment", "2026-27", {"days_owned": 365, "nights_rented": 100})
    assert code == 2 and "365" in out["error"]


def test_2027_28_is_a_366_day_year_so_nights_must_add_to_366():
    # 1 Jul 2027 to 30 Jun 2028 includes 29 Feb 2028. The default days owned is 366, so 100 nights alone do not
    # account for the year (exit 2), and 365 nights (a 2026-27 style year) do not either.
    code, out = run("short_stay_apportionment", "2027-28", {"nights_rented": 100})
    assert code == 2 and "366" in out["error"]
    code, out = run("short_stay_apportionment", "2027-28", {"nights_rented": 365})
    assert code == 2 and "366" in out["error"]


def test_2027_28_time_factor_uses_a_366_day_denominator():
    # Owned all 366 days: rented 250 nights, available on commercial terms 55, owner use 61 (250 + 55 + 61 = 366).
    # Time factor (PCG 2026/2) = (nights rented + nights available) / days owned = (250 + 55) / 366 = 305 / 366.
    # Ownership costs 12,000 x 305 / 366 = 12,000 x 0.833333... = 10,000.00 deductible; private portion 2,000.
    # Direct letting costs 1,500 deductible in full. Gross rent 40,000. Net = 40,000 - 1,500 - 10,000 = 28,500.
    # (Holiday home gate: owner use of the whole property with holiday_home_mainly_for_rent yes keeps the costs.)
    out = ok("short_stay_apportionment", "2027-28", nights_rented=250, nights_available_commercial_terms=55, nights_owner_use=61,
             gross_rent=40000, direct_costs=[{"description": "cleaning", "amount": 1500}],
             ownership_costs=[{"description": "rates and insurance", "amount": 12000}], holiday_home_mainly_for_rent="yes")
    assert out["apportionment"]["days_in_income_year"] == 366 and out["apportionment"]["time_factor"] == approx(0.833333, 1e-6)
    assert out["ownership_costs_deductible"] == approx(10000) and out["private_portion_of_ownership_costs"] == approx(2000)
    assert out["net_rental_result"] == approx(28500)
    # the same nights in 2026-27 (365 days) do not add up: 366 nights is not a 2026-27 year
    code, res = run("short_stay_apportionment", "2026-27", {"nights_rented": 250, "nights_available_commercial_terms": 55,
                                                             "nights_owner_use": 61})
    assert code == 2 and "365" in res["error"]


def test_2027_28_serr_due_dates_and_thresholds_are_in_the_2027_28_overlay():
    # ATO SERR page: 31 January (1 Jul to 31 Dec transactions) and 31 July (1 Jan to 30 Jun). In the 2027-28 income year:
    # 31 Jan 2028 is a Monday and 31 Jul 2028 is a Monday (1 Jan 2028 and 1 Jul 2028 are Saturdays), so no weekend warning.
    # 31 Jul 2028 is after the holiday data, so it is returned unrolled with an AU-GEN-004 field note (tested below).
    # LI 2025/5: substantial supplier 1,000,000 GST inclusive; substantial property 2,000 transactions.
    out = ok("serr_report_check", "2027-28", booking_entered_date="2027-09-10", supplier_value_12m_gst_inclusive=999999.99)
    assert out["status"] == "reportable"
    due = out["platform_report_due_dates"]
    assert due["period_1_jul_to_31_dec"]["due"] == "2028-01-31" and due["period_1_jul_to_31_dec"]["weekday"] == "Monday"
    assert due["period_1_jan_to_30_jun"]["due"] == "2028-07-31" and due["period_1_jan_to_30_jun"]["weekday"] == "Monday"
    assert not any("weekend" in w for w in out["warnings"])
    out = ok("serr_report_check", "2027-28", booking_entered_date="2027-09-10", supplier_value_12m_gst_inclusive=1000000)
    assert out["status"] == "exempt"
    out = ok("serr_report_check", "2027-28", booking_entered_date="2027-09-10", property_platform_transactions_12m=2000)
    assert out["status"] == "exempt"


def test_misspelt_field_is_rejected():
    code, _ = run("short_stay_apportionment", "2026-27", {"nights_rentd": 5})
    assert code == 2


# ------------------------------------------------------------ gst_short_stay_classification

def test_two_furnished_spare_rooms_linen_only_input_taxed():
    # GSTR 2012/6 Example 3 (paras 51-52): house with two furnished spare rooms, linen only: not CRP, input taxed.
    out = ok("gst_short_stay_classification", premises_kind="rooms_in_owners_home", annual_rent=30000)
    assert out["classification"] == "residential_premises_input_taxed"
    assert out["gst_charged_on_rent"] is False
    assert out["input_tax_credits_on_related_costs"] is False
    assert out["counts_toward_gst_turnover"] is False
    assert out["division_87_applies"] is False
    assert out["handoff_gst_registration_check"] == {"input_taxed_sales_included": 30000}


def test_house_let_on_platforms_input_taxed_whatever_the_length_of_stay():
    out = ok("gst_short_stay_classification", premises_kind="house", annual_rent=250000)
    assert out["classification"] == "residential_premises_input_taxed"


def test_strata_apartment_let_through_on_site_agent_manager_input_taxed():
    # GSTR 2012/6 Example 12 (paras 82-85): one strata apartment let through an on-site manager acting as agent.
    out = ok("gst_short_stay_classification", premises_kind="room_or_apartment_in_managed_complex",
             perspective="owner_letting_own_premises", annual_rent=40000)
    assert out["classification"] == "residential_premises_input_taxed"
    assert any("agent" in n.lower() for n in out["notes"])


def test_owner_leasing_apartment_to_hotel_operator_input_taxed_for_owner():
    # GSTR 2012/6 paras 95-98 and Example 16: the owner's lease of one apartment is input taxed;
    # the operator's supplies to guests are a separate question.
    out = ok("gst_short_stay_classification", premises_kind="room_or_apartment_in_managed_complex",
             perspective="owner_leasing_to_operator")
    assert out["classification"] == "residential_premises_input_taxed"
    assert any("operator" in n.lower() for n in out["notes"])


def test_owner_leasing_whole_complex_refuses_gst_002():
    assert refused("gst_short_stay_classification", premises_kind="room_or_apartment_in_managed_complex",
                   perspective="owner_leasing_to_operator", leased_together_with_whole_complex=True) == "AU-GST-002"


def test_hosted_bnb_with_daily_cleaning_breakfast_reception_refuses_gst_002():
    # GSTR 2012/6 Example 2 (paras 49-50): three bedrooms, communal dining, on-site owner, daily cleaning, breakfast:
    # the ATO reaches CRP. The tool never decides; it refuses.
    assert refused("gst_short_stay_classification", premises_kind="rooms_in_owners_home",
                   daily_cleaning_or_housekeeping=True, meals_or_communal_dining_provided=True,
                   reception_or_front_desk_operated_by_supplier=True) == "AU-GST-002"


def test_single_indicator_is_enough_to_escalate():
    assert refused("gst_short_stay_classification", premises_kind="house", meals_or_communal_dining_provided=True) == "AU-GST-002"


def test_head_lease_operator_refuses_gst_002():
    assert refused("gst_short_stay_classification", premises_kind="unit_or_apartment",
                   perspective="operator_supplying_guests") == "AU-GST-002"


def test_listed_crp_category_refuses_gst_002():
    assert refused("gst_short_stay_classification", premises_kind="hotel_motel_inn_hostel_or_boarding_house") == "AU-GST-002"
    assert refused("gst_short_stay_classification", premises_kind="caravan_park_or_camping_ground") == "AU-GST-002"


def test_registration_question_from_platform_income_warns_and_names_ss_001():
    out = ok("gst_short_stay_classification", premises_kind="house", asked_must_register_because_of_platform_income=True)
    assert any("AU-SS-001" in w for w in out["warnings"])
    assert out["classification"] == "residential_premises_input_taxed"


def test_example_e_registration_turnover_excludes_the_residential_rent():
    # Brief Example E. Rent 180,000 (input taxed) + consulting 60,000 + management fees 20,000 = 260,000 gross.
    # GST turnover = 260,000 - 180,000 = 80,000, which is 5,000 over the 75,000 threshold on the ATO page.
    # Before the management fees: 240,000 - 180,000 = 60,000, under the threshold.
    cls = ok("gst_short_stay_classification", premises_kind="house", annual_rent=180000)
    inp = cls["handoff_gst_registration_check"]
    under = ok("gst_registration_check", entity_type="business", current_gst_turnover=240000, projected_gst_turnover=240000, **inp)
    assert under["current_gst_turnover"] == approx(60000) and under["status"] == "not_required"
    over = ok("gst_registration_check", entity_type="business", current_gst_turnover=260000, projected_gst_turnover=260000, **inp)
    assert over["current_gst_turnover"] == approx(80000) and over["status"] == "must_register"


# ------------------------------------------------------------ div87_stay_gst (brief Examples F and G)

NIGHTLY = 330  # GST-inclusive: 300 plus 30


def test_example_f_forty_nights_not_predominantly_long_term():
    # Nights 1 to 27 at full price: 27 x 330 = 8,910, GST 27 x 30 = 810.
    # Nights 28 to 40 (13): price 13 x 330 = 4,290; value = 50% of that = 2,145 (s 87-10(1)(d)); GST 10% = 214.50.
    # Total GST 810 + 214.50 = 1,024.50. Without Div 87: 40 x 30 = 1,200.
    out = ok("div87_stay_gst", crp_confirmed=True, nights=40, nightly_price_gst_inclusive=NIGHTLY,
             bookings_total_12m=100, bookings_28_nights_or_more_12m=10)
    assert out["long_term_accommodation"] is True and out["predominantly_long_term"] is False
    assert out["gst_first_27_days"] == approx(810)
    assert out["value_after_first_27_days"] == approx(2145)
    assert out["gst_after_first_27_days"] == approx(214.50)
    assert out["gst_payable"] == approx(1024.50)
    assert out["gst_without_division_87"] == approx(1200)
    assert out["gst_per_night_after_first_27_days"] == approx(16.50)
    assert out["total_charged_if_gst_exclusive_rate_unchanged"] == approx(13024.50)


def test_example_f_predominantly_long_term_halves_from_day_one():
    # 70 of 100 bookings are 28 nights or more: at least 70%, so predominantly long-term (s 87-20(3)).
    # Value = 50% x (40 x 330 = 13,200) = 6,600; GST 660.
    out = ok("div87_stay_gst", crp_confirmed=True, nights=40, nightly_price_gst_inclusive=NIGHTLY,
             bookings_total_12m=100, bookings_28_nights_or_more_12m=70)
    assert out["predominantly_long_term"] is True
    assert out["gst_payable"] == approx(660)


def test_just_below_seventy_percent_is_not_predominantly_long_term():
    out = ok("div87_stay_gst", crp_confirmed=True, nights=40, nightly_price_gst_inclusive=NIGHTLY,
             bookings_total_12m=100, bookings_28_nights_or_more_12m=69)
    assert out["predominantly_long_term"] is False and out["gst_payable"] == approx(1024.50)


def test_example_f_election_not_to_apply_division_87_input_taxes_the_long_stay():
    # s 87-25: long-term supplies input taxed, GST nil (and no credits on the operator's costs).
    out = ok("div87_stay_gst", crp_confirmed=True, nights=40, nightly_price_gst_inclusive=NIGHTLY,
             bookings_total_12m=100, bookings_28_nights_or_more_12m=10, elected_not_to_apply_division_87=True)
    assert out["gst_payable"] == 0
    assert out["input_taxed"] is True


def test_example_f_twenty_night_stay_is_fully_taxable_even_with_election():
    # 20 x 30 = 600 GST (1/11 of 20 x 330 = 6,600 is 600).
    out = ok("div87_stay_gst", crp_confirmed=True, nights=20, nightly_price_gst_inclusive=NIGHTLY,
             bookings_total_12m=100, bookings_28_nights_or_more_12m=10, elected_not_to_apply_division_87=True)
    assert out["long_term_accommodation"] is False
    assert out["gst_payable"] == approx(600)
    assert out["input_taxed"] is False


def test_example_g_counting_to_28_from_dates():
    # Check-in 1 Mar 2027 to check-out 28 Mar: arrival day counts, departure day does not: 27 days, not long-term.
    a = ok("div87_stay_gst", crp_confirmed=True, check_in="2027-03-01", check_out="2027-03-28",
           nightly_price_gst_inclusive=NIGHTLY, bookings_total_12m=100, bookings_28_nights_or_more_12m=10)
    assert a["days_provided"] == 27 and a["long_term_accommodation"] is False
    assert a["gst_payable"] == approx(27 * 30)
    # Check-out 29 Mar: 28 days, long-term. First 27 days 810 GST; one more day at half: 10% x 165 = 16.50.
    b = ok("div87_stay_gst", crp_confirmed=True, check_in="2027-03-01", check_out="2027-03-29",
           nightly_price_gst_inclusive=NIGHTLY, bookings_total_12m=100, bookings_28_nights_or_more_12m=10)
    assert b["days_provided"] == 28 and b["long_term_accommodation"] is True
    assert b["gst_payable"] == approx(810 + 16.50)


def test_div87_needs_crp_confirmed_by_a_person():
    assert refused("div87_stay_gst", crp_confirmed=False, nights=40, nightly_price_gst_inclusive=NIGHTLY,
                   bookings_total_12m=100, bookings_28_nights_or_more_12m=10) == "AU-GST-002"


def test_div87_dates_and_nights_must_agree():
    code, out = run("div87_stay_gst", "2026-27", {"crp_confirmed": True, "check_in": "2027-03-01", "check_out": "2027-03-29",
                                                  "nights": 20, "nightly_price_gst_inclusive": 330,
                                                  "bookings_total_12m": 10, "bookings_28_nights_or_more_12m": 1})
    assert code == 2


def test_div87_figures_are_reported():
    out = ok("div87_stay_gst", crp_confirmed=True, nights=40, nightly_price_gst_inclusive=NIGHTLY,
             bookings_total_12m=100, bookings_28_nights_or_more_12m=10)
    keys = {f["key"] for f in out["figures_used"]}
    assert {"gst.div87_long_term_days", "gst.div87_predominantly_long_term_share", "gst.div87_value_share", "gst.rate"} <= keys


# ------------------------------------------------------------ serr_report_check

def test_short_stay_booking_from_a_normal_host_is_reportable():
    out = ok("serr_report_check", booking_entered_date="2026-08-10", supplier_value_12m_gst_inclusive=61480,
             property_platform_transactions_12m=40)
    assert out["status"] == "reportable"
    assert out["host_filing_duty"] is False
    assert out["applies_from"] == "2023-07-01"
    assert out["exemptions_triggered"] == []
    assert "fees and commissions withheld" in " ".join(out["what_is_reported"]).lower()


def test_no_90_day_limit_in_the_current_instrument():
    # LI 2025/5 has no 90-consecutive-day concept; a long booking is not exempt for that reason.
    out = ok("serr_report_check", booking_entered_date="2026-08-10", supplier_value_12m_gst_inclusive=20000)
    assert out["status"] == "reportable"
    assert not any("90" in r for r in out["reasons"])


def test_booking_before_start_date_not_in_scope():
    out = ok("serr_report_check", booking_entered_date="2023-06-30")
    assert out["status"] == "not_in_scope"
    out2 = ok("serr_report_check", booking_entered_date="2023-07-01")
    assert out2["status"] == "reportable"


def test_substantial_supplier_exempt_at_one_million_and_prorated_for_new_supplier():
    # 1,000,000 or more (GST inclusive) in the 12 months: exempt (LI 2025/5 s 7(2)).
    assert ok("serr_report_check", booking_entered_date="2026-08-10", supplier_value_12m_gst_inclusive=1000000)["status"] == "exempt"
    assert ok("serr_report_check", booking_entered_date="2026-08-10", supplier_value_12m_gst_inclusive=999999.99)["status"] == "reportable"
    # New supplier active 100 days: prorated amount = 1,000,000 x 100/365 = 273,972.60. 300,000 is at or above it.
    out = ok("serr_report_check", booking_entered_date="2026-08-10", supplier_value_12m_gst_inclusive=300000,
             days_supplier_active_on_platform_12m=100)
    assert out["status"] == "exempt"
    assert out["substantial_supplier_amount_applied"] == approx(273972.60)


def test_substantial_property_exempt_at_two_thousand_transactions_prorated():
    assert ok("serr_report_check", booking_entered_date="2026-08-10", property_platform_transactions_12m=2000)["status"] == "exempt"
    assert ok("serr_report_check", booking_entered_date="2026-08-10", property_platform_transactions_12m=1999)["status"] == "reportable"
    # Listed 73 days: prorated = 2,000 x 73/365 = 400. 400 transactions is at the amount.
    out = ok("serr_report_check", booking_entered_date="2026-08-10", property_platform_transactions_12m=400,
             days_property_listed_12m=73)
    assert out["status"] == "exempt" and out["substantial_property_amount_applied"] == approx(400)


def test_other_exemptions_listed_entity_platform_agent_no_price_and_chain():
    for kw in ({"supplier_is_listed_entity_or_government": True},
               {"booking_has_no_price_and_no_platform_payment": True},
               {"another_platform_reports_and_exemption_notified": True}):
        assert ok("serr_report_check", booking_entered_date="2026-08-10", **kw)["status"] == "exempt", kw
    out = ok("serr_report_check", booking_entered_date="2026-08-10", platform_role="agent_on_own_site_only")
    assert out["status"] == "not_in_scope"


def test_foreign_supplier_exemption_needs_all_four_conditions():
    assert ok("serr_report_check", booking_entered_date="2026-08-10", supplier_has_no_australian_link_on_all_four_tests=True)["status"] == "exempt"
    assert ok("serr_report_check", booking_entered_date="2026-08-10", supplier_has_no_australian_link_on_all_four_tests=False)["status"] == "reportable"


def test_overseas_property_refuses_ss_002():
    # Open question O3: Australian-resident host of a Bali villa. State the rule and escalate.
    assert refused("serr_report_check", booking_entered_date="2026-08-10", property_location="overseas") == "AU-SS-002"


def test_report_due_dates_for_2026_27_roll_to_the_next_business_day():
    # TAA 1953 Sch 1 s 388-52: a due date that is not a business day moves to the first business day after.
    # 31 Jan 2027 is a Sunday (1 Jan 2027 is a Friday, so 31 Jan is 30 days later = Sunday) -> Mon 1 Feb 2027, not a holiday.
    # 31 Jul 2027 is a Saturday (1 Jul 2027 is a Thursday) and Sun 1 Aug 2027 -> Mon 2 Aug 2027 is Picnic Day in the NT, a public
    # holiday for the whole of a Territory (ATO table prints the same for 3 Aug 2026), so the date is Tue 3 Aug 2027.
    out = ok("serr_report_check", booking_entered_date="2026-08-10")
    d = out["platform_report_due_dates"]
    a = d["period_1_jul_to_31_dec"]
    assert (a["period_start"], a["period_end"]) == ("2026-07-01", "2026-12-31")
    assert (a["statutory_due"], a["statutory_weekday"]) == ("2027-01-31", "Sunday")
    assert (a["due"], a["weekday"]) == ("2027-02-01", "Monday")
    assert a["business_day_roll"]["rolled"] is True and a["business_day_roll"]["original_date"] == "2027-01-31"
    assert a["business_day_roll"]["regime"] == "commonwealth_tax" and "388-52" in a["business_day_roll"]["rule"]
    b = d["period_1_jan_to_30_jun"]
    assert (b["statutory_due"], b["statutory_weekday"]) == ("2027-07-31", "Saturday")
    assert (b["due"], b["weekday"]) == ("2027-08-03", "Tuesday")
    assert "Picnic Day" in b["business_day_roll"]["reason"]
    assert not any("weekend" in w for w in out["warnings"])
    assert out["field_refusals"] == []


def test_report_due_dates_for_2025_26():
    # 31 Jan 2026 is a Saturday -> Sun 1 Feb -> Mon 2 Feb 2026 (no holiday); 31 Jul 2026 is a Friday (business day, no roll).
    out = ok("serr_report_check", year="2025-26", booking_entered_date="2025-08-10")
    d = out["platform_report_due_dates"]
    assert d["period_1_jul_to_31_dec"]["statutory_due"] == "2026-01-31" and d["period_1_jul_to_31_dec"]["statutory_weekday"] == "Saturday"
    assert d["period_1_jul_to_31_dec"]["due"] == "2026-02-02" and d["period_1_jul_to_31_dec"]["weekday"] == "Monday"
    assert d["period_1_jan_to_30_jun"]["due"] == "2026-07-31" and d["period_1_jan_to_30_jun"]["weekday"] == "Friday"
    assert d["period_1_jan_to_30_jun"]["business_day_roll"]["rolled"] is False


def test_report_due_date_after_the_holiday_data_keeps_the_scope_result_and_flags_the_date():
    # 2027-28: 31 Jul 2028 (a Monday) is after the holiday data (ends 30 Jun 2028). The scope check is still answered; that one
    # date is the unrolled statutory date with a per-field AU-GEN-004 note. 31 Jan 2028 (Monday) is inside the data: no roll.
    out = ok("serr_report_check", "2027-28", booking_entered_date="2027-09-10")
    assert out["status"] == "reportable"
    d = out["platform_report_due_dates"]
    assert d["period_1_jul_to_31_dec"]["due"] == "2028-01-31" and d["period_1_jul_to_31_dec"]["business_day_roll"]["rolled"] is False
    j = d["period_1_jan_to_30_jun"]
    assert j["due"] == j["statutory_due"] == "2028-07-31" and j["business_day_roll"]["rolled"] is False
    assert j["business_day_roll"]["holiday_data_covers_date"] is False
    assert [f["code"] for f in out["field_refusals"]] == ["AU-GEN-004"]
    assert out["field_refusals"][0]["field"] == "platform_report_due_dates.period_1_jan_to_30_jun"
    assert "public holiday dates" in out["field_refusals"][0]["message"]
    assert any("2028-07-31" in w and "AU-GEN-004" in w for w in out["warnings"])


def test_serr_figures_reported_including_iso_date_survives_mcp():
    import anyio

    out = ok("serr_report_check", booking_entered_date="2026-08-10", supplier_value_12m_gst_inclusive=1000)
    keys = {f["key"] for f in out["figures_used"]}
    assert "shortstay.serr_start_short_term_accommodation" in keys

    server = build()

    async def go():
        return await server.call_tool("serr_report_check", {"income_year": "2026-27",
                                                            "inputs": {"booking_entered_date": "2026-08-10"}})

    assert "2023-07-01" in str(anyio.run(go))


# ------------------------------------------------------------ serr_income_reconciliation (brief Example C)

EX_C = {"platform": "platform A", "guest_payments": 62000, "cancellation_refunds": 520,
        "fees_and_commissions_withheld": 9150, "payout_received": 52330, "gross_reported_by_platform": 61480}


def test_example_c_gross_fees_and_understatement():
    # Guests paid 62,000; 520 refunded for cancellations through the platform: gross = 62,000 - 520 = 61,480.
    # Fees 9,150 are a deduction. Payout = 61,480 - 9,150 = 52,330 (matches what the host received).
    # Host declared the net payout 52,330: understated by 61,480 - 52,330 = 9,150.
    out = ok("serr_income_reconciliation", statements=[EX_C], income_declared=52330)
    assert out["gross_income_to_declare"] == approx(61480)
    assert out["platform_fees_deduction"] == approx(9150)
    assert out["expected_payout"] == approx(52330)
    assert out["payout_difference"] == approx(0)
    assert out["income_understated_by"] == approx(9150)
    assert out["platform_gross_agrees"] is True
    assert out["escalation_code"] == "AU-SS-004"
    assert "short-stay-gross-vs-net-platform-income" in out["risk_flag_ids"]


def test_example_c_declaring_gross_reconciles():
    out = ok("serr_income_reconciliation", statements=[EX_C], income_declared=61480)
    assert out["income_understated_by"] == approx(0)
    assert out["escalation_code"] is None


def test_two_platforms_are_summed():
    # A: 10,000 - 0 gross, fees 1,500. B: 5,000 - 200 = 4,800 gross, fees 600. Gross 14,800, fees 2,100, payout 12,700.
    out = ok("serr_income_reconciliation", income_declared=14800, statements=[
        {"platform": "A", "guest_payments": 10000, "fees_and_commissions_withheld": 1500},
        {"platform": "B", "guest_payments": 5000, "cancellation_refunds": 200, "fees_and_commissions_withheld": 600}])
    assert out["gross_income_to_declare"] == approx(14800)
    assert out["platform_fees_deduction"] == approx(2100)
    assert out["expected_payout"] == approx(12700)
    assert len(out["by_platform"]) == 2


def test_payout_that_does_not_reconcile_is_flagged():
    # 10,000 - 1,500 = 8,500 expected; payout received 8,000: 500 unexplained (held funds, chargebacks or a missing item).
    out = ok("serr_income_reconciliation", statements=[{"guest_payments": 10000, "fees_and_commissions_withheld": 1500,
                                                       "payout_received": 8000}])
    assert out["payout_difference"] == approx(-500)
    assert out["escalation_code"] == "AU-SS-004"


def test_platform_reported_gross_that_differs_is_flagged():
    out = ok("serr_income_reconciliation", statements=[{"guest_payments": 10000, "fees_and_commissions_withheld": 1500,
                                                       "gross_reported_by_platform": 9800}])
    assert out["platform_gross_agrees"] is False and out["escalation_code"] == "AU-SS-004"


def test_over_declared_income_is_reported_not_called_understated():
    out = ok("serr_income_reconciliation", statements=[{"guest_payments": 10000}], income_declared=10500)
    assert out["income_understated_by"] == approx(-500)
    assert any("more than" in w for w in out["warnings"])


# ------------------------------------------------------------ catalogue checks

def test_every_emitted_risk_flag_and_refusal_code_exists_in_the_data_files():
    from pathlib import Path

    import yaml

    root = Path(__file__).resolve().parents[2] / "data"
    # Only the files this skill draws flags from (data/risk_flags/trusts-partnerships.yaml has unquoted brackets and does not parse).
    flags = {f["id"] for n in ("short-stay-accommodation", "rental-property", "gst")
             for f in yaml.safe_load((root / "risk_flags" / f"{n}.yaml").read_text())["risk_flags"]}
    outs = [
        ok("short_stay_apportionment", holiday_home_mainly_for_rent="yes", **EX_A),
        ok("short_stay_apportionment", days_owned=365, nights_rented=60, nights_blocked_unused=305,
           holiday_home_mainly_for_rent="no", ownership_costs=[{"amount": 1}]),
        ok("short_stay_apportionment", days_owned=365, nights_rented=128, nights_available_commercial_terms=237, part_of_home=True,
           area_exclusive_to_tenant=14, area_shared_common=46, area_total=120, ownership_percent=50),
        ok("gst_short_stay_classification", premises_kind="house", asked_must_register_because_of_platform_income=True),
        ok("div87_stay_gst", crp_confirmed=True, nights=40, nightly_price_gst_inclusive=330, bookings_total_12m=10,
           bookings_28_nights_or_more_12m=1),
        ok("serr_report_check", booking_entered_date="2026-08-10"),
        ok("serr_income_reconciliation", statements=[EX_C], income_declared=1),
    ]
    for o in outs:
        assert set(o["risk_flag_ids"]) <= flags, set(o["risk_flag_ids"]) - flags
    codes = {r["code"] for p in (root / "refusals").glob("*.yaml") for r in yaml.safe_load(p.read_text())["refusals"]}
    assert {"AU-SS-001", "AU-SS-002", "AU-SS-003", "AU-SS-004"} <= codes
