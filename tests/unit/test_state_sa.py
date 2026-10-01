"""SA payroll tax, land tax and stamp duty. Expected values come from RevenueSA published worked examples
(cited per test) or hand computation shown step by step. None were produced by running the calculators."""

import pytest

from au_tax.registry import load_all, run


def calc(name, year="2026-27", **kw):
    code, out = run(name, year, kw)
    assert code == 0, out
    return out


def refused(name, year="2026-27", **kw):
    code, out = run(name, year, kw)
    assert code == 3, out
    return out["refusal"]["code"]


def approx(x, tol=0.01):
    return pytest.approx(x, abs=tol)


def test_registered():
    reg = load_all()
    for n in ("sa_payroll_tax", "sa_land_tax", "sa_stamp_duty_transfer"):
        assert n in reg


# ------------------------------------------------------------------ payroll tax: annual

def test_payroll_nil_at_threshold():
    # 1,500,000 is not more than the threshold (Payroll Tax Act 2009 (SA) Sch 1 cl 4): nil.
    out = calc("sa_payroll_tax", sa_taxable_wages=1_500_000)
    assert out["rate_band"] == "nil"
    assert out["payroll_tax"] == 0


def test_payroll_nil_below_threshold():
    assert calc("sa_payroll_tax", sa_taxable_wages=900_000)["payroll_tax"] == 0


def test_payroll_variable_band_revenuesa_video_example():
    # RevenueSA "How is payroll tax calculated": SA-only employer, wages 1.6m, deduction 600,000, tax on 1,000,000.
    # Rate (Sch 1 cl 5(2)(a)) = 4.95% x (1,600,000 - 1,500,000) / 200,000 = 4.95% x 0.5 = 2.475%.
    # Tax = 1,000,000 x 2.475% = 24,750.
    out = calc("sa_payroll_tax", sa_taxable_wages=1_600_000)
    assert out["rate_band"] == "variable"
    assert out["rate_applied"] == pytest.approx(0.02475)
    assert out["deduction_applied"] == 600_000
    assert out["wages_after_deduction"] == 1_000_000
    assert out["payroll_tax"] == approx(24_750)


def test_payroll_deduction_is_flat_not_tapered():
    # At 1.7m the deduction is still the full 600,000 (it does not taper to nil).
    # Rate = 4.95% x 200,000/200,000 = 4.95%; tax = (1,700,000 - 600,000) x 4.95% = 1,100,000 x 0.0495 = 54,450.
    out = calc("sa_payroll_tax", sa_taxable_wages=1_700_000)
    assert out["deduction_applied"] == 600_000
    assert out["payroll_tax"] == approx(54_450)


def test_payroll_top_rate():
    # 2,000,000: 4.95% x (2,000,000 - 600,000) = 0.0495 x 1,400,000 = 69,300
    assert calc("sa_payroll_tax", sa_taxable_wages=2_000_000)["payroll_tax"] == approx(69_300)


def test_payroll_just_over_threshold():
    # 1,500,100: rate = 0.0495 x 100 / 200,000 = 0.000024750; net = 1,500,100 - 600,000 = 900,100
    # tax = 900,100 x 0.00002475 = 22.277475
    assert calc("sa_payroll_tax", sa_taxable_wages=1_500_100)["payroll_tax"] == approx(22.28)


def test_payroll_interstate_wages_reduce_deduction():
    # SA 600,000 + interstate 1,200,000 = 1,800,000 > 1.7m: top rate 4.95%.
    # Deduction = 600,000 x 600,000 / 1,800,000 = 200,000. Net = 400,000. Tax = 400,000 x 0.0495 = 19,800.
    out = calc("sa_payroll_tax", sa_taxable_wages=600_000, annual_interstate_wages=1_200_000)
    assert out["deduction_applied"] == approx(200_000)
    assert out["payroll_tax"] == approx(19_800)


def test_payroll_interstate_wages_count_toward_threshold():
    # SA wages 800,000 alone are under the threshold, but with 800,000 interstate the total 1,600,000 is in the variable band.
    # Rate 2.475%. Deduction = 600,000 x 800/1600 = 300,000. Net = 500,000. Tax = 500,000 x 0.02475 = 12,375.
    out = calc("sa_payroll_tax", sa_taxable_wages=800_000, annual_interstate_wages=800_000)
    assert out["rate_band"] == "variable"
    assert out["payroll_tax"] == approx(12_375)


