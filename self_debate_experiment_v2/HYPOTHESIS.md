## Hypothesis — Cycle 1

**Claim:** On a re-validated 20-case benchmark of synthetic ML reasoning tasks with known
ground truth, the isolated self-debate protocol — where a language model plays explicit
Critique, Defense, and Judge roles in structured sequential prompts, with Critique and
Defense each receiving only the task_prompt (no shared context) — will achieve a benchmark
aggregate score ≥ 0.75 AND a lift of at least +0.10 over the trivial baseline (single-pass
answer plus self-critique, no revision or debate loop). Additionally: (a) issue_discovery_precision
scoring will be fixed for defense_wins cases where IDP is undefined when correct_position
= "defense"; (b) the partial-Defense-contestation failure mode observed in prior Experiment 1
(DC < 1.0 in 6/11 cases) will be re-examined under the isolated protocol on an expanded
case set; (c) agent_convergence_rate will serve as a diagnostic to distinguish easy vs.
hard cases; and (d) one new category of "real-world framing" cases (at least 2 cases) will
test protocol applicability beyond the original 5 benchmark categories.

**Mechanism:** Explicit adversarial persona assignment (Critique/Defense/Judge) in
sequential structured prompts forces the model to challenge surface-plausible framing
rather than qualify it. The isolated protocol (Defense receives only task_prompt, never
the Critique's output) prevents contamination of Defense reasoning by Critique output,
enabling genuine defense_wins paths on false-positive critiques and unbiased measurement
of agent_convergence_rate. The Judge adjudicates genuine independent divergence rather
than a pre-contaminated concession cascade.

**Signal:** Per-case rubric scores across 6 dimensions (issue_discovery_recall,
issue_discovery_precision, defense_calibration, debate_resolution_quality,
empirical_test_diagnosticity, final_verdict_correctness), the benchmark aggregate mean,
case-pass fraction, agent_convergence_rate stratified by difficulty tier, and the
debate-minus-baseline lift.

**Expected observable:**
- Debate benchmark aggregate mean ≥ 0.75 (11/11 prior cases achieved 1.000; full 20-case
  benchmark with harder and real-world-framing cases may reduce mean but should stay above
  threshold)
- Trivial baseline benchmark mean ≤ 0.60
- Debate-minus-baseline lift ≥ +0.10
- defense_wins cases correctly resolved at ≥ 75% rate (isolated protocol enables this path)
- agent_convergence_rate on easy cases > agent_convergence_rate on hard cases
- IDP dimension: no undefined scores (fixed for defense_wins cases)
- All 20 cases produce scoreable outputs (≥ 4 applicable dimensions)

**Architecture note:** This is a live API call implementation. Each case runs a real
3-agent sequential prompt chain via the Anthropic API (Critique → Defense → Judge).
Critique and Defense agents each receive only task_prompt. Judge receives task_prompt
plus both independent outputs. This is a structural departure from the prior simulated
transcript approach and directly tests whether live LLM outputs replicate the simulated
findings.

## Evaluation Metrics

**Primary:**
1. Benchmark aggregate mean (debate vs. baseline) — directly tests the +0.10 lift claim;
   the single number the hypothesis commits to. Rationale: the rubric's 6-dimension mean
   captures multi-faceted protocol quality in a single comparable scalar.
2. Case-pass fraction — catches high-mean scenarios driven by outliers; required by rubric
   (≥ 75% threshold). Rationale: a protocol that passes the aggregate threshold but fails
   on many individual cases is not reliably deployable.
3. agent_convergence_rate stratified by difficulty — the key new diagnostic for open
   question #4; tests whether convergence reliably tracks case difficulty as a signal of
   case hardness. Rationale: if easy cases show higher convergence than hard cases, this
   validates convergence rate as a proxy for case difficulty in live API settings.

**Domain:** self_debate
