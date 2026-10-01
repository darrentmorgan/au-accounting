---
type: regex
pattern: '(?<![\d,.])\$?\s?705(?:\.00)?(?![\d,])'
target: last_message
---

<!--
Schedule 1 Scale 4 (no TFN): resident rate 47% on earnings, ignoring cents. 0.47 x 1,500 = $705. (Foreign resident rate would be 45% = $675.)
Primary source: https://www.ato.gov.au/tax-rates-and-codes/payg-withholding-schedule-1-statement-of-formulas-for-calculating-amounts-to-be-withheld/coefficients-to-use-in-formulas-for-withholding-from-weekly-payments
-->
The answer states $705.
