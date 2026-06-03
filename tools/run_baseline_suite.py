"""Summarize score-rescue baseline runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.score_rescue_metrics import markdown_table, summarize_run  # noqa: E402

BASELINES = [
    "current_crown_y",
    "fixed_k50_positive_net",
    "fixed_k100_profit_per_hour",
    "fixed_k200_direct_profit_with_slack",
    "simple_balanced_greedy",
    "safe_profit_greedy",
]


def write_report(results_root: Path, out: Path) -> list[dict]:
    rows = []
    payload = []
    for name in BASELINES:
        path = results_root / name
        item = summarize_run(path)
        payload.append({"name": name, **item})
        counts = item["counts"]
        rows.append(
            [
                name,
                item["net"],
                item["penalty"],
                round(item["proxy_score"], 2),
                counts["take_order"],
                counts["wait"],
                counts["reposition"],
                counts["rejected_take"],
                item["wait_ratio"],
                item["query_minutes_per_take"],
                item["failed_driver_count"],
            ]
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Baseline Comparison",
        "",
        f"- results_root: `{results_root}`",
        "",
        *markdown_table(
            ["run", "net", "penalty", "proxy", "take", "wait", "repo", "rejected", "wait_ratio", "q_min/take", "aborts"],
            rows,
        ),
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    (out.with_suffix(".json")).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--results-root", type=Path, default=ROOT / "runs" / "rescue_baselines")
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "baseline_comparison.md")
    args = parser.parse_args()
    payload = write_report(args.results_root.resolve(), args.out.resolve())
    print(json.dumps({"runs": len(payload), "report": str(args.out.resolve())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
