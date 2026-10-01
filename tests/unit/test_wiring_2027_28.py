"""GOAL gate 2: cgt, crypto and individual-tax read the 2027-28 rates file for events and income on or after
1 July 2027, refuse cleanly where a figure is missing, and no longer read 2026-27 figures for those events.

Expected values are hand computations from legislation, shown step by step in each test (ITAA 1997 as amended by Act No. 49 of
2026; ITRA Sch 7 Pt I cl 1 for 2027-28; Medicare Levy Act 1986). None was produced by running the calculators.
"""

import pytest

from au_tax import figures as figures_module
from au_tax.figures import FigureError, Figures
from au_tax.registry import run


def call(tool, year, allow_draft=False, **kw):
    return run(tool, year, kw, allow_draft=allow_draft)


def ok(tool, year, **kw):
    code, out = run(tool, year, kw)
    assert code == 0, out
    return out


def approx(x):
    return pytest.approx(x, abs=0.01)


# ============================================================ the old behaviour is gone

def test_2026_27_file_no_longer_carries_2027_28_named_keys():
    # One fact, one key. The rates for events on or after 1 Jul 2027 live in the 2027-28 file only.
    for key in ("cgt.minimum_tax_rate_from_2027_28", "cgt.active_asset_reduction_turnover_gate_from_2027_28",
                "individual.resident_second_bracket_rate_from_2027_28"):
        with pytest.raises(FigureError) as e:
            Figures("2026-27").get(key)
        assert e.value.code == "AU-GEN-003", key
    # ... and the 2027-28 resident table is read directly (14% second bracket), no separate override key.
    with pytest.raises(FigureError):
        Figures("2027-28").get("individual.resident_second_bracket_rate_from_2027_28")
    assert Figures("2027-28").get("cgt.minimum_tax_rate_from_2027_28") == 0.3


def test_post_2027_event_never_reads_the_2026_27_file(monkeypatch):
    # Poison every 2026-27 figure a post-July-2027 event could have used in the old code. If any leaks into the answer,
    # the result changes. Requested year is 2026-27 on purpose: the event date decides the rates year.
    f26 = figures_module.load_year("2026-27")
    monkeypatch.setitem(f26["cgt"]["discount_individual_trust"], "value", 0.9)
    monkeypatch.setitem(f26["cgt"]["discount_company"], "value", 0.9)
    poisoned = [dict(b, rate=0.99) if b["rate"] else dict(b) for b in f26["individual"]["resident_rates"]["value"]]
    monkeypatch.setitem(f26["individual"]["resident_rates"], "value", poisoned)
    # New dwelling sold 10 Jan 2028 (2027-28): 100,000 gain x (1 - 0.5) = 50,000 (s115-100(a) via
    # cgt.discount_new_residential_dwelling). The old code read cgt.discount_individual_trust from the requested
    # year, which is 0.9 here, and would give 100,000 x 0.1 = 10,000.
    out = ok("capital_gain", "2026-27", asset_type="real_property", new_residential_dwelling=True,
             acquisition_date="2026-01-01", event_date="2028-01-10", capital_proceeds=700000, first_element=600000,
             taxable_income_including_gain=40000)
    assert out["net_capital_gain"] == approx(50000)
    assert out["rates_year_used"] == "2027-28"
    assert out["event_income_year"] == "2027-28"
    assert out["figures_used"] and all(f["key"].endswith("@2027-28") for f in out["figures_used"])
    # Minimum tax uses the 2027-28 resident table, not the poisoned 2026-27 one. The new dwelling keeps its discount so
    # no minimum tax capital gain arises; use a sale under 12 months (no discount, no indexation, no CPI needed):
    # bought 1 Sep 2027 for 100,000, sold 1 Jun 2028 for 130,000: gain 30,000; TI including the gain 40,000.
    # step 1 = 30% x 30,000 = 9,000; step 2 = tax(40,000) = 14% x (40,000 - 18,200) = 3,052;
    # step 3 = tax(10,000) = 0; step 4 = 3,052; step 6 = 9,000 - 3,052 = 5,948.
    out = ok("capital_gain", "2026-27", acquisition_date="2027-09-01", event_date="2028-06-01",
             capital_proceeds=130000, first_element=100000, taxable_income_including_gain=40000)
    assert out["minimum_tax"]["step2_basic_tax_on_taxable_income"] == approx(3052)
    assert out["minimum_tax"]["minimum_tax_gap_amount"] == 5948
    assert all(f["key"].endswith("@2027-28") for f in out["figures_used"])


