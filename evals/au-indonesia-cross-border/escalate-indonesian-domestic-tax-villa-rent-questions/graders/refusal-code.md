---
type: regex
pattern: '\bAU-(?:IDN-002)\b'
target: last_message
---

<!--
AU-IDN-002 trigger: Indonesian domestic tax, including rate or withholding on a payment, VAT or final tax on villa rent, land and building taxes, and tax registration (fires on: all four questions asked, and the exact Indonesian rates demanded).
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-IDN-002).