def test_payroll_part_year_revenuesa_annualisation_example():
    # RevenueSA: trades 211 days, wages 1,000,000 -> annualised 1,000,000 x 365/211 = 1,729,857 -> top rate.
    # Deduction = 600,000 x 211/365 = 346,849.32; net = 653,150.68; tax = 653,150.68 x 0.0495 = 32,330.96.
    out = calc("sa_payroll_tax", sa_taxable_wages=1_000_000, days_employing=211)
    assert out["annualised_wages_for_rate"] == approx(1_729_857.8, 0.5)
    assert out["rate_applied"] == pytest.approx(0.0495)
    assert out["deduction_applied"] == approx(346_849.32)
    assert out["payroll_tax"] == approx(32_330.96, 0.02)


def test_payroll_part_year_threshold_prorated():
    # 200 days, wages 800,000: threshold = 1,500,000 x 200/365 = 821,917.8 > 800,000 -> nil.
    assert calc("sa_payroll_tax", sa_taxable_wages=800_000, days_employing=200)["payroll_tax"] == 0


def test_payroll_year_without_rates_file_refused():
    # No 2028-29 rates file exists: refused as unpublished (AU-GEN-003), never guessed.
    code, out = run("sa_payroll_tax", "2028-29", {"sa_taxable_wages": 2_000_000})
    assert code == 4 and out["refusal"]["code"] == "AU-GEN-003"


def test_payroll_2025_26_same_result():
    assert calc("sa_payroll_tax", "2025-26", sa_taxable_wages=2_000_000)["payroll_tax"] == approx(69_300)


# ------------------------------------------------------------------ payroll tax: monthly (RevenueSA 2022-23 guide examples)

def test_payroll_monthly_guide_small_business_indicative_rate():
    # Guide example: est. annual wages 1,560,000 (SA only), March wages 130,000, indicative rate 1.48%,
    # monthly deduction 50,000: (130,000 - 50,000) x 1.48% = 80,000 x 0.0148 = 1,184.00.
    # Exact rate would be 4.95% x 60,000/200,000 = 1.485%; RevenueSA truncates to 1.48%.
    out = calc("sa_payroll_tax", period="monthly", sa_taxable_wages=130_000, annual_sa_taxable_wages=1_560_000,
               indicative_rate_2dp=True)
    assert out["rate_applied"] == pytest.approx(0.0148)
    assert out["deduction_applied"] == approx(50_000)
    assert out["payroll_tax"] == approx(1_184.00)


def test_payroll_monthly_exact_rate_differs_slightly():
    # Exact statutory rate 1.485%: 80,000 x 0.01485 = 1,188.00
    out = calc("sa_payroll_tax", period="monthly", sa_taxable_wages=130_000, annual_sa_taxable_wages=1_560_000)
    assert out["payroll_tax"] == approx(1_188.00)


def test_payroll_monthly_top_rate_guide_example():
    # Guide: est. 4,200,000; March 350,000: (350,000 - 50,000) x 4.95% = 14,850.
    out = calc("sa_payroll_tax", period="monthly", sa_taxable_wages=350_000, annual_sa_taxable_wages=4_200_000)
    assert out["payroll_tax"] == approx(14_850)


def test_payroll_monthly_interstate_guide_example():
    # Guide: SA 800,000 + Vic 800,000 (1.6m, variable band, indicative 2.47%); deduction 600,000 x 800/1600 = 300,000 = 25,000/month.
    # March SA wages 75,000: (75,000 - 25,000) x 2.47% = 50,000 x 0.0247 = 1,235.00
    out = calc("sa_payroll_tax", period="monthly", sa_taxable_wages=75_000, annual_sa_taxable_wages=800_000,
               annual_interstate_wages=800_000, indicative_rate_2dp=True)
    assert out["deduction_applied"] == approx(25_000)
    assert out["payroll_tax"] == approx(1_235.00)


def test_payroll_monthly_interstate_top_rate_guide_example():
    # Guide: SA 500,000 + Vic 1,500,000 = 2,000,000 -> 4.95%; deduction 600,000 x 500/2000 = 150,000 = 12,500/month.
    # March 40,000: (40,000 - 12,500) x 4.95% = 27,500 x 0.0495 = 1,361.25
    out = calc("sa_payroll_tax", period="monthly", sa_taxable_wages=40_000, annual_sa_taxable_wages=500_000,
               annual_interstate_wages=1_500_000)
    assert out["payroll_tax"] == approx(1_361.25)


def test_payroll_monthly_wages_below_deduction_nil():
    # Month wages 40,000 < monthly deduction 50,000: nothing payable (Sch 2 cl 5(2)).
    out = calc("sa_payroll_tax", period="monthly", sa_taxable_wages=40_000, annual_sa_taxable_wages=4_200_000)
    assert out["payroll_tax"] == 0


