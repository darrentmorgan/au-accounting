---
type: regex
pattern: '(?<![\d,])\$?\s?74,?250(?:\.\d{2})?(?![\d,])'
target: last_message
---

<!--
CORRECTED by coordinator 2026-09-29. The original expectation (103,950, "deduction tapers to nil") came from an erroneous research note. Payroll Tax Act 2009 (SA) Sch 1 and RevenueSA "How is payroll tax calculated" show a flat $600,000 deduction for a full-year SA-only employer; the rate is set by total wages (full 4.95% above $1.7m) and applied to wages less the deduction.
(2,100,000 - 600,000) x 4.95% = 74,250.
Primary: https://www.revenuesa.sa.gov.au/payroll-tax/how-is-payroll-tax-calculated ; https://www.revenuesa.sa.gov.au/payroll-tax/rates-and-thresholds
-->
The answer states SA payroll tax of $74,250.
