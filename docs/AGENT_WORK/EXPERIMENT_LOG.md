# CROWN-PTT-GreedyMPC Experiment Log

## 2026-06-01 Setup

- Read `crown_ptt_firewall_profit_codex_prompt.md`.
- Created branch `crown-ptt-firewall-profit`.
- Initial reviewer found P0 gaps: default variant was `best_rescue`, guard docs were Delta-MPC, and PTT controllers/firewall were missing.
- Current rescue reference remains official_net 5067.69 and preference_penalty 38140 on public 20260529.

## Planned Evidence

| gate | evidence |
|---|---|
| default variant | `preference_firewall_profit` in config and package smoke logs |
| PTT coverage | T01-T18 compiler/controller/firewall rows |
| synthetic behavior | T01-T18 compile, positive, negative, repair, paraphrase, runtime replacement, firewall impact |
| public eval | 20260529 and 20260509 31-day simulations |
| compliance | audit guard P0=0 and package inspection |

## Reviewer Notes

- Prompt-adherence/compliance reviewer: default PTT variant, PTT docs, PTT controllers, mandatory linker, and PTT report replacement are immediate blockers.
- Trace reports must hash diagnostic ids; action params may retain runtime `cargo_id` for official `take_order`.

## 2026-06-01 Final Evidence

- `python -m pytest tests -q`: 57 passed.
- `python -m compileall demo tools tests`: passed.
- `python tools/audit_guard.py --fail-on-p0`: P0=0.
- `python tools/qwen_preference_smoke_test.py`: Qwen3.5-Flash compile call succeeded for a non-empty preference.
- `python tools/run_ptt_synthetic_tests.py`: 18/18 PTT abstract types passed.
- 20260529 31-day local eval with `preference_firewall_profit`: official_net=-8635.06, gross_minus_cost=33364.94, preference_penalty=42000.0, failed_driver_count=0.
- 20260509 31-day local eval with `preference_firewall_profit`: official_net=87591.66, preference_penalty=99530.0, failed_driver_count=0.
- Runtime full eval used `CROWN_Y_DISABLE_RUNTIME_QWEN=1` because live Qwen calls stalled full-run throughput; default package/runtime still keeps Qwen PTT enabled.
- Package audit created only a `NOT_RECOMMENDED_DO_NOT_SUBMIT` zip: default variant `preference_firewall_profit`, root `demo/`, no disallowed entries, SHA256 recorded in `reports/ptt_submission_audit.md`.
- Stop state is `PTT_DIAGNOSTIC_SUCCESS_DO_NOT_SUBMIT`; score gates and runtime Qwen-call gate were not reached.