def test_requested_year_does_not_choose_the_rates_for_a_pre_2027_event():
    # Called for 2027-28 but the contract is 20 Jun 2027 (2026-27, old law): 50% discount from the 2026-27 file.
    # Gain 150,000 - 100,000 = 50,000; held over 12 months; net 25,000.
    out = ok("capital_gain", "2027-28", acquisition_date="2020-01-01", event_date="2027-06-20",
             capital_proceeds=150000, first_element=100000)
    assert out["law_regime"] == "before_1_july_2027" and out["rates_year_used"] == "2026-27"
    assert out["net_capital_gain"] == approx(25000)
    assert any("2026-27" in w for w in out["warnings"])


def test_pre_2027_event_in_a_year_without_a_file_refuses_when_only_the_2027_28_file_is_available():
    # 2023-24 has no rates file. The CGT constants are the same in every pre-2027-28 year, so a 2025-26 call falls back
    # (with a warning); a 2027-28 call must not, because the 2027-28 file's 0% individual discount is not that year's.
    out = ok("capital_gain", "2025-26", acquisition_date="2018-01-01", event_date="2023-10-01",
             capital_proceeds=150000, first_element=100000)
    assert out["net_capital_gain"] == approx(25000)
    assert any("No rates file for 2023-24" in w for w in out["warnings"])
    code, out = call("capital_gain", "2027-28", acquisition_date="2018-01-01", event_date="2023-10-01",
                     capital_proceeds=150000, first_element=100000)
    assert code == 4 and out["refusal"]["code"] == "AU-GEN-003"


def test_sale_in_a_year_without_a_rates_file_refuses_not_carried_forward():
    # A company selling on 1 Dec 2028 (2028-29): no rates file, so AU-GEN-003 rather than 2027-28 figures reused.
    code, out = call("capital_gain", "2027-28", entity_type="company", acquisition_date="2020-01-01",
                     event_date="2028-12-01", capital_proceeds=150000, first_element=100000)
    assert code == 4 and out["refusal"]["code"] == "AU-GEN-003"
    assert "2028-29" in out["refusal"]["detail"]


# ============================================================ cgt: 2027-28 figures for events from 1 July 2027

def test_deferred_gain_discount_comes_from_the_2027_28_deferred_key(synthetic_post_2027_cpi, monkeypatch):
    # Held 30 Jun 2027 (acquired 1 Mar 2025 for 100,000; market value 160,000; sold 1 Dec 2027 for 200,000).
    # Deferred gain = 160,000 - 100,000 = 60,000; over 12 months -> discount cgt.discount_individual_trust_deferred_gain
    # (0.5) = 30,000. Post part: reacquired at 160,000, factor Dec 2027 153.0 / Sep 2027 150.0 = 1.02 -> 163,200 (synthetic
    # test index numbers); gain 200,000 - 163,200 = 36,800; no discount. Net = 30,000 + 36,800 = 66,800.
    out = ok("capital_gain", "2027-28", acquisition_date="2025-03-01", event_date="2027-12-01", capital_proceeds=200000,
             first_element=100000, market_value_30_june_2027=160000)
    assert out["net_capital_gain"] == approx(66800)
    assert out["discount_amount"] == approx(30000)
    keys = {f["key"] for f in out["figures_used"]}
    assert "cgt.discount_individual_trust_deferred_gain" in keys
    assert "cgt.discount_individual_trust" not in keys
    # Change only the deferred key (0.5 -> 0.4): the deferred discount follows it, so it is the figure being read.
    figs = figures_module.load_year("2027-28")
    monkeypatch.setitem(figs["cgt"]["discount_individual_trust_deferred_gain"], "value", 0.4)
    out = ok("capital_gain", "2027-28", acquisition_date="2025-03-01", event_date="2027-12-01", capital_proceeds=200000,
             first_element=100000, market_value_30_june_2027=160000)
    assert out["discount_amount"] == approx(24000)  # 60,000 x 0.4


