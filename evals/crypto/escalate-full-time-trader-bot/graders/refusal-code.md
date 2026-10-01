---
type: regex
pattern: '\bAU-(?:CRYPTO-001|CGT-005)\b'
target: last_message
---

<!--
AU-CRYPTO-001 trigger: facts point to a crypto trading business (regular repeated trading with profit purpose and business-like organisation) (fires on: full-time bot, 40 trades a day, ABN, spreadsheet, holds days or weeks, wants the CGT discount). AU-CGT-005 trigger also lists crypto held as trading stock or in a business of trading. Either is correct.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-CRYPTO-001 or AU-CGT-005).
