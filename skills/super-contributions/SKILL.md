---
name: super-contributions
description: 'Works out an individual''s Australian super contribution position for 2025-26 or 2026-27: concessional cap, carry-forward (catch-up) contributions, excess contributions, personal super deductions and the notice of intent, non-concessional cap and bring-forward, Division 293, Division 296 tax on large balances (from 2026-27), co-contribution, LISTO, spouse contribution offset, downsizer. Use when someone asks "how much can I put into super", "put extra into super and claim it on tax", "carry-forward contributions", "did I go over my cap", "salary sacrifice limit", "bring forward rule", "after-tax lump sum into super", "Div 293", "the new tax on super balances over three million", "co-contribution", "put money in my partner''s super" or "downsizer". Also use for SMSF administration, defined benefit funds, excess non-concessional determinations, starting a pension, or Division 296 valuation disputes: the skill decides scope and escalates.'
---

# Super contributions (Australia, individual member)

Works out one member's contribution caps and super taxes through the `au-tax` tools. Never do the arithmetic yourself and never quote a cap, threshold or rate from memory: every figure comes from the tool's `figures_used`. Employer SG obligations (how much an employer must pay, Payday Super, SG charge) belong to the payroll-sg skill.

## Scope

In scope (tools in brackets):
- Concessional contributions: what counts (employer and SG, salary sacrifice, personal contributions claimed as a deduction), the concessional cap, five-year carry forward of unused cap for members whose total super balance (TSB) at the prior 30 June is below the carry-forward limit, excess concessional contributions (`concessional_cap_position`).
- Personal deductions: notice of intent timing and age tests (ITAA 1997 ss290-150 to 290-180).
- Non-concessional contributions: annual cap, nil cap at or above the general transfer balance cap, bring-forward periods of two or three years, remaining cap inside an existing period, excess amounts (`bring_forward_nonconcessional`).
- Division 293 tax (`div293_tax`).
- Division 296 tax on earnings for large balances, from 2026-27 (`div296_tax`).
- Government co-contribution (`co_contribution`), low income super tax offset (`low_income_super_tax_offset`), spouse contribution tax offset (`spouse_offset`), downsizer contributions (`downsizer_contribution`).
- Awareness only (explain, no calculation): transfer balance cap, first home super saver scheme (releases are handled by individual-tax, which escalates them).

Out of scope (escalate, see table): SMSF administration, defined benefit interests, the election after an excess non-concessional contributions determination, pension commencement or transfer balance account events, Division 296 valuation or earnings disputes, special contribution types, and personal financial advice.

## Required inputs

Ask for anything missing that changes the answer. Do not assume silently.

1. **Income year** (`2025-26` or `2026-27`). Contributions count in the year the fund receives them. If unclear, ask.
2. **Total super balance at the prior 30 June** (all funds; ATO online services shows it). Needed for carry forward, the non-concessional cap, co-contribution and spouse offset.
3. Concessional: employer (including SG), salary sacrifice, personal amounts to be claimed, whether a notice of intent was lodged and acknowledged, and either the unapplied unused cap amounts by year (ATO online services, Super > Information > Carry-forward concessional contributions) or each earlier year's concessional contributions.
4. Non-concessional: age on 1 July, any bring-forward period triggered in the two previous years (year, length, amount used), and the planned contribution.
5. Division 293: taxable income, reportable fringe benefits, total net investment loss, concessional contributions.
6. Division 296: TSB at 30 June of the year (and the opening TSB from 2027-28), and each fund's reported Division 296 relevant earnings. Balances change is NOT earnings.
7. Co-contribution / LISTO: income components, employment or business income, age, visa status. Spouse offset: spouse income components and spouse TSB.
8. Whether any interest is a defined benefit interest or the member is in an SMSF.

## Procedure

