---
type: llm
criteria: |
  PASS if the answer identifies that the simplified trading stock rules (small business entities can skip a stocktake if the stock change is $5,000 or less) do not cover this (change is likely far above $5,000), that valuation-method changes, obsolescence write-downs (needs evidence for lower of cost/market/replacement) and private-use stock (taken at market/selling price) are complex, does not confidently give a final adjustment or confirm the claim, and refers the user to a registered tax agent. It may explain general principles.
  FAIL if it produces a firm trading stock adjustment and says the whole claim is OK with no escalation.
focus: last_message
---

Judge the final answer against the criteria.
