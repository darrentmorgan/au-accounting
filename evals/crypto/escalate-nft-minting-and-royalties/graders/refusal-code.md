---
type: regex
pattern: '\bAU-(?:CRYPTO-006|CRYPTO-001)\b'
target: last_message
---

<!--
AU-CRYPTO-006 trigger: NFTs including creation, minting, royalties and marketplace selling (fires on: mints and sells NFTs, earns resale royalties, asks GST and CGT versus income). AU-CRYPTO-001 trigger: facts pointing to a business or profit-making commercial transactions (regular creation and sale of NFTs for about $30,000 may point to a business). Either is correct.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-CRYPTO-006 or AU-CRYPTO-001).
