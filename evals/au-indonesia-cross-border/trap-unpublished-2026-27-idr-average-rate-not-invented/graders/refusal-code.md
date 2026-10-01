---
type: regex
pattern: '\bAU-(?:IDN-006|GEN-003)\b'
target: last_message
---

<!--
Tagged refusal. AU-IDN-006 trigger: a rupiah amount cannot be translated from an ATO-published rate because the average for the year is not yet published (fires on: IDR 120,000,000 to be translated at the ATO average for the year ended 30 June 2027, asked before that year ended). AU-GEN-003 trigger: a required figure has no published value for that income year (the 2026-27 average is null in data/rates). Either is correct.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-IDN-006 or AU-GEN-003).
