"""au-indonesia-cross-border calculators. Expected values are hand computations shown step by step from the
Australia-Indonesia agreement (ATO synthesised text and tabled text), ITAA 1997 Div 770, the Income Tax
(Dividends, Interest and Royalties Withholding Tax) Act 1974 s 7 and the ATO foreign exchange tables. None were
produced by running the calculators.

Rates used by the hand computations (2025-26 base file): resident scale 18,200 to 45,000 at 16 per cent, 45,000
to 135,000 at 30 per cent on a base of 4,288; Medicare levy 2 per cent (above the shade-out range); LITO 700
reducing to 325 at 45,000 then by 1.5 cents a dollar. 2026-27 scale: 15 per cent band, 30 per cent band on a
base of 4,020.
"""

import pytest

from au_tax.registry import load_all, run

TOOLS = (
    "indonesia_presence_window", "indonesia_service_pe_screen", "indonesia_treaty_allocation",
    "indonesia_treaty_fito", "au_withholding_indonesian_payee", "idr_to_aud", "indonesia_scope_check",
)


def ok(name, year, **kw):
    code, out = run(name, year, kw)
    assert code == 0, out
    return out


def refused(name, year, expected_code, exit_code=3, **kw):
    code, out = run(name, year, kw)
    assert code == exit_code, out
    assert out["refusal"]["code"] == expected_code, out
    return out


def approx(x):
    return pytest.approx(x, abs=0.01)


def test_registered_as_tools():
    tools = load_all()
    for t in TOOLS:
        assert t in tools
    assert "indonesia_dta_check" in tools and "foreign_income_tax_offset" in tools  # reused, not replaced


# ============================================================ presence window (Arts 14(1)(b), 15(2)(a))

def trips(*pairs):
    return [{"start": a, "end": b} for a, b in pairs]


def test_presence_two_trips_across_income_years_rolling_window():
    # ATO-style rolling 12 months, not the income year. Trip A 1 Apr to 30 Jun 2026 inclusive:
    #   April 30 + May 31 + June 30 = 91 days (2025-26). Trip B 1 Jul to 15 Aug 2026 inclusive:
    #   July 31 + Aug 15 = 46 days (2026-27). Each income year alone is under 120.
    # The 12 month window starting 1 Apr 2026 ends 31 Mar 2027 and holds both trips: 91 + 46 = 137 > 120.
    out = ok("indonesia_presence_window", "2026-27", trips=trips(("2026-04-01", "2026-06-30"), ("2026-07-01", "2026-08-15")))
    assert out["days_present_total"] == 137
    assert out["max_days_in_any_12_months"] == 137
    assert out["days_limit"] == 120
    assert out["exceeds_limit"] is True
    assert out["art14_presence_test_met"] is True
    assert out["art15_presence_condition_met"] is False
    by_year = {r["income_year"]: r["days"] for r in out["by_income_year"]}
    assert by_year == {"2025-26": 91, "2026-27": 46}
    assert out["max_window_start"] == "2026-04-01" and out["max_window_end"] == "2027-03-31"
    assert out["handoff"]["days_in_other_state_12m"] == 137
    keys = {f["key"] for f in out["figures_used"]}
    assert keys == {"residency.indonesia_dta_days_threshold"}  # existing key reused, no new duplicate


def test_presence_exactly_at_limit_is_not_exceeding():
    # 1 Jan to 30 Apr 2026 inclusive: 31 + 28 + 31 + 30 = 120. Art 15(2)(a) says "not exceeding 120" (met);
    # Art 14(1)(b) says "exceeding 120" (not met). One more day (to 1 May) = 121 exceeds.
    out = ok("indonesia_presence_window", "2025-26", trips=trips(("2026-01-01", "2026-04-30")))
    assert out["max_days_in_any_12_months"] == 120
    assert out["exceeds_limit"] is False
    assert out["art15_presence_condition_met"] is True and out["art14_presence_test_met"] is False
    out = ok("indonesia_presence_window", "2025-26", trips=trips(("2026-01-01", "2026-05-01")))
    assert out["max_days_in_any_12_months"] == 121 and out["exceeds_limit"] is True


def test_presence_overlapping_trips_count_each_day_once():
    # 1 to 10 Jan 2026 (10 days) and 5 to 15 Jan 2026 (11 days) overlap on 5 to 10 Jan (6 days).
    # Distinct days: 1 to 15 Jan = 15.
    out = ok("indonesia_presence_window", "2025-26", trips=trips(("2026-01-01", "2026-01-10"), ("2026-01-05", "2026-01-15")))
    assert out["days_present_total"] == 15 and out["max_days_in_any_12_months"] == 15


def test_presence_twelve_month_boundary():
    # A period of 12 months starting 1 Jan 2026 ends 31 Dec 2026. Days on 1 Jan 2026 and 31 Dec 2026 fit: 2.
    out = ok("indonesia_presence_window", "2026-27", trips=trips(("2026-01-01", "2026-01-01"), ("2026-12-31", "2026-12-31")))
    assert out["max_days_in_any_12_months"] == 2
    # 1 Jan 2026 and 1 Jan 2027 do not fit in one 12 month period (the window from 1 Jan 2026 ends 31 Dec 2026).
    out = ok("indonesia_presence_window", "2026-27", trips=trips(("2026-01-01", "2026-01-01"), ("2027-01-01", "2027-01-01")))
    assert out["days_present_total"] == 2 and out["max_days_in_any_12_months"] == 1


