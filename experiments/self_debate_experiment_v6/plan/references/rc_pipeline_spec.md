# RC Extraction Pipeline Specification

Four sequential stages implemented in `pipeline/rc_extractor.py`.

| Stage | What | Model | Output |
|---|---|---|---|
| RC-1: Fetch | OpenReview API (RC 2020–2023) + ReScience C (GitHub) | N/A | `rc_candidates/reports_fetched.json` |
| RC-2: Flaw extraction | Report text → structured flaw records | GPT-4o | Per-report flaw JSON |
| RC-3: `must_not_claim` extraction | Separate LLM pass for sound design choices | GPT-4o | Appended to flaw records |
| RC-4: Filtering + contamination gate | Exclusion criteria + `task_prompt` keyword gate | N/A | `rc_candidates/rc_cases_raw.json` |

---

## RC Flaw Record Schema (produced by RC-2)

```json
{
  "issue_id": "rc_<report_id>_<flaw_idx>",
  "flaw_type": "methodology | evaluation | statistical | reproducibility | other",
  "description": "...",
  "severity": "minor | major | critical",
  "source": "reproducer_documented",
  "ground_truth_type": "critique | defense | mixed",
  "rc_report_id": "...",
  "original_paper_title": "..."
}
```

---

## `task_prompt` Contamination Prevention (critical — PM1 recurrence risk)

RC reports contain both the original methodology AND the reproducer's critique. If `task_prompt`
includes critique text, debate agents receive the answer key through the data channel — the same
pattern as PM1 but through the input rather than the context window.

- **Primary approach:** extract methodology from the original paper's abstract + methods section
- **Fallback:** use RC report's "original claims" summary (describes methodology without critique)
- **RC-2 prompt instruction:** explicitly separates "what the paper claims" from "what the reproducer found"
- **RC-4 contamination gate:** reject any case where `task_prompt` matches any of:
  `["we found that", "failed to reproduce", "the reported results", "our reproduction", "could not replicate"]`

---

## RC Case Categories

- `critique`: RC report documents a methodology flaw → maps to regular critique cases
- `defense`: RC report confirms paper with no flaws → maps to defense_wins cases
- `mixed`: RC report identifies a contestable choice ("mostly sound but X is overstated") → maps to mixed cases