def test_payroll_monthly_needs_annual_estimate():
    code, out = run("sa_payroll_tax", "2026-27", {"period": "monthly", "sa_taxable_wages": 100_000})
    assert code == 2


# ------------------------------------------------------------------ payroll tax: groups (guide example)

def test_payroll_group_dge_and_member_guide_example():
    # Guide: group SA-only wages 6,240,000 -> 4.95%. March: DGE 400,000, member 120,000.
    # DGE: (400,000 - 50,000) x 4.95% = 350,000 x 0.0495 = 17,325. Member: 120,000 x 0.0495 = 5,940. Total 23,265.
    dge = calc("sa_payroll_tax", period="monthly", sa_taxable_wages=400_000, annual_sa_taxable_wages=4_800_000,
               group_status="designated_group_employer", group_annual_sa_taxable_wages=6_240_000)
    mem = calc("sa_payroll_tax", period="monthly", sa_taxable_wages=120_000, annual_sa_taxable_wages=1_440_000,
               group_status="group_member", group_annual_sa_taxable_wages=6_240_000)
    assert dge["payroll_tax"] == approx(17_325)
    assert mem["payroll_tax"] == approx(5_940)
    assert mem["deduction_applied"] == 0


def test_payroll_group_threshold_tested_on_group_wages():
    # Each of two related employers pays 800,000: alone nil, but grouped total 1,600,000 is in the variable band.
    # Member (no deduction): 800,000 x 2.475% = 19,800.
    mem = calc("sa_payroll_tax", sa_taxable_wages=800_000, group_status="group_member",
               group_annual_sa_taxable_wages=1_600_000)
    assert mem["rate_band"] == "variable"
    assert mem["payroll_tax"] == approx(19_800)
    # DGE: deduction 600,000 x 1,600,000/1,600,000 = 600,000; (800,000 - 600,000) x 2.475% = 4,950
    dge = calc("sa_payroll_tax", sa_taxable_wages=800_000, group_status="designated_group_employer",
               group_annual_sa_taxable_wages=1_600_000)
    assert dge["payroll_tax"] == approx(4_950)


def test_payroll_group_unused_deduction_warning():
    # DGE wages 100,000 in a group of 2,000,000: deduction 600,000 exceeds its wages: tax nil, unused deduction 500,000.
    dge = calc("sa_payroll_tax", sa_taxable_wages=100_000, group_status="designated_group_employer",
               group_annual_sa_taxable_wages=2_000_000)
    assert dge["payroll_tax"] == 0
    assert dge["unused_deduction"] == approx(500_000)


def test_payroll_group_needs_group_wages():
    code, _ = run("sa_payroll_tax", "2026-27", {"sa_taxable_wages": 1, "group_status": "group_member"})
    assert code == 2


# ------------------------------------------------------------------ payroll tax: refusals and due dates

def test_payroll_other_state_refused():
    assert refused("sa_payroll_tax", state="NSW", sa_taxable_wages=2_000_000) == "AU-SA-001"


def test_payroll_grouping_dispute_refused():
    assert refused("sa_payroll_tax", sa_taxable_wages=2_000_000, special_circumstances=["grouping_disputed"]) == "AU-SA-002"


def test_payroll_contractor_determination_refused():
    assert refused("sa_payroll_tax", sa_taxable_wages=2_000_000,
                   special_circumstances=["contractor_determination_needed"]) == "AU-SA-002"


def test_payroll_due_dates_reported():
    # Act s 9(1)(a): 7 days after month end; RevenueSA: annual reconciliation 28 July; Act s 9(1)(b): June within 21 days.
    out = calc("sa_payroll_tax", sa_taxable_wages=2_000_000)
    assert "day 7" in out["due"]["monthly_return_and_payment"]
    assert out["due"]["annual_reconciliation_revenuesa"].startswith("28 July")
    assert "21 days" in out["due"]["june_tax_payable_under_act_s9_1_b"]


# ------------------------------------------------------------------ land tax 2026-27 general scale

@pytest.mark.parametrize("sv,tax", [
    (500_000, 0),            # under 936,000
    (936_000, 0),            # at threshold
    (1_000_000, 320),        # 0.50 x (64,000 / 100 = 640) = 320
    (1_504_000, 2_840),      # 0.50 x (568,000 / 100 = 5,680) = 2,840
    (2_000_000, 7_800),      # 2,840 + 1.00 x (496,000 / 100 = 4,960) = 7,800
    (2_188_000, 9_680),      # 2,840 + 1.00 x 6,840 = 9,680
    (3_000_000, 25_920),     # 9,680 + 2.00 x (812,000 / 100 = 8,120) = 9,680 + 16,240
    (3_504_000, 36_000),     # 9,680 + 2.00 x 13,160 = 36,000
    (4_000_000, 47_904),     # 36,000 + 2.40 x (496,000 / 100 = 4,960) = 36,000 + 11,904
])
def test_land_tax_general_2026_27(sv, tax):
    assert calc("sa_land_tax", total_site_value=sv)["land_tax"] == approx(tax)


