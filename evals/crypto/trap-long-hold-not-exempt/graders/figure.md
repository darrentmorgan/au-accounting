---
type: regex
pattern: '(?<![\d,.])2,?500(?!\d|,\d)'
target: last_message
---

<!--
ATO CGT discount page (https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/cgt-discount): holding an asset 12 months gives a 50% discount (events before 1 Jul 2027), not an exemption. ATO PUA page (https://www.ato.gov.au/individuals-and-families/investments-and-assets/crypto-asset-investments/crypto-asset-as-a-personal-use-asset) and TD 2014/26 paras 17-21: crypto held as an investment is not a personal use asset regardless of amount.
Gain = 8,600 - 3,600 = 5,000. Held over 3 years: discount 50% = 2,500. Net capital gain 2,500.
Wrong: nil (exempt); 5,000 (no discount).
-->
The answer states a net capital gain of $2,500 and rejects both the 'exempt after 12 months' and personal use claims.
