"""residency-cross-border calculators. Expected values come from the ATO FITO guide worked example, the
Australia-Indonesia treaty text, TR 2023/1, or hand computation shown step by step. None were produced by
running the calculators."""

import pytest

from au_tax.calculators.residency import offset_limit_amount
from au_tax.registry import load_all, run


def ok(name, year, **kw):
    code, out = run(name, year, kw)
    assert code == 0, out
    return out


def approx(x):
    return pytest.approx(x, abs=0.01)


def test_registered_as_tools():
    tools = load_all()
    for t in ("foreign_income_tax_offset", "residency_indicators", "indonesia_dta_check", "cross_border_scope_check"):
        assert t in tools


# ------------------------------------------------------------------ FITO limit

def test_limit_formula_ato_example_16():
    # ATO FITO guide 2024 Example 16 (Anna): step 1 tax 3,079.30; step 2 tax 309.70;
    # limit = 3,079.30 - 309.70 = 2,769.60 (greater than the default 1,000). Foreign tax paid 3,400 -> offset 2,769.60.
    limit = offset_limit_amount(1000, 3079.30, 309.70)
    assert limit == approx(2769.60)
    assert min(3400, limit) == approx(2769.60)


def test_limit_formula_default_wins_when_computed_smaller():
    # computed 600 < default 1,000 -> limit is the default
    assert offset_limit_amount(1000, 5600, 5000) == 1000


def test_fito_below_default_limit_no_computation():
    # 60,000 taxable, foreign tax 900 (<= default limit 1,000): whole 900 is the offset (s 770-75 Note 1).
    # Tax payable 2025-26: 4,288 + 0.30 x (60,000 - 45,000) = 8,788; levy 2% = 1,200; total 9,988.
    # LITO at 60,000 = 325 (at 45,000) - 0.015 x (60,000 - 45,000) = 325 - 225 = 100. After LITO 9,888. After FITO 9,888 - 900 = 8,988.
    out = ok("foreign_income_tax_offset", "2025-26", foreign_tax_paid=900, taxable_income=60000, private_hospital_cover=True)
    assert out["offset_after_limit"] == approx(900)
    assert out["computed_limit"] is None
    assert out["tax_payable_after_lito_before_fito"] == approx(9888)
    assert out["tax_payable_after_fito"] == approx(8988)
    assert out["foreign_tax_lost"] == 0


def test_fito_computed_limit_above_tax_paid_2025_26():
    # taxable 100,000 incl. 20,000 net foreign income; foreign tax paid 6,000.
    # Step 1: 4,288 + 0.30 x 55,000 = 20,788; levy 2,000; = 22,788.
    # Step 2 (taxable 80,000): 4,288 + 0.30 x 35,000 = 14,788; levy 1,600; = 16,388.
    # Limit = 22,788 - 16,388 = 6,400 > 6,000 -> offset 6,000.
    out = ok("foreign_income_tax_offset", "2025-26", foreign_tax_paid=6000, taxable_income=100000,
             foreign_net_income=20000, private_hospital_cover=True)
    assert out["tax_payable_step1"] == approx(22788)
    assert out["tax_payable_step2"] == approx(16388)
    assert out["computed_limit"] == approx(6400)
    assert out["offset_limit"] == approx(6400)
    assert out["offset_after_limit"] == approx(6000)
    assert out["tax_payable_after_fito"] == approx(16788)


def test_fito_limit_binds_2025_26():
    # same as above but foreign tax paid 7,000 -> limited to 6,400; 600 lost.
    out = ok("foreign_income_tax_offset", "2025-26", foreign_tax_paid=7000, taxable_income=100000,
             foreign_net_income=20000, private_hospital_cover=True)
    assert out["offset_after_limit"] == approx(6400)
    assert out["foreign_tax_lost"] == approx(600)
    assert any("lost" in w for w in out["warnings"])


def test_fito_limit_across_brackets_2025_26():
    # taxable 140,000 incl. 20,000 foreign. Step 1: 31,288 + 0.37 x 5,000 = 33,138; levy 2,800; = 35,938.
    # Step 2 (120,000): 4,288 + 0.30 x 75,000 = 26,788; levy 2,400; = 29,188. Limit = 6,750
    # (check: 0.37x5,000 + 0.30x15,000 + 0.02x20,000 = 1,850 + 4,500 + 400 = 6,750).
    out = ok("foreign_income_tax_offset", "2025-26", foreign_tax_paid=9000, taxable_income=140000,
             foreign_net_income=20000, private_hospital_cover=True)
    assert out["computed_limit"] == approx(6750)
    assert out["offset_after_limit"] == approx(6750)


