---
name: cgt
description: 'Works out Australian capital gains tax for individuals, trusts, super funds and companies - capital gain or loss on selling shares, property or other assets, the CGT discount and 12-month rule, cost base, capital losses and carry-forward, the main residence exemption (partial exemption, 6-year rule, renting out a former home, Airbnb in part of the home), foreign resident CGT and withholding (FRCGW), and the 1 July 2027 changes (indexation, minimum tax on capital gains, new dwelling discount, pre-CGT reset). Use when someone asks "how much CGT will I pay", "capital gain on selling my rental", "is my home exempt", "sold my shares", "capital gain on an investment property", "carried forward capital losses", "sell before or after July 2027", or "I am a non-resident selling property". Also use for small business CGT concessions, rollovers, trust capital gains and streaming, earnouts and deceased estates: the skill screens scope and escalates. Bitcoin and other crypto go to the crypto skill.'
---

# Capital gains tax (Australia)

Works out capital gains and losses through the `capital_gain`, `net_capital_gain`, `main_residence_exemption` and `small_business_cgt_screen` tools. Never do the arithmetic yourself and never quote a rate, threshold or percentage from memory: every figure comes from the tool output and its `figures_used`.

## Scope

In scope:
- CGT events A1 (disposal, including crypto swaps and sales for fiat), C1, C2, D1, H2 and I1 (ceasing residency, with the s104-165 choice). Timing is the contract date (ITAA 1997 s104-10(3)), not settlement.
- Cost base (five elements, s110-25) and reduced cost base (s110-55); capital works deductions reduce both; pre-CGT assets (acquired before 20 Sep 1985) disregarded until 30 Jun 2027.
- Discount: individuals and trusts, complying super funds (one-third, `cgt.discount_complying_super_fund`), none for companies; 12-month rule; apportioned discount for foreign and temporary residents after 8 May 2012 (s115-105, s115-115, including the market value choice).
- Frozen indexation for assets acquired before 21 Sep 1999 (choice against the discount; companies index).
- Law from 1 Jul 2027 (Treasury Laws Amendment (Tax Reform No. 1) Act 2026, No. 49): see `references/rules.md`. The tools apply it by the event's contract date.
- Capital losses: current-year then carried-forward losses before the discount; collectable and personal use asset rules (s108-10, s108-20, s118-10).
- Main residence exemption: full, partial (days), part income use by floor area, 6-year absence rule, 6-month changeover, first used to produce income rule, foreign resident exclusion and life events test.
- Foreign residents: taxable Australian property only; FRCGW amount; changes from 1 Oct 2026 (Act No. 86 of 2026 Sch 2).
- Crypto: disposal and swap as A1; personal use asset exemption is narrow. For crypto ledgers, parcel matching, staking and airdrop income and lost crypto use the `crypto` skill, which passes each matched parcel to `capital_gain` and `net_capital_gain`.
- Small business CGT concessions: eligibility screen only.

Out of scope (escalate, see Escalation): applying the small business concessions, rollovers, trust CGT events and streaming, trust or super fund gains from events on or after 1 Jul 2027, earnouts, K6 and other events, DeFi, crypto lending, wrapping and bridging, airdrops in business, deceased estate dwellings, land over 2 hectares, construction, spouses with different homes, indirect real property interests of foreign residents.

## Required inputs

Ask for anything missing that changes the answer. Do not assume silently.

1. **Income year** of the CGT event. Derive it from the **sale contract date**; confirm dates rather than assuming the current year. Pass the event's own income year as `income_year`. The tools read the rates file of the income year of the contract date whatever year is passed (the result shows `rates_year_used`): an event on or after 1 Jul 2027 uses the 2027-28 file, including its resident rates for the minimum tax test, and never the 2026-27 figures. A contract date in an income year with no rates file (2028-29 onwards) refuses AU-GEN-003: quote it and stop; do not reuse another year's figures. A contract date the user gives that is later than today is a planned sale: work it as stated.
2. **Who owns the asset**: individual, trust, complying super fund or company (share of ownership if joint: work each owner separately).
3. **Residency** at the event and any foreign or temporary residency after 8 May 2012 (days or dates).
4. **Dates**: purchase contract date and sale contract date; settlement dates for a home.
5. **Amounts**: proceeds; purchase price; purchase costs (stamp duty, legal); improvements; non-deductible holding costs; selling costs; capital works deductions claimed.
6. **Other gains and losses** in the year and carried-forward net capital losses.
7. For a home: periods lived in, periods rented or used for business (and floor area share), whether another home was treated as the main residence, market value when first rented (if after 20 Aug 1996).
8. For a sale on or after 1 Jul 2027 of an asset held on 30 Jun 2027: market value just before 1 Jul 2027; whether the dwelling is claimed as a new residential dwelling; taxable income for the minimum tax test.

