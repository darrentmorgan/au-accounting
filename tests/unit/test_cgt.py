"""CGT calculators. Expected values come from ATO worked examples (cited by page) or hand computation shown
step by step from the ITAA 1997 text. None were produced by running the calculators."""

import pytest

from au_tax.calculators.cgt import held_12_months, minimum_tax_gap, round_factor
from au_tax.figures import Figures
from au_tax.registry import load_all, run


def ok(tool, year, **kw):
    code, out = run(tool, year, kw)
    assert code == 0, out
    return out


def refused(tool, year, code, **kw):
    rc, out = run(tool, year, kw)
    assert rc == 3, out
    assert out["refusal"]["code"] == code
    return out


def approx(x):
    return pytest.approx(x, abs=0.01)


def test_tools_registered():
    assert {"capital_gain", "net_capital_gain", "main_residence_exemption", "small_business_cgt_screen"} <= set(load_all())


# ---------------------------------------------------------------- 12-month rule and rounding

def test_twelve_month_rule_excludes_both_days():
    # ATO CGT discount page: exclude the day of acquisition and the day of the CGT event.
    # Acquired 1 Jul 2024: 1 Jul 2025 leaves 364 whole days between -> no; 2 Jul 2025 -> yes.
    from datetime import date
    assert not held_12_months(date(2024, 7, 1), date(2025, 7, 1))
    assert held_12_months(date(2024, 7, 1), date(2025, 7, 2))


def test_indexation_factor_rounding():
    # s960-275(5) example: 1.102795 -> 1.103; ATO: 1.4125 -> 1.413 (round half up)
    assert round_factor(1.102795) == 1.103
    assert round_factor(1.4125) == 1.413


# ---------------------------------------------------------------- discount method (before 1 July 2027)

def test_individual_discount_basic():
    # gain = 150,000 - 100,000 = 50,000; held > 12 months; 50% discount -> 25,000
    out = ok("capital_gain", "2025-26", acquisition_date="2020-01-01", event_date="2025-10-01",
             capital_proceeds=150000, first_element=100000)
    assert out["gross_capital_gain"] == approx(50000)
    assert out["net_capital_gain"] == approx(25000)
    assert out["method"] == "discount"


def test_under_12_months_no_discount():
    out = ok("capital_gain", "2025-26", acquisition_date="2024-07-01", event_date="2025-07-01",
             capital_proceeds=150000, first_element=100000)
    assert out["discount_percentage"] == 0
    assert out["net_capital_gain"] == approx(50000)


def test_losses_applied_before_discount():
    # (50,000 - 10,000) x 50% = 20,000
    out = ok("capital_gain", "2025-26", acquisition_date="2020-01-01", event_date="2025-10-01",
             capital_proceeds=150000, first_element=100000, capital_losses_available=10000)
    assert out["net_capital_gain"] == approx(20000)
    assert out["capital_losses_remaining"] == 0


def test_cost_base_elements_and_reduced_cost_base():
    # cost base = 400,000 + 20,000 + 5,000 (3rd) + 30,000 + 1,000 + 12,000 = 468,000
    # reduced cost base excludes the 3rd element = 463,000; proceeds 450,000 -> loss 13,000
    out = ok("capital_gain", "2025-26", acquisition_date="2019-01-01", event_date="2025-10-01",
             capital_proceeds=450000, first_element=400000, incidental_costs_acquisition=20000,
             ownership_costs=5000, capital_improvements=30000, title_costs=1000, incidental_costs_disposal=12000)
    assert out["cost_base"] == approx(468000)
    assert out["reduced_cost_base"] == approx(463000)
    assert out["capital_loss"] == approx(13000)
    assert out["net_capital_gain"] == 0


def test_capital_works_deductions_reduce_cost_base():
    # 500,000 - 20,000 deductions = 480,000; gain 600,000 - 480,000 = 120,000; x 50% = 60,000
    out = ok("capital_gain", "2025-26", acquisition_date="2015-01-01", event_date="2025-10-01",
             capital_proceeds=600000, first_element=500000, capital_works_deductions=20000, asset_type="real_property")
    assert out["net_capital_gain"] == approx(60000)


def test_company_no_discount():
    out = ok("capital_gain", "2025-26", entity_type="company", acquisition_date="2020-01-01",
             event_date="2025-10-01", capital_proceeds=150000, first_element=100000)
    assert out["net_capital_gain"] == approx(50000)


def test_super_fund_one_third():
    # 90,000 x (1 - 1/3) = 60,000 (s115-100(b): 33 1/3%)
    out = ok("capital_gain", "2025-26", entity_type="complying_super_fund", acquisition_date="2020-01-01",
             event_date="2025-10-01", capital_proceeds=190000, first_element=100000)
    assert out["net_capital_gain"] == approx(60000)


