---
name: bookkeeping-year-end
description: 'Australian small-business bookkeeping and year-end close: how long to keep records, chart of accounts and GST codes, bank feed rules, month end and 30 June close (bank and credit card reconciliation, GST control account to BAS, payroll and super payable to STP, accruals, prepayments and the 12-month rule, trading stock and stocktake, depreciation register, bad debts, bonuses and director fees), trial balance checks, and whether a company must prepare financial statements (large proprietary company test, special purpose vs general purpose, AASB 1060). Use when someone says "year end checklist", "does my GST account match my BAS", "can I claim this prepayment before 30 June", "do I need a stocktake", "how long do I keep records", "is my trial balance right", "are we a large proprietary company", "do we need audited accounts", "owner drawings vs wages". Also use for audits, consolidated group accounts, revenue, lease or impairment accounting judgements and ASIC relief: the skill decides scope and escalates.'
---

# Bookkeeping and year-end close (Australia)

Sets up and closes a small business ledger and answers the reporting-threshold question. Arithmetic goes through four tools; never compute a prepayment split, a GST variance, a trial balance or a size test yourself, and never quote a threshold from memory. Figures are named by key in `figures_used`.

## Scope

In scope:
- Record keeping: retention periods, what to keep, digital and cloud records, cash vs accrual choices for income tax and for GST (see `references/records-and-accounts.md`).
- Chart of accounts design, GST codes, payroll and ATO clearing accounts, bank feed rules, drawings vs wages vs loans (`references/records-and-accounts.md`).
- Month end and year end close procedure (`references/close-checklist.md`) and the four calculators below.
- Financial reporting thresholds and types of statements (`references/financial-reporting.md`).

Point to another skill, do not answer here: Division 7A loans, benchmark rate, UPEs (company-div7a); instant asset write-off, depreciation pools, business income and deductions (sole-trader-business); BAS labels, GST cycles, GST credits and bad debt GST adjustments (gst-bas); PAYG withholding, super guarantee, STP (payroll-sg); PAYG instalments (payg-instalments-lodgment); trust distributions (trusts-partnerships).

Out of scope, escalate (Escalation below): audit or assurance work, consolidated group financial statements, judgement areas under the accounting standards (revenue from complex contracts, leases, impairment, business combinations, financial instruments), ASIC relief applications, and whether an entity is a reporting entity when it is disputed.

## Required inputs

Ask for what changes the answer; never assume silently.
1. **Income year** (`2025-26` or `2026-27`) and balance date. Every output states the year applied.
2. **Entity type** (sole trader, partnership, company, trust) and whether it is a small business entity or would be one (aggregated turnover), GST registered, and cash or accrual for tax and for GST.
3. Per tool: see the field lists below.

## Procedure

1. Classify the question: records/accounts design, close procedure, one of the four calculations, reporting obligation, or out of scope. Load the matching reference file for the checklist or rules.
2. For a calculation, gather inputs, confirm the income year, call the tool with `income_year` and `inputs`:
   - `trial_balance_check`: `accounts` list of `{name, debit, credit, type, current, suspense}`; `type` is asset, liability, equity, income, cost_of_sales or expense (needed for ratios); `tolerance`. Use at month end before any reporting.
   - `gst_control_reconciliation`: `ledger_gst_collected`, `ledger_gst_paid`, `bas_1a`, `bas_1b`, optional `ledger_taxable_sales_ex_gst`, `ledger_creditable_purchases_ex_gst`, `opening_balance_payable`, `payments_to_ato`, `refunds_from_ato`, `closing_balance_payable`, `tolerance`, `period`. Variance is ledger minus BAS. The tool gives the GST-inclusive size of a transaction that would explain each variance; investigate that, do not just post a balancing journal.
   - `prepayment_deduction`: `amount` (excluding GST credits), `payment_date`, `service_start`, `service_end`, `taxpayer` (`small_business` includes an entity that would be a small business entity at the medium-entity turnover ceiling; `individual_non_business`; `other_business`; `other_non_business`), optional `aggregated_turnover`, `excluded_expenditure`, `claim_immediate_if_eligible`, `tax_shelter_arrangement`. The `income_year` argument is the year you want the deduction for; the schedule shows every year.
   - `large_proprietary_test`: `entity` and `controlled_entities` each `{name, revenue, gross_assets, employees}` (employees as full-time equivalent at year end), `intra_group_revenue_eliminations`, `intra_group_asset_eliminations`, `company_type`, `control_uncertain`, `foreign_controlled`, `crowd_sourced_funding_shareholders`, `asic_direction`, `shareholder_direction`, `financial_year_end`.
3. Read the envelope:
   - `exit_code` 0: present the result. Quote figures as returned.
   - `exit_code` 3 with `refusal`: quote the code and message verbatim, stop that part, say what can still be done.
   - `exit_code` 4 (AU-GEN-001): a figure is not verified; quote the message. AU-GEN-003 (also exit 4): the figure has no published value for that year, so no draft is possible; quote the message and stop that part.
   - `exit_code` 2: fix the input and call again.
4. For close and design questions, work through the checklist and give the user a short ordered list of the steps that apply to their entity, with the tool call where one exists. Do not present a generic checklist without tailoring it.
5. Trading stock, bad debts, bonuses, depreciation and accruals have no calculator: apply the rules below, state the outcome and the assumptions.

## Judgement rules

