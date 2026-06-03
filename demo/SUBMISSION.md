NOT RECOMMENDED FOR B榜 SUBMISSION

# CROWN-FUSE Review-Only Notes

## Package Scope

- This package is for review of the CROWN-FUSE / RESCUE-SWITCH v10 evidence only.
- It is not a recommended or experimental B leaderboard submission package.
- The ZIP root is `demo/`.
- Included: `demo/agent/` and this `demo/SUBMISSION.md`.
- Not included: `demo/server/`, `demo/server/data/`, `demo/results/`, local reports, local run outputs, or local secrets.

## Runtime Entry

- Official evaluation should load `demo/agent/model_decision_service.py`.
- The default runtime policy is `best_rescue`; no environment variable is required.
- `CROWN_Y_VARIANT` can still override the policy for local experiments, but the packaged default is the B0 rescue fallback selected as B11.

## Model Calls

- Qwen is used for preference contract compilation and observed-vocabulary linking, never for final action selection.
- The agent first uses the injected `SimulationApiPort.model_chat_completion` when available.
- Qwen numeric auditor score adjustment is off by default because the A1/A2 ablation did not beat auditor off.

## Compliance

- Runtime code uses the injected simulation API for driver state, cargo, history, and model calls.
- Runtime code does not read raw data files, local reports, oracle artifacts, or future cargo data.
- `take_order` uses only current post-query actionable cargo.
- Every query path refreshes world state before filtering and scoring.
