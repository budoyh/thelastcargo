"""Audit that pivot variants use the independent PivotRedlinePlanner path."""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import pivot_redline_common as common  # noqa: E402


def _call_name(node: ast.Call) -> str:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        base = _attr_name(func.value)
        return f"{base}.{func.attr}" if base else func.attr
    return ""


def _attr_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _attr_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def _find_decide_func(tree: ast.Module) -> ast.FunctionDef | None:
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != "ModelDecisionService":
            continue
        for item in node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "decide":
                return item
    return None


def _pivot_branch_statements(decide: ast.FunctionDef) -> list[ast.stmt]:
    for stmt in decide.body:
        if not isinstance(stmt, ast.Try):
            continue
        for inner in stmt.body:
            if not isinstance(inner, ast.If):
                continue
            condition = ast.unparse(inner.test) if hasattr(ast, "unparse") else ""
            if "IS_PIVOT_REDLINE" in condition:
                return inner.body
    return []


def _count_calls(nodes: list[ast.AST]) -> dict[str, int]:
    counts = {
        "_decide_rescue_call_count": 0,
        "rescue_scorer_score_call_count": 0,
        "rescue_scorer_choose_call_count": 0,
        "pivot_decide_call_count": 0,
    }
    for node in nodes:
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            name = _call_name(child)
            if name.endswith("._decide_rescue") or name == "self._decide_rescue":
                counts["_decide_rescue_call_count"] += 1
            if name in {"rescue_scorer.score", "rescue_scorer.score_options"}:
                counts["rescue_scorer_score_call_count"] += 1
            if name == "rescue_scorer.choose":
                counts["rescue_scorer_choose_call_count"] += 1
            if name.endswith("PivotRedlinePlanner.decide") or name.endswith(".decide"):
                text = ast.unparse(child) if hasattr(ast, "unparse") else name
                if "pivot_planner" in text or "PivotRedlinePlanner" in text:
                    counts["pivot_decide_call_count"] += 1
    return counts


def _scan_pivot_package() -> list[str]:
    failures: list[str] = []
    if not common.PIVOT_AGENT.exists():
        return ["missing demo/agent/pivot_redline package"]
    for path in sorted(common.PIVOT_AGENT.glob("*.py")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "rescue_scorer" in text and path.name not in {"b0_shadow.py"}:
            failures.append(f"{path.relative_to(ROOT)} imports or references rescue_scorer")
        if "_decide_rescue" in text:
            failures.append(f"{path.relative_to(ROOT)} references _decide_rescue")
        if "reports/" in text or "runs/" in text or "archive/" in text:
            failures.append(f"{path.relative_to(ROOT)} references offline/report artifacts")
    return failures


def audit(variant: str) -> dict[str, Any]:
    service = ROOT / "demo" / "agent" / "model_decision_service.py"
    tree = ast.parse(service.read_text(encoding="utf-8"))
    decide = _find_decide_func(tree)
    failures: list[str] = []
    if decide is None:
        failures.append("ModelDecisionService.decide missing")
        branch: list[ast.stmt] = []
    else:
        branch = _pivot_branch_statements(decide)
        if not branch:
            failures.append("decide has no IS_PIVOT_REDLINE branch")
    counts = _count_calls(branch)
    failures.extend(_scan_pivot_package())
    payload: dict[str, Any] = {
        "variant": variant,
        "service_file": str(service.relative_to(ROOT)).replace("\\", "/"),
        **counts,
        "failures": failures,
        "status": "PASS" if not failures and counts["pivot_decide_call_count"] > 0 and counts["_decide_rescue_call_count"] == 0 and counts["rescue_scorer_score_call_count"] == 0 and counts["rescue_scorer_choose_call_count"] == 0 else "FAIL",
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", required=True)
    parser.add_argument("--fail-on-rescue-path", action="store_true")
    args = parser.parse_args()
    payload = audit(args.variant)
    common.RUNTIME_PATH_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    common.RUNTIME_PATH_AUDIT.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(payload)
    return 1 if args.fail_on_rescue_path and payload["status"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
