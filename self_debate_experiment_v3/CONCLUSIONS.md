# v3 Experiment Conclusions

Generated from `v3_results.json`, `stats_results.json`, `sensitivity_analysis_results.json`,
`within_case_variance_results.json`, `difficulty_validation_results.json`, `v3_external_results.json`.

---

## Benchmark Pass/Fail Criteria

| Criterion | Threshold | Result | Status |
|-----------|-----------|--------|--------|
| Isolated debate mean | ≥ 0.65 | 0.975 | **PASS** |
| Case pass rate (isolated, 2/3 rule) | ≥ 75% | 93.9% (46/49) | **PASS** |
| Lift over baseline | ≥ +0.10 | +0.341 | **PASS** |

**BENCHMARK OVERALL: PASSES**

---

## Per-Case Scoring Table

| Case ID | Category | Diff | Pos | Isolated | Multiround | Ensemble | Baseline | Delta | Pass |
|---------|----------|------|-----|----------|------------|----------|----------|-------|------|
| broken_baseline_forecast_002 | broken_baseline | medium | critique | 1.000 | 1.000 | 1.000 | 0.700 | +0.300 | YES |
| broken_baseline_ocr_003 | broken_baseline | medium | critique | 1.000 | 1.000 | 1.000 | 0.750 | +0.250 | YES |
| broken_baseline_clinical_004 | broken_baseline | medium | critique | 1.000 | 1.000 | 1.000 | 0.700 | +0.300 | YES |
| broken_baseline_fraud_006 | broken_baseline | medium | critique | 1.000 | 1.000 | 1.000 | 0.750 | +0.250 | YES |
| broken_baseline_recsys_007 | broken_baseline | medium | critique | 1.000 | 1.000 | 1.000 | 0.700 | +0.300 | YES |
| broken_baseline_energy_010 | broken_baseline | medium | critique | 1.000 | 1.000 | 1.000 | 0.700 | +0.300 | YES |
| broken_baseline_genomics_011 | broken_baseline | medium | critique | 1.000 | 1.000 | 1.000 | 0.700 | +0.300 | YES |
| broken_baseline_radiology_009 | broken_baseline | medium | critique | 1.000 | 1.000 | 1.000 | 0.750 | +0.250 | YES |
| metric_mismatch_churn_013 | metric_mismatch | medium | critique | 1.000 | 1.000 | 1.000 | 0.750 | +0.250 | YES |
| metric_mismatch_vision_012 | metric_mismatch | medium | critique | 1.000 | 1.000 | 1.000 | 0.700 | +0.300 | YES |
| metric_mismatch_clinical_016 | metric_mismatch | medium | critique | 1.000 | 1.000 | 1.000 | 0.750 | +0.250 | YES |
| metric_mismatch_recsys_014 | metric_mismatch | medium | critique | 1.000 | 1.000 | 1.000 | 0.700 | +0.300 | YES |
| metric_mismatch_lending_019 | metric_mismatch | medium | critique | 1.000 | 1.000 | 1.000 | 0.750 | +0.250 | YES |
| metric_mismatch_search_018 | metric_mismatch | medium | critique | 1.000 | 1.000 | 1.000 | 0.700 | +0.300 | YES |
| metric_mismatch_survival_020 | metric_mismatch | medium | critique | 1.000 | 1.000 | 1.000 | 0.700 | +0.300 | YES |
| hidden_confounding_hospital_rollout_201 | hidden_confounding | hard | mixed | 1.000 | 1.000 | 1.000 | 0.583 | +0.417 | YES |
| hidden_confounding_college_support_209 | hidden_confounding | medium | critique | 1.000 | 1.000 | 1.000 | 0.700 | +0.300 | YES |
| hidden_confounding_member_feed_206 | hidden_confounding | hard | mixed | 1.000 | 1.000 | 1.000 | 0.583 | +0.417 | YES |
| hidden_confounding_winter_queue_202 | hidden_confounding | medium | critique | 1.000 | 1.000 | 1.000 | 0.700 | +0.300 | YES |
| hidden_confounding_ads_market_210 | hidden_confounding | hard | critique | 1.000 | 1.000 | 1.000 | 0.700 | +0.300 | YES |
| hidden_confounding_energy_regions_203 | hidden_confounding | hard | mixed | 1.000 | 1.000 | 1.000 | 0.583 | +0.417 | YES |
| hidden_confounding_icu_transfer_207 | hidden_confounding | hard | critique | 1.000 | 1.000 | 1.000 | 0.700 | +0.300 | YES |
| hidden_confounding_skin_sites_205 | hidden_confounding | hard | critique | 1.000 | 1.000 | 1.000 | 0.700 | +0.300 | YES |
| scope_intent_abandonment_offer_301 | scope_intent | medium | critique | 1.000 | 1.000 | 1.000 | 0.700 | +0.300 | YES |
| scope_intent_moderation_308 | scope_intent | medium | critique | 1.000 | 1.000 | 1.000 | 0.700 | +0.300 | YES |
| scope_intent_radiology_queue_302 | scope_intent | hard | mixed | 1.000 | 1.000 | 1.000 | 0.750 | +0.250 | YES |
| scope_intent_credit_launch_303 | scope_intent | hard | mixed | 1.000 | 1.000 | 1.000 | 0.750 | +0.250 | YES |
| scope_intent_wearable_screen_307 | scope_intent | hard | mixed | 1.000 | 1.000 | 1.000 | 0.750 | +0.250 | YES |
| defense_wins_001 | defense_wins | medium | defense | 1.000 | 1.000 | 1.000 | 0.500 | +0.500 | YES |
| defense_wins_002 | defense_wins | medium | defense | 1.000 | 1.000 | 1.000 | 0.500 | +0.500 | YES |
| defense_wins_003 | defense_wins | medium | defense | 1.000 | 1.000 | 1.000 | 0.500 | +0.500 | YES |
| defense_wins_005 | defense_wins | medium | defense | 1.000 | 1.000 | 1.000 | 0.500 | +0.500 | YES |
| defense_wins_006 | defense_wins | medium | defense | 1.000 | 1.000 | 1.000 | 0.500 | +0.500 | YES |
| defense_wins_007 | defense_wins | hard | defense | 1.000 | 1.000 | 1.000 | 0.500 | +0.500 | YES |
| defense_wins_009 | defense_wins | hard | defense | 1.000 | 1.000 | 1.000 | 0.500 | +0.500 | YES |
| defense_wins_010 | defense_wins | medium | defense | 1.000 | 1.000 | 1.000 | 0.500 | +0.500 | YES |
| defense_wins_011 | defense_wins | hard | defense | 1.000 | 1.000 | 1.000 | 0.500 | +0.500 | YES |
| defense_wins_012 | defense_wins | medium | defense | 1.000 | 1.000 | 1.000 | 0.500 | +0.500 | YES |
| defense_wins_013 | defense_wins | hard | defense | 1.000 | 1.000 | 1.000 | 0.500 | +0.500 | YES |
| real_world_framing_004 | real_world_framing | medium | critique | 1.000 | 1.000 | 1.000 | 0.700 | +0.300 | YES |
| real_world_framing_001 | real_world_framing | medium | critique | 1.000 | 1.000 | 1.000 | 0.750 | +0.250 | YES |
| real_world_framing_006 | real_world_framing | hard | mixed | 1.000 | 1.000 | 1.000 | 0.583 | +0.417 | YES |
| real_world_framing_007 | real_world_framing | hard | mixed | 1.000 | 1.000 | 1.000 | 0.583 | +0.417 | YES |
| real_world_framing_009 | real_world_framing | hard | mixed | 1.000 | 1.000 | 1.000 | 0.583 | +0.417 | YES |
| real_world_framing_002 | real_world_framing | hard | critique | 0.917 | 1.000 | 0.917 | 0.583 | +0.333 | YES |
| real_world_framing_010 | real_world_framing | hard | critique | 1.000 | 1.000 | 0.917 | 0.583 | +0.417 | YES |
| real_world_framing_003 | real_world_framing | hard | mixed | 0.333 | 0.333 | 1.000 | 0.333 | +0.000 | **NO** |
| real_world_framing_005 | real_world_framing | hard | critique | 0.750 | 1.000 | 0.917 | 0.583 | +0.167 | **NO** |
| real_world_framing_008 | real_world_framing | hard | critique | 0.750 | 1.000 | 0.917 | 0.583 | +0.167 | **NO** |

