---
type: regex
pattern: '(?<![\d,])\$?\s?2,?184(?:\.00)?(?![\d,])'
target: last_message
---

<!--
Base: 3 units (60 days = 3 x 28-day periods) x $364 (unit for failures on/after 1 Jul 2026) = 1,092. Medium entity (assessable income or GST turnover $1m to under $20m) multiplies base by 2 = 2,184. Size tested at the due date.
Primary sources: https://www.ato.gov.au/individuals-and-families/paying-the-ato/interest-and-penalties/penalties/failure-to-lodge-on-time-penalty ; https://www.ato.gov.au/individuals-and-families/paying-the-ato/interest-and-penalties/penalties/penalty-units
-->
The answer states a penalty of $2,184.
