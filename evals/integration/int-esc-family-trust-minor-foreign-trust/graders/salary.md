---
type: regex
pattern: '(?<![\d,])\$?\s?17,?988(?:\.\d{2})?(?![\d,])'
target: last_message
---

<!--
In-scope part computed standalone: 4,288 + 30c x (85,000 - 45,000) = 16,288; Medicare 2% x 85,000 = 1,700; total 17,988. MLS nil.
Out of scope: minor beneficiary unearned income (Div 6AA, not excepted income) and foreign trust distribution (s99B / Div 6AAA / transfers of value, interest charge, reporting), needing a registered tax agent.
Primary: https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents ; https://www.ato.gov.au/individuals-and-families/your-tax-return/instructions-to-complete-your-tax-return/paper-tax-return/tax-return-for-individuals-supplementary-section-2026/foreign-source-income-and-foreign-assets-or-property-2026
-->
The answer computes the standalone tax on the salary as $17,988 (including Medicare).
