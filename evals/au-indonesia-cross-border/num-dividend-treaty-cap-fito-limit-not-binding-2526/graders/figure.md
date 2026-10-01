---
type: regex
pattern: '(?<![\d,])\$?\s?3,?750(?:\.\d{2})?(?!\d|,\d)'
target: last_message
---

<!--
Cross-check of the offset limit: ITAA 1997 s 770-75(2) (https://www.ato.gov.au/law/view/document?docid=PAC%2F19970038%2F770-75) and ATO FITO guide (https://www.ato.gov.au/forms-and-instructions/foreign-income-tax-offset-rules-guide-2026/calculate-your-fito-or-offset-limit). Limit = greater of $1,000 and (tax payable incl. Medicare levy) less (same tax with the foreign-taxed amount, and related non-debt deductions, left out). Resident scale 2025-26 (https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents): 18,201-45,000 16c; 45,001-135,000 $4,288 + 30c over 45,000. Medicare levy 2% in full because taxable income is above the single upper threshold (data/rates/2025-26.yaml medicare.low_income_single_upper = 35,013, VERIFIED). Single with private hospital cover, so no Medicare levy surcharge (first surcharge tier starts above 101,000).
Australia-Indonesia agreement Art 10(2) (https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf): source-country tax on dividends may not exceed 15 per cent of the gross amount. ATO FITO guide (https://www.ato.gov.au/forms-and-instructions/foreign-income-tax-offset-rules-guide-2026/when-a-fito-applies): only tax correctly imposed under the foreign law AND the treaty counts; the balance is sought from the foreign tax authority.
Step 1, creditable tax: 15% x 25,000 = 3,750 (the other 1,250 of the 5,000 withheld is above the cap and does not count).
Step 2, 3,750 is above the default 1,000, so compute the limit.
Step 3, tax with the dividend: taxable 120,000 -> 4,288 + 0.30 x (120,000 - 45,000) = 4,288 + 22,500 = 26,788; Medicare 2% x 120,000 = 2,400; total 29,188.
Step 4, tax without the dividend: taxable 95,000 -> 4,288 + 0.30 x 50,000 = 19,288; Medicare 1,900; total 21,188.
Step 5, limit = 29,188 - 21,188 = 8,000. Offset = lesser of 3,750 and 8,000 = 3,750. (No LITO at this income; offsets are ignored for the limit in any case.)
Step 6, tax payable after the offset = 29,188 - 3,750 = 25,438 (not asked, shown as a cross-check).
Wrong answers: 5,000 (full withholding), 1,250 (the excess mistaken for the credit), 8,000 (the limit mistaken for the offset). Not a copy of the residency-cross-border case (that one is 100,000 taxable, 8,000 dividend).
-->
The answer states the offset of $3,750.
