# Skills (ml-lab)

Skills are user-invocable slash commands. They run in the main session and dispatch subagents as needed.

## /ml-lab

Start a structured ML hypothesis investigation.

**Invocation:**

```shell
/ml-lab
```

Or describe an ML hypothesis in natural language — Claude Code routes to ml-lab automatically via its description.

**Parameters asked at start:**

| Parameter | Options | Default |
|-----------|---------|---------|
| `review_mode` | `debate`, `ensemble` | `debate` |
| `report_mode` | `full_report`, `conclusions_only` | `full_report` |

**Workflow:** 13-step structured investigation. See [Workflow Diagram](workflow.md) for the complete flowchart.

**Artifacts produced:**

| Step | Artifact |
|------|----------|
| Pre | `HYPOTHESIS.md` |
| 1 | Proof-of-concept script |
| 2 | `README.md` |
| 3 | `CRITIQUE.md` / `ENSEMBLE_REVIEW.md` |
| 4 | `DEFENSE.md` (debate only) |
| 7 | `CONCLUSIONS.md` |
| 8 | `REPORT.md` (full_report mode) |
| 9 | `REPORT_ADDENDUM.md` |
| 10 | `PEER_REVIEW_R1.md` |
| 11 | `TECHNICAL_REPORT.md` |
| 13 | Rewritten `README.md` |
| All | `INVESTIGATION_LOG.jsonl` |

---

## /intent-watch

Monitor an experiment directory for pre-registration drift.

**Invocation:**

```shell
# One-time check
/intent-watch <experiment_dir> <source_of_truth>

# Continuous monitoring (every 2 minutes)
/loop 2m /intent-watch <experiment_dir> HYPOTHESIS.md
```

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `experiment_dir` | Path to the experiment directory |
| `source_of_truth` | Path to the binding document (typically `HYPOTHESIS.md`) |

**Output:** Clean-pass line or structured conflict report with severity levels (HIGH, CRITICAL block the experiment).

**Used at:**

- **Gate 1 (mandatory)** — one clean pass required before Step 6
- **Step 6 (active loop)** — continuous monitoring during experiment scripting

---

## /deep-dive

Generate a comprehensive technical reference document.

**Invocation:**

```shell
/deep-dive [experiment_path]
```

**Parameters:**

| Parameter | Description | Default |
|-----------|-------------|---------|
| `experiment_path` | Path to the experiment directory | Current directory |

**Output:** `DEEP_DIVE.md` — covers data construction, model architecture, scoring mechanics, statistical methods, per-test detail, quality gates, aggregation, and key design decisions with sources cited.

**Works with or without a project journal.** Degrades gracefully when artifacts are missing.
