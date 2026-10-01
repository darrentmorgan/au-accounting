---
type: regex
pattern: '(?<![\d,.])900(?!\d|,\d)'
target: last_message
---

<!--
ITAA 1997 s 118-10(3): a gain on a personal use asset is disregarded only if the first element of cost base is $10,000 or less (data/rates key individual.personal_use_asset_cgt_exempt_max_cost = 10000, VERIFIED, https://www.legislation.gov.au/C2004A05138/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_3/document_3.html).
Even if the crypto is a personal use asset (acquired and spent within days on personal goods; ATO PUA page https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/crypto-asset-as-a-personal-use-asset), the first element is $14,000, which is above the threshold, so the gain is NOT disregarded.
Event A1 on 15 Sep 2026; proceeds = market value of what is received = 14,900 (s 116-20(1)(b)). Gain = 14,900 - 14,000 = 900.
Held 2 weeks: no discount. Net capital gain 900.
Wrong: nil because 'personal use crypto is exempt' (ignores the cost-base cap).
-->
The answer states a taxable capital gain of $900 (no discount, personal use exemption not available above the cost-base threshold).
