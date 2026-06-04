"""Offline full-information preference-aware oracle for CROWN-PCE."""

from __future__ import annotations

import json

from pce_oracle_engine import command_parser, run_greedy_oracle


def main() -> int:
    parser = command_parser("Run the full-information oracle.")
    args = parser.parse_args()
    results_dir = args.results_dir or (args.runs_root / "20260529" / "full_info_oracle")
    payload = run_greedy_oracle(
        data_dir=args.data_dir,
        results_dir=results_dir,
        variant=args.variant or "full_info_oracle",
        visibility_k=None,
        mode="full_info",
        max_candidates=args.max_candidates,
        max_steps=args.max_steps,
    )
    print(json.dumps({k: v for k, v in payload.items() if k != "score_curve"}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
