---
name: company-div7a
description: 'Works out Australian company tax and Division 7A for 2025-26 or 2026-27 - base rate entity test and company tax rate, company tax payable, franking credits (maximum credit, gross-up, franking deficit), the new corporate loss carry back offset (Div 160, loss years from 1 July 2026), and Division 7A shareholder loans (complying agreements, benchmark rate, minimum yearly repayments, schedules, deemed dividends). Use when someone asks "what tax rate does my company pay", "is my company a base rate entity", "bucket company tax", "how much franking credit on a dividend", "can my company carry back a loss", "director loan", "I took money out of my company", "Div 7A minimum repayment", "Div 7A loan agreement", or "is a UPE a Div 7A loan after Bendel". Also use for company losses after a change of ownership, consolidated groups, trust distributions owed to a company (Subdiv EA, s100A), repay-and-redraw, distributable surplus and Part IVA questions: the skill decides scope and escalates to a registered tax agent.'
---

# Company tax, franking and Division 7A (Australia)

Deterministic tools do every calculation: `company_tax`, `max_franking_credit`, `loss_carry_back_offset`, `div7a_minimum_repayment`, `div7a_loan_schedule`, plus `get_figure` for a single rate. Never do the arithmetic yourself and never quote a rate, threshold, benchmark rate or term from memory; every figure comes from the tool's `figures_used`.

## Scope

