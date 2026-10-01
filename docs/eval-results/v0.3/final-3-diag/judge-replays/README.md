# Onboarding judge replays (2026-09-30)

Answer: `int-onboard-sa-sole-trader-2627`, with-plugin run 0 of integration run 20260930T190019 (live judge votes FAIL FAIL FAIL).

Prompt: `onboarding-exact-harness-prompt.txt` is the exact user prompt that `claude plugin eval` (CLI 2.1.285) builds for an llm grader: the `criteria` field, the last message, and "Respond with exactly one word: PASS or FAIL." The harness system prompt is "You are a strict, terse evaluation judge for coding-agent traces." The grader markdown body is not sent.

Replays, each `claude -p --model sonnet --system-prompt "<harness system prompt>" < onboarding-exact-harness-prompt.txt`:
- thinking default, 3 runs: `exact-thinking-default-*.txt`
- thinking off (`MAX_THINKING_TOKENS=0`, matching the harness `thinkingConfig: disabled`), 4 runs: `exact-thinking-off-*.txt`

Result: 7/7 PASS. The live diagnostic run 20260930T193707 on the same case gave PASS PASS FAIL. The replay does not reproduce every harness setting (the harness calls the model API directly), so the finding is that the live judge is noisy on this rubric, not that it is wrong.
