# Bounded individual EOFY reviewer pack

Status: preparation material, **not professionally reviewed**. This document freezes the review request and prompt; a signed opinion must bind an exact candidate commit and dependency/scenario manifest. It does not create an `/eofy` command or an EOFY agent.

## Engagement boundary

The positive review is limited to the **2025–26** income year, Australian full-year resident adults who are employees, with bank interest, unfranked dividends and independently substantiated ordinary deductions. Optional branches are ordinary Australian long-term rental property, ordinary share disposals and personal deductible super contributions with eligibility and notice evidence. HELP, Medicare and MLS are tested within these facts. The output is a preparation working paper and obligations calendar for a registered tax agent's case-specific review.

Excluded positive assurance: business/ABN activity, crypto, short-stay letting, foreign income or unsettled residency, trust/partnership/company distributions, franked dividends, property sales/main-residence decisions, SAPTO, minors' unearned income, deceased final returns, special lump sums and specialised offsets. Excluded facts test routing/refusal only. Raw employee deductions needing eligibility or substantiation judgement are not covered by acceptance of a supplied deduction figure. Family levy excess passing to a spouse is not modelled; missing material cover/spouse facts make dependent totals incomplete. No lodgment, payment or agent-calendar date is authorised.

2026–27 and 2027–28 are separate planning, handoff and year-refusal tests. They inherit no 2025–26 assurance. A selected workflow review does not mark the complete router, individual-tax, rental-property, cgt, super-contributions or payg-instalments-lodgment skill folder reviewed, and does not establish whole-return, all-year, TPB or ATO approval.

## Canonical positive prompt (E01)

> Prepare a working paper for registered-agent review for my 2025–26 individual return. I was an Australian tax resident for the whole year, an adult, single, with no dependants, SAPTO eligibility or special lump sums. Salary $110,000; an Australian rental unit bought in 2019 had an independently substantiated net rental loss of $8,000; shares held for three years produced a $12,000 gain, no capital losses. Appropriate hospital cover all year; no HELP debt; no foreign income, business, crypto, franked dividends or other deductions/offsets. Ignore PAYG credits. Show income assembly, tax components, sources, assumptions, risks, missing work and the individual obligations calendar. Do not lodge or pay anything.

The existing `evals/integration/int-num-resident-rental-shares-2526/prompt.md` is a thinner historical fixture. Use the exact prompt above for this pack. Independently derived smoke expectation: share gain after discount is $6,000; taxable income = $110,000 − $8,000 + $6,000 = $108,000; gross tax = $4,288 + ($108,000 − $45,000) × 0.30 = $23,188; LITO nil; Medicare = $108,000 × 0.02 = $2,160; MLS/HELP nil; liability before credits $25,348. A tax agent must independently verify these expectations against the sources; repeating this calculator's output is not independent evidence. E07 separately tests rental expense eligibility rather than accepting a supplied net loss.

## Rule-to-implementation review

| Positive path | Owning files/tools | Independent reviewer checks |
|---|---|---|
| Intake and assembly | `skills/router/`, `src/au_tax/calculators/router.py`: `assemble_taxable_income` | Income source/year, one annual net capital gain, duplicate prevention, no capital loss against salary, rental-loss add-back for HELP/MLS |
| Individual components | `skills/individual-tax/`, `src/au_tax/calculators/individual.py`: `individual_income_tax` | Resident rates; LITO ordering/cap; Medicare reductions/exemptions; MLS base versus test income and cover; HELP add-backs/debt cap |
| Long-term rental | `skills/rental-property/`, `src/au_tax/calculators/rental.py` | Ownership, loan purpose, private costs, repairs versus capital, capital works evidence |
| Ordinary shares | `skills/cgt/`, `src/au_tax/calculators/cgt.py`: `net_capital_gain` | Contract year, losses before discount, holding period, carried-forward losses |
| Personal super deduction | `skills/super-contributions/`, `src/au_tax/calculators/super_contrib.py` | Eligibility, fund receipt, acknowledged notice, caps/carry-forward, reportable contributions |
| Individual calendar | `skills/payg-instalments-lodgment/`, `src/au_tax/calculators/payg_lodgment.py`, router `obligations_calendar` | Primary date/rule, holiday roll, no universal agent extension; agent verifies own ATO client record |

Authorities and figure keys are in each owning skill's `references/sources.md`, `references/rules.md`, tool `figures_used` and the income-year rate files. The frozen manifest includes them. Each case record must map its exact inputs and figure keys to those authorities, their effective income year and the agent's independent computation.

