# Claude Code Plugin Skills and Eval Research

Research date: 2026-09-29
Sources: code.claude.com/docs/en/, `claude plugin eval --help`, `claude plugin --help`

## 1. Agent Skills Authoring Best Practices

### SKILL.md Frontmatter & Structure
**Source:** https://code.claude.com/docs/en/skills.md

Required fields:
- `name`: skill identifier (kebab-case for skills within a plugin, can be any name for standalone skills)
- `description`: 1-2 line summary determining Claude's auto-invocation triggering (critical for discoverability)

Optional frontmatter fields:
- `disable-model-invocation: true` - prevents Claude from auto-invoking (explicit `/skill-name` only)
- `allowed-tools: [tool1, tool2]` - declares which tools the skill needs, gates access
- `experimental.multi-turn: true` - allows skill to carry state across multiple turns (newer feature)

Body content guidance:
- Skills have lazy-loading: only their body loads when used (unlike CLAUDE.md which always loads)
- Body should be minimal until needed (reference files instead of embedding large content)
- Progressive disclosure: put complex procedures in sub-files referenced from the body
- One-level-deep references work best; deeper nesting makes skills harder to follow

Description tuning for triggering:
- Description text drives Claude's decision to auto-invoke the skill
- Vague descriptions ("do work") won't trigger; specific ones ("Generate monthly owner payouts") will
- If Claude doesn't invoke a skill on natural phrasing, adjust `description` rather than the skill's instructions
- Test with `claude plugin eval . --case <case-name> --runs 1` to iterate quickly

### Bundling Python Scripts with Skills
**Source:** https://code.claude.com/docs/en/plugins/manifest-reference.md, plugin-evals.md

Script integration patterns:
- Scripts live alongside skills in the plugin directory structure
- Reference bundled scripts via `${CLAUDE_PLUGIN_ROOT}` in skill content or hooks
- Example: `"${CLAUDE_PLUGIN_ROOT}/scripts/process.sh"` resolves to absolute path at runtime
- Environment variables available to scripts: `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA`, `CLAUDE_PROJECT_DIR`

When to use scripts vs instructions:
- Use scripts for: complex logic, binaries, repeatable operations, non-Markdown tasks
- Use instructions for: guidance, multi-step procedures, decision points where Claude adds reasoning
- Hybrid approach: skill invokes script, skill narrates what script did

Error handling patterns:
- Script exit codes: 0 = success, non-zero = error
- Capture stderr for debugging; stdout for results
- Skills should verify script output before depending on it (e.g., check for expected files)
- Document required environment variables and tool dependencies in the skill body

### Degrees of Freedom & Naming
- Plugin skill names get namespaced: `/plugin-name:skill-name`
- Standalone skills (outside plugins) run as `/skill-name`
- Avoid generic names ("process-data"); use domain-specific names ("reconcile-owner-payments")
- Name reflects the outcome, not the mechanism (e.g., "generate-statement" not "run-reconciliation-script")

### Anti-Patterns to Avoid
- Over-long skill bodies: use sub-files, reference sections, progressive disclosure
- Descriptions that are too vague or don't mention the specific outcome
- Coupling multiple distinct workflows into one skill (should be separate skills)
- Assuming Claude knows context it doesn't have (spell out assumptions)

### Evaluation-Driven Development
- Start with `claude plugin eval init` to auto-propose test cases
- Write graders for both the outcome (llm grader) and the mechanism (tool_used grader)
- Iterate on skill description if tool_used fails but outcome is correct
- Test across models with `--model` to catch model-specific triggering issues
- Run evals in CI with `--threshold 0.8` for reasonable quality gates

### Testing Across Models
- Documented fact: skill triggering varies by model; test with target model
- Adjust description specificity if Claude 3.5 triggers differently than Claude 4
- LLM-judge graders are model-specific; test judge robustness with `--judge-model sonnet`
- For production, pin both the skill-executing model and the judge model in CI


## 2. Plugin Structure & Bundling

### Plugin Directory Layout
**Source:** https://code.claude.com/docs/en/plugins/create.md, manifest-reference.md