## Procedure

1. Collect inputs. Confirm the sale contract date and the income year.
2. Screen scope. If any out-of-scope item applies, pass it in `special_circumstances` (the tool refuses with the right code) or escalate directly.
3. One asset, one event: call `capital_gain` with `income_year` and `inputs`, for example
   `inputs: {"acquisition_date": "2019-03-01", "event_date": "2026-11-20", "capital_proceeds": <amount>, "first_element": <amount>, "incidental_costs_acquisition": <amount>, "incidental_costs_disposal": <amount>, "asset_type": "shares_or_units"}`.
   Other fields: `entity_type`, `cgt_event`, `ownership_costs`, `capital_improvements`, `title_costs`, `cost_base_items` (dated items: `element`, `amount`, `date_incurred`, `disposal_cost`), `capital_works_deductions`, `residency`, `foreign_or_temporary_days_after_8_may_2012`, `foreign_or_temporary_on_8_may_2012`, `choose_market_value_method_8_may_2012`, `market_value_8_may_2012`, `taxable_australian_property`, `indirect_real_property_interest`, `frcgw_clearance_certificate`, `residential_dwelling`, `new_residential_dwelling`, `choose_indexation_for_new_dwelling`, `method_choice`, `market_value_30_june_2027`, `capital_losses_available`, `i1_choose_to_disregard`, `taxable_income_including_gain`, `receives_minimum_tax_exempt_payment`, `personal_use_crypto_claim`, `special_circumstances`.
4. Several gains or losses in a year, or carried-forward losses: call `capital_gain` for each asset (without losses), then call `net_capital_gain` for the income year of those events (2027-28 or later for events from 1 Jul 2027; categories from after that date are refused, exit 2, in earlier years) and pass each result's `components` (amount, `discount_eligible`, `discount_percentage`, `category`, collectable flag) to `net_capital_gain` with `losses`, `prior_year_net_capital_losses`, `prior_year_collectable_losses` and `quarantined_residential_amount`.
5. A home (or former home): call `main_residence_exemption` with settlement dates, `lived_in_periods`, `income_use_periods`, `choose_absence_rule`, `changing_residence_overlap`, `market_value_at_first_income_use`, `residency_at_event`, `foreign_residency_years_at_event`, `life_events_test_met`. Its `taxable_capital_gain` is the gain before losses and discount; feed it to `net_capital_gain` if there are other gains or losses.
   Set `choose_absence_rule` explicitly, because the tool's own default is true. When the owner has not said they make the s118-145 choice, pass false: the default outcome for a home that was let is the partial exemption under s118-190 (income-producing use, by floor area and days), with the cost base reset under s118-192 where it applies, and a missing market value refuses with AU-CGT-006. Show the absence choice only as a possible election that depends on the facts (no other home treated as the main residence for the period, conditions met), for a registered tax agent to confirm; do not lead with "likely fully exempt" on the strength of it. This applies to a home let short-stay as much as long-term. State the ATO apportionment method in words before any figure: the gain measured from the market value at first income use, multiplied by the floor area share used for income, multiplied by the days used to produce income over the days from first income use to sale. Say how the days used for income were counted. For a short-stay owner there are two readings of that count: nights actually let (ATO "Using your home for rental or business", step 4, "days you used your home to produce assessable income") and days the home was genuinely available to let (s 118-190(2), reasonable having regard to the interest that would have been deductible; PCG 2026/2 paras 13 to 15 count days held to produce income for the income tax side). Neither source chooses. Run the tool for each count if a figure is wanted, label both provisional, and escalate the choice to a registered tax agent instead of asserting one. Label any figure that uses the owner's own value estimate as provisional pending a valuation. Explain in words that letting can reduce the main residence exemption (s118-190: a partial exemption by floor area and time used to produce income, where interest on the money borrowed to buy the home would be deductible), and that s118-192 applies where the home was first used to produce income after 20 August 1996 and would then have been fully exempt. Order the answer: the default partial-exemption outcome first (answer "not by default" to a question asking whether the whole gain stays exempt), then the residency check, then the absence election as a possible alternative that needs the agent's confirmation. Never present the election as the first or most likely outcome.