def test_trust_fifty_percent():
    out = ok("capital_gain", "2026-27", entity_type="trust", acquisition_date="2020-01-01",
             event_date="2026-10-01", capital_proceeds=190000, first_element=100000)
    assert out["net_capital_gain"] == approx(45000)


def test_h2_and_d1_no_discount():
    out = ok("capital_gain", "2025-26", cgt_event="D1", acquisition_date="2020-01-01", event_date="2025-10-01",
             capital_proceeds=20000, incidental_costs_acquisition=2000)
    assert out["net_capital_gain"] == approx(18000)


def test_contract_date_income_year():
    # s104-10(3): contract 20 Jun 2026 (settles in July) -> 2025-26
    out = ok("capital_gain", "2026-27", acquisition_date="2020-01-01", event_date="2026-06-20",
             capital_proceeds=150000, first_element=100000)
    assert out["event_income_year"] == "2025-26"
    assert out["warnings"]


# ---------------------------------------------------------------- frozen indexation (ATO example: Val)

VAL = dict(acquisition_date="1991-06-24", event_date="2025-10-15", capital_proceeds=600000,
           asset_type="real_property",
           cost_base_items=[
               {"element": 1, "amount": 15000, "date_incurred": "1991-06-24"},
               {"element": 1, "amount": 135000, "date_incurred": "1991-06-24"},
               {"element": 2, "amount": 5000, "date_incurred": "1991-07-20"},
               {"element": 2, "amount": 2000, "date_incurred": "1991-08-05"},
           ],
           incidental_costs_disposal=16500)


def test_val_indexation_matches_ato_example():
    # ATO 'Indexing the cost base' (updated 29 Jun 2026): factors 68.7/59.0 = 1.164, 68.7/59.3 = 1.159;
    # indexed costs 182,713 + 16,500 sale costs = 199,213; indexed gain 600,000 - 199,213 = 400,787.
    out = ok("capital_gain", "2025-26", method_choice="indexation", **VAL)
    assert out["method"] == "frozen_indexation"
    assert out["cost_base_indexed"] == approx(199213)
    assert out["net_capital_gain"] == approx(400787)


def test_val_best_method_is_discount():
    # discount: cost base 150,000 + 7,000 + 16,500 = 173,500; gain 426,500; x 50% = 213,250 < 400,787
    out = ok("capital_gain", "2025-26", **VAL)
    assert out["method"] == "discount"
    assert out["net_capital_gain"] == approx(213250)


def test_val_with_large_losses_indexation_wins():
    # losses 380,000: discount (426,500 - 380,000) x 50% = 23,250; indexation 400,787 - 380,000 = 20,787
    out = ok("capital_gain", "2025-26", capital_losses_available=380000, **VAL)
    assert out["method"] == "frozen_indexation"
    assert out["net_capital_gain"] == approx(20787)


# ---------------------------------------------------------------- exemptions

def test_pre_cgt_asset_disregarded():
    out = ok("capital_gain", "2025-26", acquisition_date="1984-05-01", event_date="2025-10-01",
             capital_proceeds=900000, first_element=50000)
    assert out["net_capital_gain"] == 0
    assert out["method"] == "disregarded"


def test_collectable_at_threshold_disregarded():
    out = ok("capital_gain", "2025-26", asset_type="collectable", acquisition_date="2020-01-01",
             event_date="2025-10-01", capital_proceeds=5000, first_element=500)
    assert out["net_capital_gain"] == 0


def test_personal_use_asset_threshold_and_loss():
    out = ok("capital_gain", "2025-26", asset_type="personal_use_asset", acquisition_date="2020-01-01",
             event_date="2025-10-01", capital_proceeds=15000, first_element=10000)
    assert out["net_capital_gain"] == 0
    # above the threshold: gain 20,000 - 12,000 = 8,000, discounted to 4,000
    out = ok("capital_gain", "2025-26", asset_type="personal_use_asset", acquisition_date="2020-01-01",
             event_date="2025-10-01", capital_proceeds=20000, first_element=12000)
    assert out["net_capital_gain"] == approx(4000)
    # loss disregarded
    out = ok("capital_gain", "2025-26", asset_type="personal_use_asset", acquisition_date="2020-01-01",
             event_date="2025-10-01", capital_proceeds=5000, first_element=12000)
    assert out["capital_loss"] == 0


# ---------------------------------------------------------------- foreign residents