def test_fito_2026_27_rates():
    # 2026-27: second bracket 15%, third 4,020 + 30%. Taxable 100,000, foreign 30,000, tax paid 10,000.
    # Step 1: 4,020 + 0.30 x 55,000 = 20,520; levy 2,000 -> 22,520.
    # Step 2 (70,000): 4,020 + 0.30 x 25,000 = 11,520; levy 1,400 -> 12,920. Limit = 9,600 < 10,000.
    out = ok("foreign_income_tax_offset", "2026-27", foreign_tax_paid=10000, taxable_income=100000,
             foreign_net_income=30000, private_hospital_cover=True)
    assert out["income_year"] == "2026-27"
    assert out["computed_limit"] == approx(9600)
    assert out["offset_after_limit"] == approx(9600)


def test_fito_claim_default_limit_only():
    out = ok("foreign_income_tax_offset", "2025-26", foreign_tax_paid=6000, taxable_income=100000,
             foreign_net_income=20000, claim_default_limit_only=True, private_hospital_cover=True)
    assert out["offset_after_limit"] == approx(1000)
    assert out["foreign_tax_lost"] == approx(5000)


def test_fito_cannot_exceed_tax_payable():
    # taxable 25,000 all foreign. Gross 0.16 x (25,000 - 18,200) = 1,088. LITO 700 (full to 37,500) -> 388.
    # Levy nil (25,000 <= 28,011 lower threshold). Step 2 taxable 0 -> nil tax. Computed limit 1,088 > default.
    # Foreign tax 2,000 -> limit 1,088; usable = min(1,088, 388) = 388 (non-refundable); 1,612 lost.
    out = ok("foreign_income_tax_offset", "2025-26", foreign_tax_paid=2000, taxable_income=25000,
             foreign_net_income=25000, private_hospital_cover=True)
    assert out["computed_limit"] == approx(1088)
    assert out["offset_after_limit"] == approx(1088)
    assert out["tax_payable_after_lito_before_fito"] == approx(388)
    assert out["offset_usable_against_tax"] == approx(388)
    assert out["tax_payable_after_fito"] == 0
    assert out["foreign_tax_lost"] == approx(1612)


def test_fito_refuses_special_cases():
    code, out = run("foreign_income_tax_offset", "2025-26",
                    {"foreign_tax_paid": 5000, "taxable_income": 90000, "complications": ["jpda_income"]})
    assert code == 3 and out["refusal"]["code"] == "AU-RES-005"


def test_fito_invalid_net_income():
    code, _ = run("foreign_income_tax_offset", "2025-26", {"foreign_tax_paid": 5, "taxable_income": 100, "foreign_net_income": 200})
    assert code == 2


def test_fito_uses_verified_default_limit_figure():
    out = ok("foreign_income_tax_offset", "2025-26", foreign_tax_paid=500, taxable_income=60000, private_hospital_cover=True)
    keys = {f["key"]: f for f in out["figures_used"]}
    assert keys["residency.fito_default_offset_limit"]["value"] == 1000
    assert out["draft"] is False


# ------------------------------------------------------------------ residency indicators

def test_arriving_settled_is_likely_resident():
    # Arrived, home, family, job and assets in Australia, intends to settle, 250 days: presence 2 + home 2 + family 2 +
    # intention 2 + employment 1 + assets 1 = 10 vs 0. 250 >= 183 and no overseas-abode exception.
    out = ok("residency_indicators", "2025-26", days_in_australia=250, prior_year_resident=False, movement="arriving",
             home="australia", family="australia", employment="australia", assets="australia", intention="settle_australia")
    assert out["tests"]["resides_ordinary_concepts"]["status"] == "likely_met"
    assert out["tests"]["days_183"]["status"] == "likely_met"
    assert out["overall"] == "likely_resident"
    assert out["is_determination"] is False
    assert "escalation" not in out
    assert any("part-year" in n.lower() for n in out["notes"])


