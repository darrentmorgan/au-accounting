---
type: regex
pattern: '(?<![\d,])\$?\s?14,?620(?:\.\d{2})?(?![\d,])'
target: last_message
---

<!--
2025-26. Machine A 18,500 < 20,000 IAWO limit (extended to 30 June 2026 by Treasury Laws Amendment (Tax Incentives and Integrity) Act 2025) -> immediate deduction 18,500. Machine B 26,000 >= 20,000 -> small business pool, 15% first year = 3,900.
Taxable income = 100,000 - 18,500 - 3,900 = 77,600.
Tax: 4,288 + 30c x (77,600 - 45,000) = 4,288 + 9,780 = 14,068. LITO nil. SBITO = 16% x 14,068 (all income is net small business income) = 2,250.88, capped at 1,000, so offset 1,000. Medicare 2% x 77,600 = 1,552. Payable = 14,068 - 1,000 + 1,552 = 14,620.
Trap: the $20,000 IAWO for assets first used on/after 1 July 2026 (Tax Reform No. 2 Act 2026) does not apply; 2025-26 uses the earlier extension. Both give a $20,000 limit here.
Primary: https://www.ato.gov.au/businesses-and-organisations/income-deductions-and-concessions/depreciation-and-capital-expenses-and-allowances/simpler-depreciation-for-small-business/instant-asset-write-off ; https://www.ato.gov.au/businesses-and-organisations/small-business-newsroom/20000-instant-asset-write-off-for-2025-26 ; https://www.ato.gov.au/businesses-and-organisations/income-deductions-and-concessions/income-and-deductions-for-business/concessions-offsets-and-rebates/small-business-income-tax-offset ; https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents
-->
The answer states the total tax payable of $14,620.
