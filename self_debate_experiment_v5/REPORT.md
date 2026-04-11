# v5 Self-Debate Experiment Report

## Abstract

The primary hypothesis (H1) **fails**: the isolated self-debate protocol achieves fair-comparison lift of +0.0097 over baseline, with bootstrap 95% CI [-0.0013, +0.0217], well below the pre-registered threshold of +0.10. The experiment evaluated whether adversarial role separation (critic vs. defender) produces better ML methodology verdicts than single-pass review, testing 110 synthetic benchmark cases across five conditions (isolated_debate, multiround, forced_multiround, ensemble, baseline) with three runs per case (1,650 total output files). Despite a high absolute benchmark mean (isolated_debate = 0.9549), the debate protocol does not generate sufficient additional signal to distinguish itself from baseline on the fair-comparison dimensions (IDR, IDP, DRQ, FVC). Cross-vendor validation (gpt-4o-mini) reveals an IDR delta of -0.7737, revealing that absolute IDR values are evaluator-dependent to a degree that makes them unreliable as standalone measurements; the closed-loop confound is more severe than assumed. The recommendation is to not adopt the debate protocol as currently implemented; future work should target mixed-verdict cases and lower-ceiling benchmarks where discriminative headroom exists.

---

## Introduction and Motivation

The self-debate protocol hypothesizes that assigning adversarial roles --- a Critic tasked with finding methodological flaws and a Defender tasked with rebutting invalid critiques --- forces engagement with both sides of an ML methodology question, producing better-typed verdicts and catching false positives that correlated parallel assessors miss. Prior experiment versions (v2--v4) established the basic protocol machinery but suffered from calibration problems: cases were too easy, flaws too obvious, and baselines too weak, producing ceiling effects that obscured any protocol-level signal.

v5 was designed as a response to those calibration failures. The benchmark generation pipeline was rebuilt from scratch: synthetic cases were generated with planted methodological flaws at controlled difficulty levels, smoke-tested against the evaluation model (claude-sonnet-4-6), and filtered to retain only cases where single-pass performance left headroom for the debate protocol to demonstrate value (proxy_mean < 0.83). The resulting ARCH-1 benchmark contains 80 critique cases (planted flaws that should be identified) and 30 defense_wins cases (sound designs that should be exonerated), with no mixed cases.

The experiment's five conditions span a range of structural complexity: baseline (single-pass, no structure), isolated_debate (role separation without information exchange), multiround (up to 4 rounds with Defender seeing Critic output), forced_multiround (minimum 2 rounds, hard cases only), and ensemble (3 independent assessors with majority-vote aggregation). The primary comparison is isolated_debate vs. baseline on the four dimensions where both conditions have equal structural agency.

---

## Related Work

The debate protocol draws on **Irving et al. (2018)**, who proposed AI safety via debate as a mechanism for eliciting truthful behavior from AI systems by having two AI agents argue before a *human* judge. This experiment departs from that setting in a material way: both generation and evaluation are fully automated, with no human judge. The disanalogy matters because the human judge in Irving et al. provides an external epistemic anchor; an LLM evaluator does not. The multi-agent structure is further informed by **Du et al. (2023)**, who demonstrated that multi-agent debate improves factuality and reasoning in LLMs, and **Liang et al. (2023)**, who showed that debate-style interaction encourages divergent thinking. **Khan et al. (2024)** established that debating with more persuasive LLMs leads to more truthful answers, supporting the hypothesis that adversarial forcing produces better-calibrated outputs.

The LLM-as-judge evaluation methodology follows **Zheng et al. (2023)** (MT-Bench), which established the viability of using LLMs as evaluators with structured rubrics, and **Panickssery et al. (2024)**, who showed that LLM evaluators exhibit self-enhancement bias --- rating outputs from the same model family systematically higher. This reliability concern is directly implicated in Phase 9's cross-vendor findings. The ensemble condition's multi-assessor design is informed by **Chan et al. (2023)** (ChatEval), a multi-agent collaborative evaluation framework. The within-case variance analysis and multi-run aggregation strategy draws on **Wang et al. (2023)**, who demonstrated that self-consistency in chain-of-thought reasoning improves reliability through sampling and majority voting.

