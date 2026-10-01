---
type: regex
pattern: '(?<![\d,])\$?\s?11,?32[01](?:\.\d{1,2})?(?![\d,])'
target: last_message
---

<!--
Taxable value 6,000 exceeds the $2,000 threshold so it is reportable. RFBA is grossed up using the lower type 2 rate 1.8868 regardless of type 1 or 2: 6,000 x 1.8868 = 11,320.80. Using 2.0802 (12,481.20) would be wrong.
Primary sources: https://www.ato.gov.au/tax-rates-and-codes/fringe-benefits-tax-rates-and-thresholds
-->
The answer states a reportable fringe benefits amount of about $11,321 (11,320.80).
