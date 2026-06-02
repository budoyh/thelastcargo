"""CROWN-Y Tournament Build switches and conservative constants."""

from __future__ import annotations

import os


def _float_env(name: str, default: float, lo: float, hi: float) -> float:
    try:
        value = float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, value))


def _int_env(name: str, default: int, lo: int, hi: int) -> int:
    try:
        value = int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, value))


SUBMIT_MODE = False

ENABLE_TIME_SHADOW = True
ENABLE_PREFERENCE_MONITOR = True
ENABLE_VISIBLE_TWO_HOP = True
ENABLE_RESOURCE_ENDGAME = True
ENABLE_SCOUT_THEN_DEEPEN = False
ENABLE_REPOSITION = False
ENABLE_LEARNED_RANKER = False
ENABLE_LLM_JUDGE = False
ENABLE_THREE_HOP = False
ENABLE_OPTION_ROLLOUT = False
OFFICIAL_ALLOW_ARBITRARY_COORD_QUERY = False
ENABLE_DESTINATION_SHADOW_QUERY = False

TRACE_LEVEL = "minimal" if SUBMIT_MODE else "full"
if SUBMIT_MODE:
    ENABLE_DESTINATION_SHADOW_QUERY = False

SIMULATION_DURATION_DAYS = 31
SIMULATION_HORIZON_MINUTES = SIMULATION_DURATION_DAYS * 24 * 60
REPOSITION_SPEED_KM_PER_HOUR = 60.0
DEFAULT_COST_PER_KM = 1.5

SCOUT_K = 50
DEEPEN_K = 120
LARGE_QUERY_K = 200
MAX_QUERY_K = 600

QUERY_BATCH_SIZE = 10
HIGH_QUERY_TIME_COST = 2.8
STRONG_ORDER_ADVANTAGE = 180.0
MIN_DEEPEN_SLACK_MINUTES = 60
ENOUGH_FEASIBLE_COUNT = 18

WAIT_MINUTES_DEFAULT = 45
WAIT_MINUTES_SHORT = 20
WAIT_MINUTES_ENDGAME = 30
MIN_WAIT_MINUTES = 5
MAX_WAIT_MINUTES = 180

GLOBAL_BASE_PRICE_PER_MIN = 0.35
MIN_PRODUCTIVE_TIME_PRICE = 0.05
MAX_PRODUCTIVE_TIME_PRICE = 2.2
ENDGAME_TIME_PRICE_CAP = 2.8
TOP1_SELF_OPPORTUNITY_DISCOUNT = 0.35
INFORMATION_OPTION_VALUE_CAP = 150.0
OPTIONALITY_LOSS_CAP = 260.0
TIME_SHADOW_MODE = "full"
TIME_PRICE_MULTIPLIER = _float_env("CROWN_Y_TIME_PRICE_MULT", 1.0, 0.6, 1.4)
GLOBAL_BASE_PRICE_PER_MIN *= TIME_PRICE_MULTIPLIER

TWO_HOP_FIRST_K = 60
TWO_HOP_SECOND_K = 12
TWO_HOP_DISCOUNT = 0.55

MAX_ENDGAME_INTENSITY = 0.95
ENDGAME_HIGH = 0.72

REPOSITION_PAYBACK_MULTIPLIER = 1.8
REPOSITION_PAYBACK_P50_MAX_MIN = 6 * 60
REPOSITION_PAYBACK_P80_MAX_MIN = 12 * 60
REPOSITION_MAX_DISTANCE_KM = 140.0
REPOSITION_MIN_DISTANCE_KM = 8.0
REPOSITION_STRONG_ORDER_THRESHOLD = 150.0

LEARNED_BLEND = 0.10
LEARNED_MAX_BLEND = 0.25
LEARNED_CAP = 120.0
LEARNED_OOD_SHRINK = 0.2

LLM_MAX_COMPILE_CALLS_PER_DRIVER = 128
LLM_MAX_JUDGE_CALLS_PER_DRIVER = 0
LLM_MAX_JUDGE_CALLS_PER_DAY = 0
LLM_MAX_LINKER_CALLS_TOTAL = _int_env("CROWN_GOLD_MAX_LINKER_CALLS_TOTAL", 4096, 1, 20000)
LLM_TIMEOUT_SECONDS = 120.0
LLM_MAX_OUTPUT_TOKENS = _int_env("CROWN_GOLD_LLM_MAX_OUTPUT_TOKENS", 4096, 512, 4096)

