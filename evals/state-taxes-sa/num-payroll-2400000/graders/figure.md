---
type: regex
pattern: '(?<![\d,])\$?\s?89,?100(?:\.00)?(?![\d,])'
target: last_message
---

<!--
SA: full $600,000 deduction, rate 4.95% (wages > $1.7m). Taxable = 2,400,000 - 600,000 = 1,800,000. Tax = 1,800,000 x 4.95% = 89,100.
NOTE: the deduction does NOT taper away above $1.7m in SA; the rate is set on gross Australian wages, then applied to wages less the deduction. The naive 4.95% x 2,400,000 = 118,800 is wrong.
Primary sources: https://www.revenuesa.sa.gov.au/payroll-tax/how-is-payroll-tax-calculated ; https://www.revenuesa.sa.gov.au/payroll-tax/rates-and-thresholds ; https://www.payrolltax.gov.au/harmonisation/payroll-tax-rates-and-thresholds (max deduction $600,000)
-->
The answer states $89,100.
