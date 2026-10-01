---
type: llm
criteria: |
  PASS only if all hold:
  1. It concludes the crypto was a personal use asset (bought and spent within days on personal items) and that the capital gain of about $70 (720 less 650) is disregarded because the first element of cost base is at or below the personal use asset threshold, so nothing is taxable.
  2. It does not say the $70 is taxable and does not apply a discount to it.
  3. It notes the spend is still a disposal for CGT purposes (the exemption disregards the gain, it does not make the spend a non-event) and/or suggests keeping records of the purchase and spend.
  FAIL if it treats the $70 gain as taxable, or says the spend is not a disposal at all.
focus: last_message
---

<!--
ITAA 1997 s 108-20(2): personal use asset; s 118-10(3): gain disregarded if first element of cost base is $10,000 or less (individual.personal_use_asset_cgt_exempt_max_cost = 10000 VERIFIED); s 102-23: a CGT event still happens when the gain is disregarded.
ATO PUA page (https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/crypto-asset-as-a-personal-use-asset): acquired and used within a short time to buy personal items is more likely personal use (its example is $270 of crypto spent on concert tickets the same day). The facts deliberately avoid the ATO 'rare situations' that defeat PUA (converting to AUD/other crypto first, gift cards, prepaid cards, payment gateways) by paying the shop directly.
Proceeds = market value of the goods received 720 (s 116-20(1)(b)); cost base 650; gain 70; disregarded. Amount well under the threshold, so no boundary issue.
-->
Judge the final answer against the criteria.
