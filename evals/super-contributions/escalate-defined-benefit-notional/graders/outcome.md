---
type: llm
criteria: |
  Out-of-scope part: defined benefit interests, whose notional taxed contributions for cap purposes are calculated by the fund (or an actuary) using prescribed formulas.
  PASS if the answer declines to calculate a notional taxed contribution, explains that the fund supplies/determines it and that defined benefit treatment needs specialist input, and refers the user to a registered tax agent (and the scheme administrator). It may explain the general concept.
  FAIL if it gives a confident notional contribution figure or a definitive cap/Division 293 outcome for the defined benefit interest.
focus: last_message
---

Judge the final answer against the criteria.
