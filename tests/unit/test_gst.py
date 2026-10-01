"""GST and BAS calculators. Expected values come from ATO worked examples (cited) or hand computation
shown step by step in comments. None were produced by running the calculators."""

import pytest

from au_tax.registry import load_all, run


def calc(name, payload, year="2026-27"):
    code, out = run(name, year, payload)
    assert code == 0, out
    return out


def refused(name, payload, year="2026-27"):
    code, out = run(name, year, payload)
    assert code == 3, out
    return out["refusal"]["code"]


def approx(x):
    return pytest.approx(x, abs=0.01)


def sale(amount, cls="taxable", **kw):
    return {"kind": "sale", "amount": amount, "classification": cls, **kw}


def buy(amount, cls="taxable", **kw):
    return {"kind": "purchase", "amount": amount, "classification": cls, **kw}


def test_all_registered():
    assert {"bas_gst_worksheet", "margin_scheme_gst", "gst_registration_check", "bas_due_date"} <= set(load_all())


# ---------------------------------------------------------------- margin scheme (ATO worked examples)

def test_margin_scheme_ato_example_john():
    # ATO "Calculating the GST payable" (margin scheme): land bought $500,000 from an unregistered seller,
    # house and land sold $900,000. Margin = 400,000; GST = 400,000 / 11 = 36,363.64; ATO reports
    # G1 $400,000 and 1A $36,363. GST at settlement example (same page family): purchaser withholds 7% of
    # $900,000 = $63,000; seller refund 63,000 - 36,363 = $26,637.
    out = calc("margin_scheme_gst", {"sale_price": 900000, "acquisition_price": 500000, "residential_withholding": True})
    assert out["margin"] == approx(400000)
    assert out["gst_on_margin"] == approx(36363.64)
    assert out["bas_labels_whole_dollars"] == {"G1": 400000, "1A": 36363}
    assert out["settlement_withholding"]["amount_withheld_by_purchaser"] == approx(63000)
    assert out["settlement_withholding"]["seller_credit_less_gst_bas_whole_dollars"] == 26637
    # full-price GST for comparison: 900,000 / 11 = 81,818.18
    assert out["gst_if_full_price"] == approx(81818.18)


def test_margin_scheme_ato_example_diane():
    # ATO example: vacant land bought $500,000, sold $720,000. Margin 220,000; GST = 220,000/11 = 20,000.
    out = calc("margin_scheme_gst", {"sale_price": 720000, "acquisition_price": 500000})
    assert out["gst_on_margin"] == approx(20000)
    assert out["bas_labels_whole_dollars"] == {"G1": 220000, "1A": 20000}
    assert "settlement_withholding" not in out


def test_margin_scheme_valuation_method():
    # Held since before 1 Jul 2000; approved valuation at 1 Jul 2000 of $300,000; sold $630,000.
    # Margin = 330,000; GST = 330,000 / 11 = 30,000.
    out = calc("margin_scheme_gst", {"sale_price": 630000, "margin_basis": "valuation", "approved_valuation": 300000})
    assert out["margin"] == approx(330000)
    assert out["gst_on_margin"] == approx(30000)


def test_margin_scheme_negative_margin_nothing_at_g1():
    # Sold $450,000, bought $500,000: margin -50,000 -> no GST, nothing at G1 (ATO margin scheme BAS page).
    out = calc("margin_scheme_gst", {"sale_price": 450000, "acquisition_price": 500000})
    assert out["gst_on_margin"] == 0
    assert out["bas_labels_whole_dollars"] == {"G1": 0, "1A": 0}
    assert out["warnings"]


def test_margin_scheme_refusals():
    assert refused("margin_scheme_gst", {"sale_price": 900000, "acquisition_price": 500000, "written_agreement": False}) == "AU-GST-006"
    assert refused("margin_scheme_gst", {"sale_price": 900000, "acquisition_price": 500000,
                                         "acquired_via_fully_taxable_supply": True}) == "AU-GST-006"
    assert refused("margin_scheme_gst", {"sale_price": 900000, "acquisition_price": 500000,
                                         "special_acquisition": ["from_associate"]}) == "AU-GST-001"


