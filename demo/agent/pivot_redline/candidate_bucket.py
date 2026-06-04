"""Bucketed candidate generation without a single top-N money truncation."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field

from .. import candidate_generator, config
from ..geo import haversine_km
from ..schemas import CandidateOption, NormalizedCargo, World
from ..time_utils import remaining_minutes


@dataclass
class BucketStats:
    bucket_counts: dict[str, int] = field(default_factory=dict)

    def add(self, bucket: str, options: list[CandidateOption]) -> None:
        self.bucket_counts[bucket] = self.bucket_counts.get(bucket, 0) + len(options)
        for option in options:
            buckets = option.trace.setdefault("pivot_buckets", [])
            if bucket not in buckets:
                buckets.append(bucket)


def build_bucketed_candidates(
    world: World,
    visible: list[NormalizedCargo],
    decision_id: str,
    *,
    b0_option: CandidateOption | None = None,
) -> tuple[list[CandidateOption], BucketStats]:
    base = candidate_generator.build_options(world, visible, decision_id)
    takes = [option for option in base if option.action_type == "take_order"]
    waits = _wait_options(world, decision_id)
    repositions = _reposition_options(world, visible, decision_id, takes)
    stats = BucketStats()
    selected: "OrderedDict[str, CandidateOption]" = OrderedDict()

    def include(bucket: str, options: list[CandidateOption]) -> None:
        stats.add(bucket, options)
        for option in options:
            selected.setdefault(option.id, option)

    include("top_direct_net", _top(takes, key=lambda option: option.direct_money, n=40))
    include("top_profit_per_hour", _top(takes, key=lambda option: _pph(option), n=40))
    include("top_short_duration", _top(takes, key=lambda option: -option.occupied_minutes, n=25))
    include("top_low_pickup_deadhead", _top(takes, key=lambda option: -option.deadhead_km, n=25))
    include("top_low_total_lockup", _top(takes, key=lambda option: -(option.occupied_minutes + option.deadhead_km * 3.0), n=25))
    include("top_good_dropoff_terminal_proxy", _top(takes, key=lambda option: _terminal_proxy(option, visible), n=25))
    include("top_potential_repair_take", _top(takes, key=lambda option: _repair_proxy(option, world), n=25))
    include("top_low_pref_risk", _top(takes, key=lambda option: -_risk_proxy(option, world), n=25))
    if b0_option is not None:
        include("b0_action", [b0_option])
    include("wait_options", waits)
    include("reposition_current_pickup_clusters", repositions[:5])
    include("reposition_dropoff_terminal_clusters", repositions[5:10])
    return list(selected.values()), stats


def _top(options: list[CandidateOption], *, key, n: int) -> list[CandidateOption]:
    return sorted(options, key=key, reverse=True)[:n]


def _pph(option: CandidateOption) -> float:
    return option.direct_money / max(1.0, option.occupied_minutes / 60.0)


def _terminal_proxy(option: CandidateOption, visible: list[NormalizedCargo]) -> float:
    if option.cargo is None:
        return 0.0
    near = 0
    for cargo in visible:
        if haversine_km(option.cargo.end_lat, option.cargo.end_lng, cargo.start_lat, cargo.start_lng) <= 80.0:
            near += 1
    return near


def _repair_proxy(option: CandidateOption, world: World) -> float:
    return max(0.0, float(world.debt_market.repair_price) - 0.01 * option.occupied_minutes)


def _risk_proxy(option: CandidateOption, world: World) -> float:
    if option.cargo is None:
        return 0.0
    risk = 0.0
    if option.occupied_minutes > 18 * 60:
        risk += 2.0
    if option.finish_minutes > world.horizon.horizon_minutes - 24 * 60:
        risk += 2.0
    risk += min(3.0, option.deadhead_km / 120.0)
    return risk


def _wait_options(world: World, decision_id: str) -> list[CandidateOption]:
    remaining = remaining_minutes(world.status.simulation_progress_minutes, world.horizon.horizon_minutes)
    out: list[CandidateOption] = []
    for duration in (15, 30, 60, 120, 240):
        if remaining <= 0:
            continue
        use_duration = min(duration, remaining)
        option = CandidateOption(
            id=f"pivot_wait:{use_duration}",
            action_type="wait",
            decision_id=decision_id,
            duration_minutes=int(use_duration),
            occupied_minutes=int(use_duration),
            finish_minutes=world.status.simulation_progress_minutes + int(use_duration),
        )
        option.trace["pivot_wait_policy"] = "bucketed_wait"
        out.append(option)
    return out


def _reposition_options(
    world: World,
    visible: list[NormalizedCargo],
    decision_id: str,
    take_options: list[CandidateOption],
) -> list[CandidateOption]:
    options: list[CandidateOption] = []
    clusters = _cluster_targets(world, visible, pickup=True) + _cluster_targets(world, visible, pickup=False)
    best_direct = max((option.direct_money for option in take_options), default=0.0)
    for idx, (lat, lng, score, kind) in enumerate(clusters[:10], start=1):
        distance = haversine_km(world.status.current_lat, world.status.current_lng, lat, lng)
        if distance < 3.0 or distance > 180.0:
            continue
        duration = max(1, int(distance / config.REPOSITION_SPEED_KM_PER_HOUR * 60.0 + 0.999999))
        option = CandidateOption(
            id=f"pivot_reposition:{kind}:{idx}",
            action_type="reposition",
            decision_id=decision_id,
            target_lat=float(lat),
            target_lng=float(lng),
            direct_money=-(distance * config.DEFAULT_COST_PER_KM),
            occupied_minutes=duration,
            deadhead_km=distance,
            finish_minutes=world.status.simulation_progress_minutes + duration,
            current_best_order_advantage=best_direct,
        )
        option.trace.update(
            {
                "pivot_online_probe": kind,
                "expected_gain": max(0.0, score),
                "payback_time_p50": duration + 180,
                "payback_time_p80": duration + 420,
            }
        )
        options.append(option)
    return options


def _cluster_targets(world: World, visible: list[NormalizedCargo], *, pickup: bool) -> list[tuple[float, float, float, str]]:
    ranked = sorted(
        visible,
        key=lambda cargo: cargo.price_yuan / max(1.0, cargo.cost_time_minutes / 60.0),
        reverse=True,
    )[:8]
    out: list[tuple[float, float, float, str]] = []
    for cargo in ranked:
        lat = cargo.start_lat if pickup else cargo.end_lat
        lng = cargo.start_lng if pickup else cargo.end_lng
        score = cargo.price_yuan / max(1.0, cargo.cost_time_minutes / 60.0)
        out.append((float(lat), float(lng), float(score), "pickup_cluster" if pickup else "dropoff_terminal"))
    return out
