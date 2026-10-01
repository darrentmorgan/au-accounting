---
name: payg-instalments-lodgment
description: 'Works out Australian PAYG instalments, lodgment and payment due dates, late lodgment penalties and ATO interest for 2025-26 and 2026-27: whether someone must pay PAYG instalments, the quarterly instalment amount or rate (with the GDP adjustment), varying instalments and the safe harbour that avoids GIC, BAS and instalment due dates, self-lodged return, TPAR and STP dates, the failure to lodge on time penalty (penalty units, entity size) and general interest charge or shortfall interest charge by quarter. Use when someone asks "do I have to pay PAYG instalments", "what is my quarterly instalment", "should I vary my instalments", "when is my BAS due", "when is my tax return due", "penalty for lodging late", "how much GIC on my ATO debt", "ATO interest rate this quarter". Also use for requests to remit a penalty, set up a payment plan, object to a penalty or interest decision, or for shortfall penalties and recklessness: the skill decides scope and escalates those to a registered tax agent.'
---

# PAYG instalments, lodgment dates, penalties and interest (Australia)

Uses the `payg_entry_check`, `payg_instalment`, `payg_variation_check`, `lodgment_due_dates`, `failure_to_lodge_penalty` and `general_interest_charge` tools. Never do the arithmetic yourself and never quote a rate, threshold, penalty unit or date from memory: every figure comes from a tool result and its `figures_used`.

## Scope

In scope (Taxation Administration Act 1953 (TAA) Sch 1):
- Entry to PAYG instalments (Div 45) and whether the taxpayer must, or may voluntarily, pay.
- Instalment amount method (GDP-adjusted notional tax), instalment rate method, annual and two-instalment payers, varying an amount (T8, T9, T4) or a rate (T3), credits at 5B.
- The safe harbour test for varied instalments and indicative GIC (Subdiv 45-G).
- Due dates: quarterly BAS and instalment notices, online concession, self-lodged individual return and its payment date, TPAR, STP finalisation.
- Failure to lodge on time penalty (s 286-80).
- GIC (ss 8AAB, 8AAD) and SIC (s 280-105) by quarter, compounded daily.
- Awareness only (no calculation): shortfall penalty base percentages (Div 284), remission, safe harbour for agents.

Out of scope, escalate: consolidated groups, monthly instalment payers, GST instalments, substituted accounting periods with non-standard quarters, the ATO dynamic accounting-software method (AU-PAYG-001); remission with contested facts (AU-PAYG-003); payment plans, objections, disputes (AU-PAYG-004); shortfall penalties with recklessness or intentional disregard, or voluntary disclosure reductions (AU-PAYG-005). The tools never lodge or pay (AU-GEN-002).

## Required inputs

Ask for what changes the answer; do not assume the income year silently.
1. Income year (`2025-26` or `2026-27`). "This year" is ambiguous. For a return, the income year is the year the return covers; for quarters, the year the quarter falls in.
2. Entity type: individual (including sole trader), trust, company or super fund.
3. For instalments: the notional tax on the ATO notice (amount method), or instalment income for the quarter and the rate at T2 (rate method). Instalment income is gross business and investment income excluding GST and capital gains.
4. For a variation: estimated tax for the whole year, instalments already reported, and which quarter.
5. For a penalty: date the document was due, days late, entity size at that date (small, medium, large, significant global entity), and whether the result is a refund or nil.
6. For interest: the amount, the due date and the payment date (or calculate-to date), GIC or SIC.

## Procedure

