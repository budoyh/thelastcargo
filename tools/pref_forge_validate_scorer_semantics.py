"""Validate generic Pref-Forge scorer semantics coverage.

This is a static/runtime-boundary probe, not a substitute for official scoring.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "demo"))

from agent import preference_primitives  # noqa: E402


def main() -> int:
    specs = preference_primitives.PRIMITIVES
    failures = []
    for spec in specs:
        if not spec.family or not spec.observable_event_types:
            failures.append((spec.family, "missing_events"))
        if spec.family != "UNKNOWN_SOFT" and not spec.required_slots:
            failures.append((spec.family, "missing_required_slots"))
        if not spec.unknown_soft_fallback_conditions:
            failures.append((spec.family, "missing_unknown_soft_fallback"))
    print({"primitive_count": len(specs), "failures": failures, "status": "PASS" if not failures else "FAIL"})
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
