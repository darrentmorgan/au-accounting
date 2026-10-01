---
type: regex
pattern: '(?<![\d,.])9,?685(?!\d|,\d)'
target: last_message
---

<!--
2026-27, resident individual, event before 1 Jul 2027 so the 50% discount still applies (key cgt.discount_individual_trust = 0.5, VERIFIED).
1. Swap is CGT event A1 on 20 Aug 2026 (ITAA 1997 s 104-10; ATO swap page https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/crypto-to-crypto-exchange-or-swap).
2. Capital proceeds = AUD market value of what is received = $71,500 (s 116-20(1)(b)).
3. Cost base: first element $52,000 (money paid, s 110-25(2)) + incidental cost $130 (s 110-35) = $52,130. No swap fee, so nothing to add.
4. Gain = 71,500 - 52,130 = 19,370.
5. Held 12 Feb 2025 to 20 Aug 2026: over 12 months excluding acquisition and event days (s 115-25; ATO discount page https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/cgt-discount). Discount 50%: 19,370 x 0.5 = 9,685.
6. Net capital gain = 9,685.
Wrong answers: no tax until AUD (0); gain from 52,000 only (19,500 -> 9,750); no discount (19,370).
-->
The answer states a net capital gain of $9,685 (discounted gain of $19,370 halved).
