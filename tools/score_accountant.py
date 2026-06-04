"""Next Build v4 score accounting and forensic CSV exporter."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _short_hash(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _json_cell(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _dataset_tag(path: Path) -> str:
    text = str(path).replace("\\", "/").lower()
    if "20260509" in text or "0509" in text:
        return "20260509_reference"
    if "20260529" in text or "latest" in text:
        return "20260529_main"
    return "unknown_dataset"


def _run_id(path: Path) -> str:
    try:
        rel = path.resolve().relative_to(ROOT)
        return str(rel).replace("\\", "/")
    except ValueError:
        return path.name


def iter_result_dirs(root: Path) -> list[Path]:
    root = root.resolve()
    if (root / "monthly_income_202603.json").is_file():
        return [root]
    out = []
    for path in root.rglob("monthly_income_202603.json"):
        out.append(path.parent)
    return sorted(set(out), key=lambda p: str(p))


def iter_action_rows(run_dir: Path):
    for path in sorted(run_dir.glob("actions_202603_*.jsonl")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                yield path, line_no, row


def _trace(row: dict[str, Any]) -> dict[str, Any]:
    action = row.get("action") if isinstance(row.get("action"), dict) else {}
    trace = action.get("agent_trace") if isinstance(action, dict) else {}
    return trace if isinstance(trace, dict) else {}


def _action_name(row: dict[str, Any]) -> str:
    action = row.get("action") if isinstance(row.get("action"), dict) else {}
    return str(action.get("action", "")).strip()


def _driver_hash(row: dict[str, Any]) -> str:
    return _short_hash(str(row.get("driver_id", "unknown")))


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


def _rule_type(rule: dict[str, Any]) -> str:
    if "off_days" in rule:
        return "full_rest_day"
    if "waited_minutes" in rule:
        return "appointment_wait"
    if "order_days" in rule:
        return "quota_day"
    if "violations" in rule:
        return "violation_count"
    if "satisfied" in rule:
        return "date_specific"
    return "generic"


def _rule_progress(rule: dict[str, Any]) -> str:
    fields = {}
    for key in ("violations", "off_days", "order_days", "satisfied", "waited_minutes"):
        if key in rule:
            fields[key] = rule.get(key)
    return _json_cell(fields)


def _preference_ledger_rows(run_dir: Path, monthly: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    run_id = _run_id(run_dir)
    dataset = _dataset_tag(run_dir)
    for driver in monthly.get("drivers", []) if isinstance(monthly.get("drivers"), list) else []:
        if not isinstance(driver, dict):
            continue
        driver_hash = _short_hash(driver.get("driver_id", "unknown"))
        pref = driver.get("preference_check") if isinstance(driver.get("preference_check"), dict) else {}
        rules = pref.get("rules", []) if isinstance(pref, dict) else []
        if not isinstance(rules, list):
            continue
        for idx, rule in enumerate(rules):
            if not isinstance(rule, dict):
                continue
            penalty = _safe_float(rule.get("penalty", 0.0))
            violations = _safe_int(rule.get("violations", 0))
            satisfied = rule.get("satisfied")
            missed = penalty > 0 and (violations > 0 or satisfied is False or rule.get("off_days") is not None)
            marginal_violation = penalty / max(1, violations) if violations > 0 else penalty if penalty > 0 else 0.0
            rows.append(
                {
                    "row_type": "preference_rule",
                    "run_id": run_id,
                    "dataset_tag": dataset,
                    "driver_id_hash": driver_hash,
                    "day_index": "",
                    "rule_index": idx,
                    "rule_hash": _short_hash({"rule": rule.get("rule"), "preference": rule.get("preference_text")}),
                    "rule_type": _rule_type(rule),
                    "progress": _rule_progress(rule),
                    "debt": round(penalty, 2),
                    "deadline": "generic_month_or_rule_deadline",
                    "repair_windows": "redacted_generic_window",
                    "marginal_violation_cost": round(marginal_violation, 2),
                    "marginal_repair_value": round(penalty if penalty > 0 else 0.0, 2),
                    "actual_penalty": round(penalty, 2),
                    "missed_repair_opportunities": int(missed),
                    "longest_continuous_wait_minutes": "",
                    "wait_minutes": "",
                    "query_minutes_inside_rest_window": "",
                    "no_query_rest_block_used": "",
                    "redaction_status": "literal_banned_terms_redacted",
                    "attribution_method": "official_checker_rule_row",
                }
            )
    rows.extend(_daily_rest_rows(run_dir, run_id, dataset))
    return rows


def _daily_rest_rows(run_dir: Path, run_id: str, dataset: str) -> list[dict[str, Any]]:
    by_day: dict[tuple[str, int], dict[str, Any]] = defaultdict(
        lambda: {
            "wait_minutes": 0,
            "query_minutes_inside_rest_window": 0,
            "longest_continuous_wait_minutes": 0,
            "current_streak": 0,
            "no_query_rest_block_used": 0,
        }
    )
    for _, _, row in iter_action_rows(run_dir):
        driver_hash = _driver_hash(row)
        start = _safe_int((row.get("result") or {}).get("simulation_progress_minutes"), 0) - _safe_int(row.get("step_elapsed_minutes"), 0)
        day = max(0, start // 1440)
        bucket = by_day[(driver_hash, day)]
        query_minutes = _safe_int(row.get("query_scan_cost_minutes"), 0)
        minute_of_day = start % 1440
        if minute_of_day < 9 * 60:
            bucket["query_minutes_inside_rest_window"] += query_minutes
        if _action_name(row) == "wait":
            wait_minutes = _safe_int(row.get("action_exec_cost_minutes"), 0)
            bucket["wait_minutes"] += wait_minutes
            bucket["current_streak"] += wait_minutes
            bucket["longest_continuous_wait_minutes"] = max(bucket["longest_continuous_wait_minutes"], bucket["current_streak"])
            forensic = (_trace(row).get("rescue") or {}).get("wait_forensic", {})
            if isinstance(forensic, dict) and forensic.get("no_query_rest_block_used"):
                bucket["no_query_rest_block_used"] = 1
        else:
            bucket["current_streak"] = 0
    rows = []
    for (driver_hash, day), data in sorted(by_day.items()):
        rows.append(
            {
                "row_type": "daily_rest_matrix",
                "run_id": run_id,
                "dataset_tag": dataset,
                "driver_id_hash": driver_hash,
                "day_index": day,
                "rule_index": "",
                "rule_hash": "",
                "rule_type": "daily_rest_observation",
                "progress": _json_cell({"wait_minutes": data["wait_minutes"]}),
                "debt": "",
                "deadline": "day_end",
                "repair_windows": "redacted_daily_window",
                "marginal_violation_cost": "",
                "marginal_repair_value": "",
                "actual_penalty": "",
                "missed_repair_opportunities": "",
                "longest_continuous_wait_minutes": data["longest_continuous_wait_minutes"],
                "wait_minutes": data["wait_minutes"],
                "query_minutes_inside_rest_window": data["query_minutes_inside_rest_window"],
                "no_query_rest_block_used": data["no_query_rest_block_used"],
                "redaction_status": "literal_banned_terms_redacted",
                "attribution_method": "action_trace_daily_rollup",
            }
        )
    return rows


def _score_rows(run_dir: Path, monthly: dict[str, Any], action_stats: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    run_id = _run_id(run_dir)
    dataset = _dataset_tag(run_dir)
    run_summary = _read_json(run_dir / "run_summary_202603.json")
    failed = run_summary.get("driver_simulation_failures", {}) if isinstance(run_summary.get("driver_simulation_failures"), dict) else {}
    for driver in monthly.get("drivers", []) if isinstance(monthly.get("drivers"), list) else []:
        if not isinstance(driver, dict):
            continue
        income = driver.get("income") if isinstance(driver.get("income"), dict) else {}
        driver_id = str(driver.get("driver_id", "unknown"))
        stats = action_stats["by_driver"].get(driver_id, {})
        gross = _safe_float(income.get("gross_income"))
        cost = _safe_float(income.get("cost"))
        gross_minus_cost = round(gross - cost, 2)
        penalty = _safe_float(income.get("preference_penalty"))
        net = _safe_float(income.get("net_income"))
        expected_net = round(gross_minus_cost - penalty, 2)
        rows.append(
            {
                "run_id": run_id,
                "dataset_tag": dataset,
                "driver_id_hash": _short_hash(driver_id),
                "gross_income": round(gross, 2),
                "distance_cost": round(cost, 2),
                "gross_minus_cost": gross_minus_cost,
                "preference_penalty": round(penalty, 2),
                "official_net": round(net, 2),
                "expected_official_net": expected_net,
                "rounding_delta": round(net - expected_net, 4),
                "net_already_penalty_adjusted": abs(net - expected_net) <= 0.05,
                "proxy_double_count_forbidden": True,
                "take_order": stats.get("take_order", 0),
                "wait": stats.get("wait", 0),
                "reposition": stats.get("reposition", 0),
                "query_minutes": stats.get("query_minutes", 0),
                "query_minutes_per_take": round(stats.get("query_minutes", 0) / max(1, stats.get("take_order", 0)), 2),
                "illegal_actions": stats.get("illegal_actions", 0),
                "rejected_takes": stats.get("rejected_takes", 0),
                "income_calculation_aborted": bool(driver.get("calculation_aborted")),
                "simulation_failure": driver_id in failed,
            }
        )
    return rows


def _action_stats_and_forensics(run_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    run_id = _run_id(run_dir)
    dataset = _dataset_tag(run_dir)
    by_driver: dict[str, Counter] = defaultdict(Counter)
    aggregate = Counter()
    forensics: list[dict[str, Any]] = []
    qwen_latest: dict[str, Any] = {}
    hard_blocks = Counter()
    wait_reasons = Counter()
    rule_penalty = Counter()
    for path, line_no, row in iter_action_rows(run_dir):
        driver_id = str(row.get("driver_id", path.name))
        driver_hash = _short_hash(driver_id)
        action_name = _action_name(row)
        if action_name not in {"take_order", "wait", "reposition"}:
            by_driver[driver_id]["illegal_actions"] += 1
            aggregate["illegal_actions"] += 1
        by_driver[driver_id][action_name] += 1
        aggregate[action_name] += 1
        q_minutes = _safe_int(row.get("query_scan_cost_minutes"), 0)
        by_driver[driver_id]["query_minutes"] += q_minutes
        aggregate["query_minutes"] += q_minutes
        if action_name == "take_order" and (row.get("result") or {}).get("accepted") is False:
            by_driver[driver_id]["rejected_takes"] += 1
            aggregate["rejected_takes"] += 1
        trace = _trace(row)
        rescue = trace.get("rescue") if isinstance(trace.get("rescue"), dict) else {}
        if isinstance(rescue.get("qwen"), dict):
            qwen_latest = rescue["qwen"]
        for reason, count in (rescue.get("hard_block_reason_counts") or {}).items():
            hard_blocks[str(reason)] += _safe_int(count)
        query_row = {
            "row_type": "query",
            "run_id": run_id,
            "dataset_tag": dataset,
            "driver_id_hash": driver_hash,
            "source_file_hash": _short_hash(path.name),
            "line_no": line_no,
            "step": row.get("step", ""),
            "action": action_name,
            "wait_reason": "",
            "query_k": _safe_int(trace.get("query_k", rescue.get("query_k", 0))),
            "query_minutes": q_minutes,
            "returned_count": _safe_int(trace.get("returned_count", rescue.get("returned_count", 0))),
            "actionable_after_query": _safe_int(trace.get("visible_count", rescue.get("actionable_after_query", 0))),
            "positive_net_count": _safe_int(rescue.get("positive_net_count", rescue.get("positive_count", 0))),
            "missed_window_risk": _safe_int(rescue.get("missed_window_risk", 0)),
            "top_candidate_expired_or_unreachable_count": _safe_int((rescue.get("filter_rejection_counts") or {}).get("not_online", 0))
            + _safe_int((rescue.get("filter_rejection_counts") or {}).get("load_window_unreachable", 0)),
            "query_minutes_per_positive_candidate": round(q_minutes / max(1, _safe_int(rescue.get("positive_net_count", rescue.get("positive_count", 0)))), 2),
            "query_reward": _safe_float(rescue.get("query_reward", 0.0)),
            "preference_deadline_risk": _safe_float(trace.get("debt_value", 0.0)),
            "best_order_net": _safe_float(rescue.get("best_order_net", 0.0)),
            "best_order_per_hour": _safe_float(rescue.get("best_order_per_hour", 0.0)),
            "best_take_id_hash": "",
            "best_take_delta_official_net_estimate": "",
            "best_reposition_delta_estimate": "",
            "contributes_continuous_rest": "",
            "contributes_full_rest_day": "",
            "contributes_appointment": "",
            "contributes_market_timing": "",
            "contributes_endgame_safety": "",
            "wait_lock_bug": "",
            "top20_take_hashes": "",
            "hard_filter_reasons": _json_cell(rescue.get("hard_block_reason_counts") or {}),
            "reposition_value": _json_cell(trace.get("reposition_candidates") or []),
            "qwen_compile_calls": _safe_int(qwen_latest.get("compile_calls", 0)),
        }
        forensics.append(query_row)
        if action_name != "wait":
            continue
        forensic = rescue.get("wait_forensic") if isinstance(rescue.get("wait_forensic"), dict) else {}
        reason = str(forensic.get("wait_reason", "") or "unknown")
        wait_reasons[reason] += 1
        if forensic.get("wait_lock_bug"):
            aggregate["wait_lock_bug_count"] += 1
            by_driver[driver_id]["wait_lock_bug_count"] += 1
        if _safe_int(rescue.get("safe_positive_count", 0)) > 0:
            aggregate["positive_net_but_wait"] += 1
            by_driver[driver_id]["positive_net_but_wait"] += 1
        top20 = forensic.get("top20_rejected_take")
        if not isinstance(top20, list):
            top20 = forensic.get("top_5_rejected_take") if isinstance(forensic.get("top_5_rejected_take"), list) else []
        for item in top20:
            if isinstance(item, dict):
                rule_penalty[str(item.get("hard_filter_reason") or "soft")] += 1
        forensics.append(
            {
                **query_row,
                "row_type": "wait",
                "wait_reason": reason,
                "query_k": _safe_int(trace.get("query_k", rescue.get("query_k", 0))),
                "best_take_id_hash": str(forensic.get("best_take_id_hash", "")),
                "best_take_delta_official_net_estimate": forensic.get("best_take_delta_official_net_estimate", ""),
                "best_reposition_delta_estimate": forensic.get("best_reposition_delta_estimate", ""),
                "contributes_continuous_rest": bool(forensic.get("contributes_continuous_rest")),
                "contributes_full_rest_day": bool(forensic.get("contributes_full_rest_day")),
                "contributes_appointment": bool(forensic.get("contributes_appointment")),
                "contributes_market_timing": bool(forensic.get("contributes_market_timing")),
                "contributes_endgame_safety": bool(forensic.get("contributes_endgame_safety")),
                "wait_lock_bug": bool(forensic.get("wait_lock_bug")),
                "top20_take_hashes": ";".join(str(item.get("cargo_id_hash") or item.get("candidate_hash") or "") for item in top20 if isinstance(item, dict)),
                "hard_filter_reasons": _json_cell(Counter(str(item.get("hard_filter_reason") or "soft") for item in top20 if isinstance(item, dict))),
                "reposition_value": _json_cell(forensic.get("top_reposition_candidate") or {}),
            }
        )
    aggregate["qwen_compile_calls"] = _safe_int(qwen_latest.get("compile_calls", 0))
    return {
        "by_driver": by_driver,
        "aggregate": aggregate,
        "hard_blocks": hard_blocks,
        "wait_reasons": wait_reasons,
        "rule_penalty": rule_penalty,
        "qwen_latest": qwen_latest,
    }, forensics


def _experiment_row(run_dir: Path, monthly: dict[str, Any], action_stats: dict[str, Any]) -> dict[str, Any]:
    summary = monthly.get("summary") if isinstance(monthly.get("summary"), dict) else {}
    aggregate = action_stats["aggregate"]
    action_total = aggregate["take_order"] + aggregate["wait"] + aggregate["reposition"]
    gross = cost = penalty = net = 0.0
    income_abort = 0
    for driver in monthly.get("drivers", []) if isinstance(monthly.get("drivers"), list) else []:
        income = driver.get("income") if isinstance(driver.get("income"), dict) else {}
        gross += _safe_float(income.get("gross_income"))
        cost += _safe_float(income.get("cost"))
        penalty += _safe_float(income.get("preference_penalty"))
        net += _safe_float(income.get("net_income"))
        income_abort += int(bool(driver.get("calculation_aborted")))
    run_summary = _read_json(run_dir / "run_summary_202603.json")
    wait_reason = action_stats["wait_reasons"].most_common(1)[0][0] if action_stats["wait_reasons"] else ""
    return {
        "run_id": _run_id(run_dir),
        "dataset_tag": _dataset_tag(run_dir),
        "variant": run_dir.name,
        "official_net": round(net if monthly.get("drivers") else _safe_float(summary.get("total_net_income_all_drivers")), 2),
        "gross_income": round(gross, 2),
        "distance_cost": round(cost, 2),
        "gross_minus_cost": round(gross - cost, 2),
        "preference_penalty": round(penalty if monthly.get("drivers") else _safe_float(summary.get("total_preference_penalty")), 2),
        "take_order": aggregate["take_order"],
        "wait": aggregate["wait"],
        "reposition": aggregate["reposition"],
        "wait_ratio": round(aggregate["wait"] / max(1, action_total), 4),
        "query_minutes": aggregate["query_minutes"],
        "query_minutes_per_take": round(aggregate["query_minutes"] / max(1, aggregate["take_order"]), 2),
        "rule_level_penalty": _json_cell(action_stats["rule_penalty"]),
        "wait_reason": wait_reason,
        "wait_lock_bug_count": aggregate["wait_lock_bug_count"],
        "positive_net_but_wait": aggregate["positive_net_but_wait"],
        "rest_overlap_rejection_count": action_stats["hard_blocks"].get("rest_window_overlap", 0),
        "reposition_value": _json_cell({"reposition_count": aggregate["reposition"]}),
        "qwen_compile_calls": aggregate["qwen_compile_calls"],
        "illegal_actions": aggregate["illegal_actions"],
        "rejected_takes": aggregate["rejected_takes"],
        "income_calculation_aborts": income_abort,
        "simulation_failures": len(run_summary.get("driver_simulation_failures", {}) if isinstance(run_summary.get("driver_simulation_failures"), dict) else {}),
        "simulation_duration_days": run_summary.get("simulation_duration_days", ""),
        "completed_steps": run_summary.get("completed_steps", ""),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_reports(runs_root: Path, output_dir: Path = REPORTS) -> dict[str, Any]:
    score_rows: list[dict[str, Any]] = []
    ledger_rows: list[dict[str, Any]] = []
    forensic_rows: list[dict[str, Any]] = []
    experiment_rows: list[dict[str, Any]] = []
    for run_dir in iter_result_dirs(runs_root):
        monthly = _read_json(run_dir / "monthly_income_202603.json")
        action_stats, forensic = _action_stats_and_forensics(run_dir)
        score_rows.extend(_score_rows(run_dir, monthly, action_stats))
        ledger_rows.extend(_preference_ledger_rows(run_dir, monthly))
        forensic_rows.extend(forensic)
        experiment_rows.append(_experiment_row(run_dir, monthly, action_stats))
    score_fields = [
        "run_id",
        "dataset_tag",
        "driver_id_hash",
        "gross_income",
        "distance_cost",
        "gross_minus_cost",
        "preference_penalty",
        "official_net",
        "expected_official_net",
        "rounding_delta",
        "net_already_penalty_adjusted",
        "proxy_double_count_forbidden",
        "take_order",
        "wait",
        "reposition",
        "query_minutes",
        "query_minutes_per_take",
        "illegal_actions",
        "rejected_takes",
        "income_calculation_aborted",
        "simulation_failure",
    ]
    ledger_fields = [
        "row_type",
        "run_id",
        "dataset_tag",
        "driver_id_hash",
        "day_index",
        "rule_index",
        "rule_hash",
        "rule_type",
        "progress",
        "debt",
        "deadline",
        "repair_windows",
        "marginal_violation_cost",
        "marginal_repair_value",
        "actual_penalty",
        "missed_repair_opportunities",
        "longest_continuous_wait_minutes",
        "wait_minutes",
        "query_minutes_inside_rest_window",
        "no_query_rest_block_used",
        "redaction_status",
        "attribution_method",
    ]
    forensic_fields = [
        "row_type",
        "run_id",
        "dataset_tag",
        "driver_id_hash",
        "source_file_hash",
        "line_no",
        "step",
        "action",
        "wait_reason",
        "query_k",
        "query_minutes",
        "returned_count",
        "actionable_after_query",
        "positive_net_count",
        "missed_window_risk",
        "top_candidate_expired_or_unreachable_count",
        "query_minutes_per_positive_candidate",
        "query_reward",
        "preference_deadline_risk",
        "best_order_net",
        "best_order_per_hour",
        "best_take_id_hash",
        "best_take_delta_official_net_estimate",
        "best_reposition_delta_estimate",
        "contributes_continuous_rest",
        "contributes_full_rest_day",
        "contributes_appointment",
        "contributes_market_timing",
        "contributes_endgame_safety",
        "wait_lock_bug",
        "top20_take_hashes",
        "hard_filter_reasons",
        "reposition_value",
        "qwen_compile_calls",
    ]
    experiment_fields = [
        "run_id",
        "dataset_tag",
        "variant",
        "official_net",
        "gross_income",
        "distance_cost",
        "gross_minus_cost",
        "preference_penalty",
        "take_order",
        "wait",
        "reposition",
        "wait_ratio",
        "query_minutes",
        "query_minutes_per_take",
        "rule_level_penalty",
        "wait_reason",
        "wait_lock_bug_count",
        "positive_net_but_wait",
        "rest_overlap_rejection_count",
        "reposition_value",
        "qwen_compile_calls",
        "illegal_actions",
        "rejected_takes",
        "income_calculation_aborts",
        "simulation_failures",
        "simulation_duration_days",
        "completed_steps",
    ]
    _write_csv(output_dir / "score_accountant.csv", score_rows, score_fields)
    _write_csv(output_dir / "preference_state_ledger.csv", ledger_rows, ledger_fields)
    _write_csv(output_dir / "forensics_samples.csv", forensic_rows, forensic_fields)
    _write_csv(output_dir / "next_build_experiments.csv", experiment_rows, experiment_fields)
    return {
        "runs": len(experiment_rows),
        "score_rows": len(score_rows),
        "ledger_rows": len(ledger_rows),
        "forensic_rows": len(forensic_rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Next Build v4 score-accounting CSV artifacts.")
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs" / "next_build")
    parser.add_argument("--output-dir", type=Path, default=REPORTS)
    args = parser.parse_args()
    payload = build_reports(args.runs_root, args.output_dir)
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
