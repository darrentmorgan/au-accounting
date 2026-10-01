---
type: llm
criteria: |
  PASS if the answer says the income requirement (taxable income + reportable fringe benefits + reportable super contributions + total net investment loss, under $250,000) is not met at $260,000, so passing the assessable income test does not let the loss be offset; the $15,000 loss is deferred, unless the Commissioner's discretion applies (which is limited and needs escalation to a registered tax agent). 
  FAIL if it says the loss can be offset because the assessable income test is passed, or if it ignores the $250,000 income requirement.
focus: last_message
---

Judge the final answer against the criteria.
