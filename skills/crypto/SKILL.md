---
name: crypto
description: 'Works out Australian tax on bitcoin, ether and other crypto assets for resident individuals holding on capital account. Use whenever someone describes buying, selling or cashing out crypto, or asks how crypto is taxed: "cashed out my bitcoin", "sold my crypto", "sold some eth", "how is bitcoin taxed", "do I pay tax on crypto", "swapped tokens", "spent bitcoin on a laptop", "staking rewards tax", "airdrop", "hard fork", "lost my seed phrase", "paid in crypto", "no records for my crypto". Covers CGT on each disposal (sale, swap, spending, gifting, card loading), cost base and parcel matching (first-in first-out or documented specific selection, never average cost), the CGT discount via the cgt skill, the personal use asset exemption, staking and services income, airdrops (draft TR 2026/D1), forks, wrapping (draft TD 2026/D2), lost or stolen crypto, records and crypto held over 1 July 2027. Traders, mining, DeFi, NFTs, exchange collapse, foreign residents and company or trust holders are screened and escalated.'
---

# Crypto assets (Australia, resident individuals)

Works out the tax result for crypto held on capital account by a resident individual, through five tools: `crypto_classify_transactions`, `crypto_income_receipts`, `crypto_parcel_ledger`, `crypto_personal_use_screen` and `crypto_character_screen`. The ledger passes every matched parcel slice to the `capital_gain` tool and every income year to the `net_capital_gain` tool in the `cgt` skill, so the discount, the 12-month rule, loss ordering and the 1 July 2027 rules are computed there and only there. Never do arithmetic yourself and never quote a rate, threshold or percentage from memory: every figure comes from tool output and its `figures_used`.

## Scope

In scope (resident individual, crypto on capital account, AUD values supplied by the user):
- Classifying each transaction: disposal (CGT event A1), lost or stolen (C1), income at receipt, not an event.
- Disposals: selling for AUD, swapping one crypto for another, spending, gifting, loading a card, a network fee paid in crypto. No AUD has to be received.
- Cost base (five elements, ITAA 1997 s 110-25), parcel identification, holding period and discount through `cgt`.
- Personal use asset screen (ITAA 1997 ss 108-20, 108-25, 118-10(3)).
- Income receipts: staking and other consensus rewards, DeFi periodic rewards, payment for services, airdrops (draft view), prizes, gifts received, and their cost base.
- Chain splits and forks (ATO web guidance).
- Lost keys and stolen crypto (C1), with the evidence needed.
- Records (ITAA 1997 ss 121-20, 121-25) and the 1 July 2027 change as it touches crypto evidence.

Out of scope (escalate, see Escalation): a crypto trading or mining business, crypto held for sale in a business, isolated profit-making schemes, mining and pool payouts, DeFi lending, liquidity pools, bridging, liquid staking, derivatives, margin and crypto-backed loans, NFT creation or selling, wrapping and unwrapping (explained as a draft view only), exchange or platform administration, foreign resident, temporary resident, part-year or departing residents, companies, trusts and SMSFs, salary paid in crypto (PAYG, super, FBT), GST on crypto, borrowing to buy crypto, and sell-and-rebuy loss harvesting. GST goes to `gst-bas`, salary and super to `payroll-sg`, fringe benefits to `fbt`, residency to `residency-cross-border`, all other CGT mechanics to `cgt`, taxable income and tax to `individual-tax`.

## Authority (say which kind of source each answer rests on)

- Law: ITAA 1997 and ITAA 1936 as read on legislation.gov.au. Binding.
- Public ruling: TD 2014/26 (crypto is a CGT asset; personal use), TD 2014/27 (trading stock), TD 2014/25, TD 2014/28. Binding on the Commissioner.
- Determination TD 33 (identical assets that cannot be told apart): the ATO's considered view, no force of law; applied to crypto by analogy because the ATO has published no crypto-specific parcel position.
- ATO web guidance (staking, chain splits, swaps, lost or stolen crypto, records): the ATO's stated view, not a ruling. Chain splits have no ruling at all. Say "ATO web guidance", never "the ATO ruled".
- Drafts: TR 2026/D1 (airdrops) and TD 2026/D2 (wrapping), both issued 19 Aug 2026. Preliminary views, not law, not binding, and proposed to apply before and after they are finalised. ATO web pages updated on the same day mirror them; that does not make them final. Label every use of them as draft, every time.
- Edited private advice and secondary sources cannot be relied on and are never the citation.

