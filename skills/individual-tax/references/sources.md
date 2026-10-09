# Primary sources: individual-tax

Read 29 Sep 2026 unless stated. Figures themselves live in `data/rates/<year>.yaml` and `data/rates/<year>.d/individual.yaml`, each with its own source URL.

## Legislation
- Income Tax Rates Act 1986 (compilation in force 1 Jul 2026): Sch 7 Pt I (resident rates by year), Pt II (non-resident rates), Pt III (working holiday makers), s3A (working holiday taxable income), ss18-20 (part-year tax-free threshold). https://www.legislation.gov.au/C2004A03348/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_1/document_1.html
- Medicare Levy Act 1986 (compilation in force 1 Jul 2026): s3 (threshold amount, phase-in limit), s6 (rate), s7 (small incomes), s8 (family reduction), ss8B-8D (surcharge), s9 (prescribed persons for part of the year). https://www.legislation.gov.au/C2004A03351/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_1/document_1.html
- Treasury Laws Amendment (Delivering an Efficient and Trusted Tax System) Act 2026 (No. 58 of 2026) Sch 5: Medicare low-income thresholds for 2025-26 and later years. https://www.legislation.gov.au/C2026A00058/asmade/2026-06-30/text/original/epub/OEBPS/document_1/document_1.html
- Income Tax Assessment Act 1997 (compilation in force 1 Jul 2026), Subdiv 61-D (LITO), volume 2. https://www.legislation.gov.au/C2004A05138/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_2/document_2.html
- Income Tax Assessment Act 1936 (compilation No. 192, 1 Jul 2026; re-read 9 Oct 2026), s6(1) (resident), volume 1. https://www.legislation.gov.au/C1936A00027/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_1/document_1.html
- Income Tax Assessment Act 1936 (same compilation), s251U (prescribed persons), volume 4. https://www.legislation.gov.au/C1936A00027/2026-07-01/2026-07-01/text/original/epub/OEBPS/document_4/document_4.html
- Higher Education Support Act 2003 (compulsory repayment, repayment income). https://www.legislation.gov.au/C2004A01234/latest/text

## ATO guidance
- Resident tax rates (2019-20 to 2026-27): https://www.ato.gov.au/tax-rates-and-codes/tax-rates-australian-residents
- Foreign resident rates: https://www.ato.gov.au/tax-rates-and-codes/tax-rates-foreign-residents
- Working holiday maker rates: https://www.ato.gov.au/tax-rates-and-codes/tax-rates-working-holiday-makers
- Low income tax offset: https://www.ato.gov.au/individuals-and-families/income-deductions-offsets-and-records/tax-offsets/low-income-tax-offset
- Part-year tax-free threshold (worked example): https://www.ato.gov.au/individuals-and-families/coming-to-australia-or-going-overseas/coming-to-australia/tax-free-threshold-for-newcomers-to-australia
- Australian resident for tax purposes (part-year residents): https://www.ato.gov.au/individuals-and-families/coming-to-australia-or-going-overseas/your-tax-residency/australian-resident-for-tax-purposes
- Medicare levy reduction, low-income earners (worked example): https://www.ato.gov.au/individuals-and-families/medicare-and-private-health-insurance/medicare-levy/medicare-levy-reduction/medicare-levy-reduction-for-low-income-earners
- Medicare levy reduction, family income (worked example): https://www.ato.gov.au/individuals-and-families/medicare-and-private-health-insurance/medicare-levy/medicare-levy-reduction/medicare-levy-reduction-family-income
- M1 Medicare levy reduction or exemption 2026: https://www.ato.gov.au/forms-and-instructions/tax-return-for-individuals-2026/medicare-levy-questions-m1-m2-individual-tax-return-2026/m1-medicare-levy-reduction-or-exemption-2026
- Medicare levy surcharge income, thresholds and rates (worked example): https://www.ato.gov.au/individuals-and-families/medicare-and-private-health-insurance/medicare-levy-surcharge/medicare-levy-surcharge-income-thresholds-and-rates
- M2 Medicare levy surcharge 2026: https://www.ato.gov.au/forms-and-instructions/individual-tax-return-2026-instructions/medicare-levy-questions-m1-m2-individual-tax-return-2026/m2-medicare-levy-surcharge-2026
- Study and training loan repayment thresholds and rates (worked examples): https://www.ato.gov.au/tax-rates-and-codes/study-and-training-support-loans-rates-and-repayment-thresholds

