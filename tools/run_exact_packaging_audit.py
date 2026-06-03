"""Build and inspect a CROWN-EXACT package candidate."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--recommended", action="store_true")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    default_name = "crown_exact_rbt_mpc_submission.zip" if args.recommended else "crown_exact_NOT_RECOMMENDED_DO_NOT_SUBMIT.zip"
    out = args.out or ROOT / "runs" / "packages" / default_name
    build = subprocess.run(
        [sys.executable, "tools/build_submission_package.py", *(["--recommended"] if args.recommended else []), "--out", str(out)],
        cwd=str(ROOT),
        check=False,
    )
    inspect = subprocess.run([sys.executable, "tools/inspect_submission_package.py", str(out)], cwd=str(ROOT), check=False)
    return 0 if build.returncode == 0 and inspect.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
