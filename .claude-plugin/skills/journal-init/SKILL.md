---
name: journal-init
description: Initialize the project journal system in the current git repo. Creates .project-log/ directory, journal.jsonl, and installs journal_log.py and journal_query.py. Use when the user says /journal-init, "set up journal", "initialize journal", or "set up project logging". Only needs to be run once per repo.
user-invocable: true
---

## Step 1: Find repo root

Run `git rev-parse --show-toplevel`.

If this fails (not a git repo), tell the user and stop.

## Step 2: Check for existing setup

Check if `<repo-root>/.project-log/journal.jsonl` already exists.

If it does, tell the user the journal is already initialized and show the entry count:
```bash
wc -l <repo-root>/.project-log/journal.jsonl
```
Ask if they want to continue anyway. Stop if they say no.

## Step 3: Locate script source

The scripts `journal_log.py` and `journal_query.py` are bundled with this skill at `scripts/journal_log.py` and `scripts/journal_query.py` relative to this SKILL.md file. Confirm both exist before proceeding.

If they are missing, tell the user to reinstall the plugin and stop.

## Step 4: Confirm before creating anything

Tell the user what will be created:
- `.project-log/` directory
- `.project-log/journal.jsonl` (empty)
- `.project-log/journal_log.py` (copied from skill)
- `.project-log/journal_query.py` (copied from skill)

Ask: `► Create these files in <repo-root>? (y/n)`

Do not create anything until confirmed.

## Step 5: Create files

```bash
mkdir -p <repo-root>/.project-log
touch <repo-root>/.project-log/journal.jsonl
cp <skill-dir>/scripts/journal_log.py <repo-root>/.project-log/
cp <skill-dir>/scripts/journal_query.py <repo-root>/.project-log/
chmod +x <repo-root>/.project-log/journal_log.py
chmod +x <repo-root>/.project-log/journal_query.py
```

`<skill-dir>` is the directory containing this SKILL.md file.

## Step 6: Verify

```bash
python3 <repo-root>/.project-log/journal_log.py --type discovery --description "Journal initialized" --source "journal-init skill"
python3 <repo-root>/.project-log/journal_query.py --status
```

If either fails, show the error and stop.

## Step 7: Confirm

Tell the user:
- Journal initialized at `.project-log/journal.jsonl`
- One initialization entry logged
- Available skills: `/journal-entry`, `/checkpoint`, `/resume`, `/journal-status`, `/journal-list`, `/journal-summarize`, `/journal-commit`, `/research-note`
