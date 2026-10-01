---
type: regex
pattern: '(?<![\d,])\$?\s?125,?000(?:\.00)?(?![\d,])'
target: last_message
---

<!--
s 90 and s 92 ITAA 1936: net income is worked out without deducting partner salary (salary is not a deduction, it is a distribution). Ann = 50,000 salary + 50% x (200,000 - 50,000) = 50,000 + 75,000 = 125,000. Ben = 75,000. Total 200,000.
Primary sources: https://www.ato.gov.au/law/view/document?docid=PAC%2F19360027%2F92 ; https://www.ato.gov.au/law/view/document?docid=PAC%2F19360027%2F90
-->
Ann's share is $125,000 (Ben $75,000).