---

## Experimental Design

### Conditions

| Condition | Description | Scope |
|---|---|---|
| `isolated_debate` | Critic and Defender each receive only the task prompt; orchestrator adjudicates | All 110 cases |
| `multiround` | Defender sees Critic output; up to 4 rounds | All 110 cases |
| `forced_multiround` | Same as multiround but minimum 2 rounds enforced | Hard cases only (n=42) |
| `ensemble` | 3 independent assessors with majority-vote aggregation | All 110 cases |
| `baseline` | Single-pass critique, no adversarial structure | All 110 cases |

Each condition was run 3 times per case, yielding 1,650 raw output files (excluding forced_multiround medium-difficulty N/A entries).

### Benchmark

The ARCH-1 benchmark comprises 110 synthetic cases: 80 critique (planted methodological flaws) and 30 defense_wins (sound designs). Cases are labeled as hard (n=42) or medium (n=68) based on proxy_mean thresholds from smoke-testing, though difficulty label validation failed (see Results). All cases have binary ground truth (critique_wins or defense_wins); no mixed cases exist in ARCH-1. This is an intentional scope restriction --- mixed-verdict cases, where both sides have valid claims, are the most relevant test of adversarial protocol value but require a different benchmark architecture. All conclusions are scoped to binary-verdict cases.

### Scoring Dimensions

| Dimension | Definition | Applicability |
|---|---|---|
| **IDR** (Issue Detection Rate) | Fraction of must_find_issue_ids correctly identified | Critique cases only |
| **IDP** (Issue Detection Precision) | Fraction of raised issues that are valid | Critique cases only |
| **DRQ** (Decision Resolution Quality) | Typed verdict matches expected resolution | All cases |
| **FVC** (Final Verdict Correctness) | Verdict in acceptable_resolutions list | All cases |
| **DC** (Debate Correctness) | Defense correctly reached verdict type | Diagnostic only; N/A for baseline |
| **ETD** (Exchange Trajectory Divergence) | Empirical test design quality | N/A for all ARCH-1 cases |

**Fair-comparison dimensions:** IDR, IDP, DRQ, FVC. These four dimensions are the primary scoring surface where all conditions have equal structural agency. ETD is excluded because no ARCH-1 case has empirical_test_agreed as its ideal resolution --- ETD is structurally inapplicable to cases with binary ground truth. DC is excluded from fair comparison because baseline has no Defender role; including DC would artificially inflate debate-condition scores. DC is reported as a diagnostic in Table B.

**Per-case pass criterion:** mean(non-null primary dimensions) >= 0.65 AND all applicable primary dimensions >= 0.5.

### Pre-Registration

The pre-registration (PREREGISTRATION.json) specified:
- **H1 (Primary):** Fair-comparison lift (isolated_debate FC mean minus baseline FC mean) >= +0.10
- **Debate pass rate:** >= 75%
- **Benchmark mean:** >= 0.65
- **H2 (Secondary):** Forced multiround outperforms natural multiround on hard cases
- **H3 (Secondary):** Ensemble FVC >= 0.5 on >= 60% of defense_wins cases

Method A (per-case mean then aggregate) and Method B (per-dimension mean then aggregate) were both pre-specified, with a divergence flag threshold of 0.05.

### IDR/IDP Rescoring

A post-Phase 6 audit identified that the original orchestrator had `scoring_targets.must_find_issue_ids` in context during scoring, collapsing IDR/IDP to approximately 1.0 for all conditions (answer-key leakage). All IDR/IDP values reported in this document are from `v5_rescored_idr_idp.json`, produced by an isolated Claude Haiku semantic scorer with no answer-key context. The rescoring covers all 80 critique cases across applicable conditions.

---

## Results

### Table A: Isolated Debate vs. Ensemble vs. Baseline (Fair-Comparison Dimensions)

Dimensions: IDR, IDP, DRQ, FVC. ETD excluded (N/A for all ARCH-1 cases --- no empirical_test_agreed ground-truth cases exist). DC excluded (N/A for baseline; diagnostic-only for debate conditions).

