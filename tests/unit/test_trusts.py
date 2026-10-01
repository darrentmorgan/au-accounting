"""trust_distribution_shares, div6aa_minor_tax, partnership_shares. Expected values come from ATO worked
examples (cited) or hand computation shown step by step. None were produced by running the calculators."""

import pytest

from au_tax.registry import load_all, run


def ok(name, year, **kw):
    code, out = run(name, year, kw)
    assert code == 0, out
    return out


def approx(x):
    return pytest.approx(x, abs=0.01)


def ben(out, name):
    return next(b for b in out["beneficiaries"] if b["name"] == name)


def test_registered():
    assert {"trust_distribution_shares", "div6aa_minor_tax", "partnership_shares"} <= set(load_all())


# ================================================================ trust distribution shares

def test_ato_lang_trust_franked_streaming_example():
    # ATO "Calculating shares of the franked distribution and attached franking credit" (Lang Trust):
    # rental 100,000 - 20,000 expenses + franked 70,000 => trust income 150,000; net income 180,000 (incl. 30,000 FC).
    # Hannah specifically entitled to 50,000 of the franked distribution, total PE 75,000; Lucy PE 75,000.
    # Adjusted trust income = 150,000 - 50,000 = 100,000. Hannah 25,000/100,000 = 25%; Lucy 75%.
    # Franked shares: Hannah 50,000 + 25% x 20,000 = 55,000; Lucy 15,000. FC: 30,000 x 55/70 = 23,571.43; Lucy 6,428.57.
    # Ordinary (adjusted) net income = 180,000 - 70,000 - 30,000 = 80,000 -> Hannah 20,000, Lucy 60,000.
    for year in ("2025-26", "2026-27"):
        out = ok("trust_distribution_shares", year, net_income=180000, trust_income=150000,
                 franked_distributions=70000, franking_credits=30000, resolution_by_30_june=True,
                 beneficiaries=[{"name": "Hannah", "present_entitlement": 75000, "specific_franked_distribution": 50000},
                                {"name": "Lucy", "present_entitlement": 75000}])
        h, lu = ben(out, "Hannah"), ben(out, "Lucy")
        assert h["adjusted_division_6_percentage"] == approx(25)
        assert lu["adjusted_division_6_percentage"] == approx(75)
        assert h["attributable_franked_distribution"] == approx(55000)
        assert lu["attributable_franked_distribution"] == approx(15000)
        assert h["franking_credit"] == approx(23571.43)
        assert lu["franking_credit"] == approx(6428.57)
        # ATO: Hannah's assessable franked amount 78,571; Lucy 21,429 (plus Div 6 shares of other income)
        assert h["attributable_franked_distribution"] + h["franking_credit"] == approx(78571.43)
        assert h["share_of_ordinary_net_income"] == approx(20000)
        assert lu["share_of_ordinary_net_income"] == approx(60000)
        assert out["trustee"]["s99a_amount"] == 0
        assert out["total_assessed_check"] == approx(180000)
        assert "s100a-red-zone-4-screen" not in out["risk_flags"]  # franking credit gross-up is not a mismatch


def test_proportionate_approach_with_unallocated_income_2025_26():
    # Net income 100,000; trust income 50,000. A entitled to 25,000 (50%), B to 15,000 (30%); 10,000 (20%) unallocated.
    # Bamford proportionate approach: A = 50% x 100,000 = 50,000; B = 30,000; trustee s99A on 20% = 20,000.
    # s99A tax = 45% x 20,000 = 9,000; Medicare levy 2% x 20,000 = 400; total 9,400.
    out = ok("trust_distribution_shares", "2025-26", net_income=100000, trust_income=50000, resolution_by_30_june=True,
             beneficiaries=[{"name": "A", "present_entitlement": 25000}, {"name": "B", "present_entitlement": 15000}])
    assert ben(out, "A")["total_assessed"] == approx(50000)
    assert ben(out, "B")["total_assessed"] == approx(30000)
    t = out["trustee"]
    assert t["s99a_amount"] == approx(20000)
    assert t["s99a_tax"] == approx(9000)
    assert t["medicare_levy"] == approx(400)
    assert t["s99a_tax_and_medicare"] == approx(9400)
    assert "s99a-unallocated-income" in out["risk_flags"]


