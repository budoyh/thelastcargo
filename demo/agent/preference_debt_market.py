"""Price soft preference debt without hard-blocking low confidence rules."""

from __future__ import annotations

from .schemas import CompiledPreferenceSet, DriverStatus, PreferenceDebtMarket, RuleLedger
from .time_utils import remaining_minutes


def price(
    status: DriverStatus,
    ledger: RuleLedger,
    rules: CompiledPreferenceSet,
    horizon_minutes: int,
) -> PreferenceDebtMarket:
    if not rules.rules:
        return PreferenceDebtMarket(0.0, 0.0, False, 0.0, 0.0)
    remaining = remaining_minutes(status.simulation_progress_minutes, horizon_minutes)
    rule_mass = float(len(rules.rules))
    amount_mass = 0.0
    confidence_mass = 0.0
    for rule in rules.rules:
        amount_mass += max(0.0, float(rule.reward_or_penalty.get("amount", 0.0) or 0.0))
        confidence_mass += max(0.0, min(1.0, rule.confidence))
    avg_confidence = confidence_mass / max(1.0, rule_mass)
    unknown_risk = max(0.0, rule_mass - confidence_mass) * 6.0
    time_pressure = 1.0 - min(1.0, remaining / float(horizon_minutes))
    debt_value = min(
        360.0,
        0.002 * amount_mass * max(0.25, avg_confidence)
        + 90.0 * time_pressure * min(1.0, rule_mass / 6.0),
    )
    emergency = (remaining < 3 * 1440 and rule_mass > 0) or (remaining < 7 * 1440 and debt_value + unknown_risk > 160.0)
    repair_price = 0.35 * debt_value + 0.2 * unknown_risk
    violation_price = 0.55 * debt_value + unknown_risk
    return PreferenceDebtMarket(
        debt_value=debt_value,
        unknown_risk=unknown_risk,
        emergency=emergency,
        repair_price=repair_price,
        violation_price=violation_price,
    )