6. Business asset: call `small_business_cgt_screen`, report the screen, then escalate with its AU-CGT-001 entry. Do not apply any concession.
7. Read the envelope:
   - `exit_code` 0: present the result (Output below). Quote `warnings` and `escalations`.
   - `exit_code` 3 with `refusal`: quote the code and message verbatim, stop that part, offer what can still be done.
   - `exit_code` 0 with `partial: true` and `field_refusals`: show every figure returned (for example `deferred_component`), quote each field refusal code and message verbatim against the field it names, and mark anything that depends on that field "incomplete: depends on <code>".
   - `exit_code` 4 with AU-GEN-001: a figure is not verified; quote the message; do not substitute a remembered figure. AU-GEN-003 (also exit 4): the figure has no published value for that year, so no draft is possible; quote the message and stop that part.
   - `exit_code` 2: fix the input and call again.
8. Quote the tool's numbers as returned, in dollars and cents. Do not re-round or recompute.

## Judgement rules

- The event happens at the contract date; a contract signed on or before 30 Jun 2027 keeps the old discount even if settlement is later (s104-10(3)). A contract in June is reported in that income year.
- Capital losses reduce gains before the discount; apply them to non-discount gains first (s102-5). Net capital losses never reduce other income (s102-10) and carry forward indefinitely.
- Crypto swaps are disposals. Crypto held as an investment is not a personal use asset. Own-wallet transfers are not disposals. Missing records do not justify a nil cost base.
- Owner abroad who lets the property: where the question is the whole picture for a let-out property (rent, tax-free threshold and sale) from someone who has moved overseas and residency rests only on their statement, the lead-with rule in short-stay-accommodation, rental-property and individual-tax applies: open with AU-RES-004 verbatim, and do not call `capital_gain` or `main_residence_exemption` on illustrative figures or give a final tax figure. A sale question with a stated contract date and stated foreign residency (for example the main residence exemption and withholding) is answered from the rules below.
- Foreign residents: only taxable Australian property is taxed (s855-10). A person who is a foreign resident at the sale contract date gets no main residence exemption at all, for any period (s118-110(3)), unless foreign for 6 years or less and a life event applies (terminal illness, death of a spouse or minor child, relationship breakdown). The 6-year absence rule cannot restore it; say so plainly and do not suggest it might. Only becoming an Australian resident again before signing changes that. The discount is apportioned for foreign residency days after 8 May 2012. FRCGW applies at settlement; foreign residents cannot get a clearance certificate (only a variation).
- Six-year rule: only while the former home is rented or used for income; unlimited if vacant; a fresh period each time the owner moves back in; no other home can be the main residence for that time except the 6-month changeover (s118-145, s118-140).
- First used to produce income after 20 Aug 1996, with only a partial exemption: cost base resets to market value at that time and the 12 months run from then (s118-192). Ask for a valuation; never estimate one.
- From 1 Jul 2027 the discount no longer applies to individuals' or trusts' gains accruing after 30 Jun 2027 (except new residential dwellings): state this first. An asset held on 30 Jun 2027 splits into a discounted deferred gain (to market value just before 1 Jul 2027) and an indexed later gain; ask for that market value and do not estimate it (AU-CGT-006). Indexation from 1 Jul 2027 reads its CPI index numbers only from the rates file (`cgt.indexation_cpi_from_2027`), which has no published value yet. For an asset held on 30 Jun 2027 that would be indexed (held at least 12 months), the tool does not refuse the whole event: it returns `deferred_component` (the notional gain from the deemed sale, its discount and the discounted amount) as a figure and refuses only the post-1 Jul 2027 part at field level (`field_refusals`, AU-GEN-003, in draft mode too), with `partial: true` and no net capital gain or minimum tax figure. Present the deferred component as a figure, quoting its amounts as returned. Present the post-1 Jul 2027 part as refused pending CPI: quote the refusal, explain the method (later gain indexed, no discount, minimum tax) and say that part cannot be worked out until the index numbers are published and loaded. Never show a range, upper bound or guess for the refused part, never ask the user for index numbers to type in and never estimate them. Do not pass a partial result to `net_capital_gain` as if it were the whole event, and say the year's net capital gain is incomplete. An asset acquired on or after 1 Jul 2027 has no deferred component, so the whole event refuses AU-GEN-003 (quote it and stop that part). A sale under 12 months needs no index numbers.
- New residential dwelling: the discount is kept only if the dwelling meets requirements in a Ministerial instrument not made as at 29 Sep 2026. Treat the flag as the user's assertion and say so.
- The minimum tax (Div 119) applies to resident individuals on post-1 Jul 2027 non-deferred gains other than new dwelling and affordable housing gains, unless a listed payment (for example age pension, JobSeeker, family tax benefit) was received in the year.
- Small business concessions from the income year including 1 Jul 2027: the active asset reduction alone uses the higher turnover gate (`cgt.active_asset_reduction_turnover_gate_from_2027_28`). Rental assets are generally not active assets.
- Draft rulings TR 2026/D1 (airdrops) and TD 2026/D2 (wrapping) are drafts; label them as the ATO's preliminary view.

