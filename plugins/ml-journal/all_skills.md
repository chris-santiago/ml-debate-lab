# Journal System — All Skills

---

# Skill: journal-init

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

The scripts `journal_log.py` and `journal_query.py` are bundled with this skill. When installed as a plugin, they live alongside this SKILL.md at `scripts/journal_log.py` and `scripts/journal_query.py` relative to the skill directory. Confirm both exist before proceeding.

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

`<skill-dir>` is the directory containing this SKILL.md file (i.e., the `journal-init/` skill directory). When installed as a plugin, this resolves to the plugin cache path for the journal-init skill.

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

---

# Skill: journal-entry

---
name: journal-entry
description: Log a typed entry to the project journal. Use when the user says "log this", "record this", "log this issue / decision / discovery / experiment / hypothesis / resolution / post mortem / summary", or any phrasing indicating something from the conversation should be captured. Infers entry type from context. Handles all entry types except checkpoint (use /checkpoint) and git commits (use /journal-commit).
user-invocable: true
---

## Step 0: Check journal exists

Run `git rev-parse --show-toplevel` to find repo root.

Check that `<repo-root>/.project-log/journal.jsonl` exists. If not, tell the user to run `/journal-init` first and stop.

## Step 1: Infer entry type

Determine type from conversation context using these heuristics:

| Signal | Type |
|---|---|
| "we found that", "turns out", "discovered", "realized" | `discovery` |
| "we learned", "lesson", "takeaway", "going forward we should", "next time" | `lesson` |
| "broken", "failing", "bug", "error", "problem" | `issue` |
| "we decided", "going with", "chose", "agreed on" | `decision` |
| "hypothesis", "we think", "expecting", "if we do X then Y" | `hypothesis` |
| "the experiment showed", "result was", "it worked / didn't work" | `experiment` |
| "fixed", "resolved", "solved" | `resolution` |
| "what went wrong", "post mortem", "retrospective" | `post_mortem` |
| "end of session", "wrapping up", "summary of today" | `summary` |

State the inferred type before proceeding. If genuinely ambiguous, ask the user.

## Step 2: Extract field values

Extract relevant field values from the conversation. Do not invent details not present in the conversation.

**Field extraction by type:**

`issue` — description (what is wrong), severity (low/moderate/high/critical — infer from impact), tags (comma-separated topics), context (what was happening when discovered)

`resolution` — description (what was done), linked_issue_id (if there is a prior issue entry this resolves — ask or search recent entries), approach (how it was fixed)

`decision` — description (what was decided), rationale (why), alternatives (what else was considered)

`lesson` — description (the lesson), context (what situation surfaced it), applies_to (what area/component/workflow it affects), linked_id (any related entry — optional)

`discovery` — description (what was learned), implications (what this means for the work), source (how it was found — experiment, reading, debugging, etc.)

