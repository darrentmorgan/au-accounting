---
type: llm
criteria: |
  PASS only if all hold:
  1. It corrects the user: the benchmark rate for the income year ended 30 June 2027 is 8.77% (RBA indicator lending rate published 5 June 2026), not 8.37% (which is the 2025-26 rate).
  2. It explains the rate is fixed per income year from the RBA rate last published before the year starts.
  FAIL if it accepts 8.37% for 2026-27, or gives some other rate for 2026-27.
focus: last_message
---

Judge the final answer against the criteria.