| Condition | IDR (rescored) | IDP (rescored) | DRQ | FVC | FC Mean |
|---|---|---|---|---|---|
| isolated_debate | 0.8969 | 0.8549 | 1.0000 | 1.0000 | 0.9477 |
| ensemble (majority IDR) | 0.7679 | 0.9583 | 0.9727 | 0.9727 | 0.9179 |
| ensemble (union IDR†) | 0.8725 | 0.9583 | 0.9727 | 0.9727 | 0.9441 |
| baseline | 0.8729 | 0.8549 | 0.9894 | 0.9894 | 0.9266 |

†Union IDR: any-assessor-found replaces majority-vote aggregation. IDR recovers +0.1046 (43/240 critique runs affected, mean gain +0.5837). Under union IDR, ensemble FC mean (0.9441) exceeds baseline (0.9266) by +0.0175 and approximately matches isolated_debate (0.9477). See ENSEMBLE_ANALYSIS.md — Union IDR Sensitivity Analysis.

Wilcoxon (isolated vs. ensemble, fair dims): W=648.5, p=0.119 --- not significant.

### Table B: Debate Conditions vs. Each Other (All Applicable Dimensions)

Dimensions: IDR, IDP, DC (diagnostic), DRQ, FVC. ETD excluded (N/A for all ARCH-1 cases).

| Condition | IDR (rescored) | IDP (rescored) | DC (diag) | DRQ | FVC | Overall Mean |
|---|---|---|---|---|---|---|
| isolated_debate | 0.8969 | 0.8549 | 1.0000 | 1.0000 | 1.0000 | 0.9504 |
| multiround | 0.8925 | 0.8580 | 1.0000 | 1.0000 | 1.0000 | 0.9501 |
| forced_multiround* | 1.0000 | 0.9259 | 0.7500 | 0.9286 | 0.9286 | 0.9066 |
| ensemble | 0.7679 | 0.9583 | 0.9625 | 0.9727 | 0.9727 | 0.9268 |
| baseline | 0.8729 | 0.8549 | N/A | 0.9894 | 0.9894 | 0.9267 |

*forced_multiround restricted to 42 hard cases. IDR/IDP from rescored file (9 critique hard cases). DC/DRQ/FVC from v5_results.json.

Wilcoxon (isolated vs. multiround, fair dims): W=133.5, p=0.561 --- not significant.
Wilcoxon (isolated vs. baseline, fair dims): W=314.0, p=0.047 --- marginally significant; effect size r=0.32.

### Primary Metric: Fair-Comparison Lift

**fc_lift = +0.0097**, bootstrap 95% CI: **[-0.0013, +0.0217]**.

The CI includes zero. The observed lift is one-tenth of the pre-registered threshold (+0.10). Sensitivity analysis confirms no plausible scoring variation changes this verdict: Method B (per-dimension aggregation) yields +0.0112, the bootstrap CI upper bound is +0.0217, and even adding DC to the isolated mean produces a maximum possible lift of approximately +0.027 --- all far below the threshold.

The dimension-level decomposition of the lift:

| Dimension | isolated_debate | baseline | Lift |
|---|---|---|---|
| IDR (rescored) | 0.8969 | 0.8729 | +0.0240 |
| IDP (rescored) | 0.8549 | 0.8549 | 0.0000 |
| DRQ | 1.0000 | 0.9894 | +0.0106 |
| FVC | 1.0000 | 0.9894 | +0.0106 |

The lift is driven primarily by IDR (+0.0240): the debate format identifies planted issues at a slightly higher rate than baseline. IDP is identical across conditions. DRQ and FVC contribute small positive increments at the margin of ceiling.

### Within-Case Variance

| Condition | Mean within-case variance |
|---|---|
| isolated_debate | 0.0053 |
| multiround | 0.0059 |
| ensemble | 0.0086 |
| baseline | 0.0044 |

