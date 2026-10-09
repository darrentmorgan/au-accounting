"""payg_lodgment calculators. Expected values come from ATO worked examples (cited) or hand computation
shown step by step. None were produced by running the calculators."""

import pytest

from au_tax.registry import load_all, run


def call(name, year, **kw):
    code, out = run(name, year, kw)
    assert code == 0, out
    return out


def refused(name, year, **kw):
    code, out = run(name, year, kw)
    assert code == 3, out
    return out["refusal"]["code"]


def approx(x):
    return pytest.approx(x, abs=0.01)


def test_registered_as_tools():
    tools = load_all()
    for n in ("payg_entry_check", "payg_instalment", "payg_variation_check", "lodgment_due_dates",
              "failure_to_lodge_penalty", "general_interest_charge"):
        assert n in tools


# ---------------------------------------------------------------- entry thresholds (ATO 'Starting PAYG instalments')

def test_individual_entry_all_three_at_minimum():
    # ATO: instalment income >= 4,000 AND tax payable >= 1,000 AND notional tax >= 500. All equal the minimum -> in.
    out = call("payg_entry_check", "2026-27", entity_type="individual", instalment_income=4000,
               tax_payable_on_assessment=1000, notional_tax=500)
    assert out["automatic_entry"] is True


@pytest.mark.parametrize("inc,tax,notional", [(3999, 1000, 500), (4000, 999, 500), (4000, 1000, 499)])
def test_individual_entry_fails_if_any_one_test_fails(inc, tax, notional):
    out = call("payg_entry_check", "2026-27", entity_type="individual", instalment_income=inc,
               tax_payable_on_assessment=tax, notional_tax=notional)
    assert out["automatic_entry"] is False


def test_company_entry_any_one_test():
    # ATO: company enters if ANY of instalment income >= 2,000,000, notional tax >= 500, head company.
    assert call("payg_entry_check", "2026-27", entity_type="company", instalment_income=2_000_000)["automatic_entry"]
    assert call("payg_entry_check", "2026-27", entity_type="company", instalment_income=100, notional_tax=500)["automatic_entry"]
    assert call("payg_entry_check", "2026-27", entity_type="company", instalment_income=100,
                is_consolidated_head_company=True)["automatic_entry"]
    assert not call("payg_entry_check", "2026-27", entity_type="company", instalment_income=1_999_999,
                    notional_tax=499)["automatic_entry"]


# ---------------------------------------------------------------- instalment amount

def test_amount_quarterly_2026_27():
    # GDP adjustment 2026-27 is 5%. Notional tax 10,000 x 1.05 = 10,500; / 4 = 2,625.
    out = call("payg_instalment", "2026-27", method="amount", notional_tax=10000)
    assert out["instalment_amount"] == approx(2625)
    assert out["labels"]["T7"] == approx(2625)
    assert out["gdp_adjustment_applied"] == 0.05


def test_amount_quarterly_2025_26():
    # GDP adjustment 2025-26 is 4%. 10,000 x 1.04 = 10,400; / 4 = 2,600.
    out = call("payg_instalment", "2025-26", method="amount", notional_tax=10000)
    assert out["instalment_amount"] == approx(2600)


def test_amount_sap_keeps_prior_year_factor_2026_27():
    # ATO software developers page: SAP year starting 1 Jan/1 Feb/1 Mar 2026 keeps the 4% factor.
    # 10,000 x 1.04 = 10,400; / 4 = 2,600.
    out = call("payg_instalment", "2026-27", method="amount", notional_tax=10000, sap_income_year_start="2026-02-01")
    assert out["instalment_amount"] == approx(2600)
    assert any(f["key"].startswith("payg_instalments.gdp_adjustment@2025-26") for f in out["figures_used"])


def test_amount_sap_from_april_uses_current_factor():
    # Income year commencing from 1 April 2026 gets the 5% adjustment: 10,000 x 1.05 / 4 = 2,625.
    out = call("payg_instalment", "2026-27", method="amount", notional_tax=10000, sap_income_year_start="2026-04-01")
    assert out["instalment_amount"] == approx(2625)


def test_amount_annual_no_gdp_adjustment():
    # ATO: GDP adjustment does not affect annual payers. Annual instalment = notional tax 7,999 (< 8,000 limit).
    out = call("payg_instalment", "2026-27", method="amount", frequency="annual", notional_tax=7999)
    assert out["instalment_amount"] == approx(7999)
    assert out["annual_option_eligible_on_notional_tax"] is True
    assert call("payg_instalment", "2026-27", method="amount", frequency="annual",
                notional_tax=8000)["annual_option_eligible_on_notional_tax"] is False


