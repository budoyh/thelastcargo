"""Small macro commitment state for pivot decisions."""

from __future__ import annotations

from dataclasses import dataclass

from ..schemas import CandidateOption


@dataclass
class PivotMacroStats:
    started: int = 0
    completed: int = 0
    aborted: int = 0

    def payload(self) -> dict[str, int]:
        return {"started": self.started, "completed": self.completed, "aborted": self.aborted}


def mark_if_macro(option: CandidateOption, stats: PivotMacroStats) -> None:
    if option.action_type == "wait" and option.duration_minutes >= 120:
        option.trace["pivot_macro_type"] = "long_wait_window"
        option.score_components["pivot_macro_commitment"] = 0.0
        stats.started += 1
