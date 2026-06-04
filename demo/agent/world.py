"""World refresh barrier for every decision and post-query state."""

from __future__ import annotations

from simkit.ports import SimulationApiPort

from . import config
from . import endgame_planner, preference_debt_market, rule_ledger, time_shadow_market
from .memory import DriverMemory
from .normalization import normalize_status
from .preference_compiler import compile_if_changed, hash_preferences
from .schemas import SimulationHorizon, World


def refresh_world(
    api: SimulationApiPort,
    driver_id: str,
    *,
    memory: DriverMemory,
    prev_world: World | None = None,
) -> World:
    status = normalize_status(api.get_driver_status(driver_id))
    pref_hash = hash_preferences(status.preferences)
    rules = compile_if_changed(
        api=api,
        status=status,
        pref_hash=pref_hash,
        prev_rules=None if prev_world is None else prev_world.rules,
    )
    memory_view = memory.snapshot()
    ledger = rule_ledger.update_or_rebuild(
        status=status,
        rules=rules,
        prev_world=prev_world,
        observed_summary_count=memory_view.observations_count,
    )
    horizon = SimulationHorizon(
        duration_days=config.SIMULATION_DURATION_DAYS,
        horizon_minutes=config.SIMULATION_HORIZON_MINUTES,
    )
    debt = preference_debt_market.price(status, ledger, rules, horizon.horizon_minutes)
    endgame = endgame_planner.price_resource_pressure(
        status_minutes=status.simulation_progress_minutes,
        horizon_minutes=horizon.horizon_minutes,
        ledger=ledger,
        debt_market=debt,
        market_liquidity=memory_view.recent_feasible_count,
    )
    time_market = time_shadow_market.price(memory=memory_view, debt_market=debt, endgame=endgame)
    return World(
        status=status,
        pref_hash=pref_hash,
        rules=rules,
        ledger=ledger,
        debt_market=debt,
        endgame=endgame,
        time_market=time_market,
        memory_view=memory_view,
        horizon=horizon,
    )
