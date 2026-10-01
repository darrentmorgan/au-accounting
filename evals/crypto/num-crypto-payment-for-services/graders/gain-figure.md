---
type: regex
pattern: '(?<![\d,.])350(?!\d|,\d)'
target: last_message
---

<!--
Swap 9 Sep 2026 is A1: proceeds = AUD market value of SOL received = 11,150; cost base 10,800; gain 350. Held 34 days, no discount. Net capital gain 350 (ATO swap page https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/crypto-to-crypto-exchange-or-swap; services page https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/crypto-assets-payments-relating-to-employment-or-services).
Wrong: gain of 11,150 (double taxes the 10,800).
-->
The answer states a net capital gain of $350 on the swap.
