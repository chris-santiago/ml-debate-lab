# EXECUTION_PLAN.md — Self-Debate Protocol v3

**Status:** Approved pending verification of four pre-execution gates (see Section 7).
**Source:** Written after DEBATE.md resolution. All debate-resolution action items are incorporated.

---

## 1. Verified Cases

**Source:** `benchmark_cases_verified.json` — 49 cases. All four conditions use this file exclusively.

**Distribution:**
- By correct_position: critique=22, mixed=16, defense=11
- By category: broken_baseline=8, metric_mismatch=7, hidden_confounding=8, scope_intent_misunderstanding=5, defense_wins=11, real_world_framing=10
- By difficulty: easy=12, medium=17, hard=20

**Agent context:** Agents receive ONLY the `task_prompt` field from each case. No case_id, category, difficulty, ground_truth, planted_issues, scoring_targets, or any answer-key field is passed to agents. (Debate P8 resolution: category field leaks correct_position for the defense_wins category — confirmed closed by this constraint.)

---

## 2. Four Conditions and Their Configurations

### 2a. Isolated Debate (isolated_debate)

**Mechanism:** Asymmetric role-instruction ensemble. The Critic is biased toward flaw detection; the Defender is biased toward exoneration. Each receives task_prompt only. The orchestrator synthesizes the two outputs into a final verdict. Neither agent sees the other's output before producing its assessment.

**This is NOT standard ml-lab debate.** It tests whether role-assignment alone (without adversarial exchange) outperforms single-pass critique.

**Dispatch:**
1. ml-critic receives: task_prompt only. No other context.
2. ml-defender receives: task_prompt only. No Critic output. No other context.
3. Orchestrator receives: Critic output + Defender output. Synthesizes final verdict.

**Output fields required per run:**
```json
{
  "verdict": "critique_wins | defense_wins | mixed | empirical_test_agreed",
  "issues_found": ["issue_id_1", "issue_id_2"],
  "all_issues_raised": ["issue_id_1", "issue_id_2", "issue_id_3"],
  "empirical_test": {
    "measure": "...",
    "success_criterion": "...",
    "failure_criterion": "..."
  },
  "critic_raw_verdict": "critique_wins | defense_wins | mixed | empirical_test_agreed",
  "defender_raw_verdict": "critique_wins | defense_wins | mixed | empirical_test_agreed"
}
```

Note: `critic_raw_verdict` and `defender_raw_verdict` must be extracted from raw agent outputs before synthesis. These are required for convergence metric computation.

### 2b. Multi-Round Debate (multiround)

**Mechanism:** Standard ml-lab adversarial exchange. Defender sees Critique and responds point-by-point. Maximum 4 exchange rounds. This tests whether adversarial exchange on top of role-assignment adds value beyond isolated role-assignment alone.

**Dispatch:**
1. ml-critic receives: task_prompt only.
2. ml-defender receives: task_prompt + Critic output.
3. Orchestrator runs up to 4 rounds of ml-critic (Mode 2) and ml-defender (Mode 2) on contested points.
4. Final synthesized verdict after rounds complete.

**Output fields:** same schema as isolated_debate. `convergence_metric` field: 1.0 if critic_raw_verdict == defender_raw_verdict after final round; 0.5 if they diverge.

### 2c. ETD-Constrained Ensemble (ensemble)

**Mechanism:** Compute-matched control. Three independent ml-critic passes over task_prompt (no Defender). All three outputs synthesized by orchestrator. Purpose: tests whether the ETD advantage is structural (adversarial architecture) or prompt-design (ETD constraint instruction).

**ETD constraint — verbatim instruction applied to ensemble synthesizer:**

> When synthesizing verdicts, if the case involves a contested empirical claim, you MUST produce an empirical test specification with three required components: (1) measure — the specific metric or observable to be measured; (2) success_criterion — the result that confirms the critique position; (3) failure_criterion — the result that confirms the defense position. A response without all three components does not satisfy the empirical test requirement.

This exact instruction is applied to the ensemble synthesizer. No equivalent instruction is added to isolated_debate or multiround synthesizers. (Debate P6 resolution: ETD constraint operationally locked.)

**Output fields:** same schema as isolated_debate. `critic_raw_verdict` = verdict of first Critic pass; `defender_raw_verdict` = null (no Defender in ensemble).

### 2d. Baseline (baseline)

**Mechanism:** Single-pass ml-critic. No Defender. No synthesis.

**Dispatch:** ml-critic receives: task_prompt only. Critic output IS the final output.

**Structural overrides (pre-registered):**
- DC hardcoded 0.0 for all baseline cases — structural, not a reasoning penalty. Baseline has no Defender role.
- DRQ capped at 0.5 for all baseline cases — structural. Baseline cannot produce a typed resolution from adversarial exchange.

**Output fields:** same schema as isolated_debate minus `critic_raw_verdict` / `defender_raw_verdict` (not applicable).

---

## 3. Pre-Specified Verdict Criteria

### Primary Hypothesis (H1)

**Success requires ALL THREE of the following** (raw lift AND honest lift — Debate P5 resolution):

