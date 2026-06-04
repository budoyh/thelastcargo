"""Future-safe abstract preference primitive registry for Pref-Forge.

The registry deliberately contains only generic monitor families. It does not
include public examples, place names, cargo labels, driver ids, cargo ids, or
coordinates.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PrimitiveSpec:
    family: str
    observable_event_types: tuple[str, ...]
    required_slots: tuple[str, ...]
    optional_slots: tuple[str, ...]
    aggregation_semantics: str
    polarity_semantics: tuple[str, ...]
    repair_action_types: tuple[str, ...]
    state_fields: tuple[str, ...]
    can_hard_block_conditions: tuple[str, ...]
    unknown_soft_fallback_conditions: tuple[str, ...]


def _spec(
    family: str,
    events: tuple[str, ...],
    required: tuple[str, ...],
    optional: tuple[str, ...],
    aggregation: str,
    polarity: tuple[str, ...],
    repair: tuple[str, ...],
    state: tuple[str, ...],
    hard_block: tuple[str, ...],
) -> PrimitiveSpec:
    return PrimitiveSpec(
        family=family,
        observable_event_types=events,
        required_slots=required,
        optional_slots=optional,
        aggregation_semantics=aggregation,
        polarity_semantics=polarity,
        repair_action_types=repair,
        state_fields=state,
        can_hard_block_conditions=hard_block,
        unknown_soft_fallback_conditions=(
            "missing_required_slot",
            "ambiguous_polarity",
            "ambiguous_counting_unit",
            "unverified_scorer_semantics",
            "unsupported_hidden_shape",
        ),
    )


PRIMITIVES: tuple[PrimitiveSpec, ...] = (
    _spec("CONTINUOUS_REST", ("wait", "active_interval"), ("duration_minutes",), ("time_window",), "per_day_max_continuous_wait", ("require",), ("wait",), ("daily_wait_intervals",), ("verified_duration_and_repairable",)),
    _spec("SCHEDULED_NO_MOVE_WINDOW", ("wait", "take_order", "reposition"), ("time_window",), ("date_window",), "interval_overlap", ("forbid", "require"), ("wait",), ("covered_windows",), ("verified_window_overlap",)),
    _spec("FULL_DAY_INACTIVE", ("wait", "take_order", "reposition"), ("day_count",), ("date_window",), "full_day_no_active_motion", ("require",), ("wait",), ("inactive_days",), ("only_when_full_day_remaining",)),
    _spec("NO_ORDER_DAY", ("take_order", "wait"), ("day_count",), ("date_window",), "day_with_zero_orders", ("require",), ("wait",), ("no_order_days",), ("only_order_count_matters",)),
    _spec("CARGO_ATTRIBUTE_AVOID", ("take_order", "query"), ("field_ref", "value_ref"), ("confidence",), "per_action", ("avoid", "forbid"), ("avoid_take",), ("matched_take_count",), ("high_confidence_visible_match",)),
    _spec("CARGO_ATTRIBUTE_REQUIRE_OR_TARGET", ("take_order", "query"), ("field_ref", "value_ref"), ("day_count",), "distinct_days_or_count", ("require", "prefer"), ("take_matching",), ("matched_days",), ("visible_matching_current_actionable",)),
    _spec("LOCATION_REGION_AVOID", ("take_order", "reposition", "wait"), ("region_ref",), ("radius_km",), "position_or_endpoint_relation", ("avoid", "forbid"), ("avoid_take",), ("region_hits",), ("verified_region_relation",)),
    _spec("LOCATION_REGION_REQUIRE", ("take_order", "reposition", "wait"), ("region_ref",), ("dwell_minutes", "day_count"), "visit_or_dwell", ("require", "prefer"), ("take_towards_target", "wait", "reposition"), ("region_visits",), ("executable_current_target",)),
    _spec("BOUNDARY_STAY_LIMIT", ("take_order", "reposition", "wait"), ("region_ref", "operator"), ("time_window",), "position_containment", ("require", "forbid"), ("avoid_take", "wait"), ("boundary_state",), ("verified_boundary_geometry",)),
    _spec("PICKUP_DEADHEAD_LIMIT", ("take_order",), ("distance_km",), ("operator",), "per_action", ("limit",), ("avoid_take",), ("pickup_deadhead_violations",), ("distance_metric_verified",)),
    _spec("HAUL_DISTANCE_LIMIT", ("take_order",), ("distance_km",), ("operator",), "per_action", ("limit",), ("avoid_take",), ("haul_distance_violations",), ("distance_metric_verified",)),
    _spec("CUMULATIVE_EMPTY_DISTANCE_BUDGET", ("take_order", "reposition"), ("distance_km",), ("date_window",), "cumulative_sum", ("limit",), ("avoid_take", "avoid_reposition"), ("empty_distance_total",), ("budget_near_exhausted",)),
    _spec("DAILY_ACTION_COUNT_LIMIT", ("take_order",), ("count",), ("operator",), "per_day_count", ("limit",), ("wait",), ("daily_order_counts",), ("verified_counting_unit",)),
    _spec("FIRST_EVENT_DEADLINE", ("take_order", "wait"), ("deadline_minutes",), ("event_type",), "first_event_per_day", ("require", "limit"), ("take_matching",), ("first_event_times",), ("deadline_before_action",)),
    _spec("DISTINCT_DAY_QUOTA", ("take_order", "wait"), ("day_count",), ("field_ref", "value_ref"), "distinct_days", ("require",), ("take_matching",), ("qualified_days",), ("visible_matching_current_actionable",)),
    _spec("DATE_LOCATION_DWELL", ("take_order", "reposition", "wait"), ("target_ref", "dwell_minutes"), ("date_window",), "target_dwell", ("require",), ("take_towards_target", "wait", "reposition"), ("dwell_progress",), ("executable_target_and_window",)),
    _spec("SEQUENCE_TASK", ("take_order", "reposition", "wait"), ("sequence_refs",), ("deadline_minutes", "dwell_minutes"), "ordered_progress", ("require",), ("take_towards_target", "wait", "reposition"), ("sequence_index",), ("current_step_executable",)),
    _spec("SPECIFIC_TARGET_EVENT", ("take_order", "reposition", "wait"), ("target_ref", "event_type"), ("deadline_minutes",), "once_if_failed", ("require",), ("take_towards_target", "wait", "reposition"), ("target_event_state",), ("event_target_verified",)),
    _spec("WORK_PATTERN_COMPOSITE", ("take_order", "reposition", "wait"), ("subrules",), ("date_window",), "composite_all", ("require", "limit"), ("wait", "take_matching", "avoid_take"), ("subrule_states",), ("all_subrules_verified",)),
    _spec("UNKNOWN_SOFT", ("take_order", "reposition", "wait", "query"), (), ("unresolved_reason",), "soft_risk_only", ("unknown",), ("none",), ("unknown_soft_count",), ()),
)


PRIMITIVE_BY_FAMILY: dict[str, PrimitiveSpec] = {item.family: item for item in PRIMITIVES}


def primitive_families() -> tuple[str, ...]:
    return tuple(item.family for item in PRIMITIVES)
