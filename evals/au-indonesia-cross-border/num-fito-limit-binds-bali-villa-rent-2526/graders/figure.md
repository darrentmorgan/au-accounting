---
type: regex
pattern: '(?<![\d,])\$?\s?6,?400(?:\.\d{2})?(?!\d|,\d)'
target: last_message
---

<!--
Cross-check of the offset limit: ITAA 1997 s 770-75(2) (https://www.ato.gov.au/law/view/document?docid=PAC%2F19970038%2F770-75) and ATO FITO guide (https://www.ato.gov.au/forms-and-instructions/foreign-income-tax-offset-rules-guide-2026/calculate-your-fito-or-offset-limit). Limit = greater of $1,000 and (tax payable incl. Medicare levy) less (same tax with the foreign-taxed amount, and related non-debt deductions, left out). Resident scale 2025-26 (https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents): 18,201-45,000 16c; 45,001-135,000 $4,288 + 30c over 45,000. Medicare levy 2% in full because taxable income is above the single upper threshold (data/rates/2025-26.yaml medicare.low_income_single_upper = 35,013, VERIFIED). Single with private hospital cover, so no Medicare levy surcharge (first surcharge tier starts above 101,000).
Rent from Bali land is Art 6 income, taxable in Indonesia with no treaty rate cap (https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf), so with the prompt's confirmation the whole 7,000 counts as foreign income tax; the test is the limit.
Step 1, tax with the rent: taxable 75,000 -> 4,288 + 0.30 x 30,000 = 13,288; Medicare 1,500; total 14,788.
Step 2, tax without the 20,000 net rent: taxable 55,000 -> 4,288 + 0.30 x 10,000 = 7,288; Medicare 1,100; total 8,388.
Step 3, limit = 14,788 - 8,388 = 6,400 (32% x 20,000: 30% marginal plus 2% levy).
Step 4, offset = lesser of 7,000 and 6,400 = 6,400. The 600 balance is not refunded or carried forward (ATO FITO guide, 'Calculate your FITO or offset limit').
Wrong answers: 7,000 (limit ignored); 5,200 (30% x 20,000 less Medicare omitted, or another 26% mistake); 6,000 (30% marginal only, levy omitted).
-->
The answer states the offset of $6,400.
