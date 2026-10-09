# Skill map and handoffs

## Routing table

| Skill | Load when | Produces for the combined paper | Hands to |
|---|---|---|---|
| rates-lookup | A single figure is asked for | Figure, status, source | none |
| residency-cross-border | Any individual with time overseas, foreign income, visa questions, departing or arriving | Residency indicators (never a determination), resident months, FITO and its limit, exempt foreign employment income, Indonesia treaty outcomes | individual-tax (`residency`, `resident_months`, `exempt_foreign_employment_income`); cgt (departing resident event I1) |
| au-indonesia-cross-border | Bali or Indonesian income, the Indonesia tax treaty, days in Indonesia, staff working in Indonesia, Indonesian tax as a foreign income tax offset, withholding on payments to an Indonesian resident, rupiah conversion | Treaty allocation by article, rolling 12-month day counts, service permanent establishment screen, treaty-capped creditable Indonesian tax and offset, Australian withholding for an Indonesian payee, AUD translation from ATO rates; escalations AU-IDN-001 to AU-IDN-006 | individual-tax (foreign income and the offset result, as `residency-cross-border` hands them); cgt (net capital gain of a villa sale) |
| bookkeeping-year-end | Year-end close, bookkeeping, chart of accounts, prepayments, trading stock, financial reporting obligations | Adjusted trial balance and accounting profit, year-end adjustments, reporting obligations | company-div7a, sole-trader-business, trusts-partnerships (accounting profit and trust income) |
| gst-bas | GST registered, near the registration threshold, BAS preparation | BAS labels, net GST, registration outcome, BAS due dates | sole-trader-business, company-div7a, bookkeeping-year-end (GST-exclusive amounts) |
| payroll-sg | Employees, contractors, super guarantee, STP, PAYG withholding | Withholding, SG and Payday Super deadlines, SG charge, worker status | individual-tax (withholding for an employee), bookkeeping-year-end |
| fbt | Cars, loans, parking, entertainment or other benefits to employees or associates | FBT payable, return due date, reportable fringe benefits amount per employee | individual-tax (`reportable_fringe_benefits`), super-contributions (Div 293) |
| state-taxes-sa | Payroll tax, land tax, stamp duty in SA; other states for scoping | SA tax amounts and due dates; AU-SA-001 for other states | bookkeeping-year-end (accruals) |
| company-div7a | A company: tax rate, base rate entity, franking, losses, loan carry-back, loans or payments to shareholders, Bendel | Company taxable income and tax, franking account, Div 7A minimum repayments and deemed dividends | individual-tax (dividends and franking credits, deemed dividends to shareholders) |
| trusts-partnerships | A trust or partnership | Net income, each beneficiary's or partner's share (ordinary, capital gain, franked), s99A and Div 6AA tax, s100A and Bendel flags | individual-tax (shares), cgt (streamed capital gains), company-div7a (corporate beneficiary) |
| sole-trader-business | ABN income as an individual | Net business income, depreciation, car and home office, small business income tax offset, non-commercial loss and PSI outcomes | individual-tax (business income; offset reported separately) |
| rental-property | Residential rental or holiday home; also rent from property outside Australia (its `foreign_rental_net` path) | Net rental result with Div 43 and Div 40, deductible and quarantined parts (quarantining from 1 Jul 2027), holiday home apportionment; for overseas property the net foreign rent from stated amounts with AU-RENT-005 as a scope note | individual-tax (net rental result; loss to `net_investment_losses`), super-contributions (Div 293 net investment loss) |
| crypto | Crypto sales, swaps, spending, staking or airdrop income, forks, lost or stolen crypto, or "is my crypto exempt" (resident individual, capital account) | Per-transaction classification, income at receipt and cost base, parcel-matched gain or loss and net capital gain per income year (through the `cgt` tools), personal use screen; escalations for traders, mining, DeFi, NFTs | cgt (components for combined netting), individual-tax (other income) |
| short-stay-accommodation | Airbnb, Stayz or other short-stay letting by an individual: GST on short-stay rent, private-use and blocked-out nights, holiday home, platform reporting | GST screen (input taxed or escalated), night apportionment and the `rental_property_result` handoff, platform reconciliation, SERR status | rental-property (`rental_property_result_handoff`); gst-bas (`handoff_gst_registration_check`); individual-tax via rental-property |
| cgt | Sales of shares, crypto, property, business assets; main residence; foreign resident CGT; small business concessions screen | Net capital gain after losses and discount (indexation option from 1 Jul 2027), carried-forward capital loss | individual-tax (net capital gain), company-div7a (company gains, no discount) |
| super-contributions | Contributions, caps, personal deductions, Div 293, Div 296, co-contribution, downsizer | Cap positions, deductible personal contributions, Div 293 and Div 296 tax | individual-tax (deduction, `reportable_super_contributions`) |
| individual-tax | An individual's tax figure or income-year settlement | Tax components; `individual_tax_settlement` refund/amount owing with confirmed PAYG, refundable franking and PHI reconciliation; other offsets/unresolved inputs refuse | combined position |
| payg-instalments-lodgment | Lodgment and payment dates, PAYG instalments, failure-to-lodge penalties, GIC and SIC | Instalment amounts, due dates (`lodgment_due_dates`, which `obligations_calendar` reuses), agent lodgment program pointers, penalty and interest estimates | combined calendar (`not_computed` items such as agent program and company or trust return dates) |

