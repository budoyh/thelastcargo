"""Shared metrics for score-rescue reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def iter_rows(results_dir: Path):
    for path in sorted(results_dir.glob("actions_202603_*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                yield row


def summarize_run(results_dir: Path) -> dict[str, Any]:
    monthly_path = results_dir / "monthly_income_202603.json"
    run_path = results_dir / "run_summary_202603.json"
    monthly = json.loads(monthly_path.read_text(encoding="utf-8")) if monthly_path.exists() else {"summary": {}}
    run = json.loads(run_path.read_text(encoding="utf-8")) if run_path.exists() else {}
    counts = {"take_order": 0, "wait": 0, "reposition": 0, "other": 0, "rejected_take": 0}
    query_minutes = 0
    illegal = 0
    feasible_positive_but_wait = 0
    wait_reasons: dict[str, int] = {}
    hard_blocks: dict[str, int] = {}
    qwen: dict[str, Any] = {}
    top_rejected: list[dict[str, Any]] = []
    consecutive_wait = 0
    max_consecutive_wait = 0
    wait_streaks: list[int] = []
    for row in iter_rows(results_dir):
        action = row.get("action") if isinstance(row.get("action"), dict) else {}
        name = str(action.get("action", "")).strip()
        if name not in {"take_order", "wait", "reposition"}:
            illegal += 1
            name = "other"
        counts[name if name in counts else "other"] += 1
        if name == "take_order" and (row.get("result") or {}).get("accepted") is False:
            counts["rejected_take"] += 1
        query_minutes += int(row.get("query_scan_cost_minutes", 0) or 0)
        trace = action.get("agent_trace") if isinstance(action, dict) else {}
        trace = trace if isinstance(trace, dict) else {}
        rescue = trace.get("rescue", {})
        rescue = rescue if isinstance(rescue, dict) else {}
        if rescue.get("qwen"):
            qwen = rescue["qwen"]
        if name == "wait":
            consecutive_wait += 1
            max_consecutive_wait = max(max_consecutive_wait, consecutive_wait)
            if int(rescue.get("safe_positive_count", 0) or 0) > 0:
                feasible_positive_but_wait += 1
            forensic = rescue.get("wait_forensic", {})
            forensic = forensic if isinstance(forensic, dict) else {}
            reason = str(forensic.get("wait_reason", "") or "unknown")
            wait_reasons[reason] = wait_reasons.get(reason, 0) + 1
            for item in forensic.get("top_5_rejected_take", []) if isinstance(forensic.get("top_5_rejected_take"), list) else []:
                if isinstance(item, dict) and len(top_rejected) < 20:
                    top_rejected.append(item)
        else:
            if consecutive_wait:
                wait_streaks.append(consecutive_wait)
            consecutive_wait = 0
        for key, value in (rescue.get("hard_block_reason_counts") or {}).items():
            hard_blocks[str(key)] = hard_blocks.get(str(key), 0) + int(value)
    if consecutive_wait:
        wait_streaks.append(consecutive_wait)
    action_total = counts["take_order"] + counts["wait"] + counts["reposition"]
    net = float(monthly.get("summary", {}).get("total_net_income_all_drivers", 0.0) or 0.0)
    penalty = float(monthly.get("summary", {}).get("total_preference_penalty", 0.0) or 0.0)
    return {
        "results_dir": str(results_dir),
        "net": net,
        "penalty": penalty,
        "proxy_score": net - penalty,
        "failed_driver_count": int(monthly.get("summary", {}).get("failed_driver_count", 0) or 0),
        "simulation_failures": run.get("driver_simulation_failures", {}),
        "simulation_duration_days": run.get("simulation_duration_days"),
        "completed_steps": run.get("completed_steps"),
        "counts": counts,
        "query_minutes": query_minutes,
        "query_minutes_per_take": round(query_minutes / max(1, counts["take_order"]), 2),
        "wait_ratio": round(counts["wait"] / max(1, action_total), 4),
        "illegal_actions": illegal,
        "feasible_positive_cargo_but_wait": feasible_positive_but_wait,
        "wait_regret_v2": max(0, counts["wait"] - len(wait_streaks)),
        "max_consecutive_wait": max_consecutive_wait,
        "p95_consecutive_wait": sorted(wait_streaks)[int(0.95 * (len(wait_streaks) - 1))] if wait_streaks else 0,
        "wait_reasons": wait_reasons,
        "hard_blocks": hard_blocks,
        "qwen": qwen,
        "top_rejected": top_rejected,
        "monthly": monthly,
        "run": run,
    }


def markdown_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return lines
