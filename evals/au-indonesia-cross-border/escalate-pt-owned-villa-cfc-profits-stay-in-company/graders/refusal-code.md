---
type: regex
pattern: '\bAU-(?:RES-002|IDN-003)\b'
target: last_message
---

<!--
AU-RES-002 trigger: an Australian resident controlling an offshore company such as an Indonesian PT, and controlled foreign company rules (Part X ITAA 1936) (fires on: 100% owner of PT Sunset Villas, profits retained, no dividends). AU-IDN-003 trigger: an Indonesian company (PT) is part of the matter (also fires). Either is correct.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-RES-002 or AU-IDN-003).
