"""obligations_calendar tests. Expected dates are hand computed from the rules on the cited ATO and RevenueSA
pages (the rule is quoted in each comment) and a printed calendar (`cal`), not by running the calculator.

Weekdays used (from `cal`): 28 Oct 2026 Wed; 11 Nov 2026 Wed; 25 Nov 2026 Wed; 28 Feb 2027 Sun; 1 Mar 2027 Mon;
7 Mar 2027 Sun; 8 Mar 2027 Mon; 12 May 2027 Wed; 21 May 2027 Fri; 26 May 2027 Wed; 28 Jul 2027 Wed;
11 Aug 2027 Wed; 7 Aug 2026 Fri; 21 Feb 2027 Sun; 22 Feb 2027 Mon; 31 Oct 2027 Sun; 1 Nov 2027 Mon.
"""

from au_tax.registry import load_all, run


def cal(payload, year="2026-27", draft=False):
    code, out = run("obligations_calendar", year, payload, allow_draft=draft)
    assert code == 0, out
    return out


def dates(out, prefix):
    return [i["due_date"] for i in out["calendar"] if i["obligation"].startswith(prefix)]


def test_registered():
    assert "obligations_calendar" in load_all()


def test_quarterly_bas_online_2026_27():
    # ATO BAS due dates: quarterly due the 28th of the month after the quarter, Q2 due 28 Feb; online lodgment adds
    # two weeks to lodge and pay for Q1, Q3, Q4.
    # Q1: 28 Oct 2026 + 14 days = 11 Nov 2026 (Wed). Q2: 28 Feb 2027 is a Sunday and Mon 1 Mar 2027 is Labour Day (WA)
        # -> Tue 2 Mar 2027 (ATO table, TAA 1953 s 8AAZMB; this test expected 1 Mar before holidays were wired in).
    # Q3: 28 Apr 2027 + 14 = 12 May 2027 (Wed). Q4: 28 Jul 2027 + 14 = 11 Aug 2027 (Wed).
    out = cal({"entity_type": "sole_trader", "gst_registered": True, "gst_cycle": "quarterly"})
    assert dates(out, "BAS: GST") == ["2026-11-11", "2027-03-02", "2027-05-12", "2027-08-11"]
    assert out["draft"] is False
    assert all(i["sources"] for i in out["calendar"])


def test_registered_agent_q4_unverified_is_skipped_not_guessed():
    # Agent program: Q1 2026-27 25 Nov 2026, Q3 26 May 2027 (VERIFIED); Q2 has no program date, 28 Feb 2027 (Sun) -> Tue 2 Mar 2027 (Mon 1 Mar is Labour Day, WA).
    # Q4 25 Aug 2027 is SOURCE-CITED ("to be confirmed"), so without draft mode it must be listed as unverified.
    out = cal({"entity_type": "company", "gst_registered": True, "lodgment": "registered_agent"})
    assert dates(out, "BAS: GST") == ["2026-11-25", "2027-03-02", "2027-05-26"]
    assert [u["refusal_code"] for u in out["unverified"]] == ["AU-GEN-001"]
    assert "Q4" in out["unverified"][0]["obligation"]


def test_registered_agent_q4_in_draft_mode():
    out = cal({"entity_type": "company", "gst_registered": True, "lodgment": "registered_agent"}, draft=True)
    assert dates(out, "BAS: GST")[-1] == "2027-08-25"
    assert out["draft"] is True


def test_fbt_return_self_and_agent():
    # FBT return and payment due 21 May after the FBT year: FBT2027 -> Fri 21 May 2027.
    # Agent lodging electronically: generally 25 June -> 25 Jun 2027 (June 2027 starts on a Tuesday, so a Friday).
    out = cal({"entity_type": "company", "provides_fringe_benefits": True, "lodges_income_tax_return": False})
    item = next(i for i in out["calendar"] if i["obligation"].startswith("FBT"))
    assert (item["period"], item["due_date"]) == ("FBT2027", "2027-05-21")
    out = cal({"entity_type": "company", "provides_fringe_benefits": True, "lodgment": "registered_agent"})
    assert dates(out, "FBT") == ["2027-06-25"]


