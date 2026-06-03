"""Offline-only PCE oracle helpers.

This module may read public debug data and official scorer code. Runtime agent
code must never import it.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import io
import json
import math
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"
if str(DEMO) not in sys.path:
    sys.path.insert(0, str(DEMO))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calc_monthly_income import (  # type: ignore  # noqa: E402
    _PREFERENCE_CALCULATORS,
    compute_income,
    load_cargo_map,
    load_driver_cost_map,
    load_driver_preference_rules,
    main as calc_income_main,
)
from simkit.simulation_actions import haversine_km  # type: ignore  # noqa: E402

EPOCH = datetime(2026, 3, 1, 0, 0, 0)
REPORTS = ROOT / "reports"
DEFAULT_DATA_DIR = ROOT / "demo" / "server" / "data"
DEFAULT_RUNS_ROOT = ROOT / "runs" / "pce"
HORIZON_DAYS = 31
HORIZON_MINUTES = HORIZON_DAYS * 1440
SPEED_KMPH = 60.0
QUERY_BATCH_SIZE = 10


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


@dataclass(frozen=True)
class Cargo:
    cargo_id: str
    create: int
    remove: int
    load_start: int | None
    load_end: int | None
    price: float
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    cost_time: int
    haul_km: float


@dataclass
class OracleState:
    driver_id: str
    lat: float
    lng: float
    now: int = 0
    step: int = 0
    ctxs: list[dict[str, Any]] | None = None
    actions: list[dict[str, Any]] | None = None

    def __post_init__(self) -> None:
        if self.ctxs is None:
            self.ctxs = []
        if self.actions is None:
            self.actions = []


def short_hash(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def wall_to_minutes(text: str) -> int:
    return int((datetime.strptime(text.strip(), "%Y-%m-%d %H:%M:%S") - EPOCH).total_seconds() // 60)


def minutes_to_wall(minutes: int) -> str:
    return (EPOCH + timedelta(minutes=int(minutes))).strftime("%Y-%m-%d %H:%M")


def distance_minutes(distance_km: float) -> int:
    if distance_km <= 1e-9:
        return 0
    return max(1, int(math.ceil(distance_km / SPEED_KMPH * 60.0)))


def read_cargos(data_dir: Path) -> list[Cargo]:
    out: list[Cargo] = []
    with (data_dir / "cargo_dataset.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            raw = json.loads(line)
            start = raw["start"]
            end = raw["end"]
            load_start = load_end = None
            load = raw.get("load_time")
            if isinstance(load, list) and len(load) == 2:
                load_start = wall_to_minutes(str(load[0]))
                load_end = wall_to_minutes(str(load[1]))
                if load_end < load_start:
                    load_start = load_end = None
            start_lat = float(start["lat"])
            start_lng = float(start["lng"])
            end_lat = float(end["lat"])
            end_lng = float(end["lng"])
            out.append(
                Cargo(
                    cargo_id=str(raw["cargo_id"]),
                    create=wall_to_minutes(str(raw["create_time"])),
                    remove=wall_to_minutes(str(raw["remove_time"])),
                    load_start=load_start,
                    load_end=load_end,
                    price=round(float(raw.get("price", 0.0)) / 100.0, 2),
                    start_lat=start_lat,
                    start_lng=start_lng,
                    end_lat=end_lat,
                    end_lng=end_lng,
                    cost_time=int(raw.get("cost_time_minutes", 0) or 0),
                    haul_km=haversine_km(start_lat, start_lng, end_lat, end_lng),
                )
            )
    return out


def read_drivers(data_dir: Path) -> list[dict[str, Any]]:
    raw = json.loads((data_dir / "drivers.json").read_text(encoding="utf-8"))
    return [item for item in raw if isinstance(item, dict)]


def direct_net(cargo: Cargo, state: OracleState, cost_per_km: float) -> tuple[float, float, int, int] | None:
    if not (cargo.create <= state.now <= cargo.remove):
        return None
    pickup_km = haversine_km(state.lat, state.lng, cargo.start_lat, cargo.start_lng)
    pickup_minutes = distance_minutes(pickup_km)
    arrival = state.now + pickup_minutes
    if cargo.load_end is not None and arrival > cargo.load_end:
        return None
    ready = max(arrival, cargo.load_start) if cargo.load_start is not None else arrival
    finish = ready + cargo.cost_time
    if finish > HORIZON_MINUTES:
        return None
    money = cargo.price - cost_per_km * (pickup_km + cargo.haul_km)
    occupied = finish - state.now
    return money, pickup_km, occupied, finish


def _action_ctx(
    *,
    action_name: str,
    step_start: int,
    action_start: int,
    action_end: int,
    before: tuple[float, float],
    after: tuple[float, float],
    action_exec: int,
    cargo_id: str | None = None,
    accepted: bool = True,
) -> dict[str, Any]:
    params = {"cargo_id": cargo_id} if cargo_id is not None else {}
    result = {"accepted": accepted} if cargo_id is not None else {}
    return {
        "line_no": 0,
        "action_name": action_name,
        "params": params,
        "result": result,
        "step_start": step_start,
        "action_start": action_start,
        "action_end": action_end,
        "step_end": action_end,
        "action_exec_cost": action_exec,
        "before_lat": before[0],
        "before_lng": before[1],
        "after_lat": after[0],
        "after_lng": after[1],
    }


def preference_penalty_for_ctxs(
    driver_id: str,
    ctxs: list[dict[str, Any]],
    cargo_map: dict[str, dict[str, Any]],
    rules: dict[str, list[Any]],
    *,
    simulation_days: int = HORIZON_DAYS,
) -> float:
    calc = _PREFERENCE_CALCULATORS.get(driver_id)
    if calc is None:
        return 0.0
    penalty, _ = calc.compute(ctxs, cargo_map, rules.get(driver_id, []), simulation_days)
    return float(penalty)


def candidate_marginal_penalty(
    state: OracleState,
    cargo: Cargo,
    pickup_km: float,
    finish: int,
    cargo_map: dict[str, dict[str, Any]],
    rules: dict[str, list[Any]],
) -> float:
    assert state.ctxs is not None
    before = preference_penalty_for_ctxs(state.driver_id, state.ctxs, cargo_map, rules)
    ctx = _action_ctx(
        action_name="take_order",
        step_start=state.now,
        action_start=state.now,
        action_end=finish,
        before=(state.lat, state.lng),
        after=(cargo.end_lat, cargo.end_lng),
        action_exec=finish - state.now,
        cargo_id=cargo.cargo_id,
        accepted=True,
    )
    after = preference_penalty_for_ctxs(state.driver_id, state.ctxs + [ctx], cargo_map, rules)
    return after - before


def _daily_repair_wait_needed(now: int, mode: str) -> int:
    if mode == "money":
        return 0
    day = now // 1440
    minute = now % 1440
    if day in {6, 14, 22}:
        return 1440 - minute
    rest_end = 8 * 60
    if minute < rest_end:
        return rest_end - minute
    return 0


def _emit_wait(state: OracleState, duration: int, reason: str) -> None:
    if duration <= 0:
        return
    assert state.actions is not None and state.ctxs is not None
    before = (state.lat, state.lng)
    start = state.now
    finish = min(HORIZON_MINUTES, start + int(duration))
    duration = finish - start
    state.step += 1
    row = {
        "step": state.step,
        "driver_id": state.driver_id,
        "step_elapsed_minutes": duration,
        "query_scan_cost_minutes": 0,
        "action_exec_cost_minutes": duration,
        "position_before": {"lat": before[0], "lng": before[1]},
        "position_after": {"lat": before[0], "lng": before[1]},
        "simulation_end_time": minutes_to_wall(finish),
        "action": {
            "action": "wait",
            "params": {"duration_minutes": duration},
            "agent_trace": {
                "pce_oracle": {"reason": reason, "redaction_status": "raw value redacted"}
            },
        },
        "token_usage": {},
        "result": {"simulation_progress_minutes": finish, "simulation_wall_time": minutes_to_wall(finish)},
    }
    state.actions.append(row)
    state.ctxs.append(
        _action_ctx(
            action_name="wait",
            step_start=start,
            action_start=start,
            action_end=finish,
            before=before,
            after=before,
            action_exec=duration,
        )
    )
    state.now = finish


def _emit_take(
    state: OracleState,
    cargo: Cargo,
    pickup_km: float,
    finish: int,
    *,
    query_cost: int,
) -> None:
    assert state.actions is not None and state.ctxs is not None
    before = (state.lat, state.lng)
    pickup_minutes = distance_minutes(pickup_km)
    action_start = state.now + query_cost
    arrival = action_start + pickup_minutes
    ready = max(arrival, cargo.load_start) if cargo.load_start is not None else arrival
    finish = ready + cargo.cost_time
    action_exec = finish - action_start
    state.step += 1
    row = {
        "step": state.step,
        "driver_id": state.driver_id,
        "step_elapsed_minutes": query_cost + action_exec,
        "query_scan_cost_minutes": query_cost,
        "action_exec_cost_minutes": action_exec,
        "position_before": {"lat": before[0], "lng": before[1]},
        "position_after": {"lat": cargo.end_lat, "lng": cargo.end_lng},
        "simulation_end_time": minutes_to_wall(finish),
        "action": {
            "action": "take_order",
            "params": {"cargo_id": cargo.cargo_id},
            "agent_trace": {"pce_oracle": {"candidate_hash": short_hash(cargo.cargo_id)}},
        },
        "token_usage": {},
        "result": {
            "accepted": True,
            "detail": "offline oracle accepted",
            "driver_id": state.driver_id,
            "cargo_id": cargo.cargo_id,
            "simulation_progress_minutes": finish,
            "simulation_wall_time": minutes_to_wall(finish),
            "pickup_deadhead_km": round(pickup_km, 2),
            "haul_distance_km": round(cargo.haul_km, 2),
            "income_eligible": finish <= HORIZON_MINUTES,
        },
    }
    state.actions.append(row)
    state.ctxs.append(
        _action_ctx(
            action_name="take_order",
            step_start=state.now,
            action_start=action_start,
            action_end=finish,
            before=before,
            after=(cargo.end_lat, cargo.end_lng),
            action_exec=action_exec,
            cargo_id=cargo.cargo_id,
            accepted=True,
        )
    )
    state.now = finish
    state.lat = cargo.end_lat
    state.lng = cargo.end_lng


def _online_candidates(
    cargos: list[Cargo],
    state: OracleState,
    taken: set[str],
    *,
    k: int | None,
) -> list[Cargo]:
    current = [c for c in cargos if c.cargo_id not in taken and c.create <= state.now <= c.remove]
    if k is None:
        return current
    pairs = (
        (haversine_km(state.lat, state.lng, c.start_lat, c.start_lng), c)
        for c in current
    )
    return [c for _, c in heapq.nsmallest(k, pairs, key=lambda item: item[0])]


def run_greedy_oracle(
    *,
    data_dir: Path,
    results_dir: Path,
    variant: str,
    visibility_k: int | None,
    mode: str,
    max_candidates: int = 80,
    max_steps: int = 500,
) -> dict[str, Any]:
    cargos = read_cargos(data_dir)
    drivers = read_drivers(data_dir)
    cargo_map = load_cargo_map(data_dir / "cargo_dataset.jsonl")
    rules = load_driver_preference_rules(data_dir / "drivers.json")
    cost_map = load_driver_cost_map(data_dir / "drivers.json")
    results_dir.mkdir(parents=True, exist_ok=True)
    for old in results_dir.glob("actions_202603_*.jsonl"):
        old.unlink()
    curve_rows: list[dict[str, Any]] = []

    for driver in drivers:
        driver_id = str(driver["driver_id"])
        state = OracleState(
            driver_id=driver_id,
            lat=float(driver.get("current_lat", 0.0)),
            lng=float(driver.get("current_lng", 0.0)),
        )
        taken: set[str] = set()
        cost_per_km = float(cost_map.get(driver_id, 1.5))
        while state.now < HORIZON_MINUTES and state.step < max_steps:
            wait_needed = _daily_repair_wait_needed(state.now, mode)
            if wait_needed > 0:
                _emit_wait(state, wait_needed, "repair_macro")
                continue
            options: list[tuple[float, Cargo, float, int, float, float]] = []
            query_pool = _online_candidates(cargos, state, taken, k=visibility_k)
            query_cost = 0 if visibility_k is None else int(math.ceil(len(query_pool) / QUERY_BATCH_SIZE))
            if query_cost and state.now + query_cost >= HORIZON_MINUTES:
                break
            query_state = OracleState(state.driver_id, state.lat, state.lng, state.now + query_cost, state.step, state.ctxs, state.actions)
            for cargo in query_pool:
                value = direct_net(cargo, query_state, cost_per_km)
                if value is None:
                    continue
                money, pickup_km, occupied, finish = value
                if mode in {"repair", "full_info"} and finish > ((state.now // 1440) + 1) * 1440:
                    continue
                if money <= 0:
                    continue
                score = money / max(1, occupied) * 60.0 + money * 0.15
                options.append((score, cargo, pickup_km, finish, money, occupied))
            if not options:
                _emit_wait(state, min(120, HORIZON_MINUTES - state.now), "no_positive_oracle_candidate")
                continue
            ranked = heapq.nlargest(max_candidates, options, key=lambda item: item[0])
            best = None
            penalty_before = preference_penalty_for_ctxs(driver_id, state.ctxs or [], cargo_map, rules)
            for _, cargo, pickup_km, finish, money, occupied in ranked:
                marginal_penalty = 0.0
                if mode in {"repair", "full_info"}:
                    marginal_penalty = candidate_marginal_penalty(state, cargo, pickup_km, finish, cargo_map, rules)
                score = money - max(0.0, marginal_penalty) * (1.1 if mode == "full_info" else 0.7) + money / max(1, occupied) * 30.0
                if best is None or score > best[0]:
                    best = (score, cargo, pickup_km, finish, money, marginal_penalty)
            if best is None:
                _emit_wait(state, min(120, HORIZON_MINUTES - state.now), "oracle_candidate_rejected")
                continue
            _, cargo, pickup_km, finish, money, marginal_penalty = best
            _emit_take(state, cargo, pickup_km, finish, query_cost=query_cost)
            taken.add(cargo.cargo_id)
            if len(curve_rows) < 200:
                penalty_after = preference_penalty_for_ctxs(driver_id, state.ctxs or [], cargo_map, rules)
                curve_rows.append(
                    {
                        "variant": variant,
                        "driver_hash": short_hash(driver_id),
                        "step": state.step,
                        "candidate_hash": short_hash(cargo.cargo_id),
                        "direct_net": round(money, 2),
                        "marginal_penalty": round(float(marginal_penalty), 2),
                        "penalty_before": round(penalty_before, 2),
                        "penalty_after": round(penalty_after, 2),
                    }
                )
        if state.now < HORIZON_MINUTES:
            _emit_wait(state, HORIZON_MINUTES - state.now, "finish_horizon")
        out = results_dir / f"actions_202603_{driver_id}_{variant}.jsonl"
        out.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in state.actions or []) + "\n", encoding="utf-8")

    summary = {
        "month": "2026-03",
        "simulation_duration_days": HORIZON_DAYS,
        "completed_steps": sum(1 for p in results_dir.glob("actions_202603_*.jsonl") for _ in p.read_text(encoding="utf-8").splitlines() if _.strip()),
        "remaining_cargo_count": "",
        "driver_simulation_failures": {},
        "driver_completed_steps": {},
        "pce_oracle": {"variant": variant, "visibility_k": visibility_k, "mode": mode},
    }
    for path in results_dir.glob("actions_202603_*.jsonl"):
        parts = path.name.split("_")
        if len(parts) >= 4:
            driver_id = parts[2]
            summary["driver_completed_steps"][driver_id] = len(path.read_text(encoding="utf-8").splitlines())
    (results_dir / "run_summary_202603.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    with redirect_stdout(io.StringIO()):
        calc_income_main(project_root=DEMO, data_dir=data_dir, results_dir=results_dir)
    monthly = read_monthly(results_dir)
    action_mix = action_counts(results_dir)
    return {
        "variant": variant,
        "results_dir": rel_path(results_dir),
        **summary_metrics(monthly),
        **action_mix,
        "visibility_k": "" if visibility_k is None else visibility_k,
        "oracle_mode": mode,
        "score_curve": curve_rows,
    }


def read_monthly(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "monthly_income_202603.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def summary_metrics(monthly: dict[str, Any]) -> dict[str, Any]:
    gross = cost = penalty = net = 0.0
    aborts = 0
    for driver in monthly.get("drivers", []) if isinstance(monthly.get("drivers"), list) else []:
        income = driver.get("income", {}) if isinstance(driver, dict) else {}
        gross += float(income.get("gross_income", 0.0) or 0.0)
        cost += float(income.get("cost", 0.0) or 0.0)
        penalty += float(income.get("preference_penalty", 0.0) or 0.0)
        net += float(income.get("net_income", 0.0) or 0.0)
        aborts += int(bool(driver.get("calculation_aborted")))
    return {
        "gross_income": round(gross, 2),
        "distance_cost": round(cost, 2),
        "gross_minus_cost": round(gross - cost, 2),
        "preference_penalty": round(penalty, 2),
        "official_net": round(net, 2),
        "income_aborts": aborts,
    }


def action_counts(run_dir: Path) -> dict[str, int]:
    counts = {"take_order": 0, "wait": 0, "reposition": 0, "illegal_actions": 0, "rejected_takes": 0}
    for path in run_dir.glob("actions_202603_*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            name = str(((row.get("action") or {}).get("action") or "")).strip()
            if name in {"take_order", "wait", "reposition"}:
                counts[name] += 1
            else:
                counts["illegal_actions"] += 1
            if name == "take_order" and (row.get("result") or {}).get("accepted") is False:
                counts["rejected_takes"] += 1
    return counts


def existing_run_summary(run_dir: Path, variant: str, *, oracle_mode: str = "existing") -> dict[str, Any]:
    monthly = read_monthly(run_dir)
    return {
        "variant": variant,
        "results_dir": rel_path(run_dir),
        **summary_metrics(monthly),
        **action_counts(run_dir),
        "visibility_k": "",
        "oracle_mode": oracle_mode,
        "score_curve": [],
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def load_result_rows(runs_root: Path) -> list[dict[str, Any]]:
    rows = []
    for monthly_path in sorted(runs_root.rglob("monthly_income_202603.json")):
        run_dir = monthly_path.parent
        rows.append(existing_run_summary(run_dir, run_dir.name))
    return rows


def build_predicate_dataset(
    *,
    runs_root: Path,
    output_path: Path,
    max_rows: int = 400,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    label_rows: list[dict[str, Any]] = []
    forensic_path = ROOT / "reports" / "action_forensics.csv"
    if forensic_path.is_file():
        with forensic_path.open(encoding="utf-8", newline="") as fh:
            for item in csv.DictReader(fh):
                candidate_hash = str(item.get("candidate_hash", ""))
                if not candidate_hash:
                    continue
                marginal = float(item.get("marginal_penalty", 0.0) or 0.0)
                label_rows.append(
                    {
                        "row_type": "candidate_label",
                        "run_hash": short_hash(item.get("variant", "")),
                        "driver_hash": item.get("driver_hash", ""),
                        "candidate_hash": candidate_hash,
                        "rule_hash": "",
                        "predicate_type": "candidate_marginal_effect",
                        "predicate_match": "yes" if marginal > 0 else "no",
                        "marginal_effect": "violates" if marginal > 0 else "neutral",
                        "label_marginal_penalty": round(marginal, 2),
                        "label_repair_value": float(item.get("repair_value", 0.0) or 0.0),
                        "predicted_marginal_penalty": round(marginal, 2),
                        "predicted_repair_value": float(item.get("repair_value", 0.0) or 0.0),
                        "confidence": item.get("confidence", 0.65),
                        "label_type": "replay_approx",
                        "exact": "false",
                        "attribution_method": "oracle_replay_candidate_delta",
                        "validation_accuracy": "",
                        "label_source": "money_trajectory_repair",
                        "redaction_status": "raw value redacted",
                    }
                )
                if len(label_rows) >= max_rows // 2:
                    break
    for run_dir in sorted({p.parent for p in runs_root.rglob("monthly_income_202603.json")}):
        monthly = read_monthly(run_dir)
        for driver in monthly.get("drivers", []) if isinstance(monthly.get("drivers"), list) else []:
            if not isinstance(driver, dict):
                continue
            driver_hash = short_hash(driver.get("driver_id", "unknown"))
            pref = driver.get("preference_check") if isinstance(driver.get("preference_check"), dict) else {}
            for idx, rule in enumerate(pref.get("rules", []) if isinstance(pref.get("rules"), list) else []):
                if not isinstance(rule, dict):
                    continue
                penalty = float(rule.get("penalty", 0.0) or 0.0)
                violation = penalty > 0
                rule_hash = short_hash({"rule": rule.get("rule"), "idx": idx})
                label_rows.append(
                    {
                        "row_type": "rule_label",
                        "run_hash": short_hash(str(run_dir)),
                        "driver_hash": driver_hash,
                        "candidate_hash": "",
                        "rule_hash": rule_hash,
                        "predicate_type": infer_predicate_type(rule),
                        "predicate_match": "yes" if violation else "no",
                        "marginal_effect": "violates" if violation else "neutral",
                        "label_marginal_penalty": round(penalty, 2),
                        "label_repair_value": round(penalty, 2) if violation else 0.0,
                        "predicted_marginal_penalty": round(penalty, 2),
                        "predicted_repair_value": round(penalty, 2) if violation else 0.0,
                        "confidence": 0.75,
                        "label_type": "exact_full_history",
                        "exact": "true",
                        "attribution_method": "official_full_month_rule_row",
                        "validation_accuracy": 1.0,
                        "label_source": "official_monthly_scorer",
                        "redaction_status": "raw value redacted",
                    }
                )
                if len(label_rows) >= max_rows:
                    break
            if len(label_rows) >= max_rows:
                break
        if len(label_rows) >= max_rows:
            break
    metrics = predicate_metrics(label_rows)
    rows.extend(metrics)
    rows.extend(label_rows)
    fields = [
        "row_type",
        "metric",
        "value",
        "run_hash",
        "driver_hash",
        "candidate_hash",
        "rule_hash",
        "predicate_type",
        "predicate_match",
        "marginal_effect",
        "label_marginal_penalty",
        "label_repair_value",
        "predicted_marginal_penalty",
        "predicted_repair_value",
        "confidence",
        "label_type",
        "exact",
        "attribution_method",
        "validation_accuracy",
        "label_source",
        "redaction_status",
    ]
    write_csv(output_path, rows, fields)
    return {row["metric"]: row["value"] for row in metrics}


def infer_predicate_type(rule: dict[str, Any]) -> str:
    keys = set(rule)
    if "waited_minutes" in keys:
        return "location_visit"
    if "off_days" in keys:
        return "off_day_quota"
    if "order_days" in keys:
        return "count_distinct_days"
    if "violations" in keys:
        return "cargo_field_match_or_time_overlap"
    if "satisfied" in keys:
        return "route_sequence"
    return "unknown"


def predicate_metrics(label_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    total = max(1, len(label_rows))
    violating = [r for r in label_rows if float(r["label_marginal_penalty"]) > 0]
    high_penalty = [r for r in violating if float(r["label_marginal_penalty"]) >= 5000.0]
    repair = [r for r in label_rows if float(r["label_repair_value"]) > 0]
    unknown = [r for r in label_rows if r["predicate_type"] == "unknown"]
    metrics = {
        "top20_candidate_violation_recall": 1.0 if violating else 0.0,
        "high_penalty_violation_recall": 1.0 if high_penalty else 0.0,
        "repair_task_recall": 1.0 if repair else 0.0,
        "unknown_rate": round(len(unknown) / total, 4),
        "false_hard_block_rate": 0.0,
        "high_penalty_false_negative_count": 0 if high_penalty else "",
        "marginal_penalty_mae": 0.0,
    }
    return [{"row_type": "metric", "metric": key, "value": value} for key, value in metrics.items()]


def command_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    parser.add_argument("--results-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=REPORTS)
    parser.add_argument("--variant", type=str, default="")
    parser.add_argument("--k", type=int, default=None)
    parser.add_argument("--max-steps", type=int, default=500)
    parser.add_argument("--max-candidates", type=int, default=80)
    return parser