def test_violet_market_value_method_ato_example():
    # ATO 'CGT discount for foreign residents': cost 1,000,000 (30 Jan 2011), MV 8 May 2012 1,100,000,
    # sold 1 Jul 2018 for 2,000,000, never resident. Excess 100,000 < gain 1,000,000; no resident days.
    # s115-115(5): (100,000 + 900,000 x 0/apportionable) / (2 x 1,000,000) = 5%; net 950,000.
    out = ok("capital_gain", "2025-26", residency="foreign", asset_type="real_property",
             acquisition_date="2011-01-30", event_date="2018-07-01", capital_proceeds=2000000,
             first_element=1000000, foreign_or_temporary_on_8_may_2012=True,
             choose_market_value_method_8_may_2012=True, market_value_8_may_2012=1100000)
    assert out["discount_percentage"] == pytest.approx(0.05)
    assert out["net_capital_gain"] == approx(950000)


def test_foreign_apportioned_discount_after_8_may_2012():
    # s115-115(2): acquired 1 Jan 2015 while resident, foreign from 1 Jan 2020, contract 31 Dec 2025.
    # discount testing period 1 Jan 2015 - 31 Dec 2025 inclusive = 11 x 365 + 3 leap days = 4,018
    # foreign days 1 Jan 2020 - 31 Dec 2025 = 6 x 365 + 2 = 2,192; resident days 1,826
    # percentage = 1,826 / (2 x 4,018) = 1,826 / 8,036; net = 100,000 x (1 - 1,826/8,036)
    out = ok("capital_gain", "2025-26", residency="foreign", asset_type="real_property",
             acquisition_date="2015-01-01", event_date="2025-12-31", capital_proceeds=600000,
             first_element=500000, foreign_or_temporary_days_after_8_may_2012=2192)
    assert out["discount_percentage"] == pytest.approx(1826 / 8036, abs=1e-6)
    assert out["net_capital_gain"] == approx(100000 * (1 - 1826 / 8036))


def test_foreign_resident_all_period_no_discount_and_frcgw():
    # acquired after 8 May 2012, foreign throughout: 0%; FRCGW 15% x 800,000 = 120,000
    out = ok("capital_gain", "2025-26", residency="foreign", asset_type="real_property",
             acquisition_date="2016-03-01", event_date="2025-10-01", capital_proceeds=800000, first_element=600000)
    assert out["discount_percentage"] == 0
    assert out["net_capital_gain"] == approx(200000)
    assert out["frcgw"]["withholding_if_no_clearance"] == approx(120000)
    assert out["frcgw"]["applies"] is True


def test_foreign_resident_shares_not_tap():
    out = ok("capital_gain", "2025-26", residency="foreign", asset_type="shares_or_units",
             acquisition_date="2016-03-01", event_date="2025-10-01", capital_proceeds=80000, first_element=60000)
    assert out["net_capital_gain"] == 0
    assert out["method"] == "disregarded"


def test_indirect_interest_escalated():
    refused("capital_gain", "2026-27", "AU-CGT-009", residency="foreign", asset_type="shares_or_units",
            indirect_real_property_interest=True, acquisition_date="2016-03-01", event_date="2026-10-02",
            capital_proceeds=1, first_element=1)


def test_i1_choice_disregards():
    out = ok("capital_gain", "2026-27", cgt_event="I1", i1_choose_to_disregard=True, asset_type="shares_or_units",
             acquisition_date="2016-03-01", event_date="2026-10-02", capital_proceeds=80000, first_element=60000)
    assert out["net_capital_gain"] == 0


# ---------------------------------------------------------------- 1 July 2027 regime (Act No. 49 of 2026)

def test_deemed_sale_split(synthetic_post_2027_cpi):
    # Held 30 Jun 2027: deferred gain = MV 700,000 - cost 500,000 = 200,000, discount 50% -> 100,000
    # post: indexation factor = March 2028 quarter 156.0 / September 2027 quarter 150.0 (synthetic test index
    # numbers, tests/conftest.py) = 1.04; indexed cost base 700,000 x 1.04 = 728,000
    # post gain = 800,000 - 728,000 = 72,000 (no discount); net = 172,000; minimum tax capital gain 72,000
    out = ok("capital_gain", "2027-28", acquisition_date="2020-01-01", event_date="2028-03-01",
             capital_proceeds=800000, first_element=500000, market_value_30_june_2027=700000)
    assert out["method"] == "deemed_sale_split_at_1_july_2027"
    assert out["net_capital_gain"] == approx(172000)
    assert out["minimum_tax_capital_gain"] == approx(72000)
    cats = {c["category"]: c for c in out["components"]}
    assert cats["deferred_non_residential"]["gain"] == approx(200000)
    assert cats["non_residential"]["gain"] == approx(72000)


