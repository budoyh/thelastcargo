"""Build the current Pivot-Redline final/report artifacts honestly."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import pivot_redline_common as common  # noqa: E402


def _remote_tracking() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
        cwd=str(common.ROOT),
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.stdout.strip() if proc.returncode == 0 else "not_set"


def main() -> int:
    common.ensure_dirs()
    if not common.EXPERIMENT_GRID.is_file():
        common.write_csv(common.EXPERIMENT_GRID, [], common.GRID_FIELDS)
    common.PACKAGE_AUDIT.write_text(
        "\n".join(
            [
                "# Pivot-Redline Package Audit",
                "",
                "package_audit_status: NOT_CREATED",
                "reason: score/evidence gates are not reached; prompt forbids submission/probe zip below experimental gate.",
                "package_path: none",
                "sha256: none",
                "default_variant: not_packaged",
                "",
            ]
        ),
        encoding="utf-8",
    )
    report = f"""DO_NOT_SUBMIT_WITH_INCOMPLETE_IMPLEMENTATION: independent pivot runtime path exists, but B0/no-op/full-run/search/model/Qwen evidence gates are not complete.

# CROWN-PIVOT-REDLINE v1 Status

- branch: {common.current_branch()}
- commit: {common.current_commit()}
- upstream: {_remote_tracking()}
- package: none
- first_broken_link: no executed B0/R1-R6 pivot no-op and no clean-money full-run evidence yet

## Score Accounting

No Pivot-Redline 31-day official-style rows have been executed in `reports/pivot_redline_experiment_grid.csv`. B0 reference gates remain the required comparison target: official_net 5067.69, gross_minus_cost 43207.69, preference_penalty 38140.0.

## B0 And No-Op

- B0 reproduction: missing for this branch/run set.
- R1-R6 true pivot no-op: missing.
- `tools/audit_pivot_runtime_path.py` static audit: PASS for `crown_pivot_redline_v1` and `crown_pivot_redline_money_clean`; pivot branch does not call `_decide_rescue`, `rescue_scorer.score_options`, or `rescue_scorer.choose` on its main path.

## Code Audit

`reports/pivot_redline_forensics.csv` records 14 Stage 0 source-audit rows. The read-only Anti-Shell Source Auditor failed prior Dragon evidence as a Rescue shell overlay and required an independent PivotRedlinePlanner path.

## Implemented Runtime Path

- `demo/agent/pivot_redline/` now contains an independent planner, B0 pure shadow, bucketed candidate generation, money scoring, preference debt accounting, action risk, terminal value, query optimization, online probe, month-end guard, macro stats, and depth-2/3 beam rollout code.
- `demo/agent/model_decision_service.py` routes pivot variants to `PivotRedlinePlanner.decide()` before the Rescue path.
- Deterministic tests in `tests/test_pivot_redline_core.py` cover candidate diversity, risk ranking, terminal value, beam expansion, B0 shadow side effects, end-to-end trace, and full-precision reposition output.

## Missing Evidence

- High-score archaeology exact/near reproduction is not complete.
- Clean money 40-row grid is not executed.
- Qwen compiler gym/cache freeze is not complete.
- Scorer probe semantic profile is not generated.
- Risk/Value/IQL-CQL-lite models have no training/validation/full-run ablation evidence.
- 120+ executed 20260529 rows and 20260509 sanity are missing.
- Required stage reviewers after Stage 0 are missing.

## User Idea Checklist

| idea | status | reason |
|---|---|---|
| clean money backbone | IMPLEMENTED_BUT_NOT_ACTIVE | runtime code and tests exist; no full-run gross evidence |
| Qwen ensemble compiler | IMPLEMENTED_BUT_NOT_ACTIVE | semantic boundary exists; no live gym/cache evidence |
| Preference Debt Accountant | IMPLEMENTED_BUT_NOT_ACTIVE | runtime debt scoring exists; no full-run/ablation |
| scorer probe | DIAGNOSTIC_ONLY | profile container exists; probes not executed |
| RiskModel(s,a) | IMPLEMENTED_BUT_NOT_ACTIVE | behavior test exists; no trained labels/full-run |
| ValueModel(s') | IMPLEMENTED_BUT_NOT_ACTIVE | terminal estimator test exists; no trained labels/full-run |
| IQL/CQL-lite conservative ranker | DIAGNOSTIC_ONLY | not trained |
| query budget optimizer | IMPLEMENTED_BUT_NOT_ACTIVE | runtime code exists; no query metrics full-run |
| unload terminal value | IMPLEMENTED_BUT_NOT_ACTIVE | runtime estimator exists; no ablation |
| legal online probe | IMPLEMENTED_BUT_NOT_ACTIVE | reposition probe candidates exist; no full-run |
| month-end horizon protection | IMPLEMENTED_BUT_NOT_ACTIVE | runtime component exists; no ablation |
| Macro Commitment | IMPLEMENTED_BUT_NOT_ACTIVE | runtime stats exist; no full-run stats |
| depth=2/3 beam rollout | IMPLEMENTED_BUT_NOT_ACTIVE | BeamNode test exists; no full-run |
| counterfactual regret analyzer | DIAGNOSTIC_ONLY | not implemented for real traces |
| Regret-LNS | DIAGNOSTIC_ONLY | not implemented for full-run candidates |
| ReEvo heuristic evolution | DIAGNOSTIC_ONLY | not executed |

## Shortest Next Path

1. Execute B0 and R1-R6 no-op rows with `variant=crown_pivot_redline_v1`.
2. Run archaeology and clean money grid; stop if best clean-money gross is below 52000.
3. Only after clean-money and Qwen artifacts are frozen, run model/beam/search stages.
"""
    common.FINAL_REPORT.write_text(report, encoding="utf-8")
    print({"final_report": str(common.FINAL_REPORT.relative_to(common.ROOT)), "package_audit": str(common.PACKAGE_AUDIT.relative_to(common.ROOT))})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
