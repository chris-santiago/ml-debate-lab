# Phase 2 — Case Library Assembly

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - CWD: Bash tool CWD is always repo root (`ml-lab/`). Prefix all bash commands with `cd self_debate_experiment_v6 &&`.
> - Subagent context: authenticated Claude Code session. No direct API calls.

## Required Reading
- [schema_b.md](../references/schema_b.md) — normalization target; all pipelines must produce this schema
- [design_decisions.md §2](../references/design_decisions.md#2-case-composition-target-n--120) — target composition (60 critique + 20 defense + 40 mixed)
- [design_decisions.md §3](../references/design_decisions.md#3-pipeline-architecture) — three pipelines converging at `normalize_cases.py`
- [v5_mitigations.md](../references/v5_mitigations.md) — PM3: `proxy_mean` must NOT be used for difficulty gating

## Key Constraints
- `acceptable_resolutions` MUST be a flat string array everywhere — `self_debate_poc.py` line 168 reads it without unwrapping.
- `_pipeline.proxy_mean` is stored for traceability but is **NOT** an input to `select_cases.py`.
- Mixed stratum diversity: minimum 3 distinct domain clusters; no domain > 30% of mixed stratum.

---

## Steps

### 2.1 Generate synthetic mixed cases (if needed per Phase 1 decision gate)
```bash
cd self_debate_experiment_v6 && uv run pipeline/orchestrator.py --mixed 40
```
If RC mixed yield was sufficient (>= 20), skip or generate a smaller supplement.
If RC regular yield < 60, also run synthetic regular cases with a lower proxy threshold.

### 2.2 Normalize all sources via `normalize_cases.py`
Implement/run `pipeline/normalize_cases.py` to produce Schema B for all sources.

**RC case field mapping:**
- `issue_id` → `planted_issues[].issue_id` + `scoring_targets.must_find_issue_ids`
- `corruption_id = null` (RC cases have no planted corruption ID)
- `sound_design_reference = null`
- `is_real_paper_case = true`
- `_pipeline.case_type = "rc"`
- `difficulty = null` at normalization (Phase 3 pilot fills this)

**Synthetic case field mapping:**
- Pass through pipeline fields
- `is_real_paper_case = false`
- `_pipeline.case_type = "regular"` or `"mixed"`
- `difficulty = null` at normalization

**All cases:**
- `acceptable_resolutions` must be a flat string array — validate before output
- `_pipeline.proxy_mean` stored as-is; NOT modified by normalization

```bash
cd self_debate_experiment_v6 && uv run pipeline/normalize_cases.py
```

### 2.3 Validate all normalized cases pass Schema B field check
```bash
cd self_debate_experiment_v6 && uv run python -c "
import json
cases = json.load(open('benchmark_cases_normalized.json'))
required = ['case_id','hypothesis','domain','category','task_prompt',
            'ground_truth','ideal_debate_resolution','scoring_targets',
            'planted_issues','is_real_paper_case','_pipeline']
errors = []
for c in cases:
    for f in required:
        if f not in c:
            errors.append(f'{c[\"case_id\"]}: missing {f}')
    ar = c.get('scoring_targets', {}).get('acceptable_resolutions', None)
    if not isinstance(ar, list):
        errors.append(f'{c[\"case_id\"]}: acceptable_resolutions not a flat list')
    elif any(isinstance(x, dict) for x in ar):
        errors.append(f'{c[\"case_id\"]}: acceptable_resolutions contains nested object')
print(f'{len(errors)} errors' if errors else 'All cases valid')
for e in errors[:20]: print(e)
"
```

### 2.4 Select cases via `select_cases.py`
Implement/run `pipeline/select_cases.py` with stratification and difficulty gating from Phase 3 pilot rubric performance.

- Target: 60 critique + 20 defense + 40 mixed
- Difficulty labels come from Phase 3 pilot — run Phase 3 before final selection
- `_pipeline.proxy_mean` is stored in normalized cases but NOT used as a gate input
- Mixed stratum: enforce >= 3 domain clusters, no domain > 30%

```bash
cd self_debate_experiment_v6 && uv run pipeline/select_cases.py --tier-mixed 40
```

### 2.5 Produce overcomplete candidate pool
Before Phase 3 pilot, produce an overcomplete pool (~150+ cases) to allow discard of cases with baseline FC > 0.80.

**Output:** `benchmark_cases_raw.json` (overcomplete candidate pool)

---

## Verification
- [ ] All normalized cases pass Schema B field validation before Phase 3
- [ ] `_pipeline.proxy_mean` is NOT used as input to `select_cases.py` difficulty gating
- [ ] `acceptable_resolutions` is a flat string array (not nested object) in all benchmark case files

## Outputs
- `benchmark_cases_raw.json` (overcomplete candidate pool, ~150+ cases)

## Gate
All cases pass Schema B validation. Candidate pool is large enough for Phase 3 pilot to discard high-ceiling cases and still reach target N.
