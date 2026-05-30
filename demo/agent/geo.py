"""Geographic helpers kept local to the agent."""

from __future__ import annotations

import math


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_km = 6371.0
    p1 = math.radians(float(lat1))
    l1 = math.radians(float(lng1))
    p2 = math.radians(float(lat2))
    l2 = math.radians(float(lng2))
    dp = p2 - p1
    dl = l2 - l1
    h = math.sin(dp * 0.5) ** 2 + math.cos(p1) * math.cos(p2) * (math.sin(dl * 0.5) ** 2)
    h = min(1.0, max(0.0, h))
    return 2.0 * radius_km * math.asin(math.sqrt(h))


def distance_to_minutes(distance_km: float, speed_km_per_hour: float) -> int:
    if distance_km <= 0:
        return 1
    return max(1, int(math.ceil((float(distance_km) / float(speed_km_per_hour)) * 60.0)))


def pickup_minutes(distance_km: float, speed_km_per_hour: float) -> int:
    if distance_km <= 1e-6:
        return 0
    return distance_to_minutes(distance_km, speed_km_per_hour)

