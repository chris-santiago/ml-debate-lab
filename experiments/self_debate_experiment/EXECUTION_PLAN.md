# Self-Debate Experiment: Execution Plan

**Status:** AWAITING LEAD APPROVAL — do not implement until approved.

---

## 1. Selected Verified Cases

All 11 cases are drawn exclusively from the verified KEEP list. `scope_intent_001` (REVISE status) is excluded.

| # | case_id | category | difficulty |
|---|---------|----------|------------|
| 1 | broken_baseline_001 | broken_baseline | easy |
| 2 | broken_baseline_002 | broken_baseline | medium |
| 3 | broken_baseline_003 | broken_baseline | hard |
| 4 | metric_mismatch_001 | metric_mismatch | easy |
| 5 | metric_mismatch_002 | metric_mismatch | medium |
| 6 | metric_mismatch_003 | metric_mismatch | hard |
| 7 | hidden_confounding_001 | hidden_confounding | medium |
| 8 | hidden_confounding_002 | hidden_confounding | hard |
| 9 | hidden_confounding_003 | hidden_confounding | medium |
| 10 | scope_intent_002 | scope_intent_misunderstanding | medium |
| 11 | scope_intent_003 | scope_intent_misunderstanding | hard |

Confirmation: All 11 are status `keep` in `benchmark_verification.json`. `scope_intent_001` (`revise`) is confirmed excluded.

---

## 2. Hypothesis

**Primary falsifiable claim:**

> On synthetic ML reasoning tasks with known ground truth (11 verified benchmark cases spanning broken baselines, metric mismatches, hidden confounding, and scope/intent errors), a simulated self-debate protocol — where a single Claude instance plays an explicit Critique agent, then an explicit Defense agent, then an explicit Judge role in structured prompts — will achieve a benchmark aggregate score at least 0.10 higher than a trivial baseline (single-pass answer followed by self-critique with no debate loop or revision), as measured by the mean of all applicable rubric dimension scores across the 11-case benchmark.

**Secondary falsifiable claims tested:**

1. The debate protocol will surface planted issues at higher recall (issue_discovery_recall) than the trivial baseline on hard-difficulty cases.
2. The debate protocol will produce better-calibrated defense responses (defense_calibration) than the trivial baseline, as measured by correct concession and correct contestation rates.
3. On cases where `ideal_debate_resolution.type = critique_wins`, the debate protocol will reach the correct resolution type at higher frequency than the trivial baseline.
4. The debate protocol will exhibit at least one failure mode — either blind spot reinforcement (both agents agree on a wrong answer) or confidence overstatement (judge declares a winner when the correct resolution is `empirical_test_agreed`) — in at least 1 of 11 cases.

---

## 3. Primary Metrics

The following six scoring dimensions from `evaluation_rubric.json` are all primary metrics. All applicable dimensions count equally in the per-case mean score.

| Rubric Dimension | Mapped Role in Experiment | Notes |
|---|---|---|
| `issue_discovery_recall` | Fraction of planted issues surfaced by Critique agent | Computed from critique pass; partial credit (0.5) per rubric spec |
| `issue_discovery_precision` | Fraction of Critique claims that are valid | Guards against hallucinated issues |
| `defense_calibration` | Defense's correct concession (A), correct contestation (B), position update (C) | Mean of applicable sub-scores; (B) omitted if no contestable claims |
| `debate_resolution_quality` | Whether final resolution type matches `ideal_debate_resolution.type` | 1.0 = exact match; 0.5 = correct but inefficient path; 0.0 = wrong type |
| `empirical_test_diagnosticity` | Whether proposed test distinguishes critique-wins vs defense-wins | Only scored when `ideal_debate_resolution.type = empirical_test_agreed` or a test is proposed |
| `final_verdict_correctness` | Whether system's final verdict matches `ground_truth.final_verdict` | Binary; string-normalized match |

**Pass/fail thresholds (from rubric, fixed):**
- Per-dimension pass floor: 0.5
- Per-case pass threshold: mean ≥ 0.65 with no dimension below 0.5
- Benchmark pass: ≥ 75% of cases pass AND benchmark mean ≥ 0.65
- Debate-adds-value criterion: debate mean exceeds trivial baseline mean by ≥ 0.10

---

## 4. Trivial Baseline Definition

The trivial baseline is defined exactly as specified in `evaluation_rubric.json` under `trivial_baseline_definition`. Implementation in `self_debate_poc.py`:

