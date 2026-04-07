# Phase 6 Qualitative Observations

Anomalous cases only — silence is the default for clean cases.
Format: `[case_id] [condition]: <note>`

---

## Batch 4 Observations (eval_scenario_007, 008, 009, 013, 017, 025, 026, 041, 045)

[eval_scenario_007] forced_multiround_run2, run3: Hollow forced rounds. Defender concedes all four benchmark design issues (endpoint, timestamp, cohort, split) in Round 1; Round 2 produces no new resolutions and verdict is unchanged. Pattern: when all issues are immediately conceded by the defender on a mixed case, Round 2 adds no information.

[eval_scenario_008] forced_multiround_run3: Hollow forced round. Defender concedes all four issues in Round 1 (objective mismatch, DR estimator contamination, threshold self-selection, asymmetric optimization). Round 2 is a restatement. This is the cleanest four-issue concession pattern in the batch.

[eval_scenario_009] forced_multiround_run2: Hollow forced round. Critique_wins case where defender concedes all four issues (feed mismatch, label maturation, threshold self-selection, model-pipeline bundling) in Round 1. Round 2 is confirmatory only. Note: eval_scenario_009 is the only batch 4 hard case where the forced_multiround verdict is critique_wins rather than empirical_test_agreed, consistent with its ground truth.

[eval_scenario_013] forced_multiround_run3: Hollow forced round. Three-issue case (metric mismatch, temporal persistence, latency) where defender concedes all three in Round 1. Round 2 is confirmatory. Borderline verdict assignment in isolated_debate runs: defender's partial rebuttal on Issue 3 (38ms within ECU budget) is a reasonable point, but the latency impact on effective lead time remains an open empirical question requiring planner-in-the-loop testing.

[eval_scenario_017] forced_multiround_run2, run3: Hollow forced rounds. Three-issue case where the debate converges quickly — finding-label scope gap, edit distance proxy invalidity, and missing workflow study are all conceded by the defender. The committee recommendation to proceed to "limited operational deployment" creates a borderline adjudication call: the defender argues this is a staged approach, not unconditional approval, which is partially defensible.

[eval_scenario_025] forced_multiround_run2, run3: Hollow forced rounds. Three-issue case (weather regime, outage regime, forecast cutoff mismatch) where defender concedes all three. The NERC forced-outage exclusion being applied consistently to both vendors is a valid mitigating point raised by the defender but does not resolve the weather regime or cutoff mismatch.

[eval_scenario_026] forced_multiround_run1, run3: Hollow forced rounds. Four-issue case where self-selection, seasonal confound, integration selection, and regional timing are all acknowledged as confounds by the defender. The high hollow rate (2 of 3 runs) on this case reflects that the observational pilot has no credible defense beyond "the signal is promising and needs a cleaner test."

---

## Batch 6 Observations (eval_scenario_005, 015, 022, 024, 029, 030, 033, 048)

**Run date:** 2026-04-07  
**All 8 cases are difficulty=easy. No forced_multiround condition run.**

### Verdict Summary

| Case | isolated_debate | multiround | ensemble | baseline |
|------|----------------|------------|----------|----------|
| eval_scenario_005 | critique_wins (3/3) | critique_wins (3/3) | critique_wins (3/3) | critique_wins (3/3) |
| eval_scenario_015 | critique_wins (3/3) | critique_wins (3/3) | critique_wins (3/3) | critique_wins (3/3) |
| eval_scenario_022 | critique_wins (3/3) | critique_wins (3/3) | critique_wins (3/3) | critique_wins (3/3) |
| eval_scenario_024 | critique_wins (3/3) | critique_wins (3/3) | critique_wins (3/3) | critique_wins (3/3) |
| eval_scenario_029 | critique_wins (3/3) | critique_wins (3/3) | critique_wins (3/3) | critique_wins (3/3) |
| eval_scenario_030 | critique_wins (3/3) | critique_wins (3/3) | critique_wins (3/3) | critique_wins (3/3) |
| eval_scenario_033 | critique_wins (3/3) | critique_wins (3/3) | critique_wins (3/3) | critique_wins (3/3) |
| eval_scenario_048 | defense_wins (3/3) | defense_wins (3/3) | defense_wins (3/3) | defense_wins (3/3) |

### Hollow Round Check (Batch 6)

No hollow forced rounds in this batch. The `forced_multiround` condition was not run (all cases are difficulty=easy). In standard multiround runs, two cases achieved full convergence in round 1 (debate_rounds: 1) without requiring a round 2:

- **eval_scenario_024 multiround runs 2 and 3**: Defender conceded both issues (retention call contamination; promotion cohort) in round 1. Round 2 was omitted as convergence was complete.
- **eval_scenario_030 multiround run 3**: Defender conceded all four issues in round 1.
- **eval_scenario_033 multiround run 2**: Defender conceded all three issues in round 1.
- **eval_scenario_048 multiround runs 1, 2, 3**: Defender agreed with the assessment of all three auditor objections in round 1.

These are genuine rapid-convergence cases, not hollow rounds — the debate concluded because both sides reached substantive agreement, not because round 2 was a restatement.

### Notable Case Findings

**[eval_scenario_048] defense_wins — Clean and unanimous.** This is the only `position=defense` case in Batch 6. The auditor's Objection 3 (threshold selected on development set = data leakage) is technically incorrect in a specific and correctable direction. The evaluation design described (untouched holdout, lock-before-modeling, threshold on dev set, evaluation on holdout) is textbook-correct. All conditions and all 3 runs returned defense_wins with strong agreement. The most important finding to document: Objection 3, if accepted, would encourage the bad practice of threshold re-selection on held-out data, which IS actual leakage. The bank should correct the auditor's understanding clearly.

**[eval_scenario_029] Nursing score leakage has genuine empirical ambiguity.** Unlike other easy cases, the nursing early-warning score issue has a legitimate counter-argument: the score is a validated clinical instrument based on objective measurements, not clinical intuition. The community hospital deployment scope concern is the decisive critique. Empirical_test conditions were specified in isolated_debate runs 1 and 3 for the nursing score ablation. This is the only Batch 6 case where an empirical_test was identified in isolated_debate (vs. null in all other cases).

**[eval_scenario_033] Human review layer is consistently acknowledged as meaningful mitigation but does not change the verdict.** Across all runs, both critic, defender, and ensemble assessors acknowledge that the false-positives-reviewed-before-action policy limits harm. However, this mitigation does not address the evaluation gap (same-campaign circularity) or the systematic cultural annotation limitation. The verdict is stable at critique_wins.

**[eval_scenario_015] Training objective asymmetry rated as more decisive than provisional labels.** In adjudications across all runs, the recency-weighted vs. uniform training objective asymmetry (Issue 2) is consistently judged to be the stronger of the two identified critique issues. The provisional label concern (Issue 1) is partially mitigated by the symmetry argument (both models face same labels). The attribution problem (cannot decompose AUC improvement into features vs. objective) is the decisive remaining gap.

**[eval_scenario_005] Three confounds all operate in the same direction.** Data target asymmetry, horizon mismatch, and evaluation protocol asymmetry each individually invalidate the comparison, and all three favor the new model's appearance of improvement. This creates a particularly strong critique case. The defender consistently concedes all three issues by round 2 or earlier.

**[eval_scenario_022] Fastest convergence pattern.** The defender concedes the full expansion is unsupported in round 1 across all multiround runs. All three isolated_debate defenders reach the same concession by run's end. This is the clearest "pilot scope vs. expansion scope" mismatch case in the batch.

**Cross-case pattern — Defender concession rate in multiround:** Defenders partially or fully concede core critique issues in round 1 across 7 of 8 cases (all except eval_scenario_048 where defense is the correct position). This confirms that the Batch 6 cases are correctly classified as easy.

---

## Schema Fixes Applied (All Batches)

All prior-batch baseline files were missing `issues_found` and `all_issues_raised` fields. These were reconstructed from the raw text content using keyword matching against must_find_issue_ids from the benchmark case definitions. All multiround files using condition name `multiround_debate` were corrected to `multiround`. Two summary files (`phase6_batch1_summary.json`, `phase6_batch3_summary.json`) were moved out of the v4_raw_outputs/ directory to prevent schema validation failures.

---

## Hollow Round Summary (Batch 4)

Total hollow forced rounds: 11 of 21 (52%)
- eval_scenario_007: runs 2, 3
- eval_scenario_008: run 3
- eval_scenario_009: run 2
- eval_scenario_013: run 3
- eval_scenario_017: runs 2, 3
- eval_scenario_025: runs 2, 3
- eval_scenario_026: runs 1, 3

The high hollow rate in batch 4 reflects that all 7 hard cases are either mixed or critique_wins scenarios where the benchmark design flaws are clear enough that defenders concede quickly rather than mounting substantive rebuttals. This is consistent with the intended behavior of forced_multiround for well-scoped critique cases.