## Handoff fields (tool output to tool input)

Pass the upstream field exactly as returned. Every income amount for an individual goes into `assemble_taxable_income` as a component (`kind`, `amount`, `source_skill`, `source_tool`); its `taxable_income` then goes to `individual_income_tax`.

| Upstream tool (skill) | Output field | Component `kind` or downstream input |
|---|---|---|
| user or payment summary | salary, allowances, interest | `salary_wages`, `employment_other`, `interest` (`source_skill: user`) |
| `standard_work_deduction` (individual-tax), 2026-27 onwards | `additional_deduction` | one `work_related_deduction` (`source_skill: individual-tax`, `source_tool: standard_work_deduction`); existing eligible deductions stay as their own components, once |
| `crypto_income_receipts` (crypto) | `total_assessable_income_aud` (by income year), `acquisitions` | `other_income` (`source_skill: user`, `source_tool: crypto_income_receipts`, label "crypto staking and services income"); `acquisitions` go into `crypto_parcel_ledger` |
| `crypto_parcel_ledger` (crypto) | `net_capital_gain_by_income_year`; each slice's `cgt.components` | With no other CGT events: `net_capital_gain` for that year (as returned). With other assets or carried-forward losses: the components join the `gains` and `losses` of `net_capital_gain` (cgt), never added by hand |
| `capital_gain` (cgt), one call per asset | the result's components (amount, discount flag, category) | the `gains` or `losses` list of `net_capital_gain`; never into assembly directly |
| `net_capital_gain` (cgt) | `net_capital_gain`; `net_capital_loss_carried_forward` | `net_capital_gain` (one per year); report the carried-forward loss |
| `main_residence_exemption` (cgt) | taxable part of the gain | a gain in `net_capital_gain` |
| `foreign_rental_net` (rental-property), per overseas property | `assemble_taxable_income_components` (gross rent as `foreign_income`, costs as `other_deduction`), `net_foreign_rental_income_aud`, `indonesia_treaty_fito_inputs`, `foreign_income_tax_offset_inputs` | the components go into `assemble_taxable_income` as returned; the FITO inputs go to `indonesia_treaty_fito` (with `taxable_income` from the assembly) or `foreign_income_tax_offset`; never `rental_property_result` for overseas property |
| `rental_property_result` (rental-property), per property | `net_rental_result` (after any quarantine); `negative_gearing.quarantined_carried_forward` | `rental_net`; a loss also feeds `net_investment_losses` via the assembly handoff `net_rental_loss_for_net_investment_losses` |
| `short_stay_apportionment` (short-stay-accommodation) | `rental_property_result_handoff` | the short-stay fields of `rental_property_result`, with expenses by category and `acquisition_date` added; `net_rental_result` comes from `rental_property_result` |
| `gst_short_stay_classification` (short-stay-accommodation) | `handoff_gst_registration_check` | `input_taxed_sales_included` in `gst_registration_check`, with the host's other taxable turnover |
| `trust_distribution_shares` (trusts-partnerships), per beneficiary | `share_of_ordinary_net_income`, `attributable_franked_distribution`, `franking_credit`, `capital_gain_grossed_up` (and `attributable_capital_gain`) | `trust_ordinary_share`, `trust_franked_distribution`, `franking_credit`; the grossed-up gain goes into `net_capital_gain` as a gain (discount-eligible when the trust applied the discount). Do not also pass `total_assessed` |
| `partnership_shares` (trusts-partnerships) | each partner's `share_of_net_income` | `partnership_share` |
| `div6aa_minor_tax` (trusts-partnerships) | Div 6AA tax | reported beside the minor's tax, not assembled |
| `simplified_depreciation`, `car_expense_cents_per_km`, `home_office_fixed_rate` (sole-trader-business) | deduction amounts | inside the business result the skill states; pass the net result as `business_net` |
| `non_commercial_loss_test` (sole-trader-business) | `deductible_loss`, `deferred_loss` | `business_net` (negative); set `deferred_non_commercial_loss` for a deferred loss |
| `small_business_income_tax_offset` (sole-trader-business) | `offset` | run after assembly with the assembled `taxable_income`; report beside the tax, never subtract it by hand |
| `company_tax` (company-div7a) | `taxable_income`, `net_tax_payable`, `base_rate_entity` | company section; company taxable income is not assembled with an individual's |
| `max_franking_credit` (company-div7a) | `shareholder.grossed_up_dividend`, `shareholder.franking_tax_offset` | shareholder's `dividends_franked` (the dividend) plus `franking_credit` |
| `div7a_minimum_repayment`, `div7a_loan_schedule` (company-div7a) | `deemed_dividend`, `shortfall_deemed_dividend` | shareholder's `deemed_dividend` (unfranked) |
| `reportable_fringe_benefits_amount` (fbt) | the reportable amount | `individual_income_tax.reportable_fringe_benefits`; `div293_tax.reportable_fringe_benefits` (not in taxable income) |
| `concessional_cap_position` (super-contributions) | `personal_deductible` | `personal_super_deduction`; salary sacrifice plus personal deductible amounts to `reportable_super_contributions` |
| `residency_indicators` (residency-cross-border) | overall indication, months resident | `individual_income_tax.residency`, `resident_months` |
| foreign income facts (residency-cross-border) | gross foreign income in AUD | `foreign_income` (gross, `net_of_foreign_tax: false`) |
| `foreign_income_tax_offset` (residency-cross-border) | `offset_after_limit`, `tax_payable_after_fito` | run after `individual_income_tax` with its tax figures; quote `tax_payable_after_fito` |
| `indonesia_treaty_fito` (au-indonesia-cross-border) | `creditable_foreign_tax`, `fito.offset_after_limit`, `fito.tax_payable_after_fito` | as `foreign_income_tax_offset`: gross Indonesian income goes in as `foreign_income`; run after `individual_income_tax`; quote `fito.tax_payable_after_fito`; the capital gain part needs the cgt `net_capital_gain` first |
| `payg_withholding` (payroll-sg) or payment summaries | confirmed year tax withheld | `individual_tax_settlement.tax_withheld`; component estimates only: `individual_income_tax.tax_withheld` |
| ATO income-year instalment reconciliation | credit net of variations | `individual_tax_settlement.payg_instalment_credit`; unpaid instalment debts stay on the account |
| Dividend statements and confirmed individual entitlement | credit, dividend/gross-up already included once in assembly | `individual_tax_settlement.franking`; never infer eligibility from `max_franking_credit` alone |
| Allocated PHI statement rows and confirmed income/family/age facts | gross eligible premiums excluding loading; rebate received | `individual_tax_settlement.private_health_rebate`; selected-year period/age tables calculate entitlement |
| `obligations_calendar` (router) | `calendar`, `recurring_rules`, `not_computed`, `unverified` | calendar section |

