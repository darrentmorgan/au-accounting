---
type: regex
pattern: '(?<![\d,])\$?\s?2,?250(?:\.00)?(?![\d,])'
target: last_message
---

<!--
Div 6AA: over $1,307 the rate is 45% of the total amount (not just the excess). 5,000 x 0.45 = 2,250. The tax-free threshold is not available against this income. A figure of about $1,647 or a marginal-rates result is a fail.
Primary source: https://www.ato.gov.au/tax-rates-and-codes/tax-rates-if-you-re-under-18-years-old
-->
The answer states $2,250.
