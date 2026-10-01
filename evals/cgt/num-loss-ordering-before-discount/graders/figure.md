---
type: regex
pattern: '(?<![\d,])16,?000(?:\.00)?(?![\d,])'
target: last_message
---

<!--
Total losses 12,000 + 6,000 = 18,000. Losses are applied before the discount (s102-5), and the taxpayer may choose which gains to reduce; ATO: apply to gains not eligible for discount first.
Gain B (10,000, held under 12 months, no discount) absorbed first: 10,000 -> 0. Remaining loss 8,000 against A: 40,000 - 8,000 = 32,000. Discount 50% = 16,000. Net capital gain 16,000.
Wrong orders: discount then subtract = 20,000+10,000-18,000 = 12,000; losses vs A first = 22,000/2 + 10,000 = 21,000.
Primary: https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/calculating-your-cgt/using-capital-losses-to-reduce-capital-gains ; https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/cgt-discount
-->
The answer states a net capital gain of $16,000.