`div293_tax` inputs: `taxable_income` (the assembled figure), `reportable_fringe_benefits` (fbt), `net_investment_loss` (the assembly handoff plus any financial investment loss), `concessional_contributions` (super-contributions).

## Worked routing examples

**"I'm a sole trader with a rental and some crypto, 2026-27, resident."**
Plan: gst-bas (only if registered or near the threshold) > sole-trader-business > rental-property > cgt (crypto disposals) > super-contributions (if personal contributions) > individual-tax > `obligations_calendar` (entity_type sole_trader) > payg-instalments-lodgment. `assemble_taxable_income` components: `business_net`, `rental_net`, `net_capital_gain`, other income, `personal_super_deduction`. Then `individual_income_tax`, then `small_business_income_tax_offset` with the assembled taxable income.

**"I'm on a salary, staked some ETH, swapped a bit and sold shares, 2026-27, resident."**
Plan: crypto (`crypto_character_screen` > `crypto_classify_transactions` > `crypto_income_receipts` for staking > `crypto_parcel_ledger`) > cgt (share sale as `capital_gain`, then one `net_capital_gain` over the crypto slice components and the share result) > individual-tax. `assemble_taxable_income` components: `salary_wages`, `other_income` (staking income from `crypto_income_receipts`), `net_capital_gain`. A refusal on one crypto row (for example a liquidity pool, AU-CGT-005) is listed under "Parts not completed" and the other rows and the shares still run.

