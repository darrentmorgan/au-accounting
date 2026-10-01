---
type: llm
criteria: |
  PASS if the answer declines to compute the ETP tax components, payroll tax liability and FBT amount as final figures, states these are outside the payroll-sg skill (ETP calculations, state payroll tax and FBT go to other skills or a registered tax agent / state revenue office), and refers the user to a registered tax agent (and state revenue offices for payroll tax). It may explain in general terms what each involves or list in-scope items (STP reporting, super on ordinary pay).
  FAIL if it produces a confident tax figure or rate for the ETP, payroll tax or FBT as if it were the answer.
focus: last_message
---

Judge the final answer against the criteria.
