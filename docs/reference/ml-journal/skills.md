# Skills (ml-journal)

All ten journal skills, their invocations, and what they produce.

## Session logging

### /log-entry

Main logging path. Infers entry type from conversation context, extracts fields, presents a draft for confirmation, then writes to `journal.jsonl`.

```shell
/log-entry
```

Supports all entry types (see [Entry Types & Schema](entry-types.md)). Light entries are logged immediately; medium and heavy entries show a draft first.

### /log-commit

Git commit + journal log in one atomic step.

```shell
/log-commit
```

Stages files, synthesizes a commit message, creates the commit, and writes a `git` journal entry with a `diff_summary` — a prose description of *why* the commit exists. Separating commit from log breaks the audit trail.

### /log-init

One-time repo setup.

```shell
/log-init
```

Creates `.project-log/`, installs `journal_log.py` and `journal_query.py`, writes a verification entry.

---

## Session state

### /checkpoint

Save session state for handoff to future sessions or post-compact recovery.

```shell
/checkpoint
```

Captures: `in_progress`, `pending_decisions`, `recently_completed`, `key_context`, `git_state`, `open_threads`.

### /resume

Load and display the most recent checkpoint.

```shell
/resume
```

Injects the checkpoint into conversation context so Claude knows where you left off.

---

## Query and browse

### /log-status

Quick overview of journal health.

```shell
/log-status
```

Shows: last checkpoint timestamp, entry counts by type, unresolved issues, recent commits.

### /log-list

List entries by type with optional time filter.

```shell
/log-list <type> [--since <duration>]
```

**Examples:**

```shell
/log-list decision --since 7d
/log-list issue
/log-list experiment --since 30d
```

---

## Synthesis

### /log-summarize

Prose synthesis of all entries of a given type.

```shell
/log-summarize <type>
```

Produces a narrative summary rather than raw entries.

### /research-note

Generate a session or day-scoped formatted markdown note.

```shell
/research-note
```

**Output:** `RESEARCH_NOTE_<date>.md` (~40–80 lines). Sections: Summary, Key Decisions, Discoveries & Results, Issues, Current State, Next Steps.

### /research-report

Full project or phase retrospective.

```shell
/research-report
```

Dispatches the `report-drafter` subagent to read the full journal, git history, and supplementary docs. Produces `RESEARCH_REPORT.md` with 9 sections.

**Output sections:** Problem Statement, Timeline, What Was Tried/Failed/Worked, Key Decisions, Issues and Resolutions, Open Questions.

---

## Comparison: /research-note vs /research-report

| | /research-note | /research-report |
|---|---|---|
| **Scope** | Session or day | Full project or phase |
| **Output** | `RESEARCH_NOTE_<date>.md` (~40–80 lines) | `RESEARCH_REPORT.md` (comprehensive) |
| **Mechanism** | Runs inline from recent entries | Dispatches `report-drafter` subagent |
| **When to use** | After a work session, before a PR | End of phase or project, onboarding |
