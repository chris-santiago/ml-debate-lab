# Benchmark Cases

## Reconciled Position

v7 has 280 cases across 3 strata. Approximately 40 are defense cases (derived from "4 conditions × 40 cases × 3 runs = 480 defense evaluations" in the v7 design). v8 uses v7 as the starting benchmark — not a full regeneration.

Two pre-run gates before any case is used in an evaluation:

1. **Ground truth audit** — are the defense cases actually sound?
2. **Taxonomy coverage check** — does v7 cover the flaw categories at adequate depth?

"Designed to be sound" is not "verified to be sound." Fix or replace bad cases. Do not regenerate everything.

---

## Gate 1 — Ground Truth Audit

**Scope:** All defense cases (~40). Defense cases are the highest-risk for label error — a mislabeled defense case (contains a real flaw but labeled sound) directly contaminates DER.

**Process:**
1. Read each defense case: hypothesis, PoC code, and any design rationale
2. For each case, ask: is there any genuine methodology flaw that a careful ML engineer would flag?
3. Label: CONFIRMED SOUND / UNCERTAIN / HAS REAL FLAW
4. For UNCERTAIN: get a second opinion (either a different human or a capable model not in the pool)
5. For HAS REAL FLAW: either fix the case (correct the methodology) or replace with a freshly generated defense case
6. Document all changes in a case audit log

**Acceptable outcome:** All defense cases confirmed sound or replaced. No cases labeled "uncertain" entering the benchmark.

---

## Gate 2 — Taxonomy Coverage Check

**The 16 flaw categories:**

Regular cases (9 types):
1. Synthetic data assumptions that don't hold in production
2. Evaluation design choices that inflate performance
3. Missing baselines or comparisons
4. Implicit distributional assumptions
5. Signal leakage between train and evaluation sets
6. Failure modes under distribution shift
7. Metric choice limitations
8. Silent misconfiguration (plausible-looking results, wrong behavior)
9. Unverified prerequisite assumptions

Mixed/ambiguous cases (6 types):
1. Flaw present but significance genuinely uncertain
2. Flaw present but fixable without invalidating hypothesis
3. Design choice unconventional but defensible
4. Ambiguous evidence (could support hypothesis or not)
5. Flaw conditional on deployment context (unknown)
6. Flaw real but below experiment threshold

Defense cases (1 type):
- Sound methodology that should be exonerated

**Coverage target:** ≥5 cases per category minimum; ≥10 preferred for reliable detection estimates.

**Process:** Map each v7 case to its primary flaw category. Flag any category with <5 cases. Generate targeted replacements for thin categories only — not a full regeneration.

---

## Canary Set Composition

**Size:** 40 cases (20 defense / 10 regular / 10 mixed)

The 10/10/10 split from the initial design was changed to 20/10/10. Reasons:
- DER on defense cases is the primary metric; n=10 produces unacceptably high variance
- 20 defense cases reduces SE by ~30% (from ~0.10 to ~0.07 at p=0.30)
- The canary is where most iteration happens — defense-case variance is the biggest noise source

**Selection criteria:**
- Defense cases: stratified by complexity (easy / medium / hard to exonerate). Do not select only easy cases — canary must stress-test the intervention.
- Regular cases: one per major flaw category where possible (coverage over randomness)
- Mixed cases: select the most ambiguous cases from the v7 benchmark (highest inter-annotator disagreement if available)

**Canary is drawn once and held constant.** Do not re-draw between iterations. The canary cases are fixed; only the prompts change.

---

## Sizing Reference

For the model randomization experiment (full benchmark, not just prompt iteration):

| Component | Target | Basis |
|---|---|---|
| Defense cases | 30-40 | ~40 in v7, satisfies requirement |
| Regular cases per flaw type | ≥10 | 9 types × 10 = 90 cases minimum |
| Mixed cases per ambiguity type | ≥10 | 6 types × 10 = 60 cases minimum |
| Total | 180-200 | v7's 280 likely exceeds this |
| Runs per case | 3 | Random model draws |
| Total evaluations | ~540-600 | vs. v7's 3,360 (4 conditions) |

v7's 280 cases likely satisfies the sizing requirement — the audit and coverage check will confirm. If not, targeted generation for thin categories.
