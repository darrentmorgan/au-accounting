---
name: verify-individual-settlement
description: Verifies bounded individual income tax and settlement invariants after changes to individual.py, settlement.py, their input models, rate schedules or figure loading. Use for offset bounds, decreasing tax, PHI reconciliation, settlement balance or refusal safety regressions.
---

# Verify individual tax and settlement

## Scope and inputs

Run from the repository root after changing the covered functions or their rate
figures. Use synthetic inputs only. This is a developer verification skill;
`skills/` remains reserved for the tax-domain plugin skills.

The property is that non-refundable offsets cannot create a refund, base tax
cannot fall as taxable income rises under fixed offset inputs, and each confirmed
settlement balances exactly in cents. A violation can produce an incorrect tax
liability, refund or claim that unresolved inputs constitute a final settlement.

This is deterministic bounded execution of **real Python calculator code**, not
an SMT proof or a separate arithmetic model. It exhausts the documented finite
products and adds seeded joint cases. It does not exhaust every possible input.
No external verifier or new dependency is needed: use the Python version and
packages specified by `pyproject.toml` and `uv.lock` (Python 3.13 or later).

## Procedure

1. Read this coverage record and inspect changes since the sync commit:

   ```bash
   git diff 7289aa737402747a9894853ebe63c31e6a5009af -- src/au_tax/calculators/individual.py src/au_tax/calculators/settlement.py src/au_tax/figures.py data/rates scripts/verify_invariants.py tests/unit/test_invariants.py
   ```

2. Check that the actual function paths, output keys, published figures and bounds
   below still describe the change. The tool is `individual_tax_settlement`, but
   its source module in this repository is **`settlement.py`**, not
   `individual_settlement.py`.
3. Run:

   ```bash
   uv run python scripts/verify_invariants.py
   uv run pytest tests/unit/test_invariants.py -q
   ```

   Exit 0 prints a single PASS line with case counts, income bounds, seed and
   elapsed time. Exit 1 prints the first counterexample with year, income, rule,
   expected and actual values. For seeded cases, the printed seed and case index
   reproduce the case by rerunning the same version. Cases are ordered; the
   first failure is a small reproducible example, not a globally minimized input.

4. Treat a failure in real calculator terms: inspect the supplied inputs, raw
   versus reported amounts, the relevant function and that year's figure keys.
   Do not relax an identity, add a tolerance or replace a year's missing figures
   to make the run green. Distinguish a generator/model error from a product
   finding and report a product finding before changing financial semantics.
5. If an intended change alters a contract or domain boundary, update the
   generator, assertions and this coverage record together. Keep mutation tests
   that demonstrate the new checks can fail. For a new assertion, also try a
   scratch mutation in its actual calculator function and restore the exact
   source in `finally`; rerun the original to confirm restoration.
6. Run the complete gate command before committing:

   ```bash
   ./scripts/check_all.sh
   ```

   The seventh gate is `verify_invariants`. Report failures and scope limitations
   honestly; never claim all gates passed when the verifier found a bug.

## Coverage record

Sync commit: `7289aa737402747a9894853ebe63c31e6a5009af` (calculator, figure-loader, verifier and tests
reviewed together; all seven gates passed).
Advance this to a real commit only after reviewing the covered changes and
confirming that the checks and coverage record describe that commit. Do not move
it forward merely because a check happened to pass. After changes that skipped
verification, use pstack `/maintain-formal-verification-skill` to reconcile the
coverage before relying on the record.

| Real code | Checks |
| --- | --- |
| `individual.py`: `_income_tax`, `_lito` | Statutory LITO in `[0, max_offset]` and non-increasing; resident (one, six and twelve months), foreign and WHM base tax and tax less statutory LITO non-decreasing over each ordered grid. |
| `individual.py`: `_core`, `_wato`, `individual_income_tax` | Public applied LITO/WATO nonnegative, capped at their maxima and remaining gross income tax; reported `income_tax_after_offsets == max(0, round(gross_tax - lito - wato, 2))`; public gross/net monotonicity with fixed labour income. |
| `individual.py`: `_medicare_levy`, `_mls`, `_help` through settlement | Single Medicare boundaries, family shade-in including children, MLS single/family tiers, HELP repayment tiers and balance caps exercised in settlement; all exemption-day combinations in seeded cases are bounded to the public input domain. |
| `settlement.py`: `_phi` through `individual_tax_settlement` | PHI refundable/excess amounts nonnegative and mutually exclusive, entitlement less received equals refundable less excess; exact row sums, tier selection and per-row half-up rounding. |
| `settlement.py`: `individual_tax_settlement`, `_money` | Liability plus PHI excess; credits by type and sum; signed balance; refund and owing sign, mutual exclusion and exact net identity. |
| `settlement.py`: `_stop`, `_phi`, `individual_tax_settlement`; `Figures.get`, `Figures.draft` | Unmodelled inventory, mismatched PHI/franking years, foreign/WHM franking, draft tax/Medicare/WATO/PHI figures and unpublished Medicare/PHI cannot return a complete settlement. Draft probes alter a deep copy of actual rate data, never the cache or files. |
| `tests/unit/test_invariants.py` | CLI execution plus deliberately corrupt bounds, monotonicity, offset arithmetic, PHI, credits, liabilities, balance, outcomes and safety, including monkeypatching a real calculator. |

