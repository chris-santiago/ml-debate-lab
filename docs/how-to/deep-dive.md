# Generate a Deep Dive

`/deep-dive` produces a comprehensive technical reference document (`DEEP_DIVE.md`) after an investigation or experiment phase is complete.

## When to use

Run `/deep-dive` after:

- A full `/ml-lab` investigation completes
- A major experiment phase finishes
- You want a standalone technical reference covering implementation details

## Generate the document

```shell
/deep-dive [experiment_path]
```

If `experiment_path` is omitted, `/deep-dive` looks for experiment artifacts in the current directory.

## What it covers

The generated `DEEP_DIVE.md` includes:

- **Data construction** — how inputs were generated or collected
- **Model architecture** — design choices and parameters
- **Scoring mechanics** — rubrics, judge configurations, aggregation
- **Statistical methods** — tests used, multiple comparison corrections
- **Per-test detail** — individual test breakdowns with results
- **Quality gates** — validation checks and their outcomes
- **Aggregation** — how individual results compose into conclusions
- **Key design decisions** — sourced from journal entries and plan documents

## How it finds information

`/deep-dive` surveys:

1. Experiment scripts (`.py` files)
2. Results schemas (JSON/JSONL output files)
3. Journal decisions (from `.project-log/journal.jsonl`)
4. Existing documentation (REPORT.md, CONCLUSIONS.md, plan files)

It works with or without a project journal and degrades gracefully when artifacts are missing.

## You have now...

Generated a comprehensive technical reference document that covers implementation details end-to-end, with sources cited from scripts, results, and journal entries.
