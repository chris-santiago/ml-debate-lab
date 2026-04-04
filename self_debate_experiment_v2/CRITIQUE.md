# CRITIQUE.md — Self-Debate Protocol v2

**Critic:** Adversarial critic subagent (Mode 1 — Initial Critique)
**Date:** 2026-04-04

---

## Critique — Cycle 1

The experiment reports a +0.586 lift and declares the isolated self-debate protocol
substantially superior to a single-pass baseline. I find seven issues of varying severity,
organized below by their shared root assumptions. Several are fundamental enough to
challenge the primary claim; others are narrower but still material.

---

### Group A: The Scoring System Is Not Independent of the Protocol Designer

**Issues 1 and 2 share the same root:** the entity that designed the benchmark, wrote the
task prompts, specified the ground-truth labels, defined the rubric dimensions, and then
scored the transcripts is the same model instance that produced those transcripts — or at
minimum, operates from the same context and knowledge base in the same experimental session.

---

#### Issue 1 — The Scorer Is the Same Model as the Agents It Scores

**Claim being made:** The rubric scores (IDR, IDP, DC, DRQ, ETD, FVC) represent an
objective assessment of protocol quality by an independent judge.

**Why this might be wrong:** The README states that scoring is performed by a fourth LLM
call per case: "The Scorer produces a JSON object with scores (1.0 / 0.5 / 0.0 / null)
and one-sentence justifications for each of the 6 rubric dimensions." The model playing
the Scorer role is the same model (claude-sonnet-4-6) that played the Critic, Defender,
and Judge roles. The Scorer has access to the ground-truth `must_find` labels — which
were themselves written by the same model family during benchmark construction.

The specific failure mechanism: a language model asked to score its own outputs against
ground truth that it effectively generated will exhibit self-consistency bias. It will
recognize the phrasing it used in the agent transcripts and match it to the `must_find`
labels it knows — not because the outputs are genuinely correct, but because they are
stylistically concordant with the expected answers. This is not independence; it is
circular validation.

**What would constitute evidence:**
- Have a different model family (e.g., GPT-4o or Gemini 1.5 Pro) score the same transcripts
  against the same rubric without access to the `must_find` labels. If IDR scores differ
  by more than ±0.1 on average, the self-scoring hypothesis is material.
- Alternatively: present a scorer from the same model family with deliberately incorrect
  transcripts (ones that use the right ML vocabulary but identify the wrong issues) and
  verify that it scores them at IDR=0.0, not IDR=1.0. If the scorer grants credit based on
  surface plausibility rather than correctness, self-consistency bias is operative.

---

#### Issue 2 — The Benchmark Was Constructed by the Protocol Designer, Creating Optimality Bias

**Claim being made:** The 20 benchmark cases are a fair, representative, and difficult test
of ML reasoning that the protocol must overcome genuinely.

**Why this might be wrong:** The task prompts in BENCHMARK_PROMPTS.md are clean, well-scoped
single-scenario descriptions with one or two explicitly nameable flaws. The `must_find`
labels are strings like `"unequal_eval_set_size"`, `"training_regime_confound"`, and
`"sku_mix_confound"` — labels that directly name the issue rather than requiring the model
to derive it from context.

The mechanism of failure: when the same system that knows what the planted flaws are also
writes the task prompts, it will unconsciously write prompts that make those flaws
discoverable via the kind of reasoning it knows it can do. The prompts are almost uniformly
one-flaw or two-flaw scenarios with the critical information stated explicitly in the task
description. Real ML reasoning tasks involve ambiguity about whether there is a problem,
multiple interacting confounds, missing information that the evaluator must flag, and
genuine irreducible uncertainty. None of the 20 cases involve missing information as the
primary challenge. All 20 have a determinate ground-truth answer known to the scorer.

The 1.000 IDR across all 15 critique-wins/mixed cases — i.e., the protocol found every
planted issue in every applicable case — is more consistent with benchmark leakage than
with genuine recall at ceiling performance.

**What would constitute evidence:**
- Construct a parallel 10-case benchmark using a genuinely independent source: cases drawn
  from published ML paper retractions, NeurIPS reproducibility study failures, or Kaggle
  post-mortems, where the "ground truth" is established by domain consensus, not by the
  protocol designer. Run the same protocol on these cases and report IDR.
