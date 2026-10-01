# GST tests for short-stay accommodation

Explain these tests. Do not make the CRP determination (AU-GST-002). Figures are in `data/rates/<year>.d/gst.yaml` and are named by key.

## The two boxes

| Rule | Statement | Authority |
|---|---|---|
| Residential premises | Land or a building occupied as a residence or for residential accommodation, or intended and capable of being so occupied, regardless of the term of occupation or intended occupation. | GSTA 1999 s 195-1 |
| Input taxed | A lease, hire or licence of residential premises is input taxed to the extent the premises are to be used predominantly for residential accommodation, other than a supply of commercial residential premises or of accommodation in it by the entity that owns or controls it. | s 40-35(1)(a), (2)(a) |
| Physical test | Whether premises are residential premises depends on physical character (suitable and capable for living accommodation). Legal bans on short or long occupation do not change it. | GSTR 2012/5 |
| CRP | A hotel, motel, inn, hostel or boarding house; school accommodation; a ship mainly let on hire or used for entertainment or transport; a marina with berths occupied by residence ships; a caravan park or camping ground; anything similar. Student accommodation of a non-school education institution is excluded. | s 195-1; GSTR 2012/6 para 6 |
| Taxable | A sale or lease of CRP, and accommodation in CRP provided to an individual by the entity that owns or controls it, is taxable if the s 9-5 conditions are met (for consideration, in an enterprise, connected with Australia, supplier registered or required to be). | GSTR 2012/6; s 9-5 |

## Indicators used by `gst_short_stay_classification`

The tool asks about the supplier of the stay. Any one answered true stops the screen and returns AU-GST-002, because the ruling weighs the whole picture and one feature can tip a close case.

- Daily or regular housekeeping during the stay. Cleaning after the guest leaves and providing linen are not indicators.
- Meals, or a communal dining room.
- A reception or front desk run by the supplier (an agent for the owner running a desk does not count against the owner).
- Marketing to the public as a hotel, guest house, lodge or B&B business.
- Several premises booked, allocated and supplied centrally in the supplier's own right.

These follow GSTR 2012/6 para 12 (characteristics of hotels and similar premises: business-like operation, capacity for several unrelated guests, held out to the public, accommodation as the main purpose, central management, supply in own right, services and facilities, occupants who are guests). The features pointing away from CRP in para 41 (periodic lease, condition report, exit cleaning fee, pets and alterations allowed, occupant arranges utilities and cleaning, unfurnished) are context, and their absence does not prove CRP.

## ATO conclusions to rely on (the ruling's own examples)

| Facts | ATO conclusion |
|---|---|
| B&B, three bedrooms, communal dining, on-site owner, daily cleaning, breakfast (Example 2, paras 49-50) | CRP, taxable |
| House with two furnished spare rooms, linen only (Example 3, paras 51-52) | Not CRP, input taxed |
| Farm stay suites, daily cleaning, on-site manager supplying in its own right (Example 4, paras 53-55) | CRP |
| One strata holiday apartment let through an on-site manager acting as agent for several apartments (Example 12, paras 82-85) | Not CRP, owner's supply input taxed |
| Separately titled unit leased on its own, without the commercial infrastructure (para 98, Example 16 paras 102-107) | Residential, regardless of how the building operates |

Rooms or apartments combined with enough commercial infrastructure (reception, dining, function rooms, laundry, car parking) can be run as CRP (paras 95-97), so the owner of a whole building or many units leased together is escalated.

Court authority on the same split: the Full Federal Court in the South Steyne litigation (summarised in MBI Properties v FCT [2013] FCA 56) held apartment leases to the hotel operator were input taxed residential premises and the room supplied to a guest was a taxable supply of CRP accommodation by the operator as principal. A Tribunal decision on a host renting rooms in her own four-bedroom home with continental breakfast found no business and no CRP (FFYS and FCT [2021] AATA 4844, cited in TR 2026/1 footnote 4); it is not binding precedent but a useful fact pattern. An archived 2016 ATO private advice on serviced apartments must not be relied on.

The draft update GSTR 2012/6DC (5 Nov 2025) targets build-to-rent, hostels and boarding houses and is not final; the ATO says its view is unchanged. Cite the current ruling.

