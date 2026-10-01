"""payroll-sg calculators. Expected values come from ATO sample data and worked examples (cited), LCR 2026/3
worked examples, or hand computation shown step by step. None were produced by running the calculator."""

from datetime import date

import pytest

from au_tax.calculators.payroll import SgcInput, _sgc_payday, business_days_after
from au_tax.figures import Figures
from au_tax.registry import load_all, run


def calc(name, year, **kw):
    code, out = run(name, year, kw)
    assert code == 0, out
    return out


def refused(name, year, **kw):
    code, out = run(name, year, kw)
    assert code == 3, out
    return out["refusal"]["code"]


def test_registered():
    assert {"payg_withholding", "no_abn_withholding", "super_guarantee", "sg_charge_estimate",
            "worker_status_indicators"} <= set(load_all())


# ---------------------------------------------------------------- PAYG 2026-27: ATO Schedule 1 sample data
# Source: ato.gov.au .../payg-withholding-schedule-1-.../sample-data/withholding-amounts-sample-data (17 Jun 2026)
# Columns: earnings, scale 1, scale 2, scale 3, scale 5, scale 6.
W26 = [
    (116, 17, 0, 35, 0, 0), (187, 28, 0, 56, 0, 0), (362, 65, 0, 109, 0, 0), (370, 66, 1, 111, 1, 1),
    (538, 100, 27, 161, 27, 27), (672, 143, 60, 202, 47, 47), (907, 219, 108, 272, 90, 90),
    (931, 227, 116, 279, 97, 98), (1134, 292, 181, 340, 158, 170), (1135, 292, 181, 340, 159, 170),
    (1845, 519, 409, 553, 372, 391), (2246, 647, 537, 674, 492, 515), (2491, 743, 616, 747, 566, 591),
    (3303, 1060, 925, 1041, 859, 892), (3653, 1224, 1062, 1170, 989, 1025),
]
F26 = [
    (232, 34, 0, 70, 0, 0), (740, 132, 2, 222, 2, 2), (1076, 200, 54, 322, 54, 54), (1862, 454, 232, 558, 194, 196),
    (2270, 584, 362, 680, 318, 340), (4240, 1214, 994, 1272, 910, 952), (7306, 2448, 2124, 2340, 1978, 2050),
]
M26 = [
    (502.67, 74, 0, 152, 0, 0), (1083.33, 178, 0, 325, 0, 0), (1603.33, 286, 4, 481, 4, 4),
    (2331.33, 433, 117, 698, 117, 117), (4038.67, 984, 503, 1213, 420, 425), (9186.67, 2630, 2154, 2756, 1972, 2063),
    (15829.67, 5304, 4602, 5070, 4286, 4442),
]
# 2025-26: NAT 1004 dated 1 Jul 2024 (applies 1 Jul 2025 to 30 Jun 2026 per ATO 'Tax tables for 2025-26'), sample data.
W25 = [
    (116, 19, 0, 35, 0, 0), (370, 71, 2, 111, 2, 2), (625, 134, 55, 187, 42, 42), (864, 211, 99, 259, 82, 83),
    (1053, 272, 160, 316, 139, 150), (2596, 790, 655, 779, 603, 629), (3653, 1230, 1067, 1170, 994, 1030),
]
F25 = [(1250, 268, 110, 374, 84, 84), (5192, 1580, 1310, 1558, 1206, 1258)]
M25 = [(1083.33, 195, 0, 325, 0, 0), (2708.33, 581, 238, 810, 182, 182), (11249.33, 3423, 2838, 3376, 2613, 2726)]

SCALES = [  # (column index, kwargs)
    (1, {"tax_free_threshold_claimed": False}),
    (2, {}),
    (3, {"residency": "foreign"}),
    (4, {"medicare_exemption": "full"}),
    (5, {"medicare_exemption": "half"}),
]


def _cases(rows, period, year):
    return [(year, period, r[0], r[i], kw) for r in rows for i, kw in SCALES]


