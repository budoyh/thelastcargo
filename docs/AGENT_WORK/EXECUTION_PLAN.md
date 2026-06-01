# CROWN-Delta MPC Execution Plan

## Success Criteria

- Primary: official-net improvement with scorer-delta evidence.
- Strong success requires all gates from `agent.md`, including 20260529 official_net at least 45000 and push to `origin/crown-delta-mpc`.
- Partial success requires official_net at least 20000, preference_penalty below 30000, positive macro completion evidence, clean audits, and 0509 sanity.
- Otherwise stop as `DO_NOT_SUBMIT_WITH_DELTA_EVIDENCE`.

## Work Order

1. Archive old report clutter and keep final `reports/` limited to five Delta-MPC files.
2. Reuse existing run outputs to build the baseline score table and confirm no double-count score proxy.
3. Implement cheap official-delta labeler for top regret intervals with explicit validity fields.
4. Implement Preference Automata interfaces and scorer-semantics adapter.
5. Add macro repair candidates and macro commitment to runtime.
6. Add unified top-5 action decomposition.
7. Run 20260529 31-day evaluation and trigger fallback if worse than rescue.
8. Run ablations and 20260509 sanity.
9. Run tests, compile, audit, round-bug check, Qwen smoke, hidden-style synthetic tests.
10. Generate final five reports, perform final reviewers, commit, and push.

## Keep/Kill Policy

- Keep a module only if it improves official net or closes a named official-delta regret without catastrophic 0509 regression.
- Disable terminal/ranker until official-net ablation proves positive.
- Disable high-confidence hard blocks unless scorer semantics adapter supports the automaton.
- Treat invalid replay labels as diagnostics only.

## Known Risks

- The best known public 20260529 offline repair frontier is below the strong target.
- Existing runtime variants have not proven stable above the partial threshold.
- Qwen availability may vary; deterministic fallback must remain legal but may not score well.
- Some official-delta labels may be replay approximations rather than exact official labels.

## Final Execution Status

- Steps 1-10 were executed for this branch.
- Terminal/ranker remains disabled because no official-net-positive ablation was found.
- High-lambda automata use remains disabled; automata stay available as diagnostic/soft state.
- The branch must not be submitted as a scoring success: 20260529 Delta-MPC runtime score is below rescue and below partial/strong thresholds.
