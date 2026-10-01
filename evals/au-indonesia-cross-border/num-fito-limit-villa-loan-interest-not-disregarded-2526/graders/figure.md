---
type: regex
pattern: '(?<![\d,])\$?\s?3,?840(?:\.\d{2})?(?!\d|,\d)'
target: last_message
---

<!--
Cross-check of the offset limit: ITAA 1997 s 770-75(2) (https://www.ato.gov.au/law/view/document?docid=PAC%2F19970038%2F770-75) and ATO FITO guide (https://www.ato.gov.au/forms-and-instructions/foreign-income-tax-offset-rules-guide-2026/calculate-your-fito-or-offset-limit). Limit = greater of $1,000 and (tax payable incl. Medicare levy) less (same tax with the foreign-taxed amount, and related non-debt deductions, left out). Resident scale 2025-26 (https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents): 18,201-45,000 16c; 45,001-135,000 $4,288 + 30c over 45,000. Medicare levy 2% in full because taxable income is above the single upper threshold (data/rates/2025-26.yaml medicare.low_income_single_upper = 35,013, VERIFIED). Single with private hospital cover, so no Medicare levy surcharge (first surcharge tier starts above 101,000).
ITAA 1997 s 770-75(4) (https://www.ato.gov.au/law/view/document?docid=PAC%2F19970038%2F770-75): the second tax calculation assumes (a) the foreign-taxed amount is left out of assessable income and (b) no entitlement to (i) debt deductions attributable to an overseas permanent establishment, or (ii) deductions OTHER THAN debt deductions reasonably related to that foreign amount. So interest on a personal loan for the villa (a debt deduction, not attributable to an overseas PE) stays deducted in the second calculation. ATO supplementary return instructions 2026, Q20 (rent): foreign rental debt deductions are claimed at D15, not in the foreign rent worksheet.
Step 1, tax with the rent (taxable 57,000): 4,288 + 0.30 x 12,000 = 7,888; Medicare 1,140; total 9,028.
Step 2, taxable 57,000 - 12,000 net rent = 45,000 (the 3,000 interest deduction stays): tax 4,288 + 0 = 4,288; Medicare 900; total 5,188.
Step 3, limit = 9,028 - 5,188 = 3,840. Offset = lesser of 4,000 and 3,840 = 3,840. 160 lost.
Wrong answer if the interest is also disregarded (step 2 base 48,000 -> 4,288 + 900 = 5,188 + ... = 6,148 with levy 960): limit 2,880. Wrong answer 4,000 if the limit is ignored.
-->
The answer states an offset limit and offset of $3,840.
