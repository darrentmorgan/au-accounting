# Runbook: the annual July update

Written for an agent that did not build the plugin. Follow it in order. Rules are in `CONVENTIONS.md`; this file says what to run and what to expect. Do not restate figures here or in your notes: point to `data/rates/`.

## Terms used below

- `PREV`: the newest income year that has a rates file when you start (for example `2027-28` in July 2027).
- `NEW`: the next income year, the one you are creating (for example `2028-29`).
- `NEW_START`: 1 July of the first calendar year in `NEW`.
- A step marked **Needs the project owner** stops until the project owner answers. Everything else an agent can do alone.

## What this runbook does not do

- It does not invent, index or estimate figures. If a figure is not on a primary page, it stays `SUSPECT` with `value: null` and a `checked_at` date (`CONVENTIONS.md` section 2).
- It does not merge to `main`, spend money, schedule anything or change global config. Those need the project owner.
- It does not make anything "reviewed". Review status comes from `data/reviews/` (`CONVENTIONS.md` section 9).

## Timing

Run it in the first two weeks of July. The ATO, ASIC and RevenueSA publish most indexed amounts in June and July, and some later in the year. Expect to run steps 4 and 5 again in September, and again whenever `scripts/law_watch.py` reports a change (step 12).

## Step 0. Set up

1. Read `CONVENTIONS.md`, `docs/STATUS.md` and the newest `docs/PROGRESS-*.md`.
2. Work on a branch, in a worktree under `.claude/worktrees/`, never on the primary checkout. Replace `NEW` with the year label (for example `2028-29`) and `BASE` with the branch that holds the latest merged work. That is `main` once the previous release is merged; until then use the release branch the project owner names (for example `goal/v0.3`). Check first that `BASE` already has the `PREV` rates file (`git ls-tree --name-only BASE data/rates/`). On the 2027-28 dry run `main` had no 2027-28 file.

```
git worktree add .claude/worktrees/july-NEW -b july/NEW BASE
cd .claude/worktrees/july-NEW
```

3. Confirm the starting state is green.

```
scripts/check_all.sh
```

Expected: six lines, each starting with `PASS` (pytest, validate_rates, validate_holidays, lint_skills, lint_refusals, lint_risk_flags), and exit code 0. If not, stop and report; do not build on a red base.

Needs the project owner: no.

## Step 1. Create the NEW rates file by mirroring PREV

How the 2027-28 file was built (commit `a73e7f9`; see `git log -- 'data/rates/2027-28*'`): the base file and 17 overlays under `data/rates/2027-28.d/` (the same 17 files as 2026-27) mirror the keys of 2026-27, with the deliberate differences described after the copy step below. Figures that were legislated or published by the compile date are `VERIFIED`. Everything else is `SUSPECT`, `value: null`, with `checked_at`, the URL that was checked and a note saying what the page did and did not publish. Nothing was indexed forward.

Do the same for `NEW`:

1. Copy the layout.

```
cp data/rates/PREV.yaml data/rates/NEW.yaml
mkdir data/rates/NEW.d
cp data/rates/PREV.d/*.yaml data/rates/NEW.d/
```

   The copy fails `validate_rates.py` with `meta.income_year '<PREV>' does not match filename` until the next step is done. That is expected.

   Then compare the key names with `PREV`. The only differences should be the re-based calendar keys (step 4), history keys, keys for new law, and a `PREV` key left out on purpose (say why in your report).

```
diff <(cat data/rates/PREV.yaml data/rates/PREV.d/*.yaml | grep -E '^  [a-z_0-9]+:$' | sort) \
     <(cat data/rates/NEW.yaml data/rates/NEW.d/*.yaml | grep -E '^  [a-z_0-9]+:$' | sort)
```

   For the 2027-28 file this shows: the GIC and SIC quarter keys and the PHI April rebate key moved to 2028; history keys `concessional_cap_2026_27` and `nonconcessional_cap_2026_27` added; new-law keys added (CGT reform, working Australians tax offset, and similar); and `state.sa.payroll_tax_december_return_due_yyyymmdd` left out because RevenueSA has published no 2027-28 table (the calculator then uses the ordinary due date and warns). A `PREV` key that is missing from `NEW` for any other reason is a defect: add it as null, `SUSPECT`, with `checked_at`, or record why it went.