Standard layout (each directory optional):
```
my-plugin/
├── .claude-plugin/
│   └── plugin.json           # Required by Anthropic's directory; optional for local use
├── skills/
│   ├── deploy/
│   │   └── SKILL.md
│   └── check-status/
│       └── SKILL.md
├── agents/                    # Subagent definitions
│   └── reviewer.md
├── commands/                  # Legacy; prefer skills/ for new plugins
│   └── about.md
├── hooks/
│   └── hooks.json
├── .mcp.json                 # MCP server definitions
├── .lsp.json                 # LSP server configurations
├── bin/                       # Executables on Bash PATH (not for claude.ai/Cowork)
├── scripts/                   # Helper scripts bundled with plugin
├── output-styles/
├── themes/
├── monitors/
│   └── monitors.json
├── workflows/                 # Workflow .js files
└── evals/                     # Eval cases (default location)
```

Key files NOT in .claude-plugin/:
- All components go at plugin root, not inside .claude-plugin/
- Only plugin.json goes inside .claude-plugin/

### plugin.json Manifest Fields
**Source:** https://code.claude.com/docs/en/plugins/manifest-reference.md

Required:
- `name`: kebab-case identifier, namespaces all components

Metadata (optional but recommended):
- `version`: semantic version; when set, pins users to that version until it changes
- `description`: short explanation of what plugin provides
- `author.name`: required within author object; email/url optional
- `displayName`: shown in UI instead of name
- `defaultEnabled`: boolean, default true

Component declarations:
- `skills`: array of paths to skill directories, default scans `skills/`
- `commands`: path, array, or object map; replaces default `commands/` scan
- `agents`: array of agent .md file paths
- `hooks`: path to hooks.json or inline hooks object; merges with `hooks/hooks.json`
- `mcpServers`: path(s), bundle URL, or inline object; merges with `.mcp.json`

Experimental fields:
- `experimental.evals`: directory name for eval cases (default: "evals"); overridden by CLI `--eval-dir`
- `experimental.themes`: directory for theme JSON files
- `experimental.monitors`: path to monitors.json or inline array

Critical for eval integration:
```json
{
  "name": "accounting-tools",
  "experimental": {
    "evals": "evals"
  }
}
```

### Referencing Bundled Scripts in Skills
**Source:** code.claude.com and manifest-reference.md

Environment variables available in skill content:
- `${CLAUDE_PLUGIN_ROOT}`: absolute path to installed plugin version (changes on update)
- `${CLAUDE_PLUGIN_DATA}`: persistent data dir (~/.claude/plugins/data/<id>/), survives updates
- `${CLAUDE_PROJECT_DIR}`: project root directory

Example skill invoking a Python script:
```markdown
---
name: reconcile-payments
description: Reconcile owner payments against bank deposits
allowed-tools: [Read, Write, Bash]
---

I'll reconcile the payment data. Run this analysis:

${CLAUDE_PLUGIN_ROOT}/scripts/reconcile.py --input data.csv
```

For scripts, use `${CLAUDE_PLUGIN_ROOT}` for code/tools, `${CLAUDE_PLUGIN_DATA}` for caches/deps (persists across plugin updates).


## 3. Plugin Eval (`claude plugin eval`) 

### Exact Case Format

**Source:** https://code.claude.com/docs/en/plugin-evals.md, CLI help

Case directory structure:
```
evals/case-name/
├── prompt.md                 # frontmatter + prompt body
├── case.yaml                 # optional; adds context.* fields
├── graders/
│   ├── outcome.md           # llm or regex grader
│   └── skill-fired.md       # tool_used grader
└── fixtures/                 # optional; files referenced in mocks or history_file
```

### prompt.md Frontmatter Fields
All fields optional except `allowed_tools` often needed:

| Field | Default | Type | Purpose |
|-------|---------|------|---------|
| `schema_version` | "1.1" | string | Format version (auto-set) |
| `name` | directory name | string | Case identifier for --case filtering |
| `description` | | string | Human-readable purpose |
| `tags` | [] | array | Labels for --tag filtering |
| `runs` | 3 | number | Runs per arm (1-50) |
| `max_turns` | 10 | number | Max conversation turns (1-200) |
| `timeout_seconds` | 300 | number | Wall-clock timeout (1-3600 seconds) |
| `model` | default | string | Override model for this case |
| `allowed_tools` | [] | array | Tools case needs: Read, Glob, Grep, Skill, Agent, Bash, Write, Edit, WebFetch, WebSearch, etc. |
| `append_system_prompt` | | string | Text appended to system prompt |
| `env` | {} | object | Environment variables, keys must be EVAL_* pattern |
| `plugins` | auto-detect | array | Plugin directories under test; e.g., ["../.."] |

Example:
```yaml
---
name: owner-statement-generation
tags: [smoke, month-end]
runs: 3
max_turns: 15
timeout_seconds: 600
model: claude-sonnet-5
allowed_tools: [Read, Write, Bash, Skill]
env:
  EVAL_TEST_MONTH: "2026-09-01"
---

Generate owner payment statements for September 2026 from the provided data files.
```

### case.yaml Companion File
Optional; adds fields that prompt.md can't express:

```yaml
schema_version: "1.1"
name: revenue-reconciliation
tags: [core, bank-match]
context:
  scaffold_script: setup-repo.sh      # runs before prompt (only with --scaffold)
  history_file: prior-session.jsonl   # replays earlier conversation
  add_dirs: [fixtures, bank-data]     # directories Claude can read
execution:
  prompt: |
    Your prompt here...
  max_turns: 20
```

### Grader Types (6 Total)

**Deterministic graders (no model call, free):**

1. **regex**: Match pattern in output
   ```yaml
   ---
   type: regex
   pattern: "Total:\s+\$[0-9,]+\.[0-9]{2}"
   target: last_message           # or trace, files, {source: file, path: ...}, mock_calls
   match: contains                # or not_contains, "count:N"
   flags: i                        # case-insensitive
   ---
   ```
   - Passes when regex found in target (default target: last_message)
   - Good for structured output (CSV, JSON, numbers)

2. **tool_used**: Assert tool was called
   ```yaml
   ---
   type: tool_used
   tool: Skill
   input_match: '"skill"\s*:\s*"(?:[\w-]+:)?my-skill"'  # optional regex on JSON input
   min: 1
   max: 5
   ---
   ```
   - Passes when tool calls match count falls in [min, max]
   - For "must not call": min: 0, max: 0
   - Plugin skill example: tool: Skill, input_match on the skill name

3. **tool_order**: Assert precedence
   ```yaml
   ---
   type: tool_order
   before: { tool: Read, input_match: "requirements" }
   after: { tool: Write, input_match: "implementation" }
   ---
   ```
   - Passes when before tool call precedes after call

4. **file_exists**: Check for created files
   ```yaml
   ---
   type: file_exists
   path: "*.json"
   exists: true
   ---
   ```
   - Passes when glob matches file Claude created
   - Only counts files created during run, not pre-existing or modified-only

**LLM-judged graders (call judge model, costs tokens):**

5. **llm**: Judge model votes
   ```yaml
   ---
   type: llm
   criteria: |
     PASS if statement contains line-item breakdown with dates and amounts.
     FAIL if any line lacks a date or amount.
   focus: last_message            # or trace, files, {source: file, path: ...}, mock_calls
   weight: 2                       # optional; multiplier for scoring
   ---
   ```
   - Judge model votes 2-of-3 on rubric
   - Good for semantic assessment
   - Prefer deterministic graders for long outputs (LLM judges noisy on length)

6. **baseline**: Compare to reference transcript
   ```yaml
   ---
   type: baseline
   baseline_file: good-run.jsonl
   criteria: |
     PASS if at least as complete and accurate as baseline.
   ---
   ```
   - Compares run quality to saved baseline transcript
   - Rare; used to lock in acceptable behavior

### Scoring & Weights

- One run = one attempt at the prompt
- Default 3 runs per case per arm (with-arm: with plugin, without-arm: no plugin)
- Run score = mean of graders (weighted if you set `weight: N`)
- Case score = mean across its runs
- Pass threshold default 1.0 (perfect score); set `--threshold` to lower

### Baseline Ablation (With vs. Without Plugin)

**Source:** plugin-evals.md

