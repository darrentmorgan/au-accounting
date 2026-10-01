---
type: llm
criteria: |
  PASS only if the answer gives a foreign income tax offset of $940 (the full foreign tax paid) and does not reduce it to a computed limit (for example about $800 or $640).
  FAIL if it caps the offset below $940, or claims more than $940.
focus: last_message
---

Judge the final answer against the criteria.
