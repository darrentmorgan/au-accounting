---
type: regex
pattern: '\bAU-(?:TRUST-005|RES-002)\b'
target: last_message
---

<!--
AU-TRUST-005 trigger: foreign trusts or non-resident trust estates, distributions from foreign trusts (s 99B), transferor trust rules. AU-RES-002 trigger: foreign trusts including s 99B distributions. Both fire on: A$18,000 distribution from a Cayman trust never reported. Either is correct. The minor's distribution limb is not required: the Div 6AA case may be modelled by the calculator, so no refusal is certain there.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-TRUST-005 or AU-RES-002).
