"""Shared helpers for CROWN-Delta MPC offline reports."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RUNS = ROOT / "runs"


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def short_hash(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def json_cell(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def dataset_tag(path: Path) -> str:
    text = str(path).replace("\\", "/").lower()
    if "20260509" in text or "0509" in text:
        return "20260509"
    if "20260529" in text or "latest" in text or "pce/20260529" in text:
        return "20260529"
    return "unknown"


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


def action_name(row: dict[str, Any]) -> str:
    action = row.get("action") if isinstance(row.get("action"), dict) else {}
    return str(action.get("action", "")).strip()


def trace(row: dict[str, Any]) -> dict[str, Any]:
    action = row.get("action") if isinstance(row.get("action"), dict) else {}
    raw = action.get("agent_trace") if isinstance(action, dict) else {}
    return raw if isinstance(raw, dict) else {}


def run_id(run_dir: Path) -> str:
    try:
        return str(run_dir.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(run_dir)


def summarize_run(run_dir: Path, *, variant: str | None = None, notes: str = "") -> dict[str, Any]:
    monthly = read_json(run_dir / "monthly_income_202603.json")
    run_summary = read_json(run_dir / "run_summary_202603.json")
    gross = cost = penalty = net = 0.0
    income_aborts = 0
    qwen_compile_calls = 0
    if isinstance(monthly.get("drivers"), list):
        for driver in monthly["drivers"]:
            if not isinstance(driver, dict):
                continue
            income = driver.get("income") if isinstance(driver.get("income"), dict) else {}
            gross += float(income.get("gross_income", 0.0) or 0.0)
            cost += float(income.get("cost", 0.0) or 0.0)
            penalty += float(income.get("preference_penalty", 0.0) or 0.0)
            net += float(income.get("net_income", 0.0) or 0.0)
            income_aborts += int(bool(driver.get("calculation_aborted")))
            usage = driver.get("token_usage") if isinstance(driver.get("token_usage"), dict) else {}
            qwen_compile_calls += int(usage.get("compile_calls", 0) or 0) if "compile_calls" in usage else 0
    else:
        summary = monthly.get("summary") if isinstance(monthly.get("summary"), dict) else {}
        net = float(summary.get("total_net_income_all_drivers", 0.0) or 0.0)
        penalty = float(summary.get("total_preference_penalty", 0.0) or 0.0)
    counts = {"take_order": 0, "wait": 0, "reposition": 0, "other": 0}
    rejected = illegal = query_minutes = macro_completed = macro_started = 0
    macro_gain = 0.0
    top5_count = 0
    latest_qwen: dict[str, Any] = {}
    for _, _, row in iter_action_rows(run_dir):
        name = action_name(row)
        if name in counts:
            counts[name] += 1
        else:
            counts["other"] += 1
            illegal += 1
        if name == "take_order" and (row.get("result") or {}).get("accepted") is False:
            rejected += 1
        query_minutes += int(row.get("query_scan_cost_minutes", 0) or 0)
        tr = trace(row)
        rescue = tr.get("rescue") if isinstance(tr.get("rescue"), dict) else {}
        if isinstance(rescue.get("qwen"), dict):
            latest_qwen = rescue["qwen"]
        macro = rescue.get("macro") if isinstance(rescue.get("macro"), dict) else {}
        macro_started = max(macro_started, int(macro.get("macro_started_count", 0) or 0))
        macro_completed = max(macro_completed, int(macro.get("macro_completed_count", 0) or 0))
        macro_gain = max(macro_gain, float(macro.get("official_delta_measured_macro_gain", 0.0) or 0.0))
        if isinstance(tr.get("top5_delta_mpc_decomposition"), list):
            top5_count += 1
    qwen_compile_calls = max(qwen_compile_calls, int(latest_qwen.get("compile_calls", 0) or 0))
    gross_minus_cost = round(gross - cost, 2)
    expected_net = round(gross_minus_cost - penalty, 2)
    return {
        "run_id": run_id(run_dir),
        "dataset": dataset_tag(run_dir),
        "variant": variant or run_dir.name,
        "sim_days": run_summary.get("simulation_duration_days", ""),
        "gross_income": round(gross, 2),
        "distance_cost": round(cost, 2),
        "gross_minus_cost": gross_minus_cost,
        "preference_penalty": round(penalty, 2),
        "official_net": round(net, 2),
        "expected_official_net": expected_net,
        "score_accounting_ok": abs(round(net - expected_net, 2)) <= 0.05,
        "take_count": counts["take_order"],
        "wait_count": counts["wait"],
        "reposition_count": counts["reposition"],
        "query_minutes": query_minutes,
        "query_minutes_per_take": round(query_minutes / max(1, counts["take_order"]), 2),
        "illegal_count": illegal,
        "rejected_take_count": rejected,
        "income_abort_count": income_aborts,
        "simulation_failures": len(run_summary.get("driver_simulation_failures", {}) if isinstance(run_summary.get("driver_simulation_failures"), dict) else {}),
        "qwen_compile_calls": qwen_compile_calls,
        "qwen_auditor_calls": int(latest_qwen.get("auditor_calls", 0) or 0),
        "macro_started_count": macro_started,
        "macro_completed_count": macro_completed,
        "official_delta_measured_macro_gain": round(macro_gain, 2),
        "top5_decomposition_steps": top5_count,
        "notes": notes,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_command(cmd: list[str], *, env: dict[str, str] | None = None) -> int:
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, cwd=str(ROOT), env=env, check=False).returncode


def current_python() -> str:
    return sys.executable