## Escalation

| Trigger | Code |
|---|---|
| Applying small business concessions (after the screen) | AU-CGT-001 |
| Any rollover, including relationship breakdown transfers | AU-CGT-002 |
| Trust CGT events, streaming, beneficiary gains, trust or super fund gains from 1 Jul 2027 | AU-CGT-003 |
| Earnouts, K6, other unmodelled events, non-widely held entity interests | AU-CGT-004 |
| DeFi, crypto lending, liquidity pools, wrapping or bridging, airdrops in business, crypto trading business | AU-CGT-005 |
| Market value needed (just before 1 Jul 2027, or first income use) and not provided | AU-CGT-006 |
| Post 1 Jul 2027 combinations not modelled (mixed residency, partial home exemption) | AU-CGT-007 |
| Main residence special rules (deceased estate, over 2 hectares, construction, spouses) | AU-CGT-008 |
| Foreign resident with an indirect real property interest (principal asset test) | AU-CGT-009 |
| A needed figure for the year is not verified | AU-GEN-001 |
| A needed figure has no published value for the year (no draft possible) | AU-GEN-003 |
| Asked to lodge or pay | AU-GEN-002 |

Surface the code and its message exactly as returned, then stop the affected work.

## Output

End every answer with this working paper (CONVENTIONS section 8):

1. **Result** for the stated income year of the event: capital proceeds; cost base (and reduced cost base for a loss); gross capital gain or loss; method (discount, indexation, deemed split at 1 Jul 2027, main residence fraction); discount percentage and amount; losses applied and carried forward; net capital gain; minimum tax capital gain and gap where relevant; FRCGW amount where relevant. For a partial result: the deferred component as a figure, and the post-1 Jul 2027 part shown as refused pending CPI.
2. **Figures used**: key, value, status, source URL for each entry in `figures_used`.
3. **Assumptions**: the tool's `assumptions` plus any you made.
4. **Risk flags**: relevant entries from `data/risk_flags/cgt.yaml` (for example CGT-CONTRACT-DATE, CGT-2027-VALUATION, CGT-MRE-ABSENCE-CHOICE), or "none".
5. **Refusals or escalations**: codes and messages, or "none". Include the tool's `warnings`.
6. "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use." Copy this sentence verbatim as the last line of the answer; do not paraphrase it.

References: `references/rules.md` (calculation rules, 1 July 2027 regime), `references/sources.md` (primary sources).
