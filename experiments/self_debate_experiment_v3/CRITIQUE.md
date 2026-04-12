# CRITIQUE.md — Self-Debate Protocol v3 Experimental Design

**Role:** ml-critic (Mode 1, initial critique)
**Inputs:** HYPOTHESIS.md, PREREGISTRATION.json, evaluation_rubric.json
**Target:** The v3 experimental design itself — its claims, metrics, and validity

---

## Critique — Cycle 1

The following issues are organized by root cause. Each entry states the claim being made, the mechanism by which it could be wrong, and what evidence would settle it.

---

### Root Cause A: Measurement Infrastructure — DC Conflation

**Issue 1 — DC is structurally identical to FVC in isolated_debate and ensemble conditions**

*Claim being made:* DC (Debate Coverage) and FVC (Final Verdict Correctness) are reported as distinct dimensions, contributing separately to the case mean and to the pass/fail determination.

*Why it might be wrong:* The dc_note in PREREGISTRATION.json concedes this directly: "In isolated_debate and ensemble conditions, DC is structurally identical to FVC for non-baseline." Both use the same `compute_fvc` function with the same arguments. A case mean that includes DC and FVC as two separate dimensions is double-counting one signal when they are identical. This inflates scores mechanically — not because the protocol is performing better, but because the same correct verdict is counted twice.

*What would settle it:* Remove DC from the case mean calculation for isolated_debate and ensemble conditions and recompute benchmark means. If the aggregate drops materially (>0.03), the inflation is non-trivial and the pre-registered threshold of 0.65 may be inflated relative to what a four-distinct-dimension rubric would produce. The PREREGISTRATION.json acknowledges this but does not pre-specify a corrected mean or adjusted threshold. This is an omission, not a feature.

---

**Issue 2 — The v3 rubric measures 4 distinct dimensions on non-defense_wins/non-mixed cases, not 6**

*Claim being made:* The six-dimension rubric (IDR, IDP, DC, DRQ, ETD, FVC) is the operative scoring framework for all cases.

*Why it might be wrong:* ETD is null on critique_wins and defense_wins cases. IDR and IDP are null on defense_wins cases. DC equals FVC in isolated_debate/ensemble. The effective dimensionality for a typical critique_wins case in isolated_debate is: IDR, IDP, DRQ, FVC — with DC a duplicate of FVC and ETD null. That is 4 values, two of which are mechanically correlated. The six-dimension framing overstates the independence of the rubric's coverage.

*What would settle it:* Pre-specify the effective dimension count per case type and condition. Show the mean formula with the actual non-null, non-duplicate dimensions in play. The benchmark_passes threshold was calibrated against the full six-dimension rubric concept. If the operative rubric is effectively three or four independent dimensions, the threshold calibration needs reexamination.

---

### Root Cause B: Isolation Architecture — the Central Empirical Claim

**Issue 3 — Isolated debate is two parallel critics, not a debate**

*Claim being made:* The isolated self-debate protocol produces "adversarial role separation" that "forces engagement with both sides of each case."

*Why it might be wrong:* In the isolated condition, both ml-critic and ml-defender receive only the task prompt. Neither agent sees the other's output before producing its verdict. This is not adversarial role separation — it is two independent single-pass assessors with different system prompts. The Defender cannot concede, rebut, or mark issues as empirically open because there are no issues to respond to. The "forcing function" claimed in HYPOTHESIS.md Mechanism section requires the agents to interact with each other's reasoning. That does not happen in the isolated condition.

*What would settle it:* The dc_note already concedes this. The experiment calls this isolation a "benchmark-specific design choice, not the ml-lab protocol." But HYPOTHESIS.md claims the mechanism is adversarial role separation. If the mechanism is actually "two independent assessors with asymmetric instructions," the hypothesis and mechanism statement should say that. The evidence needed: does the Defender's output in isolated_debate show any engagement with opposing arguments — or is it structurally indistinguishable from a second Critic run with a different system prompt? Compute the text-overlap / verdict-correlation between Critic and Defender outputs in the isolated condition. High correlation indicates the "adversarial" claim is unfounded.

---

**Issue 4 — The +0.10 lift threshold was not derived from a power analysis**

