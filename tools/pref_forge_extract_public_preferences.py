"""Extract public preferences into private raw storage and redacted census rows."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import pref_forge_common as common


def main() -> int:
    rows = common.freeze_raw_preferences()
    common.append_work_log(f"extracted public preference rows={len(rows)} to private store")
    print({"rows": len(rows), "private_path": str(common.RAW_PREFS), "expected": 46})
    return 0 if rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