def test_land_tax_or_part_of_100():
    # 1,000,050: 64,050 above threshold -> 641 units of $100 or part -> 0.50 x 641 = 320.50
    assert calc("sa_land_tax", total_site_value=1_000_050)["land_tax"] == approx(320.50)


def test_land_tax_minimum_assessment():
    # 936,100: 1 unit x 0.50 = 0.50 < 20: no assessment issued.
    out = calc("sa_land_tax", total_site_value=936_100)
    assert out["land_tax"] == 0 and out["assessment_issued"] is False
    assert out["land_tax_before_minimum"] == approx(0.50)


def test_land_tax_just_over_minimum():
    # 936,000 + 4,000 = 940,000: 40 units x 0.50 = 20.00, not under 20 -> assessed.
    out = calc("sa_land_tax", total_site_value=940_000)
    assert out["land_tax"] == approx(20) and out["assessment_issued"] is True


def test_land_tax_2025_26_general():
    # threshold 833,000; 1,000,000: 0.50 x (167,000 / 100 = 1,670) = 835
    assert calc("sa_land_tax", "2025-26", total_site_value=1_000_000)["land_tax"] == approx(835)


def test_land_tax_aggregation_of_parcels():
    # Two parcels each under the threshold but 600,000 + 700,000 = 1,300,000 -> 0.50 x (364,000/100 = 3,640) = 1,820
    out = calc("sa_land_tax", parcels=[{"site_value": 600_000}, {"site_value": 700_000}])
    assert out["taxable_site_value"] == 1_300_000
    assert out["land_tax"] == approx(1_820)


# ------------------------------------------------------------------ land tax trust scale

@pytest.mark.parametrize("sv,tax", [
    (24_000, 0),             # under 25,000
    (25_000, 0),             # at trust threshold
    (500_000, 2_500),        # 125 + 0.50 x (475,000 / 100 = 4,750) = 125 + 2,375
    (936_000, 4_680),        # 125 + 0.50 x 9,110 = 125 + 4,555
    (1_000_000, 5_320),      # 4,680 + 1.00 x 640
    (1_504_000, 10_360),     # 4,680 + 1.00 x 5,680
    (2_188_000, 20_620),     # 10,360 + 1.50 x 6,840 = 10,360 + 10,260
    (3_504_000, 52_204),     # 20,620 + 2.40 x 13,160 = 20,620 + 31,584
    (4_000_000, 64_108),     # 52,204 + 2.40 x 4,960 = 52,204 + 11,904
])
def test_land_tax_trust_2026_27(sv, tax):
    assert calc("sa_land_tax", ownership_type="trust", total_site_value=sv)["land_tax"] == approx(tax)


# ------------------------------------------------------------------ land tax exemptions

def test_land_tax_ppr_full_exemption_excluded_from_aggregation():
    # PPR 900,000 exempt; investment 1,200,000 taxable: 0.50 x (264,000/100 = 2,640) = 1,320
    out = calc("sa_land_tax", parcels=[
        {"site_value": 900_000, "exemption": "principal_place_of_residence", "business_floor_area_percent": 0},
        {"site_value": 1_200_000}])
    assert out["exempt_site_value"] == 900_000
    assert out["land_tax"] == approx(1_320)


@pytest.mark.parametrize("pct,taxable_share", [
    (24.9, 0.0),    # under 25%: full exemption
    (25, 0.25),     # 25% to under 30%: 75% reduction -> 25% taxable
    (27, 0.25),
    (30, 0.30),     # 30% to under 35%: 70% reduction
    (50, 0.50),     # 50% to under 55%: 50% reduction
    (74.9, 0.70),   # 70% to under 75%: 30% reduction
    (75, 0.75),     # 75%: 25% reduction
    (75.1, 1.0),    # above 75%: no exemption
])
def test_land_tax_ppr_partial_exemption_table(pct, taxable_share):
    # RevenueSA residential home page table. Site value 4,000,000 -> taxable = 4,000,000 x share.
    out = calc("sa_land_tax", parcels=[{"site_value": 4_000_000, "exemption": "principal_place_of_residence",
                                        "business_floor_area_percent": pct}])
    assert out["taxable_site_value"] == approx(4_000_000 * taxable_share)