All conditions show low within-case variance, indicating stable run-to-run behavior. The ensemble condition has the highest variance (0.0086), consistent with the conservative majority-vote rule producing different outcomes depending on assessor agreement patterns.

---

## Hypothesis Verdicts

### H1 (Primary): Fair-Comparison Lift >= +0.10

**FAILS (ceiling-limited).** fc_lift = +0.0097. Bootstrap 95% CI: [-0.0013, +0.0217]. The CI includes zero. The Wilcoxon test on fair-comparison dimensions (isolated vs. baseline) reached p=0.047, but this is a marginal result with small effect size (r=0.32); the bootstrap CI is the definitive gate per pre-registration. Importantly, the +0.10 threshold exceeds the ~0.05 of headroom available at the observed baseline performance level (0.9452), making H1 structurally impossible to pass on this benchmark regardless of protocol quality. The verdict is H1 FAILS, but the failure should be read as "the benchmark could not resolve whether the protocol adds value" rather than as evidence the protocol provides no value.

### H2 (Secondary): Protocol Lifts Harder Cases More

**NOT INTERPRETABLE.** H2 required H1 to pass as a prerequisite. With H1 failed, stratified lift analysis is not meaningful. Difficulty labels are additionally invalidated: Spearman rho = +0.046, p=0.687 --- the labels do not predict rubric performance (see Failure Mode Analysis).

### Secondary: Ensemble FVC >= 0.5 on >= 60% of Defense_Wins Cases

**PASSES.** Ensemble FVC >= 0.5 on 30/30 (100%) of defense_wins cases. The ensemble reliably identifies defense-winning designs. Given H1 failure, this finding is interpreted as showing ensemble does not harm defense_wins calibration, not as evidence of superiority over baseline.

### Secondary: Forced Multiround > Natural Multiround on Hard Cases

**PASSES (corrected).** FM hard mean = 0.9921 vs. MR hard mean = 0.9826. Three critique hard cases (eval_scenario_381, 411, 616) were originally Phase 6 batch-agent stubs misclassified as not_applicable_difficulty, depressing FM hard mean to 0.9425. After Phase 9.5 re-run with correct FM protocol, all 9 files produced critique_wins verdicts. The directional result holds but the margin is small and the Wilcoxon test is non-significant (W=12.5, p=0.376).

### Difficulty Label Validation

**FAILS.** Spearman rho = +0.046, p=0.687 (non-defense_wins cases, n=80). The difficulty labels do not predict rubric performance. The expected direction was negative (harder labels correspond to lower baseline scores); the observed direction is slightly positive but insignificant. Means by stratum: medium = 0.9242, hard = 0.9271. This invalidation is consistent with a ceiling effect: baseline performance (0.9452) is high enough that hard/medium separation is compressed into a narrow band.

### Benchmark Pass/Fail Summary

| Criterion | Threshold | Actual | Pass? |
|---|---|---|---|
| H1: fc_lift isolated vs. baseline | >= +0.10 | +0.0097 [-0.0013, +0.0217] | **FAIL** |
| Debate pass rate | >= 75% | 89.1% (98/110) | PASS |
| Benchmark mean (isolated_debate) | >= 0.65 | 0.9549 | PASS |
| H2: FM > MR on hard | FM mean > MR mean | FM=0.9921 > MR=0.9826 (corrected) | PASS |
| Ensemble FVC >= 0.5 on >= 60% defense_wins | >= 60% | 100% (30/30) | PASS |
| Difficulty label validity | rho < 0, p < 0.05 | rho=0.046, p=0.687 | **FAIL** |

**Overall: FAIL** --- the primary hypothesis is not met.

---

## Failure Mode Analysis

### Failure Attribution Taxonomy

| Attribution | Count | Fraction |
|---|---|---|
| none (clean pass) | 294 | 88.6% |
| ambiguous | 15 | 4.5% |
| agent | 21 | 6.3% |
| protocol | 0 | 0.0% |

Counts are from 330 isolated_debate evaluation files (110 cases x 3 runs). The dominant failure mode is agent-level (6.3%): cases where the agent missed a planted issue or raised a false positive at sufficient rate to score below threshold. No protocol-level failures were identified --- the debate structure itself did not cause failures where agents performed their roles correctly.

