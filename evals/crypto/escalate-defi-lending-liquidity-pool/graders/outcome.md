---
type: llm
criteria: |
  PASS only if all hold:
  1. It does not accept that nothing is taxable until withdrawal to AUD; it says depositing into a lending protocol or a liquidity pool can be a CGT event (for example on depositing, proceeds being the market value of the tokens or rights received) and that periodic rewards or fees are assessable income at market value.
  2. It says the answer turns on the protocol's terms and how it actually operates and that this is outside what it can settle, recommending a registered tax agent or specialist.
  3. It does not give one definitive tax figure for the DeFi activity.
  FAIL if it confidently says the deposits are not disposals, or calculates a definitive tax number for the lending and pool activity without escalating.
focus: last_message
---

<!--
ATO DeFi page (https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/decentralised-finance-and-wrapping-crypto): lending or borrowing in DeFi often ends beneficial ownership, giving a CGT event where proceeds are the market value of what is received; depositing to a liquidity pool is a CGT event with proceeds the market value of the LP tokens or rights received; periodic rewards are assessable at market value at receipt. The terms and actual operation decide (events likely A1, E2, C2, H2; most specific applies). Existing refusal AU-CGT-005 covers DeFi, lending, liquidity pools; brief E-03.
No figure asserted: the numbers given are insufficient by design (no market values at deposit).
-->
Judge the final answer against the criteria.