2. In `NEW.yaml` set `meta.income_year`, `meta.start`, `meta.end`, `meta.compiled` (today) and `meta.fbt_year_ending`. Overlays carry no `meta` block.
3. Rewrite the header comment at the top of each file: the `As at` date, and the sentence on what is VERIFIED.
4. For every figure, in the file and each overlay, decide one of three outcomes. Read the primary page named in `source` (or find the successor page). Primary sources only (`CONVENTIONS.md` section 1).
   - The `NEW` value is published or legislated and you read it: set `value`, `status: VERIFIED`, `source` (the exact page), `as_at` (today). Put the reading in `notes`.
   - It is not published: set `value: null`, `status: SUSPECT`, `checked_at` (today), keep `source` as the page you checked, and say in `notes` what the page showed.
   - It is a statutory constant that does not change by year (a rate fixed in an Act, a penalty multiple): carry it over, and confirm it on the legislation compilation in force. Set `as_at` to today.
5. Do not carry any `PREV` value into `NEW` because "it is usually the same". A carried value needs a source that says it applies to `NEW`.
6. Calendar-named keys (step 4) are re-based, not copied.
7. One fact, one key. Do not add a key that duplicates one in the base file or an overlay. New law gets a new key with a name that says what it is.
8. Keep the domain overlays in step with the skills. If a skill has been added since last July, it may have an overlay under `PREV.d/`; it is copied with the rest.

Validate as you go.

```
uv run scripts/validate_rates.py
```

With no arguments it checks every rates file and overlay; given a file path it checks only that file and its overlays. Expected: `OK (0 errors)`, and a line per file and overlay giving counts by status. Common errors:

- `null value requires a note`: every null figure needs a note saying what the page showed.
- `null value requires checked_at`: the rule applies from `2026-27` onward, so every null in `NEW` needs the date its `source` URL was checked. Set `checked_at`.
- `null value requires status SUSPECT`: null is only allowed with `SUSPECT`.
- `already defined in base file`: an overlay key collides with the base. Delete the duplicate.
- `meta.income_year ... does not match filename`: fix `meta`.
- Missing required domain or key: `validate_rates.py` lists them; add them.
- Bracket lists: `from` and `to` must join, rates run between 0 and 1, and `base` must match the ATO's rounded base within a dollar or so. Dated series (for example quarterly rates) need `from`, `to` and `rate`, in order, with no overlap.

Needs the project owner: yes, for any figure you derived by formula rather than read from a primary page (for example a threshold worked out from a published indexation factor). Do not set such a figure `VERIFIED`. Record the working in `notes`, set `SUSPECT` with the value, and list it in your report so the project owner approves or rejects it. Figures read straight off a primary page do not need approval.

## Step 2. Re-check PREV's SUSPECT figures

Before promoting anything in `NEW`, list what is still open in `PREV`.

```
grep -c "status: SUSPECT" data/rates/PREV.yaml data/rates/PREV.d/*.yaml
grep -n -B3 "status: SUSPECT" data/rates/PREV.yaml data/rates/PREV.d/*.yaml | grep -E 'yaml-[0-9]+-  [a-z_0-9]+:$'
```

The first gives the count per file. The second lists the key of every `SUSPECT` figure with its file and line number (for 2026-27 it lists 29 keys: 16 in the base file and 13 in `au_indonesia.yaml`). It includes a `SUSPECT` figure that has a value (a conflict or stale figure), which a search for `value: null` would miss. Open each one to read its `source`, `checked_at` and `notes`.

For each, follow step 3. `PREV` is now the current year, so most of its remaining unknowns should have been published by July.

Needs the project owner: no.

## Step 3. Promote SUSPECT figures to VERIFIED

Do this in step 1 for `NEW`, in step 2 for `PREV`, and again whenever a source publishes. The pages to check, by the figure's domain. Use the `source` URL already on each figure first; these are where to look if it has moved.

| Figures | Publisher | Where to look |
|---|---|---|
| Resident and foreign resident rates, offsets, Medicare levy and its low-income thresholds, MLS, HELP repayment thresholds, home office fixed rate | ATO, Treasury, legislation.gov.au | ATO individual income tax rates page; Medicare levy thresholds page; ATO home office expenses page; Income Tax Rates Act 1986 and the Income Tax Assessment Regulations compilations |
| Super caps, transfer balance cap, SG rate, LISTO, Div 293 and Div 296 | ATO, legislation.gov.au | ATO key superannuation rates and thresholds page; SGAA 1992 and ITAA 1997 compilations |
| PAYG withholding schedules, STSL schedule | ATO | ATO tax tables and schedules pages |
| FBT rates, gross-up rates, statutory formula, cents per km, thresholds | ATO | ATO FBT rates and thresholds page; FBT rulings for the year |
| GIC and SIC quarterly rates | ATO | ATO GIC rates and SIC rates pages |
| Penalty unit | ATO, legislation.gov.au | Crimes Act 1914 s 4AA; the ATO penalties pages |
| ASIC annual review, registration, late and special purpose fees | ASIC | The ASIC information sheet for the new financial year (see the `source` URL on the existing ASIC figures) |
| SA payroll tax, land tax scales and thresholds, stamp duty, ReturnToWorkSA amounts | RevenueSA, SA legislation, ReturnToWorkSA | RevenueSA rates and thresholds pages; the register page on rtwsa.com |
| NSW payroll tax figures kept for cross-checks | Revenue NSW | The Revenue NSW payroll tax rates page |
| Minimum wage and award-linked amounts | Fair Work Commission | The FWC annual wage review decision |
| Company, small business and CGT constants | legislation.gov.au, ATO | Compilations of the relevant Act; the ATO page for the concession |