### Ceiling Effect and Low Discriminative Power

With isolated_debate mean = 0.9549 and baseline mean = 0.9452, the dynamic range available for lift measurement is approximately 0.05 on a [0, 1] scale. DRQ and FVC are at ceiling for isolated_debate, multiround, and baseline (all >= 0.989), leaving IDR and IDP as the only dimensions where meaningful cross-condition differences exist. The debate protocol does not generate enough additional deliberative signal to move IDR beyond what baseline achieves on a single-pass critique.

The ceiling effect is the primary structural explanation for H1's failure: both conditions perform well enough that the difference between them is compressed into a band narrower than the pre-registered threshold.

### Ensemble IDR Suppression

The ensemble condition shows IDR = 0.7679, notably lower than baseline (0.8729) and isolated_debate (0.8969). This is the majority-vote suppression mechanism: when 2/3 assessors agree on critique_wins but identify different specific issues, the conservative ensemble rule may not surface the correct planted issue even if each assessor individually flagged it. Ensemble IDP is simultaneously high (0.9583) --- the ensemble rarely raises false positives --- but the IDR suppression means it trades recall for precision. Cases eval_scenario_3 and eval_scenario_295 exemplify this pattern: both showed consistent 2/3 critique_wins splits where the defense argument was substantively compelling, and the conservative rule fired correctly to prevent false consensus at the cost of IDR credit.

A retroactive union-IDR sensitivity analysis (`union_idr_analysis.py`) recovers ensemble IDR to 0.8725 (+0.1046) by crediting any assessor's identification of a planted issue, raising ensemble FC mean to ~0.9437 --- above baseline and approximately matching isolated_debate. This demonstrates the suppression is entirely in the aggregation rule: the three assessors collectively surface planted issues at near-isolated_debate recall rates; majority-vote synthesis discards what the critics have already found.

### Defense_Wins Uniformity

All 30 defense_wins cases scored 1.0 across all conditions on all runs. This strong result confirms the protocol reliably identifies defense-winning designs. However, the uniformity also means the defense_wins stratum contributes no discriminative signal to cross-condition comparisons --- all conditions score identically on these cases.

### Forced Multiround Hollow Rounds

The POST_MORTEM.md audit identified a 20.5% hollow-round rate in forced_multiround (24/117 files across 8 defense_wins cases). All 8 cases consistently produced hollow rounds across all 3 runs, suggesting these are structurally vacuous second rounds where the Defender resolved all points in round 1, leaving nothing substantive for round 2. This is below the 0.5 critical threshold but indicates that forcing additional rounds on defense_wins cases does not generate useful adversarial exchange.

### Batch 2 Contamination and Remediation

During Phase 6, 165 of the original batch 2 output files showed zero stochastic variance, indicating the batch agent loaded planted_issues into context before dispatch. The contaminated files were self-deleted and re-run with a clean subagent. The re-run files are clean. This was the most significant data integrity event in the experiment. The contamination detection mechanism --- zero cross-run variance --- was effective and is worth retaining in future pipelines.

---

## Cross-Vendor Validation (Phase 9)

### Protocol

An independent scorer (openai/gpt-4o-mini via OpenRouter) re-evaluated all 110 cases on critique-applicable dimensions (IDR, IDP, FVC). The cross-vendor scorer operated without access to debate outputs or answer keys, receiving only the task prompt and the isolated_debate condition's critique text.

### Results

Comparison is restricted to the 80 critique cases where IDR is applicable (defense_wins cases have IDR=N/A by protocol).

| Dimension | Claude (rescored) | Delta (gpt-4o-mini minus Claude) | Material? (> 0.1) |
|---|---|---|---|
| IDR | 0.8969 | -0.7737 | Yes |
| IDP | 0.8549 | +0.1181 | Yes |
| FVC | 1.0000 | -0.1875 | Yes |

