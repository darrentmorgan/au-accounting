"""bookkeeping-year-end calculators. Expected values come from ATO worked examples (prepayments: the ATO
"Deductions for prepaid expenses" guide, dates shifted four years so they fall in years we hold rates for),
the Corporations Act s 45A / reg 1.0.02B thresholds, or hand computation shown in each test. None were produced
by running the calculators."""

import pytest

from au_tax.figures import Figures
from au_tax.registry import load_all, run


def ok(name, year="2026-27", **kw):
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
    assert {"trial_balance_check", "gst_control_reconciliation", "prepayment_deduction",
            "large_proprietary_test"} <= set(load_all())


# ------------------------------------------------------------ trial balance

def test_tb_balanced_with_ratios():
    # Debits: cash 10,000 + cost of sales 2,000 + expenses 1,000 = 13,000
    # Credits: income 8,000 + GST payable 500 + equity 4,500 = 13,000 -> balanced
    # gross margin = (8,000 - 2,000) / 8,000 = 0.75; net profit = 8,000 - 2,000 - 1,000 = 5,000; net margin = 0.625
    # current ratio = current assets 10,000 / current liabilities 500 = 20
    out = ok("trial_balance_check", accounts=[
        {"name": "Bank", "debit": 10000, "type": "asset", "current": True},
        {"name": "Sales", "credit": 8000, "type": "income"},
        {"name": "Purchases", "debit": 2000, "type": "cost_of_sales"},
        {"name": "Rent", "debit": 1000, "type": "expense"},
        {"name": "GST", "credit": 500, "type": "liability", "current": True},
        {"name": "Share capital", "credit": 4500, "type": "equity"},
    ])
    assert out["total_debits"] == 13000 and out["total_credits"] == 13000
    assert out["balanced"] is True and out["difference"] == 0
    r = out["ratios"]
    assert r["gross_margin"] == 0.75 and r["net_profit"] == 5000 and r["net_profit_margin"] == 0.625
    assert r["current_ratio"] == 20.0
    assert out["suspense"]["accounts"] == []


def test_tb_unbalanced_hints_and_suspense():
    # Debits 5,000 + 90 = 5,090; credits 5,000. Difference 90 = 9,000 cents, divisible by 9 -> transposition hint.
    # The suspense account (Dr 90) balance equals the difference -> "account balance equals the difference" hint.
    out = ok("trial_balance_check", accounts=[
        {"name": "Bank", "debit": 5000},
        {"name": "Suspense", "debit": 90},
        {"name": "Capital", "credit": 5000},
    ])
    assert out["balanced"] is False and out["difference"] == 90
    text = " ".join(out["hints"])
    assert "divisible by 9" in text and "equals the difference" in text
    assert out["suspense"]["net_debit_balance"] == 90
    assert out["warnings"]


def test_tb_reversed_entry_hint():
    # Debits 1,000 + 100 + 200 = 1,300; credits 700 + 400 = 1,100 -> difference 200.
    # Half the difference is 100, which matches the balance of account "Wrong side": a Dr 100 posted that should be a Cr 100.
    out = ok("trial_balance_check", accounts=[
        {"name": "A", "debit": 1000}, {"name": "Wrong side", "debit": 100}, {"name": "B", "debit": 200},
        {"name": "C", "credit": 700}, {"name": "D", "credit": 400},
    ])
    assert out["difference"] == 200
    assert any("wrong side" in h for h in out["hints"])


def test_tb_tolerance():
    out = ok("trial_balance_check", accounts=[{"name": "A", "debit": 100.004}, {"name": "B", "credit": 100}])
    assert out["balanced"] is True


def test_tb_invalid_negative_is_exit_2():
    code, _ = run("trial_balance_check", "2026-27", {"accounts": [{"name": "A", "debit": -5}]})
    assert code == 2


# ------------------------------------------------------------ GST control

def test_gst_recon_variance_and_inclusive_value():
    # 1A variance = 11,000 - 10,000 = 1,000 (ledger higher). GST rate 10%: a GST-inclusive item of 1,000 x 11 = 11,000
    # carries 1,000 GST. 1B agrees (4,000 vs 4,000). Net ledger 7,000 vs BAS 6,000 -> net variance 1,000.
    out = ok("gst_control_reconciliation", ledger_gst_collected=11000, ledger_gst_paid=4000, bas_1a=10000, bas_1b=4000)
    assert out["label_1a"]["variance"] == 1000 and out["label_1a"]["status"] == "variance"
    assert out["label_1b"]["status"] == "agrees"
    assert out["net_gst"]["ledger"] == 7000 and out["net_gst"]["bas"] == 6000 and out["net_gst"]["variance"] == 1000
    assert out["reconciled"] is False
    assert any("11000.00" in h for h in out["hints"])
    assert out["figures_used"][0]["key"] == "gst.rate"


