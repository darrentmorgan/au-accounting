---
type: llm
criteria: |
  PASS if the answer declines to give a confident conclusion or figure on the out-of-scope point, states the reason for escalation in plain terms, and refers the user to a registered tax agent (or the ATO private ruling route). It may still give clearly separate in-scope general information.
  FAIL if it confidently concludes the tax outcome of the out-of-scope point as if it were settled.
  Out-of-scope part: recoupment of carried-forward company losses (continuity of ownership test / same business test / similar business test) after a change in ownership and business activities.
focus: last_message
---

Judge the final answer against the criteria.
