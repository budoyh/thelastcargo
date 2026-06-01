"""Offline official-scorer micro-probes for CROWN-EXACT controller gates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"
if str(DEMO) not in sys.path:
    sys.path.insert(0, str(DEMO))

from calc_monthly_income import (  # type: ignore  # noqa: E402
    PreferenceRuleSpec,
    _active_minutes_by_day,
    _eval_daily_rest,
    _eval_off_days,
    _eval_pickup_deadhead,
    _eval_required_region_cargo_days,
    _eval_route_stops,
    _eval_scheduled_rest_window,
    _eval_wait_at_location_on_day,
    _penalty_count,
    _penalty_failed,
    RouteStop,
)

REPORT = ROOT / "reports" / "scorer_semantics_probe.csv"


def _rule(amount: float = 1000.0, cap: float | None = None) -> PreferenceRuleSpec:
    return PreferenceRuleSpec(
        content="PROTECTED_LITERAL_REDACTED",
        start_minutes=0,
        end_minutes=31 * 1440 - 1,
        penalty_amount=amount,
        penalty_cap=cap,
    )


def _ctx(
    action_name: str,
    *,
    step_start: int,
    query: int = 0,
    duration: int,
    accepted: bool = True,
    cargo_id: str = "runtime_entity_hash",
    before: tuple[float, float] = (0.0, 0.0),
    after: tuple[float, float] = (0.0, 0.0),
) -> dict[str, Any]:
    return {
        "line_no": 1,
        "action_name": action_name,
        "params": {"cargo_id": cargo_id},
        "result": {"accepted": accepted},
        "step_start": step_start,
        "action_start": step_start + query,
        "action_end": step_start + query + duration,
        "step_end": step_start + query + duration,
        "action_exec_cost": duration,
        "before_lat": before[0],
        "before_lng": before[1],
        "after_lat": after[0],
        "after_lng": after[1],
    }


def _hash(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]


def _row(
    primitive: str,
    probe: str,
    predicted: str,
    observed: str,
    penalty_delta: float,
    aligned: bool,
    confidence: float,
    enabled_hard: bool,
    notes: str,
) -> dict[str, Any]:
    return {
        "primitive_name": primitive,
        "rule_hash_or_probe_id": _hash(primitive + probe),
        "probe_name": probe,
        "trajectory_description_hash": _hash(predicted + observed + notes),
        "predicted_by_controller": predicted,
        "observed_by_official_scorer": observed,
        "penalty_delta": round(float(penalty_delta), 2),
        "aligned": bool(aligned),
        "confidence": round(float(confidence), 3),
        "enabled_hard": bool(enabled_hard),
        "notes": notes,
    }


def build_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rule = _rule(1000.0)

    detail: list[dict[str, Any]] = []
    rest_ok = _eval_daily_rest([_ctx("wait", step_start=0, query=30, duration=480)], [0], 8, rule, "daily_rest", detail)
    rows.append(_row("WAIT_COVERAGE", "query_plus_wait_counts_as_wait_span", "query does not break wait coverage", "penalty=0" if rest_ok == 0 else "penalty>0", rest_ok, rest_ok == 0, 0.88, False, "wait intervals use step_start..step_end"))

    detail = []
    quiet_bad = _eval_scheduled_rest_window([_ctx("take_order", step_start=0, duration=120)], [0], 0, 0, 6, 0, rule, "quiet", detail)
    rows.append(_row("INTERVAL_OVERLAP", "take_during_quiet_window_penalized", "active take violates quiet window", f"penalty={quiet_bad}", quiet_bad, quiet_bad > 0, 0.9, False, "scheduled rest requires wait coverage across full window"))

    active_wait = _active_minutes_by_day([_ctx("wait", step_start=0, duration=1440)], [0])[0]
    active_repo = _active_minutes_by_day([_ctx("reposition", step_start=0, duration=60)], [0])[0]
    rows.append(_row("FULL_DAY_INACTIVE", "wait_inactive_reposition_active", "wait inactive; reposition active", f"wait_active={active_wait};reposition_active={active_repo}", active_repo - active_wait, active_wait == 0 and active_repo > 0, 0.92, False, "official inactive day counts take/reposition action time only"))

    detail = []
    off_pen = _eval_off_days([_ctx("wait", step_start=0, duration=1440)], [0], 1, rule, "off_day", detail)
    rows.append(_row("NO_ORDER_DAY", "full_wait_day_satisfies_off_day", "no take/reposition satisfies off day", f"penalty={off_pen}", off_pen, off_pen == 0, 0.91, False, "query is not active in active_minutes_by_day"))

    cargo_map = {
        "runtime_entity_hash": {
            "start_lat": 1.0,
            "start_lng": 0.0,
            "end_lat": 1.1,
            "end_lng": 0.1,
            "start_city": "runtime_value_hash",
            "end_city": "other_runtime_value_hash",
            "cargo_name": "GENERIC_CATEGORY",
        }
    }
    detail = []
    deadhead_pen = _eval_pickup_deadhead([_ctx("take_order", step_start=0, duration=60)], cargo_map, 55.0, rule, "deadhead", detail)
    rows.append(_row("PICKUP_DEADHEAD_LE", "pickup_deadhead_uses_before_to_start", "take over threshold penalized per take", f"penalty={deadhead_pen}", deadhead_pen, deadhead_pen > 0, 0.94, True, "direct action metric aligned"))

    detail = []
    region_pen = _eval_required_region_cargo_days([_ctx("take_order", step_start=1500, duration=60)], cargo_map, "runtime_value_hash", 1, rule, "distinct_day", detail)
    rows.append(_row("COUNT_DISTINCT_DAY", "required_region_counts_action_start_day", "accepted matching take repairs distinct-day quota", f"penalty={region_pen}", region_pen, region_pen == 0, 0.86, False, "month-end failed penalty, not per-action hard block"))

    capped = _penalty_count(4, _rule(1000.0, cap=2500.0))
    rows.append(_row("COUNT_CAPPED", "penalty_cap_applies_to_repeated_count", "4 violations capped at 2500", f"penalty={capped}", capped, capped == 2500.0, 0.95, True, "hard only when direct metric also aligned"))

    once = _penalty_failed(True, _rule(3000.0, cap=None))
    rows.append(_row("COUNT_ONCE_IF_FAILED", "failed_once_not_per_take", "failed terminal task charges once", f"penalty={once}", once, once == 3000.0, 0.9, False, "soft risk until terminal failure is certain"))

    detail = []
    dwell_ok = _eval_wait_at_location_on_day([_ctx("wait", step_start=0, duration=120, after=(0.0, 0.0))], 0, 0.0, 0.0, 2.0, 120, rule, "dwell", detail)
    rows.append(_row("DWELL_MINUTES", "wait_near_target_satisfies_dwell", "arrival then 120 wait repairs dwell", f"penalty={dwell_ok}", dwell_ok, dwell_ok == 0, 0.82, False, "location primitives remain repair-value only unless exact target slots are present"))

    detail = []
    route_ok = _eval_route_stops([_ctx("wait", step_start=0, duration=30, after=(0.0, 0.0))], [RouteStop(day=0, lat=0.0, lng=0.0, min_wait_minutes=0)], rule, "ordered", detail)
    rows.append(_row("ORDERED_SEQUENCE", "single_stop_arrival_satisfies_order_prefix", "arrival after previous stop advances sequence", f"penalty={route_ok}", route_ok, route_ok == 0, 0.8, False, "sequence is terminal/repair-value only"))

    return rows


def write_probe(out: Path = REPORT) -> list[dict[str, Any]]:
    rows = build_rows()
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "primitive_name",
        "rule_hash_or_probe_id",
        "probe_name",
        "trajectory_description_hash",
        "predicted_by_controller",
        "observed_by_official_scorer",
        "penalty_delta",
        "aligned",
        "confidence",
        "enabled_hard",
        "notes",
    ]
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--out", type=Path, default=REPORT)
    args = parser.parse_args()
    rows = write_probe(args.out)
    aligned = sum(1 for row in rows if row["aligned"])
    print({"rows": len(rows), "aligned": aligned, "out": str(args.out), "simulation_days": args.simulation_days})
    return 0 if aligned else 1


if __name__ == "__main__":
    raise SystemExit(main())