def test_presence_window_spanning_a_leap_day():
    # Window from 1 Mar 2027 ends 29 Feb 2028 (2028 is a leap year): days on 1 Mar 2027 and 29 Feb 2028 fit (2).
    # 1 Mar 2027 and 1 Mar 2028 do not (1).
    out = ok("indonesia_presence_window", "2026-27", trips=trips(("2027-03-01", "2027-03-01"), ("2028-02-29", "2028-02-29")))
    assert out["max_days_in_any_12_months"] == 2
    out = ok("indonesia_presence_window", "2026-27", trips=trips(("2027-03-01", "2027-03-01"), ("2028-03-01", "2028-03-01")))
    assert out["max_days_in_any_12_months"] == 1


def test_presence_rejects_end_before_start_and_unknown_fields():
    code, out = run("indonesia_presence_window", "2025-26", {"trips": trips(("2026-02-01", "2026-01-01"))})
    assert code == 2
    code, out = run("indonesia_presence_window", "2025-26", {"trips": trips(("2026-01-01", "2026-01-02")), "working_days_only": True})
    assert code == 2


# ============================================================ service PE screen (Art 5(2)(j))

def periods(*rows):
    return [{"person": p, "start": a, "end": b} for p, a, b in rows]


def test_service_pe_counting_methods_diverge_e5b():
    # Adelaide Pty Ltd sends A (1 Mar to 30 Apr 2026 = 31 + 30 = 61 days) and B (15 Mar to 15 May 2026 =
    # 17 + 30 + 15 = 62 days), both working every day, to the same Bali project.
    # Enterprise days (each day once): 1 Mar to 15 May = 31 + 30 + 15 = 76. Person days: 61 + 62 = 123.
    # Limit 120: enterprise method 76 is under; person method 123 is over. The text does not choose.
    out = ok("indonesia_service_pe_screen", "2025-26", same_or_connected_project=True,
             periods=periods(("A", "2026-03-01", "2026-04-30"), ("B", "2026-03-15", "2026-05-15")))
    assert out["enterprise_days_max_12m"] == 76
    assert out["person_days_max_12m"] == 123
    assert out["days_limit"] == 120
    assert out["exceeds_on_enterprise_days"] is False and out["exceeds_on_person_days"] is True
    assert out["screen_result"] == "methods_disagree"
    assert out["service_pe_indicated"] is None
    assert out["escalation"]["code"] == "AU-IDN-001"
    assert {f["key"] for f in out["figures_used"]} == {"au_indonesia.dta_pe_services_days"}


def test_service_pe_below_on_both_methods():
    # A: 1 to 31 Mar 2026 = 31 days. B: 1 to 15 Mar 2026 = 15 days. Enterprise days 31; person days 31 + 15 = 46. Both under 120.
    out = ok("indonesia_service_pe_screen", "2025-26", same_or_connected_project=True,
             periods=periods(("A", "2026-03-01", "2026-03-31"), ("B", "2026-03-01", "2026-03-15")))
    assert out["enterprise_days_max_12m"] == 31 and out["person_days_max_12m"] == 46
    assert out["screen_result"] == "below_limit_on_both_methods"
    assert out["service_pe_indicated"] is False
    assert "escalation" not in out or out["escalation"] is None


def test_service_pe_above_on_both_methods():
    # One person 1 Mar to 30 Jul 2026: 31 + 30 + 31 + 30 + 30 = 152 days. Enterprise days 152; person days 152. Both over 120.
    out = ok("indonesia_service_pe_screen", "2025-26", same_or_connected_project=True,
             periods=periods(("A", "2026-03-01", "2026-07-30")))
    assert out["enterprise_days_max_12m"] == 152 and out["person_days_max_12m"] == 152
    assert out["screen_result"] == "above_limit_on_both_methods"
    assert out["service_pe_indicated"] is True
    assert out["escalation"]["code"] == "AU-IDN-001"  # attribution of profits (Art 7) is not computed


def test_service_pe_uses_any_12_month_window_not_the_total():
    # One person: 1 Jan to 10 Apr 2026 (31 + 28 + 31 + 10 = 100 days) and 1 to 30 Jan 2027 (30 days). Total 130.
    # A 12 month window starting on day s in Jan 2026 holds (100 - (s - 1 Jan)) days of the first trip and
    # (s - 1 Jan) days of January 2027: always 100. Max 100 < 120 on both methods.
    out = ok("indonesia_service_pe_screen", "2026-27", same_or_connected_project=True,
             periods=periods(("A", "2026-01-01", "2026-04-10"), ("A", "2027-01-01", "2027-01-30")))
    assert out["enterprise_days_total"] == 130
    assert out["enterprise_days_max_12m"] == 100 and out["person_days_max_12m"] == 100
    assert out["screen_result"] == "below_limit_on_both_methods"


def test_service_pe_same_person_overlapping_periods_not_double_counted():
    # Person A listed twice for 1 to 10 Jan 2026 and 5 to 15 Jan 2026: distinct days 15, so person days 15 (not 21).
    out = ok("indonesia_service_pe_screen", "2025-26", same_or_connected_project=True,
             periods=periods(("A", "2026-01-01", "2026-01-10"), ("A", "2026-01-05", "2026-01-15")))
    assert out["person_days_max_12m"] == 15 and out["enterprise_days_max_12m"] == 15


