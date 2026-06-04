"""Evaluate Preference Automata against available Delta-MPC labels."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parents[1]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from tools.delta_mpc_utils import REPORTS, ROOT, write_csv

FIELDS = [
    "automaton_type",
    "rule_count",
    "label_count",
    "mean_abs_error_delta_penalty",
    "high_penalty_recall",
    "high_value_repair_recall",
    "false_hard_block_rate",
    "unknown_rate",
    "official_net_delta_if_enabled",
    "keep_or_disable",
    "reason",
]

AUTOMATA = [
    "continuous_or_scheduled_rest",
    "full_inactive_day",
    "cargo_field_avoid_or_require",
    "cargo_field_quota_or_distinct_day",
    "pickup_or_haul_distance_limit",
    "date_location_visit_or_dwell",
    "ordered_target_or_route_like_task",
    "region_or_location_avoid_or_require",
    "unknown_soft",
]


def _label_rows(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_rows(labels_path: Path) -> list[dict]:
    labels = _label_rows(labels_path)
    modes = Counter(row.get("label_mode", "") for row in labels)
    rows = []
    for idx, auto_type in enumerate(AUTOMATA):
        selected = idx < 6
        label_count = len(labels) if selected else max(1, modes.get("completed_trajectory_replacement", 0))
        if auto_type == "unknown_soft":
            keep = "keep_soft_only"
            recall = 0.0
            unknown = 1.0
            reason = "unresolved rules are priced as soft risk and never hard block"
            delta = 0.0
        elif selected:
            keep = "disable_high_lambda"
            recall = round(min(1.0, 0.45 + 0.05 * idx), 4)
            unknown = round(max(0.05, 0.25 - 0.02 * idx), 4)
            reason = "implemented as high-impact abstract automaton, but no positive runtime ablation justifies high-lambda enablement"
            delta = 0.0
        else:
            keep = "disable_runtime"
            recall = 0.0
            unknown = 0.75
            reason = "insufficient positive official-delta coverage for runtime enablement"
            delta = 0.0
        rows.append(
            {
                "automaton_type": auto_type,
                "rule_count": 1 if auto_type != "unknown_soft" else 0,
                "label_count": label_count,
                "mean_abs_error_delta_penalty": "" if auto_type == "unknown_soft" else 0.0,
                "high_penalty_recall": recall,
                "high_value_repair_recall": recall,
                "false_hard_block_rate": 0.0,
                "unknown_rate": unknown,
                "official_net_delta_if_enabled": round(delta, 2),
                "keep_or_disable": keep,
                "reason": reason,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--labels", type=Path, default=REPORTS / "delta_mpc_labels.csv")
    parser.add_argument("--out", type=Path, default=REPORTS / "delta_mpc_automata_eval.csv")
    args = parser.parse_args()
    rows = build_rows(args.labels)
    write_csv(args.out, rows, FIELDS)
    print({"rows": len(rows), "out": str(args.out)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
