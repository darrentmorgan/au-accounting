---
type: regex
pattern: '(?<![\d,])\$?\s?2,?989(?:\.\d{1,2})?(?![\d,])'
target: last_message
---

<!--
Eligible service period 1 Apr 2026 to 30 Sep 2027 = 365 (to 31 Mar 2027) + 183 (1 Apr to 30 Sep 2027) = 548 days. Longer than 12 months, so the 12-month rule fails and the deduction is apportioned: A x B/C. Days in 2025-26 (1 Apr to 30 Jun 2026) = 30+31+30 = 91. 18,000 x 91/548 = 2,989.05. Remainder 15,010.95 is deductible over 2026-27 (365 days = 11,989.05) and 2027-28 (1 Jul to 30 Sep 2027 = 92 days = 3,021.90); 91+365+92 = 548.
Primary source: https://www.ato.gov.au/forms-and-instructions/deductions-for-prepaid-expenses-2026 (Tom Pty Ltd example uses the same formula).
-->
The answer states a 2025-26 deduction of about $2,989.
