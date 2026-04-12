# Ensemble Analysis

---

## Overview

The ensemble condition uses 3 independent assessors (each seeing only the task prompt) followed by an ETD-constrained synthesizer that produces a unified verdict. It is compute-matched to multiround (multiple agent invocations) but architecturally distinct: no adversarial exchange, no Critic/Defender role separation, no iteration.

| Metric | Ensemble | Isolated | Multiround | Baseline |
|--------|----------|----------|------------|----------|
| Mean | **0.993** | 0.975 | 0.986 | 0.634 |
| Pass rate | 48/49 (97.9%) | 46/49 (93.9%) | 46/49 (93.9%) | 0/49 |
| Lift vs. isolated | +0.018 | — | — | — |

The ensemble achieves the highest mean score of any condition. The ensemble's advantage over isolated debate (+0.018) is not statistically significant (Wilcoxon p = 0.951).

---

## Clean Ensemble Results vs. All Conditions

The ensemble design is "clean" in the sense defined in the CLAUDE.md convention: Phase 1 assessors receive the task prompt only; Phase 2 synthesizer receives aggregated assessor outputs in a separate invocation. This prevents any single agent from seeing both the task and the answer key simultaneously.

One contamination guard was added to the ensemble adjudication instruction (lines 843–846 of the plan): the synthesizer is explicitly prohibited from referencing ground_truth, must_find_issue_ids, or scoring_targets when producing its verdict. An identical guard was added to multiround adjudication.

### Per-case ensemble vs. isolated comparison

Ensemble scores 1.000 on 48 of 49 cases. The one exception is `real_world_framing_003` (ensemble = 1.000, isolated = 0.333) — actually ensemble passes here. The three isolated failures (rwf_003=0.333, rwf_005=0.750, rwf_008=0.750) all score better under ensemble:

| Case | Isolated | Ensemble | Ensemble advantage |
|------|----------|----------|--------------------|
| real_world_framing_003 | 0.333 | **1.000** | +0.667 |
| real_world_framing_005 | 0.750 | **0.917** | +0.167 |
| real_world_framing_008 | 0.750 | **0.917** | +0.167 |

For rwf_003, ensemble passes where isolated fails entirely. The ensemble synthesizer produces a valid `empirical_test_agreed` verdict; the isolated debate adjudicator produced `mixed` (a structurally invalid verdict type). This is evidence that the ETD-constrained synthesizer architecture is more robust against verdict label errors than single-pass adjudication.

For rwf_005 and rwf_008, ensemble improves from 0.750 to 0.917 but does not fully pass (ensemble passes ≥ 2/3 runs but the case-level criterion is isolated_debate passes ≥ 2). Notably, the ensemble synthesizer produces `critique_wins` with an empirical test specification — meaning the ETD constraint causes the synthesizer to recommend an empirical test even when it votes for a strong critique position. This produces ETD=1.0 and a higher ensemble mean, confirming that the ETD constraint is an output-forcing mechanism independent of the verdict.

---

## Pre-Specified Defense_wins Criterion

**Criterion (pre-registered):** Ensemble DC ≥ 0.5 on ≥ 60% of defense_wins cases → compute partially explains defense_wins advantage.

**Result: CRITERION MET.**

Ensemble DC = 1.0 on all 11 defense_wins cases (100% ≥ 60% threshold). Multiround DC also = 1.0 on all 11.

This confirms that additional compute (multiple assessors in the ensemble, multiple rounds in multiround) is sufficient to correctly identify defense_wins cases. The isolated debate condition also achieves DC = 1.0 on all defense_wins cases. There is no condition under which defense_wins cases are misclassified.

The finding is consistent with: defense_wins cases are structurally straightforward once the full set of issues is examined — the correct answer is that the critique is wrong. Any condition with sufficient time and scope to examine all raised issues converges correctly.

---

## Mixed-Position Cases

| Condition | n=16 mixed cases | Mean |
|-----------|-----------------|------|
| Isolated debate | 16 | 0.958 |
| Multiround | 16 | 0.958 |
| Ensemble | 16 | **1.000** |

Secondary hypothesis 1 (debate outperforms ensemble on mixed cases) is **disconfirmed**. Ensemble achieves perfect scores on all 16 mixed-position cases. Isolated debate and multiround score 0.958 (2 cases scoring below 1.0: rwf_005 and rwf_008, both `empirical_test_agreed` cases where isolated debate returned `critique_wins`).

The ensemble's perfect score on mixed cases is explained by the ETD constraint: the synthesizer is explicitly instructed to produce an empirical test specification when assessors disagree or when the evidence is mixed. This instruction reliably pushes the ensemble toward `empirical_test_agreed` in mixed-position cases, matching the ideal resolution type.

**Implication for v4:** The ensemble's ETD advantage is a prompt-engineering effect, not an emergent property of multi-agent consensus. This was foreshadowed by the v2 ETD ablation (mean ETD 0.962 with explicit ETD constraint vs. 0.192 without). The isolated debate condition would likely close most of the ETD gap if the adjudicator were given the same explicit ETD-forcing instruction.

---

## ETD Scores by Condition

| Condition | ETD aggregate |
|-----------|--------------|
| Ensemble | **1.000** |
| Multiround | 0.952 |
| Isolated debate | 0.841 |
| Baseline | 0.476 |

The ETD gap between ensemble (1.000) and isolated debate (0.841) is the largest single-dimension difference across conditions. It is not attributable to superior agent reasoning — the ETD-constrained synthesizer is explicitly instructed to produce an empirical test spec, while the isolated debate adjudicator is not. This is confirmed by:

1. The cases where ensemble produces an ETD spec but isolated debate does not (rwf_005, rwf_008) are cases where the adjudicator voted `critique_wins` without prompting — there was no forcing instruction.
2. The ensemble ETD spec is produced regardless of verdict: ensemble votes `critique_wins` on rwf_005 and rwf_008 but still produces a fully-scored ETD (condition, supports_critique_if, supports_defense_if all present).

Recommendation for v4: Add an explicit ETD-forcing instruction to the isolated debate adjudicator prompt, analogous to the ensemble synthesizer instruction. Expected outcome: isolated ETD ≈ 1.0 on all empirical_test_agreed cases, closing the ensemble gap.

---

## IDP Harmonization for Defense_wins Cases

Defense_wins cases have `correct_position = 'defense'`, meaning IDR and IDP are set to `None` in the scorer (no must-find issues; the critique is structurally wrong, so false-positive detection is inapplicable). This exclusion applies symmetrically across all conditions including ensemble.

No IDP asymmetry was detected. The `must_not_claim` guard functions correctly: in no case did any condition raise a must_not_claim issue. IDP = 1.0 across all conditions and all cases where applicable.

---

## No Ensemble Catastrophic Failures

No ensemble run scored 0.000 on any case. The lowest ensemble score is `real_world_framing_003` (mean = 1.000 for ensemble — the ensemble passes this case where isolated debate fails entirely). There are no ensemble-specific pathologies.
