---
type: regex
pattern: '(?<![\d,])\$?\s?33,?51[78](?:\.\d{1,2})?(?![\d,])'
target: last_message
---
<!--
CORRECTED by coordinator 2026-09-29 (original 37,636.87 used a remaining term of 6, which is wrong).
ITAA 1936 s109E(6): remaining term = 7 minus the number of whole income years that have elapsed between the end of the income year in which the loan was made and the start of the current year. Loan made 1 July 2025 (2025-26); current year 2026-27; 0 years elapsed, so remaining term = 7 (matches the ATO worked example: loan made in one year, first repayment next year with 7 years remaining).
MYR = 170,000 x 0.0877 / (1 - 1.0877^-7) = 14,909 / 0.444806 = 33,517.15. Rate 8.77% for 2026-27.
Sources: https://www.ato.gov.au/tax-rates-and-codes/division-7a-benchmark-interest-rate ; ITAA 1936 s109E (legislation.gov.au)
-->
The answer states a minimum yearly repayment of about $33,517.