@pytest.mark.parametrize("year,period,gross,expected,kw",
                         _cases(W26, "weekly", "2026-27") + _cases(F26, "fortnightly", "2026-27")
                         + _cases(M26, "monthly", "2026-27") + _cases(W25, "weekly", "2025-26")
                         + _cases(F25, "fortnightly", "2025-26") + _cases(M25, "monthly", "2025-26"))
def test_ato_sample_data(year, period, gross, expected, kw):
    out = calc("payg_withholding", year, gross_earnings=gross, period=period, **kw)
    assert out["total_withholding"] == expected


def test_prue_scale5_offsets_2026():
    # ATO 'Examples of calculating the withholding amounts' (2026): fortnightly 1,299.30, scale 5, offsets 1,645.
    # x = 649.99; y = 0.15 x 649.99 - 54.3462 = 43.15 -> 43; x2 = 86; offsets 3.8% x 1,645 = 62.51 -> 63; net 23.
    out = calc("payg_withholding", "2026-27", gross_earnings=1299.30, period="fortnightly",
               medicare_exemption="full", withholding_declaration_offsets=1645)
    assert (out["withholding_before_offsets"], out["offsets_reduction"], out["total_withholding"]) == (86, 63, 23)


def test_tan_monthly_offsets_2026():
    # ATO example (2026): monthly 5,400.33 (+1c because it ends in 33c) x 3 / 13 = 1,246.23 -> x = 1,246.99
    # y = 0.3227 x 1,246.99 - 185.1935 = 217.21 -> 217; x 13 / 3 = 940.33 -> 940; offsets 8.3% x 1,365 = 113.30 -> 113; 827.
    out = calc("payg_withholding", "2026-27", gross_earnings=5400.33, period="monthly", withholding_declaration_offsets=1365)
    assert (out["withholding_before_offsets"], out["total_withholding"]) == (940, 827)


def test_prue_and_tan_2025():
    # NAT 1004 (1 Jul 2024) examples: Prue 92 - 63 = 29; Tan 962 - 113 = 849.
    assert calc("payg_withholding", "2025-26", gross_earnings=1299.30, period="fortnightly", medicare_exemption="full",
                withholding_declaration_offsets=1645)["total_withholding"] == 29
    assert calc("payg_withholding", "2025-26", gross_earnings=5400.33, period="monthly",
                withholding_declaration_offsets=1365)["total_withholding"] == 849


def test_quarterly_conversion():
    # Hand: quarterly 13,000 -> weekly 13,000 / 13 = 1,000 -> x = 1,000.99 (2026-27 scale 2 row 865-1,282)
    # y = 0.3227 x 1,000.99 - 185.1935 = 323.0195 - 185.1935 = 137.826 -> 138; x 13 = 1,794.
    assert calc("payg_withholding", "2026-27", gross_earnings=13000, period="quarterly")["total_withholding"] == 1794


def test_offsets_ignored_on_scale1():
    out = calc("payg_withholding", "2026-27", gross_earnings=1134, period="weekly", tax_free_threshold_claimed=False,
               withholding_declaration_offsets=1000)
    assert out["total_withholding"] == 292 and out["offsets_reduction"] == 0


def test_no_tfn_scale4():
    # Scale 4 resident 47%: 1,500.80 -> cents ignored -> 0.47 x 1,500 = 705. Foreign 45%: 0.45 x 1,500 = 675.
    assert calc("payg_withholding", "2026-27", gross_earnings=1500.80, period="weekly", tfn_provided=False)["total_withholding"] == 705
    assert calc("payg_withholding", "2026-27", gross_earnings=1500, period="weekly", tfn_provided=False,
                residency="foreign")["total_withholding"] == 675
    # 0.47 x 1,333 = 626.51 -> cents ignored -> 626
    assert calc("payg_withholding", "2025-26", gross_earnings=1333, period="fortnightly", tfn_provided=False)["total_withholding"] == 626


# ---------------------------------------------------------------- Schedule 8 study loan component