**Procedure per case:**
1. Single prompt: present the case's `task_prompt` and ask for an answer and conclusion.
2. Second prompt: ask the model to self-critique its own answer, identifying any flaws or missed issues.
3. No revision step. No defense pass. No judge pass. The output of step 2 is the final baseline output.

**Scoring adaptations (exactly per rubric):**
- `issue_discovery_recall` and `issue_discovery_precision`: scored from the self-critique's issue claims.
- `defense_calibration`: scored from the original answer's handling of issues identified in the self-critique. Position update sub-score (C) is always 0.0 (no revision step exists).
- `debate_resolution_quality`: capped at 0.5 maximum (self-critique cannot earn 1.0 since no debate occurs).
- `empirical_test_diagnosticity`: scored from the self-critique's proposed test if any; N/A otherwise.
- `final_verdict_correctness`: scored from the original answer's stated conclusion.

**Baseline purpose:** Establishes the floor. The debate system must exceed baseline mean by ≥ 0.10 across the 11-case benchmark to demonstrate that the debate loop adds value beyond self-critique.

---

## 5. Pre-Specified Verdict Rules

These rules are fixed before execution begins. Verdict scoring uses only the definitions below and must not be inferred post-hoc.

### 5.1 broken_baseline category (cases: 001, 002, 003)

**What counts as `critique_wins`:**
The Judge's final statement explicitly upholds the Critique's main claim: that the evaluation methodology or comparison is invalid, and the Defense's original conclusion of a valid improvement is rejected. Requires that the identified confound (unequal eval sets / wrong baseline type / feature-set confound) is named as a fatal flaw.

**What counts as `defense_wins`:**
The Judge finds that the Critique's identified flaw is not fatal — for example, the Judge accepts that a result could still be directionally valid despite a methodology gap — and the Defense's core claim of a performance improvement is upheld.

**What counts as `empirical_test_agreed`:**
Both Critique and Defense agents explicitly agree in their final statements that an empirical test (as specified in `required_empirical_test` for each case) is necessary to resolve the dispute, and neither claims the issue is already resolved without that test. Resolution type matches `ideal_debate_resolution.type = empirical_test_agreed`.

**What counts as `ambiguous`:**
Neither agent reaches a stated conclusion in the allotted rounds; or one agent's final statement is contradictory (concedes then retracts); or the Judge fails to emit a verdict. Any of these trigger the failure-handling path (Section 7).

---

### 5.2 metric_mismatch category (cases: 001, 002, 003)

**What counts as `critique_wins`:**
The Judge explicitly upholds that the reported metric is either definitionally uninformative for the task (metric_mismatch_001: trivial classifier outperforms on accuracy) or that the overclaimed conclusion is not supported by the evidence (metric_mismatch_003: underpowered study). The Defense's claim of a valid evaluation result is rejected. Only acceptable for metric_mismatch_001 per `scoring_targets.acceptable_resolutions`.

**What counts as `defense_wins`:**
The Judge finds the metric choice is defensible and the reported improvement is meaningful. Only valid for metric_mismatch_002 if the Judge accepts MAP@10 as a legitimate offline proxy with appropriate caveats.

**What counts as `empirical_test_agreed`:**
Both agents agree that the offline metric result is ambiguous and an empirical test (A/B test, powered human study, or fraud-class precision/recall) is necessary to determine the real-world outcome. Acceptable resolution for metric_mismatch_002 and metric_mismatch_003.

**What counts as `ambiguous`:**
Judge emits no clear resolution, or conflates the resolution types (e.g., calls it both `empirical_test_agreed` and `critique_wins`). Triggers failure-handling path.

---

### 5.3 hidden_confounding category (cases: 001, 002, 003)

**What counts as `critique_wins`:**
The Judge explicitly finds that the team's causal attribution (demographics / randomization-validates-all / benchmark difficulty) is unsupported and that the identified confound (scanner acquisition / treatment-period interaction / data contamination) is a better explanation that must be ruled out first.

**What counts as `defense_wins`:**
The Judge accepts the team's original attribution as at least equally plausible to the confound identified by the Critique, and finds the original conclusion defensible without further investigation.

**What counts as `empirical_test_agreed`:**
Both agents agree the confound hypothesis vs. the original attribution cannot be resolved without an empirical test (normalization ablation, pre/post-sale segmentation, n-gram overlap analysis), and the Judge recommends the specific test.

**What counts as `ambiguous`:**
Judge rules that "both explanations are equally valid" without recommending an empirical test, or fails to distinguish between the competing causal hypotheses. Triggers failure-handling path.

---