def test_sa_payroll_tax_months_and_reconciliation():
    # RevenueSA: monthly return due the 7th of the following month (next business day if a weekend or SA public holiday); June
    # is in the annual reconciliation due 28 July. July 2026 wages -> Fri 7 Aug 2026. Feb 2027 wages -> 7 Mar 2027 is a Sunday
    # and Mon 8 Mar 2027 is Adelaide Cup Day -> Tue 9 Mar 2027 (RevenueSA published date; this test expected 8 Mar before holidays
    # were wired in). Dec 2026 wages -> RevenueSA's published extension Thu 14 Jan 2027. Reconciliation: Wed 28 Jul 2027.
    # 11 monthly returns (July to May).
    out = cal({"entity_type": "company", "sa_payroll_tax_registered": True})
    monthly = dates(out, "SA payroll tax monthly")
    assert len(monthly) == 11
    assert monthly[0] == "2026-08-07"
    assert "2027-03-09" in monthly and "2027-03-08" not in monthly
    assert "2027-01-14" in monthly
    assert monthly == ["2026-08-07", "2026-09-07", "2026-10-07", "2026-11-09", "2026-12-07", "2027-01-14", "2027-02-08",
                       "2027-03-09", "2027-04-07", "2027-05-07", "2027-06-07"]   # RevenueSA published 2026-27 table
    assert dates(out, "SA payroll tax annual") == ["2027-07-28"]
    assert not any("NOT checked" in w for w in out["warnings"])
    feb = next(i for i in out["calendar"] if i["period"] == "February 2027" and i["obligation"].startswith("SA payroll"))
    assert feb["business_day_roll"]["regime"] == "sa_state_tax" and "Adelaide Cup" in feb["business_day_roll"]["reason"]


def test_calendar_items_carry_the_business_day_roll_and_rule_source():
    # Q2 BAS 28 Feb 2027: Sunday, then Labour Day (WA) Mon 1 Mar 2027 -> Tue 2 Mar 2027 (ATO table); rule TAA 1953 s 8AAZMB.
    out = cal({"entity_type": "sole_trader", "gst_registered": True})
    q2 = next(i for i in out["calendar"] if i["obligation"].endswith("Q2"))
    assert q2["due_date"] == "2027-03-02" and q2["original_due_date"] == "2027-02-28"
    roll = q2["business_day_roll"]
    assert roll["regime"] == "commonwealth_tax" and roll["rolled"] and "Labour Day" in roll["reason"]
    assert "https://www.legislation.gov.au/C1953A00001/latest/text" in q2["sources"]
    assert any("8AAZMB" in a for a in out["assumptions"])


def test_monthly_bas_december_concession():
    # Monthly BAS due the 21st of the next month; December monthly BAS 21 Feb for eligible electronic lodgers.
    # 21 Feb 2027 is a Sunday -> Mon 22 Feb 2027. July 2026 -> 21 Aug 2026 (Fri).
    out = cal({"entity_type": "company", "gst_registered": True, "gst_cycle": "monthly", "gst_turnover": 5_000_000})
    monthly = dates(out, "BAS: GST")
    assert len(monthly) == 12
    assert monthly[0] == "2026-08-21"
    assert "2027-02-22" in monthly


def test_annual_gst_return():
    # Annual GST return due 31 October after the year: 31 Oct 2027 is a Sunday -> Mon 1 Nov 2027.
    out = cal({"entity_type": "sole_trader", "gst_registered": True, "gst_cycle": "annual"})
    assert dates(out, "Annual GST return") == ["2027-11-01"]


