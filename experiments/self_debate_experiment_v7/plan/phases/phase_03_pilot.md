# Phase 3 — Pilot & Calibration

> **Reminders:** `uv run` only. CWD: repo root.

## Required Reading
- [design_decisions.md §2](../references/design_decisions.md#2-case-composition-target-n--260) — difficulty calibration gate
- [hypotheses.md](../references/hypotheses.md) — TOST bound review after pilot

---

## Goal
Run baseline on a representative sample to confirm:
1. Cases are not too easy (baseline ceiling effect would suppress signal)
2. N per stratum is sufficient after difficulty filtering
3. TOST equivalence bounds (±0.05) are appropriate

---

## Steps

### 3.1 Sample pilot cases
Select ~40 cases per stratum for pilot (40 regular, 20 mixed, 10 defense = 70 total).
Stratified random sample from `benchmark_cases_v7_raw.json`.

### 3.2 Run baseline on pilot sample
```bash
cd experiments/self_debate_experiment_v7 && \
uv run pipeline/phase5_benchmark.py \
  --cases pilot_cases_sanitized.json \
  --output-dir pilot_raw_outputs \
  --conditions baseline \
  --max-concurrent 10 \
  --temperature 1.0
```

### 3.3 Score pilot outputs
```bash
cd experiments/self_debate_experiment_v7 && \
uv run pipeline/v7_scoring.py \
  --input pilot_raw_outputs \
  --cases benchmark_cases_v7_raw.json \
  --output pilot_results.json
```

### 3.4 Apply difficulty gate
```bash
cd experiments/self_debate_experiment_v7 && \
uv run python -c "
import json
results = json.load(open('pilot_results.json'))
by_case = {}
for r in results:
    k = r['case_id']
    by_case.setdefault(k, []).append(r['fc'])
means = {k: sum(v)/len(v) for k, v in by_case.items()}
hard = [k for k, m in means.items() if m < 0.80]
easy = [k for k, m in means.items() if m >= 0.80]
print(f'Hard (pass): {len(hard)}, Easy (discard): {len(easy)}')
print(f'Baseline FC mean (hard cases): {sum(means[k] for k in hard)/len(hard):.4f}' if hard else 'No hard cases')
"
```
**Gate:** baseline FC mean across pilot regular cases must be < 0.80. If ≥ 0.80: increase
case difficulty in case assembly, lower the difficulty target, or consult v6_lessons for
calibration guidance.

### 3.5 Review TOST bounds
After pilot, check whether ±0.05 FC is still appropriate:
- If pilot baseline FC mean ≈ 0.75, then 5pp = 7% relative change — reasonable.
- If pilot baseline FC mean ≈ 0.60, then 5pp = 8% relative change — may consider ±0.04.
- **Do not change TOST bounds after Phase 4 commit.** Decide here.

### 3.6 Final case selection
Filter full `benchmark_cases_v7_raw.json` to cases passing the difficulty gate.
Update `v7_cases_sanitized.json` to reflect the filtered set.

Confirm final N per stratum meets minimums:
- Regular: ≥ 160
- Mixed: ≥ 60 (target 80)
- Defense: ≥ 15 (target 20)

---

## Verification
- [ ] `baseline_fc_mean < 0.80` on pilot regular cases
- [ ] Final regular N ≥ 160, mixed N ≥ 60
- [ ] TOST bound decision recorded before Phase 4

## Outputs
- `pilot_results.json`
- Updated `v7_cases_sanitized.json` (difficulty-filtered)

## Gate
Pilot baseline FC mean < 0.80. Sufficient cases per stratum after filtering. TOST bound confirmed.
