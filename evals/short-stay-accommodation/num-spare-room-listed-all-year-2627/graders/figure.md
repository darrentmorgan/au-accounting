---
type: regex
pattern: '(?<![\d,.])\$?\s?18,33[12](?:\.\d{1,2})?(?![\d,])'
target: last_message
---

<!--
Working (2026-27, 365 days):
1. Area share (PCG 2026/2 para 29) = (A + B/2) / C = (14 + 46/2) / 120 = 37/120 = 30.8333%.
2. Time share: a room in your own home has zero held days even if the listing stays live (PCG 2026/2 paras 15 and 41; ATO "Renting out part of a home", Jane example). So days = 128 only; share = 128/365 = 35.0685%.
3. Combined = 37/120 x 128/365 = 4,736/43,800 = 10.8128%.
4. Deductible ownership costs = 22,000 x 10.8128% = $2,378.81.
5. Direct costs 1,050 + 1,280 = $2,330, deductible in full.
6. Total deductions = $4,708.81. Net rental income = 23,040 - 4,708.81 = $18,331.19.
A room in the owner's home is not a holiday home (never used for the owner's holidays), so s 26-50 is not in play. Trap: treating the 237 unbooked nights as held (365/365 x 30.8333% = 30.83%, deduction $6,783.33, net $13,926.67).
Tolerance: 18,331 or 18,332 (rounding the factor first) accepted.
Sources: PCG 2026/2 https://www.ato.gov.au/law/view/document?docid=COG%2FPCG20262%2FNAT%2FATO%2F00001
-->
The answer states net rental income of about $18,331.
