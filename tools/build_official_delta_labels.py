"""Build cheap official-scorer delta labels with explicit validity fields."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT_PATH = Path(__file__).resolve().parents[1]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from tools.delta_mpc_utils import REPORTS, ROOT, iter_action_rows, json_cell, short_hash, summarize_run, trace, write_csv

FIELDS = [
    "run_id",
    "dataset",
    "driver_hash",
    "step_hash",
    "action_type",
    "candidate_type",
    "chosen_action_type",
    "delta_official_net",
    "delta_gross_minus_cost",
    "delta_preference_penalty",
    "delta_query_minutes",
    "delta_time_minutes",
    "label_mode",
    "continuation_policy",
    "exact_official_label",
    "replay_valid_after_replacement",
    "visibility_valid",
    "legality_valid",
    "state_compatibility_ok",
    "confidence",
    "notes",
]


def _run_level_label(base: Path, alt: Path, mode: str, candidate_type: str, notes: str) -> dict[str, Any]:
    b = summarize_run(base)
    a = summarize_run(alt)
    return {
        "run_id": f"{b['run_id']}__vs__{a['run_id']}",
        "dataset": a["dataset"],
        "driver_hash": "aggregate",
        "step_hash": "run_pair",
        "action_type": "policy",
        "candidate_type": candidate_type,
        "chosen_action_type": b["variant"],
        "delta_official_net": round(float(a["official_net"]) - float(b["official_net"]), 2),
        "delta_gross_minus_cost": round(float(a["gross_minus_cost"]) - float(b["gross_minus_cost"]), 2),
        "delta_preference_penalty": round(float(a["preference_penalty"]) - float(b["preference_penalty"]), 2),
        "delta_query_minutes": round(float(a["query_minutes"]) - float(b["query_minutes"]), 2),
        "delta_time_minutes": "",
        "label_mode": mode,
        "continuation_policy": "paired_completed_policy_run",
        "exact_official_label": True,
        "replay_valid_after_replacement": True,
        "visibility_valid": True,
        "legality_valid": a["illegal_count"] == 0 and a["rejected_take_count"] == 0,
        "state_compatibility_ok": True,
        "confidence": 0.95,
        "notes": notes,
    }


def _action_labels(run_dir: Path, limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path, line_no, row in iter_action_rows(run_dir):
        if len(rows) >= limit:
            break
        tr = trace(row)
        rescue = tr.get("rescue") if isinstance(tr.get("rescue"), dict) else {}
        forensic = rescue.get("wait_forensic") if isinstance(rescue.get("wait_forensic"), dict) else {}
        top_items = forensic.get("top20_rejected_take") if isinstance(forensic.get("top20_rejected_take"), list) else []
        action = row.get("action") if isinstance(row.get("action"), dict) else {}
        chosen = str(action.get("action", ""))
        for item in top_items[:5]:
            if not isinstance(item, dict):
                continue
            delta = float(item.get("score", 0.0) or 0.0)
            rows.append(
                {
                    "run_id": str(run_dir).replace("\\", "/"),
                    "dataset": "20260529" if "20260529" in str(run_dir) or "latest" in str(run_dir) else "unknown",
                    "driver_hash": short_hash(row.get("driver_id", path.name)),
                    "step_hash": short_hash({"file": path.name, "line": line_no}),
                    "action_type": chosen,
                    "candidate_type": "top_rejected_take",
                    "chosen_action_type": chosen,
                    "delta_official_net": round(delta, 2),
                    "delta_gross_minus_cost": "",
                    "delta_preference_penalty": "",
                    "delta_query_minutes": 0,
                    "delta_time_minutes": "",
                    "label_mode": "completed_trajectory_replacement",
                    "continuation_policy": "local_greedy_replan",
                    "exact_official_label": False,
                    "replay_valid_after_replacement": False,
                    "visibility_valid": True,
                    "legality_valid": True,
                    "state_compatibility_ok": False,
                    "confidence": 0.35,
                    "notes": "heuristic_from_runtime_wait_forensic:" + json_cell({"reason": item.get("hard_filter_reason", "")}),
                }
            )
            if len(rows) >= limit:
                break
        macro = rescue.get("macro") if isinstance(rescue.get("macro"), dict) else {}
        if macro and int(macro.get("macro_completed_count", 0) or 0) > 0:
            rows.append(
                {
                    "run_id": str(run_dir).replace("\\", "/"),
                    "dataset": "20260529" if "20260529" in str(run_dir) or "latest" in str(run_dir) else "unknown",
                    "driver_hash": short_hash(row.get("driver_id", path.name)),
                    "step_hash": short_hash({"file": path.name, "line": line_no, "macro": macro}),
                    "action_type": chosen,
                    "candidate_type": "macro_repair",
                    "chosen_action_type": chosen,
                    "delta_official_net": float(macro.get("official_delta_measured_macro_gain", 0.0) or 0.0),
                    "delta_gross_minus_cost": "",
                    "delta_preference_penalty": "",
                    "delta_query_minutes": "",
                    "delta_time_minutes": "",
                    "label_mode": "macro_repair_insertion",
                    "continuation_policy": "macro_completion",
                    "exact_official_label": False,
                    "replay_valid_after_replacement": False,
                    "visibility_valid": True,
                    "legality_valid": True,
                    "state_compatibility_ok": True,
                    "confidence": 0.45,
                    "notes": "runtime_macro_completion_trace",
                }
            )
    return rows


def build_rows(sample_limit: int) -> list[dict[str, Any]]:
    rows = [
        _run_level_label(
            ROOT / "runs" / "latest_rescue",
            ROOT / "runs" / "pce" / "20260529" / "money_trajectory_repair",
            "macro_repair_insertion",
            "offline_money_trajectory_repair",
            "exact official run-pair delta; diagnostic, not runtime-safe label",
        ),
        _run_level_label(
            ROOT / "runs" / "latest_rescue",
            ROOT / "runs" / "pce" / "20260529" / "visibility_k600_oracle",
            "completed_trajectory_replacement",
            "online_visibility_oracle",
            "exact official run-pair delta; online oracle diagnostic",
        ),
        _run_level_label(
            ROOT / "runs" / "next_build" / "20260529" / "money_greedy_no_pref",
            ROOT / "runs" / "latest_rescue",
            "action_knockout",
            "high_penalty_replay",
            "exact official run-pair delta showing high-gross penalty knockout value",
        ),
    ]
    rows.extend(_action_labels(ROOT / "runs" / "latest_rescue", sample_limit))
    rows.extend(_action_labels(ROOT / "runs" / "pce" / "20260529" / "pce_final", sample_limit // 2))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--sample-limit", type=int, default=200)
    parser.add_argument("--out", type=Path, default=REPORTS / "delta_mpc_labels.csv")
    args = parser.parse_args()
    rows = build_rows(args.sample_limit)
    write_csv(args.out, rows, FIELDS)
    print({"rows": len(rows), "out": str(args.out), "simulation_days": args.simulation_days})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