## Scenario register

All positive cases begin in 2025–26. Boundary variants use the chosen year's keys (below, at and above each threshold). These are required review scenarios, not a claim that model runs passed. Capture exact prompt, complete intake facts, skill/tool trace, inputs, envelopes, figures_used, final paper, UTC run time, software/model versions, candidate commit, pass/fail/not-run and reviewer comments. Initially every installed-model/professional run is **not-run**; local unit results belong in a separate run record.

| ID | Synthetic case | Required reviewer check / acceptance |
|---|---|---|
| E01 | Canonical salary + supplied rental loss + long-held shares | Load owning skills, use one net CGT figure and assembly; verify $108,000/$25,348 and full paper/calendar contract |
| E02 | Salary $45,000, single, full hospital cover, no HELP | Independently verify gross tax $4,288, LITO $325, levy $900, liability $4,863; no business skill required |
| E03 | LITO and resident-bracket boundaries, cents in taxable income | Nil tax at $18,200; LITO cap/tapers; whole-dollar assessment handling and cents presentation (`tests/unit/test_individual.py:31–89,379`) |
| E04 | Medicare $28,011/$28,012, $29,000 and $35,013; married/sole-parent variants | Validate single shade-in (at $29,000 levy $98.90), family reduction/apportionment and any unmodelled spouse excess (`tests/unit/test_individual.py:121–171`; rules.md:9) |
| E05 | MLS tier boundary; reportable benefits/super and investment losses; partial-year cover | Distinguish tier-testing income from surcharge base; spouse/dependants and days covered; missing cover must be contingent, not a final nil amount |
| E06 | HELP repayment income around $67,000/$125,000/$179,285; debt smaller than repayment | Marginal method, correct add-backs, debt cap, and offsets not reducing compulsory repayment (`tests/unit/test_individual.py:276–292`) |
| E07 | Detailed long-term jointly owned rental; loan redraw for private use; repairs versus capital | Ownership share, loan-purpose tracing, private expense exclusion, capital works evidence; reconcile net result to source, not net bank deposits |
| E08 | Share gains with current and carried-forward losses, short-held asset and exact 12-month boundary | Losses before discount, one annual net capital gain, carried-forward loss never deducted against salary, contract-date year |
| E09 | Personal super deduction with acknowledged notice; late/invalid notice and fund receipt near 30 June | Eligibility and cap/carry-forward facts before accepting deduction; distinguish voluntary/reportable amounts from ordinary employer SG |
| E10 | Duplicate rental/CGT components; raw capital loss; inconsistent year or residency | Assembly block must prevent final taxable income/tax; fix at source, no guessed arithmetic workaround |
| E11 | PAYG withheld with no unmodelled offsets; then add franked dividends/PHI rebate/PAYG instalments | Only first case can use calculator refund as complete within scope; latter cases show exclusions/agent reconciliation and no asserted final refund |
| E12 | Self-lodged versus registered-agent return, prior outstanding return and weekend date | Calendar carries source/roll; registered-agent date verified against agent's own client record; never promise a universal extension |
| E13 | “This year” asked in October 2026; missing residency/cover/spouse facts | Clarify income year and material missing inputs before producing a complete figure; consistent intake defaults |
| E14 | SAPTO/pension, minor unearned income, deceased final return, ETP/redundancy/super lump sum | Verbatim AU-IND-001/002 as applicable; stop dependent total. Existing `evals/individual-tax/escalate-*` cover examples |
| E15 | Foreign-resident HELP or complicated WHM; owner moved overseas with thin facts | AU-IND-003/004 or residency escalation; do not silently treat stated move as settled residency |
| E16 | Calculator unavailable; unverified versus unpublished figure; request to lodge/pay | AU-GEN-001/003/002 as applicable; only unverified-with-value can be draft; no manual fallback arithmetic or external action |
| E17 | 2026–27 low-income Medicare and wage standard-deduction case; 2027–28 unknown indexed thresholds | Refuse missing figures; test the standard-deduction top-up and single assembly handoff, never apply it to 2025–26; keep future-year cases outside positive assurance; do not copy prior-year tables |
| E18 | One excluded crypto/short-stay/foreign/trust component added to E01 | Load the owning skill or explicitly unavailable/escalated; dependent total incomplete. Run relevant integration fixtures only if extending the review |

## Paper and signed review contract

At the top state year, taxpayer/entity, permitted scope, unsettled material facts and **Parts not completed**. Show source-labelled income build-up, components, calendar (including not-computed dates), figures_used, assumptions, risks and verbatim refusals. End exactly: “Working paper only. Review by a registered tax agent (or BAS agent for BAS matters) before use.”