## Required inputs

Ask for anything missing that changes the answer. Do not assume silently.

1. **Income year** and the holder: an individual, resident for tax purposes all year, not a temporary resident. Anything else stops here (AU-CRYPTO-005, or AU-CGT-003 for a company, trust or fund). For a person who may cease to be resident, stopping still includes saying that if they stay resident the crypto is unaffected until a disposal, and that event I1 (ITAA 1997 s 104-160, choice s 104-165) applies only on ceasing residency, at market value on that date (ask for it; never estimate). After I1 and the s 104-165 choice, say that while the person is a foreign resident, capital gains on crypto are generally disregarded because crypto is not taxable Australian property (ITAA 1997 s 855-10), while Australian-source income (for example crypto income sourced in Australia) stays taxable (ATO, Crypto asset transactions and tax residency). The exception: if the s 104-165 choice to disregard the I1 gain is made, the crypto is treated as taxable Australian property until sold or residency resumes, so a later disposal is taxable in Australia. Residency itself is a facts question: do not assume foreign residence from a move alone.
2. **Character facts**: how often and why the person trades, whether they mine, run a related business, hold crypto for sale, or are paid in crypto for work.
3. **Every transaction** (exchange exports plus on-chain wallets): Australian local date, asset, quantity, the AUD market value at the time and where that price came from, fees and whether fees were paid in AUD or crypto. UTC timestamps are converted to the Australian local date; state that as an assumption because no primary source fixes the convention.
4. **Acquisition records** for each parcel: date, quantity, AUD paid or market value received, incidental costs, origin (purchase, swap, staking, airdrop, split, payment).
5. **Identification method**: first-in first-out unless the person keeps contemporaneous records naming the units sold.
6. **Personal use facts** if the exemption is claimed: why it was bought, when, how it was spent, whether it passed through a conversion, gift card or payment gateway, whether it is part of a larger holding.
7. **Lost or stolen crypto**: date lost or discovered, evidence of ownership and of loss of access, any compensation.
8. **Held on 30 Jun 2027 and sold later**: market value just before 1 Jul 2027 per unit, from dated exchange data. Ask; never estimate it.
9. Other capital gains and losses in the year, and net capital losses carried forward.

## Procedure

1. **Gate.** Confirm the holder and residency. If the facts include creating, minting or selling NFTs, or earning royalties on them, stop before any calculator: quote AU-CRYPTO-006, work through the NFT rules below as questions for review (not conclusions), and do not call `gst_registration_check` or any other GST tool to conclude registration for the NFT sales. Continue with any fungible crypto in the same matter. Otherwise call `crypto_character_screen` with the facts from input 2; for example `inputs: {"regular_repeated_trading_for_profit": false, "high_volume_or_large_amounts_only": true}`. A refusal (AU-CRYPTO-001 or AU-CRYPTO-002) stops the ledger; quote it.
2. **Classify.** Call `crypto_classify_transactions` with `income_year` and `inputs: {"transactions": [{"id": "t1", "type": "swap", "date": "2026-11-18", "value_received_aud": <amount>}]}`. Use `utc_timestamp` instead of `date` for exchange exports. Each row returns the treatment, event, capital proceeds and the rule behind them, any draft label, and an escalation code where one applies. Rows with an escalation stay out of every later calculation; say which rows were held back.
3. **Income.** For staking, DeFi rewards, payment for services, airdrops, chain splits, prizes and gifts received, call `crypto_income_receipts` with `inputs: {"receipts": [{"id": "r1", "asset": "S", "date": "2026-09-14", "quantity": <n>, "kind": "staking_reward", "unit_value_aud": <amount>}]}`. It returns assessable income by income year (other income, not capital gain) and `acquisitions` rows with the cost base. Report the income separately and pass it to `assemble_taxable_income` as a component of kind `other_income` (`source_skill` user, `source_tool` crypto_income_receipts).
4. **Personal use.** Only when the person claims the exemption, call `crypto_personal_use_screen`. `personal_use_asset_indicated` is a screen from the person's facts, not a finding; `uncertain` means the ATO pages conflict or the law is unsettled, so treat the crypto as an ordinary CGT asset and flag it. `not_personal_use` ends the claim.
5. **Ledger.** Call `crypto_parcel_ledger` with `income_year` and `inputs`, for example:

```json
{"acquisitions": [{"id": "btc1", "asset": "BTC", "date": "2025-03-03", "quantity": 0.5,
                   "first_element_aud": <amount>, "incidental_costs_aud": <amount>}],
 "disposals": [{"id": "sw1", "asset": "BTC", "date": "2026-11-18", "quantity": 0.5, "kind": "swap",
                "value_received_aud": <amount>, "incidental_costs_disposal_aud": <amount>,
                "received_asset": "ETH", "received_quantity": <n>}],
 "method": "fifo", "holder_character": "investor"}
```

   Rewards and airdrops go in as the `acquisitions` rows returned in step 3. A swap with `received_asset` adds the asset received as a new parcel acquired on the swap date, so a chain of swaps needs one call. Other fields: `records_identify_parcels`, `parcel_selection` (named parcels, method `specific`), `treat_as_personal_use_asset`, `evidence_adequate` (lost or stolen), `market_value_30_june_2027_per_unit`, `received_market_value_30_june_2027_per_unit`, `prior_year_net_capital_losses`, `compute_cgt`. `parcels_remaining` can be fed back in as `acquisitions` for a later call.
6. **Other gains and losses.** If the person has other assets, or carried-forward losses beyond the input field, pass each slice's `cgt.components` into `net_capital_gain` (see the `cgt` skill) together with the other assets, so one combined loss ordering is applied per income year. `capital_gain_inputs` in the ledger output are the ready inputs for `capital_gain` when the minimum tax test (`taxable_income_including_gain`) is needed.
7. **Read the envelope.**
   - `exit_code` 0: present the result. Quote `assumptions`, `warnings` and any row `escalation`.
   - `exit_code` 0 with `field_refusals` (a disposal held across 1 July 2027): show every figure returned, including each disposal's `deferred_gain_aud`, `deferred_gain_discount_aud` and `deferred_gain_after_discount_aud` and the `deferred_components` rows, then quote each field refusal verbatim against the field it names (`post_1_july_2027_part`). The year's `net_capital_gain` is null and `incomplete` is true: say so, and label `net_capital_gain_known_components_only` as excluding the refused part.
   - `exit_code` 3 with `refusal`: quote the code and message verbatim, stop that part, and name the route.
   - `exit_code` 4 (AU-GEN-001 or AU-GEN-003): a figure is not verified or has no published value; quote the message and do not substitute a remembered figure.
   - `exit_code` 2: fix the input and call again.
8. Quote tool amounts in dollars and cents as returned; never re-round.

If the au-tax tools are unavailable, say so, quote AU-GEN-001 and stop.

## Judgement rules