- **Retention.** Tax records: the general period is `bookkeeping.record_retention_years`, counted from the later of preparation and completion of the transaction (ITAA 1936 s 262A; TAA 1953 Sch 1 s 382-5). Some records run longer: to the end of the period of review of any return that uses them, and for CGT assets and depreciating assets for as long as owned plus the general period after disposal. Company financial records: `bookkeeping.company_financial_records_retention_years` after the transactions are completed (Corporations Act s 286(2)). Keep the longer period that applies to the record. Digital records must be complete, unaltered and readable after software changes (TR 2018/2); scanned paper is acceptable if true and clear.
- **Prepayments.** The 12-month rule (ITAA 1936 s 82KZM) is a choice for small business entities (and would-be ones) and for individuals with non-business deductions. Both limbs must hold: service period within `bookkeeping.prepayment_max_service_months` and ending no later than the last day of the next income year. Otherwise apportion by days, service period capped at `bookkeeping.prepayment_max_apportion_years`. Amounts below `bookkeeping.prepayment_excluded_amount` (net of GST credits), amounts required by law, wages and capital or private amounts are excluded and deductible when incurred. Tax shelter arrangements are refused (AU-BKP-002).
- **Trading stock.** A stocktake at year end is the default. A small business entity, or one that would be at the medium-entity ceiling (`bookkeeping.medium_entity_turnover_ceiling`), may skip the stocktake and not account for the change if opening stock and a reasonable estimate of closing stock differ by no more than `bookkeeping.simplified_trading_stock_change_max` (ITAA 1997 s 328-285). The choice is per year; a stocktake can still be done. Otherwise value each item at cost, market selling value or replacement value, chosen item by item, with obsolete stock at a reasonable lower value (ITAA 1997 s 70-45); opening stock equals last year's closing stock.
- **Bad debts.** Deductible only if the debt was included in assessable income (so not for cash-basis income) and the decision to write it off is made and recorded in writing before 30 June (ITAA 1997 s 25-35). A company must also pass the continuity of ownership or a business continuity test (s 165-120). A write-off dated 1 July or later belongs to the next year. Whether GST on the debt can be adjusted goes to gst-bas.
- **Accruals.** For accrual-basis taxpayers, an outgoing is deductible when the entity is definitely committed to it, not when paid; unpaid wages, super and supplier invoices at 30 June are accrued. Payday Super: super for each payday is due to be received by the fund within `super.payday_super_usual_period_business_days` (payroll-sg; from 1 Jul 2026) business days after payday, so super payable at year end is only the amounts still inside that window; anything older is late.
- **Bonuses and director fees.** A deduction for the year needs a binding commitment (resolution and notice to the recipient) made by 30 June, not a discretion exercised afterwards. PAYG withholding and super apply when paid or, for super, on qualifying earnings. If terms are unclear, treat as a registered tax agent question.
- **Owner money.** Sole trader or partner drawings are not expenses. In a company, money to a shareholder or associate is wages (withholding and super), a dividend (declared, franked as appropriate), a Division 7A compliant loan, or a director loan account balance that may become a deemed dividend: record it in a separate loan account and use company-div7a. Trust distributions belong to trusts-partnerships.
- **Cash vs accrual.** Income tax basis follows the taxpayer's circumstances (TR 98/1), GST accounting basis is a separate election (GSTA s 29-40, limited by turnover, `gst.cash_accounting_turnover_max`). The ledger should show which basis each report uses; do not mix them within one report.
- **Reporting.** Small proprietary companies are exempt from preparing financial reports unless foreign-controlled, having crowd-sourced funding shareholders, or directed by ASIC or qualifying shareholders (Corporations Act ss 292-294). Large proprietary companies (s 45A; thresholds in `asic.large_proprietary_*`) must prepare, audit and lodge, due `bookkeeping.financial_report_lodgement_months` months after year end (s 319). Which accounting framework applies (general purpose Tier 1 or Tier 2 under AASB 1060, or a special purpose framework) depends on reporting entity status and is for the accountant; explain the options in `references/financial-reporting.md` and do not choose for a large company.
- **Trial balance to tax.** A balanced trial balance does not mean correct coding. Reconcile accounting profit to taxable income with a list of adjustments (non-deductible items, timing differences such as prepayments, stock, depreciation, bad debts, entertainment, private use). State the reconciling items; taxable income itself belongs in the entity's return skill.

## Escalation

| Trigger | Code |
|---|---|
| Audit or assurance, consolidated group accounts, control of another entity unclear, complex revenue, leases, impairment, ASIC relief | AU-BKP-001 |
| Prepayment under a tax shelter arrangement | AU-BKP-002 |
| Size test asked for an entity that is not a proprietary company (public, disclosing, scheme, CLG) | AU-BKP-003 |
| A needed figure for the year is not verified | AU-GEN-001 |
| A needed figure has no published value for the year (no draft possible) | AU-GEN-003 |
| Asked to lodge a report or BAS or to pay | AU-GEN-002 |

Surface the code and message exactly as returned or as in `data/refusals/`, then stop the affected work.

## Output

End every answer with this working paper (CONVENTIONS section 8):
1. **Result** for the stated income year (tool output, or the tailored checklist).
2. **Figures used**: key, value, status, source URL for each `figures_used` entry.
3. **Assumptions**: the tool's `assumptions` plus your own (basis, entity type, small business status).
4. **Risk flags**: relevant entries from `data/risk_flags/bookkeeping.yaml` (for example BKP-RF-001 to BKP-RF-008), or "none". Include the tool's `warnings`.
5. **Refusals or escalations**: codes and messages, or "none".
6. "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use." Copy this sentence verbatim as the last line of the answer; do not paraphrase it.

References: `references/records-and-accounts.md`, `references/close-checklist.md`, `references/financial-reporting.md`, `references/sources.md`.
