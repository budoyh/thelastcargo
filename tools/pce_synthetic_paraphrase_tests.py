"""Offline hidden-style paraphrase checks for executable preference predicates.

This tool intentionally writes only redacted predicate-level rows into the PCE
predicate report. It does not run inside the runtime agent.
"""

from __future__ import annotations

import csv
import hashlib
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"
if str(DEMO) not in sys.path:
    sys.path.insert(0, str(DEMO))

from agent import config  # noqa: E402
from agent.preference_compiler import compile_if_changed, hash_preferences  # noqa: E402
from agent.schemas import DriverStatus  # noqa: E402

PREDICATE_EVAL = ROOT / "reports" / "predicate_eval.csv"


def _hash(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]


def _status(preferences: list[dict[str, Any]]) -> DriverStatus:
    return DriverStatus(
        driver_id="synthetic",
        current_lat=0.0,
        current_lng=0.0,
        simulation_progress_minutes=0,
        simulation_wall_time="2026-03-01 00:00:00",
        truck_length="4.2m",
        preferences=tuple(preferences),
        completed_order_count=0,
    )


def _case(name: str, text: str, amount: float, expected: str) -> dict[str, Any]:
    return {
        "name": name,
        "preference": {"content": text, "penalty_amount": amount, "penalty_cap": None},
        "expected": expected,
    }


def run_cases() -> list[dict[str, Any]]:
    cases = [
        _case("distance_a", "Keep pickup approach under 80 km; charge 700 per breach.", 700, "pickup_deadhead_limit"),
        _case("distance_b", "The loading approach may not exceed 120 kilometers; charge 300.", 300, "pickup_deadhead_limit"),
        _case("time_a", "Every day from 23:00 to 06:00 the truck must stay still; charge 600.", 600, "continuous_wait"),
        _case("time_b", "From 12:00 until 13:00 each day there should be no driving or order pickup.", 200, "continuous_wait"),
        _case("coordinate_a", "Visit the service point near 12.3456,123.4567 before the month ends.", 1000, "location_visit"),
        _case("count_quota_a", "Need 3 complete days in the month with no orders; charge 5000 if short.", 5000, "off_day_quota"),
        _case("field_match_a", "Do not carry cargo category Alpha; charge 800 for each match.", 800, "cargo_field_match"),
    ]
    old_qwen = config.ENABLE_QWEN_PREFERENCE_COMPILER
    config.ENABLE_QWEN_PREFERENCE_COMPILER = False
    rows: list[dict[str, Any]] = []
    try:
        for item in cases:
            status = _status([item["preference"]])
            pref_hash = hash_preferences(status.preferences)
            compiled = compile_if_changed(api=None, status=status, pref_hash=pref_hash, prev_rules=None)
            rule = compiled.rules[0]
            observed = rule.predicate_type
            passed = observed == item["expected"]
            rows.append(
                {
                    "name": item["name"],
                    "expected": item["expected"],
                    "observed": observed,
                    "passed": passed,
                    "confidence": rule.confidence,
                    "unresolved": rule.unresolved_reason,
                }
            )
    finally:
        config.ENABLE_QWEN_PREFERENCE_COMPILER = old_qwen
    return rows


def append_report(rows: list[dict[str, Any]]) -> None:
    if not PREDICATE_EVAL.exists():
        raise FileNotFoundError(f"missing predicate report: {PREDICATE_EVAL}")
    with PREDICATE_EVAL.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        for row in rows:
            writer.writerow(
                [
                    "synthetic_paraphrase",
                    "semantic_pass",
                    "1.0" if row["passed"] else "0.0",
                    _hash("synthetic"),
                    "",
                    _hash(row["name"]),
                    _hash(row["expected"]),
                    row["observed"],
                    "yes" if row["passed"] else "no",
                    "neutral",
                    "",
                    "",
                    "",
                    "",
                    f"{row['confidence']:.4f}",
                    "synthetic_paraphrase",
                    "false",
                    "deterministic_compiler_gate",
                    "",
                    "hidden_style_synthetic",
                    "raw value redacted",
                ]
            )


def main() -> int:
    rows = run_cases()
    append_report(rows)
    passed = sum(1 for row in rows if row["passed"])
    failed = len(rows) - passed
    print(f"synthetic_paraphrase_cases={len(rows)} passed={passed} failed={failed}")
    for row in rows:
        status = "PASS" if row["passed"] else "FAIL"
        print(f"{status} {row['name']} expected={row['expected']} observed={row['observed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
