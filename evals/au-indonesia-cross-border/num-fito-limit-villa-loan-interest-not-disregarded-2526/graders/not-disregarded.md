---
type: llm
criteria: |
  PASS only if the answer gives $3,840 as the offset and does NOT reach the wrong limit of $2,880 (which comes from also ignoring the loan interest deduction in the second calculation). It may explain that debt deductions are only left out for an overseas permanent establishment, and that here only the A$12,000 net rent is removed.
  FAIL if it gives $2,880 or $4,000, or claims the limit is unaffected by the interest.
focus: last_message
---

<!--
Expected working is in the figure grader. Confidence note for the eval author: moderate. s 770-75(4)(b) text read in the ATO legal database on 2026-09-29; 'debt deduction' is defined by reference to ITAA 1997 s 820-40 (dictionary), which the section applies as written.
-->
Judge the final answer against the criteria.
