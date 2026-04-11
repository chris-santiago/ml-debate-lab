# Phase 8 — Sensitivity & Robustness

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - CWD: Bash tool CWD is always repo root (`ml-debate-lab/`). Prefix all bash commands with `cd self_debate_experiment_v6 &&`.
> - Subagent context: authenticated Claude Code session. No direct API calls.

## Required Reading
- [hypotheses.md](../references/hypotheses.md) — H3 hollow rate prediction, H4 ETD directional prediction
- [v5_mitigations.md](../references/v5_mitigations.md) — PM3 difficulty validation (Spearman ρ must be meaningful this time)

## Key Constraints
- **FM hollow-round rate analysis must use v6 data only.** v5 schema repair pass set `point_resolution_rate = 0` as default for repaired files — per-round hollow detection is unreliable in v5 data. Do not import v5 FM data for this check.
- If IDP is flat across all debate conditions including `biased_debate`, audit whether `all_issues_raised` is extracted from Critic raw output vs adjudicator synthesis — flat IDP across all conditions + biased_debate confirms an orchestrator-level extraction bug, not a persona/protocol limitation.

---

## Steps

### 8.1 Method A vs Method B aggregation divergence
Compute fc_mean using both aggregation methods. Flag if divergence > 0.05.

### 8.2 Threshold sensitivity analysis
Re-run H1a test at ±0.02 around the pre-registered threshold. Report whether the PASS/FAIL outcome changes at the boundary.

### 8.3 Per-dimension lift decomposition
Decompose fc_mean lift into IDR, IDP, DRQ, FVC components. Which dimension(s) drive the signal (or null result)?

### 8.4 Difficulty stratification validation
Validate that Phase 3 difficulty labels predict rubric performance (Spearman ρ). This is PM3 verification — if ρ ≈ 0 again, the calibration failed.
```bash
cd self_debate_experiment_v6 && uv run python -c "
from scipy.stats import spearmanr
import json
results = json.load(open('v6_results.json'))
labels = [r['difficulty_label'] for r in results if r.get('difficulty_label')]
scores = [r['baseline_fc'] for r in results if r.get('difficulty_label')]
rho, p = spearmanr(labels, scores)
print(f'Spearman rho: {rho:.4f}, p={p:.4f}')
"
```

### 8.5 IDP diagnostic
If IDP is flat across all conditions (including biased_debate):
- Audit `all_issues_raised` extraction path in `pipeline/orchestrator.py`
- Check: is it pulling from Critic raw output or from adjudicator synthesis?
- Compare `IDP_raw` vs `IDP_adj` — if they're the same, `all_issues_adjudicated` isn't being extracted correctly
- Flat IDP across all debate + biased_debate = orchestrator-level extraction bug, not persona/protocol limitation
- Document finding in `SENSITIVITY_ANALYSIS.md`

### 8.6 Conditional FM hollow-round rate
Using v6 native data:
```bash
cd self_debate_experiment_v6 && uv run python -c "
import json, glob
files = glob.glob('v6_raw_outputs/*_conditional_fm_*.json')
hollow = [f for f in files
          if json.load(open(f)).get('gate_fired') and
             json.load(open(f)).get('round2_new_points_resolved', 1) == 0]
print(f'Hollow rate: {len(hollow)}/{len(files)} = {len(hollow)/len(files):.1%}')
print(f'Gate: {\"PASS\" if len(hollow)/len(files) < 0.10 else \"FAIL — hollow rate >= 10%\"}')
"
```

---

## Verification
- [ ] Conditional FM hollow rate < 10% (v6 data only)

## Outputs
- `SENSITIVITY_ANALYSIS.md`
- `CONCLUSIONS.md`

## Gate
All sensitivity checks complete. `CONCLUSIONS.md` written with verdict on Q1, Q2, Q3, Q4 questions.
