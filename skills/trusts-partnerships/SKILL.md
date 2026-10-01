---
name: trusts-partnerships
description: 'Works out how Australian trust and partnership income is taxed for 2025-26 or 2026-27 - beneficiaries'' shares of trust net income (Bamford proportionate approach, s97), streaming capital gains and franked dividends, trustee tax under s98 and s99A on undistributed income, tax on distributions to children (Division 6AA minors'' unearned income), and partners'' shares of partnership profit or loss including partner salaries. Use when someone asks "how do I split the family trust income", "distribute to my kids", "trust distribution to a bucket company", "didn''t do the trustee resolution by 30 June", "stream the capital gain", "is section 100A a problem", "what does Bendel mean for UPEs", "partner salary deductible?", or "partnership loss split". Also use for trust deed questions, trust vesting, trust losses and family trust elections, foreign trusts, unit trust capital distributions (CGT event E4) and s100A risk reviews: the skill decides what is in scope and escalates to a registered tax agent or lawyer.'
---

# Trusts and partnerships (Australia)

Works out who is taxed on a trust's or partnership's net income, and how much, through three tools: `trust_distribution_shares`, `div6aa_minor_tax` and `partnership_shares`. Never do the arithmetic yourself and never quote a rate or threshold from memory; every figure comes from the tool's `figures_used`.

## Scope

In scope:
- Partnerships (ITAA 1936 Div 5): net income or partnership loss (s90), each partner's interest (s92), partner salaries and interest on capital as profit appropriations (TR 2005/7), the partnership return (an information return; the partnership pays no income tax).
- Resident trusts (ITAA 1936 Div 6): net income (s95), present entitlement and the proportionate approach (s97, FCT v Bamford [2010] HCA 10), trustee assessments under s98 (beneficiaries under a legal disability, including minors, and non-residents) and s99A (income nobody is presently entitled to), Div 6E and streaming of capital gains (ITAA 1997 Subdiv 115-C) and franked distributions (Subdiv 207-B).
- Minors (Div 6AA): tax on a resident minor's eligible (unearned) income, excepted persons and excepted income.
- Integrity awareness: s100A (TR 2022/4, PCG 2022/2 zones), Commissioner of Taxation v Bendel [2026] HCA 18 on corporate beneficiary UPEs, Subdiv EA, Part IVA, family trust elections and family trust distribution tax, trust losses, TFN reporting.

Out of scope (escalate, see Escalation): deciding whether s100A applies, trust deed interpretation, vesting and resettlements, trust loss tests and family trust elections, foreign trusts and non-resident beneficiaries' tax, unit trust capital payments (CGT event E4), MITs/AMITs and public trading trusts, deceased and bankrupt estates, non-resident minors and minors with shares from several trusts, corporate limited partnerships and partner changes during the year.

The individual, company or other beneficiary's own tax on their share belongs to the individual-tax or company skills. This skill stops at the share (and, for minors, the Div 6AA tax).

## Required inputs

Ask for anything missing that changes the answer. Do not assume silently.

1. **Income year** (`2025-26` or `2026-27`). If unclear, ask.
2. **Entity**: trust (discretionary, fixed, unit, hybrid, deceased estate, foreign?) or partnership (carrying on business, or co-owners receiving income jointly?).
3. For a trust:
   - Net income under s95 (tax figure) and trust income as the deed defines it (accounting figure). If the user has only one number, ask for the other; if they are equal say so as an assumption.
   - Net capital gain in net income, the gain before discount, whether the trust applied the discount, and whether the deed treats capital gains as income.
   - Franked distributions, franking credits, and any expenses directly relevant to them.
   - Each beneficiary: name, type (adult, minor under 18 on 30 June, company, trust, non-resident, other legal disability), dollar amount of trust income they are presently entitled to, and any amount of a capital gain or franked distribution they are specifically entitled to.
   - Whether the resolution was made by 30 June (and streaming recorded in time), and whether a family trust election exists.
4. For a minor: unearned income net of its deductions, excepted income net of its deductions, whether an excepted person, residency.
5. For a partnership: net income (or assessable income and deductions), any partner salaries or interest on capital (and whether they were expensed), profit-sharing and loss-sharing ratios, when the agreement was made.

## Procedure

1. Confirm the income year and the entity type. If the question is only about something in the Escalation table, surface that code and stop.
2. **Trusts.** Call `trust_distribution_shares` with `income_year` and `inputs`, for example
   `inputs: {"net_income": <n>, "trust_income": <t>, "resolution_by_30_june": true, "beneficiaries": [{"name": "A", "kind": "resident_individual", "present_entitlement": <amount>}]}`.
   Other fields: `net_capital_gain`, `capital_gain`, `cgt_discount_applied`, `capital_gains_in_trust_income`, `franked_distributions`, `franking_credits`, `franked_distribution_expenses`, `trust_kind`; per beneficiary `specific_capital_gain`, `specific_franked_distribution`, `outside_family_group`. A beneficiary's `present_entitlement` includes any specific entitlement that forms part of trust income.
   If the user gives percentages ("split 50/50"), convert them to dollar entitlements of trust income before calling.
