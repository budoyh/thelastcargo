"""Post-run stability audit for LODO, time blocks and perturbations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import regret_dashboard  # noqa: E402

REPORT = ROOT / "reports" / "stability_audit.md"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _driver_rows(results_dir: Path) -> list[dict[str, Any]]:
    data = _load_json(results_dir / "monthly_income_202603.json")
    return list(data.get("drivers") or [])


def _summary(results_dir: Path) -> dict[str, Any]:
    data = _load_json(results_dir / "monthly_income_202603.json")
    stats = regret_dashboard.build_stats(results_dir)
    counts = {"take_order": 0, "wait": 0, "reposition": 0, "other": 0}
    for path in sorted(results_dir.glob("actions_202603_*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            action = ((row.get("action") or {}).get("action") or "other").strip()
            counts[action if action in counts else "other"] += 1
    summary = data["summary"]
    return {
        "net": float(summary["total_net_income_all_drivers"]),
        "penalty": float(summary["total_preference_penalty"]),
        "failed": int(summary["failed_driver_count"]),
        "query_minutes": stats.query_minutes,
        "illegal": stats.illegal_actions,
        "regret": stats.counts,
        "counts": counts,
    }


def _lodo_rows(results_dir: Path) -> list[dict[str, Any]]:
    drivers = _driver_rows(results_dir)
    rows: list[dict[str, Any]] = []
    for omitted in drivers:
        kept = [d for d in drivers if d is not omitted]
        rows.append(
            {
                "omitted": omitted.get("driver_id", "unknown"),
                "kept_drivers": len(kept),
                "net": round(sum(float(d["income"]["net_income"]) for d in kept), 2),
                "penalty": round(sum(float(d["income"]["preference_penalty"]) for d in kept), 2),
                "aborted": sum(1 for d in kept if d.get("calculation_aborted")),
            }
        )
    return rows


def _time_blocks(results_dir: Path, block_minutes: int = 7 * 24 * 60) -> list[dict[str, Any]]:
    blocks: dict[int, dict[str, Any]] = {}
    for path in sorted(results_dir.glob("actions_202603_*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            minute = int((row.get("result") or {}).get("simulation_progress_minutes", 0) or 0)
            idx = min(4, max(0, minute // block_minutes))
            item = blocks.setdefault(idx, {"block": idx, "steps": 0, "take": 0, "wait": 0, "reposition": 0, "illegal": 0})
            item["steps"] += 1
            action = ((row.get("action") or {}).get("action") or "").strip()
            if action == "take_order":
                item["take"] += 1
            elif action == "wait":
                item["wait"] += 1
            elif action == "reposition":
                item["reposition"] += 1
            else:
                item["illegal"] += 1
    return [blocks[key] for key in sorted(blocks)]


def write_report(latest: Path, old: Path | None, perturbations: list[tuple[str, Path]]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stability Audit",
        "",
        "Scope: post-run stability checks. The build has no trained ranker enabled, so LODO is a score-sensitivity audit rather than a retraining audit.",
        "",
        "## Final Default",
        "",
    ]
    default_summary = _summary(latest)
    lines.extend(
        [
            f"- results_dir: `{latest}`",
            f"- net: {default_summary['net']}",
            f"- penalty: {default_summary['penalty']}",
            f"- failed_driver_count: {default_summary['failed']}",
            f"- illegal_actions: {default_summary['illegal']}",
            f"- query_minutes: {default_summary['query_minutes']}",
            "",
            "## LODO Sensitivity",
            "",
            "| source | omitted_driver | kept_drivers | net_without_driver | penalty_without_driver | aborted_without_driver |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in _lodo_rows(latest):
        lines.append(f"| latest | {row['omitted']} | {row['kept_drivers']} | {row['net']} | {row['penalty']} | {row['aborted']} |")
    if old is not None and (old / "monthly_income_202603.json").exists():
        for row in _lodo_rows(old):
            lines.append(f"| old_0509 | {row['omitted']} | {row['kept_drivers']} | {row['net']} | {row['penalty']} | {row['aborted']} |")
    lines.extend(
        [
            "",
            "## Leave Time Block",
            "",
            "| block | steps | take | wait | reposition | illegal |",
            "|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for row in _time_blocks(latest):
        lines.append(f"| {row['block']} | {row['steps']} | {row['take']} | {row['wait']} | {row['reposition']} | {row['illegal']} |")
    lines.extend(
        [
            "",
            "## Perturbations",
            "",
            "| run | net | penalty | failed | query_minutes | illegal | take | wait | reposition |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for label, path in [("default", latest), *perturbations]:
        item = _summary(path)
        counts = item["counts"]
        lines.append(
            f"| {label} | {item['net']} | {item['penalty']} | {item['failed']} | {item['query_minutes']} | {item['illegal']} | {counts['take_order']} | {counts['wait']} | {counts['reposition']} |"
        )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(REPORT), "default": default_summary}, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--latest", type=Path, default=ROOT / "runs" / "latest")
    parser.add_argument("--old", type=Path, default=ROOT / "runs" / "old_0509")
    parser.add_argument("--perturbation", action="append", default=[], help="label=path")
    args = parser.parse_args()
    perturbations: list[tuple[str, Path]] = []
    for item in args.perturbation:
        if "=" not in item:
            raise ValueError("--perturbation must be label=path")
        label, path = item.split("=", 1)
        perturbations.append((label, Path(path).resolve()))
    write_report(args.latest.resolve(), args.old.resolve(), perturbations)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
