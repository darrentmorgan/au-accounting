---
type: regex
pattern: '(?<![\d,])\$?\s?22,?988(?:\.\d{2})?(?![\d,])'
target: last_message
---

<!--
2025-26. Taxable income = 90,000 + 20,000 = 110,000. Tax 4,288 + 30c x 65,000 = 23,788. Medicare 2,200. Step 1 (tax payable incl. Medicare, before offsets) = 25,988.
FITO claimed 3,000 > 1,000 so limit applies. Step 2: tax if foreign income disregarded: taxable 90,000 -> 4,288 + 13,500 = 17,788 + Medicare 1,800 = 19,588. Limit = 25,988 - 19,588 = 6,400. FITO = lesser of foreign tax paid 3,000 and limit 6,400 = 3,000.
Net = 25,988 - 3,000 = 22,988. MLS nil (hospital cover held).
Note the ATO limit calculation includes Medicare levy in both steps.
Primary: https://www.ato.gov.au/forms-and-instructions/foreign-income-tax-offset-rules-guide-2024/calculate-your-fito-or-offset-limit ; https://www.ato.gov.au/api/public/content/0-54c8ecca-9ca0-43c3-9de6-100ac2156e26 ; https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents ; treaty art 15 and art 24: https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf
-->
The answer states the net tax payable of $22,988.