def test_small_business_screen_reads_the_event_years_gate():
    # Called for 2026-27; the event (1 Sep 2027) is in 2027-28, so the ten million gate is read from the 2027-28 file.
    out = ok("small_business_cgt_screen", "2026-27", event_date="2027-09-01", aggregated_turnover=8000000,
             net_asset_value=7000000, asset_acquired="2015-01-01", active_asset_years=12)
    assert out["rates_year_used"] == "2027-28"
    assert out["active_asset_50_percent_reduction_screen"] is True
    assert "cgt.active_asset_reduction_turnover_gate_from_2027_28@2027-28" in {f["key"] for f in out["figures_used"]}
    # An event on 1 May 2027 reads 2026-27 and never asks for the gate.
    out = ok("small_business_cgt_screen", "2026-27", event_date="2027-05-01", aggregated_turnover=8000000,
             net_asset_value=7000000, asset_acquired="2015-01-01", active_asset_years=12)
    assert out["rates_year_used"] == "2026-27"
    assert not any("active_asset_reduction" in f["key"] for f in out["figures_used"])


def test_main_residence_full_exemption_after_1_july_2027_uses_2027_28():
    # Lived in the home throughout: fully exempt, nothing to discount; the rates year is the event year.
    out = ok("main_residence_exemption", "2026-27", capital_proceeds=900000, cost_base=500000,
             ownership_start="2020-01-10", ownership_end="2027-09-10", event_date="2027-08-01",
             lived_in_periods=[{"start": "2020-01-10", "end": "2027-09-10"}])
    assert out["exemption"] == "full" and out["rates_year_used"] == "2027-28"
    assert out["net_capital_gain"] == 0


# ============================================================ net_capital_gain: the year decides the discount

def test_net_capital_gain_2027_28_discounts_only_deferred_and_new_dwelling_gains():
    # 2027-28, individual. Deferred residential gain 50,000 (discount eligible): x 50% = 25,000.
    # New residential dwelling gain 40,000 (eligible): x 50% = 20,000.
    # Other residential gain 30,000 (eligible): no discount for events from 1 Jul 2027, so 30,000.
    # Net capital gain = 25,000 + 20,000 + 30,000 = 75,000; discount amount 25,000 + 20,000 = 45,000.
    out = ok("net_capital_gain", "2027-28", gains=[
        {"amount": 50000, "category": "deferred_residential", "discount_eligible": True, "label": "deferred"},
        {"amount": 40000, "category": "residential", "discount_eligible": True, "new_residential_dwelling": True,
         "label": "new"},
        {"amount": 30000, "category": "residential", "discount_eligible": True, "label": "other"}])
    assert out["net_capital_gain"] == approx(75000)
    assert out["discount_amount"] == approx(45000)
    assert any("other" in w and "discount removed" in w for w in out["warnings"])
    keys = {f["key"] for f in out["figures_used"]}
    assert {"cgt.discount_individual_trust_deferred_gain", "cgt.discount_new_residential_dwelling"} <= keys


def test_net_capital_gain_rejects_categories_from_the_wrong_side_of_1_july_2027():
    code, out = call("net_capital_gain", "2026-27", gains=[{"amount": 1000, "category": "residential"}])
    assert code == 2 and "1 July 2027" in out["error"]
    code, out = call("net_capital_gain", "2027-28", gains=[{"amount": 1000, "category": "pre_2027",
                                                            "discount_eligible": True}])
    assert code == 2 and "earlier income year" in out["error"]


def test_net_capital_gain_2027_28_super_fund_and_company_rules_unchanged():
    # Complying super fund keeps one-third (s115-100(b)): 30,000 x (1 - 1/3) = 20,000. Company never discounted.
    out = ok("net_capital_gain", "2027-28", entity_type="complying_super_fund",
             gains=[{"amount": 30000, "category": "residential", "discount_eligible": True}])
    assert out["net_capital_gain"] == approx(20000)
    out = ok("net_capital_gain", "2027-28", entity_type="company",
             gains=[{"amount": 30000, "category": "pre_2027", "discount_eligible": True}])
    assert out["net_capital_gain"] == approx(30000)


# ============================================================ individual-tax: 2027-28