How to promote one figure:

1. Open the primary page. Read the value for the right year. Do not use a firm, news or blog page as the citation; use it only to find the primary page.
2. Set `value`, `status: VERIFIED`, `source` (the page you read), `as_at` (today). Remove `checked_at` if present (it belongs to null figures; the validator allows it on others, but it is stale once a value exists).
3. In `notes`, write what you read, the page's own "updated" date if it shows one, and the statute or instrument reference.
4. If a page shows a different value from the file, stop. A primary source contradicting a `VERIFIED` figure that evals rely on is a stop condition in `GOAL.md` (section "Stop conditions"); treat it as one even if a later goal file has replaced it. Record both sources and report to the project owner.
5. If a page still does not publish the figure, leave `value: null`, `SUSPECT`, and set `checked_at` to today. Update `notes` only if the evidence changed.
6. `SOURCE-CITED` figures (cited but not re-read) are promoted the same way once you read the page.

Some pages render in JavaScript and return nothing to a plain fetch. If a page looks empty, use a browser to read it before you record it as "not published". Some pages (the ATO site, in the 2027-28 dry run) answer a plain fetch tool with HTTP 403; the Exa fetch tool read the same page. A failed fetch is never evidence that a figure is unpublished. The 2026-27 ASIC fees were found this way (see commit `a73e7f9`).

After each batch:

```
uv run scripts/validate_rates.py
uv run pytest tests/data -q
```

Expected: `OK (0 errors)` and all data tests pass. `tests/data/test_rates_2027_28.py` checks named figures against the primary sources; when a figure it expects changes status, update the test with the primary-source value, never with a value produced by our code (`CONVENTIONS.md` section 5).

Needs the project owner: only for the derived-by-formula case in step 1 and for any contradiction under item 4.

## Step 4. Re-base calendar keys

Some keys are named for a period, not a year. They do not copy across; they move.

1. Interest rate quarters. `penalties_interest.gic_quarterly` and `sic_quarterly` hold a dated series, and each income year's file has its own. While no quarter of `NEW` is published, the series in `NEW` is `value: null`, `SUSPECT`, with `checked_at` (the interest engine in `payg_lodgment.py` reads a null series in a year after 2026-27 as "the whole year is pending"). When the first quarter of `NEW` is announced, replace the null with a list holding that row, and add rows as they come. Per-quarter keys for periods whose rate is not yet out are named by calendar quarter (for example `gic_jan_mar_2028`), null and `SUSPECT`. In `NEW`, add the quarters from January onward of the calendar year that ends `NEW`, using the same pattern. In `PREV`, replace a null quarter key with a row in the `*_quarterly` list as the ATO announces it (about two weeks before the quarter starts), then delete the now-empty pending key. Rows must be in date order, with no overlap. Check the GIC and SIC pages for each. Add the new pending quarter names to `_PENDING_LABELS` (step 7).
2. Private health insurance rebate. Rebate rates change on 1 April, so the year has two rebate periods. In `NEW`, keep `phi_rebate_1jul_to_31mar_*` for the first period and name the April key for the year it starts in (the 2027-28 file uses `phi_rebate_from_2028_04_01`). Do not duplicate the previous year's April key: it belongs to `PREV` and stays there. Source: the ATO PHI rebate income thresholds and rates page.
3. FBT year. `meta.fbt_year_ending` and FBT figures follow the FBT year that ends inside `NEW` (1 April to 31 March). Update the `FBT` label wherever the year is named.
4. Keys with the year in the name (for example `..._2026_27`, `..._from_2027_28`). These carry history or a start date. When `NEW` passes the start date, check whether the key is still needed. Keep history keys the calculators read; remove none without a search for its users (`grep -rn '<key>' src tests skills`).
5. Keys that mark a future change (a start date in `NEW` or later) stay date-effective. Model them in the calculator, not in prose (`CONVENTIONS.md` section 3).

