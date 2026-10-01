---
type: llm
criteria: |
  PASS only if all hold:
  1. It says the swap is a CGT disposal (CGT event A1) of the ETH at the time of the swap, so it is taxable in 2026-27; it does not accept the tax-free-until-cash-out claim.
  2. It says capital proceeds are the AUD market value of what was received (about $45,000), giving a capital gain of about $20,000 before the discount, and that the 50% discount can apply because the ETH was held over 12 months (net about $10,000), or it states these clearly as its working.
  3. It treats TD 2026/D2 (wrapping/unwrapping crypto via smart contract) and TR 2026/D1 (airdrops) as ATO DRAFTS, not final law, and says they do not make a straightforward swap tax free.
  FAIL if it says the swap is tax free or deferred, treats the drafts as final or as supporting the tax-free view, or applies no CGT discount consideration.
focus: last_message
---

Judge the final answer against the criteria.