1. `benchmark_isolated_debate_mean >= 0.65`
2. `debate_pass_fraction >= 0.75` (fraction of 49 cases where isolated_debate passes >= 2 of 3 runs)
3. `lift_isolated_vs_baseline >= 0.10` (raw lift)
4. `honest_lift_isolated_vs_baseline >= 0.10` (honest lift: baseline DC reset to 0.5, DRQ uncapped)

If conditions 1-3 pass but condition 4 fails, result is: "Primary hypothesis passes on raw metrics but fails corrected — lift attributable to structural baseline suppression." This is a negative result.

**Bootstrap CI co-condition** (Debate P4 resolution): Report 95% bootstrap CI on the lift (10,000 resamples, case-level). If CI lower bound <= 0.0, report as statistically inconclusive regardless of point estimate.

### Secondary Hypothesis H2 — ETD-Constrained Ensemble Comparison

**Success criterion:** `isolated_debate_mean(ETD, mixed_position_cases) > ensemble_mean(ETD, mixed_position_cases)`

**Filter:** mixed_position_cases = cases where `correct_position == 'mixed'` (16 cases).
**Metric:** ETD scores only (null cases excluded per standard ETD null rule).

### Secondary Hypothesis H3 — Defense Recall at Ensemble Budget

**Success criterion:** `ensemble_DC_fraction_on_defense_wins >= 0.6`

Where `ensemble_DC_fraction_on_defense_wins` = fraction of defense_wins cases (11 cases) where `ensemble['mean DC across 3 runs'] >= 0.5`.

If >= 60% of defense_wins cases have ensemble DC >= 0.5: "Compute budget partially explains defense_wins advantage."

### Secondary Hypothesis H4 — Multiround DRQ vs. Isolated Debate DRQ

**Success criterion:** `multiround_mean(DRQ, non_defense_wins_cases) > isolated_debate_mean(DRQ, non_defense_wins_cases)`

**Filter:** non_defense_wins_cases = cases where `correct_position != 'defense'` (38 cases). (Debate P9 resolution: DRQ filter locked here.)

Note: DC is reported for completeness but is NOT independently tested in this hypothesis. DC is structurally identical to FVC in non-multiround conditions; in multiround it reflects adversarial exchange outcome. See dc_note in PREREGISTRATION.json.

---

## 4. Artifact Plan

Every item below must exist before Phase 11 (git commit). Phase column is from claude_code_plan_v3_experiment.md.

| Artifact | Phase | Notes |
|----------|-------|-------|
| `benchmark_cases.json` | Input | From synthetic-candidates/ |
| `benchmark_cases_verified.json` | Phase 1 | 49 cases — all conditions use this |
| `benchmark_verification.json` | Phase 1 | Decision, reasons, ambiguity_risk per case |
| `BENCHMARK_PROMPTS.md` | Phase 2 | task_prompt fields only; no answer-key fields |
| `HYPOTHESIS.md` | Phase 2 | Locked before any agent run |
| `PREREGISTRATION.json` | Phase 3 | Locked before any agent run |
| `evaluation_rubric.json` | Phase 3 | Locked before any agent run |
| `CRITIQUE.md` | Phase 4 | This document's source |
| `DEFENSE.md` | Phase 4 | This document's source |
| `DEBATE.md` | Phase 4 | All 10 points resolved |
| `EXECUTION_PLAN.md` | Phase 4 | This document |
| `README.md` | Phase 4 | One-paragraph hypothesis + quickstart |
| `self_debate_poc.py` | Phase 5 | Scoring engine; includes convergence metric |
| `check_isolation.py` | Phase 6 | Verifies agent dispatch passed only task_prompt |
| `v3_raw_outputs/` | Phase 6 | 49 cases × 4 conditions × 3 runs = 588 output files |
| `INVESTIGATION_LOG.jsonl` | Phase 6+ | Append-only; one entry per agent dispatch, output write, adjudication |
| `v3_results.json` | Phase 7 | Aggregate + per-case scores across all conditions |
| `evaluation_results.json` | Phase 7 | Per-case pass/fail, found/missed issues, attribution |
| `CONCLUSIONS.md` | Phase 8 | Primary + secondary hypothesis verdicts; convergence diagnostic |
| `SENSITIVITY_ANALYSIS.md` | Phase 8 | Honest lift, rubric variant analysis |
| `ENSEMBLE_ANALYSIS.md` | Phase 8 | ETD comparison, defense_wins DC fraction |
| `stats_analysis.py` | Phase 8 | Bootstrap CI, filtered DRQ comparison, significance tests |
| `stats_results.json` | Phase 8 | Output of stats_analysis.py |
| `sensitivity_analysis.py` | Phase 8 | Honest lift, DC-excluded mean, corrected threshold analysis |
| `sensitivity_analysis_results.json` | Phase 8 | Output of sensitivity_analysis.py |
| `difficulty_validation.py` | Phase 8 | Score distribution by difficulty level |
| `difficulty_validation_results.json` | Phase 8 | Output of difficulty_validation.py |
| `within_case_variance_results.json` | Phase 8 | Cross-run variance per case per condition |
| `*.png` (analysis figures) | Phase 8 | Score distributions, lift by category, ETD comparison |
| `REPORT.md` | Phase 9 | Full results report |
| `REPORT_ADDENDUM.md` | Phase 9 | Honest lift and corrected metric discussion |
| `PEER_REVIEW.md` | Phase 9 | Round 1 (Opus); Round 2 (Haiku) if major issues found |
| `FINAL_SYNTHESIS.md` | Phase 9 | Internal summary; not a substitute for TECHNICAL_REPORT.md |
| `TECHNICAL_REPORT.md` | Phase 9.75 | Publication-ready results |
| `post_report_coherence_audit.py` | Phase 9.5 | Checks all documents for stale claims |
| `coherence_audit.py` | Phase 8.5 | Mid-experiment consistency check |
| `cross_model_scorer.py` | Phase 10 | Cross-vendor scoring (requires operator API key) |
| `cross_vendor_scores_v3.json` | Phase 10 | Output of cross_model_scorer.py |

