---
name: log-summarize
description: Synthesize a prose summary of all journal entries of a requested type. Use when the user says "summarize decisions", "what decisions have we made", "give me a summary of open issues", "synthesize our experiments", "what have we discovered", or any phrasing asking for a narrative synthesis of logged entries.
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
