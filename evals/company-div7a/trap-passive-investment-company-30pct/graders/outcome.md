---
type: llm
criteria: |
  PASS only if all hold:
  1. It says the company is NOT a base rate entity because more than 80% of its assessable income is base rate entity passive income (dividends, interest, rent, etc.), even though turnover is under $50m.
  2. It applies the 30% corporate rate: tax of $30,000 on $100,000 taxable income (not $25,000).
  FAIL if it applies 25% or says the company is a base rate entity.
focus: last_message
---

Judge the final answer against the criteria.
