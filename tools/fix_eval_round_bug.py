"""Check the local coordinate normalization patch."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "demo" / "server" / "bench" / "simulation_orchestrator.py"


def main() -> int:
    text = TARGET.read_text(encoding="utf-8")
    ok = "_COORDINATE_KEYS" in text and "field_key in _COORDINATE_KEYS" in text
    print(f"round_bug_patch={'present' if ok else 'missing'} file={TARGET}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