*Claim being made:* A +0.10 lift over baseline constitutes meaningful improvement.

*Why it might be wrong:* 49 cases with 3 runs each gives within-case variance information, but the PREREGISTRATION.json does not report the expected variance of the benchmark mean or the minimum detectable effect at any confidence level. A lift of +0.10 on a benchmark mean may or may not be distinguishable from noise depending on the cross-case variance. If the standard deviation of case-level scores is ~0.15 (plausible given the 0.0/0.5/1.0 scoring grid), the standard error of the mean over 49 cases is ~0.021. A lift of +0.10 would be ~4.7 standard errors — likely significant. But this calculation is not pre-specified. The threshold could have been chosen post-hoc to be attainable.

*What would settle it:* A pre-specified power calculation or bootstrap confidence interval plan. The experiment does include stats_analysis.py, but the plan does not commit to a specific statistical test or alpha level before execution begins. The success criterion is point-estimate only — no confidence interval requirement.

---

### Root Cause C: Baseline Construction — Structural Overrides

**Issue 5 — The structural DC=0.0 override for baseline suppresses ambiguous cases**

*Claim being made:* Assigning DC=0.0 to all baseline cases is a "structural, not a reasoning penalty" that is fair and pre-registered.

*Why it might be wrong:* DC in the v3 rubric measures verdict correctness via a defense function. A baseline Critic that produces the correct verdict type (e.g., correctly identifies critique_wins) would score 0.0 on DC despite getting the verdict right. This means the baseline is penalized on DC regardless of its output quality. If DC and FVC are both included in the baseline mean, the baseline is structurally suppressed by one dimension — not because its outputs are wrong, but because it lacks a Defender role. Combined with DRQ capped at 0.5, this means two of the six rubric dimensions are structurally capped for baseline. The lift claim becomes: "debate outperforms a structurally handicapped baseline," which is not the same as "debate outperforms a compute-matched single-pass assessor."

*What would settle it:* The honest_lift calculation in PREREGISTRATION.json (DC=0.5 and DRQ uncapped for baseline) is the right corrected metric. The experiment commits to reporting both, which is correct. But the primary hypothesis threshold (+0.10) is stated against the raw lift, not the honest lift. The primary success criterion should be stated against the honest lift to avoid baseline suppression inflating the headline number.

---

**Issue 6 — Ensemble ETD constraint is pre-applied but not operationally specified**

*Claim being made:* The ensemble synthesizer will receive an explicit ETD constraint (measure / success_criterion / failure_criterion instruction) to control for the prompt-design effect found in v2.

*Why it might be wrong:* Phase 4 of the plan states the ETD constraint is pre-applied to ensemble synthesizer, but neither PREREGISTRATION.json nor evaluation_rubric.json specifies the exact instruction text. If the ETD constraint is implemented differently across runs (e.g., different prompt wording for the ensemble vs. the debate condition), the ETD comparison is confounded by prompt variation rather than structural difference. The v2 finding was that ETD advantage was prompt design, not adversarial architecture — this experiment claims to control for that, but the control is not locked down in the pre-registration.

*What would settle it:* Include the exact ETD constraint instruction text in EXECUTION_PLAN.md and commit it before any agent runs. Verify that the same instruction appears in ensemble prompts and that no equivalent instruction appears in isolated_debate prompts. Without this, the ETD comparison is not interpretable.

---

### Root Cause D: Benchmark Quality — External Validity

**Issue 7 — 49 cases from a single external generator with unknown generation protocol**

*Claim being made:* The benchmark_cases_verified.json (49 cases) provides a valid evaluation corpus for comparing debate architectures.

*Why it might be wrong:* All cases originated from one external model run (GPT-5.4 on Perplexity Computer). A single-source corpus may have systematic biases — consistent framing conventions, recurring must_find issue patterns, or vocabulary cues that correlate with ground-truth labels in ways that advantage a system prompt trained on similar data. If the Critic's system prompt shares distributional properties with the case generator, IDR scores may be inflated not because the debate protocol found issues, but because the Critic recognizes stylistic fingerprints of the case generator.