def test_gst_recon_agrees_within_rounding():
    out = ok("gst_control_reconciliation", ledger_gst_collected=5000.40, ledger_gst_paid=1200.00, bas_1a=5000, bas_1b=1200)
    assert out["reconciled"] is True and out["label_1a"]["status"] == "agrees"


def test_gst_rate_checks_and_roll_forward():
    # Sales ex GST 100,000 x 10% = 10,000 expected; ledger 10,000 -> 0. Purchases 40,000 x 10% = 4,000 vs ledger 3,500 -> -500.
    # Roll-forward: opening payable 3,000 + collected 10,000 - paid 3,500 - ATO payment 3,000 = 6,500 expected closing.
    # Ledger closing 6,000 -> unexplained -500.
    out = ok("gst_control_reconciliation", ledger_gst_collected=10000, ledger_gst_paid=3500, bas_1a=10000, bas_1b=3500,
             ledger_taxable_sales_ex_gst=100000, ledger_creditable_purchases_ex_gst=40000,
             opening_balance_payable=3000, payments_to_ato=3000, closing_balance_payable=6000)
    rc = out["rate_checks"]
    assert rc["expected_gst_on_sales"] == 10000 and rc["gst_on_sales_vs_expected"] == 0
    assert rc["expected_gst_on_purchases"] == 4000 and rc["gst_on_purchases_vs_expected"] == -500
    assert out["roll_forward"]["expected_closing_balance_payable"] == 6500
    assert out["roll_forward"]["unexplained_difference"] == -500


# ------------------------------------------------------------ prepayments (ATO worked examples, dates +4 years)

def test_prepay_jacobs_12_month_rule_immediate():
    # ATO example (Jacobs Trust): $24,000 paid 1 Jun for a 12-month lease 1 Jul to 30 Jun; SBE; immediate deduction of $24,000.
    # Shifted: paid 1 Jun 2026, lease 1 Jul 2026 to 30 Jun 2027; year 2025-26.
    out = ok("prepayment_deduction", "2025-26", amount=24000, payment_date="2026-06-01", service_start="2026-07-01",
             service_end="2027-06-30", taxpayer="small_business")
    assert out["treatment"] == "immediate"
    assert out["deduction_in_requested_income_year"] == 24000
    assert out["schedule"] == [{"income_year": "2025-26", "days": None, "deduction": 24000.0}]
    assert out["twelve_month_rule"]["satisfied"] is True


def test_prepay_tom_apportioned_over_395_days():
    # ATO example (Tom Pty Ltd): $15,000 paid 31 May for 1 Jun to 30 Jun next year (395 days): 30 days in year 1,
    # 365 in year 2. 15,000 x 30 / 395 = 1,139 (ATO rounds); 15,000 x 365 / 395 = 13,861. Shifted +4 years.
    out = ok("prepayment_deduction", "2025-26", amount=15000, payment_date="2026-05-31", service_start="2026-06-01",
             service_end="2027-06-30", taxpayer="small_business")
    assert out["treatment"] == "apportioned"
    assert out["eligible_service_period"]["days"] == 395
    s = out["schedule"]
    assert s[0]["income_year"] == "2025-26" and s[0]["days"] == 30 and s[0]["deduction"] == approx(1139, 0.5)
    assert s[1]["income_year"] == "2026-27" and s[1]["days"] == 365 and s[1]["deduction"] == approx(13861, 0.5)
    assert sum(x["deduction"] for x in s) == approx(15000)
    assert out["deduction_in_requested_income_year"] == s[0]["deduction"]


def test_prepay_noel_ends_after_next_income_year():
    # ATO example (Noel Pty Ltd): $10,200 paid 30 Jun for 15 Jul to 14 Jul next year (365 days, within 12 months but
    # ends after the last day of the next income year). Year 1 nil; year 2: 10,200 x 351 / 365 = 9,809; year 3: x 14 / 365 = 391.
    # Shifted +4 years: paid 30 Jun 2026, 15 Jul 2026 to 14 Jul 2027.
    out = ok("prepayment_deduction", "2026-27", amount=10200, payment_date="2026-06-30", service_start="2026-07-15",
             service_end="2027-07-14", taxpayer="small_business")
    assert out["treatment"] == "apportioned"
    assert out["twelve_month_rule"]["service_period_within_12_months"] is True
    assert out["twelve_month_rule"]["ends_by_last_day_of_next_income_year"] is False
    s = {x["income_year"]: x for x in out["schedule"]}
    assert s["2025-26"]["deduction"] == 0
    assert s["2026-27"]["days"] == 351 and s["2026-27"]["deduction"] == approx(9809, 0.5)
    assert s["2027-28"]["days"] == 14 and s["2027-28"]["deduction"] == approx(391, 0.5)
    assert out["deduction_in_requested_income_year"] == s["2026-27"]["deduction"]


