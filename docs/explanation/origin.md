# Project Origin & Motivation

## The initial question

ml-lab started from a single question: *can FastText-encoded device IDs and attributes be used as features for ML model consumption?* The initial experiment ran in an interactive Claude Code session. Once the process proved worth keeping, it became a saved monolith prompt — a single Claude command that ran end-to-end.

## The architecture recursion

That monolith was refactored into modular agent dispatches as complexity grew, but the granularity got too fine and the agents lost overall context. The architecture consolidated back toward a mostly-monolithic structure with two agents debating each other, with context carefully bounded and controlled. That eventually became a reusable Claude Code plugin.

The plugin raised a new question: *how do you evaluate the debate protocol itself?* That led to a series of meta-evaluation experiments (v2, v3, v4) — testing whether the critic/defender debate structure actually surfaces real ML methodology flaws. Each round revealed calibration problems: cases were too easy, flaws were too obvious, baselines were too weak.

v5 was the response — generating a harder, more rigorous benchmark case library before running the main experiment. The case generation pipeline itself underwent the same architectural recursion: monolith LLM prompt, then agentic multi-stage prompt, then Python-orchestrated multi-LLM pipeline with concurrent execution, validation gates, and automated smoke testing.

The original FastText idea has now recursed several levels deep into its own evaluation infrastructure.

## Why this matters

ml-lab exists because manual code review of ML experiments misses systematic issues. A human reviewer looking at a proof-of-concept tends to focus on obvious bugs and miss implicit assumptions — the claim that a metric is sufficient, the assumption that a baseline is meaningful, the belief that a sample size is adequate. Adversarial debate forces these assumptions into the open by giving one agent the job of finding them and another the job of defending them.

The alternative — running experiments without structured review — works when the hypothesis is simple and the measurement is well-understood. It fails when the evaluation methodology itself has hidden flaws, which is most of the time in ML research.

## The standalone question

ml-lab is also an answer to a practical question: *what would rigorous ML investigation look like if it were a reusable tool instead of a one-off process?* The 13-step workflow, the pre-registration gates, the convergent debate loop, and the production re-evaluation are all features that exist because they solved real problems encountered during the self-evaluation experiments. Nothing was designed speculatively.
