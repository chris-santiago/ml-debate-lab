# H5 Precision Parity Audit

> Audit date: 2026-04-13. Triggered by H5 reversal: v6 delta=+0.017 vs v7 delta=-0.103.

---

## Summary

The H5 FAIL verdict is genuine. The precision gap survives recomputation from raw
issue data (-0.094) and is driven by a real composition effect: minority-flagged
issues contain more spurious noise than consensus issues. The v6 parity result was
likely a combination of a more generous classifier model, a smaller sample, and
insufficient statistical power.

One pipeline bug was identified (LLM-computed precisions stored verbatim without
validation), but it does not change the verdict.

---

## 1. Pipeline Bug: LLM-Computed Precisions

### Problem

`v7_scoring.py:score_file()` stores `tier_precisions` and `tier_counts` directly from
the gpt-5.4-mini JSON response with no post-processing or validation. The LLM is asked
to classify issues AND compute the arithmetic in the same response.

20.7% of tier-level precision values (267/1291) disagree with values recomputed from
the `unique_issues` array in the same response. The 1of3 tier is most affected (193
mismatches). Additionally, 53 issues (1.4%) have `raised_by: []` (phantom issues with
no assessor attribution).

### Example

File `eval_scenario_006__ensemble_3x__run0.json`:

| Field | LLM reported | Recomputed from unique_issues |
|-------|-------------|-------------------------------|
| 1of3 count | 3 | 4 |
| 1of3 precision | 0.667 | 0.750 |

### Comparison to v6

v6's `v6_minority_precision.py` had the LLM classify issues, then Python code computed
counts and precisions from the classifications. The arithmetic was never delegated to
the LLM. This is the correct approach.

### Impact

Even with recomputed precisions from unique_issues:

| Tier | Recomputed Precision | N issues |
|------|---------------------|----------|
| 1of3 | 0.804 | 2,256 |
| 2of3 | 0.860 | 722 |
| 3of3 | 0.897 | 925 |

Recomputed delta: -0.094 (from raw unique_issues arrays). After the fix was applied
to `run_analysis()` (paired bootstrap on Python-recomputed per-file precisions), the
final H5 result is:

```
Point estimate: -0.080
95% CI: [-0.108, -0.052]
n: 432
Verdict: FAIL (CI entirely outside +/-0.03)
```

The LLM arithmetic inflated the gap by ~0.023. **Verdict unchanged.**

### Remediation (applied)

`run_analysis()` now recomputes tier precisions from `unique_issues` in Python.
For each issue: skips phantoms with empty `raised_by`, derives tier from
`len(raised_by)`, classifies as valid if `classification in (planted_match,
valid_novel)`, computes `precision = valid / total` per tier. This matches
v6's approach in `v6_minority_precision.py`.

---

## 2. Pipeline Differences: v6 vs v7

| Aspect | v6 | v7 |
|--------|-----|-----|
| Classifier model | GPT-4o (via OpenRouter) | gpt-5.4-mini (via OpenRouter) |
| Precision computation | Python code | LLM (in JSON response) |
| Deduplication | GPT-4o clusters issues | gpt-5.4-mini deduplicates |
| Cases scored | 60 critique x 3 runs = 180 | 160 regular x 3 runs = 480 |
| Critic model | Older Claude (agent dispatch) | Claude Sonnet 4.6 (API) |
| Critic prompt | Dynamic from orchestrator | Fixed `critic.md` with anti-hedging |
| Classification script | `v6_minority_precision.py` | `v7_scoring.py:build_h5_classification_prompt()` |
| H5 status in experiment | Separate Phase 9 analysis | Pre-registered hypothesis |

### Critic prompt differences

v7 adds explicit guidance not present in v6:

- Anti-hedging calibration: "If you find yourself reaching for 'this might not
  generalize' without a specific mechanism for failure, that is not a critique"
- Silent misconfiguration category
- Prerequisite assumptions category

v6 used dynamic agent-based dispatch with multi-round debate transcripts. v7 uses
single-pass structured critique with fixed system prompts.

---

## 3. Root Cause: Composition Effect

The precision gap is driven by what each tier contains:

| Tier | % planted_match | % valid_novel | % spurious | % false_claim |
|------|----------------|---------------|-----------|--------------|
| 1of3 | 14.5% | 65.9% | 15.0% | 4.6% |
| 3of3 | 55.1% | 34.6% | ~5% | ~5% |

### Interpretation

- **3/3 issues** are majority planted_match (55%). These are the obvious planted flaws
  that all 3 independent assessors find. High precision because planted issues are by
  definition valid.
- **1/3 issues** are majority valid_novel (66%). These are genuine findings that only
  one assessor catches. But they also carry more spurious noise (15% vs ~5%).

This is structurally expected: issues found by only one assessor include more edge
cases, borderline observations, and subjective concerns. The minority tier is where
assessor-specific creativity lives, and creativity comes with noise.

### Issue volume

- Total unique issues across 480 scored files: 3,903
- Mean per case: 8.13 (range: 3-20)
- 56.4% of issues are at the 1/3 tier (unique to one assessor)
- 23.7% are at 3/3 (unanimous)
- 18.5% are at 2/3

The majority of issues are assessor-unique. With temperature=1.0 and independent
sampling, each critic explores different parts of the issue space.

---

## 4. Why v6 Showed Parity

v6 result: 1/3 precision=0.946, 3/3 precision=0.929, delta=+0.017, CI [-0.028, +0.068].

Three factors likely contributed:

### 4a. Different classifier model

GPT-4o (v6) may classify borderline minority issues more generously as `valid_novel`
rather than `spurious`. A more capable model might recognize subtle validity in
single-assessor observations that gpt-5.4-mini marks as spurious.

This is the most likely primary driver. The classification boundary between
`valid_novel` and `spurious` is subjective — a stricter classifier mechanically
produces lower minority precision.

### 4b. Smaller, potentially different case set

v6 used 60 hand-selected critique cases. v7 uses 160 regular cases from a broader
automated pipeline. Case difficulty and composition differences affect how many
borderline issues get raised.

### 4c. Statistical power

v6 CI: [-0.028, +0.068] at n=180. Wide enough to include both parity and a meaningful
gap. v7 at n=433 has much tighter CIs: [-0.133, -0.073]. v6 may have been
underpowered to detect a real gap.

---

## 5. Verdict

**H5 FAIL is genuine.** Minority-flagged issues carry a real precision penalty.

The recommendation from HYPOTHESIS.md applies: "Union pooling should be qualified:
use union pooling with tier weighting."

### What this means for the framework

The P1 result (ensemble IDR >> multiround IDR, +0.169) remains robust — union pooling
finds more planted flaws. But H5's failure means the recall advantage comes at a
precision cost. The practical recommendation is tier-weighted union pooling: weight
1/3-flagged issues lower than 3/3-flagged issues, rather than treating all
union-pooled issues as equal.

### Open question for future work

Re-run the H5 classification with GPT-4o as the classifier (matching v6) to isolate
whether the precision gap is model-dependent or structural. If GPT-4o also shows a gap
at v7 scale, the v6 parity was a power artifact. If GPT-4o restores parity, the gap
is classifier-dependent and the choice of classification model is a confound.
