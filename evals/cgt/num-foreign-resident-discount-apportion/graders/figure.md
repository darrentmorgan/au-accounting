---
type: regex
pattern: '(?<![\d,])234,5[5-9]\d(?![\d])'
target: last_message
---

<!--
Owned 1 Jul 2017 to 1 Sep 2026 inclusive = 3,350 days. Resident days 1 Jul 2017 to 30 Jun 2021 inclusive = 1,461 days.
Foreign resident discount (s115-105): 50% x (1,461 / 3,350) = 21.806%. Discount = 300,000 x 21.806% = 65,418. Net capital gain = 300,000 - 65,418 = 234,582.
Regex accepts 234,55x to 234,59x (exclusive-day counting gives ~234,563). Sale before 1 Oct 2026, so the new foreign resident CGT regime does not affect this.
Wrong: full 50% = 150,000; no discount = 300,000.
Primary: https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/cgt-discount ; https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/calculating-your-cgt/how-to-calculate-your-cgt
-->
The answer states a net capital gain of about $234,582.
