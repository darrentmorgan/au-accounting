---
type: regex
pattern: '(?<![\d,])\$?\s?3,?162(?:\.00)?(?![\d,])'
target: last_message
---

<!--
Benchmark (statutory) interest rate for FBT year ending 31 Mar 2027 = 8.27%. Interest at benchmark 60,000 x 8.27% = 4,962. Interest actually charged 60,000 x 3% = 1,800. Taxable value = 4,962 - 1,800 = 3,162.
Primary sources: https://www.ato.gov.au/tax-rates-and-codes/fringe-benefits-tax-rates-and-thresholds ; https://www.ato.gov.au/businesses-and-organisations/hiring-and-paying-your-workers/fringe-benefits-tax/types-of-fringe-benefits/loan-and-debt-waiver-fringe-benefits
-->
The answer states a taxable value of $3,162.
