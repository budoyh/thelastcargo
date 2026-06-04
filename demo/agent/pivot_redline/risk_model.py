"""Runtime action risk scorer using generic observable features."""

from __future__ import annotations

from dataclasses import dataclass

from ..schemas import CandidateOption, World


@dataclass(frozen=True)
class RiskScore:
    value: float
    reasons: tuple[str, ...]


class PivotRiskModel:
    """Conservative action-level risk model.

    This is runtime code. It is not claimed as trained/validated until the
    offline model audit and full-run ablation gates pass.
    """

    def score(self, option: CandidateOption, world: World) -> RiskScore:
        risk = 0.0
        reasons: list[str] = []
        if option.action_type == "take_order":
            if option.occupied_minutes > 18 * 60:
                risk += 2.0
                reasons.append("long_lockup")
            if option.deadhead_km > 120.0:
                risk += 1.5
                reasons.append("pickup_deadhead")
            if option.finish_minutes > world.horizon.horizon_minutes - 24 * 60:
                risk += 2.5
                reasons.append("month_end_lockup")
            if option.pref_cert and option.pref_cert.violation_debt > 0:
                risk += min(4.0, option.pref_cert.violation_debt / 800.0)
                reasons.append("preference_debt")
        elif option.action_type == "reposition":
            risk += min(2.5, option.deadhead_km / 100.0)
            reasons.append("empty_move")
        elif option.duration_minutes > 120:
            risk += 0.5
            reasons.append("long_wait")
        return RiskScore(round(risk, 6), tuple(reasons))
