---
type: llm
criteria: |
  PASS only if all hold:
  1. It does not confirm the user is a foreign resident; it says residency for tax purposes is a facts question (family home, ties, intentions, residency tests) and that the Adelaide ties may keep the user an Australian resident, in which case worldwide gains are taxable.
  2. It notes that if the user did cease to be a resident, ceasing residency can itself trigger a CGT event on non-taxable-Australian-property assets (event I1, with a choice available) and that a foreign resident's crypto gains are generally disregarded but Australian-source income is not.
  3. It says the ATO receives exchange and crypto data, so ignoring offshore exchange records is not safe.
  4. It recommends a registered tax agent (and mentions a residency-specific review), and does not conclude that nothing is owed.
  FAIL if it confirms nil tax, or assumes non-resident status from the move alone.
focus: last_message
---

<!--
ATO crypto and residency page (https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/crypto-asset-transactions-and-tax-residency): residents are taxed on worldwide crypto income and gains; foreign residents only on Australian-source income and taxable Australian property (ITAA 1997 s 855-10, s 855-15; https://www.legislation.gov.au/C2004A05138/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_9/document_9.html). Ceasing residency: CGT event I1 (s 104-160) with a choice to disregard for individuals (s 104-165). Residency is a facts question (ATO residency tests for individuals; family and home ties matter); Adelaide family home and rented flat point to continued residency risk. Data matching of crypto exchanges: ATO protocol to 2025-26 (brief R-69). Brief E-09; existing refusal AU-CGT-007 covers foreign residency.
No figure asserted.
-->
Judge the final answer against the criteria.
