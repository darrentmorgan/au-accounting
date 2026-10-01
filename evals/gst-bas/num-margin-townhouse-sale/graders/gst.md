---
type: regex
pattern: '(?<![\d,.])\$?\s?34,?09[01](?:\.\d{1,2})?(?:\.00)?(?![\d,])'
target: last_message
---

<!--
Margin = 825,000 - 450,000 = 375,000. GST on margin = 1/11 x 375,000 = 34,090.91 (34,091). Reported at 1A. Not 10% of the price (75,000) and not 1/11 of the price.
Sources: https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/in-detail/your-industry/property/gst-and-the-margin-scheme/calculating-the-gst-payable
-->
The answer states GST of about $34,091.
