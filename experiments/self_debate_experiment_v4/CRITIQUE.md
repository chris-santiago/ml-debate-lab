# CRITIQUE — v4 Self-Debate Experiment

**Critic:** Adversarial subagent  
**Date:** 2026-04-06  
**Mode:** Initial critique (Mode 1)  
**Files reviewed:** HYPOTHESIS.md, PREREGISTRATION.json, evaluation_rubric.json, self_debate_poc.py, benchmark_cases_verified.json, benchmark_verification.json

---

## Root Cause A: The Primary Condition Does Not Test the Stated Mechanism

### Issue 1 — isolated_debate is role-framing, not adversarial debate

**Claim:** The primary hypothesis states the mechanism is "adversarial role separation forces engagement with both sides, producing better-typed verdicts and catching false positives that correlated parallel assessors miss."

**Why it might be wrong:** In `isolated_debate`, the Critic receives only the task prompt and the Defender receives only the task prompt. Neither agent sees the other's output. The Defender cannot engage with, challenge, or concede any specific claim the Critic made, because the Critique has not been shown to it. The "adversarial" component is entirely a role-prompt injection: the Critic is told to critique; the Defender is told to defend. What is being tested is whether role-framing two parallel independent agents improves over a single neutral agent. This is a role-framing effect, not an adversarial debate effect.

The mechanism as described — forcing engagement with both sides, catching false positives via adversarial challenge — requires that the Defender actually see the Critique and respond to specific points. That exchange structure exists only in `multiround` and `forced_multiround`. Both of those are secondary conditions. The primary hypothesis is therefore built around the condition that most weakly instantiates the stated mechanism.

**What would settle it:** Compare `isolated_debate` against a "dual neutral" condition — two neutral assessors receiving the same task prompt, with no role framing, whose outputs are synthesized by the same orchestrator. If `isolated_debate` outperforms dual neutral, the role-framing effect is real but distinct from adversarial exchange. If `multiround` substantially outperforms `isolated_debate` on fair-comparison dims, the adversarial-exchange mechanism is the operative variable and the primary condition is misaligned with the hypothesis. If `isolated_debate` approximately matches `ensemble` (three neutral assessors), the framing effect is marginal and the structural claim cannot be made.

---

### Issue 2 — isolated_debate and ensemble are structurally nearly identical

**Claim:** The experiment treats `isolated_debate` and `ensemble` as distinct conditions answering the question "does adversarial role structure improve issue identification beyond compute-matched parallel passes?"

**Why it might be wrong:** `isolated_debate` uses two role-framed agents (critic + defender) plus one orchestrator. `ensemble` uses three neutral agents plus one synthesizer. Both conditions are structurally parallel-independent-assessment-then-synthesis. The only difference is role framing and the number of independent assessors (2 vs 3). If the two conditions score similarly, the design cannot distinguish whether similarity means (a) role framing adds nothing, or (b) two agents are simply weaker than three regardless of framing. If `isolated_debate` outperforms `ensemble`, this could be explained by the asymmetric compute allocation (3 synthesized passes vs 4) rather than adversarial structure.

The design claims compute-matching between `ensemble` and debate conditions, but this is not verified. `isolated_debate` uses approximately 3 LLM calls; `ensemble` uses 4 (3 assessors + synthesizer); `multiround` uses up to 9 (4 rounds × 2 agents + orchestrator). Call counts are not equated and token budgets are not tracked. Any result favoring debate over ensemble is confounded with the number of independent perspectives synthesized.

**What would settle it:** Run a true compute-matched baseline: 2 neutral assessors + 1 synthesizer (same call budget as `isolated_debate`) versus `isolated_debate`. If `isolated_debate` outperforms this 2-neutral control on fair-comparison dims, the role-framing effect is real. The current `ensemble` (3+1 calls) is not a valid compute control for `isolated_debate` (2+1 calls).

---

## Root Cause B: The Fair-Comparison Lift Metric Is Not Case-Balanced

### Issue 3 — fc_lift pools dimension-instances, not cases

**Claim:** The primary metric "fair-comparison lift" measures whether `isolated_debate` outperforms `baseline` by +0.10 on fair-comparison dimensions (IDR, IDP, DRQ, FVC). The rubric implies this is a per-dimension mean.

**Why it might be wrong:** The `fair_comparison_mean` function pools all non-null dimension values across all cases and all runs into a single list and averages them. It does not compute a per-case mean first and then average across cases. This means dimension-instance counts drive the aggregate:

