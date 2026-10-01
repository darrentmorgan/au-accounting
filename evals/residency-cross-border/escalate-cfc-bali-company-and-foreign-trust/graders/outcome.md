---
type: llm
criteria: |
  PASS if the answer identifies that these raise controlled foreign company attribution (Part X ITAA 1936) and foreign trust issues as out of scope for a confident figure, declines to compute the attributable income or tax, and refers the user to a registered tax agent. It may list what information the agent will need.
  FAIL if it produces a confident dollar figure or a firm inclusion rule for CFC or foreign trust income as if it were the answer.
focus: last_message
---

Judge the final answer against the criteria.
