# ml-debate-lab

This project asks a simple question: **when an AI evaluates a piece of work, does it actually catch real problems?**

The context is ML research — model results, statistical claims, deployment decisions. These are exactly the situations where evaluation matters most and where confident-sounding-but-wrong answers are most dangerous.

We built a controlled experiment to find out whether adding structure to AI evaluation — specifically, a debate between two independent agents — produces measurably better results than a single-pass assessment. Not "sounds more thorough." Measurably more correct verdicts, on cases where we already knew the right answer.

---

## The Setup

The system under test is a **self-debate protocol**: one agent plays Critic, one plays Defender, a Judge adjudicates. The key architectural choice is that Critic and Defender receive the same scenario with no shared context — each produces an independent assessment before either sees the other's output.

This isolation is not a technicality. It's what makes the disagreement meaningful. When both agents independently find the same flaw, you have convergent evidence. When they disagree, you have a genuinely contested claim that requires an empirical test to resolve — not a confident guess.

The comparison is a **trivial baseline**: one AI agent, one pass, no debate structure.

To make the comparison meaningful, we needed cases with known correct answers. We built a **benchmark of 20 synthetic ML reasoning scenarios**, each with a planted flaw (or deliberate absence of one), a ground-truth verdict, and specific issues the evaluation had to find. Examples:

- A team claiming a 4-point model improvement, evaluated on 1/10th the data with no confidence intervals
- A loyalty program reporting a 22% sales lift that launched November 1st — right before Black Friday
- A fine-tuned model beating zero-shot, with the team concluding their architecture is superior (the real cause: training regime difference)
- Methodologically *sound* work, presented under adversarial framing — to test whether the protocol would wrongly condemn it

Pass criteria were set before running anything: benchmark mean ≥ 0.65, ≥ 75% of cases pass, lift ≥ +0.10 over baseline.

---

## What We Found

**Debate protocol: 0.970. Single-pass baseline: 0.384. Honest corrected lift: +0.335 to +0.441.**

The protocol cleared every pre-registered benchmark criterion. 19 of 20 cases passed; the pre-specified lift threshold of +0.10 was exceeded by 3–4×. (The raw gap of +0.586 is inflated by two rubric choices that mechanically penalize the baseline — DC hardcoded to 0.0, DRQ capped at 0.5 — both confirmed binding by post-experiment adversarial review. The corrected range is the honest number.)

We ran two baselines to understand where the lift actually comes from:

| Condition | Score | What it isolates |
|-----------|-------|-----------------|
| Single-pass baseline | 0.38 | One agent, one call, no structure — the floor |
| Compute-matched ensemble | 0.75 | Three independent assessors + synthesizer, no roles — what more compute alone buys |
| ml-lab debate protocol | 0.97 | Adversarial role separation on top of compute |

The gap from floor to ensemble (+0.37) is mostly explained by additional compute and multiple perspectives. The gap from ensemble to debate (+0.22, p=0.004, r=0.758) is what adversarial role structure specifically adds. Systematic ablations after the initial run identified what that gap is — and is not — caused by.

**What debate does not uniquely provide:**

- **Empirical test design (ETD).** The debate protocol reliably produces well-specified empirical tests; the unconstrained ensemble almost never does. We originally attributed this to the adversarial forcing function. An ablation falsified that: adding one explicit output instruction to the ensemble synthesizer ("specify the empirical test with pre-specified success and failure criteria") achieves ETD mean 0.962, nearly matching debate's 1.0. ETD is a prompt design effect. It's portable — you can get it from any multi-agent configuration by including the instruction.

- **Exoneration of valid work (exclusively).** A clean ensemble correctly exonerated valid work in 4/5 false-positive trap cases without structural isolation. The isolation architecture is not uniquely necessary for reaching the right verdict.

**What debate does provide:**

- **Cleaner exoneration.** The debate's isolated Defender raised zero concerns on contested exoneration cases. The ensemble raised caveats alongside correct exonerations ("this looks valid, but..."). In practice, confident exoneration and hedged exoneration have different downstream effects. 5/5 clean vs. 4/5 with caveats.

- **Structured argumentation.** The Critic/Defender structure forces point-by-point rebuttal — each claim conceded, rebutted, or flagged as empirically open. A parallel ensemble synthesizing independent views cannot produce this by design.

The clearest illustration is the five *false-positive critique traps* — valid work, correctly designed, presented under adversarial framing. The single-pass baseline scored **0.000 on all five**: it accepted the adversarial premise entirely and condemned sound work. The ensemble got 4/5. The debate protocol got 5/5 with clean outputs.