- A `critique_wins` case contributes 4 non-null values per run × 3 runs = 12 dimension-instances.
- A `defense_wins` case contributes 2 non-null values per run (only DRQ + FVC; IDR and IDP are N/A) × 3 runs = 6 dimension-instances.

Critique cases get twice the weight in the pooled mean as defense cases. There are 26 critique cases and 11 defense cases in the benchmark. The fc_lift is therefore dominated by the relative performance of the two conditions on critique-wins cases, not across the full case distribution.

If `isolated_debate` is disproportionately better at IDR and IDP (issue identification) but not at verdict quality, the lift would be inflated by the higher weight of the four-dimensional critique cases. Conversely, a condition that is good at verdicts but weak at issue identification would appear weaker than it is because verdict-only contributions are underweighted.

**What would settle it:** Compute fc_lift both ways: the current pooled approach and a case-balanced approach (compute per-case fair_comparison_mean first, then average across cases). If the two lift estimates agree within 0.02, the weighting choice does not matter. If they diverge by more than 0.02, report which favors which condition and use the case-balanced version as primary since it assigns equal weight to each evaluation scenario regardless of ground-truth type.

---

### Issue 4 — The +0.10 threshold is not calibrated against any prior measurement

**Claim:** A fair-comparison lift of +0.10 over baseline on IDR/IDP/DRQ/FVC constitutes evidence that the debate protocol improves assessment quality.

**Why it might be wrong:** The threshold is stated in the preregistration without reference to any pilot, prior experiment result, or expected baseline score. The interpretation depends entirely on where baseline sits. If baseline achieves 0.80 on fair-comparison dims (which is plausible on the 12 easy cases where single-pass assessors are expected to score ≥0.85), then +0.10 requires debate to reach 0.90, which is near-ceiling on a coarsely discretized rubric. If baseline achieves 0.55, then +0.10 is an undemanding bar. The threshold says nothing about effect size in either regime.

Additionally, the benchmark contains 12 easy cases that are explicitly expected to be within single-pass capability. These cases dilute any lift signal by providing a floor effect on baseline — baseline should score near-ceiling on easy cases regardless of protocol, and so should debate. The +0.10 threshold would need to come from medium and hard cases to be meaningful, but the lift is computed across all 53 cases uniformly.

**What would settle it:** Report fc_lift separately for each difficulty tier (easy / medium / hard). If lift is concentrated in hard cases and absent for easy cases, the mechanism is real but limited to complex scenarios. If lift is uniform across difficulty, it may reflect task familiarity rather than protocol benefit. Pre-register the expected baseline score on fair-comparison dims by difficulty tier, derived from v3 results or a small pilot run, before execution.

---

## Root Cause C: Scoring Asymmetries Create Unequal Pass Thresholds by Case Type

### Issue 5 — The 0.65 pass threshold is harder for empirical_test_agreed cases than for any other type

**Claim:** The per-case pass criterion `mean(non-null PRIMARY dims) >= 0.65 AND all applicable primary dims >= 0.5` applies uniformly across all cases.

**Why it might be wrong:** The number of non-null primary dimensions varies structurally by case type:

- `defense_wins` cases: IDR=N/A, IDP=N/A, ETD=N/A (ideal=defense_wins). Only DRQ and FVC enter the mean. These cases need mean(DRQ, FVC) >= 0.65 — achievable with DRQ=0.5 + FVC=0.8 = 0.65 exactly.
- `critique_wins` cases: IDR, IDP, DRQ, FVC all scored; ETD=N/A. Four-dimensional mean must be ≥ 0.65.
- `empirical_test_agreed` cases: All five primary dims scored (IDR, IDP, DRQ, ETD, FVC). Five-dimensional mean must be ≥ 0.65, and each must be ≥ 0.5.

The `empirical_test_agreed` cases are simultaneously the structurally hardest to pass (five dims, including ETD which requires producing a well-structured empirical test) and the most ambiguous cases in the benchmark (all 16 are mixed-position, 12 are hard difficulty). A condition that performs well on the clearer cases but struggles on the genuinely ambiguous cases will fail ETD specifically on the cases where ambiguity is warranted, not as a protocol failure but as a task-appropriate response.

**What would settle it:** Report per-case-type pass rates separately (defense_wins, critique_wins, empirical_test_agreed). If the overall 75% pass-rate threshold is met by strong performance on defense_wins and critique_wins while empirical_test_agreed cases consistently fail, the protocol is passing the easy claims and failing the hard ones — and the aggregate pass rate conceals this. A 75% overall pass rate with 90% on 2-dim cases and 40% on 5-dim cases is not equivalent to a uniform 75%.

