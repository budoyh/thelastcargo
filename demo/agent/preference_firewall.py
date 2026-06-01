"""Action-level Preference Firewall for PTT controllers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

from simkit.ports import SimulationApiPort

from . import config, ptt_transducer, qwen_preference_compiler, scorer_semantics_adapter
from .observed_vocab_linker import ObservedVocabLink
from .preference_controllers import ControllerImpact, PreferenceController
from .ptt_types import PTTRule
from .schemas import CandidateOption, World


@dataclass
class FirewallStats:
    scored_candidate_count: int = 0
    candidate_rule_eval_count: int = 0
    score_changed_by_controller_count: int = 0
    blocked_count: int = 0
    massive_penalty_count: int = 0
    soft_penalty_count: int = 0
    repair_value_count: int = 0
    unknown_soft_risk_count: int = 0
    audit_required_count: int = 0
    audited_candidate_count: int = 0
    auditor_changed_score_count: int = 0
    auditor_changed_decision_count: int = 0
    high_confidence_violation_count: int = 0
    repair_candidate_count: int = 0
    lost_repair_window_total: float = 0.0
    affected_actions: list[dict[str, Any]] = field(default_factory=list)

    def payload(self) -> dict[str, Any]:
        return {
            "scored_candidate_count": self.scored_candidate_count,
            "candidate_rule_eval_count": self.candidate_rule_eval_count,
            "score_changed_by_controller_count": self.score_changed_by_controller_count,
            "blocked_count": self.blocked_count,
            "massive_penalty_count": self.massive_penalty_count,
            "soft_penalty_count": self.soft_penalty_count,
            "repair_value_count": self.repair_value_count,
            "unknown_soft_risk_count": self.unknown_soft_risk_count,
            "audit_required_count": self.audit_required_count,
            "audited_candidate_count": self.audited_candidate_count,
            "auditor_changed_score_count": self.auditor_changed_score_count,
            "auditor_changed_decision_count": self.auditor_changed_decision_count,
            "high_confidence_violation_count": self.high_confidence_violation_count,
            "repair_candidate_count": self.repair_candidate_count,
            "lost_repair_window_total": round(self.lost_repair_window_total, 2),
            "affected_actions": self.affected_actions[:20],
        }


def _hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def apply_firewall(
    *,
    options: list[CandidateOption],
    world: World,
    controllers: list[PreferenceController],
    links: tuple[ObservedVocabLink, ...],
    stats: FirewallStats,
) -> list[CandidateOption]:
    if not controllers:
        return options
    rules_by_id = {controller.rule.rule_id: controller.rule for controller in controllers}
    for option in options:
        impacts: list[ControllerImpact] = []
        for controller in controllers:
            impact = controller.marginal_cost(option, world, links)
            impact = scorer_semantics_adapter.gate_impact(controller.rule, impact)
            impacts.append(impact)
            stats.candidate_rule_eval_count += 1
            ptt_transducer.STATS.candidate_rule_eval_count += 1
        marginal = sum(item.marginal_penalty * item.confidence for item in impacts)
        repair = sum(item.repair_value * item.confidence for item in impacts)
        lost = sum(item.lost_repair_window_cost * item.confidence for item in impacts)
        failure_delta = max((item.future_failure_probability_delta for item in impacts), default=0.0)
        confidence = max((item.confidence for item in impacts), default=0.0)
        unknown_soft = _low_confidence_risk(impacts, rules_by_id)
        decision = _combined_decision(impacts)
        stats.scored_candidate_count += 1
        ptt_transducer.STATS.controller_scored_candidate_count += 1
        if decision == "block":
            stats.blocked_count += 1
            ptt_transducer.STATS.hard_block_count += 1
            option.trace["hard_block_reason"] = "ptt_firewall_block"
        elif decision == "massive_penalty":
            stats.massive_penalty_count += 1
            ptt_transducer.STATS.hard_block_count += 1
            if not option.trace.get("hard_block_reason"):
                option.trace["hard_block_reason"] = "ptt_firewall_massive_penalty"
        elif decision == "qwen_audit_required":
            stats.audit_required_count += 1
        if any(item.effect == "violates" and item.confidence >= 0.6 for item in impacts):
            stats.high_confidence_violation_count += 1
        if repair > 0:
            stats.repair_candidate_count += 1
            stats.repair_value_count += 1
            ptt_transducer.STATS.repair_value_count += 1
        if marginal > 0 or lost > 0 or failure_delta > 0:
            stats.soft_penalty_count += 1
            ptt_transducer.STATS.soft_penalty_count += 1
        if unknown_soft > 0:
            stats.unknown_soft_risk_count += 1
            ptt_transducer.STATS.unknown_soft_risk_count += 1
        stats.lost_repair_window_total += lost
        score_delta = repair - marginal - lost - failure_delta * 120.0 - unknown_soft
        if abs(score_delta) > 1e-9:
            stats.score_changed_by_controller_count += 1
            ptt_transducer.STATS.score_changed_by_controller_count += 1
        option.score_components["preference_marginal_penalty"] = -round(marginal, 2)
        option.score_components["preference_repair_value"] = round(repair, 2)
        option.score_components["lost_repair_window_cost"] = -round(lost, 2)
        option.score_components["unknown_soft_risk"] = -round(unknown_soft, 2)
        option.score_components.setdefault("qwen_audit_adjustment", 0.0)
        option.score_components["ptt_marginal_penalty"] = -round(marginal, 2)
        option.score_components["ptt_repair_value"] = round(repair, 2)
        option.score_components["ptt_lost_repair_window_cost"] = -round(lost, 2)
        option.score_components["ptt_failure_probability_delta"] = -round(failure_delta * 120.0, 2)
        option.score_components["ptt_low_confidence_risk"] = -round(unknown_soft, 2)
        option.trace["ptt_firewall"] = {
            "candidate_hash": _hash(option.id),
            "decision": decision,
            "marginal_penalty": round(marginal, 2),
            "repair_value": round(repair, 2),
            "lost_repair_window_cost": round(lost, 2),
            "future_failure_probability_delta": round(failure_delta, 4),
            "confidence": round(confidence, 4),
            "top_impacts": [
                {
                    "rule_hash": _hash(item.rule_id),
                    "type": item.controller_type,
                    "effect": item.effect,
                    "decision": item.decision,
                    "penalty": item.marginal_penalty,
                    "repair": item.repair_value,
                    "reason": item.reason,
                }
                for item in sorted(impacts, key=lambda x: (x.marginal_penalty + x.repair_value), reverse=True)[:5]
            ],
        }
        if marginal or repair or lost:
            stats.affected_actions.append(
                {
                    "candidate_hash": _hash(option.id),
                    "action_type": option.action_type,
                    "decision": decision,
                    "marginal_penalty": round(marginal, 2),
                    "repair_value": round(repair, 2),
                    "lost_repair_window_cost": round(lost, 2),
                }
            )
    return options


def generate_repair_candidates(
    *,
    controllers: list[PreferenceController],
    world: World,
    visible_cargos: list[Any],
    decision_id: str,
) -> list[CandidateOption]:
    out: list[CandidateOption] = []
    for controller in controllers:
        out.extend(controller.generate_repair_candidates(world, visible_cargos, decision_id))
    return out


def maybe_audit_high_risk(
    *,
    api: SimulationApiPort | None,
    world: World,
    options: list[CandidateOption],
    stats: FirewallStats,
    limit: int = 14,
) -> None:
    if not config.ENABLE_PTT_AUDITOR or config.DISABLE_RUNTIME_QWEN or not qwen_preference_compiler.runtime_completion_available(api):
        return
    risky = _audit_candidates(options, limit)
    if not risky:
        return
    if qwen_preference_compiler.STATS.auditor_calls >= config.PTT_MAX_AUDITOR_CALLS_TOTAL:
        qwen_preference_compiler.STATS.budget_exhausted_count += 1
        return
    qwen_preference_compiler.record_auditor_call()
    ptt_transducer.STATS.auditor_trigger_count += len(risky)
    ptt_transducer.STATS.audited_candidate_count += len(risky)
    stats.audited_candidate_count += len(risky)
    try:
        resp = qwen_preference_compiler.completion_with_runtime_order(
            api=api,
            payload={
                "model": qwen_preference_compiler.STATS.last_model_name,
                "messages": [
                    {"role": "system", "content": "Return compact valid JSON only; no explanation."},
                    {
                        "role": "user",
                        "content": (
                            "Audit candidate preference effects. Return JSON {assessments:[{candidate_id,rule_id,relation,effect,risk_level,repair_level,confidence,evidence,missing_info}]}. "
                            "relation is irrelevant/supports/risk/violation/uncertain. effect is repairs/violates/neutral/reduces_repairability/unknown. "
                            "risk_level and repair_level are none/low/medium/high/catastrophic. "
                            "Do not choose an action. Input is current runtime-only visible data: "
                            + json.dumps([_audit_payload(world, option) for option in risky], ensure_ascii=False, sort_keys=True)
                        ),
                    },
                ],
                "temperature": 0,
                "max_tokens": 192,
                "enable_thinking": False,
                "thinking_budget": 0,
            },
        )
        qwen_preference_compiler._usage_from_response(resp)
        data = qwen_preference_compiler._extract_json(qwen_preference_compiler._content_from_response(resp)) or {}
        audits = data.get("assessments", data.get("audits", [])) if isinstance(data, dict) else []
        if not isinstance(audits, list):
            audits = []
        by_hash = {
            str(item.get("candidate_hash") or item.get("candidate_id") or ""): item
            for item in audits
            if isinstance(item, dict)
        }
        for option in risky:
            item = by_hash.get(_hash(option.id), {})
            relation = str(item.get("relation", item.get("match", "unknown"))) if isinstance(item, dict) else "unknown"
            effect = str(item.get("effect", "unknown")) if isinstance(item, dict) else "unknown"
            risk = str(item.get("risk_level", "none")) if isinstance(item, dict) else "none"
            repair = str(item.get("repair_level", "none")) if isinstance(item, dict) else "none"
            evidence_value = item.get("evidence", "") if isinstance(item, dict) else ""
            missing_value = item.get("missing_info", "") if isinstance(item, dict) else ""
            if relation in {"unknown", "uncertain"} or effect == "unknown":
                ptt_transducer.STATS.auditor_unknown_count += 1
            adjustment = _audit_adjustment(relation, effect, risk, repair, item.get("confidence", 0.0) if isinstance(item, dict) else 0.0)
            if adjustment:
                option.score_components["qwen_audit_adjustment"] = round(adjustment, 2)
                option.score_components["ptt_auditor_adjustment"] = round(adjustment, 2)
                stats.auditor_changed_score_count += 1
                ptt_transducer.STATS.auditor_changed_score_count += 1
            option.trace.setdefault("ptt_auditor", []).append(
                {
                    "candidate_hash": _hash(option.id),
                    "relation": relation if relation in {"irrelevant", "supports", "risk", "violation", "uncertain", "yes", "no", "unknown"} else "unknown",
                    "effect": effect if effect in {"violates", "repairs", "neutral", "reduces_repairability", "unknown"} else "unknown",
                    "risk_level": risk if risk in {"none", "low", "medium", "high", "catastrophic"} else "none",
                    "repair_level": repair if repair in {"none", "low", "medium", "high", "catastrophic"} else "none",
                    "confidence": _conf(item.get("confidence", 0.0)) if isinstance(item, dict) else 0.0,
                    "evidence_hash": _hash(evidence_value) if evidence_value else "",
                    "missing_info_hash": _hash(missing_value) if missing_value else "",
                }
            )
        return
    except Exception as exc:  # pragma: no cover - remote failures vary.
        qwen_preference_compiler.STATS.api_error_count += 1
        qwen_preference_compiler.STATS.last_error_type = exc.__class__.__name__
        return

    # Unreachable legacy per-candidate path retained only for diff locality.
    for option in risky:
        if qwen_preference_compiler.STATS.auditor_calls >= config.PTT_MAX_AUDITOR_CALLS_TOTAL:
            qwen_preference_compiler.STATS.budget_exhausted_count += 1
            return
        qwen_preference_compiler.record_auditor_call()
        ptt_transducer.STATS.auditor_trigger_count += 1
        try:
            resp = qwen_preference_compiler.completion_with_runtime_order(
                api=api,
                payload={
                    "model": qwen_preference_compiler.STATS.last_model_name,
                    "messages": [
                        {"role": "system", "content": "Return valid JSON only."},
                        {
                            "role": "user",
                            "content": (
                                "Audit candidate preference effect. Return JSON with match yes/no/unknown, "
                                "effect violates/repairs/neutral/reduces_repairability, confidence. "
                                "Do not choose an action. Input is current runtime-only visible data: "
                                + json.dumps(_audit_payload(world, option), sort_keys=True)
                            ),
                        },
                    ],
                    "temperature": 0,
                    "max_tokens": 128,
                }
            )
            qwen_preference_compiler._usage_from_response(resp)
            data = qwen_preference_compiler._extract_json(qwen_preference_compiler._content_from_response(resp)) or {}
            match = str(data.get("match", "unknown"))
            effect = str(data.get("effect", "unknown"))
            if match == "unknown" or effect == "unknown":
                ptt_transducer.STATS.auditor_unknown_count += 1
            option.trace.setdefault("ptt_auditor", []).append(
                {
                    "candidate_hash": _hash(option.id),
                    "match": match if match in {"yes", "no", "unknown"} else "unknown",
                    "effect": effect if effect in {"violates", "repairs", "neutral", "reduces_repairability", "unknown"} else "unknown",
                    "confidence": _conf(data.get("confidence", 0.0)),
                }
            )
        except Exception as exc:  # pragma: no cover - remote failures vary.
            qwen_preference_compiler.STATS.api_error_count += 1
            qwen_preference_compiler.STATS.last_error_type = exc.__class__.__name__


def _combined_decision(impacts: list[ControllerImpact]) -> str:
    if any(item.decision == "block" for item in impacts):
        return "block"
    if any(item.decision == "massive_penalty" for item in impacts):
        return "massive_penalty"
    if any(item.decision == "qwen_audit_required" for item in impacts):
        return "qwen_audit_required"
    return "pass"


def _audit_candidates(options: list[CandidateOption], limit: int) -> list[CandidateOption]:
    selected: list[CandidateOption] = []

    def add(items: list[CandidateOption]) -> None:
        for option in items:
            if option in selected:
                continue
            selected.append(option)
            if len(selected) >= limit:
                return

    risky = [
        option for option in sorted(options, key=lambda item: item.direct_money, reverse=True)
        if (option.trace.get("ptt_firewall") or {}).get("decision") in {"qwen_audit_required", "massive_penalty", "block"}
    ]
    if not risky and not _close_preference_score_gap(options):
        return []
    add(risky)
    add(sorted([o for o in options if o.action_type == "take_order"], key=lambda item: item.direct_money, reverse=True)[:8])
    add(sorted([o for o in options if o.action_type == "wait"], key=lambda item: item.score, reverse=True)[:3])
    add(sorted([o for o in options if o.action_type == "reposition"], key=lambda item: item.score, reverse=True)[:3])
    return selected[:limit]


def _close_preference_score_gap(options: list[CandidateOption]) -> bool:
    changed = [
        option for option in options
        if any(
            abs(float(option.score_components.get(name, 0.0) or 0.0)) > 1e-9
            for name in ("ptt_marginal_penalty", "ptt_repair_value", "ptt_lost_repair_window_cost", "ptt_low_confidence_risk")
        )
    ]
    if not changed:
        return False
    ranked = sorted(options, key=lambda item: item.score, reverse=True)[:2]
    if len(ranked) < 2:
        return False
    return abs(ranked[0].score - ranked[1].score) <= 180.0


def _audit_adjustment(relation: str, effect: str, risk: str, repair: str, confidence: Any) -> float:
    conf = _conf(confidence)
    risk_scale = {"none": 0.0, "low": 40.0, "medium": 120.0, "high": 300.0, "catastrophic": 700.0}
    repair_scale = {"none": 0.0, "low": 35.0, "medium": 100.0, "high": 240.0, "catastrophic": 500.0}
    penalty = risk_scale.get(risk, 0.0)
    bonus = repair_scale.get(repair, 0.0)
    if relation == "violation" or effect == "violates":
        penalty = max(penalty, 180.0)
    if effect == "repairs" or relation == "supports":
        bonus = max(bonus, 100.0)
    if effect == "reduces_repairability":
        penalty = max(penalty, 140.0)
    return (bonus - penalty) * max(0.15, conf)


def _low_confidence_risk(impacts: list[ControllerImpact], rules_by_id: dict[str, PTTRule]) -> float:
    total = 0.0
    for item in impacts:
        rule = rules_by_id.get(item.rule_id)
        if rule is None:
            continue
        if item.effect == "unknown":
            total += rule.penalty_scale() * (1.0 - item.confidence) * config.PTT_SOFT_RISK_MULTIPLIER
    return total


def _audit_payload(world: World, option: CandidateOption) -> dict[str, Any]:
    trace = option.trace.get("ptt_firewall") or {}
    cargo = option.cargo
    visible_runtime_fields = {}
    if cargo is not None:
        visible_runtime_fields = {
            "cargo_name": cargo.cargo_name,
            "start_city": cargo.start_city,
            "end_city": cargo.end_city,
        }
    return {
        "pref_hash": _hash(world.pref_hash),
        "candidate_id": _hash(option.id),
        "candidate_hash": _hash(option.id),
        "action_type": option.action_type,
        "current_preference_text": world.status.preferences,
        "visible_runtime_fields": visible_runtime_fields,
        "direct_net_bucket": _bucket(option.direct_money),
        "occupied_minutes": option.occupied_minutes,
        "deadhead_km_bucket": _bucket(option.deadhead_km),
        "haul_km_bucket": _bucket(option.haul_km),
        "firewall_decision": trace.get("decision", ""),
        "top_impacts": trace.get("top_impacts", []),
    }


def _bucket(value: float) -> str:
    if value < 0:
        return "negative"
    if value < 200:
        return "low"
    if value < 800:
        return "medium"
    return "high"


def _conf(value: Any) -> float:
    try:
        return round(max(0.0, min(1.0, float(value))), 4)
    except (TypeError, ValueError):
        return 0.0
