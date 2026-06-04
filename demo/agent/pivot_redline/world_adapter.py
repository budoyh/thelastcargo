"""Runtime-only world and query helpers for Pivot-Redline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PivotQueryPlan:
    kind: str
    k: int
    reason: str


def query_here(api: Any, driver_id: str, world: Any, k: int) -> list[dict[str, Any]]:
    if k <= 0:
        return []
    response = api.query_cargo(
        driver_id=driver_id,
        latitude=world.status.current_lat,
        longitude=world.status.current_lng,
        k=int(k),
    )
    items = response.get("items", [])
    return items if isinstance(items, list) else []