RESCUE_QUERY_K_DEFAULT = 120
RESCUE_QUERY_K_HIGH = 200
RESCUE_DIRECT_NET_FLOOR = 35.0
RESCUE_PROFIT_PER_HOUR_FLOOR = 18.0
RESCUE_NEGATIVE_HARD_BLOCK = -80.0
RESCUE_SOFT_RISK_CAP = 80.0
RESCUE_TIME_COST_CAP = 90.0
RESCUE_WAIT_PENALTY_STEP = 35.0
RESCUE_WAIT_MINUTES_DEFAULT = 150
RESCUE_FORCE_TAKE_AFTER_WAITS = 6
RESCUE_LOOP_BREAK_AFTER_WAITS = 3
RESCUE_MICRO_REPOSITION_MIN_KM = 5.0
RESCUE_MICRO_REPOSITION_MAX_KM = 30.0
RESCUE_MICRO_REPOSITION_TRIGGER_WAITS = 3
RESCUE_DAILY_REST_UNTIL_MINUTE = _int_env("CROWN_Y_REST_UNTIL_MINUTE", 9 * 60, 0, 12 * 60)
RESCUE_FULL_REST_PERIOD_DAYS = _int_env("CROWN_Y_FULL_REST_PERIOD_DAYS", 15, 0, 31)
RESCUE_MIN_REMOVE_SLACK_MINUTES = 60
ENABLE_RESCUE_SCORER = False
ENABLE_RESCUE_WAIT_PENALTY = False
ENABLE_RESCUE_MICRO_REPOSITION = False
ENABLE_RESCUE_PREFERENCE_SOFT = False
ENABLE_RESCUE_TWOHOP_LITE = False
ENABLE_RESCUE_TIME_SHADOW_LITE = False
ENABLE_RESCUE_REST_GUARD = False
ENABLE_QWEN_PREFERENCE_COMPILER = False
ENABLE_NEXT_MARGINAL_PREF = False
ENABLE_NEXT_DYNAMIC_QUERY_K = False
ENABLE_NEXT_NO_QUERY_REST_BLOCK = False
ENABLE_NEXT_OBSERVATION_REPOSITION = False
ENABLE_NEXT_PREFERENCE_STATE_MACHINE = False
ENABLE_PCE_REPAIR_FIRST = False
ENABLE_PTT_FIREWALL = False
ENABLE_PTT_LINKER = False
ENABLE_PTT_AUDITOR = False
ENABLE_GOLD_CONTRACT_MPC = False
ENABLE_LEGACY_RESCUE_QWEN = False
DISABLE_RUNTIME_QWEN = os.environ.get("CROWN_Y_DISABLE_RUNTIME_QWEN", "").strip() == "1"
PTT_MAX_AUDITOR_CALLS_TOTAL = _int_env("CROWN_GOLD_MAX_AUDITOR_CALLS_TOTAL", 4096, 1, 20000)
PTT_SOFT_RISK_MULTIPLIER = 0.45
PTT_MASSIVE_PENALTY_MULTIPLIER = 2.5
PTT_UNKNOWN_HIGH_PENALTY_SCALE = 1200.0
TRIDENT_STAGE = os.environ.get("CROWN_TRIDENT_STAGE", "").strip().lower()
TRIDENT_QWEN_AUDIT_SCALE = _float_env("CROWN_TRIDENT_QWEN_AUDIT_SCALE", 1.0, 0.0, 4.0)
TRIDENT_UNKNOWN_AUDIT_SOFT_RISK = _float_env("CROWN_TRIDENT_UNKNOWN_AUDIT_SOFT_RISK", 35.0, 0.0, 300.0)
ENABLE_EXACT_RBT = False
ENABLE_VISIBLE_GRAPH_MPC = False
EXACT_MPC_DEFAULT_ON = os.environ.get("CROWN_EXACT_ENABLE_VISIBLE_GRAPH_MPC", "").strip() == "1"
EXACT_QWEN_MIN_REAL_COMPILE = True
VISIBLE_GRAPH_ALPHA = _float_env("CROWN_TRIDENT_VISIBLE_GRAPH_ALPHA", 0.20, 0.0, 0.35)
VISIBLE_GRAPH_ALPHA_TEST_VALUES = (0.05, 0.10, 0.20, 0.35)
VISIBLE_GRAPH_BONUS_CAP = _float_env("CROWN_TRIDENT_VISIBLE_GRAPH_BONUS_CAP", 160.0, 0.0, 300.0)
VISIBLE_GRAPH_NEGATIVE_BONUS_CAP = _float_env("CROWN_TRIDENT_VISIBLE_GRAPH_NEGATIVE_BONUS_CAP", 120.0, 0.0, 300.0)
VISIBLE_GRAPH_CELL_DEGREES = _float_env("CROWN_TRIDENT_VISIBLE_GRAPH_CELL_DEGREES", 0.25, 0.05, 1.0)

