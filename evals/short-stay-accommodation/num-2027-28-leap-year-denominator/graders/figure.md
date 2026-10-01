---
type: regex
pattern: '(?<![\d,.])\$?\s?31,95[67](?:\.\d{1,2})?(?![\d,])'
target: last_message
---

<!--
Working: 2027-28 runs 1 Jul 2027 to 30 Jun 2028 and includes 29 Feb 2028, so it has 366 days (calendar fact; no stored figure needed).
1. Share = (225 + 119) / 366 = 344/366 = 93.9891%.
2. Deductible ownership costs = 34,000 x 344/366 = $31,956.28. Private portion = $2,043.72.
Trap: dividing by 365 gives $32,043.84. The ATO examples use 365 because they are non-leap years; PCG 2026/2 para 14 defines the comparison as days in the income year the property is owned, so a leap year uses 366.
Net result is positive in this scenario so the 2027-28 residential dwelling loss quarantine (ITAA 1997 s 26-155) does not bite; a good answer may note that it applies only to an excess of deductions over income for dwellings that are not grandfathered.
Tolerance: 31,956 or 31,957 accepted.
Uncertainty: the calculators may refuse a 2027-28 year while 2027-28 rates data or the AU-RENT-002 trigger is unresolved; the arithmetic needs no stored figure, so the expectation stands.
Sources: PCG 2026/2 para 14 https://www.ato.gov.au/law/view/document?docid=COG%2FPCG20262%2FNAT%2FATO%2F00001
-->
The answer states about $31,956 (344/366 of $34,000), using 366 days.
