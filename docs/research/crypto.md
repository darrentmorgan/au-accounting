# Crypto assets: primary-source brief (v0.3, gate 10)

As at 29 Sep 2026. Branch `v0.3/research-crypto`. Two readers:

- **eval-author** (writes cases and graders from this brief and primary sources, without reading the skill): sections 1, 3, 4, 5, 6, 8.2, 9.
- **skill-builder** (builds `skills/crypto`, its calculator, refusals, risk flags): sections 2, 3, 5, 7, 8.1, 9.

Nothing here is copied from any commercial guide. No secondary source is cited. ATO pages were read through Exa fetch (direct fetch of ato.gov.au returns 403); legislation.gov.au was read directly.

## 0. Conventions used in this brief

- IDs: `R-nn` rule, `T-nn` trap, `E-nn` escalation trigger, `W-nn` worked example, `Q-nn` open question, `S-nn` source. Every rule carries source IDs; the register in section 11 gives the URL for each.
- Authority tags: **LAW** statute read in ITAA 1997 compilation 266 (in force 1 Jul 2026); **RULING** public ruling, binding on the Commissioner; **DET** CGT cell determination (TD 33: "considered view of the ATO", no force of law); **WEB** ATO website guidance (not a ruling; the ATO's stated view); **DRAFT** draft ruling or determination (preliminary view, not binding); **EV** edited version of private advice (cannot be relied on); **Gov** Treasury or Government statement; **INFERRED** my reasoning, no primary source says it, flagged so nobody asserts it as fact.
- Read tags: **[R]** page or provision read in full this session; **[E]** extract only (SOURCE-CITED quality).
- "Resident individual" means an Australian resident for tax purposes who is not a temporary resident. Every worked example assumes this, an event before 1 Jul 2027 unless stated, no other gains or losses unless stated, AUD values supplied, and whole-dollar rounding.
- Statute citations are to ITAA 1997 unless stated. `cgt` means the existing `cgt` skill and `src/au_tax/calculators/cgt.py`.

## 1. Bottom line

1. There are no special tax rules for crypto. Ordinary rules apply and the ATO says the treatment depends on how the asset is acquired, held and disposed of (S-22, WEB [R]). The Government agreed in March 2025 that no crypto-specific legislation should be introduced (S-52 [R]).
2. Crypto is a CGT asset (s 108-5(1); TD 2014/26 paras 1 and 12, RULING). Each crypto asset is a separate CGT asset (S-22, S-25).
3. Disposal is CGT event A1 and includes selling for AUD, swapping one crypto for another, spending on goods or services, gifting, and loading a card (S-23, S-24, S-32). No AUD has to be received. Proceeds for a swap are the AUD market value of what is received (s 116-20(1)(b); S-24).
4. Moving crypto between wallets you own is not a disposal. Paying a network fee in crypto is a disposal of the crypto spent (S-27).
5. The personal use asset exemption is narrow. Statute: gain disregarded if the first element of cost base is $10,000 or less (s 118-10(3)); losses always disregarded (s 108-20(1)). ATO view: kept or used mainly to buy items for personal use or consumption, acquired and used within a short time; investment holdings do not qualify (S-26).
6. Investor vs trader vs business is a facts question. Business or commercial profit-making transactions put crypto on revenue account (trading stock, ordinary income, no CGT discount). The skill should screen and escalate, not decide (TD 2014/26 paras 22 to 25; S-45).
7. Staking rewards are ordinary income at AUD market value when received, and that value is also the cost base of the reward tokens (S-28). Airdrops depend on the recipient's character and are governed by DRAFT TR 2026/D1 (S-18). Chain splits give no income at receipt and a nil cost base (S-29, WEB only, no ruling). Wrapping is CGT event C2 under DRAFT TD 2026/D2 (S-19).
8. Drafts TR 2026/D1 and TD 2026/D2 were issued 19 Aug 2026 (comments close 16 Oct and 2 Oct 2026) and are not law. ATO web pages updated 19 Aug 2026 already describe the same positions, which makes them easy to mistake for final guidance (S-21, S-28, S-30).
9. Records: the ATO says exchange statements are not enough. Statute requires records of every act or transaction relevant to a gain or loss, reconstructed if missing, kept until 5 years after no further CGT event can happen (ss 121-20, 121-25). The ATO matches exchange data to returns (S-39, S-40, S-41).
10. From 1 Jul 2027 the 50% discount stops for resident individuals' gains from events on or after that date, replaced by indexation for assets held 12 months, with a deemed sale at market value just before 1 Jul 2027 for assets already held. That market value must be evidenced. The draft apportioning method (not law) is aimed at real property and assets with no readily ascertainable market value, so it will not normally fit liquid coins (s 112-155; S-53). All the arithmetic stays in `cgt`.
11. No figures need to be added to the rates files for this skill (section 7). No conflict with any existing VERIFIED figure this brief touches was found.

## 2. Division of labour with `cgt` (what already exists)

Read from `skills/cgt/SKILL.md`, `skills/cgt/references/rules.md`, `src/au_tax/calculators/cgt.py`, `data/refusals/cgt.yaml`, `data/risk_flags/cgt.yaml`.

| Topic | `cgt` already does | `crypto` skill should do |
|---|---|---|
| Gain or loss on one event | `capital_gain`: A1 (and C1, C2, D1, H2, I1), cost base 5 elements, discount, 12-month rule (acquisition and event days excluded), indexation and deemed sale for events from 1 Jul 2027, minimum tax | Decide the event, the AUD proceeds, the parcel and cost base, then call it with `asset_type: crypto` (or `personal_use_asset` when the facts support it) |
| Several gains and losses | `net_capital_gain`: loss ordering before discount, collectable and personal use loss rules | Assemble the per-disposal results and pass them on |
| Personal use asset | Applies the exemption only when `asset_type: personal_use_asset` and the first element is at or below `individual.personal_use_asset_cgt_exempt_max_cost`; `personal_use_crypto_claim` only adds a warning | Decide whether the facts fit the ATO's narrow view and say why; never assume |
| Escalation | AU-CGT-005 already covers DeFi, lending, liquidity pools, staking derivatives, wrapping or bridging (draft TD 2026/D2), airdrops received in business, crypto trading business or trading stock | Add the crypto-specific gaps in section 5 |
| 2027 law | Date-effective rules by event contract date | Explain crypto-specific evidence (section 3.14), never recompute |
| Not covered by `cgt` | Income receipts (staking, services), parcel matching, record keeping, trader-vs-investor screen, lost or stolen assets, chain splits, GST or FBT pointers | This skill |

Existing `cgt` evals already cover `trap-crypto-swap-tax-free` (10 ETH swapped for SOL, cost 25,000, value 45,000) and `trigger-casual-bitcoin-sale`. Do not duplicate those facts.

## 3. Rules with citations

### 3.1 What crypto is for tax

| ID | Rule | Auth | Source |
|---|---|---|---|
| R-01 | Bitcoin holding rights are property, so a CGT asset under s 108-5(1)(a). The ATO applies the same reasoning to other crypto assets. TD 2014/26 issued 17 Dec 2014, consolidated 28 Nov 2019. | RULING, LAW | S-10 [R], S-01 [R], S-17 [R] |
| R-02 | Bitcoin is not "foreign currency" for Div 775 and transactions are treated like barter (TD 2014/25 paras 1 and 34). The statute now defines foreign currency as a currency other than Australian currency, digital currency, or a prescribed thing (s 995-1), where digital currency has the GST Act meaning. For tax purposes crypto is not a form of money. | RULING, LAW | S-09 [E], S-05 [R], S-22 [R] |
| R-03 | The relevant property is the bundle of holding rights over a keypair-controlled balance. A dealing in the private key or wallet is also capable of being a CGT event (TD 2014/26 paras 8, 13, 14). | RULING | S-10 [R] |
| R-04 | Each crypto asset you hold is a separate asset, even inside one wallet. | WEB | S-22 [R], S-25 [R] |
| R-05 | Government response (Mar 2025): no crypto-specific tax legislation at present; DAOs, DeFi, GameFi and NFTs flagged for possible later work. | Gov | S-52 [R] |

### 3.2 Disposals, timing, proceeds, acquisition date

| ID | Rule | Auth | Source |
|---|---|---|---|
| R-06 | CGT event A1 happens on disposal: a change of ownership to another entity. No change of ownership if you stop being the legal owner but remain the beneficial owner (s 104-10(1), (2)). Time of event: the contract date, or if no contract, when ownership changes (s 104-10(3)). A CGT event still happens even if the gain or loss is disregarded (s 102-23). | LAW | S-01 [R] |
| R-07 | ATO disposal list: sell; gift; trade, exchange or swap one crypto for another; convert to AUD or foreign currency; buy goods or services with crypto. Reinvesting into other tokens and paying for goods are reportable even with no cash received. | WEB | S-23 [R], S-24 [R], S-40 [R] |
| R-08 | Swap: you dispose of one CGT asset and acquire another. Capital proceeds are the AUD market value of what you receive (s 116-20(1)(b)). If the received asset cannot be valued (for example a token not yet listed), use the market value of the crypto you give up (s 116-30(2)(a)); the ATO swap page says the same. | LAW, WEB | S-01 [R], S-24 [R] |
| R-09 | Spending on goods or services: proceeds are the market value of what is received (s 116-20(1)(b)), with the s 116-30(2)(a) fallback. Gift card bought with crypto: proceeds are the gift card's market value. Loading a gift or debit card: proceeds are the increase in the card balance. Card denominated in crypto: each use is its own disposal (ATO example: card bought with 500 units at $1.00 each; 400 units spent when a unit was $0.95; capital loss $20). | LAW, WEB | S-01, S-32 [R] |
| R-10 | Gifting crypto is a disposal; with no proceeds you are taken to receive market value (s 116-30(1)). Receiving a gift is not a CGT event; keep the market value at receipt. Donations are disposals; the ATO lists narrow no-CGT cases for gifts to deductible gift recipients (gift under a will, Cultural Gifts Program, personal use crypto). | LAW, WEB | S-01, S-33 [R] |
| R-11 | Transfers between your own wallets are not disposals while you keep ownership. If the holding shrinks to pay a network fee, the fee is a disposal. Sending a fungible token to an address you do not control that already holds the same token is generally a CGT event (ATO, DeFi context). | WEB | S-27 [R], S-30 [R] |
| R-12 | Deposit with a centralised exchange: no ATO page read says whether that is a disposal. TD 2026/D2 para 3 excludes custodian counterparties. The exchange-failure page treats the customer as holding an interest in the exchange. INFERRED: s 104-10(2) turns on beneficial ownership under the account terms. | LAW, INFERRED | S-01, S-19 [R], S-37 [R] |
| R-13 | Valuation: every transaction, including swaps with no AUD leg, is recorded in AUD at market value at the time of the transaction. The ATO has used RBA exchange rates for foreign currency since 1 Jan 2020; where none is listed, any reasonable external rate. For crypto prices the ATO examples use the rate shown on a reputable exchange at the time. No approved daily-average shortcut was found. | WEB | S-23 [R], S-24 [R], S-40 [R] |
| R-14 | The asset received in a swap is acquired when the swap happens (s 109-5(1), (2) table, A1 case 1). The 12-month test excludes the day of acquisition and the day of the event (s 115-25(1); ATO). So a swap restarts the 12-month clock on the asset received. | LAW, WEB | S-01, S-44 [R] |
| R-15 | Cost base has 5 elements (s 110-25). First element for a purchase is the money paid; for a swap it is the market value of the property given (s 110-25(2)(b)). Incidental costs (s 110-35: broker or agent remuneration, costs of transfer, valuation costs) are the second element. ATO examples add AUD brokerage at acquisition and at swap to cost base rather than netting it off proceeds. The third element (ownership costs such as interest, only for assets acquired after 20 Aug 1991) does not apply to personal use assets (s 110-25(4) note; s 108-30). Foreign currency amounts are converted to AUD. | LAW, WEB | S-01 [R], S-27 [R], S-51 [E] |
| R-16 | Acquired with no payment (staking or DeFi rewards, prizes, payments in crypto, airdrops): the ATO pages state the first element is market value at receipt (nil if nil or negligible). The statutory route in s 112-20(1) requires an acquisition from another entity (Q-16). | WEB, DRAFT | S-28, S-30, S-34, S-35, S-18 |
| R-17 | Capital loss rules (defer to `cgt`): net capital loss cannot be deducted from other income and carries forward; personal use asset losses are disregarded (s 108-20(1)). | LAW | S-01 [R], S-25 [R] |
| R-18 | Anti-overlap: a capital gain is reduced to the extent an amount is assessable elsewhere (s 118-20), for example crypto already taxed as ordinary income. Gains and losses on trading stock are disregarded (s 118-25). | LAW | S-01 [R] |

### 3.3 Cost base and parcel identification (FIFO, specific identification, averaging)

| ID | Rule | Auth | Source |
|---|---|---|---|
| R-19 | TD 33 (19 Dec 1991; consolidated 1994): where identical holdings cannot be individually distinguished the taxpayer decides which were disposed of and must keep adequate records to support the decision; the Commissioner accepts first-in first-out and also accepts the taxpayer's own selection; average cost is not acceptable unless the units are in the same company, acquired the same day and carry identical rights (TD 33A). Its note (i) extends the determination to other identical assets that cannot be individually distinguished, "for example coins, stamps and units". | DET | S-13 [R] |
| R-20 | No crypto-specific ATO statement on FIFO, LIFO, HIFO or specific identification was found on the ATO crypto pages (updated 22 Jun 2026 to 1 Jul 2026). Applying TD 33 to crypto is by analogy through its note (i). The Board of Taxation (May 2024) recommended the ATO publish a position; the Government response (Mar 2025) left that to the ATO. Nothing published since was found. | INFERRED | S-13, S-52 [R], S-54 [E] |
| R-21 | Practical consequence: a method other than FIFO (for example highest cost first) is defensible only if contemporaneous records show which units were disposed of. Average cost across parcels bought on different days is not acceptable on the TD 33 reasoning. | DET, INFERRED | S-13 |
| R-22 | Parcels acquired by swap, staking, airdrop or split each carry their own acquisition date and cost base (R-14, R-16). | LAW | S-01 |

### 3.4 Personal use asset exemption

| ID | Rule | Auth | Source |
|---|---|---|---|
| R-23 | Statute. A personal use asset is a CGT asset (not a collectable) used or kept mainly for your or your associate's personal use or enjoyment (s 108-20(2)(a)). Capital losses on it are disregarded (s 108-20(1)). A capital gain on it, or on part of it, is disregarded if the first element of its cost base is **$10,000 or less** (s 118-10(3)); a fixed statutory amount. | LAW | S-01 [R] |
| R-24 | TD 2014/26 paras 17 to 21: whether bitcoin is used or kept mainly for personal use depends on the facts; relevant are the purpose it was acquired and kept for and what is bought with it. Kept or used mainly to buy items for personal use or consumption: ordinarily personal use. Kept for profit or investment, or to facilitate business or purchases of income-producing investments: not personal use. A miner who keeps coins for years to sell at good rates: not personal use. | RULING | S-10 [R] |
| R-25 | ATO web view (22 Jun 2026). The test is applied at disposal on how the asset was actually kept and used; the original intention is evidence, not the test. Acquired and used within a short time to buy personal items: more likely personal use. Held for some time, or only a small proportion spent: less likely. Investment holdings later spent are not personal use assets, and using returns to buy personal items does not change that. Example: $270 of crypto bought and spent on concert tickets the same day is a personal use asset. | WEB | S-26 [R] |
| R-26 | The ATO lists "rare situations" only where crypto is not a personal use asset if you: exchange it for AUD or another crypto to buy personal items; buy a gift card and spend that; top up a prepaid debit card; or use a payment gateway or bill payment intermediary (Bitpay, Coinbase, PayPal, Apple Pay and similar) to buy on your behalf. The 1 Jul 2026 investors toolkit example says the opposite for a one-off gateway use by a regular short-term personal spender (Q-05). | WEB | S-26 [R], S-27 [R] |
| R-27 | Sets: if personal use assets that would ordinarily be disposed of as a set are disposed of separately to try to obtain the exemption, they are taken to be one asset and each disposal a disposal of part (s 108-25). TD 2014/26 fn 18 says s 108-25 may apply to bitcoin disposed of in parts for this purpose. How that applies to fungible crypto is not settled (Q-05). | LAW, RULING | S-01 [R], S-10 [R] |
| R-28 | Collectables (artwork, jewellery, antiques, coins or medallions, rare folios, manuscripts, books, stamps or first day covers kept mainly for personal use or enjoyment; s 108-10(2)) use a separate threshold: gain or loss disregarded if the first element is $500 or less (s 118-10(1)); collectable losses only offset collectable gains (s 108-10(1)). ATO NFT examples: gaming NFT cards with no rights to the artwork are personal use assets, not collectables; an NFT giving a relative yearly private gallery viewings is personal use. The ATO says an NFT is a personal use asset only in rare circumstances. | LAW, WEB | S-01 [R], S-31 [R] |

### 3.5 Investor vs trader vs business; mining

| ID | Rule | Auth | Source |
|---|---|---|---|
| R-29 | ATO business page (29 Jun 2022): crypto held (a) in a crypto business (trading, mining, exchange, NFT selling) is trading stock, the cost is deductible and sales are assessable; (b) to exchange for goods or services in the ordinary course of any business is also trading stock; (c) as an investment is subject to CGT. Its worked example values leftover stock at year end using a fair market value from a reputable exchange. | WEB | S-45 [R] |
| R-30 | TD 2014/27: bitcoin held for sale or exchange in the ordinary course of a business is trading stock (s 70-10(1)); this includes bitcoin held by a mining or exchange business and bitcoin received as payment by a business that sells goods and holds it for sale or exchange (para 14). | RULING | S-11 [E] |
| R-31 | Business indicators (ATO 2022 crypto page and "Are you in business?" 2026): commercial reasons, viable, profit intention, planned and business-like, repeated regularly. High volume, large transactions or sophistication alone do not make a business. TR 97/11 (primary production; the principles apply generally) lists the indicators. | WEB, RULING | S-45 [R], S-47 [E], S-15 [E] |
| R-32 | Even without a business, a gain on an isolated transaction is ordinary income where the purpose was profit and the transaction was a commercial transaction; the CGT gain is then reduced under s 118-20. Relevant factors include amounts involved, magnitude of profit sought, holding time, and whether the asset has no use other than trade (TR 92/3 paras 6 and 13, and the explanation TD 2014/26 cites at para 49). Small hobby mining followed by a sale after two years to buy an investment: CGT, not ordinary income, and not a personal use asset. myTax 2026 repeats that profits on commercial disposals are ordinary income. | RULING, WEB | S-10 [R], S-14 [R], S-43 [R] |
| R-33 | Trading stock consequences: compare opening and closing value each year (s 70-35); closing value elected at cost, market selling value or replacement value per item (s 70-45); a small business entity (turnover under $10m per the ATO) may skip the stocktake if the estimated change in value is $5,000 or less (s 328-285(1)(b)). Starting to hold crypto you already own as trading stock is a deemed sale and rebuy at cost or market value by election (s 70-30); electing market value can trigger a capital gain (CGT event K4). | LAW, WEB | S-01 [R], S-03 [R], S-48 [R] |
| R-34 | An individual carrying on a business at a loss is subject to the non-commercial loss rules (Div 35); the `non_commercial_loss_test` tool exists. Not modelled in the crypto skill. | LAW, WEB | S-49 [E] |
| R-35 | Mining. Business miners (alone or via a pool): mined crypto is trading stock; mining services are taxable for GST to an Australian pool operator and GST-free to a non-resident operator; selling the digital currency received is an input taxed financial supply unless GST-free (page last updated 18 Nov 2022). Hobby miner: TD 2014/26 paras 21 and 24 only (a later sale is a CGT event). The ATO does not publish the cost base of hobby-mined coins or how pool payout schemes are characterised (Q-06). | WEB, RULING | S-46 [R], S-10 [R] |

### 3.6 Income receipts (staking, services, DeFi yield, prizes)

| ID | Rule | Auth | Source |
|---|---|---|---|
| R-36 | Staking and other consensus rewards (validators, proof of authority or credit, agent and guardian nodes, premium stakers, proxy staking, voting): ordinary income equal to the AUD money value of the tokens at the time received, declared as other income; cost base of the tokens is that market value; a later disposal is a separate CGT event. Ordinary income is s 6-5; non-cash money value is ITAA 1936 s 21(1). Page updated 19 Aug 2026. | LAW, WEB | S-28 [R], S-02 [R], S-06 [R] |
| R-37 | Timing under s 6-5(4): an amount is received when applied or dealt with on your behalf or as you direct. An edited private advice (2022) reasons that staking rewards locked or inaccessible until conditions are met are not received until you can withdraw or access them. EV: not binding, cannot be relied on. | LAW, EV | S-02 [R], S-17 [R] |
| R-38 | Payment for services or employment in crypto: assessable income at AUD market value when received; an employer must still meet PAYG withholding and super on that value; a fan or sponsor payment tied to your employment is assessable, not a gift; cost base is the market value at receipt. Valid salary sacrifice into crypto is a property fringe benefit (TD 2014/28); without a valid arrangement it is ordinary salary or wages. | WEB, RULING | S-35 [R], S-45 [R], S-12 [E] |
| R-39 | DeFi periodic rewards: report the AUD market value at receipt as assessable income; the ATO says taxed similarly to interest income; cost base is the market value at receipt. Renting crypto to another user for a share of rewards: ordinary income at market value (EV). | WEB, EV | S-30 [R], S-17 [R] |
| R-40 | Prizes and gambling: lottery, raffle and game-show prizes are generally not ordinary income, and gains or losses directly from gambling are ignored for CGT. A crypto prize later held as an investment has a cost base equal to market value when won. | WEB | S-34 [R] |

### 3.7 Airdrops (DRAFT TR 2026/D1)

Draft ruling "Income tax: receipt and disposal of crypto assets by an airdrop", issued 19 Aug 2026, comments due 16 Oct 2026. It addresses Australian resident taxpayers. A taxpayer who relies on it reasonably and in good faith and is proved wrong avoids interest and penalties but still owes the tax (S-18 [R]).

| ID | Rule (paragraph of the draft) | Source |
|---|---|---|
| R-41 | Recipient carrying on a business of crypto asset trading: market value of any airdropped crypto is ordinary income under s 6-5 even if unsolicited or a windfall (13). | S-18 |
| R-42 | Airdropped in return for goods or services: money value is ordinary income (s 6-5 with ITAA 1936 s 21) (14). Example 2 (an influencer given 100,000 coins for actively promoting the platform) is ordinary income. The draft lists "bounty airdrops" (simple tasks such as posting or signing up) as a type but does not say in terms whether they are income (Q-17). | S-18 |
| R-43 | Non-business recipient with no services and no income-producing activity: not ordinary income (16, 75); capital account (84); the airdropped asset is a separate CGT asset from any underlying coin that qualified you (16, 83); A1 on later disposal (17). Hobby or entertainment receipt: no income and no deduction for costs (21). | S-18 |
| R-44 | Cost base: where s 112-20 applies the first element is market value when acquired; nil or negligible market value means nil (20, 85 to 87). An established token has a market value; a newly minted token with no or negligible market value is generally nil. Wallet clean-up costs go in the second element in the draft (51); the ATO web page says "cost base" (Example 5). | S-18, S-28 |
| R-45 | Not covered by the draft (9): receiving crypto in exchange for AUD or other crypto; airdrops as a reward for providing liquidity to a DEX; non-arm's-length transactions; rebasing tokens. | S-18 |
| R-46 | Issuer: A1 when issued; deemed proceeds market value; gain or loss disregarded if the coin is trading stock (15; s 116-30(1); s 118-25). | S-18 |
| R-47 | Date of effect (66): proposed to apply before and after the final issue date, except **initial allocation airdrops** (the first distribution where nothing had traded before), which the final ruling would cover only for airdrops after its issue date. What applies to an earlier initial allocation is not addressed (Q-08). | S-18 |
| R-48 | A phishing offer whose tokens never reach your wallet: nothing received, no CGT asset, no income (Example 4). | S-18, S-28 |

### 3.8 Chain splits and forks

TD 2014/26 does not deal with chain splits and no public ruling on the topic was found. The ATO position is web guidance (S-29, updated 22 Jun 2026 [R]).

| ID | Rule | Source |
|---|---|---|
| R-49 | As an investor, a new crypto asset received because of a chain split is neither ordinary income nor a capital gain when received. Its cost base is nil. A later disposal is a CGT event and the 12-month discount can apply once held 12 months. In carrying on a business it "may be treated differently". | S-29 |
| R-50 | Work out which side is new: if one asset keeps the same rights and relationships as the original it is the continuation and the other is new. ATO Ethereum Classic example: the chain that rejected the protocol change is the continuation; the ETH the holder now has is the new asset, acquired on the split date. | S-29 |
| R-51 | If nothing continues the original (both sides changed core rules), CGT event C2 happens to the original at the split; each asset now held is new, acquired on the split date with nil cost base. ATO example: original cost base $8,300, capital loss $8,300, both new assets nil. Statute note: for C2, proceeds are replaced by market value (worked out as if the event had not occurred) where actual proceeds are less (s 116-30(2)(b)(ii), (3A)); the ATO example does not discuss this, so do not assert beyond the ATO example. | S-29, S-01 |

### 3.9 Wrapping, DeFi, liquidity pools (mostly escalate)

| ID | Rule | Auth | Source |
|---|---|---|---|
| R-52 | Wrapping through a lock-and-mint smart contract. Wrap: CGT event C2 when the original coin is sent to the contract (ownership ends by abandonment; alternatively surrender or release). Proceeds: market value of the wrapped token received (if less than the value sent because of a fee, the market value of the coin sent). Cost base of the wrapped token: market value of the original at that time. Unwrap: C2 when the wrapped token is burnt; proceeds: market value of the coin released; cost base of the new coin: market value of the token burnt. They are separate CGT assets. No ordinary income arises and s 118-20 does not reduce the gain. | DRAFT | S-19 [R] |
| R-53 | TD 2026/D2 limits: only the described smart-contract arrangement; not custodian transfers; not businesses or isolated commercial transactions; gas and platform fees expressly not addressed; A1 rejected (no counterparty); C1 would be the fallback with substantially the same result (most specific event applies, s 102-25(1)); Subdiv 124-B replacement rollover not available; s 106-60 not accepted. Issued 19 Aug 2026, comments close 2 Oct 2026, proposed to apply before and after issue. ATO advice-under-development page (7 Sep 2026): final "to be advised". | DRAFT | S-19 [R], S-21 [R] |
| R-54 | DeFi "lending" or "borrowing" often ends beneficial ownership, so it is a CGT event: proceeds are the market value of what you receive (another crypto, or a right to receive equivalent tokens later). ATO examples: 50 coins that cost $400 lent when worth $500, gain $100; a pooled loan of 100 coins that cost $1,000 when worth $900 gives a $100 loss and a right with cost base $900, then repayment when the coins are worth $1,000 gives a $100 gain. Securities lending rules do not apply. Most likely events: A1, E2, C2, H2; the most specific applies; the terms and actual operation of the protocol decide. | WEB | S-30 [R] |
| R-55 | Liquidity pools: depositing is a CGT event (proceeds are the market value of LP tokens or rights received); withdrawing is a CGT event on the LP token or right (proceeds are the market value withdrawn). ATO Example 3: 1 unit that cost $2 for 20 pool tokens worth $20, gain $18, discount can apply. | WEB | S-30 [R] |
| R-56 | Bridging, liquid staking, restaking, staking through custodians, derivatives, margin, perpetuals, crypto-backed loans: not covered by any ATO material read. Escalate (E-03). | INFERRED | S-19, S-30 |

### 3.10 Lost, stolen, scammed, exchange failure

| ID | Rule | Auth | Source |
|---|---|---|---|
| R-57 | CGT event C1 happens if an asset you own is lost or destroyed. Time of event: when compensation is first received, or if none, when the loss is discovered. The capital loss uses the reduced cost base (s 104-20). | LAW | S-01 [R] |
| R-58 | ATO (22 Jun 2026): a capital loss is claimable for lost or stolen crypto if you can evidence ownership and loss of access. Something recoverable (for example from a hard drive) is not lost; a lost private key cannot be recovered. Compensation reduces the loss and can create a gain if it exceeds cost base; a rollover may be chosen if compensation is received and another crypto asset is acquired within a year of the end of the income year. Example: 2 ETH cost $2,672, key found lost 21 May 2026, loss $2,672 in 2025-26. Evidence list: public key, dates key acquired and lost, wallet address, acquisition cost, value when lost, proof of control, hardware, verified exchange history. | WEB | S-36 [R], S-40 [R] |
| R-59 | Exchange or platform in external administration: the CGT event generally happens when administration is finalised; distributions first reduce cost base, and later distributions above cost base are gains; a loss cannot be worked out before the event. | WEB | S-37 [R] |

### 3.11 Residency

| ID | Rule | Auth | Source |
|---|---|---|---|
| R-60 | Resident (not also a temporary resident): tax on all crypto income and capital gains worldwide, wherever sourced. Foreign resident or temporary resident: tax only on Australian-sourced income; crypto has no physical location so source turns on where the activity or service was performed, where the platform or exchange is, and where payer and payee are. | WEB, LAW | S-38 [R], S-02 [R] |
| R-61 | A foreign resident disregards gains and losses on assets that are not taxable Australian property (s 855-10). Crypto is only TAP if used in carrying on a business through an Australian permanent establishment (s 855-15 item 3) or after an individual chose to disregard CGT event I1 on ceasing residency (s 104-165(3); s 855-15 item 5). | LAW, WEB | S-04 [R], S-38 [R] |
| R-62 | Ceasing residency: CGT event I1 treats each non-TAP asset as sold at market value at that time (s 104-160); an individual may choose to disregard the gain or loss, and the asset then stays TAP until sold or residency resumes (s 104-165). ATO example: Bitcoin cost $10,000, worth $22,000 on leaving; gain $12,000 or choose to disregard, and a later sale at $52,000 gives $42,000 taxable in Australia. Becoming a resident: first element of cost base is market value at that time and the asset is treated as acquired then (s 855-45) for non-TAP assets acquired on or after 20 Sep 1985. Temporary residents have special rules (s 768-950, referred to in s 855-45); escalate. | LAW, WEB | S-01, S-04, S-38 |
| R-63 | Indexation from 1 Jul 2027 needs the individual to be neither a foreign nor a temporary resident at any time from the later of 1 Jul 2027 and acquisition to the event (s 114-25). The discount is apportioned for foreign or temporary residency after 8 May 2012 (ATO discount page; `cgt`). | LAW, WEB | S-01 [R], S-44 [R] |

### 3.12 GST, FBT and payroll pointers (route out; do not compute here)

| ID | Rule | Auth | Source |
|---|---|---|---|
| R-64 | For GST, "digital currency" is a fungible, freely usable unit not denominated in a country's currency and with no value tied to something else (Bitcoin, Ethereum and Litecoin named). NFTs are not digital currency (taxable unless GST-free). Pegged stablecoins are not digital currency (input taxed financial supply unless GST-free). Paying with digital currency is not itself a supply (GST Act s 9-10(4)); selling digital currency for money or other digital currency is an input taxed financial supply unless the counterparty is a non-resident (GST-free). Route to `gst-bas`. | WEB, RULING | S-50 [R], S-20 [E] |
| R-65 | Crypto salary: PAYG withholding and super on the AUD value; valid salary sacrifice is a property fringe benefit (R-38). Route to `payroll-sg` and `fbt`. | WEB | S-45 [R], S-35 [R] |

### 3.13 Records, data matching, reporting

| ID | Rule | Auth | Source |
|---|---|---|---|
| R-66 | Statute (s 121-20): keep records of every act, transaction, event or circumstance that can reasonably be expected to be relevant to whether you made a gain or loss (past or future events); in English or readily convertible; showing nature, date, who did it or who the parties were, and amounts; **if records do not exist you must reconstruct them** (a valuation may be needed); penalty 30 penalty units, strict liability. Retention (s 121-25(2)): until the end of 5 years after it becomes certain no CGT event (or no further event) can happen for which the records could be relevant. | LAW | S-01 [R] |
| R-67 | ATO records list: receipts, date of each transaction, purpose and counterparty (a wallet address suffices), exchange records, AUD value at the time of each transaction, agent, accountant and legal costs, wallet records and keys, software costs for managing tax affairs. Export history regularly (at least every 3 months), export fully before closing an account, use a blockchain explorer or the exchange to rebuild lost records. The web summary "5 years from the later of preparing the record, completing the transaction, or the CGT event year" is looser than the statute; use s 121-25(2). Page last updated 23 Jun 2025. | WEB | S-39 [R] |
| R-68 | ATO tax professionals newsroom (29 Jun 2026), top errors: relying on exchange records; not backing up; not recording AUD value of swaps; not reporting staking or airdrop income; not reporting disposals with no cash; treating investment crypto as personal use; lost crypto and scams need evidence. | WEB | S-40 [R] |
| R-69 | Data matching: the ATO protocol covers 2014-15 to 2025-26 (notice April 2024, Gazette C2024G00249). Data from crypto designated service providers: identity details and transactions (wallet addresses, dates, times, type, quantities, coin type); about 700,000 to 1,200,000 individuals and entities each year; collected annually April to July; retained 7 years. myTax 2026 pre-fills an indicator that you may have a crypto CGT event. Discrepancies are put to taxpayers, who have up to 28 days to verify before administrative action. No newer program period was found. | WEB | S-41 [R], S-08 [E], S-43 [R] |
| R-70 | CARF and domestic crypto reporting: announced 17 Dec 2025 (MYEFO 2025-26); the ATO page says "not yet law" and that the first CARF exchange is expected in 2028. | WEB | S-42 [R] |

### 3.14 The 1 July 2027 change: what is crypto-specific (arithmetic stays in `cgt`)

Sources for all: Treasury Laws Amendment (Tax Reform No. 1) Act 2026, No. 49, as compiled into ITAA 1997 (S-01 [R], S-05 [R], S-07), and the Treasurer's release (S-53 [R]).

| ID | Rule | Note |
|---|---|---|
| R-71 | Discount percentage 50% only for an individual's gain from a CGT event before 1 Jul 2027 (s 115-100(aa)); trusts likewise (ab); complying super one-third; new residential dwellings are the exception. Indexation of all cost base elements except the third applies to events from 1 Jul 2027, only if acquired at least 12 months before the event and the residency test is met (ss 110-36(1A), 114-10, 114-25). | Crypto is not a dwelling, so the exceptions do not apply. |
| R-72 | Resident individuals holding an asset on 30 Jun 2027 are taken to sell it just before 1 Jul 2027 at market value and reacquire it (s 112-155). The notional gain or loss is deferred to the year of the real disposal (s 112-160). A deferred gain is a discount gain if the asset was held 12 months up to the real disposal, ignoring the deemed sale for that count (ss 112-160(5), 114-10(9)). | "Market value just before 1 July 2027" is not defined further; for a 24 hour market no ATO guidance on the instant, time zone or price source was found (Q-09). |
| R-73 | The choice between market value and an apportioning method is made when lodging the return for the year of the real disposal (s 112-155(4), Note 2). The Minister may determine the method (s 112-185). The 4 Aug 2026 exposure draft instrument is described as covering real property and assets without a readily ascertainable market value; consultation closed 21 Aug 2026; not law. INFERRED: a coin with a public exchange price has a readily ascertainable market value, so keep price evidence for just before 1 Jul 2027 for every parcel likely to be sold after that date. | Q-10. |
| R-74 | Any CGT event other than E4, E10 and G1 is a realisation event (s 977-5), so a swap, spend, gift or C2 after 30 Jun 2027 recognises the deferred gain or loss on the asset given up in that year (s 112-160). The asset received starts fresh (new acquisition date, first element market value of what was given), so its 12-month test for indexation restarts. | Deferred gain is discounted only if the old parcel meets the 12-month test. |
| R-75 | Rewards and airdrops received after 30 Jun 2027 get a first element equal to market value at receipt (R-16); indexation, if held 12 months, follows the `cgt` tools. Div 119 minimum tax may apply to resident individuals' post-1 Jul 2027 gains (`cgt`). | CPI index numbers for future quarters are unpublished; the tools show an upper bound. |

## 4. Traps

D = deterministic (a number or yes/no is safe to assert). J = judgement rubric. E = escalation case.

| ID | Wrong belief or common error | What is right | Rules | Use |
|---|---|---|---|---|
| T-01 | "A crypto-to-crypto swap is not taxable until I cash out to AUD." | A1 at the swap; proceeds are the AUD value of what was received | R-07, R-08 | D (W-01) |
| T-02 | "Moving coins to another wallet or my exchange is a sale" or, opposite, "paying gas is nothing" | Own-wallet transfer is not a disposal; a network fee paid in crypto is a disposal of that crypto | R-11 | J |
| T-03 | "Spending crypto on goods is not a sale" | It is a disposal at the AUD value of what you receive | R-09 | D |
| T-04 | "Held over 12 months means exempt" | 12 months gives the discount (50% before 1 Jul 2027), not exemption; and a swap restarts the clock on what you receive | R-14 | D |
| T-05 | "I spent some on a laptop so it is a personal use asset" | Investment holdings later spent are not personal use assets; PUA needs acquired-and-used-mainly for personal consumption, usually quickly | R-24, R-25 | D (W-03 E) |
| T-06 | "The threshold is under $10,000" | Statute: $10,000 or less. Two ATO web pages say "less than $10,000"; the statute, TD 2014/26 para 17, myTax 2026 and an edited private advice say "$10,000 or less". Assert the statute; accept answers that note the wording difference | R-23 | D only if the grader accepts the note |
| T-07 | "My loss on crypto I bought and spent for personal use can offset gains" | PUA losses are disregarded | R-23 | D (W-03 D) |
| T-08 | Splitting a large parcel into sub-$10,000 disposals to reach the exemption | s 108-25 may treat a set as one asset; TD 2014/26 fn 18 flags it for bitcoin; application is unsettled | R-27 | J only (Q-05) |
| T-09 | "Staking rewards have nil cost base and are only taxed when sold" or "taxed at the 50% discount" | Ordinary income at receipt at AUD market value; that value is the cost base; only a later gain can attract the discount | R-36 | D (W-02) |
| T-10 | "A forked coin is income when it arrives" or "inherits my old cost and date" | No income and no gain at receipt; nil cost base; acquisition date is the split date; work out which side is the continuation | R-49 to R-51 | D (W-04) |
| T-11 | "Airdrops are always income" or "never income" | Depends on character: business, services: income; unsolicited holder airdrop to a non-business investor: not income, cost base market value | R-41 to R-44 | J, draft label (W-05) |
| T-12 | "The ATO says wrapping is tax free" | Draft TD 2026/D2: C2 on wrap and on unwrap; draft only, comments to 2 Oct 2026 | R-52, R-53 | J, must label draft (W-06) |
| T-13 | "The draft rulings are final law" | They are preliminary views; web pages updated 19 Aug 2026 mirror them | R-47, R-53 | J |
| T-14 | "Lots of trades or holding long decides investor vs trader" | Volume or sophistication alone is not the test; purpose, commerciality, regularity, organisation decide; a profit-making commercial isolated transaction can be ordinary income | R-31, R-32 | E |
| T-15 | "No records, so cost base is nil" | s 121-20(5) requires reconstruction; the ATO says exchange statements alone are not enough; nil is not the legal default | R-66, R-67 | J |
| T-16 | "Average cost across my buys is fine" | Not on TD 33 reasoning (except same-day identical units); FIFO or a documented selection | R-19 to R-21 | J |
| T-17 | "The UTC timestamp decides the date" | INFERRED: the Australian local date fixes the income year (and the 1 Jul 2027 regime). A swap at 14:45 UTC on 30 Jun 2027 is 00:15 ACST on 1 Jul 2027. No primary source fixes the convention | Q-09 | J only, never a hard expectation |
| T-18 | "Stablecoins are cash, so moving into USDC is not a sale" | Crypto is not money or foreign currency; BTC to a stablecoin is a swap; stablecoin to AUD is a disposal | R-02 | D |
| T-19 | "Lost or hacked crypto is an automatic loss" | Evidence of ownership and loss of access; recoverable is not lost; timing is discovery or first compensation; compensation reduces the loss | R-57, R-58 | J |
| T-20 | "Foreign resident crypto gains are taxable in Australia" or "residents can ignore foreign exchanges" | Foreign resident: gains disregarded unless TAP, but Australian-source ordinary income is taxable; residents are taxed worldwide; I1 on leaving; s 855-45 reset on arriving | R-60 to R-62 | J (Bali cases) |
| T-21 | "Sell at a loss on 30 June and rebuy on 1 July" | TR 2008/1 covers wash sales of CGT assets under Part IVA; escalate | S-16 | E |
| T-22 | "The 50% discount continues after 1 Jul 2027" | Only for the deferred pre-2027 part of a held asset; new events get indexation (12 months) and possible minimum tax | R-71, R-72 | D on the deferred part only (W-08) |
| T-23 | "I can use the formula method for my crypto" | The draft instrument targets real property and assets without a readily ascertainable market value; coins with exchange prices need market value evidence | R-73 | J |
| T-24 | "GST applies to buying and selling Bitcoin" | Digital currency is not a taxable supply; NFTs and stablecoins differ | R-64 | J, route out |
| T-25 | "A client's or fan's crypto payment is a gift" | A payment related to work is assessable at market value | R-38 | D (W-09) |

## 5. Escalation triggers and suggested codes

`AU-CGT-005` (existing) states: DeFi, lending or borrowing, liquidity pools, staking derivatives, wrapping or bridging (draft TD 2026/D2), airdrops received in business, crypto held as trading stock or in a business of trading. Reuse it for those. The gaps below are proposals for `data/refusals/crypto.yaml` (the skill-builder decides names; a code must be added there before any skill text uses it).

| ID | Trigger | Why not computable | Existing code | Proposed |
|---|---|---|---|---|
| E-01 | Facts suggest a business or commercial profit-making scheme (frequent trading, profit purpose, business-like organisation, crypto received as payment held for sale) | Fact-heavy characterisation; revenue treatment, trading stock, GST, Div 35 | AU-CGT-005 covers "trading business" | AU-CRYPTO-001 (character screen) |
| E-02 | Mining (any) or pool payouts | Cost base and characterisation unpublished; GST | AU-CGT-005 partly | AU-CRYPTO-002 |
| E-03 | Bridging, liquid staking or restaking, custodial staking, perps, options, margin, crypto-backed loans, NFT lending or renting, DAO tokens | Not covered by ATO material; terms decide the CGT event | AU-CGT-005 | reuse |
| E-04 | Wrap or unwrap (draft TD 2026/D2) | Draft; alternative views; fees not addressed | AU-CGT-005 | reuse; may explain the draft view |
| E-05 | Airdrop received by a trading business; initial allocation before the final ruling; rebasing tokens; liquidity-reward airdrops; bounty airdrops | Outside or not yet covered by draft TR 2026/D1 | AU-CGT-005 covers "in business" only | AU-CRYPTO-003 for the rest |
| E-06 | Exchange or platform in administration, hacked exchange, compensation or insurance, recovery claims | Timing and distributions; possible rollover | none | AU-CRYPTO-004 |
| E-07 | Lost key, theft or scam with weak evidence, or a claim larger than the evidence supports | Evidence quality decides whether a loss is real | none | AU-CRYPTO-004 |
| E-08 | Holder is a company, trust, SMSF or other fund | Different discount, streaming and 1 Jul 2027 trust or fund rules | AU-CGT-003 | reuse |
| E-09 | Foreign resident, temporary resident, part-year resident, ceasing or becoming resident, treaty question, Bali or other overseas income source | Residency, I1, s 855-45, s 768-950, apportioned discount, draft rules for mixed residents | AU-CGT-007, `residency-cross-border` | reuse or AU-CRYPTO-005 |
| E-10 | Crypto paid as salary, salary sacrifice, third-party work payments at scale | PAYG, super, FBT | none | route to `payroll-sg`, `fbt` |
| E-11 | NFT creation, minting, royalties, marketplaces, collectable classification | Business, GST, collectable vs PUA | AU-CGT-004 (other events) | AU-CRYPTO-006 |
| E-12 | Gifts to family at scale, donations to DGRs, deceased estate holdings, relationship breakdown transfers | Rollovers, estates, deductions | AU-CGT-002, AU-CGT-004 | reuse |
| E-13 | Loan-funded purchase, interest deductibility, margin lending | Deductibility of interest for non-yielding crypto; third element | none | AU-CRYPTO-007 or general |
| E-14 | Year-end loss harvesting or round-trip trades (sell and rebuy) | TR 2008/1 (Part IVA) | none | AU-CRYPTO-008 |
| E-15 | Worthless, delisted or depegged tokens, "negligible value" claims | No ATO guidance found on realising a loss without a disposal (Q-14) | none | AU-CRYPTO-004 |
| E-16 | Personal use claims that depend on payment gateways, split disposals, mixed use, or purchases above the threshold | ATO pages conflict; s 108-25 unsettled | none | J only (T-06, T-08) |
| E-17 | Market value just before 1 Jul 2027 needed but not provided | Valuation evidence | AU-CGT-006 | reuse |
| E-18 | Asked to lodge, pay, or prepare BAS or an ATO response | Not in scope | AU-GEN-002 | reuse |

Suggested risk flags (proposals for `data/risk_flags/crypto.yaml`; fields id, topic, description, citations, skills): CRYPTO-SWAP-DISPOSAL (R-08); CRYPTO-AUD-VALUATION (R-13); CRYPTO-FEES-IN-CRYPTO (R-11, Q-02); CRYPTO-PARCEL-IDENTIFICATION (R-19 to R-21); CRYPTO-PUA-NARROW (R-23 to R-27); CRYPTO-CHARACTER-SCREEN (R-31, R-32); CRYPTO-STAKING-INCOME (R-36); CRYPTO-DRAFT-RULINGS (R-47, R-53; extends the existing CGT-CRYPTO-DRAFTS); CRYPTO-CHAIN-SPLIT (R-49 to R-51); CRYPTO-LOSS-EVIDENCE (R-57, R-58); CRYPTO-RECORDS (R-66 to R-68); CRYPTO-DATA-MATCHING (R-69); CRYPTO-RESIDENCY (R-60 to R-62); CRYPTO-2027-VALUATION (R-72, R-73; extends CGT-2027-VALUATION); CRYPTO-WASH-SALE (TR 2008/1).

## 6. Worked examples

Assumptions: resident individual, AUD values as stated, event before 1 Jul 2027 unless noted, discount 50% (key `cgt.discount_individual_trust`), losses applied before the discount, no other gains or losses, whole dollars. Arithmetic checked by hand and with plain arithmetic, not with the project's calculators (CONVENTIONS section 5: never generate expected values from our own code).

### W-01 Swap BTC for ETH (investor, held over 12 months)

Facts: 0.50 BTC bought 3 Mar 2025 for $60,000 plus a $150 exchange fee paid in AUD. Swapped 18 Nov 2026 for 12.0 ETH on a reputable exchange; the exchange shows 12.0 ETH worth $84,000 at that moment ($7,000 each). Swap fee $120, paid in AUD.

1. Event: CGT event A1 on 18 Nov 2026, income year 2026-27 (R-06, R-08).
2. Capital proceeds: market value of what was received, $84,000 (s 116-20(1)(b); ATO swap example).
3. Cost base: first element $60,000 + incidental acquisition cost $150 + incidental cost of the swap $120 = $60,270 (R-15).
4. Capital gain: $84,000 - $60,270 = $23,730.
5. Holding: 3 Mar 2025 to 18 Nov 2026 is over 12 months excluding the acquisition and event days, so a discount capital gain (R-14).
6. Discount: $23,730 x 50% = $11,865; net capital gain $11,865 (statutory income; tax at marginal rates not computed here).
7. The 12.0 ETH: acquired 18 Nov 2026, first element $84,000 (market value of the BTC given up). The $120 fee is kept in the disposed asset's cost base as in the ATO's own example; the ATO says nothing on adding it again to the new asset, so do not (Q-03). The ETH's 12-month clock starts 18 Nov 2026.
8. Wrong answers to catch: "no tax until AUD"; gain worked out from $60,000 only; ETH treated as acquired 3 Mar 2025.

### W-02 Staking rewards then disposal (2026-27, no discount)

Facts: an investor stakes Token S. Reward 1: 2.0 units received 14 Sep 2026 at $240 per unit. Reward 2: 1.5 units received 9 Dec 2026 at $270 per unit. On 3 Feb 2027 all of reward 1 is sold at $310 per unit with a $10 AUD fee. On 5 Mar 2027 all of reward 2 is sold at $220 per unit, no fee.

1. Ordinary income at receipt: reward 1 = 2.0 x $240 = $480; reward 2 = 1.5 x $270 = $405; total other income $885 in 2026-27 (R-36).
2. Cost base: reward 1 = $480; reward 2 = $405 (market value at receipt).
3. Reward 1 sale: proceeds 2.0 x $310 = $620; cost base $480 + $10 fee = $490; gain $130. Held under 12 months, no discount.
4. Reward 2 sale: proceeds 1.5 x $220 = $330; reduced cost base $405; capital loss $75.
5. Net: $130 gain - $75 loss = net capital gain $55.
6. Return outcome: other income $885 and net capital gain $55.
7. Wrong answers: nil cost base gives gains $610 and $330 (total $940), taxing the $885 twice; treating the rewards as untaxed until sold.

### W-03 Personal use asset: six cases (resident individuals, events in 2026-27)

| Case | Facts | Result |
|---|---|---|
| A under | $400 of crypto bought 3 Oct 2026, all spent 6 Oct 2026 on a concert ticket priced $430 | Personal use (acquired and used within days for personal consumption). Gain $430 - $400 = $30 disregarded (first element $400 is $10,000 or less). A1 still happens (s 102-23); nothing to report |
| B at threshold | $10,000 of crypto bought 1 Feb 2027, all spent 5 Feb 2027 on personal items priced $10,600 | Gain $600 disregarded: $10,000 or less (s 118-10(3)). ATO web pages saying "less than $10,000" differ (T-06) |
| C over | $12,000 of crypto bought 1 Mar 2027, all spent within two weeks on furniture worth $12,900 | Personal use, but first element $12,000 exceeds $10,000, so the $900 gain is not disregarded; held under 12 months so no discount; $900 taxable capital gain |
| D loss | $9,000 of crypto bought 1 Mar 2027, spent 4 Mar 2027 on a personal item worth $8,500 | Loss $500 disregarded (s 108-20(1)); cannot offset any gain |
| E investment | $5,000 of crypto bought 10 Jan 2026 to sell later at a better price; 20 Nov 2026 all spent on a laptop priced $8,000 | Not a personal use asset (held as an investment). A1: gain $8,000 - $5,000 = $3,000. Under 12 months (10 Jan 2026 to 20 Nov 2026), so no discount; $3,000 taxable |
| F investment, over 12 months | as E but spent 20 Mar 2027 | Gain $3,000; discount 50% = $1,500 net capital gain |

Case B, split-parcel variations and payment-gateway variations are not deterministic expectations (T-06, T-08, E-16).

### W-04 Chain split, original continues (2026-27 sale)

Facts: an investor holds 4 units of Coin P, cost base $8,000. On 12 Aug 2025 a chain split creates Coin Q; Coin P carries the original rights, so Coin Q is new and 4 units of it are received. On 20 Oct 2026 the investor sells 2 units of Q for $900 each.

1. At the split: no income and no capital gain (R-49). Coin Q first element nil, acquired 12 Aug 2025.
2. Sale: proceeds 2 x $900 = $1,800; cost base nil; capital gain $1,800.
3. Held from 12 Aug 2025 to 20 Oct 2026: over 12 months, so discount 50% = $900; net capital gain $900.
4. Coin P: unchanged cost base $8,000 and original acquisition date.
5. Variant (nothing continues): C2 on the original at the split with a capital loss equal to its cost base per the ATO example (R-51); both new assets nil cost base acquired on the split date.

### W-05 Airdrops (DRAFT TR 2026/D1 view; label as preliminary)

(a) Non-business investor, established token, holder airdrop. 5,000 tokens land in the wallet on 10 Feb 2026 while the token trades at $0.40. No ordinary income (R-43). First element 5,000 x $0.40 = $2,000 (R-44). Sold 20 Feb 2027 for $3,500: gain $1,500, held over 12 months, discount $750, net capital gain $750.

(b) Newly minted token with no observable price at receipt. First element nil (R-44). Sold 13 months later for $900: gain $900, discount $450. Whether an earlier initial allocation airdrop is covered is unsettled (R-47, Q-08).

(c) Reward for services (an influencer paid in tokens for promoting a project). 60,000 tokens at $0.002 each = $120 ordinary income when received; cost base $120 (R-42).

(d) Recipient runs a crypto trading business. Market value at receipt is ordinary income and the tokens are trading stock (R-41). Escalate the rest.

### W-06 Wrap and unwrap (DRAFT TD 2026/D2 view; label as preliminary)

Facts: 3.0 ETH bought 15 Feb 2024 for $7,500. Wrapped 10 Oct 2026 through a lock-and-mint contract; the 3.0 WETH received are worth $13,500. Unwrapped 20 Mar 2027; the 3.0 ETH released are worth $12,300. Gas ignored (the draft does not address it).

1. Wrap: C2 on 10 Oct 2026. Proceeds $13,500 (market value of WETH received); cost base $7,500; gain $6,000, held over 12 months so discount-eligible. WETH first element $13,500, acquired 10 Oct 2026.
2. Unwrap: C2 on 20 Mar 2027. Proceeds $12,300; reduced cost base of the WETH $13,500; capital loss $1,200. New ETH first element $12,300, acquired 20 Mar 2027.
3. 2026-27 net: loss applied before the discount: ($6,000 - $1,200) x 50% = $2,400 net capital gain.
4. Caveats: draft, comments close 2 Oct 2026; the ATO acknowledges alternative views (R-53).

### W-07 Lost private key (C1)

Facts: 0.8 BTC bought 5 May 2025 for $48,000 all-in. Hardware wallet and seed lost; loss discovered 12 Feb 2027; no compensation; ownership evidence held (R-58).

1. C1 on discovery, 12 Feb 2027, income year 2026-27 (s 104-20(2)(b)).
2. Proceeds nil; reduced cost base $48,000; capital loss $48,000.
3. The loss cannot reduce salary or other income; it offsets capital gains in 2026-27 or carries forward.
4. Variant: $10,000 compensation first received 1 Apr 2027: C1 time is 1 Apr 2027; proceeds $10,000; loss $38,000. If compensation were first received after 30 Jun 2027 the event date and income year would move to that receipt.

### W-08 Crypto held across 1 Jul 2027 (deferred discounted part only)

Facts: 1.0 BTC bought 10 Jan 2026 for $100,000 all-in. Market value just before 1 Jul 2027, evidenced from exchange data: $140,000. Sold 15 Mar 2028 for $155,000. Resident individual throughout.

1. Deemed sale 30 Jun 2027 at $140,000; reacquisition 1 Jul 2027 at $140,000 (s 112-155).
2. Initial notional gain $140,000 - $100,000 = $40,000, deferred to 2027-28 (s 112-160).
3. Held from 10 Jan 2026 to 15 Mar 2028, over 12 months ignoring the deemed sale, so the deferred gain is a discount gain: $40,000 x 50% = $20,000 (before losses).
4. Post-1 Jul 2027 part: proceeds $155,000, cost base $140,000 indexed from 1 Jul 2027; the nominal gain of $15,000 is an upper bound. Indexation needs CPI numbers for quarters not published as at 29 Sep 2026, so use the `cgt` tool output; no discount applies; Div 119 minimum tax may apply.
5. For scale only (not the law for this event): a sale for $155,000 before 1 Jul 2027 would give a gain of $55,000, discounted to $27,500.
6. Eval-safe assertions: deemed proceeds $140,000, deferred gain $40,000, discounted deferred amount $20,000, post-July gain at most $15,000 nominal, no 50% discount on the post-July part, valuation evidence required.

### W-09 Crypto received for services

Facts: a freelancer is paid 0.05 BTC on 4 Nov 2026 when BTC is $150,000; swaps it on 20 Dec 2026 for ETH worth $7,900.

1. Ordinary income on 4 Nov 2026: 0.05 x $150,000 = $7,500 (R-38). Cost base of the 0.05 BTC: $7,500 (ATO business page example).
2. Swap: proceeds $7,900; cost base $7,500; gain $400; under 12 months, no discount.
3. Wrong answers: no income until swapped; a gain of $7,900 (double tax); calling it a gift.

### W-10 Year-end boundary and time zone (INFERRED convention; judgement case only)

A swap executes at 14:45 UTC on 30 Jun 2027. In South Australia (ACST, UTC+9:30) that is 00:15 on 1 Jul 2027; in AEST it is 00:45 on 1 Jul 2027. If Australian local time governs, the event is on 1 Jul 2027: income year 2027-28 and, for individuals, outside the deemed-sale regime for that asset. No primary source found fixes the time zone convention (Q-09), so an eval may ask the model to raise the issue and state its assumption, not to reach a fixed answer.

## 7. Figures

No new figure keys are proposed. A crypto calculator needs only figures that already exist:

| Key | Value | Status | Source | Use |
|---|---|---|---|---|
| `individual.personal_use_asset_cgt_exempt_max_cost` | 10000 | VERIFIED (existing) | legislation.gov.au ITAA 1997 compilation 266 vol 3, s 118-10(3) "$10,000 or less" (re-read 29 Sep 2026; S-01) | Personal use screen |
| `cgt.discount_individual_trust` | 0.5 | VERIFIED (existing) | s 115-100(aa), (ab) re-read 29 Sep 2026 (S-01) | Events before 1 Jul 2027 only |
| `cgt.collectable_exempt_max_cost` | 500 | VERIFIED (existing) | s 118-10(1) re-read 29 Sep 2026 (S-01) | NFT or coin-like collectables |
| `bookkeeping.record_retention_years` | 5 | VERIFIED (existing) | ATO record keeping overview (as cited in the overlay) | General rule only; the CGT record rule is s 121-25(2), 5 years after no further CGT event, a different start point |

Considered and rejected as new keys: crypto prices, RBA rates and 30 Jun 2027 market values (user or source supplied, never stored); CPI index numbers after the latest published quarter (unpublished; a SUSPECT/null entry belongs in `cgt`, not here); the 5-year CGT record period (a statutory constant already covered by the existing bookkeeping key for the number); the record-keeping penalty (30 penalty units; the penalty unit value is not a crypto figure); the $10,000 CGT schedule trigger in myTax (a reporting rule, not needed for this skill).

Suggested note edit (no value change): on `individual.personal_use_asset_cgt_exempt_max_cost`, add "s 118-10(3) is inclusive ('or less'); two ATO crypto web pages say 'less than $10,000'".

Side observations for the orchestrator (not crypto figures):

- `bookkeeping.simplified_trading_stock_change_max` and `business.simplified_trading_stock_change_max` both hold $5,000 and cite different sections. The $5,000 test is s 328-285(1)(b); s 328-295 is the valuation consequence (read in compilation 266 vol 7, S-03). The overlay notes disagree, and "one fact, one key" suggests keeping one. The ATO page (27 May 2026, S-48) also now defines small business by aggregated turnover under $10 million.
- No conflict with any existing VERIFIED figure or with the crypto text in `docs/research/verification-federal-2026-09.md` or the `cgt` skill was found. Federal verification row 15b (TD 2026/D2 content "per secondary summary") is now confirmed on the primary page (S-19).

## 8. Build and eval guidance

### 8.1 For the skill-builder

- **Scope line**: individuals only (resident, not temporary), crypto held on capital account or received as income. Everything in section 5 stops and quotes a code.
- **Procedure**: (1) confirm holder, residency and income year (event date in Australian local time); (2) classify each row as receipt (income or not), disposal (A1), other event (C1, C2, chain split), or non-event (own-wallet); (3) character screen (investor vs business); (4) personal use screen from facts; (5) parcel matching method and records check; (6) AUD value and source recorded per row; (7) call `cgt` tools per disposal; (8) present other income separately from net capital gain.
- **Calculator idea**: a parcel ledger taking acquisitions (date, quantity, AUD first element, AUD incidental costs, origin) and disposals (date, quantity, AUD proceeds, AUD costs, method FIFO or named parcels), returning per-disposal cost base, holding-period flag, and rows ready for `capital_gain` or `net_capital_gain`. No price lookups. Refuse average-cost requests unless units are same-day identical. The personal use call is a fact question, not something to compute.
- **Never in SKILL.md prose** (lint): dollar amounts, percentages, thousands separators, business-day counts, or day counts equal to a figure. Say "the personal use asset threshold" and "the discount". Only the allowlisted 50% discount phrase is safe. Numbers belong in fenced blocks or tool output.
- **Label drafts** every time: TR 2026/D1 (airdrops) and TD 2026/D2 (wrapping) are drafts; the ATO web pages that mirror them do not remove that status.
- **Output contract** (CONVENTIONS section 8) plus the AUD source and timestamp per row, and the residency and income year stated.
- **Description** must trigger on casual phrasing ("sold some eth", "swapped tokens", "staking rewards tax", "airdrop", "lost my seed phrase", "do I pay tax on bitcoin", "is my crypto exempt") and name the out-of-scope cases (mining, DeFi, exchange collapse, trader) so escalations fire.
- **`law_watch.py` candidates**: ATO pages S-22 to S-33, S-35 to S-39, S-45, S-46 (each shows a "last updated" date), S-21 (advice under development), S-18 and S-19 (draft to final), S-41 (data-matching protocol), S-42 (CARF).

### 8.2 For the eval-author

- Plain Claude gets simple swaps right, so weight cases toward: cost base of rewards, personal use vs investment, chain split cost base and date, draft labelling, records, parcel identification, escalations, and 2027 evidence.
- Suggested menu (16 or more needed; pick freely): numeric W-01, W-02, W-03 (A, C, D, E), W-04, W-05(a), W-06 (draft label), W-07, W-08 (deferred part only), W-09; traps T-01 to T-07, T-09, T-10, T-12 to T-16, T-18 to T-20; escalations E-01, E-02, E-03, E-06, E-09, E-14; triggers (casual phrasing above).
- **Do not assert** (unsettled; see the Q list): gas or network fee treatment in cost base; whether a swap fee is also part of the new asset's cost base; payment gateway spending as personal use; exactly-$10,000 outcome without accepting the note about ATO wording; split disposals to reach the exemption; hobby-mining cost base; liquid staking; custodial deposits; initial allocation airdrops before the final ruling; bounty airdrops; the statutory route to a staking cost base; time zone for the year boundary; CARF dates beyond the ATO page; final versions of TR 2026/D1 or TD 2026/D2; indexation amounts after 1 Jul 2027; whether a thinly traded token has a readily ascertainable market value.
- Existing `cgt` cases already cover the ETH to SOL swap and the casual bitcoin trigger.
- Graders should accept "ATO web guidance" as the source for chain splits, staking, records and personal use, and should not demand a public ruling for them.

## 9. Open questions

| ID | Question | Where it matters |
|---|---|---|
| Q-01 | Is depositing crypto with a centralised exchange a disposal? Depends on beneficial ownership under the account terms (s 104-10(2)); ATO silent | R-12 |
| Q-02 | Gas or network fees: TD 2026/D2 footnotes reserve them; the ATO says fees paid in crypto are disposals but not how the value counts in cost base | R-11 |
| Q-03 | Is a swap fee both a cost of disposing and a cost of acquiring (double count)? | W-01 |
| Q-04 | No ATO crypto-specific parcel identification position; TD 33 note (i) by analogy | R-20 |
| Q-05 | Personal use: per-unit vs per-parcel test for the $10,000 amount; part disposals of a larger parcel ("or part of the asset"); s 108-25 sets; conflicting ATO pages on payment gateways and on "less than" vs "or less" | R-23 to R-27 |
| Q-06 | Hobby mining and pool payouts: cost base and timing unpublished | R-35 |
| Q-07 | Liquid staking, restaking, custodial staking: is there an event on deposit? | R-56 |
| Q-08 | Initial allocation airdrops made before a final ruling | R-47 |
| Q-09 | Time zone and instant for the income-year boundary and for "just before 1 July 2027" | T-17, R-72 |
| Q-10 | Whether thinly traded tokens or NFTs have a "readily ascertainable market value" for the draft apportioning instrument; the instrument was not registered as at 29 Sep 2026 (the `cgt` notes say so; the Treasury release read shows only the 4 Aug 2026 draft) | R-73 |
| Q-11 | Final TR 2026/D1 and TD 2026/D2 may differ; TD 2026/D2 proposes retrospective application | R-47, R-53 |
| Q-12 | CARF and domestic reporting: announced, not law; the ATO page gives only "first exchange 2028" | R-70 |
| Q-13 | Data-matching coverage for 2026-27 onwards: no notice found | R-69 |
| Q-14 | Worthless or delisted tokens: when a capital loss is realised without a disposal; no ATO guidance found | E-15 |
| Q-15 | Whether the ATO will accept HIFO or LIFO for crypto where records identify the parcels (TD 33 accepts the taxpayer's selection for identical assets, note (i)) | R-21 |
| Q-16 | Statutory route to a market value cost base for staking and DeFi rewards: s 112-20(1) needs an acquisition from another entity, and TD 2026/D2 para 48 says an autonomous smart contract is not an entity; the ATO states the outcome but not the provision | R-16 |
| Q-17 | Whether a bounty airdrop (simple tasks) is a reward for services: the draft lists the type but does not classify it | R-42 |

## 10. Verification log

Read this session on the primary page (29 Sep 2026): ITAA 1997 compilation 266 volumes 1, 3, 7, 9, 10 (ss 6-5, 6-10, 70-10, 70-30, 70-35, 70-45, 102-20 to 102-25, 104-10, 104-20, 104-25, 104-160, 104-165, 108-5, 108-10, 108-20, 108-25, 108-30, 109-5, 110-25, 110-35, 110-36, 112-20, 112-25, 112-30, 112-155 to 112-185, 114-10, 114-25, 114-30, 115-10, 115-25, 115-100, 116-20, 116-30, 118-10, 118-20, 118-25, 121-20, 121-25, 328-285, 328-295, 855-10, 855-15, 855-45, 977-5, and the s 995-1 definition of foreign currency); ITAA 1936 s 21; TD 2014/26; TD 33; TR 2026/D1; TD 2026/D2; TR 92/3 (first part); TR 2008/1 (opening); the edited private advice; the ATO web pages marked [R] in the register; the Treasurer's release of 4 Aug 2026; the Government response (Mar 2025).

Extract only ([E]): TD 2014/25, TD 2014/27, TD 2014/28, TR 97/11, GSTR 2006/9 addendum, ATO non-commercial loss pages, ATO "Are you in business?", the Board of Taxation report, the ATO cost base page, the Gazette notice.

Statutory items that differ from a reading of an ATO web page: personal use amount (statute "or less"; two ATO pages "less than"); record retention (statute "5 years after no further CGT event"; ATO web "5 years from the later of...").

## 11. Source register

Legislation

- S-01 ITAA 1997 compilation 266 (in force 1 Jul 2026; includes Act No. 49 of 2026), vol 3 (Div 70; Parts 3-1 and 3-3; Div 121): https://www.legislation.gov.au/C2004A05138/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_3/document_3.html
- S-02 ITAA 1997 vol 1 (ss 6-5, 6-10): https://www.legislation.gov.au/C2004A05138/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_1/document_1.html
- S-03 ITAA 1997 vol 7 (Div 328): https://www.legislation.gov.au/C2004A05138/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_7/document_7.html
- S-04 ITAA 1997 vol 9 (Div 855): https://www.legislation.gov.au/C2004A05138/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_9/document_9.html
- S-05 ITAA 1997 vol 10 (s 977-5, s 995-1): https://www.legislation.gov.au/C2004A05138/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_10/document_10.html
- S-06 ITAA 1936 s 21: https://www.ato.gov.au/law/view/document?docid=PAC/19360027/21
- S-07 Treasury Laws Amendment (Tax Reform No. 1) Act 2026, No. 49: https://www.legislation.gov.au/C2026A00049/asmade/2026-06-26/text/original/epub/OEBPS/document_1/document_1.html
- S-08 Gazette, crypto asset data-matching notice, April 2024 [E]: https://www.legislation.gov.au/C2024G00249/asmade/2024-04-26/text/original/pdf

ATO rulings, determinations and drafts

- S-09 TD 2014/25 (bitcoin not foreign currency) [E]: https://www.ato.gov.au/law/view/document?DocID=TXD%2FTD201425%2FNAT%2FATO%2F00001&PiT=99991231235958
- S-10 TD 2014/26 (bitcoin is a CGT asset) [R]: https://www.ato.gov.au/law/view/document?docid=TXD/TD201426/NAT/ATO/00001
- S-11 TD 2014/27 (bitcoin as trading stock) [E]: https://www.ato.gov.au/law/view/document?docid=TXD%2FTD201427%2FNAT%2FATO%2F00001
- S-12 TD 2014/28 (FBT, bitcoin to employees) [E]: https://www.ato.gov.au/law/view/view.htm?DocID=TXD%2FTD201428%2FNAT%2FATO%2F00001
- S-13 TD 33 [R] https://www.ato.gov.au/law/view/document?DocID=CGD%2FTD33%2FNAT%2FATO%2F00001&PiT=99991231235958 and TD 33A [E] https://www.ato.gov.au/law/view/print?DocID=CGD%2FTD33A%2FNAT%2FATO%2F00001&PiT=99991231235958
- S-14 TR 92/3 (isolated transactions) [R]: https://www.ato.gov.au/law/view/document?docid=TXR/TR923/NAT/ATO/00001
- S-15 TR 97/11 (indicators of a business) [E]: https://www.ato.gov.au/law/view/pdf?DocID=TXR%2FTR9711%2FNAT%2FATO%2F00001&PiT=20121024000001&filename=law%2Fview%2Fpdf%2Fpbr%2Ftr1997-011c2.pdf
- S-16 TR 2008/1 (wash sales, Part IVA) [R opening]: https://www.ato.gov.au/law/view/document?docid=TXR/TR20081/NAT/ATO/00001
- S-17 Edited private advice 1051934343575, 27 Sep 2022 (not binding) [R]: https://www.ato.gov.au/law/view/print?DocID=EV/1051934343575&PiT=99991231235958
- S-18 DRAFT TR 2026/D1, 19 Aug 2026, comments to 16 Oct 2026 [R]: https://www.ato.gov.au/law/view/document?DocID=DTR%2FTR2026D1%2FNAT%2FATO%2F00001&PiT=99991231235958
- S-19 DRAFT TD 2026/D2, 19 Aug 2026, comments to 2 Oct 2026 [R]: https://www.ato.gov.au/law/view/document?DocID=DXT%2FTD2026D2%2FNAT%2FATO%2F00001&PiT=99991231235958
- S-20 GSTR 2006/9 Addendum A8, GST treatment of digital currency from 1 Jul 2017 [E]: https://www.ato.gov.au/law/view/document?PiT=20181212000001&docid=GST%2FGSTR20069A8%2FNAT%2FATO%2F00001
- S-21 ATO advice under development, CGT issues (updated 7 Sep 2026) [R]: https://www.ato.gov.au/about-ato/ato-advice-and-guidance/advice-under-development-program/advice-under-development-capital-gains-tax-issues

ATO web guidance, individuals (crypto section)

- S-22 What are crypto assets? (19 Aug 2026) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/what-are-crypto-assets
- S-23 Crypto asset transactions (22 Jun 2026) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/crypto-asset-transactions
- S-24 Crypto to crypto exchange or swap (22 Jun 2026) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/crypto-to-crypto-exchange-or-swap
- S-25 How to work out and report CGT on crypto (22 Jun 2026) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/how-to-work-out-and-report-cgt-on-crypto
- S-26 Crypto asset as a personal use asset (22 Jun 2026) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/crypto-asset-as-a-personal-use-asset
- S-27 Tax and crypto asset investments, investors toolkit (1 Jul 2026): own-wallet transfers, network fees, payment gateway example, "less than $10,000" wording [R]: https://www.ato.gov.au/tax-and-super-professionals/for-tax-professionals/prepare-and-lodge/tax-time/tax-time-toolkits/tax-time-toolkit-for-investors/tax-and-crypto-asset-investments
- S-28 Staking rewards and airdrops (19 Aug 2026) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/staking-rewards-and-airdrops
- S-29 Crypto chain splits (22 Jun 2026) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/crypto-chain-splits
- S-30 Decentralised finance and wrapping crypto (19 Aug 2026) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/decentralised-finance-and-wrapping-crypto
- S-31 Non-fungible tokens (22 Jun 2026) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/non-fungible-tokens
- S-32 Crypto asset transactions with gift cards or debit cards (22 Jun 2026) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/crypto-asset-transactions-with-gift-cards-or-debit-cards
- S-33 Gifts and donations of crypto assets (22 Jun 2026) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/gifts-and-donations-of-crypto-assets
- S-34 Crypto asset prizes and gambling winnings (22 Jun 2026) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/crypto-asset-prizes-and-gambling-winnings
- S-35 Crypto asset payments relating to employment or services (22 Jun 2026) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/crypto-assets-payments-relating-to-employment-or-services
- S-36 Loss or theft of crypto assets (22 Jun 2026) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/loss-or-theft-of-crypto-assets
- S-37 Crypto exchanges and platforms under administration (22 Jun 2026) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/crypto-exchanges-and-platforms-under-administration
- S-38 Crypto asset transactions and tax residency (22 Jun 2026) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/transactions-acquiring-and-disposing-of-crypto-assets/crypto-asset-transactions-and-tax-residency
- S-39 Keeping crypto records (23 Jun 2025) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/keeping-crypto-records

ATO other

- S-40 Clarity on crypto reporting, tax professionals newsroom (29 Jun 2026) [R]: https://www.ato.gov.au/tax-and-super-professionals/for-tax-professionals/tax-professionals-newsroom/clarity-on-crypto-reporting
- S-41 Crypto assets data-matching program protocol to 2025-26 (26 Apr 2024) [R]: https://www.ato.gov.au/about-ato/commitments-and-reporting/in-detail/privacy-and-information-gathering/how-we-use-data-matching/crypto-assets-data-matching-program-protocol ; sub-pages .../crypto-assets-data-matching-program-protocol/crypto-data and .../crypto-assets-data-matching-program-protocol/how-we-undertake-data-matching-on-crypto-assets under https://www.ato.gov.au/about-ato/commitments-and-reporting/in-detail/privacy-and-information-gathering/how-we-use-data-matching/
- S-42 OECD Crypto Asset Reporting Framework and domestic reporting (published 17 Dec 2025) [R]: https://www.ato.gov.au/about-ato/new-legislation/in-detail/international/oecd-crypto-asset-reporting-framework-and-domestic-reporting
- S-43 myTax 2026 capital gains or losses (published 1 Jun 2026) [R]: https://www.ato.gov.au/individuals-and-families/your-tax-return/instructions-to-complete-your-tax-return/mytax-instructions/2026/income/australian-income-or-losses-from-investments-or-property/capital-gains
- S-44 CGT discount (updated 29 Jun 2026) [R]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/cgt-discount
- S-45 Crypto assets used in business (29 Jun 2022) [R]: https://www.ato.gov.au/businesses-and-organisations/income-deductions-and-concessions/income-and-deductions-for-business/crypto-assets-and-business/crypto-assets-used-in-business
- S-46 Crypto mining (18 Nov 2022) [R]: https://www.ato.gov.au/businesses-and-organisations/income-deductions-and-concessions/income-and-deductions-for-business/crypto-assets-and-business/crypto-mining
- S-47 Are you in business? (Apr 2026) [E]: https://www.ato.gov.au/businesses-and-organisations/starting-registering-or-closing-a-business/starting-your-own-business/are-you-in-business
- S-48 Simplified trading stock rules (27 May 2026) [R]: https://www.ato.gov.au/businesses-and-organisations/income-deductions-and-concessions/income-and-deductions-for-business/accounting-for-trading-stock/simplified-trading-stock-rules
- S-49 Non-commercial losses, individuals or sole traders [E]: https://www.ato.gov.au/businesses-and-organisations/income-deductions-and-concessions/losses/non-commercial-losses/offset-or-defer-the-loss-individuals-or-sole-traders
- S-50 GST and digital currency (5 Jul 2023) [R]: https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/in-detail/your-industry/gst-and-crypto-assets/gst-and-digital-currency
- S-51 Cost base of assets [E]: https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/calculating-your-cgt/cost-base-of-asset

Treasury and Government

- S-52 Government Response to the Board of Taxation review of digital assets (Mar 2025) [R]: https://treasury.gov.au/sites/default/files/2025-03/p2025-639068-gov-response.pdf
- S-53 Treasurer's release, consultation on the next tranche of tax reform legislation (4 Aug 2026) [R]: https://ministers.treasury.gov.au/ministers/jim-chalmers-2022/media-releases/consultation-next-tranche-tax-reform-legislation
- S-54 Board of Taxation, Review of the tax treatment of digital assets and transactions in Australia (May 2024) [E]: https://taxboard.gov.au/sites/taxboard.gov.au/files/2024-05/bot-report-review-digital-assets-transactions.pdf