---

## Dimension-Level Aggregates

| Dimension | Isolated | Multiround | Ensemble | Baseline |
|-----------|----------|------------|----------|----------|
| IDR | 1.000 | 1.000 | 1.000 | 1.000 |
| IDP | 1.000 | 1.000 | 1.000 | 1.000 |
| DC | 0.980 | 0.980 | **1.000** | 0.000† |
| DRQ | 0.956 | **0.980** | 0.959 | 0.490† |
| ETD | 0.841 | 0.952 | **1.000** | 0.476 |
| FVC | 0.980 | 0.980 | **1.000** | 0.980 |
| **Mean** | **0.975** | **0.986** | **0.993** | **0.634** |

†Baseline DC=0.0 and DRQ≤0.5 are structural overrides (pre-registered). See SENSITIVITY_ANALYSIS.md for corrected scores.

DC is structurally identical to FVC in this scorer for all non-baseline conditions — `compute_dc()` calls `compute_fvc()` directly. DC provides no independent signal over FVC; it is reported for completeness per pre-registration (see `dc_note` in PREREGISTRATION.json).

---

## Statistical Tests

| Comparison | Point estimate | 95% CI | Wilcoxon W | p-value |
|------------|---------------|--------|------------|---------|
| Isolated vs. baseline | +0.341 | [+0.309, +0.371] | 1176.0 | < 0.001 |
| Multiround vs. baseline | +0.352 | [+0.322, +0.381] | 1176.0 | < 0.001 |
| Isolated vs. ensemble | −0.019 | [−0.051, +0.002] | 1.0 | 0.951 |
| Multiround vs. isolated | +0.012 | [0.000, +0.027] | 6.0 | 0.087 |