## Cases
- Addy v Commissioner of Taxation [2021] HCA 34 (working holiday maker rates and treaty non-discrimination): ATO decision impact statement https://www.ato.gov.au/law/view/document?docid=LIT%2FICD%2FQUD108of2018%2F00001 ; judgment http://classic.austlii.edu.au/au/cases/cth/HCA/2021/34.html

- Standard work deduction: ITAA 1997 s 25-130, inserted by Act No. 49 of 2026 Sch 4 items 3 and 17 (2026–27 and later; re-read 9 Oct 2026). https://www.legislation.gov.au/C2026A00049/asmade/2026-06-26/text/original/epub/OEBPS/document_1/document_1.html

Scoped EOFY source refresh: 9 Oct 2026; key/year-specific reads and saved content hashes are in `docs/eofy-source-freshness.md` and `data/eofy/source-evidence.json`. Sources outside that bounded pack retain their original read dates.

## Individual settlement rules

Applied income year is returned on each `individual_tax_settlement.rule_authorities` entry. Tax, Medicare/MLS and HELP retain the primary sources and selected-year figures above. Settlement supports 2025-26 to 2027-28 only where each required figure is published and verified; missing later-year PHI tables are refused. These additions do not extend the scoped EOFY professional-review boundary.

- ITAA 1997 s63-10: non-refundable offsets before refundable offsets; unused refundable offsets follow Div67. https://www.ato.gov.au/law/view/document?docid=PAC/19970038/63-10
- ITAA 1997 s207-20: include the franking gross-up in assessable income and credit the corresponding offset once (read 9 Oct 2026). https://www.ato.gov.au/law/view/document?docid=PAC/19970038/207-20
- ITAA 1997 s207-145: qualified-person and integrity restrictions must be resolved before confirming entitlement. https://www.ato.gov.au/law/view/document?docid=PAC/19970038/207-145
- ITAA 1997 s67-25 and Div67: eligible individual franking offsets are refundable; excluded entities/regimes are not assumed eligible. https://www.ato.gov.au/law/view/document?docid=PAC/19970038/67-25
- ATO claiming the PHI rebate (read 9 Oct 2026): premium reduction versus refundable offset, exclude lifetime health cover loading, excess recovery and unclaimed entitlement. https://www.ato.gov.au/individuals-and-families/medicare-and-private-health-insurance/private-health-insurance-rebate/claiming-the-private-health-insurance-rebate
- ATO PHI thresholds and rebate tables (read 9 Oct 2026): payment-period and oldest-person age bands, family status, qualifying children and adult allocation. Figures remain in the selected year's `medicare.phi_rebate_*` tables. https://www.ato.gov.au/individuals-and-families/medicare-and-private-health-insurance/private-health-insurance-rebate/income-thresholds-and-rates-for-the-private-health-insurance-rebate
- TAA 1953 Sch1 s18-15: credit for confirmed PAYG withholding. https://www.ato.gov.au/law/view/document?docid=PAC/19530001/Sch1-18-15
- TAA 1953 Sch1 s45-30 (read 9 Oct 2026): income-year instalment credit net of claimed credits, including unpaid instalments; unpaid instalment liability remains separate. https://www.ato.gov.au/law/view/document?docid=PAC/19530001/Sch1-45-30
- PS LA 2011/21, tax offsets and Attachment A: ordering, refund/account offsets and PAYG credit priority for compulsory study-loan repayments. https://www.ato.gov.au/law/view/view.htm?docid=PSR/PS201121/NAT/ATO/00001
