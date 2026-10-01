---
type: regex
pattern: '(?<![\d,])\$?\s?940(?:\.\d{2})?(?![\d,])'
target: last_message
---

<!--
s 770-75(2): the offset limit is the GREATER of $1,000 and the computed amount. ATO: if claiming a FITO of $1,000 or less you only record the actual foreign tax paid; no limit calculation is needed.
For reference, the computed amount: taxable 50,000 -> tax 4,288 + 0.30 x 5,000 = 5,788, Medicare 1,000. Taxable 47,500 -> tax 4,288 + 0.30 x 2,500 = 5,038, Medicare 950. Difference = (5,788 - 5,038) + (1,000 - 950) = 800.
Computed 800 < $1,000, so the limit is $1,000. Foreign tax paid 940 is under the limit, so offset = 940 in full (not 800).
Primary sources: https://www.austlii.edu.au/au/legis/cth/consol_act/itaa1997240/s770.75.html ; https://www.ato.gov.au/forms-and-instructions/foreign-income-tax-offset-rules-guide-2024/calculate-your-fito-or-offset-limit
-->
The answer states the offset of $940.
