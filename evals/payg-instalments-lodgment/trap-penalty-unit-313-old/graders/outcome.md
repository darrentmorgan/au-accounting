---
type: llm
criteria: |
  PASS if the answer says $313 is out of date for this failure: the due date (28 July 2026) is after 1 July 2026 so the penalty unit is $364, giving 2 units x $364 = $728. It may mention that $330 applied 7 Nov 2024 to 30 June 2026 and $313 applied before 7 Nov 2024.
  FAIL if it accepts $626, or computes with $313 or $330 (e.g. $660), or omits the unit value in force at the time of the failure.
focus: last_message
---

Judge the final answer against the criteria.
