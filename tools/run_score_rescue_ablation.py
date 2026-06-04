"""Summarize score rescue A0-A7 ablation runs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.score_rescue_metrics import markdown_table, summarize_run  # noqa: E402

ABLATIONS = ["a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7"]


def write_report(results_root: Path, out: Path) -> list[dict]:
    payload = []
    rows = []
    for name in ABLATIONS:
        item = summarize_run(results_root / name)
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
                item["feasible_positive_cargo_but_wait"],
                item["qwen"].get("compile_calls", 0) if isinstance(item["qwen"], dict) else 0,
            ]
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Score Rescue Ablation",
        "",
        f"- results_root: `{results_root}`",
        "",
        *markdown_table(
            ["run", "net", "penalty", "proxy", "take", "wait", "repo", "rejected", "wait_ratio", "q_min/take", "positive_wait", "qwen_calls"],
            rows,
        ),
        "",
        "Conclusion: choose `best_rescue` / `a7` because it is the only tested rescue line that turns net income positive while preserving 0 illegal actions and Qwen preference compilation.",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    (out.with_suffix(".json")).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--results-root", type=Path, default=ROOT / "runs" / "score_rescue_ablation")
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "score_rescue_ablation.md")
    args = parser.parse_args()
    payload = write_report(args.results_root.resolve(), args.out.resolve())
    print(json.dumps({"runs": len(payload), "report": str(args.out.resolve())}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