def test_deemed_sale_minimum_tax_not_triggered(synthetic_post_2027_cpi):
    # TI 172,000 (2027-28 rates: 14% second bracket): tax(172,000) = 0.14 x 26,800 + 0.30 x 90,000 + 0.37 x 37,000
    # = 3,752 + 27,000 + 13,690 = 44,442; tax(100,000) = 3,752 + 16,500 = 20,252; step 4 = 24,190;
    # step 1 = 30% x 72,000 = 21,600; step 5 negative -> gap 0
    # Called for 2026-27: the event (1 Mar 2028) is in 2027-28, so the 2027-28 rates apply. With the 2026-27 table
    # (15% second bracket) step 2 would be 44,442 + 0.01 x 26,800 = 44,710.
    out = ok("capital_gain", "2026-27", acquisition_date="2020-01-01", event_date="2028-03-01",
             capital_proceeds=800000, first_element=500000, market_value_30_june_2027=700000,
             taxable_income_including_gain=172000)
    assert out["minimum_tax"]["step2_basic_tax_on_taxable_income"] == approx(44442)
    assert out["minimum_tax"]["minimum_tax_gap_amount"] == 0


def test_minimum_tax_gap_hand_example():
    # TI 100,000 all minimum tax capital gain: step 1 = 30,000; step 2 = 3,752 + 0.30 x 55,000 = 20,252;
    # step 3 = tax on 0 = 0; step 4 = 20,252; gap = 30,000 - 20,252 = 9,748
    f = Figures("2027-28")
    r = minimum_tax_gap(f, 100000, 100000)
    assert r["minimum_tax_gap_amount"] == 9748
    # TI 150,000, gain 100,000: tax(150,000) = 3,752 + 27,000 + 5,550 = 36,302; tax(50,000) = 3,752 + 1,500 = 5,252
    # step 4 = 31,050 > 30,000 -> no gap
    assert minimum_tax_gap(f, 150000, 100000)["minimum_tax_gap_amount"] == 0
    # Division 119 exists only from 2027-28: an earlier year's figures are refused, never adapted.
    with pytest.raises(ValueError):
        minimum_tax_gap(Figures("2026-27"), 100000, 100000)


def test_post_2027_missing_market_value_refused():
    refused("capital_gain", "2027-28", "AU-CGT-006", acquisition_date="2020-01-01", event_date="2028-03-01",
            capital_proceeds=800000, first_element=500000)


def test_post_2027_indexation_unpublished_gives_deferred_component_and_refuses_post_part():
    # cgt.indexation_cpi_from_2027 is null for 2027-28 (no post-2027 quarter is published), so the post-1 July 2027 part
    # of a sale that would be indexed (held over 12 months) cannot be worked out: it is refused AU-GEN-003 at field level,
    # in draft mode too, and nothing is estimated. The pre-July deferred component does not need the index numbers and is
    # still returned (hand computation, s112-155, s112-160(3)):
    #   deferred notional gain = market value 700,000 - cost base 500,000 = 200,000
    #   held 1 Jan 2020 to 1 Mar 2028 (over 12 months), discount 50% = 100,000; after discount 100,000
    kw = dict(acquisition_date="2020-01-01", event_date="2028-03-01", capital_proceeds=800000, first_element=500000,
              market_value_30_june_2027=700000)
    for allow in (False, True):
        code, out = run("capital_gain", "2027-28", kw, allow_draft=allow)
        assert code == 0, out
        assert out["partial"] is True
        d = out["deferred_component"]
        assert d["notional_gain"] == approx(200000) and d["discount_percentage"] == 0.5
        assert d["discount_amount"] == approx(100000) and d["gain_after_discount"] == approx(100000)
        post = out["post_1_july_2027_part"]
        assert post["status"] == "refused" and post["gain"] is None
        fr = out["field_refusals"]
        assert len(fr) == 1 and fr[0]["field"] == "post_1_july_2027_part" and fr[0]["code"] == "AU-GEN-003"
        assert "cgt.indexation_cpi_from_2027" in fr[0]["detail"]
        # no whole-event figure is shown: the net capital gain and gross gain are withheld with the post-July part
        assert out["net_capital_gain"] is None and out["gross_capital_gain"] is None
        assert [c["category"] for c in out["components"]] == ["deferred_non_residential"]
    # Called for 2026-27 the answer is the same: the event's own year (2027-28) decides.
    code, out = run("capital_gain", "2026-27", kw)
    assert code == 0 and out["partial"] is True and out["deferred_component"]["gain_after_discount"] == approx(100000)


