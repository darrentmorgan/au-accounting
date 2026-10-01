# Rules and edge cases: payg-instalments-lodgment

## Activity statement labels (ATO instructions)
- Amount method: T7 instalment amount; when varying, T8 estimated tax for the year, T9 varied amount, T4 reason code; 5A the instalment; 5B credit if T9 works out negative.
- Rate method: T1 instalment income for the period, T2 instalment rate; when varying, T3 new varied rate, T4 reason code; T11 = T1 x T2 (or T3), carried to 5A; 5B credit if the varied rate is lower than the earlier rate.
- Annual payers: T5 annual instalment on the instalment notice.
- The ATO worked example enters the whole-dollar amount at T11 and 5A (cents dropped).

## Varying by amount, by quarter (ATO)
Quarter 1: a quarter of the estimated tax. Quarter 2: half, less quarter 1 paid. Quarter 3: three quarters, less earlier instalments, plus credits claimed for quarter 2. Quarter 4: all of it, less earlier instalments, plus credits claimed in quarters 2 and 3. A taxpayer starting mid-year treats the first quarter paid as quarter 1.

## Safe harbour for varying (Subdiv 45-G)
- Rate method (s 45-230): GIC if the varied rate is below the safe harbour share of the benchmark rate.
- Amount method (s 45-232): GIC if the estimated benchmark tax used is below the share of the Commissioner's benchmark tax; GIC is on the instalment shortfall from each due date to the due date of the assessed tax, reduced by later-quarter top-ups (s 45-233).
- Annual payers (s 45-235): same test on the annual instalment.
- The Commissioner notifies the GIC; 14 days to pay; remission where fair and reasonable (s 45-240).
- ATO plain-language warning: if varied instalments are under the safe harbour share of total tax on instalment income, GIC may apply on the difference, and penalties may apply depending on circumstances.

## Entity and cycle notes
- Individuals and trusts enter only if all three thresholds are met; companies and super funds if any of the ATO's three tests is met (the tool states this and asks for confirmation from the notice).
- Instalment income above the monthly limit means monthly lodgment and payment: out of scope (AU-PAYG-001).
- Two-instalment payers: primary production and special professionals paying by amount only.
- Annual option: the notional tax notified must be under the annual limit and the first quarter not yet lodged; the choice is confirmed by the 28th of the month after the first quarter.

## Registered agent lodgment program (ATO published, re-check each year)
Read 29 Sep 2026; agent dates are set by the ATO annually, so treat these as dated statements and re-verify.
- Activity statements: quarter 4 2025-26 lodged and paid by 25 August 2026; quarter 1 2026-27 by 25 November 2026; quarter 2 2026-27 has no extension (28 February 2027, a Sunday, so 1 March 2027); quarter 3 by 26 May 2027; quarter 4 by 25 August 2027 (to be confirmed with the 2027-28 program). Instalment notices (forms R, S, T) get no extension.
- Individuals and trusts, 2026 returns: 31 October 2026 if prior-year returns were outstanding at 30 June 2026; 31 March 2027 if the latest return showed a large tax liability; 15 May 2027 for the rest, with a concessional 5 June date for eligible clients; large and medium trusts earlier.
- Companies and super funds, 2026 returns: 31 October 2026 (prior returns outstanding), 31 January 2027 (large and medium, taxable last year), 31 March 2027 (higher total income entities), 15 May 2027 (remaining), 5 June 2027 concession.
- To be eligible the agent must be engaged before 31 October; a taxpayer with earlier returns outstanding loses the program.

## Penalty edge cases
- Periods of `penalties_interest.ftl_period_days` days (or part) count from the day after the due date: one day late is one period, a day past the first full period is two, and so on; the base cap is reached on the first day of the fifth period.
- Multiplier tests use the size when the document was due (assessable income or GST turnover, or withholder size).
- A late lodgment does not stop GIC on an unpaid amount; GIC runs from the beginning of the due day to the last day the amount remains unpaid at the end of the day.
- Remission: the ATO expects the document to be lodged first; holidays, workload and short illnesses are unlikely to be accepted; severe illness, disaster, missing third-party information and family violence are examples the ATO would likely accept.

## Shortfall penalty awareness (Div 284)
Base penalty amount is a share of the shortfall set by behaviour: failure to take reasonable care, recklessness, intentional disregard (figures `penalties_interest.shortfall_penalty_*`). Voluntary disclosure can reduce it, and agent safe harbour can apply. Do not compute or predict; escalate under AU-PAYG-005.

## Interest edge cases
- GIC and SIC daily rates are published per quarter and change; the tool refuses a day in an unpublished quarter (AU-PAYG-002) rather than assuming the last rate.
- SIC applies on amended assessments; GIC on late payment, underestimated instalments and late returns.
- Neither is deductible when incurred from 1 July 2025.
