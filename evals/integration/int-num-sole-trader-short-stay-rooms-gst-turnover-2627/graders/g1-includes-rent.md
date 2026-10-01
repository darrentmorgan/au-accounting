---
type: regex
pattern: '(?<![\d,])\$?\s?(?:36,?270|34,?200)(?:\.\d{2})?(?![\d,])'
target: last_message
---

<!-- ATO BAS step 1: G1 total sales includes GST-free, input taxed and taxable sales. GST-inclusive 22,770 + 13,500 = 36,270; GST-exclusive 20,700 + 13,500 = 34,200. -->
The answer reports total sales at G1 as $36,270 (GST-inclusive) or $34,200 (GST-exclusive), i.e. including the input taxed room rent.
