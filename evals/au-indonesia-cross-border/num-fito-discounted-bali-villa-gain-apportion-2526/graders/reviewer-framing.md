---
type: regex
pattern: 'registered\s+tax\s+agent|registered\s+agent|tax\s+agent'
flags: i
target: last_message
---

<!--
CONVENTIONS section 8: every working paper ends with a review line naming a registered tax agent. This lenient regex only checks that the answer frames itself for agent review; the strict wording is checked in num-working-paper-dividend-fito-2526.
-->
The answer must frame the output for review by a registered tax agent.

<!-- Orchestrator 2026-09-30: inline (?i)/(?is) flag removed (the eval regex engine rejects it and the grader crashed); case-insensitivity moved to `flags: i`. Expectation unchanged. -->