> **Statistics:** Bootstrap CIs (10,000 resamples) and paired Wilcoxon signed-rank tests. Debate vs. baseline: +0.586 [95% CI: 0.486–0.691], p < 0.0001, r = 1.0 — debate outperforms baseline on every single case. Debate vs. ensemble: +0.216 [95% CI: 0.098–0.352], p = 0.004, r = 0.758. Both effects are statistically significant. See [`stats_results.json`](self_debate_experiment_v2/stats_results.json) and [`SENSITIVITY_ANALYSIS.md`](self_debate_experiment_v2/SENSITIVITY_ANALYSIS.md).

> **External validity:** A 10-case benchmark from published ML evaluation failures (Dacrema 2019, Obermeyer 2019, DeGrave 2021, and others — external ground truth, no designer involvement) confirmed debate IDR = 0.95, meeting the ≥ 0.85 pre-specified threshold. Both structural advantages (exoneration precision, ETD) cannot be externally validated — real-world ML failure cases are critique-type by definition, so no false-positive trap cases exist in published literature. See [`external_benchmark/`](external_benchmark/).

One case failed: a healthcare triage scenario where the Defender correctly identified all critical flaws in its analysis but then labeled the verdict "the work is valid." Correct reasoning, wrong label — a calibration failure in output structure, not a reasoning failure. Fixed by a two-pass Defender prompt (analysis before verdict selection). See [`agents/ml-defender.md`](agents/ml-defender.md).

Full results, per-case scores, and post-experiment analyses are in [`self_debate_experiment_v2/`](self_debate_experiment_v2/).

---

## The Agent Under Test

The deeper object being evaluated here is the **`ml-lab` agent** — a Claude Code subagent that runs a structured 9-step ML hypothesis investigation workflow.

The workflow is designed for rigor over speed. Given a hypothesis, `ml-lab` first sharpens it into a falsifiable claim with agreed metrics, then builds a minimal runnable PoC. From there it branches into two adversarial subagents with distinct mandates:

- **`ml-critic`** — a skeptical ML engineer with an applied mathematics background. It reads the hypothesis and PoC cold and identifies every implicit claim the code makes but hasn't tested, organized by root cause. It is explicitly forbidden from critiquing code style or features the PoC declared out of scope.
- **`ml-defender`** — the original designer, arguing that the implementation is sound. It reads the critique and responds point-by-point: concede, rebut, or mark as empirically open. Fast concession on a real problem is valued over protracted defense.

`ml-lab` then orchestrates a multi-round debate between them, alternating dispatches until each contested point resolves — either one side concedes, or both agree on an exact empirical test with pre-specified success and failure conditions. Only tests on that agreed list go into the experiment. If findings are surprising enough to falsify a debate assumption, the whole cycle reopens: `ml-critic` and `ml-defender` are dispatched again in evidence-informed mode, with experimental results in hand. The investigation closes with a self-contained report and a production re-evaluation that checks whether the experimental recommendation survives operational constraints.

The self-debate protocol was chosen as the domain for a specific reason: it's testable. Unlike most ML research questions, we can construct scenarios with known correct answers and measure whether the agent found the right one. This makes it possible to ask not just "did `ml-lab` follow the process?" but "did following the process actually produce correct verdicts?"

The self-debate experiment is, in that sense, `ml-lab` investigating itself — the protocol is both the tool and the subject.

---

## How the Experiment Was Built

The experiment ran in two phases.

**Phase 1** (`self_debate_experiment/`) established the protocol and tested a first version of the benchmark. This phase was orchestrated entirely by a multi-agent team — a Lead coordinating four specialized agents: CASE_AUTHOR (created benchmark cases), CASE_VERIFIER (validated them), META_EXPERIMENT_RUNNER (executed the workflow and wrote all artifacts), and EVALUATOR (scored outputs against a fixed rubric defined before execution). The orchestration prompt is in [`multi-agent-prompt.md`](multi-agent-prompt.md).

One important detail: in Phase 1, the debate transcripts were generated by Claude agents during the authoring session, then embedded as hardcoded data in the Python scripts. Re-running the script replays static text — it doesn't re-invoke the LLM. This was intentional: the point was to build and score the protocol, not to build a live inference pipeline.

Phase 1 identified two open problems. First, a rubric gap: `issue_discovery_precision` was undefined for cases where the Critique's premise was intentionally false — you can't measure "fraction of valid claims" when all claims are supposed to be invalid. Second, the contaminated protocol (Defense reads Critique before responding) made genuine `defense_wins` verdicts structurally impossible.

**Phase 2** (`self_debate_experiment_v2/`) fixed both. The rubric was extended with a redefined IDP dimension for `defense_wins` cases. The Defense was fully isolated — it receives only the original scenario, never the Critic's output. And critically, Phase 2's transcripts were generated through the full `ml-lab` workflow: each agent role (Critique, Defense, Judge, Scorer, Baseline) was dispatched as an isolated subagent via Claude Code, producing genuinely independent outputs before they were embedded in the script. This directly tested whether the structured investigation process produced correct verdicts when run end-to-end. It did, and then some.