def test_capital_gain_streamed_in_trust_income():
    # Ordinary net income 100,000; capital gain 100,000 discounted by the trust -> net capital gain 50,000; NI 150,000.
    # Deed includes capital gains in income: trust income 200,000. Bob specifically entitled to the 100,000 gain
    # (PE 100,000); Alice PE 50,000; Carol PE 50,000. Adjusted TI = 200,000 - 100,000 = 100,000 -> Alice 50%, Carol 50%, Bob 0%.
    # Adjusted NI = 150,000 - 50,000 = 100,000 -> Alice 50,000, Carol 50,000.
    # Bob: share of gain 100% -> attributable 50,000, grossed up to 100,000 (s115-215).
    out = ok("trust_distribution_shares", "2026-27", net_income=150000, trust_income=200000, net_capital_gain=50000,
             cgt_discount_applied=True, resolution_by_30_june=True,
             beneficiaries=[{"name": "Bob", "present_entitlement": 100000, "specific_capital_gain": 100000},
                            {"name": "Alice", "present_entitlement": 50000}, {"name": "Carol", "present_entitlement": 50000}])
    b = ben(out, "Bob")
    assert b["adjusted_division_6_percentage"] == approx(0)
    assert b["attributable_capital_gain"] == approx(50000)
    assert b["capital_gain_grossed_up"] == approx(100000)
    assert b["total_assessed"] == approx(50000)
    assert ben(out, "Alice")["total_assessed"] == approx(50000)
    assert ben(out, "Carol")["total_assessed"] == approx(50000)
    assert out["trustee"]["s99a_amount"] == approx(0)


def test_unstreamed_capital_gain_follows_percentage_and_trustee_share():
    # Ordinary NI 40,000 + non-discounted capital gain 20,000 (not trust income) -> NI 60,000; trust income 40,000.
    # A entitled to 30,000 = 75%; trustee 25%.
    # A: 75% x 40,000 = 30,000 + 75% x 20,000 gain = 15,000 -> 45,000.
    # Trustee: 10,000 + 5,000 = 15,000; s99A tax 45% = 6,750; levy 2% = 300.
    out = ok("trust_distribution_shares", "2025-26", net_income=60000, trust_income=40000, net_capital_gain=20000,
             capital_gains_in_trust_income=False, resolution_by_30_june=True,
             beneficiaries=[{"name": "A", "present_entitlement": 30000}])
    assert ben(out, "A")["attributable_capital_gain"] == approx(15000)
    assert ben(out, "A")["total_assessed"] == approx(45000)
    assert out["trustee"]["s99a_amount"] == approx(15000)
    assert out["trustee"]["s99a_tax"] == approx(6750)
    assert out["trustee"]["medicare_levy"] == approx(300)


def test_no_resolution_by_30_june_trustee_assessed_on_everything():
    # Nobody presently entitled: trustee s99A on all 80,000: tax 36,000 + levy 1,600 = 37,600.
    out = ok("trust_distribution_shares", "2026-27", net_income=80000, trust_income=80000, resolution_by_30_june=False,
             beneficiaries=[{"name": "A", "present_entitlement": 80000}])
    assert ben(out, "A")["total_assessed"] == 0
    assert out["trustee"]["s99a_amount"] == approx(80000)
    assert out["trustee"]["s99a_tax_and_medicare"] == approx(37600)


def test_minor_and_company_beneficiaries_flagged():
    # 50/50 of 20,000: each 10,000. Minor share > 416 -> Div 6AA flag, s98 assessment; company -> Bendel/UPE flag.
    out = ok("trust_distribution_shares", "2025-26", net_income=20000, trust_income=20000, resolution_by_30_june=True,
             beneficiaries=[{"name": "Kid", "kind": "resident_minor", "present_entitlement": 10000},
                            {"name": "Bucket Co", "kind": "resident_company", "present_entitlement": 10000}])
    assert ben(out, "Kid")["total_assessed"] == approx(10000)
    assert "s98" in ben(out, "Kid")["assessed_under"]
    assert "div6aa-minor" in out["risk_flags"]
    assert "corporate-beneficiary-upe" in out["risk_flags"]
    assert any("Bendel" in w for w in out["warnings"])


def test_trust_net_loss_refuses_sch2f():
    # A trust cannot distribute a tax loss and later use depends on the Sch 2F tests (not modelled): refuse, no shares.
    code, out = run("trust_distribution_shares", "2025-26",
                    {"net_income": -5000, "trust_income": 0, "beneficiaries": [{"name": "A", "present_entitlement": 0}]})
    assert code == 3 and out["refusal"]["code"] == "AU-TRUST-004"
    assert "beneficiaries" not in out


def test_trust_nil_net_income_no_shares():
    out = ok("trust_distribution_shares", "2025-26", net_income=0, trust_income=0,
             beneficiaries=[{"name": "A", "present_entitlement": 0}])
    assert out["beneficiaries"] == []


@pytest.mark.parametrize("kind,code", [("deceased_estate", "AU-TRUST-007"), ("foreign", "AU-TRUST-005"),
                                       ("mit_or_amit", "AU-TRUST-006")])
