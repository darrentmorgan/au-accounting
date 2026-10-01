# CGT calculation rules

Figures are named by key; values come from the rates files. Section references are to ITAA 1997 as compiled at 1 Jul 2026 (compilation 266, which includes Act No. 49 of 2026).

## 1. Single event (`capital_gain`)

1. **Time of event**: contract date (s104-10(3)); no contract, change of ownership. I1: when residency ends.
2. **Cost base** (s110-25): purchase price; incidental costs of buying and selling; costs of ownership (third element, only if not deducted and asset acquired after 20 Aug 1991; never for collectables or personal use assets); capital improvements; costs of defending title. Less capital works deductions (s110-45(1B)). **Reduced cost base** omits the third element and indexation.
3. **Gain** = proceeds less cost base; **loss** = reduced cost base less proceeds.
4. **Exemptions**: pre-CGT asset (acquired before 20 Sep 1985) until 30 Jun 2027; collectable with first element at or below `cgt.collectable_exempt_max_cost`; personal use asset gain with first element at or below `individual.personal_use_asset_cgt_exempt_max_cost` (losses always ignored).
5. **Discount** (Div 115): entity must be an individual, trust or complying super fund; asset held at least 12 months excluding the days of acquisition and event; not events D1, D2, D3, E9, F1, F2, F5, H2, J2, J5, J6, K10. Rates: `cgt.discount_individual_trust`, `cgt.discount_complying_super_fund`, `cgt.discount_company`.
6. **Foreign and temporary residents** (s115-115): period starting after 8 May 2012: resident days over twice the total days. Starting earlier and resident on 8 May 2012: total days less foreign days after 8 May 2012, over twice the total. Foreign on 8 May 2012: resident days after 8 May 2012 over twice the total, or the market value choice (full rate if the 8 May 2012 excess covers the gain, otherwise excess plus the resident share of the shortfall, over twice the gain). Days are counted inclusively.
7. **Frozen indexation** (s110-36(1), s960-275): assets acquired at or before 11.45 am 21 Sep 1999; each element except the third indexed from the quarter incurred to the September 1999 quarter using `cgt.frozen_indexation_cpi`, factor to three decimal places (round half up). Choose the lower result after losses; indexation and discount cannot both apply (s115-20). Companies use indexation. Individuals and trusts lose this for events from 1 Jul 2027.
8. **Losses** passed in `capital_losses_available` are applied before the discount.
9. **Foreign residents** are taxed only on taxable Australian property (s855-10). FRCGW (`cgt.frcgw_rate`) applies to the purchase price of Australian real property unless the vendor has a clearance certificate; it is a credit, not the final tax.

## 2. Law for CGT events on or after 1 July 2027 (Act No. 49 of 2026 Sch 1)

- **Discount** for individuals and trusts only for events before 1 Jul 2027 (s115-100(aa), (ab)); complying super funds keep one-third; companies unchanged.
- **Indexation** for individuals and trusts (s110-36(1A)): elements other than the third, from the quarter incurred (or 1 Jul 2027) to the quarter of the event (s960-275(1B)); 12 months ownership (s114-10, ignoring the deemed reacquisition); individuals must not be foreign or temporary residents at any time from the later of 1 Jul 2027 and acquisition to the event (s114-25). No indexation for losses.
- **Deemed sale** (s112-155, s112-160): a resident individual's asset held on 30 Jun 2027 is taken to be sold just before 1 Jul 2027 at market value and reacquired for that amount. The notional gain or loss is deferred to the year of the real sale; the deferred gain is a discount gain if the asset was held 12 months up to the real sale. Not for new dwellings or affordable housing gains, or where the foreign resident discount rules apply. A Ministerial apportioning method (s112-185) may replace market value; none made as at 29 Sep 2026.
- **Pre-CGT assets** (s112-175): deemed sold and reacquired at market value just before 1 Jul 2027; that gain or loss is disregarded; the asset stops being pre-CGT.
- **New residential dwellings** (s115-102): individuals (and via trusts and partnerships) keep the discount on the whole gain, or may choose indexation. The definition depends on a Ministerial instrument under s26-160(4) not made as at 29 Sep 2026.
- **Ordering** (s102-5): current-year losses reduce deferred non-residential, then deferred residential, then non-residential, then residential gains; then prior-year losses in the same order; then the quarantined residential amount (s26-155) against deferred residential then residential gains; then the discount; then small business concessions. Residential gains are those from residential dwellings, apportioned by residential accommodation days (s102-6).
- **Minimum tax** (Div 119, ITRA s12AA): resident individuals. Minimum tax capital gain = remaining residential and non-residential gains (not deferred, not new dwelling or affordable housing), less deductible gifts. Gap = minimum rate (`cgt.minimum_tax_rate_from_2027_28`) times that gain, less the income tax attributable to it (tax on taxable income less tax on taxable income without it), rounded down. Extra tax equals the gap. Excluded if a listed social security, veterans' or military payment was received in the year (s119-15). The tool reads the 2027-28 file for these figures, including the 2027-28 resident rates table (`individual.resident_rates`); it never uses the 2026-27 table.

