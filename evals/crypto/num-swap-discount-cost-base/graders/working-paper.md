---
type: regex
pattern: 'working paper only[^a-z]{0,12}review by a registered tax agent'
flags: i
target: last_message
---

<!-- CONVENTIONS section 8, output contract item 6: the review line must close every working paper. -->
The answer ends with the review line: working paper only, review by a registered tax agent before use.

<!-- Orchestrator 2026-09-30: inline (?i)/(?is) flag removed (the eval regex engine rejects it and the grader crashed); case-insensitivity moved to `flags: i`. Expectation unchanged. -->
