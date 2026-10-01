---
type: regex
pattern: '\bAU-(?:CGT-005)\b'
target: last_message
---

<!--
AU-CGT-005 trigger: complex crypto, namely DeFi lending or borrowing and liquidity pools (fires on: 10 ETH into a lending protocol for receipt tokens, tokens into a liquidity pool for LP tokens). crypto.yaml notes complex DeFi reuses AU-CGT-005, so no AU-CRYPTO code applies.
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-CGT-005).
