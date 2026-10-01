---
type: regex
pattern: '(?<![\d,.])\$?\s?(?:169|170|171)(?:\.\d{1,2})?(?![\d,])'
target: last_message
---

<!--
Schedule 1 (Withholding Schedules Instrument 2026, effective 1 July 2026), Scale 2 weekly coefficients. x = whole dollars + 99c = 1,100.99. Band 'less than 1,282': a = 0.3227, b = 185.1935. y = 0.3227 x 1,100.99 - 185.1935 = 355.2895 - 185.1935 = 170.0960, rounded to the nearest dollar = $170. Regex allows $169 to $171 (rounding tolerance of $1).
Primary sources: https://www.ato.gov.au/tax-rates-and-codes/payg-withholding-schedule-1-statement-of-formulas-for-calculating-amounts-to-be-withheld/coefficients-to-use-in-formulas-for-withholding-from-weekly-payments ; https://www.legislation.gov.au/F2026L00716/asmade/2026-06-12/text/original/pdf
-->
The answer states about $170.
