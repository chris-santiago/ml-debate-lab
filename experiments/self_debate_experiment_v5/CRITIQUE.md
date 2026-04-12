# CRITIQUE.md — v5 Experimental Design

**Phase 4 Protocol Self-Review — Mode 1 Initial Critique**

Subject: The v5 experimental design — its hypothesis, conditions, rubric, and pre-registration.
This is a methodological critique of the experiment itself, not of any individual benchmark case.

Issues are organized by root cause. Each issue states the implicit claim, the mechanism of potential failure, and what evidence would settle the question.

---

## Root Cause A: Same-Model Circularity in Benchmark Selection

### Issue 1 — Benchmark difficulty is calibrated for the model under test

**The claim being made:** The benchmark cases are appropriately difficult and representative of
cases where the debate protocol should show advantage.

**Why that claim might be wrong:** Cases were smoke-tested by claude-sonnet-4-6 running blind, and
`proxy_mean` (the primary difficulty signal and case-filter input) is a Sonnet score. Cases with
`proxy_mean > 0.83` were discarded as too easy. The main experiment then evaluates those same
filtered cases using the same model across five conditions. The benchmark has been specifically
selected to contain cases that Sonnet gets wrong in single-pass mode — i.e., cases that target
this model's specific failure modes.

The mechanism of failure: if debate helps on these cases via any route — regression to mean from
multiple attempts, slightly different prompt framing in the adversarial structure, or simply more
total inference compute — the fc_lift will be positive without that lift reflecting a generalizable
protocol advantage. You are selecting hard cases for Model X, then measuring whether giving Model X
a second chance (under role structure) helps it. The second chance confounds with structure.

Additionally, the cross-vendor scorer (Phase 9) runs after H1 is already judged. It is the only
design element that could distinguish model-specific calibration from protocol-generalizable
improvement, but it is positioned as an optional post-hoc check rather than a pre-condition for
the primary conclusion.

**What would settle it:** Run Phase 9 scoring in parallel with Phase 7 rather than after H1 is
judged. If cross-vendor fc_lift is consistent with claude-sonnet-4-6 fc_lift (within CI), the
model-circularity concern is addressed empirically. If the cross-vendor model shows a materially
different lift direction or magnitude, H1's claim to generality is undermined and should be
explicitly flagged in conclusions rather than treated as a robustness check.

---

## Root Cause B: Primary Hypothesis Does Not Test the Stated Mechanism

### Issue 2 — H1 is a compute comparison; the mechanism claim requires H2

