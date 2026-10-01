---
type: regex
pattern: '\bAU-(?:CRYPTO-003)\b'
target: last_message
---

<!--
AU-CRYPTO-003 trigger: an airdrop outside draft TR 2026/D1, listing an initial allocation airdrop made before a final ruling (fires on: first distribution of a brand new token, before it traded, received December 2025, investor not in business). AU-CGT-005 does not fit because it covers airdrops received in business and this holder is not in business.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-CRYPTO-003).