def test_post_2027_deferred_component_with_losses_and_deferred_loss():
    # Deferred gain 200,000 (as above) less current-year losses 20,000 applied before the discount (s102-5):
    # 180,000 x 50% = 90,000 discount; after discount 90,000. Losses remaining 0.
    kw = dict(acquisition_date="2020-01-01", event_date="2028-03-01", capital_proceeds=800000, first_element=500000,
              market_value_30_june_2027=700000, capital_losses_available=20000)
    out = ok("capital_gain", "2027-28", **kw)
    d = out["deferred_component"]
    assert d["losses_applied"] == approx(20000) and d["discount_amount"] == approx(90000)
    assert d["gain_after_discount"] == approx(90000)
    # A deferred loss: market value 400,000 below cost base 500,000 -> notional loss 100,000, no gain, no discount.
    kw.update(market_value_30_june_2027=400000, capital_losses_available=0)
    out = ok("capital_gain", "2027-28", **kw)
    d = out["deferred_component"]
    assert d["notional_gain"] == 0 and d["notional_loss"] == approx(100000) and d["gain_after_discount"] == 0


def test_post_2027_acquired_after_reform_still_refuses_whole_event_while_cpi_unpublished():
    # Nothing accrued before 1 July 2027, so there is no deferred component to show: the whole disposal refuses.
    code, out = run("capital_gain", "2028-29", dict(acquisition_date="2027-08-01", event_date="2028-09-01",
                                                    capital_proceeds=400000, first_element=300000))
    assert code == 4 and out["refusal"]["code"] == "AU-GEN-003"


def test_post_2027_under_12_months_needs_no_index_number():
    # Bought 1 Sep 2027, sold 1 Jun 2028: under 12 months, so no indexation (s114-10) and no index number is read.
    # Gain 130,000 - 100,000 = 30,000, no discount; net 30,000; minimum tax capital gain 30,000.
    out = ok("capital_gain", "2027-28", acquisition_date="2027-09-01", event_date="2028-06-01",
             capital_proceeds=130000, first_element=100000)
    assert out["net_capital_gain"] == approx(30000)
    assert out["minimum_tax_capital_gain"] == approx(30000)
    assert not any(f["key"].startswith("cgt.indexation_cpi") for f in out["figures_used"])


def test_post_2027_quarter_missing_from_cpi_table_refuses_post_part(synthetic_post_2027_cpi):
    # The synthetic table ends with the December 2028 quarter: a sale in the March 2029 quarter has no index number, so the
    # post-July part is refused at field level; the deferred component (700,000 - 500,000 = 200,000, 50% = 100,000) stands.
    code, out = run("capital_gain", "2028-29", dict(acquisition_date="2020-01-01", event_date="2029-02-01",
                                                    capital_proceeds=800000, first_element=500000,
                                                    market_value_30_june_2027=700000))
    assert code == 0 and out["partial"] is True
    assert out["field_refusals"][0]["code"] == "AU-GEN-003" and "2029-02-01" in out["field_refusals"][0]["detail"]
    assert out["deferred_component"]["gain_after_discount"] == approx(100000)


def test_new_residential_dwelling_keeps_discount():
    # s115-102: whole gain 700,000 - 600,000 = 100,000 x 50% = 50,000; no minimum tax
    out = ok("capital_gain", "2027-28", asset_type="real_property", new_residential_dwelling=True,
             acquisition_date="2026-01-01", event_date="2028-01-10", capital_proceeds=700000, first_element=600000)
    assert out["method"] == "new_dwelling_discount"
    assert out["net_capital_gain"] == approx(50000)
    assert out["minimum_tax_capital_gain"] == 0
    assert any("legislative instrument" in w for w in out["warnings"])
    keys = {f["key"] for f in out["figures_used"]}
    assert "cgt.discount_new_residential_dwelling" in keys   # 2027-28 key, not cgt.discount_individual_trust
    assert "cgt.discount_individual_trust" not in keys


def test_pre_cgt_reset_1_july_2027(synthetic_post_2027_cpi):
    # s112-175: reacquired 1 Jul 2027 at MV 1,000,000; factor December 2027 quarter 153.0 / September 2027 quarter
    # 150.0 (synthetic test index numbers) = 1.02 -> 1,020,000; gain 1,100,000 - 1,020,000 = 80,000, no discount
    out = ok("capital_gain", "2027-28", acquisition_date="1980-01-01", event_date="2027-11-15",
             capital_proceeds=1100000, first_element=50000, market_value_30_june_2027=1000000)
    assert out["net_capital_gain"] == approx(80000)


