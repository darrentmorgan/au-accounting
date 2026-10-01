---
type: regex
pattern: '\bAU-(?:GST-002)\b[\s\S]*\bAU-(?:CRYPTO-001|CGT-005)\b|\bAU-(?:CRYPTO-001|CGT-005)\b[\s\S]*\bAU-(?:GST-002)\b'
target: last_message
---

<!--
Two limbs, both codes required. AU-GST-002 trigger: short-stay operator where the answer depends on commercial residential premises status, for example a head-lease or principal model across many dwellings with hotel-like services (fires on: eight head-leased apartments, daily cleaning, breakfast packs, front desk, GST not registered). AU-CRYPTO-001 (or AU-CGT-005, which also lists a business of trading) trigger: crypto trading business (fires on: bot, about 4,000 trades, spreadsheet, wants the 50% discount).
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-GST-002 and AU-CRYPTO-001 or AU-CGT-005).