_VARIANT = os.environ.get("CROWN_Y_VARIANT", "crown_trident_gold2").strip().lower()
RESCUE_VARIANT = _VARIANT
ENABLE_LEGACY_RESCUE_QWEN = _VARIANT in {"a6", "a7", "best_rescue"}
if _VARIANT in {"a", "baseline", "safe_greedy"}:
    ENABLE_TIME_SHADOW = False
    ENABLE_VISIBLE_TWO_HOP = False
    ENABLE_SCOUT_THEN_DEEPEN = False
    ENABLE_REPOSITION = False
    TIME_SHADOW_MODE = "baseline_profit_per_hour"
elif _VARIANT in {"b", "no_reposition"}:
    ENABLE_REPOSITION = False
elif _VARIANT in {"no_rollout", "rollout_off"}:
    ENABLE_VISIBLE_TWO_HOP = False
elif _VARIANT in {"no_time_shadow", "time_shadow_off"}:
    ENABLE_TIME_SHADOW = False
    TIME_SHADOW_MODE = "baseline_profit_per_hour"
elif _VARIANT in {"no_scout", "fixed_scout"}:
    ENABLE_SCOUT_THEN_DEEPEN = False
elif _VARIANT in {"c", "default", ""}:
    pass

if _VARIANT in {
    "fixed_k50_positive_net",
    "fixed_k100_profit_per_hour",
    "fixed_k200_direct_profit_with_slack",
    "simple_balanced_greedy",
    "safe_profit_greedy",
    "a0",
    "a1",
    "a2",
    "a3",
    "a4",
    "a5",
    "a6",
    "a7",
    "best_rescue",
    "money_greedy_no_pref",
    "strict_pref",
    "marginal_pref_only",
    "calendar_rest_only",
    "dynamic_query_k",
    "dynamic_query_reposition",
    "preference_state_machine",
    "next_best",
    "predicate_compiler_only",
    "predicate_vocab_linker",
    "predicate_repair_planner",
    "predicate_repair_verifier",
    "pce_repair_first",
    "pce_final",
    "delta_mpc",
    "delta_mpc_delta_only",
    "delta_mpc_macro",
    "delta_mpc_fallback",
    "preference_firewall_profit",
    "crown_exact_rbt_mpc",
    "crown_gold_contract_mpc",
    "crown_trident_gold2",
}:
    ENABLE_RESCUE_SCORER = True
    ENABLE_SCOUT_THEN_DEEPEN = False
    ENABLE_TIME_SHADOW = False
    ENABLE_VISIBLE_TWO_HOP = False
    ENABLE_RESOURCE_ENDGAME = False
    ENABLE_REPOSITION = False
    TIME_SHADOW_MODE = "rescue_lite"

if _VARIANT in {"a1", "a2", "a3", "a4", "a5", "a6", "a7", "best_rescue", "preference_firewall_profit", "crown_gold_contract_mpc", "crown_trident_gold2"}:
    ENABLE_RESCUE_WAIT_PENALTY = True
if _VARIANT in {"a2", "a3", "a4", "a5", "a6", "a7", "best_rescue", "preference_firewall_profit", "crown_gold_contract_mpc", "crown_trident_gold2"}:
    ENABLE_RESCUE_MICRO_REPOSITION = True
if _VARIANT in {"a3", "a4", "a5", "a6", "a7", "best_rescue", "preference_firewall_profit", "crown_gold_contract_mpc", "crown_trident_gold2"}:
    ENABLE_RESCUE_PREFERENCE_SOFT = True