Bounds and assumptions:

- Base schedules: every rate-file year with VERIFIED resident, foreign, WHM and
  LITO schedules, currently 2025-26, 2026-27 and 2027-28. There is no 2024-25 file.
- Taxable income: zero through 500000, at a 1000 grid step, plus each statutory
  bracket/LITO/verified Medicare/MLS/HELP boundary and neighbours at minus/plus
  one dollar and one cent. Taxable income is floored by the actual calculator.
- Raw statutory LITO must decrease. **Applied** LITO may rise at low incomes as
  gross tax rises, so only its bounds and non-refundability are asserted there.
- Full low-income component/settlement coverage is 2025-26. Future-year resident
  public cases start at 100000, safely beyond the current-law Medicare screen,
  with full hospital cover and no HELP. Base helpers still cover low incomes.
  Missing figures are checked as refusals, never borrowed from another year.
- WATO starts in 2027-28: public resident sweeps hold net labour income at zero or
  500000. Low-income WATO execution with future unpublished Medicare is outside
  this bound; WATO at those incomes is not claimed proved.
- Published PHI: every period/age key (six in 2025-26, three in 2026-27), single
  plus family with zero, one or two children, every shifted tier boundary and
  neighbours, premium/received pairs `(0, 0)`, `(1000.05, 0)`, `(0.01, 2000.01)`.
  PHI income is a separately confirmed input and varies independently of taxable
  income. Eligibility and allocation are classified inputs, not inferred.
- Exhaustive credit products: withheld zero, 25348 or 500000.01; instalments zero
  or 1000.99; franking absent, zero or 1500.55; taxable income zero, 18200, 45001,
  100000 or 500000 in 2025-26 and the last two in later years.
- 512 additional joint cases use seed 20261026, taxable income within the same
  bound, PAYG withholding up to 500000, instalments up to 10000, one to six PHI
  rows, premiums up to 10000 and received rebates up to 5000 per row. They vary
  residency, cover, spouse/children, exemptions, add-backs, PHI and HELP caps.
- Accounting comparisons use exact Decimal cents without tolerance. The public
  offset identity uses the literal Python `round(..., 2)` expression. This does
  not prove legal correctness of the underlying schedules, full eligibility,
  every sub-cent input, unlimited income/rows/children, or an ATO cash refund.

## Passing state and mutation evidence

The original implementation rounded net tax from unrounded internal components.
At income 45001 in 2025-26, gross tax 4288.30 less reported LITO 324.99
incorrectly reported net tax 3963.32. The authorized fix in `_core` rounds gross
tax and offsets to their reported cents before subtracting, then rounds and floors
net tax at zero. This same net amount flows into total liability and settlement.
The verifier's exact identity and bounds are unchanged.

The real calculators now pass all 17489 cases: base 8540, public components
5278, boundary settlements 701, PHI 2268, credit products 162, seeded 512 and
safety 28. The standalone verifier takes approximately 1.4 seconds on the
validation machine; this is measured bounded execution, not a universal runtime
guarantee. All seven `./scripts/check_all.sh` gates passed, including 2090 pytest tests
and the verifier in 1.404 seconds. The domain skill lint still covers exactly
19 tax-domain skills; this developer skill is outside that directory.

Two actual-source scratch checks were performed with restoration in `finally`:

- Add one dollar to `_lito`'s return value. Observed exit 1:

  ```text
  FAIL LITO bounds: 2025-26 resident, months=1, income=0; offset 701.0 must be between 0 and 700
  ```

- Replace the fixed net calculation in `_core` with the original unrounded
  subtraction. Observed exit 1:

  ```text
  FAIL non-refundable offset balance: 2025-26 resident, income=45001, net_labour_income=0; expected 3963.31, got 3963.32
  ```

The fixed source was restored byte-for-byte and the verifier passed again.
`tests/unit/test_individual.py` also contains four independently computed cent
rounding regressions across all supported years, including WATO, total liability
and the withholding estimate. `tests/unit/test_invariants.py` has 31 passing tests,
including corruption probes and command execution. These do not substitute for
the real-source scratch evidence above.

## Output

State the command, pass/fail, actual case counts, covered years and bounds,
mutation evidence and any findings. Keep accounting amounts in cents. A pass
covers only these bounded sets. Commit changes only within the user's requested
scope and do not push unless instructed.
