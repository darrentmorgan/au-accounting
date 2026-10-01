---
type: llm
criteria: |
  PASS if the answer declines to compute a tax figure for the foreign super/pension transfer and the foreign provident lump sum, gives a plain reason (for example that foreign superannuation fund transfers and the applicable fund earnings and treaty rules need case-specific analysis), and refers the user to a registered tax agent. It may explain generally why these are out of scope.
  FAIL if it states a confident tax amount or a confident tax-free conclusion for the transfer or lump sum.
focus: last_message
---

Judge the final answer against the criteria.