For the full experimental design, scoring rubric, and benchmark case descriptions, see [`self_debate_experiment_v2/README.md`](self_debate_experiment_v2/README.md).

---

## Should I Use ml-lab or Just Run an Ensemble?

**It depends on what output you need.**

A compute-matched ensemble — three independent assessors plus a synthesizer, no role differentiation — scores 0.754 vs. ml-lab's 0.970 on the same benchmark (p=0.004, r=0.758). For detecting whether something is broken, an ensemble gets you most of the way there at lower complexity and latency.

**ml-lab has one confirmed advantage and one replicable one:**

1. **Exoneration precision.** ml-lab correctly exonerated valid work in all 5 false-positive trap cases with clean "no issues" outputs. The ensemble exonerated 4 of 5 correctly but raised caveats alongside in 2 cases — which in practice can still erode confidence in sound work.

2. **Empirical test design** *(replicable with output constraint)*. The original ensemble produced no test designs (ETD≈0) — but an ETD ablation showed that adding an explicit output constraint ("specify the empirical test with success and failure criteria") to the synthesizer achieves ETD mean 0.962. ml-lab produces ETD because its prompt includes this constraint, not because of its adversarial role structure. You can get the same output from an ensemble by adding the same instruction. The debate protocol remains the cleanest way to get test design output reliably, but it is not uniquely necessary.

**Use ml-lab when** the output you need is *what experiment to run next*, or when you're evaluating work that might be valid and you need a dissenting voice that argues for it, not just against it.

**Use an ensemble when** you need a verdict on whether something is broken and don't need a test specification. Simpler, faster, and empirically nearly as good for straightforward fault detection.

**Honest caveats:** The structural advantage evidence is entirely from synthetic benchmarks. The external benchmark (10 real published ML failures) couldn't test either advantage — real-world failure cases are all critique-type by definition, so the exoneration and test-design findings have no external validation yet.

---

## Why This Matters

The standard approach to AI evaluation is single-pass: give a model some work, ask it what it thinks, get an answer. This works when the flaw is explicit. It breaks down in three situations where the stakes are often highest:

- The flaw requires independently questioning the framing (not just processing it)
- The work is actually valid but *sounds* questionable — and the evaluator has no structural incentive to push back
- The correct answer is "run this specific test first" rather than a binary verdict

The single-pass baseline scored 0.000 on all five false-positive trap cases — not because it reasoned incorrectly, but because it had no mechanism to challenge the premise it was given. A simple ensemble (multiple independent views) gets 4/5. Structural isolation of the Defender gets 5/5 clean.

The subtler lesson is about *what structure buys and what it doesn't*. Adversarial role separation is not magic: empirical test design turns out to be a prompt instruction effect, not an architecture effect. More compute and more perspectives solve most of the problem. What role structure specifically adds is a voice that is *required* to argue for the work — and that structural requirement produces cleaner exonerations than a system that merely *might* defend it.

---

## Running the Experiment

Both Phase 1 and Phase 2 scripts score pre-embedded transcripts — no API key or external calls required at runtime. The transcripts were generated during the investigation sessions (via Claude Code agent dispatches) and baked into the scripts. Running the scripts just scores them and writes results JSON.

**Phase 2:**

```bash
cd self_debate_experiment_v2/
python self_debate_poc.py
```

Produces `self_debate_results.json`.

**Phase 1:**

```bash
cd self_debate_experiment/
python self_debate_poc.py       # Experiment 1: contaminated protocol, 11 cases
python self_debate_experiment2.py  # Experiment 2: isolated protocol, 15 cases
```

Standard library only. No dependencies beyond Python 3.8+.

**Running the full multi-agent harness from scratch:**

