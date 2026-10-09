"""individual_income_tax. Expected values come from ATO worked examples (cited) or hand computation
shown step by step. None were produced by running the calculator."""

import copy

import pytest

from au_tax.calculators.individual import IndividualTaxInput, family_reduction, individual_income_tax
from au_tax.figures import FigureError, Figures
from au_tax.registry import load_all, run


def calc(year, **kw):
    code, out = run("individual_income_tax", year, kw)
    assert code == 0, out
    return out


def approx(x):
    return pytest.approx(x, abs=0.01)


# ---------------------------------------------------------------- registration

def test_registered_as_tool():
    assert "individual_income_tax" in load_all()


# ---------------------------------------------------------------- resident rates 2025-26

def test_2025_26_tax_free_threshold_boundary():
    # 18,200 is the top of the nil band. LITO 700 is capped at gross tax 0. Medicare: 18,200 <= 28,011 lower -> nil.
    out = calc("2025-26", taxable_income=18200)
    assert out["gross_tax"] == 0
    assert out["offsets"]["lito"] == 0
    assert out["medicare_levy"] == 0
    assert out["total_liability"] == 0


def test_2025_26_at_45000():
    # gross = 16% x (45,000 - 18,200) = 0.16 x 26,800 = 4,288
    # LITO at 45,000 (end of 5c taper band) = 700 - 0.05 x (45,000 - 37,500) = 700 - 375 = 325
    # levy = 2% x 45,000 = 900 (above 35,013 upper threshold)
    # total = 4,288 - 325 + 900 = 4,863
    out = calc("2025-26", taxable_income=45000)
    assert out["gross_tax"] == approx(4288)
    assert out["offsets"]["lito"] == approx(325)
    assert out["medicare_levy"] == approx(900)
    assert out["total_liability"] == approx(4863)


def test_2025_26_lito_full_at_37500():
    # gross = 0.16 x (37,500 - 18,200) = 0.16 x 19,300 = 3,088; LITO = 700 (full up to 37,500)
    # levy = 0.02 x 37,500 = 750; total = 3,088 - 700 + 750 = 3,138
    out = calc("2025-26", taxable_income=37500)
    assert out["gross_tax"] == approx(3088)
    assert out["offsets"]["lito"] == approx(700)
    assert out["total_liability"] == approx(3138)


def test_2025_26_lito_mid_second_taper():
    # 60,000: gross = 4,288 + 0.30 x 15,000 = 8,788; LITO = 325 - 0.015 x 15,000 = 100
    # levy = 1,200; total = 8,788 - 100 + 1,200 = 9,888
    out = calc("2025-26", taxable_income=60000)
    assert out["gross_tax"] == approx(8788)
    assert out["offsets"]["lito"] == approx(100)
    assert out["total_liability"] == approx(9888)


def test_2025_26_lito_cut_out_66667():
    # gross = 4,288 + 0.30 x 21,667 = 4,288 + 6,500.10 = 10,788.10
    # LITO = 325 - 0.015 x 21,667 = 325 - 325.005 -> below nil -> 0
    # levy = 0.02 x 66,667 = 1,333.34; total = 12,121.44
    out = calc("2025-26", taxable_income=66667)
    assert out["gross_tax"] == approx(10788.10)
    assert out["offsets"]["lito"] == 0
    assert out["total_liability"] == approx(12121.44)


@pytest.mark.parametrize("ti,tax", [
    (135000, 31288),                 # 4,288 + 0.30 x 90,000 = 31,288 (ATO table base)
    (190000, 51638),                 # 31,288 + 0.37 x 55,000 = 51,638 (ATO table base)
    (250000, 78638),                 # 51,638 + 0.45 x 60,000 = 78,638
])
def test_2025_26_upper_brackets(ti, tax):
    assert calc("2025-26", taxable_income=ti)["gross_tax"] == approx(tax)


def test_2025_26_marginal_rates():
    # 90,000: 30% bracket + 2% levy, no LITO -> 0.32
    assert calc("2025-26", taxable_income=90000)["marginal_rate_tax_and_medicare"] == approx(0.32)
    # 40,000: 16% bracket + 5c LITO taper + 2% levy (above upper threshold) -> 0.23
    assert calc("2025-26", taxable_income=40000)["marginal_rate_tax_and_medicare"] == approx(0.23)


