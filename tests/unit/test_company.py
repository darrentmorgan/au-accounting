"""company_tax, max_franking_credit, div7a_minimum_repayment, div7a_loan_schedule, loss_carry_back_offset.
Expected values come from ATO worked examples, the worked example in the Act (cited), or hand computation
shown step by step. None were produced by running the calculators."""

from datetime import date

import pytest

from au_tax.calculators.company import Repayment, _interest_daily, minimum_yearly_repayment
from au_tax.registry import load_all, run


def ok(tool, year, **kw):
    code, out = run(tool, year, kw)
    assert code == 0, out
    return out


def refused(tool, year, **kw):
    code, out = run(tool, year, kw)
    assert code == 3, out
    return out["refusal"]["code"]


def approx(x, tol=0.01):
    return pytest.approx(x, abs=tol)


def test_registered():
    assert {"company_tax", "max_franking_credit", "div7a_minimum_repayment", "div7a_loan_schedule",
            "loss_carry_back_offset"} <= set(load_all())


# ---------------------------------------------------------------- company_tax (ITRA s23AA; ATO company tax rate page)

def test_base_rate_entity_25():
    # turnover 2m < 50m, passive 10% <= 80% -> BRE -> 25% x 100,000 = 25,000
    out = ok("company_tax", "2026-27", taxable_income=100000, aggregated_turnover=2_000_000, passive_income_share=0.10)
    assert out["base_rate_entity"] is True
    assert out["company_tax_rate"] == 0.25
    assert out["gross_tax"] == approx(25000)


def test_bucket_company_passive_income_30():
    # passive 100% of assessable income (trust distributions of interest/dividends) > 80% -> 30% x 200,000 = 60,000
    out = ok("company_tax", "2026-27", taxable_income=200000, aggregated_turnover=0,
             base_rate_entity_passive_income=200000, assessable_income=200000)
    assert out["base_rate_entity"] is False
    assert out["gross_tax"] == approx(60000)


def test_boundaries():
    # turnover must be LESS than 50m: exactly 50m fails -> 30%
    assert ok("company_tax", "2025-26", taxable_income=1000, aggregated_turnover=50_000_000,
              passive_income_share=0)["company_tax_rate"] == 0.3
    # passive income "80% or less": exactly 80% passes -> 25%
    assert ok("company_tax", "2025-26", taxable_income=1000, aggregated_turnover=1,
              passive_income_share=0.8)["company_tax_rate"] == 0.25


def test_franking_offset_and_payg():
    # 25% x 100,000 = 25,000; franking offset 10,000 -> 15,000; PAYG paid 12,000 -> 3,000 payable
    out = ok("company_tax", "2026-27", taxable_income=100000, aggregated_turnover=1_000_000, passive_income_share=0.3,
             franking_credits_received=10000, payg_instalments_paid=12000)
    assert out["net_tax_payable"] == approx(15000)
    assert out["balance_payable_or_refund"] == approx(3000)


def test_excess_franking_offset_converts_to_loss():
    # tax 25% x 10,000 = 2,500; credits 4,000 -> offset 2,500, excess 1,500; loss = 1,500 / 0.25 = 6,000 (s36-55)
    out = ok("company_tax", "2026-27", taxable_income=10000, aggregated_turnover=0, passive_income_share=0.5,
             franking_credits_received=4000)
    assert out["net_tax_payable"] == 0
    assert out["excess_franking_offset_as_tax_loss"] == approx(6000)


def test_imputation_rate_differs_from_tax_rate():
    # LCR 2019/5 Example 2.4 pattern: this year BRE (25%), but LAST year's passive share 82% -> imputation rate 30%
    out = ok("company_tax", "2026-27", taxable_income=100000, aggregated_turnover=46_000_000, passive_income_share=0.75,
             prior_year_aggregated_turnover=48_000_000, prior_year_passive_income_share=0.82)
    assert out["company_tax_rate"] == 0.25
    assert out["corporate_tax_rate_for_imputation"] == 0.3
    assert out["warnings"]


@pytest.mark.parametrize("kw,code", [
    ({"consolidated_group": True}, "AU-COMP-001"),
    ({"prior_losses_deducted": 5000, "ownership_or_control_changed": True}, "AU-COMP-002"),
    ({"special_company_type": "non_profit"}, "AU-COMP-008"),
])
def test_company_refusals(kw, code):
    assert refused("company_tax", "2026-27", taxable_income=1, aggregated_turnover=1, passive_income_share=0, **kw) == code


def test_passive_share_required():
    code, _ = run("company_tax", "2026-27", {"taxable_income": 1, "aggregated_turnover": 1})
    assert code == 2


