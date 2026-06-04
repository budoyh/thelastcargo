"""Month-end horizon protection."""

from __future__ import annotations

from ..schemas import CandidateOption, World


def penalty(option: CandidateOption, world: World) -> float:
    remaining_after = world.horizon.horizon_minutes - option.finish_minutes
    if option.action_type != "take_order":
        return 0.0
    if remaining_after < 0:
        return 10000.0
    if remaining_after < 24 * 60 and option.occupied_minutes > 8 * 60:
        return 2.0
    if remaining_after < 12 * 60:
        return 1.0
    return 0.0
