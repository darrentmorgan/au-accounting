# Australia-Indonesia cross-border: primary-source brief (GOAL v0.3, gate 11)

Read and verified 2026-09-29 on branch `v0.3/research-au-id` (from `goal/v0.3`). Audience: the eval-author (who will not read any skill) and the skill-builder for `au-indonesia-cross-border`. Everything below is in our own words, from primary pages only (ATO, legislation.gov.au, Treasury, the treaty texts, the OECD's own Model Tax Convention where the ATO says it is an interpretive aid). No third-party guide material was opened.

Confidence tags: **KNOWN** = read on the cited primary page this session. **INFERRED** = my reasoning from KNOWN text, or an interpretive aid the treaty text does not itself contain. **OPEN** = unresolved, escalate. **NOT VERIFIED** = Indonesian domestic law, out of scope (listed only as a treaty input or escalation trigger).

Framing for anything built from this: working paper only, for registered tax agent review. This project is not a registered agent.

---

## 1. Bottom line

1. **Treaty**: 1992 Australia-Indonesia double tax agreement, in force since 14 Dec 1992, no protocol, modified by the MLI (both countries ratified; effective for every income year from 2021-22, so 2025-26 onward is fully inside the modified text). [S1, S5]
2. **120 days, three different tests.** Art 14(1)(b) (independent services) and Art 15(2)(a) (employment) count the individual's presence; Art 5(2)(j) (service PE) counts days on which the enterprise furnishes services; Art 5(2)(h) and (i) count how long an installation or building site lasts. None is 183 days and none is the income year. [S1, S2]
3. **Employment exemption is all four conditions, all-or-nothing.** If any fails (for example the employer is an Indonesian company, or the 12-month presence count is exceeded), Indonesia may tax the remuneration for the work done in Indonesia, not only the excess days. [S1 Art 15, S3]
4. **Some Indonesian taxing rights have no day count at all**: a fixed base regularly available (Art 14(1)(a)), directors' fees (Art 16), real property income (Art 6), gains on Indonesian real property (Art 13(1)), and gains on shares in real-property-rich companies (Art 13(4)). [S1]
5. **Treaty rates are ceilings.** Only Indonesian tax correctly imposed under Indonesian law and the treaty counts for the Australian foreign income tax offset (FITO); the excess must be reclaimed from Indonesia. [S7 s 770-15, S8]
6. **The treaty never stops Australia taxing its own residents** (MLI Art 11 saving clause), except for the listed benefits, which include the Art 24 credit. Relief is FITO under ITAA 1997 Div 770, capped by s 770-75. [S1, S7]
7. **Generic OECD habits that are wrong here**: tie-breaker order (habitual abode comes before personal and economic relations, no nationality step, no mutual agreement step), 183 days, a residence-only rule for share gains (Art 13(5) leaves gains on other property to domestic law), and a non-discrimination article (this agreement has none). [S1, S17]
8. **Australian withholding on payments to Indonesian residents**: unfranked dividends 15% instead of 30%, franked dividends nil, interest 10% (no relief), royalties 10% or 15% instead of 30%. [S1, S3, S12]
9. **FX**: the ATO does publish rupiah rates (annual, half-year and monthly). Average rates suit spread-out income; a one-off capital event needs the rate at the event; a year-end rate is not allowed for foreign income not received in Australia in the year derived. [S9, S10, S11]
10. **Source conflicts to report (no v0.2 VERIFIED figure is contradicted)**: see section 11 (ATO FITO guide Example 16 vs Medicare threshold; earlier briefs said the treaty is "scheduled" to the Act, it is not; the premise of eval `trap-unverified-fx-rate`).

---

## 2. Source index

| ID | Source | URL |
|---|---|---|
| S1 | ATO synthesised text of the MLI and the Agreement (joint with Indonesia's Ministry of Finance; not itself a source of law) | https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf (HTML: https://www.ato.gov.au/law/view/document?DocID=MLI%2FMLI-Indonesia-agreement) |
| S2 | Tabled 1992 treaty text, Parliament of Australia | https://parlinfo.aph.gov.au/parlInfo/search/display/display.w3p;query=Id%3A%22publications%2Ftabledpapers%2FHSTP05892_1990-92%22;src1=sm1 |
| S3 | Explanatory Memorandum, Income Tax (International Agreements) Amendment Bill 1992 | https://www.ato.gov.au/law/view/print?DocID=NEM/EM92018/NAT/ATO/00004&PiT=99991231235958 |
| S4 | International Tax Agreements Act 1953 (compilation 43, 29 Jun 2023; latest table of contents lists the same provisions) | https://www.legislation.gov.au/C1953A00082/2023-06-29/2023-06-29/text/original/epub/OEBPS/document_1/document_1.html and https://www.legislation.gov.au/C1953A00082/latest/text |
| S5 | Treasury, Income tax treaties table (last updated 24 Mar 2026) | https://treasury.gov.au/tax-treaties/income-tax-treaties |
| S6 | Treasury, Multilateral Instrument page | https://treasury.gov.au/tax-treaties/multilateral-instrument |
| S7 | ITAA 1997 ss 770-10, 770-15, 770-75 (ATO legal database) | https://www.ato.gov.au/law/view/document?docid=PAC%2F19970038%2F770-10 ; .../770-15 ; .../770-75 |
| S8 | ATO Guide to foreign income tax offset rules 2026: When a FITO applies; Calculate your FITO or offset limit | https://www.ato.gov.au/forms-and-instructions/foreign-income-tax-offset-rules-guide-2026/when-a-fito-applies ; https://www.ato.gov.au/forms-and-instructions/foreign-income-tax-offset-rules-guide-2026/calculate-your-fito-or-offset-limit |
| S9 | ITAA 1997 s 960-50 (ATO legal database) | https://www.ato.gov.au/law/view/document?docid=PAC%2F19970038%2F960-50 |
| S10 | ATO Translation (conversion) rules; General information on average rates | https://www.ato.gov.au/businesses-and-organisations/corporate-tax-measures-and-assurance/foreign-exchange-gains-and-losses/translation-conversion-rules ; https://www.ato.gov.au/businesses-and-organisations/corporate-tax-measures-and-assurance/foreign-exchange-gains-and-losses/in-detail/general-information-on-average-rates |
| S11 | ATO published rates: annual FY2026; monthly FY2026; monthly FY2027 | https://www.ato.gov.au/tax-rates-and-codes/foreign-exchange-rates-annual-2026-financial-year ; https://www.ato.gov.au/tax-rates-and-codes/foreign-exchange-rates-monthly-2026-financial-year ; https://www.ato.gov.au/tax-rates-and-codes/foreign-exchange-rates-monthly-2027-financial-year |
| S12 | Withholding on payments to foreign residents: Income Tax (Dividends, Interest and Royalties Withholding Tax) Act 1974 s 7; ATO rate and payer pages | https://classic.austlii.edu.au/au/legis/cth/consol_act/itiarwta1974590/s7.html ; https://www.ato.gov.au/businesses-and-organisations/hiring-and-paying-your-workers/payg-withholding/payments-you-need-to-withhold-from/withholding-from-investment-income/investment-income-and-royalties-paid-to-foreign-residents/withholding-rate ; https://www.ato.gov.au/businesses-and-organisations/international-tax-for-business/in-detail/income/withholding-from-dividends-paid-to-foreign-residents ; https://www.ato.gov.au/individuals-and-families/investments-and-assets/foreign-resident-investments/interest-unfranked-dividends-and-royalties |
| S13 | ATO individual supplementary tax return 2026 instructions, Q20 (foreign source income and assets) and Q21 | https://www.ato.gov.au/forms-and-instructions/individual-supplementary-tax-return-2026-instructions/income-questions-13-24-supplementary-tax-return-2026/20-foreign-source-income-and-foreign-assets-or-property-2026 ; https://www.ato.gov.au/forms-and-instructions/individual-supplementary-tax-return-2026-instructions/income-questions-13-24-supplementary-tax-return-2026/21-rent-2026 |
| S14 | ATO certificate of residency and overseas tax relief form (updated 3 Jun 2026) | https://www.ato.gov.au/individuals-and-families/coming-to-australia-or-going-overseas/certificate-of-residency-and-overseas-tax-relief-form |
| S15 | ATO foreign income return form guide: CFC listed countries (Income Tax Assessment (1936 Act) Regulation 2015 reg 19) | https://www.ato.gov.au/law/view/document?locid=%27SAV%2FFIRFG%2FH7%27 ; https://www.ato.gov.au/forms-and-instructions/foreign-income-return-form-guide-2020/chapter-1-attribution-of-the-current-year-profits-of-a-controlled-foreign-company-cfc/part-1-are-you-subject-to-the-cfc-measures |
| S16 | TR 2001/13 (interpreting Australia's DTAs, use of OECD Commentaries); TR 2023/1 para 86 (part-day counts for the domestic 183-day test) | https://www.ato.gov.au/law/view/print?DocID=TXR%2FTR200113%2FNAT%2FATO%2F00001&PiT=99991231235958 ; https://www.ato.gov.au/law/view/document?DocID=TXR%2FTR20231%2FNAT%2FATO%2F00001 |
| S17 | OECD Model Tax Convention 2017, condensed version (Art 4(2) text; Commentary on Art 4 paras 13 to 19; Commentary on Art 5 paras 157 to 163; Commentary on Art 15 paras 5 and 5.1) | https://www.oecd.org/content/dam/oecd/en/publications/reports/2017/12/model-tax-convention-on-income-and-on-capital-condensed-version-2017_g1g8769b/mtc_cond-2017-en.pdf |
| S18 | Indonesian Directorate General of Taxes, PER-43/PJ/2011 (domestic residence of individuals; Indonesian text, currency of the regulation not checked) | https://pajak.go.id/en/node/62005 |
| S19 | ITAA 1997 s 6-5, s 102-20, s 768-5 (ATO legal database) | https://www.ato.gov.au/law/view/document?docid=PAC%2F19970038%2F6-5 ; .../102-20 ; .../768-5 |

Fetch notes: ATO PDFs and several ATO pages return 403 to plain fetchers; they were read through Exa fetch and curl with a browser user agent. AustLII's treaty page for [1992] ATS 40 returned 403, so the authentic-text cross-check is the tabled treaty on ParlInfo (S2), which agreed with S1 on every figure below.

---

## 3. The instruments and their status

| Item | Fact | Source | Tag |
|---|---|---|---|
| Agreement | Signed at Jakarta 22 Apr 1992; text is [1992] ATS 40; in force 14 Dec 1992 (GN 5 [1993] at 461) | S4 s 3, S5 | KNOWN |
| Force of law | ITAA 1953 s 5 table row "Indonesian agreement" (no related provisions). The Act's only Schedule is the Taipei agreement, so the Indonesian text is **not scheduled to the Act**. Earlier repo briefs said "scheduled"; that is a wording error, not a figure error | S4 | KNOWN |
| Priority over domestic law | ITAA 1953 s 4(2): the Act prevails over inconsistent provisions of the assessment Acts and Acts imposing Australian tax, except Part IVA ITAA 1936 and Subdiv 195-C ITAA 1997 (s 4(3)). So the general anti-avoidance rule can override treaty outcomes | S4 | KNOWN |
| Treaty limit on Australian withholding | ITAA 1953 s 17A(1): where a treaty limits Australian tax on a dividend or royalty and the withholding exceeds the limit, the liability is reduced by the excess | S4 | KNOWN |
| Dividend source | ITAA 1953 s 18: a foreign-incorporated company that is resident in the treaty country under that country's law is treated as paying a dividend sourced there, for the treaty | S4 | KNOWN |
| Land-rich shares, older treaties | ITAA 1953 s 3A(2) extends pre-27 April 1998 land-rich provisions to indirect interests through interposed entities, only for Australian real property; s 3A(4) switches it off if the provision is later amended or substituted through the Act. Whether the MLI's Art 9 change triggered s 3A(4) for Art 13(4) is unresolved | S4 | OPEN |
| Protocols | None. The Treasury table lists only the 1992 DTA for Indonesia (status "In force"). The Treasury treaties landing page shows no Indonesia negotiation notice | S5, Treasury tax treaties page https://treasury.gov.au/tax-treaties | KNOWN |
| Effective in Australia | Art 29: withholding taxes for income derived on or after 1 Jul of the year after entry into force; other Australian tax for years of income beginning on or after that 1 Jul. Entry into force 14 Dec 1992 gives 1 Jul 1993 | S1 Art 29, S3 | INFERRED (arithmetic) |
| Termination | Continues indefinitely; either country may give notice by 30 Jun in any year after the first five years. No notice appears in Treasury's table | S1 Art 30, S5 | KNOWN |

### MLI (Treasury MLI page and the ATO synthesised text)

- Both countries signed the MLI on 7 Jun 2017. Australia ratified 26 Sep 2018 (in force for Australia 1 Jan 2019). Indonesia ratified 28 Apr 2020 (in force for Indonesia 1 Aug 2020). Treasury's table marks the Indonesia agreement as modified by the MLI, entry into force 1 Aug 2020, synthesised text available. [S1, S5, S6] KNOWN
- Effect dates (ATO synthesised text): withholding taxes, events on or after 1 Jan 2021; other Australian taxes, taxable periods beginning on or after 26 Jun 2021; other Indonesian taxes, periods beginning on or after 1 Jan 2022. [S1] KNOWN. Australian income years start on 1 July, so the first Australian income year inside the MLI text is 2021-22. INFERRED (arithmetic).
- MLI provisions that actually modify this agreement (boxes in the synthesised text): Art 6 (preamble), Art 4 (dual-resident non-individuals: competent authorities settle by agreement, having regard to place of effective management, place of incorporation and other factors; no treaty relief if they do not agree), Art 7 (principal purposes test, no simplified limitation-on-benefits), Art 9 (land-rich shares, tested at any time in the preceding 365 days, extended to comparable interests such as partnership or trust interests), Art 11 (saving clause), Art 13 (Option A anti-fragmentation of the specific-activity exemptions), Art 14 (splitting up of contracts, building-site limb only), Art 15 (closely related: control, or more than 50% of beneficial interest or of vote and value), Art 16(3) (mutual agreement wording). [S1] KNOWN
- Not shown in the synthesised text, so they do not modify this agreement: MLI Arts 3, 5, 8, 10, 12, 17. Treasury confirms Australia did not adopt Arts 5, 10 and 12. [S1, S6] KNOWN. Consequence: no MLI commissionaire rule (Art 12), so agency PE stays under the treaty's own Art 5(4) and (5).
- Saving clause detail (MLI Art 11 as shown): the agreement does not affect a country's taxation of its own residents, except for the benefits in Art 9(3), Art 18(4), Arts 19, 20, 21, 24, 25 and 27. [S1] KNOWN. Practical result: Art 14 or 15 "taxable only in the residence State" language never exempts an Australian resident from Australian tax; the exception list keeps the Art 24 credit, the teacher and student exemptions, government service and the mutual agreement procedure.

---

## 4. Article guide

Fixed text: S1 (modified) and S2 (tabled original). EM commentary: S3. Article numbers below are the agreement's own.

### 4.1 Overview table

| Art | Subject | Rule in one line | Day or rate figure (existing key in bold) |
|---|---|---|---|
| 1, 2 | Scope, taxes | Persons resident in one or both countries. Covers Australian income tax and petroleum resource rent tax, and Indonesian income tax. No GST, VAT, payroll or stamp taxes | none |
| 3 | Definitions | "Enterprise" = business of a resident. Undefined terms take domestic-law meaning at the time of application (3(3)). Competent authority: Commissioner of Taxation, and Indonesia's Minister of Finance | none |
| 4 | Residence | Domestic residence first; tie-breaker for individuals; MLI Art 4 for other persons | none |
| 5 | Permanent establishment | Fixed place, plus deemed PEs (installation, building site, service furnishing), agents | 120 days x3 (see 4.3) |
| 6 | Real property income | Taxable where the land is, including letting and any other use; leases and mineral rights count as real property | none |
| 7 | Business profits | Residence State only, unless a PE; then profits of the PE plus same-or-similar sales and activities | none |
| 8 | Ships and aircraft | Residence State for international traffic | none |
| 9 | Associated enterprises | Arm's length re-allocation, with a correlative adjustment (9(3)) | none |
| 10 | Dividends | Source State cap; PE and fixed base exception; branch profits additional tax cap | **`residency.indonesia_dta_wht_dividends`**; PE-branch cap proposed key |
| 11 | Interest | Source State cap | **`residency.indonesia_dta_wht_interest`** |
| 12 | Royalties | Two-tier source State cap | **`residency.indonesia_dta_wht_royalties_equipment_know_how`**, **`..._royalties_other`** |
| 13 | Alienation of property | Real property and land-rich shares taxable where the property is; other gains left to domestic law | 365-day look-back (MLI) proposed key |
| 14 | Independent personal services | Residence State only, unless a fixed base or presence over the days limit | **`residency.indonesia_dta_days_threshold`** |
| 15 | Dependent personal services | Work State may tax unless all four exemption conditions hold | **`residency.indonesia_dta_days_threshold`** |
| 16 | Directors' fees | Company's State may tax; no threshold | none |
| 17 | Entertainers | Performance State may tax, overriding Arts 14 and 15 | none |
| 18 | Pensions and annuities | Residence State; source State may tax up to a cap | pensions cap proposed key |
| 19 to 21 | Government service, teachers, students | Special rules; teacher exemption for visits within a limit; student maintenance payments exempt | 2 years proposed key |
| 22, 23 | Other income; deemed source | Residence State only, source State may also tax; income the treaty lets a State tax is deemed sourced there for the credit and domestic law | none |
| 24 | Elimination of double tax | Australia credits Indonesian tax (subject to Australian credit law); Indonesia credits Australian tax; underlying credit for 10%-voting corporate dividends | 10% voting share proposed key |
| 25, 26 | Mutual agreement, information exchange | Case within a period of first notification; exchange of information | 3 years proposed key |
| 28 to 30 | Timor Zone saving, entry into force, termination | see section 3 | none |

There is **no non-discrimination article** in the agreement (Arts 1 to 30 all read; the word does not appear in S1 or S2). [S1, S2] KNOWN. INFERRED consequence: an Addy-style argument (High Court, 2021, turning on the UK agreement's non-discrimination article) has no textual hook in this treaty. Confirm against the individual-tax skill's working holiday maker escalation before relying on it.

### 4.2 Residence, Article 4

- 4(1): a person is resident of a State if resident under that State's tax law. 4(2): not resident if liable to tax there only on income from sources in that State. [S1]
- 4(3), individuals resident of both under domestic law: (a) permanent home available in one State only decides; (b) if a permanent home is available in both or neither, habitual abode; (c) if habitual abode is in both or neither, the State with which economic and personal relations are closer. There is no nationality step and no competent authority step. [S1] KNOWN
- **Order differs from the OECD Model.** The OECD 2017 Model reads: permanent home, then closer personal and economic relations (centre of vital interests), then habitual abode, then nationality, then mutual agreement. This agreement puts habitual abode before relations and drops the last two steps. [S17 Art 4(2)] KNOWN
- Interpretive aid (the Commentary is not treaty text; the ATO treats OECD Commentaries as relevant under TR 2001/13 paras 101 to 111) [S16, S17] INFERRED: a home is "available" if the individual has arranged to have it at all times continuously, not only for a short stay; a house rented out and effectively handed to an unrelated party is not available (Commentary on Art 4, para 13). Habitual abode looks at frequency, duration and regularity of stays that are part of the settled routine of life, not just which country had more days, and a person can have a habitual abode in both States (paras 19 and 19.1). Consequence for a Bali villa that is let out through platforms most of the year: it may not count as a permanent home available to the owner. Fact-dependent: escalate rather than conclude.
- EM effect (KNOWN): a dual resident deemed solely Indonesian resident gets Australian treaty benefits for Australian-source income, and Indonesia owes the Art 24 relief; but the person stays a resident for Australian domestic law "so far as the agreement allows", and Art 13(5) preserves Australia's capital gains rules for such a person. Art 22 then stops Australia taxing items of income not covered by another article (for example Indonesian-source or third-country income) unless connected with an Australian PE or fixed base. [S3 Art 4 note]
- Companies and other non-individuals: MLI Art 4 replaces the old place-of-effective-management rule. Competent authorities decide by mutual agreement; without agreement the entity gets no treaty relief. A dual-resident company seeks that agreement through a competent authority request under MLI Art 4(1), lodged with the ATO's mutual agreement procedure program; the ATO early engagement request for a treaty residency determination is for individuals (corrected 2026-09-30 after judge round 2, ATO 'Mutual agreement procedure' page). [S1, S14] KNOWN
- Trusts and partnerships: "person" means an individual, a company and any other body of persons (Art 3(1)(d)); the text does not say how an Australian discretionary trust is treated. Art 7(8) treats a resident beneficiary's share of a trustee's business profits as a PE profit where the trustee would have a PE. Escalate trust structures. [S1, S3] OPEN

### 4.3 Permanent establishment, Article 5

Text as modified (S1; S2 agrees on the 120-day limbs).

- 5(1): fixed place of business through which business is wholly or partly carried on. 5(2) lists: place of management, branch, office, factory, workshop, extraction places, farms and plantations; **(h)** installation, rig or ship used for exploring or exploiting natural resources where the use continues for more than 120 days; **(i)** building site, construction, installation or assembly project or supervisory activities lasting more than 120 days (MLI Art 14 splitting-up rule applies to this count only); **(j)** furnishing of services, including consultancy, through employees or other personnel engaged for the purpose, if furnished for the same or a connected project within the State for periods aggregating more than 120 days within any 12 month period.
- (j) needs **no fixed place of business** and is not limited to consultancy. It is the main PE risk for an Australian company whose people work in Bali. KNOWN
- 5(3): usual exceptions (storage, display, processing, purchasing, information, preparatory or auxiliary activity), tightened by MLI Art 13 Option A: they do not apply where the same or a closely related enterprise has another place there and the combined activity is not preparatory or auxiliary, or if that other place is itself a PE, provided the activities are complementary parts of a cohesive operation. KNOWN
- 5(4) dependent agent: a person who manufactures or processes goods for the enterprise, habitually exercises authority to conclude contracts on its behalf (unless limited to purchasing), or habitually keeps stock for regular delivery, creates a PE. 5(5): a genuinely independent broker or agent does not, but a person acting wholly or principally for the enterprise (or for it and enterprises under common control) is not independent. 5(6): a subsidiary is not by itself a PE of its parent. KNOWN
- **Counting days for (j)** is not defined in the treaty. INFERRED aid: the OECD's comparable alternative services-PE provision counts, at enterprise level, the days on which services are actually being performed in the State through at least one individual, and each day counts once however many people work that day (Commentary on Art 5, paras 160 and 163); "connected projects" means projects with commercial coherence (para 162). The days are normally working days, not all days of presence. The Indonesian text is not identical to the OECD alternative provision, so treat this as an aid, not settled. [S17] INFERRED / OPEN

### 4.4 Business profits and associated enterprises, Arts 7 and 9

- Art 7(1): business profits of an enterprise are taxable only in its State unless it carries on business in the other State through a PE, in which case that State may tax the profits attributable to the PE, plus profits from sales of the same or similar goods and from business activities of the same or similar kind in that State (limited "force of attraction", 7(1)(b) and (c)). 7(2) and (3): arm's length attribution, deduction of expenses incurred for the PE wherever incurred, but no deduction or income recognition for royalties, fees or commissions between the PE and head office, other than reimbursement of actual expenses (interest only for banks). 7(4): no profit for mere purchasing. 7(5): domestic estimation laws apply where information is inadequate. 7(6): items dealt with in other Articles keep their own treatment. 7(8): resident beneficiary of a trust carrying on business through a trustee PE. [S1, S3] KNOWN
- Art 9: re-allocation of profits between associated enterprises at arm's length, and the other State gives a correlative adjustment if it agrees the first adjustment is justified (9(3)). Transfer pricing itself is out of scope (GOAL); an Adelaide entity charging an Indonesian company (or the reverse) is an escalation trigger. [S1, S3]
- Individuals: an individual carrying on a professional or independent activity is Art 14, not Art 7. A company, partnership or trustee carrying on the same activity is Art 7 and Art 5. Where a sole trader uses employees or subcontractors in Indonesia, Art 5(2)(j) is at least arguable. Classifying software development, IT consulting or digital marketing as "professional services or other independent activities of a similar character" (Art 14(2)) is a judgement, not settled by the text. INFERRED / OPEN

### 4.5 Personal services, Arts 14 to 21

| Art | Rule | Trap |
|---|---|---|
| 14(1) | Income of an individual resident of one State from professional or other independent services is taxable only there **unless** (a) a fixed base is regularly available in the other State for the activities (then income attributable to that base may be taxed there, with no day count), or (b) the individual is present in the other State for periods exceeding 120 days in any 12 months (then income derived from activities there may be taxed there) | Fixed base needs no days at all. A regularly available desk, co-working membership or home office in Bali is a fixed-base question. INFERRED: escalate. Presence counts all days (holidays included) on the physical-presence reading |
| 14(2) | "Professional services" includes independent scientific, literary, artistic, educational or teaching activities and doctors, lawyers, engineers, architects, dentists and accountants | List is inclusive, not exhaustive |
| 15(1) | Remuneration of a resident employee is taxable only in the residence State unless the employment is exercised in the other State, which may then tax remuneration derived from that exercise. Subject to Arts 16, 18, 19, 20 | Art 17 (entertainers) overrides Arts 14 and 15 |
| 15(2) | Exempt in the work State only if **all** hold: (a) presence not exceeding 120 days in aggregate in any 12 months; (b) paid by or for an employer who is not a resident of the work State; (c) not deductible in a PE or fixed base the employer has in the work State; (d) the remuneration is or will be subject to tax in the residence State | If any fails, Art 15(1) applies to the remuneration for the Indonesian work. Employer resident in Indonesia (a PT) fails (b) even for a few days |
| 15(3) | Ship or aircraft in international traffic: the operator's State may tax | none |
| 16 | Directors' fees and similar payments from a company resident in the other State may be taxed there | No days, no fixed base. Applies to a member of the board or any similar organ; whether an Indonesian commissioner counts is INFERRED yes; escalate |
| 17 | Entertainers and athletes: performance State may tax, including where the income goes to another person | none |
| 18 | Pensions and annuities: residence State only, but the source State may tax up to a cap; alimony taxable only in the payer's State | Indonesia's reason (pension contributions untaxed on the way in) is in the EM |
| 19 | Government service: paying State only, unless local resident national | none |
| 20 | Visiting professor or teacher, within a limit of years: exempt in the visited State to the extent taxed at home | EM: this takes the pay outside the old s 23AG exemption, so it stays taxable in Australia |
| 21 | Student: payments from abroad for maintenance or education exempt in the host State | Local part-time work is Art 15 |

**Day counting (Arts 14(1)(b) and 15(2)(a)).** The treaty does not define a day. INFERRED aid: the OECD Commentary on Art 15 para 5 uses "days of physical presence": part of a day, arrival and departure days, weekends, holidays, short breaks and sick days in the work State all count; days spent in transit between two points outside the work State and whole days outside the State do not. Para 5.1: days when the person was already resident of the work State are not counted. [S17, S16 for the ATO's stance that the Commentaries inform DTA interpretation] The 12-month window is any period of 12 months, tested on a rolling basis, not the income year (Art 15(2)(a) and 14(1)(b) both say "any period of 12 months"). KNOWN.

### 4.6 Withholding, Arts 10 to 12 (source-State caps)

| Art | Cap | Notes |
|---|---|---|
| 10(2) dividends | 15% of gross | One rate: no separate rate for company shareholders. Not applied where the holding is effectively connected with a PE or fixed base in the source State (10(4)); then Art 7 or 14 apply. 10(5): no extraterritorial tax on dividends of a company resident of the other State paid to third-country residents. 10(6): additional tax on PE profits of a company, capped at 15% of profits after the source State's tax (proposed key). 10(7): Indonesian oil and gas production sharing carve-out |
| 11(2) interest | 10% of gross | "Interest" includes government securities, bonds, debentures and other debt claims (11(3)). PE and fixed base exception (11(4)). Source rule: payer's residence or, if the debt is borne by a PE, where the PE is (11(5)). Special relationship: only the arm's length amount gets the cap (11(6)). Central bank reserve interest exempt (11(7)) |
| 12(2)(a) royalties | 10% of gross | Royalties for industrial, commercial or scientific **equipment** (3(b)), supply of scientific, technical, industrial or commercial **knowledge** (3(c)), and, to the extent related, ancillary assistance (3(d)) and forbearance (3(f)) |
| 12(2)(b) royalties | 15% of gross | Everything else: copyright, patents, designs, trademarks, secret processes (3(a)), films and tapes for television and radio (3(e)). EM: natural resource royalties are Art 6 real property income and are not capped |

Common: the caps limit the tax "according to the law of" the source State; they do not create a rate. The competent authorities settle the mode of application (10(2), 11(2), 12(2)). MLI PPT (Art 7) can deny a cap where obtaining it was a principal purpose of an arrangement. [S1, S3] KNOWN. Software licences: whether a payment is a royalty under Art 12(3) is a characterisation question; escalate, do not compute.

### 4.7 Property, Arts 6 and 13, and other income, Arts 22 and 23

- Art 6: income from real property, including direct use, letting and any other use, may be taxed where the property is, even without a PE or fixed base (6(4), 6(5), EM). "Real property" has the local law meaning and includes leases of land, interests in or over land, and rights to payments for exploiting natural resources; ships, boats and aircraft are not real property. So Bali villa rent is taxable in Indonesia; an Australian resident is taxed on it here as well, with FITO. [S1, S3] KNOWN
- Art 13(1): gains from alienating real property in the other State may be taxed there. 13(2): gains on business property of a PE or fixed base. 13(3): ships and aircraft. **13(4)**: gains on shares or comparable interests in a company whose assets are wholly or principally real property in the other State may be taxed there; MLI Art 9 tests the threshold at any time in the previous 365 days and extends the paragraph to partnership and trust interests. **13(5)**: nothing affects domestic law on capital gains from any other property, for either State. [S1, S3] KNOWN
- Consequence: the OECD's residence-only rule for share gains is **not** in this treaty. A gain on shares in an Indonesian company that is not land-rich can be taxed by Indonesia under its domestic law with no treaty ceiling, and Australia taxes its resident on the gain as well (Div 770 relief, section 5.2). The EM says Art 13(5) exists precisely to let Australia's CGT rules apply. [S3 Art 13] KNOWN
- Art 22: income not covered elsewhere is taxable only in the residence State, but the source State may also tax income from sources in that State (22(2)), except income connected with a PE or fixed base (22(3)). Art 23: income a State may tax under Arts 6 to 8, 10 to 19 or 22 is deemed sourced there for Art 24 and each State's domestic law, so Indonesian-taxable income of an Australian resident is foreign-source for the credit rules. [S1, S3] KNOWN

### 4.8 Relief, mutual agreement, information, Arts 24 to 26

- Art 24(1): Indonesian tax paid under Indonesian law **and in accordance with the agreement** on Indonesian-source income of an Australian resident is credited against Australian tax on that income, subject to Australian credit law (which cannot defeat the general principle). Australia applies this through its general foreign tax credit rules, now ITAA 1997 Div 770. 24(2): an Australian company holding directly or indirectly at least 10% of the votes of an Indonesian company gets the credit extended to underlying tax on the profits behind a dividend. 24(3) and (4): Indonesia credits Australian tax, with Australian FBT paid by an Indonesian resident added first. [S1, S3] KNOWN
- EM notes: relief for "exemption with progression" applied to foreign service under the old s 23AG. That section is now narrower (existing overlay note on `residency.s23ag_min_foreign_service_days`); do not assume exemption for ordinary employment in Bali. The EM also said Indonesia was a "comparable tax" country for the then accruals measures; the current CFC "listed country" list has seven countries and Indonesia is not one (section 6). [S3, S15] KNOWN
- Art 25: a resident who considers taxation is contrary to the agreement may present a case to their own competent authority within 3 years of first notification of the action; solutions are implemented despite domestic time limits; MLI Art 16(3) adds a general consultation power. Art 26: information exchange limited to what the agreement and domestic laws need. [S1, S3] KNOWN

---

## 5. Australian domestic interaction

### 5.1 Resident with Indonesian income: what Australia does

- A resident's assessable income includes ordinary income from all sources in or out of Australia (ITAA 1997 s 6-5(2)); a foreign resident's includes Australian-source ordinary income (s 6-5(3)). [S19] KNOWN
- Capital gains: a CGT event is needed (s 102-20). A resident individual's foreign assets (a Bali villa, shares in a PT) are CGT assets; the discount and loss mechanics belong to the `cgt` skill. [S19] KNOWN
- Return: foreign income goes to question 20 of the supplementary return. For 2025-26 the ATO instructions say: convert everything to AUD; add back foreign tax withheld to get gross rent; foreign rental **debt deductions (interest, borrowing costs) are excluded from the foreign rent worksheet** unless attributable to an overseas PE and are claimed at D15 instead; net foreign rent goes to label R; assessable foreign source income to label E; answer label P Yes if overseas assets were worth A$50,000 or more at any time in 2025-26. Labels change by year and must be re-read each year. [S13] KNOWN (2025-26 only)
- The ATO's certificate of residency, or certification of the Indonesian relief form, is what an Australian resident gives Indonesia's payer to claim treaty rates; how to apply for the reduction is the source country's procedure (ATO treaty page). [S14] KNOWN

### 5.2 FITO (ITAA 1997 Div 770)

1. **Entitlement** (s 770-10(1)): a tax offset for foreign income tax paid on an amount included in assessable income for the year. It belongs to the year the income was included, even if the tax was paid in another year. NANE income does not qualify (except s 23AI and 23AK amounts). [S7, S8]
2. **What counts** (s 770-15(1)): a tax on income, profits or gains, or another tax within a treaty; only tax **correctly imposed** under the foreign law and, where there is a treaty, in accordance with the treaty. The ATO's own example: a 10% treaty cap and a 25% domestic rate means only 10% counts and the balance must be sought as a refund from the foreign authority. [S7, S8] KNOWN
3. **Paid or deemed paid**: withholding by a payer counts as paid by the taxpayer. Tax refundable to the taxpayer does not count. Penalties, fines and interest are not foreign income tax; Art 3(1)(g) also excludes penalty and interest from "tax" and the EM says so for the Art 24 credit. [S8, S1, S3] KNOWN
4. **Gross-up**: include the gross foreign amount (before withholding) in assessable income. [S8] KNOWN
5. **Part of an amount / discounted gains / losses**: only the share of foreign tax that matches the assessable part counts. A discounted foreign capital gain means the foreign tax is apportioned; a net capital gain of nil means no offset (loss ordering can be chosen to keep foreign-taxed gains in the net). [S8] KNOWN
6. **NANE dividends** (s 768-5: an Australian corporate tax entity with the participation interest): the dividend is not assessable, so Indonesian withholding on it earns no FITO, whatever Art 24(2) says. [S19, S8 Example 13] KNOWN
7. **Limit** (s 770-75): the greater of A$1,000 (existing key `residency.fito_default_offset_limit`) and (tax payable with the foreign income) minus (tax payable with the s 770-75(4) assumptions), both disregarding offsets. Assumptions: leave out the foreign-taxed amounts and other non-Australian-source income; ignore deductions reasonably related to them, but **debt deductions are ignored only if attributable to an overseas PE**. Tax payable includes Medicare levy and surcharge. If the total claim is A$1,000 or less no calculation is needed. [S7, S8] KNOWN
8. **Order and refunds**: FITO is a non-refundable offset applied after the other non-refundable offsets; excess is not refunded or carried forward. [S8] KNOWN
9. **Timing**: if foreign tax is paid after the year the income was included, amend that year; the ATO guide allows 4 years from paying the tax (also for later increases or refunds). Statute for this special period not read. [S8] KNOWN (guide) / OPEN (section)
10. Special cases already refused by the repo's tool (AU-RES-005): deferred non-commercial business losses, foreign loss component, attribution account payments, JPDA income, foreign tax in another year, refunds. [repo] KNOWN

### 5.3 Foreign-resident withholding (Australia paying an Indonesian resident) and related

| Payment | Domestic rate | Treaty cap | Result for an Indonesian resident (beneficially entitled) |
|---|---|---|---|
| Unfranked dividend | 30% (1974 Act s 7(a); s 128B(4) ITAA 1936) | 15% | 15% (ITAA 1953 s 17A(1) reduces the liability). Withhold only on the unfranked part |
| Franked dividend | Nil under domestic law (EM) | 15% | Nil |
| Interest | 10% (s 7(b)) | 10% | 10%, no reduction |
| Royalty | 30% (s 7(c)) | 10% (equipment, know-how) or 15% (other) | 10% or 15% |

- The reduced treaty rate applies only where the payee is a resident of the treaty country **and** beneficially entitled; where the payment is effectively connected with the payee's Australian PE, the payer need not withhold on royalties and dividends and the amount is assessed instead. The ATO tells a foreign resident payee to give the Australian payer a current overseas address so the right rate is withheld; the payer may otherwise withhold at a higher default rate. [S12] KNOWN
- Indonesian resident working in Australia: Art 15 still allocates the remuneration; the exemption needs all four conditions. Australian PAYG uses the foreign resident scale (existing key `individual.foreign_resident_rates`) unless the person is an Australian resident under domestic law. Foreign resident capital gains withholding (FRCGW) applies to Australian real property sales by foreign residents at the existing key `cgt.frcgw_rate`; not re-read here. [repo, S1]
- Indonesian resident selling Australian real property, or shares that are land-rich in Australian real property: Art 13(1) and 13(4) let Australia tax; ITAA 1953 s 3A and the MLI Art 9 interplay is OPEN (section 3).

### 5.4 FX translation

- ITAA 1997 s 960-50(6) table (current, read in the ATO legal database): item 5, a transaction or event relevant to CGT (Parts 3-1 or 3-3), is translated at the rate applicable **at the time of the transaction or event**, so each cost-base element uses its own date; item 6, ordinary income, at the rate at receipt if received at or before derivation, otherwise at derivation; item 7, statutory income (other than Div 102 gains), same idea on the first time inclusion arose; item 8, deductions, at payment if paid at or before the time deductible, otherwise when deductible; item 11 (a receipt or payment not covered above) at the time of the receipt or payment. s 960-50(7): regulations can modify (reg 960-50.01 supplies the average-rate alternative; instrument name not read). [S9] KNOWN
- ATO administrative position: an average rate over a period of up to 12 months chosen by the taxpayer is acceptable only if it reasonably approximates spot rates at the specific translation times; a rate from an associate or from yourself is not acceptable. For foreign income derived overseas the ATO allows spot or an appropriate average, and **not** an end-of-year rate where the income was not received in Australia in the same year it was derived. Regular foreign rent is a proper case for an average; a one-off sale of a large capital asset is not (ATO examples 6 and 7). [S10] KNOWN
- Foreign tax paid: INFERRED that item 11 (payment) translates foreign tax at the time paid; the ATO's functional currency guide says FITO foreign tax is translated when the tax is paid. https://www.ato.gov.au/businesses-and-organisations/corporate-tax-measures-and-assurance/foreign-exchange-gains-and-losses/in-detail/guide-to-functional-currency-rules
- **The ATO publishes rupiah rates.** Rupiah per A$1: average year ended 30 Jun 2026 = 11,446.3586; average year ended 31 Dec 2025 = 10,621.7928; nearest actual rate 30 Jun 2026 = 12,298.0000; nearest actual 31 Dec 2025 = 11,174.0000 (published 13 Jul 2026, from the RBA). Monthly averages: Jul 2025 10,657.6522; Aug 10,578.6500; Sep 10,890.5000; Oct 10,866.9091; Nov 10,868.7000; Dec 11,084.4762; Jan 2026 11,410.4000; Feb 11,870.4500; Mar 11,896.7727; Apr 12,167.7895; May 12,620.3810; Jun 12,569.7143; and for 2026-27, Jul 2026 12,543.4348, Aug 2026 12,653.3000, Sep 2026 not yet published (page updated 9 Sep 2026). Check: the quote-weighted mean of the twelve 2025-26 monthly averages is 11,446.3586 to four places, matching the annual figure. Where the ATO does not publish a currency or year, it accepts a rate from an Australian bank (including the bank receiving the income) or another reliable external source, with the rate and source kept. [S11] KNOWN
- Daily rates come from the RBA (ATO points there). A one-off event needs the actual day's rate, which is not in the ATO tables unless the day is 30 Jun or 31 Dec.

### 5.5 Bali income, one line each (Australian resident unless stated)

| Income | Indonesia may tax? | Australia | Escalate when |
|---|---|---|---|
| Rent from a villa held personally | Yes, Art 6, no cap | Assessable, gross rent, FITO if Indonesia taxed it correctly; interest is a debt deduction (D15, not disregarded at FITO step 2) | Short-stay operator structure, PT owns the villa, private use apportionment (rental and short-stay skills) |
| Dividend from a PT held personally | Yes, up to the cap (Indonesian domestic rate not verified) | Assessable, unfranked, gross-up, FITO on the capped tax | PT controlled by the taxpayer (CFC), franking or NANE questions |
| Dividend from a PT held by an Australian company with the participation interest | Yes, up to the cap | NANE, no FITO (s 768-5) | Any corporate structure |
| Interest from an Indonesian bank | Yes, up to the cap | Assessable, FITO on the capped tax | Loans between related parties (Art 11(6)) |
| Employment income, Australian employer | Only if Art 15(2) fails | Assessable; relief via FITO if Indonesia taxes | Employer PE in Indonesia, PT as employer |
| Employment income, Indonesian employer (PT) | Yes from day 1 (Art 15(2)(b) fails) | Assessable, FITO | Tie-breaker, s 23AG claims |
| Consulting as a sole trader | If fixed base or presence over the limit | Assessable, FITO | Fixed base, services through employees (Art 5(2)(j)) |
| Director or commissioner fees from a PT | Yes (Art 16) | Assessable, FITO | Executive services alongside |
| Sale of villa | Yes (Art 13(1)) | CGT, foreign-currency asymmetry (E8), FITO only on the assessable share (E9) | Land-rich PT share sale (Art 13(4)), main residence claims |
| Sale of PT shares (not land-rich) | Domestic law, no ceiling (Art 13(5)) | CGT | Any |

---

## 6. Escalation triggers

### Australian-side triggers (route: registered tax agent or international tax adviser)

| Trigger | Why | Existing code |
|---|---|---|
| Australian resident controls an Indonesian PT or PT PMA (meets one of the CFC control tests) | Part X CFC. Indonesia is an **unlisted** country (the seven listed countries are Canada, France, Germany, Japan, New Zealand, the UK and the US). A PT holding a villa or other passive income fails the active income test. Attribution happens whether or not cash is paid. [S15] | AU-RES-002 |
| Foreign trust, s 99B, transferor trust | Part X and trust rules | AU-RES-002 |
| Foreign super or pension balances or transfers | Div 305, Art 18 | AU-RES-003 |
| Dual resident with conflicting facts, or needing a treaty determination | Art 4(3) for individuals, with an ATO early engagement request for a certificate of residency; a company uses an MLI Art 4(1) competent authority request [S14] | AU-RES-001, AU-RES-004 |
| Dual-resident company, for example an Australian company managed from Bali | MLI Art 4: no relief without competent authority agreement [S1] | AU-RES-001 |
| Service PE screen near or over the days limit; employees or subcontractors working in Bali; dependent agent facts; fixed base in Bali | Art 5(2)(j), 5(4), Art 14(1)(a). Counting method not settled by the text [S1, S17] | new |
| Indonesian company as employer; Australian employer with an Indonesian PE | Art 15(2)(b) and (c) fail | new |
| Land-rich PT share sale; villa held through a PT; indirect Australian land interests of an Indonesian resident | Art 13(4), MLI Art 9, ITAA 1953 s 3A | new |
| FITO special cases, tax paid in another year, refunds | Existing calculator scope [repo] | AU-RES-005 |
| Related-party charges between an Australian entity and an Indonesian PT (fees, loans, royalties) | Art 9, 11(6), 12(6), transfer pricing out of scope | new |
| Trusts or partnerships with Indonesian income | Art 1, 3(1)(d), 7(8) unclear | new |
| Software or licence payments where royalty status is unclear | Art 12(3) characterisation | new |
| Treaty benefit denial concerns (interposed entities) | MLI PPT | new |
| A needed rate or figure unpublished or unverified | | AU-GEN-001, AU-GEN-003 |

### Indonesian domestic triggers (NOT VERIFIED here; say so, route to an Indonesian adviser)

- Whether the person or a company is an Indonesian **domestic** resident (the treaty's Art 4(1) input). DJP regulation PER-43/PJ/2011 states individuals are domestic residents if they live in Indonesia, are present more than 183 days in any 12 months, or are present in a tax year and intend to reside (work visa, temporary stay permit, contract over 183 days are treated as evidence of intent); part of a day counts as a full day for the 183-day count. Regulation currency not checked. [S18] SOURCE-CITED, NOT VERIFIED
- Indonesian withholding rates under domestic law, any withholding on treaty payments, VAT on villa rentals, final tax on rent, land and building taxes, transfer duties, PT PMA licensing and ownership rules, treaty-benefit documentation for the Indonesian payer, permits (KITAS or KITAP), tax registration, Indonesian penalties and refunds of over-withheld tax. None of this is verified in this repo.
- Indonesian tax paid in rupiah must be evidenced (withholding slips, assessment); the skill can ask for them but cannot judge Indonesian correctness.

Suggested new codes (builder to define in `data/refusals/au_indonesia.yaml`): PE or fixed base determination; Indonesian domestic tax question; PT or structure question; dual-resident company; land-rich or indirect property gains; unresolved day-count or fixed-base facts; treaty benefit documentation.

---

## 7. Proposed overlay keys

Create `data/rates/<year>.d/au_indonesia.yaml` (new domain `au_indonesia`) for 2025-26, 2026-27 and 2027-28. Do **not** edit `residency.yaml` (owned by another skill; avoids merge conflicts).

**Existing keys, do not duplicate** (in `residency.yaml`, both years): `residency.indonesia_dta_days_threshold` (Arts 14 and 15), `residency.indonesia_dta_wht_dividends`, `residency.indonesia_dta_wht_interest`, `residency.indonesia_dta_wht_royalties_equipment_know_how`, `residency.indonesia_dta_wht_royalties_other`, `residency.fito_default_offset_limit`, `residency.s23ag_min_foreign_service_days`. Also existing: `cgt.frcgw_rate`, `cgt.discount_individual_trust`, `individual.foreign_resident_rates`, `individual.resident_rates`, the `medicare.*` group.

Tested: the block below (2025-26 version) passed `uv run scripts/validate_rates.py` (0 errors, 17 figures) and `lint_skills.py` (0 problems) when placed temporarily in `data/rates/2025-26.d/`, then removed. Lint warning for the builder: with keys of unit `days` valued 120, 30 and 365 present, SKILL.md and references prose may not contain "120 days", "30 days" or "365 days" (write "the treaty days limit" or name the key). Do not add a key valued 183 days (the existing skills write about the 183-day residency test). The validator rejects any field other than value, unit, status, source, as_at and notes, so a `checked_at` date must go in `notes` (the brief for this task asks for `checked_at`; the schema does not allow it).

```yaml
au_indonesia:
  # ---- treaty constants (identical every income year) ----
  dta_pe_resource_installation_days:   # Art 5(2)(h)
    value: 120
    unit: days
    status: VERIFIED
    source: https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf
    as_at: 2026-09-29
    notes: 'Installation, rig or ship for natural resources: PE where use continues for more than this many days. Tabled 1992 text agrees.'
  dta_pe_building_site_days:           # Art 5(2)(i)
    value: 120
    unit: days
    status: VERIFIED
    source: https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf
    as_at: 2026-09-29
    notes: 'Building site, construction, installation or assembly project, or supervisory activities: more than this many days. MLI Art 14 splitting-up applies to the count. Tabled 1992 text agrees.'
  dta_pe_services_days:                # Art 5(2)(j)
    value: 120
    unit: days
    status: VERIFIED
    source: https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf
    as_at: 2026-09-29
    notes: 'Services furnished through employees or other personnel, same or connected project, periods aggregating more than this many days within any 12 month period. No fixed place needed. Day-count method not defined in the treaty (see brief section 4.3). Tabled 1992 text agrees.'
  dta_wht_pensions_annuities:          # Art 18(2)
    value: 0.15
    unit: rate
    status: VERIFIED
    source: https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf
    as_at: 2026-09-29
    notes: 'Source-State tax on a pension or annuity paid to a resident of the other State may not exceed this share of the gross amount. Tabled 1992 text agrees.'
  dta_branch_profits_additional_tax_cap:   # Art 10(6)
    value: 0.15
    unit: rate
    status: VERIFIED
    source: https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf
    as_at: 2026-09-29
    notes: 'Additional tax on profits of a PE of a company resident in the other State: not more than this share of profits after the source State tax on them. Art 10(7) carves out Indonesian oil and gas production sharing contracts.'
  dta_underlying_tax_credit_min_voting_share:   # Art 24(2)
    value: 0.10
    unit: rate
    status: VERIFIED
    source: https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf
    as_at: 2026-09-29
    notes: 'Australian company holding not less than this share of the voting power of an Indonesian company: credit extends to underlying tax. ITAA 1997 s 768-5 can make the dividend non-assessable non-exempt, so no credit arises (ATO FITO guide Example 13).'
  dta_teacher_visit_max_years:         # Art 20(1)
    value: 2
    unit: years
    status: VERIFIED
    source: https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf
    as_at: 2026-09-29
    notes: 'Visiting professor or teacher for a period not exceeding this many years: remuneration exempt in the visited State to the extent taxed at home.'
  dta_map_case_presentation_years:     # Art 25(1)
    value: 3
    unit: years
    status: VERIFIED
    source: https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf
    as_at: 2026-09-29
    notes: 'Mutual agreement case must be presented within this many years of the first notification of the action; the solution is implemented despite domestic time limits (Art 25(2)).'
  mli_splitting_up_min_activity_days:  # MLI Art 14(1) on Art 5(2)(i)
    value: 30
    unit: days
    status: SOURCE-CITED
    source: https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf
    as_at: 2026-09-29
    notes: 'Activities at a building site above this many days, and connected activities by closely related enterprises each above this many days, are added together. Read only in the ATO synthesised text (not a source of law); authentic MLI text [2019] ATS 1 not separately read.'
  mli_land_rich_lookback_days:         # MLI Art 9 on Art 13(4)
    value: 365
    unit: days
    status: SOURCE-CITED
    source: https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf
    as_at: 2026-09-29
    notes: 'Land-rich value threshold tested at any time in this many days before the alienation; extends to comparable interests (partnership, trust). ATO synthesised text only.'
  mli_closely_related_control_share:   # MLI Art 15(1)
    value: 0.5
    unit: rate
    status: SOURCE-CITED
    source: https://www.ato.gov.au/law/view/pdf/mli/indonesia_c1.pdf
    as_at: 2026-09-29
    notes: 'Closely related where one holds more than this share of the beneficial interest (for a company, of aggregate vote and value) in the other. ATO synthesised text only.'
  # ---- Australian domestic withholding constants used with Arts 10 to 12 ----
  au_wht_unfranked_dividend_rate:
    value: 0.30
    unit: rate
    status: VERIFIED
    source: https://classic.austlii.edu.au/au/legis/cth/consol_act/itiarwta1974590/s7.html
    as_at: 2026-09-29
    notes: 'Income Tax (Dividends, Interest and Royalties Withholding Tax) Act 1974 s 7(a). Also on the ATO withholding rate page. Reduced to the Art 10(2) cap for Indonesian residents by ITAA 1953 s 17A(1).'
  au_wht_interest_rate:
    value: 0.10
    unit: rate
    status: VERIFIED
    source: https://classic.austlii.edu.au/au/legis/cth/consol_act/itiarwta1974590/s7.html
    as_at: 2026-09-29
    notes: '1974 Act s 7(b). Equal to the Art 11(2) cap, so no treaty reduction.'
  au_wht_royalty_rate:
    value: 0.30
    unit: rate
    status: VERIFIED
    source: https://classic.austlii.edu.au/au/legis/cth/consol_act/itiarwta1974590/s7.html
    as_at: 2026-09-29
    notes: '1974 Act s 7(c). Reduced by Art 12(2) to the two royalty caps held in residency.'
  # ---- year-specific: 2025-26 values shown; see below for 2026-27 and 2027-28 ----
  foreign_assets_reporting_threshold:
    value: 50000
    unit: AUD
    status: VERIFIED
    source: https://www.ato.gov.au/forms-and-instructions/individual-supplementary-tax-return-2026-instructions/income-questions-13-24-supplementary-tax-return-2026/20-foreign-source-income-and-foreign-assets-or-property-2026
    as_at: 2026-09-29
    notes: 'Supplementary return 2026 question 20 label P: Yes if overseas assets were worth this amount or more at any time in 2025-26. A form threshold, re-read each year.'
  fx_idr_per_aud_average_year_to_30_jun:
    value: 11446.3586
    unit: IDR per AUD
    status: VERIFIED
    source: https://www.ato.gov.au/tax-rates-and-codes/foreign-exchange-rates-annual-2026-financial-year
    as_at: 2026-09-29
    notes: 'ATO annual table, Indonesia (Rupiah), average for the year ended 30 Jun 2026 (published 13 Jul 2026, RBA rates). For spread-out income and deductions only; a one-off capital event uses the rate at the event (ITAA 1997 s 960-50(6) item 5).'
  fx_idr_per_aud_nearest_actual_30_jun:
    value: 12298.0
    unit: IDR per AUD
    status: VERIFIED
    source: https://www.ato.gov.au/tax-rates-and-codes/foreign-exchange-rates-annual-2026-financial-year
    as_at: 2026-09-29
    notes: 'ATO annual table, Indonesia, nearest actual rate to 30 Jun 2026. Right only for a transaction on that date.'
```

**2026-27 and 2027-28 year-specific keys** (never index forward; use these SUSPECT/null entries, `as_at: 2026-09-29`):

```yaml
  foreign_assets_reporting_threshold:
    value: null
    unit: AUD
    status: SUSPECT
    source: https://www.ato.gov.au/forms-and-instructions/individual-supplementary-tax-return-2026-instructions/income-questions-13-24-supplementary-tax-return-2026/20-foreign-source-income-and-foreign-assets-or-property-2026
    as_at: 2026-09-29
    notes: 'Checked 2026-09-29 at the URL: only the 2025-26 instructions are published. The 2026-27 return instructions are not out. Do not carry forward.'
  fx_idr_per_aud_average_year_to_30_jun:
    value: null
    unit: IDR per AUD
    status: SUSPECT
    source: https://www.ato.gov.au/tax-rates-and-codes/foreign-exchange-rates-monthly-2027-financial-year
    as_at: 2026-09-29
    notes: 'Checked 2026-09-29: year to 30 Jun 2027 not yet published. Only monthly averages Jul 2026 (12543.4348) and Aug 2026 (12653.3000) exist (page updated 9 Sep 2026). Do not average or extrapolate.'
  fx_idr_per_aud_nearest_actual_30_jun:
    value: null
    unit: IDR per AUD
    status: SUSPECT
    source: https://www.ato.gov.au/tax-rates-and-codes/foreign-exchange-rates-monthly-2027-financial-year
    as_at: 2026-09-29
    notes: 'Checked 2026-09-29: 30 Jun 2027 has not happened. Needs the ATO annual table for the year ending 30 Jun 2027 (published after that date).'
```

Optional: the monthly table above can be a dated series (`from`, `to`, `rate`) if the builder wants a monthly tool; the annual keys are enough for the numeric evals here.

---

## 8. Worked examples (all hand-computed; a tool run afterwards agreed with E1 and E2)

Rates used: 2025-26 resident scale (18,200 to 45,000 at 16%; 45,000 to 135,000 at 30% on a base of 4,288) and Medicare levy at 2% (taxpayers above the single upper threshold pay it in full, so no shade-in); 2026-27 scale (15% band; 30% band on a base of 4,020). Both from the base rates files. Cross-check from the ATO's own worked example (S8 Example 17): tax plus levy on 80,000 is 16,388 and on 60,000 is 9,988, which my steps reproduce.

### E1. Indonesian dividend, treaty cap, limit not binding (2025-26)
Facts: single, hospital cover, taxable income A$120,000 including a gross A$25,000 dividend from an Indonesian company (held personally). Indonesia withheld 20% (A$5,000). The 20% is assumed for the illustration; the Indonesian domestic rate is not verified here. No related deductions.
1. Cap: 15% of 25,000 = 3,750 counts. The other 1,250 was not correctly imposed under the treaty: seek a refund from Indonesia; it is not FITO.
2. Assessable income includes the gross 25,000 (gross-up).
3. Claim 3,750 is above the default limit of 1,000, so compute the limit.
4. Step 1: 4,288 + 0.30 x (120,000 - 45,000) = 4,288 + 22,500 = 26,788; levy 2,400; total 29,188.
5. Step 2 (taxable income 95,000): 4,288 + 0.30 x 50,000 = 19,288; levy 1,900; total 21,188.
6. Limit = 29,188 - 21,188 = 8,000 (32% x 25,000).
7. Offset = the lesser of 3,750 and 8,000 = **3,750**. No LITO at this income, so tax payable after FITO = 29,188 - 3,750 = **25,438**.
8. Extra Australian tax caused by the dividend = 8,000; after the credit Australia keeps 4,250. If the excess 1,250 is never recovered from Indonesia the total burden is 5,000 + 4,250 = 9,250.
2026-27 variant: step 1 = 4,020 + 22,500 = 26,520 + 2,400 = 28,920; step 2 = 4,020 + 15,000 = 19,020 + 1,900 = 20,920; limit 8,000; offset 3,750; tax after FITO 25,170. (The existing eval `num-indonesia-dividend-treaty-cap-credit` covers 100,000 with 8,000; do not duplicate its numbers.)

### E2. Limit binds; interest is not disregarded (2025-26)
Facts: single, hospital cover, taxable income A$60,000 including net Bali villa rent of A$12,000 (gross 20,000 less non-debt deductions 8,000). Indonesian tax paid on the rent A$4,000 (assumed, treated as correctly imposed).
1. Step 1 (60,000): 8,788 + levy 1,200 = 9,988.
2. Step 2 (60,000 - 12,000 = 48,000): 4,288 + 0.30 x 3,000 = 5,188 + levy 960 = 6,148.
3. Limit = 9,988 - 6,148 = 3,840. Offset = lesser of 4,000 and 3,840 = **3,840**; **160 is lost** (no refund, no carry-forward).
4. LITO at 60,000 = 325 - 0.015 x 15,000 = 100, applied first: tax after LITO 9,888; after FITO 6,048.
Variant with A$3,000 villa loan interest (debt deduction, not attributable to an overseas PE; claimed at D15, not in the foreign rent worksheet): taxable income becomes 57,000. Correct step 2 removes only the 12,000 net rent: 45,000 gives 4,288 + levy 900 = 5,188; step 1 (57,000) = 4,288 + 0.30 x 12,000 = 7,888 + 1,140 = 9,028; limit **3,840**. Wrongly disregarding the interest too would give a step 2 base of 48,000 (6,148) and a wrong limit of 2,880.

### E3. Interest and royalties, then the combined default limit (2025-26)
1. Interest gross A$4,000 from an Indonesian bank; Indonesia withheld 20% = 800 (assumed). Cap 10% = 400 counts.
2. Royalty gross A$5,000 for book copyright (Art 12(3)(a), 15% tier): 750 counts. If instead the A$5,000 was for supplying know-how (Art 12(3)(c), 10% tier): 500.
3. Each alone is under 1,000, but the **total** counting is 400 + 750 = 1,150, above the default limit, so the limit must be computed. Assume taxable income 80,000 including the 9,000 gross: step 1 = 16,388; step 2 (71,000) = 4,288 + 0.30 x 26,000 = 12,088 + levy 1,420 = 13,508; limit = 2,880. Offset = **1,150** (limit not binding).

### E4. Art 15: 12-month window across income years
Facts: Australian resident employed and paid by an Adelaide company; no Indonesian PE; remuneration taxed in Australia. Physical presence in Indonesia: 1 Apr 2026 to 30 Jun 2026 inclusive, then 1 Jul 2026 to 15 Aug 2026 inclusive.
1. Trip A: April 30 + May 31 + June 30 = 91 days (all in 2025-26). Trip B: July 31 + August 15 = 46 days (all in 2026-27).
2. Each income year alone is under 120 (91; 46), which is the wrong test.
3. Window 16 Aug 2025 to 15 Aug 2026 (12 months) contains both trips: 91 + 46 = **137** days, above 120. (Checked by scanning every window: 137 is the maximum.)
4. Condition (a) fails, so Art 15(1) applies: Indonesia may tax the remuneration for the work done in Indonesia (not only 17 excess days). Australia still taxes it; relief through FITO if Indonesia taxes it correctly.
Contrast: 118 days in 12 months but paid by an Indonesian company: fails (b), taxable in Indonesia from day 1.

### E5. Art 14 presence, and Art 5(2)(j) for a company
a. Sole-trader consultant, Australian resident: 100 working days plus 30 holiday days in Bali within 12 months. Presence 130 exceeds 120, so Art 14(1)(b) lets Indonesia tax income derived from the activities in Indonesia (the 100 working days' income), not her whole income. If she had a regularly available fixed base, Art 14(1)(a) would apply regardless of days.
b. Adelaide Pty Ltd sends A (1 Mar to 30 Apr 2026 = 31 + 30 = 61 days) and B (15 Mar to 15 May 2026 = 17 + 30 + 15 = 62 days) to the same Bali project, both working every day. Days on which at least one person furnishes services: 1 Mar to 15 May = 31 + 30 + 15 = **76**. Person-days would be 61 + 62 = 123. Under the OECD analogy (each day counts once, working days) the 76 is below 120 and no service PE arises from this; person-day counting would give 123 and a PE. The treaty text does not choose: OPEN, escalate, do not state a PE conclusion.

### E6. Australian withholding on payments to an Indonesian resident (beneficially entitled)
1. A$10,000 unfranked dividend: domestic 30% = 3,000; treaty cap 15% = 1,500; withhold **1,500**, net 8,500.
2. A$10,000 dividend 60% franked: unfranked part 4,000 x 15% = **600**; franked 6,000 nil; net 9,400.
3. A$10,000 interest: 10% = **1,000** (domestic equals cap).
4. A$10,000 royalty for know-how: domestic 3,000; cap 10% = **1,000**. For a trademark licence: 15% = **1,500**.
5. If the payee is a conduit or not beneficially entitled, the treaty rate is not available: domestic rates.

### E7. FX: average versus year-end (2025-26)
Facts: IDR 240,000,000 of villa rent received evenly over 2025-26 into an Indonesian account, not remitted.
1. ATO average for the year ended 30 Jun 2026: 240,000,000 / 11,446.3586 = **A$20,967.37**. Acceptable for regular rent (ATO example 6).
2. Year-end rate: 240,000,000 / 12,298.0000 = A$19,515.37. Not allowed for income not received in Australia in the year derived; it understates by A$1,452.00.
3. Indonesian tax on the rent is translated when paid, a different date from the income.

### E8. FX asymmetry on a villa sale (hypothetical purchase rate)
Facts: sold 30 Jun 2026 for IDR 3,600,000,000; bought years ago for IDR 3,000,000,000 when, for the illustration, A$1 = IDR 10,000 (assumed, not a published rate). No other cost-base elements.
1. Proceeds at the event date: 3,600,000,000 / 12,298 = A$292,730.53 (spot for that date, from the ATO's nearest-actual column).
2. Cost base at its own date: 3,000,000,000 / 10,000 = A$300,000.
3. Result: capital loss **A$7,269.47** although the rupiah gain is 20%. Any Indonesian tax on the rupiah gain earns no FITO if the Australian result is a loss or nets to nil (ATO guide Example 12). An average rate is inappropriate for this one-off asset.

### E9. Discounted foreign gain: apportioning foreign tax (2025-26)
Facts: resident individual sells a Bali villa held for more than 12 months; the Australian-dollar gain before discount is A$100,000 (all elements translated per E8); no other CGT items; Indonesia taxed the gain, tax A$8,000 (assumed, treated as correctly imposed); discount 50% (existing key `cgt.discount_individual_trust`).
1. Net capital gain in assessable income = 50,000.
2. Only the share of foreign tax matching the assessable amount counts: 8,000 x 50,000 / 100,000 = **4,000** (the ATO guide requires apportioning foreign tax on a discounted gain).
3. Taxable income 130,000 incl. the 50,000: step 1 = 4,288 + 0.30 x 85,000 = 29,788 + levy 2,600 = 32,388; step 2 (80,000) = 16,388; limit 16,000. Offset = lesser of 4,000 and 16,000 = **4,000**; the other 4,000 of Indonesian tax gets no Australian offset.

### E10. Tie-breaker walk-through (qualitative)
Facts: owns a home in Adelaide, where spouse and business are; a Bali villa let out to guests for most of the year, with the owner staying in it a few weeks each year; about 210 days in Adelaide and 155 in Bali; resident of Australia under the domestic tests; Indonesian domestic residence unclear.
1. Art 4(3) applies only if resident of both States under each State's law. Indonesian domestic residence is NOT VERIFIED: stop and escalate if unclear (AU-RES-001).
2. If it does apply: (a) Adelaide home is a permanent home; the let-out villa may not be "available" (Commentary para 13). If only Adelaide, the person is resident solely of Australia. If both, go to (b) habitual abode: both States can be habitual abodes (para 19); if both, go to (c) closer economic and personal relations (family, business, assets in Adelaide), which points to Australia. No nationality step.
3. Present the result as an indication only, and list the missing facts.

### E11. Directors' fees
An Australian resident is paid A$30,000 a year as a director of an Indonesian PT and visits for 10 days. Art 16 lets Indonesia tax the fees with no days test; Australia taxes them too (worldwide income); FITO subject to the limit.

---

## 9. Traps (each is an eval candidate; expected answer and source)

| # | Trap | Correct position | Source |
|---|---|---|---|
| T1 | "The 183-day rule means Indonesia cannot tax my salary" | Art 15 uses the days limit in `residency.indonesia_dta_days_threshold`, plus three other conditions | S1 |
| T2 | Testing the income year | Any 12-month window, rolling (E4) | S1 |
| T3 | Only working days count | Presence: all days present, part days, weekends; transit and whole days away do not; days already resident of Indonesia not counted | S17 |
| T4 | Employer is a PT, "only 60 days" | Art 15(2)(b) fails; Indonesia may tax from day 1 | S1 |
| T5 | Exemption is "the excess only" | If the exemption fails, all remuneration for the Indonesian work is taxable there | S1, S3 |
| T6 | Consultant with no days needs no thought | Fixed base regularly available needs no days (Art 14(1)(a)); directors' fees (Art 16) need none | S1 |
| T7 | Company staff in Bali fewer than the limit each | Service PE counts enterprise days on the same or connected project; OPEN counting method (E5b) | S1, S17 |
| T8 | Treaty rate is the rate Indonesia charges | Caps only; excess is not FITO and must be reclaimed | S7, S8 |
| T9 | Two small foreign taxes, no limit needed | The default-limit test applies to the total counting (E3) | S7 |
| T10 | Interest on Bali villa loan is disregarded for the limit | Debt deductions disregarded only for an overseas PE; claim at D15 (E2) | S7, S13 |
| T11 | Full foreign tax on a discounted gain counts | Apportion (E9); net gain nil means no FITO | S8 |
| T12 | Indonesian tax on a wholly owned PT's dividend earns FITO | NANE under s 768-5: no FITO, no underlying credit in practice | S19, S8 |
| T13 | FITO can be carried forward or refunded | No | S8 |
| T14 | Treaty makes the Bali income exempt in Australia | MLI Art 11 saving clause; only relief is the credit | S1 |
| T15 | s 23AG exempts my Bali job (1992 EM language) | s 23AG is now narrow; existing key and risk flag RES-005 | S3, repo |
| T16 | Tie-breaker: centre of vital interests, then nationality | Here: home, habitual abode, closer relations; no nationality, no mutual agreement | S1, S17 |
| T17 | Let-out villa is a "permanent home" | Not if effectively handed to guests; fact-dependent | S17 |
| T18 | Non-discrimination protects a working holiday maker | No such article in this agreement | S1, S2 |
| T19 | Share gains are taxed only in the seller's country | Art 13(5): domestic law; Art 13(4) land-rich | S1, S3 |
| T20 | Australian franked dividends to Indonesia suffer 15% | Franked: nil; only unfranked, 15% (not 30%) | S3, S12 |
| T21 | Interest to an Indonesian lender gets relief | Domestic rate equals the cap | S1, S12 |
| T22 | "ATO does not publish rupiah rates" | It does (annual, half-year, monthly); year-end rate is not allowed for unremitted foreign income; a one-off sale needs the event date rate | S9, S10, S11 |
| T23 | Indonesia is a "comparable tax" country for CFC purposes (1992 EM) | Unlisted today; PT passive income can be attributed | S15 |
| T24 | Australian company run from Bali is only Australian resident | Possible dual-resident company; MLI Art 4; no relief without agreement | S1 |
| T25 | The treaty text is in the Act | Text is [1992] ATS 40; force of law via s 5; s 4(3) Part IVA still applies | S4 |

Suggested eval matrix (at least 16 cases needed): numeric: E1, E2, E3, E6, E7, E9; trap: T2/E4, T4, T6, T10, T11, T20, T22; judgement: E10, E5b; escalation: PT control (CFC), dual-resident company, Indonesian domestic tax question, land-rich PT shares; refusal: unpublished figures (2026-27 FX, 2026-27 asset threshold); trigger: natural phrasings ("Bali villa rent", "PT PMA dividend", "120 days Jakarta", "Indonesia tax treaty").

---

## 10. What already exists versus what is new

**Exists** (do not duplicate; the new skill must reuse or reference):
- `skills/residency-cross-border` with `references/indonesia-dta.md` and `references/sources.md`; tools `indonesia_dta_check` (articles: independent_services, employment, dividends, interest, royalties, residence_tie_breaker), `foreign_income_tax_offset`, `residency_indicators`, `cross_border_scope_check` in `src/au_tax/calculators/residency.py`; tests `tests/unit/test_residency.py`.
- Overlay `data/rates/{2025-26,2026-27}.d/residency.yaml` (keys listed in section 7); refusals AU-RES-001 to 005; risk flags RES-001 to RES-007 (RES-003 is the 120-day trap).
- Evals under `evals/residency-cross-border/` with several Indonesia cases.
- Base file `data/rates/<year>.yaml` has resident scales, foreign resident scale, LITO, Medicare group, `cgt.frcgw_rate`.

I compared the existing tool and prose with the treaty text and found no contradiction of a VERIFIED figure. Small points: the Art 15 warning names Arts 16, 18, 19, 20 but Art 17 also overrides Arts 14 and 15; SKILL.md says "a non-resident employer" where the text is an employer who is not a resident of the **work** State; the tool does not model Art 6(2)(b) natural-resource royalties (uncapped) or Arts 11(6) and 12(6).

**New** (needs building or extending):
1. Service PE and days-in-window screening (Art 5, Art 14, Art 15): a deterministic rolling 12-month max-presence tool taking trips (from, to), inclusive counting, with per-income-year subtotals and the four Art 15 conditions.
2. Treaty-capped foreign tax feeding FITO in one step (cap, creditable amount, excess to reclaim, then the limit), including discounted-gain apportionment.
3. Australian withholding on payments to an Indonesian resident (franked and unfranked split, interest, royalty tiers).
4. Rupiah conversion helper that refuses when the rate for the date or year is unpublished (ATO annual, half-year and monthly rates are published; one-off events need the day's RBA rate supplied).
5. Article coverage the existing tool lacks: Arts 5, 6, 7, 13, 16, 18 (routing and cap), 22.
6. Overlay `au_indonesia` (section 7), refusals `AU-<DOMAIN>-NNN`, risk flags, router entry, plugin registration, 16 or more evals, integration scenarios (GOAL 12).
7. Boundary decision for the orchestrator: keep `residency-cross-border` as the owner of the four existing Indonesia articles and the tool, with the new skill owning PE, business profits, property, directors, pensions, inbound withholding, FX and Bali scenarios; or move all Indonesia content. Either way `indonesia_dta_check` must stay registered (existing evals rely on it).

Skill-builder notes: no numerals for days or rates in SKILL.md (lint); cite articles and keys; output contract per CONVENTIONS section 8 with `figures_used`; state the income year; the treaty constants are the same in every year but the overlay is per year.

---

## 11. Open questions and source conflicts

1. **ATO FITO guide 2026, Example 16 vs the Medicare threshold (conflict between two ATO pages).** The example (Anna, year ended 30 Jun 2026) gives tax on 31,130 of 2,459.60 including levy, which implies a lower Medicare threshold of 27,222; the ATO Medicare low-income page updated 30 Jun 2026 gives 28,011 lower and 35,013 upper for 2025-26 (matching `medicare.low_income_single_lower` in the base file, unchanged here). With 28,011 the tax is 2,380.70 and the limit 2,380.70 - 260.80 = 2,119.90, not the ATO's 2,198.80; the repo's calculator returns 2,119.90. Sources: https://www.ato.gov.au/forms-and-instructions/foreign-income-tax-offset-rules-guide-2026/calculate-your-fito-or-offset-limit and https://www.ato.gov.au/individuals-and-families/medicare-and-private-health-insurance/medicare-levy/medicare-levy-reduction/medicare-levy-reduction-for-low-income-earners . Eval authors should not copy the ATO example's 2,198.80 for 2025-26, and all examples in section 8 use incomes above the shade-out range. Orchestrator to decide.
2. **Eval `trap-unverified-fx-rate`.** Its premise is that the rate is unavailable. The ATO does publish rupiah rates, so the skill must not say it does not. The case still works because the prompt gives only "June 2026" for a one-off capital sale (the event-date rate is needed) and the grader accepts pointing to the RBA basis; check that no new skill wording implies the ATO has no rupiah rate.
3. **Earlier briefs said the treaty is scheduled to the Act**: corrected in section 3.
4. Day-count method for Art 5(2)(j), fixed base for a Bali home office or co-working desk, "permanent home available" for a let-out villa: OPEN, aids only.
5. MLI effect on ITAA 1953 s 3A(4) for Art 13(4): OPEN. Saving clause interplay with a tie-breaker result (EM says the dual resident stays a domestic resident "so far as the agreement allows"): needs a specialist.
6. Not re-read: the 4-year FITO amendment section in ITAA 1936 (ATO guide only); ITAA 1997 s 23AH text for branch profits (EM only); reg 960-50.01 instrument name; the current in-force version of DJP PER-43/PJ/2011; ATO FRCGW page (existing key carried).
7. Software and licence payments: Art 12(3) characterisation not verified; escalate.
8. Overlay schema disallows `checked_at`; recorded in notes instead. The Indonesian pension rule and other rarely used keys are proposed for completeness; the builder may drop any not used by a tool or eval.
9. Status: `VERIFIED` means read on a primary page this session; three MLI-derived constants are `SOURCE-CITED` because the ATO synthesised text is the only place I read them and it states it is not a source of law.
