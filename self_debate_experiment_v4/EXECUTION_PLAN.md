# EXECUTION_PLAN.md — v4 Self-Debate Experiment

---

## Pre-Flight Checklist

*Dynamically constructed from the Phase 4 Defender's Pass 2 verdict table. Every item must be CLOSED before Phase 5 begins.*

| # | Source | Item | Verification Method | Status |
|---|--------|------|---------------------|--------|
| 1 | DEFENSE.md Issue 7 (Concede) | Secondary H2 reframed: DC → FVC for defense_wins cases | Check PREREGISTRATION.json `secondary_defense_wins.criterion` contains "FVC" | CLOSED |
| 2 | DEFENSE.md Issue 8 (Concede) | Verification status written back to all case objects | Check `benchmark_cases_verified.json` — all `verifier_status` fields must be non-"pending" | CLOSED |
| 3 | DEFENSE.md Issue 8 (Concede) | 12 verification check definitions documented | `benchmark_verification_checks.md` exists with all 12 checks defined | CLOSED |
| 4 | DEFENSE.md Issue 1 (Partial concede) | Mechanism text clarified in HYPOTHESIS.md | HYPOTHESIS.md mechanism text updated to distinguish role separation from exchange | CLOSED |
| 5 | DEFENSE.md Issue 2 (Partial concede) | "compute-matched" label dropped from HYPOTHESIS.md | HYPOTHESIS.md ensemble condition description no longer uses "compute-matched" | CLOSED — label was never in HYPOTHESIS.md conditions table; acknowledged as confound in DEBATE.md |
| 6 | DEFENSE.md Issue 5 (Partial concede) | Per-case-type pass rates preregistered as required reporting output | PREREGISTRATION.json includes per-case-type pass rate requirement | CLOSED — committed in PREREGISTRATION.json reporting_commitments via Phase 8 analysis directives |
| 7 | DEFENSE.md Issue 6 (Partial concede) | IDP neutrals audit committed to preregistration | Post-execution: compute fraction of raised issues in must_find / must_not_claim / neither; note if neutral fraction > 30% | CLOSED — committed as Phase 7/8 analysis step |
| 8 | DEBATE.md Issue 9 (critique_wins) | Difficulty pilot revised: 15 cases minimum, 5+ per tier, three-branch decision rule | PREREGISTRATION.json `difficulty_pilot_gate` block present with correct spec | CLOSED |

**All 8 items CLOSED. Gate cleared.**

---

## Conditions

| Condition | Description | Scope |
|-----------|-------------|-------|
| `isolated_debate` | Critic and Defender each receive only `task_prompt`; orchestrator adjudicates | All 53 cases |
| `multiround` | Defender sees Critique; up to 4 rounds; orchestrator adjudicates | All 53 cases |
| `forced_multiround` | Same as multiround; minimum 2 rounds enforced | Hard cases only (18 cases) |
| `ensemble` | 3 independent assessors + ETD-constrained synthesizer | All 53 cases |
| `baseline` | Single-pass, no structure | All 53 cases |

**Runs per case:** 3  
**Total case-runs:** 53 × 3 × 5 conditions − (35 non-hard × 3 runs for forced_multiround) = ~690 runs  
**Estimated agent calls:** ~1200–1500

---

## Difficulty Pilot Gate (Phase 5.5)

Before Phase 6 full execution, run a 15-case baseline pilot (5+ easy, 5+ medium, 5+ hard):

| Outcome | Action |
|---------|--------|
| Easy baseline mean < 0.70 | Audit and relabel all easy cases; do not proceed to Phase 6 until complete |
| Easy baseline mean 0.70–0.84 | Proceed with calibration uncertainty noted in reporting |
| Easy baseline mean ≥ 0.85 | Proceed as planned |

---

## Pre-Specified Verdict Criteria

### Primary Hypotheses

| Hypothesis | Pass Criterion |
|------------|---------------|
| Fair-comparison lift | isolated_debate fc_lift − baseline fc_lift ≥ +0.10 (IDR/IDP/DRQ/FVC only) |
| Case pass rate | ≥ 75% of cases pass (mean non-null primary dims ≥ 0.65 AND all applicable primary dims ≥ 0.5) |
| Benchmark mean | Debate benchmark mean ≥ 0.65 |

### Secondary Hypotheses

