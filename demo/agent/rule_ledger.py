"""Incremental preference and action ledger."""

from __future__ import annotations

from .schemas import CompiledPreferenceSet, DriverStatus, RuleLedger, World


def update_or_rebuild(
    status: DriverStatus,
    rules: CompiledPreferenceSet,
    prev_world: World | None,
    observed_summary_count: int,
) -> RuleLedger:
    if prev_world is not None and prev_world.pref_hash == rules.pref_hash:
        revision = prev_world.ledger.revision + 1
        action_counts = dict(prev_world.ledger.action_counts)
    else:
        revision = 1
        action_counts = {"take_order": 0, "wait": 0, "reposition": 0}
    preference_pressure = min(1.0, 0.08 * len(rules.rules) + 0.01 * max(0, status.completed_order_count))
    return RuleLedger(
        revision=revision,
        status_minutes=status.simulation_progress_minutes,
        completed_orders=status.completed_order_count,
        action_counts=action_counts,
        observed_summary_count=observed_summary_count,
        preference_pressure=preference_pressure,
    )

