"""Offline online-visibility oracle for CROWN-PCE."""

from __future__ import annotations

import json

from pce_oracle_engine import command_parser, run_greedy_oracle


def main() -> int:
    parser = command_parser("Run the online-visibility oracle.")
    parser.set_defaults(k=300)
    args = parser.parse_args()
    k = int(args.k or 300)
    results_dir = args.results_dir or (args.runs_root / "20260529" / f"visibility_k{k}_oracle")
    payload = run_greedy_oracle(
        data_dir=args.data_dir,
        results_dir=results_dir,
        variant=args.variant or f"visibility_k{k}_oracle",
        visibility_k=k,
        mode="repair",
        max_candidates=args.max_candidates,
        max_steps=args.max_steps,
    )
    payload["visibility_validation"] = "approximate_current_online_nearest_k_with_query_time_cost"
    print(json.dumps({k: v for k, v in payload.items() if k != "score_curve"}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