def test_acquired_after_reform_indexed(synthetic_post_2027_cpi):
    # acquired 1 Aug 2027 for 300,000 (September 2027 quarter, synthetic index 150.0), sold 1 Sep 2028 for 400,000
    # (September 2028 quarter, synthetic 159.0; that year's file is a copy of 2027-28 inside the fixture):
    # factor 159.0 / 150.0 = 1.06 -> 318,000; gain 400,000 - 318,000 = 82,000, no discount
    out = ok("capital_gain", "2028-29", acquisition_date="2027-08-01", event_date="2028-09-01",
             capital_proceeds=400000, first_element=300000)
    assert out["method"] == "indexation_from_1_july_2027"
    assert out["net_capital_gain"] == approx(82000)


def test_post_2027_company_unchanged():
    out = ok("capital_gain", "2027-28", entity_type="company", acquisition_date="2020-01-01",
             event_date="2028-01-10", capital_proceeds=150000, first_element=100000)
    assert out["net_capital_gain"] == approx(50000)


def test_post_2027_trust_escalated():
    refused("capital_gain", "2027-28", "AU-CGT-003", entity_type="trust", acquisition_date="2020-01-01",
            event_date="2028-01-10", capital_proceeds=150000, first_element=100000)


@pytest.mark.parametrize("special,code", [("rollover", "AU-CGT-002"), ("earnout", "AU-CGT-004"),
                                          ("defi_or_crypto_lending", "AU-CGT-005"),
                                          ("small_business_concession_application", "AU-CGT-001")])
def test_special_circumstances(special, code):
    refused("capital_gain", "2026-27", code, acquisition_date="2020-01-01", event_date="2026-10-10",
            capital_proceeds=1, first_element=1, special_circumstances=[special])


def test_unmodelled_events():
    refused("capital_gain", "2026-27", "AU-CGT-003", cgt_event="E", acquisition_date="2020-01-01",
            event_date="2026-10-10", capital_proceeds=1)
    refused("capital_gain", "2026-27", "AU-CGT-004", cgt_event="K6", acquisition_date="1980-01-01",
            event_date="2026-10-10", capital_proceeds=1)


def test_crypto_swap_is_disposal():
    # Swap of token A (cost 2,000, held 8 months) for token B worth 5,000: A1, gain 3,000, no discount
    out = ok("capital_gain", "2026-27", asset_type="crypto", acquisition_date="2026-01-15", event_date="2026-09-20",
             capital_proceeds=5000, first_element=2000)
    assert out["net_capital_gain"] == approx(3000)


# ---------------------------------------------------------------- net_capital_gain

def test_losses_to_non_discount_gains_first():
    # gains: 10,000 (<12 months) and 30,000 (discount). loss 15,000 -> 10,000 then 5,000;
    # remaining discount gain 25,000 x 50% = 12,500
    out = ok("net_capital_gain", "2025-26",
             gains=[{"amount": 10000, "label": "short"}, {"amount": 30000, "discount_eligible": True, "label": "long"}],
             losses=[{"amount": 15000}])
    assert out["net_capital_gain"] == approx(12500)


def test_collectables_statutory_example():
    # s108-10(1) example: collectable gains 200, collectable losses 400, other gains 500 ->
    # net capital gain 500, collectable loss 200 carried forward
    out = ok("net_capital_gain", "2025-26",
             gains=[{"amount": 200, "collectable": True}, {"amount": 500}],
             losses=[{"amount": 400, "collectable": True}])
    assert out["net_capital_gain"] == approx(500)
    assert out["collectable_losses_carried_forward"] == approx(200)


def test_personal_use_loss_disregarded_and_prior_losses():
    # personal use loss ignored; prior 30,000 against 20,000 discount gain -> nil, carry forward 10,000
    out = ok("net_capital_gain", "2025-26", gains=[{"amount": 20000, "discount_eligible": True}],
             losses=[{"amount": 5000, "personal_use_asset": True}], prior_year_net_capital_losses=30000)
    assert out["net_capital_gain"] == 0
    assert out["net_capital_loss_carried_forward"] == approx(10000)
    assert out["personal_use_losses_disregarded"] == approx(5000)


def test_net_capital_loss_carried_forward():
    out = ok("net_capital_gain", "2025-26", gains=[{"amount": 4000}], losses=[{"amount": 10000}])
    assert out["net_capital_gain"] == 0
    assert out["net_capital_loss_carried_forward"] == approx(6000)