def test_stsl_ato_examples_2026():
    # Schedule 8 (1 Jul 2026) example 1: weekly 2,608.36 TFT: 0.17 x 2,608.99 - 250.4527 = 193.08 -> 193.
    out = calc("payg_withholding", "2026-27", gross_earnings=2608.36, period="weekly", study_loan_debt=True)
    assert out["stsl_component"] == 193
    # Schedule 1 part: 0.32 x 2,608.99 - 181.7319 = 653.14 -> 653? No: 2,608.99 >= 2,596 -> a = 0.39, b = 363.4627:
    # 0.39 x 2,608.99 = 1,017.5061 - 363.4627 = 654.04 -> 654. Total 654 + 193 = 847.
    assert out["total_withholding"] == 847
    # Example 2: fortnightly 4,409.75 TFT -> x = 2,204.99; 0.15 x 2,204.99 - 200.5615 = 130.19 -> 130 x 2 = 260.
    assert calc("payg_withholding", "2026-27", gross_earnings=4409.75, period="fortnightly",
                study_loan_debt=True)["stsl_component"] == 260


def test_stsl_example3_no_tft_2026():
    # Example 3: monthly 10,627.88, no TFT: x 3 / 13 = 2,452.59 -> x = 2,452.99 (row 2,144-2,727, 0.17, 190.9527)
    # 0.17 x 2,452.99 = 417.0083 - 190.9527 = 226.0556 -> 226; monthly 226 x 13 / 3 = 979.33 -> 979.
    out = calc("payg_withholding", "2026-27", gross_earnings=10627.88, period="monthly", study_loan_debt=True,
               tax_free_threshold_claimed=False)
    assert out["stsl_component"] == 979


def test_stsl_top_band_whole_income():
    # 2026-27 weekly 4,000 TFT: x = 4,000.99 >= 3,577 -> 10% x 4,000.99 = 400.10 -> 400.
    assert calc("payg_withholding", "2026-27", gross_earnings=4000, period="weekly", study_loan_debt=True)["stsl_component"] == 400


def test_stsl_2025_26_examples_and_date_rule():
    # Schedule 8 (24 Sep 2025 to 30 Jun 2026) example 1: 0.17 x 2,608.99 - 241.3462 = 202.18 -> 202.
    out = calc("payg_withholding", "2025-26", gross_earnings=2608.36, period="weekly", study_loan_debt=True,
               payment_date="2026-03-05")
    assert out["stsl_component"] == 202
    # Example 3: monthly 10,627.88 no TFT: 0.17 x 2,452.99 - 181.8462 = 235.16 -> 235; x 13 / 3 = 1,018.33 -> 1,018.
    out = calc("payg_withholding", "2025-26", gross_earnings=10627.88, period="monthly", study_loan_debt=True,
               tax_free_threshold_claimed=False, payment_date="2026-01-15")
    assert out["stsl_component"] == 1018
    assert refused("payg_withholding", "2025-26", gross_earnings=2608.36, period="weekly", study_loan_debt=True,
                   payment_date="2025-08-01") == "AU-PAY-006"


def test_payg_refusals():
    assert refused("payg_withholding", "2026-27", gross_earnings=900, period="weekly",
                   special_circumstances=["working_holiday_maker"]) == "AU-PAY-006"
    assert refused("payg_withholding", "2026-27", gross_earnings=900, period="weekly",
                   payment_date="2026-06-30") == "AU-PAY-008"


def test_no_abn():
    # 0.47 x 2,000 = 940; at or below 75 ex GST -> nil; ABN quoted -> nil
    assert calc("no_abn_withholding", "2026-27", payment_ex_gst=2000)["withholding"] == 940
    assert calc("no_abn_withholding", "2026-27", payment_ex_gst=75)["withholding"] == 0
    assert calc("no_abn_withholding", "2026-27", payment_ex_gst=2000, abn_quoted=True)["withholding"] == 0
    # 0.47 x 110 (cents ignored from 110.90) = 51.70 -> 51
    assert calc("no_abn_withholding", "2025-26", payment_ex_gst=110.90)["withholding"] == 51


