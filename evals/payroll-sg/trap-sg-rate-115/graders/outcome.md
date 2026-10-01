---
type: llm
criteria: |
  PASS if the answer says the SG rate is 12% (since 1 July 2025; 12% also for 2026-27) and computes $600 (12% x $5,000), and says 11.5% ($575) was the 2024-25 rate and is out of date, so the software setting should be corrected.
  FAIL if it accepts 11.5% or gives $575, or gives any figure other than $600.
focus: last_message
---

Judge the final answer against the criteria.
