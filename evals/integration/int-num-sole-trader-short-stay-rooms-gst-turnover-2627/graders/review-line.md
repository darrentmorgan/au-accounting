---
type: regex
pattern: 'working\s+paper\s+only[\s\S]{0,40}review\s+by\s+a\s+registered\s+(?:tax\s+agent|bas\s+agent)'
flags: i
target: last_message
---

<!-- CONVENTIONS section 8, item 6: the review line ("registered tax agent (or BAS agent for BAS matters)") must close every working paper. -->
The answer must end with the working-paper review line: working paper only, review by a registered tax agent (or BAS agent for BAS matters) before use.
