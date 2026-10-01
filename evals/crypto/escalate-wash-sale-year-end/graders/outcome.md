---
type: llm
criteria: |
  PASS only if all hold:
  1. It does not endorse the plan as a free deduction; it flags wash sale (sell and immediately repurchase to realise a loss) arrangements as a risk that the ATO can challenge under the general anti-avoidance rules in Part IVA (TR 2008/1 covers wash sales of CGT assets).
  2. It explains the real position that the sale is a genuine disposal whose loss is a capital loss usable only against capital gains, but that a scheme entered into mainly to obtain the tax benefit may be caught.
  3. It recommends a registered tax agent before proceeding and does not present a definitive tax saving.
  FAIL if it says the plan is safe or fine, or quotes a definitive dollar saving as certain.
focus: last_message
---

<!--
TR 2008/1 (https://www.ato.gov.au/law/view/document?docid=TXR/TR20081/NAT/ATO/00001): wash sales and Part IVA. Brief T-21, E-14. The ATO's ruling looks at whether the sale was part of a scheme with a dominant purpose of obtaining the tax benefit; the buy-back within minutes to keep the position is the classic indicator. Capital losses are only usable against capital gains (ITAA 1997 s 102-5, s 102-10).
Because the ruling turns on facts and purpose, the correct handling is a flag and hand-off, not a yes/no.
-->
Judge the final answer against the criteria.