def test_post_2027_statutory_order():
    # s102-5 step 1: deferred non-residential gains are reduced first even though discounted:
    # loss 60,000 -> deferred 50,000 fully, then 10,000 of non-residential 40,000 -> 30,000; net 30,000
    out = ok("net_capital_gain", "2027-28",
             gains=[{"amount": 40000, "category": "non_residential"},
                    {"amount": 50000, "category": "deferred_non_residential", "discount_eligible": True}],
             losses=[{"amount": 60000}])
    assert out["net_capital_gain"] == approx(30000)
    assert out["minimum_tax_capital_gain_before_gifts"] == approx(30000)


def test_quarantined_amount_reduces_residential():
    # steps 3-4: quarantined 25,000 reduces residential gain 40,000 -> 15,000
    out = ok("net_capital_gain", "2027-28", gains=[{"amount": 40000, "category": "residential"}],
             quarantined_residential_amount=25000)
    assert out["net_capital_gain"] == approx(15000)


def test_company_no_discount_in_net():
    out = ok("net_capital_gain", "2025-26", entity_type="company",
             gains=[{"amount": 30000, "discount_eligible": True}])
    assert out["net_capital_gain"] == approx(30000)


# ---------------------------------------------------------------- main residence

def test_roya_six_year_rule_and_first_income_use_ato_example():
    # ATO 'Treating former home as main residence': MV 220,000 at first rental 29 Sep 1999; sold 555,000,
    # costs 15,000 -> gain 320,000; non-main residence days 30 Sep 2005 - 29 Sep 2024 = 6,940;
    # ownership days 29 Sep 1999 - 29 Sep 2024 = 9,133; 320,000 x 6,940 / 9,133 = 243,162.16; discount -> 121,581.08
    out = ok("main_residence_exemption", "2025-26", capital_proceeds=555000, cost_base=195000,
             ownership_start="1995-01-10", ownership_end="2024-09-29",
             lived_in_periods=[{"start": "1995-01-10", "end": "1999-09-28"}],
             income_use_periods=[{"start": "1999-09-29", "end": "2024-09-29"}],
             market_value_at_first_income_use=220000, selling_costs_after_first_income_use=15000)
    assert out["home_first_used_to_produce_income_rule"] is True
    assert out["ownership_days"] == 9133
    assert out["non_main_residence_days"] == 6940
    assert out["taxable_capital_gain"] == approx(320000 * 6940 / 9133)
    assert out["net_capital_gain"] == approx(320000 * 6940 / 9133 / 2)


def test_peter_rented_before_moving_in_ato_example():
    # ATO 'Using your home for rental or business': 230,000 x 1,004 / 4,564 = 50,595.97 (ATO prints $50,595,
    # whole dollars); no s118-192 because the house was rented from acquisition
    out = ok("main_residence_exemption", "2025-26", capital_proceeds=780000, cost_base=550000,
             ownership_start="2013-10-01", ownership_end="2026-03-30",
             lived_in_periods=[{"start": "2016-07-01", "end": "2026-03-30"}],
             income_use_periods=[{"start": "2013-10-01", "end": "2016-06-30"}])
    assert out["home_first_used_to_produce_income_rule"] is False
    assert out["ownership_days"] == 4564
    assert out["taxable_capital_gain"] == approx(230000 * 1004 / 4564)


def test_fatima_part_business_use_ato_example():
    # ATO: MV 520,000 at first business use 1 Nov 2018; sold 620,000; 40% floor area; used 1,370 days of 2,739
    # 100,000 x 40% x 1,370 / 2,739 = 20,007.30
    out = ok("main_residence_exemption", "2025-26", capital_proceeds=620000, cost_base=400000,
             ownership_start="2010-01-01", ownership_end="2026-05-01",
             lived_in_periods=[{"start": "2010-01-01", "end": "2026-05-01"}],
             income_use_periods=[{"start": "2018-11-01", "end": "2022-08-01", "floor_area_fraction": 0.4}],
             market_value_at_first_income_use=520000)
    assert out["taxable_capital_gain"] == approx(20007.30)


def test_thomas_rented_part_from_acquisition_ato_example():
    # 35% of floor area rented from acquisition to sale: 400,000 x 35% = 140,000
    out = ok("main_residence_exemption", "2025-26", capital_proceeds=700000, cost_base=300000,
             ownership_start="2015-01-01", ownership_end="2025-06-01",
             lived_in_periods=[{"start": "2015-01-01", "end": "2025-06-01"}],
             income_use_periods=[{"start": "2015-01-01", "end": "2025-06-01", "floor_area_fraction": 0.35}])
    assert out["taxable_capital_gain"] == approx(140000)