def test_days_needed_is_more_than_half_of_year():
    # 2025-26 has 365 days (1 Jul 2025 to 30 Jun 2026): more than half = 183. 182 days fails, 183 passes.
    a = ok("residency_indicators", "2025-26", days_in_australia=182, intention="settle_australia")
    b = ok("residency_indicators", "2025-26", days_in_australia=183, intention="settle_australia")
    assert a["days_needed_for_183_test"] == 183
    assert a["tests"]["days_183"]["status"] == "likely_not_met"
    assert b["tests"]["days_183"]["status"] == "likely_met"


def test_working_holiday_visitor_is_likely_non_resident():
    # TR 2023/1 Example 15 shape: WHM works casually, home and family overseas, visiting only.
    # presence 2 + employment 1 = 3 (australia); home 2 + family 2 + intention 2 + assets 1 = 7 (overseas); 7 - 3 = 4 >= 3.
    out = ok("residency_indicators", "2025-26", days_in_australia=300, prior_year_resident=False, home="overseas",
             family="overseas", employment="australia", assets="overseas", intention="visit_only",
             domicile="overseas", usual_place_of_abode_overseas=True, working_holiday_visa=True, temporary_visa_holder=True,
             spouse_australian_resident=False)
    assert out["tests"]["resides_ordinary_concepts"]["status"] == "likely_not_met"
    assert out["tests"]["days_183"]["status"] == "likely_not_met"  # exception applies
    assert out["tests"]["domicile"]["status"] == "likely_not_met"
    assert out["overall"] == "likely_non_resident"
    assert out["temporary_resident"] == "likely_temporary_resident"
    assert any("AU-IND-004" in n for n in out["notes"])


def test_departing_with_permanent_move_is_likely_non_resident():
    # Australian domicile but home, family and job overseas, indefinite stay of 36 months (>= 24): overseas 2+2+2+1 = 7,
    # australia 1 (assets). Presence neutral (previous resident). 7 - 1 = 6 >= 4. Domicile proviso (para 63-82) applies.
    out = ok("residency_indicators", "2025-26", days_in_australia=20, prior_year_resident=True, movement="departing",
             home="overseas", family="overseas", employment="overseas", assets="australia",
             intention="stay_overseas_indefinitely", domicile="australia", planned_overseas_stay_months=36)
    assert out["tests"]["resides_ordinary_concepts"]["status"] == "likely_not_met"
    assert out["tests"]["domicile"]["status"] == "likely_not_met"
    assert out["overall"] == "likely_non_resident"
    assert any("does not end on the departure date" in n for n in out["notes"])


def test_two_homes_australian_domicile_leans_resident():
    # Adelaide and Bali homes, spouse in Adelaide, intends to return: australia = home 2 + family 2 + intention 2 +
    # employment 1 + assets 1 = 8; overseas = home 2 + employment 1 = 3. 8 - 3 = 5 >= 4 -> resides likely met.
    # Domicile: Australian, home in both -> permanent place of abode not overseas (para 67) -> likely met.
    out = ok("residency_indicators", "2026-27", days_in_australia=150, prior_year_resident=True, home="both",
             family="australia", employment="both", assets="australia", intention="return_to_australia_foreseen",
             domicile="australia")
    assert out["tests"]["resides_ordinary_concepts"]["status"] == "likely_met"
    assert out["tests"]["domicile"]["status"] == "likely_met"
    assert out["tests"]["days_183"]["status"] == "likely_not_met"
    assert out["overall"] == "likely_resident"


def test_conflicting_facts_return_uncertain_escalate():
    # Foreign domicile, 120 days, home/family/employment/assets in both places, intention unsure, not previously resident.
    # australia: home 2 + family 2 + employment 1 + assets 1 = 6; overseas: 6 + presence 1 = 7. Both >= 3, gap 1 < 4 -> conflict.
    out = ok("residency_indicators", "2025-26", days_in_australia=120, prior_year_resident=False, home="both",
             family="both", employment="both", assets="both", intention="unsure", domicile="overseas")
    assert out["conflicting_indicators"] is True
    assert out["overall"] == "uncertain_escalate"
    assert out["escalation"]["code"] == "AU-RES-004"
    assert out["is_determination"] is False


def test_missing_facts_are_uncertain_and_listed():
    out = ok("residency_indicators", "2025-26", days_in_australia=100)
    assert out["overall"] == "uncertain_escalate"
    for f in ("home", "family", "employment", "assets", "intention", "prior_year_resident"):
        assert f in out["missing_facts"]


