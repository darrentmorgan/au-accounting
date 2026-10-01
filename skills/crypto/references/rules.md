# Crypto rules map

Authority tags: LAW (statute), RULING (public ruling, binds the Commissioner), DET (CGT cell determination, the ATO's considered view), WEB (ATO web guidance, the ATO's stated view, not a ruling), DRAFT (draft ruling, preliminary view, not law), INFERRED (our reasoning, no primary source says it). Sources are in `sources.md`. No figures here: amounts come from tool output.

## What each tool decides

| Tool | Decides | Does not decide |
|---|---|---|
| `crypto_classify_transactions` | Event per transaction, capital proceeds and the rule used, local date and income year, draft labels, escalation code per row | Cost base, gain, character, personal use |
| `crypto_income_receipts` | Income at receipt and cost base for staking, rewards, payment for services, airdrops, chain splits, prizes, gifts received | Trading business airdrops, mining, unclear chain splits (escalated) |
| `crypto_parcel_ledger` | Parcel matching, per-slice cost base, holding period, personal use application, then `capital_gain` per slice and `net_capital_gain` per income year | Discount, indexation, loss ordering and 1 July 2027 mechanics (owned by `cgt`) |
| `crypto_personal_use_screen` | Whether the person's facts indicate a personal use asset, and whether the gain is disregarded on the threshold test | Whether the facts are true |
| `crypto_character_screen` | Whether any business or profit-making indicator is present | Whether the person is in business (a registered tax agent decides) |

## Rules by topic

| Topic | Rule | Authority |
|---|---|---|
| CGT asset | Crypto holding rights are property, so a CGT asset. Each crypto asset is separate. | RULING TD 2014/26; LAW ITAA 1997 s 108-5; WEB |
| Not money | Bitcoin is not foreign currency; dealings are like barter. | RULING TD 2014/25; LAW s 995-1 |
| Disposal | Change of ownership is event A1. Selling, swapping, spending, gifting, loading a card. | LAW s 104-10; WEB |
| Proceeds, swap | Market value of what is received; fallback market value of what is given up. | LAW s 116-20(1)(b), s 116-30(2)(a); WEB |
| Proceeds, gift | Taken to be market value. | LAW s 116-30(1) |
| Acquisition by swap | Acquired when the swap happens; first element is the market value given. | LAW ss 109-5, 110-25 |
| Own-wallet transfer | Not a disposal while ownership is kept. | WEB |
| Fee in crypto | A disposal of the crypto spent; cost base effect unsettled. | WEB; DRAFT TD 2026/D2 reserves gas fees |
| Parcel identification | First-in first-out or a selection supported by records; not average cost across days. | DET TD 33 (by analogy); INFERRED for crypto |
| Personal use asset | Losses disregarded; gain disregarded at or below the threshold; used or kept mainly for personal use or consumption. | LAW ss 108-20, 118-10(3); RULING TD 2014/26; WEB |
| Set of assets | Split disposals may be treated as one asset. | LAW s 108-25; unsettled for fungible crypto |
| Business or trader | Revenue account: trading stock, ordinary income, no discount. | RULING TD 2014/26, TD 2014/27, TR 92/3, TR 97/11; WEB |
| Staking and DeFi rewards | Ordinary income at market value when received; that value is the cost base. | LAW s 6-5, ITAA 1936 s 21; WEB |
| Payment for services | Assessable at market value; cost base is that value. | WEB |
| Airdrops | Character depends on the recipient; holder airdrop to a non-business investor is not income. | DRAFT TR 2026/D1; WEB |
| Chain split | No income or gain on receipt, nil cost base, split-date acquisition. | WEB only |
| Wrapping | Event C2 on wrap and on unwrap. | DRAFT TD 2026/D2 |
| Lost or stolen | Event C1, time is compensation or discovery, evidence needed. | LAW s 104-20; WEB |
| Records | Keep and reconstruct; retain until 5 years after no further CGT event can happen. | LAW ss 121-20, 121-25; WEB |
| Residency | Residents taxed worldwide; foreign residents only on taxable Australian property gains and Australian-source income. | LAW ss 855-10, 855-15; WEB |
| 1 July 2027 | Indexation and deemed sale for residents; computed by `cgt`. | LAW Act No. 49 of 2026 Sch 1 |

## Points the ATO has not settled (never assert; flag)

- Whether depositing crypto with a centralised exchange is a disposal.
- How a network or platform fee paid in crypto counts in cost base, and whether a swap fee counts in both assets.
- Any crypto-specific parcel identification position, and whether highest-cost-first or last-in first-out is accepted where records identify the units.
- Personal use: whether the threshold is tested per unit, per parcel or per disposal; part disposals of a larger parcel; the set rule for fungible crypto; payment gateways (the ATO pages conflict); "less than" against "or less" wording on two ATO pages.
- Hobby mining and pool payouts: cost base and timing.
- Liquid staking, restaking, custodial staking, bridging: whether there is an event on deposit.
- Initial allocation airdrops made before a final airdrop ruling; bounty airdrops.
- The statutory route to a market value cost base for rewards and airdrops (the ATO states the outcome, not the provision).
- The time zone and the instant for the year boundary and for "just before 1 July 2027".
- Whether a thinly traded token or NFT has a readily ascertainable market value for the draft apportioning instrument.
- Worthless or delisted tokens: when a loss is realised without a disposal.
- Final versions of draft TR 2026/D1 and draft TD 2026/D2; the drafts propose to apply before and after issue.
- CARF and domestic crypto reporting: announced, not law.

## Traps to name when they arise

- A swap is not tax free until cash out.
- Moving coins between your own wallets is not a sale; paying gas in crypto is a disposal.
- Held over 12 months gives the discount before 1 Jul 2027, not exemption; a swap restarts the clock.
- Spent some on a laptop does not make it a personal use asset.
- Staking rewards are income when received, not only on sale, and are not discounted.
- A forked coin is not income on arrival and does not inherit the old cost base or date.
- The drafts are not final law.
- No records does not mean nil cost base.
- Average cost across purchases is not accepted.
- Stablecoins are crypto, not cash.
- Lost crypto is a loss only with evidence.
- The 50% discount does not continue for new events from 1 Jul 2027.
