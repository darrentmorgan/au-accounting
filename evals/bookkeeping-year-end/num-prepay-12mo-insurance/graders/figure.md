---
type: regex
pattern: '(?<![\d,])\$?\s?9,?000(?:\.00)?(?![\d,])'
target: last_message
---

<!--
Small business entity (turnover under $10m). Eligible service period 1 May 2026 to 30 Apr 2027 = 12 months, ends in the next income year, so the 12-month rule allows an immediate deduction. GST-exclusive cost = 9,900 / 1.1 = 9,000. Deduction in 2025-26 = 9,000 (the $900 GST is an input tax credit on the BAS, not part of the deduction).
Wrong answer if apportioned: 9,000 x 61/365 = 1,504.
Primary source: https://www.ato.gov.au/forms-and-instructions/deductions-for-prepaid-expenses-2026 
-->
The answer states an immediate deduction of $9,000 (GST-exclusive).
