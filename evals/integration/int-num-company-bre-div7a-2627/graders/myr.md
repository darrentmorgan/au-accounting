---
type: regex
pattern: '(?<![\d,])\$?\s?29,?57[34](?:\.\d{2})?(?![\d,])'
target: last_message
---

<!--
Loan made in the 2025-26 year, so the first minimum yearly repayment is for 2026-27 (none is required in the year the loan is made). P = 150,000 (nothing repaid), I = 2026-27 benchmark rate 8.77% (not the 8.37% 2025-26 rate), remaining term T = 7 - 0 = 7 years.
MYR = P x I / (1 - (1+I)^-T) = 150,000 x 0.0877 / (1 - 1.0877^-7) = 13,155 / 0.44481... = 29,573.95, i.e. about 29,574.
Primary: https://www.ato.gov.au/tax-rates-and-codes/division-7a-benchmark-interest-rate ; https://www.ato.gov.au/businesses-and-organisations/corporate-tax-measures-and-assurance/private-company-benefits-division-7a-dividends/in-detail/division-7a-loans
-->
The answer states a minimum yearly repayment of about $29,574 (either $29,573 or $29,574 is accepted).
