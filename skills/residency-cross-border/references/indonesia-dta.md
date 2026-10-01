# Australia-Indonesia double tax agreement (1992, as modified by the MLI)

Text read in the ATO synthesised version and the tabled treaty (see sources.md). The agreement allocates taxing rights; domestic law of each country still decides what is taxed and at what rate. Australia taxes its residents on worldwide income and gives a credit for Indonesian tax under Art 24, applied through the general foreign tax credit rules (now Div 770).

| Article | Rule | Tool |
|---|---|---|
| 4(1)-(3) | Residence follows each state's domestic law. A person taxed only on local-source income is not a resident. A dual-resident individual is resident solely of the state with a permanent home; if both or neither, habitual abode; if both or neither, closer personal and economic relations. No nationality step, no mutual agreement step for individuals. Each step is a question of fact and Indonesian domestic residence is unverified, so report the outcome as an indication only, with the missing facts and AU-RES-001 and AU-IDN-002. | `indonesia_dta_check` article `residence_tie_breaker` |
| 5 | Permanent establishment, including services furnished through employees for more than the days threshold in any 12 months. | Not modelled; escalate PE questions. |
| 7 | Business profits taxable in the residence state unless a permanent establishment. | Not modelled. |
| 6 | Income from real property (for example a Bali villa) may be taxed where the property is. | Explain; Australian resident still taxed here with credit. |
| 10 | Dividends: source-state tax limited to the treaty ceiling. | article `dividends` |
| 11 | Interest: source-state tax limited to the treaty ceiling. | article `interest` |
| 12 | Royalties: lower ceiling for equipment rentals and know-how, higher for other royalties. | article `royalties` |
| 14 | Independent personal services: residence state only, unless a fixed base is regularly available in the other state, or presence exceeds the days threshold in any 12 months (income derived from activities there). | article `independent_services` |
| 15 | Employment: other state may tax remuneration for work done there unless all four hold: presence not above the days threshold in any 12 months, employer not resident of the work state, not borne by a permanent establishment or fixed base, and taxed in the residence state. Subject to Arts 16, 18, 19, 20. | article `employment` |
| 24 | Australia credits Indonesian tax; Indonesia credits Australian tax. | Use `foreign_income_tax_offset`. |

## Points to state
- The 120-day measure is any 12-month period, not the income year and not 183 days.
- A treaty ceiling is not the rate charged. Foreign tax above the ceiling that can be recovered from the foreign authority may not count for the offset.
- The MLI saving clause means the treaty does not restrict a country taxing its own residents, apart from listed articles.
- Indonesian domestic residency, the domestic withholding rate, VAT, PT PMA rules and DGT treaty-benefit forms are not verified here. Say so.
