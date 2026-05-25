# Scripts & CLI

Scripts used by ml-lab and ml-journal. All are stdlib-only Python (no external dependencies beyond the standard library).

## journal_log.py

**Location:** `.project-log/journal_log.py` (installed by `/log-init`)

Entry writer. Validates fields against the type schema, constructs the envelope (`id`, `timestamp`, `type`, `project`, `session_id`), and appends a single JSON line to `journal.jsonl`.

**Usage:** Called by ml-journal skills internally. Can also be invoked via `uv run log_entry.py` for ml-lab's investigation log.

!!! warning
    Always use `uv run log_entry.py` or `/log-entry` for journal writes. Manual JSONL appends break schema validation and sequence monotonicity.

---

## journal_query.py

**Location:** `.project-log/journal_query.py` (installed by `/log-init`)

Read-only query interface for the journal.

**Operations:**

```bash
# Journal health overview
python3 .project-log/journal_query.py --status

# List entries by type (with optional time filter)
python3 .project-log/journal_query.py --list <type> [--since <duration>]

# Unresolved issues
python3 .project-log/journal_query.py --unresolved-issues

# Resolved issues with linked resolutions
python3 .project-log/journal_query.py --resolved-issues

# Recent entries (with optional time filter)
python3 .project-log/journal_query.py --recent <N> [--since <duration>]

# Lookup by ID prefix
python3 .project-log/journal_query.py --entry <id_prefix>

# Latest checkpoint
python3 .project-log/journal_query.py --latest-checkpoint
```

**Time durations:** `7d` (days), `4h` (hours), `30m` (minutes).

---

## log_entry.py

**Location:** Experiment directory root (e.g., `experiments/self_debate_experiment_v8/`)

Investigation log writer for ml-lab experiments. Appends sequenced entries to `INVESTIGATION_LOG.jsonl` with step numbers and timestamps.

**Usage:**

```bash
uv run log_entry.py --step <N> --type <type> --description "..."
```

---

## generate_figures.py

**Location:** Repository root

Generates publication-ready figures from experiment results using matplotlib. Uses PEP 723 inline metadata for dependency resolution.

**Usage:**

```bash
uv run generate_figures.py
```

---

## Hook scripts

### journal-precompact.sh

**Location:** `plugins/ml-journal/journal-precompact.sh`

Auto-writes a checkpoint before `/compact` runs. Configure as a `PreCompact` hook.

### journal-session-start.sh

**Location:** `plugins/ml-journal/journal-session-start.sh`

Injects the latest checkpoint as session context at session start. Configure as a `SessionStart` hook.

### sync-plugin-cache.sh

**Location:** `.claude/hooks/sync-plugin-cache.sh`

PostToolUse hook that auto-rsyncs edits in `plugins/ml-lab/` or `plugins/ml-journal/` to the versioned plugin cache. Fires on any file edit within the plugin directories.