if _VARIANT in {"a4", "a5", "a6", "a7", "best_rescue", "preference_firewall_profit", "crown_gold_contract_mpc", "crown_trident_gold2"}:
    ENABLE_RESCUE_TWOHOP_LITE = True
if _VARIANT in {"a5", "a6", "a7", "best_rescue", "preference_firewall_profit", "crown_gold_contract_mpc", "crown_trident_gold2"}:
    ENABLE_RESCUE_TIME_SHADOW_LITE = True
if _VARIANT in {"a6", "a7", "best_rescue", "preference_firewall_profit", "crown_gold_contract_mpc", "crown_trident_gold2"}:
    ENABLE_QWEN_PREFERENCE_COMPILER = True
if _VARIANT in {"a6", "a7", "best_rescue", "preference_firewall_profit", "crown_gold_contract_mpc", "crown_trident_gold2"}:
    ENABLE_RESCUE_REST_GUARD = True

if _VARIANT in {
    "money_greedy_no_pref",
    "strict_pref",
    "marginal_pref_only",
    "calendar_rest_only",
    "dynamic_query_k",
    "dynamic_query_reposition",
    "preference_state_machine",
    "next_best",
}:
    ENABLE_QWEN_PREFERENCE_COMPILER = True
    ENABLE_RESCUE_WAIT_PENALTY = True
    RESCUE_DIRECT_NET_FLOOR = 1.0
    RESCUE_PROFIT_PER_HOUR_FLOOR = 0.0
    RESCUE_QUERY_K_DEFAULT = 100

if _VARIANT in {"strict_pref", "next_best"}:
    ENABLE_RESCUE_PREFERENCE_SOFT = True
    ENABLE_RESCUE_REST_GUARD = True

if _VARIANT in {"marginal_pref_only", "dynamic_query_k", "dynamic_query_reposition"}:
    ENABLE_RESCUE_PREFERENCE_SOFT = True
    ENABLE_NEXT_MARGINAL_PREF = True

if _VARIANT in {"calendar_rest_only"}:
    ENABLE_RESCUE_REST_GUARD = True
    ENABLE_NEXT_NO_QUERY_REST_BLOCK = True

if _VARIANT in {"dynamic_query_k", "dynamic_query_reposition"}:
    ENABLE_NEXT_DYNAMIC_QUERY_K = True

if _VARIANT in {"dynamic_query_reposition"}:
    ENABLE_RESCUE_MICRO_REPOSITION = True
    ENABLE_NEXT_OBSERVATION_REPOSITION = True

if _VARIANT in {"preference_state_machine", "next_best"}:
    ENABLE_RESCUE_PREFERENCE_SOFT = True
    ENABLE_RESCUE_REST_GUARD = True
    ENABLE_NEXT_MARGINAL_PREF = True
    ENABLE_NEXT_DYNAMIC_QUERY_K = True
    ENABLE_NEXT_NO_QUERY_REST_BLOCK = True
    ENABLE_NEXT_OBSERVATION_REPOSITION = True
    ENABLE_NEXT_PREFERENCE_STATE_MACHINE = True
    ENABLE_RESCUE_MICRO_REPOSITION = True
    RESCUE_FULL_REST_PERIOD_DAYS = 10

if _VARIANT in {
    "predicate_compiler_only",
    "predicate_vocab_linker",
    "predicate_repair_planner",
    "predicate_repair_verifier",
    "pce_repair_first",
    "pce_final",
    "delta_mpc",
    "delta_mpc_delta_only",
    "delta_mpc_macro",
    "delta_mpc_fallback",
}:
    ENABLE_QWEN_PREFERENCE_COMPILER = True
    ENABLE_RESCUE_PREFERENCE_SOFT = True
    ENABLE_NEXT_MARGINAL_PREF = True
    ENABLE_NEXT_DYNAMIC_QUERY_K = True
    RESCUE_DIRECT_NET_FLOOR = 1.0
    RESCUE_PROFIT_PER_HOUR_FLOOR = 0.0
    RESCUE_QUERY_K_DEFAULT = 200

if _VARIANT in {"predicate_repair_planner", "predicate_repair_verifier", "pce_repair_first", "pce_final"}:
    ENABLE_RESCUE_REST_GUARD = True
    ENABLE_NEXT_NO_QUERY_REST_BLOCK = True
    ENABLE_NEXT_PREFERENCE_STATE_MACHINE = True
    ENABLE_PCE_REPAIR_FIRST = True

