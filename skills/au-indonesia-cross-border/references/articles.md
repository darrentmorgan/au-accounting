# Australia-Indonesia agreement: article guide (as modified by the MLI)

Written from the ATO synthesised text and the tabled 1992 text (see sources.md), in our own words. The agreement allocates taxing rights; each country's domestic law still decides what is taxed and at what rate. Every day limit and ceiling below is a figure key: read the value from a tool's `figures_used`.

| Art | Subject | Rule | Tool and figure keys |
|---|---|---|---|
| 1, 2, 3 | Scope, taxes, definitions | Residents of either or both countries. Australian income tax and petroleum resource rent tax; Indonesian income tax. No GST, VAT, payroll or stamp taxes. Undefined terms take the domestic meaning at the time. | none |
| 4 | Residence | Domestic residence first; individual tie-breaker: permanent home, habitual abode, closer personal and economic relations. MLI Art 4 for other persons. | `indonesia_dta_check` (`residence_tie_breaker`) |
| 5 | Permanent establishment | Fixed place of business, listed places, resource installations, building sites, service furnishing (no fixed place needed), agents. | `indonesia_service_pe_screen`; `au_indonesia.dta_pe_services_days`, `dta_pe_building_site_days`, `dta_pe_resource_installation_days` |
| 6 | Real property income | Taxable where the property is, including letting; leases and natural resource rights are real property. | `indonesia_treaty_allocation` |
| 7 | Business profits | Enterprise's own state only, unless a permanent establishment; then attributable profits plus same-or-similar sales and activities. | `indonesia_treaty_allocation` |
| 8, 9 | Ships and aircraft; associated enterprises | Residence state for international traffic; arm's length re-allocation with a correlative adjustment. Transfer pricing is out of scope. | AU-IDN-003 |
| 10 | Dividends | Source-state ceiling on the gross amount; not applied where connected with a permanent establishment or fixed base; branch profits additional tax cap; Indonesian production sharing carve-out. | `indonesia_dta_check`; `residency.indonesia_dta_wht_dividends`; `au_indonesia.dta_branch_profits_additional_tax_cap` |
| 11 | Interest | Source-state ceiling; arm's length amount only where a special relationship exists. | `residency.indonesia_dta_wht_interest` |
| 12 | Royalties | Two tiers: equipment, know-how, related ancillary assistance and forbearance take the lower; copyright, patents, designs, trademarks, secret processes, film and broadcast take the higher. | `residency.indonesia_dta_wht_royalties_equipment_know_how`, `residency.indonesia_dta_wht_royalties_other` |
| 13 | Alienation of property | Real property (13(1)); permanent establishment business property (13(2)); ships and aircraft (13(3)); shares or comparable interests in land-rich entities (13(4), MLI Art 9 lookback); anything else is left to domestic law (13(5)). | `indonesia_treaty_allocation`; `au_indonesia.mli_land_rich_lookback_days` |
| 14 | Independent personal services | Residence state only, unless a fixed base is regularly available or presence exceeds the limit in any 12 months. | `indonesia_presence_window`, `indonesia_dta_check`; `residency.indonesia_dta_days_threshold` |
| 15 | Dependent personal services | Work state may tax unless all four exemption conditions hold. | same as Art 14 |
| 16 | Directors' fees | Company's state may tax; no threshold. | `indonesia_treaty_allocation` |
| 17 | Entertainers and athletes | Performance state may tax, overriding Arts 14 and 15. | `indonesia_treaty_allocation` |
| 18 | Pensions and annuities | Residence state; source state may tax up to a ceiling. | `au_indonesia.dta_wht_pensions_annuities` |
| 19 to 21 | Government service, teachers, students | Special rules; teacher visits within a limit of years. | `au_indonesia.dta_teacher_visit_max_years` |
| 22, 23 | Other income; source | Residence state; source state may also tax; income the agreement lets a state tax is deemed sourced there for the credit and domestic law. | `indonesia_treaty_allocation` |
| 24 | Elimination of double tax | Australia credits Indonesian tax paid under Indonesian law and the agreement (through Div 770); Indonesia credits Australian tax. Underlying credit for a corporate dividend holder with enough voting power. | `indonesia_treaty_fito`; `au_indonesia.dta_underlying_tax_credit_min_voting_share` |
| 25, 26 | Mutual agreement, information | Case presented within a period of first notification; exchange of information. | `au_indonesia.dta_map_case_presentation_years` |
| 28 to 30 | Timor Zone, entry into force, termination | In force since December 1992; effective in Australia from the 1993-94 income year for other taxes; continues indefinitely. | none |

## Points that differ from the OECD Model

- Tie-breaker order: permanent home, then habitual abode, then closer relations. No nationality step, no mutual agreement step for individuals.
- The limits are in days in any 12 months, counted by presence; they are not the domestic 183-day residency test and not the income year.
- Service permanent establishment (Art 5(2)(j)) needs no fixed place of business.
- Share gains: no residence-only rule (Art 13(5)); land-rich shares are taxable where the property is (Art 13(4)).
- No non-discrimination article.
- The saving clause (MLI Art 11) keeps each country's right to tax its own residents, except for the listed benefits including the Art 24 credit.

## Not covered (escalate)

Indonesian domestic tax and residency, structures (PT, PT PMA, trusts, partnerships), related-party charges, permanent establishment and fixed base determinations, land-rich entities, software or licence characterisation, the MLI principal purpose test, dual-resident companies.