1. Confirm the income year and entity. If any out-of-scope circumstance applies, pass it in `special_circumstances` (AU-PAYG-001 comes back) or say which escalation code applies and stop that part.
2. Pick the tool:
   - "Do I have to pay instalments": `payg_entry_check` with `entity_type`, `instalment_income`, `tax_payable_on_assessment`, `notional_tax`.
   - "What is my instalment": `payg_instalment` with `method` (`amount`, `rate`, `varied_amount`, `varied_rate`), `quarter`, `frequency`, and the amount fields. Field names: `notional_tax`, `instalment_income`, `instalment_rate_percent` (a percentage figure, for example the number 11 for an eleven per cent rate), `estimated_tax`, `earlier_instalments_paid`, `credits_claimed_earlier`, `sap_income_year_start`.
   - "Will varying cost me GIC": `payg_variation_check` with `benchmark_tax`, `estimated_tax`, `instalments_paid` (one entry per quarter) and optionally `assessment_due_date`; or `method: rate` with `varied_rate_percent` and `benchmark_rate_percent`.
   - "When is X due": `lodgment_due_dates` with `obligation` and `quarter` where relevant.
   - "Late lodgment penalty": `failure_to_lodge_penalty` with `days_late`, `due_date`, `entity_size`.
   - "Interest on a debt": `general_interest_charge` with `amount`, `from_date` (the due date), `to_date`, `charge`.
3. Read the envelope:
   - `exit_code` 0: present the result.
   - `exit_code` 3 with `refusal`: quote the code and message verbatim and stop that part. AU-PAYG-002 means a rate for a period is not published or not loaded: give the result up to the last published quarter if useful, say which quarter is missing, and do not estimate a rate.
   - `exit_code` 4 (AU-GEN-001): a figure for that year is not verified; quote the message. AU-GEN-003 (also exit 4): the figure has no published value for that year, or a due date touches a public holiday whose date is not declared, so no draft is possible; quote the message and stop that part. Exit 3 with AU-GEN-004: the due date is outside the public holiday data; quote it and send the user to the ATO's lodgment and payment dates on weekends or public holidays page.
   - `exit_code` 2: fix the input.
4. Quote numbers as returned. Do not round differently.
5. Mention the tool's `warnings` that matter (business day roll, concession, refund or nil practice, safe harbour).

## Judgement rules

- Instalments are prepayments of the year's income tax, credited in the assessment; varying does not change the tax for the year. Instalments must be lodged and paid before the return is lodged so the credit is taken.
- Choosing amount or rate ("which should I pick"): the choice never changes the tax for the year, only the timing of prepayments, because instalments are credited in the assessment. The rate method (T1 x T2 = T11) rises and falls with each quarter's instalment income, so it suits lumpy or falling income and cash flow, but the taxpayer must report instalment income every quarter. The amount method (T7) is a fixed quarterly payment from the last return uplifted by the GDP adjustment, so it is simple but can overpay in a quiet quarter and leave a large tax bill after a strong year. The taxpayer chooses on the first activity statement of the income year and keeps that option for the rest of the year; switching waits until the next year. Look up the GDP adjustment for the year with `get_figure` (`payg_instalments.gdp_adjustment`) and state its value; never state it from memory.
- The GDP adjustment applies to the amount method only, not the rate method or annual payers, and differs by income year; substituted accounting period taxpayers whose year began 1 January to 1 March 2026 keep the earlier factor (the tool handles it when `sap_income_year_start` is given).
- Varying: the test is on the estimate used and the instalments paid against the benchmark tax (or rate) for the year, not on cash flow. If unsure, advise not to vary, because overpaid instalments are refunded. The ATO expects a reasoned forecast; the dynamic method for accounting software users is draft guidance (PCG 2026/D3) and out of scope.
- Every "should I vary" answer, including a conceptual answer where no tool is called, must do three things. (1) Name the activity statement labels: amount method T8 (estimated tax for the year) and T9 (varied amount); rate method T3 (varied rate); and T4, the reason code, with either method (`references/rules.md`; ATO instalment activity statement instructions). (2) Read the safe harbour ratio with `get_figure` (`payg_instalments.variation_safe_harbour_ratio`), state it as a number, and say that GIC applies to the shortfall if the varied instalments fall below that share of the benchmark tax or rate (TAA Sch 1 Subdiv 45-G, ss 45-230, 45-232, 45-235). (3) Say that administrative penalties (TAA Sch 1 Div 284) may also apply if reasonable care is not taken with the estimate. Do not encourage varying to nil for cash flow unless the estimate is supported by the actual position.
- The benchmark the ATO applies is the Commissioner's own (Subdiv 45-K); the tool takes the taxpayer's figure as a stand-in, so present the GIC figure as indicative. The Commissioner may remit the GIC (s 45-240).
- A due date that is not a business day moves to the first business day after (TAA 1953 s 8AAZMB for payments, Sch 1 s 388-52 for approved forms). Business day means not a Saturday, Sunday or a public holiday for the whole of any State, the ACT or the NT, wherever the taxpayer is; the tool reads the holidays from the public holiday data and returns the original date, the rolled date, the reason and the rule in `business_day_roll`. GIC is not rolled. A date outside the holiday data is refused (AU-GEN-004) by `lodgment_due_dates`, where the date is the answer; `payg_instalment` still returns the instalment amount and lists AU-GEN-004 in `field_refusals` against the unrolled date, which you must not present as checked; a date that touches a holiday not yet declared behaves like an unverified figure (AU-GEN-001 with a marked draft, or AU-GEN-003). Where the ATO's own table prints a different first business day from the statute, the tool returns the statutory date and warns with the ATO's printed date: quote both. The two-week online concession applies to online-lodged quarterly BAS in quarters 1, 3 and 4 only, never quarter 2, never instalment notices.
- Registered tax or BAS agent clients may have later lodgment program dates set by the ATO each year; the tool does not compute them. See `references/rules.md`; tell the user to check their client listing.
- The failure to lodge penalty uses the penalty unit in force on the day the document was due, not the day it was lodged. Size is tested at the due date. The ATO generally does not penalise a late return or activity statement that ends in a refund or nil, with exceptions (third-party data reports, large withholders, penalty already applied). Safe harbour can apply when a registered agent was given everything in time.
- GIC and SIC compound daily and keep running under a payment plan. They are not deductible when incurred from 1 July 2025.
- Shortfall penalties are set as a share of the shortfall by behaviour (failure to take reasonable care, recklessness, intentional disregard): state the base percentages from the figures, never compute or predict a penalty, and escalate.

