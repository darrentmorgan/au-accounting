---
type: regex
pattern: '(?<![\d,.])11,?150(?!\d|,\d)'
target: last_message
---

<!--
Crypto (including stablecoins) is a CGT asset, not money or foreign currency for tax (TD 2014/26, TD 2014/25; ITAA 1997 s 995-1 definition of foreign currency excludes digital currency; ATO https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/crypto-to-crypto-exchange-or-swap).
Disposal 1, BTC -> USDT on 2 Sep 2026 (A1): proceeds 52,000; cost base 30,000; gain 22,000; held over 12 months (3 Jun 2024 to 2 Sep 2026), discount 50% = 11,000.
Disposal 2, USDT -> AUD on 20 Sep 2026 (A1): proceeds 52,150; cost base 52,000 (market value of BTC given up); gain 150; held 18 days, no discount = 150.
Net capital gain = 11,000 + 150 = 11,150.
Wrong: treating only the AUD conversion as the event: 52,150 - 30,000 = 22,150, discount 11,075. Wrong: no tax until AUD.
-->
The answer states a net capital gain of $11,150 (two disposals, discount only on the BTC leg).