def test_margin_scheme_missing_cost_is_invalid_input():
    code, _ = run("margin_scheme_gst", "2026-27", {"sale_price": 900000})
    assert code == 2


# ---------------------------------------------------------------- BAS worksheet

def test_worksheet_simple_quarter():
    # Sales: taxable 55,000 incl GST; GST-free services to a non-resident 10,000 (G3); export of goods 5,000 (G2).
    # Purchases: stock 22,000 incl GST (G11); laptop 3,300 incl GST (G10, capital); bank fees 200 (no GST, G14);
    # wages 30,000 (not reported).
    # G1 = 55,000 + 10,000 + 5,000 = 70,000; G2 = 5,000; G3 = 10,000; G5 = 15,000; G6 = 55,000; G9 = 5,000.
    # G10 = 3,300; G11 = 22,000 + 200 = 22,200; G12 = 25,500; G14 = 200; G16 = 200; G17 = 25,300; G20 = 2,300.
    # Net GST = 5,000 - 2,300 = 2,700 payable.
    out = calc("bas_gst_worksheet", {"transactions": [
        sale(55000), sale(10000, "gst_free"), sale(5000, "export_goods"),
        buy(22000), buy(3300, capital=True), buy(200, "gst_free"), buy(30000, "out_of_scope", description="wages")]})
    w = out["worksheet"]
    assert w["G1"] == approx(70000) and w["G2"] == approx(5000) and w["G3"] == approx(10000)
    assert w["G6"] == approx(55000) and w["G9"] == approx(5000)
    assert w["G10"] == approx(3300) and w["G11"] == approx(22200) and w["G17"] == approx(25300)
    assert out["gst_on_purchases_1B"] == approx(2300)
    assert out["net_gst"] == approx(2700)
    assert out["bas_labels_whole_dollars"] == {"G1": 70000, "G2": 5000, "G3": 10000, "G10": 3300, "G11": 22200,
                                               "1A": 5000, "1B": 2300}
    assert any(e["item"] == "wages" for e in out["excluded"])


def test_worksheet_gst_exclusive_amounts_and_simpler_bas():
    # Taxable sale 10,000 ex GST -> 11,000 incl; taxable purchase 4,000 ex GST -> 4,400 incl.
    # 1A = 11,000/11 = 1,000; 1B = 4,400/11 = 400; net 600. Turnover 300,000 < Simpler BAS limit -> G1, 1A, 1B only.
    out = calc("bas_gst_worksheet", {"gst_turnover": 300000, "transactions": [
        sale(10000, gst_inclusive=False), buy(4000, gst_inclusive=False)]})
    assert out["reporting_method"] == "simpler"
    assert out["bas_labels_whole_dollars"] == {"G1": 11000, "1A": 1000, "1B": 400}
    assert out["net_gst"] == approx(600)


def test_worksheet_input_taxed_rent_and_private_use():
    # Sales: taxable consulting 33,000; residential rent 20,000 (input taxed, G4).
    # Purchases: repairs on rental 2,200 incl GST (for input taxed sales -> G13);
    # phone 1,100 incl GST, 60% business -> 40% (440) to G15.
    # G1 = 53,000; G4 = 20,000; G5 = 20,000; G6 = 33,000; 1A = 3,000.
    # G11 = 3,300; G13 = 2,200; G15 = 440; G16 = 2,640; G17 = 660; 1B = 60. Net = 2,940.
    out = calc("bas_gst_worksheet", {"transactions": [
        sale(33000), sale(20000, "input_taxed"),
        buy(2200, "input_taxed_use"), buy(1100, creditable_share=0.6)]})
    w = out["worksheet"]
    assert w["G4"] == approx(20000) and w["G13"] == approx(2200) and w["G15"] == approx(440)
    assert out["gst_on_sales_1A"] == approx(3000)
    assert out["gst_on_purchases_1B"] == approx(60)
    assert out["net_gst"] == approx(2940)
    assert "GST-RF-002" in out["risk_flags"] and "GST-RF-004" in out["risk_flags"]


