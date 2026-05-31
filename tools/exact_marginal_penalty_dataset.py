"""Build offline marginal preference labels for CROWN-PCE.

Rows are redacted and full-history based unless explicitly marked otherwise.
"""

from __future__ import annotations

import json

from pce_oracle_engine import REPORTS, build_predicate_dataset, command_parser


def main() -> int:
    parser = command_parser("Build the PCE predicate evaluation dataset.")
    parser.add_argument("--max-rows", type=int, default=400)
    args = parser.parse_args()
    output = args.output_dir / "predicate_eval.csv"
    metrics = build_predicate_dataset(runs_root=args.runs_root, output_path=output, max_rows=args.max_rows)
    if not output.is_file() and args.output_dir != REPORTS:
        metrics = build_predicate_dataset(runs_root=args.runs_root, output_path=REPORTS / "predicate_eval.csv", max_rows=args.max_rows)
    print(json.dumps({"output": str(output), "metrics": metrics}, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