if _VARIANT in {"pce_repair_first", "pce_final"}:
    ENABLE_RESCUE_MICRO_REPOSITION = True
    ENABLE_NEXT_OBSERVATION_REPOSITION = True

if _VARIANT in {"delta_mpc", "delta_mpc_delta_only", "delta_mpc_macro", "delta_mpc_fallback"}:
    ENABLE_RESCUE_WAIT_PENALTY = True
    ENABLE_QWEN_PREFERENCE_COMPILER = True
    ENABLE_RESCUE_REST_GUARD = True
    ENABLE_NEXT_NO_QUERY_REST_BLOCK = True
    ENABLE_RESCUE_PREFERENCE_SOFT = True
    RESCUE_DIRECT_NET_FLOOR = 1.0
    RESCUE_PROFIT_PER_HOUR_FLOOR = 0.0
    RESCUE_DAILY_REST_UNTIL_MINUTE = _int_env("CROWN_Y_REST_UNTIL_MINUTE", 8 * 60, 0, 12 * 60)
    RESCUE_FULL_REST_PERIOD_DAYS = _int_env("CROWN_Y_FULL_REST_PERIOD_DAYS", 10, 0, 31)
if _VARIANT in {"delta_mpc", "delta_mpc_macro"}:
    ENABLE_NEXT_DYNAMIC_QUERY_K = True
    ENABLE_NEXT_PREFERENCE_STATE_MACHINE = True
    ENABLE_PCE_REPAIR_FIRST = True
    ENABLE_RESCUE_MICRO_REPOSITION = True
    ENABLE_NEXT_OBSERVATION_REPOSITION = True
if _VARIANT == "delta_mpc_delta_only":
    ENABLE_NEXT_DYNAMIC_QUERY_K = False
    ENABLE_NEXT_PREFERENCE_STATE_MACHINE = False
    ENABLE_PCE_REPAIR_FIRST = False
    ENABLE_RESCUE_MICRO_REPOSITION = False
if _VARIANT == "delta_mpc_fallback":
    ENABLE_NEXT_DYNAMIC_QUERY_K = False
    ENABLE_NEXT_PREFERENCE_STATE_MACHINE = False
    ENABLE_PCE_REPAIR_FIRST = False
    ENABLE_NEXT_MARGINAL_PREF = False
    ENABLE_RESCUE_MICRO_REPOSITION = True
    ENABLE_RESCUE_TWOHOP_LITE = True
    ENABLE_RESCUE_TIME_SHADOW_LITE = True
    RESCUE_QUERY_K_DEFAULT = 120
    RESCUE_DAILY_REST_UNTIL_MINUTE = _int_env("CROWN_Y_REST_UNTIL_MINUTE", 9 * 60, 0, 12 * 60)
    RESCUE_FULL_REST_PERIOD_DAYS = _int_env("CROWN_Y_FULL_REST_PERIOD_DAYS", 15, 0, 31)

if _VARIANT == "preference_firewall_profit":
    ENABLE_PTT_FIREWALL = True
    ENABLE_PTT_LINKER = True
    ENABLE_PTT_AUDITOR = True
    ENABLE_QWEN_PREFERENCE_COMPILER = True
    ENABLE_RESCUE_PREFERENCE_SOFT = True
    ENABLE_RESCUE_REST_GUARD = True
    ENABLE_NEXT_NO_QUERY_REST_BLOCK = True
    ENABLE_RESCUE_MICRO_REPOSITION = True
    ENABLE_RESCUE_TWOHOP_LITE = True
    ENABLE_RESCUE_TIME_SHADOW_LITE = True
    RESCUE_QUERY_K_DEFAULT = 120
    RESCUE_DIRECT_NET_FLOOR = 1.0
    RESCUE_PROFIT_PER_HOUR_FLOOR = 0.0
    RESCUE_DAILY_REST_UNTIL_MINUTE = _int_env("CROWN_Y_REST_UNTIL_MINUTE", 9 * 60, 0, 12 * 60)
    RESCUE_FULL_REST_PERIOD_DAYS = _int_env("CROWN_Y_FULL_REST_PERIOD_DAYS", 12, 0, 31)