## 3. Net capital gain (`net_capital_gain`)

Personal use losses ignored. Collectable losses (current, then carried forward) only against collectable gains; excess carried forward separately. Other current-year losses, then prior-year net capital losses (oldest first), reduce gains in category order and, within a category, the gains with the lowest discount first. Then quarantined amounts, then the discount. Unused losses carry forward.

## 4. Main residence (`main_residence_exemption`)

- Ownership period: settlement of purchase to settlement of sale, days inclusive.
- Each day is main residence (lived in), covered (absence choice), or taxable. Days lived in but partly used for income count at the floor area share (s118-190).
- Absence (s118-145): unlimited while not income producing; while income producing, 6 years per absence counted to the anniversary date; a new absence starts after the owner moves back in.
- Changeover (s118-140): both homes exempt for up to 6 months ending at settlement of the old one, if it was lived in for 3 continuous months in the last 12 and not income producing while not lived in.
- First used to produce income after 20 Aug 1996 (s118-192): if the dwelling was fully exempt up to then and only a partial exemption results, it is taken to be acquired then at market value; days and the 12-month test run from then.
- Taxable gain = gain times taxable days over ownership days (s118-185). Then losses and the discount.
- Foreign resident at the contract date: no exemption unless foreign for 6 years or less and a life event applies (terminal illness, death of spouse or minor child, relationship breakdown) (s118-110(3)-(5)).

## 5. Small business screen (`small_business_cgt_screen`)

Basic conditions (s152-10): CGT small business entity (turnover below `cgt.small_business_aggregated_turnover`) or maximum net asset value not above `cgt.small_business_max_net_asset_value`, and the active asset test (s152-35: active for half the ownership period, or 7.5 years if owned over 15 years). From the income year including 1 Jul 2027 the active asset reduction alone uses a small business entity test below `cgt.active_asset_reduction_turnover_gate_from_2027_28` (s152-205(2)). Screen only; always escalate application (AU-CGT-001).

## 6. Foreign resident CGT from 1 October 2026 (Act No. 86 of 2026 Sch 2)

For CGT events from 1 Oct 2026: statutory "real property" definition (s995-1) covering interests, rights, licences and fixed or installed things; taxable Australian real property includes things fixed or installed on Australian land and water entitlements; the principal asset test for indirect interests is met at the event or at any time in the 365 days before. Vendors of membership interests at or above the value threshold in TAA 1953 Sch 1 s14-210(3)(d)(ii) must notify the ATO before relying on a declaration that the interest is not an indirect Australian real property interest. Sch 3: foreign entities (not individuals) get a 50% discount on Australian renewable energy assets for events from 1 Oct 2026 and before 1 Jul 2040.

## 7. Crypto

A1 on sale, swap or spending (TD 2014/26). C2 on wrap and unwrap per draft TD 2026/D2 (preliminary view). Airdrops: capital account recipients hold a new CGT asset with cost base generally market value at receipt, business traders ordinary income, per draft TR 2026/D1. Personal use asset only if acquired and used mainly to buy items for personal consumption.