def test_service_pe_unconnected_projects_are_not_aggregated_so_refuse():
    refused("indonesia_service_pe_screen", "2025-26", "AU-IDN-001", same_or_connected_project=False,
            periods=periods(("A", "2026-03-01", "2026-03-31")))


# ============================================================ treaty allocation (Arts 6, 7, 13, 16, 17, 18, 22)

def alloc(**kw):
    base = {"residence_state": "australia", "source_state": "indonesia"}
    base.update(kw)
    return ok("indonesia_treaty_allocation", "2025-26", **base)


def test_allocation_real_property_income_art6_no_cap():
    out = alloc(income_type="real_property_income")
    assert out["article"] == "Art 6(1), (4)"
    assert out["other_state"] == "indonesia" and out["other_state_may_tax"] is True
    assert out["treaty_limit_rate"] is None
    assert "indonesia_treaty_fito" in out["relief"]


def test_allocation_directors_fees_art16_no_days_test():
    out = alloc(income_type="directors_fees")
    assert out["article"] == "Art 16" and out["other_state_may_tax"] is True
    assert "days" in out["notes"][0] and out["treaty_limit_rate"] is None


def test_allocation_pension_art18_cap_from_key():
    # Art 18(1): residence State only; Art 18(2): source State may tax up to 15 per cent of the gross amount.
    out = alloc(income_type="pension_annuity")
    assert out["article"] == "Art 18(2)"
    assert out["other_state_may_tax"] is True and out["treaty_limit_rate"] == 0.15
    assert {f["key"] for f in out["figures_used"]} == {"au_indonesia.dta_wht_pensions_annuities"}


def test_allocation_business_profits_needs_pe_fact():
    out = alloc(income_type="business_profits")
    assert out["other_state_may_tax"] is None and out["escalation"]["code"] == "AU-IDN-001"
    out = alloc(income_type="business_profits", pe_or_fixed_base_in_source_state=False)
    assert out["article"] == "Art 7(1)" and out["other_state_may_tax"] is False and out.get("escalation") is None
    out = alloc(income_type="business_profits", pe_or_fixed_base_in_source_state=True)
    assert out["other_state_may_tax"] is True and out["escalation"]["code"] == "AU-IDN-001"  # attribution not computed


def test_allocation_company_pe_adds_branch_profits_cap():
    out = alloc(income_type="business_profits", pe_or_fixed_base_in_source_state=True, enterprise_is_company=True)
    assert out["branch_profits_additional_tax_cap"] == 0.15
    assert "au_indonesia.dta_branch_profits_additional_tax_cap" in {f["key"] for f in out["figures_used"]}


def test_allocation_gains():
    out = alloc(income_type="real_property_gain")
    assert out["article"] == "Art 13(1)" and out["other_state_may_tax"] is True and out["treaty_limit_rate"] is None
    # Shares that are not land-rich: Art 13(5) leaves the gain to domestic law, no treaty answer, no ceiling.
    out = alloc(income_type="share_gain", land_rich=False)
    assert out["article"] == "Art 13(5)" and out["other_state_may_tax"] is None
    assert out["treaty_limit_rate"] is None and out["escalation"] is None
    # Land-rich shares: Art 13(4) lets the property country tax; the MLI and s 3A interplay is escalated.
    out = alloc(income_type="share_gain", land_rich=True)
    assert out["article"] == "Art 13(4)" and out["other_state_may_tax"] is True and out["escalation"]["code"] == "AU-IDN-004"
    out = alloc(income_type="share_gain")
    assert out["other_state_may_tax"] is None and out["escalation"]["code"] == "AU-IDN-004"


def test_allocation_other_income_art22_source_state_may_also_tax():
    out = alloc(income_type="other_income")
    assert out["article"] == "Art 22(1), (2)" and out["other_state_may_tax"] is True
    out = alloc(income_type="other_income", source_state="australia")
    assert out["other_state_may_tax"] is False  # no cross-border source, nothing for Indonesia


def test_allocation_delegates_articles_already_modelled():
    for t, art in (("independent_services", "independent_services"), ("employment", "employment"),
                   ("dividend", "dividends"), ("interest", "interest"), ("royalty", "royalties")):
        out = alloc(income_type=t)
        assert out["delegate_tool"] == "indonesia_dta_check" and out["delegate_article"] == art
    out = alloc(income_type="dividend", residence_state="indonesia", source_state="australia")
    assert out["delegate_tool"] == "au_withholding_indonesian_payee"


def test_allocation_indonesian_resident_australian_source_property():
    out = alloc(income_type="real_property_income", residence_state="indonesia", source_state="australia")
    assert out["other_state"] == "australia" and out["other_state_may_tax"] is True
    assert "Art 24(3)" in out["relief"]


def test_allocation_same_state_means_no_treaty_claim():
    out = alloc(income_type="real_property_income", source_state="australia")
    assert out["cross_border"] is False and out["other_state_may_tax"] is False


# ============================================================ treaty capped foreign tax feeding FITO

def fito(year="2025-26", **kw):
    kw.setdefault("private_hospital_cover", True)
    return ok("indonesia_treaty_fito", year, **kw)