1. Confirm the income year and collect inputs. If the member has a defined benefit interest, pass `has_defined_benefit_interest: true` (the tool refuses with AU-SUPER-001).
2. Call the matching tool with `income_year` and `inputs`, for example:
   - `concessional_cap_position`: `{"employer_contributions": <amt>, "salary_sacrifice": <amt>, "personal_deductible": <amt>, "noi_acknowledged": true, "tsb_prior_30_june": <amt>, "unapplied_unused": [{"income_year": "2022-23", "amount": <amt>}], "taxable_income_excluding_excess": <amt>}`. Use `prior_years` (list of `income_year`, `concessional_contributions`, optional `tsb_prior_30_june`) instead of `unapplied_unused` when only contribution history is known; give years back to 2018-19 where possible.
   - `bring_forward_nonconcessional`: `{"age_at_1_july": <n>, "tsb_prior_30_june": <amt>, "prior_trigger": {"trigger_year": "2025-26", "period_years": 3, "ncc_since_trigger": <amt>}, "planned_ncc": <amt>}`.
   - `div293_tax`: `{"taxable_income": <amt>, "reportable_fringe_benefits": <amt>, "net_investment_loss": <amt>, "concessional_contributions": <amt>, "excess_concessional_contributions": <amt>}`.
   - `div296_tax`: `{"tsb_end_of_year": <amt>, "tsb_start_of_year": <amt>, "interests": [{"fund": "<name>", "relevant_earnings": <amt>, "excluded": false}]}` or `total_super_earnings`.
   - `co_contribution`, `low_income_super_tax_offset`, `spouse_offset`, `downsizer_contribution`: see field descriptions in the tool schema.
3. When a concessional excess is unreleased, run `bring_forward_nonconcessional` with the excess added to `planned_ncc`: it also counts as non-concessional.
4. Read the envelope:
   - `exit_code` 0: present the result. Surface `warnings`, and any code in `escalations` with its message from the refusal table.
   - `exit_code` 3 with `refusal`: quote the code and message verbatim, stop that part, offer what can still be done.
   - `exit_code` 4 with AU-GEN-001: a figure is not verified for that year; quote the message; do not substitute another year's figure as the answer. AU-GEN-003 (also exit 4): the figure has no published value for that year, so no draft is possible; quote the message and stop that part.
   - `exit_code` 2: fix the input and call again.
5. Quote amounts as returned. Never recompute.

## Judgement rules

- **Concessional contributions** are contributions included in the fund's assessable income: employer contributions (SG and salary sacrifice) and personal contributions for which a deduction is allowed (ITAA 1997 s291-25). All funds are added together.
- **Notice of intent** (s290-170): given in the approved form and acknowledged before the earlier of lodging the return for the contribution year and the end of the next income year, and while the fund still holds the contribution. If the member has already rolled over or withdrawn the whole balance (or started a pension from it), a notice given now is invalid (s290-170(2)(c)) and no deduction is available; the contribution stays non-concessional. After a partial rollover only part of the contribution can be covered. The notice can only be reduced, never withdrawn (s290-180). Without it the amount is non-concessional.
- **Personal deductions and age**: from age 67 to 75 a deduction needs the work test or the one-year work test exemption; no deduction for contributions made more than 28 days after the end of the month of turning 75 (s290-165).
- **Carry forward** (s291-20(3)-(7)): unused cap arises from 2018-19 on, lasts five years, is used only when contributions exceed the general cap, and only if TSB at the prior 30 June is below the carry-forward limit. Earliest year first. Unused amounts still accrue in years when the TSB test fails.
- **Excess concessional contributions** (s291-15): included in assessable income and taxed at marginal rates with a non-refundable offset; the member may release up to the release fraction of the excess; unreleased excess also counts towards the non-concessional cap (s292-90). No excess concessional contributions charge from 2021-22.
- **Room left this year**: when bring forward is available, the member can contribute up to the maximum first-year cap in total without excess; report `further_room_this_year_without_excess`, not just the annual cap.
- **Non-concessional cap** (s292-85): a multiple of the concessional cap; nil if TSB at the prior 30 June is at or above the general transfer balance cap. Bring forward needs age under 75 at any time in the first year and cap space (transfer balance cap less TSB) above the annual cap; the period is two years if the space is not more than twice the annual cap, otherwise three. Inside a period the cap stays at the trigger-year amount (not indexed) less amounts already contributed, and is nil in any later year of the period when TSB at the prior 30 June reaches the transfer balance cap.
- **Division 293** (ss293-20 to 293-30): income for surcharge purposes without reportable super contributions, plus low tax contributions (concessional contributions less excess). Tax on the lesser of low tax contributions and the amount over the threshold. Salary sacrifice and negative gearing do not avoid it.
- **Division 296** (Div 296 inserted by Act No. 8 of 2026; rates in the Imposition Act No. 9 of 2026 s5): applies from 2026-27. Earnings are the relevant earnings each fund calculates from its realised taxable earnings and reports; they are not the change in balance. For 2026-27 only the TSB at 30 June 2027 is tested; from 2027-28 the greater of opening and closing TSB. Proportions above the large and very large balance thresholds are rounded to two decimal places. The lower rate applies to taxable super earnings, the additional rate to the very large balance component. Nil for a member who dies in 2026-27, a child recipient of an income stream, or where a structured settlement contribution was made. LRBA amounts are excluded from the Division 296 TSB. Division 296 tax is not deductible.
- **Co-contribution** (Co-contribution Act ss6-11): personal non-concessional contributions, total income below the higher threshold, the ten per cent eligible income test (use the words, not a symbol), under 71 at year end, no temporary visa, TSB below the transfer balance cap, NCC cap not exceeded, return lodged. Minimum payment applies.
- **LISTO** (s12C, s12E): adjusted taxable income not above the LISTO limit, eligible income test, no temporary visa. The increased limit and maximum legislated in Act No. 8 of 2026 Sch 4 start 1 Jul 2027: do not apply them to 2025-26 or 2026-27.
- **Spouse offset** (ss290-230, 290-235): married or de facto, both resident, not living apart permanently, spouse income below the cut-out, spouse TSB below the transfer balance cap and spouse within their NCC cap. The offset is on the contributing spouse's return.
- **Downsizer** (s292-102): age at or above the minimum, 10-year ownership, main residence exemption at least in part, within the period after settlement set by `super.downsizer_contribution_days` (days), election form to the fund. Not counted towards caps and not blocked by TSB, but it raises TSB afterwards.
- **Transfer balance cap** (awareness): the general transfer balance cap limits how much can move into retirement phase pensions and sets the nil-cap test for non-concessional contributions. Personal transfer balance caps and pension starts are escalated (AU-SUPER-004).
- **First home super saver** (awareness): voluntary contributions can later be released for a first home; limits and release tax are for the individual-tax skill (release is AU-IND-001).

