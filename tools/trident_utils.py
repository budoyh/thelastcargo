"""Shared Trident ablation and parameter-search helpers.

These helpers intentionally stay outside ``demo/agent``.  They only run or
summarize official-style local evaluations and never feed scorer outputs back
into runtime policy code.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RUNS = ROOT / "runs"

TRIDENT_EXPERIMENT_FIELDS = [
    "stage",
    "variant_name",
    "variant",
    "dataset",
    "simulation_days",
    "run_id",
    "status",
    "official_net",
    "gross_income",
    "distance_cost",
    "gross_minus_cost",
    "preference_penalty",
    "official_net_delta_vs_b0",
    "gross_delta_vs_b0",
    "preference_penalty_delta_vs_b0",
    "expected_official_net",
    "score_accounting_ok",
    "take_count",
    "wait_count",
    "reposition_count",
    "query_minutes",
    "query_minutes_per_take",
    "qwen_compile_calls",
    "qwen_compile_cache_hits",
    "qwen_compile_or_cache_hit_count",
    "qwen_link_calls",
    "qwen_link_or_cache_hit_count",
    "qwen_auditor_calls",
    "qwen_audit_adjustment_nonzero_count",
    "controller_scored_candidate_count",
    "candidate_rule_eval_count",
    "score_changed_by_controller_count",
    "changed_decision_count",
    "hard_block_count",
    "soft_penalty_count",
    "repair_value_count",
    "visible_graph_used_count",
    "terminal_value_used_count",
    "income_abort_count",
    "illegal_count",
    "rejected_take_count",
    "simulation_failures",
    "abort_count",
    "failure_count",
    "objective_score",
    "keep_or_kill",
    "params_json",
    "env_json",
    "notes",
    "command",
    "exit_code",
    "started_at",
    "finished_at",
    "duration_seconds",
]

DATA_DIRS = {
    "20260529": ROOT / "demo" / "server" / "data",
    "20260509": ROOT / "_offline_reference_20260509" / "demo" / "server" / "data",
}


def current_python() -> str:
    return sys.executable


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def json_cell(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def run_id(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def dataset_data_dir(dataset: str) -> Path:
    return DATA_DIRS.get(dataset, DATA_DIRS["20260529"])


def dataset_income_command(dataset: str, run_dir: Path) -> list[str] | None:
    if dataset != "20260509":
        return None
    old_demo = ROOT / "_offline_reference_20260509" / "demo"
    if not (old_demo / "calc_monthly_income.py").is_file():
        return None
    return [
        current_python(),
        str(old_demo / "calc_monthly_income.py"),
        "--project-root",
        str(old_demo),
        "--results-dir",
        str(run_dir),
    ]


def clean_eval_env(overrides: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env.pop("CROWN_Y_DISABLE_RUNTIME_QWEN", None)
    env.pop("CROWN_EXACT_ENABLE_VISIBLE_GRAPH_MPC", None)
    env.update({key: str(value) for key, value in (overrides or {}).items() if value is not None})
    return env


def run_local_eval(
    *,
    dataset: str,
    variant: str,
    run_dir: Path,
    simulation_days: int,
    env_overrides: dict[str, str] | None = None,
    max_steps: int | None = None,
) -> tuple[int, str, float, str, str]:
    run_dir.mkdir(parents=True, exist_ok=True)
    env = clean_eval_env({"CROWN_Y_VARIANT": variant, **(env_overrides or {})})
    cmd = [
        current_python(),
        "tools/run_local_eval.py",
        "--simulation-days",
        str(simulation_days),
        "--variant",
        variant,
        "--results-dir",
        str(run_dir),
        "--data-dir",
        str(dataset_data_dir(dataset)),
    ]
    if max_steps is not None:
        cmd.extend(["--max-steps", str(max_steps)])
    if dataset == "20260509":
        cmd.append("--skip-income")
    command_text = " ".join(cmd)
    started = time.strftime("%Y-%m-%dT%H:%M:%S")
    start = time.monotonic()
    rc = subprocess.run(cmd, cwd=str(ROOT), env=env, check=False).returncode
    if rc == 0:
        income_cmd = dataset_income_command(dataset, run_dir)
        if income_cmd is not None:
            rc = subprocess.run(income_cmd, cwd=str(ROOT), env=env, check=False).returncode
            command_text += " && " + " ".join(income_cmd)
    duration = round(time.monotonic() - start, 2)
    finished = time.strftime("%Y-%m-%dT%H:%M:%S")
    return rc, command_text, duration, started, finished


def iter_action_rows(run_dir: Path):
    for path in sorted(run_dir.glob("actions_202603_*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line_no, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                yield path, line_no, row


def _action_name(row: dict[str, Any]) -> str:
    action = row.get("action") if isinstance(row.get("action"), dict) else {}
    return str(action.get("action", "")).strip()


def _trace(row: dict[str, Any]) -> dict[str, Any]:
    action = row.get("action") if isinstance(row.get("action"), dict) else {}
    trace = action.get("agent_trace") if isinstance(action.get("agent_trace"), dict) else {}
    return trace if isinstance(trace, dict) else {}


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _max_payload_int(payload: dict[str, Any], key: str, current: int = 0) -> int:
    return max(current, _safe_int(payload.get(key)))


def objective_score(row: dict[str, Any]) -> float:
    official = _safe_float(row.get("official_net"))
    gross = _safe_float(row.get("gross_minus_cost"))
    penalty = _safe_float(row.get("preference_penalty"))
    bad = (
        _safe_int(row.get("income_abort_count"))
        + _safe_int(row.get("illegal_count"))
        + _safe_int(row.get("rejected_take_count"))
        + _safe_int(row.get("simulation_failures"))
    )
    return round(official - 0.5 * max(0.0, 52000.0 - gross) - 0.8 * max(0.0, penalty - 28000.0) - 10000.0 * bad, 2)


def keep_or_kill(row: dict[str, Any], b0_net: float | None = None) -> str:
    if str(row.get("status")) not in {"OK", "EXISTING"}:
        return "kill_internal_failure"
    if any(_safe_int(row.get(key)) > 0 for key in ("income_abort_count", "illegal_count", "rejected_take_count", "simulation_failures")):
        return "kill_invalid_run"
    if b0_net is not None and _safe_float(row.get("official_net")) < b0_net:
        return "kill_below_b0"
    if _safe_float(row.get("official_net")) >= 30000.0 and _safe_float(row.get("preference_penalty")) <= 28000.0:
        return "keep_experimental_candidate"
    return "diagnostic_only"


def apply_b0_deltas(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    b0_by_dataset: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("variant_name") != "B0_historical_rescue_restored":
            continue
        if row.get("official_net") in {"", None}:
            continue
        dataset = str(row.get("dataset", ""))
        if row.get("stage") == "B0" or dataset not in b0_by_dataset:
            b0_by_dataset[dataset] = row

    for row in rows:
        b0 = b0_by_dataset.get(str(row.get("dataset", "")))
        if not b0 or row.get("official_net") in {"", None}:
            row.setdefault("official_net_delta_vs_b0", "")
            row.setdefault("gross_delta_vs_b0", "")
            row.setdefault("preference_penalty_delta_vs_b0", "")
            continue
        net_delta = round(_safe_float(row.get("official_net")) - _safe_float(b0.get("official_net")), 2)
        gross_delta = round(_safe_float(row.get("gross_minus_cost")) - _safe_float(b0.get("gross_minus_cost")), 2)
        penalty_delta = round(_safe_float(row.get("preference_penalty")) - _safe_float(b0.get("preference_penalty")), 2)
        row["official_net_delta_vs_b0"] = net_delta
        row["gross_delta_vs_b0"] = gross_delta
        row["preference_penalty_delta_vs_b0"] = penalty_delta
        if row.get("variant_name") == "B0_historical_rescue_restored":
            row["keep_or_kill"] = "keep_b0_reference"
        elif str(row.get("status")) not in {"OK", "EXISTING"}:
            row["keep_or_kill"] = keep_or_kill(row, _safe_float(b0.get("official_net")))
        elif any(_safe_int(row.get(key)) > 0 for key in ("income_abort_count", "illegal_count", "rejected_take_count", "simulation_failures")):
            row["keep_or_kill"] = "kill_invalid_run"
        elif _safe_float(row.get("official_net")) >= 30000.0 and _safe_float(row.get("preference_penalty")) <= 28000.0:
            row["keep_or_kill"] = "keep_experimental_candidate"
        elif net_delta > 0:
            row["keep_or_kill"] = "keep_score_positive_vs_b0"
        else:
            row["keep_or_kill"] = "kill_below_b0"
    return rows


def summarize_trident_run(
    run_dir: Path,
    *,
    stage: str,
    variant_name: str,
    variant: str,
    dataset: str,
    simulation_days: int,
    status: str = "EXISTING",
    notes: str = "",
    params: dict[str, Any] | None = None,
    env_overrides: dict[str, str] | None = None,
    command: str = "",
    exit_code: int | str = "",
    started_at: str = "",
    finished_at: str = "",
    duration_seconds: float | str = "",
) -> dict[str, Any]:
    monthly = read_json(run_dir / "monthly_income_202603.json")
    run_summary = read_json(run_dir / "run_summary_202603.json")
    if not monthly:
        row = {
            "stage": stage,
            "variant_name": variant_name,
            "variant": variant,
            "dataset": dataset,
            "simulation_days": simulation_days,
            "run_id": run_id(run_dir),
            "status": "MISSING_RUN" if status == "EXISTING" else status,
            "params_json": json_cell(params or {}),
            "env_json": json_cell(env_overrides or {}),
            "notes": notes or "missing monthly_income_202603.json",
            "command": command,
            "exit_code": exit_code,
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_seconds": duration_seconds,
        }
        row["objective_score"] = ""
        row["keep_or_kill"] = "planned_not_evaluated" if status == "PLANNED" else "kill_missing_run"
        return row

    gross = cost = penalty = net = 0.0
    income_abort_count = 0
    drivers = monthly.get("drivers") if isinstance(monthly.get("drivers"), list) else []
    if drivers:
        for driver in drivers:
            if not isinstance(driver, dict):
                continue
            income = driver.get("income") if isinstance(driver.get("income"), dict) else {}
            gross += _safe_float(income.get("gross_income"))
            cost += _safe_float(income.get("cost"))
            penalty += _safe_float(income.get("preference_penalty"))
            net += _safe_float(income.get("net_income"))
            income_abort_count += int(bool(driver.get("calculation_aborted")))
    else:
        summary = monthly.get("summary") if isinstance(monthly.get("summary"), dict) else {}
        net = _safe_float(summary.get("total_net_income_all_drivers"))
        penalty = _safe_float(summary.get("total_preference_penalty"))

    counts = {"take_order": 0, "wait": 0, "reposition": 0, "other": 0}
    rejected_take_count = 0
    query_minutes = 0
    latest_qwen: dict[str, Any] = {}
    latest_ptt: dict[str, Any] = {}
    latest_firewall: dict[str, Any] = {}
    visible_graph_used_count = 0
    terminal_value_used_count = 0
    for _, _, action_row in iter_action_rows(run_dir):
        name = _action_name(action_row)
        if name in counts:
            counts[name] += 1
        else:
            counts["other"] += 1
        if name == "take_order" and (action_row.get("result") or {}).get("accepted") is False:
            rejected_take_count += 1
        query_minutes += _safe_int(action_row.get("query_scan_cost_minutes"))
        rescue = _trace(action_row).get("rescue")
        rescue = rescue if isinstance(rescue, dict) else {}
        qwen = rescue.get("qwen") if isinstance(rescue.get("qwen"), dict) else {}
        if qwen:
            latest_qwen = qwen
        ptt = rescue.get("ptt") if isinstance(rescue.get("ptt"), dict) else {}
        stats = ptt.get("stats") if isinstance(ptt.get("stats"), dict) else {}
        if stats:
            latest_ptt = stats
        firewall = ptt.get("firewall") if isinstance(ptt.get("firewall"), dict) else {}
        if firewall:
            latest_firewall = firewall
        graph = rescue.get("visible_graph_mpc") if isinstance(rescue.get("visible_graph_mpc"), dict) else {}
        if graph.get("enabled"):
            visible_graph_used_count += 1
            if _safe_float(graph.get("best_path_score")):
                terminal_value_used_count += 1

    qwen_compile = max(_safe_int(latest_qwen.get("compile_calls")), _safe_int(latest_ptt.get("compile_calls")))
    qwen_cache = max(_safe_int(latest_qwen.get("cache_hits")), _safe_int(latest_ptt.get("cache_hits")))
    qwen_link = max(_safe_int(latest_qwen.get("linker_calls")), _safe_int(latest_ptt.get("linker_call_count")))
    qwen_auditor = _safe_int(latest_qwen.get("auditor_calls"))
    gross_minus_cost = round(gross - cost, 2)
    expected_net = round(gross_minus_cost - penalty, 2)
    sim_failures = run_summary.get("driver_simulation_failures")
    sim_failure_count = len(sim_failures) if isinstance(sim_failures, dict) else 0
    row = {
        "stage": stage,
        "variant_name": variant_name,
        "variant": variant,
        "dataset": dataset,
        "simulation_days": simulation_days,
        "run_id": run_id(run_dir),
        "status": status,
        "official_net": round(net, 2),
        "gross_income": round(gross, 2),
        "distance_cost": round(cost, 2),
        "gross_minus_cost": gross_minus_cost,
        "preference_penalty": round(penalty, 2),
        "expected_official_net": expected_net,
        "score_accounting_ok": abs(round(net - expected_net, 2)) <= 0.05,
        "take_count": counts["take_order"],
        "wait_count": counts["wait"],
        "reposition_count": counts["reposition"],
        "query_minutes": query_minutes,
        "query_minutes_per_take": round(query_minutes / max(1, counts["take_order"]), 2),
        "qwen_compile_calls": qwen_compile,
        "qwen_compile_cache_hits": qwen_cache,
        "qwen_compile_or_cache_hit_count": qwen_compile + qwen_cache,
        "qwen_link_calls": qwen_link,
        "qwen_link_or_cache_hit_count": qwen_link + qwen_cache,
        "qwen_auditor_calls": qwen_auditor,
        "qwen_audit_adjustment_nonzero_count": max(
            _safe_int(latest_qwen.get("qwen_audit_adjustment_nonzero_count")),
            _safe_int(latest_qwen.get("audit_adjustment_nonzero_count")),
            _safe_int(latest_ptt.get("auditor_changed_score_count")),
            _safe_int(latest_firewall.get("auditor_changed_score_count")),
        ),
        "controller_scored_candidate_count": _safe_int(latest_ptt.get("controller_scored_candidate_count")),
        "candidate_rule_eval_count": _safe_int(latest_ptt.get("candidate_rule_eval_count")),
        "score_changed_by_controller_count": _safe_int(latest_ptt.get("score_changed_by_controller_count")),
        "changed_decision_count": _safe_int(latest_ptt.get("changed_decision_count")),
        "hard_block_count": _safe_int(latest_ptt.get("hard_block_count")),
        "soft_penalty_count": _safe_int(latest_ptt.get("soft_penalty_count")),
        "repair_value_count": _safe_int(latest_ptt.get("repair_value_count")),
        "visible_graph_used_count": visible_graph_used_count,
        "terminal_value_used_count": terminal_value_used_count,
        "income_abort_count": income_abort_count,
        "illegal_count": counts["other"],
        "rejected_take_count": rejected_take_count,
        "simulation_failures": sim_failure_count,
        "abort_count": income_abort_count + sim_failure_count,
        "failure_count": income_abort_count + sim_failure_count + counts["other"] + rejected_take_count,
        "params_json": json_cell(params or {}),
        "env_json": json_cell(env_overrides or {}),
        "notes": notes,
        "command": command,
        "exit_code": exit_code,
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_seconds": duration_seconds,
    }
    row["objective_score"] = objective_score(row)
    row["keep_or_kill"] = keep_or_kill(row)
    return row


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] = TRIDENT_EXPERIMENT_FIELDS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def merge_rows(existing: list[dict[str, Any]], new_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(row: dict[str, Any]) -> tuple[str, str, str, str]:
        return (
            str(row.get("dataset", "")),
            str(row.get("stage", "")),
            str(row.get("variant_name", "")),
            str(row.get("run_id", "")),
        )

    by_key = {key(row): row for row in existing}
    for row in new_rows:
        by_key[key(row)] = row
    return sorted(
        by_key.values(),
        key=lambda row: (
            str(row.get("dataset", "")),
            str(row.get("stage", "")),
            str(row.get("variant_name", "")),
            str(row.get("run_id", "")),
        ),
    )


def write_merged_experiments(out: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged = merge_rows(read_csv(out), rows)
    merged = apply_b0_deltas(merged)
    write_csv(out, merged)
    return merged
