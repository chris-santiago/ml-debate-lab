# Agent Definitions

This directory contains reference copies of the three Claude Code agents that power the ml-debate-lab investigation workflow.

## Agents

| File | Role | Spawned by |
|------|------|------------|
| `ml-lab.md` | Orchestrator — runs the full 9-step investigation | User / calling agent |
| `ml-critic.md` | Adversarial critic — finds flaws the PoC hasn't tested | `ml-lab` |
| `ml-defender.md` | Design defender — argues for the implementation, concedes valid points | `ml-lab` |

`ml-critic` and `ml-defender` are subagents. They are never invoked directly — `ml-lab` dispatches them at Steps 3, 4, and 5 (and again during macro-iteration cycles) via the Claude Code Agent tool.

## Installing

Copy the three files to `~/.claude/agents/`:

```bash
cp agents/ml-lab.md ~/.claude/agents/
cp agents/ml-critic.md ~/.claude/agents/
cp agents/ml-defender.md ~/.claude/agents/
```

Once installed, Claude Code will make `ml-lab` available as a spawnable agent. Invoke it by describing an ML hypothesis — it will ask you to sharpen it into a falsifiable claim before starting the investigation.

## What these copies are

These are sanitized reference copies. Two changes were made from the originals before committing here:

1. **Memory path generalized** — the original references a hardcoded user home directory path for agent memory. The reference copy uses `~/.claude/agent-memory/ml-lab/` so it works for any installer.
2. **`memory: user` scope removed** — the original grants the agent access to the global user memory system. The reference copy removes this, scoping the agent to its own memory directory only. Add `memory: user` back to your local copy if you want cross-project memory access.

## How the agents interact

```
User hypothesis
      |
   [ml-lab]  ←——————————————— orchestrates all 9 steps
      |
      +——— Step 1-2:  builds PoC, reviews intent
      |
      +——— Step 3:   dispatches [ml-critic]  →  CRITIQUE.md
      |
      +——— Step 4:   dispatches [ml-defender] → DEFENSE.md
      |
      +——— Step 5:   alternates dispatches until contested points resolve → DEBATE.md
      |
      +——— Steps 6-7: designs and runs experiment, synthesizes conclusions
      |
      +——— Macro-iteration: if results surprise, re-dispatches ml-critic and ml-defender
      |    in evidence-informed mode (Mode 3) with experimental results in hand
      |
      +——— Steps 8-9: writes self-contained report, re-evaluates under production constraints
```

The key architectural constraint is **context isolation**: `ml-critic` and `ml-defender` each receive only the task materials — never each other's output — before producing their independent assessments. The Defender's independence is what makes genuine `defense_wins` verdicts possible on false-positive critique cases.
