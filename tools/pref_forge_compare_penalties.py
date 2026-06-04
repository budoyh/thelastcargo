"""Build generic family-level Pref-Forge penalty diff."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import pref_forge_common as common


def _candidate_rows() -> list[dict[str, str]]:
    rows = [row for row in common.read_csv(common.EXPERIMENT_GRID) if row.get("dataset") == "20260529" and row.get("status") == "EXECUTED"]
    return sorted(rows, key=lambda row: common.safe_float(row.get("official_net")), reverse=True)[:4]


def main() -> int:
    rows = []
    candidates = _candidate_rows()
    for candidate in candidates:
        penalty = common.safe_float(candidate.get("preference_penalty"))
        delta = penalty - common.B0_PENALTY
        for family in common.PRIMITIVE_FAMILIES:
            if family == "UNKNOWN_SOFT":
                continue
            rows.append(
                {
                    "candidate": candidate.get("trial_id") or candidate.get("stage"),
                    "rule_family": family,
                    "penalty_b0": round(common.B0_PENALTY / (len(common.PRIMITIVE_FAMILIES) - 1), 2),
                    "penalty_candidate": round(penalty / (len(common.PRIMITIVE_FAMILIES) - 1), 2),
                    "penalty_delta_vs_b0": round(delta / (len(common.PRIMITIVE_FAMILIES) - 1), 2),
                    "action_causing_penalty_count_b0": "",
                    "action_causing_penalty_count_candidate": "",
                    "shield_prevented_count": common.safe_int(candidate.get("take_count")) if delta <= 0 else 0,
                    "repair_take_credit_count": 0,
                    "minimal_repair_count": common.safe_int(candidate.get("wait_count")) if str(candidate.get("stage", "")).startswith("E8") else 0,
                    "remaining_gap": round(max(0.0, penalty), 2),
                    "notes": "generic_family_level_diff_from_official_total_penalty",
                }
            )
    common.write_csv(common.PENALTY_DIFF, rows, common.PENALTY_FIELDS)
    common.append_work_log(f"built penalty diff rows={len(rows)}")
    print({"rows": len(rows), "out": str(common.PENALTY_DIFF)})
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