def test_individual_tax_2027_28_uses_the_2027_28_resident_rates():
    # ITRA Sch 7 Pt I cl 1, 2027-28: 14% on 18,201 to 45,000; 30% on 45,001 to 135,000. TI 60,000:
    # gross tax = 0.14 x 26,800 + 0.30 x 15,000 = 3,752 + 4,500 = 8,252 (2026-27 table gives 4,020 + 4,500 = 8,520).
    # LITO at 60,000 = 325 - 1.5% x (60,000 - 45,000) = 325 - 225 = 100.
    # Working Australians tax offset (s 61-160), net labour income 60,000: lesser of 250 and the basic income tax on
    # 60,000 (8,252) = 250. Income tax after offsets = 8,252 - 100 - 250 = 7,902.
    # Medicare levy 2% x 60,000 = 1,200 (income above the current-law low-income range). Full private hospital cover:
    # no surcharge. Total = 7,902 + 1,200 = 9,102.
    out = ok("individual_income_tax", "2027-28", taxable_income=60000, private_hospital_cover=True,
             net_labour_income=60000)
    assert out["gross_tax"] == approx(8252)
    assert out["offsets"]["lito"] == approx(100)
    assert out["offsets"]["working_australians_tax_offset"] == approx(250)
    assert out["income_tax_after_offsets"] == approx(7902)
    assert out["medicare_levy"] == approx(1200)
    assert out["total_liability"] == approx(9102)
    out26 = ok("individual_income_tax", "2026-27", taxable_income=60000, private_hospital_cover=True)
    assert out26["gross_tax"] == approx(8520)
    assert "working_australians_tax_offset" not in out26["offsets"]


@pytest.mark.parametrize("nli,expected", [
    (20000, 250),    # basic tax on 20,000 = 14% x (20,000 - 18,200) = 252 -> lesser of 250 and 252
    (19000, 112),    # 14% x 800 = 112, below the 250 cap
    (18200, 0),      # not above the tax-free threshold (s 61-155(1)(b))
])
def test_working_australians_tax_offset_amount(nli, expected):
    # Taxable income set high (100,000) so the offset is not capped by the tax payable; the amount depends only on the
    # net labour income (s 61-160).
    out = ok("individual_income_tax", "2027-28", taxable_income=100000, private_hospital_cover=True, net_labour_income=nli)
    assert out["offsets"]["working_australians_tax_offset"] == approx(expected)


def test_working_australians_tax_offset_cannot_exceed_tax_payable(monkeypatch):
    # TI 19,000: gross tax = 14% x 800 = 112; LITO at 19,000 = 700 but limited to the tax, 112; nothing left for the
    # working Australians tax offset (non-refundable, s 63-10): tax after offsets 0.
    # (The 2027-28 Medicare low-income threshold is unpublished, so a test-only value is set here to reach the offsets
    # for income this low; it is restored after the test.)
    med = figures_module.load_year("2027-28")["medicare"]["low_income_single_lower"]
    monkeypatch.setitem(med, "value", 20000)
    monkeypatch.setitem(med, "status", "VERIFIED")
    out = ok("individual_income_tax", "2027-28", taxable_income=19000, private_hospital_cover=True, net_labour_income=19000)
    assert out["gross_tax"] == approx(112)
    assert out["offsets"]["lito"] == approx(112)
    assert out["offsets"]["working_australians_tax_offset"] == 0
    assert out["income_tax_after_offsets"] == 0


def test_working_australians_tax_offset_not_applied_without_net_labour_income_or_for_non_residents():
    out = ok("individual_income_tax", "2027-28", taxable_income=60000, private_hospital_cover=True)
    assert out["offsets"]["working_australians_tax_offset"] == 0
    assert any("net_labour_income" in w for w in out["warnings"])
    out = ok("individual_income_tax", "2027-28", taxable_income=60000, residency="foreign", net_labour_income=60000)
    assert out["offsets"]["working_australians_tax_offset"] == 0
    out = ok("individual_income_tax", "2026-27", taxable_income=60000, private_hospital_cover=True,
             net_labour_income=60000)
    assert any("starts with the 2027-28" in w for w in out["warnings"])


