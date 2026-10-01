# Classification and calculation order

The `rental_property_result` tool applies these steps. Figures are named by key; values come from `data/rates/<year>.d/rental.yaml`.

## Classification of expenses

| Kind | Examples | Treatment |
|---|---|---|
| Direct letting | agent letting and management fees, platform commissions, advertising, cleaning and linen after paying guests | Deductible in full, no apportionment (PCG 2026/2 paras 10-12) |
| Ownership and use | interest, council rates, water, land tax, insurance, ordinary body corporate levies, repairs and maintenance, gardening, bank fees | Apportioned by the private-use factor; denied for a holiday home that is not mainly for rent |
| Borrowing expenses | loan establishment, mortgage stamp duty, valuation for the loan, lender's mortgage insurance billed to you | Spread over the shorter of the loan term, repayment date or the maximum period; in full if the year's total is within the small-amount limit (`rental.borrowing_expense_max_years`, `rental.borrowing_expense_immediate_limit`) |
| Depreciating assets | carpet, blinds, oven, dishwasher, furniture | Prime cost or diminishing value on effective life; second-hand assets denied unless grandfathered (`rental.second_hand_asset_*`); low-cost items in full within `rental.low_cost_asset_immediate_deduction_limit` |
| Capital works | building, extensions, structural improvements, initial repairs | Div 43: cost x rate for the construction start date x days claimed over days in year (`rental.capital_works_rate_*`) |
| Denied | travel to a residential rental (s 26-31); holding costs of vacant land (s 26-102); ownership costs of a holiday home not used mainly for rent (s 26-50) | Nil |
| Capital, not deductible now | purchase stamp duty and legal costs, sale costs, improvements, initial repairs | CGT cost base, or capital works or depreciation where available |

## Order of calculation

1. Refuse out-of-scope owners and uses (AU-RENT-001, AU-RENT-005); refuse an unresolved holiday home test (AU-RENT-003).
2. Direct letting expenses are summed. Interest has its non-rental purpose share removed. Depreciation, borrowing expenses and capital works are computed on their own rules for the ownership period.
3. Holiday home not mainly for rent, or vacant land: ownership costs, borrowing, depreciation and capital works are set to nil and reported as denied.
4. Apportionment factor = time factor x area factor.
   - Time factor = (days rented + days available on commercial terms) / days in period; nil available days for a room in the home.
   - Area factor = (area exclusive to tenant + shared area / 2) / total area.
5. Deductions = direct letting + factor x (ownership + borrowing + depreciation + capital works).
6. Rent below market to family or friends: deductions capped at the rent received.
7. Ownership percent scales income and deductions to the taxpayer's legal-title share.
8. Loss quarantine: applies only when the income year starts on or after the year in `rental.negative_gearing_first_income_year`. Excess of (deductions + amount brought forward) over income is not deductible and carries forward, reduced by net income from exempt dwellings (s 26-155(6)(a)). Before that year the tool reports status and, on request, a preview labelled illustrative.

## Capital works dates (Div 43)

Rate is set by the date construction began. The general residential and income-producing building rate applies from the dates in `rental.capital_works_rate_residential`; the traveller accommodation series in `rental.capital_works_rate_traveller_accommodation` applies only where you own or lease at least `rental.capital_works_traveller_minimum_units` apartment units, or the hotel, motel or guest house has at least that many bedrooms, intended for short-term traveller accommodation. A single dwelling let short-stay uses the general rate. Deductions begin when construction is complete. The claim cannot exceed undeducted construction expenditure. A certain class of pre-16 September 1987 contracts has a special rate that is not modelled (AU-RENT-004).

## What the tool does not model

Split-loan tracing beyond the private-share input, low-value pools, the sale of a depreciating asset, balancing adjustments, the offset of quarantined amounts against capital gains, the aggregation of several dwellings for quarantine, GST, and any foreign tax.
