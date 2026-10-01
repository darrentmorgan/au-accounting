---
type: regex
pattern: '\bAU-(?:CRYPTO-005|RES-004)\b'
target: last_message
---

<!--
AU-CRYPTO-005 trigger: holder is a foreign resident or is ceasing or becoming an Australian resident, or an overseas-source question arises (fires on: moved to Bali, assumes non-resident, CGT event I1 risk). AU-RES-004 trigger: residency indicators conflict or point both ways (fires on: wife and kids and a rented flat still in Adelaide). Either is correct.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-CRYPTO-005 or AU-RES-004).