## Who is the supplier

- **Agent model.** Where a manager supplies as agent for the owner, the owner makes the supply. The arrangement documents show whether an agent-principal relationship exists (GSTR 2012/6 paras 24, 83-84). The manager's fee is a separate supply to the owner.
- **Head-lease or principal model.** The owner's lease is input taxed. The operator's guest supplies may be CRP. It turns on facts and contracts: AU-GST-002.
- **Platforms.** Usually the host, not the platform, is the supplier. A platform that only acts as agent on its own site is not an electronic distribution platform for SERR.
- **A single apartment inside a CRP complex**, leased to a guest or to a management company that runs it as part of the complex, remains an input taxed lease for the owner.

## Credits and costs

- No input tax credit for acquisitions to the extent they relate to making input taxed supplies (s 11-15(2)(a)). Management, cleaning and platform fees are costs, not credits.
- A registered CRP operator claims credits on its costs and pays GST at 1/11 of the GST-inclusive price on stays shorter than `gst.div87_long_term_days`.
- A person making both taxable supplies and input taxed rent needs a documented apportionment of shared overheads: AU-GST-003.

## Registration

GST turnover excludes input taxed supplies (s 188-15(1)(a)), supplies not for consideration and supplies not made in an enterprise. So residential short-stay rent never counts. Other taxable income counts. Registration: `gst.registration_threshold`, `gst.registration_deadline_days`. Offshore sellers of Australian commercial accommodation count those sales; residential-style lettings do not attract GST. Use `gst_registration_check` with `input_taxed_sales_included`.

The ATO Registering for GST page lists income through the sharing economy or digital platforms among cases where you must register. For accommodation hosts this reads as conflicting with s 23-5 and with the ATO's own accommodation pages (residential rent is input taxed; only ride-sourcing has a regardless-of-turnover rule). It is unresolved: AU-SS-001.

## Division 87 (CRP only)

| Rule | Statement | Authority |
|---|---|---|
| Commercial accommodation | The right to occupy any part of CRP, with cleaning, utilities and similar supplied as part of that right. Separately charged extras carry normal GST. | s 87-15 |
| Long-term | Provided for a continuous period of at least `gst.div87_long_term_days` days in the same premises. Arrival day counts; departure day is disregarded. | s 87-20(1), (2) |
| Predominantly long-term | At least `gst.div87_predominantly_long_term_share` of individuals provided with commercial accommodation get it as long-term accommodation. The ruling accepts counting bookings, on the last 12 months' actual or next 12 months' projected occupancy. | s 87-20(3); GSTR 2012/7 paras 53-56 |
| Predominantly long-term premises | Value is `gst.div87_value_share` of the price that would otherwise apply, from day one. Price means the GST-inclusive price. | s 87-5 |
| Other premises | The first `gst.div87_long_term_days` less one days are valued normally; the part after is valued at `gst.div87_value_share` of its price. | s 87-10 |
| Election | The supplier may choose not to apply Division 87; long-term supplies are then input taxed (s 40-35(1)(b)), including the first days of a long booking; shorter stays stay taxable. Covers all commercial accommodation, no revocation within 12 months, no ATO notice. No credits for costs of input taxed supplies. | s 87-25; GSTR 2012/7 paras 58, 60, 61 |
| Residential premises | Division 87 does not apply; already input taxed. | s 40-35(1)(a) |

The Act says `gst.div87_value_share` "or such other percentage as is specified in the regulations"; the figure key holds the verified value.

## GST traps

1. Confusing short stay with hotel. Length of stay never turns residential premises into CRP.
2. Charging or claiming GST because the platform shows a GST line on its own fee.
3. Counting residential rent in GST turnover.
4. Applying Division 87 to a normal Airbnb house.
5. Counting to the long-stay threshold wrongly: check in on the 1st and check out on the 28th is one day short; check out on the 29th reaches it.
6. Treating an agent-manager's fee as GST-free or claiming it.
7. Serviced apartment in a hotel pool: owner residential, operator taxable.
8. Adding hotel-like services (daily cleaning, breakfast, reception, central booking for several dwellings) and drifting into CRP without noticing.
9. Telling a host they must register because they earn on a platform.
