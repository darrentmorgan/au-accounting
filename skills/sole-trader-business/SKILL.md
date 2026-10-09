---
name: sole-trader-business
description: 'Prepares Australian sole trader (ABN, freelancer, contractor, gig worker, tradie) business income tax workings for 2025-26 and 2026-27 - business deductions and private-use apportionment, small business entity status, simplified depreciation and the instant asset write-off (including the permanent threshold for assets first used from 1 July 2026), the small business pool, car expenses (cents per km v logbook), home office (fixed rate v actual cost), the small business income tax offset, non-commercial (hobby-style) business losses, and personal services income (PSI rules, personal services business tests, "am I a contractor or an employee for tax"). Use for "can I write off this ute/laptop", "instant asset write-off", "how much small business tax offset", "can I claim my business loss against my wages", "do the PSI rules apply to me", "work from home rate for my business". Also use when a sole trader asks about a PSB determination, trading stock, GST or a partnership: the skill decides scope and escalates.'
---

# Sole trader business (Australia)

Works out sole trader business deductions, depreciation, offsets and loss rules through the `au-tax` calculators. Never do the arithmetic yourself and never quote a rate or threshold from memory; every figure comes from a tool's `figures_used`.

## Scope

In scope:
- Business income and deductions for an individual carrying on a business (general deduction ITAA 1997 s 8-1; private and domestic apportionment s 8-1(2)(b)).
- Small business entity status (ITAA 1997 s 328-110): aggregated turnover below the small business entity threshold, tested per year on the aggregated (connected entities and affiliates) figure. Concession thresholds differ; see Judgement rules.
- Simplified depreciation (Subdiv 328-D): instant asset write-off and the general small business pool, `simplified_depreciation`.
- Car expenses (Div 28): `car_expense_cents_per_km` (cents per km v logbook).
- Home office: `home_office_fixed_rate` (PCG 2023/1) v actual cost.
- Small business income tax offset (Subdiv 328-F): `small_business_income_tax_offset`.
- Non-commercial losses (Div 35): `non_commercial_loss_test`.
- Personal services income (Pt 2-42, Divs 84 to 87): `psi_tests`.
- Simplified trading stock rules: see Judgement rules.

Out of scope, escalate: personal services business determinations, Commissioner's discretion for non-commercial losses (AU-BUS-002), excepted activities and partnership losses, trading stock valuation elections beyond the simplified rules, hobby v business disputes, general (non-simplified) depreciation, partnerships and trusts (use `trusts-partnerships`), GST and BAS (use `gst-bas`), CGT on business assets and small business CGT concessions (use `cgt`), companies (use `company-div7a`). Tax on the resulting taxable income is the `individual-tax` skill.

## Required inputs

Ask for anything missing that changes the answer.

1. **Income year** (`2025-26` or `2026-27`). Ask if unclear. Depreciation depends on the date each asset was first used or installed ready for use, not the purchase date.
2. **Aggregated turnover** (own plus connected entities and affiliates) and whether the business is a sole trader.
3. Task-specific facts: assets (cost, first-use date, business use, GST credit status), opening pool balance, disposals; car kilometres or logbook; hours worked from home and how they are recorded; net business income and taxable income; loss, other income and the four-test facts; PSI client and test facts.

## Procedure

1. Establish the income year and small business entity status. If aggregated turnover is not below the entity threshold, simplified depreciation is unavailable (`simplified_depreciation` refuses AU-BUS-003) and the small business income tax offset has a lower threshold again.
2. Pick the calculator:
   - Asset write-offs: `simplified_depreciation`. Pass `assets` (name, cost, first_used_date, business_use_percent, asset_type), `opening_pool_balance`, `disposals`, `cost_additions`. Cost is GST-exclusive if GST credits are claimed, otherwise GST-inclusive. Set `asset_type` to `passenger_car` for cars.
   - Car: `car_expense_cents_per_km` with `business_km` and, to compare, `logbook_total_car_expenses` and `logbook_business_use_percent`.
   - Home office: `home_office_fixed_rate` with `hours_worked_from_home`, `hours_record_kept` and optionally `actual_running_costs_business_portion`.
   - Offset: `small_business_income_tax_offset` with `aggregated_turnover`, `net_small_business_income`, `taxable_income`.
   - Loss: `non_commercial_loss_test`; PSI: `psi_tests`.
3. Read the envelope:
   - `exit_code` 0: use the result. Present every `warnings` entry.
   - `exit_code` 3 with `refusal`: quote the code and message verbatim, stop that part, and say what can still be done.
   - `exit_code` 4 (AU-GEN-001): a figure is not verified for that year. Quote the message. AU-GEN-003: no published value, so no draft is possible. For the home office fixed rate in 2026-27 no rate has been published (AU-GEN-003): say so, offer the actual cost method, and if a comparison helps give the prior-year result clearly labelled as prior year.
   - `exit_code` 2: fix the input and call again.
4. Combine results only by stating them side by side. Do not compute a blended tax figure; pass taxable income to `individual-tax`.
5. Quote the tool's numbers as returned, in dollars and cents.