def test_payday_super_rule_and_lodgment_items():
    # lodgment.* figures (payg-instalments-lodgment overlay, ATO pages): STP finalisation 14 July after the year
    # -> Wed 14 Jul 2027; TPAR 28 August -> 28 Aug 2027 is a Saturday -> Mon 30 Aug 2027; instalment quarters on the
    # 28th of Oct, Feb, Apr, Jul with no online concession: 28 Oct 2026 (Wed), 28 Feb 2027 Sun -> Tue 2 Mar 2027 (Labour Day WA),
    # 28 Apr 2027 (Wed), 28 Jul 2027 (Wed).
    out = cal({"entity_type": "company", "has_employees": True, "payg_withholding_registered": True,
               "payg_instalments": True, "tpar_industry": True})
    sg = next(r for r in out["recurring_rules"] if r["obligation"].startswith("Super guarantee"))
    assert "Payday Super" in sg["obligation"] and sg["tool"] == "super_guarantee"
    assert dates(out, "STP finalisation") == ["2027-07-14"]
    assert dates(out, "Taxable payments annual report") == ["2027-08-30"]
    assert dates(out, "PAYG instalment notice") == ["2026-10-28", "2027-03-02", "2027-04-28", "2027-07-28"]
    pending = {p["obligation"]: p["owner_skill"] for p in out["not_computed"]}
    assert pending["income_tax_return"] == "payg-instalments-lodgment"  # company return: agent program / history
    assert pending["asic_annual_review"] == "company-div7a"  # no registration date given
    # PAYG withholding without GST: quarterly activity statement, flagged as an assumption.
    assert len(dates(out, "BAS: PAYG withholding")) == 4
    assert any("small withholder" in a for a in out["assumptions"])
    stp = next(i for i in out["calendar"] if i["obligation"].startswith("STP"))
    assert stp["figure_keys"] == ["lodgment.stp_finalisation_due_month", "lodgment.stp_finalisation_due_day"]
    assert stp["sources"]


def test_instalments_on_quarterly_bas_are_a_rule_not_separate_items():
    out = cal({"entity_type": "sole_trader", "gst_registered": True, "payg_instalments": True})
    assert dates(out, "PAYG instalment notice") == []
    assert any(r["obligation"] == "PAYG instalments" for r in out["recurring_rules"])


def test_individual_self_lodged_return():
    # Self-lodged return due 31 October after the year: 31 Oct 2027 is a Sunday -> Mon 1 Nov 2027. Payment
    # 21 November if lodged on time: 21 Nov 2027 is a Sunday -> Mon 22 Nov 2027 (TAA 1953 s 8AAZMB(1)).
    out = cal({"entity_type": "individual"})
    assert dates(out, "Individual income tax return") == ["2027-11-01"]
    pay = next(r for r in out["recurring_rules"] if r["obligation"] == "Individual income tax payment")
    assert "2027-11-22" in pay["rule"]
    out = cal({"entity_type": "individual", "lodgment": "registered_agent"})
    assert dates(out, "Individual income tax return") == []
    assert any(p["obligation"] == "income_tax_return" for p in out["not_computed"])


def test_asic_annual_review_date():
    # Review date is the anniversary of registration: registered 15 Mar 2015 -> 15 Mar 2027 (Mon) in 2026-27.
    out = cal({"entity_type": "company", "company_registration_date": "2015-03-15", "lodges_income_tax_return": False})
    assert dates(out, "ASIC annual review") == ["2027-03-15"]


def test_quarterly_sg_regime_2025_26():
    out = cal({"entity_type": "company", "has_employees": True}, year="2025-26")
    sg = next(r for r in out["recurring_rules"] if r["obligation"].startswith("Super guarantee"))
    assert "quarterly" in sg["obligation"]


def test_calendar_sorted_and_other_state_flagged():
    out = cal({"entity_type": "company", "gst_registered": True, "sa_payroll_tax_registered": True,
               "provides_fringe_benefits": True, "other_states": ["VIC"]})
    ds = [i["due_date"] for i in out["calendar"]]
    assert ds == sorted(ds)
    assert any("AU-SA-001" in p["why"] for p in out["not_computed"])


def test_individual_with_gst_is_invalid():
    code, out = run("obligations_calendar", "2026-27", {"entity_type": "individual", "gst_registered": True})
    assert code == 2


# ---------------------------------------------------------------- assemble_taxable_income (hand arithmetic)

def asm(components, **kw):
    code, out = run("assemble_taxable_income", "2026-27", {"components": components, **kw})
    assert code == 0, out
    return out


def comp(kind, amount, skill="user", **kw):
    return {"kind": kind, "amount": amount, "source_skill": skill, **kw}


def test_assemble_sole_trader_rental_crypto():
    # 60,000 business + (-4,250.50) rental + 3,000 net capital gain + 1,200 interest - 2,500 personal super deduction
    # = 60,000 - 4,250.50 + 3,000 + 1,200 - 2,500 = 57,449.50
    out = asm([comp("business_net", 60000, "sole-trader-business", gst_inclusive=False),
               comp("rental_net", -4250.50, "rental-property"),
               comp("net_capital_gain", 3000, "cgt", source_tool="net_capital_gain"),
               comp("interest", 1200),
               comp("personal_super_deduction", 2500, "super-contributions")], gst_registered=True)
    assert out["consistent"] is True
    assert out["taxable_income"] == 57449.50
    assert out["deductions_included"] == 2500
    assert out["handoffs"]["net_rental_loss_for_net_investment_losses"] == 4250.50


