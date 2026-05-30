"""Limited yes/no/unknown preference judge adapter."""

from __future__ import annotations

import json
from typing import Any

from . import config
from .schemas import CandidateOption, World

ALLOWED_KEYS = {"candidate_id", "violates_preference", "rule_ids", "evidence", "confidence"}
ALLOWED_ANSWERS = {"yes", "no", "unknown"}


def parse_judge_response(content: str) -> dict[str, Any]:
    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return {"violates_preference": "unknown", "confidence": 0.0}
    if not isinstance(payload, dict):
        return {"violates_preference": "unknown", "confidence": 0.0}
    if any(key not in ALLOWED_KEYS for key in payload):
        return {"violates_preference": "unknown", "confidence": 0.0}
    answer = str(payload.get("violates_preference", "unknown")).strip().lower()
    if answer not in ALLOWED_ANSWERS:
        answer = "unknown"
    try:
        confidence = max(0.0, min(1.0, float(payload.get("confidence", 0.0))))
    except (TypeError, ValueError):
        confidence = 0.0
    return {
        "candidate_id": str(payload.get("candidate_id", "")),
        "violates_preference": answer,
        "rule_ids": list(payload.get("rule_ids") or []),
        "evidence": str(payload.get("evidence", "")),
        "confidence": confidence,
    }


def apply_limited(options: list[CandidateOption], world: World, *_: Any) -> list[CandidateOption]:
    if not config.ENABLE_LLM_JUDGE:
        return options
    # The online build keeps this disabled unless an external caller supplies
    # a compliant yes/no/unknown result. No action is ever produced here.
    return options

