---
name: residency-cross-border
description: 'Decides Australian tax residency for individuals and handles cross-border income - the four residency tests, part-year residency when arriving or leaving, temporary residents, working holiday maker status, foreign income of residents, the foreign income tax offset and its limit, exempt foreign employment income (s 23AG), departing-resident CGT event I1 awareness, and the Australia-Indonesia tax treaty (120-day rules, tie-breaker, withholding limits). Use when someone asks "am I an Australian tax resident", "do I stop being a resident if I move to Bali", "183 days", "tax on my overseas income", "foreign tax credit", "FITO", "double tax agreement", "Indonesia tax treaty", "expat", "leaving Australia", "temporary resident". Also use for controlled foreign companies, foreign trusts, foreign super transfers, an Indonesian PT owned by an Australian, or any treaty other than Indonesia: the skill decides scope and escalates.'
---

# Residency and cross-border (Australia)

Works out the individual residency indicators, the foreign income tax offset (FITO) and the Australia-Indonesia treaty outcomes through the `residency_indicators`, `foreign_income_tax_offset`, `indonesia_dta_check` and `cross_border_scope_check` tools. Never do the arithmetic yourself and never quote a threshold or treaty rate from memory; every figure comes from the tool's `figures_used`.

## Scope

In scope:
- Individual residency under ITAA 1936 s 6(1) as explained in TR 2023/1: resides (ordinary concepts), domicile, 183-day, Commonwealth superannuation. Indicators only. It is a question of fact and this skill never issues a determination.
- Part-year residency when arriving or leaving; how the months feed `individual_income_tax`.
- Temporary residents (ITAA 1997 Subdiv 768-R): foreign-source income and most foreign gains are not assessable.
- Working holiday maker residency boundary. Rates and tax computation are done by the individual-tax skill.
- Residents are taxed on worldwide income (ITAA 1997 s 6-5(2)); foreign income tax offset (ITAA 1997 Div 770) with the s 770-75 offset limit.
- Exempt foreign employment income (ITAA 1936 s 23AG), as currently worded.
- Departing residents: awareness of CGT event I1 and the s 104-165 choice (detail belongs to the cgt skill), foreign resident capital gains withholding (FRCGW), departing Australia superannuation payments (detail belongs to the super-contributions skill).
- Australia-Indonesia double tax agreement, structured articles only: 4(3), 10, 11, 12, 14, 15.
- Indonesia treaty questions beyond a single structured article check (rolling 12-month day counts, permanent establishment, Bali rent or property sales, Indonesian tax as an offset, withholding on payments to an Indonesian resident, rupiah conversion): load the `au-indonesia-cross-border` skill, which owns the treaty article analysis and reuses `indonesia_dta_check` and `foreign_income_tax_offset`.

Out of scope (escalate; call `cross_border_scope_check` to get the code and message): controlled foreign companies, foreign investment funds, foreign trusts (including s 99B), an Australian resident controlling an offshore company such as an Indonesian PT (AU-RES-002); foreign super or pension transfers and balances (AU-RES-003); any treaty other than Indonesia, and dual residents needing a tie-breaker determination on conflicting facts (AU-RES-001); conflicting or missing residency facts (AU-RES-004); complex FITO cases (AU-RES-005). Indonesian domestic tax (residency, VAT, PT PMA rules, withholding under domestic law) is not verified here: say so and do not state it.

## Required inputs

Ask for what is missing. Do not assume silently.
1. **Income year** (`2025-26` or `2026-27`). Residency is tested for each income year separately.
2. Residency facts: days physically in Australia in the year, previous year's status, where the home, spouse and children, employment and assets are, intention (settle, return, stay overseas indefinitely, visit), domicile, planned length overseas, visa type, Commonwealth super membership.
3. Foreign income: amounts in AUD, foreign tax paid on each amount, taxable income, deductions related to the foreign income.
4. For Indonesia: days in Indonesia in any rolling 12 months (not the income year), whether a fixed base is regularly available, who employs the person and where that employer is resident, homes available in each country.

## Procedure