Note: Wilcoxon r-values for isolated vs. baseline and multiround vs. baseline saturate at the formula ceiling (W=1176 = n*(n+1)/2, all differences positive). The effect-size formula `r = 1 - 2W/(n*(n+1))` returns 0.0 at maximum W, not a true zero effect. The correct interpretation is maximum effect size — every case improved. p < 0.001 is reliable.

---

## Hypothesis Verdicts

### Primary Hypotheses

| Hypothesis | Criterion | Result | Verdict |
|------------|-----------|--------|---------|
| Debate benchmark mean ≥ 0.65 | mean ≥ 0.65 | 0.975 | **CONFIRMED** |
| Case pass rate ≥ 75% | pass rate ≥ 75% | 93.9% | **CONFIRMED** |
| Lift over baseline ≥ +0.10 | lift ≥ 0.10 | +0.341 | **CONFIRMED** |

### Secondary Hypotheses

**Secondary 1 — Ensemble on mixed-position cases**
Hypothesis: Debate outperforms ETD-constrained ensemble on mixed-position cases.
Result: **DISCONFIRMED.** Isolated debate mean on mixed cases = 0.958; ensemble = 1.000. Ensemble is not inferior on mixed cases; it achieves perfect scores. The ETD constraint appears to help rather than hurt on mixed cases, which by definition require empirical resolution.

