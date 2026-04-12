# seq_fraud_experiment

> **Note:** This is a trace artifact from a spec validation run — not a formal ml-lab evaluation experiment. It is not part of the self-debate benchmark series and is not tracked in `experiments/`. See below for provenance.

This directory contains artifacts from a test run of the `ml-lab` agent design spec, executed using Claude Opus to validate that the agent correctly navigates the full iteration stack.

The investigation used a fraud detection hypothesis as the domain (see `HYPOTHESIS.md`). The run was not meant to produce a publishable fraud model — it was meant to exercise the spec under realistic conditions, including cases where micro-iteration is insufficient and the hypothesis itself needs reformulation.

`TEST2_FINDINGS.md` contains the full pipeline trace and a summary of which spec features proved load-bearing.

This investigation was run externally (outside this repo) and the artifacts here are the outputs brought in after the fact. A complete `ml-lab` run would also produce `CRITIQUE.md`, `DEFENSE.md`, `DEBATE.md`, experiment scripts, `CONCLUSIONS.md`, `REPORT.md`, and `REPORT_ADDENDUM.md`.
