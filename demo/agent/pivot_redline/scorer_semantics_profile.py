"""Runtime semantic profile container."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticProfile:
    name: str = "default_unknown_soft"
    hard_blocks_verified: bool = False
    massive_penalty_verified: bool = False

    def payload(self) -> dict[str, object]:
        return {
            "name": self.name,
            "hard_blocks_verified": self.hard_blocks_verified,
            "massive_penalty_verified": self.massive_penalty_verified,
        }
