---
type: regex
pattern: '(?<![\d,])\$?\s?600(?:\.\d{2})?(?![\d,])'
target: last_message
---

<!--
Payday Super from 1 July 2026: SG = 12% of qualifying earnings. QE includes salary sacrificed super contributions, so QE = 5,000 (4,800 cash + 200 sacrificed). SG = 12% x 5,000 = 600. Trap: 12% x 4,800 = 576.
Primary: https://www.ato.gov.au/businesses-and-organisations/super-for-employers/payday-super/about-payday-super ; https://www.ato.gov.au/businesses-and-organisations/super-for-employers/paying-super-on-payday/how-to-work-out-and-pay-super
-->
The answer states SG of $600 for the payday.