# ---------------------------------------------------------------- business days (ATO / LCR 2026/3 examples)

def test_business_days_ato_examples():
    picnic_2026 = {date(2026, 8, 3)}  # NT Picnic Day, a public holiday for the whole of the NT
    # ATO 'Payment deadlines for Payday Super': Hannah, QE 9 Jul 2026 first contribution -> 7 Aug 2026 (20 bd);
    # QE 30 Jul 2026 -> 11 Aug 2026 (7 bd). Both include the Picnic Day.
    assert business_days_after(date(2026, 7, 9), 20, picnic_2026) == date(2026, 8, 7)
    assert business_days_after(date(2026, 7, 30), 7, picnic_2026) == date(2026, 8, 11)
    # Floyd: QE 7 Aug 2026 new fund -> 4 Sep 2026; QE 4 Sep 2026 -> 15 Sep 2026.
    assert business_days_after(date(2026, 8, 7), 20, set()) == date(2026, 9, 4)
    assert business_days_after(date(2026, 9, 4), 7, set()) == date(2026, 9, 15)
    # LCR 2026/3 Example 11: QE 7 Sep 2028 -> usual period ends 18 Sep 2028 (late period starts 19 Sep).
    assert business_days_after(date(2028, 9, 7), 7, set()) == date(2028, 9, 18)


def test_super_guarantee_payday_hannah():
    out = calc("super_guarantee", "2026-27", payments=[
        {"pay_date": "2026-07-09", "ordinary_time_earnings": 1000},
        {"pay_date": "2026-07-30", "ordinary_time_earnings": 1000}],
        first_contribution_new_employee=True, public_holidays=["2026-08-03"])
    assert [l["due_date"] for l in out["lines"]] == ["2026-08-07", "2026-08-11"]
    assert out["sg_total"] == 240.0  # 12% x 1,000 x 2


def test_super_guarantee_bunching_lcr_example8():
    # LCR 2026/3 Example 8 (2028 dates, same rule): QE 11 Aug 2028 first contribution -> 8 Sep 2028;
    # QE 25 Aug 2028 usual period ends 5 Sep 2028, extended to 8 Sep 2028. Checked via the helper and rule.
    first_end = business_days_after(date(2028, 8, 11), 20, set())
    assert first_end == date(2028, 9, 8)
    assert business_days_after(date(2028, 8, 25), 7, set()) == date(2028, 9, 5)


def test_super_guarantee_qe_components_2026():
    # QE = OTE 3,000 + commission outside ordinary hours 200 + salary sacrificed OTE 300 = 3,500; overtime 400 excluded.
    # SG = 12% x 3,500 = 420. Due: Fri 11 Sep 2026 + 7 bd = Tue 22 Sep 2026.
    out = calc("super_guarantee", "2026-27", payments=[{"pay_date": "2026-09-11", "ordinary_time_earnings": 3000,
               "commissions_outside_ordinary_hours": 200, "salary_sacrificed_ote": 300, "overtime": 400}])
    assert out["lines"][0]["sg_amount"] == 420.0
    assert out["lines"][0]["due_date"] == "2026-09-22"


def test_super_guarantee_annual_mcb_2026():
    # Annual base 270,830. Already paid 265,000; this pay 10,000 -> counted 5,830 -> SG 12% x 5,830 = 699.60.
    out = calc("super_guarantee", "2026-27", ytd_base_before=265000,
               payments=[{"pay_date": "2027-05-14", "ordinary_time_earnings": 10000}])
    assert out["lines"][0]["qualifying_earnings_counted"] == 5830.0
    assert out["sg_total"] == 699.6


