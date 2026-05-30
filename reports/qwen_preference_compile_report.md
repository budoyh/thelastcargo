# Qwen Preference Compile Report

- results_dir: `C:\budostudy\only_for_codex\thelatstcargo\runs\latest_rescue`
- status: `ok`
- env_present_names: `DASHSCOPE_API_KEY`
- model_name: `qwen3.5-flash`
- compile_calls: 5
- judge_calls: 0
- cache_hits / cache_misses: 2 / 5
- fallback_unknown_count: 0
- api_error_count: 0
- dummy_key_blocked_count: 0
- budget_blocked_count: 0
- token_usage_input/output/total: 1848 / 29781 / 31629

Compiler boundary: Qwen compiles runtime preferences into abstract DSL rules only. It does not emit or select actions; the runtime action remains deterministic and certificate-gated.
