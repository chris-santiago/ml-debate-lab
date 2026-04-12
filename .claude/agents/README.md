# Project-Local Agents

These agents live in `.claude/agents/` and are available only within this repo. They are **not** part of the distributable ml-lab plugin — for those, see `agents/`.

---

## How invocation works

Neither agent runs automatically. Both require explicit dispatch.

- **You → agent:** Ask Claude in plain language ("audit the v3 results", "draft a new post-mortem issue about X"). Claude reads the agent descriptions and dispatches the right one as a subagent.
- **Skill → agent:** The `/new-issue` skill dispatches `issue-drafter` automatically as part of its workflow.
- **Hooks:** Not configured. Nothing triggers these agents on file save or script completion.

---

## Agents

### `experiment-auditor`
Audits experiment result JSON files for metric anomalies and scorer bugs. Seeded with v3 post-mortem failure signatures (Issues 6, 13, 15) so it recognizes known failure patterns on recurrence.

**Invoke by asking:** "audit the v3 results", "check the scoring output for anomalies before I analyze it", "run the experiment auditor on `v3_results_eval.json`"

**Produces:** A structured audit report with per-check PASS / FLAG / ANOMALY verdicts and a recommended actions list.

---

### `issue-drafter`
Drafts a new numbered post-mortem issue in the established `POST_MORTEM.md` format. Reads existing issues to assign the next number and match conventions. Presents a draft for confirmation before anything is written.

**Invoke via:** `/new-issue` (preferred) — the skill handles context gathering and confirmation.

**Or by asking:** "draft a new post-mortem issue about X" — Claude will dispatch this agent directly.

**Does not write anything without confirmation.**

---

### `intent-monitor`
Monitors a working directory for file changes that conflict with a stated source-of-truth document (e.g. `HYPOTHESIS.md`). Each invocation: reads the source-of-truth to extract binding constraints, detects recent changes via git (uncommitted diffs, untracked files, recent commits), and evaluates each change for conflicts.

**Invoke via:** `/intent-watch <dir> <source-of-truth>` (preferred) — the skill handles argument parsing and dispatch.

**For continuous monitoring:** `/loop 2m /intent-watch experiments/self_debate_experiment_v6/ experiments/self_debate_experiment_v6/HYPOTHESIS.md`

**Output:** A single terse clean-pass line if no conflicts, or a structured conflict report with file, change summary, violated constraint, and severity (CRITICAL / HIGH / MEDIUM).
