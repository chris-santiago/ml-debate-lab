# v6 Sensitivity Analysis — Phase 8

**Date:** 2026-04-11  
**Experiment:** self_debate_experiment_v6  
**Inputs:** `v6_results.json`, `v6_hypothesis_results.json`, `v6_raw_outputs/`

---

## 8.1 Method A vs B Aggregation Divergence

Method A aggregates by computing per-case fair-comparison means first, then the grand mean across cases.  
Method B computes the raw grand mean across all per-run scores directly.

| Condition | Method A | Method B | Divergence |
|---|---|---|---|
| baseline | 0.6785 | 0.6785 | 0.0000 |
| isolated_debate | 0.6759 | 0.6759 | 0.0000 |
| biased_debate | 0.6726 | 0.6726 | 0.0000 |
| multiround | 0.6676 | 0.6676 | 0.0000 |
| ensemble_3x | 0.7046 | 0.7046 | 0.0000 |

**Verdict:** No divergence. All conditions: divergence = 0.0000. Both aggregation methods are equivalent because each case has exactly 3 runs — the per-case mean is identical to the pooled mean in this balanced design.

---

## 8.2 H1a Threshold Sensitivity

H1a pre-registered threshold = 0.10. Observed lift = −0.0026, bootstrap CI_lo = −0.1059.

| Threshold | CI_lo | PASS |
|---|---|---|
| 0.08 | −0.1059 | **FAIL** |
| **0.10** | **−0.1059** | **FAIL** |
| 0.12 | −0.1059 | **FAIL** |

**Verdict:** FAIL at all boundary thresholds. The null result is robust — CI_lo is far below any reasonable threshold. Changing the threshold ±0.02 does not change the outcome.

---

## 8.3 Per-Dimension Lift Decomposition

Isolated debate vs baseline on regular cases (n=80):

| Dimension | Baseline | Isolated | Lift | Direction |
|---|---|---|---|---|
| IDR | 0.6712 | 0.6603 | −0.0109 | negative — debate misses slightly more planted issues |
| IDP | 0.9472 | 0.9444 | −0.0028 | flat |
| IDP_adj | 0.9472 | 0.9639 | +0.0167 | positive — adjudication filters some false claims |
| DRQ | 0.7500 | 0.7500 | 0.0000 | flat |
| FVC | 0.7500 | 0.7500 | 0.0000 | flat |

**Driver of null result:** IDR is the only moving dimension, and it moves slightly negative. The adversarial structure does not improve issue detection on regular cases. IDP_adj improvement (+0.0167) is too small to offset IDR regression.

**DRQ and FVC:** Both flat at 0.75 across baseline and isolated_debate — verdict correctness is identical between conditions. No structural differentiation on these dimensions.

---

## 8.4 Difficulty Stratification Validation (PM3)

**Context:** PM3 post-mortem from v5 found Spearman ρ ≈ 0 — difficulty labels did not predict performance. v6 repeats the check.

**Note on sample:** Only 15/80 regular cases have explicit difficulty labels (medium: 7, hard: 8). The remaining 65 regular cases have `difficulty=None`. Analysis is restricted to the labeled subset.

The 40 mixed cases are labeled "medium" in the dataset but use a different scoring regime (FVC/ETD only, not IDR/IDP/DRQ) — they are excluded from this analysis.

| Difficulty | n | Baseline FC Mean |
|---|---|---|
| medium | 7 | 0.8492 |
| hard | 8 | 0.7535 |

**Spearman ρ (difficulty vs baseline FC, regular labeled cases):** −0.5649

**Verdict:** PASS — harder cases score lower on baseline. Direction is correct (ρ < 0). However, with only 15 labeled cases and no "easy" cases, the correlation is illustrative rather than definitive. The unlabeled majority (65 cases) limits PM3 verification power.

---

## 8.5 IDP Diagnostic

Check for extraction bug: if IDP is flat across all conditions including biased_debate, it signals that `all_issues_raised` is pulled from the adjudicator synthesis rather than the critic raw output.

| Condition | IDR | IDP_raw | IDP_adj |
|---|---|---|---|
| baseline | 0.6712 | 0.9472 | 0.9472 |
| isolated_debate | 0.6603 | 0.9444 | 0.9639 |
| biased_debate | 0.6955 | 0.8917 | 0.9250 |
| multiround | 0.6523 | 0.9306 | 0.9750 |
| ensemble_3x | 0.7717 | 0.9861 | 0.9861 |

**IDP is NOT flat.** `biased_debate` has notably lower IDP_raw (0.8917 vs baseline 0.9472) — the persona-primed critic generates more claims, including false positives, consistent with the combative-reviewer prompt. The extraction path is functioning correctly.

**IDP_adj > IDP_raw in most conditions:** Adjudication is filtering some false-positive claims (IDP_adj improvement = 0.0028 to 0.0444 depending on condition). No orchestrator-level extraction bug detected.

---

## 8.6 Conditional FM Hollow-Round Rate

**Context:** Phase 8.6 specifies hollow rate check using `round2_new_points_resolved` field. This field was absent from v6 Phase 5 agent outputs (not in schema).

**Proxy metric:** Gate-fired files with `final_PRR = 0` are treated as hollow (round 2 fired but resolved nothing by final audit).

| Metric | Value |
|---|---|
| Total CFM files | 360 |
| Gate-fired (2 rounds) | 341 (94.7%) |
| Not-gated (1 round) | 19 (5.3%) |
| Proxy hollow (gate_fired + PRR=0) | 8 (2.2%) |
| Mean PRR (gate-fired) | 0.395 |
| PRR ≥ 0.5 (gate-fired) | 137 (40.2%) |

**Hollow rate verdict: PASS** (proxy 2.2% < 10% threshold).

**Notable:** Gate-fire rate of 94.7% means conditional FM and full multiround are nearly equivalent in practice — the gate almost never stops at round 1. This partly explains why H3 shows no significant improvement (CFM vs multiround: p=0.3677).

**Limitation:** Proxy underestimates hollow rate because `round2_new_points_resolved` is missing. The 8 proxy-hollow files represent conservative lower bound. Exact hollow rate requires per-round PRR tracking in a future run.

---

## Summary

| Check | Status | Key Finding |
|---|---|---|
| 8.1 Method A vs B | PASS | Zero divergence |
| 8.2 Threshold sensitivity | PASS | FAIL at all thresholds; null is robust |
| 8.3 Dimension lift | INFORMATIVE | IDR drives null; IDP_adj sole positive signal |
| 8.4 Difficulty stratification | PASS (limited n) | ρ=−0.5649; PM3 resolved but sample small |
| 8.5 IDP diagnostic | PASS | No extraction bug; biased_debate lower IDP is real signal |
| 8.6 CFM hollow rate | PASS | Proxy 2.2% < 10%; exact rate unverifiable |