**"Year-end for my company, it pays me a salary and I borrowed from it."**
Plan: bookkeeping-year-end > gst-bas > payroll-sg > fbt (if benefits) > state-taxes-sa (if SA payroll tax) > company-div7a (tax, franking, Div 7A loan) > individual-tax for the director (salary, dividends, any deemed dividend) > `obligations_calendar` (entity_type company) > payg-instalments-lodgment.

**"Family trust owns a rental; distributes to me, my spouse and a bucket company."**
Plan: rental-property (trust's rental result, as trust net income input) > trusts-partnerships (shares, s100A and Bendel flags) > company-div7a (corporate beneficiary) > individual-tax for each individual beneficiary > `obligations_calendar` for the trust and the company.

**"I moved to Bali in March; I have Australian rent and Indonesian consulting income."**
Plan: residency-cross-border first. If residency comes back `uncertain_escalate` (AU-RES-004), quote it and show later results only as labelled alternatives. Then rental-property, sole-trader-business (if carrying on business), individual-tax with `resident_months`, FITO reported separately.

**"I own a villa in Bali, let it out, and my Adelaide company sends two staff there for a project."**
Plan: residency-cross-border (residency indication) > au-indonesia-cross-border (`idr_to_aud`, `indonesia_treaty_allocation` for the rent, `indonesia_service_pe_screen` for the staff; an Indonesian company, a villa held through an entity or a fixed base escalates) > rental-property (`foreign_rental_net` for the villa, never `rental_property_result`) and cgt for the Australian side > `assemble_taxable_income` (villa gross rent as `foreign_income`, its costs as `other_deduction`) > individual-tax > `indonesia_treaty_fito`, offset reported beside the tax. AU-RENT-005 is quoted as a scope note on the villa costs and the total is still given.

**One part refused.** Example: the trust's s100A position is refused (AU-TRUST-001). The router still completes the trust shares, the rental result and each beneficiary's tax, lists AU-TRUST-001 under "Parts not completed" at the top and in section 5, and marks any figure that depended on the s100A outcome as incomplete.

## Settlement handoff

For supported individual income-year settlements, call `individual_tax_settlement` with assembled taxable income, the same tax facts and assembly limitations unchanged. Follow `skills/individual-tax/references/settlement.md`. Keep FITO, SBITO and every other unmodelled offset/credit or unresolved input in `unmodelled_inputs`; any entry or component limitation blocks the final figure. Company/trust assessments and ATO account balances remain separate. Never hand-net separately returned offsets.
