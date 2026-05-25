# Query the Journal

## Using the skill

For a quick overview:

```shell
/log-status
```

To list entries by type:

```shell
/log-list decision --since 7d
```

## Using the CLI directly

The journal query script supports several operations:

```bash
# Journal health overview
python3 .project-log/journal_query.py --status

# List all decisions from the last week
python3 .project-log/journal_query.py --list decision --since 7d

# List unresolved issues
python3 .project-log/journal_query.py --unresolved-issues

# List resolved issues with linked resolutions
python3 .project-log/journal_query.py --resolved-issues

# Show the 10 most recent entries
python3 .project-log/journal_query.py --recent 10

# Show recent entries within a time window
python3 .project-log/journal_query.py --recent 5 --since 7d

# Look up a specific entry by ID prefix
python3 .project-log/journal_query.py --entry abc123

# Show the latest checkpoint
python3 .project-log/journal_query.py --latest-checkpoint
```

## Filtering by type

The `--list` flag accepts any entry type:

```bash
--list decision      # design choices with rationale
--list issue         # bugs and inconsistencies
--list resolution    # verified fixes
--list discovery     # unexpected findings
--list experiment    # verdicts (confirmed/refuted/inconclusive)
--list lesson        # root cause explanations
--list hypothesis    # testable claims
--list summary       # phase completion summaries
--list post_mortem   # failure analyses
```

## Synthesis

For prose summaries rather than raw entries:

```shell
# Prose synthesis of a specific entry type
/log-summarize decision

# Session or day-scoped formatted note
/research-note

# Full project retrospective (dispatches report-drafter agent)
/research-report
```

## You have now...

Learned to query the journal by type, time, and status using both skills and the CLI script.
