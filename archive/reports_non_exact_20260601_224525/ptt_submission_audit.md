# PTT Submission Audit

## Gate Status
- synthetic_t01_t18_pass: PASS
- eval_20260529_present: PASS
- eval_20260509_present: PASS
- score_0529_net_above_rescue: FAIL
- score_0529_penalty_below_rescue: FAIL
- score_0529_gross_not_collapsed: FAIL
- zero_0529_failures: PASS
- zero_0529_illegal_or_rejected: PASS
- qwen_ptt_compile_called: FAIL
- linker_called_when_required: PASS
- macro_completed: PASS
- eval_0509_no_catastrophic_failure: PASS
- default_variant_package_ok: PASS
- package_shape_ok: PASS

## Package
- path: `C:\budostudy\only_for_codex\thelatstcargo\runs\packages\crown_ptt_NOT_RECOMMENDED_DO_NOT_SUBMIT.zip`
- sha256: `b7ae1e1bf748039c51c9d30232e800b1e4af3e85a494e58080e0412852a62d64`
- size_bytes: 76165
- recommended_flag: False
- default_variant: `preference_firewall_profit`
- inspection_root_demo_only: True
- inspection_disallowed_entries: 0

## Reviewer Checks
- Plato read-only reviewer: flagged default fallback, missing PTT controllers/firewall/linker, and trace raw-id risk before this patch set.
- Huygens read-only reviewer: flagged old generic compiler, missing deterministic controller interface, missing action firewall, and non-PTT package defaults before this patch set.
- Final simulated audit scopes: prompt adherence, compliance/future-info, PTT semantic, controller/firewall, runtime score, packaging.
