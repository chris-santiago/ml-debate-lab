# Phase 3 — Pilot & Calibration

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - CWD: Bash tool CWD is always repo root (`ml-debate-lab/`). Prefix all bash commands with `cd self_debate_experiment_v6 &&`.
> - Subagent context: authenticated Claude Code session. No direct API calls.

## Required Reading
- [design_decisions.md §2](../references/design_decisions.md#2-case-composition-target-n--120) — difficulty calibration approach, hard gate rationale
- [hypotheses.md](../references/hypotheses.md) — H1a threshold formula (set here)

## Key Constraints
- **Hard stop:** if `baseline_fc_mean >= 0.80`, the pilot gate fails — do not proceed to Phase 5. Either expand the candidate pool or trigger the fallback case source strategy.
- Difficulty filtering uses **GPT-4o**, not Claude — PM3 recurrence prevention (same-model calibration proved uncorrelated with rubric performance in v5: Spearman ρ = +0.046).
- Threshold formula: `threshold = max(0.03, min(0.10, (1.0 - baseline_fc_mean) * 0.5))` — set here, committed to `HYPOTHESIS.md` before Phase 5.

---

## Steps

### 3.1 Run baseline on ~30 candidate cases
Sample ~30 cases from `benchmark_cases_raw.json` (stratified: ~15 regular, ~15 mixed).
Run `baseline` condition only.

```bash
cd self_debate_experiment_v6 && uv run self_debate_poc.py --pilot --condition baseline --n 30
```

### 3.2 Run GPT-4o scorer on the same 30 cases
Use GPT-4o (via OpenRouter) for IDR/IDP scoring on the pilot outputs.
This establishes cross-scorer agreement rate early and provides difficulty labels.

### 3.3 Compute pilot metrics
```bash
cd self_debate_experiment_v6 && uv run python -c "
import json, statistics
results = json.load(open('pilot_results.json'))
fc_scores = [r['fc_mean'] for r in results if r['category'] == 'regular']
fvc_scores = [r['fvc'] for r in results if r['category'] == 'mixed']
baseline_fc_mean = statistics.mean(fc_scores)
baseline_fvc_mixed = statistics.mean(fvc_scores) if fvc_scores else None
threshold = max(0.03, min(0.10, (1.0 - baseline_fc_mean) * 0.5))
print(f'baseline_fc_mean: {baseline_fc_mean:.4f}')
print(f'baseline_fvc_mixed: {baseline_fvc_mixed}')
print(f'H1a threshold: {threshold:.4f}')
print(f'Gate: {\"PASS\" if baseline_fc_mean < 0.80 else \"FAIL — hard stop\"}')
"
```

### 3.4 Set H1a threshold
Record the computed threshold in `HYPOTHESIS.md`. This value is locked before Phase 5.

### 3.5 Adjust final N if needed
If within-case variance across the 3 pilot runs > 0.05, increase N for the main benchmark.

### 3.6 Discard high-ceiling cases
Discard any case where baseline FC > 0.80. Update difficulty labels in `benchmark_cases_raw.json`.

### 3.7 Finalize case library
Run `select_cases.py` with difficulty labels from pilot rubric performance to produce the final verified set.

**Output:** `benchmark_cases_verified.json`

---

## Verification
- [ ] Pilot gate: `baseline_fc_mean < 0.80` AND `>= 80 regular + 30 mixed` cases pass the filter

## Outputs
- `pilot_results.json`
- `benchmark_cases_verified.json` (final case library, difficulty-labeled)
- H1a threshold recorded in `HYPOTHESIS.md`

## Gate
`baseline_fc_mean < 0.80` AND `>= 80 regular + 30 mixed` cases survive filtering. Hard stop if gate fails.
