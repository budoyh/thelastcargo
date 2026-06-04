"""Report Qwen preference compiler evidence from rescue traces."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.score_rescue_metrics import summarize_run  # noqa: E402


def write_report(results_dir: Path, out: Path) -> dict[str, Any]:
    item = summarize_run(results_dir)
    qwen = item.get("qwen") if isinstance(item.get("qwen"), dict) else {}
    env_present = [name for name in ("DASHSCOPE_API_KEY", "BAILIAN_API_KEY", "ALIYUN_API_KEY") if os.environ.get(name)]
    compile_calls = int(qwen.get("compile_calls", 0) or 0)
    api_errors = int(qwen.get("api_error_count", 0) or 0)
    dummy_blocks = int(qwen.get("dummy_key_blocked_count", 0) or 0)
    if compile_calls > 0 and api_errors == 0 and dummy_blocks == 0:
        status = "ok"
    elif compile_calls > 0 and dummy_blocks == 0:
        status = "ok_with_fallbacks"
    else:
        status = "fallback_or_unavailable"
    payload = {
        "results_dir": str(results_dir),
        "status": status,
        "env_present_names": env_present,
        "qwen": qwen,
        "preferences_nonempty_count": qwen.get("preferences_nonempty_count", 0),
        "compile_calls": qwen.get("compile_calls", 0),
        "judge_calls": qwen.get("judge_calls", 0),
        "dummy_key_blocked_count": qwen.get("dummy_key_blocked_count", 0),
        "token_usage_total": qwen.get("token_usage_total", 0),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Qwen Preference Compile Report",
        "",
        f"- results_dir: `{results_dir}`",
        f"- status: `{status}`",
        f"- env_present_names: `{', '.join(env_present) if env_present else 'none'}`",
        f"- model_name: `{qwen.get('model_name', 'qwen3.5-flash')}`",
        f"- compile_calls: {qwen.get('compile_calls', 0)}",
        f"- judge_calls: {qwen.get('judge_calls', 0)}",
        f"- cache_hits / cache_misses: {qwen.get('cache_hits', 0)} / {qwen.get('cache_misses', 0)}",
        f"- fallback_unknown_count: {qwen.get('fallback_unknown_count', 0)}",
        f"- api_error_count: {qwen.get('api_error_count', 0)}",
        f"- dummy_key_blocked_count: {qwen.get('dummy_key_blocked_count', 0)}",
        f"- budget_blocked_count: {qwen.get('budget_blocked_count', 0)}",
        f"- token_usage_input/output/total: {qwen.get('token_usage_input', 0)} / {qwen.get('token_usage_output', 0)} / {qwen.get('token_usage_total', 0)}",
        "",
        "Compiler boundary: Qwen compiles runtime preferences into abstract DSL rules only. It does not emit or select actions; the runtime action remains deterministic and certificate-gated.",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(out), "status": status, "compile_calls": payload["compile_calls"]}, ensure_ascii=False))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=ROOT / "runs" / "latest_rescue")
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "qwen_preference_compile_report.md")
    args = parser.parse_args()
    write_report(args.results_dir.resolve(), args.out.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
