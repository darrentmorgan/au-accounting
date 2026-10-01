---
type: regex
pattern: '(?<![\d,])\$?\s?1,?500(?:\.\d{2})?(?!\d|,\d)'
target: last_message
---

<!--
Cross-check of the offset limit: ITAA 1997 s 770-75(2) (https://www.ato.gov.au/law/view/document?docid=PAC%2F19970038%2F770-75) and ATO FITO guide (https://www.ato.gov.au/forms-and-instructions/foreign-income-tax-offset-rules-guide-2026/calculate-your-fito-or-offset-limit). Limit = greater of $1,000 and (tax payable incl. Medicare levy) less (same tax with the foreign-taxed amount, and related non-debt deductions, left out). Resident scale 2025-26 (https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents): 18,201-45,000 16c; 45,001-135,000 $4,288 + 30c over 45,000. Medicare levy 2% in full because taxable income is above the single upper threshold (data/rates/2025-26.yaml medicare.low_income_single_upper = 35,013, VERIFIED). Single with private hospital cover, so no Medicare levy surcharge (first surcharge tier starts above 101,000).
Art 10(2) cap 15% of 10,000 = 1,500; tax withheld 1,500 equals the cap, so all of it counts.
1,500 is above 1,000, so compute the limit. Taxable 90,000 -> 4,288 + 0.30 x 45,000 = 17,788 + Medicare 1,800 = 19,588. Taxable 80,000 -> 4,288 + 0.30 x 35,000 = 14,788 + Medicare 1,600 = 16,388. Limit = 3,200. Offset = lesser of 1,500 and 3,200 = 1,500.
Portfolio holding (about 5%), individual shareholder: no NANE (s 768-5 needs a company) and no Art 24(2) underlying credit.
-->
The answer states the offset of $1,500.