if _VARIANT == "crown_exact_rbt_mpc":
    ENABLE_EXACT_RBT = True
    ENABLE_PTT_FIREWALL = False
    ENABLE_PTT_LINKER = True
    ENABLE_PTT_AUDITOR = False
    ENABLE_QWEN_PREFERENCE_COMPILER = True
    ENABLE_RESCUE_PREFERENCE_SOFT = True
    ENABLE_RESCUE_REST_GUARD = True
    ENABLE_NEXT_NO_QUERY_REST_BLOCK = False
    ENABLE_RESCUE_MICRO_REPOSITION = True
    ENABLE_RESCUE_TWOHOP_LITE = True
    ENABLE_RESCUE_TIME_SHADOW_LITE = True
    ENABLE_VISIBLE_GRAPH_MPC = EXACT_MPC_DEFAULT_ON
    RESCUE_QUERY_K_DEFAULT = 120
    RESCUE_DIRECT_NET_FLOOR = 1.0
    RESCUE_PROFIT_PER_HOUR_FLOOR = 0.0
    RESCUE_DAILY_REST_UNTIL_MINUTE = _int_env("CROWN_Y_REST_UNTIL_MINUTE", 9 * 60, 0, 12 * 60)
    RESCUE_FULL_REST_PERIOD_DAYS = _int_env("CROWN_Y_FULL_REST_PERIOD_DAYS", 15, 0, 31)
    RESCUE_VARIANT = "crown_exact_rbt_mpc"

if _VARIANT in {"crown_gold_contract_mpc", "crown_trident_gold2"}:
    ENABLE_GOLD_CONTRACT_MPC = True
    ENABLE_EXACT_RBT = True
    ENABLE_PTT_FIREWALL = os.environ.get("CROWN_GOLD_ENABLE_FIREWALL", "1").strip() != "0"
    ENABLE_PTT_LINKER = os.environ.get("CROWN_GOLD_ENABLE_LINKER", "1").strip() != "0"
    ENABLE_PTT_AUDITOR = os.environ.get("CROWN_GOLD_ENABLE_AUDITOR", "1").strip() != "0"
    ENABLE_QWEN_PREFERENCE_COMPILER = True
    ENABLE_RESCUE_PREFERENCE_SOFT = True
    ENABLE_RESCUE_REST_GUARD = True
    ENABLE_NEXT_PREFERENCE_STATE_MACHINE = os.environ.get("CROWN_GOLD_ENABLE_REPAIR", "0").strip() == "1"
    ENABLE_RESCUE_MICRO_REPOSITION = True
    ENABLE_RESCUE_TWOHOP_LITE = True
    ENABLE_RESCUE_TIME_SHADOW_LITE = True
    graph_env = "CROWN_TRIDENT_ENABLE_VISIBLE_GRAPH_MPC" if _VARIANT == "crown_trident_gold2" else "CROWN_GOLD_ENABLE_VISIBLE_GRAPH_MPC"
    query_env = "CROWN_TRIDENT_QUERY_K" if _VARIANT == "crown_trident_gold2" else "CROWN_GOLD_QUERY_K"
    direct_env = "CROWN_TRIDENT_DIRECT_NET_FLOOR" if _VARIANT == "crown_trident_gold2" else "CROWN_GOLD_DIRECT_NET_FLOOR"
    pph_env = "CROWN_TRIDENT_PROFIT_PER_HOUR_FLOOR" if _VARIANT == "crown_trident_gold2" else "CROWN_GOLD_PROFIT_PER_HOUR_FLOOR"
    ENABLE_VISIBLE_GRAPH_MPC = os.environ.get(graph_env, "0").strip() == "1"
    RESCUE_QUERY_K_DEFAULT = _int_env(query_env, 120, 50, 600)
    RESCUE_DIRECT_NET_FLOOR = _float_env(direct_env, 1.0, -200.0, 500.0)
    RESCUE_PROFIT_PER_HOUR_FLOOR = _float_env(pph_env, 0.0, -50.0, 200.0)
    RESCUE_DAILY_REST_UNTIL_MINUTE = _int_env("CROWN_Y_REST_UNTIL_MINUTE", 9 * 60, 0, 12 * 60)
    RESCUE_FULL_REST_PERIOD_DAYS = _int_env("CROWN_Y_FULL_REST_PERIOD_DAYS", 15, 0, 31)
    RESCUE_VARIANT = _VARIANT

