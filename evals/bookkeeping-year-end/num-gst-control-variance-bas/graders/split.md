---
type: llm
criteria: |
  PASS if the answer attributes $1,150 to the GST collected (sales, 1A) side (ledger higher than BAS) and $400 to the GST paid (purchases, 1B) side (ledger lower than BAS), and recommends investigating the differences or a BAS revision/adjustment rather than ignoring them.
  FAIL if the split is wrong or missing.
focus: last_message
---

Judge the final answer against the criteria.