def test_super_guarantee_quarterly_2025_26():
    # Q1 2025-26: OTE 70,000 above quarterly base 62,500 -> SG 12% x 62,500 = 7,500 (ATO table: max 7,500.00).
    # Due 28 Oct 2025 (Tue). Q4: OTE 10,000 + sacrificed 1,000 = 11,000 -> 1,320; due 28 Jul 2026 (Tue).
    out = calc("super_guarantee", "2025-26", payments=[
        {"pay_date": "2025-08-15", "ordinary_time_earnings": 70000, "overtime": 5000},
        {"pay_date": "2026-05-15", "ordinary_time_earnings": 10000, "salary_sacrificed_ote": 1000}])
    q = {l["quarter"]: l for l in out["lines"]}
    assert q[1]["sg_amount"] == 7500.0 and q[1]["due_date"] == "2025-10-28"
    assert q[4]["sg_amount"] == 1320.0 and q[4]["due_date"] == "2026-07-28"


def test_super_guarantee_quarter_due_weekend():
    # Q2 2025-26 due 28 Jan 2026 is a Wednesday; Q3 due 28 Apr 2026 is a Tuesday. Use a weekend case:
    # 28 Jan 2023 would be Saturday, but outside the rates; check the rule on Q2 with a public holiday on 28 Jan -> 29 Jan.
    out = calc("super_guarantee", "2025-26", payments=[{"pay_date": "2025-11-14", "ordinary_time_earnings": 1000}],
               public_holidays=["2026-01-28"])
    assert out["lines"][0]["due_date"] == "2026-01-29"


def test_super_guarantee_under_18():
    out = calc("super_guarantee", "2026-27", payments=[{"pay_date": "2026-09-11", "ordinary_time_earnings": 500}],
               employee_under_18_hours_over_30=False)
    assert out["sg_total"] == 0


# ---------------------------------------------------------------- SG charge: Payday Super (LCR 2026/3 Example 16)

def test_sgc_lcr_example16():
    # QE 30 Jul 2027; on-time deadline 11 Aug 2027 (2 Aug 2027 NT Picnic Day); assessment 29 Sep 2027 (late period
    # to 28 Sep); GIC assumed 10%. Ruling: final 1,160; NE 6.75 + 2.40 + 9.93 = 19.08; uplift 40% x 1,179.08 = 471.63;
    # choice loading 25% x 450 = 112.50; SG shortfall 1,763.21; assessed amount 1,763.20 (down to 5 cents).
    inp = SgcInput(qe_day=date(2027, 7, 30), calculation_date=date(2027, 9, 29), assessment_date=date(2027, 9, 29),
                   public_holidays=[date(2027, 8, 2)], gic_annual_rate_override=0.10, employees=[
                       {"name": "Sam", "qualifying_earnings": 3000, "on_time_contributions": 360},
                       {"name": "Nia", "qualifying_earnings": 3750, "on_time_contributions": 450, "non_choice_compliant_contributions": 450},
                       {"name": "William", "qualifying_earnings": 4250},
                       {"name": "Ella", "qualifying_earnings": 5500, "on_time_contributions": 200,
                        "late_contributions": [{"amount": 460, "received": date(2027, 8, 30)}]},
                       {"name": "Kai", "qualifying_earnings": 6250,
                        "late_contributions": [{"amount": 100, "received": date(2027, 8, 30)}]}])
    out = _sgc_payday(Figures("2026-27"), inp, [], [])
    ne = {r["name"]: (r["notional_earnings"], r["notional_earnings_days"]) for r in out["employees"]}
    assert ne["William"] == (6.75, 48) and ne["Ella"] == (2.40, 19) and ne["Kai"] == (9.93, 48)
    assert out["total_individual_final_shortfall"] == 1160.0
    assert out["admin_uplift_rate"] == 0.40 and out["admin_uplift_amount"] == 471.63
    assert out["total_choice_loading"] == 112.50
    assert out["sg_charge"] == 1763.21 and out["sg_charge_as_assessed"] == 1763.20


