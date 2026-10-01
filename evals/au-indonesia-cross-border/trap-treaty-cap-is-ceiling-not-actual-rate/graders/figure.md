---
type: regex
pattern: '(?<![\d,])\$?\s?800(?:\.\d{2})?(?!\d|,\d)'
target: last_message
---

<!--
Art 10(2) (https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf): the source-country tax 'shall not exceed 15 per cent' of the gross dividend; it is a limit on the source country's own rate, not a rate. The FITO is for foreign income tax PAID (ATO FITO guide 'Tax must have been paid', https://www.ato.gov.au/forms-and-instructions/foreign-income-tax-offset-rules-guide-2026/when-a-fito-applies); Example 2 (Tim) claims what was withheld.
Tax paid 800 is under the cap (15% x 8,000 = 1,200), so 800 counts. 800 is not above the default 1,000, so no limit calculation is needed (ITAA 1997 s 770-75(2)(a) and Note 1, https://www.ato.gov.au/law/view/document?docid=PAC%2F19970038%2F770-75). Offset = 800.
Cross-check: computed limit would be taxable 95,000: 4,288 + 0.30 x 50,000 = 19,288 + 1,900 = 21,188; taxable 87,000: 4,288 + 0.30 x 42,000 = 16,888 + 1,740 = 18,628; limit 2,560, not binding.
Wrong answer: 1,200 (treaty cap treated as the amount of tax).
-->
The answer states the offset of $800.