- Alternatively: give the task prompts to a naive expert human (a senior ML engineer who has
  not seen the benchmark design) and ask them to identify issues without any rubric. Compare
  which issues they find to `must_find`. If humans miss 30-40% of the planted issues while
  the protocol finds 100%, either the humans are wrong or the benchmark is easier for LLMs
  than for humans — both warrant explanation.

---

### Group B: The Baseline Is Structurally Penalized in Ways Unrelated to Reasoning Quality

**Issues 3 and 4 share the root:** two rubric dimensions are mechanically zeroed for the
baseline regardless of what the baseline actually outputs, and these two dimensions account
for a substantial portion of the lift.

---

#### Issue 3 — Defense Calibration Is Hardwired to 0.0 for the Baseline

**Claim being made:** The baseline's 0.000 defense_calibration score reflects a genuine
inability to perform the calibration function.

**Why this might be wrong:** The scoring code at line 142 contains:

    baseline_scores["DC"] = 0.0

This is not a score assigned by a scorer; it is a hardcoded override applied unconditionally
to every baseline case before the benchmark mean is computed. DC is then applied to all 20
cases, making it the most influential single dimension in the baseline's aggregate (it
contributes 1/N_applicable per case, and N_applicable = 20). The authors justify this as
"structural: no revision step; position_update = 0.0."

The mechanism of failure: the baseline DC=0.0 is tautological. The rubric defines DC for
the baseline as 0.0 because the baseline has no revision step, and then uses DC=0.0 as
evidence that the baseline cannot calibrate its defense. This is circular: the score does
not measure the baseline's reasoning quality; it measures the rubric's definition of the
baseline. A single-pass response can absolutely express calibrated uncertainty — it can say
"the critique's concern about X is valid, but the defense of Y stands because Z." Calling
that 0.0 on DC because no structured Defense agent produced it is definitional punishment,
not empirical measurement.

The impact is large: the DC contribution alone accounts for roughly 0.133 of the 0.867
DC dimension delta (over 20 cases, DC goes from 0.0 baseline to 0.867 debate). This is
the single largest dimension gap in the experiment.

