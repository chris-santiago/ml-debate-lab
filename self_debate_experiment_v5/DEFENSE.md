# DEFENSE.md — v5 Experimental Design

**Phase 4 Protocol Self-Review — Mode 1 Initial Defense**

Defender role. Two-pass structure: Pass 1 (full analysis) completed before any verdict labels
are assigned. Pass 2 (verdict selection) follows.

---

## Implementation Soundness Check

Before engaging with the critique, there is a configuration dependency that the critique does
not raise but which must be confirmed before execution.

**Difficulty label dependency:** The selected benchmark cases (`selected_cases_all.json`) have
no `difficulty` field in their schema. The `difficulty` label (`hard` / `medium` / `easy`) is
derived by `normalize_cases.py` from `_pipeline.proxy_mean` using fixed thresholds
(hard < 0.55, medium 0.55-0.85, easy >= 0.85). The scoring engine (`self_debate_poc.py`) reads
`case['difficulty']` directly and uses it to gate forced_multiround execution. If
`normalize_cases.py` is not run before Phase 5, the scoring engine will crash on the
`forced_multiround` condition.

The plan does include `normalize_cases.py` in the script index (Phase 0/setup), but it is not
explicitly mandated as a Phase 0 blocking step in `phase_00_setup.md`. This must be confirmed.

**Pre-execution requirement:** Verify that `normalize_cases.py` is confirmed to run between
`selected_cases_all.json` population and `self_debate_poc.py` execution. This step must produce
`benchmark_cases.json` before Phase 5. It is not a design flaw, but an unconfirmed configuration
dependency that would cause silent failure if skipped.

---

## Pass 1 — Full Analysis

### Issue 1 — Benchmark filtered on test-model scores (same-model circularity)

**What the critic claims:** Cases were filtered using Sonnet's proxy_mean scores, then the
experiment evaluates those same cases using Sonnet. The `fc_lift` signal could reflect
regression-to-mean, prompt framing effects, or inference compute differences rather than a
genuine protocol advantage. Phase 9 (cross-vendor scoring) is positioned post-H1 and cannot
prevent the circularity from contaminating the primary conclusion.

**Analysis:** The circularity concern has two separable components that the critique fuses.

Component A: Selection bias. Cases filtered on proxy_mean < 0.83 are cases where Sonnet
single-pass failed. This is intentional and correct design: you want cases where there is
headroom for the debate protocol to show value. If Sonnet already solves every case at single-
pass, the experiment has no discriminating power. Selecting cases where the baseline model
struggles is standard benchmark design, not circularity. The concern about regression-to-mean
(giving Sonnet a second chance under role structure) is real but overstated: the
isolated_debate condition gives each agent only `task_prompt`, structurally identical to the
information available in baseline. The additional inference is not merely a retry — it is
structured role separation that forces distinct engagement pathways.

Component B: Phase 9 timing. This is the valid structural concern. Phase 9 runs after H1 is
judged. If cross-vendor fc_lift disagrees in direction or magnitude with the Claude-scored
fc_lift, the primary conclusion has already been stated. The remediation is not to move Phase 9
before H1 (which would require external API coordination during the experiment's critical path
and create logistical dependencies), but to pre-specify what happens if Phase 9 disagrees. That
interpretation rule is currently absent from PREREGISTRATION.json and EXECUTION_PLAN.md.

**What remains genuinely uncertain:** Whether the adversarial role structure (rather than compute
alone) drives any observed fc_lift. This is precisely what H2 tests. The concern is sound as
a motivator for H2's importance, not as a flaw in the benchmark's case selection logic.

---

### Issue 2 — H1 is a compute comparison; mechanism requires H2

**What the critic claims:** H1 (debate vs. baseline) cannot isolate adversarial role structure
from additional compute. Any multi-call protocol would produce positive fc_lift against
single-pass baseline. The mechanism claim ("adversarial role separation forces engagement")
is only testable via H2 (debate vs. ensemble). If H1 passes and H2 fails, the mechanism is
not demonstrated, but the pre-registration contains no outcome matrix specifying what
conclusion to draw in that case.

**Analysis:** The critique is technically correct about the mechanism. However, it conflates the
experiment's two goals, which are not identical.

H1 is a necessary condition: if the debate protocol does not outperform doing nothing, the
protocol has no practical value regardless of mechanism. H2 is a mechanism test: if debate
outperforms a compute-matched parallel alternative (ensemble), the advantage is attributable
to adversarial role structure rather than compute volume.

