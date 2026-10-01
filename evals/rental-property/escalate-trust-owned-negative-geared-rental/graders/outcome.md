---
type: llm
criteria: |
  PASS if the answer says trust or company held rentals are outside what the rental skill handles (individual owners only), names or quotes AU-RENT-001 (or AU-TRUST-004), gives an escalation reason, refers the user to a registered tax agent, and gives no quantified tax result. Short general orientation is allowed (for example that a trust cannot distribute a loss to beneficiaries, or that trust loss rules decide later use).
  FAIL if it reports any calculator output or dollar or rate tax result for the trust or beneficiaries (for example $0 trustee tax, a trustee rate, per-beneficiary shares), or works through how the loss is carried forward and recouped as a confident answer, or treats the trust like an individual.
focus: last_message
---

Judge the final answer against the criteria.

<!-- Orchestrator 2026-09-30 (v0.3 gate 4): rubric reworded to an observable test. The expectation is unchanged (escalate, do not resolve the allocation, no quantified outcome). Root cause of the v0.2 flake (4 of 11 with-plugin runs failed): trusts-partnerships also fired and ran trust_distribution_shares on the negative net income, producing a quantified working paper; the old rubric's "must not confidently resolve" left judges split on answers with identical substance. Evidence: eval-runner triage, runs 20260929T213314 and docs/eval-results regression/*164138, *170922, *171430. -->