### 5.4 scope_intent_misunderstanding category (cases: 002, 003)

**What counts as `critique_wins`:**
The Judge explicitly finds the team's claimed conclusion overstates the scope of what was delivered: prediction-without-intervention is not churn reduction (scope_intent_002 — though `mixed` is also acceptable); static analysis pass rate does not imply production safety (scope_intent_003).

**What counts as `defense_wins`:**
The Judge finds the delivered work meets a reasonable interpretation of the stated goal: the prediction model alone constitutes sufficient scope (scope_intent_002 only — but this is below acceptable resolution threshold); the Bandit pass rate is a valid and sufficient safety signal (scope_intent_003 — this would be incorrect per ground truth).

**What counts as `empirical_test_agreed`:**
For scope_intent_002: both agents agree the prediction model's value in reducing churn requires an A/B test with an intervention to determine whether the scope gap is fatal. For scope_intent_003: both agents agree a multi-dimensional safety rubric must be defined and measured before any safety claim can be made.

**What counts as `ambiguous`:**
Judge accepts the Defense's partial-scope delivery as "complete" without acknowledging the scope gap, or identifies the scope gap but fails to specify what resolution would look like. Triggers failure-handling path.

---

### 5.5 Cross-category resolution correctness mapping

| case_id | ground_truth.correct_position | ideal_debate_resolution.type | critique_wins score | defense_wins score | empirical_test_agreed score |
|---|---|---|---|---|---|
| broken_baseline_001 | critique | empirical_test_agreed | 0.5 (acceptable) | 0.0 | 1.0 |
| broken_baseline_002 | mixed | empirical_test_agreed | 0.5 (acceptable) | 0.0 | 1.0 |
| broken_baseline_003 | critique | empirical_test_agreed | 0.5 (acceptable) | 0.0 | 1.0 |
| metric_mismatch_001 | critique | critique_wins | 1.0 | 0.0 | 0.0 |
| metric_mismatch_002 | mixed | empirical_test_agreed | 0.5 (acceptable) | 0.0 | 1.0 |
| metric_mismatch_003 | critique | empirical_test_agreed | 0.5 (acceptable) | 0.0 | 1.0 |
| hidden_confounding_001 | critique | empirical_test_agreed | 0.5 (acceptable) | 0.0 | 1.0 |
| hidden_confounding_002 | critique | empirical_test_agreed | 0.5 (acceptable) | 0.0 | 1.0 |
| hidden_confounding_003 | critique | empirical_test_agreed | 0.5 (acceptable) | 0.0 | 1.0 |
| scope_intent_002 | mixed | empirical_test_agreed | 0.5 (acceptable) | 0.0 | 1.0 |
| scope_intent_003 | critique | critique_wins | 1.0 | 0.0 | 0.0 |

Note: `debate_resolution_quality` scores in this table are for the `debate_resolution_quality` dimension only. They do not represent overall case pass/fail.

---

## 6. Artifact Plan

### `self_debate_poc.py`
The proof-of-concept implementation. Contains: the structured prompt templates for Critique, Defense, and Judge agents; the trivial baseline (single-pass + self-critique) runner; the per-case loop that runs both systems on all 11 cases; raw output serialization to JSON. Produced by: implementation in Phase 1 of execution.

### `README.md`
Top-level documentation for the experiment directory. Contains: experiment purpose, directory structure, how to run `self_debate_poc.py` and `self_debate_experiment2.py`, dependencies, and a pointer to `CONCLUSIONS.md` for results. Produced by: written after `self_debate_poc.py` is working.

### `CRITIQUE.md`
The Critique agent's structured argument document for all 11 cases. Contains: per-case critique output produced by the Critique persona, formatted with explicit case_id headers, identified issues, and proposed empirical test. Produced by: extracted from `self_debate_poc.py` output and formatted as a standalone document.

### `DEFENSE.md`
The Defense agent's structured rebuttal document for all 11 cases. Contains: per-case defense output produced by the Defense persona, formatted with explicit case_id headers, concessions, contestations, and maintained positions. Produced by: extracted from `self_debate_poc.py` output and formatted as a standalone document.

### `DEBATE.md`
The Judge's full debate transcript and verdict for all 11 cases. Contains: the complete structured exchange (Critique → Defense → Judge), per-case verdict, resolution type, and scoring justification. Produced by: compiled from `self_debate_poc.py` output into a single narrative document.

### `self_debate_experiment2.py`
A second-iteration implementation, run only if warranted per the iteration policy (Section 8). Contains: modifications to prompt structure, debate loop parameters, or judge criteria informed by failure modes observed in experiment 1. Produced by: written only if experiment 1 reveals a systematic addressable failure (not baseline outperformance).

