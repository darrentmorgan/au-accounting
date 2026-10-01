# Apportionment for short-stay use

Time-based and area-based factors follow PCG 2026/2. The tool `short_stay_apportionment` does the arithmetic; this file says how to classify the facts. Amounts here are described by rule, never by figure.

## Classify every night owned

The nights must add up to the days owned in the income year (365 or 366 by the calendar; part-year ownership uses days owned).

| Night class | Tool field | In the time factor? |
|---|---|---|
| Occupied by paying guests, or paid for though nobody stayed (PCG 2026/2 para 14) | `nights_rented` | Yes (used to produce income) |
| Unoccupied, genuinely available for rent on commercial terms | `nights_available_commercial_terms` | Yes (held to produce income), except for a room in the owner's home |
| Owner used it, or otherwise unused and private | `nights_owner_use` | No |
| Family or friends free or at a reduced rate | `nights_family_friends_free_or_reduced` | No (preparer's conservative treatment; flagged) |
| Blocked out or reserved, unused and not available | `nights_blocked_unused` | No |
| Closed for repairs or renovation | `nights_closed_repairs` | Not settled: AU-SS-003 |

A room in the owner's own home has no held nights: on nights it is not rented it is private, even with a live listing (PCG 2026/2 paras 15 and 41). Market-rate nights for a relative go in `nights_rented` only if the rate was evidenced when set (a valuation or comparable listings, PCG 2026/2 paras 47-49).

## Available on commercial terms

For (broad exposure, rent comparable with similar properties, requests actively monitored) and against (advertised only at work, by word of mouth or restricted groups; blocked for the owner, family or friends at below-market rates during likely demand; unlikely to attract renters because of location, condition or access; unreasonable conditions such as rent above comparables, references for short holiday stays, no children, parts inaccessible; requests not monitored or refused without adequate reason) are in PCG 2026/2 paras 16-17. If the against factors dominate the ATO says the property is generally not held to produce income and no expenses are deductible for the year. The ATO example (an Adelaide owner who sets rent above comparables, rejects applicants and refuses agent advice) is a total denial, not an apportionment. Nights off the market for repairs are not addressed in the material read.

Evidence: booking calendars, price history and enquiry response records (PCG 2026/2 para 2 requires records that support how the Guideline applies).

## Time factor and area factor

- Time factor = (nights rented or paid for + nights available on commercial terms) divided by days owned. Whole property: time only. Part of a home for part of the year: time and area.
- Area factor (part of a home only) = (area used only by the guest + half of the shared areas) divided by the whole area (PCG 2026/2 paras 29-32). The half weighting of shared areas is the ATO's fixed convention.
- Combined = time factor multiplied by area factor (paras 33-43). Do not round the factor before multiplying. Percentages and dollars in the ATO's own examples are rounded or truncated; tolerate a dollar.
- A whole main residence let occasionally while the owner is away: time only, on nights let, direct costs in full.

## Buckets

| Bucket | Contents | Treatment |
|---|---|---|
| A. Direct letting | Platform commissions, agent letting and management fees, advertising to find guests, cleaning and laundering relating to guest stays | Deductible in full, no apportionment, and still deductible where s 26-50 denies ownership costs |
| B. Ownership and use | Interest (after removing any private-purpose share, TR 2000/2), borrowing expenses, council and water rates, body corporate, land tax, repairs and maintenance, insurance, electricity and internet, decline in value, capital works | Apportion. If s 26-50 denies them, nothing is deductible and there is no apportionment |
| C. Denied, capital or private | Own travel (s 26-31), second-hand depreciating assets in residential rentals (s 40-27), initial repairs and improvements (capital), private use, vacant land holding costs | Not deductible now; some costs add to the CGT cost base |

Land tax is incurred when the liability arises under state law, not when assessed or paid, and it is an ownership cost (TR 2026/1 para 71). Each property is examined separately (PCG 2026/2 para 9). A loan used partly for private purposes must be split; redraws take the character of what was bought.

## Holiday home gate (s 26-50)

1. **Is it a holiday home?** Whole property, not the owner's main residence, and the owner, family or friends use it for holidays free or at a reduced rate, or the owner holds or reserves it for that use. A room in the owner's home is not a holiday home. A property never used or reserved for the owner's or friends' holidays, with all reasonable steps taken to rent it, is not a holiday home (TR 2026/1 Example 10).
2. **Used or held mainly to produce rent at all times in the income year?** Objective and qualitative (TR 2026/1 paras 37-43 and 104-114). Factors: actual use; time dedicated to income use; time used or held for private use; how available or used as a rental when holiday demand peaks (school holidays, public holidays, seasonal peaks). A property advertised for more than half the year but unavailable or unused for rent in the desirable periods points to not mainly rental (para 112).
3. **Result.** Mainly rent: ownership costs stay deductible, apportioned for private use. Not mainly rent: all ownership and use costs denied, no apportionment, direct costs stay deductible.
4. **Transitional.** The ATO will not devote compliance resources to s 26-50 for expenses incurred before `rental.holiday_home_compliance_start` (TR 2026/1 para 138; PCG 2026/3 paras 12-13). The section itself is unchanged, and the ATO will still state the same view in a private ruling or assessment.

PCG 2026/3 zones are qualitative and have no day thresholds:

| Zone | Behaviour (paraphrased) | ATO approach |
|---|---|---|
| Green | High income-producing use, especially at desirable times; little personal use; income prioritised; commercial terms; actively maximising income | No compliance resources except to confirm the facts |
| Amber | More personal use by the owner and friends at no cost or below market; forgoing income to keep it available; personal use at peak times; limited attempts to rent | May apply compliance resources |
| Red | Blocking times each year for personal use, particularly peaks; limited attempts to rent; major features inaccessible; unreasonable restrictions; no effort to lift occupancy; pricing above market | Priority attention, may audit |

ATO example conclusions (PCG 2026/3): a Gold Coast apartment in a rental pool with four weeks blocked in low demand is green (Example 1); a Barossa house with one week of owner use in the four-month peak, otherwise actively managed, is green (Example 2); a Melbourne CBD apartment used by Adelaide owners for major sporting events is amber (Example 6); a Sorrento house rented for three to four weeks, with the owner's wine collection, boat and jet-ski inaccessible, is red and denied (Example 8); a Busselton house always blocked for Christmas, Easter and summer holidays, with the agent instructed not to let and many enquiries rejected, is red (Example 9).

Part-year exception (s 26-50(4)): needs a definite and sustained change in the pattern of use during the year (for example the owner moves overseas and lifts all restrictions). A one-off different use or a regular seasonal pattern is not a change.

## Worked shapes (tool output must be used for the numbers)

- **Whole house, light off-peak owner and friends use, actively let:** holiday home, mainly for rent, ownership costs apportioned by nights rented plus available over days owned; the private nights fall out of the numerator.
- **Same house with peak periods blocked and few nights rented:** not mainly for rent; ownership costs denied; direct costs deductible; net income is rent less the direct costs.
- **Spare room in the owner's home:** area factor times time factor, with no held nights; direct costs in full; not a holiday home.
- **Rent to a relative below market:** assessable in full; deductions apportioned or limited to rent received.

## Income tax traps

1. Net-of-fees income declared instead of gross.
2. Ownership costs claimed in full on a property the owner and friends use at peak times.
3. Held nights counted for a room in the owner's home.
4. Nights blocked for friends or family counted as available.
5. Using 365 in a leap income year: the day count comes from the calendar, and the tool applies it.
6. Rounding the factor before multiplying.
7. Claiming own travel to clean or hand over keys (s 26-31).
8. Depreciation on second-hand furniture bought for a residential rental (s 40-27).
9. The higher traveller-accommodation capital works rate on a single dwelling.
10. Treating the ATO transitional relief for s 26-50 as a change in the law.
11. Ignoring that discounted or free stays by friends and family make it a holiday home.
12. Forgetting the 2027-28 quarantine for a planned purchase after the cut-off.
13. Treating a business-scale operator as an individual passive investor.
14. Apportioning by area when the whole property is let.
15. Treating a listing as available on commercial terms when it is priced above comparables or requests go unanswered.
