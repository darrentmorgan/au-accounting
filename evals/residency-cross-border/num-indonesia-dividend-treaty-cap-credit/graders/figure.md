---
type: regex
pattern: '(?<![\d,])\$?\s?1,?200(?:\.\d{2})?(?![\d,])'
target: last_message
---

<!--
Australia-Indonesia DTA Art 10(2) (ATO synthesised text): source-country tax on dividends may not exceed 15% of the gross amount. ATO FITO guide: foreign tax must be correctly imposed under the treaty; only the treaty-capped part counts and the balance is recovered from the foreign tax authority.
Creditable foreign tax = 15% x 8,000 = 1,200. (The excess 400 is not creditable.)
1,200 > $1,000 so the limit is computed: taxable 100,000: 4,288 + 0.30 x 55,000 = 20,788 + Medicare 2,000 = 22,788. Taxable 92,000: 4,288 + 0.30 x 47,000 = 18,388 + Medicare 1,840 = 20,228. Limit 2,560. Offset = min(1,200, 2,560) = 1,200.
Wrong: 1,600 (full withholding).
Primary sources: https://www.ato.gov.au/law/view/document?DocID=MLI%2FMLI-Indonesia-agreement ; https://www.ato.gov.au/api/public/content/0-54c8ecca-9ca0-43c3-9de6-100ac2156e26 ; https://www.austlii.edu.au/au/legis/cth/consol_act/itaa1997240/s770.75.html
-->
The answer states the offset of $1,200.
