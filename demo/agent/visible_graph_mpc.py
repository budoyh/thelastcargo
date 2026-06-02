"""Visible Opportunity Graph MPC over current actionable cargo only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
    alpha: float = 0.0
    scored_options: int = 0
    score_changed_count: int = 0
    visible_graph_used_count: int = 0
    terminal_value_used_count: int = 0
    wait_then_take_count: int = 0
    reposition_then_take_count: int = 0
    visible_pair_count: int = 0
    total_bonus: float = 0.0
    online_summary_cell_count: int = 0

    def payload(self) -> dict[str, float | int | bool]:
        return {
            "enabled": self.enabled,
            "nodes": self.nodes,
            "edges": self.edges,
            "best_path_score": round(self.best_path_score, 2),
            "alpha": round(self.alpha, 4),
            "scored_options": self.scored_options,
            "score_changed_count": self.score_changed_count,
            "visible_graph_used_count": self.visible_graph_used_count,
            "terminal_value_used_count": self.terminal_value_used_count,
            "wait_then_take_count": self.wait_then_take_count,
            "reposition_then_take_count": self.reposition_then_take_count,
            "visible_pair_count": self.visible_pair_count,
            "total_bonus": round(self.total_bonus, 2),
            "online_summary_cell_count": self.online_summary_cell_count,
        }


def apply_visible_graph_mpc(
    options: list[CandidateOption],
    world: World,
    visible: list[NormalizedCargo],
    online_summary: dict[str, Any] | None = None,
) -> MpcStats:
    """Add a conservative path-value bonus without using future cargo."""
    alpha = float(config.VISIBLE_GRAPH_ALPHA)
    if not config.ENABLE_VISIBLE_GRAPH_MPC:
        return MpcStats(enabled=False, alpha=alpha)
    online_summary = online_summary or {}
    take_options = [item for item in options if item.action_type == "take_order" and item.cargo is not None]
    edges = 0
    best_path = 0.0
    score_changed = 0
    used_count = 0
    terminal_count = 0
    wait_count = 0
    reposition_count = 0
    pair_count = 0
    total_bonus = 0.0
    for option in options:
        direct = option.score
        plan_type = "single_take"
        current_visible = _current_visible(visible, option.decision_id)
        continuation = 0.0
        terminal = 0.0
        edge_count = 0
        if option.action_type == "take_order" and option.cargo is not None:
            continuation, edge_count = _best_second_hop(option, world, current_visible)
            edges += edge_count
            if continuation > 0:
                plan_type = "visible_A_to_B_pair"
                pair_count += 1
            else:
                terminal = _terminal_value(option, world, current_visible, online_summary)
                continuation = terminal
                plan_type = "single_take_terminal"
        elif option.action_type in {"wait", "reposition"}:
            terminal = _terminal_value(option, world, current_visible, online_summary)
            continuation = terminal
            if option.action_type == "wait":
                plan_type = "wait_then_A"
                wait_count += 1
            elif option.trace.get("preference_repair") or option.trace.get("macro_candidate"):
                plan_type = "preference_reposition_then_wait_or_take"
                reposition_count += 1
            else:
                plan_type = "route_start_reposition_then_A"
                reposition_count += 1
        path_score = direct + continuation
        best_path = max(best_path, path_score)
        bonus = _clamp(continuation * alpha, -config.VISIBLE_GRAPH_NEGATIVE_BONUS_CAP, config.VISIBLE_GRAPH_BONUS_CAP)
        option.score += bonus
        option.score_components["visible_graph_mpc"] = round(bonus, 2)
        if plan_type in {"visible_A_to_B_pair"}:
            option.score_components["visible_graph_route_value"] = round(bonus, 2)
        elif abs(bonus) > 1e-9:
            option.score_components["visible_graph_terminal_value"] = round(bonus, 2)
            option.score_components["terminal_value"] = option.score_components.get("terminal_value", 0.0) + round(bonus, 2)
        option.trace["visible_graph_mpc"] = {
            "plan_type": plan_type,
            "alpha": round(alpha, 4),
            "bonus": round(bonus, 2),
            "path_score": round(path_score, 2),
            "continuation_value": round(continuation, 2),
            "terminal_value": round(terminal, 2),
            "visible_pair_edges": edge_count,
            "current_actionable_count": len(current_visible),
            "online_summary_cell_count": int(online_summary.get("cell_count", 0) or 0),
            "horizon": 2,
            "uses_current_actionable_only": True,
            "uses_same_driver_online_summary": bool(online_summary),
            "no_offline_heatmap": True,
        }
        if abs(bonus) > 1e-9:
            score_changed += 1
            used_count += 1
            total_bonus += bonus
        if abs(terminal) > 1e-9:
            terminal_count += 1
    return MpcStats(
        enabled=True,
        nodes=len(take_options) + 2,
        edges=edges,
        best_path_score=best_path,
        alpha=alpha,
        scored_options=len(options),
        score_changed_count=score_changed,
        visible_graph_used_count=used_count,
        terminal_value_used_count=terminal_count,
        wait_then_take_count=wait_count,
        reposition_then_take_count=reposition_count,
        visible_pair_count=pair_count,
        total_bonus=total_bonus,
        online_summary_cell_count=int(online_summary.get("cell_count", 0) or 0),
    )


def _current_visible(visible: list[NormalizedCargo], decision_id: str) -> list[NormalizedCargo]:
    return [
        cargo
        for cargo in visible
        if cargo.source_scope == CURRENT_ACTIONABLE and cargo.decision_id == decision_id
    ]


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


def _terminal_value(
    option: CandidateOption,
    world: World,
    visible: list[NormalizedCargo],
    online_summary: dict[str, Any],
) -> float:
    start_minutes, lat, lng = _option_end_state(option, world)
    positive = 0
    best_per_hour = 0.0
    for cargo in visible:
        if option.cargo is not None and cargo.cargo_id == option.cargo.cargo_id:
            continue
        if not is_online(cargo, start_minutes):
            continue
        dead_km = haversine_km(lat, lng, cargo.start_lat, cargo.start_lng)
        dead_min = pickup_minutes(dead_km, config.REPOSITION_SPEED_KM_PER_HOUR)
        arrival = start_minutes + dead_min
        if cargo.load_end_minutes is not None and arrival > cargo.load_end_minutes:
            continue
        finish = finish_minutes_for_cargo(cargo, start_minutes, dead_min)
        if finish > world.horizon.horizon_minutes:
            continue
        direct = cargo.price_yuan - config.DEFAULT_COST_PER_KM * (dead_km + cargo.haul_distance_km)
        if direct <= 0:
            continue
        positive += 1
        best_per_hour = max(best_per_hour, direct / max(1, finish - start_minutes) * 60.0)
    online_value = _online_summary_value(lat, lng, online_summary)
    remaining_pref_debt = world.debt_market.debt_value + world.debt_market.unknown_risk
    deadline_pressure = world.endgame.intensity * 100.0
    reposition_cost = abs(option.direct_money) if option.action_type == "reposition" else 0.0
    current_value = positive * 18.0 + best_per_hour * 1.5
    memory_value = max(0.0, online_value, world.memory_view.recent_best_profit_per_min * 60.0)
    return current_value + memory_value * 0.35 - remaining_pref_debt * 0.03 - deadline_pressure - reposition_cost


def _option_end_state(option: CandidateOption, world: World) -> tuple[int, float, float]:
    if option.action_type == "take_order" and option.cargo is not None:
        return option.finish_minutes, option.cargo.end_lat, option.cargo.end_lng
    if option.action_type == "reposition" and option.target_lat is not None and option.target_lng is not None:
        return option.finish_minutes, float(option.target_lat), float(option.target_lng)
    return option.finish_minutes, world.status.current_lat, world.status.current_lng


def _online_summary_value(lat: float, lng: float, online_summary: dict[str, Any]) -> float:
    cells = online_summary.get("cells")
    if not isinstance(cells, dict):
        return 0.0
    stats = cells.get(_cell_id(lat, lng), {})
    if not isinstance(stats, dict):
        return 0.0
    return (
        float(stats.get("positive_margin_count", 0.0) or 0.0) * 12.0
        + float(stats.get("pickup_density_ema", 0.0) or 0.0) * 8.0
        + float(stats.get("delivery_inflow_ema", 0.0) or 0.0) * 6.0
        + float(stats.get("profit_per_min_ema", 0.0) or 0.0) * 90.0
        + float(stats.get("top_margin_ema", 0.0) or 0.0) * 0.08
    )


def _cell_id(lat: float, lng: float) -> tuple[int, int]:
    size = max(0.000001, float(config.VISIBLE_GRAPH_CELL_DEGREES))
    return int(float(lat) // size), int(float(lng) // size)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
