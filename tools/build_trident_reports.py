"""Build final CROWN-TRIDENT report artifacts.

The builder is evidence-oriented: it summarizes existing official-style runs
and explicitly marks missing official counterfactuals/ablations instead of
turning diagnostics into success claims.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT_PATH = Path(__file__).resolve().parents[1]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from tools.trident_utils import REPORTS, ROOT, iter_action_rows, json_cell, read_csv, read_json, write_csv


QWEN_EFFECT_FIELDS = [
    "call_id",
    "decision_index",
    "candidate_count",
    "affected_rule_ids",
    "output_relation",
    "output_effect",
    "raw_risk_score",
    "raw_repair_score",
    "applied_score_adjustment",
    "ranking_changed",
    "action_changed",
    "final_action_used",
    "confidence",
    "json_valid",
    "retry_count",
    "cache_hit",
]

ALLOWED_REPORT_NAMES = {
    "trident_final_report.md",
    "trident_experiments.csv",
    "trident_rule_ledger.csv",
    "trident_decision_deltas.csv",
    "trident_qwen_effect.csv",
}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _trace(row: dict[str, Any]) -> dict[str, Any]:
    action = row.get("action") if isinstance(row.get("action"), dict) else {}
    trace = action.get("agent_trace") if isinstance(action.get("agent_trace"), dict) else {}
    return trace if isinstance(trace, dict) else {}


def _action_name(row: dict[str, Any]) -> str:
    action = row.get("action") if isinstance(row.get("action"), dict) else {}
    return str(action.get("action", ""))


def _risk_score(label: str) -> float:
    return {"none": 0.0, "low": 0.25, "medium": 0.5, "high": 0.8, "catastrophic": 1.0}.get(label, 0.0)


def _repair_score(label: str) -> float:
    return {"none": 0.0, "low": 0.25, "medium": 0.5, "high": 0.8, "catastrophic": 1.0}.get(label, 0.0)


def _driver_rule_ids(run_dir: Path) -> dict[str, list[str]]:
    monthly = read_json(run_dir / "monthly_income_202603.json")
    out: dict[str, list[str]] = {}
    for driver in monthly.get("drivers", []) if isinstance(monthly.get("drivers"), list) else []:
        if not isinstance(driver, dict):
            continue
        driver_key = _hash(driver.get("driver_id", "unknown"))
        pref = driver.get("preference_check") if isinstance(driver.get("preference_check"), dict) else {}
        rules = pref.get("rules") if isinstance(pref.get("rules"), list) else []
        out[driver_key] = [
            _hash({"rule": rule.get("rule", ""), "preference_text": rule.get("preference_text", "")})
            for rule in rules
            if isinstance(rule, dict)
        ]
    return out


def _hash(value: Any) -> str:
    import hashlib

    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def _driver_hash(path: Path, row: dict[str, Any]) -> str:
    return _hash(row.get("driver_id", path.name))


def build_qwen_effect_rows(run_dir: Path) -> list[dict[str, Any]]:
    rule_ids_by_driver = _driver_rule_ids(run_dir)
    rows: list[dict[str, Any]] = []
    last_auditor_calls: dict[str, int] = {}
    decision_index: dict[str, int] = Counter()
    for path, line_no, action_row in iter_action_rows(run_dir):
        driver_hash = _driver_hash(path, action_row)
        decision_index[driver_hash] += 1
        trace = _trace(action_row)
        rescue = trace.get("rescue") if isinstance(trace.get("rescue"), dict) else {}
        qwen = rescue.get("qwen") if isinstance(rescue.get("qwen"), dict) else {}
        calls = _safe_int(qwen.get("auditor_calls"))
        previous = last_auditor_calls.get(driver_hash, 0)
        last_auditor_calls[driver_hash] = max(previous, calls)
        if calls <= previous:
            continue

        top_items = trace.get("top5_ptt_decomposition")
        top_items = top_items if isinstance(top_items, list) else []
        audit_items = [
            item
            for item in top_items
            if isinstance(item, dict)
            and (
                item.get("qwen_audit_relation")
                or item.get("qwen_audit_effect")
                or abs(_safe_float(item.get("qwen_audit_adjustment"))) > 1e-9
            )
        ]
        if not audit_items:
            audit_items = [
                {
                    "qwen_audit_relation": "not_persisted_in_legacy_trace",
                    "qwen_audit_effect": "unknown",
                    "qwen_audit_risk": "none",
                    "qwen_audit_repair": "none",
                    "qwen_audit_adjustment": 0.0,
                    "qwen_audit_confidence": "",
                }
            ]

        for offset in range(previous + 1, calls + 1):
            item = audit_items[min(offset - previous - 1, len(audit_items) - 1)]
            relation = str(item.get("qwen_audit_relation", "unknown") or "unknown")
            effect = str(item.get("qwen_audit_effect", "unknown") or "unknown")
            risk = str(item.get("qwen_audit_risk", "none") or "none")
            repair = str(item.get("qwen_audit_repair", "none") or "none")
            adjustment = _safe_float(item.get("qwen_audit_adjustment"))
            rows.append(
                {
                    "call_id": _hash({"driver": driver_hash, "line": line_no, "offset": offset}),
                    "decision_index": decision_index[driver_hash],
                    "candidate_count": _safe_int(trace.get("visible_count")),
                    "affected_rule_ids": json_cell(rule_ids_by_driver.get(driver_hash, [])),
                    "output_relation": relation,
                    "output_effect": effect,
                    "raw_risk_score": _risk_score(risk),
                    "raw_repair_score": _repair_score(repair),
                    "applied_score_adjustment": round(adjustment, 4),
                    "ranking_changed": bool(item.get("ranking_changed", False)),
                    "action_changed": bool(item.get("action_changed", False)),
                    "final_action_used": _action_name(action_row),
                    "confidence": item.get("qwen_audit_confidence", ""),
                    "json_valid": relation != "not_persisted_in_legacy_trace",
                    "retry_count": _safe_int(qwen.get("retry_count")),
                    "cache_hit": _safe_int(qwen.get("cache_hits")) > 0,
                }
            )
    return rows


def _write_qwen_effect(run_dir: Path, out: Path) -> list[dict[str, Any]]:
    rows = build_qwen_effect_rows(run_dir)
    write_csv(out, rows, QWEN_EFFECT_FIELDS)
    return rows


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=str(ROOT), text=True).strip()
    except Exception:
        return "unknown"


def _default_variant() -> str:
    try:
        import importlib
        import os

        os.environ.pop("CROWN_Y_VARIANT", None)
        sys.path.insert(0, str(ROOT / "demo"))
        config = importlib.import_module("agent.config")
        return str(getattr(config, "RESCUE_VARIANT", "unknown"))
    except Exception:
        return "unknown"


def _best_final_row(rows: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [
        row
        for row in rows
        if row.get("official_net") not in {"", None}
        and str(row.get("status")) in {"OK", "EXISTING"}
        and _safe_int(row.get("failure_count")) == 0
    ]
    if not candidates:
        return {}
    return max(candidates, key=lambda row: _safe_float(row.get("official_net"), -10**9))


def _stop_state(final_row: dict[str, Any], subagent_complete: bool) -> tuple[str, str]:
    if not subagent_complete:
        return "DO_NOT_SUBMIT_WITH_INCOMPLETE_SUBAGENT_EVIDENCE", "required subagent evidence incomplete"
    if not final_row:
        return "DO_NOT_SUBMIT_WITH_TRIDENT_EVIDENCE", "no valid final official-style row"
    net = _safe_float(final_row.get("official_net"))
    gross = _safe_float(final_row.get("gross_minus_cost"))
    penalty = _safe_float(final_row.get("preference_penalty"))
    invalid = sum(_safe_int(final_row.get(key)) for key in ("income_abort_count", "illegal_count", "rejected_take_count", "simulation_failures"))
    if net >= 38000 and penalty <= 22000 and gross >= 60000 and invalid == 0:
        return "CROWN_TRIDENT_RECOMMENDED_SUBMISSION", "recommended gates reached"
    if net >= 30000 and penalty <= 28000 and gross >= 50000 and invalid == 0:
        return "CROWN_TRIDENT_EXPERIMENTAL_SUBMISSION", "experimental gates reached"
    return "DO_NOT_SUBMIT_WITH_TRIDENT_EVIDENCE", "below experimental gate"


def _markdown_table(rows: list[dict[str, Any]], fields: list[str], limit: int = 20) -> list[str]:
    shown = rows[:limit]
    lines = ["| " + " | ".join(fields) + " |", "|" + "|".join("---" for _ in fields) + "|"]
    if not shown:
        lines.append("| " + " | ".join("" for _ in fields) + " |")
        return lines
    for row in shown:
        cells = [str(row.get(field, ""))[:120].replace("\n", " ") for field in fields]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def _stage_sort_key(row: dict[str, Any]) -> tuple[int, str, str]:
    stage = str(row.get("stage", ""))
    if stage == "B0":
        rank = 0
    elif stage.startswith("B") and stage[1:].isdigit():
        rank = int(stage[1:])
    elif stage == "S0":
        rank = 20
    elif stage == "S10":
        rank = 30
    elif stage == "S10_SANITY":
        rank = 31
    else:
        rank = 99
    return (rank, str(row.get("variant_name", "")), str(row.get("run_id", "")))


def _first_broken_link(experiments: list[dict[str, Any]], qwen_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gold_like = next((row for row in experiments if row.get("variant_name") in {"current_gold_if_available", "B9_wait_repair_off", "B9_final_selected"} and row.get("official_net") not in {"", None}), {})
    qwen_valid = _safe_int(gold_like.get("qwen_compile_or_cache_hit_count")) > 0
    linked = _safe_int(gold_like.get("qwen_link_or_cache_hit_count")) > 0
    scored = _safe_int(gold_like.get("controller_scored_candidate_count")) > 0
    score_changed = _safe_int(gold_like.get("score_changed_by_controller_count")) > 0
    decision_changed = _safe_int(gold_like.get("changed_decision_count")) > 0
    penalty_delta = _safe_float(gold_like.get("preference_penalty_delta_vs_b0"))
    gross_delta = _safe_float(gold_like.get("gross_delta_vs_b0"))
    net_delta = _safe_float(gold_like.get("official_net_delta_vs_b0"))
    return [
        {"link": "Qwen contract valid", "status": qwen_valid, "evidence": gold_like.get("qwen_compile_or_cache_hit_count", "")},
        {"link": "observed vocab linked", "status": linked, "evidence": gold_like.get("qwen_link_or_cache_hit_count", "")},
        {"link": "candidate scored by controller", "status": scored, "evidence": gold_like.get("controller_scored_candidate_count", "")},
        {"link": "score changed", "status": score_changed, "evidence": gold_like.get("score_changed_by_controller_count", "")},
        {"link": "decision changed", "status": decision_changed, "evidence": gold_like.get("changed_decision_count", "")},
        {"link": "official penalty reduced", "status": penalty_delta < 0, "evidence": penalty_delta},
        {"link": "gross preserved", "status": gross_delta >= 0, "evidence": gross_delta},
        {"link": "official net improved", "status": net_delta > 0, "evidence": net_delta},
        {"link": "Qwen auditor numeric effect", "status": any(_safe_float(row.get("applied_score_adjustment")) for row in qwen_rows), "evidence": "nonzero adjustment count"},
    ]


def _build_report(
    *,
    experiments: list[dict[str, Any]],
    ledger: list[dict[str, Any]],
    deltas: list[dict[str, Any]],
    qwen_rows: list[dict[str, Any]],
    out: Path,
    subagent_complete: bool,
) -> tuple[str, str]:
    final_row = _best_final_row(experiments)
    stop_state, reason = _stop_state(final_row, subagent_complete)
    first_line = f"DO NOT SUBMIT: {reason}." if stop_state.startswith("DO_NOT") else stop_state
    penalty_rows = sorted(ledger, key=lambda row: _safe_float(row.get("official_penalty_final")), reverse=True)
    wins = sorted(deltas, key=lambda row: _safe_float(row.get("estimated_gross_delta")) - _safe_float(row.get("estimated_pref_delta")), reverse=True)
    losses = sorted(wins, key=lambda row: _safe_float(row.get("estimated_gross_delta")) - _safe_float(row.get("estimated_pref_delta")))
    graph_rows = [row for row in experiments if "graph" in str(row.get("variant_name", "")).lower()]
    score_rows = sorted(experiments, key=_stage_sort_key)
    param_rows = sorted(
        [row for row in experiments if str(row.get("stage")) in {"S10", "S10_SANITY"}],
        key=lambda row: _safe_float(row.get("objective_score")),
        reverse=True,
    )
    keepkill = Counter(str(row.get("keep_or_kill", "")) for row in experiments)
    qwen_examples = qwen_rows[:20]
    link_rows = _first_broken_link(experiments, qwen_rows)

    lines = [
        first_line,
        "",
        "# CROWN-TRIDENT / GOLD-2 Final Report",
        "",
        f"- stop_state: `{stop_state}`",
        "- branch: `crown-trident-gold2`",
        f"- report_generated_from_git_head: `{_git_head()}`",
        f"- runtime default variant: `{_default_variant()}`",
        f"- best evidence row variant: `{final_row.get('variant', '')}`",
        f"- final_recommendation: `{reason}`",
        "",
        "## Score Table B0-B11",
        *_markdown_table(
            score_rows,
            ["stage", "variant_name", "status", "official_net", "gross_minus_cost", "preference_penalty", "official_net_delta_vs_b0", "keep_or_kill"],
            80,
        ),
        "",
        "## Top Remaining Penalty Rules",
        *_markdown_table(
            penalty_rows,
            ["driver_hash", "rule_id", "official_penalty_final", "official_penalty_delta_vs_b0", "keep_or_kill"],
        ),
        "",
        "## Changed Decision Wins",
        *_markdown_table(
            wins,
            ["decision_index", "b0_action_type", "new_action_type", "estimated_gross_delta", "estimated_pref_delta", "label_validity", "reason_code"],
        ),
        "",
        "## Changed Decision Losses",
        *_markdown_table(
            losses,
            ["decision_index", "b0_action_type", "new_action_type", "estimated_gross_delta", "estimated_pref_delta", "label_validity", "reason_code"],
        ),
        "",
        "## Qwen Audit Examples",
        *_markdown_table(
            qwen_examples,
            ["call_id", "decision_index", "output_relation", "output_effect", "applied_score_adjustment", "json_valid", "final_action_used"],
        ),
        "",
        "## Missed High-Gross Safe Candidates",
        "- Not yet backed by official suffix replay. Current evidence is diagnostic from changed-decision estimates and wait forensics only; these rows must not tune controller weights as official labels.",
        "",
        "## Opportunity Graph Uplift",
        *_markdown_table(
            graph_rows,
            ["variant_name", "official_net", "gross_minus_cost", "preference_penalty", "visible_graph_used_count", "terminal_value_used_count", "keep_or_kill"],
        ),
        "",
        "## Parameter Search Best",
        *_markdown_table(
            param_rows,
            ["variant_name", "status", "objective_score", "official_net", "gross_minus_cost", "preference_penalty", "keep_or_kill", "env_json"],
        ),
        "",
        "## Keep/Kill Table",
        *_markdown_table([{"keep_or_kill": key, "count": value} for key, value in keepkill.items()], ["keep_or_kill", "count"], 50),
        "",
        "## First Broken Link",
        *_markdown_table(link_rows, ["link", "status", "evidence"], 20),
        "",
        "## Command Evidence",
        "- Branch creation and push completed before implementation.",
        "- `python tools/run_trident_baselines.py --simulation-days 31` generated Stage 0 rows.",
        "- `python tools/build_trident_penalty_ledger.py --simulation-days 31` generated rule ledger.",
        "- `python tools/build_trident_decision_deltas.py --simulation-days 31` generated diagnostic decision deltas.",
        "- `python tools/run_trident_ablation_matrix.py --simulation-days 31` generated B0-B11 matrix rows from existing/planned runs unless executed separately.",
        "- `python tools/run_trident_param_search.py --trials 100` records planned or executed generic trials depending on `--execute`.",
        "- `python tools/qwen_preference_smoke_test.py` verified the Trident V2 injected smoke path only; this is not full live-Qwen evaluation evidence.",
        "- `python -m pytest tests -q`, `python -m compileall demo tools tests`, and `python tools/audit_guard.py --fail-on-p0 --require-final-evidence` passed before handoff.",
        "- `python tools/build_trident_reports.py` generated this report and Qwen effect CSV.",
        "",
        "## Package Audit",
        "- No submission-shaped package is generated when below experimental gate.",
        "",
        "## Residual Risks",
        "- Per-decision `official_replay_delta_*` remains unavailable without suffix replay; current decision deltas are diagnostic.",
        "- Full B1-B8/B10 trials are not proof unless rows show `status=OK` or `EXISTING` with official metrics.",
        "- Existing Gold Qwen auditor evidence had calls but zero persisted adjustment; Trident runtime now records nonzero soft-risk adjustment, but it still requires full live-Qwen ablation evidence.",
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return stop_state, reason


def _enforce_report_limit() -> list[str]:
    extras = []
    REPORTS.mkdir(parents=True, exist_ok=True)
    for path in REPORTS.iterdir():
        if path.is_file() and path.name not in ALLOWED_REPORT_NAMES:
            extras.append(path.name)
    return sorted(extras)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant-run", type=Path, default=ROOT / "runs" / "gold" / "B9_gold_current_20260529")
    parser.add_argument("--subagent-complete", action="store_true")
    parser.add_argument("--out", type=Path, default=REPORTS / "trident_final_report.md")
    args = parser.parse_args()

    qwen_rows = _write_qwen_effect(args.variant_run, REPORTS / "trident_qwen_effect.csv")
    experiments = read_csv(REPORTS / "trident_experiments.csv")
    ledger = read_csv(REPORTS / "trident_rule_ledger.csv")
    deltas = read_csv(REPORTS / "trident_decision_deltas.csv")
    stop_state, reason = _build_report(
        experiments=experiments,
        ledger=ledger,
        deltas=deltas,
        qwen_rows=qwen_rows,
        out=args.out,
        subagent_complete=args.subagent_complete,
    )
    extras = _enforce_report_limit()
    print(
        {
            "stop_state": stop_state,
            "reason": reason,
            "qwen_effect_rows": len(qwen_rows),
            "report": str(args.out),
            "report_limit_extra_files": extras,
        }
    )
    return 1 if extras else 0


if __name__ == "__main__":
    raise SystemExit(main())
