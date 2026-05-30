"""Scout-then-deepen query policy."""

from __future__ import annotations

from dataclasses import dataclass

from . import config
from .schemas import NormalizedCargo, World
from .time_shadow_market import query_plan_score


@dataclass(frozen=True)
class QueryPlan:
    kind: str
    k: int = 0
    scout_k: int = 0
    deepen_k: int = 0
    reason: str = ""


@dataclass(frozen=True)
class CandidateSummary:
    feasible_count: int
    best_advantage: float
    best_load_slack_minutes: int
    top_margin_good: bool


def choose(world: World) -> QueryPlan:
    if world.endgame.remaining_minutes <= config.MIN_WAIT_MINUTES:
        return QueryPlan(kind="no_query", reason="horizon_exhausted")
    if world.debt_market.emergency or world.endgame.intensity >= config.ENDGAME_HIGH:
        return QueryPlan(kind="current_small_query", k=30, reason="pressure_small_query")
    if not config.ENABLE_SCOUT_THEN_DEEPEN:
        return QueryPlan(kind="current_small_query", k=config.SCOUT_K, reason="fixed_scout")
    return QueryPlan(kind="scout_then_deepen", scout_k=config.SCOUT_K, deepen_k=config.DEEPEN_K, reason="default_scout")


def summarize_candidates_fast(world: World, cargos: list[NormalizedCargo]) -> CandidateSummary:
    feasible_count = len(cargos)
    if not cargos:
        return CandidateSummary(0, 0.0, 0, False)
    values: list[float] = []
    best_slack = 0
    for cargo in cargos:
        time_base = max(1, cargo.cost_time_minutes)
        value = cargo.price_yuan / time_base
        values.append(value)
        if cargo.load_end_minutes is not None:
            best_slack = max(best_slack, cargo.load_end_minutes - world.status.simulation_progress_minutes)
        else:
            best_slack = max(best_slack, 24 * 60)
    values.sort(reverse=True)
    best_advantage = values[0] * 100.0 if values else 0.0
    top_margin_good = len(values) >= 2 and values[0] > values[1] * 1.22
    return CandidateSummary(feasible_count, best_advantage, best_slack, top_margin_good)


def estimate_query_minutes(k: int) -> int:
    if k <= 0:
        return 0
    return (int(k) + config.QUERY_BATCH_SIZE - 1) // config.QUERY_BATCH_SIZE


def estimate_info_gain_from_deepen(world: World, summary: CandidateSummary) -> float:
    scarcity_bonus = max(0.0, config.ENOUGH_FEASIBLE_COUNT - summary.feasible_count) * 4.0
    uncertainty_bonus = world.time_market.information_option_value
    return min(260.0, scarcity_bonus + uncertainty_bonus)


def estimate_missed_window_risk(world: World, summary: CandidateSummary, k: int) -> float:
    if summary.best_load_slack_minutes <= 0:
        return 80.0
    q_minutes = estimate_query_minutes(k)
    if summary.best_load_slack_minutes < q_minutes + 20:
        return 120.0
    return 0.0


def should_deepen(world: World, scout_visible: list[NormalizedCargo]) -> bool:
    if world.debt_market.emergency:
        return False
    if world.endgame.intensity >= 0.65:
        return False
    if world.time_market.query_time_cost >= config.HIGH_QUERY_TIME_COST:
        return False
    summary = summarize_candidates_fast(world, scout_visible)
    if summary.best_advantage >= config.STRONG_ORDER_ADVANTAGE:
        return False
    if summary.best_load_slack_minutes < config.MIN_DEEPEN_SLACK_MINUTES:
        return False
    if summary.feasible_count >= config.ENOUGH_FEASIBLE_COUNT and summary.top_margin_good:
        return False
    expected_gain = estimate_info_gain_from_deepen(world, summary)
    expected_cost = world.time_market.query_time_cost * estimate_query_minutes(config.DEEPEN_K)
    missed_risk = estimate_missed_window_risk(world, summary, config.DEEPEN_K)
    return query_plan_score(expected_gain, estimate_query_minutes(config.DEEPEN_K), world, missed_risk) > 0.25 * expected_cost