def test_refund_estimate():
    # 90,000: gross 4,288 + 0.30 x 45,000 = 17,788; levy 1,800; total 19,588; withheld 20,000 -> refund 412
    out = calc("2025-26", taxable_income=90000, tax_withheld=20000)
    assert out["total_liability"] == approx(19588)
    assert out["estimated_refund"] == approx(412)


# ---------------------------------------------------------------- resident rates 2026-27

def test_2026_27_at_45000_uses_15_percent():
    # gross = 0.15 x 26,800 = 4,020; LITO 325; levy 900 (45,000 is above the screen, see screen tests)
    # total = 4,020 - 325 + 900 = 4,595
    out = calc("2026-27", taxable_income=45000)
    assert out["gross_tax"] == approx(4020)
    assert out["total_liability"] == approx(4595)
    assert not out["draft"]


def test_2026_27_top_bracket():
    # 200,000: 51,370 + 0.45 x 10,000 = 55,870
    assert calc("2026-27", taxable_income=200000)["gross_tax"] == approx(55870)


# ---------------------------------------------------------------- Medicare levy low-income (2025-26)

def test_medicare_shade_in_ato_example_angie():
    # ATO "Medicare levy reduction for low-income earners" example: 2025-26, single, TI 29,000 -> levy 98.90
    # (0.10 x (29,000 - 28,011) = 98.90). Tax: 0.16 x 10,800 = 1,728 - LITO 700 = 1,028. Total 1,126.90.
    out = calc("2025-26", taxable_income=29000)
    assert out["medicare_levy"] == approx(98.90)
    assert out["total_liability"] == approx(1126.90)


def test_medicare_lower_threshold_inclusive():
    # MLA s7(1): TI not exceeding 28,011 -> no levy
    assert calc("2025-26", taxable_income=28011)["medicare_levy"] == 0


def test_medicare_at_upper_threshold():
    # 35,013 <= phase-in limit: levy capped at 0.10 x (35,013 - 28,011) = 700.20 (< 0.02 x 35,013 = 700.26)
    assert calc("2025-26", taxable_income=35013)["medicare_levy"] == approx(700.20)
    # 35,014 is above the phase-in limit: full 0.02 x 35,014 = 700.28
    assert calc("2025-26", taxable_income=35014)["medicare_levy"] == approx(700.28)


def test_medicare_family_reduction_spouse_not_liable():
    # TI 40,000, spouse 10,000, no children. s7 levy = min(800, 0.1 x 11,989) = 800
    # FI 50,000 > FIT 47,238: reduction = 0.02 x 47,238 - 0.08 x (50,000 - 47,238) = 944.76 - 220.96 = 723.80
    # spouse TI 10,000 <= 28,011 so no s8(3) apportionment. Levy = 800 - 723.80 = 76.20
    out = calc("2025-26", taxable_income=40000, has_spouse=True, spouse_taxable_income=10000)
    assert out["medicare_levy"] == approx(76.20)


def test_medicare_family_reduction_apportioned():
    # TI 30,000, spouse 29,000 (spouse > 28,011 so liable). s7 levy = min(600, 0.1 x 1,989) = 198.90
    # FI 59,000: reduction = 944.76 - 0.08 x 11,762 = 944.76 - 940.96 = 3.80
    # s8(3): x 30,000 / 59,000 = 1.9322; levy = 198.90 - 1.9322 = 196.97
    out = calc("2025-26", taxable_income=30000, has_spouse=True, spouse_taxable_income=29000)
    assert out["medicare_levy"] == approx(196.97)


def test_medicare_sole_parent_two_children_no_levy():
    # FIT = 47,238 + 2 x 4,338 = 55,914; FI 50,000 <= FIT -> no levy (MLA s8(1))
    # gross = 4,288 + 0.30 x 5,000 = 5,788; LITO = 325 - 0.015 x 5,000 = 250; total 5,538
    out = calc("2025-26", taxable_income=50000, dependent_children=2)
    assert out["medicare_levy"] == 0
    assert out["total_liability"] == approx(5538)


