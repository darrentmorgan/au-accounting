---
type: llm
criteria: |
  PASS only if all hold:
  1. It says nil cost base is not the legal default and that missing records must be reconstructed (for example from blockchain explorer data, exchange exports, bank statements, wallet history, and valuations where needed).
  2. It says the ATO's view is that exchange statements alone are often not enough and that the AUD market value at the time of each transaction (including swaps) needs to be worked out and recorded.
  3. It gives practical record-keeping steps (export histories now and regularly, keep wallet addresses, dates, amounts, counterparties, and AUD values) and says records are kept until five years after no further CGT event can happen, or refers to the statutory record rule.
  4. It notes the ATO matches crypto exchange data to returns, or recommends a registered tax agent to help reconstruct records.
  FAIL if it says nil cost base is fine, or that the exchange summary alone is sufficient.
focus: last_message
---

<!--
ITAA 1997 s 121-20 (records of every act relevant to a gain or loss; where records do not exist they must be reconstructed, a valuation may be needed) and s 121-25(2) (retain until 5 years after it is certain no further CGT event can happen; VERIFIED in compilation 266, https://www.legislation.gov.au/C2004A05138/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_3/document_3.html). ATO keeping crypto records (https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/keeping-crypto-records); ATO newsroom top errors (https://www.ato.gov.au/tax-and-super-professionals/for-tax-professionals/tax-professionals-newsroom/clarity-on-crypto-reporting): relying on exchange records, not recording AUD values of swaps. ATO data-matching protocol for crypto exchanges, 2014-15 to 2025-26. Brief T-15, R-66 to R-69. The 5 years-after-last-event wording is statutory; the ATO web summary is looser, so the grader accepts either.
-->
Judge the final answer against the criteria.
