---
type: llm
criteria: |
  PASS only if the answer shows ALL of these component figures:
  1. Assessable rent is the GROSS $35,700 (the platform's reported figure), not the $34,629 payout. The $1,071 host fee is claimed separately as a deduction. It says the ATO holds the platform's report (Sharing Economy Reporting Regime) so a return based on net payouts would not match.
  2. Direct letting costs deductible in full: host fee $1,071 + cleaning $4,201 = $5,272.
  3. Interest is split by the purpose of the borrowing: one quarter was spent privately so only 75% is deductible, $12,000 (not $16,000). Council rates, water and insurance $4,000 are deductible in full. Because the flat is a separate property with nights either rented ($210 nights) or held available on commercial terms (155 nights) and no private use by anyone, no time-based or area-based reduction applies and it is not a holiday home (no s 26-50 denial).
  4. Capital works deduction $3,000 (2.5% x $120,000, the residential rate for construction begun after 15 September 1987); NOT the 4% traveller accommodation rate ($4,800), which needs at least ten units or bedrooms.
  5. Total deductions $24,272; net rental income for the couple $11,428; the user's 50% share $5,714.
  6. GST: the rent is input taxed residential rent, no GST is charged, no credits are claimed, and the rent is not counted in GST turnover (no registration needed).
  7. Staking rewards are ordinary income when received: $700 + $650 + $886 = $2,236. Each reward has a cost base equal to its value when received. The reward sold on 1 March 2026 gives a capital gain of $300 ($1,000 - $700), held under 12 months so no discount; net capital gain $300. (Not $1,000, which would tax the $700 twice.)
  8. Taxable income $104,250 (96,000 + 5,714 + 2,236 + 300); tax $22,063; Medicare levy $2,085; no Medicare levy surcharge; no LITO.
  It must also satisfy: the answer is laid out as a working paper for review by a registered tax agent, with clearly identifiable sections for (a) figures used (with the source or table each came from), (b) assumptions, (c) risk flags, and (d) refusals/escalations (or an explicit statement that none are needed). It may note as a risk flag that renting out a granny flat can reduce the main residence exemption on a later sale of the block (a defer-to-CGT pointer, no figure needed).
  FAIL if the net-of-fee income is declared, if the full interest is claimed, if the 4% capital works rate is used, if GST is charged or credits claimed, if the staking rewards are treated as nil cost or untaxed until sold, or if the working-paper sections are missing.
focus: last_message
---

Judge the final answer against the criteria.

<!--
Hand computation, 2025-26 (365 days, single dwelling; no leap-year effect).
Sources: TR 2026/1 https://www.ato.gov.au/law/view/document?docid=TXR%2FTR20261%2FNAT%2FATO%2F00001 (paras 20-21, 65-68 income; co-owners by legal title paras 22, 51-53; TR 93/32) ; PCG 2026/2 https://www.ato.gov.au/law/view/document?docid=COG%2FPCG20262%2FNAT%2FATO%2F00001 (direct costs paras 10-12; mortgage with multiple purposes paras 50-51, TR 2000/2; time-based method paras 13-15) ; ATO "Rental income you must declare" and "Income and deductions for renting out your home" (declare income before platform fees) ; Div 43 https://www.ato.gov.au/individuals-and-families/investments-and-assets/property-and-land/residential-rental-properties/rental-expenses/capital-expenses/work-out-your-capital-works-deductions (data/rates rental.capital_works_rate_residential 2.5%, traveller accommodation 4% needs 10 units, VERIFIED) ; GSTA 1999 ss 40-35, 11-15(2)(a), 188-15(1)(a) ; SERR TAA 1953 Sch 1 s 396-55 item 15 ; ATO crypto staking page https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/staking-rewards-and-airdrops (ordinary income at money value when received; cost base is market value when received; read 30 Sep 2026); ITAA 1936 s 21, ITAA 1997 s 6-5(4) ; resident rates https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents.

Design note: the flat is separately titled and owner/family/friends never use it, so it is not "part of a home" (the PCG 2026/2 rule that a room in your own home has zero held days) and not a holiday home (s 26-50 needs use or holding for holidays of owner, family or friends). Nights held = 155 available on commercial terms, so time share = (210 + 155) / 365 = 100%. That avoids the unsettled point of whether a granny flat on the same title as the home is "part of a home".

1. Income = 210 x 170 = 35,700 gross (declare before fees).
2. Direct costs = 1,071 (3% x 35,700) + 4,201 = 5,272.
3. Interest: 100,000 / 400,000 = 25% private; deductible 16,000 x 75% = 12,000. Rates, water, insurance = 1,900 + 780 + 1,320 = 4,000.
4. Capital works: 120,000 x 2.5% = 3,000 (full year; completed Feb 2019, after 15 Sep 1987).
5. Deductions = 5,272 + 12,000 + 4,000 + 3,000 = 24,272. Net rent = 35,700 - 24,272 = 11,428. Each joint tenant 50% = 5,714.
6. Staking: 700 + 650 + 886 = 2,236 ordinary income. Reward 1 cost base 700; sold for 1,000 on 1 Mar 2026 (14 Aug 2025 to 1 Mar 2026 is under 12 months): gain 300, no discount; net capital gain 300.
7. Taxable income = 96,000 + 5,714 + 2,236 + 300 = 104,250.
8. Tax = 4,288 + 0.30 x (104,250 - 45,000) = 4,288 + 17,775 = 22,063. Medicare = 2% x 104,250 = 2,085. Total = 24,148. LITO nil (above 66,667); MLS nil.
Wrong answers to catch: net payout income (34,629 with fee deducted again: income understated 1,071); interest 100% (net rent 7,428, share 3,714); 4% capital works (net rent 9,628); nil cost base on reward 1 (gain 1,000, total 24,148 + 0.32 x 700 = 24,372); GST charged on rent (1/11 of 35,700 = 3,245.45).
-->
