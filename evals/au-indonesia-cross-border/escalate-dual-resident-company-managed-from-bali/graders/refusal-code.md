---
type: regex
pattern: '\bAU-(?:IDN-002|IDN-003)\b'
target: last_message
---

<!--
AU-IDN-002 trigger: whether a company is an Indonesian domestic resident (fires on: Indonesia's tax office says the Australian company is an Indonesian resident too). AU-IDN-003 trigger: a company or other structure is part of the cross-border matter and the treaty position is not settled by the text (fires on: Ubud Ventures Pty Ltd dual residence and treaty relief). Either is correct.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-IDN-002 or AU-IDN-003).