def test_family_reduction_formula_ato_ashton_example():
    # ATO "Medicare levy reduction - family income" example (2025-26, SAPTO family): TI 49,700, spouse 21,700,
    # FIT 61,623, s7 levy = min(994, 0.1 x (49,700 - 44,268) = 543.20) = 543.20; ATO result: levy 92.90.
    # Spouse (21,700) is below the SAPTO threshold 44,268, so not liable -> no apportionment.
    assert family_reduction(543.20, 49700, 71400, 61623, 0.02, 0.10, False) == approx(92.90)


def test_medicare_half_exemption_full_year():
    # 90,000 with half exemption all year: 1,800 x (1 - 0.5) = 900
    assert calc("2025-26", taxable_income=90000, medicare_half_exemption_days=365)["medicare_levy"] == approx(900)


# ---------------------------------------------------------------- 2026-27 unverified Medicare thresholds

def test_2026_27_low_income_refused_even_with_draft():
    # 2026-27 low-income thresholds are SUSPECT/null; 30,000 is inside the possible range -> AU-GEN-003 (null, no draft possible), exit 4
    code, out = run("individual_income_tax", "2026-27", {"taxable_income": 30000})
    assert code == 4 and out["refusal"]["code"] == "AU-GEN-003"
    code, out = run("individual_income_tax", "2026-27", {"taxable_income": 30000}, allow_draft=True)
    assert code == 4 and out["refusal"]["code"] == "AU-GEN-003"  # null values cannot be drafted


def test_2026_27_screen_boundary():
    # screen = current-law phase-in limit 35,013 x (0.10 / (0.10 - 0.02) = 1.25) = 43,766.25
    code, _ = run("individual_income_tax", "2026-27", {"taxable_income": 43766})
    assert code == 4
    out = calc("2026-27", taxable_income=43767)
    assert out["medicare_levy"] == approx(875.34)  # 0.02 x 43,767
    assert any(f["key"] == "medicare.low_income_current_law_single_upper" for f in out["figures_used"])


def test_2026_27_family_screen_with_children():
    # couple, FI 80,000, no children: current-law FIT 47,238 x 1.25 x 1.25 = 73,809.38 < 80,000 -> computes
    assert calc("2026-27", taxable_income=80000, has_spouse=True)["medicare_levy"] == approx(1600)
    # with 2 children: FIT 55,914 x 1.5625 = 87,365.63 >= 80,000 -> refused
    code, out = run("individual_income_tax", "2026-27",
                    {"taxable_income": 80000, "has_spouse": True, "dependent_children": 2})
    assert code == 4 and out["refusal"]["code"] == "AU-GEN-003"


# ---------------------------------------------------------------- Medicare levy surcharge

def test_mls_ato_example_tom_2026_27():
    # ATO MLS income, thresholds and rates page: Tom 2026-27, single, no cover, TI 90,000 + RFB 27,000
    # -> income for MLS 117,000, tier 1 (1%), MLS = 117,000 x 1% = 1,170.
    # Tax: 4,020 + 0.30 x 45,000 = 17,520; levy 0.02 x 90,000 = 1,800; total 17,520 + 1,800 + 1,170 = 20,490
    out = calc("2026-27", taxable_income=90000, reportable_fringe_benefits=27000, private_hospital_cover=False)
    assert out["mls_detail"]["tier"] == 1
    assert out["medicare_levy_surcharge"] == approx(1170)
    assert out["total_liability"] == approx(20490)


def test_mls_single_tier_boundaries_2025_26():
    # 101,000 is the top of the base tier (ATO: base tier "$101,000 or less") -> no MLS
    assert calc("2025-26", taxable_income=101000, private_hospital_cover=False)["medicare_levy_surcharge"] == 0
    # 110,000: tier 1, 1% x 110,000 = 1,100
    assert calc("2025-26", taxable_income=110000, private_hospital_cover=False)["medicare_levy_surcharge"] == approx(1100)


def test_mls_tier3_2026_27():
    # 200,000 > 164,000: tier 3, 1.5% x 200,000 = 3,000
    out = calc("2026-27", taxable_income=200000, private_hospital_cover=False)
    assert out["mls_detail"]["tier"] == 3
    assert out["medicare_levy_surcharge"] == approx(3000)


