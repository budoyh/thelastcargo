"""Preference debt accounting for current runtime contracts."""

from __future__ import annotations

from .. import preference_monitor
from ..schemas import CandidateOption, World


def attach_preference_debt(option: CandidateOption, world: World) -> dict[str, float]:
    option.pref_cert = preference_monitor.certify(option, world)
    violation = option.pref_cert.violation_debt if option.pref_cert else 0.0
    repair = option.pref_cert.repair_value if option.pref_cert else 0.0
    unknown = option.pref_cert.unknown_risk if option.pref_cert else 0.0
    return {
        "pivot_preference_debt": -float(violation),
        "pivot_preference_repair_credit": float(repair),
        "pivot_unknown_soft_risk": -float(unknown),
    }