**Secondary 2 — Defense_wins compute budget**
Hypothesis: Ensemble DC ≥ 0.5 on ≥ 60% of defense_wins cases (compute partially explains advantage).
Result: **CONFIRMED.** Ensemble DC = 1.0 on all 11 defense_wins cases (100% ≥ 60% threshold). Multiround DC = 1.0 as well. Both multi-agent and adversarial exchange conditions fully recognize correct defenses.

**Secondary 3 — Multiround DRQ advantage**
Hypothesis: Multiround DRQ > isolated debate DRQ across non-defense_wins cases.
Result: **DIRECTIONALLY CONFIRMED, not statistically significant.** Multiround DRQ = 0.980 vs. isolated DRQ = 0.956 (+0.024). Wilcoxon p = 0.087 — directional improvement observed, but does not reach α = 0.05.

Reminder: DC is structurally identical to FVC in this scorer (see PREREGISTRATION.json `dc_note`). DRQ is the only dimension where multiround has an independent structural advantage by design (typed verdict quality after adversarial exchange).

---

## Multiround vs. Isolated Comparison

Multiround mean (0.986) exceeds isolated debate mean (0.975) by +0.012 (95% CI: [0.000, +0.027]). The improvement is entirely concentrated in DRQ (+0.024) and ETD (+0.111). DRQ improvement is consistent with the adversarial exchange design — agents who have debated are more likely to converge on the ideal resolution type rather than an acceptable-but-non-ideal one.

Multiround operated with high efficiency: mean rounds per run = 1.03. Of 189 multiround runs across all cases, 173 resolved in a single round (91.5%), 11 required 2 rounds (5.8%), and 5 recorded 0 rounds (2.6%, likely baseline-adjacent cases or cases where debate was not triggered). Force-resolutions occurred across 21 runs (11.1%), accounting for 57 points total — concentrated in the 3 remaining failing cases.

**Limitation:** The multiround condition uses orchestrator adjudication (the lead agent reads the debate transcript and produces a verdict) rather than ml-lab's canonical agent-consensus adjudication (where verdicts emerge from explicit agent concessions in DEBATE.md). If agent-consensus adjudication is a genuine performance feature, the measured multiround advantage (+0.012 on overall mean, +0.024 on DRQ) is a lower bound on what the canonical ml-lab protocol would produce.

**Convergence analysis:** The pre-registered convergence metric (critic_verdict vs. defender_verdict per isolated_debate run) could not be extracted from raw outputs. The `critic_raw` and `defender_raw` fields contain prose critique and defense text respectively — neither agent role emits an explicit verdict label in the isolated_debate condition. Verdict emerges only from the orchestrator adjudication step. This is a pre-registration gap: the metric was defined as extractable but the raw output format does not support it. Reported as N/A.

---

## Failure Mode Taxonomy

### Passing cases (failure_attribution = 'none')
137 of 147 scored isolated_debate runs passed. No failure to attribute.

### Agent failures (failure_attribution = 'agent') — 3 runs
Agent failures are traceable to specific agent output: Critic missed a must-find issue, or Defender reasoning/label disconnect.

- **real_world_framing_003 run1–3**: Isolated debate verdict = `mixed` across all 3 runs. `mixed` is not in acceptable_resolutions (`['empirical_test_agreed', 'critique_wins']`). FVC=0.0, DC=0.0, DRQ=0.0 → mean=0.333. The adjudicator produced a structurally invalid verdict type. Note: ensemble scored 1.000 on this case (ensemble synthesizer constrained to emit a valid verdict type). Attribution: agent (adjudicator label error).

### Ambiguous failures — 7 runs
Cannot distinguish agent vs. protocol from outputs alone.

- **real_world_framing_005 run1–3 (isolated)**: Verdict = `critique_wins`, no empirical test produced (ETD=0.0). Ideal = `empirical_test_agreed`. The critique identified all must-find issues and the verdict is in acceptable_resolutions, but the protocol failed to push toward the empirical-test resolution. Attribution: ambiguous — could be adjudicator (chose acceptable but non-ideal resolution) or protocol (isolated design with no adversarial pressure toward ETD).
- **real_world_framing_008 run1–3 (isolated)**: Same pattern as rwf_005.

