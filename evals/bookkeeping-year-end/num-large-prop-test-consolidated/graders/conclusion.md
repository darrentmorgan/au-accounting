---
type: llm
criteria: |
  PASS if the answer concludes the company is small proprietary because only one of the three tests (revenue of $50m, met exactly) is satisfied, with consolidated assets $24.5m and 98 employees both below threshold, and it notes small proprietary companies are generally exempt from lodging financial reports unless directed (for example by ASIC or 5 percent of members).
  FAIL if it concludes large proprietary, or uses unconsolidated or non-eliminated figures.
focus: last_message
---

Judge the final answer against the criteria.