def test_fito_dividend_cap_limit_not_binding_e1():
    # Single, hospital cover, taxable income 120,000 including a gross 25,000 dividend from an Indonesian company
    # held personally. Indonesia withheld 5,000 (20 per cent, assumed for illustration).
    # Cap: 15 per cent x 25,000 = 3,750 counts; excess 5,000 - 3,750 = 1,250 is not FITO (seek refund from Indonesia).
    # Step 1: 4,288 + 0.30 x (120,000 - 45,000) = 26,788; levy 2,400; total 29,188.
    # Step 2 (taxable 95,000): 4,288 + 0.30 x 50,000 = 19,288; levy 1,900; total 21,188. Limit 8,000.
    # Offset = min(3,750, 8,000) = 3,750. No LITO at this income. Tax payable after FITO 29,188 - 3,750 = 25,438.
    out = fito(items=[{"kind": "dividend", "gross_aud": 25000, "foreign_tax_paid_aud": 5000}], taxable_income=120000)
    assert out["creditable_foreign_tax"] == approx(3750)
    assert out["excess_over_treaty_cap"] == approx(1250)
    assert out["fito"]["offset_limit"] == approx(8000)
    assert out["fito"]["offset_after_limit"] == approx(3750)
    assert out["fito"]["tax_payable_after_fito"] == approx(25438)
    assert out["items"][0]["treaty_limit_rate"] == 0.15
    keys = {f["key"] for f in out["figures_used"]}
    assert "residency.indonesia_dta_wht_dividends" in keys and "residency.fito_default_offset_limit" in keys


def test_fito_dividend_cap_2026_27_variant():
    # 2026-27: step 1 = 4,020 + 0.30 x 75,000 = 26,520; levy 2,400; total 28,920.
    # Step 2 (95,000): 4,020 + 0.30 x 50,000 = 19,020; levy 1,900; total 20,920. Limit 8,000. Offset 3,750.
    # After FITO 28,920 - 3,750 = 25,170.
    out = fito("2026-27", items=[{"kind": "dividend", "gross_aud": 25000, "foreign_tax_paid_aud": 5000}], taxable_income=120000)
    assert out["fito"]["offset_limit"] == approx(8000)
    assert out["fito"]["tax_payable_after_fito"] == approx(25170)


def test_fito_rent_limit_binds_and_interest_not_disregarded_e2():
    # Taxable 60,000 includes net Bali rent 12,000 (gross 20,000 less non-debt deductions 8,000).
    # Indonesian tax on the rent 4,000 (assumed correctly imposed; Art 6 has no ceiling).
    # Step 1 (60,000): 4,288 + 0.30 x 15,000 = 8,788; levy 1,200; = 9,988.
    # Step 2 (60,000 - 12,000 = 48,000): 4,288 + 0.30 x 3,000 = 5,188; levy 960; = 6,148.
    # Limit 9,988 - 6,148 = 3,840. Offset = min(4,000, 3,840) = 3,840; 160 is lost.
    # LITO at 60,000 = 325 - 0.015 x 15,000 = 100 applied first: tax after LITO 9,888; after FITO 6,048.
    out = fito(items=[{"kind": "rent_real_property", "gross_aud": 20000, "foreign_tax_paid_aud": 4000}],
               related_deductions_aud=8000, taxable_income=60000)
    assert out["foreign_net_income_step2"] == approx(12000)
    assert out["fito"]["offset_limit"] == approx(3840)
    assert out["fito"]["offset_after_limit"] == approx(3840)
    assert out["fito"]["foreign_tax_lost"] == approx(160)
    assert out["fito"]["tax_payable_after_lito_before_fito"] == approx(9888)
    assert out["fito"]["tax_payable_after_fito"] == approx(6048)
    assert out["excess_over_treaty_cap"] == 0  # Art 6 has no treaty ceiling
    assert any("correctly imposed" in w for w in out["warnings"])  # Indonesian correctness is not verified


def test_fito_villa_loan_interest_stays_in_step2_income():
    # Same rent but 3,000 villa loan interest is a debt deduction (not attributable to an overseas PE): claimed
    # as a normal deduction, so taxable income is 57,000 and step 2 removes only the 12,000 net rent.
    # Step 2 (57,000 - 12,000 = 45,000): 4,288; levy 900; = 5,188. Step 1 (57,000): 4,288 + 0.30 x 12,000 = 7,888;
    # levy 1,140; = 9,028. Limit = 9,028 - 5,188 = 3,840 (wrongly ignoring the interest gives 2,880).
    out = fito(items=[{"kind": "rent_real_property", "gross_aud": 20000, "foreign_tax_paid_aud": 4000}],
               related_deductions_aud=8000, taxable_income=57000)
    assert out["fito"]["offset_limit"] == approx(3840)
    assert any("debt deduction" in w for w in out["warnings"])


def test_fito_two_small_taxes_total_over_default_limit_e3():
    # Interest gross 4,000, Indonesia withheld 800: cap 10 per cent = 400 counts.
    # Royalty gross 5,000 for copyright (15 per cent tier), Indonesia withheld 1,000: cap 750 counts.
    # Each alone is under the default limit 1,000 but the total counting is 400 + 750 = 1,150, above it.
    # Taxable 80,000 incl. 9,000 gross. Step 1: 4,288 + 0.30 x 35,000 = 14,788; levy 1,600; = 16,388.
    # Step 2 (71,000): 4,288 + 0.30 x 26,000 = 12,088; levy 1,420; = 13,508. Limit 2,880. Offset 1,150.
    out = fito(items=[{"kind": "interest", "gross_aud": 4000, "foreign_tax_paid_aud": 800},
                      {"kind": "royalty_other", "gross_aud": 5000, "foreign_tax_paid_aud": 1000}], taxable_income=80000)
    assert out["creditable_foreign_tax"] == approx(1150)
    assert out["excess_over_treaty_cap"] == approx(400 + 250)
    assert out["fito"]["computed_limit"] == approx(2880)
    assert out["fito"]["offset_after_limit"] == approx(1150)
    assert [i["treaty_limit_rate"] for i in out["items"]] == [0.10, 0.15]