In scope:
- Company tax rate: the base rate entity test (Income Tax Rates Act 1986 s23AA; aggregated turnover below the threshold AND base rate entity passive income no more than the maximum share of assessable income), company tax payable, the non-refundable franking tax offset for dividends received, PAYG instalment balance.
- Franking: corporate tax rate for imputation purposes (from the PREVIOUS year's facts, ITAA 1997 s995-1; LCR 2019/5), maximum franking credit and gross-up (s202-60), shareholder gross-up and franking tax offset, franking account debits and deficit awareness (Div 205), benchmark rule awareness (Div 203).
- Loss carry back: new ITAA 1997 Div 160 inserted by the Treasury Laws Amendment (Tax Reform No. 2) Act 2026 (No. 71 of 2026) Sch 1, for loss years starting on or after 1 July 2026.
- Division 7A (ITAA 1936 Pt III Div 7A): payments (s109C), loans (s109D), debt forgiveness (s109F) to shareholders and associates; complying loan agreements (s109N); minimum yearly repayment and shortfall (s109E); distributable surplus cap (s109Y, when given); Bendel and unpaid present entitlements.

Out of scope (escalate, see Escalation): consolidated groups, loss recoupment tests after ownership change, Subdiv EA and s100A arrangements, working out distributable surplus, anti-avoidance (s109R, s109T, Part IVA), refinanced or expired Div 7A loans, the Commissioner's discretions, special company types, imputation penalty rules.

## Required inputs

Ask for anything missing that changes the answer. Do not assume silently.
1. **Income year** (`2025-26` or `2026-27`). "This year" is ambiguous; ask. A standard 1 July to 30 June year is assumed; a substituted accounting period is escalated.
2. For company tax: taxable income, aggregated turnover for the year (including connected entities and affiliates), and base rate entity passive income as a share of assessable income (or the two amounts). Passive income = dividends and franking credits, interest, rent, royalties, net capital gains, and trust or partnership distributions traceable to those.
3. For franking: the frankable distribution, franking percentage, and LAST year's aggregated turnover and passive income share (or whether the company existed last year). Franking account balance if a deficit is possible.
4. For loss carry back: the tax loss, whether the company is a base rate entity in the loss year, the income tax liability (and net exempt income) for each of the two prior years, the franking account balance at the END of the loss year, lodgment history, and any change of ownership.
5. For Division 7A: the income year the loan was made, amount outstanding, whether a written agreement was signed before the company's lodgment day, term, whether secured by a registered mortgage (and property value), repayments with dates, and distributable surplus if known.

## Procedure

1. Confirm the income year and which question is asked. Check the escalation list first; if a trigger applies, surface the code and stop that part.
2. Call the tool with `income_year` and `inputs`:
   - Rate and tax: `company_tax` with `taxable_income`, `aggregated_turnover`, `passive_income_share` (or `base_rate_entity_passive_income` and `assessable_income`), optional `existed_prior_year`, `prior_year_aggregated_turnover`, `prior_year_passive_income_share`, `franking_credits_received`, `payg_instalments_paid`, `prior_losses_deducted`, `ownership_or_control_changed`, `consolidated_group`, `special_company_type`.
   - Franking: `max_franking_credit` with `frankable_distribution` and either `corporate_tax_rate_for_imputation` or the prior-year facts; optional `franking_percentage`, `franking_account_balance`, `benchmark_franking_percentage`.
   - Carry back: `loss_carry_back_offset` with `tax_loss`, `base_rate_entity` (or `aggregated_turnover` and `passive_income_share`), `franking_account_balance`, `carry_back_years` (list of `income_year`, `income_tax_liability`, `net_exempt_income`, `liability_already_used`, optional `loss_carried_back`), plus the flags `significant_global_entity`, `lodgment_condition_met`, `consolidated_group_or_transferred_losses`, `change_of_control_scheme`, `foreign_resident`. The income year of the call is the LOSS year.
   - Div 7A for one year: `div7a_minimum_repayment` with `opening_balance`, `loan_income_year` (or `years_elapsed`), `loan_term_years`, `secured`, `security_value_ratio`, `repayments_in_year`, `repayments_before_lodgment_day`, `written_agreement_before_lodgment_day`, `distributable_surplus`, `reborrowed_or_interposed`. The income year of the call is the year the repayment is for.
   - Div 7A over the loan's life: `div7a_loan_schedule` with `loan_income_year`, `loan_amount`, `loan_term_years`, `secured`, `lodgment_day`, `repayments` (date and amount), optional `benchmark_rate_overrides`.
3. Read the envelope: `exit_code` 0 present the result; 3 quote the refusal code and message verbatim and stop that part; 4 (AU-GEN-001) a figure is not verified, say so; 4 (AU-GEN-003) a figure has no published value, no draft is possible, quote it and stop that part; 2 fix the input and call again. Surface every `warnings` and `escalations` entry.
4. Quote numbers exactly as returned, in dollars and cents, with the income year.

## Judgement rules

- **Tax rate vs franking rate.** The base rate entity test uses THIS year's turnover and passive income; the rate for franking this year's dividends uses LAST year's figures against this year's threshold. They can differ; always say which applies. A new company franks at the lower rate.
- **Bucket companies.** A company whose income is mainly trust distributions of passive income usually fails the passive income test and pays the general rate, however small it is.
- **Loss carry back (Div 160, Act 71 of 2026).** Loss years starting before 1 July 2026 cannot be carried back (the earlier temporary regime ended with 2022-23). The entity must be a corporate tax entity throughout, not a significant global entity, and have lodged (or not been required to lodge) for the loss year and the five years before. A carry back year must be one of the two prior years with an income tax liability. Each component uses the corporate tax rate for the LOSS year, net exempt income reduces the loss carried back, and the total is capped at the franking account balance at the end of the loss year. The offset is refundable. The choice is made in the approved form by the loss-year lodgment day. Schemes that trade shares for the value of the offset are caught (s160-30).
- **Loss recoupment.** Deducting prior-year losses needs the continuity of ownership test or the business continuity test; any ownership or control change escalates (AU-COMP-002).
- **Division 7A trigger.** A payment, loan or forgiven debt to a shareholder or associate is an unfranked deemed dividend at 30 June of the year it is made, to the extent of distributable surplus, unless repaid, excluded, or put under a complying written agreement before the company's lodgment day (the earlier of the return due date and the date it is lodged). Asset use (for example a company holiday home or car) is a payment (s109CA).
- **Complying loan (s109N).** Written agreement before lodgment day; interest at least the benchmark rate for each later year; term no longer than the maximum (`div7a.max_term_unsecured_years`, or `div7a.max_term_secured_years` where the whole loan is secured by a registered mortgage over real property worth at least `div7a.secured_loan_min_security_ratio` times the loan net of prior debts).
- **Minimum yearly repayment (s109E).** No repayment is due in the loan year. From the next year, MYR uses that year's benchmark rate (`div7a.benchmark_interest_rate`) and the remaining term. For the first year the balance is the loan less repayments made before lodgment day; those repayments also count towards the first year's MYR (ATO worked example). Any shortfall is an unfranked deemed dividend. Do not count the loan year as "year 1" of the term: in the first income year after the loan year the remaining term is the full agreement term (s109E(6); ATO worked example), and it falls by one each later year. Let the tool work it out from `loan_income_year`. Benchmark rates for future years are not known until just before each year starts; schedules mark them as projected.
- **Repayments that do not count.** Journal entries without a real payment, set-offs without mutual liabilities, accrued interest, and repayments funded by reborrowing are disregarded (s109R); escalate AU-COMP-006.
- **Bendel.** Commissioner of Taxation v Bendel [2026] HCA 18 (10 June 2026) held that a company's unpaid present entitlement left uncalled is not a loan under s109D(3). The ATO's decision impact statement (26 June 2026) accepts this where the company took no relevant action, whether or not the amount is on a separate trust, and says TD 2022/11 will be withdrawn (the ruling is marked as under review). Entitlements already converted into loans or put on complying loan terms remain loans. Subdiv EA and s100A still apply: escalate AU-COMP-004.
- **No clearance on s100A or Subdiv EA.** Whether a reimbursement agreement (s100A) exists or Subdiv EA catches trust payments to shareholders depends on the trust deed, resolutions, cash flows and purpose. Never answer yes or no, even if asked for one, and never say exposure "likely" exists or does not. Explain that Bendel does not decide these provisions, list the facts that matter, quote AU-COMP-004 verbatim, and refer to a registered tax agent (or an ATO private ruling).
- Division 7A deemed dividends are not frankable (except by Commissioner discretion) and are assessable to the recipient; send the shareholder's tax to the individual-tax skill.

- **Getting money out of the company (salary, director fees, dividends, loans).** Lay out each option with its compliance consequences (salary: PAYG withholding, STP, super guarantee, deductible to the company; dividend: resolution, profits available, franking; loan: Division 7A complying agreement, benchmark interest, minimum yearly repayments) and the decision factors (other income and marginal rate, franking account balance, cash needs, super). Do not declare one option the best: the mix depends on modelling, which goes to a registered tax agent. Labelled illustrative figures from the tools are fine.

## Escalation

| Trigger | Code |
|---|---|
| Consolidated or MEC group, losses transferred within a group | AU-COMP-001 |
| Prior-year losses deducted after an ownership or control change (COT, business continuity test) | AU-COMP-002 |
| Carry back integrity rule, foreign resident, excess franking offset losses, amended choice, substituted accounting period | AU-COMP-003 |
| Unpaid trust entitlements owed to a company where Subdiv EA, s100A or sub-trusts are in issue | AU-COMP-004 |
| Distributable surplus must be worked out (revaluations, provisions) | AU-COMP-005 |
| Repay-and-redraw, interposed entities, journal-only repayments, Part IVA | AU-COMP-006 |
| Div 7A loan past its term, refinanced or re-secured, pre-4 December 1997 loan, Commissioner's discretion, non-resident company | AU-COMP-007 |
| Life insurer, RSA provider, pooled development fund, non-profit, strata, non-resident or liquidating company | AU-COMP-008 |
| Benchmark rule breach, franking deficit offset reduction, exempting entities, streaming | AU-COMP-009 |
| A needed figure for the year is not verified | AU-GEN-001 |
| A needed figure has no published value for the year (no draft possible) | AU-GEN-003 |
| Asked to lodge or pay | AU-GEN-002 |

Surface the code and its message exactly as returned (or as in `data/refusals/company-div7a.yaml`), then stop the affected work and offer what can still be done.

## Output

End every answer with this working paper (CONVENTIONS section 8):
1. **Result** for the stated income year: rate and whether a base rate entity (with reasons); tax payable; imputation rate and maximum franking credit; carry back offset with components; MYR, shortfall and deemed dividend; or the schedule table.
2. **Figures used**: key, value, status, source URL from `figures_used`.
3. **Assumptions**: the tool's `assumptions` plus your own.
4. **Risk flags**: relevant entries from `data/risk_flags/company-div7a.yaml` (for example RF-COMP-001 bucket company rate, RF-DIV7A-002 MYR shortfall, RF-DIV7A-005 UPEs after Bendel), or "none".
5. **Refusals or escalations**: codes and messages, plus the tool's `warnings` and `escalations`, or "none".
6. "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use." Copy this sentence verbatim as the last line of the answer; do not paraphrase it.

References: `references/sources.md` (primary sources), `references/rules.md` (method detail and worked-example checks).