def test_2027_28_medicare_levy_surcharge_thresholds_unpublished_refuse_when_needed():
    # medicare.mls_single_tiers and mls_family_tiers are null for 2027-28. The surcharge is nil for a person with cover
    # all year, so no figure is needed; without cover, or with days without cover, the amount depends on the missing
    # thresholds: refuse AU-GEN-003 (no draft possible).
    out = ok("individual_income_tax", "2027-28", taxable_income=120000, private_hospital_cover=True)
    assert out["medicare_levy_surcharge"] == 0
    for kw in ({"private_hospital_cover": False}, {"private_hospital_cover": True, "days_without_cover": 30}):
        for allow in (False, True):
            code, res = call("individual_income_tax", "2027-28", allow_draft=allow, taxable_income=120000, **kw)
            assert code == 4 and res["refusal"]["code"] == "AU-GEN-003", kw
            assert "medicare.mls_single_tiers" in res["refusal"]["detail"]
    # Cover not stated: no contingent amount can be shown; the total excludes it and says so.
    out = ok("individual_income_tax", "2027-28", taxable_income=120000)
    assert out["medicare_levy_surcharge"] == 0 and out["mls_detail"]["applies"] is False
    assert any("surcharge" in w for w in out["warnings"])
    # Family: the family tiers are the missing figure.
    code, res = call("individual_income_tax", "2027-28", taxable_income=120000, has_spouse=True,
                     spouse_taxable_income=50000, private_hospital_cover=False)
    assert code == 4 and "medicare.mls_family_tiers" in res["refusal"]["detail"]


def test_2027_28_help_repayment_refuses_because_the_schedule_is_unpublished():
    code, res = call("individual_income_tax", "2027-28", allow_draft=True, taxable_income=90000, has_help_debt=True,
                     private_hospital_cover=True)
    assert code == 4 and res["refusal"]["code"] == "AU-GEN-003"
    assert "help.repayment_schedule" in res["refusal"]["detail"]


def test_2027_28_is_a_366_day_year_for_medicare_exemption_days():
    # 1 Jul 2027 to 30 Jun 2028 includes 29 Feb 2028: 366 days. Full Medicare exemption for 183 days of a resident's
    # year: levy 2% x 100,000 = 2,000 x (1 - 183/366) = 2,000 x 0.5 = 1,000 (MLA s 9 apportionment by days).
    # The 365-day 2026-27 year: 2,000 x (1 - 183/365) = 997.26.
    out = ok("individual_income_tax", "2027-28", taxable_income=100000, private_hospital_cover=True,
             medicare_full_exemption_days=183)
    assert out["medicare_levy"] == approx(1000)
    assert out["medicare_levy_detail"]["exemption_days"]["days_in_year"] == 366
    out = ok("individual_income_tax", "2026-27", taxable_income=100000, private_hospital_cover=True,
             medicare_full_exemption_days=183)
    assert out["medicare_levy"] == approx(997.26)
    assert out["medicare_levy_detail"]["exemption_days"]["days_in_year"] == 365


def test_2027_28_medicare_low_income_range_refuses():
    # The 2027-28 low-income thresholds are unpublished (null). Income inside the possible range (30,000) cannot be
    # screened against current law, so the levy cannot be given: AU-GEN-003, no draft possible.
    for allow in (False, True):
        code, res = call("individual_income_tax", "2027-28", allow_draft=allow, taxable_income=30000,
                         private_hospital_cover=True)
        assert code == 4 and res["refusal"]["code"] == "AU-GEN-003"
        assert "medicare.low_income_single_lower" in res["refusal"]["detail"]


# ============================================================ payg-lodgment: date-effective penalty unit

def test_failure_to_lodge_penalty_unit_comes_from_the_due_dates_own_year(monkeypatch):
    # Due 1 Sep 2027 (2027-28), 30 days late: periods = ceil(30 / 28) = 2 base units; penalty = 2 x the penalty unit in
    # force on the due date. The 2027-28 file holds 364 (Crimes Act s 4AA); the 2026-27 file's unit is poisoned to 999 to
    # show the old "everything from 1 Jul 2026 reads 2026-27" behaviour is gone: 2 x 364 = 728.
    monkeypatch.setitem(figures_module.load_year("2026-27")["penalties_interest"]["penalty_unit"], "value", 999)
    out = ok("failure_to_lodge_penalty", "2026-27", days_late=30, due_date="2027-09-01")
    assert out["penalty"] == approx(728)
    assert any(f["key"] == "penalties_interest.penalty_unit@2027-28" for f in out["figures_used"])
    # A due date in 2028-29 has no rates file: refuse, do not reuse another year's unit.
    code, res = call("failure_to_lodge_penalty", "2026-27", days_late=30, due_date="2028-09-01")
    assert code == 3 and res["refusal"]["code"] == "AU-PAYG-002"


# ============================================================ 2027-28 au-indonesia overlay

