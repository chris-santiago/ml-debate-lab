# DEFENSE — v4 Self-Debate Experiment

**Defender:** Design-defender subagent
**Date:** 2026-04-06
**Mode:** Initial Defense (Mode 1, Cycle 1)
**Files reviewed:** HYPOTHESIS.md, PREREGISTRATION.json, evaluation_rubric.json,
plan/scripts/self_debate_poc.py, benchmark_cases_verified.json, benchmark_verification.json,
v3_external_results.json (prior experiment data)

---

## Implementation Soundness Check (Pre-Analysis)

Before defending individual design choices, I verify whether the implementation produces
interpretable results at all.

**Scoring engine (self_debate_poc.py):** The PoC is a pure scoring engine — it reads
pre-generated agent outputs from `v4_raw_outputs/` and computes metrics. No LLM parameters
to misconfigure. All dimension functions are explicit (IDR, IDP, DC, DRQ, ETD, FVC), N/A
rules are applied before scoring, and pass/fail logic is pre-registered. The engine is
sound for its purpose.

**One confirmed implementation flaw (Issue 7):** `score_run()` sets `DC = None`
unconditionally for all defense cases before reaching the branch that would call
`compute_dc()`. This means Secondary Hypothesis 2 ("Ensemble DC >= 0.5 on >= 60% of
defense_wins cases") will produce zero computable values. This is not a scoring engine
parameter misconfiguration — it is a registered N/A rule that conflicts with a registered
hypothesis. The flaw is real and must be fixed before execution.

No other implementation-level flaws detected. The remaining issues are design and
interpretation questions, not code errors that silently invalidate results.

---

## Pass 1 — Full Analysis

### Issue 1 — isolated_debate tests role-framing, not adversarial exchange

**What the critic claims:** The mechanism stated in the hypothesis — "adversarial role
separation forces engagement with both sides, producing better-typed verdicts and catching
false positives that correlated parallel assessors miss" — requires agents to see each
other's outputs and respond. `isolated_debate` does not have this exchange. Therefore the
primary condition is misaligned with the stated mechanism.

**Analysis:** The critic identifies a genuine ambiguity in the mechanism claim. The hypothesis
uses "adversarial role separation" as the operative phrase, not "adversarial exchange." These
are distinct:

- Role separation: a critic posture and a defender posture are assigned to separate agents,
  ensuring structural asymmetry in how each agent approaches the task.
- Exchange: agents see each other's outputs and argue specific points.

`isolated_debate` instantiates role separation. The elaboration "catching false positives
that correlated parallel assessors miss" does not strictly require that the Defender saw the
Critique — it requires that the system-level output (Orchestrator synthesizing both) is
sensitive to the Defender's independent resistance to overclaiming. The Defender with a
defense posture will produce a more skeptical output than a neutral assessor without being
shown a specific Critique. The Orchestrator integrating both can catch false positives that
a single-pass or correlated parallel assessor would not.

However, the critic is correct that the *elaboration* language — "forcing engagement with
both sides" — implies within-agent engagement that `isolated_debate` does not have. That
phrase maps better to `multiround`. The hypothesis text allows the weaker reading; the
elaboration implies the stronger one.

**Genuine concession:** The mechanism claim partially overreaches what `isolated_debate` can
test. The condition tests system-level role separation, not agent-level adversarial exchange.
If `isolated_debate` outperforms `baseline`, this establishes a role-framing effect. The
secondary comparison of `multiround` vs `isolated_debate` is where the exchange-specific
mechanism would be isolated. The design does not have a mechanism-pure primary condition.

**What is not wrong:** The experimental design is still valid as a comparison between role-
framed parallel assessment and single-pass baseline. The hypothesis should be read as testing
whether structural role assignment (rather than adversarial exchange specifically) improves
assessment quality. The design does NOT falsely claim that `isolated_debate` is exchange-
based — it explicitly defines `isolated_debate` as agents receiving only the task prompt.
The critic's complaint is with the *mechanism text*, not with any factual misrepresentation
of the condition.

**What remains empirically open:** Whether the role-framing effect (isolated_debate) is
substantially smaller than the exchange effect (multiround) is answerable from the experiment
itself by comparing the two conditions on fair-comparison dims.

---

### Issue 2 — isolated_debate and ensemble are structurally nearly identical

**What the critic claims:** Both conditions are parallel-independent-assessment-then-synthesis.
The only difference is role framing and assessor count (2 vs 3). If results are similar, the
design cannot distinguish between "role framing adds nothing" and "two agents weaker than
three." The "compute-matched" claim in the design is false because isolated_debate (~3 calls)
uses fewer LLM calls than ensemble (4 calls).

**Analysis:** The critic is correct that call counts are not equated. `isolated_debate` is
approximately 3 calls per run (Critic + Defender + Orchestrator). `ensemble` is 4 calls per
run (3 assessors + synthesizer). The design documents claim compute-matching, but this claim
is not operationalized anywhere in the scoring engine or agent protocols.

The structural similarity point is real but overstated. The two conditions differ in:
(a) role framing — one condition assigns asymmetric postures, the other assigns neutral postures;
(b) number of independent perspectives — 2 vs 3;
(c) synthesis task — the Orchestrator in isolated_debate adjudicates between opposing outputs,
whereas the ensemble synthesizer aggregates similar-posture outputs.

The adjudication vs. aggregation distinction is meaningful and is not captured by call count.

**Genuine concession:** The "compute-matched" label in the design is imprecise. The comparison
is not compute-matched in calls or tokens. Any performance advantage for isolated_debate over
ensemble is confounded with the assessor-count difference (2 vs 3 independent perspectives).
The design should acknowledge this confound rather than claim matching it does not achieve.

**What is not wrong:** The comparison still answers a meaningful question: does adversarial
role framing in a 2-agent system outperform neutral aggregation in a 3-agent system? This
is a valid practical question even if it is not a clean mechanism-isolated comparison. The
design does not need perfect compute-matching to produce useful results — it needs honest
labeling of what the comparison shows.

**What remains empirically open:** Whether isolated_debate outperforms ensemble is an
empirical question. If it does, the confound means we cannot credit role framing alone.
If it does not, we know 3-agent neutral aggregation is at least as good as 2-agent role-framed
for the fair-comparison dimensions.

---

### Issue 3 — fc_lift pools dimension-instances, not cases

**What the critic claims:** `fair_comparison_mean` pools all non-null dimension values across
all cases and all runs into a single list, weighting critique_wins cases (4 dims) twice as
heavily as defense_wins cases (2 dims). The lift estimate is therefore biased toward critique
case performance.

**Analysis:** The critic's description of the implementation is factually incorrect. The
actual fc_lift computation in `self_debate_poc.py` (lines 275-277) is:

```python
isolated_fc = [r['isolated_debate']['fair_comparison_mean'] for r in all_results ...]
baseline_fc = [r['baseline']['fair_comparison_mean'] for r in all_results ...]
fc_lift = round(sum(isolated_fc) / len(isolated_fc) - sum(baseline_fc) / len(baseline_fc), 4)
```

`r['isolated_debate']['fair_comparison_mean']` is a single float per case, computed by
`aggregate_runs()` which calls `fair_comparison_mean(run_results)`. The fc_lift then averages
these per-case floats. Each case contributes exactly one value to the list, regardless of
whether it is a 2-dimensional defense case or a 4-dimensional critique case. This IS
case-balanced by construction: each of the 53 cases has weight 1/53 in fc_lift.

The within-case pooling (pooling 3-run dimension values to produce one case-level float)
does not create cross-case imbalance because all runs within a case have the same ideal
resolution type and therefore the same N/A pattern.

**The critic is wrong on the implementation claim.** fc_lift is already case-balanced.

**Residual design question:** Within `fair_comparison_mean(runs)`, pooling all dimension
values across 3 runs (e.g., 12 values for a critique case) rather than averaging run means
first produces the same result when runs are internally consistent. This is not a bias.

---

### Issue 4 — The +0.10 threshold is not calibrated against any prior measurement

**What the critic claims:** The +0.10 threshold is stated without reference to pilot data,
prior experiment results, or expected baseline scores. It is arbitrary relative to both
ceiling effects (if baseline is already 0.80) and floor effects (if baseline is 0.55).

**Analysis:** The critic is correct that the threshold is not derived from a documented
calibration procedure. However, prior experiment data exists and is informative:

In v3 (external scoring), `benchmark_baseline_mean` was 0.6281 overall. Broken down by
difficulty: easy=0.50, medium=0.60, hard=0.71. The isolated_debate mean was 1.0 (ceiling,
due to a known scoring issue in v3 that was subsequently fixed). These numbers suggest
baseline operates in the 0.50-0.70 range on current-generation cases.

In v4, fair-comparison dims exclude DC and ETD for baseline (N/A). On critique cases, baseline
competes on IDR/IDP/DRQ/FVC. On defense cases, baseline competes on DRQ/FVC only. Given the
v3 baseline performance and the v4 rubric structure, baseline likely lands in the 0.55-0.70
range on fair-comparison dims.

A +0.10 threshold in this regime requires debate to reach 0.65-0.80. On a rubric with discrete
scores (0.0, 0.5, 1.0), a +0.10 lift requires approximately one additional half-credit per
case on average. This is a non-trivial but achievable lift — not a ceiling trap and not a
trivially easy bar.

**Partial concession:** The threshold is not formally derived from a pre-experiment pilot,
and that derivation should be documented. The fact that prior data exists and is consistent
with the threshold being in a reasonable regime does not substitute for explicit calibration.
The critic is right that the threshold meaning depends on where baseline sits, and reporting
difficulty-stratified lift is necessary for interpretability.

**What is not wrong:** The threshold is not arbitrary in the sense of being randomly chosen.
+0.10 is a conventional minimum meaningful effect for structured protocol comparison. The
prior experiment data provides enough evidence that this is in the right regime, even if not
formally preregistered as a calibration step.

---

### Issue 5 — The 0.65 pass threshold is harder for empirical_test_agreed cases

**What the critic claims:** defense_wins cases have 2 scorable dimensions; critique_wins
cases have 4; empirical_test_agreed cases have 5 including ETD. The 0.65 threshold + 0.5
floor per dim is harder to meet with 5 dimensions than with 2. The 75% overall pass rate
therefore conflates structurally different pass requirements.

**Analysis:** The structural asymmetry is real. A defense_wins case needs only DRQ + FVC >=
0.65 with each >= 0.5. This is achievable with one correct verdict. An empirical_test_agreed
case needs IDR + IDP + DRQ + ETD + FVC >= 0.65 with each >= 0.5, including ETD which requires
producing a well-structured empirical test.

However, this asymmetry is a reflection of the task, not a measurement artifact. defense_wins
cases ARE structurally simpler — there is no issue to find, no precision to measure. The
protocol's job on these cases is only to correctly identify and reach the right verdict.
empirical_test_agreed cases are genuinely harder (all 16 are mixed-position, 12 are hard
difficulty). Giving them a 5-dimensional threshold is appropriate — the pass criterion scales
with the task complexity.

The critic's concern is about aggregate pass rate concealment: if 90% of 2-dim cases pass
and 40% of 5-dim cases pass, the aggregate 75% is misleading. This is a reporting issue,
not a criterion design issue. The preregistration does not forbid per-type breakdown.

**Partial concession:** The aggregate 75% pass rate threshold should be supplemented with
per-case-type reporting as a pre-execution commitment. The aggregate alone is insufficient
to characterize protocol performance. This is a reporting gap that should be closed before
execution, not a reason to revise the threshold.

---

### Issue 6 — IDP awards full credit for raising no scorable issues

**What the critic claims:** `compute_idp` returns 1.0 when denominator = 0 (no valid + no
invalid issues among the raised issues). An agent that raises only neutral issues (neither
in must_find_ids nor in must_not_claim) scores IDP=1.0 regardless of how many neutral
issues it generates. IDP therefore measures "trap-avoidance" rather than precision.

**Analysis:** The critic's description is factually correct. The code:

```python
denominator = len(valid) + len(invalid)
if denominator == 0:
    return 1.0
```

This means neutral-only raises score the same as no raises. An agent producing 10 neutral
fabrications gets IDP=1.0, the same as an agent producing none.

**Design intent:** IDP was designed to measure false positive rate on the specific "trap" issues
that the benchmark authors explicitly planted as must_not_claim items. The rubric acknowledges
that not all agent-raised issues can be exhaustively classified. For cases with must_not_claim
items, IDP correctly penalizes explicit false positives. For cases without must_not_claim
items, IDP trivially returns 1.0 because there are no traps to fall into.

The critic is correct that this means IDP provides almost no signal when most raised issues
are neutral. The design does not claim IDP is a general precision metric — it is specifically
a planted-trap detection metric. The metric name "IDP" (Issue Detection Precision) is
misleading if the benchmark only plants a few traps per case.

**Genuine concession:** IDP is a precision signal only on the must_not_claim items. If agents
systematically raise many neutral issues and few or no invalid ones, IDP will be uninformative
(consistently 1.0). The metric name suggests broader precision measurement than the
implementation delivers. Tracking the distribution of neutral-vs-planted raises post-execution
is necessary to assess whether IDP is contributing to the aggregate score or is a
near-constant.

**What is not wrong:** The trap-avoidance design choice is deliberate — you cannot score a
general precision metric without a complete oracle of all valid issues, which the benchmark
does not provide. IDP provides what it can: sensitivity to specific false positives the
benchmark author explicitly identified. The limitation is real but known.

---

### Issue 7 — Secondary H2 is structurally unverifiable

**What the critic claims:** `score_run()` sets `DC = None` unconditionally for all defense
cases, meaning Secondary H2 ("Ensemble DC >= 0.5 on >= 60% of defense_wins cases") produces
zero computable values. The hypothesis cannot be verified from the current implementation.

**Analysis:** The critic is correct. The code at lines 169-172:

```python
if correct_position == 'defense':
    scores['IDR'] = None
    scores['IDP'] = None
    scores['DC'] = None  # defense_wins: N/A per v4 rubric
```

This executes before `compute_dc()` is called. There is no path to a computed DC value for
any defense case in any condition. The hypothesis requires this specific data and cannot
produce a verdict.

**Genuine concession (full):** This is a real flaw that prevents Secondary H2 from producing
any result. The fix is to reframe H2 using a metric that IS computed for defense cases. FVC
is scored for all cases regardless of position (computed after the if/else block). The
reframed hypothesis should be: "Ensemble FVC >= 0.5 on >= 60% of defense_wins cases" —
this is computable with existing logic and answers the same underlying question (whether
compute budget alone produces correct verdicts on exoneration cases).

This must be corrected in the preregistration before execution begins.

---

### Issue 8 — Verification not written back to case objects

**What the critic claims:** All 53 cases in `benchmark_cases_verified.json` have
`verifier_status: "pending"`. The verification outcome exists only in `benchmark_verification.json`.
The 12 checks are not documented anywhere accessible. The verification cannot be audited.

**Analysis:** The critic is correct on the factual state. All 53 case objects show
`verifier_status: "pending"`. The verification file confirms 53 keep, 1 revise, 0 reject,
with per-case `checks_passed` and `checks_failed` arrays. The checks themselves (what 1-12
mean) are nowhere documented in either file or in the preregistration.

The mislabeled case (eval_scenario_035) was caught by check 12, and the revise note explains
what check 12 tests. Checks 1-11 have no descriptions visible in any available file.

**Genuine concession:** The verification status not being written back to case objects is a
documentation gap. An auditor reading `benchmark_cases_verified.json` sees only "pending"
and cannot determine whether cases have been reviewed. This should be corrected — the word
"verified" in the filename is contradicted by the "pending" status in every case object.

The check definitions being undocumented is a separate and more serious gap: there is no way
to audit whether the 12 checks were appropriate, consistently applied, or comprehensive.
The design is relying on an opaque verification pass.

**What is defensible:** The verification file shows evidence of real review (12 structured
checks, specific case citations, concrete failure descriptions). This is not no review — it
is undocumented review. The fix is to document the checks and write back the status. The
underlying rigor may be sound; the documentation of that rigor is not.

---

### Issue 9 — Difficulty labels empirically unvalidated

**What the critic claims:** Difficulty labels are human-assigned and checked by a 12-point
verification that caught one mislabeling. There is no pilot run confirming that easy cases
empirically achieve >= 0.85 baseline scores. The +0.10 threshold and forced_multiround
scoping both depend on labels being accurate.

**Analysis:** The critic is correct that no empirical validation of difficulty labels has been
run. The verification caught one case (eval_scenario_035) where the label was inconsistent
with the ground truth rationale. This suggests the verification check functions as intended —
it caught a real mislabeling. But it is a consistency check (does the label match the rationale
text?), not an empirical check (do single-pass assessors actually score easy cases >= 0.85?).

From v3 data, baseline on easy cases was 0.50. This is well below the 0.85 expectation. V3
and v4 have different case sets, so direct inference is limited — but the v3 result suggests
difficulty labels may be systematically optimistic relative to actual single-pass performance.

**Partial concession:** A small pilot (5-10 cases across difficulty tiers, baseline condition
only) before the full experiment is a reasonable gate. If baseline easy-case scores fall below
0.70, the forced_multiround scope and the per-difficulty lift interpretation should both be
revisited. The v3 evidence that easy baseline = 0.50 provides enough prior signal to make
this worth checking.

**What is not wrong:** Difficulty labels are used for two purposes: gating forced_multiround
(hard only) and stratifying the fc_lift interpretation. The gating effect is that forced_multiround
runs on too few cases if labels are optimistic (more cases labeled easy/medium that are actually
hard). This is a scope reduction risk, not a result invalidation risk. The lift stratification
is diagnostic, not part of the primary pass/fail criterion.

---

### Issue 10 — Point resolution rate conflates substantive concession and capitulation

**What the critic claims:** Any DEBATE.md entry marked "Resolved" increments the metric
identically, regardless of whether the concession was driven by new evidence or social
pressure. The metric is therefore ambiguous as evidence for genuine convergence.

**Analysis:** The critic is correct that the metric cannot distinguish types of resolution.
A Defender who capitulates when the Critic restates its position more forcefully contributes
the same "Resolved: critic wins" as a Defender who concedes after the Critic introduces a
specific counterexample.

However, the preregistration already describes this as "diagnostic only — not used in
pass/fail determination." The metric is not being used to assess whether the debate mechanism
is superior to alternatives; it is a convergence diagnostic for the multiround and
forced_multiround conditions.

**Concession limited to scope:** If point_resolution_rate were used as primary evidence for
the debate mechanism's effectiveness, the conflation would be a serious flaw. Since it is
diagnostic-only, the risk is interpretive rather than conclusive. The critic's proposed
human-evaluation validation (classify 10 resolved points as substantive vs. social) is a
reasonable check to run if the metric is later cited in conclusions. It is not a prerequisite
for execution.

---

## Pass 2 — Verdict Table

| # | Issue | Verdict | Basis |
|---|-------|---------|-------|
| 1 | isolated_debate tests role-framing, not adversarial exchange | **Rebut (partial concede)** | The mechanism claim is ambiguous and partially overreaches, but the design transparently defines isolated_debate as role-framing and the experiment measures its effect relative to baseline. The mechanism text should be revised to "role separation" rather than "adversarial exchange." Not a fatal flaw — the comparison is still valid. |
| 2 | isolated_debate and ensemble structurally similar; compute not matched | **Rebut (partial concede)** | The "compute-matched" label is imprecise and should be dropped. The comparison still answers a meaningful practical question. The critic is right that the confound with assessor count (2 vs 3) must be acknowledged explicitly. The design is defensible as-is with honest labeling. |
| 3 | fc_lift pools dimension-instances, not cases | **Rebut** | The critic's description of the implementation is factually incorrect. fc_lift averages per-case fair_comparison_means (one float per case). Each case has weight 1/53 regardless of ideal_resolution type. The implementation is already case-balanced. |
| 4 | +0.10 threshold not calibrated | **Rebut (partial concede)** | Prior v3 data places baseline in the 0.50-0.70 range, which puts +0.10 in a reasonable regime. The threshold is not purely arbitrary. However, the calibration reasoning was not formally documented in the preregistration, which is a gap that should be closed. Difficulty-stratified lift reporting should be preregistered as a required output. |
| 5 | Asymmetric pass threshold by case type | **Rebut (partial concede)** | The asymmetry is structurally appropriate — defense cases are simpler and correctly scored on fewer dimensions. The aggregate 75% rate is insufficient to characterize protocol performance. Per-case-type pass rates must be reported. This is a reporting commitment, not a criterion revision. |
| 6 | IDP awards 1.0 for neutral fabrications | **Rebut (partial concede)** | The design intent is trap-avoidance measurement, not general precision. The metric name is misleading but the behavior is deliberate. The post-execution audit (what fraction of raised issues are neutral?) is necessary to assess whether IDP contributed real signal. This audit should be committed to in the preregistration. |
| 7 | Secondary H2 unverifiable (DC N/A for defense cases) | **Concede** | The code unconditionally sets DC=None for all defense cases. Zero computable values will exist. The hypothesis must be reframed as FVC >= 0.5 on defense_wins cases for ensemble. This must be corrected before execution. |
| 8 | Verification not written back to case objects | **Concede** | The "pending" status in all case objects contradicts the filename and the verification file. Check definitions are undocumented. Both gaps must be closed: write back verification outcomes to case objects and document the 12 checks in a companion file or in the preregistration. |
| 9 | Difficulty labels empirically unvalidated | **Rebut (partial concede)** | The verification caught one mislabeling, providing evidence the process functions. But v3 data (easy baseline = 0.50) suggests labels may be optimistic. A 5-10 case baseline pilot before full execution is warranted as a scope gate for forced_multiround and for calibrating the threshold interpretation. |
| 10 | Point resolution rate conflates concession types | **Rebut** | The metric is explicitly diagnostic-only and excluded from pass/fail. The conflation risk is real but constrained to interpretive use. No pre-execution correction required. If the metric is cited in conclusions, the human-classification check should be run at that time. |

---

## Pre-Execution Requirements

The following items must be confirmed or completed before Phase 5 (agent execution) begins.
These are derived from conceded and partially conceded issues above.

**Hard blockers (execution cannot proceed without resolution):**

1. **Secondary H2 must be reframed** (Issue 7, full concession). Replace "Ensemble DC >= 0.5
   on >= 60% of defense_wins cases" with "Ensemble FVC >= 0.5 on >= 60% of defense_wins
   cases" in PREREGISTRATION.json and HYPOTHESIS.md. No code change required — FVC is
   already computed for these cases.

2. **Verification status must be written back to case objects** (Issue 8, full concession).
   Each case object in `benchmark_cases_verified.json` should have `verifier_status` updated
   to reflect the verification outcome, minimally `"verified"` for the 53 cases that passed
   all checks and `"requires_revision"` for eval_scenario_035. The 12 check definitions must
   be documented in a companion file.

**Recommended pre-execution actions (not hard blockers, but address known gaps):**

3. **Mechanism text clarification** (Issue 1). Revise the hypothesis mechanism statement from
   "adversarial role separation forces engagement with both sides" to "structural role separation
   produces asymmetric postures that the orchestrator integrates, with exchange-based engagement
   tested in multiround conditions." This aligns the language with what isolated_debate actually
   does.

4. **Drop "compute-matched" label** (Issue 2). Replace in HYPOTHESIS.md: "ensemble = 3
   independent assessors + ETD-constrained synthesizer; compute-matched" should note the
   assessor-count confound explicitly ("3-assessor ensemble vs 2-agent role-framed; call counts
   not equated; differences in both framing and scale").

5. **Per-case-type pass rates as a required reporting output** (Issue 5). Preregister that
   the Phase 9 cross-vendor analysis will report pass rates separately for defense_wins,
   critique_wins, and empirical_test_agreed cases, in addition to the aggregate 75% threshold.

6. **IDP neutrals audit committed to preregistration** (Issue 6). Add to preregistration:
   post-execution, compute what fraction of all raised issues fall into must_find, must_not_claim,
   and neither. If neutral fraction > 30%, note that IDP is measuring trap-avoidance only.

7. **Baseline pilot for difficulty calibration** (Issue 9). Run 5-10 cases (2 easy, 2 medium,
   2 hard) with baseline condition before committing to the forced_multiround scope. If easy
   baseline < 0.70, revisit difficulty labels before full execution.

---

## Overall Assessment

The design is sound in its core structure. The scoring engine produces interpretable results.
The primary comparison (isolated_debate vs baseline on fair-comparison dims) is valid, the
rubric dimensions are appropriately scoped, and the N/A rules are coherent and pre-registered.

Two issues require correction before execution (Secondary H2 reframing, verification writebacks).
Five issues are valid design critiques that require either documentation changes or added
reporting commitments. Three issues either rest on incorrect factual premises (Issue 3) or
are correctly constrained by the preregistration's own diagnostic labeling (Issue 10).

The mechanism claim in Issue 1 is the most substantively interesting critique: it correctly
identifies that `isolated_debate` tests role-framing rather than adversarial exchange, and
that the hypothesis mechanism text does not perfectly match the primary condition. This does
not invalidate the experiment — it means a positive result on isolated_debate establishes
a role-framing effect, and the comparison of multiround vs isolated_debate within the
experiment isolates the additional exchange effect. The design supports both inferences;
the hypothesis text should be revised to say so cleanly.

The overall verdict on whether this design can produce interpretable evidence for or against
the hypothesis: **yes, with the two blockers resolved and the reporting commitments added.**
