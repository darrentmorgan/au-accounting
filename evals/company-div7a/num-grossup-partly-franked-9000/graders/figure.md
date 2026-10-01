---
type: regex
pattern: '(?<![\d,])\$?\s?10,?800(?:\.00)?(?![\d,])'
target: last_message
---

<!--
Franked part = 9,000 x 60% = 5,400. Credit = 5,400 x 25/75 = 1,800. Assessable = 9,000 + 1,800 = 10,800 (offset 1,800).
Primary source: https://www.ato.gov.au/individuals-and-families/investments-and-assets/dividends-and-shares/dividends-and-franking-credits (ITAA 1936 s207-20 via ITAA 1997)
-->
The answer states assessable income of $10,800 (dividend $9,000 plus $1,800 franking credit).
