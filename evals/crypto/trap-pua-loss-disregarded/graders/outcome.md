---
type: llm
criteria: |
  PASS only if all hold:
  1. It says the $500 loss on the crypto is disregarded because the crypto was a personal use asset (bought and spent within days on a personal item), so it cannot reduce the share gain.
  2. It gives a net capital gain of $3,000 (no discount, shares held under 12 months).
  FAIL if it nets the $500 loss (net $2,500) or applies a discount to the shares gain.
focus: last_message
---

<!--
ITAA 1997 s 108-20(1): a capital loss from a CGT event on a personal use asset is disregarded (VERIFIED note on individual.personal_use_asset_cgt_exempt_max_cost, https://www.legislation.gov.au/C2004A05138/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_3/document_3.html). ATO PUA page (https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/crypto-asset-as-a-personal-use-asset): acquired and used within a short time to buy personal items is personal use; the facts pay the retailer directly to avoid the ATO's 'rare situations' (gateway, gift card, converting first).
Proceeds 8,500 (market value of goods), cost base 9,000, loss 500 disregarded. Shares: 3,000 gain held 8 months, no discount. Net capital gain 3,000.
Wrong: 2,500.
-->
Judge the final answer against the criteria.