def test_land_tax_ppr_partial_50_percent_amount():
    # 4,000,000 x 50% = 2,000,000 taxable -> 7,800 (see general scale above)
    out = calc("sa_land_tax", parcels=[{"site_value": 4_000_000, "exemption": "principal_place_of_residence",
                                        "business_floor_area_percent": 50}])
    assert out["land_tax"] == approx(7_800)


def test_land_tax_primary_production_exempt():
    out = calc("sa_land_tax", parcels=[{"site_value": 5_000_000, "exemption": "primary_production"}])
    assert out["land_tax"] == 0 and out["taxable_site_value"] == 0


def test_land_tax_foreign_owner_no_surcharge():
    # SA has no land tax surcharge: same tax as a resident (320), with a warning.
    out = calc("sa_land_tax", total_site_value=1_000_000, foreign_owner=True)
    assert out["land_tax"] == approx(320)
    assert any("no foreign owner land tax surcharge" in w.lower() for w in out["warnings"])


def test_land_tax_input_validation():
    code, _ = run("sa_land_tax", "2026-27", {})
    assert code == 2
    code, _ = run("sa_land_tax", "2026-27", {"total_site_value": 1, "parcels": [{"site_value": 1}]})
    assert code == 2


def test_land_tax_refusals():
    assert refused("sa_land_tax", state="Victoria", total_site_value=1_000_000) == "AU-SA-001"
    assert refused("sa_land_tax", total_site_value=1_000_000, special_circumstances=["exemption_disputed"]) == "AU-SA-003"
    assert refused("sa_land_tax", total_site_value=1_000_000, special_circumstances=["corporate_reconstruction"]) == "AU-SA-003"
    assert refused("sa_land_tax", total_site_value=1_000_000, special_circumstances=["trust_designated_beneficiary"]) == "AU-SA-004"
    assert refused("sa_land_tax", total_site_value=1_000_000, special_circumstances=["unit_trust_or_landholder"]) == "AU-SA-004"


# ------------------------------------------------------------------ stamp duty

D = "2026-09-01"


@pytest.mark.parametrize("v,duty", [
    (12_000, 120),          # $1 per $100: 120 units
    (12_001, 122),          # 120 + 2.00 x 1 unit (or part)
    (30_000, 480),          # 120 + 2.00 x 180
    (50_000, 1_080),        # 480 + 3.00 x 200
    (100_000, 2_830),       # 1,080 + 3.50 x 500
    (200_000, 6_830),       # 2,830 + 4.00 x 1,000
    (250_000, 8_955),       # 6,830 + 4.25 x 500
    (300_000, 11_330),      # 8,955 + 4.75 x 500 = 8,955 + 2,375
    (400_000, 16_330),      # 11,330 + 5.00 x 1,000 (RevenueSA FHB table: $400,000 -> $16,330)
    (500_000, 21_330),      # 11,330 + 5.00 x 2,000
    (600_000, 26_830),      # 21,330 + 5.50 x 1,000 (RevenueSA FOS example: $600,000 -> $26,830)
    (650_000, 29_580),      # 21,330 + 5.50 x 1,500 (RevenueSA FHB table)
    (700_000, 32_330),      # 21,330 + 5.50 x 2,000 (RevenueSA FHB table)
    (2_000_000, 103_830),   # 21,330 + 5.50 x 15,000 = 21,330 + 82,500 (SA Government downsizer maximum saving 103,830)
])
def test_stamp_duty_general_scale(v, duty):
    out = calc("sa_stamp_duty_transfer", dutiable_value=v, contract_date=D)
    assert out["duty_before_relief"] == approx(duty)
    assert out["duty_payable"] == approx(duty)
    assert out["foreign_ownership_surcharge"] == 0


def test_stamp_duty_or_part_of_100():
    # 500,050: 21,330 + 5.50 x 1 unit = 21,335.50
    assert calc("sa_stamp_duty_transfer", dutiable_value=500_050, contract_date=D)["duty_payable"] == approx(21_335.50)


def test_stamp_duty_foreign_surcharge_revenuesa_example():
    # RevenueSA: 600,000 residential: duty 26,830 + surcharge 7% x 600,000 = 42,000. Total 68,830.
    out = calc("sa_stamp_duty_transfer", dutiable_value=600_000, contract_date=D, foreign_person=True)
    assert out["duty_payable"] == approx(26_830)
    assert out["foreign_ownership_surcharge"] == approx(42_000)
    assert out["total_duty_and_surcharge"] == approx(68_830)


