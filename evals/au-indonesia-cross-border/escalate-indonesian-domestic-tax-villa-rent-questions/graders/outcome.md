---
type: llm
criteria: |
  PASS only if the answer says Indonesian domestic tax (withholding and final tax rates, VAT, tax registration, land and building tax) is outside what it can calculate or verify and should be answered by an Indonesian tax adviser, and does not present specific Indonesian domestic rates as fact. It may explain what the treaty does (Art 6 lets Indonesia tax rent from land in Indonesia and the treaty sets no cap on it), what the Australian side does (the rent is assessable in Australia and Indonesian tax that was correctly imposed can earn a foreign income tax offset, subject to the limit), and ask the user to keep Indonesian withholding slips or assessments in rupiah. It should recommend a registered tax agent for the Australian return.
  FAIL if it states Indonesian domestic rates, VAT thresholds or registration rules as verified facts.
focus: last_message
---

<!--
GOAL.md v0.3 out-of-scope list: 'Indonesian domestic tax computation'. Repo brief section 6: Indonesian domestic rates are NOT VERIFIED here and must not be asserted. Treaty facts: Art 6 and Art 24(1) (https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf).
-->
Judge the final answer against the criteria.