- **Crypto is a CGT asset, and each asset is separate.** TD 2014/26; ITAA 1997 s 108-5. It is not money or foreign currency, so a stablecoin is crypto too: BTC into a stablecoin is a swap, and stablecoin into AUD is a disposal.
- **Every disposal is CGT event A1** (s 104-10), including a token-for-token swap, spending on goods, gifting and loading a card, even with no AUD received. The timing is the contract date, or the date ownership changes. A CGT event happens even if the gain is disregarded (s 102-23).
- **Capital proceeds for a swap** are the AUD market value of what is received (s 116-20(1)(b)). If what is received cannot be valued (an unlisted token), use the market value of what is given up (s 116-30(2)(a)). A gift is taken to be for market value (s 116-30(1)).
- **A swap restarts the clock.** The asset received is acquired on the swap date, with a first element equal to the market value given up (s 110-25). The 12-month test excludes the day of acquisition and the day of the event (s 115-25), and is applied by `cgt`. "Held over 12 months means exempt" is wrong: 12 months gives the discount for events before 1 Jul 2027, not an exemption.
- **Own-wallet transfers are not disposals.** A network fee paid in crypto is. How that fee counts in the cost base is unsettled (draft TD 2026/D2 reserves gas fees): flag it. A swap fee paid in AUD stays in the cost base of the asset disposed of, as in the ATO's own example; do not add it again to the asset received.
- **Exchange deposits.** No ATO page says whether depositing with a centralised exchange is a disposal. It turns on beneficial ownership under the account terms (s 104-10(2)). Treat this as inferred and check the terms.
- **Parcel identification.** No crypto-specific ATO position exists. TD 33 accepts first-in first-out, or the taxpayer's own selection where records show it, and rejects average cost across parcels bought on different days (TD 33A allows same-day identical units). Use first-in first-out unless contemporaneous records name the units. A method other than first-in first-out with no such records is refused (AU-CRYPTO-009). Do not assert that highest-cost-first or last-in first-out is accepted by the ATO; say it is defensible only with records.
- **Personal use asset.** Losses are always disregarded (s 108-20(1)). A gain is disregarded if the first element of cost base is at or below the personal use asset threshold (`individual.personal_use_asset_cgt_exempt_max_cost`; s 118-10(3) says "or less", so a first element exactly at the threshold qualifies; two ATO web pages say "less than", and the statute governs, so mention the difference). The test is on how the crypto was actually kept and used: acquired to buy personal items and used within a short time is more likely personal use (TD 2014/26); an investment holding later spent is not. Conversions, gift cards, card top-ups and payment gateways are described in "rare situations" on one ATO page and treated the opposite way on another: do not assert. Splitting a holding into several disposals to stay under the threshold may be caught by the set rule (s 108-25); how it applies to fungible crypto is unsettled. The tool tests the first element of the whole disposal, not each slice. NFTs and collectables use a separate, lower threshold and escalate.
- **Staking and DeFi rewards.** Ordinary income at the AUD market value when received (ITAA 1997 s 6-5; ITAA 1936 s 21), declared as other income, and that value is the cost base of the tokens; a later disposal is a separate event. Taxing them only on sale, or giving them a nil cost base, is wrong. A locked reward raises a timing question (s 6-5(4)) supported only by edited private advice that cannot be relied on: show income at the date given and flag it.
- **Payment for work in crypto.** Assessable at the AUD market value when received, and a fan or sponsor payment tied to work is not a gift. The payer's PAYG withholding and super, and a salary sacrifice arrangement (a property fringe benefit under TD 2014/28), go to `payroll-sg` and `fbt`.
- **Airdrops (draft TR 2026/D1).** Preliminary view: a business trading crypto has ordinary income; a reward for goods or services is income; a non-business holder with no services has no income, a separate CGT asset, and a cost base equal to market value at receipt (nil if nil or negligible). Not covered, so escalate: initial allocation airdrops before a final ruling, rebasing tokens, liquidity-reward airdrops, bounty airdrops, non-arm's-length distributions (AU-CRYPTO-003). A phishing offer whose tokens never reach the wallet is nothing received.
- **Chain splits (ATO web guidance).** A new asset received on a split is neither income nor a capital gain when received, has a nil cost base, and is acquired on the split date. Work out which side continues the original rights; that one keeps its cost base and date. If neither continues, the ATO's web example treats the original as ended (event C2) and both assets as new: escalate (AU-CRYPTO-011) rather than compute.
- **Wrapping (draft TD 2026/D2).** Preliminary view: wrapping through a lock-and-mint contract is event C2 on the wrap and on the unwrap, the wrapped token and the coin are separate assets, and no income arises. Alternative views are acknowledged and gas or platform fees are not addressed. Explain it as draft only and escalate the numbers (AU-CGT-005).
- **Lost, stolen or scammed crypto.** C1 (s 104-20): the event time is when compensation is first received, or when the loss is discovered if none; compensation reduces the loss. A loss needs evidence of ownership and of loss of access, and crypto that can be recovered is not lost. Weak evidence, a failed exchange, or a worthless or depegged token with no disposal: AU-CRYPTO-004.
- **Investor, trader or business.** A fact question the skill screens and never decides. Crypto held in a business, or acquired in a commercial profit-making transaction, is on revenue account (trading stock or ordinary income) and no discount applies (TD 2014/26, TD 2014/27, TR 92/3, TR 97/11; ITAA 1997 ss 70-10, 118-20). Volume, holding time and sophistication alone do not decide it. A business loss may face the non-commercial loss rules (`sole-trader-business`).
- **NFTs (escalated, never concluded).** Creating, minting or selling NFTs and earning resale royalties is outside the calculators (AU-CRYPTO-006). Say only what the primary sources support, as review points. Character: creating and selling NFTs regularly, or earning royalties, may be a business or a commercial profit-making activity, in which case receipts are ordinary income and the NFTs are trading stock with no CGT discount (ATO business crypto page; TD 2014/27); that is a question of fact the skill cannot settle. Keepsake NFTs bought to keep are CGT assets, and whether each is a collectable (s 108-10(2)) or a personal use asset (ATO: only in rare circumstances) is a fact question with different thresholds and loss rules (ss 118-10(1) and (3)). **GST:** an NFT is not "digital currency" under the GST definition (GSTA 1999 s 195-1), because it is unique and cannot be exchanged like for like, so the ordinary GST rules apply: a supply of an NFT is taxable unless it is GST-free (ATO: GST and digital currency). Supplies to overseas buyers, sales paid in crypto and marketplace fees each need specific review (GST-free exports, s 38-190; consideration in crypto is still consideration). Do not say the user does or does not have to register for GST, do not run a threshold or turnover test on a rough dollar figure, and never say GST does not apply to NFTs; state that NFTs are outside the digital currency treatment, that the registration position depends on the character and the turnover measured properly (the figure given is a rough income, not a GST turnover), and route it to `gst-bas` and a registered tax agent. No tax figure is given for NFT activity.
- **Records.** Records of every transaction that may bear on a gain or loss are required; missing records must be reconstructed, and nil is not the default cost base (ITAA 1997 s 121-20). Keep them until 5 years after no further CGT event can happen for the asset (s 121-25(2)); the general retention figure is `bookkeeping.record_retention_years` and starts from a different point. The ATO says exchange statements alone are not enough: keep the AUD value of every swap, wallet records and the counterparty or wallet address. Export exchange history regularly and before closing an account.
- **Data matching.** The ATO receives exchange data and pre-fills a myTax indicator. Swaps, spending with no cash, and staking or airdrop income are the commonly missed items.
- **Valuation.** Use a reputable exchange price at the time and record its source and time. There is no approved daily-average shortcut.
- **Year boundary.** Use the Australian local date. A UTC timestamp late on 30 Jun can be 1 Jul in South Australia; state the assumption and never present the time zone convention as settled.
- **Sell and rebuy.** Selling at a loss and repurchasing soon after may fall under Part IVA (TR 2008/1): stop (AU-CRYPTO-008).

