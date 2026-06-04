"""Legal online probe accounting for reposition candidates."""

from __future__ import annotations

from ..schemas import CandidateOption


def probe_value(option: CandidateOption) -> float:
    if option.action_type != "reposition":
        return 0.0
    expected = float(option.trace.get("expected_gain", 0.0) or 0.0)
    cost = abs(float(option.direct_money))
    return round(max(0.0, expected * 0.15 - cost), 6)