def test_fito_royalty_know_how_tier_and_default_limit_shortcut():
    # Know-how royalty gross 5,000, tax 1,000: 10 per cent tier = 500. With interest 400 the total is 900, at or below
    # the default limit 1,000, so no limit calculation is needed and the whole 900 is the offset (s 770-75 Note 1).
    out = fito(items=[{"kind": "interest", "gross_aud": 4000, "foreign_tax_paid_aud": 800},
                      {"kind": "royalty_equipment_know_how", "gross_aud": 5000, "foreign_tax_paid_aud": 1000}], taxable_income=80000)
    assert out["creditable_foreign_tax"] == approx(900)
    assert out["fito"]["computed_limit"] is None and out["fito"]["offset_after_limit"] == approx(900)


def test_fito_discounted_gain_apportions_foreign_tax_e9():
    # Sold a Bali villa held over 12 months. Gain before discount 100,000; discount 50 per cent leaves a net
    # capital gain of 50,000 in assessable income (from the cgt skill). Indonesia taxed the gain 8,000.
    # Creditable = 8,000 x 50,000 / 100,000 = 4,000. Taxable 130,000.
    # Step 1: 4,288 + 0.30 x 85,000 = 29,788; levy 2,600; = 32,388. Step 2 (80,000): 4,288 + 0.30 x 35,000 = 14,788;
    # levy 1,600; = 16,388. Limit 16,000. Offset min(4,000, 16,000) = 4,000. After FITO 32,388 - 4,000 = 28,388.
    out = fito(items=[{"kind": "capital_gain", "gross_aud": 100000, "assessable_aud": 50000, "foreign_tax_paid_aud": 8000}],
               taxable_income=130000)
    assert out["items"][0]["creditable_foreign_tax"] == approx(4000)
    assert out["items"][0]["not_creditable_non_assessable_part"] == approx(4000)
    assert out["fito"]["offset_limit"] == approx(16000)
    assert out["fito"]["offset_after_limit"] == approx(4000)
    assert out["fito"]["tax_payable_after_fito"] == approx(28388)


def test_fito_gain_absorbed_by_losses_gives_no_offset():
    # Net capital gain nil (losses absorb the gain): assessable 0, so creditable 8,000 x 0 / 100,000 = 0.
    out = fito(items=[{"kind": "capital_gain", "gross_aud": 100000, "assessable_aud": 0, "foreign_tax_paid_aud": 8000}],
               taxable_income=60000)
    assert out["creditable_foreign_tax"] == 0 and out["fito"]["offset_after_limit"] == 0


def test_fito_capital_gain_needs_assessable_amount():
    code, out = run("indonesia_treaty_fito", "2025-26", {"items": [{"kind": "capital_gain", "gross_aud": 100000, "foreign_tax_paid_aud": 8000}], "taxable_income": 130000})
    assert code == 2


def test_fito_nane_dividend_earns_no_offset():
    # ITAA 1997 s 768-5: a dividend to an Australian company with the participation interest is non-assessable
    # non-exempt income, so the Indonesian tax on it earns no FITO (ATO FITO guide Example 13).
    out = fito(items=[{"kind": "dividend", "gross_aud": 25000, "foreign_tax_paid_aud": 3750, "nane_dividend": True},
                      {"kind": "rent_real_property", "gross_aud": 10000, "foreign_tax_paid_aud": 500}], taxable_income=90000)
    assert out["items"][0]["creditable_foreign_tax"] == 0
    assert out["creditable_foreign_tax"] == approx(500)
    assert out["foreign_net_income_step2"] == approx(10000)  # the NANE dividend is not in taxable income


def test_fito_pension_uses_pension_cap_key():
    # Pension gross 20,000, tax 4,000: Art 18(2) cap 15 per cent = 3,000 counts; excess 1,000.
    out = fito(items=[{"kind": "pension_annuity", "gross_aud": 20000, "foreign_tax_paid_aud": 4000}], taxable_income=90000)
    assert out["creditable_foreign_tax"] == approx(3000) and out["excess_over_treaty_cap"] == approx(1000)


def test_fito_tax_below_cap_is_creditable_in_full():
    # Tax paid 1,000 on a 25,000 dividend is under the 3,750 ceiling: all of it is creditable, no excess.
    out = fito(items=[{"kind": "dividend", "gross_aud": 25000, "foreign_tax_paid_aud": 1000}], taxable_income=120000)
    assert out["creditable_foreign_tax"] == approx(1000) and out["excess_over_treaty_cap"] == 0


