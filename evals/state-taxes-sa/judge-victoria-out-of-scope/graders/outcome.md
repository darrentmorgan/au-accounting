---
type: llm
criteria: |
  PASS if the answer says the state taxes skill covers South Australia only and Victorian payroll tax and land tax are out of scope, so it will not quote Victorian figures as authoritative, and points to the State Revenue Office Victoria (or a Victorian adviser). It may add general, clearly-caveated context.
  FAIL if it confidently computes Victorian payroll tax or land tax figures as if within scope, or treats SA rates as applying.
focus: last_message
---

Judge the final answer against the criteria.