**What would constitute evidence:**
- Score a sample of baseline outputs on DC using human raters who are not told the
  experimental condition, using the same rubric definition ("does the response acknowledge
  real issues while defending sound aspects?"). If human raters assign DC > 0.0 to even
  30% of baseline responses, the structural zeroing is incorrect.
- As a direct test: evaluate whether a baseline response that explicitly concedes planted
  issues and defends sound aspects would receive DC=0.0 or DC>0.0 under the current
  scoring code. The code says it would receive DC=0.0 regardless. If that is correct, the
  rubric is not measuring calibration — it is measuring protocol structure.

---

#### Issue 4 — DRQ Is Capped at 0.5 for the Baseline

**Claim being made:** The baseline's debate_resolution_quality scores represent a fair
measurement of its resolution quality.

**Why this might be wrong:** Line 143-144 of the scoring code caps the baseline's DRQ at
0.5 unconditionally:

    if baseline_scores.get("DRQ") is not None and baseline_scores["DRQ"] > 0.5:
        baseline_scores["DRQ"] = 0.5

DRQ is applied to all 20 cases (N_applicable=20). DRQ at 0.5 for the baseline means
it can never be scored as having produced the correct resolution type — even if its
single-pass response happens to correctly identify that the case requires an empirical
test and specifies what that test should be. The authors justify this because "no actual
debate was performed." But the empirical test for a single-pass response is whether it
arrives at the correct verdict type, not whether it used a debate protocol to get there.

Combined with Issue 3, the baseline is penalized by design on two of the six dimensions
before any empirical measurement of its outputs occurs. The baseline mean of 0.384 is
partly a function of these structural penalties, not purely of output quality. The true
lift attributable to the protocol's reasoning advantage — as distinct from the lift
attributable to rubric design choices — is not reported.

**What would constitute evidence:**
- Re-score all 20 baseline outputs removing the DC=0.0 override and the DRQ cap, using
  the same scoring logic applied to the debate protocol. Report the recalculated baseline
  mean and lift. This is a within-experiment sensitivity analysis that requires no new
  data collection.
- If the lift at 0.586 shrinks to, say, 0.3 under the uncapped baseline, then 0.286 of
  the headline lift is attributable to rubric design rather than protocol performance.

---

### Group C: Compute Confound — The Protocol Gets More Tokens

**Issue 5 — The Lift May Be a Token Budget Effect**

**Claim being made:** The lift attributable to the isolated debate protocol stems from the
adversarial role structure — the mechanism described in the hypothesis ("explicit adversarial
persona assignment forces the model to challenge surface-plausible framing").

**Why this might be wrong:** The debate protocol makes six LLM calls per case: Critic,
Defender, Judge, Scorer, Baseline, Scorer-for-baseline. The debate path alone (Critic +
Defender + Judge) generates approximately 3x the output tokens that the baseline generates.
The Judge then adjudicates by reading both prior outputs — it receives not just the task
prompt but also the full Critic and Defender outputs, giving it substantially more context
from which to synthesize a correct verdict.

The hypothesis mechanism is "adversarial persona assignment forces challenge." But an
alternative equally plausible mechanism is "the Judge sees three independent passes through
the problem (task prompt, Critic output, Defender output) and synthesizes from more
information." This is not an adversarial debate effect; it is a chain-of-thought and
information aggregation effect. A self-consistency ensemble (run the same single-pass
baseline three times and take the majority verdict) might achieve comparable IDR and FVC
without any persona structure at all.

The baseline gets one pass. The effective information available to the Judge is equivalent
to a 3-sample ensemble. No attempt is made to control for this compute difference.

**What would constitute evidence:**
- Run a compute-matched baseline: three independent single-pass responses to the same task
  prompt, synthesized by a fourth call that reads all three and produces a final verdict.
  No Critic/Defender role distinction. Compare this ensemble baseline to the debate protocol
  on the same 20 cases.
- Alternatively: run only the Judge prompt (with three fabricated "neutral" inputs of
  equivalent length) and measure FVC. If FVC approaches 1.0 even without adversarial roles,
  the role structure is not doing the causal work.

---

### Group D: The Convergence Reversal Is Rationalized, Not Explained

**Issue 6 — The Convergence Non-Finding Is a Pre-Registered Hypothesis Failure Dressed Up as an Insight**

**Claim being made:** The observation that hard cases show higher convergence than easy
cases is "expected and desired" and "the difficulty categorization reflects reasoning depth,
not issue discoverability."

**Why this might be wrong:** The hypothesis explicitly pre-registered:
"agent_convergence_rate on easy cases > agent_convergence_rate on hard cases."
This is the only secondary hypothesis in the experiment that was not supported. The report's
explanation — that hard case confounds are easily discoverable while defense_wins cases
require subtle judgment — is generated after observing the data, not before.

The specific mechanism of post-hoc rationalization: the authors observe that the easy cases
with convergence=0.5 are all defense_wins cases (defense_wins_003), then reframe "easy"
as a difficulty label that does not predict discoverability. But this reframing is
unfalsifiable: any convergence pattern can be explained post-hoc by redefining what
"difficulty" is measuring. The pre-registered expectation was grounded in the intuition
that harder issues require more specialized reasoning to independently discover — if
that intuition was wrong, the authors should say so and acknowledge we do not understand
what drives convergence, not claim the result "confirms" a theory they did not hold before
seeing the data.

Furthermore: there are only 3 easy cases in the benchmark. A convergence estimate over 3
cases has enormous variance. The easy=0.833 value is driven by a single defense_wins_003
case with conv=0.5. One case determines the entire difficulty stratum. The convergence
comparison by difficulty is noise, not signal.

**What would constitute evidence:**
- 3 easy cases is not a sample. Any claim about convergence stratified by difficulty
  requires at least 10 cases per difficulty tier to be interpretable. The present result
  cannot distinguish "hard cases show higher convergence" from "we have 3 easy cases and
  one of them failed."
- A fair test: fix the difficulty labels before running the experiment and pre-specify the
  convergence prediction case-by-case, not just at the tier level. Then examine whether
  convergence is predicted by difficulty within non-defense_wins cases, where the
  judgment call ambiguity is removed.

---

### Group E: The "Failure Modes Are Tractable" Claim Is Assertion, Not Evidence

**Issue 7 — The Protocol's Failure Rate on Its Own Terms Is Higher Than Reported**

**Claim being made:** "Both failure modes are tractable: they are prompt-level calibration
failures, not architectural limitations of the isolated protocol."

**Why this might be wrong:** This claim rests on a confidence that the two failure modes
(reasoning/label disconnect in real_world_framing_001; under-confidence in
defense_wins_003 and defense_wins_005) are prompt-engineering problems rather than
model-level limitations. There is no evidence for this distinction.

The specific failure mechanism: the reasoning/label disconnect in real_world_framing_001
is not a minor calibration error. The Defender produced a correct internal analysis and
then assigned an inconsistent verdict label. This is precisely the class of failure that
structured prompting is supposed to prevent — if the model's reasoning process and its
output label can diverge even under structured persona prompting, then the entire
assumption that explicit role assignment produces reliable verdict typing is undermined.
The authors propose a fix ("require the Defender to complete analysis before selecting a
verdict label") that is itself an additional prompting constraint that may or may not
work. Whether it works is an empirical question that this experiment does not test.

More concretely: the disconnect failure appeared in the real_world_framing category with
1/2 cases (50% failure rate within that category). The authors recommend adding more
real_world_framing cases. But if the failure rate in that category is 50%, adding more
such cases would likely lower the benchmark score, not support the conclusion that the
failure mode is tractable.

Similarly: the under-confidence failure on defense_wins cases occurred in 2/5 cases
(40% failure rate on DC within defense_wins cases, counting 0.5 as a partial failure).
The protocol's success on defense_wins is presented as its most compelling result, but
40% of defense_wins cases showed partial or complete DC failure. The headline "all 5
defense_wins cases reach the correct defense_wins verdict" is technically true but masks
the fact that the scoring mechanism is what rescued those cases — DRQ and FVC remained
1.0 because the Judge assigned the right verdict, while DC=0.5 on the Defender itself.

**What would constitute evidence:**
- Implement the proposed Defender prompt fix (two-pass analysis-then-label) and re-run
  the 3 failed/partial cases. If the failure rate drops to 0/3, the fix is tractable.
  If it drops to 1/3, it is partially tractable. If it remains 2-3/3, it is not a
  prompt-engineering problem.
- Run the real_world_framing category on 10 additional cases of similar complexity. A
  50% failure rate on 2 cases is uncertain; a 50% failure rate on 12 cases is a finding.

---

## Summary of Claims vs. Evidence

| Issue | Root cause | Severity | Testable? |
|-------|-----------|----------|-----------|
| 1. Self-scoring bias | Same model scores its own outputs | High | Yes — cross-model scorer |
| 2. Benchmark leakage | Designer knows the planted issues | High | Yes — independent benchmark |
| 3. DC hardcoded to 0.0 | Rubric penalizes baseline by definition | High | Yes — sensitivity rerun |
| 4. DRQ capped at 0.5 | Same as Issue 3 | Medium | Yes — sensitivity rerun |
| 5. Compute confound | Protocol runs 3x tokens vs. baseline | High | Yes — ensemble baseline |
| 6. Convergence post-hoc | 3 cases is not a sample; result rationalized | Medium | Yes — larger per-tier N |
| 7. Tractability unproven | No evidence prompt fix works | Medium | Yes — targeted rerun |

The four high-severity issues (1, 2, 3, 5) are structural and would each independently
reduce the claimed lift if addressed. The combination — same-model scoring of same-model
outputs on designer-constructed benchmarks, with hardcoded rubric penalties on the baseline
and no compute control — means the experiment as run cannot distinguish "the debate protocol
reasons better" from "the experiment is set up to make the debate protocol look better."

The hypothesis may still be true. The mechanism described (adversarial role separation
enabling genuine defense_wins paths) is coherent and worth investigating. But the current
evidence does not establish it.
