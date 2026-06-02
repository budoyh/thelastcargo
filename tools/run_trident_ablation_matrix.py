"""Run or summarize the Trident B0-B11 official ablation matrix."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parents[1]
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

from tools.trident_utils import (  # noqa: E402
    REPORTS,
    ROOT,
    RUNS,
    run_local_eval,
    summarize_trident_run,
    write_merged_experiments,
)


@dataclass(frozen=True)
class AblationSpec:
    stage: str
    variant_name: str
    variant: str
    env: dict[str, str] = field(default_factory=dict)
    notes: str = ""
    fallbacks: tuple[Path, ...] = ()


GOLD_BASE_ENV = {
    "CROWN_GOLD_ENABLE_FIREWALL": "1",
    "CROWN_GOLD_ENABLE_LINKER": "1",
    "CROWN_GOLD_ENABLE_AUDITOR": "1",
    "CROWN_GOLD_ENABLE_REPAIR": "0",
    "CROWN_GOLD_ENABLE_VISIBLE_GRAPH_MPC": "0",
}
TRIDENT_VARIANT = "crown_trident_gold2"


def _gold_env(**updates: str) -> dict[str, str]:
    env = dict(GOLD_BASE_ENV)
    env.update(updates)
    return env


def _trident_env(stage: str, **updates: str) -> dict[str, str]:
    env = _gold_env(CROWN_TRIDENT_STAGE=stage)
    env.update(updates)
    return env


def _best_param_env() -> dict[str, str]:
    path = RUNS / "trident_param_search" / "best_params.json"
    if not path.is_file():
        return dict(GOLD_BASE_ENV)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return dict(GOLD_BASE_ENV)
    env = data.get("env") if isinstance(data.get("env"), dict) else {}
    return {str(key): str(value) for key, value in env.items()}


def ablation_specs() -> list[AblationSpec]:
    best_env = _best_param_env()
    return [
        AblationSpec(
            stage="B0",
            variant_name="B0_historical_rescue_restored",
            variant="best_rescue",
            notes="Immutable rescue baseline.",
            fallbacks=(
                RUNS / "trident_b0_best_rescue_verify",
                RUNS / "gold" / "B0_best_rescue_restored_20260529",
                RUNS / "gold" / "B0_best_rescue_20260529",
                RUNS / "latest_rescue",
            ),
        ),
        AblationSpec(
            stage="B1",
            variant_name="B1_contract_compile_logging_only",
            variant=TRIDENT_VARIANT,
            env=_trident_env(
                "b1",
                CROWN_GOLD_ENABLE_FIREWALL="0",
                CROWN_GOLD_ENABLE_LINKER="0",
                CROWN_GOLD_ENABLE_AUDITOR="0",
                CROWN_GOLD_ENABLE_REPAIR="0",
                CROWN_GOLD_ENABLE_VISIBLE_GRAPH_MPC="0",
            ),
            notes="Existing Gold contract compile path; no linker, firewall, auditor, repair, or graph scoring.",
        ),
        AblationSpec(
            stage="B2",
            variant_name="B2_contract_monitor_no_score",
            variant=TRIDENT_VARIANT,
            env=_trident_env(
                "b2",
                CROWN_GOLD_ENABLE_FIREWALL="0",
                CROWN_GOLD_ENABLE_LINKER="0",
                CROWN_GOLD_ENABLE_AUDITOR="0",
                CROWN_GOLD_ENABLE_REPAIR="0",
                CROWN_GOLD_ENABLE_VISIBLE_GRAPH_MPC="0",
            ),
            notes="Monitor/no-score wrapper mapping; current runtime has no separate monitor-only env switch.",
        ),
        AblationSpec(
            stage="B3",
            variant_name="B3_controller_soft_scoring",
            variant=TRIDENT_VARIANT,
            env=_trident_env(
                "b3",
                CROWN_GOLD_ENABLE_FIREWALL="1",
                CROWN_GOLD_ENABLE_LINKER="0",
                CROWN_GOLD_ENABLE_AUDITOR="0",
                CROWN_GOLD_ENABLE_REPAIR="0",
                CROWN_GOLD_ENABLE_VISIBLE_GRAPH_MPC="0",
            ),
            notes="Controller scoring without Qwen linker/auditor/graph.",
        ),
        AblationSpec(
            stage="B4",
            variant_name="B4_verified_hard_firewall_only",
            variant=TRIDENT_VARIANT,
            env=_trident_env(
                "b4",
                CROWN_GOLD_ENABLE_FIREWALL="1",
                CROWN_GOLD_ENABLE_LINKER="1",
                CROWN_GOLD_ENABLE_AUDITOR="0",
                CROWN_GOLD_ENABLE_REPAIR="0",
                CROWN_GOLD_ENABLE_VISIBLE_GRAPH_MPC="0",
            ),
            notes="Existing ScorerSemanticsAdapter-gated firewall with linker; auditor/graph off.",
        ),
        AblationSpec(
            stage="B5",
            variant_name="B5_qwen_auditor_nonzero_adjustment",
            variant=TRIDENT_VARIANT,
            env=_trident_env(
                "b5",
                CROWN_GOLD_ENABLE_FIREWALL="1",
                CROWN_GOLD_ENABLE_LINKER="1",
                CROWN_GOLD_ENABLE_AUDITOR="1",
                CROWN_GOLD_ENABLE_REPAIR="0",
                CROWN_GOLD_ENABLE_VISIBLE_GRAPH_MPC="0",
            ),
            notes="Auditor enabled; runner records nonzero adjustment count separately from call count.",
        ),
        AblationSpec(
            stage="B6",
            variant_name="B6_observed_vocab_linker_only",
            variant=TRIDENT_VARIANT,
            env=_trident_env(
                "b6",
                CROWN_GOLD_ENABLE_FIREWALL="0",
                CROWN_GOLD_ENABLE_LINKER="1",
                CROWN_GOLD_ENABLE_AUDITOR="0",
                CROWN_GOLD_ENABLE_REPAIR="0",
                CROWN_GOLD_ENABLE_VISIBLE_GRAPH_MPC="0",
            ),
            notes="Observed vocab linker without scoring modules.",
        ),
        AblationSpec(
            stage="B7",
            variant_name="B7_opportunity_graph_only",
            variant=TRIDENT_VARIANT,
            env=_trident_env(
                "b7",
                CROWN_GOLD_ENABLE_FIREWALL="0",
                CROWN_GOLD_ENABLE_LINKER="0",
                CROWN_GOLD_ENABLE_AUDITOR="0",
                CROWN_GOLD_ENABLE_REPAIR="0",
                CROWN_GOLD_ENABLE_VISIBLE_GRAPH_MPC="1",
            ),
            notes="Runtime-only visible graph enabled, preference overlay disabled.",
        ),
        AblationSpec(
            stage="B8",
            variant_name="B8_opportunity_graph_plus_auditor",
            variant=TRIDENT_VARIANT,
            env=_trident_env(
                "b8",
                CROWN_GOLD_ENABLE_FIREWALL="1",
                CROWN_GOLD_ENABLE_LINKER="1",
                CROWN_GOLD_ENABLE_AUDITOR="1",
                CROWN_GOLD_ENABLE_REPAIR="0",
                CROWN_GOLD_ENABLE_VISIBLE_GRAPH_MPC="1",
            ),
            notes="Graph plus full Gold preference overlay.",
        ),
        AblationSpec(
            stage="B9",
            variant_name="B9_wait_repair_off",
            variant="crown_gold_contract_mpc",
            env=_gold_env(CROWN_GOLD_ENABLE_REPAIR="0", CROWN_GOLD_ENABLE_VISIBLE_GRAPH_MPC="0"),
            notes="Wait repair sweep: off.",
            fallbacks=(RUNS / "gold" / "B9_gold_current_20260529", RUNS / "gold" / "B9_gold_default_20260529"),
        ),
        AblationSpec(
            stage="B9",
            variant_name="B9_wait_repair_half",
            variant="crown_gold_contract_mpc",
            env=_gold_env(
                CROWN_GOLD_ENABLE_REPAIR="1",
                CROWN_GOLD_ENABLE_VISIBLE_GRAPH_MPC="0",
                CROWN_Y_FULL_REST_PERIOD_DAYS="20",
            ),
            notes="Wait repair sweep: reduced frequency through generic rest-period env.",
        ),
        AblationSpec(
            stage="B9",
            variant_name="B9_wait_repair_full",
            variant="crown_gold_contract_mpc",
            env=_gold_env(
                CROWN_GOLD_ENABLE_REPAIR="1",
                CROWN_GOLD_ENABLE_VISIBLE_GRAPH_MPC="0",
                CROWN_Y_FULL_REST_PERIOD_DAYS="10",
            ),
            notes="Wait repair sweep: full existing repair-state machinery.",
        ),
        AblationSpec(
            stage="B10",
            variant_name="B10_parameter_search_best",
            variant=TRIDENT_VARIANT,
            env=best_env,
            notes="Best generic parameter set from runs/trident_param_search/best_params.json, or Gold defaults if absent.",
        ),
        AblationSpec(
            stage="B11",
            variant_name="B11_final_selected",
            variant=TRIDENT_VARIANT,
            env=best_env,
            notes="Final selected wrapper row; final strategy selection must be justified by evidence outside this runner.",
        ),
    ]


def _run_dir(dataset: str, spec: AblationSpec) -> Path:
    return RUNS / "trident_ablation" / dataset / spec.variant_name


def _existing_dir(dataset: str, spec: AblationSpec) -> tuple[Path, str]:
    path = _run_dir(dataset, spec)
    if (path / "monthly_income_202603.json").is_file():
        return path, "EXISTING"
    if dataset == "20260529":
        for fallback in spec.fallbacks:
            if (fallback / "monthly_income_202603.json").is_file():
                return fallback, "EXISTING"
    return path, "MISSING_RUN"


def build_rows(
    *,
    datasets: list[str],
    stages: set[str] | None,
    execute: bool,
    simulation_days: int,
    max_steps: int | None,
) -> list[dict]:
    rows = []
    for dataset in datasets:
        for spec in ablation_specs():
            if stages and spec.stage not in stages and spec.variant_name not in stages:
                continue
            run_dir, status = _existing_dir(dataset, spec)
            command = ""
            exit_code: int | str = ""
            started = finished = ""
            duration: float | str = ""
            if status == "MISSING_RUN" and execute:
                exit_code, command, duration, started, finished = run_local_eval(
                    dataset=dataset,
                    variant=spec.variant,
                    run_dir=_run_dir(dataset, spec),
                    simulation_days=simulation_days,
                    env_overrides=spec.env,
                    max_steps=max_steps,
                )
                run_dir = _run_dir(dataset, spec)
                status = "OK" if exit_code == 0 else "INTERNAL_RUN_FAILURE"
            rows.append(
                summarize_trident_run(
                    run_dir,
                    stage=spec.stage,
                    variant_name=spec.variant_name,
                    variant=spec.variant,
                    dataset=dataset,
                    simulation_days=simulation_days,
                    status=status,
                    notes=spec.notes,
                    env_overrides=spec.env,
                    command=command,
                    exit_code=exit_code,
                    started_at=started,
                    finished_at=finished,
                    duration_seconds=duration,
                )
            )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--datasets", nargs="*", default=["20260529"], choices=["20260529", "20260509"])
    parser.add_argument("--stages", nargs="*", default=None, help="Stage ids such as B0 B1, or full variant names.")
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--out", type=Path, default=REPORTS / "trident_experiments.csv")
    args = parser.parse_args()
    rows = build_rows(
        datasets=args.datasets,
        stages=set(args.stages) if args.stages else None,
        execute=args.execute,
        simulation_days=args.simulation_days,
        max_steps=args.max_steps,
    )
    merged = write_merged_experiments(args.out, rows)
    print(
        {
            "rows_written": len(rows),
            "rows_total": len(merged),
            "out": str(args.out),
            "execute": args.execute,
            "datasets": args.datasets,
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
