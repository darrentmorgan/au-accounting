---
type: llm
criteria: |
  PASS if the answer says the GDP adjustment applies only to the instalment amount method (quarterly or twice-yearly payers using T7), not to the rate method, so the rate stays 12% (T11 = T1 x T2) with no 5% uplift.
  FAIL if it agrees that the rate should be uplifted to 12.6%, or applies GDP to instalment income under the rate method.
focus: last_message
---

Judge the final answer against the criteria.