def test_trust_kind_refusals(kind, code):
    c, out = run("trust_distribution_shares", "2025-26", {"net_income": 1000, "trust_income": 1000, "trust_kind": kind})
    assert c == 3 and out["refusal"]["code"] == code


def test_net_income_below_streamed_amounts_refused():
    # NI 30,000 < net capital gain 50,000 -> rateable reduction not modelled
    c, out = run("trust_distribution_shares", "2025-26", {"net_income": 30000, "trust_income": 30000, "net_capital_gain": 50000})
    assert c == 3 and out["refusal"]["code"] == "AU-TRUST-008"


def test_entitlements_exceeding_income_is_invalid():
    c, _ = run("trust_distribution_shares", "2025-26", {"net_income": 1000, "trust_income": 1000,
               "beneficiaries": [{"name": "A", "present_entitlement": 800}, {"name": "B", "present_entitlement": 800}]})
    assert c == 2


# ================================================================ Div 6AA

def test_div6aa_at_threshold_no_div6aa():
    # ETI 416 is not above the threshold (ITRA s13(1)(b)): ordinary rates on 416 -> nil.
    out = ok("div6aa_minor_tax", "2025-26", unearned_income=416)
    assert out["div6aa_applies"] is False
    assert out["income_tax"] == 0


def test_div6aa_phase_in_1000():
    # 66% x (1,000 - 416) = 0.66 x 584 = 385.44 (< 45% x 1,000 = 450). ATO under-18 table 2025-26.
    out = ok("div6aa_minor_tax", "2025-26", unearned_income=1000)
    assert out["div6aa_tax"] == approx(385.44)
    assert out["phase_out_limit"] == 1307  # 416 x 0.66 / (0.66 - 0.45) = 1,307.43 rounded down (s13(10))


def test_div6aa_at_and_above_phase_out():
    # 1,307: 0.66 x 891 = 588.06 vs 0.45 x 1,307 = 588.15 -> 588.06
    assert ok("div6aa_minor_tax", "2025-26", unearned_income=1307)["div6aa_tax"] == approx(588.06)
    # 1,308: above the limit -> 45% of the whole = 588.60
    assert ok("div6aa_minor_tax", "2026-27", unearned_income=1308)["div6aa_tax"] == approx(588.60)


def test_div6aa_trust_distribution_5000_with_job_2025_26():
    # ETI 5,000 -> 45% x 5,000 = 2,250. Excepted wages 10,000 taxed alone: below 18,200 -> nil. LITO 700 cannot
    # reduce the Div 6AA tax (s61-115) -> 0 applied. Medicare: TI 15,000 <= 28,011 -> nil. Total 2,250.
    out = ok("div6aa_minor_tax", "2025-26", unearned_income=5000, excepted_income=10000)
    assert out["div6aa_tax"] == approx(2250)
    assert out["lito_applied"] == 0
    assert out["medicare_levy"] == 0
    assert out["total_tax"] == approx(2250)


def test_div6aa_with_taxable_excepted_income_2025_26():
    # Excepted 30,000: 0.16 x (30,000 - 18,200) = 1,888. LITO on TI 33,000 = 700 (<= 1,888).
    # Div 6AA: 45% x 3,000 = 1,350. Income tax = 1,888 - 700 + 1,350 = 2,538.
    # Medicare: TI 33,000 between 28,011 and 35,013 -> 10% x (33,000 - 28,011) = 498.90 (< 2% x 33,000 = 660).
    # Total 2,538 + 498.90 = 3,036.90.
    out = ok("div6aa_minor_tax", "2025-26", unearned_income=3000, excepted_income=30000)
    assert out["tax_on_other_income"] == approx(1888)
    assert out["lito_applied"] == approx(700)
    assert out["div6aa_tax"] == approx(1350)
    assert out["income_tax"] == approx(2538)
    assert out["medicare_levy"] == approx(498.90)
    assert out["total_tax"] == approx(3036.90)


def test_div6aa_top_slice_cap():
    # ETI 800, excepted 150,000 (2025-26). s13(2): cap = greater of 0.66 x 384 = 253.44 and top-slice tax
    # 0.37 x 800 = 296 (150,000 -> 150,800 all in the 37% band) = 296; less than 0.45 x 800 = 360 -> 296.
    out = ok("div6aa_minor_tax", "2025-26", unearned_income=800, excepted_income=150000)
    assert out["div6aa_tax"] == approx(296)
    assert "top slice" in out["div6aa_basis"]


def test_div6aa_excepted_person_and_adult():
    # Excepted person: ordinary rates on 5,000 -> nil.
    assert ok("div6aa_minor_tax", "2025-26", unearned_income=5000, excepted_person=True)["income_tax"] == 0
    assert ok("div6aa_minor_tax", "2025-26", unearned_income=5000, under_18_on_30_june=False)["div6aa_applies"] is False


