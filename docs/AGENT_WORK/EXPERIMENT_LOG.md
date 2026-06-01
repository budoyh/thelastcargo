# CROWN-EXACT RBT-MPC Experiment Log

## 2026-06-01 CROWN-EXACT Kickoff

- Branch created and pushed: `crown-exact-rbt-mpc`.
- Previous PTT evidence imported as failure baseline: 20260529 official_net -8635.06, gross_minus_cost 33364.94, preference_penalty 42000, qwen_compile_calls 0, ptt_compile_calls 0.
- Exact gates adopted: real Qwen compile/cache, scorer semantics probe, action-level controller scoring, official score uplift, P0 clean, reviewer PASS.
- Working assumption: use `best_rescue` legality core as base; exact modules are additive and must be disabled by default if ablation shows gross collapse or no penalty improvement.

## 2026-06-01 Historical PTT Record

- This section is archived context from the failed PTT build, not the current CROWN-EXACT plan.
- PTT branch `crown-ptt-firewall-profit` used default variant `preference_firewall_profit`.
- The PTT run was not submission-ready: 20260529 official_net=-8635.06, gross_minus_cost=33364.94, preference_penalty=42000.0.
- The PTT run used `CROWN_Y_DISABLE_RUNTIME_QWEN=1` for full eval and therefore cannot satisfy the CROWN-EXACT real-Qwen gate.
- Current CROWN-EXACT default is `crown_exact_rbt_mpc`; runtime Qwen was enabled in the full exact evals.

## Historical PTT Planned Evidence

| gate | evidence |
|---|---|
| historical default variant | `preference_firewall_profit` in config and package smoke logs |
| PTT coverage | T01-T18 compiler/controller/firewall rows |
| synthetic behavior | T01-T18 compile, positive, negative, repair, paraphrase, runtime replacement, firewall impact |
| public eval | 20260529 and 20260509 31-day simulations |
| compliance | audit guard P0=0 and package inspection |

## Historical PTT Reviewer Notes

- Prompt-adherence/compliance reviewer: default PTT variant, PTT docs, PTT controllers, mandatory linker, and PTT report replacement are immediate blockers.
- Trace reports must hash diagnostic ids; action params may retain runtime `cargo_id` for official `take_order`.

## 2026-06-01 PTT Final Evidence

- `python -m pytest tests -q`: 57 passed.
- `python -m compileall demo tools tests`: passed.
- `python tools/audit_guard.py --fail-on-p0`: P0=0.
- `python tools/qwen_preference_smoke_test.py`: Qwen3.5-Flash compile call succeeded for a non-empty preference.
- `python tools/run_ptt_synthetic_tests.py`: 18/18 PTT abstract types passed.
- 20260529 31-day local eval with `preference_firewall_profit`: official_net=-8635.06, gross_minus_cost=33364.94, preference_penalty=42000.0, failed_driver_count=0.
- 20260509 31-day local eval with `preference_firewall_profit`: official_net=87591.66, preference_penalty=99530.0, failed_driver_count=0.
- Historical PTT full eval used `CROWN_Y_DISABLE_RUNTIME_QWEN=1` because live Qwen calls stalled full-run throughput; this is explicitly invalid for CROWN-EXACT success.
- Package audit created only a `NOT_RECOMMENDED_DO_NOT_SUBMIT` zip: default variant `preference_firewall_profit`, root `demo/`, no disallowed entries, SHA256 recorded in `reports/ptt_submission_audit.md`.
- Stop state is `PTT_DIAGNOSTIC_SUCCESS_DO_NOT_SUBMIT`; score gates and runtime Qwen-call gate were not reached.

## 2026-06-01 CROWN-EXACT Evidence

- Real Qwen path was kept enabled: `CROWN_Y_DISABLE_RUNTIME_QWEN` was not set for exact full evals, and real compile/link calls appeared in traces.
- Scorer semantics microprobe produced 10 rows with 9 aligned cases and hard-enable evidence for aligned semantics.
- 20260529 exact after disabling negative PTT firewall default: official_net -163.93, gross_minus_cost 41296.06, preference_penalty 41460.0, qwen_compile_calls 12, qwen_linker_calls 243, simulation_failures 0.
- Current-code `best_rescue` reproduction matched exact at official_net -163.93, showing the exact default no longer adds a score regression beyond the current rescue/Qwen path, but it also does not reach rescue historical score.
- Numeric parameter probe `90min_wait_8am_rest` failed: official_net -20415.93 and preference_penalty 62680.0, so it was reverted from default.
- Gate consequence: CROWN-EXACT is not recommended unless a later run reaches official_net >=30000, preference_penalty <=22000, gross_minus_cost >=45000, real Qwen compile/cache >0, controller scoring >0, scorer semantics aligned >0, P0 clean, and 0509 non-catastrophic.
