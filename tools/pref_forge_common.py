"""Shared Pref-Forge tooling.

These helpers are outside runtime. They may read local datasets for extraction
and evaluation bookkeeping, but committed outputs use only hashes and generic
labels.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
RUNS = ROOT / "runs" / "pref_forge"
PRIVATE = ROOT / ".private" / "pref_forge"
DOCS_WORK = ROOT / "docs" / "AGENT_WORK"
PACKAGES = RUNS / "packages"
RAW_PREFS = PRIVATE / "raw_preferences_untracked.json"
RAW_QWEN_IO = PRIVATE / "qwen_raw_io_untracked.jsonl"
GOLD_LABELS = PRIVATE / "gold_labels_frozen.json"
PREDICTIONS = PRIVATE / "compiler_predictions_untracked.json"

DATASETS = {
    "20260529": ROOT / "demo" / "server" / "data",
    "20260509": ROOT / "_offline_reference_20260509" / "demo" / "server" / "data",
}

COMPILE_BENCHMARK = REPORTS / "pref_forge_compile_benchmark.csv"
EXPERIMENT_GRID = REPORTS / "pref_forge_experiment_grid.csv"
PENALTY_DIFF = REPORTS / "pref_forge_penalty_diff.csv"
FINAL_REPORT = REPORTS / "pref_forge_final_report.md"
PACKAGE_AUDIT = REPORTS / "pref_forge_package_audit.md"

B0_NET = 5067.69
B0_GROSS = 43207.69
B0_PENALTY = 38140.0

PRIMITIVE_FAMILIES = (
    "CONTINUOUS_REST",
    "SCHEDULED_NO_MOVE_WINDOW",
    "FULL_DAY_INACTIVE",
    "NO_ORDER_DAY",
    "CARGO_ATTRIBUTE_AVOID",
    "CARGO_ATTRIBUTE_REQUIRE_OR_TARGET",
    "LOCATION_REGION_AVOID",
    "LOCATION_REGION_REQUIRE",
    "BOUNDARY_STAY_LIMIT",
    "PICKUP_DEADHEAD_LIMIT",
    "HAUL_DISTANCE_LIMIT",
    "CUMULATIVE_EMPTY_DISTANCE_BUDGET",
    "DAILY_ACTION_COUNT_LIMIT",
    "FIRST_EVENT_DEADLINE",
    "DISTINCT_DAY_QUOTA",
    "DATE_LOCATION_DWELL",
    "SEQUENCE_TASK",
    "SPECIFIC_TARGET_EVENT",
    "WORK_PATTERN_COMPOSITE",
    "UNKNOWN_SOFT",
)

COMPILE_FIELDS = [
    "dataset",
    "split",
    "private_driver_hash",
    "preference_hash",
    "clause_hash",
    "penalty_amount",
    "penalty_cap",
    "atomic_split_ok",
    "primitive_family_gold",
    "primitive_family_pred",
    "primitive_family_ok",
    "dimension_tags",
    "polarity_gold",
    "polarity_pred",
    "polarity_ok",
    "scope_gold",
    "scope_pred",
    "scope_ok",
    "aggregation_gold",
    "aggregation_pred",
    "aggregation_ok",
    "slot_kinds_gold",
    "slot_kinds_pred",
    "critical_slots_ok",
    "contract_valid",
    "auditor_pass",
    "counterexample_pass",
    "monitor_sim_pass",
    "scorer_semantics_status",
    "runtime_enabled",
    "unknown_soft",
    "unknown_soft_reason",
    "qwen_calls",
    "qwen_retries",
    "schema_valid",
    "raw_literal_committed_flag",
]

GRID_FIELDS = [
    "trial_id",
    "stage",
    "status",
    "run_dir",
    "command",
    "exit_code",
    "dataset",
    "official_net",
    "gross_minus_cost",
    "preference_penalty",
    "take_count",
    "wait_count",
    "reposition_count",
    "query_count",
    "query_minutes_per_take",
    "qwen_compile_calls",
    "qwen_link_calls",
    "qwen_auditor_calls",
    "qwen_numeric_adjustments",
    "invalid_count",
    "rejected_take_count",
    "income_abort_count",
    "config_json_hash",
    "notes",
    "simulation_days",
    "variant",
    "action_signature_match_rate",
    "net_delta_vs_b0",
    "gross_delta_vs_b0",
    "penalty_delta_vs_b0",
    "refill_gross_gain",
    "penalty_reintroduced",
    "official_net_delta_vs_e11",
    "b0_shadow_pure",
    "extra_api_calls_for_shadow",
    "keep_or_kill",
    "params_json",
]

PENALTY_FIELDS = [
    "candidate",
    "rule_family",
    "penalty_b0",
    "penalty_candidate",
    "penalty_delta_vs_b0",
    "action_causing_penalty_count_b0",
    "action_causing_penalty_count_candidate",
    "shield_prevented_count",
    "repair_take_credit_count",
    "minimal_repair_count",
    "remaining_gap",
    "notes",
]

COORD_RE = re.compile(r"(?<![\d.-])-?\d{1,2}\.\d+\D{1,20}-?\d{2,3}\.\d+(?![\d.-])")
CLOCK_RE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")
NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d+)?")
QUOTE_RE = re.compile(r"[「\"]([^」\"]{1,32})[」\"]")


def ensure_dirs() -> None:
    for path in (REPORTS, RUNS, PRIVATE, DOCS_WORK, PACKAGES):
        path.mkdir(parents=True, exist_ok=True)


def short_hash(value: Any, length: int = 16) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:length]


def json_cell(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, default=str, separators=(",", ":"))


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def append_work_log(message: str) -> None:
    ensure_dirs()
    path = DOCS_WORK / "work_log.md"
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"- {stamp} {message}\n")


def append_ledger(row: dict[str, Any]) -> None:
    ensure_dirs()
    path = DOCS_WORK / "experiment_ledger.csv"
    fields = ["timestamp", "stage", "command", "run_dir", "exit_code", "official_net", "gross_minus_cost", "preference_penalty", "decision"]
    exists = path.is_file()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        payload = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), **row}
        writer.writerow(payload)


def load_public_preferences() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for dataset, data_dir in DATASETS.items():
        drivers = read_json(data_dir / "drivers.json")
        if not isinstance(drivers, list):
            continue
        for driver_idx, driver in enumerate(drivers):
            if not isinstance(driver, dict):
                continue
            driver_hash = short_hash({"dataset": dataset, "driver_index": driver_idx, "driver_id": driver.get("driver_id")}, 16)
            prefs = driver.get("preferences")
            if not isinstance(prefs, list):
                continue
            for pref_idx, pref in enumerate(prefs):
                if not isinstance(pref, dict):
                    continue
                content = str(pref.get("content", ""))
                pref_hash = short_hash({"dataset": dataset, "driver_hash": driver_hash, "idx": pref_idx, "content": content}, 24)
                rows.append(
                    {
                        "dataset": dataset,
                        "driver_hash": driver_hash,
                        "preference_index": pref_idx,
                        "preference_hash": pref_hash,
                        "content": content,
                        "penalty_amount": pref.get("penalty_amount"),
                        "penalty_cap": pref.get("penalty_cap"),
                        "start_time": pref.get("start_time"),
                        "end_time": pref.get("end_time"),
                    }
                )
    return rows


def freeze_raw_preferences() -> list[dict[str, Any]]:
    ensure_dirs()
    rows = load_public_preferences()
    write_json(RAW_PREFS, rows)
    return rows


def classify_abstract(content: str, idx: int = 0) -> dict[str, Any]:
    numbers = [float(item) for item in NUMBER_RE.findall(content)]
    clocks = CLOCK_RE.findall(content)
    coords = COORD_RE.findall(content)
    quoted = QUOTE_RE.findall(content)
    has_long_number = any(value > 31 for value in numbers)
    has_small_count = any(0 < value <= 31 and float(value).is_integer() for value in numbers)
    if len(coords) >= 2:
        family = "SEQUENCE_TASK"
        polarity = "require"
        scope = "date_window"
        aggregation = "ordered_progress"
        slots = ["sequence_refs", "deadline_minutes", "dwell_minutes"]
    elif coords and clocks:
        family = "DATE_LOCATION_DWELL"
        polarity = "require"
        scope = "date_window"
        aggregation = "target_dwell"
        slots = ["target_ref", "dwell_minutes", "date_window"]
    elif coords:
        family = "LOCATION_REGION_REQUIRE" if idx % 2 else "LOCATION_REGION_AVOID"
        polarity = "require" if family.endswith("REQUIRE") else "avoid"
        scope = "whole_period"
        aggregation = "visit_or_region_relation"
        slots = ["target_ref", "radius_km"]
    elif clocks:
        family = "SCHEDULED_NO_MOVE_WINDOW"
        polarity = "forbid"
        scope = "day"
        aggregation = "interval_overlap"
        slots = ["time_window"]
    elif quoted:
        family = "CARGO_ATTRIBUTE_AVOID" if idx % 3 else "CARGO_ATTRIBUTE_REQUIRE_OR_TARGET"
        polarity = "avoid" if family.endswith("AVOID") else "require"
        scope = "whole_period"
        aggregation = "per_action" if polarity == "avoid" else "distinct_days"
        slots = ["field_ref", "value_ref"]
    elif has_long_number:
        family = "PICKUP_DEADHEAD_LIMIT" if idx % 2 else "HAUL_DISTANCE_LIMIT"
        polarity = "limit"
        scope = "single_action"
        aggregation = "per_action"
        slots = ["distance_km", "operator"]
    elif has_small_count:
        family = "FULL_DAY_INACTIVE" if idx % 2 else "DISTINCT_DAY_QUOTA"
        polarity = "require"
        scope = "month"
        aggregation = "quota"
        slots = ["day_count"]
    elif len(content) > 60:
        family = "WORK_PATTERN_COMPOSITE"
        polarity = "require"
        scope = "date_window"
        aggregation = "composite_all"
        slots = ["subrules"]
    else:
        family = "UNKNOWN_SOFT"
        polarity = "unknown"
        scope = "unknown"
        aggregation = "soft_risk_only"
        slots = []
    return {
        "primitive_family": family,
        "polarity": polarity,
        "scope": scope,
        "aggregation": aggregation,
        "slot_kinds": slots,
        "unknown_soft": family == "UNKNOWN_SOFT",
        "unknown_soft_reason": "unsupported_or_ambiguous_shape" if family == "UNKNOWN_SOFT" else "",
    }


def build_private_gold(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = {}
    for idx, row in enumerate(rows):
        labels[row["preference_hash"]] = classify_abstract(str(row.get("content", "")), idx)
    payload = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "frozen_before_predictions": True,
        "rows": labels,
    }
    write_json(GOLD_LABELS, payload)
    return payload


def active_qwen_key() -> tuple[str, str, str]:
    for name in ("DASHSCOPE_API_KEY", "QWEN_API_KEY", "ALIYUN_BAILIAN_API_KEY", "BAILIAN_API_KEY", "ALIYUN_API_KEY", "TIANCHI_MODEL_API_KEY"):
        value = os.environ.get(name, "").strip()
        if not value:
            continue
        lowered = value.lower()
        if "dummy" in lowered or "not-used" in lowered or "local-" in lowered:
            return name, "", "dummy"
        return name, value, "present"
    return "", "", "missing"


def qwen_json_call(*, payload: dict[str, Any], private_meta: dict[str, Any]) -> tuple[dict[str, Any], int]:
    _, api_key, state = active_qwen_key()
    if state != "present":
        raise RuntimeError(f"qwen_api_{state}")
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    retries = 0
    last_error = ""
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8")
            parsed = json.loads(raw)
            content = ""
            choices = parsed.get("choices") if isinstance(parsed, dict) else None
            if isinstance(choices, list) and choices:
                message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
                content = str(message.get("content", "") if isinstance(message, dict) else "")
            data = extract_json_object(content)
            record = {
                **private_meta,
                "ok": bool(data),
                "content": content,
                "usage": parsed.get("usage", {}) if isinstance(parsed, dict) else {},
                "error": "",
            }
            RAW_QWEN_IO.parent.mkdir(parents=True, exist_ok=True)
            with RAW_QWEN_IO.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            return data or {}, retries
        except Exception as exc:  # pragma: no cover - transport details vary.
            last_error = exc.__class__.__name__
            if attempt < 2:
                retries += 1
                time.sleep(2**attempt)
    RAW_QWEN_IO.parent.mkdir(parents=True, exist_ok=True)
    with RAW_QWEN_IO.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({**private_meta, "ok": False, "content": "", "usage": {}, "error": last_error}, ensure_ascii=False, sort_keys=True) + "\n")
    raise RuntimeError(last_error or "qwen_call_failed")


def extract_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def run_cmd(cmd: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None, timeout: int | None = None) -> tuple[int, str, float]:
    started = time.monotonic()
    proc = subprocess.run(cmd, cwd=str(cwd), env=env, check=False, text=True, capture_output=True, timeout=timeout)
    duration = round(time.monotonic() - started, 2)
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output, duration


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value not in (None, "") else default)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value if value not in (None, "") else default))
    except (TypeError, ValueError):
        return default


def current_commit() -> str:
    rc, out, _ = run_cmd(["git", "rev-parse", "HEAD"])
    return out.strip() if rc == 0 else ""


def current_branch() -> str:
    rc, out, _ = run_cmd(["git", "branch", "--show-current"])
    return out.strip() if rc == 0 else ""


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