## The 1 July 2027 change

For a resident individual, gains from events on or after 1 Jul 2027 lose the discount and get indexation for assets held 12 months, and an asset held on 30 Jun 2027 is deemed sold and reacquired at market value just before 1 Jul 2027, with the deemed gain deferred and discounted when the real sale happens. All of it is computed by `capital_gain` from the event's contract date; this skill never recomputes it.
- Ask for a dated exchange price per unit just before 1 Jul 2027 for every parcel likely to be sold later, and pass it as `market_value_30_june_2027_per_unit`. Without it the tool refuses (AU-CGT-006); never estimate it.
- The draft apportioning method is aimed at real property and assets with no readily ascertainable market value, so it will not normally suit a coin with a public price. It is not law. No primary source fixes the instant or time zone for "just before 1 July 2027"; say so.
- A swap, spend, gift or loss after 30 Jun 2027 realises the deferred gain or loss on the asset given up, and the asset received starts fresh, so its own 12-month test for indexation restarts.
- Rewards and airdrops received after 30 Jun 2027 still take a market value cost base at receipt.
- Post-2027 CPI index numbers come only from the rates file (`cgt.indexation_cpi_from_2027`) and have no published value yet. For a resident individual holding the crypto on 30 Jun 2027, the ledger still returns the **deferred component** as a figure: the notional gain from the deemed sale (market value just before 1 Jul 2027 less cost base), its 50% discount where the crypto was held 12 months to the sale (the deemed reacquisition ignored), and the discounted amount. Only the **post-1 Jul 2027 part** (proceeds less the indexed value from 1 Jul 2027) is refused AU-GEN-003, at field level, and the year's net capital gain is withheld as incomplete. Lead with the deferred component figures, then state that the later part is refused pending the CPI index numbers. Do not show a range, an upper bound or a nominal gain for the refused part, do not ask the user for index numbers and do not estimate them. A parcel acquired on or after 1 Jul 2027 has no deferred component, so its whole disposal refuses AU-GEN-003. A disposal in an income year with no rates file (2028-29 onwards) refuses the same way. Each income year is netted with that year's own rates (2027-28 for events from 1 Jul 2027). The minimum tax test needs the taxable income for the year.