def test_commonwealth_super_member_is_resident():
    out = ok("residency_indicators", "2025-26", days_in_australia=0, home="overseas", family="overseas",
             commonwealth_super_member=True)
    assert out["tests"]["commonwealth_super"]["status"] == "likely_met"
    assert out["overall"] == "likely_resident"


def test_temporary_resident_note_only_with_visa():
    out = ok("residency_indicators", "2025-26", days_in_australia=365, temporary_visa_holder=True, spouse_australian_resident=False,
             home="australia", family="australia", employment="australia", assets="australia", intention="settle_australia")
    assert out["temporary_resident"] == "likely_temporary_resident"
    assert "s 768-910" in out["temporary_resident_note"]
    out2 = ok("residency_indicators", "2025-26", days_in_australia=365, temporary_visa_holder=True, spouse_australian_resident=True)
    assert out2["temporary_resident"] == "not_temporary_resident"


# ------------------------------------------------------------------ Indonesia treaty

def test_art14_days_threshold_is_120_not_183():
    # Art 14(1)(b): presence "exceeding 120 days in any period of 12 months" -> 121 may be taxed in the other state.
    over = ok("indonesia_dta_check", "2025-26", article="independent_services", residence_state="australia",
              days_in_other_state_12m=121, fixed_base_available=False)
    assert over["other_state_may_tax"] is True
    at = ok("indonesia_dta_check", "2025-26", article="independent_services", residence_state="australia",
            days_in_other_state_12m=120, fixed_base_available=False)
    assert at["other_state_may_tax"] is False
    assert at["days_threshold"] == 120


def test_art14_fixed_base_alone_gives_other_state_taxing_right():
    out = ok("indonesia_dta_check", "2025-26", article="independent_services", residence_state="australia",
             days_in_other_state_12m=30, fixed_base_available=True)
    assert out["other_state_may_tax"] is True


def test_art15_exemption_needs_all_four_conditions():
    base = dict(article="employment", residence_state="australia", days_in_other_state_12m=120,
                employer_resident_in_work_state=False, remuneration_borne_by_pe_or_fixed_base=False,
                remuneration_taxed_in_residence_state=True)
    assert ok("indonesia_dta_check", "2025-26", **base)["taxable_only_in_residence_state"] is True
    assert ok("indonesia_dta_check", "2025-26", **{**base, "days_in_other_state_12m": 121})["other_state_may_tax"] is True
    assert ok("indonesia_dta_check", "2025-26", **{**base, "employer_resident_in_work_state": True})["other_state_may_tax"] is True
    assert ok("indonesia_dta_check", "2025-26", **{**base, "remuneration_borne_by_pe_or_fixed_base": True})["other_state_may_tax"] is True
    assert ok("indonesia_dta_check", "2025-26", **{**base, "remuneration_taxed_in_residence_state": False})["other_state_may_tax"] is True


def test_art15_missing_fact_gives_no_answer():
    out = ok("indonesia_dta_check", "2025-26", article="employment", residence_state="australia", days_in_other_state_12m=90)
    assert out["taxable_only_in_residence_state"] is None


def test_withholding_limits():
    # Arts 10(2), 11(2), 12(2): dividends 15%, interest 10%, royalties 10% (equipment, know-how) or 15% (other). On 10,000: 1,500 / 1,000 / 1,000 / 1,500.
    d = ok("indonesia_dta_check", "2025-26", article="dividends", gross_amount=10000)
    i = ok("indonesia_dta_check", "2025-26", article="interest", gross_amount=10000)
    r1 = ok("indonesia_dta_check", "2025-26", article="royalties", royalty_type="equipment_or_know_how", gross_amount=10000)
    r2 = ok("indonesia_dta_check", "2025-26", article="royalties", royalty_type="other", gross_amount=10000)
    assert (d["source_state_tax_limit_rate"], d["source_state_tax_limit_amount"]) == (0.15, 1500)
    assert (i["source_state_tax_limit_rate"], i["source_state_tax_limit_amount"]) == (0.10, 1000)
    assert (r1["source_state_tax_limit_rate"], r1["source_state_tax_limit_amount"]) == (0.10, 1000)
    assert (r2["source_state_tax_limit_rate"], r2["source_state_tax_limit_amount"]) == (0.15, 1500)


def test_royalty_needs_type():
    code, out = run("indonesia_dta_check", "2025-26", {"article": "royalties", "gross_amount": 100})
    assert code == 3 and out["refusal"]["code"] == "AU-RES-001"


