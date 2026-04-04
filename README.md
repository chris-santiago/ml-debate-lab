# Claude `lab.md` Multi-Agent Evaluation Harness

This project is a turnkey multi-agent evaluation harness for testing how effective Claude is when executing the `lab.md` research workflow on a self-debate experiment.

The core idea is simple:

- We treat the `lab.md` command/process as the **method under test**.
- We treat Claude running that method as the **agent under test**.
- We use **synthetic benchmark cases with known ground truth** so we can measure whether the method actually works, rather than relying on subjective impressions.
- We use a **multi-agent team** so benchmark creation, verification, execution, and scoring are separated.

The result is a controlled way to answer questions like:

- Does Claude actually follow the `lab.md` process faithfully?
- Does the critique/defense/debate loop surface real weaknesses?
- Does it propose diagnostic experiments instead of vague objections?
- Does it beat a trivial baseline like single-pass answer plus self-critique?
- Does it reach the correct final verdict on cases where we already know the answer?

---

## What this evaluates

This harness evaluates the effectiveness of Claude using the `lab.md` workflow, specialized to a self-debate setting.

In other words, it is **not just testing “Claude debate” in general**. It is specifically testing whether Claude can successfully execute the structured investigation process defined by `lab.md`, including:

1. Building a minimal proof of concept
2. Clarifying intent
3. Writing an adversarial critique
4. Writing a calibrated defense
5. Debating contested points to resolution
6. Designing and running empirical tests
7. Synthesizing conclusions
8. Writing a self-contained report
9. Re-evaluating under production constraints

The self-debate protocol is the domain-specific target, but the larger object being evaluated is:

> **Claude using the `lab.md` command/process as a research agent**

---

## Why a multi-agent setup is used

A single agent can easily leak information across roles:

- It can invent its own test cases
- Then run the workflow on those cases
- Then grade itself afterward

That makes it hard to know whether the method is genuinely strong or merely persuasive.

This harness separates responsibilities across agents so the evaluation is more trustworthy.

### Team roles

#### Lead
Coordinates the whole process, enforces sequencing, approves plans, and produces the final synthesis.

#### Case Author
Creates synthetic benchmark cases with:
- known ground truth
- planted flaws
- expected critique targets
- expected defense behavior
- expected empirical resolution tests

#### Case Verifier
Checks that the cases are:
- coherent
- non-ambiguous
- diagnostic
- aligned with the scoring rubric

#### Meta-Experiment Runner
Executes the full `lab.md`-style workflow on the verified cases and produces the main artifacts.

#### Evaluator
Scores the outputs against a fixed rubric defined **before execution**.

---

## What is being benchmarked

The system under test is the structured reasoning loop:

**critique -> defense -> debate -> experiment -> conclusion**

The benchmark asks whether that loop can:

- identify planted weaknesses
- avoid false-positive critiques
- calibrate defenses appropriately
- propose empirical tests that actually distinguish critique from defense
- reach the correct final verdict
- outperform trivial baselines

---

## Why synthetic cases are used first

This first version uses **synthetic ML reasoning tasks only**.

That choice is intentional.

Synthetic tasks let us create cases where we know:

- what the hidden flaw is
- what a good critique should notice
- what a good defense should concede or contest
- what experiment would settle the disagreement
- what the correct final verdict should be

That gives us controlled evaluation.

Real-world tasks can come later, but they are a worse starting point because the “correct answer” is often disputed, underspecified, or entangled with domain knowledge.

---

## Benchmark case categories

The benchmark contains 16 synthetic cases across five categories (15 verified KEEP, 1 excluded):

1. **Broken baseline**
2. **Metric mismatch**
3. **Hidden confounding**
4. **Scope / intent misunderstanding**
5. **Defense wins** *(false-positive critique traps — added after Experiment 1 to test the protocol on valid work under false attack)*

These categories are chosen because they stress core commitments inside `lab.md`, especially:

- preserving the trivial baseline
- distinguishing intent from implementation error
- requiring testable critiques
- demanding diagnostic empirical tests
- resisting vague or persuasive-but-empty reasoning

---

## How this relates to `lab.md`

The `lab.md` file remains central.

It is the **inner protocol**.

This multi-agent harness is the **outer execution and evaluation wrapper**.

### In practice

- The **Meta-Experiment Runner** uses the `lab.md` process as its operating procedure.
- The **Case Author** creates synthetic tasks designed to stress whether that procedure works.
- The **Case Verifier** filters out weak or ambiguous test cases.
- The **Evaluator** measures how well the `lab.md` procedure performed on those cases.
- The **Lead** coordinates the entire run and writes the final synthesis.

So the harness does **not replace** `lab.md`.

It evaluates Claude’s ability to use `lab.md` effectively.

---

## The embedded master workflow

The experiment uses a specialized “master prompt” built on top of `lab.md`.

That master workflow adapts the original process to a self-debate setting where:

- two instances of Claude argue opposite sides
- a judging component evaluates the debate
- the workflow measures whether self-debate helps uncover real issues
- the evaluation is grounded in synthetic tasks with known answers

The master workflow preserves the same artifact-driven structure as `lab.md`, while making the experiment target more specific.

---

## Artifacts produced

A successful run should produce the following files.

### Benchmark control artifacts
- `benchmark_cases.json`
- `benchmark_verification.json`
- `evaluation_rubric.json`
- `evaluation_results.json`

