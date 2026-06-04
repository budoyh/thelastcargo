"""Qwen contract ensemble boundary.

The live compiler path is intentionally semantic-only. Runtime scoring reads
compiled generic contract state from the normal world object and never accepts
Qwen-chosen actions, cargo ids, or numeric final score adjustments.
"""

from __future__ import annotations

from ..schemas import World


def stats_payload(world: World) -> dict[str, int | str]:
    return {
        "pref_hash_present": int(bool(world.pref_hash)),
        "compiled_rule_count": len(world.rules.rules),
        "numeric_auditor": "off",
    }
