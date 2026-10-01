---
type: regex
pattern: '(?<![\d,.])\$?\s?12,?000(?:\.00)?(?![\d,])'
target: last_message
---

<!--
1A: GST on taxable sales 10% x 180,000 = 18,000. Exports (G2), the GST-free purchase and bank interest (input-taxed financial supply) carry no GST. 1B: creditable purchases 1/11 x (55,000 + 11,000) = 1/11 x 66,000 = 6,000. GST-free purchase and wages give no credit. Net = 1A - 1B = 18,000 - 6,000 = 12,000 payable to the ATO.
Sources: https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/in-detail/managing-gst-in-your-business/reporting-paying-and-activity-statements/completing-your-bas-for-gst/complete-your-bas/step-1-sales
-->
The answer states a net GST payable of $12,000 (1A $18,000, 1B $6,000).