All three dimension deltas exceed the 0.1 materiality threshold. The IDR delta is particularly large (-0.7737): gpt-4o-mini assigns substantially lower IDR scores to the same critique outputs that Claude's rescorer credited with identifying planted issues. The IDP delta is positive (+0.1181), meaning gpt-4o-mini rates issue precision higher. The FVC delta is negative (-0.1875), meaning gpt-4o-mini disagrees on verdict correctness for a meaningful fraction of cases.

### Interpretation

Phase 9 does not mitigate the closed-loop confound --- it reveals its severity. An IDR delta of -0.7737 means the two scorers disagree on issue detection for the same outputs to a degree that makes absolute IDR values evaluator-dependent and unreliable as standalone measurements. The directional disagreement on IDR vs. IDP (gpt-4o-mini scores IDR much lower, IDP slightly higher) is consistent with model-specific threshold calibration: what Claude's rescorer treats as identifying a planted issue, gpt-4o-mini more often does not credit. The self-enhancement bias literature (Panickssery et al., 2024) provides a plausible mechanism. The H1 verdict is not affected --- the lift is too small to pass under any plausible scorer --- but the dimension-level values in Tables A and B should not be treated as calibrated measurements. They are Claude-evaluator-relative scores, and the true values under a human or cross-model rubric may differ substantially.

---

## Limitations

### 1. Closed-Loop Evaluation Confound

**(a) Threat:** The same model family (Claude) generates debate outputs and scores them. Evaluation scores may reflect model-specific biases (e.g., a Claude evaluator may be more generous to Claude-generated text) rather than objective quality.

**(b) Evidence on magnitude:** Cross-vendor validation (Phase 9) shows material scorer disagreement on all three evaluated dimensions: IDR delta = -0.7737, IDP delta = +0.1181, FVC delta = -0.1875. The IDR disagreement is large enough to indicate that absolute IDR values are evaluator-dependent. However, the fc_lift (+0.0097) compares two conditions both scored by the same evaluator, so within-evaluator bias cancels in the lift computation as long as the bias is condition-independent.

**(c) Status:** Cross-vendor scoring was conducted on all 110 cases. The results reveal the confound is more severe than assumed: absolute IDR values are evaluator-dependent and should not be treated as calibrated measurements. The lift conclusion (H1 FAILS) is unaffected because the lift magnitude is too small to pass under any plausible rescoring, and within-evaluator bias cancels in lift computation as long as it is condition-independent. Readers should treat Tables A and B as Claude-evaluator-relative scores, not ground-truth quality measurements.

### 2. Same-Model Benchmark Selection Bias

**(a) Threat:** Cases were filtered using claude-sonnet-4-6 proxy_mean scores (retaining cases where proxy_mean < 0.83). The benchmark is calibrated for this model's specific failure modes. A protocol advantage observed on model-specific hard cases may not generalize to other models or real-world methodology review tasks.

**(b) Evidence on magnitude:** The difficulty labels derived from proxy_mean do not predict rubric performance (Spearman rho = 0.046, p = 0.687), suggesting the proxy_mean filtering did not create a clean difficulty gradient even for the test model. The ceiling effect (baseline mean = 0.9452) indicates the filter may have been insufficiently aggressive.

**(c) Mitigation:** The benchmark-selection bias is partially mitigated by the negative H1 result: the protocol fails to demonstrate advantage even on cases specifically selected to favor it. A positive result on model-calibrated cases would have required cross-model validation; a negative result is more conservative.

### 3. No Mixed Cases in Benchmark

**(a) Threat:** The ARCH-1 benchmark contains only binary-verdict cases (critique_wins or defense_wins). Mixed cases --- where flaws exist but do not invalidate the design --- are the scenario where adversarial role structure is most differentiated from single-pass review. The experiment cannot speak to protocol performance on the case type most relevant to the mechanism claim.

**(b) Evidence on magnitude:** The synthetic case generation pipeline structurally produces binary cases (planted clearcut flaws or clearcut-sound designs). The absence of mixed cases is a pipeline design choice, not sampling variation. All 110 cases have unambiguous ground truth.