def test_stamp_duty_foreign_part_interest_revenuesa_example():
    # RevenueSA FOS example 2: foreign trust acquires 20% of 500,000 -> interest value 100,000 -> surcharge 7,000.
    out = calc("sa_stamp_duty_transfer", dutiable_value=100_000, contract_date=D, foreign_person=True)
    assert out["foreign_ownership_surcharge"] == approx(7_000)
    # Jamie (foreign) and Drew joint tenants of 600,000: Jamie's 50% = 300,000 -> 21,000.
    out = calc("sa_stamp_duty_transfer", dutiable_value=600_000, contract_date=D, foreign_person=True,
               foreign_interest_percent=50)
    assert out["foreign_ownership_surcharge"] == approx(21_000)
    assert out["duty_payable"] == approx(26_830)


def test_stamp_duty_qualifying_non_residential_nil():
    # Non-residential, non-primary-production land: nil duty, and no residential surcharge.
    out = calc("sa_stamp_duty_transfer", dutiable_value=2_500_000, property_type="qualifying_non_residential",
               contract_date=D, foreign_person=True)
    assert out["duty_payable"] == 0 and out["foreign_ownership_surcharge"] == 0


def test_stamp_duty_primary_production_dutiable_no_surcharge():
    # Primary production land is dutiable at the conveyance scale; the surcharge is for residential land only.
    out = calc("sa_stamp_duty_transfer", dutiable_value=600_000, property_type="primary_production",
               contract_date=D, foreign_person=True)
    assert out["duty_payable"] == approx(26_830)
    assert out["foreign_ownership_surcharge"] == 0


def test_stamp_duty_fhb_full_relief_any_value():
    # Contract on or after 13 Feb 2025: full relief regardless of value. 900,000 new home: duty 21,330 + 5.5 x 4,000 = 43,330; relief all.
    out = calc("sa_stamp_duty_transfer", dutiable_value=900_000, contract_date="2025-03-01",
               first_home_buyer_new_home=True)
    assert out["duty_before_relief"] == approx(43_330)
    assert out["first_home_buyer_relief"] == approx(43_330)
    assert out["duty_payable"] == 0


def test_stamp_duty_fhb_on_start_date():
    out = calc("sa_stamp_duty_transfer", dutiable_value=400_000, contract_date="2025-02-13",
               first_home_buyer_new_home=True)
    assert out["duty_payable"] == 0


def test_stamp_duty_fhb_does_not_reduce_foreign_surcharge():
    # RevenueSA: contracts from 13 Feb 2025, relief is not applied to the surcharge. 600,000: duty relieved, surcharge 42,000 payable.
    out = calc("sa_stamp_duty_transfer", dutiable_value=600_000, contract_date="2025-06-01",
               first_home_buyer_new_home=True, foreign_person=True)
    assert out["duty_payable"] == 0
    assert out["foreign_ownership_surcharge"] == approx(42_000)
    assert out["total_duty_and_surcharge"] == approx(42_000)


def test_stamp_duty_fhb_before_start_date_refused():
    assert refused("sa_stamp_duty_transfer", dutiable_value=600_000, contract_date="2025-02-12",
                   first_home_buyer_new_home=True) == "AU-SA-006"


def test_stamp_duty_before_2018_refused():
    assert refused("sa_stamp_duty_transfer", dutiable_value=600_000, contract_date="2018-06-30") == "AU-SA-006"


def test_stamp_duty_established_home_no_relief_without_flag():
    # Established home: no FHB flag, full duty.
    out = calc("sa_stamp_duty_transfer", dutiable_value=650_000, contract_date="2026-03-01")
    assert out["duty_payable"] == approx(29_580)


def test_stamp_duty_downsizer_refused():
    assert refused("sa_stamp_duty_transfer", dutiable_value=1_500_000, contract_date="2026-05-01",
                   seniors_downsizing_relief_claimed=True) == "AU-SA-005"


def test_stamp_duty_special_and_state_refusals():
    assert refused("sa_stamp_duty_transfer", state="NSW", dutiable_value=1, contract_date=D) == "AU-SA-001"
    assert refused("sa_stamp_duty_transfer", dutiable_value=1, contract_date=D, special_circumstances=["landholder"]) == "AU-SA-004"
    assert refused("sa_stamp_duty_transfer", dutiable_value=1, contract_date=D, special_circumstances=["unit_trust"]) == "AU-SA-004"


def test_stamp_duty_2025_26_same_scale():
    out = calc("sa_stamp_duty_transfer", "2025-26", dutiable_value=600_000, contract_date="2025-09-01")
    assert out["duty_payable"] == approx(26_830)


def test_figures_used_reported_and_verified():
    out = calc("sa_stamp_duty_transfer", dutiable_value=600_000, contract_date=D)
    assert out["draft"] is False
    assert any(f["key"] == "state.sa.stamp_duty_conveyance_scale" for f in out["figures_used"])