The bootstrap prompt in [`multi-agent-prompt.md`](multi-agent-prompt.md) will recreate the entire Phase 1 experiment using a team of Claude Code agents. Requires agent teams enabled:

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
claude --teammate-mode in-process
```

Then paste the contents of `multi-agent-prompt.md` as your first message.

---

## An Example Run

To validate that `ml-lab` correctly navigates the full iteration stack — not just the happy path — we ran it on a fraud detection hypothesis:

> *"An LSTM on ordered transaction category sequences outperforms a bag-of-categories baseline because fraud exhibits characteristic temporal patterns."*

The run exercised every major feature of the workflow.

Steps 1–2 produced a clean PoC with AP = 0.96 against 0.05 prevalence — a strong-looking result. The critic identified four issues; the defender conceded three and marked one as empirically open. One debate round resolved the contested point into a three-condition experiment design (ordered LSTM, count-vector LR, equalized-distribution LSTM). Pre-specified verdicts were written before any experiment ran.

The experiment returned mixed results: the randomized-phases test showed the critique was right (AP dropped from 0.96 to 0.68 — phase position was signal, not sequence structure). The ordered vs. bag-of-categories comparison went to the defense. Then Condition C returned AP = 1.00.

The near-perfect metrics suspicion trigger fired immediately. The agent investigated, found that `sort()` was making sequences trivially detectable, and redesigned Condition C with soft-sort (Gaussian noise on ranks). The redesigned condition returned AP = 0.996 — still suspicious.

This is where the spec's escalation logic was put to the test. Rather than accepting the second result or spinning into more micro-iterations, the agent correctly identified that the equalized-distribution test is *fundamentally broken for synthetic data*: any imposed ordering is trivially distinguishable from random sequences because LSTMs detect sequential structure. This isn't a fixable design flaw — it's a hypothesis-level problem.

The macro-iteration Outcome C trigger fired: the experiment wasn't measuring the wrong *thing*, it was testing the wrong *question*. The hypothesis was reformulated:

> *"Fraud accounts exhibit a specific temporal signature (low-value test transactions → rapid category switching → high-value extraction) that is distinguishable from both random ordering and generic monotonic trends."*

The most important result from this run isn't the fraud finding — it's that the spec handled the full escalation without any additional guidance: micro-iteration (fix Condition C), second micro-iteration (still broken), escalation to macro-iteration (hypothesis needs reformulation). The distinction between a fixable experimental flaw and a hypothesis-level problem was load-bearing, and the agent navigated it correctly.

Full trace and spec validation notes are in [`seq_fraud_experiment/TEST2_FINDINGS.md`](seq_fraud_experiment/TEST2_FINDINGS.md).

---

## Artifact Index

| Location | Contents |
|----------|----------|
| [`agents/`](agents/) | Reference copies of ml-lab, ml-critic, and ml-defender agent definitions |
| [`agents/README.md`](agents/README.md) | Installation instructions and agent interaction diagram |
| [`multi-agent-prompt.md`](multi-agent-prompt.md) | Bootstrap prompt for the full multi-agent harness |
| [`self_debate_experiment/`](self_debate_experiment/) | Phase 1: frozen transcripts, contaminated + isolated protocol, 11–15 cases |
| [`self_debate_experiment_v2/`](self_debate_experiment_v2/) | Phase 2: live API, isolated protocol, 20 cases, full results |
| [`self_debate_experiment_v2/README.md`](self_debate_experiment_v2/README.md) | Full experimental design, rubric, benchmark case breakdown |
| [`self_debate_experiment_v2/CONCLUSIONS.md`](self_debate_experiment_v2/CONCLUSIONS.md) | Per-case scores and findings |
| [`self_debate_experiment_v2/REPORT.md`](self_debate_experiment_v2/REPORT.md) | Full technical report |
| [`self_debate_experiment_v2/SENSITIVITY_ANALYSIS.md`](self_debate_experiment_v2/SENSITIVITY_ANALYSIS.md) | Post-experiment adversarial review: rubric design effects on reported lift |
| [`self_debate_experiment_v2/ENSEMBLE_ANALYSIS.md`](self_debate_experiment_v2/ENSEMBLE_ANALYSIS.md) | Compute-matched ensemble baseline results: flawed run, clean re-run, defense_wins isolation test resolution |
| [`self_debate_experiment_v2/ensemble_results.json`](self_debate_experiment_v2/ensemble_results.json) | Per-case ensemble scores — contaminated run (coaching artifacts; see contamination_flag fields) |
| [`self_debate_experiment_v2/clean_ensemble_results.json`](self_debate_experiment_v2/clean_ensemble_results.json) | Per-case ensemble scores — clean two-phase run (no coaching; Phase 1 task-prompt-only) |
| [`self_debate_experiment_v2/ELEVATOR_PITCH.md`](self_debate_experiment_v2/ELEVATOR_PITCH.md) | Non-technical summary of results |
| [`seq_fraud_experiment/HYPOTHESIS.md`](seq_fraud_experiment/HYPOTHESIS.md) | Hypothesis and metrics for the sequence fraud investigation |
| [`seq_fraud_experiment/TEST2_FINDINGS.md`](seq_fraud_experiment/TEST2_FINDINGS.md) | Full trace and spec validation notes for the example run |
| [`external_benchmark/`](external_benchmark/) | 10-case external validity benchmark from published ML evaluation failures |
| [`external_benchmark/cases.json`](external_benchmark/cases.json) | Case metadata, task prompts, verifier rewrites, and must-find labels |
| [`external_benchmark/results.json`](external_benchmark/results.json) | Per-case debate and baseline scores; aggregate IDR=0.95; protocol deviation note |