| Hypothesis | Pass Criterion |
|------------|---------------|
| Debate vs ensemble | Debate mean on fair-comparison dims > ensemble mean (IDR/IDP/DRQ/FVC; DC/ETD excluded) |
| Defense_wins FVC | Ensemble FVC ≥ 0.5 on ≥ 60% of defense_wins cases |
| Forced multiround | forced_multiround_mean(hard) > multiround_mean(hard) on DRQ and IDR |

### N/A Rules (pre-registered)

| Dimension | Condition | Rationale |
|-----------|-----------|-----------|
| DC | baseline | No Defender role — structural inapplicability |
| DC | defense_wins cases | Correct resolution is exoneration; Defender role trivially satisfied |
| ETD | ensemble, baseline | No adversarial exchange; no contested-point structure |
| IDR, IDP | defense_wins cases | No must-find issues; no false positive traps applicable |

---

## Artifact Plan

| Artifact | Phase | Description |
|----------|-------|-------------|
| `benchmark_cases.json` | Input | 54 cases from synthetic-candidates |
| `benchmark_cases_verified.json` | 1 | 53 verified cases (verifier_status written back) |
| `benchmark_verification.json` | 1 | Full verification results with checks_passed/failed |
| `benchmark_verification_checks.md` | 1 | 12 check definitions |
| `BENCHMARK_PROMPTS.md` | 2 | Task prompts only (no answer keys) |
| `HYPOTHESIS.md` | 2 | Formal hypothesis, 5 conditions |
| `PREREGISTRATION.json` | 3 | Locked before any agent run; includes pilot gate |
| `evaluation_rubric.json` | 3 | Locked rubric |
| `log_entry.py` | 0 | Logging utility |
| `CRITIQUE.md` | 4 | Protocol self-critique |
| `DEFENSE.md` | 4 | Protocol self-defense with verdict table |
| `DEBATE.md` | 4 | Contested points, 2 rounds, final status |
| `EXECUTION_PLAN.md` | 4 | This document |
| `README.md` | 4 | Experiment overview |
| `self_debate_poc.py` | 5 | Scoring engine |
| `v4_raw_outputs/` | 6 | Per-case outputs, all conditions |
| `PHASE6_OBSERVATIONS.md` | 6 | Anomalous cases during benchmark run |
| `v4_results.json` | 7 | Aggregated scores |
| `v4_results_eval.json` | 7 | Pass/fail evaluation |
| `stats_results.json` | 7 | Bootstrap CIs, Wilcoxon tests |
| `sensitivity_analysis_results.json` | 7 | Fair-comparison lift decomposition |
| `difficulty_validation_results.json` | 7 | Difficulty label validation (Spearman) |
| `within_case_variance_results.json` | 7 | Within-case variance analysis |
| `CONCLUSIONS.md` | 8 | Primary conclusions |
| `SENSITIVITY_ANALYSIS.md` | 8 | Sensitivity analysis narrative |
| `ENSEMBLE_ANALYSIS.md` | 8 | Ensemble vs debate analysis |
| `*.png` | 8 | Analysis figures |
| `REPORT.md` | 10 | Final report |
| `PEER_REVIEW_R1.md` | 10 | Peer review Round 1 |
| `FINAL_SYNTHESIS.md` | 10 | Synthesis after peer review |
| `TECHNICAL_REPORT.md` | 10.75 | Publication-ready technical report |
| `INVESTIGATION_LOG.jsonl` | 0+ | Append-only audit trail |

---

## Failure Handling

| Failure | Response |
|---------|----------|
| Agent produces malformed output | Log `workflow/rerun_triggered`, re-run once; if still malformed, log `decision/output_rejected` and record as missing |
| Isolation breach detected by `check_isolation.py` | Log `decision/isolation_breach_detected`; flag case; do not re-run |
| Case-level scoring error | Log error; exclude case from aggregate; note in PHASE6_OBSERVATIONS.md |
| Pilot gate fails (easy baseline < 0.70) | Stop before Phase 6; relabel easy cases; re-run pilot |
| Primary hypothesis fails | Report honestly; do not adjust criteria post-hoc |

---

## Interpretation Commitments (Issue 1, empirical_test_required)

The multiround vs. isolated_debate comparison is confounded by Defender information exposure: in multiround, the Defender sees the Critique before its first response, while the Critic does not see the Defender's initial output before Round 2. Any performance difference between these conditions conflates (a) Defender information access and (b) exchange rounds. Results will be reported as descriptive comparisons only. Mechanistic attribution ("exchange rounds drive the lift") is not supported by this design and will not be stated in conclusions.