# ---------------------------------------------------------------- max_franking_credit (s202-60; ATO allocating franking credits)

def test_max_franking_30_ato_example():
    # ATO: prior turnover over 50m -> 30%; gross-up (1-0.3)/0.3 = 2.3333; 100,000 / 2.3333 = 42,857.14
    out = ok("max_franking_credit", "2026-27", frankable_distribution=100000,
             prior_year_aggregated_turnover=60_000_000, prior_year_passive_income_share=0.1)
    assert out["corporate_tax_rate_for_imputation"] == 0.3
    assert out["maximum_franking_credit"] == approx(42857.14)


def test_max_franking_25_gross_up():
    # 25%: gross-up (1-0.25)/0.25 = 3; 75,000 / 3 = 25,000; grossed-up dividend 100,000
    out = ok("max_franking_credit", "2026-27", frankable_distribution=75000,
             prior_year_aggregated_turnover=2_000_000, prior_year_passive_income_share=0.2)
    assert out["maximum_franking_credit"] == approx(25000)
    assert out["shareholder"]["grossed_up_dividend"] == approx(100000)
    assert out["shareholder"]["franking_tax_offset"] == approx(25000)


def test_partial_franking_ato_do_pty_ltd():
    # ATO over-franking page: 7,000 at 30% -> max 3,000; 50% franked -> 1,500
    out = ok("max_franking_credit", "2026-27", frankable_distribution=7000, corporate_tax_rate_for_imputation=0.3,
             franking_percentage=0.5)
    assert out["maximum_franking_credit"] == approx(3000)
    assert out["franking_credit_allocated"] == approx(1500)


def test_new_company_uses_lower_rate():
    # did not exist in previous year -> lower rate 25% -> 30,000 / 3 = 10,000
    out = ok("max_franking_credit", "2026-27", frankable_distribution=30000, existed_prior_year=False)
    assert out["maximum_franking_credit"] == approx(10000)


def test_over_franking_capped_and_deficit_warned():
    # 150% requested -> capped at max 3,000 (s202-60(1)); balance 1,000 - 3,000 = -2,000 deficit
    out = ok("max_franking_credit", "2026-27", frankable_distribution=7000, corporate_tax_rate_for_imputation=0.3,
             franking_percentage=1.5, franking_account_balance=1000)
    assert out["franking_credit_allocated"] == approx(3000)
    assert out["franking_account_balance_after"] == approx(-2000)
    assert any(e["code"] == "AU-COMP-009" for e in out["escalations"])


def test_bad_imputation_rate_rejected():
    # only the two company rates in the rates file are valid imputation rates; the tool raises (MCP returns an error)
    with pytest.raises(ValueError):
        run("max_franking_credit", "2026-27", {"frankable_distribution": 1, "corporate_tax_rate_for_imputation": 0.275})


# ---------------------------------------------------------------- Div 7A MYR formula (ATO "Loans by private companies" examples)

def test_myr_ato_example_2015():
    # ATO: 55,000 x 0.0595 / (1 - (1/1.0595)^7) = 3,272.5 / 0.332743 = 9,835 (rounded)
    assert minimum_yearly_repayment(55000, 0.0595, 7) == approx(9835, 0.5)


def test_myr_ato_example_2016():
    # ATO: 50,430 x 0.0545 / (1 - (1/1.0545)^6) = 2,748.435 / 0.27268843 = 10,079 (rounded)
    assert minimum_yearly_repayment(50430, 0.0545, 6) == approx(10079, 0.5)


def test_daily_interest_ato_example():
    # ATO: 5.95% x 75,000 x 61/365 + 5.95% x 55,000 x 272/365 + 5.95% x 47,000 x 32/365
    #    = 745.79 + 2,438.68 + 245.17 = 3,429.64 (ATO rounds to 3,430)
    interest, paid = _interest_daily(75000, 0.0595, date(2014, 7, 1), date(2015, 6, 30),
                                     [Repayment(date=date(2014, 8, 31), amount=20000),
                                      Repayment(date=date(2015, 5, 30), amount=8000)])
    assert interest == approx(3429.64)
    assert paid == 28000


