# v7 Hypotheses (Pre-Registered)

Pre-registration must be committed to git **before Phase 5 (benchmark run) begins**.
See `HYPOTHESIS.md` (v7 experiment root) for the full formal document.

**Critical:** Any change to hypotheses, thresholds, or test specifications after Phase 5
begins invalidates pre-registration and converts the result to exploratory.

---

## Pre-Registered Framework Predictions (Primary)

These two predictions are the minimum sufficient test of the convergent/divergent framework.
Both must hold for the framework to be prospectively confirmed.

**P1 — Divergent detection (ensemble wins):**
```
IDR: ensemble_3x > multiround_2r  [regular cases, n=120]
95% CI lower bound > 0  (one-sided bootstrap)
```
Rationale: independent redundancy with union pooling should find more issues than adversarial
exchange on divergent detection tasks, at matched 3× compute.

**P2 — Convergent judgment (multiround_2r wins):**
```
FVC_mixed: multiround_2r > ensemble_3x  [mixed cases, n=80]
95% CI lower bound > 0  (one-sided bootstrap)
```
Rationale: iterative adversarial exchange structurally enables recognizing empirical ambiguity
(the `empirical_test_agreed` verdict) better than independent redundancy.

**Interpretation rules:**
- Both P1 and P2 hold → framework confirmed
- Only P1 holds → ensemble advantage general; convergent task claim unsupported
- Only P2 holds → multiround_2r advantage at 3× is task-specific but detection claim fails
- Neither holds → framework not supported at matched compute

---

## H1a — Debate vs Baseline (Regular Cases)

**Test:** TOST equivalence test + standard two-sided bootstrap

```
FC: isolated_debate  vs  baseline  [regular cases, n=120]
Bootstrap 95% CI, two-sided
TOST equivalence bounds: ±0.05 FC (set before Phase 5)
```

**Equivalence verdict (H1a_tost_pass):** CI falls within [−0.05, +0.05] → formally equivalent.
**Non-equivalence verdict:** CI extends outside bounds → meaningful difference exists.

Note: TOST bounds must be committed to `HYPOTHESIS.md` before Phase 5. If pilot data
(Phase 3) suggests ±0.05 is inappropriate, revise **before** committing — not after.

---

## H2 — Ensemble vs Debate (Primary)

**Test:** Two-sided bootstrap

```
FC: ensemble_3x  vs  isolated_debate  [regular cases, n=120]
FVC_mixed: ensemble_3x  vs  isolated_debate  [mixed cases, n=80]
```

**PASS (ensemble wins):** ensemble_3x CI lower bound > 0 on FC (regular cases).
**INCONCLUSIVE:** CI spans zero.
**FAIL (debate wins):** debate_isolated CI lower bound > 0.

This is a two-dimension test: regular cases (primary) and mixed cases (secondary).
If ensemble wins regular but debate wins mixed — consistent with P1/P2 framework.

---

## H3 — multiround_2r vs isolated_debate on FVC_mixed

**Test:** One-sided bootstrap

```
FVC_mixed: multiround_2r  vs  isolated_debate  [mixed cases, n=80]
```

This addresses v6's structural gap: `isolated_debate` was the compute-matched debate control
in v6, but it structurally cannot produce `empirical_test_agreed` (neither agent sees the
other). `multiround_2r` provides the information-passing debate at 3×. H3 tests whether
information-passing is necessary for convergent judgment.

**PASS:** multiround_2r CI lower bound > 0 on FVC_mixed.

---

## Bootstrap Protocol

- All CIs: paired bootstrap, n=10,000, seed=42
- Report: point estimate + 95% CI for every hypothesis test
- Primary analysis: regular cases (n=120) for IDR/IDP/DRQ/FVC/FC
- Convergent analysis: mixed cases (n=80) for FVC_mixed
- Cross-stratum comparisons (RC vs synthetic subgroup) reported as secondary
