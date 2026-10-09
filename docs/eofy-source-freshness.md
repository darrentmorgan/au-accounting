# EOFY scoped source refresh — 9 October 2026

This is a preparation/provenance record, not professional sign-off. The machine-readable index is `data/eofy/source-evidence.json`: source URL, UTC read time, HTTP/fetch status, exact fetched-byte SHA-256, optional extracted-text SHA-256, effective income year and figure-key disposition. Retain the external `sources/` snapshots with that index; this task saved them in firstmate's `data/aa-eofy-fix/`. Raw primary text is kept outside the repository. The dependency manifest freezes this index and all rate/source/watch files.

## Read and compared

| Scoped figures / rules | Primary evidence and disposition |
|---|---|
| 2025–26 resident rates, Medicare rate; 2026–27 resident rates for handoff tests | ATO resident tables and dated Income Tax Rates Act compilation. Brackets/base arithmetic agree with the selected-year records. |
| LITO | ATO LITO eligibility and non-refundability; dated ITAA 1997 compilation. Cap/tapers agree; offsets do not reduce levy or HELP. |
| 2025–26 Medicare individual/family thresholds, shade-in, exemptions | ATO M1, single and family reduction pages; Medicare Levy Act and Act 58 Schedule 5; ITAA 1936 volume 4. Threshold records agree. Upper family/child published limits are recorded separately from the statutory reduction formula. Spouse excess remains outside the model. |
| MLS tiers and income tests | ATO MLS page for the selected year. Rates, single/family boundaries and child addition agree; distinguish test income from surcharge base. |
| HELP | ATO repayment page: selected-year marginal schedule and income add-backs agree. HESA register baseline captures compilation identity; it does not claim a full statute review. |
| Ordinary share discount | ATO CGT discount page and dated ITAA 1997 share provisions. Discount and loss-before-discount ordering agree for 2025–26. Future reforms confer no prior-year assurance. |
| Long-term rental | ATO capital works, second-hand assets and diminishing-value pages; ITAA 1997 ss 25-25 and 40-80 in dated volumes 1/2. Residential construction-date schedule, borrowing period/limit and asset limit agree. Blocked AustLII fetches are not verification: figure URLs now point to the directly read Federal Register sections. Act 49 commencement keys were checked for the inactive 2025–26 reform branch. |
| Personal super and cap/carry-forward checks | ATO personal-contribution and historical cap pages; dated ITAA 1997 volume 6. Receipt/notice requirements, current/historical caps, balance/window tests and supplied excess-contribution constants agree. Excess-tax/credit composition is not final personal settlement. |
| Individual dates / optional quarterly instalment calendar | ATO preparation and BAS dates pages, TAA s 8AAZMB, ATO weekend/holiday table, Fair Work 2025/2026 holiday lists. Standard dates agree. WA Labour Day requires the March 2026 quarter roll to continue past Monday. Agent-program dates remain client-specific and not_computed. |
| Employee handoff / future traps | Act 49 Schedule 4 confirms the 2026–27 standard top-up, specified reductions and insurance/association exclusions; Schedule 3 starts WATO in 2027–28. Current Medicare and HELP pages do not publish the selected future low-income/repayment figures; those records stay null/SUSPECT. |

Only the 54 figure records identified in the index have refreshed `as_at` (and `checked_at` for nulls). Numerical values are unchanged. Other domains/years remain at their own verification dates. All positive assurance remains limited to the reviewer-pack boundary; indexed amounts are never copied forward.

## Corrected discrepancy

The self-lodged calendar previously said that the alternative payment date was the period after assessment without distinguishing a late return. The primary ATO page says late lodgment retains the standard November payment date. Runtime warnings, router calendar wording and corresponding rate notes now distinguish on-time later assessment from late lodgment. Two regression tests established the old failure and pass after correction. No assessment-specific due date is invented: the agent must check the actual assessment and any ATO deferral.

## Scoped watch baselines

Thirteen existing watch entries were baselined from the saved primary pages: resident rates, LITO, HELP, single/family Medicare, MLS, CGT discount, super caps, BAS dates, preparation/payment dates, the HESA register, Fair Work 2026 holidays and the ATO holiday-roll page. The ATO preparation page supplies its body in `__NEXT_DATA__`; its offline baseline uses that exact `route.fields.contentBody.value` wrapped in the expected content section, and the raw response hash is retained separately. A future raw-fetch extraction error remains an error, not an unchanged result. No challenge page was baselined and no watch scheduling was created.

Reproduce a saved raw hash with `shasum -a 256 <snapshot>`. `text_sha256` includes the saved UTF-8 text's terminal newline; the law-watch digest uses its established normalization instead. Different digest definitions are explicit in the index.

Professional interpretation, independent scenario arithmetic, installed-model runs and signed review are still outstanding. The archived integration failures and required reruns remain in `docs/eofy-reviewer-pack.md`.