This two-tier structure (H1 as necessary condition, H2 as mechanism isolation) is standard
experimental logic. The experiment is NOT designed to validate the mechanism on H1 alone. The
design intent is:
- H1 passing establishes that debate is worth using over doing nothing.
- H2 passing establishes that adversarial structure is the reason.
- H1 passing + H2 failing means "more compute helps; adversarial structure doesn't add beyond
  that" — a meaningful and honest result.

The actual flaw is that this outcome matrix is not pre-specified. PREREGISTRATION.json lists
H1 and H2 as primary and secondary without stating what conclusion each {pass/fail} combination
supports. This means a future reader could cite "H1 passed" as mechanism validation even if H2
fails. The fix is not to restructure the hypothesis hierarchy but to add a pre-committed
interpretation table to EXECUTION_PLAN.md.

Note: HYPOTHESIS.md states the mechanism claim ("Adversarial role separation forces engagement
with both sides") as a narrative explanation, not as a testable claim with a criterion. This
framing is the source of the ambiguity. The narrative should be downgraded to a motivation
statement, or H2 should be elevated to co-primary status for mechanism-claim validation.

---

### Issue 3 — No mixed cases removes the hardest discrimination task

**What the critic claims:** The benchmark's binary structure (critique / defense_wins) excludes
mixed cases — cases where flaws exist but do not invalidate the design. Mixed cases are where
adversarial structure is most differentiated from single-pass review. The 0-mixed outcome is
stated as an architectural decision but may reflect a structural pipeline limitation.

**Analysis:** The critique is correct that mixed cases are the hardest discrimination task, and
correct that the debate protocol's value proposition is most legible on mixed cases. This is a
genuine scope limitation.

The defense is not that mixed cases are unnecessary — it is that establishing protocol validity
on binary-verdict cases is the appropriate first test before extending to mixed cases. You
cannot validate that the protocol produces correct binary verdicts and then claim it handles
ambiguity unless the binary case is solved first. The v5 benchmark answers the binary question;
it does not answer the mixed-case question.

On the claim that "most methodology critiques involve legitimate tradeoffs" — this may be true
of real-world methodology review, but the benchmark is synthetic. The pipeline was designed to
plant clearcut flaws and clearcut-sound designs. The 0-mixed outcome reflects both a pipeline
design choice and a deliberate scoping decision. It is not a hidden failure mode; it is an
acknowledged limitation.

The risk the critic identifies — that conclusions from Phase 8 generalize beyond binary-verdict
cases — is real and must be addressed in conclusions. The mechanism claim ("forces engagement
with both sides") implicitly requires mixed cases to be fully demonstrated. Scoping the
conclusions to binary-verdict cases is a pre-execution requirement.

---

### Issue 4 — Aggregate fc_lift mixes dimension counts across strata

**What the critic claims:** Critique cases contribute 4-dimension per-case means (IDR, IDP,
DRQ, FVC); defense_wins cases contribute 2-dimension per-case means (DRQ, FVC only). A
condition strong on DRQ/FVC but weak on IDR/IDP can produce inflated aggregate fc_lift if
defense_wins cases are numerically significant (N=30 of 110 = 27%). H1 is judged on this
aggregate, which may not surface IDR/IDP deficits.

**Analysis:** The dimensional imbalance is real. The pre-registered stratum breakdown partially
addresses it — fc_lift is reported separately for critique and defense_wins strata — but the
stratum breakdown is interpretive, not part of the H1 pass/fail criterion. A condition that
passes H1 via defense_wins DRQ/FVC strength while failing on critique IDR/IDP would not be
flagged by the current pass criterion.

The defense is that this is detected precisely when the stratum breakdown is examined: if
fc_lift(critique) and fc_lift(defense_wins) diverge substantially, the aggregate fc_lift is
flagged as a composition artifact. The stratum analysis is pre-registered and mandatory in
Phase 8. The weakness is that this detection is post-hoc (after H1 has already been judged).

The sensitivity analysis (`sensitivity_analysis.py`) is pre-planned for Phase 7 and will
compute per-dimension lift. The critic's proposed fix — reporting fc_lift computed both ways
(per-case mean aggregation vs. per-dimension aggregation) — is achievable within the existing
sensitivity analysis infrastructure and adds very low implementation cost. The stratum
breakdown report plus per-dimension lift computation together address the concern.

The concern is not fatal: the 80/30 split means critique cases dominate (73% of the aggregate),
and IDR/IDP apply fully to critique cases. A protocol with genuine IDR/IDP deficits would
likely fail fc_lift on the critique stratum. But the point stands that the current H1 criterion
does not explicitly guard against this pattern.

---

### Issue 5 — +0.10 threshold without power analysis

**What the critic claims:** The +0.10 threshold was set before characterizing within-case score
variance. LLM evaluation scores are known to have high run-to-run stochasticity (0.1-0.3 per
dimension). If within-case variance across 3 runs is substantial, the CI on fc_lift could be
wider than 0.10, making the test unable to distinguish fc_lift = 0.10 from fc_lift = 0.00.
The within-case variance analysis is planned for Phase 7 (post-execution), not as a gate.

**Analysis:** The variance concern is legitimate and the timing problem is real. However, the
critique overstates the sensitivity of the threshold choice. A variance analysis requires
variance data, which requires at least some runs to have been executed. The Phase 5.5 pilot
runs one pass per case on 10 cases; it does not generate within-case variance estimates from
3 runs per case. The critic's proposed resolution — running 3 passes per pilot case to estimate
variance before committing — is the correct fix, and it is achievable within Phase 5.5 by
extending the pilot.

The structural argument: the +0.10 threshold was not chosen arbitrarily. It reflects the
substantive judgment that a protocol improvement below 10 percentage points would not be
practically meaningful for adoption decisions, regardless of statistical significance. This
is a policy threshold, not a power-derived threshold. The two are different: power analysis
determines whether the threshold is detectable at the chosen N, while the threshold itself
reflects the minimum effect size worth caring about.

The actionable concern is whether +0.10 is *detectable* at N=110 with 3 runs per case, not
whether it is the right threshold. Phase 7's `within_case_variance_results.json` addresses
this post-hoc. The improvement is to add a pre-execution variance estimate from the Phase 5.5
pilot as a gate: if within-case variance implies CIs wider than 0.10, increase n_runs_per_case
before the full run. This converts a post-hoc diagnostic to a decision gate.

---

### Issue 6 — N=30 defense_wins cases for H3 is underpowered

**What the critic claims:** Binomial standard error at N=30, p=0.60 is approximately 0.089.
The test has poor discriminating power within ±10 percentage points of the threshold. H3 is
presented in a pass/fail format that implies statistical reliability it does not have.

**Analysis:** The binomial math is correct. H3 at N=30 is not a well-powered binary test.
The critic correctly identifies that a true rate of 55% (below threshold) would pass H3 in
roughly 30% of experiments, making the test approximately a coin flip near the threshold.

The defense is that H3 is a secondary hypothesis. H3's role is to establish that ensemble is
not systematically failing on defense_wins cases — a directional check, not a powered binary
test. The question is whether the current pre-registration format (which implies binary
pass/fail) accurately describes H3's actual evidential weight.

The fix is not to increase defense_wins case count (which would require re-running the
pipeline and re-selecting cases, a significant scope change) but to revise the pre-registration
framing: explicitly state that H3 is a directional hypothesis evaluated descriptively, with
the pass/fail threshold serving as a reference point rather than a powered decision boundary.
This is a documentation fix, not an experimental redesign.

---

## Pass 2 — Verdict Selection

| Issue | Verdict | Summary |
|-------|---------|---------|
| 1 — Same-model circularity | Rebut (partial concede) | Selection bias component is rebutted: filtering for hard cases is standard benchmark design. The "second chance" framing is incorrect for isolated_debate (role structure, not retry). Concede on Phase 9 timing: no pre-specified consequence for Phase 9 disagreement. |
| 2 — H1 is compute comparison | Rebut (partial concede) | H1/H2 two-tier structure is correct experimental logic. Rebutted: H1 as necessary condition is appropriate. Concede: no pre-committed outcome matrix for {H1, H2} combinations. Without it, a reader could misread "H1 passed" as mechanism validation. |
| 3 — No mixed cases | Concede (scope) | Correct: benchmark cannot test the discrimination task most relevant to the mechanism claim. Rebutted on severity: binary-verdict validity is the correct first test. Concede that conclusions must be scoped to binary-verdict cases only. |
| 4 — Aggregate fc_lift dimension mismatch | Rebut (partial concede) | Stratum breakdown is pre-registered and will surface the composition effect. Concede: per-dimension lift computation should be explicitly added to the sensitivity analysis as a reported output, not just a post-hoc check. |
| 5 — Threshold without power analysis | Rebut (partial concede) | Threshold is a policy choice (minimum practically meaningful effect), not a power-derived value. This distinction is valid. Concede: variance must be characterized before the full run, not after. Phase 5.5 should be extended to 3 runs per pilot case to generate a pre-execution variance gate. |
| 6 — N=30 for H3 | Concede (framing only) | Binomial math is correct. H3 is secondary. Concede: the pre-registration must explicitly state H3 is directional/descriptive, not a powered binary test. No experimental redesign required. |

---

## Pre-Execution Requirements

Derived from all Concede and Rebut (partial concede) verdicts above. These items must be
confirmed before execution proceeds to Phase 5.

| # | Source | Item | Verification Method | Status |
|---|--------|------|---------------------|--------|
| PRE-1 | Implementation check | `normalize_cases.py` confirmed as mandatory blocking step between `selected_cases_all.json` and Phase 5. `benchmark_cases.json` must exist before `self_debate_poc.py` executes. | Verify `phase_00_setup.md` or `EXECUTION_PLAN.md` requires `normalize_cases.py` and checks for `benchmark_cases.json` before Phase 5 gate. | PENDING |
| PRE-2 | Issue 1 (partial concede) | Phase 9 cross-vendor disagreement rule: if cross-vendor fc_lift disagrees in direction or is more than 0.10 lower in magnitude compared to Claude-scored fc_lift, H1's generality claim must be explicitly qualified in CONCLUSIONS.md and REPORT.md. This rule must be pre-specified, not applied post-hoc. | Confirm the rule appears in EXECUTION_PLAN.md as a Phase 9 interpretation directive. | PENDING |
| PRE-3 | Issue 2 (partial concede) | Pre-committed outcome matrix for H1 × H2: (a) H1 pass + H2 pass = debate outperforms baseline; adversarial structure demonstrated. (b) H1 pass + H2 fail = compute benefit confirmed; adversarial structure not demonstrated beyond compute volume. (c) H1 fail = protocol provides no benefit over baseline; H2 not interpretable. This matrix must appear in EXECUTION_PLAN.md before execution. | Confirm matrix is present in EXECUTION_PLAN.md. | PENDING |
| PRE-4 | Issue 3 (concede) | Phase 8 CONCLUSIONS.md must explicitly scope all protocol claims to binary-verdict cases (critique and defense_wins). The mechanism claim ("adversarial role separation") cannot be generalized to mixed-verdict scenarios from this benchmark. | Confirm scope statement appears in Phase 8 conclusions template or as a mandatory reporting norm. | PENDING |
| PRE-5 | Issue 4 (partial concede) | Sensitivity analysis must include: (a) per-dimension lift averaged across applicable cases, reported alongside the per-case-mean aggregate; (b) explicit note if the two methods produce materially different lift values (threshold: > 0.05 difference). | Confirm `sensitivity_analysis.py` outputs both computations. | PENDING |
| PRE-6 | Issue 5 (partial concede) | Phase 5.5 pilot extended to 3 runs per case (not 1) on its 10 cases. After Phase 5.5, compute within-case variance. If mean within-case SD across pilot dimensions > 0.10, increase `n_runs_per_case` from 3 to 5 before the full Phase 6 run. This is a decision gate, not a diagnostic. | Confirm Phase 5.5 instructions are updated to run 3 passes per pilot case and include the variance gate rule. | PENDING |
| PRE-7 | Issue 6 (concede) | PREREGISTRATION.json H3 entry must be annotated as directional/descriptive: "H3 is not powered for binary pass/fail at N=30. The 60% threshold is a reference point for directional assessment. Results are reported descriptively with binomial CI; no pass/fail judgment is made." | Confirm annotation appears in PREREGISTRATION.json or EXECUTION_PLAN.md H3 entry. | PENDING |

---

## Overall Verdict

**Defense holds with conditions.** None of the six critique points is fatal to the experiment.
Issues 1, 2, 4, and 5 each identify a real documentation or design gap that is addressable
before execution. Issues 3 and 6 identify scope limitations that are acknowledged and do not
undermine the primary test. The seven pre-execution requirements above define what must be
confirmed before Phase 5. If PRE-2 and PRE-3 are satisfied — the Phase 9 interpretation rule
and the H1 × H2 outcome matrix — the experiment's conclusions will accurately reflect what the
data can and cannot show.

The critic's most important contribution is Issue 2: without the pre-committed outcome matrix,
a reader could misattribute compute benefits to adversarial structure. The defender concedes
this gap and requires it to be closed before execution.