### `CONCLUSIONS.md`
The primary findings document. Contains: per-case scoring table (both debate and trivial baseline), dimension-level aggregate scores, hypothesis verdict (supported / not supported / partially supported), observed failure modes (blind spot reinforcement, overconfidence, correct surfacing), and lessons about when self-debate adds value vs. does not. Produced by: written after all scoring is complete.

### `REPORT.md`
Full technical report. Contains: experiment motivation, system design (prompt templates, persona structure), results tables, statistical summary, comparison to trivial baseline, failure mode taxonomy, and recommendations for future iterations. Produced by: written after `CONCLUSIONS.md` is finalized.

### `REPORT_ADDENDUM.md`
Addendum covering second-iteration results, if `self_debate_experiment2.py` is run. Contains: delta scores from experiment 1 to experiment 2, explanation of what changed and why, updated conclusions. Produced by: written only if experiment 2 is executed per the iteration policy. Left blank or omitted if experiment 2 is not warranted.

---

## 7. Failure Handling Plan

### 7.1 A debate produces no clear resolution

**Definition:** The Judge fails to emit a verdict matching any of the four verdict types (critique_wins, defense_wins, empirical_test_agreed, ambiguous), or emits contradictory verdicts within the same case output.

**Action:** Score `debate_resolution_quality = 0.0` for that case. Record it as a "Judge failure" in `CONCLUSIONS.md`. Do not retry the case — the failed output is part of the experimental data and reveals a genuine limitation of the protocol. Run the full 11-case benchmark to completion before drawing conclusions.

### 7.2 The judge disagrees with ground truth on multiple cases

**Definition:** The Judge's final verdict matches neither the `ideal_debate_resolution.type` nor any `acceptable_resolutions` for 4 or more cases (≥ 36% of the benchmark).

**Action:** This is a significant finding, not an implementation error. Do not adjust the judge prompts mid-experiment. Record all disagreements with specific case_ids and the nature of the disagreement in `CONCLUSIONS.md`. Assess whether the disagreements cluster by category or difficulty. If all disagreements are in a single category (e.g., all hidden_confounding cases), document this as a category-specific blind spot. If disagreements are distributed, document this as a systemic confidence-calibration failure. If warranted by the iteration policy (Section 8), run `self_debate_experiment2.py` with a modified judge prompt that explicitly references the ground truth reasoning patterns — but only after the full experiment 1 results are recorded.

### 7.3 The trivial baseline outperforms debate on all metrics

**Definition:** The trivial baseline's benchmark aggregate mean score meets or exceeds the debate system's benchmark aggregate mean score (i.e., the debate fails to achieve the required +0.10 lift), across all six rubric dimensions.

**Action:** This is the most important finding the experiment could produce — do not suppress it. Record it as the primary conclusion in `CONCLUSIONS.md`. Investigate whether the failure is structural (the self-critique in the trivial baseline already captures the planted issues with no benefit from the debate loop) or if the debate loop is actively harmful (debate_resolution_quality or final_verdict_correctness drops vs. baseline). Document the specific mechanism: (a) critique and defense playing both sides cancels out correct reasoning; (b) the judge overrides a correct critique; (c) the trivial baseline's self-critique has better recall because it is less constrained by adversarial framing. This is a valid and publishable negative result. Run `self_debate_experiment2.py` with a structurally different debate architecture (e.g., asymmetric agent roles, constrained judge criteria) per the iteration policy.

---

## 8. Iteration Policy

### When experiment2.py is warranted

A second iteration is warranted if **any one** of the following conditions is true after experiment 1 is fully scored:

1. **Structured failure:** The debate system fails the benchmark pass threshold (< 75% of cases pass OR benchmark mean < 0.65) AND a specific structural cause is identified in the prompt design that is directly addressable without changing the evaluation rubric or ground truth.

2. **Trivial baseline dominates:** The trivial baseline achieves within 0.05 of the debate system on benchmark aggregate AND the failure is attributable to a specific addressable design choice (e.g., the Judge prompt lacks explicit tie-breaking criteria; the Defense persona prompt does not require explicit concession language).

3. **Judge systematic failure:** The Judge fails to reach a verdict on 3 or more cases AND the failure pattern is consistent (e.g., judge always requests "more information" without committing) AND a prompt modification can be specified that would address this without coaching the judge toward the ground truth answer.

