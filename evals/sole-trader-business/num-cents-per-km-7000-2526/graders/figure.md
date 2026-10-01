---
type: regex
pattern: '(?<![\d,])\$?\s?4,?400(?:\.00)?(?![\d,])'
target: last_message
---

<!--
Cents per km is capped at 5,000 business km per car per year; 2025-26 rate 88c. 5,000 x 0.88 = 4,400. (7,000 x 0.88 = 6,160 is the wrong answer.)
Primary source: https://www.ato.gov.au/individuals-and-families/income-deductions-offsets-and-records/deductions-you-can-claim/work-related-deductions/cars-transport-and-travel/motor-vehicle-and-car-expenses/expenses-for-a-car-you-own-or-lease/cents-per-kilometre-method
-->
The answer states $4,400.