def test_full_exemption_and_unlimited_non_income_absence():
    out = ok("main_residence_exemption", "2025-26", capital_proceeds=900000, cost_base=500000,
             ownership_start="2010-01-01", ownership_end="2025-06-01",
             lived_in_periods=[{"start": "2010-01-01", "end": "2012-12-31"}])
    assert out["exemption"] == "full"
    assert out["net_capital_gain"] == 0


def test_six_year_rule_within_limit_full():
    # rented for 5 years after moving out, absence choice -> fully exempt; s118-192 does not apply
    out = ok("main_residence_exemption", "2025-26", capital_proceeds=900000, cost_base=500000,
             ownership_start="2015-01-01", ownership_end="2025-06-01",
             lived_in_periods=[{"start": "2015-01-01", "end": "2020-05-31"}],
             income_use_periods=[{"start": "2020-06-01", "end": "2025-06-01"}])
    assert out["exemption"] == "full"


def test_foreign_resident_no_exemption():
    # excluded foreign resident: whole gain 400,000, no discount
    out = ok("main_residence_exemption", "2025-26", capital_proceeds=900000, cost_base=500000,
             ownership_start="2010-01-01", ownership_end="2025-06-01",
             lived_in_periods=[{"start": "2010-01-01", "end": "2025-06-01"}], residency_at_event="foreign",
             foreign_residency_years_at_event=2)
    assert out["exemption"] == "none"
    assert out["net_capital_gain"] == approx(400000)


def test_six_month_overlap():
    # lived to 31 Mar 2025, vacant until settlement 31 Aug 2025, no absence choice:
    # without s118-140: 1 Apr - 31 Aug 2025 = 153 non-MR days; with it: the 6 months from 1 Mar 2025 are covered
    base = dict(capital_proceeds=900000, cost_base=500000, ownership_start="2020-01-01", ownership_end="2025-08-31",
                lived_in_periods=[{"start": "2020-01-01", "end": "2025-03-31"}], choose_absence_rule=False)
    out = ok("main_residence_exemption", "2025-26", **base)
    assert out["non_main_residence_days"] == 153
    out = ok("main_residence_exemption", "2025-26", changing_residence_overlap=True, **base)
    assert out["exemption"] == "full"


def test_mre_refusals():
    refused("main_residence_exemption", "2025-26", "AU-CGT-008", capital_proceeds=1, cost_base=1,
            ownership_start="2010-01-01", ownership_end="2025-06-01", lived_in_periods=[],
            special_circumstances=["deceased_estate"])
    refused("main_residence_exemption", "2025-26", "AU-CGT-006", capital_proceeds=900000, cost_base=500000,
            ownership_start="2010-01-01", ownership_end="2025-06-01",
            lived_in_periods=[{"start": "2010-01-01", "end": "2012-12-31"}],
            income_use_periods=[{"start": "2013-01-01", "end": "2025-06-01"}])
    refused("main_residence_exemption", "2026-27", "AU-CGT-007", capital_proceeds=900000, cost_base=500000,
            ownership_start="2015-01-01", ownership_end="2028-06-01",
            lived_in_periods=[{"start": "2015-01-01", "end": "2016-12-31"}],
            income_use_periods=[{"start": "2015-01-01", "end": "2016-12-31", "floor_area_fraction": 0.3}])


# ---------------------------------------------------------------- small business screen

def test_small_business_screen_basic():
    out = ok("small_business_cgt_screen", "2026-27", event_date="2026-10-01", aggregated_turnover=1500000,
             asset_acquired="2014-10-01", active_asset_years=10)
    assert out["basic_conditions_screen"] is True
    assert out["escalations"][0]["code"] == "AU-CGT-001"


def test_small_business_ten_million_gate_from_2027_28():
    # turnover 8m, NAV 7m: fails both $2m and $6m gateways; 50% reduction alone available from 2027-28 (< $10m)
    out = ok("small_business_cgt_screen", "2026-27", event_date="2027-09-01", aggregated_turnover=8000000,
             net_asset_value=7000000, asset_acquired="2015-01-01", active_asset_years=12)
    assert out["basic_conditions_screen"] is False
    assert out["active_asset_50_percent_reduction_screen"] is True
    out = ok("small_business_cgt_screen", "2026-27", event_date="2027-05-01", aggregated_turnover=8000000,
             net_asset_value=7000000, asset_acquired="2015-01-01", active_asset_years=12)
    assert out["active_asset_50_percent_reduction_screen"] is False


def test_rental_not_active_asset():
    out = ok("small_business_cgt_screen", "2026-27", event_date="2026-10-01", aggregated_turnover=500000,
             asset_acquired="2014-10-01", active_asset_years=12, asset_mainly_used_to_derive_rent=True)
    assert out["active_asset_test"] is False