1. Confirm the income year and the question: residency, foreign income offset, treaty, or departing-resident awareness.
   **Owner abroad**: for a person who owns or lets Australian property, says they have moved overseas or are a foreign resident, rests that only on their statement and asks what tax they pay (rent, tax-free threshold, sale): open with AU-RES-004 verbatim (AU-RES-001 instead where a treaty country such as Singapore is in play; both messages are in `data/refusals/residency.yaml`), before any headline. Give no tax payable, taxable income, total, rate application, Medicare or CGT amount, no worked illustration with made-up figures, and call no calculator on the rent or the sale. Orientation in words only: a foreign resident is generally taxed on Australian-source rent at foreign resident rates with no tax-free threshold and no Medicare levy, a foreign resident at the sale contract date generally cannot use the main residence exemption, and withholding can apply on a sale. Ask for the residency facts (departure date, days in Australia, where the home and family are, visa, intended length of stay) and hand the review to a registered tax agent with cross-border experience. Do not run `residency_indicators` on assumed or invented facts.
2. If the facts mention any out-of-scope item above, call `cross_border_scope_check` with the matching `situations` and quote the returned code and message verbatim. Stop that part of the work. Other parts (for example the residency indicators) can continue.
3. Residency: call `residency_indicators` with the facts you have. Leave unknown fields out rather than guessing.
   - Report each test's status and the ruling paragraphs. Report `overall` and `leaning` in words such as "the indicators lean towards resident" and never as a conclusion.
   - If `overall` is `uncertain_escalate` (conflicting or missing facts), quote the `escalation` code and message verbatim, list `missing_facts`, and stop the residency-dependent work. Do not compute tax on either basis as if residency were settled; you may show both bases clearly labelled as alternatives if the user asks. Then still give the residency-independent facts in step 10.
   - If `overall` is `likely_resident` or `likely_non_resident`, say that residency is a question of fact and still needs confirmation, then continue.
4. Part-year: if the person arrived or left, ask for the month residency starts or ends and pass the months to the individual-tax skill (`resident_months` in `individual_income_tax`). Residency for the first or last part of the year is decided from when behaviour became or stopped being consistent with residing, not from the visa date or the departure date alone.
5. Temporary resident: check the `temporary_resident` result. If a resident who is a temporary resident, foreign-source income (other than employment or services performed while a temporary resident) is not assessable and most foreign gains are disregarded; Australian-source income is fully taxable.
6. Foreign income offset: for a resident with foreign tax paid, call `foreign_income_tax_offset` with `foreign_tax_paid`, `taxable_income`, `foreign_net_income` (foreign income less related deductions) and the Medicare family details. Read the envelope:
   - `exit_code` 0: report the offset, the limit, `foreign_tax_lost` and the warnings. The offset is non-refundable, is applied after other non-refundable offsets, and unused foreign tax is lost.
   - `exit_code` 3 with `AU-RES-005`: quote the message verbatim and stop.
   - `exit_code` 4 (`AU-GEN-001` unverified, or `AU-GEN-003` no published value and no draft possible): quote the message. Do not guess a Medicare threshold for 2026-27 low incomes.
   - `exit_code` 2: fix the input and call again.
   Foreign tax counts only on amounts included in assessable income. Ask whether foreign gains were discounted or absorbed by losses.
7. Exempt foreign employment income (s 23AG): check the current conditions in Judgement rules. Most ordinary overseas jobs do not qualify. If it does qualify, the exempt income still counts for Medicare levy surcharge income and study loan repayment income, and foreign tax paid on it gives no foreign income tax offset (ITAA 1997 s 770-10); `individual_income_tax` has `exempt_foreign_employment_income`.
8. Indonesia treaty: call `indonesia_dta_check` with `article` and the facts. Never use 183 days for Articles 14 and 15. A missing fact gives a null result; ask for it. Treaty limits are ceilings, not the rate Indonesia actually charges.
   For `residence_tie_breaker` the result is an indication only, never "resident of X only": report where the steps point, list the tool's `missing_facts`, and quote its `escalations` (AU-RES-001 and AU-IDN-002, the latter because Indonesian domestic residence is unverified) verbatim rather than writing "none". Load `au-indonesia-cross-border` for the full treaty walk.
