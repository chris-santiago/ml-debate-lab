# v5 Weakness Mitigations

Per-journal-post-mortem mapping: failure mode → specific v6 design decision that prevents recurrence.

| PM | Hash | Failure mode | v6 Mitigation |
|---|---|---|---|
| 1 | `45eee14b` | Orchestrator `issues_found` literal match contaminated IDR scoring | GPT-4o semantic scoring from `critic_raw`; smoke literal match sandboxed to `gate_pass` only |
| 2 | `bc3a08d0` | Closed-loop confound: Claude scored Claude outputs (cross-vendor IDR delta = −0.77) | GPT-4o primary scorer for IDR/IDP/ETD; Claude secondary for H5 confound quantification only |
| 3 | `358b7a5a` | Same-model benchmark calibration: `proxy_mean` didn't predict rubric performance (Spearman ρ = +0.046) | Difficulty from Phase 3 pilot (GPT-4o scorer); `proxy_mean` stored for traceability, NOT used for gating |
| 4 | `fee829a4` | H1 threshold (+0.10) exceeded total available headroom (~0.05) | Dynamic threshold: `max(0.03, min(0.10, (1 − pilot_fc_mean) × 0.5))`; hard stop if `pilot_fc_mean ≥ 0.80` |
| 5 | `3363672c` | Majority-vote IDR suppressed ensemble recall (0.77 vs 0.87 union) | Union IDR for ensemble (any-assessor-found); majority-vote for verdict only |

---

## Explicit Constraint

`_pipeline.proxy_mean` is **NOT** an input to `select_cases.py`. The Stage 5 smoke test role
is structural validation (`gate_pass`) only.

---

## PM Class Note

The `stage3_mixed_assembler.md` `acceptable_resolutions` bug (fixed in Phase 0) is structurally
identical to PM1: an upstream artifact silently overrides the scoring engine's intended behavior,
making a primary hypothesis untestable with no runtime error. Spec-implementation divergence in
prompt templates is the primary recurrence vector. The verification checklist grep item exists
to catch future instances.
