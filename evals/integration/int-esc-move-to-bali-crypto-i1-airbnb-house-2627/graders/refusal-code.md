---
type: regex
pattern: '\bAU-(?:CRYPTO-005|RES-004|RES-001)\b[\s\S]*\bAU-(?:IDN-002)\b|\bAU-(?:IDN-002)\b[\s\S]*\bAU-(?:CRYPTO-005|RES-004|RES-001)\b'
target: last_message
---

<!--
Two limbs, both required. AU-CRYPTO-005 trigger: holder ceasing to be an Australian resident, CGT event I1 (fires on: move to Bali 1 March 2027, ETH cost $30,000 now $80,000). AU-RES-004 trigger: residency indicators point both ways (fires on: keeps the Adelaide home, Australian employer and account, rents in Bali for at least two years); either is correct for that limb. AU-IDN-002 trigger: Indonesian domestic tax, including whether a person is an Indonesian domestic resident (fires on: do I owe Indonesian tax on my salary).
Source: data/refusals/*.yaml (trigger text is the public contract; CONVENTIONS section 10 refusal cases expect the verbatim code).
-->
The answer quotes the verbatim refusal code (AU-CRYPTO-005 or AU-RES-004 and AU-IDN-002).

<!-- Orchestrator 2026-09-30: AU-RES-001 added to the first limb. Its trigger in data/refusals/residency.yaml covers an individual who may be resident of two countries with conflicting facts, which these facts fire (Indonesia may treat the person as resident); run 20260930T064346 quoted it legitimately. -->
