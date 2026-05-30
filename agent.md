# Agent Operating Rules

This file mirrors `AGENTS.md` for tools that look for a lowercase agent rule file.

The durable project memory is in `docs/PROJECT_MEMORY.md`; experiment evidence is in `docs/EXPERIMENT_LOG.md`; final handoff evidence belongs in `reports/final_audit_report.md`.

Score rescue evidence belongs in the centralized score-rescue reports:
`reports/baseline_comparison.md`, `reports/score_forensic_audit.md`,
`reports/regret_dashboard_v2.md`, `reports/qwen_preference_compile_report.md`,
`reports/score_rescue_ablation.md`, `reports/module_switches_score_rescue.md`,
`reports/subagent_reviews_score_rescue.md` and
`reports/score_rescue_final_report.md`.

For rescue work, do not normalize wait-heavy negative-net behavior into success. The
agent must either meet the hard rescue gate or leave a forensic failure report with
the shortest next path.
