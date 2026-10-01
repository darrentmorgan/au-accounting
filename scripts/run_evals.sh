#!/usr/bin/env bash
# Run plugin evals with the project's standard flags.
# Usage: scripts/run_evals.sh [extra claude plugin eval flags], e.g.
#   scripts/run_evals.sh --tag individual-tax --runs 1 --ablation none
set -euo pipefail
cd "$(dirname "$0")/.."
stamp=$(date +%Y%m%dT%H%M%S)
# LLM graders use Sonnet by default (EVAL_JUDGE_MODEL): the harness default (Haiku) split repeatedly on correct answers in v0.3.
# Grant every calculator tool by exact name (wildcards are not accepted by the eval runner).
tools=$(uv run --quiet python -c "from au_tax.registry import load_all; print(' '.join('mcp__plugin_au-accounting_au-tax__'+n for n in sorted(set(load_all())|{'list_figures','get_figure'}) if not n.startswith('zz_')))")
exec claude plugin eval . \
  --trust-plugin --allow-real-servers --allow-tools $tools \
  --no-publish --max-cost-usd "${EVAL_MAX_COST:-10}" --threshold "${EVAL_THRESHOLD:-0.8}" \
  --judge-model "${EVAL_JUDGE_MODEL:-sonnet}" \
  --output-dir ".eval-results/$stamp" --json ".eval-results/$stamp/result.json" "$@"
