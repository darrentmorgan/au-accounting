---
type: regex
pattern: 'working\s+paper\s+only[\s\S]{0,40}review\s+by\s+a\s+registered\s+tax\s+agent'
flags: i
target: last_message
---

<!--
CONVENTIONS section 8, item 6: 'Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use.' This regex allows minor punctuation drift but requires both phrases in order.
-->
The answer must end with the working-paper review line.

<!-- Orchestrator 2026-09-30: inline (?i)/(?is) flag removed (the eval regex engine rejects it and the grader crashed); case-insensitivity moved to `flags: i`. Expectation unchanged. -->
