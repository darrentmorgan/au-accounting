---
type: regex
pattern: '\bAU-(?:IDN-004|IDN-003)\b'
target: last_message
---

<!--
AU-IDN-004 trigger: gain on shares in a company whose assets are principally real property, or a villa held through a company (Art 13(4), MLI Art 9) (fires on: 30% of PT Bukit Estate, which owns land and villas). AU-IDN-003 trigger: an Indonesian company (PT) is part of the matter (also fires). Either is correct; AU-IDN-004 is the more specific.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-IDN-004 or AU-IDN-003).
