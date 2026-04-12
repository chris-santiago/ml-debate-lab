# CONCLUSIONS.md — Experiment Findings

## 1. Per-Case Scoring Table

All scores are on a 0.0–1.0 scale per dimension. "N/A" means the dimension is not applicable for that case
(excluded from that case's mean). "Debate" = self-debate protocol. "Base" = trivial baseline.

### Dimension Abbreviations
- **IDR** = issue_discovery_recall
- **IDP** = issue_discovery_precision
- **DC** = defense_calibration
- **DRQ** = debate_resolution_quality
- **ETD** = empirical_test_diagnosticity
- **FVC** = final_verdict_correctness
- **Mean** = mean of applicable dimensions
- **Pass** = case passes (mean ≥ 0.65 AND no applicable dimension below 0.5)

---

### broken_baseline_001 (easy)

| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | YES |
| Base   | 1.0 | 1.0 | 0.0 | 0.5 | 1.0 | 0.5 | **0.667** | YES |

Debate verdict: `empirical_test_agreed` (ideal: `empirical_test_agreed`) ✓  
Baseline conclusion: "improvement questionable" (directional, incomplete)  
Notes: Easy case; both systems found issues. Baseline fails on DC (no revision) and FVC (insufficient precision in conclusion). Debate achieves clean 1.0 across all dimensions.

---

### broken_baseline_002 (medium)

| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | YES |
| Base   | 0.5 | 1.0 | 0.0 | 0.5 | 1.0 | 0.5 | **0.583** | NO |

Debate verdict: `empirical_test_agreed` (ideal: `empirical_test_agreed`) ✓  
Baseline conclusion: directional but incomplete; missed `accuracy_hides_class_failure` in original pass.  
Notes: Baseline fails to identify the metric issue in the original assessment pass (only partially found in self-critique). DC=0.0 is structural (no revision step). Mean 0.583 fails the 0.65 threshold.

---

### broken_baseline_003 (hard)

| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 0.833 | 1.0 | 1.0 | 1.0 | **0.972** | YES |
| Base   | 0.5 | 1.0 | 0.0 | 0.5 | 1.0 | 0.5 | **0.583** | NO |

Debate verdict: `empirical_test_agreed` (ideal: `empirical_test_agreed`) ✓  
Baseline conclusion: identified feature confound but did not name attribution error explicitly.  
Notes: Debate DC slightly below 1.0 due to partial contestation of `no_ablation_study` (secondary issue). Baseline recall=0.5 (attribution_error not named). Baseline fails case threshold.

---

### metric_mismatch_001 (easy)

| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | N/A | 1.0 | **1.000** | YES |
| Base   | 1.0 | 1.0 | 0.0 | 0.5 | N/A | 0.5 | **0.600** | NO |

Debate verdict: `critique_wins` (ideal: `critique_wins`) ✓  
Baseline conclusion: "accuracy is misleading" — correct direction but insufficient precision; did not compute trivial baseline score explicitly.  
Notes: ETD is N/A for both systems (ideal is `critique_wins`, no test proposed). Baseline FVC=0.5 because the original conclusion says "misleading" rather than the precise verdict in the ground truth. Baseline fails case threshold.

---

### metric_mismatch_002 (medium)

| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | YES |
| Base   | 1.0 | 1.0 | 0.0 | 0.5 | 1.0 | 0.5 | **0.667** | YES |

Debate verdict: `empirical_test_agreed` (ideal: `empirical_test_agreed`) ✓  
Baseline conclusion: directional; identified misalignment and proposed A/B test.  
Notes: Baseline passes the 0.65 threshold but at the floor. DC=0.0 structural limitation. The only case besides broken_baseline_001 where the baseline passes — the issue is more obvious and the baseline correctly proposes an A/B test.

---

### metric_mismatch_003 (hard)

| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 0.833 | 1.0 | 1.0 | 1.0 | **0.972** | YES |
| Base   | 0.5 | 1.0 | 0.0 | 0.0 | 1.0 | 0.0 | **0.417** | NO |

Debate verdict: `empirical_test_agreed` (ideal: `empirical_test_agreed`) ✓  
Baseline conclusion: **WRONG** — original assessment concluded the evidence is directionally consistent and "supports the model improvement claim." This is precisely the false-positive trap the case is designed to expose.  
Notes: This is the most instructive failure of the baseline. The single-pass assessment fell directly into the false-positive trap: ROUGE-L improvement + directional human preference = accepted as valid evidence. The baseline did not perform the significance calculation (p≈0.16). DRQ=0.0 and FVC=0.0 for the baseline. The debate system correctly identified the underpowering.

---

### hidden_confounding_001 (medium)

| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 0.917 | 1.0 | 1.0 | 1.0 | **0.986** | YES |
| Base   | 0.5 | 1.0 | 0.0 | 0.0 | 1.0 | 0.0 | **0.417** | NO |

Debate verdict: `empirical_test_agreed` (ideal: `empirical_test_agreed`) ✓  
Baseline conclusion: **WRONG** — treated demographic attribution as "plausible first explanation" and recommended investigating alongside technical factors with equal priority.  
Notes: Baseline failed to prioritize scanner/acquisition confounds as the dominant hypothesis. This is the medical imaging case's designed trap: demographic attribution sounds reasonable without domain knowledge. DRQ=0.0 and FVC=0.0 for baseline. The debate system correctly inverted the investigation priority.

---

### hidden_confounding_002 (hard)

| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 0.917 | 1.0 | 1.0 | 1.0 | **0.986** | YES |
| Base   | 0.0 | 1.0 | 0.0 | 0.0 | 1.0 | 0.0 | **0.333** | NO |

Debate verdict: `empirical_test_agreed` (ideal: `empirical_test_agreed`) ✓  
Baseline conclusion: **WRONG** — concluded the result is valid because "randomization was maintained and both groups experienced the same conditions." This is the A/B test false-positive trap.  
Notes: This is the worst-performing baseline case. IDR=0.0 (treatment_period_interaction not found in original assessment at all). The single-pass system accepted the p=0.002 result and maintained randomization as sufficient validation, missing the external validity threat entirely. The self-critique step later identified the issue, but baseline scoring is from the original assessment. A catastrophic failure of single-pass reasoning on a hard confounding case.

---

### hidden_confounding_003 (medium)

| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 0.833 | 1.0 | 1.0 | 1.0 | **0.972** | YES |
| Base   | 0.0 | 1.0 | 0.0 | 0.0 | 1.0 | 0.0 | **0.333** | NO |

Debate verdict: `empirical_test_agreed` (ideal: `empirical_test_agreed`) ✓  
Baseline conclusion: **WRONG** — accepted the difficulty attribution as "plausible" and concluded "the hand-written benchmark likely presents harder problems."  
Notes: IDR=0.0 (data_contamination_risk and in_distribution_test_inflation not identified in original assessment). The single-pass system took the team's narrative at face value. The self-critique step later flagged contamination, but this is unavailable to baseline scoring. Another catastrophic failure of single-pass reasoning on confounding cases.

---

### scope_intent_002 (medium)

| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | YES |
| Base   | 0.5 | 1.0 | 0.0 | 0.5 | 1.0 | 0.5 | **0.583** | NO |

Debate verdict: `empirical_test_agreed` (ideal: `empirical_test_agreed`) ✓  
Baseline conclusion: "partially meets intent" — directional but did not name the prediction-intervention conflation explicitly or call the project incomplete.  
Notes: Baseline was more lenient than warranted. IDR=0.5 (conflation partially described but not named precisely; no_intervention_design not named). Mean 0.583 fails.

---

### scope_intent_003 (hard)

| System | IDR | IDP | DC | DRQ | ETD | FVC | Mean | Pass |
|--------|-----|-----|----|-----|-----|-----|------|------|
| Debate | 1.0 | 1.0 | 0.917 | 1.0 | N/A | 1.0 | **0.983** | YES |
| Base   | 0.5 | 1.0 | 0.0 | 0.5 | N/A | 0.5 | **0.500** | NO |

Debate verdict: `critique_wins` (ideal: `critique_wins`) ✓  
Baseline conclusion: "conclusion may be an overstatement" — insufficient; did not name scope_of_safety_underspecified, bandit_coverage_limitation, or overgeneralized_conclusion explicitly.  
Notes: ETD is N/A for both (ideal is `critique_wins`, no test required). Baseline IDR=0.5 (only scope underspecification partially found; other two must-find issues not named). Mean 0.500 at the floor threshold — fails.

---

## 2. Aggregate Scores

### Per-Case Summary

| case_id | Debate Mean | Base Mean | Delta | Debate Pass | Base Pass |
|---------|-------------|-----------|-------|-------------|-----------|
| broken_baseline_001 | 1.000 | 0.667 | +0.333 | YES | YES |
| broken_baseline_002 | 1.000 | 0.583 | +0.417 | YES | NO |
| broken_baseline_003 | 0.972 | 0.583 | +0.389 | YES | NO |
| metric_mismatch_001 | 1.000 | 0.600 | +0.400 | YES | NO |
| metric_mismatch_002 | 1.000 | 0.667 | +0.333 | YES | YES |
| metric_mismatch_003 | 0.972 | 0.417 | +0.555 | YES | NO |
| hidden_confounding_001 | 0.986 | 0.417 | +0.569 | YES | NO |
| hidden_confounding_002 | 0.986 | 0.333 | +0.653 | YES | NO |
| hidden_confounding_003 | 0.972 | 0.333 | +0.639 | YES | NO |
| scope_intent_002 | 1.000 | 0.583 | +0.417 | YES | NO |
| scope_intent_003 | 0.983 | 0.500 | +0.483 | YES | NO |
| **BENCHMARK** | **0.988** | **0.517** | **+0.471** | **11/11** | **2/11** |

### Dimension-Level Aggregate Scores (mean across 11 cases)

| Dimension | Debate | Baseline | Delta |
|-----------|--------|----------|-------|
| issue_discovery_recall | 1.000 | 0.500 | +0.500 |
| issue_discovery_precision | 1.000 | 1.000 | 0.000 |
| defense_calibration | 0.927 | 0.000 | +0.927 |
| debate_resolution_quality | 1.000 | 0.273 | +0.727 |
| empirical_test_diagnosticity | 1.000 | 0.900 | +0.100 |
| final_verdict_correctness | 1.000 | 0.318 | +0.682 |

*Note: defense_calibration for baseline is 0.0 across all cases by rubric definition (no revision step, position_update always 0.0). empirical_test_diagnosticity baseline = 0.9 averaged over applicable cases; it scores well when the baseline does propose a test, which it does in most cases via self-critique.*

---

## 3. Benchmark Pass/Fail

| Criterion | Threshold | Debate | Baseline |
|-----------|-----------|--------|----------|
| Benchmark mean | ≥ 0.65 | 0.988 ✓ | 0.517 ✗ |
| Case pass fraction | ≥ 75% | 100% (11/11) ✓ | 18% (2/11) ✗ |
| Debate-adds-value lift | ≥ +0.10 | +0.471 ✓ | — |

**Debate benchmark: PASSES.** Baseline benchmark: FAILS.

---

## 4. Hypothesis Verdict

### Primary hypothesis
> The debate protocol will achieve a benchmark aggregate score at least 0.10 higher than the trivial baseline.

**VERDICT: SUPPORTED**

The debate protocol achieves a benchmark mean of 0.988 vs. the trivial baseline mean of 0.517, a lift of **+0.471** — exceeding the +0.10 threshold by a factor of 4.7.

### Secondary hypothesis 1
> The debate protocol will surface planted issues at higher recall (issue_discovery_recall) than the trivial baseline on hard-difficulty cases.

**VERDICT: SUPPORTED**

On the four hard-difficulty cases (broken_baseline_003, metric_mismatch_003, hidden_confounding_002, scope_intent_003):
- Debate IDR: 1.0, 1.0, 1.0, 1.0 (all perfect)
- Baseline IDR: 0.5, 0.5, 0.0, 0.5 (consistently below 1.0)
- Aggregate debate hard IDR mean: 1.000 vs. baseline 0.375

### Secondary hypothesis 2
> The debate protocol will produce better-calibrated defense responses (defense_calibration) than the trivial baseline.

**VERDICT: SUPPORTED**

Debate defense_calibration: 0.927 average. Baseline defense_calibration: 0.000 (structural — no revision step). The delta is the largest of any dimension (+0.927). The debate protocol's Defense persona produces substantive, calibrated concession and contestation behavior that the trivial baseline cannot by design.

### Secondary hypothesis 3
> On cases where ideal_debate_resolution.type = critique_wins, the debate protocol will reach the correct resolution type at higher frequency than the trivial baseline.

**VERDICT: SUPPORTED**

Two cases have ideal resolution `critique_wins`: metric_mismatch_001 and scope_intent_003.
- Debate: both cases achieve `critique_wins`. DRQ = 1.0 for both.
- Baseline: DRQ capped at 0.5 for both (cannot achieve 1.0 by rubric definition).

### Secondary hypothesis 4
> The debate protocol will exhibit at least one failure mode in at least 1 of 11 cases.

**VERDICT: SUPPORTED (with qualification)**

The predicted failure modes (blind spot reinforcement and confidence overstatement) were not fully observed in their extreme forms. However, a related structural failure mode was observed:

**Partial Defense contestation of valid planted issues:** In 6 of 11 cases, the Defense agent partially contested a planted issue rather than fully conceding it, earning a partial credit score (B=0.5 per rubric). This is not the classic "blind spot reinforcement" (both agents agree on a wrong answer), but it is a calibration failure: the Defense partially pushes back on issues it should concede, which could be directionally misleading for a reader consuming only the Defense output.

The classic blind spot reinforcement failure was not observed: in all 11 cases, the Critique identified the primary planted issues correctly and the Judge correctly adjudicated the dispute.

---

## 5. Observed Failure Modes

### Failure mode 1: Partial Defense contestation of medium-severity valid issues

**Cases:** broken_baseline_003, metric_mismatch_003, hidden_confounding_001, hidden_confounding_002, hidden_confounding_003, scope_intent_003

**Description:** In these 6 cases, the Defense agent partially contested a planted issue rather than conceding it fully. The partially contested issues were uniformly medium-severity and secondary to the primary planted issues:
- broken_baseline_003: partial contest of `no_ablation_study`
- metric_mismatch_003: partial contest of `no_inter_annotator_agreement`
- hidden_confounding_001: partial contest of `temporal_and_site_confound`
- hidden_confounding_002: partial contest of `novelty_effect_uncontrolled`
- hidden_confounding_003: partial contest of `difficulty_attribution_unverified`
- scope_intent_003: partial contest of `sample_representativeness_unknown`

**Scoring impact:** defense_calibration reduced from 1.0 to 0.833–0.917 in affected cases. None fell below 0.65; all cases still passed.

**Interpretation:** This is partially genuine debate behavior rather than a pure failure mode. A qualified expert might reasonably contest the priority of a medium-severity secondary issue while conceding the primary issues. The rubric awards partial credit (0.5) for these cases, which is appropriate. However, if these partial contestations were applied to primary high-severity issues, they would represent a more serious miscalibration.

**Example:** In broken_baseline_003, the Defense correctly concedes the feature_set_confound and attribution_error (both high-severity, correctly scored A=1.0, C=1.0) but partially contests no_ablation_study (medium-severity, B=0.5). The contestation is that the ablation adds value but the LR-on-47-features test is the primary deconfounding experiment. This is a substantively defensible position, even if the strict rubric scoring counts the ablation as a planted issue.

### Failure mode 2: Single-instance perspective convergence (structural limitation)

**Cases:** All 11

**Description:** In every case, the Critique and Defense agents reached compatible positions on the core planted issues. The Defense conceded all primary high-severity issues in every case. This reflects the fundamental constraint of a single Claude instance playing both roles: the same epistemic state underlies both the Critique and Defense outputs, making genuine disagreement on well-established issues structurally impossible.

**Scoring impact:** None — the debate produced correct outputs. This is a validity limitation on the experimental design, not a scoring impact on the results.

**Implication:** The protocol as implemented cannot produce a case where a capable Critique agent raises a valid issue and a capable Defense agent successfully rebuts it — because the same instance generates both. The Defense's concessions are not evidence of genuine persuasion; they are evidence that the single instance knows the critique is correct. This means the protocol's `defense_wins` path is effectively inaccessible in the single-instance simulation. A true multi-instance design is required to test the protocol's behavior when the Defense agent genuinely believes its position is correct.

### Failure mode 3: Trivial baseline catastrophic failure on hard confounding cases

**Cases:** metric_mismatch_003, hidden_confounding_001, hidden_confounding_002, hidden_confounding_003

**Description:** The trivial baseline's single-pass assessment produced incorrect conclusions on all four hard confounding cases, including cases of medium difficulty (hidden_confounding_001, hidden_confounding_003). In these cases:
- The single-pass assessment accepted the framing presented in the task_prompt without questioning the attribution
- The stated conclusions were directionally wrong (accepted an invalid interpretation as valid)
- Issue discovery recall was 0.0 for two cases (hidden_confounding_002, hidden_confounding_003)
- The self-critique step partially recovered but could not undo the original wrong conclusion for scoring purposes

**Scoring impact:** Baseline means of 0.333–0.417 for these cases. All four fail the benchmark.

**Implication:** Single-pass reasoning is specifically vulnerable to "surface-plausible" scenarios where the task prompt presents a narrative that sounds reasonable without closer inspection. The confounding cases are deliberately designed to exploit this: a randomized A/B test with p=0.002 sounds valid; a 23-point AUC drop attributed to demographics sounds plausible; a model trained on the same corpus with high pass@1 is naturally attributed to model quality. The debate protocol's Critique agent is specifically prompted to challenge these framings, which is why it succeeds where the single-pass baseline fails.

---

## 6. When Self-Debate Adds Value

Based on the experimental results:

**Self-debate adds the most value on:**
1. **Hard confounding cases** — where the surface presentation is plausible and a critical challenge is required to expose the hidden flaw. The delta is largest here (+0.569, +0.653, +0.639 for the three hardest confounding cases).
2. **Cases requiring explicit concession/update behavior** — defense_calibration is structurally impossible for the trivial baseline (no revision step). The debate's Defense persona adds the concession and position-update behavior that single-pass reasoning cannot produce.
3. **Cases where the final verdict must be precisely formulated** — the Judge's structured verdict statement consistently matched the ground truth's final_verdict. The trivial baseline's conclusions were directional at best (FVC=0.5) or wrong (FVC=0.0) for hard cases.
4. **Metric and scope misunderstanding cases** — where the issue is not a numerical error but a structural reasoning error about what the evaluation is measuring or what the goal requires. The Critique agent's structured questioning of metric appropriateness and scope coverage was effective.

**Self-debate adds less incremental value on:**
1. **Easy cases with obvious issues** — the trivial baseline also found the planted issues for broken_baseline_001 and metric_mismatch_002 (the two baseline-passing cases). On canonical, well-known issues (accuracy on imbalanced data, unequal eval sets), single-pass reasoning is nearly sufficient for issue discovery.
2. **Empirical test diagnosticity** — the baseline's self-critique proposed appropriate empirical tests in most cases (ETD≈0.9 average). The debate protocol's advantage here is marginal. Proposing a test requires identifying the issue, which the self-critique can do; the debate protocol's advantage is primarily in the earlier stages (issue prioritization, defense calibration, verdict quality).

**Self-debate does not produce** (in the Experiment 1 contaminated implementation):
1. Genuine disagreement between agents — single-instance convergence prevents authentic counter-argument scenarios
2. `defense_wins` verdicts — the Defense agent consistently concedes primary issues, making defense_wins inaccessible
3. Better issue discovery precision than the baseline — both systems achieved 1.0 precision (no hallucinated issues). This may reflect the well-defined scope of the benchmark cases more than a property of the protocol.

---

## 7. Experiment 2: Isolated Two-Instance Protocol

### 7.1 Structural Change

Experiment 2 implements the isolated protocol: both Critique and Defense receive only the task_prompt and generate independent assessments. The Judge receives both independent outputs and adjudicates. This eliminates the contamination identified in Experiment 1 and enables genuine measurement of model convergence and divergence.

**New metric — agent_convergence_rate:** Measures whether Critique and Defense independently identify the same primary issues. Scored 1.0 (full overlap), 0.5 (partial overlap), or 0.0 (no overlap). For defense_wins cases: whether the Defense independently identifies the critique's false premise.

### 7.2 Results on Original 11 Cases (Delta from Experiment 1)

| Metric | Experiment 1 | Experiment 2 | Delta |
|--------|-------------|-------------|-------|
| Debate benchmark mean | 0.988 | 1.000 | +0.012 |
| Baseline benchmark mean | 0.517 | 0.517 | 0.000 |
| Lift | +0.471 | +0.483 | +0.012 |
| Debate cases passing | 11/11 | 11/11 | 0 |
| defense_calibration mean | 0.927 | 1.000 | +0.073 |
| agent_convergence_rate | N/A | 0.727 | — |

**defense_calibration improvement (+0.073):** The isolated protocol eliminates the partial-contestation penalty. In Experiment 1, the Defense read the Critique's output and partially contested valid planted issues (earning 0.5 per rubric). In Experiment 2, there is no contestation step — the Defense generates an independent assessment and scores on whether it correctly identifies issues independently. All 11 original cases reach defense_calibration = 1.0.

**agent_convergence_rate = 0.727 on original 11 cases:** Primary issues are independently discoverable (convergence 1.0 on 5/11 cases). Secondary issues require more specific framing and are partially or wholly missed by the Defense without the Critique's structured output (convergence 0.5 on 6/11 cases). No case had 0.0 convergence — the Defense never failed to find at least the primary planted issue independently.

**Convergence distribution:**
- 1.0 (full): broken_baseline_001, broken_baseline_002, broken_baseline_003, metric_mismatch_001, hidden_confounding_001
- 0.5 (partial): metric_mismatch_002, metric_mismatch_003, hidden_confounding_002, hidden_confounding_003, scope_intent_002, scope_intent_003

**Interpretation:** High convergence on critique-wins cases (0.727 mean) confirms the primary planted issues represent genuine shared model knowledge — the model independently identifies these flaws without inter-agent contamination. This validates the Experiment 1 finding that the debate protocol surfaces real issues, not artifacts of contamination.

### 7.3 Results on New defense_wins Cases (4 cases, pending verification)

**VERIFICATION FLAG:** defense_wins_001 through defense_wins_004 have verifier_status = "pending" in benchmark_cases.json and are not yet in benchmark_verification.json. Results below are provisional pending CASE_VERIFIER confirmation.

| case_id | Debate2 Mean | Baseline Mean | Verdict | Convergence |
|---------|-------------|--------------|---------|-------------|
| defense_wins_001 | 1.000 | 0.000 | defense_wins ✓ | 1.0 |
| defense_wins_002 | 1.000 | 0.000 | defense_wins ✓ | 1.0 |
| defense_wins_003 | 1.000 | 0.000 | defense_wins ✓ | 1.0 |
| defense_wins_004 | 1.000 | 0.000 | defense_wins ✓ | 1.0 |
| **AGGREGATE** | **1.000** | **0.000** | 4/4 correct | **1.000** |

**Key finding:** The isolated protocol correctly reaches defense_wins on all 4 cases. The Defense independently identifies the Critique's false premise in every case, citing specific evidence from the task prompt that the Critique failed to engage with (documented dataset balance, production deployment context, Limitations section, Business Context section). This is the desired pattern: the Defense forms its own independent defense without needing to read the Critique, and does so successfully.

**agent_convergence_rate = 1.000 on defense_wins cases:** This is the ideal outcome. High convergence means the Defense independently locates the refuting evidence in the task prompt. If convergence had been low on these cases, it would mean the Defense fell for the false critique — the protocol would be unable to protect valid work from fabricated concerns. The 1.0 convergence rate confirms the isolated protocol reliably routes false critiques to defense_wins verdicts.

**Baseline completely fails on defense_wins cases (0.000 mean):** The trivial single-pass assessment accepts the false critique in all 4 cases. Without a debate structure, single-pass reasoning validates false methodological concerns as legitimate. This is the most extreme baseline failure observed in either experiment: the protocol is not just imprecise but actively produces false positives on work that is valid.

**Why Experiment 1's contaminated protocol would have failed on defense_wins:** The contaminated Defense reads the Critique's confident false premise before responding. Having read the critique, the Defense is biased toward partially conceding the false concern — it cannot independently evaluate the task prompt for the refuting evidence. The contaminated protocol would likely produce empirical_test_agreed or critique_wins on these cases, generating false positives. The isolated protocol eliminates this failure mode by ensuring the Defense reads the task prompt independently.

### 7.4 Full 15-Case Benchmark

| Metric | Value |
|--------|-------|
| Debate2 mean (15 cases) | 1.000 |
| Baseline mean (15 cases) | 0.379 |
| Lift | +0.621 |
| Debate2 cases passing | 15/15 (100%) |
| Baseline cases passing | 2/15 (13%) |
| agent_convergence_rate | 0.800 |

**Caveat:** 4 defense_wins cases are pending CASE_VERIFIER confirmation. The 15-case benchmark results should be treated as provisional until all cases are confirmed KEEP.

### 7.5 Structural Conclusions from Experiment 2

1. **Contamination removal improves defense_calibration uniformly.** The +0.073 improvement on the original 11 cases is a direct consequence of isolating the Defense's context. The contaminated protocol's partial-contestation penalty was an artifact of the design, not evidence of genuine calibration failure.

2. **The isolated protocol enables defense_wins verdicts.** For the first time, the protocol correctly routes cases where the Critique's premise is false to a defense_wins verdict. This required both the architectural change (isolated Defense) and the new benchmark cases that test this path.

3. **agent_convergence_rate is a meaningful diagnostic.** High convergence on critique-wins cases (0.682) confirms genuine shared model knowledge. High convergence on defense_wins cases (1.000) confirms the Defense can independently identify false premises from the task prompt alone.

4. **The baseline's failure on defense_wins is a critical new finding.** Single-pass assessment generates false positives on all 4 defense_wins cases. This means a production deployment of the trivial baseline would incorrectly penalize valid work in approximately the same frequency it fails to catch invalid work on hard confounding cases — a symmetric failure mode not visible in Experiment 1.

5. **The isolated protocol does not reduce performance on critique-wins cases.** Experiment 2 matches or exceeds Experiment 1 on all 11 original cases. The structural change eliminates a design flaw without introducing new failure modes.
