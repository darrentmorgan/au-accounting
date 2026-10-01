---
type: regex
pattern: '\bAU-(?:GST-002)\b'
target: last_message
---

<!--
AU-GST-002 trigger: short-stay or serviced accommodation where the answer depends on whether premises are commercial residential premises (s 195-1, GSTR 2012/6), for example hotel-like services (fires on: apartment in a hotel rental pool with an existing management agreement, going-concern GST-free and GST credits asked). AU-GST-001 is for developer and margin scheme positions, which do not apply to an end buyer.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-GST-002).
