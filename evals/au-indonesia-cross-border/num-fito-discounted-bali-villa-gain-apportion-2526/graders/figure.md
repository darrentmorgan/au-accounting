---
type: regex
pattern: '(?<![\d,])\$?\s?4,?000(?:\.\d{2})?(?!\d|,\d)'
target: last_message
---

<!--
Cross-check of the offset limit: ITAA 1997 s 770-75(2) (https://www.ato.gov.au/law/view/document?docid=PAC%2F19970038%2F770-75) and ATO FITO guide (https://www.ato.gov.au/forms-and-instructions/foreign-income-tax-offset-rules-guide-2026/calculate-your-fito-or-offset-limit). Limit = greater of $1,000 and (tax payable incl. Medicare levy) less (same tax with the foreign-taxed amount, and related non-debt deductions, left out). Resident scale 2025-26 (https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents): 18,201-45,000 16c; 45,001-135,000 $4,288 + 30c over 45,000. Medicare levy 2% in full because taxable income is above the single upper threshold (data/rates/2025-26.yaml medicare.low_income_single_upper = 35,013, VERIFIED). Single with private hospital cover, so no Medicare levy surcharge (first surcharge tier starts above 101,000).
ATO FITO guide 'When a FITO applies' (https://www.ato.gov.au/forms-and-instructions/foreign-income-tax-offset-rules-guide-2026/when-a-fito-applies): 'If only part of a foreign capital gain is assessable in Australia (for example ... the discount capital gains concessions in Division 115) the foreign tax paid on the gain must be apportioned accordingly.'
Step 1, discount: individual, held over 12 months, 50% (ITAA 1997 Div 115; repo key cgt.discount_individual_trust). Net capital gain in assessable income = 100,000 x 50% = 50,000.
Step 2, creditable foreign tax = 8,000 x 50,000 / 100,000 = 4,000. The other 4,000 gets no Australian offset.
Step 3, limit: taxable 130,000 -> 4,288 + 0.30 x 85,000 = 29,788 + Medicare 2,600 = 32,388. Taxable 80,000 (remove the 50,000 net gain) -> 4,288 + 0.30 x 35,000 = 14,788 + Medicare 1,600 = 16,388. Limit = 16,000, not binding.
Offset = 4,000.
Wrong answer: 8,000 (full foreign tax on a discounted gain).
-->
The answer states the offset of $4,000.
