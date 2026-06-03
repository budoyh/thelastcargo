"""Generate wait-lock and score forensic report for rescue runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.score_rescue_metrics import markdown_table, summarize_run  # noqa: E402


def write_report(results_dir: Path, out: Path) -> dict:
    item = summarize_run(results_dir)
    counts = item["counts"]
    reason_rows = sorted(item["wait_reasons"].items(), key=lambda kv: kv[1], reverse=True)
    hard_rows = sorted(item["hard_blocks"].items(), key=lambda kv: kv[1], reverse=True)
    rejected_rows = []
    for row in item["top_rejected"][:10]:
        rejected_rows.append(
            [
                row.get("candidate_id", ""),
                row.get("direct_net", ""),
                row.get("profit_per_hour", ""),
                row.get("hard_filter_reason", ""),
                row.get("score", ""),
            ]
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Score Forensic Audit",
        "",
        f"- results_dir: `{results_dir}`",
        f"- net: {item['net']}",
        f"- penalty: {item['penalty']}",
        f"- take/wait/reposition: {counts['take_order']} / {counts['wait']} / {counts['reposition']}",
        f"- query_minutes_per_take: {item['query_minutes_per_take']}",
        f"- feasible_positive_cargo_but_wait: {item['feasible_positive_cargo_but_wait']}",
        f"- max_consecutive_wait: {item['max_consecutive_wait']}",
        "",
        "## Wait Reason Distribution",
        "",
        *markdown_table(["wait_reason", "count"], [[k, v] for k, v in reason_rows]),
        "",
        "## Hard Block Reason Counts",
        "",
        *markdown_table(["hard_block_reason", "count"], [[k, v] for k, v in hard_rows]),
        "",
        "## Top Rejected Take Snapshots",
        "",
        *markdown_table(["candidate", "direct_net", "profit_per_hour", "hard_filter_reason", "score"], rejected_rows),
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    (out.with_suffix(".json")).write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(out), "net": item["net"], "wait_ratio": item["wait_ratio"]}, ensure_ascii=False))
    return item


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=ROOT / "runs" / "latest_rescue")
    parser.add_argument("--runs-root", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "score_forensic_audit.md")
    args = parser.parse_args()
    results_dir = args.results_dir
    if args.runs_root is not None:
        candidate = args.runs_root / "a7"
        if candidate.exists():
            results_dir = candidate
    write_report(results_dir.resolve(), args.out.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