**(c) Mitigation:** Conclusions are explicitly scoped to binary-verdict cases. The mechanism claim ("adversarial role separation forces engagement with both sides") requires mixed cases for full demonstration and is not validated by this experiment.

### 4. Answer-Key Leakage in Original Scoring (Corrected)

**(a) Threat:** The Phase 6 orchestrator had scoring_targets.must_find_issue_ids in context during initial IDR/IDP scoring, collapsing these dimensions to approximately 1.0 for all conditions and eliminating the primary signal source for the fair-comparison lift.

**(b) Evidence on magnitude:** All IDR/IDP values were rescored using an isolated Claude Haiku scorer with no answer-key context. The rescored values show meaningful cross-condition differences (e.g., IDR ranges from 0.7679 to 0.8969 across conditions), confirming the original leakage was complete.

**(c) Mitigation:** The rescoring is comprehensive (all 80 critique cases across all applicable conditions). All values in this report use rescored IDR/IDP. The original contaminated scores are not used in any analysis.

### 5. Phase 6 Batch Contamination (Remediated)

**(a) Threat:** 165 of the original batch 2 output files showed zero stochastic variance, indicating the batch agent loaded planted_issues into context before dispatch. These files would have produced artificially inflated IDR scores.

**(b) Evidence on magnitude:** Zero within-case variance across 3 runs for affected files is diagnostic of contamination. The contamination was detected before scoring via the variance check.

**(c) Mitigation:** All 165 contaminated files were deleted and re-run with a clean subagent that had no access to planted_issues. The re-run files pass the variance check. No contaminated data enters the analysis.

### 6. Small Effect Size Relative to Statistical Power

**(a) Threat:** The +0.10 threshold was set as a policy choice (minimum practically meaningful effect) without a pre-execution power analysis. The narrow CI [-0.0013, +0.0217] indicates the experiment has sufficient precision to detect effects of this magnitude, but the threshold itself may be miscalibrated relative to the benchmark's dynamic range.

**(b) Evidence on magnitude:** The baseline mean (0.9452) leaves approximately 0.05 of headroom on a [0, 1] scale. A threshold of +0.10 exceeds the available headroom, making the test structurally impossible to pass at the observed baseline performance level. Within-case variance is low (0.0044--0.0086), confirming the narrow CI is real and not an artifact of noisy estimation.

**(c) Mitigation:** The sensitivity analysis confirms no plausible scoring variation changes the H1 verdict. The bootstrap CI upper bound (+0.0217) is itself far below threshold. The fundamental issue is the ceiling effect, not insufficient power.

### 7. Forced Multiround Stub Misclassification (Corrected)

**(a) Threat:** Three hard critique cases (eval_scenario_381, 411, 616) were generated as batch-agent stubs with not_applicable_difficulty routing, producing null-verdict output files that scored 0.25 and depressed the FM hard mean from its true value.

**(b) Evidence on magnitude:** FM hard mean was 0.9425 with stubs vs. 0.9921 after correction --- a 0.0496 difference affecting 7.1% of hard cases (3/42).

**(c) Mitigation:** All 9 stub files were re-run in Phase 9.5 with correct forced_multiround protocol. All produced critique_wins verdicts with debate_rounds=2. The corrected values are used throughout this report.

---

## Artifacts

