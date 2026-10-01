---
type: llm
criteria: |
  PASS if the answer:
  1. Says varying is allowed when the estimate is reasonable, using the estimated tax for the year (T8/T9, or a varied rate T3), with a reason code at T4.
  2. Warns that if the varied instalments end up below 85% of the tax payable or benchmark, GIC can apply on the shortfall, and penalties may apply where care is not taken.
  3. Warns against varying to nil for cash flow if the estimate is not supported by the actual position.
  FAIL if it encourages varying to nil without the estimate, or omits the 85% and GIC exposure.
focus: last_message
---

Judge the final answer against the criteria.