def test_div6aa_2026_27_medicare_not_available_but_tax_computed():
    out = ok("div6aa_minor_tax", "2026-27", unearned_income=5000)
    assert out["div6aa_tax"] == approx(2250)
    assert out["medicare_levy"] is None
    assert out["warnings"]


@pytest.mark.parametrize("kw", [{"residency": "non_resident"}, {"shares_from_multiple_trusts": True},
                                {"special_income_component": True}])
def test_div6aa_refusals(kw):
    c, out = run("div6aa_minor_tax", "2025-26", {"unearned_income": 5000, **kw})
    assert c == 3 and out["refusal"]["code"] == "AU-TRUST-009"


# ================================================================ partnerships

def test_tr2005_7_example_1():
    # Profit after Anna's 20,000 salary 35,000 -> net income 55,000. Anna 20,000 + 50% x 35,000 = 37,500; Robert 17,500.
    out = ok("partnership_shares", "2025-26", net_income=35000, partner_appropriations_deducted=20000,
             partners=[{"name": "Anna", "profit_share": 50, "salary": 20000}, {"name": "Robert", "profit_share": 50}])
    p = {r["name"]: r for r in out["partners"]}
    assert out["net_income_or_loss"] == approx(55000)
    assert p["Anna"]["share_of_net_income"] == approx(37500)
    assert p["Robert"]["share_of_net_income"] == approx(17500)


def test_tr2005_7_example_2_salary_exceeds_profit():
    # Loss after salary (10,000) + salary 20,000 -> net income 10,000, all to Christine; 10,000 advance of future profits.
    out = ok("partnership_shares", "2025-26", net_income=-10000, partner_appropriations_deducted=20000,
             partners=[{"name": "Christine", "profit_share": 1, "salary": 20000}, {"name": "Julia", "profit_share": 1}])
    p = {r["name"]: r for r in out["partners"]}
    assert p["Christine"]["share_of_net_income"] == approx(10000)
    assert p["Christine"]["drawings_in_advance_of_profits"] == approx(10000)
    assert p["Julia"]["share_of_net_income"] == 0


def test_tr2005_7_example_3_loss():
    # Loss after salary (30,000) + salary 20,000 -> loss (10,000), shared 50/50: (5,000) each.
    out = ok("partnership_shares", "2026-27", net_income=-30000, partner_appropriations_deducted=20000,
             partners=[{"name": "Christine", "profit_share": 1, "salary": 20000}, {"name": "Julia", "profit_share": 1}])
    p = {r["name"]: r for r in out["partners"]}
    assert out["result"] == "partnership loss"
    assert p["Christine"]["share_of_net_income"] == approx(-5000)
    assert p["Julia"]["share_of_net_income"] == approx(-5000)
    assert p["Christine"]["drawings_in_advance_of_profits"] == approx(20000)


def test_partnership_salary_interest_and_ratio():
    # Income 300,000 - deductions 120,000 = 180,000. Salaries: P1 40,000; interest on capital P1 5,000, P2 10,000.
    # Residual 180,000 - 55,000 = 125,000 shared 60/40: P1 75,000, P2 50,000.
    # P1 = 45,000 + 75,000 = 120,000; P2 = 10,000 + 50,000 = 60,000.
    out = ok("partnership_shares", "2025-26", assessable_income=300000, deductions=120000,
             partners=[{"name": "P1", "profit_share": 0.6, "salary": 40000, "interest_on_capital": 5000},
                       {"name": "P2", "profit_share": 0.4, "interest_on_capital": 10000}])
    p = {r["name"]: r for r in out["partners"]}
    assert p["P1"]["share_of_net_income"] == approx(120000)
    assert p["P2"]["share_of_net_income"] == approx(60000)
    assert out["total_allocated"] == approx(180000)


def test_partnership_loss_ratio():
    # Loss (9,000), loss shares 2:1 -> (6,000) and (3,000).
    out = ok("partnership_shares", "2025-26", net_income=-9000,
             partners=[{"name": "X", "profit_share": 1, "loss_share": 2}, {"name": "Y", "profit_share": 1, "loss_share": 1}])
    p = {r["name"]: r for r in out["partners"]}
    assert p["X"]["share_of_net_income"] == approx(-6000)
    assert p["Y"]["share_of_net_income"] == approx(-3000)


@pytest.mark.parametrize("kw", [{"corporate_limited_partnership": True}, {"partner_changes_during_year": True},
                                {"agreement_before_year_end": False}])
def test_partnership_refusals(kw):
    c, out = run("partnership_shares", "2025-26", {"net_income": 1000, "partners": [{"name": "A", "profit_share": 1}], **kw})
    assert c == 3 and out["refusal"]["code"] == "AU-TRUST-010"