def test_assemble_blocks_double_counted_trust_gain():
    out = asm([comp("trust_total_assessed", 20000, "trusts-partnerships", capital_gain_part=5000),
               comp("net_capital_gain", 5000, "cgt")])
    assert out["consistent"] is False and out["taxable_income"] is None
    assert any("double count" in b for b in out["blocking_issues"])


def test_assemble_blocks_gst_inclusive_raw_cgt_and_net_foreign():
    out = asm([comp("business_net", 55000, "sole-trader-business", gst_inclusive=True),
               comp("capital_gain_gross", 8000, "user"),
               comp("foreign_income", 10000, "residency-cross-border", net_of_foreign_tax=True)])
    assert out["taxable_income"] is None
    text = " ".join(out["blocking_issues"])
    assert "includes GST" in text and "net_capital_gain tool" in text and "net of foreign tax" in text


def test_assemble_blocks_duplicate_and_wrong_ncg_source():
    out = asm([comp("salary_wages", 80000), comp("salary_wages", 80000, "payroll-sg"),
               comp("net_capital_gain", 1000, "trusts-partnerships")])
    text = " ".join(out["blocking_issues"])
    assert "Possible double count" in text and "must come from the cgt skill" in text
    out = asm([comp("salary_wages", 80000, confirmed_distinct=True), comp("salary_wages", 80000, confirmed_distinct=True)])
    assert out["taxable_income"] == 160000


def test_assemble_excludes_deferred_and_quarantined_and_applies_losses():
    # 70,000 wages; business loss 6,000 deferred (Div 35) -> excluded; rental -3,000 quarantined -> excluded;
    # 70,000 - 1,000 work deduction = 69,000; prior tax losses 10,000 -> 59,000, none carried forward.
    out = asm([comp("salary_wages", 70000), comp("business_net", -6000, "sole-trader-business", deferred_non_commercial_loss=True),
               comp("rental_net", -3000, "rental-property", quarantined=True), comp("work_related_deduction", 1000)],
              prior_year_tax_losses=10000)
    assert out["taxable_income"] == 59000
    assert out["prior_year_tax_losses_applied"] == 10000
    assert [l["effect"] for l in out["lines"]] == ["add", "excluded", "excluded", "subtract"]


def test_assemble_loss_year():
    # 10,000 wages + (-25,000) business loss (allowed) = -15,000 -> taxable income 0, tax loss 15,000 carried forward.
    out = asm([comp("salary_wages", 10000), comp("business_net", -25000, "sole-trader-business")])
    assert out["taxable_income"] == 0
    assert out["tax_loss_carried_forward"] == 15000


def test_assemble_franking_warning():
    out = asm([comp("dividends_franked", 700)])
    assert any("franking credit" in w for w in out["warnings"])


def test_mid_year_start_skips_earlier_periods():
    # GST registered from 1 Oct 2026 and first wages 2 Nov 2026: no Q1 (Jul-Sep) BAS; Q2 due 28 Feb 2027 (Sun) ->
    # Tue 2 Mar 2027 (Labour Day WA); Q3 28 Apr 2027 +14 online = 12 May 2027; Q4 28 Jul 2027 +14 = 11 Aug 2027.
    out = cal({"entity_type": "sole_trader", "gst_registered": True, "gst_registered_from": "2026-10-01",
               "payg_withholding_registered": True, "employing_from": "2026-11-02", "has_employees": True})
    bas = [i for i in out["calendar"] if i["obligation"].startswith("BAS")]
    assert [i["due_date"] for i in bas] == ["2027-03-02", "2027-05-12", "2027-08-11"]
    assert [i["original_due_date"] for i in bas] == ["2027-02-28", "2027-04-28", "2027-07-28"]
    assert all("PAYG withholding" in i["obligation"] for i in bas)