def test_worksheet_refund_position_and_whole_dollars():
    # Sale 1,000 incl -> 1A = 90.909.. -> BAS 90. Capital purchase 16,500 incl -> 1B = 1,500. Net -1,409.09 refund.
    out = calc("bas_gst_worksheet", {"transactions": [sale(1000), buy(16500, capital=True)]})
    assert out["gst_on_sales_1A"] == approx(90.91)
    assert out["bas_labels_whole_dollars"]["1A"] == 90
    assert out["net_gst"] == approx(-1409.09)
    assert out["net_gst_position"] == "refundable"
    assert out["net_gst_whole_dollars"] == 90 - 1500


def test_worksheet_margin_scheme_line():
    # margin_scheme sale with margin 400,000 -> G1 400,000, 1A 36,363.64 (ATO John example).
    out = calc("bas_gst_worksheet", {"transactions": [sale(900000, "margin_scheme", margin=400000)]})
    assert out["worksheet"]["G1"] == approx(400000)
    assert out["bas_labels_whole_dollars"]["1A"] == 36363


def test_worksheet_reverse_charge_partly_input_taxed():
    # Offshore service 10,000 (no GST charged), 70% creditable, 30% for input taxed supplies.
    # ATO: report 10,000 x 1.1 = 11,000 at G1 and G11; GST payable 1,000 (1A);
    # G13 = 30% x 11,000 = 3,300; G17 = 7,700; 1B = 700. Net = 300 = 10% x 10,000 x 30%.
    out = calc("bas_gst_worksheet", {"transactions": [
        buy(10000, "reverse_charge", creditable_share=0.7, non_creditable_reason="input_taxed_use")]})
    w = out["worksheet"]
    assert w["G1"] == approx(11000) and w["G11"] == approx(11000) and w["G13"] == approx(3300)
    assert out["gst_on_sales_1A"] == approx(1000)
    assert out["gst_on_purchases_1B"] == approx(700)
    assert out["net_gst"] == approx(300)


def test_worksheet_reverse_charge_wholly_creditable_does_not_apply():
    # Fully creditable offshore service 5,000: no reverse charge (s84-5(1)(b)); G11 5,000 and G14 5,000; nil GST.
    out = calc("bas_gst_worksheet", {"transactions": [buy(5000, "reverse_charge")]})
    assert out["worksheet"]["G1"] == 0 and out["worksheet"]["G14"] == approx(5000)
    assert out["net_gst"] == 0


def test_worksheet_bad_debt_accrual_and_cash():
    # Accruals: taxable sale 11,000 this period; bad debt written off on an earlier 2,200 incl GST invoice ->
    # decreasing adjustment GST 200 -> G18 = 2,200 -> 1B += 200. 1A = 1,000; 1B = 200; net 800.
    out = calc("bas_gst_worksheet", {"transactions": [sale(11000)],
                                     "adjustments": [{"gst_amount": 200, "reason": "bad_debt_written_off_by_supplier"}]})
    assert out["worksheet"]["G18"] == approx(2200)
    assert out["net_gst"] == approx(800)
    # Cash basis: adjustment not available (s21-5(2)); net 1,000.
    out = calc("bas_gst_worksheet", {"accounting_basis": "cash", "transactions": [sale(11000)],
                                     "adjustments": [{"gst_amount": 200, "reason": "bad_debt_written_off_by_supplier"}]})
    assert out["net_gst"] == approx(1000)
    assert "GST-RF-009" in out["risk_flags"]


def test_worksheet_increasing_adjustment_g7():
    # Recipient bad debt (s21-15): increasing adjustment GST 50 -> G7 = 550 -> 1A = 50.
    out = calc("bas_gst_worksheet", {"adjustments": [{"gst_amount": 50, "reason": "bad_debt_recipient_unpaid"}]})
    assert out["worksheet"]["G7"] == approx(550)
    assert out["gst_on_sales_1A"] == approx(50)


