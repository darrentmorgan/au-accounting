"""Public settlement behaviour; synthetic expectations are computed independently below.

2025-26 ATO resident/LITO/Medicare tables; PHI year/period/age rates in the cited ATO table.
Franking: ITAA 1997 ss207-20, 67-25, 63-10; PAYG: TAA Sch1 ss18-15, 45-30.
"""

import copy

import pytest

from au_tax.figures import Figures
from au_tax.registry import run


def inputs(**updates):
    return {"taxable_income": 108000, "private_hospital_cover": True,
            "tax_withheld": 27000, "payg_instalment_credit": 0,
            "franking": None, "private_health_rebate": None, "unmodelled_inputs": [], **updates}


def frank(credit=1200, **updates):
    return {"income_year": "2025-26", "credit": credit, "gross_up_included": True,
            "refundable_eligibility_confirmed": True, **updates}


def phi(**updates):
    return {"income_year": "2025-26", "eligibility_and_allocation_confirmed": True,
            "income_for_rebate": 108000, "family": False, "dependent_children": 0,
            "rows": [{"period": "1jul_to_31mar", "age_band": "under_65",
                      "eligible_premium": 1800, "rebate_received": 450},
                     {"period": "1apr_to_30jun", "age_band": "under_65",
                      "eligible_premium": 600, "rebate_received": 150}], **updates}


def settle(year="2025-26", **updates):
    code, out = run("individual_tax_settlement", year, inputs(**updates))
    assert code == 0, out
    return out


def refusal(payload, detail, year="2025-26"):
    code, out = run("individual_tax_settlement", year, payload)
    assert code == 3, out
    assert out["refusal"]["code"] == "AU-IND-005"
    assert detail in out["refusal"]["detail"]
    assert not {"refund", "amount_owing", "net_amount_owing", "estimated_refund"} & out.keys()


def test_report_108000_example_and_e11_withholding_only():
    # Tax: 4,288 + 30% * (108,000 - 45,000) = 23,188, LITO nil.
    # Medicare: 2% * 108,000 = 2,160; MLS and HELP nil. Liability = 25,348.
    # Withheld 27,000 -> 1,652 refund. Matches report's restricted baseline, now explicit credits.
    out = settle()
    assert out["tax_components"]["income_tax_after_offsets"] == 23188
    assert out["tax_components"]["medicare_levy"] == 2160
    assert out["liability_including_phi_excess"] == 25348
    assert out["refund"] == 1652
    assert out["amount_owing"] == 0
    assert out["net_amount_owing"] == -1652
    assert out["settlement_complete"] is True
    assert "estimated_refund" not in out["tax_components"]


def test_e11_resolved_franking_phi_and_instalments():
    # Taxable income already includes dividend + gross-up: 104,000 + 2,800 + 1,200 = 108,000.
    code, assembled = run("assemble_taxable_income", "2025-26", {"components": [
        {"kind": "salary_wages", "amount": 104000, "source_skill": "user"},
        {"kind": "dividends_franked", "amount": 2800, "source_skill": "user"},
        {"kind": "franking_credit", "amount": 1200, "source_skill": "user"}]})
    assert code == 0 and assembled["consistent"], assembled
    assert assembled["taxable_income"] == 108000
    # PHI tier1: 1,800 * .16192 -> 291.46; 600 * .16079 -> 96.47.
    # Entitlement 387.93, already received 600 -> 212.07 excess liability.
    # 25,348 + 212.07 - 27,000 - 500 - 1,200 = -3,139.93.
    out = settle(taxable_income=assembled["taxable_income"],
                 upstream_limitations=assembled["limitations"], franking=frank(),
                 private_health_rebate=phi(), payg_instalment_credit=500)
    assert out["private_health_rebate"]["entitlement"] == 387.93
    assert out["private_health_rebate"]["excess_rebate_liability"] == 212.07
    assert out["refund"] == 3139.93
    assert out["total_credits"] == 28700
    assert out["tax_components"]["taxable_income"] == 108000  # no second gross-up


@pytest.mark.parametrize("updates,expected", [
    ({"franking": frank()}, 2852),  # baseline + 1,200 refundable credit
    ({"payg_instalment_credit": 500}, 2152),  # baseline + 500 instalment credit
    ({"private_health_rebate": phi()}, 1439.93),  # baseline - 212.07 excess PHI
])
def test_e11_each_settlement_component(updates, expected):
    assert settle(**updates)["refund"] == expected


