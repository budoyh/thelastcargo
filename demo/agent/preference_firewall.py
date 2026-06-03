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

_AUDIT_CACHE: dict[str, dict[str, Any]] = {}


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
    qwen_effect_rows: list[dict[str, Any]] = field(default_factory=list)
    _auditor_trace_finalized: bool = False

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
            "qwen_effect_rows": self.qwen_effect_rows[:80],
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
            impact.past_debt = round(max(0.0, controller.final_penalty_lower_bound(world)), 2)
            impact.candidate_delta = round(impact.marginal_penalty - impact.repair_value, 2)
            impact.future_repairability_delta = round(
                impact.lost_repair_window_cost + impact.future_failure_probability_delta * controller.rule.penalty_scale(),
                2,
            )
            impacts.append(impact)
            stats.candidate_rule_eval_count += 1
            ptt_transducer.STATS.candidate_rule_eval_count += 1
        marginal = sum(item.marginal_penalty * item.confidence for item in impacts)
        repair = sum(item.repair_value * item.confidence for item in impacts)
        lost = sum(item.lost_repair_window_cost * item.confidence for item in impacts)
        past_debt = sum(item.past_debt * item.confidence for item in impacts)
        candidate_delta = sum(item.candidate_delta * item.confidence for item in impacts)
        future_repairability_delta = sum(item.future_repairability_delta * item.confidence for item in impacts)
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
        option.score_components["preference_candidate_delta"] = -round(max(0.0, candidate_delta), 2)
        option.score_components["preference_future_repairability_delta"] = -round(max(0.0, future_repairability_delta), 2)
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
            "past_debt": round(past_debt, 2),
            "candidate_delta": round(candidate_delta, 2),
            "future_repairability_delta": round(future_repairability_delta, 2),
            "lost_repair_window_cost": round(lost, 2),
            "future_failure_probability_delta": round(failure_delta, 4),
            "confidence": round(confidence, 4),
            "top_impacts": [
                {
                    "rule_hash": _hash(item.rule_id),
                    "type": item.controller_type,
                    "effect": item.effect,
                    "decision": item.decision,
                    "past_debt": item.past_debt,
                    "candidate_delta": item.candidate_delta,
                    "future_repairability_delta": item.future_repairability_delta,
                    "penalty": item.marginal_penalty,
                    "repair": item.repair_value,
                    "lost_repair_window_cost": item.lost_repair_window_cost,
                    "reason": item.reason,
                }
                for item in sorted(impacts, key=lambda x: (x.marginal_penalty + x.repair_value), reverse=True)[:5]
            ],
        }
        option.trace["preference_contract_v2_state_delta"] = {
            "candidate_hash": _hash(option.id),
            "past_debt": round(past_debt, 2),
            "candidate_delta": round(candidate_delta, 2),
            "future_repairability_delta": round(future_repairability_delta, 2),
            "marginal_penalty": round(marginal, 2),
            "repair_value": round(repair, 2),
            "lost_repair_window_cost": round(lost, 2),
            "unknown_soft_risk": round(unknown_soft, 2),
            "rule_count": len(impacts),
        }
        if marginal or repair or lost:
            stats.affected_actions.append(
                {
                    "candidate_hash": _hash(option.id),
                    "action_type": option.action_type,
                    "decision": decision,
                    "past_debt": round(past_debt, 2),
                    "candidate_delta": round(candidate_delta, 2),
                    "future_repairability_delta": round(future_repairability_delta, 2),
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
    limit = min(limit, int(getattr(config, "PTT_AUDITOR_CANDIDATE_LIMIT", limit) or limit))
    risky = _audit_candidates(options, limit)
    if not risky:
        return
    payloads = [_audit_payload(world, option) for option in risky]
    audit_key = _hash({"pref_hash": world.pref_hash, "payloads": payloads})
    decision_index = _decision_index(risky[0].decision_id if risky else "")
    call_id = _hash({"audit_key": audit_key, "decision_index": decision_index})
    cache_hit = audit_key in _AUDIT_CACHE
    ptt_transducer.STATS.auditor_trigger_count += len(risky)
    ptt_transducer.STATS.audited_candidate_count += len(risky)
    stats.audited_candidate_count += len(risky)
    try:
        retry_before = qwen_preference_compiler.STATS.retry_count
        if cache_hit:
            qwen_preference_compiler.STATS.cache_hits += 1
            data = _AUDIT_CACHE[audit_key]
        else:
            if qwen_preference_compiler.STATS.auditor_calls >= config.PTT_MAX_AUDITOR_CALLS_TOTAL:
                qwen_preference_compiler.STATS.budget_exhausted_count += 1
                return
            qwen_preference_compiler.STATS.cache_misses += 1
            qwen_preference_compiler.record_auditor_call()
            resp = qwen_preference_compiler.completion_with_runtime_order(
                api=api,
                payload={
                    "model": qwen_preference_compiler.STATS.last_model_name,
                    "messages": [
                        {"role": "system", "content": "Return compact valid JSON only; no explanation."},
                        {
                            "role": "user",
                            "content": (
                                "Audit each candidate preference effect. Return compact JSON only: "
                                "{\"assessments\":[{\"candidate_hash\":\"one input candidate_hash\","
                                "\"rule_id\":\"redacted_or_empty\",\"relation\":\"violation|repair|neutral|unknown\","
                                "\"effect\":\"violates|repairs|neutral|reduces_repairability|unknown\","
                                "\"risk_score\":0.0,\"repair_score\":0.0,\"confidence\":0.0,"
                                "\"evidence\":\"short runtime evidence\",\"missing_info\":\"\"}]}. "
                                "risk_score and repair_score are numeric 0..1. Include one compact assessment for every input candidate_hash, in the same order. "
                                "Keep evidence under 6 words and missing_info empty unless required. "
                                "Do not choose an action, do not veto an action, and do not output a final action. "
                                "Input is current runtime-only visible data: "
                                + json.dumps(payloads, ensure_ascii=False, sort_keys=True)
                            ),
                        },
                    ],
                    "temperature": 0,
                    "max_tokens": 1024,
                    "enable_thinking": False,
                },
            )
            qwen_preference_compiler._usage_from_response(resp)
            data = qwen_preference_compiler._extract_json(qwen_preference_compiler._content_from_response(resp)) or {}
            if isinstance(data, list):
                data = {"assessments": data}
            if isinstance(data, dict):
                data = {k: v for k, v in data.items() if k not in {"action", "final_action", "chosen_action"}}
                _AUDIT_CACHE[audit_key] = data
        retry_count = qwen_preference_compiler.STATS.retry_count - retry_before
        audits = _coerce_audits(data)
        json_valid = isinstance(data, dict) and isinstance(audits, list)
        if not isinstance(audits, list):
            audits = []
        by_hash = _audit_items_by_candidate(audits)
        rank_before = _rank_order(options, include_pending_audit=False)
        pending_rows: list[dict[str, Any]] = []
        for offset, option in enumerate(risky):
            item = by_hash.get(_hash(option.id)) or by_hash.get(option.id)
            if item is None and offset < len(audits) and isinstance(audits[offset], dict):
                item = audits[offset]
            has_assessment = isinstance(item, dict)
            relation = _normalize_relation(item.get("relation", item.get("match", "unknown"))) if has_assessment else "unknown"
            effect = _normalize_effect(item.get("effect", "unknown")) if has_assessment else "unknown"
            risk = str(item.get("risk_level", "none")) if has_assessment else "none"
            repair = str(item.get("repair_level", "none")) if has_assessment else "none"
            evidence_value = item.get("evidence", "") if isinstance(item, dict) else ""
            missing_value = item.get("missing_info", "") if isinstance(item, dict) else ""
            if relation in {"unknown", "uncertain"} or effect == "unknown":
                ptt_transducer.STATS.auditor_unknown_count += 1
            confidence = _conf(item.get("confidence", 0.0)) if has_assessment else 0.0
            risk_score = (
                _audit_numeric_score(item.get("risk_score"), option, kind="risk")
                if has_assessment
                else None
            )
            repair_score = (
                _audit_numeric_score(item.get("repair_score"), option, kind="repair")
                if has_assessment
                else None
            )
            if risk_score is None:
                risk_score = _audit_level_score(risk, option, kind="risk") if has_assessment else 0.0
            if repair_score is None:
                repair_score = _audit_level_score(repair, option, kind="repair") if has_assessment else 0.0
            adjustment = _audit_adjustment(
                relation,
                effect,
                risk,
                repair,
                confidence,
                option=option,
                risk_score=risk_score,
                repair_score=repair_score,
                has_assessment=has_assessment,
            )
            adjustment *= getattr(config, "TRIDENT_QWEN_AUDIT_SCALE", 1.0)
            if adjustment:
                option.score_components["qwen_audit_adjustment"] = round(adjustment, 2)
                option.score_components["ptt_auditor_adjustment"] = round(adjustment, 2)
                qwen_preference_compiler.record_audit_adjustment(adjustment)
                stats.auditor_changed_score_count += 1
                ptt_transducer.STATS.auditor_changed_score_count += 1
            row = {
                "call_id": call_id,
                "decision_index": decision_index,
                "candidate_hash": _hash(option.id),
                "candidate_count": len(risky),
                "affected_rule_ids": _affected_rule_ids(option, item if has_assessment else {}),
                "output_relation": relation if relation in {"irrelevant", "supports", "repair", "risk", "neutral", "violation", "uncertain", "yes", "no", "unknown"} else "unknown",
                "output_effect": effect if effect in {"violates", "repairs", "neutral", "reduces_repairability", "unknown"} else "unknown",
                "raw_risk_score": round(risk_score, 2),
                "raw_repair_score": round(repair_score, 2),
                "applied_score_adjustment": round(adjustment, 2),
                "ranking_changed": False,
                "action_changed": False,
                "final_action_used": False,
                "confidence": confidence,
                "json_valid": bool(json_valid and has_assessment),
                "retry_count": retry_count,
                "cache_hit": cache_hit,
                "evidence_hash": _hash(evidence_value) if evidence_value else "",
                "missing_info_hash": _hash(missing_value) if missing_value else "",
            }
            pending_rows.append(row)
            option.trace.setdefault("ptt_auditor", []).append(dict(row))
        rank_after = _rank_order(options, include_pending_audit=True)
        ranking_changed = rank_before != rank_after
        for row in pending_rows:
            row["ranking_changed"] = ranking_changed
            stats.qwen_effect_rows.append(row)
        for option in risky:
            for row in option.trace.get("ptt_auditor", []):
                if isinstance(row, dict) and row.get("call_id") == call_id:
                    row["ranking_changed"] = ranking_changed
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


def finalize_auditor_effect_trace(
    *,
    options: list[CandidateOption],
    chosen: CandidateOption,
    stats: FirewallStats,
) -> None:
    if stats._auditor_trace_finalized or not stats.qwen_effect_rows:
        return
    stats._auditor_trace_finalized = True
    chosen_hash = _hash(chosen.id)
    eligible = [
        option
        for option in options
        if not (option.action_cert and not option.action_cert.safe)
    ]
    if not eligible:
        eligible = options
    without_qwen_best = max(
        eligible,
        key=lambda option: float(option.score) - _option_qwen_adjustment(option),
        default=chosen,
    )
    action_changed = without_qwen_best.id != chosen.id
    if action_changed:
        stats.auditor_changed_decision_count += 1
        ptt_transducer.STATS.auditor_changed_decision_count += 1
        ptt_transducer.STATS.auditor_changed_action_count += 1
    for row in stats.qwen_effect_rows:
        candidate_hash = row.get("candidate_hash")
        row["final_action_used"] = candidate_hash == chosen_hash
        row["action_changed"] = bool(action_changed)
    for option in options:
        for row in option.trace.get("ptt_auditor", []):
            if not isinstance(row, dict):
                continue
            row["final_action_used"] = row.get("candidate_hash") == chosen_hash
            row["action_changed"] = bool(action_changed)


def _option_qwen_adjustment(option: CandidateOption) -> float:
    for key in ("qwen_audit_adjustment_applied", "qwen_audit_adjustment", "ptt_auditor_adjustment"):
        try:
            value = float(option.score_components.get(key, 0.0) or 0.0)
        except (TypeError, ValueError):
            value = 0.0
        if abs(value) > 1e-9:
            return value
    return 0.0


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


def _rank_order(options: list[CandidateOption], *, include_pending_audit: bool) -> list[str]:
    return [
        _hash(option.id)
        for option in sorted(
            options,
            key=lambda item: float(item.score)
            + (float(item.score_components.get("qwen_audit_adjustment", 0.0) or 0.0) if include_pending_audit else 0.0),
            reverse=True,
        )
    ]


def _decision_index(decision_id: str) -> int:
    tail = str(decision_id).rsplit(":", 1)[-1]
    try:
        return int(tail)
    except (TypeError, ValueError):
        return 0


def _coerce_audits(data: Any) -> list[Any]:
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    for key in ("assessments", "audits", "assessment", "results"):
        value = data.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            return [value]
    return []


def _audit_items_by_candidate(audits: list[Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in audits:
        if not isinstance(item, dict):
            continue
        for key in ("candidate_hash", "candidate_id", "candidate", "id"):
            value = item.get(key)
            if value in (None, ""):
                continue
            out[str(value)] = item
    return out


def _normalize_relation(value: Any) -> str:
    raw = str(value or "unknown").strip().lower()
    mapping = {
        "violates": "violation",
        "violate": "violation",
        "bad": "violation",
        "risk": "violation",
        "risky": "violation",
        "supports": "repair",
        "support": "repair",
        "repair": "repair",
        "repairs": "repair",
        "irrelevant": "neutral",
        "none": "neutral",
        "no": "neutral",
        "yes": "violation",
        "uncertain": "unknown",
        "unclear": "unknown",
    }
    raw = mapping.get(raw, raw)
    return raw if raw in {"violation", "repair", "neutral", "unknown"} else "unknown"


def _normalize_effect(value: Any) -> str:
    raw = str(value or "unknown").strip().lower()
    mapping = {
        "violation": "violates",
        "violate": "violates",
        "risk": "violates",
        "risky": "violates",
        "repair": "repairs",
        "support": "repairs",
        "supports": "repairs",
        "none": "neutral",
        "irrelevant": "neutral",
        "uncertain": "unknown",
        "unclear": "unknown",
    }
    raw = mapping.get(raw, raw)
    return raw if raw in {"violates", "repairs", "neutral", "reduces_repairability", "unknown"} else "unknown"


def _affected_rule_ids(option: CandidateOption, item: dict[str, Any]) -> list[str]:
    out: list[str] = []
    rule_id = item.get("rule_id") if isinstance(item, dict) else None
    if rule_id not in (None, ""):
        out.append(_hash(rule_id))
    for impact in (option.trace.get("ptt_firewall") or {}).get("top_impacts", []):
        if not isinstance(impact, dict):
            continue
        value = impact.get("rule_hash")
        if value not in (None, ""):
            out.append(str(value))
    return list(dict.fromkeys(out))[:8]


def _audit_level_score(level: str, option: CandidateOption, *, kind: str) -> float:
    remaining = _audit_remaining_value(option)
    risk_scale = {"none": 0.0, "low": 0.25, "medium": 0.55, "high": 1.0, "catastrophic": 1.8}
    repair_scale = {"none": 0.0, "low": 0.2, "medium": 0.5, "high": 0.9, "catastrophic": 1.25}
    scale = repair_scale if kind == "repair" else risk_scale
    return remaining * scale.get(level, 0.0)


def _audit_remaining_value(option: CandidateOption) -> float:
    firewall = option.trace.get("ptt_firewall") or {}
    return max(
        float(firewall.get("marginal_penalty", 0.0) or 0.0),
        float(firewall.get("lost_repair_window_cost", 0.0) or 0.0),
        float(firewall.get("future_repairability_delta", 0.0) or 0.0),
        120.0,
    )


def _audit_numeric_score(value: Any, option: CandidateOption, *, kind: str) -> float | None:
    if value in (None, ""):
        return None
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if score < 0.0:
        score = 0.0
    remaining = _audit_remaining_value(option)
    if score <= 1.0:
        cap = 1.25 if kind == "repair" else 1.8
        return remaining * min(score, cap)
    return min(score, remaining * (1.25 if kind == "repair" else 1.8))


def _audit_adjustment(
    relation: str,
    effect: str,
    risk: str,
    repair: str,
    confidence: Any,
    *,
    option: CandidateOption,
    risk_score: float,
    repair_score: float,
    has_assessment: bool,
) -> float:
    if not has_assessment:
        return 0.0
    conf = _conf(confidence)
    penalty = risk_score
    bonus = repair_score
    if relation in {"unknown", "uncertain"} or effect == "unknown":
        penalty = max(penalty, getattr(config, "TRIDENT_UNKNOWN_AUDIT_SOFT_RISK", 35.0))
    if relation in {"violation", "risk"} or effect == "violates":
        cap = max(0.0, float(option.direct_money)) + 420.0
        remaining = max(penalty, float((option.trace.get("ptt_firewall") or {}).get("marginal_penalty", 0.0) or 0.0), 180.0)
        penalty = min(remaining, cap) if conf >= 0.7 else remaining * 0.75
    if effect == "repairs" or relation in {"supports", "repair"}:
        bonus = max(bonus, 100.0)
    if effect == "reduces_repairability":
        penalty = max(penalty, risk_score, 140.0)
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