def test_mls_family_threshold_with_children():
    # 2025-26 family tier 1 threshold 202,000 + 1,500 x (3 - 1) = 205,000.
    # combined 150,000 + 60,000 = 210,000 > 205,000 and <= 239,000 -> tier 1; MLS = 1% x 150,000 = 1,500
    out = calc("2025-26", taxable_income=150000, has_spouse=True, spouse_taxable_income=60000,
               dependent_children=3, private_hospital_cover=False)
    assert out["mls_detail"]["tier"] == 1
    assert out["medicare_levy_surcharge"] == approx(1500)
    # combined 150,000 + 54,000 = 204,000 <= 205,000 -> base tier, no MLS
    out = calc("2025-26", taxable_income=150000, has_spouse=True, spouse_taxable_income=54000,
               dependent_children=3, private_hospital_cover=False)
    assert out["medicare_levy_surcharge"] == 0


def test_mls_part_year_without_cover():
    # 110,000, 73 days uncovered: 1% x 110,000 x 73 / 365 = 220
    out = calc("2025-26", taxable_income=110000, private_hospital_cover=True, days_without_cover=73)
    assert out["medicare_levy_surcharge"] == approx(220)


def test_mls_cover_unknown_is_contingent():
    out = calc("2025-26", taxable_income=110000)
    assert out["medicare_levy_surcharge"] == 0
    assert out["mls_detail"]["contingent_amount_if_no_cover"] == approx(1100)
    assert out["warnings"]


# ---------------------------------------------------------------- HELP

def test_help_ato_example_christina_2026_27():
    # ATO study loan page example 1: RI = 60,470 + 5,400 + 1,330 + 16,500 + 2,680 = 86,380
    # repayment = 0.15 x (86,380 - 69,528) = 0.15 x 16,852 = 2,527.80
    out = calc("2026-27", taxable_income=60470, has_help_debt=True, reportable_fringe_benefits=5400,
               net_investment_losses=1330, reportable_super_contributions=16500,
               exempt_foreign_employment_income=2680)
    assert out["help_detail"]["repayment_income"] == approx(86380)
    assert out["help_repayment"] == approx(2527.80)


def test_help_ato_examples_barry_priya_2026_27():
    # Barry: RI 137,064 -> 9,028 + 0.17 x 7,347 = 10,276.99 (ATO example 2)
    out = calc("2026-27", taxable_income=118450, reportable_super_contributions=18614, has_help_debt=True)
    assert out["help_repayment"] == approx(10276.99)
    # Priya: RI 254,780 -> 10% of total = 25,478 (ATO example 3)
    out = calc("2026-27", taxable_income=227123, reportable_super_contributions=27657, has_help_debt=True)
    assert out["help_repayment"] == approx(25478)


@pytest.mark.parametrize("ri,expected", [
    (67000, 0),            # nil band is "$0 - $67,000"
    (125000, 8700),        # 0.15 x 58,000 = 8,700
    (179285, 17928.45),    # 8,700 + 0.17 x 54,285 = 8,700 + 9,228.45
    (179286, 17928.60),    # "$179,286 and over": 10% x 179,286
])
def test_help_2025_26_thresholds(ri, expected):
    assert calc("2025-26", taxable_income=ri, has_help_debt=True)["help_repayment"] == approx(expected)


def test_help_capped_at_balance():
    # 2025-26 RI 100,000: 0.15 x 33,000 = 4,950; balance 3,000 -> 3,000
    out = calc("2025-26", taxable_income=100000, has_help_debt=True, help_debt_balance=3000)
    assert out["help_repayment"] == approx(3000)


# ---------------------------------------------------------------- part-year residents