After editing:

```
uv run scripts/validate_rates.py
uv run pytest -q
```

Expected: no errors; the tests that fail now name the keys or years still hard-coded (step 7).

Needs the project owner: no.

## Step 5. Due dates

Due dates come from the rates overlays (`payg_lodgment`, `gst`, `fbt`, `state_sa`, `payroll-sg`) and the holiday data. Update them in `NEW` from the primary pages; do not compute a date and store it unread.

1. Lodgment program dates for `NEW`. Source: the ATO lodgment program and due dates pages for tax professionals and the registered agent lodgment program. Update the keys in `data/rates/NEW.d/payg_lodgment.yaml` and the base file. Where the ATO has published a program, `VERIFIED`; where not, null and `SUSPECT` with `checked_at`.
2. BAS due dates: the ATO BAS due dates page for quarterly and monthly lodgers, and the BAS agent concession dates. These are in `data/rates/NEW.d/gst.yaml` and `payg_lodgment.yaml` (the `bas_quarterly_due_day` and `quarterly_due_day` keys). Note that the ATO states the quarterly and agent dates for the year on the page; read the year's table, not last year's.
3. FBT: return lodgment and payment dates for the FBT year ending inside `NEW`, from the ATO FBT lodging page. Key `fbt.return_due_date` and its siblings in `NEW.d/fbt.yaml`. Where a date falls on a weekend the calculators roll it using the holiday data; store the date as published or as fixed by the statute.
4. SA payroll tax return and payment dates (RevenueSA publishes a table for the year, including any December extension), and SA land tax dates. Keys in `NEW.d/state_sa.yaml`.
5. Payday Super timing (the quarter-end-day rules and business-day counts) sits in `NEW.d/payroll-sg.yaml`. Re-read the ATO Payday Super payment deadlines page.
6. GIC and SIC quarter dates are in step 4.

Then check the calculators end to end.

```
uv run pytest tests/unit/test_gst.py tests/unit/test_payg_lodgment.py tests/unit/test_fbt.py tests/unit/test_state_sa.py tests/unit/test_business_days.py tests/unit/test_payroll.py -q
```

Expected: pass. If a test fails because a due date moved, check the test's stated source before changing it. Change an expectation only when it is proven wrong against a primary source, and note the correction in the test (`GOAL.md` guardrails).

Needs the project owner: no. Lodgment or registered-agent questions that arise (for example a client deferral) are out of scope; escalate them.

## Step 6. Holidays

Data: `data/holidays/au.yaml`. Rules and the regimes (Commonwealth tax and SA state tax): `docs/research/due-dates-public-holidays.md`. Validator: `scripts/validate_holidays.py`. Loader: `src/au_tax/holidays.py`. Dates outside `meta.range_start` to `meta.range_end` are refused (`AU-GEN-004`), so the range must cover `NEW`.

1. Extend the range by one income year.
   - `meta.range_end` to 30 June at the end of `NEW`; `meta.compiled` to today.
   - `meta.income_years` to the full list, in order (the validator requires the exact list).
   - Update the `# Australian public holidays, ...` header comment.
