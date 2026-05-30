"""Preference certificates from compiled DSL rules."""

from __future__ import annotations

from .schemas import CandidateOption, PreferenceCertificate, PreferenceCertificateItem, World


def _bounded(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def _rule_exposure(option: CandidateOption, kind: str) -> float:
    total_distance = max(0.0, option.deadhead_km) + max(0.0, option.haul_km)
    duration = max(0.0, float(option.occupied_minutes))
    if option.action_type == "wait":
        return _bounded(duration / 720.0) * 0.35
    if kind == "time_window":
        return _bounded(duration / 720.0)
    if kind == "quantitative_limit":
        distance_risk = _bounded(total_distance / 650.0)
        duration_risk = _bounded(duration / 840.0)
        return max(distance_risk, duration_risk)
    if option.action_type == "reposition":
        return _bounded(total_distance / 180.0) * 0.65
    return 0.18


def certify(option: CandidateOption, world: World) -> PreferenceCertificate:
    cert = PreferenceCertificate(candidate_id=option.id)
    for rule in world.rules.rules:
        amount = max(0.0, float(rule.reward_or_penalty.get("amount", 0.0) or 0.0))
        confidence = max(0.0, min(1.0, rule.confidence))
        exposure = _rule_exposure(option, rule.kind)
        if option.action_type == "wait":
            effect = "unknown"
            debt_delta = 0.0008 * amount * exposure * (1.0 - confidence)
        elif option.action_type == "take_order":
            effect = "violates" if exposure >= 0.7 and confidence >= 0.72 else "unknown"
            debt_delta = amount * exposure * (0.006 + 0.006 * confidence)
        else:
            effect = "violates" if exposure >= 0.6 and confidence >= 0.72 else "unknown"
            debt_delta = amount * exposure * (0.008 + 0.008 * confidence)
        if (
            rule.repairability == "irreversible_after_action"
            and option.action_type in {"take_order", "reposition"}
            and confidence >= 0.72
            and exposure >= 0.7
            and amount >= 5000.0
        ):
            cert.high_confidence_irreversible_violation = True
        cert.items.append(
            PreferenceCertificateItem(
                rule_id=rule.rule_id,
                effect=effect,
                debt_delta=debt_delta,
                confidence=confidence,
                evidence=rule.evidence,
            )
        )
    return cert


def certify_virtual_take(option: CandidateOption, world: World) -> PreferenceCertificate:
    return certify(option, world)