def test_fito_foreign_assets_reporting_flag_2025_26():
    # Supplementary return 2026 label P: Yes if overseas assets were worth the threshold or more at any time.
    out = fito(items=[{"kind": "rent_real_property", "gross_aud": 10000, "foreign_tax_paid_aud": 500}], taxable_income=70000,
               overseas_assets_max_value_aud=50000)
    assert out["foreign_assets_label_p_yes"] is True
    out = fito(items=[{"kind": "rent_real_property", "gross_aud": 10000, "foreign_tax_paid_aud": 500}], taxable_income=70000,
               overseas_assets_max_value_aud=49999)
    assert out["foreign_assets_label_p_yes"] is False


def test_fito_foreign_assets_reporting_2026_27_unpublished_refuses():
    code, out = run("indonesia_treaty_fito", "2026-27", {
        "items": [{"kind": "rent_real_property", "gross_aud": 10000, "foreign_tax_paid_aud": 500}], "taxable_income": 70000,
        "private_hospital_cover": True, "overseas_assets_max_value_aud": 80000})
    assert code == 4 and out["refusal"]["code"] == "AU-GEN-003"
    code, out = run("indonesia_treaty_fito", "2026-27", {
        "items": [{"kind": "rent_real_property", "gross_aud": 10000, "foreign_tax_paid_aud": 500}], "taxable_income": 70000,
        "private_hospital_cover": True})
    assert code == 0  # not asked, so the unpublished figure is not needed


def test_fito_reuses_existing_special_case_refusal():
    refused("indonesia_treaty_fito", "2025-26", "AU-RES-005", items=[{"kind": "rent_real_property", "gross_aud": 10000, "foreign_tax_paid_aud": 500}],
            taxable_income=70000, complications=["foreign_tax_refunded"])


def test_fito_input_checks():
    base = {"items": [{"kind": "rent_real_property", "gross_aud": 10000, "foreign_tax_paid_aud": 500}], "taxable_income": 70000}
    assert run("indonesia_treaty_fito", "2025-26", {**base, "spouse_taxable_income": 5000})[0] == 2  # spouse income without has_spouse
    assert run("indonesia_treaty_fito", "2025-26", {**base, "taxable_income": 5000})[0] == 2  # foreign income exceeds taxable income
    assert run("indonesia_treaty_fito", "2025-26", {**base, "related_deductions_aud": 20000})[0] == 2  # deductions exceed the income
    assert run("indonesia_treaty_fito", "2025-26", {**base, "items": []})[0] == 2


# ============================================================ Australian withholding on an Indonesian payee

def wht(year="2025-26", **kw):
    kw.setdefault("payee_resident_of_indonesia", True)
    kw.setdefault("beneficially_entitled", True)
    return ok("au_withholding_indonesian_payee", year, **kw)


def test_wht_unfranked_dividend_15_not_30():
    # 10,000 unfranked: domestic 30 per cent = 3,000; treaty cap 15 per cent = 1,500. Withhold 1,500; net 8,500.
    out = wht(payment_kind="dividend", unfranked_amount=10000)
    assert out["withholding"] == approx(1500) and out["net_paid"] == approx(8500)
    assert out["treaty_relief"] == approx(1500) and out["applied_rate"] == 0.15 and out["domestic_rate"] == 0.30


def test_wht_part_franked_dividend_withholds_on_unfranked_part_only():
    # 10,000 dividend, 60 per cent franked: unfranked 4,000 x 15 per cent = 600; franked 6,000 nil. Net 9,400.
    out = wht(payment_kind="dividend", unfranked_amount=4000, franked_amount=6000)
    assert out["withholding"] == approx(600) and out["net_paid"] == approx(9400)
    assert out["franked_withholding"] == 0


def test_wht_interest_no_treaty_reduction():
    # 10,000 interest: domestic 10 per cent = 1,000; cap 10 per cent = 1,000. Withhold 1,000, relief nil.
    out = wht(payment_kind="interest", gross_amount=10000)
    assert out["withholding"] == approx(1000) and out["treaty_relief"] == 0


def test_wht_royalty_tiers():
    # Know-how 10,000: domestic 3,000; cap 10 per cent = 1,000. Trademark licence 10,000: cap 15 per cent = 1,500.
    assert wht(payment_kind="royalty_equipment_know_how", gross_amount=10000)["withholding"] == approx(1000)
    assert wht(payment_kind="royalty_other", gross_amount=10000)["withholding"] == approx(1500)


def test_wht_not_beneficially_entitled_gets_domestic_rates():
    # Conduit or agent: no treaty limit, so 10,000 royalty at 30 per cent = 3,000; unfranked dividend 3,000.
    out = wht(payment_kind="royalty_other", gross_amount=10000, beneficially_entitled=False)
    assert out["withholding"] == approx(3000) and out["treaty_applied"] is False
    assert out["warnings"]
    out = wht(payment_kind="dividend", unfranked_amount=10000, beneficially_entitled=False)
    assert out["withholding"] == approx(3000)


def test_wht_payee_not_indonesian_resident_domestic_only():
    out = wht(payment_kind="royalty_other", gross_amount=10000, payee_resident_of_indonesia=False)
    assert out["withholding"] == approx(3000) and out["treaty_applied"] is False


def test_wht_effectively_connected_with_australian_pe_is_escalated():
    refused("au_withholding_indonesian_payee", "2025-26", "AU-IDN-001", payment_kind="royalty_other", gross_amount=10000,
            payee_resident_of_indonesia=True, beneficially_entitled=True, connected_with_australian_pe=True)