def test_refund_can_exceed_gross_tax_and_lito_is_not_refunded():
    # Gross tax and levy zero at 5,000. LITO is capped at zero; full eligible credit refundable.
    out = settle(taxable_income=5000, tax_withheld=0, franking=frank(1500))
    assert out["tax_components"]["offsets"]["lito"] == 0
    assert out["refund"] == 1500


def test_non_refundable_lito_precedes_refundable_credit():
    # At 45,000: gross 4,288, LITO 325, Medicare 900 -> 4,863.
    # Withholding 3,000 + franking 2,000 -> refund 137; LITO does not reduce levy directly.
    out = settle(taxable_income=45000, tax_withheld=3000, franking=frank(2000))
    assert out["tax_components"]["offsets"]["lito"] == 325
    assert out["tax_components"]["medicare_levy"] == 900
    assert out["refund"] == 137


@pytest.mark.parametrize("withheld,owing,refund", [(0, 25348, 0), (25348, 0, 0), (27000, 0, 1652)])
def test_signed_balance_and_separate_nonnegative_outcomes(withheld, owing, refund):
    out = settle(tax_withheld=withheld)
    assert out["amount_owing"] == owing
    assert out["refund"] == refund
    assert out["net_amount_owing"] == owing - refund


def test_franking_does_not_reduce_help_repayment_income():
    # At 108,000 HELP = (108,000 - 67,000) * .15 = 6,150.
    # 25,348 + 6,150 - 27,000 - 1,200 = 3,298 owing.
    out = settle(has_help_debt=True, help_debt_balance=20000, franking=frank())
    assert out["tax_components"]["help_repayment"] == 6150
    assert out["tax_components"]["help_detail"]["repayment_income"] == 108000
    assert out["amount_owing"] == 3298


def test_includes_mls_without_confusing_phi_cover():
    # 108,000 tier1 singles: MLS = .01 * 108,000 = 1,080. Refund baseline - 1,080 = 572.
    assert settle(private_hospital_cover=False)["refund"] == 572


def test_phi_shortfall_is_refundable_even_with_no_income_tax():
    # 2025-26 base under65: 1,000 * .24288 = 242.88, none already received.
    row = {"period": "1jul_to_31mar", "age_band": "under_65", "eligible_premium": 1000, "rebate_received": 0}
    out = settle(taxable_income=0, tax_withheld=0, private_health_rebate=phi(income_for_rebate=0, rows=[row]))
    assert out["refund"] == 242.88
    assert out["private_health_rebate"]["refundable_offset"] == 242.88


@pytest.mark.parametrize("income,expected", [(101000, 242.88), (101001, 161.92),
                                            (118000, 161.92), (118001, 80.95),
                                            (158000, 80.95), (158001, 0)])
def test_phi_single_tier_boundaries(income, expected):
    row = {"period": "1jul_to_31mar", "age_band": "under_65", "eligible_premium": 1000, "rebate_received": 0}
    out = settle(private_health_rebate=phi(income_for_rebate=income, rows=[row]))
    assert out["private_health_rebate"]["entitlement"] == expected


@pytest.mark.parametrize("band,rate", [("under_65", .16192), ("65_69", .2024), ("70_plus", .24288)])
def test_phi_oldest_person_age_bands(band, rate):
    row = {"period": "1jul_to_31mar", "age_band": band, "eligible_premium": 1000, "rebate_received": 0}
    assert settle(private_health_rebate=phi(rows=[row]))["private_health_rebate"]["entitlement"] == round(1000 * rate, 2)


@pytest.mark.parametrize("family_income,expected", [(203500, 242.88), (203501, 161.92)])
def test_phi_family_child_threshold_shift(family_income, expected):
    # Family base threshold 202,000 + 1,500 for second qualifying child = 203,500.
    row = {"period": "1jul_to_31mar", "age_band": "under_65", "eligible_premium": 1000, "rebate_received": 0}
    out = settle(has_spouse=True, spouse_taxable_income=100000, dependent_children=2,
                 private_health_rebate=phi(family=True, dependent_children=2, income_for_rebate=family_income, rows=[row]))
    assert out["private_health_rebate"]["entitlement"] == expected


@pytest.mark.parametrize("field", ["tax_withheld", "payg_instalment_credit", "franking", "private_health_rebate", "unmodelled_inputs"])
def test_missing_reconciliation_fact_never_defaults_to_zero(field):
    payload = inputs()
    del payload[field]
    code, out = run("individual_tax_settlement", "2025-26", payload)
    assert code == 2
    assert "refund" not in out