| File | Description |
|---|---|
| `HYPOTHESIS.md` | Pre-registered hypothesis statement with conditions, dimensions, and N/A rationale |
| `PREREGISTRATION.json` | Machine-readable pre-registration: hypotheses, rubric, comparison structures, pass criteria |
| `evaluation_rubric.json` | Scoring dimension definitions and pass/fail rules |
| `CRITIQUE.md` | Phase 4 protocol self-review: 6 identified design risks with root-cause analysis |
| `DEFENSE.md` | Phase 4 defense response with verdict selection and 7 pre-execution requirements |
| `CONCLUSIONS.md` | Primary source of truth: hypothesis verdicts, per-case table, dimension aggregates |
| `stats_results.json` | Bootstrap CIs, Wilcoxon tests, dimension aggregates, variance, failure attribution |
| `SENSITIVITY_ANALYSIS.md` | Method A/B comparison, dimension-level lift decomposition, threshold sensitivity |
| `ENSEMBLE_ANALYSIS.md` | Ensemble tables, IDR suppression mechanism, union IDR sensitivity analysis, hollow-round analysis, DC/FVC diagnostic |
| `union_idr_analysis.py` | Retroactive union-of-issues IDR reanalysis script; recovers ensemble IDR from 0.7679 to 0.8725 |
| `cross_vendor_scores_v5.json` | Phase 9 gpt-4o-mini rescoring: per-case external scores, deltas, and verdicts |
| `POST_MORTEM.md` | Phase 9.5 audit: 4 anomalies (1 high, 1 moderate, 2 low) with remediation status |
| `v5_rescored_idr_idp.json` | Leakage-corrected IDR/IDP scores from isolated Haiku semantic scorer |
| `v5_results.json` | Full experiment results: per-case scores, dimension aggregates, DC/FVC diagnostic |
| `v5_results_eval.json` | Per-case evaluation records with pass/fail, failure attribution |
| `per_condition_comparison.png` | Bar chart comparing fair-comparison dimensions across conditions |
| `dimension_heatmap.png` | Heatmap of dimension scores across all conditions |
| `sensitivity_analysis_chart.png` | Visualization of lift estimates under scoring variations |
| `difficulty_scatter.png` | Scatter plot of difficulty labels vs. rubric performance |
| `forced_multiround_hard.png` | FM vs. MR comparison on hard cases |

---

## Conclusions

The v5 self-debate experiment yields an inconclusive result on its primary hypothesis, with H1 failure driven primarily by a ceiling effect rather than a demonstrated null. The fc_lift of +0.0097 is positive in direction but negligible in magnitude, and the bootstrap CI includes zero. The correct interpretation is not "the protocol does not help" but rather "this benchmark, at the observed baseline performance level (0.9452), could not detect whether the protocol helps." The +0.10 threshold exceeds the approximately 0.05 of headroom available on a near-ceiling benchmark, making H1 structurally impossible to pass regardless of protocol quality. The protocol produces outputs that pass the experiment's own rubric at a high rate (89.1% pass, benchmark mean 0.9549), but the rubric, benchmark, and evaluator were all designed for this specific model and condition --- this is necessary but not sufficient evidence of operational value.

The ceiling effect is the dominant explanation. Both conditions score near-perfectly on DRQ and FVC (verdict quality), and the IDR lift (+0.0240) --- the largest component of the fair-comparison difference --- is too small to clear the pre-registered threshold. The difficulty labels intended to stratify cases by discriminative potential failed to predict performance (Spearman rho = 0.046, p = 0.687), indicating the benchmark did not achieve the targeted difficulty gradient despite proxy_mean filtering.

The ensemble condition's IDR suppression (-0.1290 vs. isolated_debate) is an artifact of majority-vote aggregation rather than a genuine recall deficit in the assessors. A retroactive union-IDR sensitivity analysis shows that crediting any-assessor-found recovers ensemble IDR to 0.8725 and raises FC mean to ~0.9437 --- above baseline and approximately matching isolated_debate. The IDP advantage (+0.1034) is preserved under union IDR. Union-of-issues IDR is the correct aggregation rule for v6.

The secondary findings --- FM directionally outperforming MR on hard cases (0.9921 vs. 0.9826, non-significant), ensemble passing the defense_wins calibration check (100%) --- provide structural confirmation that the protocol components function as designed, but function is not the same as differential value over baseline.

For future work, the path forward requires: (1) a lower-ceiling benchmark where baseline performance leaves discriminative headroom for the protocol, (2) inclusion of mixed-verdict cases where adversarial role structure has the clearest theoretical advantage, and (3) a cross-model evaluation design where the benchmark is not calibrated specifically for the test model. Within the tested scope --- binary-verdict cases, Claude-family models, ARCH-1 benchmark --- the debate structure cannot demonstrate advantage over single-pass baseline. Whether that result transfers to mixed-verdict cases, different model families, or real-world methodology review tasks remains an open question requiring a new experimental design.
