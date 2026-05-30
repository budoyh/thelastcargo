"""P2 trace trainer stub guarded by module switches."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    out = ROOT / "reports" / "counterfactual_trace_trainer.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "status": "disabled",
                "reason": "P2 trainer requires stable v1 ablation before producing deployable weights",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

