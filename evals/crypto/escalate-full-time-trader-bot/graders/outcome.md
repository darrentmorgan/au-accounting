---
type: llm
criteria: |
  PASS only if all hold:
  1. It identifies the facts as pointing to a crypto trading business (regular, profit-seeking, business-like, ABN) whose crypto is likely trading stock with profits as ordinary income, and says the CGT discount treatment is unlikely to be available or is not something it can assume.
  2. It recommends a registered tax agent (or a suitably qualified tax adviser) for the affected part rather than deciding it itself.
  3. It does not give one definitive tax figure for the year and does not confirm CGT discount treatment.
  4. It may note that volume alone does not decide the question, but not that the facts are merely those of a casual investor.
  FAIL if it computes a discounted CGT result as the answer, or says the user is clearly an investor.
focus: last_message
---

<!--
ATO crypto assets used in business (https://www.ato.gov.au/businesses-and-organisations/income-deductions-and-concessions/income-and-deductions-for-business/crypto-assets-and-business/crypto-assets-used-in-business): crypto held in a crypto trading business is trading stock; sales are assessable, costs deductible, no CGT discount. TD 2014/27 (trading stock, ITAA 1997 s 70-10); TR 97/11 business indicators (commercial reasons, profit intention, planned and business-like, repeated regularly). Brief E-01: character screen and escalate, not decide. Existing refusal AU-CGT-005 covers a business of trading; the skill may quote it or a crypto code, so no code is asserted here.
Also relevant: Div 35 non-commercial loss rules if there is a loss year, GST on digital currency, trading stock stocktake (s 70-35).
-->
Judge the final answer against the criteria.
