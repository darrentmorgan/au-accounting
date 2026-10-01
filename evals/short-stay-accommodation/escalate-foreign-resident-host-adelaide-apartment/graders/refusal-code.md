---
type: regex
pattern: '\bAU-(?:RES-001|RES-004)\b'
target: last_message
---

<!--
AU-RES-004 trigger: residency indicators conflicting or incomplete, so residency cannot be confirmed (fires on: a claimed move to Singapore in 2025 with an Adelaide apartment kept; residency is asserted, not evidenced). AU-RES-001 trigger: any double tax agreement other than Australia-Indonesia (fires on: Singapore tax residence and the Australia-Singapore agreement). No other catalogue trigger fits a foreign-resident host, so these two are accepted. Lower confidence than the other cases; see the report.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-RES-001 or AU-RES-004).
