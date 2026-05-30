# COMPLIANCE RULES

## Runtime Boundary

The agent may call:

- `get_driver_status`
- `query_cargo`
- `query_decision_history`
- `model_chat_completion` only behind explicit LLM budget gates

The agent must not read raw data files, import evaluator implementation modules, or use hidden dataset structure.

## Source Scope

- `current_actionable`: current decision observed cargo after query, eligible for take and visible rollout.
- `shadow_liquidity_only`: aggregate liquidity feature only.
- `historical_summary_only`: aggregate memory feature only.

## Audit Command

```powershell
python tools/audit_guard.py --fail-on-p0
```

The scan covers agent code, tests, AGENTS/agent/README files, raw-data markers, blocked imports, hardcoded ID patterns, switch states and hashed forbidden preference terms.