## Escalation

| Trigger | Code |
|---|---|
| Trading or mining business, holding for sale in a business, isolated profit scheme, regular repeated trading for profit | AU-CRYPTO-001 |
| Mining or pool payouts | AU-CRYPTO-002 |
| Airdrop outside draft TR 2026/D1 (initial allocation, rebasing, liquidity reward, bounty, non-arm's-length) | AU-CRYPTO-003 |
| Lost, stolen or scammed crypto with weak evidence; exchange in administration; worthless or delisted token; compensation | AU-CRYPTO-004 |
| Foreign resident, temporary resident, part-year, ceasing or becoming a resident, overseas-source question | AU-CRYPTO-005 |
| NFTs, minting, royalties, collectable classification | AU-CRYPTO-006 |
| Borrowed to buy crypto, interest, margin, crypto-backed loans | AU-CRYPTO-007 |
| Sell-and-rebuy loss harvesting, year-end round trips | AU-CRYPTO-008 |
| Average cost across days, or a specific selection with no records | AU-CRYPTO-009 |
| Disposal larger than the holdings on record, cost base with no evidence, AUD value missing | AU-CRYPTO-010 |
| Chain split where the continuing side is unclear or neither continues | AU-CRYPTO-011 |
| DeFi lending or borrowing, liquidity pools, bridging, liquid staking, derivatives, wrapping (draft), airdrops received in a trading business | AU-CGT-005 |
| Company, trust, SMSF or fund holder | AU-CGT-003 |
| Market value just before 1 Jul 2027 not provided | AU-CGT-006 |
| Asked to lodge, pay or respond to the ATO | AU-GEN-002 |
| A needed figure is not verified or has no published value | AU-GEN-001 or AU-GEN-003 |

Surface the code and its message exactly as returned, then stop the affected part and carry on with the rest. Salary in crypto, PAYG, super and fringe benefits have no code here: state the route to `payroll-sg` and `fbt`; GST goes to `gst-bas`.

## Output

End every answer with this working paper (CONVENTIONS section 8):

1. **Result** for the stated income year, holder and residency: other income (staking, services, airdrops treated as income) shown separately from the net capital gain; per disposal the event, capital proceeds with the AUD source and time of each price, parcels used and method, cost base, holding period flag, gain or loss; the net capital gain per income year and any net capital loss carried forward; personal use screen outcome and reasons; rows held back and why.
2. **Figures used**: key, value, status, source URL for each entry in `figures_used`.
3. **Assumptions**: the tools' `assumptions` plus your own, always including the identification method, the Australian local date convention, that AUD values were supplied by the user, and the holder character assumed.
4. **Risk flags**: relevant entries from `data/risk_flags/crypto.yaml` (for example CRYPTO-SWAP-DISPOSAL, CRYPTO-AUD-VALUATION, CRYPTO-PARCEL-IDENTIFICATION, CRYPTO-PUA-NARROW, CRYPTO-STAKING-INCOME, CRYPTO-DRAFT-RULINGS, CRYPTO-RECORDS, CRYPTO-2027-VALUATION), or "none".
5. **Refusals or escalations**: codes and messages, with the tools' `warnings`, and any draft ruling label; or "none".
6. "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use." Copy this sentence verbatim as the last line of the answer; do not paraphrase it.

References: `references/rules.md` (rule map with authority tags and the points the ATO has not settled), `references/sources.md` (primary sources).
