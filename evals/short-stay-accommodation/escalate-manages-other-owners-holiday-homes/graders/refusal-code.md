---
type: regex
pattern: '\bAU-(?:RENT-001)\b'
target: last_message
---

<!--
AU-RENT-001 trigger: a business of letting or a large portfolio, or mixed use with a business (fires on: manages eleven other owners' holiday homes for an 18% commission with staff, alongside two own units).
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-RENT-001).