def test_part_year_ato_example_john():
    # ATO "Tax-free threshold for newcomers": 3 months -> 13,464 + 4,736 x 3/12 = 14,648
    # TI 30,000: gross = 0.16 x (30,000 - 14,648) = 0.16 x 15,352 = 2,456.32; LITO 700 -> 1,756.32
    # Medicare s7: min(600, 0.1 x 1,989) = 198.90; non-resident days default round(365 x 9/12) = 274
    # s9: 198.90 x (365 - 274) / 365 = 198.90 x 91/365 = 49.59; total = 1,756.32 + 49.59 = 1,805.91
    out = calc("2025-26", taxable_income=30000, resident_months=3)
    assert out["tax_free_threshold"] == approx(14648)
    assert out["gross_tax"] == approx(2456.32)
    assert out["medicare_levy"] == approx(49.59)
    assert out["total_liability"] == approx(1805.91)


def test_part_year_above_45000_2026_27():
    # 8 months: TFT = 13,464 + 4,736 x 8/12 = 13,464 + 3,157.33 = 16,621.33
    # TI 100,000: 0.15 x (45,000 - 16,621.33) = 4,256.80 ; + 0.30 x 55,000 = 16,500 -> 20,756.80
    # Medicare with 0 exemption days given: 2,000
    out = calc("2026-27", taxable_income=100000, resident_months=8, medicare_full_exemption_days=0)
    assert out["gross_tax"] == approx(20756.80)
    assert out["medicare_levy"] == approx(2000)


# ---------------------------------------------------------------- foreign residents and WHMs

def test_foreign_resident_2025_26():
    # 30% from $1: 0.30 x 100,000 = 30,000; no LITO, no levy
    out = calc("2025-26", taxable_income=100000, residency="foreign")
    assert out["gross_tax"] == approx(30000)
    assert out["offsets"]["lito"] == 0
    assert out["medicare_levy"] == 0
    assert out["total_liability"] == approx(30000)


def test_foreign_resident_2026_27():
    # ITRA Sch 7 Pt II: 40,500 + 0.37 x (150,000 - 135,000) = 40,500 + 5,550 = 46,050
    assert calc("2026-27", taxable_income=150000, residency="foreign")["total_liability"] == approx(46050)


def test_whm_2025_26():
    # 6,750 + 0.30 x (50,000 - 45,000) = 8,250; no LITO or levy
    out = calc("2025-26", taxable_income=50000, residency="whm")
    assert out["total_liability"] == approx(8250)


# ---------------------------------------------------------------- refusals, validation, draft

@pytest.mark.parametrize("payload,code", [
    ({"taxable_income": 50000, "special_circumstances": ["deceased_estate"]}, "AU-IND-001"),
    ({"taxable_income": 50000, "special_circumstances": ["minor_unearned_income"]}, "AU-IND-001"),
    ({"taxable_income": 50000, "sapto_eligible": True}, "AU-IND-002"),
    ({"taxable_income": 90000, "residency": "foreign", "has_help_debt": True}, "AU-IND-003"),
    ({"taxable_income": 30000, "residency": "whm", "whm_tax_resident": True}, "AU-IND-004"),
])
def test_scope_refusals(payload, code):
    exit_code, out = run("individual_income_tax", "2025-26", payload)
    assert exit_code == 3
    assert out["refusal"]["code"] == code
    assert out["refusal"]["message"]


def test_invalid_inputs():
    assert run("individual_income_tax", "2025-26", {"taxable_income": 50000, "residency": "foreign",
                                                     "resident_months": 6})[0] == 2
    assert run("individual_income_tax", "2025-26", {"taxable_income": -1})[0] == 2
    assert run("individual_income_tax", "2025-26", {"taxable_income": 1, "spouse_taxable_income": 5})[0] == 2


def _figures_with_unverified_levy_rate(allow_draft):
    f = Figures("2025-26", allow_draft=allow_draft)
    f.data = copy.deepcopy(f.data)  # never mutate the cached year
    f.data["medicare"]["levy_rate"]["status"] = "SOURCE-CITED"
    return f


def test_draft_mode_marks_output():
    inp = IndividualTaxInput(taxable_income=90000)
    with pytest.raises(FigureError):
        individual_income_tax(_figures_with_unverified_levy_rate(False), inp)
    f = _figures_with_unverified_levy_rate(True)
    out = individual_income_tax(f, inp)
    assert out["medicare_levy"] == approx(1800)
    assert f.draft is True