def test_prepay_excluded_below_threshold():
    # ATO example (Maree): prepaid amount 1,045 less GST credit 95 = 950, below the 1,000 excluded amount -> deductible in the
    # year incurred even though the service period is two years.
    out = ok("prepayment_deduction", "2025-26", amount=950, payment_date="2026-06-30", service_start="2026-07-01",
             service_end="2028-06-30", taxpayer="other_business")
    assert out["treatment"] == "immediate" and out["deduction_in_requested_income_year"] == 950


def test_prepay_excluded_required_by_law():
    # ATO example (John's truck registration 1,200, required by state law) -> deductible in the year incurred.
    out = ok("prepayment_deduction", "2026-27", amount=1200, payment_date="2026-12-31", service_start="2027-01-01",
             service_end="2027-12-31", taxpayer="other_business", excluded_expenditure="required_by_law")
    assert out["treatment"] == "immediate" and out["deduction_in_requested_income_year"] == 1200


def test_prepay_larger_business_apportions():
    # Not a small business: apportion 365 days. 1 Jun 2026 to 31 May 2027: 30 days in 2025-26, 335 in 2026-27.
    # 3,650 x 30 / 365 = 300; 3,650 x 335 / 365 = 3,350.
    out = ok("prepayment_deduction", "2025-26", amount=3650, payment_date="2026-06-01", service_start="2026-06-01",
             service_end="2027-05-31", taxpayer="other_business")
    s = out["schedule"]
    assert out["treatment"] == "apportioned"
    assert (s[0]["days"], s[0]["deduction"]) == (30, 300.0) and (s[1]["days"], s[1]["deduction"]) == (335, 3350.0)


def test_prepay_small_business_over_turnover_ceiling_apportions():
    out = ok("prepayment_deduction", "2025-26", amount=3650, payment_date="2026-06-01", service_start="2026-06-01",
             service_end="2027-05-31", taxpayer="small_business", aggregated_turnover=60_000_000)
    assert out["treatment"] == "apportioned" and out["warnings"]


def test_prepay_individual_non_business_12_month_rule():
    out = ok("prepayment_deduction", "2025-26", amount=2400, payment_date="2026-06-15", service_start="2026-07-01",
             service_end="2027-06-30", taxpayer="individual_non_business")
    assert out["treatment"] == "immediate" and out["deduction_in_requested_income_year"] == 2400


def test_prepay_366_days_is_over_12_months():
    # 1 Jul 2026 to 1 Jul 2027 is 12 months and one day (366 days) -> not within 12 months, apportion.
    # 2026-27: 365 days; 3,660 x 365 / 366 = 3,650; 2027-28: 1 day = 10.
    out = ok("prepayment_deduction", "2026-27", amount=3660, payment_date="2026-07-01", service_start="2026-07-01",
             service_end="2027-07-01", taxpayer="small_business")
    assert out["treatment"] == "apportioned"
    s = {x["income_year"]: x["deduction"] for x in out["schedule"]}
    assert s["2026-27"] == approx(3650) and s["2027-28"] == approx(10)


def test_prepay_ten_year_cap():
    # 20-year service capped at 10 years: 1 Jul 2026 to 30 Jun 2036 = 3,653 days (FY 2027-28, 2031-32, 2035-36 hold a 29 Feb).
    # 2026-27 has 365 days: 100,000 x 365 / 3,653 = 9,991.79.
    out = ok("prepayment_deduction", "2026-27", amount=100000, payment_date="2026-07-01", service_start="2026-07-01",
             service_end="2046-06-30", taxpayer="other_business")
    assert out["eligible_service_period"]["days"] == 3653
    assert out["deduction_in_requested_income_year"] == approx(9991.79)
    assert sum(x["deduction"] for x in out["schedule"]) == approx(100000)


def test_prepay_opt_out_of_concession():
    out = ok("prepayment_deduction", "2026-27", amount=12000, payment_date="2026-12-01", service_start="2026-12-01",
             service_end="2027-11-30", taxpayer="small_business", claim_immediate_if_eligible=False)
    assert out["treatment"] == "apportioned"


def test_prepay_immediate_for_other_year_warns():
    out = ok("prepayment_deduction", "2026-27", amount=24000, payment_date="2026-06-01", service_start="2026-07-01",
             service_end="2027-06-30", taxpayer="small_business")
    assert out["deduction_in_requested_income_year"] == 0 and out["payment_income_year"] == "2025-26"
    assert out["warnings"]


