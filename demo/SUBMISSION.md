# CROWN-Y Submission Notes

## Package Scope

- This package is for the rematch-style official evaluation.
- The ZIP root is `demo/`.
- Included: `demo/agent/` and this `demo/SUBMISSION.md`.
- Not included: `demo/server/`, `demo/server/data/`, `demo/results/`, local reports, local run outputs, or local secrets.

## Runtime Entry

- Official evaluation should load `demo/agent/model_decision_service.py`.
- The default runtime policy is `crown_exact_rbt_mpc`; no environment variable is required.
- `CROWN_Y_VARIANT` can still override the policy for local experiments, but the submitted default is the CROWN-EXACT Rule Bytecode Transducer plus scorer-semantic controller line.

## Model Calls

- Qwen is used only for preference bytecode compilation/linking/auditing, never for final action selection.
- The agent first uses the injected `SimulationApiPort.model_chat_completion` when available.
- If no injected model API exists, it falls back to compatible environment variables such as `DASHSCOPE_API_KEY`; missing or dummy keys trigger deterministic fallback.

## Compliance

- Runtime code uses the injected simulation API for driver state, cargo, history, and model calls.
- Runtime code does not read raw data files, local reports, oracle artifacts, or future cargo data.
- `take_order` uses only current post-query actionable cargo.
- Every query path refreshes world state before filtering and scoring.
