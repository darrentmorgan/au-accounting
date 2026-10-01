---
type: regex
pattern: '(?<![\d,])\$?\s?18,356(?:\.\d{1,2})?(?![\d,])'
target: last_message
---

<!--
2025-26 has 365 days. PCG 2026/2 time-based method: (days used to produce income + days held available on commercial terms) / days in period = (120 + 215) / 365 = 335/365. Owner private days (30) are excluded. Per PCG 2026/2 example 3 (Gail and Craig, 30 private days) agent commission and advertising are fully deductible and not apportioned.
Apportioned other costs = 20,000 x 335/365 = 18,356.16. Total including agent fees = 20,356.16.
The prompt asks for the amount excluding agent/advertising fees, so the key figure is 18,356. A trap answer uses 120/365 (= 6,575).
Primary source: https://www.ato.gov.au/law/view/document?docid=COG%2FPCG20262%2FNAT%2FATO%2F00001
-->
The answer states the apportioned ownership-cost deduction of about $18,356.
