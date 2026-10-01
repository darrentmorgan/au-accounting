---
type: regex
pattern: '\bAU-(?:RENT-001)\b'
target: last_message
---

<!--
AU-RENT-001 trigger: property held by a trust, or mixed use with a business, outside the individual passive-investor model; short-stay-accommodation.yaml notes AU-RENT-001 is reused for entity owner and mixed structure (fires on: family trust owns, wife's company operates, borrowing in the husband's name).
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-RENT-001).
