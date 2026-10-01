# Router intake

Ask in one short batch, skipping anything the user already gave. Group questions by the headings below. Where a fact is missing but not decisive, proceed on a labelled assumption.

## 1. Year and entities

| Question | Why | Feeds |
|---|---|---|
| Which income year (1 July to 30 June)? For FBT, which FBT year (1 April to 31 March)? | Every figure is year-specific; "this year" is ambiguous | all |
| Which entities are involved: you personally, a sole trader business, partnership, company, trust (family, unit), SMSF? | Each entity has its own return and obligations | skill map |
| Who owns, controls or benefits from each entity (shareholders, directors, beneficiaries, partners)? | Distributions, Div 7A, s100A, associates | trusts-partnerships, company-div7a |

## 2. Residency

| Question | Why | Feeds |
|---|---|---|
| Were you an Australian resident all year? Any time overseas, arrival or departure, visa type? | Residency sets rates, tax-free threshold, Medicare, CGT on foreign assets | residency-cross-border, individual-tax, cgt |
| Any foreign income, foreign tax paid, foreign super, foreign companies or trusts? | Foreign income, FITO, CFC and foreign trust escalations | residency-cross-border |

## 3. Income sources

| Question | Why | Feeds |
|---|---|---|
| Salary or wages (employer, PAYG withheld, reportable fringe benefits, reportable super)? | Base taxable income, withholding credit, income tests | individual-tax |
| Business or ABN income (sole trader, contractor, gig work, personal services)? | Business result, PSI, non-commercial losses | sole-trader-business |
| Rental properties or holiday homes (ownership share, dates, income, expenses, private use)? | Rental result, capital works and depreciation, holiday home limits | rental-property |
| Short-stay letting (Airbnb, Stayz, room or granny flat) or a hotel-run apartment? | GST screen, night apportionment, platform reporting | short-stay-accommodation, then rental-property |
| Sales of shares, property or business assets; any capital losses carried forward? | Net capital gain | cgt |
| Crypto: sales, swaps, spending, staking or airdrop rewards, forks, lost or stolen crypto? Does the person trade often, mine or run a related business? | Crypto income, capital gains and the investor or business screen | crypto |
| Distributions from a trust or share of partnership profit? | Beneficiary and partner shares | trusts-partnerships |
| Dividends (franked), interest, loans from your company? | Franking credits, Div 7A | company-div7a, individual-tax |
| Super contributions (employer, salary sacrifice, personal, after-tax), total super balance? | Caps, personal deduction, Div 293 | super-contributions |

## 4. Registrations and obligations

| Question | Why | Feeds |
|---|---|---|
| ABN? GST registered (cycle monthly, quarterly or annual; cash or accruals; GST turnover)? | BAS, due dates, GST-exclusive amounts | gst-bas, obligations_calendar |
| PAYG withholding registered? Employees or contractors? STP reporting? | Withholding, Payday Super, worker status | payroll-sg, obligations_calendar |
| In the PAYG instalment system? | Instalment dates and credits | payg-instalments-lodgment |
| Fringe benefits (cars, loans, parking, entertainment)? | FBT return and reportable amounts | fbt |
| State payroll tax, land tax, stamp duty on a purchase? Which state? | State obligations (SA modelled; others escalate) | state-taxes-sa |
| Lodging yourself or through a registered agent? | Agent lodgment program dates | obligations_calendar |

## 5. Books

| Question | Why | Feeds |
|---|---|---|
| What accounting records exist (software, bank reconciliations up to date, trading stock count, prepayments)? | Year-end adjustments before tax figures | bookkeeping-year-end |

## Fact to skill quick map

| Fact | Load |
|---|---|
| Any doubt about residency, foreign income | residency-cross-border |
| Bali or Indonesian income, days in Indonesia, the Indonesia tax treaty, Indonesian tax paid, payments to an Indonesian resident | au-indonesia-cross-border (after residency-cross-border) |
| Messy books, year-end close, chart of accounts, trading stock, financial statements | bookkeeping-year-end |
| GST registered or near the threshold | gst-bas |
| Employees, contractors, super guarantee | payroll-sg |
| Fringe benefits | fbt |
| Payroll tax, land tax, stamp duty | state-taxes-sa |
| Company, private company loans, dividends to shareholders | company-div7a |
| Trust or partnership | trusts-partnerships |
| ABN income as an individual | sole-trader-business |
| Rental or holiday home | rental-property |
| Airbnb or other short-stay letting | short-stay-accommodation (then rental-property) |
| Crypto sales, swaps, staking, airdrops, forks, lost crypto | crypto (then cgt for combined netting) |
| Other asset sales, main residence change | cgt |
| Super contributions or large balances | super-contributions |
| Individual needs a tax figure | individual-tax |
| Due dates, instalments, penalties, interest charges | payg-instalments-lodgment and `obligations_calendar` |
| Single figure question | rates-lookup |