**Convergence metric implementation** (Debate P10 resolution): Add to self_debate_poc.py. `score_run()` should extract `critic_raw_verdict` and `defender_raw_verdict` from output JSON and compute convergence = 1.0 if equal, 0.5 if not. Report per-case and aggregate in v3_results.json and CONCLUSIONS.md for isolated_debate condition.

---

## 5. Failure Handling

### Agent output missing
- Log to INVESTIGATION_LOG.jsonl with entry type `error`.
- Retry up to 2 times. If still missing after 2 retries, mark run as `null` and proceed with remaining runs.
- If >= 2 of 3 runs fail for any case-condition pair, flag that pair in v3_results.json as `insufficient_runs`. Do not compute aggregate for that pair.

### Isolation verification failure
- `check_isolation.py` runs after Phase 6 completes. It verifies that no agent output contains metadata fields (case_id, category, difficulty, ground_truth text).
- If isolation failure is detected for any case, invalidate that case's isolated_debate outputs and re-run in strict isolation.
- Log all isolation checks to INVESTIGATION_LOG.jsonl.

### Scoring engine errors
- If `score_run()` raises an exception for a case, log to INVESTIGATION_LOG.jsonl and skip that case in the aggregate. Do not impute scores.
- Report n_scored and n_skipped in v3_results.json.

### Benchmark passes with honest lift < 0.10
- Report as: "Primary hypothesis fails corrected. Raw lift [X] passes the pre-registered threshold, but honest lift [Y] does not. Lift is attributable to structural baseline suppression (DC=0.0 and DRQ cap). No deployment recommendation."
- This is a defined outcome, not an error.

---

## 6. Iteration Policy

This experiment does not iterate on cases or scoring logic after any agent run begins.

- **Rubric is locked** (evaluation_rubric.json and PREREGISTRATION.json) before Phase 6.
- **Cases are locked** (benchmark_cases_verified.json) before Phase 6.
- **No case modifications** after Phase 1 verification is complete.
- **No rubric adjustments** after any agent output is produced.
- **Post-hoc analysis is exploratory only** and clearly labeled as such in CONCLUSIONS.md and REPORT.md.

If a scoring engine bug is discovered after Phase 6 begins:
1. Halt execution at the current case boundary.
2. Log the bug discovery to INVESTIGATION_LOG.jsonl.
3. Fix the bug and document the change.
4. Re-run all cases where the bug affected output (not just the case where discovered).
5. Note the re-run in INVESTIGATION_LOG.jsonl and CONCLUSIONS.md.

---

## 7. Pre-Execution Gates — Required Before Phase 6

All four gates must pass before any agent run begins:

| Gate | Check | Status |
|------|-------|--------|
| G1 — Isolation explicit | Confirm code/dispatch spec passes task_prompt only to agents in isolated_debate condition | Required |
| G2 — ETD constraint locked | Verbatim ETD instruction text appears in this document (Section 2c) | CLOSED — text committed above |
| G3 — Structural overrides match PREREGISTRATION.json | DC=0.0 for baseline, DRQ capped at 0.5 for baseline; both verified in self_debate_poc.py source | Required |
| G4 — All conditions use benchmark_cases_verified.json | No condition reads from benchmark_cases.json or any other case file | Required |

Additional debate-resolution gates:

| Gate | Resolution Source | Required Action |
|------|------------------|-----------------|
| G5 — Honest lift co-criterion | Debate P5 | Primary criterion includes honest_lift >= 0.10 — committed in Section 3 |
| G6 — Bootstrap CI | Debate P4 | 95% CI lower bound > 0.0 committed in Section 3 |
| G7 — DRQ filter | Debate P9 | Non-defense_wins filter committed in Section 3 |
| G8 — Convergence metric | Debate P10 | Add to self_debate_poc.py before Phase 6 |
| G9 — Mechanism clarification | Debate P3 | EXECUTION_PLAN.md Section 2a/2b distinguishes isolated=role-bias vs. multiround=adversarial exchange — committed above |

Gates G5–G9: CLOSED in this document.
Gates G1, G3, G4: Verified during Phase 5 (scoring engine build) and Phase 6 setup.