2. Add one row per holiday per jurisdiction for `NEW`, in date order, using the schema in the file header (`date`, `weekday`, `name`, `jurisdictions`, `status`, `source`, `as_at`; `part_day` and `part_day_from` for Christmas Eve and New Year's Eve). Scope is whole-State or whole-Territory days only. Excluded: local or regional days, bank-only days and Tasmanian public-service-only days (see the file header).
3. Sources, per jurisdiction: each government's own public holidays page for the year; where none is published yet, the statute that fixes the date (NSW Public Holidays Act 2010; WA Public and Bank Holidays Act 1972; ACT Holidays Act 1958; Tasmania Statutory Holidays Act 2000; SA Public Holidays Act 2023 for SA proclamations). The Fair Work Ombudsman page for the year is a fallback for the Commonwealth pool. `VERIFIED` only for a date read on a primary page or fixed by the cited statute.
4. Substitute and additional days (for example when Christmas Day falls on a weekend) are separate rows with the name the State uses. Names must be in the validator's known list; a new name needs a calendar rule added to `scripts/validate_holidays.py` (`_build_rules` or `GENERIC_RULES`) and a test.
5. Extend the ATO first-business-day table (`ato_first_business_day_table`) with the rows the ATO publishes on its "lodgment and payment dates on weekends or public holidays" page for the new period. The validator checks each row against the holiday rows. If a printed row disagrees with the statutory definition, keep the definition's date, record the `discrepancy` on the row, and add a test (there is one for 25 Sep 2026).
6. Unresolved holidays. The `unresolved:` list holds days that are not yet declared or that depend on a pending law change. Each has a null date, `SUSPECT`, `checked_at`, and `expected_month` or `candidate_dates`. On every run:
   - Re-read each row's `source`. If the date is now declared, move it into `holidays:` as a `VERIFIED` row and delete it from `unresolved:`.
   - If the pending law has passed or lapsed, resolve it the same way and update the regime notes and `docs/research/due-dates-public-holidays.md` section 4.
   - If still open, update `checked_at` and `notes` only.
   - Rows open when this runbook was written: the Victorian Friday before the AFL Grand Final in September 2027; and WA Labour Day and WA Day for 2028 (candidate dates on the current law versus the pending amendment bill, which would move the WA days from 1 January 2028). Check the WA Parliament bills page and the WA Government public holidays page.
   - Add a new `unresolved:` row for any `NEW` holiday that is not yet declared (typically the Victorian AFL Friday, WA dates, and any State that publishes the next year late).
   - A due date that touches a candidate date must behave as a draft (`AU-GEN-001`); one with no candidate date behaves as unpublished (`AU-GEN-003`). Do not change that behaviour here.
7. Proclamations and ministerial orders can add or move holidays after you finish. Re-check in September and after `law_watch.py` reports a change.

Validate and test.

```
uv run scripts/validate_holidays.py
uv run pytest tests/data/test_holidays.py tests/unit/test_business_days.py -q
```

Expected: `OK` with counts by income year including `NEW`, and passing tests. The validator also checks that every jurisdiction has holidays in every income year in range, and that the common holidays (New Year's Day, Australia Day, Good Friday, Easter Monday, Anzac Day, Christmas Day) are present for every calendar year in range. Add regression tests in `tests/data/test_holidays.py` for the new Easter, the new Christmas and New Year run, and one SA-only holiday, with expected dates read from the ATO table or the State page, not from our loader.

Also search for text that names the range.

```
grep -rn "30 Jun 2028\|1 Jul 2025 to" src skills docs README.md data/refusals data/holidays | grep -v "^docs/eval-results"
```

In the grep, use `PREV`'s old `range_end` date and `range_start` date in place of `30 Jun 2028` and `1 Jul 2025`. Update the range wherever it is quoted. Places found for the 2025-26 to 2027-28 range: the holiday-list description in `src/au_tax/calculators/payroll.py`, the trigger text of `AU-GEN-004` in `data/refusals/au.yaml`, the header of `data/holidays/au.yaml`, and `docs/research/due-dates-public-holidays.md`. The grep is limited to `data/refusals` and `data/holidays` because `data/rates/` notes quote payment periods that look the same and are not the range.

Needs the project owner: no.

## Step 7. Code and tests that hard-code year ranges

Adding `NEW` does not make every calculator use it. Find each hard-coded year.

```
grep -rnE '"20[0-9]{2}-[0-9]{2}"' src
grep -rnE "20(27|28|29)" src
grep -rnE "20(27|28|29)-[0-9]{2}|\b20(28|29)\b" tests
grep -rn "no 20[0-9][0-9]-[0-9][0-9]" skills docs README.md
grep -rnE "2028-29|onwards|and later" skills hooks README.md
```

In the last grep, use the year after `NEW` in place of `2028-29`. It finds the "no data from this year on" statements in skill prose.

Known places when this runbook was written (the greps are the source of truth, not this list):

- `src/au_tax/calculators/payg_lodgment.py`: the year loop in `_interest_periods` (rate rows are read from a fixed list of income-year files), `_PENDING_LABELS` (pending GIC and SIC quarters by name), and `_penalty_unit` (chooses the rates file by the failure date). Add `NEW`, and the new pending labels from step 4.
- `src/au_tax/calculators/cgt.py` and `individual.py`: the 1 July 2027 reform date is fixed by law; check that events on or after 1 July of `NEW` read `NEW` figures, and that events in the year after `NEW` refuse cleanly (`AU-GEN-003`).
- `src/au_tax/calculators/payroll.py`, `super_contrib.py`, `company.py`, `rental.py`, `crypto.py`: year-specific branches and docstrings ("for 2025-26 or 2026-27"). Docstrings are tool descriptions the model reads, so update the year lists.
- `src/au_tax/calculators/state_sa.py`: example strings and any year-dependent date logic.
- `tests/conftest.py`: the fixture `synthetic_post_2027_cpi` makes `2028-29` resolve to a copy of the 2027-28 data so a sale in 2028-29 can be tested before that file exists. Once `NEW` is 2028-29 the alias hides the real file; remove it or move it to the first year after `NEW`.
- Tests that use "the first year with no rates file" as a refusal case. When this runbook was written they use `2028-29` (`tests/unit/test_rental.py`, `tests/unit/test_state_sa.py`, `tests/unit/test_cgt.py`, `tests/unit/test_crypto.py`, `tests/unit/test_wiring_2027_28.py`; `grep -rn "2028-29" tests` is the source of truth). Once `NEW` is that year, they will pass for the wrong reason or fail. Move each to the first year after `NEW`. Keep a test that proves a missing year returns `AU-GEN-003` and never a guessed number.
- `tests/data/test_rates_2027_28.py`: the pattern for a per-year rates test. Add `tests/data/test_rates_NEW.py` with the legislated figures you set `VERIFIED`, expected values from the primary sources named in each figure.
- Skill prose that says a year has no data (when this runbook was written: `skills/cgt/SKILL.md` and `skills/crypto/SKILL.md` ("2028-29 onwards"), `skills/fbt/SKILL.md` ("FBT2028 and later"), and the year lists in `skills/individual-tax/SKILL.md` and `skills/short-stay-accommodation/SKILL.md`). Update to say which years have data, by year label, and keep the "refuses with `AU-GEN-003`, do not extrapolate" wording. No dollar amounts, percentages or day counts (`scripts/lint_skills.py` will reject them). Also check `skills/rates-lookup/SKILL.md`, `hooks/session-context.json` and `README.md`.
- `src/au_tax/mcp_server.py` and `src/au_tax/cli.py`: example year strings only; update for tidiness.

For each place, change the code to read the year from the figures (`figures.income_year`) or from the event date, not from a list. Use test-first: write the failing test with an expected value from a primary source, then change the code (`CONVENTIONS.md` section 5). Do not compute expected values by running our own code.

Run:

```
uv run pytest -q
```

Expected: all pass (1718 on the 2027-28 branch). Report the count in step 11.

Needs the project owner: only if a change needs a design choice (for example how a calculator should treat an event in a year with no file). Otherwise no.

## Step 8. Glossary, refusals and risk flags

1. If step 6 or 7 added a refusal code, add it to `data/refusals/*.yaml` first, then use it (`CONVENTIONS.md` section 6).
2. If a law change added a risk point, add it to `data/risk_flags/*.yaml`.
3. If a new term entered skill prose, add it to `docs/GLOSSARY.md`, and any banned synonym to `data/glossary_banned.yaml`, in the same commit.
4. If a statutory constant appears in skill prose, add it to `data/lint_allowlist.yaml` with a reason.

Needs the project owner: no.

## Step 9. Run all checks

```
scripts/check_all.sh
```

Expected: six lines, all `PASS` (pytest, validate_rates, validate_holidays, lint_skills, lint_refusals, lint_risk_flags), exit code 0. On a `FAIL` the script prints the last 25 lines of that check. Fix and rerun; do not proceed to evals on a red run.

Needs the project owner: no.

## Step 10. Rerun the evals

Evals run from a worktree, never from the main checkout while `.claude/worktrees/` exists. They use a Claude subscription. There is no dollar budget, but the subscription's session and weekly limits bind.

Command: `scripts/run_evals.sh [claude plugin eval flags]`. It grants every calculator tool by name and writes `.eval-results/<stamp>/result.json` (git-ignored). Environment: `EVAL_MAX_COST` (runaway guard in USD, default set in the script; set it to about twice the expected run) and `EVAL_THRESHOLD` (default 0.8).

Flag rules:

- `--tag <skill-slug>`: every case is tagged with its skill slug. This is the way to run one skill. Add `-j 3` for parallelism.
- `--case <glob>`: a glob on the case's folder name (no path, no `slug/` prefix; the usage comment at the top of `scripts/run_evals.sh` shows a `slug/*` example that does not match this). Use it to rerun a single case, and check the filter matches something before a long run.
- `--runs N`: runs per case. `--runs 1` for iteration; the release gates use 2 (and 3 to check a flaky case).
- `--ablation none`: one arm, with the plugin only. About half the cost. Use it for iteration and for regression checks where no delta is needed.
- Default (two arms, with and without the plugin): use it whenever a delta matters, and for the record of deltas.

Order:

1. Skills whose data or code changed: `scripts/run_evals.sh --tag <slug> --runs 1 --ablation none -j 3`. Start with the numeric and trap cases for the years affected (year-boundary and "no data for that year" cases).
2. Fix by cause, in this order of suspicion. Evidence first.
   - Skill defect: the skill prose or tool use is wrong. Fix the skill.
   - Grader defect: the grader crashed or the rubric is ambiguous. Inline regex flags crashed graders in v0.3; use the `flags` field. Fix the grader and record why in the grader.
   - Expectation defect: the expected value is wrong. Change it only when proven wrong against a primary source, and document the correction in the grader.
   - Eval expectations that quote a year's figures or "no data yet" text will fail once `NEW` exists. Update them from the primary source.
3. Then the whole plugin: `scripts/run_evals.sh --runs 2 --ablation none`, and the integration cases two-arm (`--tag integration --runs 2`).
4. Summarise: `uv run scripts/eval_summary.py .eval-results/<stamp>/result.json`. It prints per-case scores, and evidence for failures.

**Session-limit rule.** A result whose graders failed with "session limit" is invalid, not failed. Discard it, note it in the progress file under invalid runs, wait for the reset, and rerun. Never triage it as a defect. If the weekly limit is hit, stop, write down what is done and what is left, and resume after the reset.

Save results. For every valid run you cite:

```
mkdir -p docs/eval-results/<label>
gzip -c .eval-results/<stamp>/result.json > docs/eval-results/<label>/<stamp>.result.json.gz
```

`<label>` is the skill slug for a per-skill run, or the release or update name (for example the `NEW` income year) for a full run. Follow the existing folders in `docs/eval-results/`.

Bars to report against (`GOAL.md` and `CONVENTIONS.md` section 10): with-plugin score at least 0.9 on numeric cases and 0.8 overall per skill; positive mean delta over baseline in two-arm runs; no skill falls below its previous recorded score by more than a small margin. Any case that splits across runs is root-caused, not rerun until it passes.

Needs the project owner: yes, before starting the full run, because it draws on subscription limits and the owner may want it timed around other use. The per-skill iteration runs do not need approval.

## Step 11. Update STATUS

Edit `docs/STATUS.md` (rewrite the heading to name the update):

1. Per-skill table: cases, score, mean delta, and run id, from the saved results.
2. Checks line: pytest count, and the status of the five validators and linters.
3. Open items: every figure still `SUSPECT`, every `unresolved` holiday, every skill blocked, with what would close each.
4. Eval usage: the API-equivalent cost estimate from the results, labelled as an estimate.
5. Expectations corrected against primary sources this run, each with its source.
6. Add a dated line to the newest `docs/PROGRESS-*.md`, including any invalid runs.

State results as they are. Do not tidy a miss into a pass.

Needs the project owner: no. Merging to `main` and pushing are the project owner's (or the orchestrator's) call.

## Step 12. Law-change watch

`scripts/law_watch.py` checks a fixed list of primary-source pages (ATO rates and codes pages, legislation.gov.au compilations, RevenueSA, ASIC fees, Fair Work Ombudsman holidays, and a few others) against stored fingerprints and reports what changed. The list is `data/law_watch/pages.yaml`; each entry's `why` names the figure keys and skills that depend on the page. Fingerprints are `data/law_watch/fingerprints.json`. Full detail: `docs/law-watch.md`. It is an alert, not a source of figures: nothing it reports is a verified figure until you have read the primary page.

Commands (run from the repo root; the network is used, one polite request per page, about 3 seconds apart per host, whole run capped at 15 minutes by default):

```
uv run scripts/law_watch.py list                          # every watched page; [no fingerprint] marks pages with no baseline yet
uv run scripts/law_watch.py check                         # all pages; exit 1 if any changed or is new, 0 otherwise
uv run scripts/law_watch.py check --only legis-itaa-1997  # one page (an id or a glob such as 'legis-*'; repeatable)
uv run scripts/law_watch.py check --only 'ato-super-*'    # a family of pages
uv run scripts/law_watch.py check --only <id> --update    # accept the current page as the new baseline
uv run scripts/law_watch.py check --only <id> --offline saved/   # read saved/<id>.html (a page saved from a browser)
uv run scripts/law_watch.py check --max-seconds 300 --timeout 20 # tighter caps if the network is slow
```

Reading the report. One line per page, then a summary line (`N pages: a unchanged, b changed, c new, d error (e blocked)`):

- `unchanged`: nothing relevant moved. A `note:` under it means a "last updated" date moved but the text did not; ignore unless the date matters.
- `CHANGED`: the extracted text (or, for legislation.gov.au, the compilation id or effective date) differs. The report shows what moved (for example `compilation_id: C2026C00400 -> C2026C00500`), the added text blocks, `why watched` (the keys and skills that depend on the page) and the URL. Old text is not stored, so removed text is only counted.
- `new`: no stored fingerprint yet. That is a missing baseline, not a change. It only appears when the page fetched cleanly. At the time of writing 78 of the 96 pages have no fingerprint, but they are the ones the sites refuse to scripted requests, so a plain `check` reports them as `error: blocked` (75) or `error: TimeoutError` (3), not `new`. A real run on 2026-09-30 gave 18 unchanged, 0 changed, 0 new, 78 error (75 blocked) in about 4 minutes, so expect that until a baseline is saved from a browser (item 3).
- `error: blocked (...)`: the site refused, served a bot challenge, or returned an empty script-rendered page. This is never a change and the tool never works around it. Check the page by hand in a browser (below).
- `error: http 404`, `error: TimeoutError (...)`, `error: URLError (...)`, `error: time limit (...)`: the page moved, the network failed or timed out, or the overall cap was reached. Rerun those pages with `--only`, or fix the URL in `pages.yaml`.

What to do per page:

1. `CHANGED`: open the URL, read what changed against the keys in `why`. A fingerprint change is a prompt to look, not proof a figure moved (a page can change its wording).
   - A figure changed: edit the rates file (steps 1 and 3; `VERIFIED` only when read on the primary page, with `source` and `as_at`), then rerun steps 9 and 10 for the skills that use it. A null or `SUSPECT` figure named in `why` may now be published: check it.
   - A rule changed (a new compilation of an Act, a ruling withdrawn): read the primary source, update the calculator or skill (step 7), add a date-effective rule where the law has a start date, and add or adjust an eval case as a trap case. Follow the skill's `references/sources.md`.
   - Nothing relevant changed: accept it.
   - Then `uv run scripts/law_watch.py check --only <id> --update` to record the new baseline, and commit `data/law_watch/fingerprints.json` with the rates change.
2. `new`: after you have read the page, `check --only <id> --update` records the baseline. A first baseline is not a review of the figures on the page.
3. `error: blocked`: open the page in a browser, save the HTML as `saved/<id>.html` (any folder; do not commit it), then `check --only <id> --offline saved/`, and add `--update` to record it. Do not script around the block. If a page stays blocked, say so in the hand-back and check it by hand each run.
4. Run `check` at the start of this runbook and again before step 13. Exit code 1 means a page changed or is `new`. Errors (blocked, timeout, 404) do NOT change the exit code: a run with 78 blocked pages and nothing else exits 0. Read the summary line, or add `--strict` (exit 3 if any page errored), so blocked pages are not mistaken for a clean pass.
5. `--offline saved/` needs the file to be named `saved/<id>.html` exactly (the `<id>` from `list`), and a missing file gives `error: no offline fixture`. That path has been exercised only for the missing-file error; it has not been run against a real saved browser page.

Do not edit `fingerprints.json` by hand.

Needs the project owner: yes to schedule it. Running it on a timer (cron, launchd, a scheduled agent) needs the project owner's approval, and none is set up; scheduling is not part of this runbook. Running it by hand does not need approval.

## Step 13. Hand back

1. Commit in small commits by concern: rates data, holidays data, code and tests, skills prose, evals, STATUS. End each message with the co-author trailer given for the session.
2. Do not merge. Report to the project owner:
   - branch and last commit;
   - figures promoted, figures still `SUSPECT` (with `checked_at`);
   - figures derived by formula, awaiting project owner approval (step 1);
   - holidays still `unresolved`;
   - the `check_all.sh` result and eval run ids, with any invalid runs;
   - anything you could not resolve, with the evidence.
3. Registered-agent framing stays. Every output remains a working paper for review by a registered tax agent (BAS agent for BAS matters). Nothing here is reviewed until `data/reviews/` says so.

## Step summary

| Step | What | Needs the project owner |
|---|---|---|
| 0 | Worktree, branch, green baseline | No |
| 1 | New rates file and overlays, mirroring PREV | Only to approve formula-derived figures |
| 2 | List PREV's open SUSPECT figures | No |
| 3 | Promote SUSPECT to VERIFIED from primary pages | Only on a contradiction |
| 4 | Re-base calendar keys (GIC/SIC quarters, PHI rebate, FBT year) | No |
| 5 | Due dates (lodgment program, BAS, FBT, SA, Payday Super) | No |
| 6 | Holidays: extend range, resolve unresolved rows | No |
| 7 | Hard-coded year ranges in code, tests and skill prose | Only for a design choice |
| 8 | Refusals, risk flags, glossary | No |
| 9 | `scripts/check_all.sh` | No |
| 10 | Eval rerun, save results | Yes for the full run (subscription limits) |
| 11 | Update STATUS and PROGRESS | No |
| 12 | Law-change watch | Yes to schedule it |
| 13 | Hand back; no merge | Merge and push are the project owner's |