def test_sgc_vds_within_30_days_nil_uplift():
    # LCR 2026/3 Example 14: VDS lodged within 30 days and clean history -> 60 - 40 - 20 = 0% uplift.
    # QE Fri 11 Sep 2026, QE 2,000 -> SG 240, nothing on time; paid in full, received 25 Sep 2026.
    # On-time deadline: 7 bd after 11 Sep = 22 Sep. Late period starts 23 Sep; ends 25 Sep (cleared) = 3 days.
    # NE = 240 x ((1 + 0.0003131507)^3 - 1) = 240 x 0.000939746 = 0.2255 -> 0.23 (Jul-Sep 2026 GIC daily rate).
    out = calc("sg_charge_estimate", "2026-27", qe_day="2026-09-11", calculation_date="2026-09-28",
               vds_lodged="2026-09-28", employees=[{"qualifying_earnings": 2000,
               "late_contributions": [{"amount": 240, "received": "2026-09-25"}]}])
    assert out["employees"][0]["notional_earnings"] == 0.23 and out["employees"][0]["notional_earnings_days"] == 3
    assert out["admin_uplift_rate"] == 0.0
    assert out["total_individual_final_shortfall"] == 0.0
    assert out["sg_charge"] == 0.23


def test_sgc_default_uplift_with_history():
    # Prior ATO-initiated assessment, no VDS -> 60%. QE 11 Sep 2026, SG 240 unpaid, calculation date 22 Sep 2026
    # (deadline day, so no late days yet): NE 0; uplift 60% x 240 = 144; total 384.
    out = calc("sg_charge_estimate", "2026-27", qe_day="2026-09-11", calculation_date="2026-09-22",
               commissioner_assessment_in_prior_24_months=True, employees=[{"qualifying_earnings": 2000}])
    assert out["admin_uplift_rate"] == 0.60 and out["sg_charge"] == 384.0


def test_sgc_gic_unpublished_refuses():
    # Late period running into Jan 2027 needs the Jan-Mar 2027 GIC rate, not yet published -> AU-GEN-003 (exit 4).
    code, out = run("sg_charge_estimate", "2026-27", {"qe_day": "2026-12-04", "calculation_date": "2027-01-20",
                                                      "employees": [{"qualifying_earnings": 2000}]})
    assert code == 4 and out["refusal"]["code"] == "AU-GEN-003"


def test_sgc_choice_loading_limit():
    # LCR 2026/3 Example 15 logic: 25% x 240 = 60, limit 1,200 less prior 1,180 = 20 -> choice loading 20.
    out = calc("sg_charge_estimate", "2026-27", qe_day="2026-10-02", calculation_date="2026-10-05",
               employees=[{"qualifying_earnings": 2000, "on_time_contributions": 240,
                           "non_choice_compliant_contributions": 240, "prior_choice_loadings_in_notice_period": 1180}])
    assert out["total_choice_loading"] == 20.0 and out["admin_uplift_amount"] == 0.0


# ---------------------------------------------------------------- SG charge: quarterly regime (ATO Module 6, Imogen)

def test_sgc_quarterly_imogen():
    # 30 employees x salary or wages 12,000 (incl. overtime) = 360,000 x 12% = 43,200. Lodged 20 Nov 2025; due 28 Nov 2025
    # (later) -> 150 days from 1 Jul 2025. NI = 43,200 / 365 x 150 x 10% = 1,775.34. Admin 30 x 20 = 600. SGC 45,575.34.
    # Late payment offset 36,000 -> payable 9,575.34.
    out = calc("sg_charge_estimate", "2025-26", quarter_end="2025-09-30", calculation_date="2025-11-20",
               late_payments_elected_offset=36000,
               employees=[{"name": f"e{i}", "qualifying_earnings": 12000} for i in range(30)])
    assert out["total_sg_shortfall"] == 43200.0 and out["nominal_interest_days"] == 150
    assert out["nominal_interest"] == 1775.34 and out["administration_fee"] == 600.0
    assert out["sg_charge"] == 45575.34 and out["sgc_payable_after_offset"] == 9575.34
    assert out["deductible"] is False