**The claim being made:** H1 tests whether adversarial role separation ("adversarial role
separation forces engagement with both sides") produces better verdicts than single-pass review.

**Why that claim might be wrong:** H1 compares isolated_debate to baseline — the cheapest
condition. The debate condition uses more total tokens and inference calls than baseline by design.
Any mechanism that benefits from more compute — ensemble averaging, simple retry, chain-of-thought
expansion — would also produce positive fc_lift against a single-pass baseline. The mechanism
claim in HYPOTHESIS.md is specifically about *adversarial structure* forcing engagement. That
mechanism is only isolable in the H2 comparison (debate vs. ensemble), which is a secondary
hypothesis. H2 is explicitly the compute-matched adversarial test.

If H1 passes and H2 fails, the correct interpretation is "more compute helps" not "adversarial
structure helps." The pre-registration does not address what conclusion to draw in this case. H1
passing would be cited as protocol validation despite the mechanism being undemonstrated.

**What would settle it:** H2 must be explicitly included in the primary pass/fail determination,
or the hypothesis statement must be revised to claim only "debate outperforms single-pass baseline"
without attributing the advantage to adversarial role separation. If the mechanism claim is
retained, the pass criterion for validating the mechanism is H2, not H1. The current design
inverts this: H1 is primary (validates claim) and H2 is secondary (tests mechanism).

---

## Root Cause C: Benchmark Structure Cannot Detect the Hardest Case Type

### Issue 3 — No mixed cases removes the discrimination task most relevant to the mechanism

**The claim being made:** The two-stratum benchmark (critique / defense_wins) is sufficient to
evaluate the debate protocol's ability to produce correctly typed verdicts.

**Why that claim might be wrong:** The ARCH-1 benchmark contains zero mixed cases — the
pre-registration explicitly notes this as an architectural decision rather than an oversight.
Mixed cases are scenarios where flaws exist but do not invalidate the design: the correct verdict
is neither "critique wins" nor "defense wins" but a qualified position requiring both genuine
criticism and genuine defense to coexist in the final verdict.

The adversarial mechanism under test — Critic and Defender each forced to argue their position —
is most differentiated from single-pass review precisely on cases where both sides have valid
claims. On a critique case, the Critic just needs to find the planted flaw; the adversarial
structure is incidental. On a defense_wins case, the Defender just needs to rebut. Only on mixed
cases does the protocol's ability to hold two positions simultaneously, weigh them, and produce
a calibrated resolution constitute a distinct capability not reducible to "who wins the argument."

The claim that mixed cases are absent because they are rare in real methodology review is an
empirical claim about the benchmark distribution, not about real-world methodology review. In
practice, most methodology critiques involve legitimate tradeoffs where the design is imperfect
but not disqualifying — the exact mixed case type.

**What would settle it:** Report what fraction of cases in the synthetic-candidates pool (before
selection) had mixed-appropriate ground truth. If the pipeline structurally cannot generate mixed
cases (all planted corruptions are designed as clearcut flaws), document this as a scope
limitation. The conclusions from Phase 8 should be scoped to binary-verdict cases only and should
not generalize to calibrated judgment under genuine ambiguity.

---

## Root Cause D: Aggregate fc_lift Mixes Incommensurable Per-Case Means

### Issue 4 — Per-case mean denominator varies by stratum, inflating defense_wins contribution

**The claim being made:** The aggregate fc_lift across all cases is a coherent summary statistic
for the fair-comparison set (IDR, IDP, DRQ, FVC).

**Why that claim might be wrong:** On critique cases, the per-case mean is computed over 4
dimensions (IDR, IDP, DRQ, FVC — all applicable). On defense_wins cases, IDR and IDP are N/A,
so the per-case mean is computed over 2 dimensions (DRQ and FVC only). The aggregate fc_lift
then averages per-case means computed over different dimensional bases: critique cases contribute
a 4-variable average, defense_wins cases contribute a 2-variable average.

A condition that does well on DRQ and FVC but poorly on IDR and IDP will show inflated fc_lift
if defense_wins cases are overrepresented in the aggregate — because those cases never expose
the IDR/IDP deficit. The current benchmark is 80 critique / 30 defense_wins. The aggregate
fc_lift denominator is consistent in case count, but the effective dimensionality per case is
2x different across strata.

This is not a fatal flaw if the stratum breakdown is reported alongside the global figure.
The problem is that H1 is judged on the global fc_lift. A protocol that fails on IDR/IDP
(missing flaws) but passes on DRQ/FVC (verdict label) across defense_wins cases can still
produce fc_lift >= 0.10 due to the dimensional imbalance.

**What would settle it:** Report fc_lift computed two ways — (a) current method (per-case mean
regardless of dimension count), and (b) per-dimension lift averaged across cases where that
dimension is applicable. If the two methods produce materially different lift values, the
aggregate confounds stratum composition with performance. If they agree, the concern is
empirically moot.

---

## Root Cause E: No Power Analysis; +0.10 Threshold Is Unjustified

### Issue 5 — The H1 threshold was fixed before variance structure was known

**The claim being made:** A benchmark lift of >= +0.10 is a meaningful and detectable effect
size for this sample.

**Why that claim might be wrong:** The +0.10 threshold was set before the variance structure
of the scoring dimensions was characterized. The pre-registration records 110 cases and 3 runs
per case but does not estimate within-case score variance, between-case score variance, or the
expected confidence interval width on fc_lift at N=110.

LLM evaluation scores on rubric dimensions are known to have high stochasticity — run-to-run
variance of 0.1–0.3 per dimension is common. If within-case variance across 3 runs is substantial,
the CI on the case-level mean could be wider than the 0.10 threshold, making the test unable to
distinguish fc_lift = 0.10 from fc_lift = 0.00 at any useful confidence level. The Wilcoxon
test in stats_analysis.py will produce a p-value, but the CI width is the more informative
quantity, and it depends on variance structure that was not pre-characterized.

The alternative failure mode: high within-case variance *helps* a condition that gets lucky in
one of the 3 runs. The 3-run average suppresses but does not eliminate this. If a single run
happens to be high-quality due to sampling, its contribution to the per-case mean carries
the same weight as consistently good runs.

**What would settle it:** After Phase 5.5 (15-case pilot), compute within-case variance across
3 runs before proceeding. If variance is high relative to 0.10, either (a) increase n_runs_per_case
from 3 to 5, or (b) report the CI explicitly and note that H1 is underpowered for the chosen
threshold. This should be a gate, not a post-hoc diagnostic.

---

## Root Cause F: Defense_wins Stratum N Is Insufficient for H3

### Issue 6 — H3 has poor discriminating power at the 60% threshold with N=30

**The claim being made:** H3 ("Ensemble FVC >= 0.5 on >= 60% of defense_wins cases") constitutes
a meaningful test of the ensemble condition's ability to handle defense cases.

**Why that claim might be wrong:** With N=30 defense_wins cases, the 60% threshold requires
18+ cases to pass. The binomial standard error at N=30, p=0.60 is sqrt(0.60 × 0.40 / 30) ≈ 0.089.
A one-sided 95% CI at the threshold runs from approximately 0.45 to 0.75. This means:

- A true ensemble FVC rate of 55% (below threshold) would pass H3 in roughly 30% of experiments
  at this sample size.
- A true ensemble FVC rate of 65% (above threshold) would fail H3 in roughly 30% of experiments.

The test is essentially a coin flip for true rates within about ±10 percentage points of the
threshold. H3 will not give a reliable signal about whether ensemble handles defense cases well.
The same low-N problem applies to the pre-registered stratum breakdown: phase 8 interpretation
relies on fc_lift stratified by critique and defense_wins, but 30-case defense_wins stratum
fc_lift has wide CIs that may render the stratum comparison uninterpretable.

**What would settle it:** Either (a) increase the defense_wins case count to at least 50 before
locking the benchmark, or (b) pre-register that H3 is a directional/descriptive hypothesis and
explicitly not powered for the binary pass/fail determination. The current pre-registration
presents H3 in a pass/fail format inconsistent with the sample size.

---

## Summary of Root Causes

| # | Issue | Root Cause | Severity |
|---|-------|-----------|---------|
| 1 | Benchmark filtered on test-model scores | Same-model circularity | High — compromises generality claim |
| 2 | H1 is compute vs. mechanism comparison | Primary H tests wrong quantity | High — mechanism claim unsupported by primary test |
| 3 | No mixed cases | Benchmark cannot test hardest discrimination | Medium — scopes but does not invalidate |
| 4 | Aggregate fc_lift mixes dimension counts | Stratum composition confound | Medium — may inflate or deflate lift depending on condition profile |
| 5 | +0.10 threshold without power analysis | Unjustified threshold | Medium — underpowered if within-case variance is high |
| 6 | N=30 defense_wins for H3 | Insufficient stratum N | Low–Medium — H3 underpowered, stratum CIs wide |