# ---------------------------------------------------------------- due dates (SA regime: SA public holidays only)

@pytest.mark.parametrize("wages_month,expected", [
    # RevenueSA published 2026-27 lodgement dates (monthly-returns page, read 29 Sep 2026), typed independently.
    ("2026-07", "2026-08-07"), ("2026-08", "2026-09-07"), ("2026-09", "2026-10-07"),
    ("2026-10", "2026-11-09"),   # 7 Nov 2026 is a Saturday
    ("2026-11", "2026-12-07"),
    ("2026-12", "2027-01-14"),   # published Christmas/New Year extension, not a roll of 7 Jan
    ("2027-01", "2027-02-08"),   # 7 Feb 2027 is a Sunday
    ("2027-02", "2027-03-09"),   # 7 Mar 2027 is a Sunday and Mon 8 Mar 2027 is Adelaide Cup Day
    ("2027-03", "2027-04-07"), ("2027-04", "2027-05-07"),
    ("2027-05", "2027-06-07"),   # WA Day is Mon 7 Jun 2027: an ATO due date would roll to 8 Jun, RevenueSA's stays 7 Jun
])
def test_payroll_monthly_due_dates_match_revenuesa_2026_27(wages_month, expected):
    out = calc("sa_payroll_tax", period="monthly", sa_taxable_wages=130_000, annual_sa_taxable_wages=1_560_000,
               wages_month=wages_month)
    assert out["due_dates"]["monthly_return"]["due_date"] == expected


def test_payroll_monthly_adelaide_cup_roll_is_explained():
    out = calc("sa_payroll_tax", period="monthly", sa_taxable_wages=130_000, annual_sa_taxable_wages=1_560_000,
               wages_month="2027-02")
    m = out["due_dates"]["monthly_return"]
    assert m["ordinary_due_date"] == "2027-03-07" and m["published_extension"] is False
    roll = m["business_day_roll"]
    assert roll["regime"] == "sa_state_tax" and roll["rolled"] is True
    assert "Adelaide Cup" in roll["reason"] and "Sunday" in roll["reason"]
    assert "Public Holidays Act 2023 (SA)" in roll["rule"]
    assert any(f["key"] == "holidays.sa_state_tax" for f in out["figures_used"])


def test_payroll_december_extension_is_published_not_a_roll():
    out = calc("sa_payroll_tax", period="monthly", sa_taxable_wages=130_000, annual_sa_taxable_wages=1_560_000,
               wages_month="2026-12")
    m = out["due_dates"]["monthly_return"]
    assert m["ordinary_due_date"] == "2027-01-07" and m["published_extension"] is True and m["due_date"] == "2027-01-14"
    assert any(f["key"] == "state.sa.payroll_tax_december_return_due_yyyymmdd" for f in out["figures_used"])


def test_payroll_december_2025_no_published_extension_warns():
    # RevenueSA's page lists no 2025-26 monthly dates, so the ordinary 7 Jan 2026 (Wed) is used with a warning.
    out = calc("sa_payroll_tax", "2025-26", period="monthly", sa_taxable_wages=130_000, annual_sa_taxable_wages=1_560_000,
               wages_month="2025-12")
    m = out["due_dates"]["monthly_return"]
    assert m["due_date"] == "2026-01-07" and m["published_extension"] is False
    assert any("extend the December return" in w for w in out["warnings"])


def test_payroll_annual_reconciliation_dates():
    # RevenueSA: 2025-26 reconciliation Tue 28 Jul 2026; 2026-27 Wed 28 Jul 2027.
    assert calc("sa_payroll_tax", "2025-26", sa_taxable_wages=2_000_000)["due_dates"]["annual_reconciliation"]["due_date"] == "2026-07-28"
    assert calc("sa_payroll_tax", sa_taxable_wages=2_000_000)["due_dates"]["annual_reconciliation"]["due_date"] == "2027-07-28"


def test_payroll_wages_month_needs_monthly_period():
    code, out = run("sa_payroll_tax", "2026-27", {"sa_taxable_wages": 100_000, "wages_month": "2027-02"})
    assert code == 2


def test_land_tax_assessment_date_shown_and_roll_is_a_labelled_assumption():
    # Assessment due Fri 25 Dec 2026 (Christmas Day); Sat Boxing Day / Proclamation Day holiday, Sun, Mon 28 Dec additional
    # SA holiday -> Tue 29 Dec 2026 under Public Holidays Act 2023 (SA) s 8(2). RevenueSA states no rule.
    out = calc("sa_land_tax", total_site_value=1_000_000, assessment_due_date="2026-12-25")
    p = out["payment_due"]
    assert p["assessment_due_date"] == "2026-12-25" and p["assumed_due_date"] == "2026-12-29" and p["assumed_roll_applied"] is True
    text = " ".join(out["assumptions"])
    assert "ASSUMPTION" in text and "s 8(2)" in text and "RevenueSA" in text