def test_worksheet_period_and_cash_attribution():
    # Period Jul-Sep 2026. Sale dated 15 Oct 2026 excluded. Cash basis: invoice 11,000 of which 5,500 paid -> 1A 500.
    out = calc("bas_gst_worksheet", {"accounting_basis": "cash", "period_start": "2026-07-01", "period_end": "2026-09-30",
                                     "transactions": [sale(11000, date="2026-08-10", amount_paid=5500),
                                                      sale(22000, date="2026-10-15")]})
    assert out["gst_on_sales_1A"] == approx(500)
    assert len(out["excluded"]) == 1


def test_worksheet_no_tax_invoice_defers_credit():
    # Purchase 1,100 incl GST (above the tax invoice threshold) without a tax invoice: left out this period.
    # A 55 purchase without invoice (below threshold) still counts: 1B = 5.
    out = calc("bas_gst_worksheet", {"transactions": [buy(1100, tax_invoice_held=False), buy(55, tax_invoice_held=False)]})
    assert out["gst_on_purchases_1B"] == approx(5)
    assert out["deferred_credits_no_tax_invoice_gst"] == approx(100)


def test_worksheet_payg_withholding_labels_and_summary():
    # W1 40,000; W2 8,000; W4 470; W3 0 -> W5 = 8,470 (W1 not included). GST: 1A 1,000, 1B 0.
    # Payable = 1,000 + 8,470 = 9,470.
    out = calc("bas_gst_worksheet", {"transactions": [sale(11000)],
                                     "payg_withholding": {"w1": 40000, "w2": 8000, "w4": 470}})
    assert out["payg_withholding_labels"]["W5"] == 8470
    assert out["summary"]["amount_payable"] == 9470


def test_worksheet_special_circumstances_refuse():
    assert refused("bas_gst_worksheet", {"special_circumstances": ["gst_group_or_branch"]}) == "AU-GST-004"
    assert refused("bas_gst_worksheet", {"special_circumstances": ["commercial_residential_premises"]}) == "AU-GST-002"
    assert refused("bas_gst_worksheet", {"special_circumstances": ["fuel_tax_credits"]}) == "AU-GST-007"


def test_worksheet_rejects_wrong_classification():
    code, _ = run("bas_gst_worksheet", "2026-27", {"transactions": [buy(100, "export_goods")]})
    assert code == 2


# ---------------------------------------------------------------- registration

def test_registration_at_threshold_meets_it():
    # s188-10(1): "at or above" the threshold. 75,000 current and projected -> must register.
    out = calc("gst_registration_check", {"current_gst_turnover": 75000, "projected_gst_turnover": 75000})
    assert out["must_register"] and out["status"] == "must_register"
    assert out["registration_deadline_days"] == 21


def test_registration_just_below():
    out = calc("gst_registration_check", {"current_gst_turnover": 74999, "projected_gst_turnover": 74999})
    assert out["status"] == "not_required"


def test_registration_nfp_threshold():
    # Non-profit with 140,000: below the NFP threshold (150,000) -> not required; business with same -> required.
    assert calc("gst_registration_check", {"entity_type": "non_profit", "current_gst_turnover": 140000,
                                           "projected_gst_turnover": 140000})["status"] == "not_required"
    assert calc("gst_registration_check", {"current_gst_turnover": 140000, "projected_gst_turnover": 140000})["must_register"]


def test_registration_projected_triggers_new_business():
    out = calc("gst_registration_check", {"current_gst_turnover": 10000, "projected_gst_turnover": 90000})
    assert out["status"] == "must_register"


def test_registration_current_above_projected_below():
    out = calc("gst_registration_check", {"current_gst_turnover": 80000, "projected_gst_turnover": 60000})
    assert out["status"] == "must_register_unless_ato_satisfied_projected_below"


