---
type: regex
pattern: '(?<![\d,.])\$?\s?24\.5\s?(?:m\b|million)|24,500,000'
target: last_message
---

<!--
Corporations Act s45A tests use consolidated figures (company and entities it controls), at least two of: revenue $50m or more, gross assets $25m or more, 100 or more employees. Consolidated revenue = 41 + 12 - 3 = 50m (test met, 'or more'). Consolidated gross assets = 22 + 4 - 1.5 = 24.5m (below 25m, not met). Employees = 60 + 38 = 98 (below 100, not met). Only one test met, so SMALL proprietary.
Primary source: https://asic.gov.au/regulatory-resources/financial-reporting-and-audit/preparers-of-financial-reports/are-you-a-large-or-small-proprietary-company ; thresholds from 1 July 2019 per Corporations Amendment (Proprietary Company Thresholds) Regulations 2019.
-->
The answer states consolidated gross assets of $24.5m.