def test_amount_two_instalments():
    # Yearly = 10,000 x 1.05 = 10,500. April = 75% = 7,875. July = the remaining 25% = 2,625.
    q3 = call("payg_instalment", "2026-27", method="amount", frequency="two_instalments", quarter=3, notional_tax=10000)
    q4 = call("payg_instalment", "2026-27", method="amount", frequency="two_instalments", quarter=4, notional_tax=10000)
    assert q3["instalment_amount"] == approx(7875)
    assert q4["instalment_amount"] == approx(2625)


# ---------------------------------------------------------------- instalment rate (ATO worked examples)

def test_rate_ato_julie_co():
    # ATO example: T1 106,000 x T2 11% = 11,660.
    out = call("payg_instalment", "2026-27", method="rate", entity_type="company",
               instalment_income=106000, instalment_rate_percent=11)
    assert out["instalment_amount"] == approx(11660)
    assert out["labels"]["T11"] == approx(11660)


def test_rate_ato_sophia_whole_dollars():
    # ATO example: 20,100 x 1.7% = 341.70; the ATO enters 341 at T11 and 5A.
    out = call("payg_instalment", "2026-27", method="rate", instalment_income=20100, instalment_rate_percent=1.7)
    assert out["instalment_amount"] == approx(341.70)
    assert out["instalment_amount_whole_dollars"] == 341


def test_rate_above_reasonable_rate_warns():
    # Reasonable rate for individuals is 55%: a 60% rate is above it.
    out = call("payg_instalment", "2026-27", method="rate", instalment_income=1000, instalment_rate_percent=60)
    assert out["reasonable_rate_percent"] == approx(55)
    assert any("reasonable" in w for w in out["warnings"])


# ---------------------------------------------------------------- varying (ATO worked examples)

def test_varied_amount_ato_cari_q3():
    # ATO example 1: estimated tax 14,000 x 75% = 10,500, minus (5,000 + 5,000) paid = 500.
    out = call("payg_instalment", "2025-26", method="varied_amount", quarter=3, estimated_tax=14000,
               earlier_instalments_paid=10000)
    assert out["labels"]["T9"] == approx(500)


def test_varied_amount_ato_cari_q4():
    # 14,000 x 100% = 14,000 minus (5,000 + 5,000 + 500) = 3,500.
    out = call("payg_instalment", "2025-26", method="varied_amount", quarter=4, estimated_tax=14000,
               earlier_instalments_paid=10500)
    assert out["labels"]["T9"] == approx(3500)


def test_varied_amount_credit_when_negative():
    # Estimated tax 6,000 x 75% = 4,500 minus 10,000 paid = -5,500: T9 nil, credit 5,500 at 5B.
    out = call("payg_instalment", "2025-26", method="varied_amount", quarter=3, estimated_tax=6000,
               earlier_instalments_paid=10000)
    assert out["labels"]["T9"] == 0
    assert out["credit_available_5B"] == approx(5500)


def test_varied_amount_adds_back_credits_claimed():
    # ATO: quarter 3 = 75% of estimate minus earlier instalments PLUS credits claimed. 8,000 x 0.75 = 6,000;
    # 6,000 - 5,000 + 1,000 = 2,000.
    out = call("payg_instalment", "2025-26", method="varied_amount", quarter=3, estimated_tax=8000,
               earlier_instalments_paid=5000, credits_claimed_earlier=1000)
    assert out["labels"]["T9"] == approx(2000)


def test_varied_rate_ato_harmander():
    # ATO example 2: 10,125 / 82,480 = 0.122757 -> ATO shows 12.27%.
    out = call("payg_instalment", "2025-26", method="varied_rate", estimated_tax=10125, instalment_income=82480)
    assert out["varied_rate_percent"] == approx(12.27)


# ---------------------------------------------------------------- due dates

