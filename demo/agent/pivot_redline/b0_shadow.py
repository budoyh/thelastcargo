"""Pure B0-style shadow comparison for pivot traces.

This module intentionally does not import rescue_scorer. It is a side-effect
free approximation used as a baseline/no-op oracle and trace comparison only.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..schemas import CandidateOption, World


@dataclass(frozen=True)
class B0ShadowResult:
    option: CandidateOption
    score: float
    reason: str


def score_b0_pure(options: list[CandidateOption], world: World, wait_lock: object | None = None) -> B0ShadowResult:
    snapshot = list(options)
    scored: list[tuple[float, CandidateOption]] = []
    consecutive_wait = int(getattr(wait_lock, "consecutive_wait", 0) or 0)
    for option in snapshot:
        score = _b0_like_score(option, world, consecutive_wait)
        scored.append((score, option))
    if not scored:
        raise ValueError("score_b0_pure requires at least one option")
    score, option = max(scored, key=lambda item: item[0])
    return B0ShadowResult(option=option, score=round(float(score), 6), reason="pure_b0_shadow_score")


def _b0_like_score(option: CandidateOption, world: World, consecutive_wait: int) -> float:
    if option.action_type == "take_order":
        pph = option.direct_money / max(1.0, option.occupied_minutes / 60.0)
        score = option.direct_money + 4.0 * pph - 2.0 * option.deadhead_km
        if option.direct_money < 1.0:
            score -= 1000.0
        if option.occupied_minutes > 18 * 60:
            score -= 80.0
        return score
    if option.action_type == "reposition":
        return -500.0 - option.deadhead_km
    wait_penalty = 20.0 + 20.0 * consecutive_wait
    if world.endgame.intensity > 0.8:
        wait_penalty += 80.0
    return -wait_penalty