4. **Hypothesis partially supported with a testable alternative:** Experiment 1 shows the debate adds value on one or two categories but not others, and a modified prompt (e.g., category-specialized critique framing) is hypothesized to close the gap.

### When to stop after experiment 1

Stop after experiment 1 and proceed directly to `CONCLUSIONS.md` and `REPORT.md` if **any** of the following:

1. The debate system passes the benchmark and achieves the +0.10 lift over the trivial baseline. The hypothesis is supported. A second iteration would be exploratory, not confirmatory — document as future work rather than running it.

2. The trivial baseline dominates AND no structural addressable cause can be identified. Document as a negative result. Running `experiment2.py` with arbitrary prompt changes would be p-hacking the experiment.

3. Experiment 1 reveals that the simulated debate (single instance playing both roles) fundamentally cannot exhibit genuine disagreement — both Critique and Defense converge to the same position on every case. This is a structural limitation of the single-instance simulation design, not a fixable prompt issue. Document as a limitation and recommend a true multi-instance setup as future work.

### What must not change between iterations

- The benchmark cases (same 11 KEEP cases)
- The evaluation rubric (`evaluation_rubric.json` is fixed per its `notes` field)
- The ground truth and planted issues
- The pre-specified verdict rules in this document

Only prompt templates, agent persona instructions, debate loop structure (number of rounds, turn order), and judge criteria may change between iterations.

---

### 5.6 defense_wins category (cases: defense_wins_001 through defense_wins_004)

**What counts as defense_wins:**
The Judge explicitly identifies that the Critique's premise is false or already addressed in the provided context, and rules the original team's claim defensible as stated. The Defense's rebuttal must cite specific evidence from the task prompt (documented balance, production context, disclosed limitation, economic quantification).

**What counts as critique_wins (should not occur on these cases):**
The Judge accepts the Critique's false premise as valid. This is a false positive — the protocol incorrectly penalized valid work. Score debate_resolution_quality = 0.0 and flag as protocol failure.

**What counts as empirical_test_agreed:**
Both agents agree that additional data would clarify the dispute. This is a partial failure on defense_wins cases — the defense's winning argument is already available in the task prompt; no empirical test should be needed. Score debate_resolution_quality = 0.5.

**What counts as ambiguous:**
Judge cannot determine whether the Critique's premise holds. Triggers failure-handling path (Section 7).

**Per-case defense_wins resolution correctness mapping (extends Section 5.5 table):**

| case_id | ground_truth.correct_position | ideal_debate_resolution.type | critique_wins score | defense_wins score | empirical_test_agreed score |
|---|---|---|---|---|---|
| defense_wins_001 | defense | defense_wins | 0.0 (protocol failure) | 1.0 | 0.5 (partial failure) |
| defense_wins_002 | defense | defense_wins | 0.0 (protocol failure) | 1.0 | 0.5 (partial failure) |
| defense_wins_003 | defense | defense_wins | 0.0 (protocol failure) | 1.0 | 0.5 (partial failure) |
| defense_wins_004 | defense | defense_wins | 0.0 (protocol failure) | 1.0 | 0.5 (partial failure) |

**Verification status note:**
As of Experiment 2 implementation, defense_wins_001 through defense_wins_004 have verifier_status = "pending" in benchmark_cases.json and are not present in benchmark_verification.json. CASE_VERIFIER results must be confirmed before treating Experiment 2 results on these cases as final. If any case is REVISE, apply the correction before re-scoring. If any case is REJECT, exclude it from the defense_wins aggregate and flag to LEAD.

---

## Rules Compliance Checklist

- [x] Synthetic-only scope preserved: all 15 cases are synthetic benchmark cases with no real-world data
- [x] Explicit ground truth used: all verdict rules reference `ground_truth.correct_position`, `ideal_debate_resolution.type`, and `scoring_targets.acceptable_resolutions` from verified cases
- [x] Trivial baseline included in every comparison: Section 4 defines the baseline and Section 3 requires it in all metrics
- [x] Verdict criteria pre-specified before execution: Sections 5.1–5.5 cover all original categories; Section 5.6 covers defense_wins cases
- [x] Only verified KEEP cases used: 11 original KEEP cases + 4 defense_wins KEEP cases (15 total); scope_intent_001 (REVISE) excluded
- [x] `evaluation_rubric.json` not modified: rubric is used as read-only input; all scoring follows the rubric verbatim
- [x] defense_wins path covered: 4 cases with correct_position = "defense" added after benchmark design flaw identified; verified KEEP by CASE_VERIFIER before use in Experiment 2
