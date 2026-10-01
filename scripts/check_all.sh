#!/usr/bin/env bash
# Run all quality checks. Exits non-zero if any fail.
cd "$(dirname "$0")/.." || exit 1
fail=0
run() {
  local label="$1"; shift
  local out
  if out=$("$@" 2>&1); then
    echo "PASS $label: $(echo "$out" | tail -n 1)"
  else
    echo "FAIL $label: $(echo "$out" | tail -n 1)"
    echo "$out" | sed 's/^/    /' | tail -n 25
    fail=1
  fi
}
run pytest uv run pytest -q
run validate_rates uv run scripts/validate_rates.py
run validate_holidays uv run scripts/validate_holidays.py
run lint_skills uv run python scripts/lint_skills.py
run lint_refusals uv run python scripts/lint_refusals.py
run lint_risk_flags uv run python scripts/lint_risk_flags.py
exit $fail