@pytest.mark.parametrize("unmodelled", ["FITO", "SBITO", "trust franking eligibility", "unresolved PHI tax claim code", "other credit"])
def test_e11_unmodelled_input_refuses_final(unmodelled):
    refusal(inputs(unmodelled_inputs=[unmodelled]), unmodelled)


@pytest.mark.parametrize("update,detail", [
    ({"private_hospital_cover": None}, "hospital_cover_not_stated"),
    ({"has_help_debt": True}, "help_balance_not_stated"),
    ({"upstream_limitations": [{"id": "unresolved_deduction", "kind": "assumption", "message": "Needs evidence"}]}, "unresolved_deduction"),
    ({"upstream_limitations": [{"id": "other_offset", "kind": "exclusion", "message": "Not modelled"}]}, "other_offset"),
])
def test_component_and_upstream_limitations_block_final(update, detail):
    refusal(inputs(**update), detail)


@pytest.mark.parametrize("credit,detail", [
    (frank(gross_up_included=False), "gross-up"),
    (frank(refundable_eligibility_confirmed=False), "eligibility"),
    (frank(income_year="2026-27"), "different income year"),
])
def test_unresolved_franking_refuses(credit, detail):
    refusal(inputs(franking=credit), detail)


@pytest.mark.parametrize("rebate,detail", [
    (phi(eligibility_and_allocation_confirmed=False), "eligibility"),
    (phi(income_year="2026-27"), "different income year"),
    (phi(dependent_children=1), "single income thresholds"),
])
def test_unresolved_phi_refuses(rebate, detail):
    refusal(inputs(private_health_rebate=rebate), detail)


@pytest.mark.parametrize("updates,code", [({"sapto_eligible": True}, "AU-IND-002"),
                                          ({"special_circumstances": ["trustee_assessed_income"]}, "AU-IND-001")])
def test_special_tax_regimes_still_refuse(updates, code):
    status, out = run("individual_tax_settlement", "2025-26", inputs(**updates))
    assert status == 3 and out["refusal"]["code"] == code


@pytest.mark.parametrize("field,value", [("tax_withheld", -1), ("payg_instalment_credit", -1),
                                         ("taxable_income", float("inf")), ("tax_withheld", float("nan"))])
def test_invalid_money_rejected(field, value):
    status, _ = run("individual_tax_settlement", "2025-26", inputs(**{field: value}))
    assert status == 2


def test_unknown_nested_field_rejected():
    payload = inputs(private_health_rebate=phi())
    payload["private_health_rebate"]["rows"][0]["premium_net"] = 1
    status, _ = run("individual_tax_settlement", "2025-26", payload)
    assert status == 2


def test_future_phi_period_never_borrows_previous_year_rates():
    status, out = run("individual_tax_settlement", "2026-27", inputs(
        private_health_rebate=phi(income_year="2026-27")))
    assert status == 4 and out["refusal"]["code"] == "AU-GEN-003"
    assert "phi_rebate_1apr_to_30jun" in out["refusal"]["detail"]


def test_draft_phi_never_asserts_final(monkeypatch):
    original = Figures.get

    def unverified(figures, key):
        if key == "medicare.phi_rebate_1jul_to_31mar_under_65":
            figures.data = copy.deepcopy(figures.data)
            figures.data["medicare"]["phi_rebate_1jul_to_31mar_under_65"]["status"] = "SOURCE-CITED"
        return original(figures, key)

    monkeypatch.setattr(Figures, "get", unverified)
    status, out = run("individual_tax_settlement", "2025-26", inputs(private_health_rebate=phi()), allow_draft=True)
    assert status == 3 and out["refusal"]["code"] == "AU-IND-005"
    assert "draft" in out["refusal"]["detail"]


def test_year_and_primary_provenance_are_returned():
    out = settle(private_health_rebate=phi())
    assert out["income_year"] == "2025-26" and not out["draft"]
    assert all(rule["income_year"] == "2025-26" and rule["source"].startswith("https://www.ato.gov.au/")
               for rule in out["rule_authorities"])
    used = {f["key"] for f in out["figures_used"]}
    assert {"medicare.phi_rebate_1jul_to_31mar_under_65", "medicare.phi_rebate_1apr_to_30jun_under_65"} <= used


def test_withholding_only_component_tool_retains_its_contract():
    status, out = run("individual_income_tax", "2025-26", {"taxable_income": 108000,
                      "private_hospital_cover": True, "tax_withheld": 27000})
    assert status == 0 and out["estimated_refund"] == 1652
    assert "final settlement not computed" in out["completeness_scope"].lower()