def test_instalment_due_dates_2026_27():
    # 28th of the month after the quarter; Q2 = 28 Feb 2027 which is a Sunday, then Mon 1 Mar 2027 is Labour Day (WA), a
    # public holiday for the whole of a State -> Tue 2 Mar 2027 (ATO, Lodgment and payment dates on weekends or public
    # holidays, 1 Mar 2027 row; TAA 1953 s 8AAZMB). Before holiday wiring this test expected 1 Mar 2027 (weekend-only roll).
    q = {n: call("payg_instalment", "2026-27", method="amount", notional_tax=1000, quarter=n)["due_date"] for n in (1, 2, 3, 4)}
    assert q == {1: "2026-10-28", 2: "2027-03-02", 3: "2027-04-28", 4: "2027-07-28"}


def test_bas_q2_no_online_concession():
    out = call("lodgment_due_dates", "2026-27", obligation="bas_quarter", quarter=2, lodges_online_themselves=True)
    # 28 Feb 2027 is a Sunday and Mon 1 Mar 2027 is Labour Day (WA): Tue 2 Mar 2027 (ATO table; TAA 1953 s 8AAZMB).
    assert out["due_date"] == "2027-03-02"
    assert out["statutory_due_date"] == "2027-02-28"
    assert out["business_day_roll"]["rolled"] is True and "Labour Day" in out["business_day_roll"]["reason"]
    assert out["concession_applies"] is False


@pytest.mark.parametrize("q,expected", [(1, "2026-11-11"), (3, "2027-05-12"), (4, "2027-08-11")])
def test_bas_online_concession_two_weeks(q, expected):
    # Statutory 28 Oct 2026 / 28 Apr 2027 / 28 Jul 2027 (all Wednesdays) + 14 days.
    out = call("lodgment_due_dates", "2026-27", obligation="bas_quarter", quarter=q, lodges_online_themselves=True)
    assert out["due_date_with_online_concession"] == expected


def test_individual_return_2025_26_weekend_roll():
    # 31 Oct 2026 is a Saturday -> next business day Monday 2 Nov 2026 (ATO: next business day).
    out = call("lodgment_due_dates", "2025-26", obligation="individual_return_self_lodged")
    assert out["statutory_due_date"] == "2026-10-31"
    assert out["due_date"] == "2026-11-02"
    # Payment date 21 Nov 2026 is a Saturday: a tax debt due on a non-business day is due on the first business day after
    # (TAA 1953 s 8AAZMB(1)) -> Mon 23 Nov 2026. The statutory date stays visible.
    assert out["payment_due_statutory"] == "2026-11-21"
    assert out["payment_due_if_lodged_by_due_date"] == "2026-11-23"


def test_tpar_and_stp_dates():
    assert call("lodgment_due_dates", "2025-26", obligation="tpar")["due_date"] == "2026-08-28"  # Friday
    assert call("lodgment_due_dates", "2026-27", obligation="tpar")["due_date"] == "2027-08-30"  # 28 Aug 2027 is Saturday
    assert call("lodgment_due_dates", "2025-26", obligation="stp_finalisation")["due_date"] == "2026-07-14"  # Tuesday


# ---------------------------------------------------------------- failure to lodge penalty

@pytest.mark.parametrize("days,periods", [(0, 0), (1, 1), (28, 1), (29, 2), (56, 2), (57, 3), (112, 4), (113, 5), (400, 5)])
def test_ftl_periods_small_2026_27(days, periods):
    # 1 base unit per 28 days or part, max 5 units. Penalty unit from 1 Jul 2026 = 364.
    out = call("failure_to_lodge_penalty", "2026-27", days_late=days, due_date="2026-10-28")
    assert out["base_units"] == periods
    assert out["penalty"] == approx(periods * 364)


def test_ftl_60_days_small():
    # 60 days = 3 periods (1-28, 29-56, 57-84) = 3 units x 364 = 1,092.
    assert call("failure_to_lodge_penalty", "2026-27", days_late=60, due_date="2026-07-28")["penalty"] == approx(1092)


def test_ftl_multipliers_at_cap():
    # 200 days: capped at 5 base units. Medium x2 = 10 units x 364 = 3,640. Large x5 = 25 units = 9,100.
    # SGE x500 = 2,500 units x 364 = 910,000.
    d = dict(days_late=200, due_date="2026-10-28")
    assert call("failure_to_lodge_penalty", "2026-27", entity_size="medium", **d)["penalty"] == approx(3640)
    assert call("failure_to_lodge_penalty", "2026-27", entity_size="large", **d)["penalty"] == approx(9100)
    assert call("failure_to_lodge_penalty", "2026-27", entity_size="sge", **d)["penalty"] == approx(910000)


