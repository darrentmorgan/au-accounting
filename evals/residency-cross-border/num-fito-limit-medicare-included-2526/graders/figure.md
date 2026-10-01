---
type: regex
pattern: '(?<![\d,])\$?\s?6,?750(?:\.\d{2})?(?![\d,])'
target: last_message
---

<!--
2025-26 resident scale (ATO tax-rates-australian-residents): 0-18,200 nil; 18,201-45,000 16c; 45,001-135,000 $4,288 + 30c; 135,001-190,000 $31,288 + 37c.
ATO FITO guide (Calculate your FITO or offset limit) and s 770-75 ITAA 1997: limit = greater of $1,000 and (income tax payable INCLUDING Medicare levy and MLS, less the same tax with the foreign income and related deductions disregarded).
Step 1: taxable 140,000. Tax 31,288 + 0.37 x 5,000 = 33,138. Medicare 2% = 2,800. Total 35,938. (Private hospital cover, so no MLS.)
Step 2: taxable 120,000. Tax 4,288 + 0.30 x 75,000 = 26,788. Medicare 2,400. Total 29,188.
Limit = 35,938 - 29,188 = 6,750. Foreign tax paid 7,000 exceeds it, so offset = 6,750. The 250 excess is not refunded or carried forward.
Common wrong answers: 6,350 (omits Medicare levy), about 5,134 (average rate x 20,000), 7,000 (ignores limit).
Primary sources: https://www.ato.gov.au/forms-and-instructions/foreign-income-tax-offset-rules-guide-2024/calculate-your-fito-or-offset-limit ; https://www.austlii.edu.au/au/legis/cth/consol_act/itaa1997240/s770.75.html ; https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents
-->
The answer states the offset of $6,750.