def test_sgc_quarterly_june_2026_no_offset():
    # Q4 2025-26: statement due 28 Aug 2026; offset not available for the June 2026 quarter.
    # One employee 10,000 -> 1,200; lodged 1 Sep 2026 -> days 1 Apr to 31 Aug inclusive = 153.
    # NI = 1,200 x 153 / 365 x 10% = 50.30; admin 20; SGC 1,270.30.
    out = calc("sg_charge_estimate", "2025-26", quarter_end="2026-06-30", calculation_date="2026-09-01",
               late_payments_elected_offset=1200, employees=[{"qualifying_earnings": 10000}])
    assert out["sgc_statement_due"] == "2026-08-28" and out["nominal_interest_days"] == 153
    assert out["sg_charge"] == 1270.30 and out["late_payment_offset"] == 0.0


def test_sgc_refusals():
    assert refused("sg_charge_estimate", "2026-27", qe_day="2026-09-11", calculation_date="2026-10-01",
                   dispute_or_penalty=True, employees=[{"qualifying_earnings": 1}]) == "AU-PAY-007"
    assert refused("sg_charge_estimate", "2025-26", quarter_end="2025-09-30", calculation_date="2025-11-20",
                   employees=[{"qualifying_earnings": 1000, "on_time_contributions": 50}]) == "AU-PAY-007"
    assert refused("sg_charge_estimate", "2026-27", quarter_end="2026-06-30", calculation_date="2026-09-01",
                   employees=[{"qualifying_earnings": 1000}]) == "AU-PAY-008"


# ---------------------------------------------------------------- worker status

def test_worker_status_lean_and_s12_3():
    out = calc("worker_status_indicators", "2026-27", right_to_control_how_work_done="yes", must_perform_personally="yes",
               paid_by_time="yes", contract_principally_for_labour="yes", has_abn=True, labelled_contractor=True)
    assert out["lean"] == "leans employee"
    assert out["sg_extended_definition_s12_3"].startswith("likely applies")


def test_worker_status_conflict_no_conclusion():
    out = calc("worker_status_indicators", "2026-27", right_to_control_how_work_done="yes",
               provides_significant_tools_equipment="yes", builds_own_goodwill="yes", paid_for_result="yes",
               contract_principally_for_labour="no")
    assert out["lean"] == "mixed: facts conflict, no conclusion"
    assert out["sg_extended_definition_s12_3"] == "unlikely to apply"


def test_worker_status_entity_and_dispute():
    out = calc("worker_status_indicators", "2026-27", worker_is_individual=False, contract_principally_for_labour="yes")
    assert out["sg_extended_definition_s12_3"].startswith("does not apply")
    assert refused("worker_status_indicators", "2026-27", dispute_or_sham_allegation=True) == "AU-PAY-001"


def test_figures_verified():
    for y in ("2025-26", "2026-27"):
        f = Figures(y)
        for k in ("payroll.payg_scale2_tft", "payroll.payg_scale1_no_tft", "payroll.payg_stsl_component_tft_or_foreign",
                  "payroll.no_abn_withholding_rate", "payroll_wages.national_minimum_wage_hourly"):
            f.get(k)  # raises if not VERIFIED
    assert Figures("2026-27").get("payroll_wages.national_minimum_wage_hourly") == 26.44
    assert Figures("2025-26").get("payroll_wages.national_minimum_wage_hourly") == 24.95


# ---------------------------------------------------------------- Payday Super business days default to the public holiday data

def test_payday_super_default_uses_holiday_data_no_list_needed():
    # ATO Payday Super example: QE 30 Jul 2026 + 7 business days = Tue 11 Aug 2026 (NT Picnic Day Mon 3 Aug is not a business day).
    # Same answer with no public_holidays given.
    assert business_days_after(date(2026, 7, 30), 7) == date(2026, 8, 11)
    out = calc("super_guarantee", "2026-27", payments=[{"pay_date": "2026-07-30", "ordinary_time_earnings": 1000}])
    assert out["lines"][0]["due_date"] == "2026-08-11"
    assert not any("No public holidays given" in w for w in out["warnings"])
    assert any(f["key"] == "holidays.commonwealth_tax" for f in out["figures_used"])