### Main workflow artifacts
- `self_debate_poc.py`
- `README.md`
- `CRITIQUE.md`
- `DEFENSE.md`
- `DEBATE.md`
- `self_debate_experiment2.py`
- `CONCLUSIONS.md`
- `REPORT.md`
- `REPORT_ADDENDUM.md`

### Final coordination artifact
- `FINAL_SYNTHESIS.md`

---

## Expected evaluation questions

This harness is designed to answer questions such as:

- Did Claude correctly identify the planted flaws?
- Did Claude hallucinate flaws that were not actually present?
- Did the defense calibrate correctly, rather than blindly resisting criticism?
- Did the debate produce sharper claims and better empirical tests?
- Did the final experiment actually resolve the disputed point?
- Did the overall workflow beat a trivial baseline?
- Did the final report and addendum reflect the evidence accurately?

---

## Scoring dimensions

The evaluator scores each case using a fixed rubric defined before execution.

Typical scoring dimensions include:

- **Issue discovery recall**  
  Fraction of planted issues that were correctly identified.

- **Issue discovery precision**  
  Fraction of claimed issues that were actually valid.

- **Defense calibration**  
  Whether the defense conceded real flaws and resisted weak critiques appropriately.

- **Debate resolution quality**  
  Whether the debate ended in the correct type of resolution.

- **Empirical test diagnosticity**  
  Whether the proposed experiment would genuinely distinguish critique from defense.

- **Final verdict correctness**  
  Whether the final conclusion matched ground truth.

---

## Why the trivial baseline matters

A major rule inherited from `lab.md` is that the trivial baseline is non-negotiable.

If a simple method can explain the result, the richer debate workflow does not deserve credit.

That is why every serious run must compare the full critique/defense/debate protocol against at least:

- single-pass answer
- single-pass answer plus self-critique

This protects against overestimating the value of the more elaborate workflow.

---

## Execution flow

The intended execution order is:

1. Create the agent team
2. Generate synthetic benchmark cases
3. Verify the cases
4. Freeze the evaluation rubric
5. Draft the meta-experiment execution plan
6. Approve or reject the plan
7. Run the full `lab.md`-style workflow on verified cases
8. Score the outputs
9. Write a final synthesis of strengths, weaknesses, and recommendations

This sequence is important because it prevents:
- grading after the fact with a changing rubric
- using ambiguous or low-quality test cases
- mixing generation and evaluation in the same role

---

## What success looks like

This harness is successful if it can produce a credible answer to:

> When Claude runs the `lab.md` process, does it actually discover real problems, design informative experiments, and reach correct conclusions on controlled benchmark cases?

A good result is not “Claude sounded smart.”

A good result is:

- the planted flaws were found,
- the defenses were calibrated,
- the experiments were diagnostic,
- the verdicts were correct,
- and the method beat the trivial baseline.

---

## Limitations

This first version is deliberately narrow.

### Current limitations
- Synthetic tasks only
- No real production hypotheses
- No external deployment system
- No claim that benchmark performance automatically transfers to real research work

### Why that is acceptable
The first objective is internal validity:
- can the workflow work at all under controlled conditions?

Only after that should the process be extended to real tasks.

---

## Recommended next phases

After the synthetic-only run is stable, the natural next steps are:

1. Add cases that specifically stress key `lab.md` commitments:
   - trivial baseline handling
   - surprise handling
   - correction handling
   - premature reporting
2. Expand the synthetic benchmark with hard `defense_wins` cases requiring domain knowledge or computation to rebut
3. Fix the `issue_discovery_precision` rubric gap for `defense_wins` cases (IDP → N/A when `correct_position = "defense"`)
4. Introduce a small number of real ML hypotheses
5. Compare results across synthetic and real tasks
6. Extend to true multi-model deployment to test genuine inter-model disagreement resolution

---

## File Placement Guide

### `lab.md` — the core research workflow

**Location:** Project root (`/your-project/lab.md`)

`lab.md` is the step-by-step investigation protocol (Steps 1–9). It is invoked via the `/lab` skill in Claude Code. Keep it in the root of any project where you want to run the full research workflow.

To use it globally (accessible from any project), copy it to `~/.claude/lab.md`.

**Invocation:**
```
/lab
```
Claude Code will prompt you for a hypothesis and primary metrics before beginning.

---

## Summary

This project is a benchmark harness for evaluating whether Claude can effectively execute the `lab.md` research process in a self-debate setting.

The important distinction is:

- `lab.md` defines the research method
- the master prompt specializes that method to self-debate
- the multi-agent harness evaluates whether Claude can actually carry out that method well

That separation lets us test the process rigorously instead of relying on style, confidence, or anecdotal success.

**Key finding from these experiments:** The isolated two-agent architecture (Critique and Defense with separate context windows) is the correct design when *evaluating a debate protocol as a benchmark*. For normal `/lab` runs on an ML hypothesis, the single-agent sequential workflow in `lab.md` is the correct design — the Defense reads the Critique and responds to it directly.

--------------------------

# Bootstrap Prompt to Run Experiment

Below is a single bootstrap prompt you can paste into a **lead** Claude Code session to create and run the full team-based experiment around your self-debate master workflow. Claude Code agent teams are experimental, require `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, and are designed around one lead session coordinating independent teammates with separate contexts.

## Launch

Start Claude Code with agent teams enabled, then paste the block below as your first message in the lead session. If you want the simplest setup, use `in-process` teammate mode first, because the lead can coordinate teammates directly without extra terminal management.

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
claude --teammate-mode in-process
```


## Bootstrap prompt

See `multi-agent-prompt.md`.