9. Departing residents: explain event I1 and the choice at overview level, hand the calculation to the cgt skill, flag FRCGW for the sale of Australian real property by a foreign resident, and flag that a departing person's super is a super-contributions matter.
10. **Residency-independent facts: state them even when the answer stops at AU-RES-001, AU-RES-004, AU-CRYPTO-005 or AU-IDN-002.** Escalating the residency outcome does not excuse leaving out what holds on either outcome. Give each that applies, as facts, with no tax figure:
   - **Indonesia employment (treaty Art 15).** An Australian resident employed by an Australian employer who works in Indonesia is taxable in Indonesia unless all four Art 15(2) conditions hold: presence not over the day limit in any 12-month period, employer not resident in Indonesia, remuneration not borne by an Indonesian permanent establishment or fixed base, and remuneration taxed in Australia. Read the day limit with `get_figure` (`residency.indonesia_dta_days_threshold`) and state the number; never write only "a day limit". A stay of two years working from Bali will not meet it. Any Indonesian tax correctly imposed is relieved in Australia only through the foreign income tax offset (treaty Art 24; ITAA 1997 Div 770). Load `au-indonesia-cross-border` for the walk.
   - **Treaty tie-breaker.** If the facts could make the person resident of both countries (for example an Australian home kept available and a long Bali stay), say both Australia and Indonesia may treat them as resident, and that Indonesian domestic residency is for an Indonesian adviser (not verified here, AU-IDN-002). Then either escalate the tie-breaker (AU-RES-001) or give the Art 4(3) order in full: permanent home available, then habitual abode, then closer personal and economic relations. There is no nationality step and no mutual agreement step, unlike the OECD Model. "Permanent home first" alone is incomplete. Report it as an indication, never a determination.
   - **Crypto.** If the person stays an Australian resident the crypto is unaffected until a disposal; event I1 (ITAA 1997 s 104-160) applies only on ceasing to be resident, at market value on that date, with the s 104-165 choice. Staking rewards are ordinary income when received while resident. No final figure without the departure-date market value (AU-CRYPTO-005).
   - **Australian home let short-stay.** The rent is assessable in Australia whether or not the owner is resident (ITAA 1997 s 6-5(2) and (3)), declared gross before platform fees (TR 2026/1). GST: an ordinary home let to guests is an input taxed supply of residential premises (GSTA 1999 s 40-35), not commercial residential premises unless it is hotel-like (GSTR 2012/6); say so, and load `short-stay-accommodation` for the classification tool rather than deferring GST as "still to be worked". If the owner is or may be a foreign resident, say this is an escalation and why: for a year spent wholly as a non-resident, foreign resident rates apply with no tax-free threshold (ITRA 1986 Sch 7 Pt II); a part-year resident uses the resident rates with a pro-rated tax-free threshold (ITRA 1986 ss 18 and 20); and there is no Medicare levy for foreign-resident days (levy limited to residents by ITAA 1936 s 251S(1)(a); exemption ITAA 1936 ss 251T and 251U(1)(d), part years Medicare Levy Act 1986 s 9; not available if a dependant is not also exempt, s 251U(2)). State that direction in words, give no amount, and leave the rate application to the registered agent once residency is settled.
   - **Main residence.** A foreign resident at the sale contract date generally has no main residence exemption (ITAA 1997 s 118-110(3)). Letting the home out can also reduce the exemption to a partial one (ITAA 1997 s 118-190). Present the absence rule (s 118-145) and the market-value reset when first let (s 118-192) as `cgt` questions for the registered agent, not as available concessions.
   - **Referral.** When residency is escalated, refer it to a registered tax agent with cross-border experience by that name, and Indonesian domestic residency and Indonesian tax to an Indonesian adviser. Say that no single total tax figure is given, and why: residency, departure-date market values, Indonesian domestic tax and the Airbnb facts are unresolved.

## Judgement rules