def test_taxable_income_cents_ignored_before_rates():
    # ATO assesses on whole dollars. 2026-27, taxable income $100,000.99 -> $100,000:
    #   tax = 4,020 (15% x 26,800 on 18,201..45,000) + 30% x (100,000 - 45,000) = 4,020 + 16,500 = 20,520
    #   Medicare levy = 2% x 100,000 = 2,000; total 22,520 (unrounded cents would add about 0.32)
    code, out = run("individual_income_tax", "2026-27", {"taxable_income": 100000.99})
    assert code == 0
    assert out["taxable_income"] == 100000
    assert out["total_liability"] == pytest.approx(22520, abs=0.001)
    assert any("rounded down to whole dollars" in a for a in out["assumptions"])


# ITAA 1997 s 25-130, Act 49 of 2026 Sch 4 items 3 and 17.
# Independent arithmetic: max(0, min(cap, qualifying labour income) - reducing deductions).
@pytest.mark.parametrize("labour,deductions,expected", [
    (60000, 0, 1000), (60000, 300, 700), (60000, 1000, 0),
    (60000, 1800, 0), (400, 0, 400), (400, 150, 250), (0, 0, 0),
])
def test_standard_work_deduction_top_up(labour, deductions, expected):
    code, out = run("standard_work_deduction", "2026-27", {
        "resident_at_any_time": True, "assessable_labour_income": labour,
        "reducing_deductions": deductions,
    })
    assert code == 0, out
    assert out["additional_deduction"] == expected
    if labour:
        assert out["figures_used"][0]["key"] == "individual.standard_work_deduction_cap"
    else:
        assert out["figures_used"] == []


@pytest.mark.parametrize("year,resident", [("2025-26", True), ("2026-27", False)])
def test_standard_work_deduction_not_eligible(year, resident):
    code, out = run("standard_work_deduction", year, {
        "resident_at_any_time": resident, "assessable_labour_income": 60000,
        "reducing_deductions": 0,
    })
    assert code == 0, out
    assert out["additional_deduction"] == 0
    assert out["eligible"] is False
    assert out["figures_used"] == []  # Never read a later-year cap into 2025-26.


def test_standard_work_deduction_missing_eligibility_or_negative_input():
    for payload in [
        {"assessable_labour_income": 60000, "reducing_deductions": 0},
        {"resident_at_any_time": True, "assessable_labour_income": 60000, "reducing_deductions": -1},
    ]:
        code, _ = run("standard_work_deduction", "2026-27", payload)
        assert code == 2


def test_standard_work_deduction_figure_verification():
    from au_tax.calculators.individual import StandardWorkDeductionInput, standard_work_deduction
    f = Figures("2026-27")
    f.data = copy.deepcopy(f.data)
    f.data["individual"]["standard_work_deduction_cap"]["status"] = "SOURCE-CITED"
    inp = StandardWorkDeductionInput(resident_at_any_time=True, assessable_labour_income=60000,
                                     reducing_deductions=0)
    with pytest.raises(FigureError, match="SOURCE-CITED"):
        standard_work_deduction(f, inp)
    f.allow_draft = True
    assert standard_work_deduction(f, inp)["additional_deduction"] == 1000
    assert f.draft
    f.data["individual"]["standard_work_deduction_cap"]["value"] = None
    with pytest.raises(FigureError, match="no published value"):
        standard_work_deduction(f, inp)


def test_standard_work_deduction_assembly_handoff_once():
    # 60,000 wages, 300 substantiated reducing costs, 200 association dues (s25-130(3)
    # excluded from reducing deductions), 700 top-up: taxable income = 58,800.
    code, deduction = run("standard_work_deduction", "2026-27", {
        "resident_at_any_time": True, "assessable_labour_income": 60000, "reducing_deductions": 300,
    })
    assert code == 0
    code, assembled = run("assemble_taxable_income", "2026-27", {"components": [
        {"kind": "salary_wages", "amount": 60000, "source_skill": "user"},
        {"kind": "work_related_deduction", "amount": 500, "source_skill": "user"},
        {"kind": "work_related_deduction", "amount": deduction["additional_deduction"],
         "source_skill": "individual-tax", "source_tool": "standard_work_deduction"},
    ]})
    assert code == 0
    assert assembled["taxable_income"] == 58800
    # Independent tax: (45,000-18,200)*.15 + (58,800-45,000)*.30 = 8,160;
    # LITO = 325-(58,800-45,000)*.015 = 118; levy = 1,176; total = 9,218.
    out = calc("2026-27", taxable_income=assembled["taxable_income"], private_hospital_cover=True)
    assert out["total_liability"] == approx(9218)


