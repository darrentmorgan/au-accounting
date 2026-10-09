---
name: individual-tax
description: 'Works out Australian individual income tax for 2025-26 to 2027-28 - tax on taxable income, low income tax offset, the working Australians tax offset, Medicare levy (including the low-income and family reductions), Medicare levy surcharge, and compulsory HELP or other study loan repayments - for residents, part-year residents, foreign residents and working holiday makers. Use when someone asks "how much tax will I pay on X", "what''s my take-home", "do I pay the Medicare levy surcharge", "MLS if I don''t have private health", "HELP repayment this year", "HECS repayment", "tax for a working holiday maker", "tax as a non-resident", or "tax if I moved to Australia part way through the year". Also use for any question about tax on a child''s or minor''s income (including trust distributions to children), a deceased person''s final return, redundancy, termination or other lump-sum payments, and super lump sums: the skill decides what is in scope and escalates special regimes to a registered tax agent.'
---

# Individual income tax (Australia)

Computes an individual's tax for one income year through the `individual_income_tax` tool. Never do the arithmetic yourself and never quote a rate or threshold from memory; every figure comes from the tool's `figures_used`.

## Scope

In scope:
- Australian residents (full year or part year), foreign residents all year, working holiday makers (visa subclass 417 or 462) who are foreign residents and whose income is all working holiday taxable income.
- Tax on taxable income (Income Tax Rates Act 1986 Sch 7; part-year tax-free threshold ITRA ss18-20).
- Low income tax offset (ITAA 1997 Subdiv 61-D). Non-refundable; never reduces the Medicare levy or study loan repayments.
- Medicare levy (Medicare Levy Act 1986 s6), low-income shade-in (s7), family reduction (s8), exemption days (s9; ITAA 1936 s251U).
- Medicare levy surcharge (MLA ss8B-8D): tier from income for MLS purposes, single or family thresholds, days without cover.
- Compulsory study loan repayment on repayment income (Higher Education Support Act 2003; marginal schedule from 2025-26).

Out of scope (tool refuses, see Escalation): seniors and pensioners tax offset, deceased estates, trustee-assessed income, minors' unearned income (ITAA 1936 Div 6AA), employment termination payments and super lump sums, lump sums in arrears, income averaging, first home super saver releases, foreign-resident study loan debtors, working holiday makers who are tax residents or have other income. Not modelled but not refused: franking credits, private health insurance rebate, other offsets, PAYG instalments. For any affected case, state **final settlement not computed** at the top. The tool's `total_liability` and `estimated_refund` cover only its modelled components; do not present them as final tax, refund or debt. Include the agent reconciliation below.

Taxable income is an input. If the user gives gross salary and deductions instead, use `assemble_taxable_income` through `router`; never subtract in prose. For deductions, rental, CGT or business income load the relevant skill first.

## Required inputs

Ask for anything missing that changes the answer. Do not assume silently.

