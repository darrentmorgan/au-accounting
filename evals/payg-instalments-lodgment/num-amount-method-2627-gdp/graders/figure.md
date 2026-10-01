---
type: regex
pattern: '(?<![\d,])\$?\s?6,?300(?:\.00)?(?![\d,])'
target: last_message
---

<!--
Amount method: notional tax uplifted by the GDP adjustment factor (5% for 2026-27, ATO page) = 24,000 x 1.05 = 25,200; quarterly payer pays a quarter: 25,200 / 4 = 6,300.
Primary sources: https://www.ato.gov.au/businesses-and-organisations/income-deductions-and-concessions/payg-instalments/calculate-your-payg-instalments/how-we-calculate-your-payg-instalment-amount-or-rate ; https://www.ato.gov.au/businesses-and-organisations/business-bulletins-newsroom/payg-instalments-for-business-and-investment-income
A plain 24,000/4 = 6,000 is the wrong answer (no uplift).
-->
The answer states a quarterly instalment of $6,300.
