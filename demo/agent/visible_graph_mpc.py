"""Visible Opportunity Graph MPC over current actionable cargo only."""

from __future__ import annotations

from dataclasses import dataclass

from . import config
from .geo import haversine_km, pickup_minutes
from .normalization import finish_minutes_for_cargo, is_online
from .schemas import CURRENT_ACTIONABLE, CandidateOption, NormalizedCargo, World


@dataclass(frozen=True)
class MpcStats:
    enabled: bool
    nodes: int = 0
    edges: int = 0
    best_path_score: float = 0.0

    def payload(self) -> dict[str, float | int | bool]:
        return {
            "enabled": self.enabled,
            "nodes": self.nodes,
            "edges": self.edges,
            "best_path_score": round(self.best_path_score, 2),
        }


def apply_visible_graph_mpc(
    options: list[CandidateOption],
    world: World,
    visible: list[NormalizedCargo],
) -> MpcStats:
    """Add a conservative path-value bonus without using future cargo."""
    if not config.ENABLE_VISIBLE_GRAPH_MPC:
        return MpcStats(enabled=False)
    take_options = [item for item in options if item.action_type == "take_order" and item.cargo is not None]
    edges = 0
    best_path = 0.0
    for option in options:
        direct = option.score
        continuation = 0.0
        if option.action_type == "take_order" and option.cargo is not None:
            continuation, edge_count = _best_second_hop(option, world, visible)
            edges += edge_count
        elif option.action_type in {"wait", "reposition"}:
            continuation = _terminal_value(option, world, visible)
        path_score = direct + continuation
        best_path = max(best_path, path_score)
        bonus = max(-120.0, min(160.0, continuation * 0.20))
        option.score += bonus
        option.score_components["visible_graph_mpc"] = round(bonus, 2)
        option.trace["visible_graph_mpc"] = {
            "path_score": round(path_score, 2),
            "continuation_value": round(continuation, 2),
            "horizon": 2,
            "uses_current_actionable_only": True,
        }
    return MpcStats(enabled=True, nodes=len(take_options) + 2, edges=edges, best_path_score=best_path)


def _best_second_hop(option: CandidateOption, world: World, visible: list[NormalizedCargo]) -> tuple[float, int]:
    assert option.cargo is not None
    time_a = option.finish_minutes
    lat_a = option.cargo.end_lat
    lng_a = option.cargo.end_lng
    best = 0.0
    edges = 0
    for cargo in visible:
        if cargo.cargo_id == option.cargo.cargo_id:
            continue
        if cargo.source_scope != CURRENT_ACTIONABLE or cargo.decision_id != option.decision_id:
            continue
        if not is_online(cargo, time_a):
            continue
        dead_km = haversine_km(lat_a, lng_a, cargo.start_lat, cargo.start_lng)
        dead_min = pickup_minutes(dead_km, config.REPOSITION_SPEED_KM_PER_HOUR)
        arrival = time_a + dead_min
        if cargo.load_end_minutes is not None and arrival > cargo.load_end_minutes:
            continue
        finish = finish_minutes_for_cargo(cargo, time_a, dead_min)
        if finish > world.horizon.horizon_minutes:
            continue
        edges += 1
        direct = cargo.price_yuan - config.DEFAULT_COST_PER_KM * (dead_km + cargo.haul_distance_km)
        time_cost = world.time_market.productive_time_shadow_price * max(1, finish - time_a)
        best = max(best, config.TWO_HOP_DISCOUNT * (direct - time_cost))
    return best, edges


def _terminal_value(option: CandidateOption, world: World, visible: list[NormalizedCargo]) -> float:
    positive = 0
    best_per_hour = 0.0
    for cargo in visible:
        if cargo.source_scope != CURRENT_ACTIONABLE:
            continue
        direct = cargo.price_yuan - config.DEFAULT_COST_PER_KM * (cargo.pickup_distance_km + cargo.haul_distance_km)
        if direct <= 0:
            continue
        positive += 1
        best_per_hour = max(best_per_hour, direct / max(1, cargo.cost_time_minutes) * 60.0)
    remaining_pref_debt = world.debt_market.debt_value + world.debt_market.unknown_risk
    deadline_pressure = world.endgame.intensity * 100.0
    reposition_cost = abs(option.direct_money) if option.action_type == "reposition" else 0.0
    return positive * 18.0 + best_per_hour * 1.5 - remaining_pref_debt * 0.03 - deadline_pressure - reposition_cost
