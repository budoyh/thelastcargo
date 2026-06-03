"""Offline money-trajectory repair experiment for CROWN-PCE."""

from __future__ import annotations

import csv
import json

from pce_oracle_engine import command_parser, run_greedy_oracle, short_hash


def _write_forensics(path, payload):
    fields = [
        "row_type",
        "variant",
        "driver_hash",
        "step",
        "candidate_hash",
        "direct_net",
        "marginal_penalty",
        "penalty_before",
        "penalty_after",
        "repair_action",
        "avoided_penalty",
        "repair_value",
        "lost_profit",
        "deadline",
        "feasibility",
        "confidence",
        "redaction_status",
    ]
    rows = []
    for row in payload.get("score_curve", [])[:200]:
        marginal = float(row.get("marginal_penalty", 0.0) or 0.0)
        rows.append(
            {
                "row_type": "money_repair_sample",
                "variant": payload["variant"],
                "driver_hash": row.get("driver_hash", ""),
                "step": row.get("step", ""),
                "candidate_hash": row.get("candidate_hash", ""),
                "direct_net": row.get("direct_net", ""),
                "marginal_penalty": row.get("marginal_penalty", ""),
                "penalty_before": row.get("penalty_before", ""),
                "penalty_after": row.get("penalty_after", ""),
                "repair_action": "delete_replace_or_wait_macro" if marginal > 0 else "none",
                "avoided_penalty": max(0.0, marginal),
                "repair_value": max(0.0, marginal),
                "lost_profit": "",
                "deadline": "redacted_runtime_boundary",
                "feasibility": "offline_replay_approx",
                "confidence": 0.65,
                "redaction_status": "raw value redacted",
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main() -> int:
    parser = command_parser("Run the money trajectory deletion/repair experiment.")
    args = parser.parse_args()
    results_dir = args.results_dir or (args.runs_root / "20260529" / "money_trajectory_repair")
    payload = run_greedy_oracle(
        data_dir=args.data_dir,
        results_dir=results_dir,
        variant=args.variant or "money_trajectory_repair",
        visibility_k=None,
        mode="repair",
        max_candidates=args.max_candidates,
        max_steps=args.max_steps,
    )
    payload["experiment_hash"] = short_hash(payload)
    forensic_rows = _write_forensics(args.output_dir / "action_forensics.csv", payload)
    payload["forensic_rows"] = forensic_rows
    print(json.dumps({k: v for k, v in payload.items() if k != "score_curve"}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
