"""Candidate-level executable predicate verifier."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

from .geo import haversine_km
from .observed_vocab_linker import ObservedVocabLink
from .schemas import CandidateOption, CompiledPreferenceRule, World


@dataclass(frozen=True)
class CandidatePreferenceCheck:
    candidate_id: str
    rule_id: str
    predicate_match: str
    marginal_effect: str
    predicted_marginal_penalty: float
    predicted_repair_value: float
    confidence: float
    source: str = "deterministic"


def _hash(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _amount(rule: CompiledPreferenceRule) -> float:
    value = rule.penalty_amount or rule.reward_or_penalty.get("amount", 0.0)
    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        return 0.0


def _numeric_threshold(rule: CompiledPreferenceRule) -> float | None:
    values = list(rule.values)
    values.extend(v for v in (rule.condition or {}).values() if isinstance(v, (int, float)))
    numbers = []
    for value in values:
        try:
            numbers.append(float(value))
        except (TypeError, ValueError):
            continue
    plausible = [v for v in numbers if 0 < v < 1000]
    return min(plausible) if plausible else None


def _coord_targets(rule: CompiledPreferenceRule) -> list[tuple[float, float]]:
    raw = rule.coordinate_target
    if raw == "unknown":
        raw = rule.condition.get("target_coordinates")
    items = raw if isinstance(raw, list) else [raw]
    out: list[tuple[float, float]] = []
    for item in items:
        if isinstance(item, dict):
            lat = item.get("lat", item.get("latitude"))
            lng = item.get("lng", item.get("longitude"))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            lat, lng = item[0], item[1]
        else:
            continue
        try:
            point = (float(lat), float(lng))
        except (TypeError, ValueError):
            continue
        if -90 <= point[0] <= 90 and -180 <= point[1] <= 180:
            out.append(point)
    return out[:3]


def _field_value(option: CandidateOption, field: str) -> str:
    cargo = option.cargo
    if cargo is None:
        return ""
    return str(getattr(cargo, field, "") or "")


def verify_candidate(
    option: CandidateOption,
    world: World,
    links: tuple[ObservedVocabLink, ...],
) -> list[CandidatePreferenceCheck]:
    checks: list[CandidatePreferenceCheck] = []
    links_by_rule = {}
    for link in links:
        links_by_rule.setdefault(link.rule_id, []).append(link)
    for rule in world.rules.rules:
        amount = _amount(rule)
        confidence = max(0.0, min(1.0, rule.confidence))
        match = "unknown"
        effect = "unknown"
        penalty = 0.0
        repair = 0.0
        source_conf = confidence
        if rule.predicate_type == "pickup_deadhead_limit" and option.action_type == "take_order":
            threshold = _numeric_threshold(rule)
            if threshold is not None:
                match = "yes" if option.deadhead_km > threshold else "no"
                effect = "violates" if match == "yes" else "neutral"
                penalty = amount * 0.25 if match == "yes" else 0.0
                source_conf = max(confidence, 0.72)
        elif rule.predicate_type in {"cargo_field_match", "count_distinct_days"} and option.action_type == "take_order":
            for link in links_by_rule.get(rule.rule_id, []):
                value = _field_value(option, link.field)
                if value and value == link.value:
                    match = "yes"
                    effect = "violates" if link.relation == "violation" else "repairs" if link.relation == "repair" else "neutral"
                    source_conf = max(source_conf, link.confidence)
                    if effect == "violates":
                        penalty += amount * link.confidence
                    elif effect == "repairs":
                        repair += amount * link.confidence
            if match == "unknown":
                match = "no"
                effect = "neutral"
        elif rule.predicate_type == "continuous_wait":
            if option.action_type == "wait" and option.duration_minutes >= 120:
                match = "yes"
                effect = "repairs"
                repair = amount * min(0.35, option.duration_minutes / 1440.0)
                source_conf = max(confidence, 0.68)
            elif option.action_type == "take_order" and option.occupied_minutes >= 480:
                match = "yes"
                effect = "reduces_repairability"
                penalty = amount * 0.08
        elif rule.predicate_type == "off_day_quota":
            if option.action_type == "wait" and option.duration_minutes >= 8 * 60:
                match = "yes"
                effect = "repairs"
                repair = amount * 0.5
                source_conf = max(confidence, 0.7)
            elif option.action_type in {"take_order", "reposition"} and option.occupied_minutes >= 360:
                match = "yes"
                effect = "reduces_repairability"
                penalty = amount * 0.06
        elif rule.predicate_type == "location_visit":
            targets = _coord_targets(rule)
            if targets and option.action_type in {"take_order", "reposition"}:
                points = []
                if option.cargo is not None:
                    points.extend([(option.cargo.start_lat, option.cargo.start_lng), (option.cargo.end_lat, option.cargo.end_lng)])
                if option.target_lat is not None and option.target_lng is not None:
                    points.append((option.target_lat, option.target_lng))
                nearest = min((haversine_km(a, b, x, y) for a, b in points for x, y in targets), default=9999.0)
                if nearest <= 8.0:
                    match = "yes"
                    effect = "repairs"
                    repair = amount * max(confidence, 0.7)
                    source_conf = max(confidence, 0.7)
                else:
                    match = "no"
                    effect = "neutral"
        if match == "unknown" and rule.unresolved_reason:
            effect = "unknown"
            source_conf = min(source_conf, 0.35)
        checks.append(
            CandidatePreferenceCheck(
                candidate_id=_hash(option.id),
                rule_id=rule.rule_id,
                predicate_match=match,
                marginal_effect=effect,
                predicted_marginal_penalty=round(penalty, 2),
                predicted_repair_value=round(repair, 2),
                confidence=round(source_conf, 4),
            )
        )
    return checks


def apply_to_options(
    options: list[CandidateOption],
    world: World,
    links: tuple[ObservedVocabLink, ...],
    *,
    top_k: int = 50,
) -> list[CandidateOption]:
    ranked = sorted(options, key=lambda item: item.score, reverse=True)
    selected = set(id(option) for option in ranked[:top_k])
    for option in options:
        if id(option) not in selected and option.action_type != "reposition":
            continue
        checks = verify_candidate(option, world, links)
        penalty = sum(item.predicted_marginal_penalty * item.confidence for item in checks)
        repair = sum(item.predicted_repair_value * item.confidence for item in checks)
        option.score += repair - penalty
        option.score_components["pce_predicted_marginal_penalty"] = -penalty
        option.score_components["pce_predicted_repair_value"] = repair
        option.trace["pce_verifier"] = {
            "candidate_hash": _hash(option.id),
            "predicate_match_yes": sum(1 for item in checks if item.predicate_match == "yes"),
            "predicate_unknown": sum(1 for item in checks if item.predicate_match == "unknown"),
            "predicted_marginal_penalty": round(penalty, 2),
            "predicted_repair_value": round(repair, 2),
            "sources": sorted({item.source for item in checks}),
        }
    return options
