# Short-stay accommodation, platforms and GST

Explain these tests; do not make the determination for an operator (AU-GST-002). The short-stay-accommodation skill owns the full short-stay workflow (GST screen, income tax apportionment, platform reporting); this file is the GST orientation for a BAS preparer.

## Residential premises vs commercial residential premises (CRP)

- Rent of residential premises for residential accommodation is input taxed (s40-35(1)(a)): no GST on the rent, no credits on the costs (s11-15). A single house or apartment let short term (Airbnb, Stayz, Booking.com) is still residential premises, including an apartment inside a complex that is itself CRP (ATO holiday apartments in commercial residential properties page).
- CRP (s195-1): hotel, motel, inn, hostel, boarding house, school accommodation, certain ships, marinas, caravan parks, camping grounds, and anything similar. Accommodation in CRP supplied by the entity that owns or controls the premises is taxable.
- GSTR 2012/6: whether premises are CRP is an overall impression of physical and operating characteristics, including commercial intention, multiple occupancy, holding out to the public, accommodation as the main purpose, central management (reservations, allocation of rooms, services), and hotel-like services. Draft update GSTR 2012/6DC (5 Nov 2025) aims at build-to-rent, hostels and boarding houses; the ATO says the Commissioner's view is unchanged. Treat GSTR 2012/6 as current.
- GSTR 2012/6 Example 12 (paras 82 to 85, in the current ruling and not only the draft): one apartment let short term through an on-site manager acting as agent for several apartments is not CRP; the owner's supply is input taxed.
- ATO private advice has treated an operator that owns or leases many apartments and runs them like a hotel as supplying CRP accommodation. Private advice binds only the applicant.

## Who is the supplier

- Agent model (manager acts for the owner, guest contracts with the owner): the owner supplies the accommodation (input taxed if residential); the manager's commission or management fee is a taxable supply to the owner, who cannot claim the credit.
- Principal model (manager holds head leases and supplies stays in its own name): the head lease from the owner stays residential and input taxed unless the premises are CRP; the operator's supplies may be CRP accommodation. Get facts and a private ruling: AU-GST-002.
- Division 153 Subdiv 153-B lets an intermediary and principal agree to treat a supply as two supplies; LCR 2018/2 para 71 says it is unavailable where an EDP operator is responsible under s84-55.

## Platforms

- The EDP rules are Subdiv 84-B: s84-55 (operator treated as the supplier of inbound intangible consumer supplies), s84-60 (extension by agreement, digital supplies only), s84-65 (meaning of inbound intangible consumer supply), s84-70 (meaning of electronic distribution platform). Section 84-81 is about low value goods and s84-100 about when an entity is not an Australian consumer; neither is about accommodation.
- A stay in Australian real property is not an inbound intangible consumer supply, so the platform does not become the supplier of the stay (inference from those sections and LCR 2018/2).
- Platform service fees: a host who only makes input taxed residential supplies cannot claim credits for GST on those fees (s11-15(2)(a)), whatever the platform charges; a registered CRP operator can. The ATO passage about an offshore platform assuming a user is unregistered unless given an ABN and declaration is in the ride-sourcing guidance; no accommodation equivalent was found, so do not state it for hosts. Report rent gross; fees are deductible for income tax.
- Sharing economy reporting regime (TAA Sch 1 Subdiv 396-B, s 396-55 table item 15; LI 2025/5): platforms report short-term accommodation bookings to the ATO twice yearly, with no limit by length of stay in the current instrument; the ATO data-matches hosts. It is a reporting duty only and does not register anyone for GST. Detail is in the short-stay-accommodation skill.

## Registration for hosts

- GST turnover excludes input taxed supplies, so a host whose only income is residential short-stay rent does not reach the registration threshold on that income, however large. Other taxable income (cleaning fees charged separately in their own right, consulting, management fees) counts.
- Use `gst_registration_check` with `input_taxed_sales_included`.

## Division 87 (only for CRP)

- Long-term accommodation: right to occupy for at least `gst.div87_long_term_days` continuous days (s87-20; GSTR 2012/7 para 10).
- Premises predominantly for long-term accommodation (at least the share in `gst.div87_predominantly_long_term_share` of supplies are long term): value of a long-term supply is `gst.div87_value_share` of the price (s87-5). Otherwise s87-10 reduces only the days from day `gst.div87_long_term_days` of the stay onwards; the earlier days are fully taxable.
- The operator may choose not to apply Div 87 (s87-25), making long-term supplies input taxed; the choice binds for at least 12 months.
- Stays shorter than `gst.div87_long_term_days` days in CRP are always fully taxable. Division 87 does not apply to residential premises (already input taxed).
