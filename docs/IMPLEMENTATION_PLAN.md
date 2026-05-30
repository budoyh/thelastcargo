# IMPLEMENTATION PLAN

## Success Criteria

- P0/P0++ tests pass.
- P1 tests pass.
- `tools/audit_guard.py --fail-on-p0` returns 0 P0.
- 31-day local simulation path runs with deterministic agent and produces income JSON.
- Regret Dashboard outputs six regret categories.
- Final report includes commit, tests, simulation, ablation, reviewer results, residual risks.

## Checklist

- [x] Initialize local branch and unpack 20260529 base.
- [x] Keep 20260509 under ignored offline reference.
- [x] Create `AGENTS.md`, `agent.md`, project docs and reports.
- [x] Implement P0/P0++ schemas, normalization, world refresh, source scope, action certificate and safety fallback.
- [x] Implement P1 Time Shadow, query policy, preference certificate, endgame, two-hop rollout, payback-gated reposition.
- [x] Implement audit guard and round bug check.
- [x] Implement unit tests for prompt-required P0/P1/P2 gate cases.
- [x] Run 31-day smoke/full local simulation on 20260529.
- [x] Run local evaluation on 20260509 reference or document blocker.
- [x] Generate regret dashboard and stability audit.
- [x] Generate final audit report.
- [x] Run final subagent/reviewer audit and remediation pass.
- [x] Commit and push or document remote blocker.
