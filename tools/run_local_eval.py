"""Run local simulation and income calculation with a deterministic agent."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], cwd: Path, env: dict[str, str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=str(cwd), env=env, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=ROOT / "demo" / "server" / "data")
    parser.add_argument("--results-dir", type=Path, default=ROOT / "runs" / "latest")
    parser.add_argument("--simulation-days", type=int, default=31)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--variant", type=str, default="")
    parser.add_argument("--skip-income", action="store_true")
    args = parser.parse_args()

    env = os.environ.copy()
    env.setdefault("DASHSCOPE_API_KEY", "local-dummy-key-not-used")
    if args.variant:
        env["CROWN_Y_VARIANT"] = args.variant
    args.results_dir.mkdir(parents=True, exist_ok=True)
    server_cmd = [
        sys.executable,
        "main.py",
        "--agent-dir",
        str(ROOT / "demo" / "agent"),
        "--data-dir",
        str(args.data_dir.resolve()),
        "--results-dir",
        str(args.results_dir.resolve()),
        "--simulation-days",
        str(args.simulation_days),
    ]
    if args.max_steps is not None:
        server_cmd.extend(["--max-steps", str(args.max_steps)])
    run(server_cmd, ROOT / "demo" / "server", env)
    if not args.skip_income:
        run(
            [
                sys.executable,
                "calc_monthly_income.py",
                "--project-root",
                str(ROOT / "demo"),
                "--results-dir",
                str(args.results_dir.resolve()),
                "--data-dir",
                str(args.data_dir.resolve()),
            ],
            ROOT / "demo",
            env,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
