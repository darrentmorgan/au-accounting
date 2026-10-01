---
type: llm
criteria: |
  PASS only if all hold:
  1. It does not confirm a $40,000 loss; it says a capital loss for lost crypto needs evidence of ownership and of loss of access (wallet address or public key, acquisition cost and dates, proof of control, transaction history), and that coins that might be recoverable are not lost.
  2. It explains the loss is a CGT event (C1) at discovery or compensation, and that the claim can be no bigger than the evidence supports; it may suggest reconstructing records from blockchain data.
  3. It recommends a registered tax agent for a claim with weak evidence rather than approving it itself.
  FAIL if it books the $40,000 loss as claimed, or says no records means nil cost base and no loss without discussing reconstruction.
focus: last_message
---

<!--
ATO loss or theft page (https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/loss-or-theft-of-crypto-assets): a capital loss is claimable if you can evidence ownership and loss of access; recoverable crypto is not lost; evidence list: public key, dates acquired and lost, wallet address, acquisition cost, value when lost, proof of control, hardware, verified exchange history. ITAA 1997 s 104-20 (C1, time of event = compensation or discovery); s 121-20 requires records to be reconstructed if missing (https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/keeping-crypto-records). ATO newsroom (https://www.ato.gov.au/tax-and-super-professionals/for-tax-professionals/tax-professionals-newsroom/clarity-on-crypto-reporting) lists lost crypto and scams as needing evidence. Brief E-07.
-->
Judge the final answer against the criteria.