---

### Issue 6 — IDP awards full credit for raising no scorable issues

**Claim:** IDP measures the fraction of claimed issues that are valid, penalizing false positives in `must_not_claim`.

**Why it might be wrong:** The `compute_idp` function computes:

```
denominator = len(valid) + len(invalid)
if denominator == 0: return 1.0
```

Where `valid` = issues in `must_find_ids` and `invalid` = issues in `must_not_claim`. Issues raised by the agent that are neither in `must_find_ids` nor in `must_not_claim` — call them neutral issues — are excluded from the denominator entirely. An agent that raises exclusively neutral issues (plausible-sounding but not planted) scores IDP=1.0 regardless of how many neutral issues it generates.

The practical consequence: an agent that finds 1 of 3 planted issues (IDR=0.33) and raises 10 additional neutral fabrications scores IDP=1.0 (denominator=1 valid + 0 invalid = 1, fraction=1.0). The per-case mean is (0.33 + 1.0 + DRQ + FVC) / 4. This is not a precision score; it is a "did you avoid the specific traps" score. If most agent-raised issues fall outside both sets, IDP provides almost no information about issue precision.

**What would settle it:** After execution, compute the distribution of `all_issues_raised` that fall into each category (must_find, must_not_claim, neutral) across all runs and conditions. If more than 30% of raised issues are neutral (neither set), IDP is measuring trap-avoidance rather than precision, and the metric label is misleading. A proper precision metric would penalize neutral fabrications by including them in the denominator.

---

## Root Cause D: Secondary Hypothesis 2 Is Structurally Unverifiable

### Issue 7 — Secondary H2 requires DC on defense_wins cases, which is always N/A

**Claim:** Secondary hypothesis 2 states: "Ensemble DC >= 0.5 on >= 60% of defense_wins cases (compute budget partially explains defense_wins advantage)."

**Why it might be wrong:** In `score_run`, the first conditional block sets `DC = None` unconditionally whenever `correct_position == 'defense'`. This applies to every condition, including `ensemble`. The `compute_dc` function is never called for defense cases because the block that would call it is inside the `else` branch that is never reached. All 11 defense cases therefore produce DC=None for every condition in every run.

The secondary hypothesis requires computing `ensemble DC >= 0.5` on these exact cases. There are zero computable DC values for defense cases in any condition. The hypothesis cannot produce a verdict — pass, fail, or inconclusive — from the existing scoring logic. Either the N/A rule for defense cases must be removed from the DC calculation for ensemble specifically (requiring a code change before execution), or the hypothesis must be reframed using a different observable. As written, it will produce no output.

**What would settle it:** Decide before execution whether DC should be computed for ensemble on defense cases. If the intent is to test whether ensemble reaches the correct verdict (defense) on defense cases, FVC is already measuring this (verdict in acceptable_resolutions), and DC would be redundant with FVC for these cases. Reframe the secondary hypothesis as: "Ensemble FVC >= 0.5 on >= 60% of defense_wins cases" — this is verifiable with the existing scoring logic and addresses the same question about whether compute budget achieves correct verdicts.

---

## Root Cause E: Benchmark Integrity and Verification Opacity

### Issue 8 — verifier_status is "pending" for all 53 cases in the verified file

**Claim:** `benchmark_cases_verified.json` contains the verified benchmark cases that will be used for scoring.

**Why it might be wrong:** Every case object in `benchmark_cases_verified.json` has `verifier_status: "pending"`. A separate file, `benchmark_verification.json`, records the outcome of a 12-check verification pass (53 keep, 1 revise, 0 reject) but the results of that verification were never written back into the case objects. The two sources are inconsistent: the verification file declares cases verified; the case objects say they are pending.

More importantly, the 12 checks in `benchmark_verification.json` are not documented anywhere that is accessible from the case objects or the preregistration. The only evidence of what the checks are comes from the single `revise` case (eval_scenario_035), where check 12 is described as a difficulty-labeling consistency check. Checks 1-11 are entirely opaque. This means the verification cannot be audited: there is no way to confirm that the 12 checks are sufficient, correctly applied, or consistently interpreted across all 53 cases.

**What would settle it:** Document the 12 verification checks explicitly in the preregistration or a companion file. Write the verification outcome back into each case object so that `verifier_status` reflects the actual state. A case that passed all 12 checks should have `verifier_status: "verified"` and `checks_passed: [1,...,12]` directly in the case object, not only in a separate document.