Findings require severity, file:line, affected case/year, authority, correction and reviewer disposition. After a material correction, freeze a new candidate, rerun affected cases and obtain re-review. A unit/LLM pass does not resolve an agent objection.

An issued assurance record must contain the agent's real name, TPB registration/entity, current registration-check URL/date/conditions, engagement identifier, review date, exact candidate commit, precise workflow/year/facts, dependency-manifest digest, scenario/results digest, qualifications/exclusions and signed document hash. No signature or professional opinion exists in this pack. Suggested wording for the agent to amend: reviewed only the stated preparation workflow, frozen files and attached scenarios for the stated year/facts, subject to limitations; every client paper still requires case-specific registered-agent review.

## Remaining integration work (P1-8)

No paid integration sweep is run in this task. The archived `docs/eval-results/v0.3/final-3/20260930T190019-integration.result.json.gz` reports 13/16 casesPassed, overallScore 0.8885416667, overallPassRate 0.78125 and meanDelta 0.5572916667. Five cases have per-run passRate below 1: bot-trader/head-lease escalation; family-trust/minor/foreign-trust escalation; Adelaide/Bali/staking onboarding; SA sole-trader onboarding; unpublished-IDR refusal. Review their expected results/rubrics and rerun on the final candidate, together with E01–E18 and affected skill suites, before relying on installed behaviour. Historic results and local deterministic tests provide no professional approval.

## Dependency and scenario freeze (P0-2)

On the clean final committed candidate run `uv run python scripts/eofy_manifest.py > <external-pack>/manifest.tsv`, then `shasum -a 256 <external-pack>/manifest.tsv`. The script records candidate commit/tree and sorted SHA-256/path rows, fails on a dirty candidate or missing required scope, and includes:

- All runtime modules (the registry imports all calculators), all rate bases/overlays for all supported years (the loader loads every overlay), complete refusal/risk catalogues, holiday data and execution configuration/lockfile.
- Every installed skill folder as a technical dependency, including the six core skills, employee WFH/car business handoff and excluded-domain routing/refusal skills; review records/status code, maintenance/lint/source-watch files and this scope/prompt/scenario register. This inventory does not expand the positive professional scope.
- All unit/data tests, individual-tax and core-domain eval fixtures/graders and the historical salary/rental/shares integration fixture. Other domain runtime/data are frozen technical dependencies, with no positive tax assurance implied.

The scenario manifest is the E01–E18 register above bound by this document's hash. Retain a separate results manifest with one row per variant: scenario ID, year, exact prompt/input/output/trace paths and hashes, candidate commit, UTC timestamp, versions, independent expected-result authority, local result, installed-model result and professional disposition. Explicitly use **not-run** rather than dropping unexecuted scenarios. Hash the results manifest and every referenced evidence file; bind both dependency and completed-results digests in the signed opinion. The generator freezes dependencies; it does not fabricate results.

### Offline results template and file-integrity check

`scripts/eofy_results_manifest.py` is separate from the dependency generator. It emits a JSON template with E01–E18 explicitly **not-run**: 19 rows, because E17 has separate 2026–27 and 2027–28 planning/refusal entries. Other scenarios are 2025–26 only. On the clean committed candidate, keep all generated records and evidence in an external pack directory:

```sh
uv run python scripts/eofy_results_manifest.py template --candidate "$(git rev-parse HEAD)" > <external-pack>/records.json
uv run python scripts/eofy_results_manifest.py freeze <external-pack>/records.json --evidence-root <external-pack> > <external-pack>/results.json
shasum -a 256 <external-pack>/results.json
uv run python scripts/eofy_results_manifest.py verify <external-pack>/results.json --evidence-root <external-pack> --sha256 <retained-results-digest>
```

Use different input and output files; shell redirection to the input file would truncate it. The initial template's evidence references and `run_at_utc` are null, `versions` is empty, and every result/disposition is `not-run`. No run time or software/model version is invented for an unexecuted scenario. Generation performs no computations, scenario execution, model calls, registration checks or signing.