def test_return_to_work_sa_registration():
    # ReturnToWorkSA (rtwsa.com register page, updated 22 Jul 2026): register within 14 days of employing unless
    # 2026-27 remuneration will be below the published minimum. Wages 20 h x 32 x 34 weeks = 21,760, above it.
    # First wages 2 Nov 2026 + 14 days = 16 Nov 2026.
    out = cal({"entity_type": "sole_trader", "has_employees": True, "employs_in_sa": True,
               "employing_from": "2026-11-02", "expected_annual_wages": 21760})
    assert dates(out, "ReturnToWorkSA") == ["2026-11-16"]
    out = cal({"entity_type": "sole_trader", "has_employees": True, "employs_in_sa": True, "expected_annual_wages": 5000})
    assert any(r["obligation"] == "ReturnToWorkSA registration" and r["rule"].startswith("Not required")
               for r in out["recurring_rules"])
    # 2025-26 minimum is not verified: listed as unverified, not guessed.
    out = cal({"entity_type": "sole_trader", "has_employees": True, "employs_in_sa": True, "expected_annual_wages": 5000},
              year="2025-26")
    assert any(u["obligation"] == "ReturnToWorkSA registration" for u in out["unverified"])


def test_return_to_work_sa_runs_from_employment_start():
    # Worker starts Mon 2 Nov 2026, first pay Fri 6 Nov 2026: 14 days run from the start, 2 Nov + 14 = 16 Nov 2026.
    out = cal({"entity_type": "sole_trader", "has_employees": True, "employs_in_sa": True,
               "employment_start": "2026-11-02", "employing_from": "2026-11-06", "expected_annual_wages": 21760})
    assert dates(out, "ReturnToWorkSA") == ["2026-11-16"]
    # Without a start date it falls back to the first pay (6 Nov + 14 = 20 Nov) and warns.
    out = cal({"entity_type": "sole_trader", "has_employees": True, "employs_in_sa": True,
               "employing_from": "2026-11-06", "expected_annual_wages": 21760})
    assert dates(out, "ReturnToWorkSA") == ["2026-11-20"]
    assert any("employment start date not given" in w for w in out["warnings"])


# ---------------------------------------------------------------- due dates after the holiday data (AU-GEN-004)

def test_calendar_2027_28_lists_dates_after_the_holiday_data_as_unverified_and_keeps_the_rest():
    # 2027-28: the holiday data ends 30 Jun 2028. Q4 BAS (28 Jul 2028), the SA reconciliation (28 Jul 2028), STP finalisation
    # (14 Jul 2028) and TPAR (28 Aug 2028) fall after it. One item outside the data must not refuse the whole calendar: it is listed
    # in `unverified` with AU-GEN-004 and its statutory date (never rolled or guessed); everything inside the data is still listed.
    out = cal({"entity_type": "company", "gst_registered": True, "payg_withholding_registered": True, "has_employees": True,
               "sa_payroll_tax_registered": True, "provides_fringe_benefits": True, "tpar_industry": True}, "2027-28")
    late = {u["obligation"]: u for u in out["unverified"] if u["refusal_code"] == "AU-GEN-004"}
    assert set(late) == {"BAS: GST and PAYG withholding (W1, W2) Q4", "SA payroll tax annual reconciliation",
                         "STP finalisation declaration", "Taxable payments annual report (TPAR)"}
    assert late["SA payroll tax annual reconciliation"]["statutory_due_date"] == "2028-07-28"
    assert late["Taxable payments annual report (TPAR)"]["statutory_due_date"] == "2028-08-28"
    assert late["STP finalisation declaration"]["statutory_due_date"] == "2028-07-14"
    assert all("public holiday" in u["reason"] for u in late.values())
    listed = {i["obligation"] for i in out["calendar"]}
    assert {"BAS: GST and PAYG withholding (W1, W2) Q1", "BAS: GST and PAYG withholding (W1, W2) Q3", "FBT return and payment"} <= listed
    assert not listed & set(late)
    assert len(dates(out, "SA payroll tax monthly")) == 11    # Aug 2027 to Jun 2028 returns are all inside the data
    # 21 May 2028 (FBT) is a Sunday (1 Jul 2028 is a Saturday; 21 May is 41 days earlier, 41 mod 7 = 6, so Sunday) -> Mon 22 May 2028.
    assert dates(out, "FBT return") == ["2028-05-22"]
