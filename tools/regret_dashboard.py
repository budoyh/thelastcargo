"""Build regret summaries from simulation action traces."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "regret_dashboard.md"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.score_rescue_metrics import markdown_table, summarize_run  # noqa: E402
REGRET_KEYS = (
    "query_too_big",
    "query_too_small",
    "long_order_trap",
    "wait_regret",
    "reposition_not_recovered",
    "preference_late_panic",
)
RESCUE_ABLATION_RUNS = ("a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7")


@dataclass
class RegretStats:
    counts: dict[str, int] = field(default_factory=lambda: {k: 0 for k in REGRET_KEYS})
    query_minutes: int = 0
    reposition_cost: float = 0.0
    steps: int = 0
    illegal_actions: int = 0
    skipped_lines: int = 0

    def add(self, key: str, amount: int = 1) -> None:
        self.counts[key] = self.counts.get(key, 0) + amount


def build_stats(results_dir: Path) -> RegretStats:
    stats = RegretStats()
    previous_by_driver: dict[str, dict[str, Any]] = {}
    pending_repositions: dict[str, list[dict[str, float]]] = {}
    for path in sorted(results_dir.glob("actions_202603_*.jsonl")):
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    stats.skipped_lines += 1
                    continue
                if not isinstance(row, dict):
                    stats.skipped_lines += 1
                    continue
                stats.steps += 1
                action = row.get("action", {})
                name = str(action.get("action", "")).strip().lower()
                if name not in {"take_order", "wait", "reposition"}:
                    stats.illegal_actions += 1
                query_cost = int(row.get("query_scan_cost_minutes", 0) or 0)
                stats.query_minutes += query_cost
                trace = action.get("agent_trace") if isinstance(action, dict) else {}
                trace = trace if isinstance(trace, dict) else {}
                visible_count = int(trace.get("visible_count", 0) or 0)
                chosen = trace.get("chosen", {})
                chosen = chosen if isinstance(chosen, dict) else {"candidate_id": str(chosen)}
                score = float(chosen.get("score", 0.0) or 0.0)
                driver = str(row.get("driver_id", path.name))
                step_end = int((row.get("result") or {}).get("simulation_progress_minutes", 0) or 0)
                if query_cost > 12 and score <= 0:
                    stats.add("query_too_big")
                if query_cost <= 5 and visible_count <= 2 and name == "wait":
                    stats.add("query_too_small")
                if name == "take_order" and int(row.get("action_exec_cost_minutes", 0) or 0) > 720:
                    stats.add("long_order_trap")
                if name == "wait":
                    prev = previous_by_driver.get(driver)
                    if prev and prev.get("action", {}).get("action") == "wait":
                        stats.add("wait_regret")
                if name == "reposition":
                    gate = trace.get("reposition_gate", {})
                    gate = gate if isinstance(gate, dict) else {}
                    cost = float(gate.get("reposition_cost", 0.0) or 0.0)
                    stats.reposition_cost += cost
                    pending_repositions.setdefault(driver, []).append(
                        {
                            "start": float(step_end),
                            "cost": cost,
                            "gain": 0.0,
                            "deadline": float(step_end + 12 * 60),
                        }
                    )
                if name == "take_order" and (row.get("result") or {}).get("accepted") is True:
                    components = chosen.get("components", {})
                    components = components if isinstance(components, dict) else {}
                    direct = float(components.get("direct_money", 0.0) or 0.0)
                    still_pending = []
                    for item in pending_repositions.get(driver, []):
                        if step_end <= item["deadline"]:
                            item["gain"] += max(0.0, direct)
                        if item["gain"] < item["cost"] and step_end < item["deadline"]:
                            still_pending.append(item)
                        elif item["gain"] < item["cost"] and step_end >= item["deadline"]:
                            stats.add("reposition_not_recovered")
                    pending_repositions[driver] = still_pending
                if float(trace.get("debt_value", 0.0) or 0.0) > 220.0:
                    sim_end = str(row.get("simulation_end_time", ""))
                    if "-03-2" in sim_end or "-03-3" in sim_end:
                        stats.add("preference_late_panic")
                previous_by_driver[driver] = row
    for items in pending_repositions.values():
        for item in items:
            if item["gain"] < item["cost"]:
                stats.add("reposition_not_recovered")
    return stats


def write_report(stats: RegretStats, results_dir: Path, out: Path = REPORT) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Regret Dashboard",
        "",
        f"- results_dir: `{results_dir}`",
        f"- steps: {stats.steps}",
        f"- query_minutes: {stats.query_minutes}",
        f"- illegal_actions: {stats.illegal_actions}",
        f"- skipped_lines: {stats.skipped_lines}",
        f"- reposition_cost_proxy: {round(stats.reposition_cost, 2)}",
        "",
        "| regret | count |",
        "|---|---:|",
    ]
    for key in REGRET_KEYS:
        lines.append(f"| {key} | {stats.counts.get(key, 0)} |")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_rescue_report(runs_root: Path, out: Path) -> list[dict[str, Any]]:
    payload = []
    rows = []
    if any((runs_root / name).is_dir() for name in RESCUE_ABLATION_RUNS):
        paths = [runs_root / name for name in RESCUE_ABLATION_RUNS if (runs_root / name).is_dir()]
    else:
        paths = sorted(p for p in runs_root.iterdir() if p.is_dir())
    for path in paths:
        if not (path / "actions_202603_D001.jsonl").exists() and not (path / "monthly_income_202603.json").exists():
            continue
        item = summarize_run(path)
        regret = build_stats(path)
        payload.append({"name": path.name, **item, "regret_counts": regret.counts})
        counts = item["counts"]
        rows.append(
            [
                path.name,
                item["net"],
                counts["take_order"],
                counts["wait"],
                counts["reposition"],
                item["wait_ratio"],
                item["query_minutes_per_take"],
                item["wait_regret_v2"],
                item["feasible_positive_cargo_but_wait"],
                counts["rejected_take"],
                item["illegal_actions"],
                regret.counts.get("query_too_big", 0),
                regret.counts.get("query_too_small", 0),
                regret.counts.get("long_order_trap", 0),
                regret.counts.get("wait_regret", 0),
                regret.counts.get("reposition_not_recovered", 0),
                regret.counts.get("preference_late_panic", 0),
            ]
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Regret Dashboard V2",
        "",
        f"- runs_root: `{runs_root}`",
        "- categories: query_too_big, query_too_small, long_order_trap, wait_regret, reposition_not_recovered, preference_late_panic",
        "- v2 additions: feasible_positive_cargo_but_wait, query_minutes_per_take, wait_ratio, rejected_take, illegal_actions",
        "",
        *markdown_table(
            [
                "run",
                "net",
                "take",
                "wait",
                "repo",
                "wait_ratio",
                "q_min/take",
                "wait_regret_v2",
                "positive_wait",
                "rejected",
                "illegal",
                "query_too_big",
                "query_too_small",
                "long_order_trap",
                "wait_regret",
                "reposition_not_recovered",
                "preference_late_panic",
            ],
            rows,
        ),
        "",
    ]
    if payload:
        best = max(payload, key=lambda item: float(item.get("net", 0.0)))
        lines.extend(
            [
                f"Best net run: `{best['name']}` with net `{best['net']}`, wait_ratio `{best['wait_ratio']}`, "
                f"wait_regret_v2 `{best['wait_regret_v2']}`, positive_wait `{best['feasible_positive_cargo_but_wait']}`.",
                "",
            ]
        )
    out.write_text("\n".join(lines), encoding="utf-8")
    (out.with_suffix(".json")).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=ROOT / "demo" / "results")
    parser.add_argument("--runs-root", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=REPORT)
    args = parser.parse_args()
    if args.runs_root is not None:
        payload = write_rescue_report(args.runs_root.resolve(), args.out.resolve())
        print(json.dumps({"runs": len(payload), "report": str(args.out.resolve())}, ensure_ascii=False))
        return 0
    stats = build_stats(args.results_dir.resolve())
    write_report(stats, args.results_dir.resolve(), args.out.resolve())
    print(json.dumps({"steps": stats.steps, "regret": stats.counts, "report": str(args.out.resolve())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
