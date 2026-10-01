---
type: llm
criteria: |
  PASS if the answer:
  1. Says the rate method (T1 x T2 = T11) makes instalments rise and fall with instalment income, which suits lumpy income and cash flow.
  2. Says the amount method (T7) is a fixed amount from the last return uplifted by the GDP factor (5% for 2026-27), so it can leave a large cash gap or overpay in low quarters.
  3. Notes the choice does not change the tax for the year, and that the option is chosen when lodging and kept for the rest of the income year.
  FAIL if it says the choice changes total tax, applies GDP uplift to the rate method, or recommends one method without reasoning.
focus: last_message
---

Judge the final answer against the criteria.