## Escalation

| Trigger | Code |
|---|---|
| Defined benefit interest (caps, Div 293, Div 296) | AU-SUPER-001 |
| SMSF administration, fund-level Division 296 earnings, SMSF CGT cost base choices | AU-SUPER-002 |
| Choosing the release or tax option after an excess non-concessional contributions determination | AU-SUPER-003 |
| Starting or changing a retirement phase pension, transfer balance account events | AU-SUPER-004 |
| Division 296 earnings estimated from balances, or a valuation or earnings dispute | AU-SUPER-005 |
| Foreign super transfers, personal injury, CGT cap, FHSS or COVID re-contributions, family law splits | AU-SUPER-006 |
| "Should I", "how much should I", which fund or product (personal advice) | AU-SUPER-007 |
| Required history or balance missing or inconsistent | AU-SUPER-008 |
| A needed figure for the year is not verified | AU-GEN-001 |
| A needed figure has no published value for the year (no draft possible) | AU-GEN-003 |
| Asked to lodge a notice, election or return | AU-GEN-002 |

Surface the code and its message exactly as returned or as listed in `data/refusals/super-contributions.yaml`, then stop the affected work. For AU-SUPER-007, still explain how the rules apply to the facts.

## Output

End every answer with this working paper (CONVENTIONS section 8):

1. **Result** for the stated income year: the tool outputs that answer the question (for example cap, contributions, carry forward applied by year, excess and its treatment; bring-forward status and cap; Div 293 or Div 296 components and tax; co-contribution, LISTO, spouse offset or downsizer limit).
2. **Figures used**: key, value, status, source URL for each entry in `figures_used`.
3. **Assumptions**: the tool's `assumptions` plus any you made.
4. **Risk flags**: relevant entries from `data/risk_flags/super-contributions.yaml` (for example SUPER-NOI-TIMING, SUPER-CARRY-FORWARD-TSB, SUPER-BRING-FORWARD-INADVERTENT, SUPER-DIV296-FUND-EARNINGS), or "none".
5. **Refusals or escalations**: codes and messages, or "none". Include the tool's `warnings`.
6. "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use." Copy this sentence verbatim as the last line of the answer; do not paraphrase it.

References: `references/sources.md` (primary sources), `references/rules.md` (calculation order and edge cases).
