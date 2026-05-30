"""Smoke-test Qwen preference compiler without printing secrets."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo"
if str(DEMO) not in sys.path:
    sys.path.insert(0, str(DEMO))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent import qwen_preference_compiler  # noqa: E402


class SmokeApi:
    def model_chat_completion(self, payload):
        return {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "rules": [
                                    {
                                        "rule_id": "r0",
                                        "kind": "unknown",
                                        "scope": "whole_period",
                                        "condition": {},
                                        "repairability": "always_soft",
                                        "reward_or_penalty": {"amount": 100, "cap": None, "direction": "penalty"},
                                        "evidence": "abstract preference",
                                        "confidence": 0.4,
                                    }
                                ]
                            }
                        )
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 8, "total_tokens": 18},
        }


def main() -> int:
    env_names = [name for name in ("DASHSCOPE_API_KEY", "BAILIAN_API_KEY", "ALIYUN_API_KEY") if os.environ.get(name)]
    rules = qwen_preference_compiler.compile_with_qwen(
        api=SmokeApi(),
        pref_hash="smoke",
        preferences=({"content": "abstract runtime preference", "penalty_amount": 100, "penalty_cap": None},),
        fallback_amounts=[{"amount": 100.0, "cap": None, "direction": "penalty"}],
    )
    payload = qwen_preference_compiler.stats_payload()
    payload["env_present_names"] = env_names
    payload["rules_returned"] = 0 if rules is None else len(rules)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if rules else 1


if __name__ == "__main__":
    raise SystemExit(main())
