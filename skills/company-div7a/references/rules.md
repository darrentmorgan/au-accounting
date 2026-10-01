# Method detail: company-div7a

How the tools compute, in the order they apply. Figure keys in brackets; values come from the rates files.

## Company tax (`company_tax`)
1. Passive share = base rate entity passive income / assessable income (ITRA s23AB).
2. Base rate entity if aggregated turnover is below `company.bre_aggregated_turnover_threshold` AND the passive share is no more than `company.bre_passive_income_max_share`. Both use THIS year's figures (LCR 2019/5: earlier years are irrelevant to the tax rate).
3. Rate = `company.rate_base_rate_entity` or `company.rate_other`; gross tax = rate x taxable income.
4. Franking tax offset for franked dividends received is non-refundable for a company; the excess converts to a tax loss (ITAA 1997 s36-55), shown as excess / rate.
5. Balance = net tax less PAYG instalments. Tax paid credits the franking account; a refund debits it.

## Imputation rate and franking (`max_franking_credit`)
1. Corporate tax rate for imputation purposes: rerun the base rate entity test assuming this year's turnover, passive income and assessable income equal LAST year's, compared with this year's threshold. A company that did not exist last year uses the lower rate.
2. Gross-up rate = (1 - imputation rate) / imputation rate. Maximum franking credit = distribution / gross-up rate (s202-60(2)).
3. Credit allocated = maximum x franking percentage; above the maximum it is limited to the maximum (s202-60(1)).
4. Shareholder: grossed-up dividend = distribution + credit; franking tax offset = credit.
5. Franking account: each allocated credit is a debit. A deficit at year end means franking deficit tax equal to the deficit; the later offset is reduced by `company.fdt_offset_reduction_rate` where the deficit exceeds `company.fdt_offset_reduction_threshold` of credits arising that year (s205-70). Escalate the reduction (AU-COMP-009).
6. Private companies have one franking period per income year; every frankable distribution in it should carry the benchmark franking percentage set by the first (Div 203).

## Loss carry back (`loss_carry_back_offset`)
Checks, all required (s160-5): loss year starts on or after 1 Jul 2026; corporate tax entity throughout; a tax loss; not a significant global entity; returns lodged, not required, or assessed for the loss year and the previous `company.loss_carry_back_lodgment_lookback_years` years; at least one eligible carry back year (one of the previous `company.loss_carry_back_years` years with an income tax liability, corporate tax entity throughout).
Amount (s160-10), for each carry back year: step 1 loss carried back; step 2 less that year's net exempt income; step 3 x corporate tax rate for the LOSS year; component = lesser of step 3 and that year's income tax liability not already used by an earlier carry back. Offset = lesser of the sum and the franking account balance at the end of the loss year. The Act's own example (a general-rate company carrying one loss back to two years) is reproduced in the unit tests.
Default split when the user gives none: older year first, carrying back only as much loss as the liability and franking cap can use; unused loss carries forward. The company makes the real choice in the approved form.

## Division 7A minimum yearly repayment (`div7a_minimum_repayment`)
1. No MYR in the loan year; the loan must be repaid or put under a complying agreement before lodgment day.
2. Remaining term = agreement term less whole years from the end of the loan year to the end of the previous year (s109E(6)).
3. MYR = balance x rate / (1 - (1 / (1 + rate)) ^ remaining term), rate = `div7a.benchmark_interest_rate` for the year of the MYR.
4. First year: balance = loan less repayments before lodgment day; those repayments also count in that year.
5. Shortfall = MYR less repayments in the year; deemed dividend = shortfall capped at distributable surplus when given (s109Y).
6. Term check: above `div7a.max_term_unsecured_years` (or `div7a.max_term_secured_years` with qualifying security) means not complying.

## Division 7A schedule (`div7a_loan_schedule`)
- Rates by year from `div7a.benchmark_interest_rate_history`; later years use overrides or are projected at the latest published rate and marked `projected`.
- Interest on the daily balance at the benchmark rate (s109E(7)); a repayment reduces the balance from its own date; denominator = days in the income year. The ATO worked example's interest and closing balance are reproduced (see `tests/unit/test_company.py`).
- Years without listed repayments: MYR treated as paid at the close of 30 June (full year of interest), which amortises the loan to nil at a constant rate.
