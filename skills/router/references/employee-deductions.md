# Employee deduction intake and substantiation

Use for wage earners before accepting any deduction into `assemble_taxable_income`. Ask only about facts not supplied, in one batch. Record income year, employer/role, each claim's source, eligibility decision, amount, method, private-use share and evidence status. A receipt alone does not establish deductibility (ITAA 1997 s 8-1; Div 900). The bounded 2025–26 EOFY pack accepts only independently substantiated supplied deductions; uncertain or raw claims remain incomplete for the registered agent.

## Common questions and evidence

| Ask | Evidence / decision to retain |
|---|---|
| Did you incur and pay the expense, and were you reimbursed or provided the item? How does it relate to your current employment income? | Invoice/receipt and payment; employment connection; exclude reimbursed/private amounts; record any allowances separately rather than treating them as deductions |
| Work travel or car use? Normal commuting, multiple workplaces, overnight travel, employer-paid costs? | Dates, purpose, route/distance, diary/logbook as required, ownership/lease facts, actual costs and work/private split; distinguish normal commuting and private travel |
| Working from home? Which method, actual hours, running costs, shared household use and equipment? | Contemporaneous hours, required evidence for covered costs, receipts and asset/work-use records; no simultaneous claim for expenses already covered by a fixed rate |
| Tools, equipment, phone/internet or other assets? First-use date, cost, work-use share, previous claims/pool or sale? | Receipts, usage records and prior depreciation schedule; determine immediate deduction versus decline in value and balancing adjustments; no duplicate asset or running-cost claims |
| Protective/occupation-specific clothing, compulsory uniforms or laundry? | Employment requirement, eligible clothing category, receipts/claim records; ordinary clothing remains private; use the chosen year's substantiation rules |
| Training/self-education? Does it maintain skills in the current role or start a new occupation? | Course outline, connection to current duties/income, fees and expense records, reimbursement and private components; escalate uncertain connection |
| Union/professional dues, professional subscriptions, insurance premiums or COVID tests? | Membership/policy/test purpose, eligible premium component and payment; distinguish s 25-130 reducing deductions from excluded insurance/association amounts in future-year handoffs |
| Gifts, tax-agent/tax-affairs fees or personal super contributions? | Eligible recipient/receipt, fee period/purpose; personal super fund receipt and acknowledged notice through `super-contributions`; keep these separate from work-cost reductions |
| Has any cost already been included in rental/business, a rate-method claim, salary packaging, supplied net income or a prior working paper? | Claim-by-claim duplicate check and reconciliation; resolve conflicting totals at source before assembly |

## Routing and evidence handoff

- `individual-tax` owns the employee standard-deduction handoff from 2026–27; never apply it in 2025–26. Confirm qualifying labour income and classified reducing deductions, insurance/association exclusions and whether supplied taxable income already contains the top-up. Refer to ITAA 1997 s 25-130 and that skill's procedure.
- Employee car/WFH calculations use the applicable tools in `sole-trader-business` only after loading that skill and checking the chosen method/year. This does not classify the employee as a business or justify applying business-only PSI, loss or concession rules. Missing year figures and doubtful deductibility stop the affected claim.
- Other ordinary employee claims enter assembly as independently substantiated supplied `work_related_deduction` components with source/year/label; eligibility and evidence gaps go to the agent. Gifts, tax affairs and personal super use distinct deduction kinds.
- An evidence threshold or allowance does not confer automatic entitlement. Retain the method-specific records for the applicable statutory period, including longer retention where asset, dispute or amended-assessment rules require it; follow the primary recordkeeping guidance rather than inventing a universal retention date.

## Primary sources

- ITAA 1997 s 8-1; s 25-130 from 2026–27 (volume 1): https://www.legislation.gov.au/C2004A05138/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_1/document_1.html
- ITAA 1997 Div 900 (volume 10 of the 1 July 2026 compilation); apply the income-year-specific substantiation law, including the changes commencing in 2026–27 rather than importing those into 2025–26: https://www.legislation.gov.au/C2004A05138/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_10/document_10.html
- ATO deductions you can claim: https://www.ato.gov.au/individuals-and-families/income-deductions-offsets-and-records/deductions-you-can-claim
- ATO records you need to keep: https://www.ato.gov.au/individuals-and-families/income-deductions-offsets-and-records/records-you-need-to-keep
- Fixed-rate method and included expenses: https://www.ato.gov.au/individuals-and-families/income-deductions-offsets-and-records/deductions-you-can-claim/work-related-deductions/working-from-home-expenses/fixed-rate-method
