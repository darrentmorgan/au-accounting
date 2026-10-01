---
type: regex
pattern: '(?<![\d,.])16,?000(?!\d|,\d)'
target: last_message
---

<!--
ATO loss or theft page (https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/loss-or-theft-of-crypto-assets): a capital loss is claimable for lost or stolen crypto if you can evidence ownership and loss of access; something recoverable is not lost. ITAA 1997 s 104-20: CGT event C1 on loss or destruction; time of event is compensation first received or, if none, when the loss is discovered (14 Aug 2026, income year 2026-27). Capital proceeds nil, reduced cost base 36,000 -> capital loss 36,000.
Losses offset the 20,000 share gain before any discount (s 102-5): 20,000 - 36,000 -> net capital gain 0; unused loss 36,000 - 20,000 = 16,000 carried forward (net capital losses cannot reduce other income; s 102-10).
Answer: net capital gain nil; carry forward 16,000.
Wrong: discounting the share gain first (10,000) leaving a loss of 26,000; deducting the loss from salary; no loss because coins still exist on-chain.
-->
The answer states a net capital loss of $16,000 carried forward (net capital gain nil).