def test_wht_same_in_2026_27():
    out = wht("2026-27", payment_kind="dividend", unfranked_amount=10000)
    assert out["withholding"] == approx(1500)


def test_wht_input_shape():
    assert run("au_withholding_indonesian_payee", "2025-26", {"payment_kind": "dividend", "gross_amount": 100, "payee_resident_of_indonesia": True, "beneficially_entitled": True})[0] == 2
    assert run("au_withholding_indonesian_payee", "2025-26", {"payment_kind": "interest", "unfranked_amount": 100, "payee_resident_of_indonesia": True, "beneficially_entitled": True})[0] == 2


# ============================================================ rupiah translation

def test_idr_annual_average_for_spread_out_income_e7():
    # IDR 240,000,000 of villa rent received evenly over 2025-26. ATO average for the year ended 30 Jun 2026 is
    # 11,446.3586 IDR per A$1. 240,000,000 / 11,446.3586 = 20,967.37 (check: 20,967.37 x 11,446.3586 = 240,000,035).
    out = ok("idr_to_aud", "2025-26", idr_amount=240000000, translation_basis="annual_average", nature="income_or_deduction_spread_over_year")
    assert out["aud_amount"] == approx(20967.37) and out["rate_used"] == 11446.3586
    assert {f["key"] for f in out["figures_used"]} == {"au_indonesia.fx_idr_per_aud_average_year_to_30_jun"}


def test_idr_year_end_rate_is_not_a_substitute_for_spread_income():
    # 240,000,000 / 12,298 = 19,515.37 would understate by 1,452.00: the ATO does not allow a year-end rate for
    # foreign income not received in Australia in the year derived, so the tool refuses rather than use it.
    refused("idr_to_aud", "2025-26", "AU-IDN-006", idr_amount=240000000, translation_basis="actual_30_jun",
            nature="income_or_deduction_spread_over_year")


def test_idr_one_off_capital_event_on_30_june_uses_nearest_actual_e8():
    # Villa sold 30 Jun 2026 for IDR 3,600,000,000. ATO nearest actual rate at 30 Jun 2026 is 12,298.
    # 3,600,000,000 / 12,298 = 292,730.53. Cost base 3,000,000,000 at its own date's rate (assumed 10,000, supplied) = 300,000.
    out = ok("idr_to_aud", "2025-26", idr_amount=3600000000, translation_basis="actual_30_jun", nature="one_off_capital_event", event_date="2026-06-30")
    assert out["aud_amount"] == approx(292730.53)
    cost = ok("idr_to_aud", "2025-26", idr_amount=3000000000, translation_basis="supplied_rate", nature="one_off_capital_event",
              event_date="2018-03-01", supplied_rate_idr_per_aud=10000, supplied_rate_source="RBA daily rate 1 Mar 2018 (illustrative)")
    assert cost["aud_amount"] == approx(300000)
    assert out["aud_amount"] - cost["aud_amount"] == approx(-7269.47)  # capital loss in AUD although the rupiah gain is 20 per cent


def test_idr_average_rejected_for_one_off_capital_event():
    for basis, extra in (("annual_average", {}), ("monthly_average", {"month": "jun"})):
        refused("idr_to_aud", "2025-26", "AU-IDN-006", idr_amount=3600000000, translation_basis=basis, nature="one_off_capital_event", **extra)


def test_idr_actual_30_jun_needs_that_date():
    refused("idr_to_aud", "2025-26", "AU-IDN-006", idr_amount=1000000, translation_basis="actual_30_jun", nature="single_dated_item", event_date="2026-06-29")
    refused("idr_to_aud", "2025-26", "AU-IDN-006", idr_amount=1000000, translation_basis="actual_30_jun", nature="single_dated_item")


def test_idr_monthly_average_2025_26():
    # January 2026 average 11,410.4 IDR per A$1: 100,000,000 / 11,410.4 = 8,763.93.
    out = ok("idr_to_aud", "2025-26", idr_amount=100000000, translation_basis="monthly_average", nature="income_or_deduction_spread_over_year", month="jan")
    assert out["aud_amount"] == approx(8763.93) and out["rate_used"] == 11410.4


def test_idr_monthly_average_from_event_date():
    # A payment on 14 Jan 2026 (single dated item) can use the January average, month taken from the date.
    out = ok("idr_to_aud", "2025-26", idr_amount=100000000, translation_basis="monthly_average", nature="single_dated_item", event_date="2026-01-14")
    assert out["aud_amount"] == approx(8763.93)
    assert any("Indonesian tax" in w or "paid" in w for w in out["warnings"])


def test_idr_event_date_outside_income_year_refused():
    refused("idr_to_aud", "2025-26", "AU-IDN-006", idr_amount=100000000, translation_basis="monthly_average", nature="single_dated_item", event_date="2026-07-14")


def test_idr_2026_27_published_months_ok():
    # August 2026 average 12,653.3: 50,000,000 / 12,653.3 = 3,951.54.
    out = ok("idr_to_aud", "2026-27", idr_amount=50000000, translation_basis="monthly_average", nature="income_or_deduction_spread_over_year", month="aug")
    assert out["aud_amount"] == approx(3951.54)
    # July 2026 average 12,543.4348: 750,000,000 / 12,543.4348 = 59,792.23.
    out = ok("idr_to_aud", "2026-27", idr_amount=750000000, translation_basis="monthly_average", nature="income_or_deduction_spread_over_year", month="jul")
    assert out["aud_amount"] == approx(59792.23)


