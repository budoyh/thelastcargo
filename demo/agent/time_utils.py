"""Time helpers copied into the agent boundary; no runtime dependency on evaluator internals."""

from __future__ import annotations

from datetime import datetime, timedelta

SIMULATION_EPOCH = datetime(2026, 3, 1, 0, 0, 0)
WALL_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def wall_time_to_minutes(text: str | None) -> int | None:
    if text is None:
        return None
    try:
        dt = datetime.strptime(str(text).strip(), WALL_TIME_FORMAT)
    except ValueError:
        return None
    return int((dt - SIMULATION_EPOCH).total_seconds() // 60)


def minutes_to_wall_time(minutes: int) -> str:
    return (SIMULATION_EPOCH + timedelta(minutes=int(minutes))).strftime(WALL_TIME_FORMAT)


def parse_load_window(value: object) -> tuple[int, int] | None:
    if not isinstance(value, list) or len(value) != 2:
        return None
    start = wall_time_to_minutes(str(value[0]))
    end = wall_time_to_minutes(str(value[1]))
    if start is None or end is None or end < start:
        return None
    return start, end


def remaining_minutes(now_minutes: int, horizon_minutes: int) -> int:
    return max(0, int(horizon_minutes) - int(now_minutes))


def day_index(now_minutes: int) -> int:
    return max(0, int(now_minutes) // 1440)

