# CROWN-PTT-GreedyMPC Execution Plan

## Success Criteria

- `PTT_SUBMISSION_READY` requires score-hard and semantics-hard gates.
- Public 20260529 must exceed rescue official_net 5067.69, materially lower preference_penalty below 38140, and keep gross_minus_cost at least 40000.
- 20260509 must have no catastrophic regression.
- T01-T18 synthetic behavioral tests must pass.
- Default package variant must be `preference_firewall_profit`.

## Work Order

1. Archive Delta reports and keep final `reports/` limited to five PTT files.
2. Update `AGENTS.md`, `agent.md`, and `docs/AGENT_WORK/*`.
3. Add PTT rule schema and compile adapter around existing Qwen compiler.
4. Add T01-T18 deterministic controllers and ScorerSemanticsAdapter downgrade gate.
5. Add Preference Firewall and Qwen auditor counters.
6. Integrate runtime order into rescue core with default `preference_firewall_profit`.
7. Add hidden-style synthetic tests and PTT report builder.
8. Run pytest, compileall, audit guard, round bug check, Qwen smoke, synthetic tests.
9. Run 20260529 and 20260509 31-day evaluations.
10. Build PTT reports; package only if gates pass, otherwise produce do-not-submit report and optional not-recommended inspection zip.
11. Commit and push branch.

## Keep/Kill Policy

- Keep deterministic controller/firewall behavior only if it improves official score or provides semantics-safe protection without gross collapse.
- High-confidence hard blocks require scorer-semantics alignment; otherwise use soft risk.
- UnknownSoft never hard-blocks.
- Learned terminal/ranker stays OFF.

## Known Risks

- Implementing all T01-T18 fully may still fail local score gates.
- Local public preferences may not cover every hidden type; synthetic tests are required but not sufficient for submission readiness.
- Qwen availability can vary; missing real compile/link/audit on preferences is an external or do-not-submit blocker.
