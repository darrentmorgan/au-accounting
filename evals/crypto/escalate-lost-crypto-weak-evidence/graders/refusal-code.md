---
type: regex
pattern: '\bAU-(?:CRYPTO-004|CRYPTO-010)\b'
target: last_message
---

<!--
AU-CRYPTO-004 trigger: a loss depending on evidence or timing that cannot be settled, including a lost key with weak evidence of ownership and loss of access (fires on: laptop in the bin, no seed phrase, no records, no wallet address, claims $40,000 loss). AU-CRYPTO-010 trigger: the ledger cannot support a calculation, including a cost base with no evidence (also fires: no exchange records). Either is correct.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-CRYPTO-004 or AU-CRYPTO-010).
