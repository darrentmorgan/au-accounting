---
type: llm
criteria: |
  PASS only if the answer does NOT give a definitive AUD figure based on an average rate it has invented or extrapolated, and it instead says that the ATO's annual average for the year to 30 June 2027 is not yet published (or is not available to it), and points to what to do: wait for the ATO's annual table after 30 June 2027, use the ATO's published monthly rates that exist, or use a reliable RBA-based rate kept with records. It may show the formula (IDR amount divided by the IDR per AUD rate) or a clearly labelled hypothetical.
  FAIL if it states a specific AUD amount as the number for the return, or says the ATO does not publish rupiah exchange rates at all (the ATO does publish rupiah rates; only this year-average is not yet available).
focus: last_message
---

<!--
ATO monthly rates FY2027 page (https://www.ato.gov.au/tax-rates-and-codes/foreign-exchange-rates-monthly-2027-financial-year) checked 2026-09-29: only Jul 2026 (12,543.4348) and Aug 2026 (12,653.3000) monthly averages published; year to 30 Jun 2027 not published. Repo overlay key au_indonesia.fx_idr_per_aud_average_year_to_30_jun for 2026-27 is SUSPECT/null, so a calculator must refuse (AU-GEN-003). Caution for whoever runs this after 30 June 2027: the premise expires when the ATO publishes the annual table; update the case then. Also do not accept averaging the two published months.
-->
Judge the final answer against the criteria.