---

### Issue 9 — Difficulty labels are not empirically validated before execution

**Claim:** The difficulty tiers (easy/medium/hard) are used to gate `forced_multiround` (hard only) and to interpret fc_lift by difficulty. The verifier expected single-pass assessors to score ≥0.85 on easy cases.

**Why it might be wrong:** The difficulty labels are human-assigned during case creation and checked only by the 12-point verification that includes at least one difficulty-labeling check (check 12, which caught one mislabeling). There is no pilot run against single-pass baseline to confirm that easy cases empirically achieve ≥0.85 baseline scores, that medium cases fall in the expected range, and that hard cases are genuinely harder. The relabeling of cases from medium to easy (visible in case notes) was justified by the case author's judgment ("single-pass assessor fails only 1 rubric dimension"), which is exactly the assumption that check 12 found problematic in at least one case.

If difficulty labels are systematically optimistic (cases labeled easy are actually medium difficulty for a single-pass assessor), then: (a) the baseline score on easy cases will be lower than expected, making the +0.10 lift threshold easier to hit via floor effects; (b) `forced_multiround` will run on too few cases to produce a meaningful secondary H3 comparison; (c) the per-difficulty lift analysis will be misleading.

**What would settle it:** Run a 5-case pilot across all difficulty tiers using baseline only before the full experiment. If baseline mean on easy cases is below 0.75, the difficulty labels are too optimistic and should be revised. This is a prerequisite gate, not an optional diagnostic.

---

## Root Cause F: Point Resolution Rate Cannot Distinguish Genuine Convergence from Capitulation

### Issue 10 — point_resolution_rate conflates substantive concession with premature closure

**Claim:** Point resolution rate — "(points resolved by concession or empirical agreement) / total contested points" — measures whether the debate protocol produces genuine convergence on contested claims.

**Why it might be wrong:** The metric counts any entry in DEBATE.md with status `"Resolved: critic wins"`, `"Resolved: defender wins"`, or `"Resolved: empirical_test_agreed"` as resolved. There is no requirement that a concession be justified by new evidence or reasoning. An agent that capitulates to social pressure (e.g., the defender concedes when the critic restates its position more forcefully without adding substance) increments the resolved count identically to a substantive concession driven by new argument or evidence.

High point_resolution_rate therefore could indicate: (a) genuine adversarial convergence on contested claims, or (b) one agent routinely capitulating to the other without substantive updating. The metric is declared diagnostic-only, but if it becomes the primary evidence cited for "the debate protocol converges," the conflation matters.

**What would settle it:** For a random sample of 10 resolved points from multiround runs, have a human evaluator classify each resolution as "substantive" (new argument or evidence drove the concession) or "social" (the conceding agent restated agreement without identifying what changed). If more than 40% of resolutions are social, the point_resolution_rate is not measuring genuine convergence and should not be cited as evidence for the debate mechanism.

---

## Summary of Critical Issues by Impact on Primary Hypothesis

| # | Issue | Threatens Primary Hypothesis | Threatens Secondary Hypotheses |
|---|-------|------------------------------|-------------------------------|
| 1 | isolated_debate tests role-framing, not adversarial exchange | Yes — mechanism mismatch | No |
| 2 | isolated_debate and ensemble are structurally similar | Yes — comparison is ambiguous | Partially (H1) |
| 3 | fc_lift is not case-balanced | Yes — lift estimate is biased | No |
| 4 | +0.10 threshold not calibrated | Yes — pass/fail boundary is arbitrary | No |
| 5 | Asymmetric pass threshold by case type | Yes — 75% pass rate conflates difficulty | Partially (H3) |
| 6 | IDP awards 1.0 for neutral fabrications | Yes — precision is not measured | No |
| 7 | Secondary H2 is unverifiable | No | Yes — H2 produces no data |
| 8 | Verification not written back to cases | Integrity risk | Integrity risk |
| 9 | Difficulty labels empirically unvalidated | Yes — forced_multiround scope uncertain | Yes (H3) |
| 10 | Point resolution rate conflates concession types | No (diagnostic only) | Interpretive risk |

Issues 1 and 7 are the most severe: Issue 1 because the primary condition does not instantiate the claimed mechanism, which means a positive result would not support the hypothesis as stated; Issue 7 because a registered secondary hypothesis has zero computable evidence under the current scoring logic.
