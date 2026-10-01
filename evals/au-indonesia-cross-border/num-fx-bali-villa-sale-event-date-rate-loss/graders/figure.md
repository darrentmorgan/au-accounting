---
type: regex
pattern: '(?<![\d,])\$?\s?7,?269(?:\.\d+)?(?!\d|,\d)'
target: last_message
---

<!--
ITAA 1997 s 960-50(6) item 5 (https://www.ato.gov.au/law/view/document?docid=PAC%2F19970038%2F960-50): amounts relevant to a CGT event are translated at the rate at the time of the transaction or event, so proceeds use the sale date and the cost base uses the purchase date. ATO translation rules (https://www.ato.gov.au/businesses-and-organisations/corporate-tax-measures-and-assurance/foreign-exchange-gains-and-losses/translation-conversion-rules): a one-off sale of a large capital asset is not a case for an average rate.
ATO annual rates FY2026 (https://www.ato.gov.au/tax-rates-and-codes/foreign-exchange-rates-annual-2026-financial-year): Indonesia, nearest actual exchange rate 30 Jun 2026 = 12,298.0000 IDR per AUD (VERIFIED, fetched 2026-09-29).
Step 1, proceeds = 3,600,000,000 / 12,298 = 292,730.53.
Step 2, cost base = 3,000,000,000 / 10,000 = 300,000.00 (rate supplied in the prompt as an assumption).
Step 3, capital result = 292,730.53 - 300,000.00 = -7,269.47, i.e. a capital LOSS of A$7,269 even though the rupiah gain is 600,000,000 (20%).
Wrong answers: a gain of about A$3,500 to A$4,000 from using one rate for both legs; a gain from using an average rate.
-->
The answer states a capital loss of about A$7,269 (A$7,269.47).