if _VARIANT == "crown_trident_gold2":
    if TRIDENT_STAGE in {"b1", "compile_logging_only"}:
        ENABLE_PTT_FIREWALL = False
        ENABLE_PTT_LINKER = False
        ENABLE_PTT_AUDITOR = False
        ENABLE_VISIBLE_GRAPH_MPC = False
    elif TRIDENT_STAGE in {"b2", "monitor_no_score", "b6", "observed_vocab_linker_only"}:
        ENABLE_PTT_FIREWALL = False
        ENABLE_PTT_LINKER = True
        ENABLE_PTT_AUDITOR = False
        ENABLE_VISIBLE_GRAPH_MPC = False
    elif TRIDENT_STAGE in {"b3", "controller_soft_scoring", "b4", "verified_hard_firewall_only"}:
        ENABLE_PTT_FIREWALL = True
        ENABLE_PTT_LINKER = True
        ENABLE_PTT_AUDITOR = False
        ENABLE_VISIBLE_GRAPH_MPC = False
    elif TRIDENT_STAGE in {"b5", "qwen_auditor_nonzero_adjustment"}:
        ENABLE_PTT_FIREWALL = True
        ENABLE_PTT_LINKER = True
        ENABLE_PTT_AUDITOR = True
        ENABLE_VISIBLE_GRAPH_MPC = False
    elif TRIDENT_STAGE in {"b7", "opportunity_graph_only"}:
        ENABLE_PTT_FIREWALL = False
        ENABLE_PTT_LINKER = False
        ENABLE_PTT_AUDITOR = False
        ENABLE_VISIBLE_GRAPH_MPC = True
    elif TRIDENT_STAGE in {"b8", "opportunity_graph_plus_auditor"}:
        ENABLE_PTT_FIREWALL = True
        ENABLE_PTT_LINKER = True
        ENABLE_PTT_AUDITOR = True
        ENABLE_VISIBLE_GRAPH_MPC = True

if _VARIANT in {"best_rescue", "a7"}:
    RESCUE_QUERY_K_DEFAULT = 120
    RESCUE_DIRECT_NET_FLOOR = 1.0
    RESCUE_PROFIT_PER_HOUR_FLOOR = 0.0
elif _VARIANT == "fixed_k50_positive_net":
    RESCUE_QUERY_K_DEFAULT = 50
    RESCUE_DIRECT_NET_FLOOR = 1.0
    RESCUE_PROFIT_PER_HOUR_FLOOR = 0.0
elif _VARIANT == "fixed_k100_profit_per_hour":
    RESCUE_QUERY_K_DEFAULT = 100
    RESCUE_DIRECT_NET_FLOOR = 1.0
    RESCUE_PROFIT_PER_HOUR_FLOOR = 20.0
elif _VARIANT == "fixed_k200_direct_profit_with_slack":
    RESCUE_QUERY_K_DEFAULT = 200
    RESCUE_DIRECT_NET_FLOOR = 30.0
    RESCUE_PROFIT_PER_HOUR_FLOOR = 0.0
elif _VARIANT == "simple_balanced_greedy":
    RESCUE_QUERY_K_DEFAULT = 120
    RESCUE_DIRECT_NET_FLOOR = 20.0
    RESCUE_PROFIT_PER_HOUR_FLOOR = 10.0

if os.environ.get("CROWN_Y_ENABLE_REPOSITION", "").strip() == "1":
    ENABLE_REPOSITION = True
if os.environ.get("CROWN_Y_DISABLE_REPOSITION", "").strip() == "1":
    ENABLE_REPOSITION = False
if os.environ.get("CROWN_Y_ENABLE_SCOUT_THEN_DEEPEN", "").strip() == "1":
    ENABLE_SCOUT_THEN_DEEPEN = True
if os.environ.get("CROWN_Y_SUBMIT_MODE", "").strip() == "1":
    SUBMIT_MODE = True
    TRACE_LEVEL = "minimal"
    ENABLE_DESTINATION_SHADOW_QUERY = False

_TRIDENT_GRAPH_FLAG = os.environ.get("CROWN_TRIDENT_ENABLE_VISIBLE_GRAPH_MPC", "").strip()
if _TRIDENT_GRAPH_FLAG == "1":
    ENABLE_VISIBLE_GRAPH_MPC = True
elif _TRIDENT_GRAPH_FLAG == "0":
    ENABLE_VISIBLE_GRAPH_MPC = False
