---
type: regex
pattern: '(?<![\d,])\$?\s?1,?150(?:\.\d{2})?(?!\d|,\d)'
target: last_message
---

<!--
Cross-check of the offset limit: ITAA 1997 s 770-75(2) (https://www.ato.gov.au/law/view/document?docid=PAC%2F19970038%2F770-75) and ATO FITO guide (https://www.ato.gov.au/forms-and-instructions/foreign-income-tax-offset-rules-guide-2026/calculate-your-fito-or-offset-limit). Limit = greater of $1,000 and (tax payable incl. Medicare levy) less (same tax with the foreign-taxed amount, and related non-debt deductions, left out). Resident scale 2025-26 (https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents): 18,201-45,000 16c; 45,001-135,000 $4,288 + 30c over 45,000. Medicare levy 2% in full because taxable income is above the single upper threshold (data/rates/2025-26.yaml medicare.low_income_single_upper = 35,013, VERIFIED). Single with private hospital cover, so no Medicare levy surcharge (first surcharge tier starts above 101,000).
Interest: Art 11(2) cap 10% of gross (https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf) -> 10% x 4,000 = 400 counts (400 of the 800 withheld is above the cap).
Royalty for copyright: Art 12(3)(a) (copyright), so the 15% limb of Art 12(2)(b) applies, not the 10% limb for equipment and know-how (12(3)(b), (c)) -> 15% x 5,000 = 750 counts (250 of 1,000 is above the cap).
Total creditable = 400 + 750 = 1,150. The 1,000 no-calculation shortcut (ITAA 1997 s 770-75(2)(a), Note 1) is about the TOTAL offset claimed, so 1,150 is over it and the limit must be computed.
Limit: taxable 80,000 -> 4,288 + 0.30 x 35,000 = 14,788 + Medicare 1,600 = 16,388. Taxable 71,000 (remove 9,000 gross) -> 4,288 + 0.30 x 26,000 = 12,088 + Medicare 1,420 = 13,508. Limit = 2,880.
Offset = lesser of 1,150 and 2,880 = 1,150.
Wrong answers: 1,800 (no caps applied), 1,000 (treated as under the default limit), 1,150 with the royalty at 10% giving 900 (wrong tier).
-->
The answer states the offset of $1,150.
