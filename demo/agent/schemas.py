"""Typed runtime schemas for the CROWN-Y agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

SourceScope = Literal["current_actionable", "shadow_liquidity_only", "historical_summary_only"]
ActionType = Literal["take_order", "wait", "reposition"]

CURRENT_ACTIONABLE: SourceScope = "current_actionable"
SHADOW_LIQUIDITY_ONLY: SourceScope = "shadow_liquidity_only"
HISTORICAL_SUMMARY_ONLY: SourceScope = "historical_summary_only"
VALID_SOURCE_SCOPES = {CURRENT_ACTIONABLE, SHADOW_LIQUIDITY_ONLY, HISTORICAL_SUMMARY_ONLY}


@dataclass(frozen=True)
class SimulationHorizon:
    duration_days: int
    horizon_minutes: int


@dataclass(frozen=True)
class DriverStatus:
    driver_id: str
    current_lat: float
    current_lng: float
    simulation_progress_minutes: int
    simulation_wall_time: str
    truck_length: str
    preferences: tuple[Any, ...]
    completed_order_count: int


@dataclass(frozen=True)
class NormalizedCargo:
    cargo_id: str
    source_scope: SourceScope
    decision_id: str
    observed_at_minutes: int
    price_yuan: float
    pickup_distance_km: float
    start_lat: float
    start_lng: float
    end_lat: float
    end_lng: float
    cost_time_minutes: int
    create_minutes: int | None
    remove_minutes: int | None
    load_start_minutes: int | None
    load_end_minutes: int | None
    haul_distance_km: float
    cargo_name: str = ""
    start_city: str = ""
    end_city: str = ""


@dataclass(frozen=True)
class CompiledPreferenceRule:
    rule_id: str
    kind: str
    scope: str
    condition: dict[str, Any]
    repairability: str
    reward_or_penalty: dict[str, Any]
    evidence: str
    confidence: float
    repair_action_kinds: tuple[str, ...] = ()
    predicate_type: str = "unknown"
    fields: tuple[str, ...] = ()
    operator: str = "unknown"
    values: tuple[Any, ...] = ()
    time_scope: str = "unknown"
    deadline: Any = "unknown"
    counter: Any = "unknown"
    coordinate_target: Any = "unknown"
    penalty_amount: float | None = None
    penalty_cap: float | None = None
    evidence_hash: str = ""
    unresolved_reason: str = ""
    contract_version: str = "legacy_v1"
    polarity: str = "unknown"
    observable: str = "unknown"
    metric: str = "unknown"
    counting: str = "unknown"
    slots: dict[str, Any] = field(default_factory=dict)
    repair: tuple[str, ...] = ()
    uncertainty: tuple[str, ...] = ()
    penalty_amount_source: str = "unknown"


@dataclass(frozen=True)
class CompiledPreferenceSet:
    pref_hash: str
    rules: tuple[CompiledPreferenceRule, ...]


@dataclass(frozen=True)
class RuleLedger:
    revision: int
    status_minutes: int
    completed_orders: int
    action_counts: dict[str, int]
    observed_summary_count: int
    preference_pressure: float


@dataclass(frozen=True)
class PreferenceDebtMarket:
    debt_value: float
    unknown_risk: float
    emergency: bool
    repair_price: float
    violation_price: float


@dataclass(frozen=True)
class ResourcePressureEndgame:
    intensity: float
    remaining_minutes: int
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class TimeShadowMarket:
    productive_time_shadow_price: float
    query_time_cost: float
    information_option_value: float
    sample_size: int
    mode: str


@dataclass(frozen=True)
class DriverMemoryView:
    observations_count: int
    recent_best_profit_per_min: float
    recent_feasible_count: float
    recent_query_minutes: int
    recent_wait_outcomes: tuple[float, ...] = ()


@dataclass(frozen=True)
class World:
    status: DriverStatus
    pref_hash: str
    rules: CompiledPreferenceSet
    ledger: RuleLedger
    debt_market: PreferenceDebtMarket
    endgame: ResourcePressureEndgame
    time_market: TimeShadowMarket
    memory_view: DriverMemoryView
    horizon: SimulationHorizon


@dataclass
class PreferenceCertificateItem:
    rule_id: str
    effect: str
    debt_delta: float
    confidence: float
    evidence: str


@dataclass
class PreferenceCertificate:
    candidate_id: str
    items: list[PreferenceCertificateItem] = field(default_factory=list)
    high_confidence_irreversible_violation: bool = False

    @property
    def violation_debt(self) -> float:
        return sum(max(0.0, item.debt_delta) * max(0.0, item.confidence) for item in self.items)

    @property
    def repair_value(self) -> float:
        return sum(max(0.0, -item.debt_delta) * max(0.0, item.confidence) for item in self.items)

    @property
    def unknown_risk(self) -> float:
        return sum(max(0.0, 1.0 - item.confidence) for item in self.items)


@dataclass
class ActionCertificate:
    candidate_id: str
    action_type: ActionType
    decision_id: str
    cargo_id: str | None
    source_scope: SourceScope | None
    safe: bool
    reasons: list[str] = field(default_factory=list)


@dataclass
class RolloutValue:
    value: float = 0.0
    used_second_hop_ids: list[str] = field(default_factory=list)


@dataclass
class CandidateOption:
    id: str
    action_type: ActionType
    decision_id: str
    cargo: NormalizedCargo | None = None
    duration_minutes: int = 0
    target_lat: float | None = None
    target_lng: float | None = None
    direct_money: float = 0.0
    occupied_minutes: int = 0
    deadhead_km: float = 0.0
    haul_km: float = 0.0
    finish_minutes: int = 0
    current_best_order_advantage: float = 0.0
    score: float = 0.0
    score_components: dict[str, float] = field(default_factory=dict)
    pref_cert: PreferenceCertificate | None = None
    action_cert: ActionCertificate | None = None
    rollout: RolloutValue = field(default_factory=RolloutValue)
    trace: dict[str, Any] = field(default_factory=dict)
