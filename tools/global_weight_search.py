"""P2 placeholder for constrained global weight search.

The Tournament Build keeps learned deployment off unless ablation proves stable.
This script records the constrained search space without exporting route or ID
features.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    payload = {
        "status": "not_run_by_default",
        "constraints": {
            "deadhead_km": "<= 0",
            "execution_risk": "<= 0",
            "preference_violation_debt": "<= 0",
            "direct_net_profit": ">= 0",
            "high_confidence_repair_value": ">= 0",
        },
        "export_policy": "no ids, no fixed coordinates, no route tables",
    }
    out = ROOT / "reports" / "global_weight_search.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

