"""Build the CROWN-TRIDENT rule-level penalty attribution ledger.

The current run artifacts expose exact rule penalties in
``monthly_income_202603.json`` and aggregate controller/Qwen counters in
hashed action traces. They do not expose per-rule controller usage, so this
tool marks those fields as aggregate approximations instead of treating them
as official counterfactual labels.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT_PATH = Path(__file__).resolve().parents[1]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from tools.delta_mpc_utils import REPORTS, ROOT, iter_action_rows, json_cell, read_json, short_hash, write_csv


FIELDS = [
    "dataset",
    "driver_hash",
    "preference_hash",
    "rule_id",
    "raw_text_hash",
    "contract_type",
    "primitive_family",
    "schema_valid",
    "executable",
    "scorer_aligned",
    "controller_attached",
    "candidate_score_used_count",
    "score_changed_count",
    "changed_decision_count",
    "qwen_compile_used",
    "qwen_link_used",
    "qwen_audit_used",
    "penalty_unit",
    "penalty_cap",
    "penalty_amount_source",
    "official_penalty_final",
    "official_penalty_delta_vs_b0",
    "final_state",
    "fulfilled",
    "violated",
    "capped",
    "still_repairable",
    "first_unrepairable_step_hash",
    "violated_day_hashes",
    "missed_repair_opportunity_count",
    "best_counterfactual_fix_type",
    "best_counterfactual_fix_delta_net",
    "compile_error",
    "link_error",
    "state_error",
    "scale_error",
    "repair_error",
    "keep_or_kill",
]


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


def _hash_text(value: Any) -> str:
    return short_hash(str(value or ""))


def _driver_hash(driver: dict[str, Any], fallback: str = "") -> str:
    return short_hash(driver.get("driver_id", fallback))


def _rule_key(driver_hash: str, rule: dict[str, Any]) -> tuple[str, str]:
    raw_rule = str(rule.get("rule", "") or "")
    raw_pref = str(rule.get("preference_text", "") or "")
    return driver_hash, short_hash({"rule": raw_rule, "preference_text": raw_pref})


def _load_monthly_rules(run_dir: Path) -> dict[tuple[str, str], dict[str, Any]]:
    monthly = read_json(run_dir / "monthly_income_202603.json")
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for driver_index, driver in enumerate(monthly.get("drivers", []) if isinstance(monthly.get("drivers"), list) else []):
        if not isinstance(driver, dict):
            continue
        driver_hash = _driver_hash(driver, str(driver_index))
        pref = driver.get("preference_check") if isinstance(driver.get("preference_check"), dict) else {}
        rules = pref.get("rules") if isinstance(pref.get("rules"), list) else []
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            key = _rule_key(driver_hash, rule)
            out[key] = {
                "driver_hash": driver_hash,
                "preference_hash": _hash_text(rule.get("preference_text")),
                "rule_id": key[1],
                "raw_text_hash": _hash_text(rule.get("rule")),
                "penalty": _safe_float(rule.get("penalty")),
                "violations": rule.get("violations"),
            }
    return out


def _driver_rule_counts(rules: dict[tuple[str, str], dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for driver_hash, _ in rules:
        counts[driver_hash] += 1
    return dict(counts)


def _trace(row: dict[str, Any]) -> dict[str, Any]:
    action = row.get("action") if isinstance(row.get("action"), dict) else {}
    trace = action.get("agent_trace") if isinstance(action.get("agent_trace"), dict) else {}
    return trace


def _trace_driver_hash(path: Path, row: dict[str, Any]) -> str:
    return short_hash(row.get("driver_id", path.name))


def _collect_driver_trace_stats(run_dir: Path) -> dict[str, dict[str, Any]]:
    by_driver: dict[str, dict[str, Any]] = defaultdict(lambda: defaultdict(float))
    for path, _line_no, row in iter_action_rows(run_dir):
        driver_hash = _trace_driver_hash(path, row)
        bucket = by_driver[driver_hash]
        trace = _trace(row)
        chosen = trace.get("chosen") if isinstance(trace.get("chosen"), dict) else {}
        components = chosen.get("components") if isinstance(chosen.get("components"), dict) else {}
        lost_cost = (
            abs(_safe_float(components.get("lost_repair_window_cost")))
            + abs(_safe_float(components.get("ptt_lost_repair_window_applied")))
            + abs(_safe_float(components.get("ptt_lost_repair_window_cost")))
        )
        if lost_cost > 0:
            bucket["missed_repair_opportunity_count"] += 1
        rescue = trace.get("rescue") if isinstance(trace.get("rescue"), dict) else {}
        ptt = rescue.get("ptt") if isinstance(rescue.get("ptt"), dict) else {}
        stats = ptt.get("stats") if isinstance(ptt.get("stats"), dict) else {}
        qwen = rescue.get("qwen") if isinstance(rescue.get("qwen"), dict) else {}
        for key in [
            "controller_scored_candidate_count",
            "candidate_rule_eval_count",
            "score_changed_by_controller_count",
            "changed_decision_count",
            "compile_calls",
            "cache_hits",
            "linker_call_count",
            "auditor_trigger_count",
            "audited_candidate_count",
        ]:
            bucket[key] = max(bucket[key], _safe_float(stats.get(key)))
        for key in ["compile_calls", "cache_hits", "linker_calls", "auditor_calls"]:
            bucket[f"qwen_{key}"] = max(bucket[f"qwen_{key}"], _safe_float(qwen.get(key)))
    return {driver_hash: dict(stats) for driver_hash, stats in by_driver.items()}


def _allocated_count(total: float, rule_count: int) -> int:
    if rule_count <= 0:
        return 0
    return int(round(total / rule_count))


def _penalty_unit_and_cap(penalty: float, violations: Any) -> tuple[str, str, str]:
    if isinstance(violations, bool):
        violations = int(violations)
    if isinstance(violations, (int, float)) and float(violations) > 0:
        return str(round(penalty / float(violations), 4)), "", "official_preference_check_per_violation"
    if penalty > 0 and violations is None:
        return "", str(round(penalty, 4)), "official_preference_check_capped_or_terminal"
    if penalty > 0:
        return "", "", "official_preference_check_unknown_scale"
    return "0", "", "official_preference_check_zero_penalty"


def _state_fields(penalty: float, violations: Any) -> dict[str, Any]:
    violation_count = _safe_float(violations, 0.0)
    violated = penalty > 0 or violation_count > 0
    capped = penalty > 0 and violations is None
    fulfilled = not violated
    if capped:
        final_state = "violated_capped_or_terminal"
    elif violated:
        final_state = "violated"
    else:
        final_state = "fulfilled"
    return {
        "final_state": final_state,
        "fulfilled": fulfilled,
        "violated": violated,
        "capped": capped,
        "still_repairable": "unknown_without_suffix_replay",
    }


def _keep_or_kill(delta_penalty: float, final_penalty: float) -> str:
    if delta_penalty > 0:
        return "kill_or_retune_penalty_worse_vs_b0"
    if delta_penalty < 0:
        return "keep_candidate_penalty_improved_vs_b0"
    if final_penalty > 0:
        return "unresolved_existing_penalty_not_fixed"
    return "neutral_no_final_penalty"


def build_rows(b0_run: Path, variant_run: Path) -> list[dict[str, Any]]:
    b0_rules = _load_monthly_rules(b0_run)
    final_rules = _load_monthly_rules(variant_run)
    rule_counts = _driver_rule_counts(final_rules)
    trace_stats = _collect_driver_trace_stats(variant_run)
    rows: list[dict[str, Any]] = []
    dataset = "20260529" if "20260529" in str(variant_run) else "unknown"

    for key, rule in sorted(final_rules.items(), key=lambda item: (item[1]["driver_hash"], item[1]["rule_id"])):
        driver_hash = rule["driver_hash"]
        stats = trace_stats.get(driver_hash, {})
        count = rule_counts.get(driver_hash, 1)
        final_penalty = _safe_float(rule["penalty"])
        b0_penalty = _safe_float(b0_rules.get(key, {}).get("penalty"))
        delta_penalty = round(final_penalty - b0_penalty, 4)
        unit, cap, source = _penalty_unit_and_cap(final_penalty, rule.get("violations"))
        state = _state_fields(final_penalty, rule.get("violations"))
        approximated_usage = bool(stats)
        state_error = ""
        scale_error = ""
        if approximated_usage:
            state_error = "per_rule_runtime_state_not_in_trace"
            scale_error = "usage_counts_evenly_allocated_from_driver_aggregate_trace_stats"
        else:
            state_error = "runtime_trace_stats_missing"
            scale_error = "usage_counts_unavailable"

        rows.append(
            {
                "dataset": dataset,
                "driver_hash": driver_hash,
                "preference_hash": rule["preference_hash"],
                "rule_id": rule["rule_id"],
                "raw_text_hash": rule["raw_text_hash"],
                "contract_type": "official_preference_check_hash_only",
                "primitive_family": "official_preference_rule",
                "schema_valid": bool(stats.get("schema_valid_count", 0) or stats.get("compile_calls", 0)),
                "executable": "unknown_without_microprobe",
                "scorer_aligned": "official_final_penalty_exact",
                "controller_attached": bool(stats.get("controller_scored_candidate_count", 0)),
                "candidate_score_used_count": _allocated_count(
                    _safe_float(stats.get("candidate_rule_eval_count")), count
                ),
                "score_changed_count": _allocated_count(
                    _safe_float(stats.get("score_changed_by_controller_count")), count
                ),
                "changed_decision_count": _allocated_count(_safe_float(stats.get("changed_decision_count")), count),
                "qwen_compile_used": bool(
                    stats.get("compile_calls", 0) or stats.get("qwen_compile_calls", 0) or stats.get("qwen_cache_hits", 0)
                ),
                "qwen_link_used": bool(stats.get("linker_call_count", 0) or stats.get("qwen_linker_calls", 0)),
                "qwen_audit_used": bool(
                    stats.get("auditor_trigger_count", 0)
                    or stats.get("audited_candidate_count", 0)
                    or stats.get("qwen_auditor_calls", 0)
                ),
                "penalty_unit": unit,
                "penalty_cap": cap,
                "penalty_amount_source": source,
                "official_penalty_final": round(final_penalty, 4),
                "official_penalty_delta_vs_b0": delta_penalty,
                "final_state": state["final_state"],
                "fulfilled": state["fulfilled"],
                "violated": state["violated"],
                "capped": state["capped"],
                "still_repairable": state["still_repairable"],
                "first_unrepairable_step_hash": "",
                "violated_day_hashes": json_cell([]),
                "missed_repair_opportunity_count": _allocated_count(
                    _safe_float(stats.get("missed_repair_opportunity_count")), count
                ),
                "best_counterfactual_fix_type": "not_run",
                "best_counterfactual_fix_delta_net": "",
                "compile_error": "",
                "link_error": "",
                "state_error": state_error,
                "scale_error": scale_error,
                "repair_error": "rule_doctor_counterfactual_not_run",
                "keep_or_kill": _keep_or_kill(delta_penalty, final_penalty),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--b0-run", type=Path, default=ROOT / "runs" / "gold" / "B0_best_rescue_restored_20260529")
    parser.add_argument("--variant-run", type=Path, default=ROOT / "runs" / "gold" / "B9_gold_current_20260529")
    parser.add_argument("--out", type=Path, default=REPORTS / "trident_rule_ledger.csv")
    args = parser.parse_args()

    rows = build_rows(args.b0_run, args.variant_run)
    write_csv(args.out, rows, FIELDS)
    final_penalty = round(sum(_safe_float(row["official_penalty_final"]) for row in rows), 2)
    delta_penalty = round(sum(_safe_float(row["official_penalty_delta_vs_b0"]) for row in rows), 2)
    print(
        {
            "rows": len(rows),
            "out": str(args.out),
            "simulation_days": args.simulation_days,
            "variant_run": str(args.variant_run),
            "b0_run": str(args.b0_run),
            "official_penalty_final_sum": final_penalty,
            "official_penalty_delta_vs_b0_sum": delta_penalty,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