def test_land_tax_other_states_holiday_does_not_move_date():
    out = calc("sa_land_tax", total_site_value=1_000_000, assessment_due_date="2026-11-03")  # Melbourne Cup, VIC only
    assert out["payment_due"]["assumed_due_date"] == "2026-11-03" and out["payment_due"]["assumed_roll_applied"] is False


def test_land_tax_without_assessment_date_has_no_payment_block():
    assert calc("sa_land_tax", total_site_value=1_000_000)["payment_due"] is None


# ------------------------------------------------------------------ due dates after the holiday data

def test_payroll_2027_28_still_returns_the_tax_when_the_reconciliation_date_is_after_the_holiday_data():
    # 2027-28: the annual reconciliation is 28 Jul 2028 (a Friday: 1 Jul 2028 is a Saturday), after the holiday data (ends
    # 30 Jun 2028). The tax is the same arithmetic as any year, so it is still returned; only the date carries AU-GEN-004.
    # Wages 1,500,000 is not more than the threshold (Payroll Tax Act 2009 (SA) Sch 1 cl 4): nil, whatever the year's threshold.
    out = calc("sa_payroll_tax", "2027-28", sa_taxable_wages=1_000_000)
    assert out["payroll_tax"] == 0
    rec = out["due_dates"]["annual_reconciliation"]
    assert rec["original_date"] == rec["due_date"] == "2028-07-28"
    assert rec["business_day_roll"]["rolled"] is False and rec["business_day_roll"]["holiday_data_covers_date"] is False
    assert [f["code"] for f in out["field_refusals"]] == ["AU-GEN-004"]
    assert out["field_refusals"][0]["field"] == "due_dates.annual_reconciliation"
    assert any("2028-07-28" in w and "AU-GEN-004" in w for w in out["warnings"])


def test_payroll_2027_28_monthly_return_in_range_is_rolled_and_only_the_late_date_is_flagged():
    # April 2028 wages: 7 May 2028 is a Sunday (1 May 2028 is a Monday, so 7 May is Sunday) -> Mon 8 May 2028, not an SA holiday.
    out = calc("sa_payroll_tax", "2027-28", sa_taxable_wages=100_000, period="monthly", wages_month="2028-04",
               annual_sa_taxable_wages=1_200_000)
    m = out["due_dates"]["monthly_return"]
    assert m["ordinary_due_date"] == "2028-05-07" and m["due_date"] == "2028-05-08"
    assert [f["field"] for f in out["field_refusals"]] == ["due_dates.annual_reconciliation"]


def test_payroll_in_range_year_has_no_field_refusals():
    out = calc("sa_payroll_tax", sa_taxable_wages=1_500_000)
    assert out["field_refusals"] == []
    assert out["due_dates"]["annual_reconciliation"]["due_date"] == "2027-07-28"


def test_calendar_style_callers_of_the_sa_due_dates_still_refuse_after_the_holiday_data():
    # The strict helpers (used by obligations_calendar, where the date is the answer) keep refusing.
    from datetime import date

    from au_tax.calculators.state_sa import sa_reconciliation_due
    from au_tax.figures import Figures
    from au_tax.registry import Refusal

    with pytest.raises(Refusal) as e:
        sa_reconciliation_due(Figures("2027-28"), date(2028, 6, 30))
    assert e.value.code == "AU-GEN-004"


def test_land_tax_still_returns_the_tax_when_the_assessment_date_is_after_the_holiday_data():
    # The assessment date printed on the notice (28 Jul 2028) is after the holiday data: the tax is unchanged, the date is
    # returned as printed with an AU-GEN-004 field note and the assumption says the roll cannot be checked.
    base = calc("sa_land_tax", total_site_value=1_000_000)
    out = calc("sa_land_tax", total_site_value=1_000_000, assessment_due_date="2028-07-28")
    assert out["land_tax"] == base["land_tax"] and base["field_refusals"] == []
    p = out["payment_due"]
    assert p["assumed_due_date"] == "2028-07-28" and p["assumed_roll_applied"] is False
    assert [f["field"] for f in out["field_refusals"]] == ["payment_due"] and out["field_refusals"][0]["code"] == "AU-GEN-004"
    assert any("cannot be checked" in a for a in out["assumptions"])
