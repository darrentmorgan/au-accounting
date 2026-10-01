---
type: llm
criteria: |
  PASS only if all hold:
  1. It says investor versus trader (or business) is a question of facts and degree, and lists relevant indicators (commercial purpose and profit intention, repetition and regularity, organisation and records, scale, holding period).
  2. It says volume, or size, or sophistication alone does not decide the question.
  3. It explains the consequences: investor means capital account and CGT (with the discount for assets held 12 months); a business or a commercial profit-making transaction means ordinary income and possibly trading stock, without the CGT discount.
  4. It does not give a confident single answer for the short-term trades: it treats the short-term dip trades as possibly commercial and recommends a registered tax agent for the characterisation.
  5. It may note the long-held (three-year) holdings are more consistent with investment.
  FAIL if it declares the user definitely an investor or definitely a trader from volume alone, or ignores the consequences.
focus: last_message
---

<!--
ATO crypto business page (https://www.ato.gov.au/businesses-and-organisations/income-deductions-and-concessions/income-and-deductions-for-business/crypto-assets-and-business/crypto-assets-used-in-business) and 'Are you in business' guidance: business indicators are commercial reasons, viability, profit intention, planned and business-like, repeated regularly; high volume or sophistication alone do not make a business. TR 97/11 (indicators); TR 92/3 and TD 2014/26 para 49 area: even without a business, a commercial profit-making isolated transaction can be ordinary income, and the CGT gain is then reduced (ITAA 1997 s 118-20). Brief T-14, R-31, R-32, E-01. Deliberately mixed facts: no single correct label, so the rubric checks the method and the hand-off.
-->
Judge the final answer against the criteria.
