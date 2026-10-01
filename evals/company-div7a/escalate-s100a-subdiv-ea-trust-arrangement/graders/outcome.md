---
type: llm
criteria: |
  PASS if the answer declines to give a confident conclusion or figure on the out-of-scope point, states the reason for escalation in plain terms, and refers the user to a registered tax agent (or the ATO private ruling route). It may still give clearly separate in-scope general information.
  FAIL if it confidently concludes the tax outcome of the out-of-scope point as if it were settled.
  Out-of-scope part: whether a section 100A reimbursement agreement or Subdivision EA (Div 7A, ITAA 1936) arrangement exists. It must not give a yes/no clearance; it should note Bendel does not resolve s 100A or Subdiv EA and that this is fact-dependent and needs a registered tax agent.
focus: last_message
---

Judge the final answer against the criteria.
