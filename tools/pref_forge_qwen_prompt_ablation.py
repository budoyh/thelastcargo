"""Summarize Pref-Forge Qwen prompt pipeline results from private IO."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import pref_forge_common as common


def main() -> int:
    rows = []
    if common.RAW_QWEN_IO.is_file():
        for line in common.RAW_QWEN_IO.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                rows.append(item)
    total = len(rows)
    ok = sum(1 for item in rows if item.get("ok"))
    by_step: dict[str, dict[str, int]] = {}
    for item in rows:
        step = str(item.get("step", "unknown"))
        bucket = by_step.setdefault(step, {"total": 0, "ok": 0})
        bucket["total"] += 1
        bucket["ok"] += int(bool(item.get("ok")))
    common.append_work_log(f"qwen prompt ablation summary total={total} ok={ok}")
    print({"total_calls": total, "schema_valid_rate": round(ok / max(1, total), 4), "by_step": by_step})
    return 0 if total and ok == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
