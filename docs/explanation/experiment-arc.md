# The Experiment Arc (v1 to v8)

Eight experiment versions trace the evolution of ml-lab's evaluation methodology. Each version was a response to problems discovered in the previous one.

## v1: Proof of concept

The first experiment tested whether the debate protocol could identify real flaws in a simple ML hypothesis. It worked — the critic found issues, the defender responded, and the process produced actionable findings. But the evaluation was entirely qualitative: a human read the output and judged whether it was useful.

## v2: Structured measurement

v2 added quantitative metrics. Instead of "did the debate seem useful?", it measured detection rates (did the critic find the planted flaws?) and verdict accuracy (did the final verdict match the ground truth?). This revealed the first calibration problem: the cases were too easy. Critics found everything because the flaws were too obvious.

## v3: Harder cases, new problems

v3 introduced more subtle methodology flaws — issues that require domain expertise to spot, not just code reading. Detection rates dropped, which was the goal. But a post-mortem (documented in `POST_MORTEM.md`) revealed scoring bugs and inconsistent rubric application across cases. The measurement infrastructure was failing before the thing being measured could be evaluated.

## v4: Pre-registration

v4 was the first pre-registered experiment. The hypothesis, metrics, and pass criteria were locked before any code ran. This caught a new class of problem: specification drift. Changes made during implementation silently violated the pre-registration constraints. The `/intent-watch` skill was born from this experience.

## v5: Benchmark case generation

v5 stepped back from running the main experiment to build a harder, more rigorous benchmark. The case generation pipeline went through its own architectural recursion — from a single LLM prompt to a multi-stage Python pipeline with concurrent execution and validation gates. The result was a library of cases with metadata: `must_find` (planted flaws the critic must detect), `acceptable_resolutions`, `correct_position`, and `ideal_resolution`.

## v6: Ensemble mode

v6 tested an alternative to adversarial debate: dispatching three independent critics with no visibility into each other's outputs, then pooling findings by support tier. This "ensemble mode" traded depth for breadth — higher recall at the cost of more false positives. It also introduced cross-vendor scoring to test whether results held across different LLM providers.

## v7: Refined evaluation

v7 tightened the evaluation methodology. A sensitivity analysis tested whether results were stable across different scoring schemes, weighting functions, and case orderings. A cohesion audit checked cross-document consistency. The result was a more robust set of findings with confidence intervals rather than point estimates.

## v8: Defense-case calibration (active)

v8 is the current active experiment. It addresses a gap discovered in v7: the evaluation was well-calibrated for detection (does the critic find flaws?) and ambiguity judgment (does the system handle genuinely ambiguous cases?), but defense-case performance — cases where the PoC is actually correct and the critic should find nothing material — had not been rigorously evaluated. v8 focuses on this calibration.

## The meta-lesson

The arc from v1 to v8 demonstrates a general pattern: evaluating a methodology requires methodology that itself needs evaluation. Each version solved the previous version's measurement problems while introducing new ones at a higher level of subtlety. The progression was not planned — it was driven by post-mortems that honestly assessed what went wrong.

This is why ml-lab enforces pre-registration, convergent debate, and macro-iteration loops. These features exist because their absence caused specific, documented failures in the self-evaluation experiments.