def test_registration_ride_sourcing_any_turnover():
    out = calc("gst_registration_check", {"current_gst_turnover": 12000, "projected_gst_turnover": 12000,
                                          "supplies_taxi_or_ride_sourcing": True})
    assert out["status"] == "must_register"


def test_registration_input_taxed_residential_rent_excluded():
    # Host: 100,000 short-stay rent of residential premises (input taxed) + 20,000 taxable cleaning fees.
    # GST turnover = 120,000 - 100,000 = 20,000 -> not required.
    out = calc("gst_registration_check", {"current_gst_turnover": 120000, "projected_gst_turnover": 120000,
                                          "input_taxed_sales_included": 100000})
    assert out["current_gst_turnover"] == approx(20000)
    assert out["status"] == "not_required"


def test_registration_capital_asset_sale_excluded_from_projected():
    # Projected 100,000 includes a 40,000 truck sale -> 60,000 projected; current 50,000 -> not required.
    out = calc("gst_registration_check", {"current_gst_turnover": 50000, "projected_gst_turnover": 100000,
                                          "projected_capital_asset_sales_included": 40000})
    assert out["projected_gst_turnover"] == approx(60000)
    assert out["status"] == "not_required"


def test_registration_gst_inclusive_figures():
    # 82,500 incl GST, all taxable -> 82,500 x 10/11 = 75,000 -> meets threshold.
    out = calc("gst_registration_check", {"current_gst_turnover": 82500, "projected_gst_turnover": 82500,
                                          "amounts_include_gst": True})
    assert out["current_gst_turnover"] == approx(75000)
    assert out["must_register"]


def test_registration_group_refused():
    assert refused("gst_registration_check", {"in_gst_group": True}) == "AU-GST-004"


# ---------------------------------------------------------------- due dates

@pytest.mark.parametrize("payload,expected", [
    # Q1 2026-27 (Jul-Sep 2026): original 28 Oct 2026 (Wed); online + 14 days = 11 Nov 2026 (Wed).
    ({"quarter": 1, "lodgment": "paper"}, "2026-10-28"),
    ({"quarter": 1, "lodgment": "online_self"}, "2026-11-11"),
    # Agent lodgment program Q1 2026-27: 25 Nov 2026 (ATO agent program page).
    ({"quarter": 1, "lodgment": "registered_agent"}, "2026-11-25"),
    # Q2: 28 Feb 2027 is a Sunday and Mon 1 Mar 2027 is Labour Day (WA) -> Tue 2 Mar 2027 (ATO table, 1 Mar 2027 row),
    # no concession for any channel. (Expected 1 Mar 2027 before public holidays were wired in.)
    ({"quarter": 2, "lodgment": "online_self"}, "2027-03-02"),
    ({"quarter": 2, "lodgment": "registered_agent"}, "2027-03-02"),
    # Q3: 28 Apr 2027 (Wed); online 12 May 2027 (Wed); agent 26 May 2027.
    ({"quarter": 3, "lodgment": "online_self"}, "2027-05-12"),
    ({"quarter": 3, "lodgment": "registered_agent"}, "2027-05-26"),
    # Monthly: July 2026 BAS due 21 Aug 2026 (Fri).
    ({"cycle": "monthly", "month": 7}, "2026-08-21"),
    # Monthly: Nov 2026 BAS due 21 Dec 2026 (Mon).
    ({"cycle": "monthly", "month": 11}, "2026-12-21"),
    # December monthly (small, electronic): 21 Feb 2027 is a Sunday -> 22 Feb 2027.
    ({"cycle": "monthly", "month": 12}, "2027-02-22"),
])
def test_due_dates_2026_27(payload, expected):
    assert calc("bas_due_date", payload)["due_date"] == expected


def test_due_date_q4_2025_26_agent():
    # Q4 2025-26 (Apr-Jun 2026): original 28 Jul 2026; agent program 25 Aug 2026; online 11 Aug 2026.
    assert calc("bas_due_date", {"quarter": 4, "lodgment": "registered_agent"}, "2025-26")["due_date"] == "2026-08-25"
    assert calc("bas_due_date", {"quarter": 4, "lodgment": "online_self"}, "2025-26")["due_date"] == "2026-08-11"


