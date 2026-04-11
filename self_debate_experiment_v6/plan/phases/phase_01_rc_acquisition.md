# Phase 1 — RC Data Acquisition

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - CWD: Bash tool CWD is always repo root (`ml-debate-lab/`). Prefix all bash commands with `cd self_debate_experiment_v6 &&`.
> - Subagent context: authenticated Claude Code session. No direct API calls.

## Required Reading
- [rc_pipeline_spec.md](../references/rc_pipeline_spec.md) — full spec for all four RC stages, flaw schema, contamination prevention
- [design_decisions.md §1](../references/design_decisions.md#1-case-source-rc-reports-primary--synthetic-mixed-supplement) — decision gate table for RC yield
- [v5_mitigations.md](../references/v5_mitigations.md) — PM1 contamination pattern (same vector as `task_prompt` leakage here)

## Key Constraints
- `task_prompt` must contain **only isolated methodology** — zero reproducer-language. RC-4 rejects any case matching: `["we found that", "failed to reproduce", "the reported results", "our reproduction", "could not replicate"]`
- RC-2 prompt must explicitly separate "what the paper claims" from "what the reproducer found"

---

## Steps

### 1.1 Build `pipeline/rc_extractor.py`
Implement all four sequential stages. See [rc_pipeline_spec.md](../references/rc_pipeline_spec.md) for the full schema and contamination prevention spec.

**RC-1 (Fetch):**
- OpenReview API: query RC 2020–2023 papers + their reproduction reports
- ReScience C: clone/pull GitHub repo, parse structured YAML frontmatter for paper metadata
- Output: `rc_candidates/reports_fetched.json`

**RC-2 (Flaw extraction, GPT-4o via OpenRouter):**
- For each report: extract structured flaw records per the schema in `rc_pipeline_spec.md`
- Prompt must explicitly separate "what the paper claims" (methodology) from "what the reproducer found" (critique)
- Output: per-report flaw JSON merged into `rc_candidates/flaws_extracted.json`

**RC-3 (`must_not_claim` extraction, GPT-4o via OpenRouter):**
- Separate LLM pass for each report: identify sound design choices a pattern-matching reviewer might wrongly challenge
- Append `must_not_claim` array to each flaw record
- This is the IDP ground truth for RC cases

**RC-4 (Filtering + contamination gate):**
- Apply exclusion criteria from `DATA_ACQUISITION.md` (in v6 root)
- Reject any case where `task_prompt` matches the contamination keywords (see Key Constraints above)
- Classify each passing case as `critique`, `defense`, or `mixed` per the RC case categories in `rc_pipeline_spec.md`
- Output: `rc_candidates/rc_cases_raw.json`

### 1.2 Execute the pipeline
```bash
cd self_debate_experiment_v6 && uv run pipeline/rc_extractor.py
```
Monitor for API errors and rate limits. Log progress to `INVESTIGATION_LOG.jsonl`.

### 1.3 Count usable cases and apply decision gate
```bash
cd self_debate_experiment_v6 && uv run python -c "
import json
cases = json.load(open('rc_candidates/rc_cases_raw.json'))
regular = [c for c in cases if c['ground_truth_type'] in ('critique', 'defense')]
mixed = [c for c in cases if c['ground_truth_type'] == 'mixed']
print(f'Regular: {len(regular)}, Mixed: {len(mixed)}, Total: {len(cases)}')
"
```

Apply decision table from [design_decisions.md §1](../references/design_decisions.md#1-case-source-rc-reports-primary--synthetic-mixed-supplement):

| RC yield | Action |
|---|---|
| regular >= 60 AND mixed >= 20 | Use RC exclusively |
| regular >= 60, mixed < 20 | Supplement mixed with synthetic pipeline (Phase 2) |
| regular < 60 | Supplement regular cases with synthetic (lower proxy threshold) |
| RC total < 30 | Full synthetic fallback: v5 architecture + lower ceiling target + mixed cases |

---

## Verification
- [ ] RC `task_prompt` passes contamination gate — no reproducer-language keywords present (spot-check 10 cases manually)

## Outputs
- `rc_candidates/rc_cases_raw.json`

## Gate
Count usable cases; record decision gate outcome in `INVESTIGATION_LOG.jsonl` before proceeding to Phase 2. If full synthetic fallback is triggered, document in log and adjust Phase 2 accordingly.
