# Agent Definitions

This directory contains reference copies of the Claude Code agents that power the ml-debate-lab investigation workflow.

## Agents

| File | Role | Spawned by |
|------|------|------------|
| `ml-lab.md` | Orchestrator — runs the full 12-step investigation | User / calling agent |
| `ml-critic.md` | Adversarial critic — finds flaws the PoC hasn't tested | `ml-lab` (Steps 3, 5) |
| `ml-defender.md` | Design defender — argues for the implementation, concedes valid points | `ml-lab` (Steps 4, 5) |
| `research-reviewer.md` | Deep peer reviewer — Opus-class structured review of REPORT.md | `ml-lab` (Step 10, Round 1) |
| `research-reviewer-lite.md` | Verification reviewer — Haiku-class follow-up review | `ml-lab` (Step 10, Rounds 2–3) |
| `readme-rewriter.md` | Outside-reader README rewriter — diagnoses and rewrites for external audiences | `ml-lab` (Step 13) |

All agents except `ml-lab` are subagents. They are never invoked directly — `ml-lab` dispatches them at the appropriate steps via the Claude Code Agent tool.

For installation instructions, invocation guide, workflow diagram, and agent interaction overview, see the [root README](../README.md#install).

## What these copies are

These are sanitized reference copies. Two changes were made from the originals before committing here:

1. **Memory path generalized** — the original references a hardcoded user home directory path for agent memory. The reference copy uses `~/.claude/agent-memory/ml-lab/` so it works for any installer.
2. **`memory: user` scope removed** — the original grants the agent access to the global user memory system. The reference copy removes this, scoping the agent to its own memory directory only. Add `memory: user` back to your local copy if you want cross-project memory access.
