"""Pivot safety helpers."""

from __future__ import annotations

from ..schemas import CandidateOption


def explain_why_not_chosen(options: list[CandidateOption], chosen: CandidateOption) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for rank, option in enumerate(sorted(options, key=lambda item: item.score, reverse=True)[:5], start=1):
        rows.append(
            {
                "rank": rank,
                "candidate_id_hash_source": option.id,
                "action_type": option.action_type,
                "score": round(float(option.score), 4),
                "chosen": option.id == chosen.id,
                "why_not_chosen": "selected" if option.id == chosen.id else _reason(option, chosen),
            }
        )
    return rows


def _reason(option: CandidateOption, chosen: CandidateOption) -> str:
    if option.action_cert is not None and not option.action_cert.safe:
        return "unsafe_action_certificate"
    if option.score < chosen.score:
        return "lower_pivot_score"
    return "tie_break_not_selected"
