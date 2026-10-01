---
type: regex
pattern: '(?<![\d,])\$?\s?1,?550(?:\.00)?(?![\d,])'
target: last_message
---

<!--
Ledger net = 31,150 - 17,600 = 13,550. BAS net = 30,000 - 18,000 = 12,000. Variance = 1,550 (ledger higher). 1A: ledger 31,150 vs BAS 30,000 = 1,150 over. 1B: ledger 17,600 vs BAS 18,000 = 400 under (ledger credits lower than BAS). 1,150 + 400 = 1,550.
Primary sources: https://www.ato.gov.au/businesses-and-organisations/preparing-lodging-and-paying/business-activity-statements-bas/how-to-complete-your-bas ; https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/in-detail/gst-and-bookkeeping 
-->
The answer states the net variance of $1,550.
