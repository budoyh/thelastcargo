"""Execute CROWN-FUSE reference rows and parameter grid rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT_PATH = Path(__file__).resolve().parents[1]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from tools.trident_utils import (  # noqa: E402
    REPORTS,
    ROOT,
    RUNS,
    TRIDENT_EXPERIMENT_FIELDS,
    iter_action_rows,
    run_local_eval,
    summarize_trident_run,
)


FUSE_GRID_FIELDS = [
    *TRIDENT_EXPERIMENT_FIELDS,
    "variant_key",
    "trial_id",
    "params_hash",
    "run_dir",
    "repair_trigger_count",
    "repair_minutes_total",
    "repair_wait_minutes_per_day_p50",
    "repair_wait_minutes_per_day_p90",
    "repair_wait_minutes_per_day_max",
    "b0_shadow_override_count",
    "b0_shadow_fallback_count",
    "net_delta_vs_b0",
    "penalty_delta_vs_b0",
    "auditor_adjustment_nonzero",
    "controller_score_changed",
    "json_valid_rate",
    "graph_alpha",
    "package_candidate",
    "top5_0509_sanity",
    "fallback_to_b0",
    "default_variant_verified",
    "selected_reason",
]


@dataclass(frozen=True)
class FuseSpec:
    variant_key: str
    variant_name: str
    variant: str
    run_dir: Path
    env: dict[str, str] = field(default_factory=dict)
    trial_id: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    dataset: str = "20260529"
    package_candidate: bool = False
    top5_0509_sanity: bool = False
    fallback_to_b0: bool = False
    default_variant_verified: bool = False
    selected_reason: str = ""


def json_cell(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def params_hash(params: dict[str, Any]) -> str:
    payload = json.dumps(params, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _gold_env(**updates: str) -> dict[str, str]:
    env = {
        "CROWN_GOLD_ENABLE_FIREWALL": "1",
        "CROWN_GOLD_ENABLE_LINKER": "1",
        "CROWN_GOLD_ENABLE_AUDITOR": "0",
        "CROWN_GOLD_ENABLE_REPAIR": "1",
        "CROWN_GOLD_ENABLE_VISIBLE_GRAPH_MPC": "0",
        "CROWN_TRIDENT_ENABLE_VISIBLE_GRAPH_MPC": "0",
    }
    env.update(updates)
    return env


def reference_specs(results_root: Path) -> list[FuseSpec]:
    return [
        FuseSpec(
            "B0",
            "B0_rescue",
            "best_rescue",
            RUNS / "fuse" / "b0_rescue",
            notes="Immutable best_rescue reference.",
        ),
        FuseSpec(
            "B9c",
            "B9c_reference_current_branch",
            "crown_gold_contract_mpc",
            results_root / "b9c_reference",
            _gold_env(CROWN_Y_FULL_REST_PERIOD_DAYS="10"),
            notes="Current-branch broad wait repair reference; used only for ledger contrast.",
        ),
    ]


def fuse_env_from_params(params: dict[str, Any]) -> dict[str, str]:
    mapping = {
        "wait_repair_strength": "CROWN_FUSE_WAIT_REPAIR_STRENGTH",
        "repair_value_scale": "CROWN_FUSE_REPAIR_VALUE_SCALE",
        "verified_penalty_scale": "CROWN_FUSE_VERIFIED_PENALTY_SCALE",
        "repair_roi_threshold": "CROWN_FUSE_REPAIR_ROI_THRESHOLD",
        "lost_gross_cap": "CROWN_FUSE_LOST_GROSS_CAP",
        "max_repair_wait_per_day": "CROWN_FUSE_MAX_REPAIR_WAIT_PER_DAY",
        "repair_start_day": "CROWN_FUSE_REPAIR_START_DAY",
        "repair_end_day": "CROWN_FUSE_REPAIR_END_DAY",
        "gross_floor_curve": "CROWN_FUSE_GROSS_FLOOR_CURVE",
        "min_profit_to_override_repair": "CROWN_FUSE_MIN_PROFIT_TO_OVERRIDE_REPAIR",
        "soft_violation_profit_threshold": "CROWN_FUSE_SOFT_VIOLATION_PROFIT_THRESHOLD",
        "unknown_soft_risk": "CROWN_FUSE_UNKNOWN_SOFT_RISK",
        "already_failed_discount": "CROWN_FUSE_ALREADY_FAILED_DISCOUNT",
        "cap_discount": "CROWN_FUSE_CAP_DISCOUNT",
    }
    env = {"CROWN_FUSE_ENABLE_TARGETED_REPAIR": "1", "CROWN_FUSE_AUDITOR_NUMERIC": str(int(bool(params.get("qwen_auditor_numeric", 0))))}
    for key, env_key in mapping.items():
        if key in params:
            env[env_key] = str(params[key])
    return env


def hand_grid(limit: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    strengths = [0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 0.75, 1.00]
    value_scales = [0.25, 0.50, 0.75, 1.00]
    penalty_scales = [0.50, 0.75, 1.00]
    roi_values = [0.8, 1.0, 1.5, 2.0, 3.0]
    lost_caps = [500, 1000, 2000, 4000, 6000]
    wait_budgets = [60, 120, 240, 360, 720, 1440]
    windows = [(1, 20), (8, 24), (12, 28), (15, 31), (20, 31)]
    floors = ["off", "mild", "medium", "strong"]
    min_profit = [100, 200, 350, 600]
    soft_profit = [200, 500, 1000]
    unknown = [0.05, 0.10, 0.25]
    failed_discount = [0.0, 0.25, 0.5, 1.0]
    cap_discount = [0.0, 0.25, 0.5, 1.0]

    # Keep trial_001 through trial_003 identical to already-executed rows.
    legacy_prefix = [
        (0.05, 0.25, 0.50, 0.8, 500, 60, (1, 20), "off", 100, 200, 0.05, 0.0, 0.0),
        (0.05, 0.25, 0.50, 0.8, 500, 60, (8, 24), "mild", 200, 500, 0.10, 0.25, 0.25),
        (0.05, 0.25, 0.50, 0.8, 500, 60, (12, 28), "medium", 350, 1000, 0.25, 0.5, 0.5),
    ]
    seeded = [
        (0.50, 1.00, 1.00, 0.8, 4000, 360, (1, 31), "off", 100, 200, 0.05, 0.0, 0.0),
        (1.00, 1.00, 1.00, 0.8, 6000, 1440, (1, 31), "off", 100, 200, 0.05, 0.0, 0.0),
        (1.00, 1.00, 1.00, 1.0, 4000, 360, (1, 24), "mild", 100, 200, 0.05, 0.25, 0.0),
        (0.75, 1.00, 1.00, 1.0, 4000, 720, (8, 31), "mild", 200, 500, 0.10, 0.25, 0.25),
        (0.30, 1.00, 1.00, 1.0, 4000, 360, (8, 31), "mild", 100, 200, 0.05, 0.25, 0.0),
        (0.50, 0.75, 1.00, 1.0, 2000, 240, (12, 31), "mild", 200, 500, 0.10, 0.25, 0.25),
        (0.30, 0.75, 0.75, 1.5, 2000, 240, (8, 24), "medium", 200, 500, 0.10, 0.50, 0.25),
        (0.20, 1.00, 1.00, 1.0, 4000, 120, (15, 31), "medium", 350, 500, 0.10, 0.25, 0.50),
        (0.50, 0.50, 1.00, 2.0, 1000, 360, (20, 31), "strong", 350, 1000, 0.25, 0.50, 0.50),
        (0.15, 1.00, 0.75, 0.8, 2000, 120, (1, 20), "off", 100, 200, 0.05, 0.0, 0.25),
        (0.30, 0.50, 1.00, 1.5, 1000, 240, (12, 28), "mild", 200, 500, 0.10, 0.25, 0.50),
        (0.20, 0.75, 1.00, 2.0, 4000, 60, (1, 31), "strong", 600, 1000, 0.25, 0.50, 0.50),
        (0.50, 1.00, 0.75, 3.0, 4000, 360, (8, 24), "medium", 600, 1000, 0.25, 1.0, 0.50),
        (0.50, 1.00, 1.00, 0.8, 6000, 1440, (8, 24), "off", 100, 200, 0.05, 0.0, 0.0),
        (0.30, 1.00, 1.00, 1.0, 6000, 1440, (15, 31), "mild", 200, 500, 0.10, 0.25, 0.0),
        (0.20, 0.75, 1.00, 1.5, 4000, 720, (8, 31), "medium", 350, 500, 0.10, 0.25, 0.25),
        (0.15, 1.00, 0.75, 2.0, 4000, 720, (20, 31), "strong", 600, 1000, 0.25, 0.50, 0.50),
    ]

    def append_tuple(values: tuple[Any, ...]) -> None:
        strength, value, penalty, roi, cap, budget, window, floor, min_take, soft_take, unknown_risk, failed, capped = values
        rows.append(
            {
                "wait_repair_strength": strength,
                "repair_value_scale": value,
                "verified_penalty_scale": penalty,
                "repair_roi_threshold": roi,
                "lost_gross_cap": cap,
                "max_repair_wait_per_day": budget,
                "repair_start_day": window[0],
                "repair_end_day": window[1],
                "gross_floor_curve": floor,
                "min_profit_to_override_repair": min_take,
                "soft_violation_profit_threshold": soft_take,
                "unknown_soft_risk": unknown_risk,
                "already_failed_discount": failed,
                "cap_discount": capped,
                "qwen_auditor_numeric": 0,
            }
        )

    for values in legacy_prefix + seeded:
        if len(rows) >= limit:
            return rows
        append_tuple(values)

    seen = {json_cell(row) for row in rows}
    salt = 0
    while len(rows) < limit:
        idx = len(rows) + salt
        params = {
            "wait_repair_strength": strengths[(idx * 5 + 1) % len(strengths)],
            "repair_value_scale": value_scales[(idx * 3 + 2) % len(value_scales)],
            "verified_penalty_scale": penalty_scales[(idx * 2 + 1) % len(penalty_scales)],
            "repair_roi_threshold": roi_values[(idx * 7 + 3) % len(roi_values)],
            "lost_gross_cap": lost_caps[(idx * 5 + 2) % len(lost_caps)],
            "max_repair_wait_per_day": wait_budgets[(idx * 3 + 1) % len(wait_budgets)],
            "repair_start_day": windows[(idx * 2 + 1) % len(windows)][0],
            "repair_end_day": windows[(idx * 2 + 1) % len(windows)][1],
            "gross_floor_curve": floors[(idx * 3) % len(floors)],
            "min_profit_to_override_repair": min_profit[(idx * 5 + 2) % len(min_profit)],
            "soft_violation_profit_threshold": soft_profit[(idx * 7 + 1) % len(soft_profit)],
            "unknown_soft_risk": unknown[(idx * 2) % len(unknown)],
            "already_failed_discount": failed_discount[(idx * 3 + 1) % len(failed_discount)],
            "cap_discount": cap_discount[(idx * 5 + 2) % len(cap_discount)],
            "qwen_auditor_numeric": 0,
        }
        key = json_cell(params)
        if key in seen:
            salt += 1
            continue
        seen.add(key)
        rows.append(params)
    return rows


def search_specs(results_root: Path, trials: int, dataset: str) -> list[FuseSpec]:
    out: list[FuseSpec] = []
    for idx, params in enumerate(hand_grid(trials), start=1):
        trial_id = f"trial_{idx:03d}"
        out.append(
            FuseSpec(
                "TRIAL",
                trial_id,
                "fuse_targeted_repair",
                results_root / dataset / trial_id,
                fuse_env_from_params(params),
                trial_id=trial_id,
                params=params,
                notes="Executed Fuse targeted repair grid row.",
                dataset=dataset,
            )
        )
    return out


def graph_specs(results_root: Path, baseline_params: dict[str, Any], dataset: str = "20260529") -> list[FuseSpec]:
    specs: list[FuseSpec] = []
    for key, alpha in [("G0", 0.0), ("G1", 0.03), ("G2", 0.05), ("G3", 0.10)]:
        params = dict(baseline_params)
        params["graph_alpha"] = alpha
        env = fuse_env_from_params(params)
        env["CROWN_TRIDENT_VISIBLE_GRAPH_ALPHA"] = str(alpha)
        env["CROWN_TRIDENT_ENABLE_VISIBLE_GRAPH_MPC"] = "1"
        env["CROWN_FUSE_GRAPH_TAKE_ONLY"] = "1"
        specs.append(
            FuseSpec(
                key,
                f"{key}_graph_alpha_{alpha:.2f}",
                "fuse_targeted_repair",
                results_root / dataset / f"{key}_graph_alpha_{alpha:.2f}",
                env,
                trial_id=key,
                params=params,
                notes="Tiny graph diagnostic; take ranking only by policy.",
                dataset=dataset,
            )
        )
    return specs


def auditor_specs(results_root: Path, baseline_params: dict[str, Any], dataset: str = "20260529") -> list[FuseSpec]:
    out: list[FuseSpec] = []
    for key, weight in [("A0", 0.0), ("A1", 0.5), ("A2", 1.5)]:
        params = dict(baseline_params)
        params["qwen_auditor_numeric"] = 1 if weight else 0
        params["auditor_weight"] = weight
        env = fuse_env_from_params(params)
        env["CROWN_FUSE_AUDITOR_NUMERIC"] = "1" if weight else "0"
        env["CROWN_TRIDENT_QWEN_AUDIT_SCALE"] = str(weight)
        out.append(
            FuseSpec(
                key,
                "A0_auditor_score_off" if key == "A0" else ("A1_auditor_score_on_low_weight" if key == "A1" else "A2_auditor_score_on_high_weight"),
                "fuse_targeted_repair",
                results_root / dataset / key,
                env,
                trial_id=key,
                params=params,
                notes="Qwen auditor numeric ablation; final default is off unless this beats A0.",
                dataset=dataset,
            )
        )
    return out


def final_specs(results_root: Path, params: dict[str, Any], *, fallback_to_b0: bool, dataset: str = "20260529") -> list[FuseSpec]:
    env = fuse_env_from_params(params)
    b10 = FuseSpec(
        "B10",
        "B10_parameter_search_best",
        "fuse_targeted_repair",
        results_root / dataset / "B10_parameter_search_best",
        env,
        trial_id="B10",
        params=params,
        notes="Best executed Fuse parameter-search row.",
        dataset=dataset,
    )
    if fallback_to_b0:
        return [
            b10,
            FuseSpec(
                "B11",
                "B11_final_selected",
                "best_rescue",
                results_root / dataset / "B11_final_selected_b0_fallback",
                {},
                trial_id="B11",
                params={},
                notes="Explicit B0 fallback rerun after Fuse search.",
                dataset=dataset,
                fallback_to_b0=True,
                default_variant_verified=True,
                selected_reason="no_search_variant_beat_b0",
            )
        ]
    return [
        b10,
        FuseSpec(
            "B11",
            "B11_final_selected",
            "fuse_targeted_repair",
            results_root / dataset / "B11_final_selected",
            env,
            trial_id="B11",
            params=params,
            notes="Final selected Fuse strategy after code/config freeze.",
            dataset=dataset,
            default_variant_verified=True,
            selected_reason="best_search_variant",
        ),
    ]


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _safe_int(value: Any) -> int:
    try:
        return int(float(value or 0))
    except (TypeError, ValueError):
        return 0


def _trace(row: dict[str, Any]) -> dict[str, Any]:
    action = row.get("action") if isinstance(row.get("action"), dict) else {}
    trace = action.get("agent_trace") if isinstance(action.get("agent_trace"), dict) else {}
    return trace if isinstance(trace, dict) else {}


def fuse_metrics(run_dir: Path) -> dict[str, Any]:
    trigger = 0
    minutes_total = 0
    overrides = 0
    fallbacks = 0
    day_minutes: dict[int, int] = {}
    json_valid = 0
    auditor_rows = 0
    auditor_nonzero = 0
    for _, _, action_row in iter_action_rows(run_dir):
        rescue = _trace(action_row).get("rescue")
        rescue = rescue if isinstance(rescue, dict) else {}
        fuse = rescue.get("fuse") if isinstance(rescue.get("fuse"), dict) else {}
        trigger += _safe_int(fuse.get("repair_trigger_count"))
        minutes = _safe_int(fuse.get("repair_minutes"))
        minutes_total += minutes
        if fuse.get("b0_shadow_override"):
            overrides += 1
        if fuse.get("b0_shadow_fallback"):
            fallbacks += 1
        if minutes:
            result = action_row.get("result") if isinstance(action_row.get("result"), dict) else {}
            progress = _safe_int(result.get("simulation_progress_minutes"))
            day = progress // 1440
            day_minutes[day] = day_minutes.get(day, 0) + minutes
        ptt = rescue.get("ptt") if isinstance(rescue.get("ptt"), dict) else {}
        firewall = ptt.get("firewall") if isinstance(ptt.get("firewall"), dict) else {}
        for item in firewall.get("qwen_effect_rows", []) if isinstance(firewall.get("qwen_effect_rows"), list) else []:
            if isinstance(item, dict):
                auditor_rows += 1
                json_valid += int(bool(item.get("json_valid")))
                auditor_nonzero += int(abs(_safe_float(item.get("applied_score_adjustment"))) > 1e-9)
    values = sorted(day_minutes.values())
    if values:
        p50 = statistics.median(values)
        p90 = values[min(len(values) - 1, int((len(values) - 1) * 0.90))]
        max_value = max(values)
    else:
        p50 = p90 = max_value = 0
    return {
        "repair_trigger_count": trigger,
        "repair_minutes_total": minutes_total,
        "repair_wait_minutes_per_day_p50": round(float(p50), 2),
        "repair_wait_minutes_per_day_p90": round(float(p90), 2),
        "repair_wait_minutes_per_day_max": max_value,
        "b0_shadow_override_count": overrides,
        "b0_shadow_fallback_count": fallbacks,
        "auditor_adjustment_nonzero": auditor_nonzero,
        "json_valid_rate": round(json_valid / auditor_rows, 4) if auditor_rows else 0.0,
    }


def read_csv(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FUSE_GRID_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def merge_rows(existing: list[dict[str, Any]], incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
        return (
            str(row.get("dataset", "")),
            str(row.get("variant_key") or row.get("stage", "")),
            str(row.get("trial_id", "")),
            str(row.get("variant_name", "")),
            str(row.get("run_id", "")),
        )

    merged = {key(row): dict(row) for row in existing}
    for row in incoming:
        merged[key(row)] = dict(row)
    return sorted(merged.values(), key=lambda row: (str(row.get("dataset", "")), str(row.get("variant_key") or row.get("stage", "")), str(row.get("trial_id", "")), str(row.get("variant_name", ""))))


def apply_b0_deltas(rows: list[dict[str, Any]]) -> None:
    b0_by_dataset: dict[str, dict[str, Any]] = {}
    for row in rows:
        if str(row.get("dataset", "20260529")) != "20260529":
            continue
        if str(row.get("variant_key") or row.get("stage")) == "B0" and row.get("official_net") not in {"", None}:
            b0_by_dataset[str(row.get("dataset", "20260529"))] = row
    for row in rows:
        b0 = b0_by_dataset.get(str(row.get("dataset", "20260529")))
        if not b0 or row.get("official_net") in {"", None}:
            continue
        net_delta = round(_safe_float(row.get("official_net")) - _safe_float(b0.get("official_net")), 2)
        gross_delta = round(_safe_float(row.get("gross_minus_cost")) - _safe_float(b0.get("gross_minus_cost")), 2)
        penalty_delta = round(_safe_float(row.get("preference_penalty")) - _safe_float(b0.get("preference_penalty")), 2)
        row["official_net_delta_vs_b0"] = net_delta
        row["gross_delta_vs_b0"] = gross_delta
        row["preference_penalty_delta_vs_b0"] = penalty_delta
        row["net_delta_vs_b0"] = net_delta
        row["penalty_delta_vs_b0"] = penalty_delta
        if row.get("keep_or_kill") in {"", None, "kill_internal_failure"} and str(row.get("status")) == "EXECUTED":
            row["keep_or_kill"] = _keep_or_kill(row, b0)


def _keep_or_kill(row: dict[str, Any], b0: dict[str, Any]) -> str:
    invalid = sum(_safe_int(row.get(key)) for key in ("income_abort_count", "illegal_count", "rejected_take_count", "simulation_failures"))
    if invalid:
        return "kill_invalid_run"
    if str(row.get("variant_key") or row.get("stage")) == "B0":
        return "keep_b0_reference"
    net = _safe_float(row.get("official_net"))
    gross = _safe_float(row.get("gross_minus_cost"))
    penalty = _safe_float(row.get("preference_penalty"))
    if net > _safe_float(b0.get("official_net")) and gross >= 39000 and penalty < _safe_float(b0.get("preference_penalty")):
        return "keep_candidate"
    return "kill_below_b0_or_no_penalty_gain"


def run_spec(spec: FuseSpec, simulation_days: int, max_steps: int | None) -> dict[str, Any]:
    command = f"existing run summarized: {spec.run_dir}"
    exit_code: int | str = 0
    started = finished = ""
    duration: float | str = ""
    if not (spec.run_dir / "monthly_income_202603.json").is_file():
        exit_code, command, duration, started, finished = run_local_eval(
            dataset=spec.dataset,
            variant=spec.variant,
            run_dir=spec.run_dir,
            simulation_days=simulation_days,
            env_overrides=spec.env,
            max_steps=max_steps,
        )
    status = "EXECUTED" if (spec.run_dir / "monthly_income_202603.json").is_file() and int(exit_code or 0) == 0 else "FAILED_EXECUTED"
    row = summarize_trident_run(
        spec.run_dir,
        stage=spec.variant_key,
        variant_name=spec.variant_name,
        variant=spec.variant,
        dataset=spec.dataset,
        simulation_days=simulation_days,
        status=status,
        notes=spec.notes,
        params=spec.params,
        env_overrides=spec.env,
        command=command,
        exit_code=exit_code,
        started_at=started,
        finished_at=finished,
        duration_seconds=duration,
    )
    row.update(fuse_metrics(spec.run_dir))
    row["variant_key"] = spec.variant_key
    row["trial_id"] = spec.trial_id
    row["params_hash"] = params_hash(spec.params)
    row["run_dir"] = row.get("run_id", str(spec.run_dir))
    row["params_json"] = json_cell(spec.params)
    row["env_json"] = json_cell(spec.env)
    row["controller_score_changed"] = row.get("score_changed_by_controller_count", 0)
    row["graph_alpha"] = spec.params.get("graph_alpha", "")
    row["package_candidate"] = str(bool(spec.package_candidate)).lower()
    row["top5_0509_sanity"] = str(bool(spec.top5_0509_sanity)).lower()
    row["fallback_to_b0"] = str(bool(spec.fallback_to_b0)).lower()
    row["default_variant_verified"] = str(bool(spec.default_variant_verified)).lower()
    row["selected_reason"] = spec.selected_reason
    return row


def best_params_from_grid(path: Path) -> tuple[dict[str, Any], bool]:
    rows = read_csv(path)
    b0 = next((row for row in rows if str(row.get("variant_key") or row.get("stage")) == "B0" and str(row.get("dataset", "20260529")) == "20260529"), None)
    executed = [
        row
        for row in rows
        if str(row.get("status")) == "EXECUTED"
        and str(row.get("dataset", "20260529")) == "20260529"
        and str(row.get("variant_key")) == "TRIAL"
    ]
    if not executed:
        return {}, True
    best = max(executed, key=lambda row: _safe_float(row.get("official_net")))
    b0_net = _safe_float(b0.get("official_net")) if b0 else 10**9
    b0_penalty = _safe_float(b0.get("preference_penalty")) if b0 else 10**9
    eligible = [
        row
        for row in executed
        if str(row.get("keep_or_kill")) == "keep_candidate"
        or (
            _safe_float(row.get("official_net")) > b0_net
            and _safe_float(row.get("gross_minus_cost")) >= 39000.0
            and _safe_float(row.get("preference_penalty")) < b0_penalty
        )
    ]
    selected = max(eligible, key=lambda row: _safe_float(row.get("official_net"))) if eligible else best
    fallback = not eligible or _safe_float(selected.get("official_net")) <= b0_net
    try:
        params = json.loads(str(selected.get("params_json") or "{}"))
    except json.JSONDecodeError:
        params = {}
    return params if isinstance(params, dict) else {}, fallback


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["references", "search", "graph", "auditor", "final"], required=True)
    parser.add_argument("--trials", type=int, default=60)
    parser.add_argument("--dataset", choices=["20260529", "20260509"], default="20260529")
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--results-root", type=Path, default=RUNS / "fuse")
    parser.add_argument("--out", type=Path, default=REPORTS / "fuse_grid.csv")
    parser.add_argument("--max-steps", type=int, default=None)
    args = parser.parse_args()

    if args.mode == "references":
        specs = reference_specs(args.results_root)
    elif args.mode == "search":
        specs = search_specs(args.results_root / "search", args.trials, args.dataset)
    else:
        params, fallback = best_params_from_grid(args.out)
        if args.mode == "graph":
            specs = graph_specs(args.results_root / "graph", params, args.dataset)
        elif args.mode == "auditor":
            specs = auditor_specs(args.results_root / "auditor", params, args.dataset)
        else:
            specs = final_specs(args.results_root / "final", params, fallback_to_b0=fallback, dataset=args.dataset)

    rows: list[dict[str, Any]] = []
    for spec in specs:
        row = run_spec(spec, args.simulation_days, args.max_steps)
        rows.append(row)
        merged = merge_rows(read_csv(args.out), [row])
        apply_b0_deltas(merged)
        write_csv(args.out, merged)
    print({"mode": args.mode, "rows_written": len(rows), "rows_total": len(read_csv(args.out)), "out": str(args.out)})
    return 0 if all(str(row.get("status")) == "EXECUTED" for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
