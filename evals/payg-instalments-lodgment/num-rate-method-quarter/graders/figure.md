---
type: regex
pattern: '(?<![\d,])\$?\s?7,?605(?:\.00)?(?![\d,])'
target: last_message
---

<!--
Rate method (ATO calculate-your-payg-instalments): T1 x T2 = T11 (= 5A). 84,500 x 0.09 = 7,605.00. No GDP uplift on the rate method.
Primary sources: https://www.ato.gov.au/businesses-and-organisations/income-deductions-and-concessions/payg-instalments/calculate-your-payg-instalments ; https://www.ato.gov.au/forms-and-instructions/payg-instalments-how-to-complete-your-activity-statement
-->
The answer states an instalment of $7,605.