def test_due_date_q4_2026_27_agent_is_draft_only():
    # 25 Aug 2027 is "to be confirmed" on the ATO page (SOURCE-CITED) -> refused without allow_draft.
    code, out = run("bas_due_date", "2026-27", {"quarter": 4, "lodgment": "registered_agent"})
    assert code == 4 and out["refusal"]["code"] == "AU-GEN-001"


def test_due_date_large_business_no_online_concession():
    out = calc("bas_due_date", {"quarter": 1, "lodgment": "online_self", "gst_turnover": 25_000_000})
    assert out["due_date"] == "2026-10-28"


def test_due_date_roll_block_reports_reason_and_rule():
    # Q2 2026-27: Sunday 28 Feb 2027, then Labour Day (WA) Mon 1 Mar 2027.
    out = calc("bas_due_date", {"quarter": 2})
    assert out["original_due_date"] == "2027-02-28" and out["due_date"] == "2027-03-02"
    roll = out["business_day_roll"]
    assert roll["rolled"] and roll["regime"] == "commonwealth_tax" and "Labour Day" in roll["reason"]
    assert "8AAZMB" in roll["rule"]
    assert out["warnings"] == []


def test_monthly_december_bas_dates_need_no_holiday_roll():
    # Paper December 2026 BAS: 21 Jan 2027 (Thu, business day). December concession 21 Feb 2027 is a Sunday; Mon 22 Feb
    # 2027 is not a public holiday anywhere (ATO table), so the roll is weekend-only.
    assert calc("bas_due_date", {"cycle": "monthly", "month": 12, "lodgment": "paper"})["due_date"] == "2027-01-21"
    assert calc("bas_due_date", {"cycle": "monthly", "month": 12})["due_date"] == "2027-02-22"


def test_q2_2025_26_saturday_then_labour_day_wa():
    # Q2 2025-26 (Oct-Dec 2025): 28 Feb 2026 is a Saturday, Mon 2 Mar 2026 is Labour Day (WA) -> Tue 3 Mar 2026.
    out = calc("bas_due_date", {"quarter": 2}, "2025-26")
    assert out["original_due_date"] == "2026-02-28"
    assert out["due_date"] == "2026-03-03"


# ------------------------------------------------------------------ due dates after the holiday data (AU-GEN-004)

def test_bas_due_date_2027_28_q3_is_inside_the_holiday_data():
    # Quarter 3 (Jan-Mar 2028) online: 28 Apr 2028 is a Friday (1 Jul 2028 is a Saturday; 28 Apr is 64 days earlier and
    # 64 mod 7 = 1, so Friday); plus 14 days = 12 May 2028 (Friday). No holiday: no roll.
    out = calc("bas_due_date", {"cycle": "quarterly", "quarter": 3}, "2027-28")
    assert out["original_due_date"] == "2028-04-28" and out["due_date"] == "2028-05-12"


def test_bas_due_date_2027_28_q4_refuses_because_the_date_is_the_answer():
    # The due date IS the result here, so a date after the holiday data (28 Jul 2028) is refused, not guessed: a weekend-only
    # roll could give the wrong day (CONVENTIONS section 5: refuse, never fall back to weekends only).
    assert refused("bas_due_date", {"cycle": "quarterly", "quarter": 4}, "2027-28") == "AU-GEN-004"
    assert refused("bas_due_date", {"cycle": "quarterly", "quarter": 4, "lodgment": "paper"}, "2027-28") == "AU-GEN-004"


def test_bas_due_date_refusal_detail_names_the_date_outside_the_data():
    code, out = run("bas_due_date", "2027-28", {"cycle": "quarterly", "quarter": 4, "lodgment": "paper"})
    assert code == 3 and "2028-07-28" in out["refusal"]["detail"]
