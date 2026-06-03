"""Build CROWN-FUSE rule-family ledger from current B0 and B9c run outputs."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

LEDGER_FIELDS = [
    "rule_family",
    "b0_penalty",
    "b9c_penalty",
    "delta_penalty",
    "estimated_delta_gross_share",
    "repair_action_types",
    "repair_minutes",
    "repair_reposition_count",
    "candidate_keep_repair_for_family",
    "controller_family_scale",
    "primitive_family_scale",
    "counting_unit_scale",
    "deadline_curve",
    "repair_multiplier",
    "already_failed_discount",
    "cap_discount",
    "reason",
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def family(rule: dict[str, Any]) -> str:
    if "off_days" in rule:
        return "full_inactive_day_quota"
    if "order_days" in rule:
        return "required_attribute_distinct_days"
    if "waited_minutes" in rule:
        return "location_visit_or_dwell"
    if "satisfied" in rule:
        return "ordered_or_location_task"
    if "violations" in rule:
        violations = max(1.0, float(rule.get("violations", 1.0) or 1.0))
        per_violation = float(rule.get("penalty", 0.0) or 0.0) / violations
        if per_violation <= 200.0:
            return "distance_or_count_limit"
        return "forbidden_attribute_or_region"
    return "unknown_soft"


def penalty_rows(run_dir: Path) -> dict[str, float]:
    monthly = read_json(run_dir / "monthly_income_202603.json")
    out: dict[str, float] = {}
    drivers = monthly.get("drivers") if isinstance(monthly.get("drivers"), list) else []
    for driver in drivers:
        pref = driver.get("preference_check") if isinstance(driver, dict) else {}
        rules = pref.get("rules") if isinstance(pref, dict) else []
        if not isinstance(rules, list):
            continue
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            rule_family = family(rule)
            out[rule_family] = out.get(rule_family, 0.0) + float(rule.get("penalty", 0.0) or 0.0)
    return out


def action_stats(run_dir: Path) -> tuple[int, int]:
    wait_minutes = 0
    reposition_count = 0
    for path in sorted(run_dir.glob("actions_202603_*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            action = row.get("action") if isinstance(row.get("action"), dict) else {}
            params = action.get("params") if isinstance(action.get("params"), dict) else {}
            if action.get("action") == "wait":
                wait_minutes += int(float(params.get("duration_minutes", 0) or 0))
            elif action.get("action") == "reposition":
                reposition_count += 1
    return wait_minutes, reposition_count


def run_dir_from_grid(grid_path: Path, names: set[str]) -> Path | None:
    for row in read_csv(grid_path):
        identity = {str(row.get(key, "")) for key in ("variant_key", "stage", "variant_name", "variant")}
        if not identity & names:
            continue
        if str(row.get("status")) != "EXECUTED":
            continue
        run_dir = row.get("run_dir") or row.get("run_id")
        if not run_dir:
            continue
        path = Path(run_dir)
        if not path.is_absolute():
            path = ROOT / path
        if path.exists():
            return path
    return None


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--grid", type=Path, default=REPORTS / "fuse_grid.csv")
    parser.add_argument("--b0-run-dir", type=Path, default=None)
    parser.add_argument("--b9c-run-dir", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=REPORTS / "fuse_rule_ledger.csv")
    args = parser.parse_args()

    b0_dir = args.b0_run_dir or run_dir_from_grid(args.grid, {"B0", "B0_rescue", "best_rescue"})
    b9c_dir = args.b9c_run_dir or run_dir_from_grid(args.grid, {"B9c", "B9c_reference_current_branch"})
    if b0_dir is None or b9c_dir is None:
        print({"error": "missing B0 or B9c run_dir", "b0": str(b0_dir), "b9c": str(b9c_dir)})
        return 1

    b0 = penalty_rows(b0_dir)
    b9c = penalty_rows(b9c_dir)
    b0_wait, b0_reposition = action_stats(b0_dir)
    b9c_wait, b9c_reposition = action_stats(b9c_dir)
    b0_monthly = read_json(b0_dir / "monthly_income_202603.json")
    b9c_monthly = read_json(b9c_dir / "monthly_income_202603.json")
    b0_gross = sum(float((driver.get("income") or {}).get("gross_income", 0.0) or 0.0) - float((driver.get("income") or {}).get("cost", 0.0) or 0.0) for driver in b0_monthly.get("drivers", []) if isinstance(driver, dict))
    b9c_gross = sum(float((driver.get("income") or {}).get("gross_income", 0.0) or 0.0) - float((driver.get("income") or {}).get("cost", 0.0) or 0.0) for driver in b9c_monthly.get("drivers", []) if isinstance(driver, dict))
    gross_loss = max(0.0, b0_gross - b9c_gross)

    families = sorted(set(b0) | set(b9c))
    improvements = {
        rule_family: max(0.0, b0.get(rule_family, 0.0) - b9c.get(rule_family, 0.0))
        for rule_family in families
    }
    total_improvement = sum(improvements.values())
    rows: list[dict[str, Any]] = []
    for rule_family in families:
        b0_penalty = b0.get(rule_family, 0.0)
        b9c_penalty = b9c.get(rule_family, 0.0)
        delta = round(b9c_penalty - b0_penalty, 2)
        share = improvements[rule_family] / total_improvement if total_improvement > 0 else 0.0
        gross_share = round(gross_loss * share, 2)
        wait_share = int(round(max(0, b9c_wait - b0_wait) * share))
        reposition_share = int(round(max(0, b9c_reposition - b0_reposition) * share))
        keep = improvements[rule_family] > 0 and improvements[rule_family] >= gross_share * 0.8
        scale = 1.0 if keep else (0.25 if improvements[rule_family] > 0 else 0.0)
        rows.append(
            {
                "rule_family": rule_family,
                "b0_penalty": round(b0_penalty, 2),
                "b9c_penalty": round(b9c_penalty, 2),
                "delta_penalty": delta,
                "estimated_delta_gross_share": gross_share,
                "repair_action_types": "wait,reposition" if reposition_share else ("wait" if wait_share else "none"),
                "repair_minutes": wait_share,
                "repair_reposition_count": reposition_share,
                "candidate_keep_repair_for_family": "keep" if keep else "kill_or_soften",
                "controller_family_scale": scale,
                "primitive_family_scale": scale,
                "counting_unit_scale": scale,
                "deadline_curve": "preserve_b0" if not keep else "soft_repair_only",
                "repair_multiplier": 1.0 if keep else 0.0,
                "already_failed_discount": 0.5 if keep else 1.0,
                "cap_discount": 0.5 if keep else 1.0,
                "reason": "penalty_reduction_roi_positive" if keep else "insufficient_roi_or_no_current_reduction",
            }
        )
    write_csv(args.out, rows)
    print({"out": str(args.out), "rows": len(rows), "b0_run_dir": str(b0_dir), "b9c_run_dir": str(b9c_dir)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
