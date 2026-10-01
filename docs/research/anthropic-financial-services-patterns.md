# Patterns from anthropics/financial-services (read 2026-09-30)

Source: https://github.com/anthropics/financial-services (main, pushed 2026-09-21). Read: README.md, CLAUDE.md, `managed-agent-cookbooks/gl-reconciler/` (agent.yaml, subagents/critic.yaml, steering-examples.json) and `plugins/agent-plugins/gl-reconciler/agents/gl-reconciler.md`. The repo layout was listed in full. This note records design patterns only; no text is copied into our skills.

## What the repo does
- **Two layers.** Vertical plugins hold the skills, slash commands and MCP connectors. Named agent plugins (Pitch Agent, GL Reconciler, Month-End Closer, KYC Screener and others) each bundle the skills they use and one canonical system prompt in `agents/<slug>.md`.
- **One source, two wrappers.** The same agent prompt and skills ship as a Cowork or Claude Code plugin and as a Managed Agents API template (`agent.yaml` plus depth-1 `subagents/*.yaml` and `steering-examples.json`).
- **Reader, critic, resolver.** In GL Reconciler, readers open untrusted documents but have no MCP or write tools. A critic re-verifies each finding against trusted internal sources, read-only. Only the resolver can write, and it never sees raw outside content. The orchestrator never writes.
- **Workflow framing.** Each agent says what it produces, gives a numbered workflow and guardrails, and names the skills it uses. The description says when to use it and when to use a sibling agent instead.
- **Slash commands** (`/comps`, `/dcf`, `/earnings`) give an explicit entry point alongside automatic skill triggering.
- **Tooling.** `scripts/check.py` lints every manifest, checks that every file, skill and agent reference resolves, and fails when a bundled skill copy drifts from its source. A pre-commit hook bumps each changed plugin's version exactly once per branch, and CI enforces it.
- **Framing.** Every output is draft work product for qualified-professional review, and the agents never post, execute or approve. This matches our working-paper rule.

## Candidates for au-accounting v0.4 (not in the v0.3 scope)
1. **Named workflow agents on top of the domain skills.** For example an EOFY individual return preparer, a quarterly BAS preparer, and a new-business onboarding agent, each with a canonical prompt that lists the skills it uses. Our router already does this implicitly. Naming the workflows would make the end-to-end runs testable as their own eval suites.
2. **A critic step for every working paper.** An independent, read-only reviewer re-runs each figure in the output through the au-tax tools and `figures_used`, and returns confirmed or rejected per figure before the answer is final. This targets the class of defect we fixed in v0.3, where figures were stated that no tool produced.
3. **Trust boundary for client documents.** When v0.4 reads bank CSVs, platform payout reports or statements, a reader worker with no write or MCP access extracts them, and only structured data reaches the calculators. This matters once the skills ingest documents rather than typed facts.
4. **Slash commands** (`/bas`, `/eofy`, `/cgt`, `/crypto`) as explicit entry points. They would reduce the trigger misses we saw (the bitcoin phrasing and the granny flat).
5. **check.py-style reference checks.** Add to `check_all.sh` a check that every skill, tool, refusal code and risk flag named in a SKILL.md, eval or agent file resolves (partly covered today by `lint_skills` and `lint_risk_flags`), plus a pre-commit version bump.
6. **Managed Agents templates.** Only if the project is to be run headless for clients: `agent.yaml` wrappers around the same prompts.

Agreed 2026-09-30: adopt the structure and practices only (not content), tracked in `docs/BUILD-PLAN.md` Phase 5. Critic step and slash commands first.