`hypothesis` — description (the hypothesis), expected_result (what you expect to happen), metric (how you'll measure it)

`experiment` — description (what was run), verdict (confirmed/refuted/inconclusive), metric (what was measured), result (what the numbers showed), linked_hypothesis_id (if applicable)

`post_mortem` — description (brief summary), what_failed (the failure), root_cause (why it happened), contributing_factors (what made it worse), lessons (what to do differently), linked_issue_id (if applicable)

`summary` — description (session overview), key_decisions (list of decisions made), open_threads (list of unresolved items)

## Step 3: Confirm or run

**Confirm before logging** (show draft, ask `► Log this? (y/n)`):
- `decision`, `post_mortem`, `experiment`, `summary`

**Log directly** (no confirmation):
- `issue`, `resolution`, `discovery`, `hypothesis`, `lesson`

Note: `git` entries are handled exclusively by `/journal-commit` (which always confirms). Do not pass `git` type through this skill.

Show proposed entry as a readable block before confirming, e.g.:
```
Type:        decision
Description: Use last hidden state pooling instead of mean pooling
Rationale:   Mean pooling destroys temporal ordering; last state captures sequence summary
Alternatives: Mean pooling, attention pooling
```

## Step 4: Construct and run command

Build the `journal_log.py` invocation with appropriate flags for the type and extracted fields. List fields (tags, key_decisions, open_threads) should be passed as comma-separated strings.

```bash
python3 <repo-root>/.project-log/journal_log.py \
  --type <type> \
  --description "..." \
  [--field "value"] ...
```

## Step 5: Surface result

Show the confirmation line from `journal_log.py` output (e.g., `Logged [issue] a3f2b1c0 at 2025-06-01 14:32Z`).

For `resolution` entries: note whether it was linked to a prior issue.
For `experiment` entries: note the verdict prominently.

---

# Skill: checkpoint

---
name: checkpoint
description: Save a session checkpoint to the project journal. Captures current work state for handoff to future sessions or post-compact recovery. Use when the user says /checkpoint, "save state", "checkpoint before compact", "end of session", or "save my progress". Also invoked automatically by the PreCompact hook.
user-invocable: true
---

## Step 0: Check journal exists

Run `git rev-parse --show-toplevel` to find repo root.

Check that `<repo-root>/.project-log/journal.jsonl` exists. If not, tell the user to run `/journal-init` first and stop.

## Step 1: Get git state

```bash
git status --short
git branch --show-current
```

Only include git state in the checkpoint if there is something noteworthy — staged files, uncommitted changes, or a non-main branch. Omit entirely if working tree is clean and on main.

## Step 2: Synthesize checkpoint fields

From the conversation history, draft concise values for:

**in_progress** — what is actively being worked on right now (specific tasks, files, decisions in flight). 1–3 sentences.

**pending_decisions** — open questions or blockers the next session must resolve. 1–3 sentences. Omit if none.

**recently_completed** — what finished this session, so the next session knows what "done" means. 1–3 sentences. Omit if nothing meaningful completed.

**key_context** — hard-won facts expensive to re-derive: confirmed root causes, design decisions already settled, gotchas discovered, corrections already made. 1–3 sentences. Omit if nothing critical.

**git_state** — e.g. "branch: feature/pooling-experiment | modified: src/model.py, config/train.yaml". Omit if clean on main.

**open_threads** — structured list of unresolved items that must not be forgotten. Each item is a short phrase. Pull from pending_decisions and any other loose ends in the conversation.

Keep each field tight. Omit fields that genuinely don't apply — do not pad with filler.

## Step 3: Show draft and confirm

Show the proposed checkpoint as a readable block:

```
In progress:          [...]
Pending decisions:    [...]
Recently completed:   [...]
Key context:          [...]
Git state:            [...]
Open threads:
  • [...]
  • [...]
```

Ask: `► Write checkpoint? (y/n)`

Do not write anything until confirmed.

## Step 4: Write checkpoint

```bash
python3 <repo-root>/.project-log/journal_log.py \
  --type checkpoint \
  --in-progress "..." \
  --pending-decisions "..." \
  --recently-completed "..." \
  --key-context "..." \
  --git-state "..." \
  --open-threads "thread1, thread2, ..."
```

Omit flags for fields that are empty.

## Step 5: Confirm

Show the confirmation line from output.

If the user is about to compact: "Checkpoint written. Run `/compact` when ready."
Otherwise: "Checkpoint written. Use `/resume` to reload this state in a future session."

---

# Skill: resume

---
name: resume
description: Load the most recent session checkpoint from the project journal and surface it to the console. Use when the user says /resume, "what were we working on", "load last checkpoint", "restore state", "catch me up", or at the start of a session when continuing prior work. Also triggered automatically by the SessionStart hook when a journal exists.
user-invocable: true
---

## Step 1: Check journal exists

Run `git rev-parse --show-toplevel` to find repo root.

If `.project-log/journal.jsonl` does not exist, say: "No journal found in this repo. Run `/journal-init` to set one up." Stop.

## Step 2: Load latest checkpoint

```bash
python3 <repo-root>/.project-log/journal_query.py --latest-checkpoint
```

## Step 3: Surface and prompt

Display the full formatted output from the query script.

Then ask: "How would you like to proceed?"

Do not summarize or reinterpret the checkpoint — surface it as-is so nothing is lost in translation.

## If no checkpoint exists

If the query returns "No checkpoint found", say:

"No checkpoint found in this journal. There are entries — use `/journal-status` to see what's been logged."

Or if the journal is empty:

"Journal exists but has no entries yet."

---

# Skill: journal-status

---
name: journal-status
description: Show a quick summary of the current project journal state — last checkpoint, entry counts for this session, unresolved issues, and recent git entries. Use when the user says /journal-status, "journal status", "where are we", "what's open", "what have we logged", or "show me the journal state".
user-invocable: true
---

## Step 1: Check journal exists

Run `git rev-parse --show-toplevel` to find repo root.

If `.project-log/journal.jsonl` does not exist, say: "No journal found in this repo. Run `/journal-init` to set one up." Stop.

## Step 2: Run status query

```bash
python3 <repo-root>/.project-log/journal_query.py --status
```

## Step 3: Surface output

Display the formatted output as-is. No further action needed.

---

# Skill: journal-list

---
name: journal-list
description: List recent journal entries of a specific type. Use when the user says "show recent issues", "list decisions", "show my hypotheses", "what experiments have we logged", "list post mortems", or any phrasing asking to see entries of a particular type. Optionally filtered by time window.
user-invocable: true
---

## Step 1: Check journal exists

Run `git rev-parse --show-toplevel` to find repo root.

If `.project-log/journal.jsonl` does not exist, say: "No journal found in this repo. Run `/journal-init` to set one up." Stop.

## Step 2: Determine type and time window

From the user's request, identify:

**Type** — one of: `issue`, `resolution`, `decision`, `discovery`, `hypothesis`, `experiment`, `post_mortem`, `summary`, `checkpoint`, `git`

If the type is ambiguous or not specified, ask: "Which entry type? (issue / resolution / decision / discovery / hypothesis / experiment / post_mortem / summary / checkpoint / git)"

**Since** (optional) — if the user says "recent", "this week", "last 24 hours", "today", etc., convert to the appropriate `--since` value:
- "today" → `1d`
- "this week" / "recent" → `7d`
- "last 24 hours" → `24h`
- Specific number: use as stated, e.g. "last 3 days" → `3d`
- No time qualifier → omit `--since` (show all)

## Step 3: Run query

```bash
python3 <repo-root>/.project-log/journal_query.py --list <type> [--since <Nd|Nh>]
```

## Step 4: Surface output

Display formatted output as-is.

If the list is long (>10 entries), offer: "Want me to summarize these? Use `/journal-summarize` for a prose synthesis."

---

# Skill: journal-summarize

---
name: journal-summarize
description: Synthesize a prose summary of all journal entries of a requested type. Use when the user says "summarize decisions", "what decisions have we made", "give me a summary of open issues", "synthesize our experiments", "what have we discovered", or any phrasing asking for a narrative synthesis of logged entries.
user-invocable: true
---

## Step 1: Check journal exists

Run `git rev-parse --show-toplevel` to find repo root.

If `.project-log/journal.jsonl` does not exist, say: "No journal found in this repo. Run `/journal-init` to set one up." Stop.

## Step 2: Determine type

From user phrasing, identify the entry type to summarize. Valid types: `issue`, `resolution`, `decision`, `discovery`, `hypothesis`, `experiment`, `post_mortem`, `summary`, `checkpoint`, `git`.

If ambiguous, ask.

## Step 3: Load entries

```bash
python3 <repo-root>/.project-log/journal_query.py --list <type>
```

If no entries of that type: say so and stop.

## Step 4: Synthesize prose summary

From the structured entry output, write a coherent prose summary appropriate to the type:

**issue** — group by severity, highlight any unresolved, note patterns
**resolution** — trace what was fixed, note approaches used
**decision** — summarize the decisions made and their rationale; note any that seem in tension
**discovery** — synthesize what has been learned; highlight implications
**hypothesis** — list active hypotheses and their status (tested/untested)
**experiment** — summarize what was tried, what verdicts came back, what patterns emerge
**post_mortem** — synthesize root causes and lessons; note recurring themes
**checkpoint** — trace how the work state has evolved session over session

Keep the summary grounded in the actual logged entries — do not speculate or add information not present in the journal.

## Step 5: Offer to log as summary entry

After the synthesis, offer: "Want me to log this as a `summary` entry in the journal? (y/n)"

If yes, run:
```bash
python3 <repo-root>/.project-log/journal_log.py \
  --type summary \
  --description "<one-sentence summary>" \
  --key-decisions "<comma-separated key points if decision type>" \
  --open-threads "<comma-separated open items if any>"
```

---

# Skill: journal-commit

---
name: journal-commit
description: Stage, commit, and log to the project journal in one step. Use when the user says /journal-commit, /jcommit, "commit and log", "commit this", or indicates work is ready to commit. Synthesizes the commit message from conversation context and logs a git entry to the journal simultaneously.
user-invocable: true
---

## Step 0: Check journal exists

Run `git rev-parse --show-toplevel` to find repo root.

If `.project-log/journal.jsonl` does not exist, say: "No journal found. Run `/journal-init` first." Stop.

## Step 1: Understand what's changed

```bash
git status --short
git diff --stat HEAD
git branch --show-current
```

Show the output to the user so they can see what will be committed.

If nothing is staged or modified, say so and stop.

## Step 2: Determine what to stage

If specific files were mentioned by the user, stage only those:
```bash
git add <files>
```

Otherwise, stage all changes:
```bash
git add -A
```

## Step 3: Synthesize commit message

From the conversation context and the diff stat, write a commit message:
- First line: imperative mood, ≤72 characters, describes *what* changed
- Optional second paragraph (after blank line): *why*, if non-obvious

Do not use generic messages like "update files" or "wip".

## Step 4: Synthesize journal fields

From the same context, prepare `git` entry fields:
- `message` — same as commit message first line
- `branch` — from `git branch --show-current`
- `files_changed` — comma-separated list of changed files
- `diff_summary` — 1–2 sentence prose description of what the commit does

## Step 5: Show draft and confirm

```
Commit message:   <message>
Files:            <file list>
Journal entry:    git | <diff_summary>
```

Ask: `► Commit and log? (y/n)`

Do not run git or write to journal until confirmed.

## Step 6: Commit

```bash
git commit -m "<message>"
```

Capture the commit hash from the output (format: `[branch abc1234]`).

If commit fails, show the error and stop. Do not log to journal.

## Step 7: Log to journal

```bash
python3 <repo-root>/.project-log/journal_log.py \
  --type git \
  --commit-hash <hash> \
  --message "<message>" \
  --branch <branch> \
  --files-changed "<file1, file2, ...>" \
  --diff-summary "<summary>"
```

## Step 8: Confirm

Show both confirmations:
- `[branch abc1234] <message>`
- `Logged [git] <id> at <timestamp>`

---

# Skill: research-note

---
name: research-note
description: Synthesize a full research narrative from the project journal, git history, and supplementary markdown files. Produces RESEARCH_NARRATIVE.md at the repo root. Use when the user says /research-note, "synthesize a research narrative", "write up what we've done", "create a project summary", or "document our research history".
user-invocable: true
---

## Step 1: Find repo root and check journal

```bash
git rev-parse --show-toplevel
```

If `.project-log/journal.jsonl` does not exist, say: "No journal found. Run `/journal-init` first." Stop.

## Step 2: Gather all inputs

### Journal entries
Read the full `.project-log/journal.jsonl`. Group by type for synthesis.

### Git history
```bash
git log --oneline --all
```

### Supplementary markdown files
Glob for files matching these patterns at repo root and up to 2 levels deep:
```bash
find <repo-root> -maxdepth 3 -name "*.md" | grep -iE "(ISSUE|lesson|POST_MORTEM|TODO|NOTES|CHANGELOG|DECISIONS)"
```
Do not hardcode paths. Read any matches and incorporate if relevant.

### Existing RESEARCH_NARRATIVE.md
Check if one already exists — note it to the user but do not let it constrain the new synthesis.

## Step 3: Synthesize narrative

Write `RESEARCH_NARRATIVE.md` with the following sections. Include only sections that have content — omit empty sections rather than writing placeholder text.

```markdown
# Research Narrative — <project name>

*Generated <date> from <N> journal entries and <N> commits.*

## Problem Statement
[What problem is this project trying to solve, derived from early decisions/discoveries]

## Timeline
[Chronological sequence of significant events — milestones, major decisions, key experiments — drawn from journal timestamps and git log]

## What Was Tried
[All approaches, experiments, and hypotheses — confirmed, refuted, and inconclusive]

## What Failed
[Issues and post-mortems — what broke, root causes, contributing factors]

## What Worked
[Confirmed experiments, successful resolutions, key discoveries with positive implications]

## Key Decisions
[All decision-type entries with rationale; note any decisions that were later revisited]

## Issues and Resolutions
[Linked pairs where available; unresolved issues clearly marked]

## Current State
[From latest checkpoint — in_progress, pending_decisions, open_threads]

## Open Questions
[Aggregated open_threads across all checkpoints, deduplicated, with oldest first]
```

Be specific — reference actual entry content, not vague summaries. Quote descriptions from the journal where they are clear and concise.

## Step 4: Show draft and confirm

Show the full draft to the user.

Ask: `► Write to RESEARCH_NARRATIVE.md? This will overwrite any existing file. (y/n)`

(Git has history — overwriting is safe.)

## Step 5: Write file

Write to `<repo-root>/RESEARCH_NARRATIVE.md`.

Confirm: "RESEARCH_NARRATIVE.md written — <N> lines."

