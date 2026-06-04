"""Generate Dragon-Orca regret-LNS refill candidates as generic JSON recipes."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import dragon_orca_common as common  # noqa: E402


def main() -> int:
    common.ensure_dirs()
    rows = common.read_csv(common.REGRET_ATTRIBUTION)
    top = rows[:20]
    payload = {
        "policy": "generic_regret_lns_refill_only",
        "destroy_families": sorted({row.get("family") for row in top if row.get("family")}),
        "repair_actions": ["bounded_rest", "visible_matching_take", "short_wait", "legal_visible_cluster_reposition"],
        "refill_rules": {
            "min_profit_per_hour": 25,
            "max_lockup_hours": 18,
            "avoid_reintroducing_top_debt": True,
            "no_ids_places_coordinates_or_future_cargo": True,
        },
        "source_top_accounts": [row.get("account_id") for row in top],
    }
    out = common.EVOLUTION / "regret_lns_refill_candidates.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    common.append_work_log(f"dragon regret LNS refill candidates={len(top)} out={out}")
    print({"source_accounts": len(top), "out": str(out)})
    return 0 if len(top) >= 20 else 1


if __name__ == "__main__":
    raise SystemExit(main())
