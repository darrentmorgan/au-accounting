---
type: regex
pattern: '\bAU-(?:IDN-006|GEN-003)\b'
target: last_message
---

<!--
AU-IDN-006 trigger: a rupiah amount cannot be translated from an ATO-published rate because the year average is not yet published (fires on: 30 September 2026, IDR 300,000,000 rent to be converted at the ATO average for 2026-27). AU-GEN-003 trigger: a required figure has no published value for that income year (fires on: au_indonesia.fx_idr_per_aud_average_year_to_30_jun is null for 2026-27). Either is correct; the existing outcome grader already says AU-GEN-003 may be cited.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-IDN-006 or AU-GEN-003).