Two-arm default behavior:
- WITH-arm: runs with plugin loaded (3 by default)
- WITHOUT-arm: runs with no plugin (same count) for comparison
- Delta = WITH score - WITHOUT score; positive means plugin helped

Graders excluded from scoring in two-arm mode (plugin-fired indicators only):
- All `tool_used: Skill` graders (can't pass without plugin)
- `tool_used` on mocked MCP tools when all are plugin-declared
- Any grader marked `arm: with-only`

Override exclusion:
- Set `arm: both` on a grader to score it in both arms (e.g., "must not invoke skill" check)
- Use `--ablation none` to run one arm only (halves cost, no baseline)

### Mocking MCP Servers
**Source:** plugin-evals.md

Layout:
```
evals/mocks/<server>/<tool>.md     # suite-wide mocks
evals/<case>/mocks/<server>/<tool>.md  # case-specific mocks override suite
```

Mock file example (fixed response):
```markdown
---
expect:
  title: string
  priority: [low, medium, high]
---

Created issue #4821: {{input.title}} at priority {{input.priority}}
```

Mock options:
- `expect:` - validates input; abort run if violated
- `error: true` - return body as error instead of result
- `type: agent` - small model answers from instructions (variable output)
- `{{input.<field>}}` - substitute from call input
- `{{file:fixtures/<name>}}` - insert fixture file

Agent mock with replay:
```yaml
---
type: agent
---

You are a GitHub API mock. Respond to issue creation calls...
```
- Agent mocks save recordings under `results/<ts>/mock-recordings/`
- Copy successful recordings to `.replay/<server>/` for deterministic replay in future runs

Real servers:
- `--allow-real-servers` - start plugin's real MCP servers for those without mocks
- `--mocks off` - ignore mocks, use all real servers

### Fixtures & Setup

In case.yaml:
```yaml
context:
  scaffold_script: setup.sh         # bash script runs before prompt (--scaffold flag required)
  add_dirs: [fixtures, test-data]   # directories readable during run
  history_file: prior.jsonl         # .jsonl transcript to continue
```

Scaffold script runs as you (not sandboxed), outside the eval session:
- Create fixture files, git repos, databases
- Only runs when you pass `--scaffold` (opt-in for trust)

### Running Evals

**Source:** CLI help, plugin-evals.md

Basic run:
```bash
claude plugin eval .                           # All cases, this plugin, with baseline
claude plugin eval . --case "owner-*"          # Filter by name glob
claude plugin eval . --tag smoke                # Filter by tag
claude plugin eval . --runs 1 --ablation none  # Single arm, faster iteration
```

Grants & tools:
```bash
claude plugin eval . --allow-tools Bash Write Edit
claude plugin eval . --allow-tools "WebFetch(domain:example.com)"  # Domain-scoped
```

Models & concurrency:
```bash
claude plugin eval . --model claude-sonnet-5 --judge-model claude-haiku-4-5
claude plugin eval . -j 4                      # 4 parallel runs (share rate limit)
```

Cost & limits:
```bash
claude plugin eval . --max-cost-usd 20         # Abort if cost exceeds ceiling
claude plugin eval . --threshold 0.8           # Pass if case score >= 0.8
```

CI / non-interactive:
```bash
claude plugin eval . \
  --trust-plugin \
  --json results.json \
  --no-publish \
  --threshold 0.8 \
  --model claude-sonnet-5 \
  --judge-model claude-haiku-4-5
```

### Results Format

**HTML Report** (report.html):
- Verdict line: summary of plugin effect across suite
- Case cards: each case's delta, score, and runs with grader verdicts
- Expandable grader details: why each grader passed/failed, judge votes
- Published to claude.ai if subscription available; pass `--no-publish` to keep local

**JSON Result** (aggregate-result.json, schemaVersion: 1):
Key fields:
- `partial`, `partialReason` - set if run interrupted or cost ceiling hit
- `aggregates.overallScore` - mean suite score
- `aggregates.casesPassed` - cases >= threshold
- `aggregates.meanDelta` - mean plugin delta
- `cases[].name`, `cases[].aggregates.score`, `cases[].aggregates.delta`
- `cases[].arms.with[].error`, `cases[].arms.with[].aborted`
- `costUsd` - list-price estimate of model calls
- `claudeVersion` - Claude Code version that ran it

Exit codes:
- 0: all cases >= threshold, no errors
- 1: case failed, load error, or not trusted
- 2: partial (cost ceiling hit or auth failed)
- 130: interrupted
- 143: terminated


## 4. Worked Examples

### Example 1: Skill Calling Python Script with Numeric Output

**Skill definition** (skills/reconcile-payments/SKILL.md):
```markdown
---
name: reconcile-payments
description: Reconcile owner payments against bank statements, outputting a CSV reconciliation
allowed-tools: [Read, Bash]
---

I'll reconcile payments. I can read your bank statement and reservation data, then run a
reconciliation script to match deposits. The script outputs a CSV with matched and unmatched items.

To use this: provide files like hostaway-export.csv and bank-statement.csv, and I'll reconcile them.
```

**Test case** (evals/reconcile-september/prompt.md):
```yaml
---
name: reconcile-september
tags: [core, month-end]
runs: 3
max_turns: 15
allowed_tools: [Read, Write, Bash, Skill]
---

Reconcile the September payment data. 
- hostaway_sep.csv: reservation income
- bank_sep.csv: deposits received
- Output: reconciliation.csv with matched items

Use the reconcile-payments skill.
```

**Graders** (evals/reconcile-september/graders/):

1. outcome.md (llm judge):
```yaml
---
type: llm
criteria: |
  PASS if reconciliation.csv exists with at least 95% of line items matched
  (matched count / total items >= 0.95).
  FAIL if less than 90% matched or file missing.
weight: 2
---
```

2. numeric-match-rate.md (regex on file contents):
```yaml
---
type: regex
target: { source: file, path: reconciliation.csv }
pattern: "^matched_count,\d+$"
---

Passes if the CSV has a header line and numeric matched_count.
```

3. skill-fired.md (tool_used):
```yaml
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?reconcile-payments"'
---
```

4. python-invoked.md (tool_used for script):
```yaml
---
type: tool_used
tool: Bash
input_match: "reconcile.py"
min: 1
max: 3
---
```

**Run**:
```bash
claude plugin eval . --case reconcile-september --runs 3
```

Output summary:
```
CASE                WITH  W/OUT Δ      RUNS COST    NOTES
reconcile-sept      0.92  0.10  +0.82  6    $1.20

1 case(s) · mean Δ +0.82 · 120s · $1.20
```

Interpretation:
- WITH-arm 0.92: numeric/skill graders 1.0, outcome LLM judge 0.83 (2-of-3 votes)
- WITHOUT-arm 0.10: only regex/tool graders pass trivially
- Delta +0.82 confirms plugin drives the result

### Example 2: LLM-Judged Quality Case

**Skill** (skills/draft-statement/SKILL.md):
```markdown
---
name: draft-statement
description: Draft a professional owner payment statement with itemized income breakdown
allowed-tools: [Read, Write]
---

I'll draft a professional owner statement from your data. The statement includes:
- Owner and property details
- Monthly income breakdown by source (Airbnb, Booking.com, Stripe)
- Management fees and deductions
- Net payment amount
- Bank account reference

Provide reservation and payout data in any tabular format.
```

**Test case** (evals/statement-formatting/prompt.md):
```yaml
---
name: statement-formatting
tags: [quality, visual]
runs: 3
max_turns: 10
allowed_tools: [Read, Write, Skill]
---

Draft an owner statement for Jane Citizen's September portfolio.

Data files:
- reservations_sep.csv: Airbnb/Booking income by property
- payouts_sep.csv: Bank deposits received
- fees_sep.csv: Management fee breakdowns

Create a professional PDF-ready statement.
```

**Graders** (evals/statement-formatting/graders/):

1. professional-format.md (llm judge - semantic):
```yaml
---
type: llm
criteria: |
  PASS if statement includes:
  - Clear owner/property identification at top
  - Month/date range
  - Line-item income breakdown with dates and amounts
  - Clear management fee calculation
  - Final payment total
  - Professional formatting without typos

  FAIL if any major section missing or format is unclear.

focus: { source: file, path: statement.md }
weight: 2
---
```

2. mathematical-accuracy.md (regex on markdown file):
```yaml
---
type: regex
target: { source: file, path: statement.md }
pattern: "Total Payable:\s+\$[0-9,]+\.[0-9]{2}"
---

Statement must have explicit total line with formatted dollar amount.
```

3. skill-fired.md (tool_used):
```yaml
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?draft-statement"'
---
```

**Run with strong judge**:
```bash
claude plugin eval . --case statement-formatting --judge-model claude-sonnet-5
```

**Troubleshooting if delta is negative:**
- May indicate the judge is sensitive to formatting differences
- Tighten rubric: specify exact structure, acceptable fonts, etc.
- Or use deterministic regex graders for objective checks


## 5. How skill-creator Differs from plugin eval

**Source:** skills.md, plugin-evals.md, CLI help

### skill-creator Plugin Workflow
- Interactive in-session tool (a plugin installed separately)
- Eval format: `evals/evals.json` (proprietary to skill-creator, not readable by plugin eval)
- Use case: iterating on one skill within Claude Code conversation
- Model: ask Claude in a session to "run evals", "/skill-creator:eval-skill", etc.
- Output: interactive feedback in chat, not a formal report

### plugin eval Workflow
- CLI command (`claude plugin eval`)
- Eval format: case.yaml + prompt.md + graders/*.md (documented, portable)
- Use case: testing full plugin before shipping, CI/CD gating, team review
- Model: runs standalone, isolated, non-interactive (no session state)
- Output: JSON + HTML report (publishable, shareable)

### When to Use Which
- **Use skill-creator** during development in active conversation; fast iteration
- **Use plugin eval** before committing; for CI; to measure against baseline; to share results with team
- **Not interchangeable**: their eval case formats don't overlap; each tool reads its own

### Integration Strategy
1. Use skill-creator in session to design and refine the skill
2. Once skill is stable, graduate to `claude plugin eval init` for formal test cases
3. Commit case files to repo, run in CI with `--threshold` gates
4. Revisit skill-creator if you need interactive tuning mid-development


## Key Takeaways & Inferences

### Documented Facts
1. Skill triggering is description-driven and varies by model; test with target model
2. `claude plugin eval` runs isolated (fresh home/config, only plugin loaded, artifact tool off)
3. With-arm and without-arm graders are scored differently; plugin-fired indicators excluded by default
4. Eval cases are plain files (YAML + Markdown); portable, version-controllable, CI-friendly
5. Mock files support both fixed and agent-type responses; agent mocks save recordings for replay

### Inferences (Not Explicitly Documented)
1. For ~15 agent skills, expect 15-30 eval cases (1-2 per skill) for good coverage; each run ~3 iterations
2. Bundled Python scripts work best via ${CLAUDE_PLUGIN_ROOT} references; persistent data goes to ${CLAUDE_PLUGIN_DATA}
3. Grader weight tuning (e.g., outcome 2x, mechanism 1x) helps balance signal when plugin is meant to improve quality not just trigger
4. Progressive disclosure in skill bodies (reference sub-files) keeps context costs low for 15-skill plugins
5. Regex graders over numeric file outputs (not llm judges) keep eval costs predictable and scores stable for data-heavy skills

### Anti-Pattern Warnings
- Avoid long skill descriptions; be specific about outcome
- Don't put complex logic directly in skill body; reference bundled scripts
- Avoid one giant eval case; break into multiple targeted cases per skill
- Don't use llm graders for long outputs (noisy, expensive); prefer regex on file contents
- Avoid running evals without --ablation none when you only want to iterate (halve cost)

---

**Documentation URLs by Section:**
- Skills & scripting: https://code.claude.com/docs/en/skills.md
- Plugin structure: https://code.claude.com/docs/en/plugins/create.md
- Manifest fields: https://code.claude.com/docs/en/plugins/manifest-reference.md
- Plugin evals (comprehensive): https://code.claude.com/docs/en/plugin-evals.md
- CLI reference: https://code.claude.com/docs/en/plugins/cli-reference.md
