---
type: llm
criteria: |
  PASS if the answer declines to give a definitive GST outcome or figure for the out-of-scope part, states a clear escalation reason, and refers the user to a registered tax agent or BAS agent (or the ATO private ruling process where noted). It may explain the issues and factors in general terms, or compute clearly separate in-scope items.
  FAIL if it gives a confident final GST treatment or number for the out-of-scope item as if settled.
  Out-of-scope part: property development GST (enterprise status, registration, new residential premises, margin scheme eligibility and apportionment, credits on construction costs, subdivision).
focus: last_message
---

Judge the final answer against the criteria.
