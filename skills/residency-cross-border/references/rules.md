# Residency indicators: how the tool weighs facts

The `residency_indicators` tool is a screening aid built from the factor lists in TR 2023/1. It is not a legal test and it never determines residency.

## The four tests (ITAA 1936 s 6(1); TR 2023/1 paras 10-16)
1. Resides (ordinary concepts, paras 17-54).
2. Domicile in Australia, unless the Commissioner is satisfied the permanent place of abode is outside Australia (paras 55-82).
3. More than half the income year present in Australia, unless usual place of abode is overseas and there is no intention to take up residence (paras 83-95).
4. Commonwealth superannuation fund (PSS or CSS) member, or their spouse or child under 16 (paras 96-97).

Any one test met means resident. A person who meets none is not a resident. Factors from the whole year and surrounding years count (para 16).

## Weights used by the tool (screening only)
- Presence 2 points for Australia when more than half the year present. For someone not resident the year before, a shorter stay is 1 point overseas (visits under about six months rarely amount to residing, para 29). For a previous resident, absence is neutral (para 25).
- Home 2, family 2, intention 2, employment 1, assets 1. Each fact points to Australia, overseas, both, or neither.
- Resides likely met: Australian points at least 5 and ahead by 4 or more. Likely not met: overseas points at least 5 and ahead by 3 or more for a person not previously resident, 4 or more for a previous resident (leaving is harder than arriving).
- Conflict: both sides at least 3 and the gap under 4. A conflict returns `uncertain_escalate`.
- Any missing fact contributes nothing and appears in `missing_facts`.

## Domicile test inputs
- Domicile is common law modified by the Domicile Act 1982 (paras 56-62); a working visa alone rarely creates a domicile of choice (para 61).
- Permanent place of abode overseas is likely only when the home and family have moved and the stay is indefinite or substantial (paras 63-82). Living in both places means it cannot be said to be overseas (para 67).

## Part-year residency (paras 105-107)
- Residency can start on arrival, even part-way through the year, when behaviour is consistent with residing (paras 27, 39, 45).
- Residency ends when a permanent place of abode overseas is established, not on the day of departure (paras 25, 63).
- The tax-free threshold is pro-rated by the months from the month residency starts to the month it ends (para 106). Pass the months to `individual_income_tax`.

## Temporary residents (Subdiv 768-R)
- Definition is in ITAA 1997 s 995-1: a holder of a temporary visa under the Migration Act 1958 who does not have an Australian-resident spouse.
- Foreign-source ordinary and statutory income is non-assessable non-exempt (s 768-910), except remuneration for employment or services performed while a temporary resident. Gains and losses that would be disregarded for a foreign resident are disregarded (s 768-915).
- Australian-source income is taxed as normal (ATO ID 2007/108).

## Reform status
- The Board of Taxation model with a 183-day bright line and secondary factor tests was recommended in 2019 and consulted on by Treasury in 2023. Inferred from searches to 29 Sep 2026: not enacted. The four tests above apply. Re-check before relying on this for a later year.
