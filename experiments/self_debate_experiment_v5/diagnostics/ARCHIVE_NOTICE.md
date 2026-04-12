# Diagnostics Archive Notice

**These files are pre-ARCH-1 historical artifacts. Nothing here is actionable.**

---

## What these files document

The diagnostic files in this directory (`ISSUE_TRACKER.md`, `CALIBRATION_DIAGNOSTIC.md`, `CASE_FORMAT_DIAGNOSTIC.md`, smoke test results, etc.) record the calibration work done on the **advocacy memo pipeline** — the original v5 case generation approach that was abandoned on 2026-04-08.

That pipeline generated retrospective advocacy memos with planted flaws. It was replaced by the **design + corruption pipeline** (ARCH-1), which generates prospective experiment designs and introduces flaws via a dedicated corruption node. See `plan/PLAN.md` for the current architecture.

## Why the issues are superseded

| Issue group | Disposition |
|-------------|-------------|
| OPEN-1 through OPEN-7 | Wrong pipeline — not applicable to ARCH-1 |
| RESOLVED-1 through RESOLVED-16 | Pre-ARCH-1 fixes — context lives in git history |
| OPEN-8 through OPEN-19 | Mix of resolved by subsequent commits or accepted/managed via post-hoc filtering |
| ARCH-1 | The decision itself — logged in journal (`c13716e`) |

**17 commits landed after the last ISSUE_TRACKER.md update** (`eb5b4cb`), including the full orchestrator rewrite, all case data batches (613 total pool, 110 selected), IDJ removal, and ARCH-1 schema compatibility fixes across all phase files.

## Current issue tracking

Active issues are tracked in `.project-log/journal.jsonl`. Run `/log-status` or `uv run .project-log/journal_query.py --status` for current unresolved issues.

## Do not update these files

These files are frozen. Future issues should be logged to the journal, not here.
