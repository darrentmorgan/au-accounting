---
type: regex
pattern: '\bAU-(?:RENT-001|FBT-006)\b'
target: last_message
---

<!--
AU-RENT-001 trigger: property held by a company, outside the individual passive-investor model (fires on: company owns the Aldinga beach house). AU-FBT-006 trigger: whether a shareholder-director is an employee or the benefit is provided in respect of employment is doubtful (fires on: directors and their kids using the house). Either is correct.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-RENT-001 or AU-FBT-006).
