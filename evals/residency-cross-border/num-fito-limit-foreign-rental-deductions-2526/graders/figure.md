---
type: regex
pattern: '(?<![\d,])\$?\s?7,?680(?:\.\d{2})?(?![\d,])'
target: last_message
---

<!--
Step 2 disregards the $30,000 foreign income and the $6,000 deductions reasonably related to it (s 770-75(4)), i.e. net $24,000 comes out. Taxable income for step 2 = 90,000 - 24,000 = 66,000.
Step 1: 90,000: 4,288 + 0.30 x 45,000 = 17,788; Medicare 1,800; total 19,588.
Step 2: 66,000: 4,288 + 0.30 x 21,000 = 10,588; Medicare 1,320; total 11,908.
Limit = 19,588 - 11,908 = 7,680 (greater than $1,000). Foreign tax paid 8,000 > 7,680, so offset = 7,680.
Wrong answers: 7,200 (no Medicare), 8,000 (no limit), about 5,223 (average rate on 24,000).
Primary sources: https://www.ato.gov.au/forms-and-instructions/foreign-income-tax-offset-rules-guide-2024/calculate-your-fito-or-offset-limit ; https://www.austlii.edu.au/au/legis/cth/consol_act/itaa1997240/s770.75.html ; https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents
-->
The answer states the offset of $7,680.