Note: rwf_005 and rwf_008 both pass in the multiround condition (mean=1.000), where adversarial exchange predictably pushed both sides toward specifying an empirical test. The multiround advantage on these cases is therefore structural — not a content improvement.

---

## Subgroup Analysis

### By category

| Category | n | Isolated mean | Pass rate |
|----------|---|---------------|-----------|
| broken_baseline | 8 | 1.000 | 8/8 |
| metric_mismatch | 7 | 1.000 | 7/7 |
| hidden_confounding | 8 | 1.000 | 8/8 |
| scope_intent | 5 | 1.000 | 5/5 |
| defense_wins | 11 | 1.000 | 11/11 |
| real_world_framing | 10 | 0.875 | 7/10 |

All failures are concentrated in `real_world_framing`. This category has the hardest cases (all labeled hard difficulty), the most complex scoring (many with `ideal = empirical_test_agreed`), and the most heterogeneous verdict space. The 3 failures are genuine — 2 ambiguous protocol failures and 1 agent label error.

### Mixed-position cases (n=16)

| Condition | Mean |
|-----------|------|
| Isolated debate | 0.958 |
| Multiround | 0.958 |
| Ensemble | **1.000** |

Ensemble achieves perfect scores on mixed cases. Debate is not inferior but also not superior. Secondary hypothesis 1 is disconfirmed.

### Difficulty label validation

Spearman ρ = −0.069, p = 0.680 (n=38, excluding defense_wins). No significant correlation between difficulty labels and baseline scores. The difficulty labels as assigned do not predict how hard the cases are for the baseline condition. This is a validity concern for difficulty-stratified analysis — the labels reflect subjective domain complexity, not empirical discriminability. See SENSITIVITY_ANALYSIS.md.

### Within-case variance

| Condition | Mean std across 3 runs |
|-----------|----------------------|
| Isolated debate | 0.0024 |
| Multiround | 0.0000 |
| Ensemble | 0.0000 |
| Baseline | 0.0000 |

Results are extremely stable across runs. One high-variance case: `real_world_framing_002` (isolated std = 0.118), attributable to the isolation breach re-run producing a different output schema than the original runs (run1 used `measure/success_criterion/failure_criterion`; runs 2–3 used `condition/supports_critique_if/supports_defense_if`), resulting in run-level ETD score variation even after the scorer fix.

---

## External Benchmark Results

External benchmark: 16 cases (13 published-paper, 3 synthetic-grounded).

| Condition | Published paper (n=13) | Synthetic grounded (n=3) | All external (n=16) |
|-----------|----------------------|--------------------------|---------------------|
| Isolated debate | 1.000 | 1.000 | 1.000 |
| Multiround | 1.000 | 1.000 | 1.000 |
| Ensemble | 1.000 | 1.000 | 1.000 |
| Baseline | 0.658 | 0.500 | 0.628 |
| Pass rate | 13/13 | 3/3 | 16/16 |

External results are a validation stratum only — not included in primary hypothesis tests or main benchmark bootstrap CIs.

All debate conditions achieve perfect scores on external cases. Baseline scores on external cases (0.628) are consistent with the main benchmark baseline (0.634), suggesting the external cases are not systematically easier or harder on the non-structural dimensions.

The 3 synthetic-grounded cases show a lower baseline mean (0.500 vs. 0.658 for published-paper cases). Synthetic-grounded cases are all `defense_wins` type, where the baseline structural override (DC=0.0) produces a lower floor. This is expected and consistent with the main benchmark defense_wins baseline behavior (0.500 per case).

No systematic differences were observed between external and main benchmark cases on debate performance. The 16/16 pass rate on external cases provides cross-corpus evidence that the protocol generalizes beyond the GPT-generated synthetic benchmark.