*What would settle it:* Cross-case correlation analysis: do must_find_issue_ids share vocabulary with task_prompt text in ways that a case from a different generator would not? The external_cases_v3.json set (from a different source) provides a partial control — compare IDR on synthetic vs. external cases. If IDR drops significantly on external cases, generator fingerprinting is plausible.

---

**Issue 8 — defense_wins category is a separate benchmark category, not a correct_position label**

*Claim being made:* "defense_wins" cases are cases where the correct position is that the methodology is sound and the critique is wrong.

*Why it might be wrong:* The benchmark has a category field named "defense_wins" AND a correct_position field. The observed distribution shows 11 cases with category="defense_wins" and 11 cases with correct_position="defense." These appear to be the same cases, but the category label leaks the correct_position to any agent that sees the case_id or category field. If category is passed to agents along with task_prompt, ground-truth leakage is possible. The case verifier checks for leakage from case_id and the first sentence of task_prompt, but may not have checked the category field itself.

*What would settle it:* Confirm that agent dispatch passes only the task_prompt field, not case metadata. Review the execution plan to verify that category, case_id format, and any other metadata fields are excluded from agent context. If category is passed, the leakage check is incomplete.

---

### Root Cause E: Multiround Condition — Protocol Coherence

**Issue 9 — Multiround DRQ hypothesis requires non-defense_wins cases only, but this is not enforced in scoring**

*Claim being made:* The secondary hypothesis H4 (multiround outperforms isolated on DRQ) is evaluated "across non-defense_wins cases."

*Why it might be wrong:* The scoring engine (self_debate_poc.py) computes aggregate means across all 49 cases, not a filtered subset. The secondary hypothesis criterion specifies "non-defense_wins cases" but the `main()` function computes `bm_multiround` over all cases. If defense_wins cases have systematically different DRQ distributions (they do — DC and IDR are null, making DRQ weight heavier in the mean), including them in the multiround vs. isolated DRQ comparison confounds the test.

*What would settle it:* The scoring engine should produce a filtered DRQ comparison: multiround_mean(DRQ) vs. isolated_mean(DRQ) on the 38 non-defense_wins cases separately. The plan mentions stats_analysis.py will handle this, but it is not pre-specified in the scoring engine or the success criterion. Lock down the filter before execution.

---

**Issue 10 — No convergence metric implementation is specified in the scoring engine**

*Claim being made:* PREREGISTRATION.json defines a convergence_metric (1.0 if critic_verdict == defender_verdict; 0.5 if they diverge) as a diagnostic for the isolated_debate condition.

*Why it might be wrong:* The scoring engine (self_debate_poc.py) has no convergence computation. The field is defined in PREREGISTRATION.json and noted as "Reported in CONCLUSIONS.md for isolated_debate condition," but no code implements it. If convergence is not computed during scoring, it cannot be reported in CONCLUSIONS.md without ad hoc post-processing. A diagnostic that is pre-registered but not implemented is a pre-registration gap.

*What would settle it:* Add convergence computation to score_run() or aggregate_runs() in self_debate_poc.py, reading critic_raw_verdict and defender_raw_verdict from the raw output files. Alternatively, specify the extraction script in EXECUTION_PLAN.md before execution begins.

---

## Summary

Ten issues identified, organized across five root causes:

| # | Root Cause | Issue | Severity |
|---|-----------|-------|---------|
| 1 | Measurement | DC=FVC double-counting in isolated/ensemble | High — inflates case mean |
| 2 | Measurement | Effective rubric is 3-4 dims, not 6 | Medium — threshold miscalibration risk |
| 3 | Isolation architecture | Isolated debate is two parallel critics | High — mechanism claim unfounded |
| 4 | Statistics | No power analysis for +0.10 threshold | Medium — threshold could be noise |
| 5 | Baseline | DC=0.0 override suppresses baseline unfairly | High — lift inflation |
| 6 | ETD control | ETD constraint not operationally locked | Medium — ETD comparison confounded |
| 7 | Benchmark quality | Single-source generator fingerprinting | Medium — IDR inflation possible |
| 8 | Benchmark quality | category field leaks correct_position | High — ground-truth leakage |
| 9 | Multiround | DRQ filter not enforced in scoring engine | Medium — hypothesis test confounded |
| 10 | Convergence | Convergence metric not implemented | Low — pre-registration gap |