3. **Minors.** For each resident minor beneficiary (or a child with dividends, interest or rent), call `div6aa_minor_tax` with `unearned_income`, `excepted_income`, `excepted_person`, and `trustee_assessed: true` when the share comes through a trust. Report the Div 6AA tax separately from the ordinary tax on excepted income.
4. **Partnerships.** Call `partnership_shares` with `net_income` (or `assessable_income` and `deductions`), `partner_appropriations_deducted` if salaries were expensed, and `partners` (`profit_share`, `loss_share`, `salary`, `interest_on_capital`).
5. Read the envelope:
   - `exit_code` 0: present the result (Output below). Read `warnings` and `risk_flags` and carry them into the answer.
   - `exit_code` 3 with `refusal`: quote the code and message verbatim, stop that part, offer what can still be done.
   - `exit_code` 4 with AU-GEN-001: a figure is not verified; quote the message. AU-GEN-003 (also exit 4): the figure has no published value for that year, so no draft is possible; quote the message and stop that part.
   - `exit_code` 2: fix the input (for example entitlements larger than trust income) and call again.
6. Quote the tool's numbers as returned. Never re-derive them.

## Judgement rules

- **Proportionate approach.** A beneficiary is taxed on the same proportion of net income as their share of trust income (Bamford), not on the cash they receive. If trust income is lower than net income, each beneficiary is taxed on more than they get; if higher, less. Any proportion nobody is entitled to goes to the trustee under s99A.
- **Resolutions and streaming.** Present entitlement must exist by 30 June (or the earlier date the deed sets); a resolution after that date does not change who is presently entitled for that year. Franked distributions are streamed only if recorded by 30 June (s207-58); capital gains if recorded within 2 months after year end (s115-228). The deed must permit streaming. Whether a resolution is valid or the deed's income definition applies is a deed question (AU-TRUST-002). Never backdate a resolution or minute: a document dated before it was signed is a false record. If no valid entitlement existed at 30 June, the deed's default beneficiary clause applies or the trustee is assessed under s99A.
- **s99A.** Applies to net income nobody is presently entitled to, and to amounts caught by s100A. The rate is `trusts.s99a_rate` plus the Medicare levy (`medicare.levy_rate`). The Commissioner's discretion for deceased estates and similar cases is out of scope (AU-TRUST-007).
- **Trust with a net loss (for example from rental property).** Do not call `trust_distribution_shares` on a negative net income and do not build a working paper: no beneficiary or trustee is assessed. Give one line of orientation (a trust cannot distribute a loss), quote AU-TRUST-004 (and AU-RENT-001 when the loss comes from a rental, which the rental-property skill leaves to a registered tax agent), and escalate.
- **Trust losses.** A trust cannot distribute a tax loss; whether a carried-forward loss can later be used depends on the trust loss tests (family trust election, the stake test, pattern of distributions, income injection). Do not confirm how or when a loss will be used: escalate (AU-TRUST-004).
- **Minors.** A beneficiary under 18 on 30 June is under a legal disability, so the trustee is assessed under s98 on their share, and the minor also includes it with a credit (s100). Div 6AA applies unless the minor is an excepted person (full-time work, disability, double orphan and similar, s102AC) or the income is excepted (work or own business income, inheritance or compensation investments, deceased estate trust income, s102AE and s102AG). Above `trusts.minor_eti_threshold` of eligible income the whole of it is taxed at `trusts.minor_eti_rate`, with a phase-in cap up to the phase-out limit the tool reports. The low income tax offset cannot reduce tax on eligible income (ITAA 1997 s61-115). The tax-free threshold is not available against it.
- **s100A (TR 2022/4, PCG 2022/2).** Flag it whenever an entitlement is paid to, lent to, gifted to or used by someone other than the beneficiary, returned to the trust, set off against units, given to a loss beneficiary outside the family, or much smaller than the share of net income. The final PCG 2022/2 has white (arrangements in years ended before 1 Jul 2014), green (low risk scenarios) and red (high risk) zones; the draft's blue zone was dropped. Name the likely zone and why; never conclude that s100A does or does not apply (AU-TRUST-001). The ordinary family or commercial dealing exception is a question of fact.
- **Corporate beneficiaries after Bendel.** Commissioner of Taxation v Bendel [2026] HCA 18 (10 Jun 2026): a company's unpaid present entitlement left uncalled is not a loan under s109D(3), so it is not a Div 7A loan. The ATO decision impact statement (26 Jun 2026) says it will not treat a UPE as a Div 7A loan where the company took no action, whether or not on a sub-trust, and that TD 2022/11 will be withdrawn. Still live: Subdiv EA (trust amounts used by the company's shareholders or associates), s100A, Part IVA, and any step that converts the UPE into a real loan (complying loan agreements are loans). Anything beyond this is AU-TRUST-011.
- **Family trusts.** A family trust election limits distributions to the family group; distributions outside it attract family trust distribution tax. Trust losses stay in the trust and depend on the Sch 2F tests. Both are AU-TRUST-004. Trustees of closely held trusts report beneficiaries' TFNs.
- **Partnerships.** Partner salaries and interest on partners' capital are not deductible; they are profit appropriations allocated before the residual is shared (TR 2005/7). They cannot create or increase a loss; any excess drawn is an advance of future profits, assessable in the year profits cover it. Changes to shares must be agreed before year end (FCT v Galland). Co-owners of a rental property are partners only for tax; income and losses follow legal title (TR 93/32) and they cannot pay salaries.
- **Announced, not law.** The minimum tax on discretionary trusts announced in the 2026-27 Budget (from 1 Jul 2028; exposure draft 3 Sep 2026) is not law; do not apply it to 2025-26 or 2026-27. The Tax Reform No. 1 Act capital gains changes start 1 Jul 2027 and do not affect these years' trust gains.

