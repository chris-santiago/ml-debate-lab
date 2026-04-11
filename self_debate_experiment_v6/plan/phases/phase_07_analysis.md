# Phase 7 — Analysis

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - CWD: Bash tool CWD is always repo root (`ml-debate-lab/`). Prefix all bash commands with `cd self_debate_experiment_v6 &&`.
> - Subagent context: authenticated Claude Code session. No direct API calls.

## Required Reading
- [hypotheses.md](../references/hypotheses.md) — all 6 hypothesis tests must be run; statistical test specs (one-sided vs two-sided, CI method)

## Key Constraints
- Bootstrap 95% CI; one-sided for H1a and H1b; two-sided for H2, H3, H6.
- Wilcoxon signed-rank for H3 pairwise comparison (hard cases only).
- IDP reported in two variants: `IDP_raw` (from `all_issues_raised`) and `IDP_adj` (from `all_issues_adjudicated`).

---

## Steps

### 7.1 Run `self_debate_poc.py`
```bash
cd self_debate_experiment_v6 && uv run self_debate_poc.py --scores v6_rescored_idr_idp.json --cases benchmark_cases_verified.json
```

### 7.2 Run all 6 hypothesis tests with bootstrap CIs

**H1a — Regular case lift (one-sided bootstrap):**
```
fc_mean(isolated_debate, regular) - fc_mean(baseline, regular) >= threshold
```
Report: lift, 95% CI, threshold value, PASS/FAIL.

**H1b — Mixed case FVC lift (one-sided bootstrap):**
```
mean FVC(isolated_debate, mixed) > mean FVC(baseline, mixed)
```
Report: lift, 95% CI (CI excludes 0 = PASS), PASS/FAIL.

**H2 — Debate vs compute-matched ensemble (two-sided):**
- Regular: `fc_mean(isolated_debate)` vs `fc_mean(ensemble_union_idr)`
- Mixed: `mean FVC(isolated_debate)` vs `mean FVC(ensemble)`
Report: delta, 95% CI, direction, interpretation.
Interpretation: PASS = CI excludes 0 (isolated > ensemble); FAIL = CI excludes 0 (ensemble > isolated);
INCONCLUSIVE = CI includes 0 (insufficient data to distinguish).

**H3 — Conditional FM vs natural multiround (Wilcoxon signed-rank, hard cases only):**
- `FM hard mean > MR hard mean`
- Hollow round rate for conditional_fm
Report: test statistic, p-value, hollow rate, PASS/FAIL.

**H4 — ETD quality by debate mode (exploratory, directional):**
- Mean ETD per condition (mixed cases, debate conditions only)
- Full credit (1.0) and partial credit (0.5) rates per condition
- Directional prediction: multiround > isolated_debate on ETD

**H5 — Cross-model scorer agreement:**
- Wait for Phase 9 Claude secondary scores; report delta here or in Phase 9
- Flag if IDR delta > 0.50

**H6 — Persona-biasing improves debate quality (two-sided bootstrap):**

PASS criterion (from HYPOTHESIS.md): biased_debate improvement on >= 2 of {IDR, IDP_adj, mixed FVC}
with CI excluding 0. IDP_raw is reported as secondary diagnostic only (expected flat-to-declining).

Per-dimension bootstrap tests (two-sided, 95% CI):
- IDR: `mean IDR(biased_debate, regular)` vs `mean IDR(isolated_debate, regular)`
- IDP_adj: `mean IDP_adj(biased_debate, regular)` vs `mean IDP_adj(isolated_debate, regular)`
- Mixed FVC: `mean FVC(biased_debate, mixed)` vs `mean FVC(isolated_debate, mixed)`

Secondary (exploratory, not in PASS criterion):
- Mixed ETD: `mean ETD(biased_debate, mixed)` vs `mean ETD(isolated_debate, mixed)`
- IDP_raw (diagnostic): `mean IDP_raw(biased_debate)` vs `mean IDP_raw(isolated_debate)` — report direction, not verdict

Report: per-dimension deltas, 95% CIs, count of dimensions with CI excluding 0, PASS/FAIL.

### 7.3 Compute per-case and per-dimension breakdowns
- Per-dimension lift decomposition: IDR, IDP, DRQ, FVC separately
- Per-case breakdown: which cases drive the lift (or lack thereof)?
- `IDP_raw` vs `IDP_adj` — report both; note any divergence

### 7.4 Failure attribution taxonomy
For cases where `isolated_debate` underperforms baseline:
- Categorize failure mode: ceiling effect, protocol failure, case type, domain
- Store attribution per case in `v6_results.json`

### 7.5 Within-case variance analysis
Compute within-case variance across 3 runs per condition. Flag cases with variance > 0.05 as unstable.

---

## Verification
- [ ] All 6 hypotheses (H1a, H1b, H2, H3, H4, H6) have PASS/FAIL with CIs and effect sizes in `v6_results.json`

## Outputs
- `v6_results.json` (full hypothesis test results, per-case breakdowns, variance analysis)

## Gate
All 6 hypotheses tested and recorded with CIs and effect sizes.
