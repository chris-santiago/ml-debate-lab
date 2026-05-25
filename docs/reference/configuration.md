# Configuration

## Environment variables

Set in `UV.env` at the repo root (gitignored, loaded automatically by `uv run`):

| Variable | Required for | Description |
|----------|-------------|-------------|
| `OPENROUTER_API_KEY` | External LLM calls | OpenRouter API key for synthetic case generation and experiment scripts |
| `CROSS_VENDOR_API_KEY` | Phase 9 cross-vendor scoring | API key for cross-vendor evaluation |
| `CROSS_VENDOR_BASE_URL` | Phase 9 cross-vendor scoring | Base URL for cross-vendor API |
| `CROSS_VENDOR_MODEL` | Phase 9 cross-vendor scoring | Model identifier for cross-vendor evaluation |

## Settings files

### .claude/settings.json

Project-level settings, committed to git. Shared across all contributors.

### .claude/settings.local.json

Per-machine settings, gitignored. Use for:

- API keys and secrets
- Hook configurations (paths vary per machine)
- Personal permission allow-rules

!!! warning
    Always prefer `settings.local.json` for hooks and secrets. Never write secrets to the git-tracked `settings.json`.

## Hooks

Configure in `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PreCompact": [
      {
        "type": "command",
        "command": "bash plugins/ml-journal/journal-precompact.sh"
      }
    ],
    "SessionStart": [
      {
        "type": "command",
        "command": "bash plugins/ml-journal/journal-session-start.sh"
      }
    ]
  }
}
```

| Hook | Script | Behavior |
|------|--------|----------|
| `PreCompact` | `journal-precompact.sh` | Auto-writes a checkpoint before `/compact` |
| `SessionStart` | `journal-session-start.sh` | Injects latest checkpoint as session context |
| `PostToolUse` | `sync-plugin-cache.sh` | Rsyncs plugin edits to versioned cache |

## Plugin registration

The plugin manifest lives at `plugins/ml-lab/.claude-plugin/plugin.json`. Agents and skills are auto-discovered from their respective directories within the plugin.

## File layout

```
.claude/
├── settings.json           # project-level (committed)
├── settings.local.json     # per-machine (gitignored)
├── hooks/
│   └── sync-plugin-cache.sh
└── scheduled_tasks.lock

plugins/
├── ml-lab/
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── agents/             # auto-discovered
│   └── skills/             # auto-discovered
└── ml-journal/
    ├── .claude-plugin/
    │   └── plugin.json
    ├── agents/
    ├── skills/
    ├── journal-precompact.sh
    └── journal-session-start.sh

UV.env                      # uv runtime env vars (gitignored)
```
