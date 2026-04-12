# PHASE6_OBSERVATIONS.md — Qualitative Anomaly Notes

Format: [case_id] [condition]: <note>
Only anomalous cases documented — silence is the default.

---

## Borderline Verdict Assignments

[eval_scenario_3] ensemble: Conservative ensemble rule fired across all 3 runs — 2/3 assessors critique_wins, 1/3 defense_wins. The AUROC-vs-limited-outreach-capacity metric alignment flaw generated genuinely contested assessments. Conservative rule correctly prevented false consensus.

[eval_scenario_295] ensemble: Same conservative-rule pattern as eval_scenario_3 across all 3 runs — AUPRC vs. overall-improvement framing produced consistent 2-critique/1-defense split. The defense argument (AUPRC appropriate for class imbalance) was substantively compelling.

[eval_scenario_125] ensemble: Conservative rule fired all 3 runs (2/3 critique_wins, 1/3 defense_wins). Temporal leakage from random stratified split in a forecasting context. The defense argument — that a temporal split tests only the most recent atypical months rather than the full demand distribution — is substantively compelling, but the core temporal validity concern holds.

[eval_scenario_332] ensemble: 2/3 critique_wins, 1/3 empirical_test_agreed across all runs (never defense_wins). Target leakage with deployment-time availability component is easier to detect than metric alignment flaws — high consensus on critique side.

---

## Forced-Multiround Substantive Exchanges

[eval_scenario_691] forced_multiround run1: Defender substantially conceded in round 2, explicitly acknowledging that "10:00 AM cutoff" proxy labels systematically misclassify deliveries where departure time precedes actual delivery time. Point_resolution_rate = 1.0 with both points resolving toward critique — unusually clean concession under adversarial pressure.

[eval_scenario_649] forced_multiround: Consistent partial-concession pattern across all 3 runs. Defender acknowledged tension between AUC-ROC primary metric and recall ≥ 0.70 constraint but consistently defended as standard practice. Forced-round engagement produced nuanced partial admissions without full concession — signal that hard cases benefit from extended format.

[eval_scenario_428] forced_multiround: Defender conceded issues 2-4 in round 1 but held on issue 1 (random holdout temporal inversion), proposing stratified AUC by acquisition cohort as a mitigation. Critic correctly rejected this in round 2 as a diagnostic rather than a validity fix. Clean 2-round adversarial arc with progressive resolution.

[eval_scenario_524] forced_multiround: Defender's "month-stratification ensures fraud epoch coverage" rebuttal in round 1 was substantively argued but correctly rejected by critic in round 2. 4-issue dense design with a clear round 2 escalation pattern.

---

## Protocol and Data Quality Notes

[eval_scenario_656] all conditions: Self-contradicting design detected consistently across all conditions and runs. Section 2 implements temporal split; Section 3 fits preprocessors on full 36-month corpus. The internal inconsistency made this the most cleanly-detectable flaw in batch 1.

---

## Schema Repair Notes (Phase 10.5 Impact)

**Hollow-round detection unreliable for repaired files:** A post-hoc schema repair pass was applied to ~111 multiround/forced_multiround files that were missing `points_resolved`, `points_force_resolved`, `point_resolution_rate` (top-level) and per-round `verdict`/`points_resolved`/`points_open` fields. Repaired files have `schema_repair_note` annotated. Conservative defaults were used:
- `points_resolved` = len(issues_found) for critique_wins cases, 0 for defense_wins
- Per-round `verdict` = final verdict (all rounds)
- Per-round `points_resolved` = 0 for all except last round (receives total)

Phase 10.5 hollow-round rate analysis will not be meaningful for these cases. Scoring engine results (self_debate_poc.py) are unaffected — it does not read these fields.

**Batch 2 ground-truth contamination:** All 165 batch 2 files were self-deleted and re-run with a clean subagent after the original batch agent loaded `planted_issues` before dispatch. Detection: zero stochastic variance across all 3 runs of 11 cases. Re-run files are clean.