def test_idr_2026_27_unpublished_refuses_with_gen_003():
    for kw in ({"translation_basis": "monthly_average", "month": "sep"}, {"translation_basis": "monthly_average", "month": "jun"},
               {"translation_basis": "annual_average"}):
        code, out = run("idr_to_aud", "2026-27", {"idr_amount": 1000000, "nature": "income_or_deduction_spread_over_year", **kw})
        assert code == 4 and out["refusal"]["code"] == "AU-GEN-003", (kw, out)
    code, out = run("idr_to_aud", "2026-27", {"idr_amount": 1000000, "translation_basis": "actual_30_jun", "nature": "single_dated_item", "event_date": "2027-06-30"})
    assert code == 4 and out["refusal"]["code"] == "AU-GEN-003"


def test_idr_supplied_rate_needs_source_and_event_date_for_one_off():
    assert run("idr_to_aud", "2025-26", {"idr_amount": 1000000, "translation_basis": "supplied_rate", "nature": "one_off_capital_event",
                                          "event_date": "2026-03-10", "supplied_rate_idr_per_aud": 11800})[0] == 2  # no source
    assert run("idr_to_aud", "2025-26", {"idr_amount": 1000000, "translation_basis": "supplied_rate", "nature": "one_off_capital_event",
                                          "supplied_rate_idr_per_aud": 11800, "supplied_rate_source": "RBA"})[0] == 2  # no date for a one-off event
    out = ok("idr_to_aud", "2025-26", idr_amount=1000000, translation_basis="supplied_rate", nature="one_off_capital_event",
             event_date="2026-03-10", supplied_rate_idr_per_aud=12500, supplied_rate_source="RBA daily rate 10 Mar 2026 (illustrative)")
    assert out["aud_amount"] == approx(80.00)  # 1,000,000 / 12,500
    assert out["figures_used"] == []


def test_idr_average_on_one_off_named_in_trap_prompt_needs_the_event_rate():
    # "June 2026" for a one-off sale gives no day: neither the June monthly average nor the annual average is allowed.
    refused("idr_to_aud", "2025-26", "AU-IDN-006", idr_amount=3600000000, translation_basis="monthly_average", nature="one_off_capital_event", month="jun")


# ============================================================ scope check

def test_scope_check_none():
    out = ok("indonesia_scope_check", "2025-26", situations=[])
    assert out["in_scope"] is True


@pytest.mark.parametrize("situation,code", [
    ("pe_or_fixed_base_question", "AU-IDN-001"), ("dependent_agent", "AU-IDN-001"), ("building_site_or_installation", "AU-IDN-001"),
    ("indonesian_domestic_tax_question", "AU-IDN-002"), ("indonesian_domestic_residency", "AU-IDN-002"),
    ("indonesian_company_or_pt", "AU-IDN-003"), ("trust_or_partnership_with_indonesian_income", "AU-IDN-003"), ("related_party_charges", "AU-IDN-003"),
    ("land_rich_or_indirect_property_interest", "AU-IDN-004"),
    ("royalty_or_software_characterisation", "AU-IDN-005"), ("treaty_benefit_denial_or_conduit", "AU-IDN-005"),
    ("dual_resident_company", "AU-RES-001"), ("other_treaty_country", "AU-RES-001"),
    ("offshore_company_controlled", "AU-RES-002"), ("foreign_pension_or_super", "AU-RES-003"),
])
def test_scope_check_maps_situations_to_codes(situation, code):
    out = refused("indonesia_scope_check", "2025-26", code, situations=[situation])
    assert out["refusal"]["message"]


def test_scope_check_lists_every_code_when_several():
    out = refused("indonesia_scope_check", "2025-26", "AU-IDN-002", situations=["indonesian_domestic_tax_question", "land_rich_or_indirect_property_interest"])
    assert "AU-IDN-004" in out["refusal"]["detail"]


# ============================================================ overlay data

def test_overlay_keys_match_between_years_and_null_only_where_unpublished():
    import yaml
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "data" / "rates"
    a = yaml.safe_load((root / "2025-26.d" / "au_indonesia.yaml").read_text())["au_indonesia"]
    b = yaml.safe_load((root / "2026-27.d" / "au_indonesia.yaml").read_text())["au_indonesia"]
    assert set(a) == set(b)
    assert not [k for k, v in a.items() if v["value"] is None]  # everything read for 2025-26
    nulls = {k for k, v in b.items() if v["value"] is None}
    expected = {"foreign_assets_reporting_threshold", "fx_idr_per_aud_average_year_to_30_jun", "fx_idr_per_aud_nearest_actual_30_jun"} | {
        f"fx_idr_per_aud_monthly_average_{m}" for m in ("sep", "oct", "nov", "dec", "jan", "feb", "mar", "apr", "may", "jun")}
    assert nulls == expected
    assert all(b[k]["status"] == "SUSPECT" for k in nulls)


def test_source_cited_mli_figure_needs_draft_mode():
    from au_tax.figures import FigureError, Figures

    with pytest.raises(FigureError) as e:
        Figures("2025-26").get("au_indonesia.mli_land_rich_lookback_days")
    assert e.value.code == "AU-GEN-001"
    f = Figures("2025-26", allow_draft=True)
    assert f.get("au_indonesia.mli_land_rich_lookback_days") == 365 and f.draft is True
