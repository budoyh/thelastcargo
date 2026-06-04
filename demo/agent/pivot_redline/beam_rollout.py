"""Deterministic depth-2/3 visible rollout over current visible candidates."""

from __future__ import annotations

from dataclasses import dataclass, field

from .value_model import PivotValueModel
from ..schemas import CandidateOption, NormalizedCargo


@dataclass
class BeamNode:
    candidate_id: str
    depth: int
    local_score: float
    continuation_score: float = 0.0
    children: list["BeamNode"] = field(default_factory=list)

    @property
    def total_score(self) -> float:
        return self.local_score + self.continuation_score


def rollout_bonus(
    option: CandidateOption,
    candidates: list[CandidateOption],
    visible: list[NormalizedCargo],
    *,
    depth: int,
    width: int,
    value_model: PivotValueModel,
) -> tuple[float, BeamNode]:
    root = BeamNode(option.id, 1, float(option.score))
    if depth <= 1 or width <= 0:
        return 0.0, root
    next_options = [
        candidate
        for candidate in sorted(candidates, key=lambda item: item.direct_money / max(1.0, item.occupied_minutes), reverse=True)
        if candidate.id != option.id and candidate.action_type == "take_order"
    ][:width]
    for child_option in next_options:
        local = child_option.direct_money + value_model.terminal_value(child_option, visible)
        child = BeamNode(child_option.id, 2, local)
        if depth >= 3:
            grandchildren = [
                candidate
                for candidate in next_options
                if candidate.id not in {option.id, child_option.id}
            ][: max(0, width - 1)]
            for grand in grandchildren:
                grand_score = 0.5 * (grand.direct_money + value_model.terminal_value(grand, visible))
                child.children.append(BeamNode(grand.id, 3, grand_score))
            child.continuation_score = max((grand.total_score for grand in child.children), default=0.0) * 0.5
        root.children.append(child)
    root.continuation_score = max((child.total_score for child in root.children), default=0.0) * 0.25
    return round(root.continuation_score, 6), root
