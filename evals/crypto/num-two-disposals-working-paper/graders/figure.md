---
type: regex
pattern: '(?<![\d,.])1,?500(?!\d|,\d)'
target: last_message
---

<!--
Both events before 1 Jul 2027, so 50% discount for held over 12 months (cgt.discount_individual_trust, VERIFIED; https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/cgt-discount).
Disposal 1: 4 Jul 2025 to 20 Jul 2026 is over 12 months excluding the acquisition and event days (s 115-25). Gain 5,000 - 3,600 = 1,400; discounted 700.
Disposal 2: 3 Feb 2026 to 8 Aug 2026 is about 6 months, no discount. Gain 2,300 - 1,500 = 800.
Net capital gain = 700 + 800 = 1,500 (no losses to apply first).
Also expect a working-paper framing: the ATO says exchange statements alone are not enough for records (https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/keeping-crypto-records) and the plugin never says 'lodge without review'.
-->
The answer states a net capital gain of $1,500.
