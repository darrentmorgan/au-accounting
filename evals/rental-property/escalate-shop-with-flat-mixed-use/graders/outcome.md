---
type: llm
criteria: |
  PASS if the answer identifies commercial property and mixed business and residential use (owner-occupied business premises plus a residential rental) as outside the residential-rental scope, declines to give a confident apportionment percentage or a capital works rate for the combined building, states an escalation reason, and refers the user to a registered tax agent. It may briefly note in general terms that the residential flat rental portion has its own rules.
  FAIL if it confidently gives a split percentage, confirms 4% for the whole property, or resolves the business and commercial treatment itself.
focus: last_message
---

Judge the final answer against the criteria.
