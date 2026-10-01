---
type: regex
pattern: '\bAU-(?:IDN-001|IDN-002)\b'
target: last_message
---

<!--
AU-IDN-001 trigger: a PE or fixed base determination the treaty text does not settle, naming a regularly available desk or co-working space in Indonesia (fires on: three staff on a Canggu co-working annual membership, yes/no PE asked). AU-IDN-002 trigger: a question about Indonesian domestic tax (fires on: how much Indonesian tax will the company pay). Either is a correct hand-off code.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-IDN-001 or AU-IDN-002).