def _assert_indication_only(out):
    # A tie-breaker result is never a determination: no conclusion-style field, the facts that could change it are listed,
    # and the tie-breaker determination (AU-RES-001) and Indonesian domestic residence (AU-IDN-002) escalations are raised.
    assert "deemed_resident_solely_of" not in out
    assert out["indication_only"] is True
    assert out["missing_facts"] and any("Indonesian domestic" in m for m in out["missing_facts"])
    codes = [e["code"] for e in out["escalations"]]
    assert "AU-RES-001" in codes and "AU-IDN-002" in codes
    assert all(e["message"] for e in out["escalations"])
    assert any("indication" in w.lower() for w in out["warnings"])


def test_tie_breaker_permanent_home_decides():
    out = ok("indonesia_dta_check", "2025-26", article="residence_tie_breaker", resident_of_both_states_under_domestic_law=True,
             permanent_home_australia=True, permanent_home_indonesia=False)
    assert out["indicated_resident_state"] == "australia"
    _assert_indication_only(out)


def test_tie_breaker_two_homes_falls_to_habitual_abode_then_relations():
    a = ok("indonesia_dta_check", "2025-26", article="residence_tie_breaker", resident_of_both_states_under_domestic_law=True,
           permanent_home_australia=True, permanent_home_indonesia=True, habitual_abode="indonesia")
    assert a["indicated_resident_state"] == "indonesia"
    _assert_indication_only(a)
    b = ok("indonesia_dta_check", "2025-26", article="residence_tie_breaker", resident_of_both_states_under_domestic_law=True,
           permanent_home_australia=True, permanent_home_indonesia=True, habitual_abode="both", closer_relations="australia")
    assert b["indicated_resident_state"] == "australia"
    _assert_indication_only(b)
    assert len(b["steps"]) == 3  # homes, habitual abode, relations: no nationality step


def test_tie_breaker_unclear_relations_escalates():
    code, out = run("indonesia_dta_check", "2025-26", {
        "article": "residence_tie_breaker", "resident_of_both_states_under_domestic_law": True,
        "permanent_home_australia": True, "permanent_home_indonesia": True, "habitual_abode": "both", "closer_relations": "unclear"})
    assert code == 3 and out["refusal"]["code"] == "AU-RES-001"


def test_tie_breaker_not_dual_resident_does_not_apply():
    out = ok("indonesia_dta_check", "2025-26", article="residence_tie_breaker", resident_of_both_states_under_domestic_law=False)
    assert out["applies"] is False


def test_other_treaty_country_refused():
    code, out = run("indonesia_dta_check", "2025-26", {"article": "dividends", "treaty_country": "Singapore", "gross_amount": 1})
    assert code == 3 and out["refusal"]["code"] == "AU-RES-001"


# ------------------------------------------------------------------ scope check

@pytest.mark.parametrize("situation,code", [
    ("controlled_foreign_company", "AU-RES-002"), ("foreign_trust", "AU-RES-002"), ("offshore_company_controlled", "AU-RES-002"),
    ("foreign_super_transfer", "AU-RES-003"), ("foreign_pension", "AU-RES-003"),
    ("other_treaty_country", "AU-RES-001"), ("dual_resident_conflicting_facts", "AU-RES-001"),
])
def test_scope_check_refuses(situation, code):
    c, out = run("cross_border_scope_check", "2025-26", {"situations": [situation]})
    assert c == 3 and out["refusal"]["code"] == code
    assert out["refusal"]["message"]


def test_scope_check_in_scope():
    out = ok("cross_border_scope_check", "2025-26", situations=[])
    assert out["in_scope"] is True


def test_tie_breaker_let_out_home_flags_availability_fact():
    # A home let to unrelated guests most of the year may not be "available" (OECD Commentary Art 4 para 13, an interpretive aid).
    out = ok("indonesia_dta_check", "2025-26", article="residence_tie_breaker", resident_of_both_states_under_domestic_law=True,
             permanent_home_australia=True, permanent_home_indonesia=False)
    assert any("available" in m for m in out["missing_facts"])


def test_tie_breaker_domestic_residence_unconfirmed_still_listed():
    out = ok("indonesia_dta_check", "2025-26", article="residence_tie_breaker")
    assert out["applies"] is False
    assert any("Indonesian domestic" in m for m in out["missing_facts"])
    assert "AU-IDN-002" in [e["code"] for e in out["escalations"]]