- **Hard limits (apply even when the user asks for "yes or no" or "exactly how to split it").** Never answer yes or no on whether s100A or Subdiv EA applies to an arrangement: say it is fact-dependent, give the PCG 2022/2 zone indicators, and escalate (AU-TRUST-001 or AU-TRUST-011). Never draft trustee resolution wording and never recommend a final distribution split as advice to adopt: you may compute clearly labelled illustrative splits with the tools, then escalate the resolution and the choice of split to a registered tax agent (AU-TRUST-002). A company beneficiary gets no CGT discount on a streamed gain.
- **Minors.** A distribution to a beneficiary under 18 is taxed under Div 6AA unless it is excepted income or the minor is an excepted person. Use `div6aa_minor_tax`, say that the trustee is usually assessed under s98 on the minor's share, and list the excepted-income checks that could change the answer.

## Escalation

| Trigger | Code |
|---|---|
| Decide whether s100A applies, or advise on a red-zone or unclassified arrangement | AU-TRUST-001 |
| Interpreting a trust deed or partnership agreement (income definition, valid resolution, power to stream, default beneficiaries) | AU-TRUST-002 |
| Vesting, variation, resettlement or winding up of a trust | AU-TRUST-003 |
| Trust loss tests, family trust or interposed entity elections, family trust distribution tax | AU-TRUST-004 |
| Foreign trusts, s99B, non-resident beneficiaries' tax | AU-TRUST-005 |
| Unit trust capital payments (CGT event E4), MITs, AMITs, public trading trusts | AU-TRUST-006 |
| Deceased or bankrupt estates, s99, s98 tax at individual or company rates | AU-TRUST-007 |
| Net income below capital gains plus franked distributions, mixed-character gains | AU-TRUST-008 |
| Non-resident minors, several trusts, averaging, Commissioner-opinion excepted income | AU-TRUST-009 |
| Corporate limited partnerships, partner changes, assignments, PCG 2021/4 | AU-TRUST-010 |
| Part IVA, Div 7A or Subdiv EA advice beyond the Bendel position | AU-TRUST-011 |
| A needed figure for the year is not verified | AU-GEN-001 |
| A needed figure has no published value for the year (no draft possible) | AU-GEN-003 |
| Asked to lodge or pay | AU-GEN-002 |

Surface the code and its message exactly as the tool returns it (or as in `data/refusals/trusts-partnerships.yaml`), then stop the affected work and continue with the rest.

## Output

End every answer with this working paper (CONVENTIONS section 8):

1. **Result** for the stated income year: for trusts, net income, trust income, each beneficiary's percentage and share (ordinary, capital gain and grossed-up gain, franked distribution, franking credit, total) and assessing section, and the trustee's s99A amount and tax; for minors, eligible taxable income, Div 6AA tax and basis, other tax, offset, Medicare levy, total; for partnerships, net income or loss and each partner's share and any drawings in advance of profits.
2. **Figures used**: key, value, status, source URL for each entry in `figures_used`.
3. **Assumptions**: the tool's `assumptions` plus your own (for example that net income equals trust income).
4. **Risk flags**: ids from the tool's `risk_flags` and `data/risk_flags/trusts-partnerships.yaml`, with one line each, or "none".
5. **Refusals or escalations**: codes and messages, or "none". Include the tool's `warnings`.
6. "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use." Copy this sentence verbatim as the last line of the answer; do not paraphrase it.

References: `references/sources.md` (primary sources), `references/rules.md` (calculation steps and worked checks).
