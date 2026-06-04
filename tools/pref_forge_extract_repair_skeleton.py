"""Extract generic repair skeleton metrics from current Pref-Forge runs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import pref_forge_common as common
from tools.trident_utils import iter_action_rows


def _trace(row: dict[str, Any]) -> dict[str, Any]:
    action = row.get("action") if isinstance(row.get("action"), dict) else {}
    trace = action.get("agent_trace") if isinstance(action.get("agent_trace"), dict) else {}
    return trace if isinstance(trace, dict) else {}


def extract(run_dir: Path) -> dict[str, Any]:
    wait_minutes = 0
    repair_events = 0
    refill_gaps = 0
    for _, _, row in iter_action_rows(run_dir):
        action = row.get("action") if isinstance(row.get("action"), dict) else {}
        name = action.get("action")
        params = action.get("params") if isinstance(action.get("params"), dict) else {}
        rescue = _trace(row).get("rescue") if isinstance(_trace(row).get("rescue"), dict) else {}
        fuse = rescue.get("fuse") if isinstance(rescue.get("fuse"), dict) else {}
        if name == "wait":
            minutes = common.safe_int(params.get("duration_minutes"))
            wait_minutes += minutes
            if minutes >= 60:
                refill_gaps += 1
        if common.safe_int(fuse.get("repair_trigger_count")):
            repair_events += 1
    return {"run_dir": str(run_dir), "repair_events": repair_events, "wait_minutes": wait_minutes, "refill_gap_count": refill_gaps}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=common.PRIVATE / "repair_skeleton_untracked.json")
    args = parser.parse_args()
    payload = extract(args.run_dir)
    common.write_json(args.out, payload)
    print(payload)
    return 0 if args.run_dir.exists() else 1


if __name__ == "__main__":
    raise SystemExit(main())