def test_myr_tool_2026_27():
    # 100,000 at 8.77%, 7 years remaining (loan made 2025-26):
    # step 1: 100,000 x 0.0877 = 8,770; step 2: 1/1.0877 = 0.9193711; step 3: ^7 = 0.5551874
    # step 4: 1 - 0.5551874 = 0.4448126; step 5: 8,770 / 0.4448126 = 19,716.0 (approx)
    # repaid 15,000 -> shortfall 4,716 = deemed dividend
    out = ok("div7a_minimum_repayment", "2026-27", opening_balance=100000, loan_income_year="2025-26",
             loan_term_years=7, repayments_in_year=15000)
    assert out["remaining_term_years"] == 7
    assert out["benchmark_interest_rate"] == 0.0877
    assert out["minimum_yearly_repayment"] == approx(19716.0, 0.1)
    assert out["shortfall"] == approx(4716.0, 0.1)


def test_myr_tool_2025_26_rate():
    # 2025-26 rate 8.37%; loan made 2023-24, so 1 year elapsed, remaining 6.
    # 50,000 x 0.0837 = 4,185; (1/1.0837)^6 = exp(-6 x 0.0803807) = exp(-0.4822842) = 0.617380
    # 1 - 0.617380 = 0.382620; 4,185 / 0.382620 = 10,937.7 (approx)
    out = ok("div7a_minimum_repayment", "2025-26", opening_balance=50000, loan_income_year="2023-24",
             loan_term_years=7, repayments_in_year=11000)
    assert out["remaining_term_years"] == 6
    assert out["minimum_yearly_repayment"] == approx(10937.7, 1)
    assert out["shortfall"] == 0


def test_myr_pre_lodgment_repayments_count_twice():
    # ATO example pattern: balance 75,000 less 20,000 paid before lodgment day -> MYR on 55,000;
    # the 20,000 also counts as a repayment in the year, so no shortfall.
    out = ok("div7a_minimum_repayment", "2026-27", opening_balance=75000, repayments_before_lodgment_day=20000,
             loan_income_year="2025-26", loan_term_years=7)
    assert out["balance_for_myr"] == approx(55000)
    assert out["repayments_counted"] == approx(20000)
    assert out["shortfall"] == 0


def test_deemed_dividend_capped_by_surplus():
    # shortfall ~19,716 (as above, nothing repaid); distributable surplus 5,000 -> deemed dividend 5,000 (s109Y)
    out = ok("div7a_minimum_repayment", "2026-27", opening_balance=100000, loan_income_year="2025-26",
             loan_term_years=7, distributable_surplus=5000)
    assert out["deemed_dividend"] == approx(5000)


def test_loan_year_has_no_myr():
    out = ok("div7a_minimum_repayment", "2026-27", opening_balance=100000, loan_income_year="2026-27", loan_term_years=7)
    assert out["minimum_yearly_repayment"] == 0 and out["loan_year"]


def test_term_over_maximum_not_complying():
    # unsecured 10-year term > 7-year maximum (s109N(3)(b))
    out = ok("div7a_minimum_repayment", "2026-27", opening_balance=1000, loan_income_year="2025-26", loan_term_years=10)
    assert out["complying"] is False


def test_secured_25_year_needs_110_percent_cover():
    out = ok("div7a_minimum_repayment", "2026-27", opening_balance=1000, loan_income_year="2025-26",
             loan_term_years=25, secured=True, security_value_ratio=1.05)
    assert out["complying"] is False
    out = ok("div7a_minimum_repayment", "2026-27", opening_balance=1000, loan_income_year="2025-26",
             loan_term_years=25, secured=True, security_value_ratio=1.2)
    assert out["complying"] is True and out["remaining_term_years"] == 25


def test_myr_refusals():
    assert refused("div7a_minimum_repayment", "2026-27", opening_balance=1000, loan_income_year="2018-19",
                   loan_term_years=7) == "AU-COMP-007"   # 7 years elapsed, remaining 0
    assert refused("div7a_minimum_repayment", "2026-27", opening_balance=1000, loan_income_year="2025-26",
                   loan_term_years=7, reborrowed_or_interposed=True) == "AU-COMP-006"


# ---------------------------------------------------------------- div7a_loan_schedule

def test_schedule_reproduces_ato_example():
    # ATO example: 2013-14 loans 75,000; lodgment day 15 May 2015; repaid 20,000 on 31 Aug 2014, 8,000 on 30 May 2015.
    # 2014-15: MYR on 55,000 at 5.95% over 7 = 9,835; repaid 28,000; interest 3,429.64; closing 50,429.64 (ATO 50,430)
    # 2015-16: MYR on 50,429.64 at 5.45% over 6 = about 10,079
    out = ok("div7a_loan_schedule", "2026-27", loan_income_year="2013-14", loan_amount=75000, loan_term_years=7,
             lodgment_day="2015-05-15",
             repayments=[{"date": "2014-08-31", "amount": 20000}, {"date": "2015-05-30", "amount": 8000}],
             benchmark_rate_overrides={"2014-15": 0.0595, "2015-16": 0.0545})
    r1, r2 = out["schedule"][0], out["schedule"][1]
    assert r1["balance_for_myr"] == approx(55000)
    assert r1["minimum_yearly_repayment"] == approx(9835, 0.5)
    assert r1["closing_balance"] == approx(50430, 0.5)
    assert r1["shortfall_deemed_dividend"] == 0
    assert r2["minimum_yearly_repayment"] == approx(10079, 1)


