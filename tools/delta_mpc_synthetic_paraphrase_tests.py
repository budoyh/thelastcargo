"""Hidden-style synthetic preference checks for Delta-MPC automata."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"
if str(DEMO) not in sys.path:
    sys.path.insert(0, str(DEMO))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent import candidate_preference_verifier, cargo_filter, candidate_generator, config, preference_automata  # noqa: E402
from agent.memory import DriverMemory  # noqa: E402
from agent.preference_compiler import hash_preferences  # noqa: E402
from agent.schemas import CURRENT_ACTIONABLE, DriverStatus  # noqa: E402
from agent.world import refresh_world  # noqa: E402


class SyntheticApi:
    def __init__(self, preferences: list[dict[str, Any]]) -> None:
        self.preferences = preferences

    def get_driver_status(self, driver_id: str) -> dict[str, Any]:
        return {
            "driver_id": driver_id,
            "current_lat": 23.0,
            "current_lng": 113.0,
            "simulation_progress_minutes": 0,
            "simulation_wall_time": "2026-03-01 00:00:00",
            "truck_length": "9.6",
            "preferences": self.preferences,
            "completed_order_count": 0,
        }


def _cargo() -> dict[str, Any]:
    return {
        "distance_km": 70.0,
        "cargo": {
            "cargo_id": "SYNTHETIC",
            "price": 1000.0,
            "create_time": "2026-03-01 00:00:00",
            "remove_time": "2026-03-02 00:00:00",
            "load_time": ["2026-03-01 00:00:00", "2026-03-02 00:00:00"],
            "start": {"lat": 23.4, "lng": 113.4},
            "end": {"lat": 23.8, "lng": 113.8},
            "cost_time_minutes": 120,
            "cargo_name": "abstract_value",
        },
    }


def _case(name: str, content: str, expected_type: str) -> dict[str, Any]:
    return {
        "name": name,
        "preference": {"content": content, "penalty_amount": 1000, "penalty_cap": None},
        "expected_type": expected_type,
    }


def main() -> int:
    old_qwen = config.ENABLE_QWEN_PREFERENCE_COMPILER
    config.ENABLE_QWEN_PREFERENCE_COMPILER = False
    cases = [
        _case("time_rest_window", "Keep a daily quiet interval from 00:00 to 06:00.", "continuous_or_scheduled_rest"),
        _case("full_inactive_day", "Reserve two complete days without order activity this month.", "full_inactive_day"),
        _case("forbidden_cargo_field", "Avoid current visible cargo values that match the disallowed field.", "cargo_field_avoid_or_require"),
        _case("required_cargo_field", "Need distinct days involving a required visible field value.", "cargo_field_avoid_or_require"),
        _case("distinct_day_quota", "Need 3 complete days in the month with no orders.", "full_inactive_day"),
        _case("distance_budget", "Keep pickup approach below 55 km.", "pickup_or_haul_distance_limit"),
        _case("visit_dwell", "Visit the runtime target near 12.3456,123.4567 and wait.", "date_location_visit_or_dwell"),
        _case("ambiguous_unknown", "Prefer the abstract private pattern when it feels suitable.", "unknown_soft"),
    ]
    rows = []
    try:
        for item in cases:
            api = SyntheticApi([item["preference"]])
            world = refresh_world(api, "synthetic", memory=DriverMemory())
            snap = preference_automata.snapshot(world)
            observed = snap.states[0].automaton_type if snap.states else "missing"
            visible = cargo_filter.normalize_and_filter(
                raw_cargos=[_cargo()],
                world=world,
                source_scope=CURRENT_ACTIONABLE,
                decision_id="synthetic",
            )
            options = candidate_generator.build_options(world, visible, "synthetic")
            checks = candidate_preference_verifier.verify_candidate(options[0], world, tuple()) if options else []
            unknown_hard_block = 0
            if observed == "unknown_soft":
                unknown_hard_block = sum(1 for check in checks if check.predicted_marginal_penalty > 5000)
            rows.append(
                {
                    "name": item["name"],
                    "compile_success": bool(world.rules.rules),
                    "automata_type": observed,
                    "expected_type": item["expected_type"],
                    "slot_extraction": bool(world.rules.rules[0].fields) if world.rules.rules else False,
                    "macro_candidate_generation": observed in {"continuous_or_scheduled_rest", "full_inactive_day", "date_location_visit_or_dwell"},
                    "candidate_verifier_behavior": "checks_generated" if checks else "no_checks",
                    "UnknownSoft_hard_block_count": unknown_hard_block,
                    "passed": observed == item["expected_type"] or item["expected_type"] == "unknown_soft" and observed == "unknown_soft",
                }
            )
    finally:
        config.ENABLE_QWEN_PREFERENCE_COMPILER = old_qwen
    passed = sum(1 for row in rows if row["passed"] and row["UnknownSoft_hard_block_count"] == 0)
    print(json.dumps({"cases": len(rows), "passed": passed, "rows": rows}, ensure_ascii=True, sort_keys=True))
    return 0 if passed >= 6 and all(row["UnknownSoft_hard_block_count"] == 0 for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
