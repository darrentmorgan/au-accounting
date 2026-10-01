---
type: llm
criteria: |
  Background: Div 296 (from 2026-27) has a large super balance threshold of $3m and very large threshold of $10m. For 2026-27 only the TSB at 30 June 2027 is tested. It applies 15% to the portion of earnings attributable to the part of TSB above $3m (extra 10% above $10m); it is not a tax on the whole balance.
  PASS if the answer says a $2.8m balance at 30 June 2026 is below the $3m threshold and Div 296 does not apply on that basis, but that the 2026-27 test is the TSB at 30 June 2027 (so growth or contributions could take it over $3m), and that it taxes only earnings on the excess portion, not the whole balance.
  FAIL if it says Div 296 applies to the $2.8m balance, says it is charged on the whole balance, or says the user is definitely exempt for 2026-27 without noting the 30 June 2027 test.
focus: last_message
---

Judge the final answer against the criteria.