1. **Income year** (`2025-26`, `2026-27` or `2027-28`; 2027-28 is 1 Jul 2027 to 30 Jun 2028). Each year reads its own rates file, so 2027-28 uses the 2027-28 resident rates and never the 2026-27 ones. If unclear, ask. "This year" is ambiguous between the year whose return is being lodged and the current income year.
2. **Residency**: resident, foreign resident, or working holiday maker. If they moved to or left Australia during the year, ask how many months they were resident (count the month of arrival or departure) and, if known, the exact non-resident days.
3. **Taxable income** for the year, or source-labelled components through router assembly. For employee deductions use `skills/router/references/employee-deductions.md` to identify method, evidence, reimbursement/private use and duplicate claims.
4. For Medicare and MLS: spouse on 30 June (and spouse's taxable income), number of dependent children, and whether they held appropriate private patient hospital cover all year (if not, how many days without cover).
5. For study loans: whether they have a HELP or other study loan debt; reportable fringe benefits, net investment losses (financial plus rental), reportable super contributions and exempt foreign employment income, which also feed the MLS income test.
6. Optional: PAYG tax withheld. Also ask about franking credits, PHI rebate adjustments, other offsets, PAYG instalments and other credits before treating an estimate as complete within the modelled scope.

## Procedure

1. Collect the inputs above. Confirm the income year before calling the tool. Run the owner abroad check first (Judgement rules): if it applies, lead with AU-RES-004 and do not call the tool.
2. **Employee deduction handoff (2026–27 and later only).** Before assembly, establish Australian residency at any time, qualifying `assessable_labour_income` under ITAA 1997 s 25-130(4), and eligible `reducing_deductions` under s 25-130(2)(c)–(g). These cover labour-related general costs, car/travel, relevant depreciating-asset deductions and COVID tests. Insurance premiums and trade/business/professional association membership in s 25-130(3) do not reduce the top-up; personal super, gifts and tax-affairs deductions do not reduce it either. Business/investment income does not qualify as labour income. Escalate special lump sums or uncertain classification. Call `standard_work_deduction` with `resident_at_any_time`, `assessable_labour_income`, `reducing_deductions`. Its cap is `individual.standard_work_deduction_cap`; pass only `additional_deduction` as one `work_related_deduction` component from `individual-tax`/`standard_work_deduction` to router assembly, retaining existing eligible deductions once. Never apply this to 2025–26, never add the full cap on top of actual costs, and never subtract again from taxable income already containing the top-up. If inclusion is unknown, resolve it first. This handoff does not override missing Medicare thresholds or any refusal in the subsequent tax calculation.
3. Call `individual_income_tax` with `income_year` and `inputs`, for example:
   `income_year: "2026-27"`, `inputs: {"taxable_income": <amount>, "residency": "resident", "private_hospital_cover": false}`.
   Field names: `taxable_income`, `residency` (`resident` | `foreign` | `whm`), `resident_months`, `has_spouse`, `spouse_taxable_income`, `spouse_income_for_mls`, `dependent_children`, `private_hospital_cover`, `days_without_cover`, `has_help_debt`, `help_debt_balance`, `reportable_fringe_benefits`, `net_investment_losses`, `reportable_super_contributions`, `exempt_foreign_employment_income`, `medicare_full_exemption_days`, `medicare_half_exemption_days`, `sapto_eligible`, `whm_tax_resident`, `whm_other_income`, `net_labour_income` (2027-28 onwards, for the working Australians tax offset: labour, personal services and individual business income less the deductions for earning it; ask for it, never derive it from taxable income), `special_circumstances`, `tax_withheld`.
4. If the person is of age pension age or receives a pension, set `sapto_eligible: true` (the tool will refuse with AU-IND-002). If any special regime in the out-of-scope list is present, pass it in `special_circumstances`.
5. Read the envelope:
   - `exit_code` 0: present the result (Output below).
   - `exit_code` 3 with `refusal`: quote the code and message verbatim, stop that part, offer what can still be done (for example, the income tax without the refused component).
   - `exit_code` 4 with refusal `AU-GEN-001`: a figure for that year is not yet verified; quote the message and offer a marked draft with `allow_draft: true`. With `AU-GEN-003`: a figure has no published value, so no draft is possible; quote the message. For 2026-27 and 2027-28 this happens (AU-GEN-003) for incomes near the Medicare low-income range because those thresholds have not been set; for 2027-28 it also happens for the Medicare levy surcharge when cover is missing or partial (the tiers are unpublished) and for any study loan repayment (the schedule is unpublished). Offer the 2025-26 figure as a comparison, clearly labelled, and do not present it as the answer for the later year. Do not retry with `allow_draft: true` after AU-GEN-003.
   - `exit_code` 2: fix the input and call again.
6. If `private_hospital_cover` was not given, the tool reports a contingent MLS amount instead of adding it (for 2027-28, where the tiers are unpublished, it shows none and says so); ask the user and rerun if it matters. For 2027-28 without `net_labour_income` the working Australians tax offset is not applied and the tax is overstated by up to the offset: say so, or ask for the figure.
7. Never recompute or round the tool's numbers differently. Quote them as returned, in dollars and cents.

## Judgement rules

- **Owner abroad (lead with the escalation).** A person who owns or lets Australian property (a let-out home, a holiday rental, a former home) and says they have moved overseas or are a foreign resident, where residency rests only on that statement (no dates, days in Australia, ties or intention given) and they ask what tax they pay, whether they get the tax-free threshold, or what happens on a sale: open with AU-RES-004 verbatim (AU-RES-001 instead where a treaty country such as Singapore is in play; both messages are in `data/refusals/residency.yaml`), before any headline. Give no tax payable, taxable income, total, rate application, Medicare or CGT amount, no worked illustration with made-up figures, and call no calculator on the rent or the sale. Orientation in words only: a foreign resident is generally taxed on Australian-source rent at foreign resident rates with no tax-free threshold and no Medicare levy, a foreign resident at the sale contract date generally cannot use the main residence exemption, and withholding can apply on a sale. Hand the residency question to `residency-cross-border` and the review to a registered tax agent with cross-border experience. Do not call `individual_income_tax` for them. This does not apply to a plain computation where residency is a settled input for the year (for example an employee stated to be a foreign resident for the whole income year, with the taxable income given): compute as usual and list residency as an assumption.
- Residency is a question of fact (ITAA 1936 s6(1) tests). If residency is unclear, do not guess: use the residency-cross-border skill or ask. A person present for part of the year may be resident for the whole year.
- Part-year residents get a reduced tax-free threshold (ITRA s20) and the non-resident days are Medicare exemption days. The tool estimates the days from months unless exact days are given; say which was used.
- Working holiday makers: Addy v Commissioner of Taxation [2021] HCA 34 means some nationals may get resident rates through a treaty non-discrimination article. Treat that as out of scope (AU-IND-004).
- Medicare family reduction for a sole parent assumes family tax benefit was payable for each child (MLA s8(6)); confirm with the user.
- MLS: the tier is set by income for MLS purposes (combined with a spouse for families), but the surcharge is charged on taxable income plus reportable fringe benefits only. A single dependant without appropriate cover can trigger the family surcharge.
- Study loan repayments are not reduced by offsets and are capped at the outstanding balance if one is given.
- "Take-home pay" needs gross pay, not taxable income. If the user asks for take-home, ask for gross pay and deductions, and describe the result as an estimate of annual tax, not a payslip.

## Escalation

| Trigger | Code |
|---|---|
| Deceased estate, trustee-assessed income, minor's unearned income, ETP or super lump sum, lump sum in arrears, income averaging, FHSS release | AU-IND-001 |
| May be entitled to the seniors and pensioners tax offset | AU-IND-002 |
| Foreign resident or overseas resident with a study loan | AU-IND-003 |
| Working holiday maker who is a tax resident, has other income, or relies on a treaty | AU-IND-004 |
| A needed figure for the year is not verified | AU-GEN-001 |
| A needed figure has no published value for the year (no draft possible) | AU-GEN-003 |
| Asked to lodge or pay | AU-GEN-002 |

Surface the code and its message exactly as returned, then stop the affected work.

## Output

Lead with **Limitations and completeness** before any amount: quote the tool's top-level `limitations` (id, kind, message and affected fields), `total_status` and `completeness_scope`; write "none" for an empty list. A false `total_complete` means the dependent total must be labelled conditional or incomplete exactly as returned, never complete. When taxable income comes from `assemble_taxable_income`, pass its `limitations` unchanged as `upstream_limitations`; the tool then folds them into its own `limitations` and `total_status`, because a complete component calculation cannot make an assumed taxable income complete. Completeness covers only the modelled component liability; it never establishes a final settlement or removes the agent reconciliation below.

End every answer with this working paper (CONVENTIONS section 8):

1. **Result** for the stated income year: taxable income; gross tax; LITO; income tax after offsets; Medicare levy (say if reduced and why); Medicare levy surcharge (tier, or contingent); study loan repayment; total liability; effective rate; marginal rate on the next dollar; a provisional withholding estimate only after confirming no omitted offsets/credits. If any are present or unknown, label the dependent settlement incomplete and show the agent reconciliation.
2. **Figures used**: key, value, status, source URL for each entry in `figures_used` (group long bracket tables as "resident rates (VERIFIED)").
3. **Assumptions**: the tool's `assumptions` plus any you made (for example, taxable income assembled from source-labelled components).
4. **Risk flags**: any relevant entries from `data/risk_flags/au.yaml` (for example, residency or MLS cover issues), or "none".
5. **Refusals or escalations**: codes and messages, or "none". Include the tool's `warnings`.
6. "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use." Copy this sentence verbatim as the last line of the answer; do not paraphrase it.

## Agent reconciliation

Record each item as absent (confirmed), supplied (source/year/amount) or unresolved: PAYG withheld; PAYG instalments actually credited by the ATO; franking gross-up and associated credit; PHI premiums/rebate received and final rebate adjustment; FITO, SBITO and other offsets; other credits and prior account balances. Separate assessable-income gross-ups from offsets/credits. Show the tool-derived components and separately produced offsets beside each other, without hand-netting. The agent must determine offset ordering, refundability, entitlement, credit matching and the final assessment/account balance. Withhold any claim of a final refund/debt for affected cases. See `docs/eofy-reviewer-pack.md`.

References: `references/sources.md` (primary sources), `references/rules.md` (calculation order and edge cases).
