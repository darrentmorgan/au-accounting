---
type: regex
pattern: '(?<![\d,.])9,?000(?!\d|,\d)'
target: last_message
---

<!--
Capital losses reduce capital gains before the discount, and the taxpayer chooses which gains to reduce; applying them first to gains that get no discount minimises the result (ATO losses page https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/calculating-your-cgt/using-capital-losses-to-reduce-capital-gains; ITAA 1997 s 102-5; discount s 115-100).
Total losses = 9,500 + 2,500 = 12,000.
SOL gain 6,000 (held under 12 months, no discount): 6,000 - 6,000 = 0. Remaining loss 6,000 against ETH: 24,000 - 6,000 = 18,000. Discount 50%: 9,000. Net capital gain 9,000.
Wrong orders: all 12,000 against ETH first = (24,000 - 12,000)/2 + 6,000 = 12,000; discount first then subtract = 12,000 + 6,000 - 12,000 = 6,000 (wrong: losses are not discounted).
-->
The answer states a net capital gain of $9,000.
