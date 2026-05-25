# Checkpoint & Resume Sessions

## Save session state

Before ending a session, compacting context, or switching tasks:

```shell
/checkpoint
```

This writes a `checkpoint` entry to the journal containing:

- `in_progress` — what you're currently working on
- `pending_decisions` — unresolved choices
- `recently_completed` — what you just finished
- `key_context` — important state that would be lost
- `git_state` — current branch and uncommitted changes
- `open_threads` — things to pick up later

## Resume in a new session

At the start of a new session:

```shell
/resume
```

This loads the most recent checkpoint into context. Claude picks up where you left off without you re-explaining the state.

## Automate with hooks

To checkpoint and resume automatically, add hooks to `.claude/settings.local.json`:

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

With hooks configured:

- **PreCompact** auto-writes a checkpoint before `/compact` runs
- **SessionStart** auto-injects the latest checkpoint at session start

## Tips

- Checkpoint early and often — the cost is one journal entry
- The first session in a new repo has no checkpoint to resume; `/resume` will report nothing
- Hooks are per-machine and must be configured on each developer's machine

## You have now...

Set up session persistence across context boundaries using `/checkpoint`, `/resume`, and optional automation hooks.