def test_ftl_unit_set_by_due_date_not_lodgment_date():
    # Due 30 Jun 2026 (unit 330), lodged 60 days later after the 1 Jul 2026 increase: 3 x 330 = 990.
    out = call("failure_to_lodge_penalty", "2026-27", days_late=60, due_date="2026-06-30")
    assert out["penalty_unit_amount"] == 330
    assert out["penalty"] == approx(990)
    # Due 1 Jul 2026: 3 x 364 = 1,092.
    assert call("failure_to_lodge_penalty", "2026-27", days_late=60, due_date="2026-07-01")["penalty"] == approx(1092)


def test_ftl_year_file_choice_2025_26_envelope():
    # Same rule when the envelope year is 2025-26 but the due date is in 2026-27: 364.
    assert call("failure_to_lodge_penalty", "2025-26", days_late=1, due_date="2026-08-28")["penalty"] == approx(364)


def test_ftl_before_loaded_period_refuses():
    assert refused("failure_to_lodge_penalty", "2025-26", days_late=10, due_date="2025-06-30") == "AU-PAYG-002"


def test_ftl_refund_and_safe_harbour_warnings():
    out = call("failure_to_lodge_penalty", "2026-27", days_late=10, due_date="2026-10-28",
               lodgment_result="refund_or_nil", agent_safe_harbour_possible=True)
    text = " ".join(out["warnings"])
    assert "refund or nil" in text and "Safe harbour" in text


# ---------------------------------------------------------------- general interest charge

def test_gic_single_quarter():
    # Jul-Sep 2026 daily rate 0.0003131507. 10,000 for 10 days (1 Jul to 10 Jul inclusive; paid 11 Jul):
    # 10,000 x ((1.0003131507)^10 - 1). Binomial: 10r = 3.131507e-3; 45 r^2 = 4.4128e-6; 120 r^3 = 3.7e-9
    # -> 3.135924e-3 x 10,000 = 31.359 -> 31.36.
    out = call("general_interest_charge", "2026-27", amount=10000, from_date="2026-07-01", to_date="2026-07-11")
    assert out["days"] == 10
    assert out["interest"] == approx(31.36)


def test_gic_across_quarter_boundary():
    # 5,000 from 20 Sep 2026 (11 days: 20-30 Sep at 0.0003131507) then 1-9 Oct (9 days at 0.0003153425), paid 10 Oct.
    # 5,000 x (1.0003131507^11 x 1.0003153425^9 - 1) = 5,000 x 0.0063015 = 31.51 (hand, 40-digit decimal check).
    out = call("general_interest_charge", "2026-27", amount=5000, from_date="2026-09-20", to_date="2026-10-10")
    assert out["days"] == 20
    assert out["interest"] == approx(31.51)
    assert [b["days"] for b in out["breakdown"]] == [11, 9]


def test_gic_across_income_year_boundary():
    # 8,000 from 20 Jun 2026 to 9 Jul 2026 inclusive of days 20 Jun-30 Jun (11 days at Apr-Jun 2026 0.000300274)
    # and 1-9 Jul (9 days at 0.0003131507): 8,000 x (1.000300274^11 x 1.0003131507^9 - 1) = 49.11.
    out = call("general_interest_charge", "2026-27", amount=8000, from_date="2026-06-20", to_date="2026-07-10")
    assert out["interest"] == approx(49.11)


def test_gic_zero_days():
    out = call("general_interest_charge", "2026-27", amount=1000, from_date="2026-08-01", to_date="2026-08-01")
    assert out["interest"] == 0


def test_gic_refuses_unpublished_quarter():
    # Jan-Mar 2027 GIC rate is null (not yet published).
    assert refused("general_interest_charge", "2026-27", amount=1000, from_date="2026-12-20", to_date="2027-01-10") == "AU-PAYG-002"


def test_gic_refuses_before_loaded_period():
    assert refused("general_interest_charge", "2026-27", amount=1000, from_date="2025-06-20", to_date="2025-07-10") == "AU-PAYG-002"


def test_sic_uses_sic_rates():
    # SIC Jul-Sep 2026 daily 0.0002035616: 10,000 x ((1.0002035616)^10 - 1) = 20.37 (hand: 10r=2.035616e-3,
    # 45r^2=1.8646e-6, 120r^3=1.0e-9 -> 2.037482e-3 x 10,000).
    out = call("general_interest_charge", "2026-27", charge="sic", amount=10000, from_date="2026-07-01", to_date="2026-07-11")
    assert out["interest"] == approx(20.37)


