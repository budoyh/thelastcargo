from __future__ import annotations

import csv
from pathlib import Path

from tools import dragon_orca_common as common


def test_dragon_report_file_policy_is_exact() -> None:
    assert common.REPORT_FILES == {
        "dragon_orca_final_report.md",
        "dragon_orca_experiment_grid.csv",
        "dragon_orca_regret_attribution.csv",
        "dragon_orca_value_model_audit.csv",
        "dragon_orca_package_audit.md",
    }


def test_dragon_grid_fields_include_required_runtime_evidence() -> None:
    required = {
        "trial_id",
        "status",
        "run_dir",
        "command",
        "exit_code",
        "official_net",
        "gross_minus_cost",
        "preference_penalty",
        "value_model_used_count",
        "beam_used_count",
        "adaptive_query_used_count",
        "month_end_protection_count",
        "regret_lns_used_count",
        "qwen_numeric_adjustments",
    }
    assert required.issubset(set(common.GRID_FIELDS))


def test_verifier_source_rejects_qwen_numeric_adjustments() -> None:
    verifier = Path("tools/verify_dragon_orca_completion.py").read_text(encoding="utf-8")
    assert "Qwen numeric auditor adjustment is nonzero" in verifier
    assert "schema failure exists but strategy search evidence has not continued" in verifier


def test_regret_fields_are_non_raw_identifier_shape() -> None:
    assert "account_id" in common.REGRET_FIELDS
    assert "driver_id" not in common.REGRET_FIELDS
    assert "cargo_id" not in common.REGRET_FIELDS
