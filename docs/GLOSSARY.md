# Glossary

One definition per term. Skills, docs and calculators use the preferred term. Where a term has a non-preferred synonym, it is listed after "Not:". A short subset of those synonyms is enforced by `scripts/lint_skills.py` from `data/glossary_banned.yaml` (see "Banned synonyms" at the end). `CONVENTIONS.md` section 4 points here.

This file defines words. It holds no rates, thresholds, caps or dates that change over time; those live in `data/rates/` and are named by figure key. Tax terms cite the primary source (legislation.gov.au). Where a term is ours, the source is the convention or path that governs it.

Acts: ITAA 1936 and ITAA 1997 (Income Tax Assessment Acts), GSTA 1999 (A New Tax System (Goods and Services Tax) Act 1999), FBTAA 1986 (Fringe Benefits Tax Assessment Act 1986), TAA 1953 (Taxation Administration Act 1953), SGAA 1992 (Superannuation Guarantee (Administration) Act 1992), SISA 1993 (Superannuation Industry (Supervision) Act 1993), TASA 2009 (Tax Agent Services Act 2009).

## 1. Plugin terms

- **assumption**. A fact the skill relied on that the user did not state, listed in the working paper. Source: `CONVENTIONS.md` section 8.
- **base file**. `data/rates/<income-year>.yaml`, the file holding a year's general figures. Overlays add domain figures beside it. Not: rates sheet. Source: `CONVENTIONS.md` section 2.
- **calculator**. A Python function in `src/au_tax/calculators/` that does the arithmetic for one domain and returns an envelope. Skills never compute by hand. Not: formula, script. Source: `CONVENTIONS.md` section 5.
- **draft mode**. Running a calculator with `--allow-draft` (MCP: `allow_draft`) so it uses a figure that is not VERIFIED. The envelope then has `draft: true` and lists the figure keys. Not: estimate mode, preview. Source: `CONVENTIONS.md` section 2.
- **envelope**. The fixed result shape every calculator returns (CLI and MCP alike): `exit_code`, `income_year`, result fields, `figures_used`, `draft`, and `refusal` when refused, plus `assumptions` and `warnings`. Not: response object, payload. Source: `CONVENTIONS.md` section 5.
- **escalation**. Handing part of the work to a person because a trigger fired (a refusal code, or a skill's own escalation rule). The skill states the trigger, the route and what was not done. Not: referral. Source: `CONVENTIONS.md` section 6.
- **eval**. A test case under `evals/<slug>/<case>/` that checks how a skill behaves on a natural prompt. Source: `CONVENTIONS.md` section 10.
- **exit code**. The number in the envelope saying how a run ended: ok, invalid input, refused, or missing or unverified figure. The values are listed in `CONVENTIONS.md` section 5.
- **figure**. A rate, threshold, cap, fee or date that changes over time, stored only in `data/rates/` with `value`, `unit`, `status`, `source`, `as_at`. Not: constant (a statutory constant that never changes is allowlisted in `data/lint_allowlist.yaml`), parameter, rate table. Source: `CONVENTIONS.md` section 2.
- **figure key**. The dotted name of a figure, `<domain>.<name>`. Skill prose names figures by key or by name, never by amount. Not: rate name, setting. Source: `CONVENTIONS.md` section 2.
- **figures used**. The list in the envelope (`figures_used`) of each figure a run read, with key, value, status and source. It becomes item 2 of the output contract. Source: `CONVENTIONS.md` sections 5 and 8.
- **handoff**. Passing one skill's result to another skill as an input, exactly as returned. Fields are in `skills/router/references/skill-map.md`. Source: `skills/router/SKILL.md`.
- **income year**. The period a rates file and a calculation apply to, labelled `2026-27`. FBT uses the FBT year; SA land tax and company financial reports use the financial year. Not: tax year, fiscal year. Source: ITAA 1997 s 995-1 ("income year"); label rule in `CONVENTIONS.md` section 3.
- **output contract**. The six-part ending every working paper has: result, figures used, assumptions, risk flags, refusals or escalations, review line. Not: report format. Source: `CONVENTIONS.md` section 8.
- **overlay**. A domain-specific rates file at `data/rates/<year>.d/<domain>.yaml`: same schema as the base file, no `meta`, no key collisions. Not: extension file, override. Source: `CONVENTIONS.md` section 5.
- **preparer**. The route value in the refusal catalogue for a refusal that the person preparing the work can clear (for example by confirming a missing figure), rather than a professional. Source: `data/refusals/au.yaml`.
- **primary source**. Legislation (legislation.gov.au), ATO pages and rulings, Treasury, courts, ASIC, state revenue offices and the Fair Work Commission. Firms, blogs and news are secondary and never the citation. Source: `CONVENTIONS.md` section 1.
- **refusal**. A calculator or skill declining to proceed, returned with a refusal code. Skills quote the code and message verbatim and stop the affected part. Not: error, failure. Source: `CONVENTIONS.md` section 6.
- **refusal code**. A code such as `AU-GEN-001`, defined with trigger, message and route in `data/refusals/*.yaml`. Never invented outside those files. Source: `CONVENTIONS.md` section 6.
- **review line**. The fixed last line of a working paper: "Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use." Source: `CONVENTIONS.md` section 8.
- **review status**. Whether a skill has a recorded human review (`data/reviews/<slug>.yaml`) matching its current content hash. Any edit reverts it to draft. Source: `CONVENTIONS.md` section 9.
- **risk flag**. A structured audit risk point in `data/risk_flags/*.yaml` (`id`, `topic`, `description`, `citations`, `skills`) that a skill lists in its output. Not: red flag, audit flash point. Source: `CONVENTIONS.md` section 7.
- **router**. The skill that works out which domain skills apply, runs them in order, and produces the combined working paper. Source: `skills/router/SKILL.md`.
- **skill**. One folder `skills/<slug>/` with a `SKILL.md`, covering one obligation or domain. Not: agent, module. Source: `CONVENTIONS.md` section 4.
- **SOURCE-CITED**. Figure status: a primary source is cited but the page was not re-read. Source: `CONVENTIONS.md` section 2.
- **SUSPECT**. Figure status: there is a conflict, the value is stale, or it was not found. `value: null` is allowed only here. Source: `CONVENTIONS.md` section 2.
- **VERIFIED**. Figure status: the value was read on a primary page. Only a VERIFIED figure is used without draft mode. Source: `CONVENTIONS.md` section 2.
- **tool**. A calculator as the model sees it, through the `au-tax` MCP server, named `<tool_name>`. Skills name tools by `<tool_name>` and never shell out. Not: function, API. Source: `CONVENTIONS.md` section 5.
- **working paper**. The written output of a skill: results with their figures, assumptions, flags and refusals, for a reviewer. It is not advice and not a lodged document. Not: workpaper, work paper, working-paper. Source: `CONVENTIONS.md` section 8; refusal `AU-GEN-002`.

## 2. People and bodies

- **ATO**. Australian Taxation Office, the agency the Commissioner heads. Source: TAA 1953; ITAA 1997 s 995-1 ("Commissioner").
- **BAS agent**. A person registered with the Tax Practitioners Board to provide BAS services. Skills route BAS matters to a BAS agent or a registered tax agent. Source: TASA 2009 s 90-1 and s 90-10.
- **Commissioner**. The Commissioner of Taxation. Source: ITAA 1997 s 995-1.
- **registered agent lodgment program**. The ATO's published due dates for lodgments made through a registered agent. Dates come from `data/rates/`; sources are in `skills/payg-instalments-lodgment/references/sources.md`. Source: ATO, as cited there.
- **registered tax agent**. A person registered with the Tax Practitioners Board to provide tax agent services, including preparing and lodging returns for a fee. Every review line and every route for work the plugin cannot do names a registered tax agent. Not: accountant, tax professional, tax practitioner (any of these may or may not be registered). Source: TASA 2009 s 90-1 and s 90-5.

## 3. Periods and entities

- **aggregated turnover**. The entity's annual turnover plus that of connected and affiliated entities. Source: ITAA 1997 s 328-115.
- **FBT year**. The fringe benefits tax year, 1 April to 31 March, labelled `FBT2027` for the year ending 31 March 2027. Not: fringe benefits tax year. Source: FBTAA 1986 s 136(1) ("FBT year"); label rule in `CONVENTIONS.md` section 3.
- **financial year**. The 1 July to 30 June year used by SA land tax and by company financial reports. It is not banned, because those laws use it. For a federal income tax calculation use income year. Source: Land Tax Act 1936 (SA); Corporations Act 2001 s 9.
- **foreign resident**. A person who is not a resident of Australia for tax purposes. Not: non-resident. Source: ITAA 1997 s 995-1 ("foreign resident").
- **personal services income (PSI)**. Income mainly a reward for a person's personal efforts or skills. The PSI rules test whether it is a personal services business. Source: ITAA 1997 s 84-5.
- **resident for tax purposes**. A person who is a resident of Australia under one of the residency tests (resides, domicile and permanent place of abode, days present, Commonwealth superannuation fund). Skills give an indication only, from facts the user supplies. Not: tax resident (write the full term in outputs). Source: ITAA 1936 s 6(1) ("resident or resident of Australia").
- **small business entity**. An entity that carries on a business and has aggregated turnover under the relevant threshold (a figure, not stated here). Source: ITAA 1997 s 328-110.
- **temporary resident**. A holder of a temporary visa, with specific exemptions for foreign income. Source: ITAA 1997 s 995-1 ("temporary resident"); Subdiv 768-R.

## 4. Income and deductions

- **assessable income**. Ordinary income and statutory income that is not exempt. Not: gross income, total income. Source: ITAA 1997 s 6-5, s 6-10.
- **capital works deduction**. A deduction for the construction cost of buildings and structures. Source: ITAA 1997 Div 43.
- **deduction**. A loss or outgoing that reduces assessable income, mostly under the general rule. Not: write-off (except in the depreciation terms below), claim. Source: ITAA 1997 s 8-1.
- **depreciating asset**. An asset with a limited effective life that can reasonably be expected to decline in value. Source: ITAA 1997 s 40-30.
- **effective life**. The period an asset can be used for a taxable purpose, self-assessed or taken from a Commissioner determination. Source: ITAA 1997 s 40-95.
- **exempt income**. Income that is not assessable and not counted, under a specific exemption provision. Source: ITAA 1997 s 6-20.
- **foreign income tax offset (FITO)**. An offset for foreign tax paid on foreign income. Source: ITAA 1997 Div 770.
- **holiday home**. Our term for a property used or held for use for the owner's holidays or recreation, or the holidays or recreation of family or friends at no or reduced rent. Its ownership and use costs are denied unless it is used or held mainly to produce rent. Source: ITAA 1997 s 26-50; TR 2026/1 para 12.
- **negative gearing**. Informal term for a net rental loss (or other investment loss) set against other income. It is not a statutory term; skills say "net rental loss" where they can. Source: ITAA 1997 s 8-1 and s 6-5.
- **net rental result**. Rent less rental deductions for a property. A loss is subject to the negative gearing rules in the rental-property skill. Source: ITAA 1997 s 8-1 and s 6-5.
- **non-commercial loss**. A business loss that may not be deducted against other income unless a test is met. Source: ITAA 1997 Div 35.
- **prepayment**. Expenditure for services to be provided in a later period, deductible over that period unless an exception applies. Source: ITAA 1936 s 82KZM.
- **simplified depreciation**. The small business depreciation rules, including the instant asset write-off and the general small business pool. Source: ITAA 1997 Subdiv 328-D.
- **tax offset**. An amount that reduces tax payable, not taxable income. Not: rebate. Source: ITAA 1997 s 4-10(3), Div 13.
- **taxable income**. Assessable income less deductions. It is the base the rates apply to. Not: net income (that means trust net income), profit. Source: ITAA 1997 s 4-15.

## 5. Capital gains tax

- **capital gain**, **capital loss**. The result of a CGT event. Capital proceeds over cost base is a gain; the reverse, using the reduced cost base, is a loss. Source: ITAA 1997 s 102-20; Div 104.
- **capital proceeds**. What the taxpayer received or is entitled to receive for the CGT event. Not: sale price, sale proceeds. Source: ITAA 1997 s 116-20.
- **capital account**, **revenue account**. Whether a receipt or gain is a capital gain (CGT) or ordinary income and trading stock. An investor holds crypto on capital account; a business or a commercial profit-making transaction puts it on revenue account, where the CGT discount does not apply. Source: ITAA 1997 s 118-20; TD 2014/26; TR 92/3.
- **CGT asset**. Any kind of property, or a legal or equitable right that is not property. Source: ITAA 1997 s 108-5.
- **CGT discount**. A reduction of a capital gain for an eligible entity that held the asset for the minimum period. The percentage is a statutory constant. Source: ITAA 1997 Div 115, s 115-100.
- **CGT event**. An event that can produce a capital gain or loss, such as disposing of an asset. Its type and time decide the rules and the income year. Source: ITAA 1997 s 104-5; s 102-20.
- **cost base**. What the asset cost, made up of the statutory elements. Not: base cost, purchase price. Source: ITAA 1997 s 110-25.
- **main residence exemption**. Exemption of a gain on a dwelling that was the owner's main residence. Source: ITAA 1997 s 118-110.
- **net capital gain**. Capital gains for the year less capital losses (current and carried forward), then any discount and small business concessions. It is the one CGT amount passed to income tax. Source: ITAA 1997 s 102-5.
- **parcel**. A quantity of one crypto asset (or other identical asset) acquired at one time with its own acquisition date and cost base; disposals are matched to parcels. Source: TD 33 (identical assets that cannot be individually distinguished); `crypto_parcel_ledger`.
- **personal use asset**. A CGT asset (not a collectable) used or kept mainly for personal use or enjoyment; a loss on it is disregarded and a gain is disregarded if the first element of cost base is at or below the threshold. Source: ITAA 1997 s 108-20; s 118-10(3).
- **reduced cost base**. The cost base with certain elements removed, used to work out a capital loss. Source: ITAA 1997 s 110-55.
- **small business CGT concessions**. Extra reductions and exemptions for gains on active business assets. Source: ITAA 1997 Div 152.

## 6. Dividends, companies and trusts

- **benchmark interest rate**. The Division 7A rate, published each year, used to test loans and set minimum repayments. It is a figure. Source: ITAA 1936 s 109N.
- **deemed dividend**. An amount Division 7A treats as a dividend to a shareholder or associate. Source: ITAA 1936 s 109C.
- **Division 7A**. Rules that treat certain private company payments, loans and debt forgiveness to shareholders and their associates as dividends. Write "Division 7A" or "Div 7A", never "Div 7". Source: ITAA 1936 Pt III Div 7A.
- **franked dividend**. A dividend paid with a franking credit attached. Source: ITAA 1997 Div 202.
- **franking credit**. Tax already paid by the company, passed to the shareholder with a franked dividend, added to assessable income and allowed as a tax offset. Not: imputation credit, dividend credit. Source: ITAA 1997 s 205-30; Div 207.
- **net income of the trust estate**. Trust income calculated as if the trustee were a resident taxpayer, before shares are assessed to beneficiaries. Not: distributable income (the trust deed's income). Source: ITAA 1936 s 95.
- **present entitlement**. A beneficiary's right to call for a share of trust income for the year. Source: ITAA 1936 s 97.
- **unpaid present entitlement (UPE)**. Trust income a beneficiary is entitled to but has not been paid. Whether a company's UPE is a Division 7A loan turns on the case law and ATO position cited in `skills/trusts-partnerships/SKILL.md`. Source: ITAA 1936 s 109D(3); FCT v Bendel [2026] HCA 18.

## 7. GST and BAS

- **BAS**. Business activity statement, the form on which GST, PAYG withholding and PAYG instalments are reported for a period. Not: GST return. Source: TAA 1953 Sch 1 Div 31.
- **BAS label**. A labelled field on the BAS (for example G1, 1A, W1). Skills report them exactly as the calculator returns them. Source: ATO BAS instructions, cited in `skills/gst-bas/references/sources.md`.
- **commercial residential premises (CRP)**. A hotel, motel, inn, hostel or boarding house, school accommodation, certain ships and marina berths, a caravan park or camping ground, or anything similar. Accommodation in CRP supplied by the entity that owns or controls it is taxable; whether hotel-like premises are CRP is a question of fact under GSTR 2012/6, which skills escalate and never decide. Not: hotel-style property. Source: GSTA 1999 s 195-1; GSTR 2012/6.
- **GST-free**. A supply on which GST is nil but credits remain available. Source: GSTA 1999 s 9-30(1).
- **GST turnover**. The value of the entity's supplies over a period, used to test registration and choose reporting options. Source: GSTA 1999 s 188-10.
- **input tax credit**. A credit for GST included in the price of a creditable acquisition. Not: GST refund, GST rebate. Source: GSTA 1999 s 11-5.
- **input taxed**. A supply on which no GST is charged and no credit is available for related purchases. Source: GSTA 1999 s 9-30(2).
- **residential premises**. Land or a building occupied, or intended and capable of being occupied, as a residence or for residential accommodation, regardless of the term of occupation. Rent of residential premises is input taxed, so a house, unit or room let short term is residential premises. Source: GSTA 1999 s 195-1; s 40-35.
- **taxable supply**. A sale that carries GST. Source: GSTA 1999 s 9-5.

## 8. PAYG, payroll, state tax and super

- **carry-forward (unused concessional cap)**. Unused concessional cap from earlier years, available to people under the total super balance test. Source: ITAA 1997 s 291-20.
- **concessional contribution**. A contribution to super taxed in the fund and counted against the concessional cap. Source: ITAA 1997 s 291-25.
- **Division 293 tax**. Additional tax on concessional contributions for people with high combined income and contributions. Source: ITAA 1997 s 293-20.
- **instalment income**. The ordinary income and statutory income that PAYG instalments are based on. Source: TAA 1953 Sch 1 Div 45.
- **land tax**. State tax on the taxable value of land owned at midnight on 30 June before the financial year. In SA, Land Tax Act 1936 (SA). Source: as stated.
- **non-concessional contribution**. A contribution to super from after-tax money, counted against the non-concessional cap. Source: ITAA 1997 s 292-90.
- **ordinary time earnings (OTE)**. The earnings base the SG rate applies to. Source: SGAA 1992 s 6(1).
- **PAYG instalment**. Prepayment of a year's income tax, worked out from instalment income or a rate. Source: TAA 1953 Sch 1 Div 45.
- **PAYG withholding**. Tax an employer or payer withholds from payments and remits to the ATO. Source: TAA 1953 Sch 1 s 12-35.
- **payroll tax**. State tax on wages above a threshold. In SA, Payroll Tax Act 2009 (SA). Source: as stated.
- **SG charge (SGC)**. The charge payable when SG is not paid on time and in full. Source: SGAA 1992 Pt 3.
- **SMSF**. Self managed superannuation fund. Source: SISA 1993 s 17A.
- **superannuation guarantee (SG)**. The employer's obligation to contribute to super for eligible employees. Not: super guarantee, compulsory super. Source: SGAA 1992.
- **total super balance**. The measure used to test eligibility for the non-concessional cap and carry-forward. Source: ITAA 1997 s 307-230.

## 9. Individuals and FBT

- **fringe benefit**. A benefit provided to an employee or associate because of employment. Source: FBTAA 1986 s 136(1).
- **gross-up rate**. The factor that converts a benefit's taxable value to the value used for FBT, by the GST type of the benefit (type 1 or type 2). It is a figure. Source: FBTAA 1986 s 5B.
- **HELP**. The higher education loan program. Repayments are worked out from repayment income. Source: Higher Education Support Act 2003 Ch 4.
- **Medicare levy**. The levy on taxable income for residents, with low-income reductions. Source: ITAA 1936 s 251S (residents only), Medicare Levy Act 1986 s 6 (rate), s 8 (low-income reductions).
- **Medicare levy surcharge (MLS)**. An extra levy for people without appropriate private hospital cover, above an income threshold. Source: Medicare Levy Act 1986 ss 8B-8D.
- **reportable fringe benefits amount**. An employee's grossed-up fringe benefits above the reporting threshold, used in income tests. Source: FBTAA 1986 s 5E.
- **taxable value**. The value of a fringe benefit after the valuation rules, before gross-up. Source: FBTAA 1986 Pt III.

## 10. ATO guidance

- **ruling**. A published ATO view. A Taxation Ruling (TR), Taxation Determination (TD) or Law Companion Ruling (LCR) can bind the Commissioner; a Practical Compliance Guideline (PCG) states compliance approach and does not bind. Cite as `TR 2026/1`. Source: TAA 1953 Sch 1 Div 358.

- **Sharing Economy Reporting Regime (SERR)**. The reporting rule under which operators of electronic distribution platforms report supplies made through them, including short-term accommodation, to the ATO. It is a platform duty: it withholds no tax and gives the host no filing duty. Source: TAA 1953 Sch 1 Subdiv 396-B, s 396-55 table item 15.

## Banned synonyms

Enforced by `scripts/lint_skills.py` in every `skills/*/SKILL.md` and `skills/*/references/*.md`, outside code fences, inline code and URLs. The machine-readable list is `data/glossary_banned.yaml`.

| Preferred | Banned synonyms |
|---|---|
| income year | tax year, fiscal year |
| working paper | workpaper, work paper, working-paper |
| risk flag | red flag, audit flash point |

Before adding to the list, search `skills/` for real use of the synonym, and check the term is never the correct one in some context (which is why "financial year" is not banned).