def test_au_indonesia_treaty_constants_carry_into_2027_28_as_verified():
    # Treaty text (ATO synthesised text, re-read 2026-09-29): Art 5(2)(j) more than 120 days; Art 18(2) pensions 15%;
    # Art 10(6) branch profits 15%; Art 24(2) not less than 10% voting power; Art 20(1) 2 years; Art 25(1) 3 years.
    # Withholding Tax Act 1974 s 7: dividends 30%, interest 10%, royalties 30%.
    f = Figures("2027-28")
    expected = {"dta_pe_services_days": 120, "dta_pe_building_site_days": 120, "dta_pe_resource_installation_days": 120,
                "dta_wht_pensions_annuities": 0.15, "dta_branch_profits_additional_tax_cap": 0.15,
                "dta_underlying_tax_credit_min_voting_share": 0.1, "dta_teacher_visit_max_years": 2,
                "dta_map_case_presentation_years": 3, "au_wht_unfranked_dividend_rate": 0.3, "au_wht_interest_rate": 0.1,
                "au_wht_royalty_rate": 0.3}
    for name, value in expected.items():
        assert f.get(f"au_indonesia.{name}") == pytest.approx(value), name
    out = ok("au_withholding_indonesian_payee", "2027-28", payment_kind="dividend", unfranked_amount=10000,
             payee_resident_of_indonesia=True, beneficially_entitled=True)
    assert out["withholding"] == approx(1500)      # 10,000 x the 15% treaty cap in Art 10(2)


def test_au_indonesia_2027_28_unpublished_figures_are_null_with_checked_at_and_refuse():
    import datetime as dt
    data = figures_module.load_year("2027-28")["au_indonesia"]
    unpublished = ["foreign_assets_reporting_threshold", "fx_idr_per_aud_average_year_to_30_jun",
                   "fx_idr_per_aud_nearest_actual_30_jun"] + [
        f"fx_idr_per_aud_monthly_average_{m}" for m in
        ("jul", "aug", "sep", "oct", "nov", "dec", "jan", "feb", "mar", "apr", "may", "jun")]
    for k in unpublished:
        assert data[k]["value"] is None and data[k]["status"] == "SUSPECT" and data[k]["checked_at"] == dt.date(2026, 9, 29), k
        assert data[k]["source"].startswith("https://www.ato.gov.au/"), k
    # No rupiah rate is invented for 2027-28: the tool refuses AU-GEN-003 (exit 4), in draft mode too.
    for allow in (False, True):
        code, res = call("idr_to_aud", "2027-28", allow_draft=allow, idr_amount=240000000,
                         translation_basis="annual_average", nature="income_or_deduction_spread_over_year")
        assert code == 4 and res["refusal"]["code"] == "AU-GEN-003"
        code, res = call("idr_to_aud", "2027-28", allow_draft=allow, idr_amount=100000000,
                         translation_basis="monthly_average", nature="single_dated_item", event_date="2027-09-15")
        assert code == 4 and res["refusal"]["code"] == "AU-GEN-003"
    # A rate the user supplies with its source is evidence, not a figure of ours: it still works.
    out = ok("idr_to_aud", "2027-28", idr_amount=150000000, translation_basis="supplied_rate",
             nature="single_dated_item", event_date="2027-09-15", supplied_rate_idr_per_aud=10000,
             supplied_rate_source="RBA daily rate (illustrative)")
    assert out["aud_amount"] == approx(15000)      # 150,000,000 / 10,000


# ============================================================ 2027-28 short-stay overlay carries the SERR constants

def test_short_stay_2027_28_overlay_is_verified_and_mirrors_2026_27():
    a, b = figures_module.load_year("2026-27")["shortstay"], figures_module.load_year("2027-28")["shortstay"]
    assert set(a) == set(b)
    assert all(b[k]["status"] == "VERIFIED" and b[k]["value"] == a[k]["value"] for k in a)


# ============================================================ Figures.for_year

def test_for_year_reports_figures_under_the_other_years_key_and_does_not_nest():
    root = Figures("2026-27")
    other = root.for_year("2027-28")
    assert other is not root and root.for_year("2026-27") is root
    assert other.get("cgt.discount_individual_trust") == 0          # the 2027-28 residual rate
    assert root.used["cgt.discount_individual_trust@2027-28"].value == 0
    assert other.for_year("2027-28") is other
    assert other.for_year("2026-27") is root                          # views delegate to the root, never nest
    with pytest.raises(FigureError) as e:
        root.for_year("2031-32")
    assert e.value.code == "AU-GEN-003"
