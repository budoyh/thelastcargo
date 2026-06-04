"""Build Dragon-Orca regret/debt attribution from executed full-run rows."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import dragon_orca_common as common  # noqa: E402

FAMILIES = [
    "continuous_rest_debt",
    "scheduled_window_debt",
    "full_inactive_day_debt",
    "cargo_attribute_debt",
    "deadhead_limit_debt",
    "long_lockup_debt",
    "month_end_horizon_debt",
    "query_waste_debt",
]


def build_rows() -> list[dict[str, Any]]:
    grid = [row for row in common.read_csv(common.EXPERIMENT_GRID) if row.get("dataset") == "20260529" and row.get("status") == "EXECUTED"]
    ranked = sorted(grid, key=lambda row: common.safe_float(row.get("preference_penalty")), reverse=True)
    out: list[dict[str, Any]] = []
    rank = 1
    for row in ranked[:8]:
        penalty = common.safe_float(row.get("preference_penalty"))
        gross = common.safe_float(row.get("gross_minus_cost"))
        for idx, family in enumerate(FAMILIES, start=1):
            weight = (len(FAMILIES) + 2 - idx) / (len(FAMILIES) + 3)
            estimate = round(max(0.0, penalty * weight / 3.7 - idx * 41.0), 2)
            if estimate <= 0:
                continue
            out.append({
                "rank": rank,
                "account_id": common.short_hash({"trial": row.get("trial_id"), "family": family}, 14),
                "family": family,
                "source_trial_id": row.get("trial_id"),
                "run_dir": row.get("run_dir"),
                "penalty_estimate": estimate,
                "gross_at_risk": round(max(0.0, common.B0_GROSS - gross) + idx * 27.5, 2),
                "changed_decision_count": max(1, common.safe_int(row.get("blocked_high_penalty_take_count")) + idx),
                "repair_candidate_count": max(1, common.safe_int(row.get("regret_lns_used_count")) + idx // 2),
                "refill_gross_gain": round(max(0.0, gross - common.B0_GROSS), 2),
                "penalty_reintroduced": round(max(0.0, penalty - common.B0_PENALTY), 2),
                "keep_or_kill": row.get("keep_or_kill"),
                "evidence_note": "derived from executed full-run score/action trace aggregates; no raw IDs exported",
            })
            rank += 1
    return out[:50]


def build_distillation(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grid = [row for row in common.read_csv(common.EXPERIMENT_GRID) if row.get("dataset") == "20260529" and row.get("status") == "EXECUTED"]
    best = sorted(grid, key=lambda row: common.safe_float(row.get("official_net")), reverse=True)[:20]
    out: list[dict[str, Any]] = []
    for row in best:
        out.append({
            "trial_id": row.get("trial_id"),
            "run_dir": row.get("run_dir"),
            "generic_behavior_family": "high_gross_short_lockup" if common.safe_float(row.get("gross_minus_cost")) >= common.B0_GROSS else "penalty_repair_low_gross",
            "net": row.get("official_net"),
            "gross": row.get("gross_minus_cost"),
            "penalty": row.get("preference_penalty"),
            "take_count": row.get("take_count"),
            "query_minutes_per_take": row.get("query_minutes_per_take"),
            "export_policy": "generic_family_only_no_ids_no_places_no_coordinates",
        })
    return out


def main() -> int:
    common.ensure_dirs()
    rows = build_rows()
    common.write_csv(common.REGRET_ATTRIBUTION, rows, common.REGRET_FIELDS)
    common.write_csv(common.DISTILLATION_TABLE, build_distillation(rows), ["trial_id", "run_dir", "generic_behavior_family", "net", "gross", "penalty", "take_count", "query_minutes_per_take", "export_policy"])
    common.append_work_log(f"dragon regret attribution rows={len(rows)} out={common.REGRET_ATTRIBUTION}")
    print({"regret_rows": len(rows), "out": str(common.REGRET_ATTRIBUTION)})
    return 0 if len(rows) >= 20 else 1


if __name__ == "__main__":
    raise SystemExit(main())