def test_payday_super_first_contribution_data_default():
    # ATO Payday Super example (Hannah): QE 9 Jul 2026, first contribution, 20 business days = Fri 7 Aug 2026.
    out = calc("super_guarantee", "2026-27", payments=[{"pay_date": "2026-07-09", "ordinary_time_earnings": 1000}],
               first_contribution_new_employee=True)
    assert out["lines"][0]["due_date"] == "2026-08-07"


def test_payday_super_over_easter_2027():
    # QE Wed 24 Mar 2027 + 7 business days. Thu 25 = 1; Fri 26 Good Friday x; Sat 27, Sun 28; Mon 29 Easter Monday x;
    # Tue 30 = 2; Wed 31 = 3; Thu 1 Apr = 4; Fri 2 Apr = 5; Mon 5 Apr = 6; Tue 6 Apr = 7 -> Tue 6 Apr 2027.
    out = calc("super_guarantee", "2026-27", payments=[{"pay_date": "2027-03-24", "ordinary_time_earnings": 1000}])
    assert out["lines"][0]["due_date"] == "2027-04-06"


def test_payday_super_over_christmas_and_new_year():
    # QE Fri 18 Dec 2026 + 7 business days. Mon 21 = 1; Tue 22 = 2; Wed 23 = 3; Thu 24 Christmas Eve (part-day in QLD, NT, SA;
    # the ATO table treats it as a holiday) x; Fri 25 x; Sat 26, Sun 27; Mon 28 additional Boxing Day holiday x; Tue 29 = 4;
    # Wed 30 = 5; Thu 31 New Year's Eve (NT, SA part-day) x; Fri 1 Jan x; Sat 2, Sun 3; Mon 4 = 6; Tue 5 Jan = 7 -> Tue 5 Jan 2027.
    out = calc("super_guarantee", "2026-27", payments=[{"pay_date": "2026-12-18", "ordinary_time_earnings": 1000}])
    assert out["lines"][0]["due_date"] == "2027-01-05"


def test_public_holidays_list_is_an_override_only():
    # An explicit empty list means weekends only: QE 30 Jul 2026 + 7 bd = Mon 10 Aug 2026 (no Picnic Day skipped).
    out = calc("super_guarantee", "2026-27", payments=[{"pay_date": "2026-07-30", "ordinary_time_earnings": 1000}],
               public_holidays=[])
    assert out["lines"][0]["due_date"] == "2026-08-10"
    assert any("override" in w for w in out["warnings"])
    assert not any(f["key"] == "holidays.commonwealth_tax" for f in out["figures_used"])


def test_quarterly_super_due_date_rolls_over_holiday_data():
    # 2025-26 quarterly regime, Q3 (Jan-Mar 2026) due 28 Apr 2026 (Tue): a business day, no roll from data.
    out = calc("super_guarantee", "2025-26", payments=[{"pay_date": "2026-02-13", "ordinary_time_earnings": 1000}])
    assert out["lines"][0]["due_date"] == "2026-04-28"


def test_business_days_outside_holiday_data_refuse():
    from au_tax.registry import Refusal
    with pytest.raises(Refusal) as e:
        business_days_after(date(2028, 9, 7), 7)   # LCR 2026/3 example dates are outside the data range
    assert e.value.code == "AU-GEN-004"
    assert business_days_after(date(2028, 9, 7), 7, set()) == date(2028, 9, 18)  # explicit override still works


def test_sgc_on_time_deadline_uses_holiday_data():
    # LCR 2026/3 Example 16 (2027 dates): QE 30 Jul 2027, on-time deadline Wed 11 Aug 2027 with Mon 2 Aug 2027 Picnic Day
    # (NT), taken from the data with no public_holidays given.
    inp = SgcInput(qe_day=date(2027, 7, 30), calculation_date=date(2027, 9, 29), assessment_date=date(2027, 9, 29),
                   gic_annual_rate_override=0.10, employees=[{"name": "Sam", "qualifying_earnings": 3000, "on_time_contributions": 360}])
    out = _sgc_payday(Figures("2026-27"), inp, [], [])
    assert out["employees"][0]["on_time_deadline"] == "2027-08-11"