def test_schedule_amortises_to_zero_at_constant_rate():
    # With MYR paid at each year end and one rate, the annuity clears the loan in exactly 7 years.
    out = ok("div7a_loan_schedule", "2026-27", loan_income_year="2025-26", loan_amount=100000, loan_term_years=7)
    rows = out["schedule"]
    assert len(rows) == 7
    assert rows[-1]["closing_balance"] == approx(0, 0.05)
    # first-year interest = 100,000 x 8.77% = 8,770 (published 2026-27 rate); later years projected
    assert rows[0]["interest"] == approx(8770)
    assert rows[0]["rate_source"] == "published" and rows[1]["rate_source"] == "projected"


# ---------------------------------------------------------------- loss_carry_back_offset (ITAA 1997 Div 160, Act 71 of 2026)

ACT_EXAMPLE = dict(tax_loss=900000, base_rate_entity=False, franking_account_balance=280000,
                   carry_back_years=[{"income_year": "2024-25", "income_tax_liability": 120000, "net_exempt_income": 5000,
                                      "loss_carried_back": 405000},
                                     {"income_year": "2025-26", "income_tax_liability": 210000, "loss_carried_back": 495000}])


def test_act_worked_example():
    # s160-10 example: (405,000 - 5,000) x 30% = 120,000 (= 2024-25 liability); 495,000 x 30% = 148,500; total 268,500
    out = ok("loss_carry_back_offset", "2026-27", **ACT_EXAMPLE)
    assert out["eligible"]
    assert out["loss_carry_back_tax_offset"] == approx(268500)


def test_franking_cap():
    # same components 268,500, franking balance 200,000 -> offset 200,000 (s160-10(1)(b))
    out = ok("loss_carry_back_offset", "2026-27", **{**ACT_EXAMPLE, "franking_account_balance": 200000})
    assert out["loss_carry_back_tax_offset"] == approx(200000)


def test_bre_rate_used_for_loss_year():
    # BRE loss year: 100,000 carried back to 2025-26 (liability 50,000) -> 100,000 x 25% = 25,000
    out = ok("loss_carry_back_offset", "2026-27", tax_loss=100000, base_rate_entity=True, franking_account_balance=60000,
             carry_back_years=[{"income_year": "2025-26", "income_tax_liability": 50000, "loss_carried_back": 100000}])
    assert out["loss_carry_back_tax_offset"] == approx(25000)


def test_component_limited_to_liability():
    # 400,000 x 30% = 120,000 but liability only 60,000 -> 60,000
    out = ok("loss_carry_back_offset", "2026-27", tax_loss=400000, base_rate_entity=False, franking_account_balance=500000,
             carry_back_years=[{"income_year": "2025-26", "income_tax_liability": 60000, "loss_carried_back": 400000}])
    assert out["loss_carry_back_tax_offset"] == approx(60000)


def test_loss_year_before_1_july_2026_ineligible():
    out = ok("loss_carry_back_offset", "2025-26", tax_loss=100000, base_rate_entity=True, franking_account_balance=50000)
    assert out["eligible"] is False and out["loss_carry_back_tax_offset"] == 0


def test_sge_and_lodgment_ineligible():
    for kw in ({"significant_global_entity": True}, {"lodgment_condition_met": False}):
        out = ok("loss_carry_back_offset", "2026-27", **{**ACT_EXAMPLE, **kw})
        assert out["eligible"] is False


def test_year_outside_window_rejected():
    with pytest.raises(ValueError):
        run("loss_carry_back_offset", "2026-27", {**ACT_EXAMPLE, "carry_back_years": [
            {"income_year": "2023-24", "income_tax_liability": 1000}]})


@pytest.mark.parametrize("kw,code", [
    ({"consolidated_group_or_transferred_losses": True}, "AU-COMP-001"),
    ({"change_of_control_scheme": True}, "AU-COMP-003"),
    ({"foreign_resident": True}, "AU-COMP-003"),
])
def test_carry_back_refusals(kw, code):
    assert refused("loss_carry_back_offset", "2026-27", **{**ACT_EXAMPLE, **kw}) == code
