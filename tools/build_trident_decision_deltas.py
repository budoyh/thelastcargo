"""Build the CROWN-TRIDENT changed-decision delta audit CSV.

This tool compares a variant run against B0 by driver-local decision index.
The repository's existing artifacts do not contain suffix replay results for
individual replacements, so per-decision official replay fields remain blank
and the rows are labeled diagnostic-only. Exact official deltas are available
only at the completed policy-run level and are printed as command output.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT_PATH = Path(__file__).resolve().parents[1]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from tools.delta_mpc_utils import (
    REPORTS,
    ROOT,
    iter_action_rows,
    json_cell,
    read_json,
    short_hash,
    summarize_run,
    write_csv,
)


FIELDS = [
    "variant_name",
    "decision_index",
    "time_bucket",
    "state_hash",
    "b0_action_type",
    "new_action_type",
    "b0_action_signature_hash",
    "new_action_signature_hash",
    "estimated_gross_delta",
    "estimated_pref_delta",
    "estimated_duration_delta",
    "affected_rule_ids",
    "rule_state_before",
    "rule_state_after",
    "qwen_audit_reason",
    "controller_reason",
    "official_replay_delta_net",
    "official_replay_delta_gross",
    "official_replay_delta_penalty",
    "delta_label_mode",
    "label_validity",
    "state_compatible",
    "visible_compatible",
    "legal_compatible",
    "regret_label_win_loss_unknown",
    "reason_code",
    "keep_kill_source",
]


PREF_COMPONENT_KEYS = {
    "lost_repair_window_cost",
    "preference_marginal_penalty",
    "preference_soft_penalty",
    "ptt_failure_risk_applied",
    "ptt_lost_repair_window_applied",
    "ptt_low_confidence_applied",
    "ptt_marginal_penalty_applied",
    "ptt_reposition_penalty_applied",
    "ptt_wait_penalty_applied",
    "qwen_audit_adjustment_applied",
    "rest_guard",
    "rest_window_penalty",
    "unknown_soft_risk",
}

CONTROLLER_COMPONENT_KEYS = {
    "lost_repair_window_cost",
    "macro_task_repair_value",
    "preference_marginal_penalty",
    "preference_repair_bonus",
    "preference_repair_value",
    "preference_soft_penalty",
    "ptt_failure_risk_applied",
    "ptt_lost_repair_window_applied",
    "ptt_low_confidence_applied",
    "ptt_marginal_penalty_applied",
    "ptt_repair_value",
    "qwen_audit_adjustment",
    "qwen_audit_adjustment_applied",
    "unknown_soft_risk",
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _action(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("action") if isinstance(row.get("action"), dict) else {}


def _trace(row: dict[str, Any]) -> dict[str, Any]:
    action = _action(row)
    return action.get("agent_trace") if isinstance(action.get("agent_trace"), dict) else {}


def _chosen(row: dict[str, Any]) -> dict[str, Any]:
    trace = _trace(row)
    return trace.get("chosen") if isinstance(trace.get("chosen"), dict) else {}


def _components(row: dict[str, Any]) -> dict[str, float]:
    chosen = _chosen(row)
    raw = chosen.get("components") if isinstance(chosen.get("components"), dict) else {}
    return {str(key): _safe_float(value) for key, value in raw.items()}


def _action_type(row: dict[str, Any]) -> str:
    action = _action(row)
    return str(action.get("action") or _chosen(row).get("action_type") or "")


def _driver_hash(path: Path, row: dict[str, Any]) -> str:
    return short_hash(row.get("driver_id", path.name))


def _state_hash(row: dict[str, Any]) -> str:
    return short_hash(
        {
            "step": row.get("step"),
            "position_before": row.get("position_before"),
            "simulation_end_time": row.get("simulation_end_time"),
        }
    )


def _signature(row: dict[str, Any]) -> str:
    action = _action(row)
    chosen = _chosen(row)
    return short_hash(
        {
            "action_type": _action_type(row),
            "candidate_hash": chosen.get("candidate_id_hash"),
            "cargo_hash": chosen.get("cargo_id_hash"),
            "params": action.get("params") if isinstance(action.get("params"), dict) else {},
        }
    )


def _time_bucket(row: dict[str, Any]) -> str:
    step = _safe_int(row.get("step"), 0)
    return f"step_bucket_{step // 24:03d}"


def _duration(row: dict[str, Any]) -> float:
    return _safe_float(row.get("step_elapsed_minutes")) + _safe_float(row.get("query_scan_cost_minutes"))


def _gross_estimate(row: dict[str, Any]) -> float:
    return _safe_float(_components(row).get("direct_net"))


def _pref_cost_estimate(row: dict[str, Any]) -> float:
    total = 0.0
    for key, value in _components(row).items():
        if key in PREF_COMPONENT_KEYS:
            total += -value if value < 0 else value
    return total


def _nonzero_controller_components(row: dict[str, Any]) -> list[str]:
    comps = _components(row)
    return sorted(key for key in CONTROLLER_COMPONENT_KEYS if abs(_safe_float(comps.get(key))) > 1e-9)


def _qwen_reason(row: dict[str, Any]) -> str:
    comps = _components(row)
    adjustment = _safe_float(comps.get("qwen_audit_adjustment_applied")) or _safe_float(
        comps.get("qwen_audit_adjustment")
    )
    trace = _trace(row)
    rescue = trace.get("rescue") if isinstance(trace.get("rescue"), dict) else {}
    qwen = rescue.get("qwen") if isinstance(rescue.get("qwen"), dict) else {}
    if abs(adjustment) > 1e-9:
        return "qwen_adjustment_nonzero"
    if _safe_int(qwen.get("auditor_calls")) > 0:
        return "qwen_auditor_called_zero_adjustment"
    return "none"


def _legal(row: dict[str, Any]) -> bool:
    chosen = _chosen(row)
    result = row.get("result") if isinstance(row.get("result"), dict) else {}
    accepted = result.get("accepted")
    safe = chosen.get("action_safe")
    return accepted is not False and safe is not False


def _visible_count(row: dict[str, Any]) -> int:
    trace = _trace(row)
    return _safe_int(trace.get("visible_count"))


def _load_action_records(run_dir: Path) -> dict[tuple[str, int], dict[str, Any]]:
    counters: dict[str, int] = defaultdict(int)
    records: dict[tuple[str, int], dict[str, Any]] = {}
    for path, line_no, row in iter_action_rows(run_dir):
        driver_hash = _driver_hash(path, row)
        counters[driver_hash] += 1
        index = counters[driver_hash]
        records[(driver_hash, index)] = {
            "row": row,
            "driver_hash": driver_hash,
            "decision_index": index,
            "line_hash": short_hash({"file": path.name, "line_no": line_no}),
        }
    return records


def _load_driver_rule_ids(run_dir: Path) -> dict[str, list[str]]:
    monthly = read_json(run_dir / "monthly_income_202603.json")
    out: dict[str, list[str]] = defaultdict(list)
    for driver_index, driver in enumerate(monthly.get("drivers", []) if isinstance(monthly.get("drivers"), list) else []):
        if not isinstance(driver, dict):
            continue
        driver_hash = short_hash(driver.get("driver_id", str(driver_index)))
        pref = driver.get("preference_check") if isinstance(driver.get("preference_check"), dict) else {}
        rules = pref.get("rules") if isinstance(pref.get("rules"), list) else []
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            rule_id = short_hash({"rule": str(rule.get("rule", "") or ""), "preference_text": str(rule.get("preference_text", "") or "")})
            out[driver_hash].append(rule_id)
    return {driver_hash: sorted(set(rule_ids)) for driver_hash, rule_ids in out.items()}


def _rule_state(row: dict[str, Any]) -> str:
    comps = _components(row)
    payload = {
        "score": _safe_float(_chosen(row).get("score")),
        "preference_components": {
            key: round(value, 4)
            for key, value in sorted(comps.items())
            if key in PREF_COMPONENT_KEYS or key in CONTROLLER_COMPONENT_KEYS
        },
    }
    return json_cell(payload)


def _reason_code(b0_row: dict[str, Any], new_row: dict[str, Any]) -> str:
    if not b0_row:
        return "new_decision_without_b0_aligned_step"
    if not new_row:
        return "b0_decision_without_new_aligned_step"
    b0_type = _action_type(b0_row)
    new_type = _action_type(new_row)
    new_components = _nonzero_controller_components(new_row)
    if b0_type != new_type:
        return f"action_type_changed_{b0_type}_to_{new_type}"
    if _signature(b0_row) != _signature(new_row):
        if new_components:
            return "same_action_type_signature_changed_with_controller_score"
        return "same_action_type_signature_changed"
    return "unchanged"


def build_rows(b0_run: Path, variant_run: Path, sample_limit: int = 0) -> list[dict[str, Any]]:
    b0_records = _load_action_records(b0_run)
    new_records = _load_action_records(variant_run)
    rule_ids_by_driver = _load_driver_rule_ids(variant_run)
    variant_name = variant_run.name
    rows: list[dict[str, Any]] = []

    all_keys = sorted(set(b0_records) | set(new_records), key=lambda item: (item[0], item[1]))
    for key in all_keys:
        b0_row = b0_records.get(key, {}).get("row", {})
        new_row = new_records.get(key, {}).get("row", {})
        if b0_row and new_row and _signature(b0_row) == _signature(new_row):
            continue
        driver_hash, decision_index = key
        controller_components = _nonzero_controller_components(new_row)
        state_compatible = bool(b0_row and new_row and _state_hash(b0_row) == _state_hash(new_row))
        visible_compatible = bool(b0_row and new_row and _visible_count(b0_row) == _visible_count(new_row))
        legal_compatible = bool((not b0_row or _legal(b0_row)) and (not new_row or _legal(new_row)))
        rows.append(
            {
                "variant_name": variant_name,
                "decision_index": decision_index,
                "time_bucket": _time_bucket(new_row),
                "state_hash": short_hash({"b0": _state_hash(b0_row), "new": _state_hash(new_row)}),
                "b0_action_type": _action_type(b0_row),
                "new_action_type": _action_type(new_row),
                "b0_action_signature_hash": _signature(b0_row),
                "new_action_signature_hash": _signature(new_row),
                "estimated_gross_delta": round(_gross_estimate(new_row) - _gross_estimate(b0_row), 4),
                "estimated_pref_delta": round(_pref_cost_estimate(new_row) - _pref_cost_estimate(b0_row), 4),
                "estimated_duration_delta": round(_duration(new_row) - _duration(b0_row), 4),
                "affected_rule_ids": json_cell(rule_ids_by_driver.get(driver_hash, [])),
                "rule_state_before": _rule_state(b0_row),
                "rule_state_after": _rule_state(new_row),
                "qwen_audit_reason": _qwen_reason(new_row),
                "controller_reason": json_cell(controller_components),
                "official_replay_delta_net": "",
                "official_replay_delta_gross": "",
                "official_replay_delta_penalty": "",
                "delta_label_mode": "trace_alignment_without_suffix_replay",
                "label_validity": "diagnostic_not_official_counterfactual",
                "state_compatible": state_compatible,
                "visible_compatible": visible_compatible,
                "legal_compatible": legal_compatible,
                "regret_label_win_loss_unknown": "unknown",
                "reason_code": _reason_code(b0_row, new_row),
                "keep_kill_source": "needs_official_suffix_replay_before_tuning",
            }
        )
        if sample_limit > 0 and len(rows) >= sample_limit:
            break
    return rows


def _aggregate(rows: list[dict[str, Any]], b0_run: Path, variant_run: Path) -> dict[str, Any]:
    b0 = summarize_run(b0_run)
    new = summarize_run(variant_run)
    reason_counts = Counter(str(row["reason_code"]) for row in rows)
    estimated = [
        (
            _safe_float(row["estimated_gross_delta"]) - _safe_float(row["estimated_pref_delta"]),
            row["decision_index"],
            row["reason_code"],
        )
        for row in rows
    ]
    positives = [item for item in estimated if item[0] > 0]
    negatives = [item for item in estimated if item[0] < 0]
    return {
        "rows": len(rows),
        "changed_decision_positive_delta_count": len(positives),
        "changed_decision_negative_delta_count": len(negatives),
        "changed_decision_unknown_count": len(rows),
        "sum_positive_delta_estimated_not_official": round(sum(item[0] for item in positives), 2),
        "sum_negative_delta_estimated_not_official": round(sum(item[0] for item in negatives), 2),
        "run_pair_official_delta_net": round(float(new["official_net"]) - float(b0["official_net"]), 2),
        "run_pair_official_delta_gross": round(float(new["gross_minus_cost"]) - float(b0["gross_minus_cost"]), 2),
        "run_pair_official_delta_penalty": round(float(new["preference_penalty"]) - float(b0["preference_penalty"]), 2),
        "top_50_bad_changes_estimated": json_cell(sorted(estimated)[:50]),
        "top_50_good_changes_estimated": json_cell(sorted(estimated, reverse=True)[:50]),
        "reason_counts": json_cell(dict(reason_counts)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--b0-run", type=Path, default=ROOT / "runs" / "gold" / "B0_best_rescue_restored_20260529")
    parser.add_argument("--variant-run", type=Path, default=ROOT / "runs" / "gold" / "B9_gold_current_20260529")
    parser.add_argument("--sample-limit", type=int, default=0, help="0 means all aligned changed decisions")
    parser.add_argument("--out", type=Path, default=REPORTS / "trident_decision_deltas.csv")
    args = parser.parse_args()

    rows = build_rows(args.b0_run, args.variant_run, args.sample_limit)
    write_csv(args.out, rows, FIELDS)
    summary = _aggregate(rows, args.b0_run, args.variant_run)
    summary.update(
        {
            "out": str(args.out),
            "simulation_days": args.simulation_days,
            "variant_run": str(args.variant_run),
            "b0_run": str(args.b0_run),
            "label_validity": "diagnostic_not_official_counterfactual",
        }
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
