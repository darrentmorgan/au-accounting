---
type: regex
pattern: '\bAU-(?:RENT-005)\b'
target: last_message
---

<!--
AU-RENT-005 trigger: rental property located outside Australia (foreign-source rent, foreign tax offsets, local tax law) (fires on: Ubud villa let on Airbnb by an Adelaide resident, Indonesian tax paid, credit and depreciation and interest asked). AU-SS-002 (SERR scope for overseas property) is not required because the prompt does not ask about platform reporting.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-RENT-005).