# ---------------------------------------------------------------- variation check

def test_variation_ato_cari_passes():
    # ATO example: benchmark (actual) tax 15,500; estimate 14,000 = 90.3% of benchmark; instalments paid 14,000.
    # 85% of 15,500 = 13,175 <= 14,000 -> safe harbour met; no GIC; shortfall at assessment 1,500.
    out = call("payg_variation_check", "2025-26", benchmark_tax=15500, estimated_tax=14000,
               instalments_paid=[5000, 5000, 500, 3500])
    assert out["estimated_tax_meets_safe_harbour"] is True
    assert out["instalments_paid_meet_safe_harbour"] is True
    assert out["gic_applies"] is False
    assert out["tax_shortfall_at_assessment"] == approx(1500)
    assert out["safe_harbour_amount"] == approx(13175)


def test_variation_fails_estimate_below_85_percent():
    # Benchmark 20,000; 85% = 17,000. Estimate 10,000 < 17,000 -> fails. Instalments 2,500 + 3 x 5,000 = 17,500
    # is above 17,000 but the estimate test alone triggers GIC (s 45-232).
    out = call("payg_variation_check", "2025-26", benchmark_tax=20000, estimated_tax=10000,
               instalments_paid=[2500, 5000, 5000, 5000])
    assert out["estimated_tax_meets_safe_harbour"] is False
    assert out["gic_applies"] is True
    # Acceptable instalment per quarter = 20,000 / 4 = 5,000; only Q1 is short: 5,000 - 2,500 = 2,500.
    assert [q["shortfall"] for q in out["quarter_shortfalls"]] == [2500, 0, 0, 0]


def test_variation_indicative_gic():
    # Q1 2025-26 due 28 Oct 2025; assessment due 27 Nov 2025: 30 days at Oct-Dec 2025 daily 0.0002906849.
    # 2,500 x ((1.0002906849)^30 - 1) = 2,500 x 0.0087574 = 21.89.
    out = call("payg_variation_check", "2025-26", benchmark_tax=20000, estimated_tax=10000,
               instalments_paid=[2500, 5000, 5000, 5000], assessment_due_date="2025-11-27")
    assert out["indicative_gic"] == approx(21.89)


def test_variation_rate_method_boundary():
    # Benchmark rate 10% x 85% = 8.5%. Varied 8.5% meets it; 8.49% does not.
    ok = call("payg_variation_check", "2026-27", method="rate", varied_rate_percent=8.5, benchmark_rate_percent=10)
    bad = call("payg_variation_check", "2026-27", method="rate", varied_rate_percent=8.49, benchmark_rate_percent=10)
    assert ok["meets_safe_harbour"] is True and bad["meets_safe_harbour"] is False


# ---------------------------------------------------------------- refusals and validation

@pytest.mark.parametrize("special", ["consolidated_head_company", "monthly_instalment_payer", "gst_instalment_combined",
                                     "substituted_accounting_period_nonstandard_quarters", "dynamic_accounting_software_method"])
def test_specials_refuse(special):
    assert refused("payg_instalment", "2026-27", method="amount", notional_tax=1000,
                   special_circumstances=[special]) == "AU-PAYG-001"


def test_missing_inputs_invalid():
    code, _ = run("payg_instalment", "2026-27", {"method": "amount"})
    assert code == 2
    code, _ = run("lodgment_due_dates", "2026-27", {"obligation": "bas_quarter"})
    assert code == 2


def test_unknown_year_is_general_refusal():
    code, out = run("general_interest_charge", "2030-31", {"amount": 1, "from_date": "2030-08-01", "to_date": "2030-08-05"})
    assert code == 4 and out["refusal"]["code"] == "AU-GEN-003"


def test_figures_used_reported():
    out = call("failure_to_lodge_penalty", "2026-27", days_late=10, due_date="2026-10-28")
    keys = {f["key"] for f in out["figures_used"]}
    assert "penalties_interest.penalty_unit" in keys
    assert out["draft"] is False


# ---------------------------------------------------------------- due dates: public holidays (TAA 1953 s 8AAZMB, Sch 1 s 388-52)