## Judgement rules

- **General deduction** (s 8-1): incurred in gaining or producing assessable income or necessarily in carrying on a business; not capital, private or domestic, or for exempt income. Apportion mixed-use expenses on a fair basis and keep records. Do not decide borderline cases (AU-BUS-006).
- **Thresholds are different concessions**: the small business entity threshold governs simplified depreciation and the instant asset write-off; the small business income tax offset threshold is lower; other concessions (GST cash basis, trading stock, prepaid expenses, PAYG instalments) each have their own. Never use one concession's threshold for another; use `list_figures`/`get_figure` for the amounts.
- **Instant asset write-off**: per asset, cost must be below the threshold; the business portion is deducted. The threshold for assets first used or installed ready for use on or after 1 July 2026 is set permanently by Treasury Laws Amendment (Tax Reform No. 2) Act 2026 Sch 2; the same amount applied to assets first used in 2025-26 under the earlier temporary extension. An asset bought in June but first used in July belongs to the later year. Assets at or above the threshold go to the pool: first-year rate on additions, later-year rate on the opening balance, whole pool written off when the balance before depreciation is below the threshold. Cars pooled at the car limit. Business use must be reviewed for the three years after pooling.
- **Simplified depreciation is all or nothing** for depreciating assets: a business that opted out may be locked out; escalate (AU-BUS-003).
- **Cents per km**: cars only, sole traders and partnerships with an individual partner, capped per car; covers all running costs and depreciation. Above the cap the logbook method must cover the whole claim. Home-to-work travel is private.
- **Home office**: the fixed rate needs a record of actual hours for the whole year, not an estimate (PCG 2023/1). It covers energy, phone, internet, stationery and consumables; depreciation of equipment is claimed separately. Occupancy expenses need an area with the character of a place of business and can affect the main residence CGT exemption (cross-refer `cgt`).
- **Non-commercial losses**: the income requirement uses taxable income before the loss plus reportable fringe benefits, reportable super and net investment losses. One passed test plus the income requirement lets the loss offset other income; otherwise it is deferred, not lost. Failing the income requirement raises the Commissioner's discretion: escalate (AU-BUS-002). Deferred losses are added back to net small business income.
- **Small business income tax offset**: sole trader (and eligible partnership or trust share) net small business income only; excludes net capital gains, PSI unless a personal services business, wages and unrelated interest. Non-refundable, one cap per individual.
- **PSI**: applies regardless of ABN. Results test alone, or another test plus the eighty per cent single-client rule. Uncertain facts, an eighty per cent client, or a determination request: escalate (AU-BUS-001). Passing a test does not remove Part IVA risk (PCG 2025/5). Consequences when the rules apply: attribution to the individual and limited deductions.
- **Standard deduction interaction (2026-27)**: the standard deduction for work-related expenses under s 25-130 is a top-up for assessable labour income (wages). A pure sole trader with no wages gets nothing from it and it is not additive to business deductions. If the person also earns wages, hand the work-related claim to `individual-tax` and keep business claims separate.
- **Trading stock**: the simplified rules let a small business skip the stocktake if the estimated change is within the tolerance; a stocktake can still be chosen. Valuation choices beyond that: escalate (AU-BUS-006).
- Tax-time changes with a start date are modelled in the tools; do not apply a rule to an earlier year than the tool did.

## Escalation

| Trigger | Code |
|---|---|
| PSB tests uncertain, eighty per cent rule blocks, determination sought, Part IVA concern | AU-BUS-001 |
| Commissioner's discretion, excepted activity, partnership loss | AU-BUS-002 |
| Not a small business entity, opted out, excluded asset | AU-BUS-003 |
| Cents per km not available, no actual-hours record | AU-BUS-004 |
| Asset first-use date outside the income year | AU-BUS-005 |
| Hobby v business, borderline deduction, trading stock election, determination application | AU-BUS-006 |
| A needed figure is not verified for the year | AU-GEN-001 |
| A needed figure has no published value for the year (no draft possible) | AU-GEN-003 |
| Asked to lodge | AU-GEN-002 |

Surface the code and message exactly as returned, then stop the affected work.

## Output

End every answer with this working paper (CONVENTIONS section 8):

1. **Result** for the stated income year, per calculator used.
2. **Figures used**: key, value, status, source URL from `figures_used`.
3. **Assumptions**: the tools' `assumptions` plus any you made.
4. **Risk flags**: relevant entries from `data/risk_flags/business.yaml` (for example BUS-DEP-001, BUS-WFH-001, BUS-NCL-001), or "none".
5. **Refusals or escalations**: codes and messages, plus the tools' `warnings`, or "none".
6. "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use." Copy this sentence verbatim as the last line of the answer; do not paraphrase it.

References: `references/sources.md` (primary sources), `references/rules.md` (calculation detail and edge cases).

For an employee standard work deduction in 2026–27 or later, hand the qualifying wage facts to `individual-tax` and its `standard_work_deduction` tool before router assembly. Business/ABN income is not qualifying assessable labour income for this deduction. Do not reuse the standard-deduction cap as a business expense.
