"""Estimate generic gross refill from E11/E12 official rows."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import pref_forge_common as common


def main() -> int:
    rows = common.read_csv(common.EXPERIMENT_GRID)
    e11 = next((row for row in rows if row.get("trial_id") == "E11" and row.get("dataset") == "20260529"), None)
    e12 = next((row for row in rows if row.get("trial_id") == "E12" and row.get("dataset") == "20260529"), None)
    if not e11 or not e12:
        print({"status": "missing_e11_or_e12"})
        return 1
    refill = {
        "refill_gross_gain": round(common.safe_float(e12.get("gross_minus_cost")) - common.safe_float(e11.get("gross_minus_cost")), 2),
        "penalty_reintroduced": round(common.safe_float(e12.get("preference_penalty")) - common.safe_float(e11.get("preference_penalty")), 2),
        "official_net_delta": round(common.safe_float(e12.get("official_net")) - common.safe_float(e11.get("official_net")), 2),
    }
    common.write_json(common.PRIVATE / "gross_refill_plan_untracked.json", refill)
    print(refill)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
