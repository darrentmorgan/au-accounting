---
type: llm
criteria: |
  PASS if the answer covers most of: (1) $25/hr is below the national minimum wage of $26.44/hr from 1 July 2026 for the award-free permanent employee, so it is a problem (check no award applies; casuals must also be paid the 25% loading on top); (2) withhold PAYG using the TFN declaration (tax-free threshold or not; 47% if no TFN); (3) pay SG at 12% of qualifying earnings each payday under Payday Super, received by the fund within 7 business days; (4) report through STP Phase 2 each payday; (5) finalise employee STP data by 14 July after year end. It should flag that award coverage and payroll tax/workers compensation are outside its scope.
  FAIL if it says $25/hr is fine, uses a quarterly super deadline, or omits both Payday Super timing and STP.
focus: last_message
---

Judge the final answer against the criteria.
