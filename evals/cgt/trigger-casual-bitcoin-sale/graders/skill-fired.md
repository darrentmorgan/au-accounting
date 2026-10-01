---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?(?:cgt|crypto)"'
min: 1
---

The cgt skill (or, since v0.3, the crypto skill, which owns crypto disposals and defers to cgt) must fire.

<!-- Orchestrator 2026-09-30: crypto skill added in v0.3 owns bitcoin disposals; either skill is a correct trigger. -->
