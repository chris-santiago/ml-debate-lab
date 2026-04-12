# Phase 7 — Analysis

> **Reminders:** `uv run` only. CWD: repo root. All tests must match pre-registered specs in `HYPOTHESIS.md`.

## Required Reading
- [hypotheses.md](../references/hypotheses.md) — all test specifications
- [design_decisions.md §4](../references/design_decisions.md#4-statistical-tests) — bootstrap protocol, TOST

---

## Steps

### 7.1 Run full analysis
```bash
cd experiments/self_debate_experiment_v7 && \
uv run pipeline/v7_scoring.py \
  --mode analyze \
  --raw v7_raw_outputs \
  --scores v7_rescored_idr_idp.json \
  --cases benchmark_cases_v7_raw.json \
  --output v7_results.json \
  --hypothesis-file HYPOTHESIS.md \
  --bootstrap-n 10000 \
  --seed 42
```

### 7.2 Required test outputs in `v7_results.json`

For each test, `v7_results.json` must contain: `point_estimate`, `ci_lower`, `ci_upper`,
`verdict` (PASS/FAIL/INCONCLUSIVE), and `n` (sample size).

| Test | Subset | Metric | Type |
|---|---|---|---|
| P1 | Regular (n≥160) | IDR: ensemble_3x vs multiround_2r | One-sided bootstrap |
| P2 | Mixed (n≥60) | FVC_mixed: multiround_2r vs ensemble_3x | One-sided bootstrap |
| H1a | Regular (n≥160) | FC: isolated_debate vs baseline (TOST) | TOST |
| H2_regular | Regular (n≥160) | FC: ensemble_3x vs isolated_debate | Two-sided bootstrap |
| H2_mixed | Mixed (n≥60) | FVC_mixed: ensemble_3x vs isolated_debate | Two-sided bootstrap |
| H3 | Mixed (n≥60) | FVC_mixed: multiround_2r vs isolated_debate | One-sided bootstrap |

**Framework verdict**: CONFIRMED if P1 AND P2 both pass; otherwise PARTIAL or NOT CONFIRMED.

### 7.3 Per-condition summary table

Compute mean ± std for each condition × metric:

| Condition | IDR | IDP_raw | DRQ | FVC | FC | FVC_mixed |
|---|---|---|---|---|---|---|
| baseline | | | | | | |
| isolated_debate | | | | | | |
| ensemble_3x | | | | | | |
| multiround_2r | | | | | | |

Fill from `v7_results.json`. Record n per condition (some cases may fail schema validation
and be excluded — document exclusions).

### 7.4 Defense case exoneration rate

Per v6 lesson L7, defense cases require separate reporting:

```bash
cd experiments/self_debate_experiment_v7 && \
uv run python -c "
import json, glob, collections
cases = {c['case_id']: c for c in json.load(open('benchmark_cases_v7_raw.json'))}
defense_ids = {cid for cid, c in cases.items() if c['category'] == 'defense'}
files = [f for f in glob.glob('v7_raw_outputs/*.json')
         if json.load(open(f))['case_id'] in defense_ids]
by_cond = collections.defaultdict(list)
for f in files:
    d = json.load(open(f))
    correct = d['verdict'] == 'defense_wins'
    by_cond[d['condition']].append(correct)
for cond, results in by_cond.items():
    rate = sum(results)/len(results)
    print(f'{cond}: {rate:.3f} ({sum(results)}/{len(results)} exonerations)')
"
```

### 7.5 RC vs synthetic subgroup (secondary)
Split results by `is_real_paper_case`. Report IDR delta (ensemble vs baseline) separately
for RC papers and synthetic cases. Expected: larger ensemble advantage on RC cases (harder,
ecologically valid) — per v6 finding (+0.172 vs +0.059).

---

## Verification
- [ ] All 6 tests present in `v7_results.json` with point estimate + CI + verdict
- [ ] Framework verdict (P1+P2) reported
- [ ] TOST verdict uses committed bounds (not modified post-hoc)
- [ ] Defense exoneration rate computed and recorded
- [ ] RC vs synthetic subgroup reported

## Outputs
- `v7_results.json` (all tests)
- `v7_results_eval.json` (per-condition per-metric means)
- `CONCLUSIONS.md` (hypothesis verdicts + framework verdict)

## Gate
`v7_results.json` complete. All 6 tests present. `CONCLUSIONS.md` written.
