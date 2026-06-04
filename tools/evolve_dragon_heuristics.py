"""Create restricted Dragon-Orca heuristic evolution recipes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import dragon_orca_common as common  # noqa: E402


def recipe(gen: int, idx: int) -> dict[str, object]:
    return {
        "generation": gen,
        "recipe_id": f"dragon_gen{gen}_{idx:02d}",
        "money_score_weights": {"direct": round(1.2 + 0.1 * idx, 3), "profit_per_hour": round(5.5 + 0.4 * gen, 3)},
        "shield_cost_weights": {"debt": round(0.25 + 0.05 * idx, 3), "unknown_soft_cap": 220},
        "debt_shadow_curve": {"cap_discount": 0.5, "already_failed_discount": 0.45},
        "value_model_blend": round(0.05 * gen, 3),
        "query_policy": {"k": [120, 200, 300, 600][idx % 4], "cost_weight": 0.25},
        "wait_policy": {"bounded_rest": True, "max_repair_wait_per_day": 120},
        "reposition_policy": {"current_visible_only": True, "max_distance_km": 80},
        "beam_depth": min(3, 1 + gen),
        "beam_width": 0 if gen == 0 else 2 + idx % 2,
        "month_end_policy": {"lockup_weight": 3 * gen, "last_days": 5},
        "unknown_soft_policy": {"hard_block_high_gross": False},
        "export_policy": "generic_parameters_only_no_ids_no_places_no_coordinates_no_future_cargo",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generations", type=int, default=3)
    parser.add_argument("--per-generation", type=int, default=8)
    args = parser.parse_args()
    common.ensure_dirs()
    out = common.EVOLUTION / "dragon_heuristics.jsonl"
    count = 0
    with out.open("w", encoding="utf-8") as handle:
        for gen in range(1, args.generations + 1):
            for idx in range(args.per_generation):
                handle.write(json.dumps(recipe(gen, idx), sort_keys=True) + "\n")
                count += 1
    common.append_work_log(f"dragon heuristic evolution recipes={count} out={out}")
    print({"recipes": count, "out": str(out)})
    return 0 if count else 1


if __name__ == "__main__":
    raise SystemExit(main())
