# Installation & Prerequisites

This tutorial walks you through installing ml-lab and ml-journal, configuring environment variables, and verifying everything works. By the end, you'll have both plugins ready to use.

## Prerequisites

- **Claude Code** — installed and authenticated ([installation guide](https://docs.anthropic.com/en/docs/claude-code/overview))
- **uv** — Python package manager ([install uv](https://docs.astral.sh/uv/getting-started/installation/))
- **Git** — required for ml-journal's audit trail

!!! note "No pyproject.toml needed"
    ml-lab scripts use PEP 723 inline metadata headers. `uv run` resolves dependencies per-script — no virtual environment or project-level dependency file required.

## Install ml-lab

```shell
/plugin marketplace add chris-santiago/ml-lab
/plugin install ml-lab@ml-lab
```

This installs the `/ml-lab` skill and all seven subagent files. Verify by typing `/ml-lab` — Claude Code should recognize it as a skill.

## Install ml-journal

```shell
/plugin install ml-journal@ml-lab
```

Then initialize the journal in your repo:

```shell
/log-init
```

This creates `.project-log/` at the repo root with `journal.jsonl`, `journal_log.py`, and `journal_query.py`.

## Set up environment variables

ml-lab's experiment scripts call external LLMs through OpenRouter. Create a `UV.env` file at the repo root (gitignored by default):

```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

`uv run` loads `UV.env` automatically — no manual `export` needed.

For cross-vendor scoring (used in some experiment configurations), you'll also need:

```
CROSS_VENDOR_API_KEY=your-key
CROSS_VENDOR_BASE_URL=https://api.example.com/v1
CROSS_VENDOR_MODEL=model-name
```

## Verify the installation

Run each of these to confirm everything is wired up:

```shell
# ml-lab skill is available
/ml-lab

# ml-journal skills are available
/log-status

# uv can resolve PEP 723 scripts
uv run --help

# Journal scripts work
python3 .project-log/journal_query.py --status
```

You should see `/ml-lab` prompt for a hypothesis, `/log-status` show journal state, and the query script report entry counts.

## Optional: configure hooks

ml-journal can auto-checkpoint before context compaction and auto-resume at session start. Add to `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PreCompact": [
      { "type": "command", "command": "bash plugins/ml-journal/journal-precompact.sh" }
    ],
    "SessionStart": [
      { "type": "command", "command": "bash plugins/ml-journal/journal-session-start.sh" }
    ]
  }
}
```

!!! warning
    Use `settings.local.json`, not `settings.json` — the local file is gitignored and won't leak API keys or per-machine hook paths.

## You have now...

- Installed ml-lab and ml-journal as Claude Code plugins
- Configured API keys for external LLM calls
- Initialized the journal audit trail
- Optionally set up auto-checkpoint/resume hooks

Next: [Worked Example: LLM Preambles](worked-example.md) — walk through a complete real-world investigation.
