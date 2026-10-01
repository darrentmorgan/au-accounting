---
type: regex
pattern: '(?<![\d,])\$?\s?600(?:\.\d{2})?(?!\d|,\d)'
target: last_message
---

<!--
Unfranked part = 10,000 x 40% = 4,000. Domestic rate on the unfranked part: 30% (Income Tax (Dividends, Interest and Royalties Withholding Tax) Act 1974 s 7(a), https://classic.austlii.edu.au/au/legis/cth/consol_act/itiarwta1974590/s7.html; ATO withholding rate page https://www.ato.gov.au/businesses-and-organisations/hiring-and-paying-your-workers/payg-withholding/payments-you-need-to-withhold-from/withholding-from-investment-income/investment-income-and-royalties-paid-to-foreign-residents/withholding-rate). Treaty cap 15% of the gross dividend (Art 10(2), https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf); ITAA 1953 s 17A(1) reduces the liability to the cap. Franked part 6,000: no dividend withholding tax (franked dividends are not subject to it).
Withholding = 15% x 4,000 = 600. Net paid = 10,000 - 600 = 9,400.
Wrong answers: 1,500 (15% of the whole dividend), 1,200 (30% of the unfranked part, treaty ignored), 3,000 (30% of the whole), 0 (both franked and unfranked ignored).
-->
The answer states withholding of $600.