def test_bas_q2_2026_27_rolls_over_labour_day_wa():
    # ATO table: Mon 1 Mar 2027 (Labour Day, WA) -> Tue 2 Mar 2027. 28 Feb 2027 is a Sunday.
    out = call("lodgment_due_dates", "2026-27", obligation="bas_quarter", quarter=2)
    assert out["due_date"] == "2027-03-02"
    assert out["business_day_roll"]["regime"] == "commonwealth_tax"
    assert "Sunday" in out["business_day_roll"]["reason"]


def test_individual_return_2026_27_lodgment_and_payment_dates():
    # 31 Oct 2027 is a Sunday -> Mon 1 Nov 2027 (no holiday; Melbourne Cup is Tue 2 Nov 2027, not reached).
    # Payment 21 Nov 2027 is a Sunday -> Mon 22 Nov 2027.
    out = call("lodgment_due_dates", "2026-27", obligation="individual_return_self_lodged")
    assert out["due_date"] == "2027-11-01" and out["payment_due_if_lodged_by_due_date"] == "2027-11-22"


def test_roll_reports_rule_source_in_figures_used():
    out = call("lodgment_due_dates", "2026-27", obligation="tpar")
    used = {f["key"]: f for f in out["figures_used"]}
    assert used["holidays.commonwealth_tax"]["status"] == "VERIFIED"
    assert out["draft"] is False



# ------------------------------------------------------------------ due dates after the holiday data (AU-GEN-004)

def test_lodgment_due_dates_after_the_holiday_data_refuse_and_name_the_unrolled_date():
    # 2027-28: TPAR is 28 Aug 2028, STP finalisation 14 Jul 2028, the self-lodged return 31 Oct 2028, Q4 28 Jul 2028: all after
    # 30 Jun 2028, the end of the holiday data. The date is the result, so each refuses rather than returning an unchecked date.
    for kw in ({"obligation": "tpar"}, {"obligation": "stp_finalisation"}, {"obligation": "individual_return_self_lodged"},
               {"obligation": "bas_quarter", "quarter": 4}, {"obligation": "payg_instalment_quarter", "quarter": 4}):
        code, out = run("lodgment_due_dates", "2027-28", kw)
        assert code == 3 and out["refusal"]["code"] == "AU-GEN-004", kw
        assert out["refusal"]["detail"].startswith("2028-"), kw   # the date that is outside the data


def test_lodgment_due_dates_2027_28_quarter_3_is_inside_the_data():
    # Q3: 28 Apr 2028 is a Friday (see the BAS test); no roll.
    out = call("lodgment_due_dates", "2027-28", obligation="payg_instalment_quarter", quarter=3)
    assert out["statutory_due_date"] == out["due_date"] == "2028-04-28"


def test_payg_instalment_2027_28_quarter_4_still_gives_the_amount_when_the_date_is_after_the_holiday_data():
    # The instalment amount is the result; the Q4 date (28 Jul 2028, after the holiday data) is secondary, so it comes back
    # unrolled with a field refusal rather than refusing the amount. Q3 (28 Apr 2028, a Friday) is inside the data.
    # Rate method: instalment = instalment income x rate = 20,000 x 11% = 2,200.00.
    q4 = call("payg_instalment", "2027-28", method="rate", instalment_income=20000, instalment_rate_percent=11, quarter=4)
    assert q4["instalment_amount"] == 2200.0
    assert q4["due_date"] == q4["due_date_statutory"] == "2028-07-28" and q4["business_day_roll"]["rolled"] is False
    assert [f["code"] for f in q4["field_refusals"]] == ["AU-GEN-004"] and q4["field_refusals"][0]["field"] == "due_date"
    q3 = call("payg_instalment", "2027-28", method="rate", instalment_income=20000, instalment_rate_percent=11, quarter=3)
    assert q3["due_date"] == "2028-04-28" and "field_refusals" not in q3
    assert q3["instalment_amount"] == q4["instalment_amount"]


def test_self_lodged_payment_rule_distinguishes_late_return():
    # ATO Preparing your tax return, Due dates / If you miss the due date (read 9 Oct 2026):
    # on-time return: later assessment can move payment; late return: November date still applies.
    out = call("lodgment_due_dates", "2025-26", obligation="individual_return_self_lodged")
    assert any("lodged on time" in w and "assessment" in w for w in out["warnings"])
    assert any("late" in w and "does not" in w for w in out["warnings"])