def test_prepay_tax_shelter_refused():
    assert refused("prepayment_deduction", amount=10000, payment_date="2026-06-01", service_start="2026-07-01",
                   service_end="2027-06-30", taxpayer="small_business", tax_shelter_arrangement=True) == "AU-BKP-002"


def test_prepay_bad_dates_exit_2():
    code, _ = run("prepayment_deduction", "2026-27", dict(amount=100, payment_date="2026-06-01", service_start="2026-07-01",
                  service_end="2026-06-01", taxpayer="small_business"))
    assert code == 2


# ------------------------------------------------------------ large proprietary test

def ent(rev=0, assets=0, emp=0, name=""):
    return {"name": name, "revenue": rev, "gross_assets": assets, "employees": emp}


def test_large_all_below_is_small():
    out = ok("large_proprietary_test", entity=ent(30e6, 20e6, 60))
    assert out["classification"] == "small" and out["tests_met_for_large"] == 0
    assert out["financial_report_required"] is False
    assert out["tests"]["revenue"]["threshold"] == 50_000_000


def test_large_boundary_inclusive_two_of_three():
    # Thresholds are "or more": revenue exactly 50,000,000 and assets exactly 25,000,000 meet two tests -> large.
    out = ok("large_proprietary_test", entity=ent(50e6, 25e6, 10), financial_year_end="2027-06-30")
    assert out["classification"] == "large" and out["tests_met_for_large"] == 2
    assert out["financial_report_required"] is True
    assert out["lodgment_due_by"] == "2027-10-31"  # 4 months after 30 June


def test_large_one_of_three_is_small():
    out = ok("large_proprietary_test", entity=ent(80e6, 10e6, 50))
    assert out["classification"] == "small" and out["tests_met_for_large"] == 1


def test_large_group_with_eliminations_and_fte():
    # Revenue 30m + 30m - 12m intra-group = 48m (< 50m, not met). Gross assets 20m + 8m - 2m = 26m (>= 25m, met).
    # Employees (FTE) 60 + 39.5 + 0.5 = 100 (>= 100, met). Two of three -> large.
    out = ok("large_proprietary_test", entity=ent(30e6, 20e6, 60),
             controlled_entities=[ent(30e6, 8e6, 39.5, "Sub A"), ent(0, 0, 0.5, "Sub B")],
             intra_group_revenue_eliminations=12e6, intra_group_asset_eliminations=2e6)
    t = out["tests"]
    assert t["revenue"]["value"] == 48e6 and t["revenue"]["meets_large_test"] is False
    assert t["gross_assets"]["value"] == 26e6 and t["gross_assets"]["meets_large_test"] is True
    assert t["employees"]["value"] == 100 and t["employees"]["meets_large_test"] is True
    assert out["classification"] == "large" and out["consolidated_entities"] == 3


def test_large_lodgment_date_30_april_for_dec_year_end():
    out = ok("large_proprietary_test", entity=ent(60e6, 30e6, 5), financial_year_end="2026-12-31")
    assert out["lodgment_due_by"] == "2027-04-30"


def test_small_with_foreign_control_still_reports():
    out = ok("large_proprietary_test", entity=ent(1e6, 1e6, 5), foreign_controlled=True)
    assert out["classification"] == "small" and out["financial_report_required"] is True
    assert out["reporting_triggers"] == ["foreign_controlled"] and out["lodgment_due_by"] is None


def test_large_uses_verified_figures_not_draft():
    out = ok("large_proprietary_test", entity=ent(1, 1, 1))
    assert out["draft"] is False
    assert {f["key"] for f in out["figures_used"]} >= {"asic.large_proprietary_revenue"}
    assert all(f["status"] == "VERIFIED" for f in out["figures_used"])


def test_large_not_proprietary_refused():
    assert refused("large_proprietary_test", entity=ent(1, 1, 1), company_type="public") == "AU-BKP-003"


def test_large_control_uncertain_refused():
    assert refused("large_proprietary_test", entity=ent(1, 1, 1), control_uncertain=True) == "AU-BKP-001"


def test_2025_26_thresholds_same():
    out = ok("large_proprietary_test", "2025-26", entity=ent(50e6, 25e6, 0))
    assert out["classification"] == "large"


def test_overlay_figures_are_verified():
    f = Figures("2026-27")
    assert f.get("bookkeeping.record_retention_years") == 5
    assert f.get("bookkeeping.simplified_trading_stock_change_max") == 5000
    assert f.get("bookkeeping.company_financial_records_retention_years") == 7
    assert not f.draft