## Escalation

| Trigger | Code |
|---|---|
| Consolidated group, monthly payer, GST instalments, non-standard substituted accounting period, dynamic accounting-software method | AU-PAYG-001 |
| Interest rate for a quarter not published, or period or penalty unit not loaded | AU-PAYG-002 |
| Remission request with contested facts or judgement about circumstances | AU-PAYG-003 |
| Payment plan, debt negotiation, objection, review or dispute | AU-PAYG-004 |
| Shortfall penalty with recklessness or intentional disregard, or one that must be calculated or reduced | AU-PAYG-005 |
| A needed figure for the year is not verified | AU-GEN-001 |
| A needed figure has no published value for the year (no draft possible) | AU-GEN-003 |
| A due date or business-day count is outside the public holiday data | AU-GEN-004 |
| Asked to lodge, vary or pay for the taxpayer | AU-GEN-002 |

Surface the code and its message exactly as returned or as written in the refusal catalogue, then stop the affected work. You may still explain what the ATO looks for in a remission request; you may not prepare or lodge it.

## Output

End every answer with this working paper (CONVENTIONS section 8):

1. **Result** for the stated income year: the amount, date, penalty or interest, with the basis (method, quarter, days, rate rows).
2. **Figures used**: key, value, status, source URL for each entry in `figures_used` (group long rate tables as "GIC quarterly rates (VERIFIED)").
3. **Assumptions**: the tool's `assumptions` plus any you made.
4. **Risk flags**: relevant entries from `data/risk_flags/payg-lodgment.yaml` (for example the safe harbour on varying, GIC not deductible, daily compounding), or "none".
5. **Refusals or escalations**: codes and messages, or "none". Include the tool's `warnings`.
6. "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use." Copy this sentence verbatim as the last line of the answer; do not paraphrase it.

References: `references/sources.md` (primary sources), `references/rules.md` (labels, calendar, edge cases).