- Residency tests (ITAA 1936 s 6(1); TR 2023/1 paras 10-16): a person is a resident if any one test is met; all applicable tests must be considered before concluding non-resident. There are no bright-line rules for the first three tests.
- Resides test (paras 17-54): usual and settled presence, not temporary and casual. Factors: presence, intention or purpose, behaviour, family and business or employment ties, assets, social and living arrangements. A person can reside in Australia and another country at once (para 24).
- Absence alone does not end residency (para 25). Working overseas while returning to an established Australian home and family generally keeps a person a resident (para 49).
- Domicile test (paras 55-82): Australian domicile makes a person resident unless the Commissioner is satisfied the permanent place of abode is outside Australia. A person cannot have the permanent place of abode in both places (para 67). Broadly, an intended stay of about two years or more is a substantial period (para 77), a rule of thumb only.
- 183-day test (paras 83-95): more than half the income year present, unless usual place of abode is overseas and there is no intention to take up residence. Fewer days does not mean non-resident. The Board of Taxation bright-line model is not law.
- Commonwealth super test (paras 96-97): only active members of the PSS or CSS and their spouse or child under 16.
- Temporary workers and working holiday makers: TR 2023/1 paras 98-104. A working holiday maker who is a resident, or who relies on a treaty non-discrimination article (Addy), goes to individual-tax's AU-IND-004.
- Foreign income tax offset: ITAA 1997 s 770-70 (amount) and s 770-75 (limit). The limit is the greater of the default limit (`residency.fito_default_offset_limit`) and the extra tax caused by the foreign income (with Medicare levy and surcharge). If the claim is not above the default limit no limit calculation is needed. No refund, no carry-forward.
- Exempt foreign employment income (ITAA 1936 s 23AG, current wording): needs a resident individual, foreign service continuous for at least the minimum days (`residency.s23ag_min_foreign_service_days`), and, under s 23AG(1AA), service directly attributable to a listed activity (aid delivery by a non-government employer, certain funds and prescribed charities, disciplined force deployment, or an activity in the regulations). Amounts exempt in the foreign country only because of a treaty or similar are excluded (s 23AG(2)). Ordinary employment overseas and self-employment do not qualify. Foreign tax paid on income that is exempt under s 23AG gives no foreign income tax offset: the offset is for foreign income tax paid in respect of an amount included in assessable income (ITAA 1997 s 770-10(1); the only non-assessable extension in s 770-10(2) is for income under ITAA 1936 ss 23AI and 23AK), and s 23AG income is exempt income. It is still exempt income with the consequences described in step 7 of the Procedure (it counts for the Medicare levy surcharge and study loan repayment income, and is not simply ignored), so do not tell the user the salary has no effect on other income.
- Departing residents: CGT event I1 applies to assets that are not taxable Australian property when residency stops (ITAA 1997 s 104-160). An individual may instead choose to disregard the gain or loss on all such assets; they then stay taxable Australian property until sold or residency resumes (s 104-165). The choice is all or nothing. Foreign residents lose the main residence exemption in most cases (ITAA 1997 s 118-110); leave detail to the cgt skill.
- Indonesia treaty: Article 4(3) tie-breaker order is permanent home, habitual abode, closer personal and economic relations, with no nationality step. Article 14: independent services taxed in the residence state unless a fixed base is regularly available or presence exceeds the days threshold in any 12 months. Article 15: employment exemption needs presence not above the days threshold, a non-resident employer, no permanent-establishment cost, and tax in the residence state. Articles 10 to 12 cap source-state tax on dividends, interest and royalties (two royalty tiers); read the rates from the tool.
- Australian residents remain taxable on Indonesian income (rent from a Bali villa, for example) with relief through the treaty credit article and Div 770.

## Escalation

| Trigger | Code |
|---|---|
| Dual resident needing a tie-breaker determination with conflicting facts; any treaty other than Indonesia | AU-RES-001 |
| Controlled foreign company, foreign trust, foreign investment fund or hybrid, controlled offshore company | AU-RES-002 |
| Foreign super or pension transfer or balance | AU-RES-003 |
| Residency indicators conflicting or incomplete | AU-RES-004 |
| Foreign income tax offset with deferred losses, foreign loss component, attribution account, JPDA income, foreign tax in a different year, or a refund | AU-RES-005 |
| A needed figure for the year is not verified | AU-GEN-001 |
| A needed figure has no published value for the year (no draft possible) | AU-GEN-003 |
| Asked to lodge or pay | AU-GEN-002 |

Surface the code and its message exactly as returned, then stop the affected work.

- **Foreign income worked papers.** Where a treaty country is involved, name the treaty and the relevant articles (for Indonesia: the employment income article and the relief/elimination of double taxation article), state that relief is the treaty credit article applied as the foreign income tax offset under ITAA 1997 Div 770, that the foreign tax must be a creditable foreign income tax actually paid and correctly imposed under the foreign law and the treaty (not verified here; for Indonesia AU-IDN-002), and flag the AUD conversion (s 960-50: generally the rate at the time the income is derived or the tax paid) and the evidence to ask for (foreign assessment, payment receipts, withholding slips).

## Output

End every answer with this working paper (CONVENTIONS section 8):

1. **Result** for the stated income year: residency indicators by test with paragraph references and the overall indication (never a determination), or the offset and limit, or the treaty outcome.
2. **Figures used**: key, value, status, source URL for each entry in `figures_used`.
3. **Assumptions**: the tool's `assumptions` plus any you made.
4. **Risk flags**: relevant entries from `data/risk_flags/residency.yaml` (for example RES-001 residency assumed to end on departure, RES-003 Indonesia thresholds, RES-004 offset limit), or "none".
5. **Refusals or escalations**: codes and messages, or "none". Include the tool's `warnings`.
6. "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use." Copy this sentence verbatim as the last line of the answer; do not paraphrase it.

References: `references/sources.md` (primary sources), `references/rules.md` (residency factors and part-year), `references/indonesia-dta.md` (treaty articles).