To record supplied local evidence, edit a row in `records.json`: select `local_result` (`pass` or `fail`) and `evidence_tier` (`synthetic` or `local`), supply the actual `run_at_utc` in `YYYY-MM-DDTHH:MM:SSZ` form and a nonempty `versions` mapping of software names to exact versions. Supply all five `evidence` entries (`prompt`, `input`, `output`, `trace`, `expected_authority`), each as `{"path": "relative/file.txt", "sha256": null}`. The authority file must retain the independently supplied expectation and source/year mapping; file hashing does not judge its correctness. Unexecuted rows may reference prompt/input/authority fixtures, but cannot claim output, trace or run metadata. Add variants with distinct lowercase `variant` slugs; do not remove required scenario/year coverage. Duplicate scenario ID/year/variant combinations, unknown IDs, out-of-scope years, mismatched candidate SHAs, unknown fields, missing files and paths escaping the evidence root are rejected.

`freeze` supplies hashes only where null; an existing hash must match, so changed evidence cannot silently be re-frozen. Output rows and object keys have stable ordering and unchanged inputs produce identical UTF-8 bytes/digests. `verify` requires the externally retained manifest digest, checks canonical bytes and every referenced file hash, and fails on modified/missing evidence. Retain the digest outside the mutable pack; the helper checks the supplied SHA's format and row consistency, but does not authenticate the candidate, run, version, result or authority claims. Bind the same candidate to the dependency manifest separately.

This offline schema keeps `installed_model_result` and `professional_disposition` fixed at **not-run**, including after a local/synthetic pass. It rejects signature/reviewer fields and creates no reviewer identity or assurance record. Actual installed-model runs and professional opinions require separate evidence and the signed-review contract above; a successful file-integrity check is not a scenario pass or professional approval.

Any dependency, scenario, scope or year change invalidates the workflow opinion pending assessment and re-review. `scripts/review_status.py` remains a skill-folder prose status: it does not validate runtime/rates, partial workflow scope, registration, signed evidence or later adverse findings. It must not be cited as EOFY assurance. No placeholders are installed as review records.

## Agent reconciliation and settlement exclusion (P0-3)

The positive pack ignores PAYG credits in E01. A withholding-only variant of E11 can show a provisional estimate within the modelled scope only after confirming absent other offsets/credits and complete material inputs. No final assessment or account settlement is assured.

For franked dividends, PHI rebates, FITO, SBITO, other offsets, PAYG instalments or unresolved credits, put **final settlement not computed** at the top. A gross-up belongs in income assembly; its credit is a separate reconciliation item. Never treat the tool's limited `total_liability` or `estimated_refund` as final for those cases, and never net separately returned offsets in prose.

| Agent reconciliation item | Evidence / disposition required |
|---|---|
| PAYG withholding | Finalised income statements/payment summaries; year and exact source amount |
| PAYG instalments | ATO account amounts credited for the year; distinguish instalments from withholding and account payments |
| Franking | Dividend/distribution statement, assessable gross-up, credit amount, eligibility/holding-period checks |
| PHI | Insurer statement, rebate already received, age/income/family facts and final rebate adjustment |
| FITO/SBITO/other offsets | Separate tool result and entitlement evidence; agent verifies ordering/cap/refundability |
| Other credits / account balances | ATO assessment and account evidence; avoid treating balances as current-year income-tax credits |

Mark every item confirmed absent, supplied (year/source/amount) or unresolved. Preserve modelled tax, levy, MLS and HELP outputs beside the reconciliation. The agent completes the assessment and account settlement. Full deterministic offset/credit composition is deferred: it needs a separate audited ordering/refundability contract and tests; no partial composition is introduced by this pack.

## Future-year employee handoff (P1-4)

`standard_work_deduction` computes the s 25-130 additional top-up from classified labour income and reducing deductions, using the verified year cap. Residency-at-any-time and deduction classification are explicit inputs. Insurance/association exclusions do not reduce the top-up. Router assembly deducts only that top-up once alongside existing eligible costs. This is a separate 2026–27 planning test and never a 2025–26 deduction or assurance extension. Low-income Medicare and other unpublished figures still refuse. Agent review of classification and depreciating-asset consequences remains necessary.

## Employee intake (P1-5)

The canonical checklist is `skills/router/references/employee-deductions.md`, linked from router intake and individual-tax. It covers eligibility and substantiation without treating a receipt, allowance or method threshold as automatic entitlement. Employee WFH/car tool routing does not expand the positive pack to raw claim assurance or business regimes.

## Scoped freshness record (P1-7)

See `docs/eofy-source-freshness.md` and `data/eofy/source-evidence.json` for the 9 October 2026 primary reads, fetched-content hashes, effective years, 54 scoped figure dispositions, 13 scoped watch baselines and the corrected self-lodged payment rule. Retain the external source snapshots with the generated manifest. Unpublished future figures remain null/SUSPECT; no other-year or whole-plugin freshness claim is made.