@pytest.mark.parametrize('year,payload,limitation,status', [
    ('2025-26', {'taxable_income': 120000}, 'hospital_cover_not_stated', 'conditional'),
    ('2025-26', {'taxable_income': 29000, 'has_spouse': True, 'spouse_taxable_income': 29000,
                 'dependent_children': 1, 'private_hospital_cover': True}, 'spouse_levy_excess', 'incomplete'),
    ('2027-28', {'taxable_income': 120000, 'private_hospital_cover': True}, 'net_labour_income_not_stated', 'incomplete'),
    ('2025-26', {'taxable_income': 40000, 'dependent_children': 1, 'private_hospital_cover': True},
     'sole_parent_family_tax_benefit', 'conditional'),
    ('2025-26', {'taxable_income': 120000, 'resident_months': 6, 'private_hospital_cover': True},
     'estimated_exemption_days', 'conditional'),
    ('2025-26', {'taxable_income': 150000, 'has_spouse': True, 'spouse_taxable_income': 100000,
                 'private_hospital_cover': False}, 'spouse_mls_income_assumed', 'conditional'),
    ('2025-26', {'taxable_income': 120000, 'has_help_debt': True, 'private_hospital_cover': True},
     'help_balance_not_stated', 'conditional'),
])
def test_total_limitations(year, payload, limitation, status):
    out = calc(year, **payload)
    assert out['total_complete'] is False
    assert out['total_status'] == status
    assert limitation in {item['id'] for item in out['limitations']}
    assert all('total_liability' in item['affects'] for item in out['limitations'])


def test_clean_total_is_complete_within_modelled_scope():
    out = calc('2025-26', taxable_income=45000, private_hospital_cover=True)
    assert out['total_complete'] is True
    assert out['total_status'] == 'complete'
    assert out['limitations'] == []
    assert out['total_liability'] == 4863


def test_mls_unknown_cover_boundary_only_flags_possible_surcharge():
    at = calc('2025-26', taxable_income=101000)
    above = calc('2025-26', taxable_income=101001)
    assert at['total_complete'] is True
    assert above['total_complete'] is False
    assert above['limitations'][0]['id'] == 'hospital_cover_not_stated'


@pytest.mark.parametrize('payload', [
    {'taxable_income': 120000, 'private_hospital_cover': True, 'has_help_debt': True, 'help_debt_balance': 1000},
    {'taxable_income': 120000, 'private_hospital_cover': True, 'resident_months': 6,
     'medicare_full_exemption_days': 182},
    {'taxable_income': 150000, 'private_hospital_cover': False, 'has_spouse': True,
     'spouse_taxable_income': 100000, 'spouse_income_for_mls': 100000},
    {'taxable_income': 45000, 'private_hospital_cover': True},
])
def test_stated_inputs_remove_conditional_limitations(payload):
    assert calc('2025-26', **payload)['total_complete'] is True


def test_unknown_cover_with_unpublished_tiers_is_conditional():
    out = calc('2027-28', taxable_income=120000, net_labour_income=120000)
    assert out['total_status'] == 'conditional'
    assert out['limitations'][0]['id'] == 'hospital_cover_not_stated'


def test_foreign_resident_missing_cover_is_not_a_limitation():
    assert calc('2025-26', taxable_income=120000, residency='foreign')['total_complete'] is True


def test_spouse_mls_assumption_remains_conditional_below_family_tier():
    # Stated taxable incomes are below the family tier, but unstated spouse MLS add-backs
    # could move the family into a surcharge tier.
    out = calc('2025-26', taxable_income=120000, has_spouse=True,
               spouse_taxable_income=50000, private_hospital_cover=False)
    assert out['medicare_levy_surcharge'] == 0
    assert out['total_status'] == 'conditional'
    assert out['limitations'][0]['id'] == 'spouse_mls_income_assumed'
