# Scoring

## The Problem with v7 Scoring

v7 used FVC (Flawed Verdict Coefficient): `defense_wins`=1.0, `empirical_test_agreed`=0.5, `critique_wins`=0.0 on defense cases. This has no penalty for being confidently wrong. Hedging is the safe strategy — a system that always outputs `empirical_test_agreed` scores 0.5 everywhere. The scoring function rewards cowardice.

## Penalty-Aware Scoring Function

**Per-case score by stratum and verdict:**

| Case type | `defense_wins` | `empirical_test_agreed` | `critique_wins` |
|---|---|---|---|
| Defense (sound methodology) | +1.0 | −0.25 | −0.5 |
| Regular (flawed methodology) | −0.5 | −0.25 | +1.0 |
| Mixed (ambiguous) | 0.0 | 0.0 | 0.0 |

**Rationale per cell:**
- `empirical_test_agreed` on clear cases: always an experiment recommendation. On stratum-clear cases (defense + regular), that recommendation is unnecessary — penalized at −0.25.
- `critique_wins` on a sound case: false alarm — penalized at −0.5, not just scored 0.
- `defense_wins` on a flawed case: missed a real flaw — penalized at −0.5.
- Mixed cases score 0 for all verdicts. They are diagnostic only — measuring calibration (ARR), not accuracy. This is intentional, not a bug. The system cannot be gamed on mixed cases by guessing.

**Score range:**
- Worst possible (all false alarms on defense, all misses on regular): −0.5
- Pure coward (always hedge): −0.25
- Perfect: +1.0

Hedging now costs −0.25, making it worse than random guessing on clear cases. The system has a reason to be confident.

## Finding-Level Scoring (Brier-Like)

The verdict-level function scores the *outcome* of the debate — did the system reach the right verdict? It cannot distinguish between a critic that raised a score-9 finding on sound methodology vs. a score-2 concern. Both produce `critique_wins`; both score −0.5. The wrong-but-confident case goes unpunished beyond the verdict penalty.

The finding-level layer fixes this by treating severity as a probability estimate and applying a proper scoring rule.

### Interpretation

`severity/10` = P(genuine flaw exists at this magnitude). Ground truth is known from the case label.

**Brier-like finding score:**

```
finding_score(severity, stratum) =

  regular case:   +[1 − (1 − severity/10)²]
  defense case:   −(severity/10)²
  mixed case:     not scored at finding level (verdict-neutral stratum)
```

**Score table (illustrative):**

| Severity | Regular case (reward) | Defense case (penalty) |
|---|---|---|
| 10 | +1.00 | −1.00 |
| 9 | +0.99 | −0.81 |
| 7 | +0.91 | −0.49 |
| 5 | +0.75 | −0.25 |
| 3 | +0.51 | −0.09 |
| 1 | +0.19 | −0.01 |
| 0 (NIT) | 0.00 | 0.00 |

NIT findings cost nothing in either direction. A score-9 wrong finding on a defense case costs 9× a score-3 wrong finding.

### Combined Scoring Function

```
case_score = w_v × verdict_score  +  w_f × mean(finding_scores)
```

Where:
- `verdict_score` — penalty-aware function from the table above
- `finding_scores` — Brier-like score per finding, averaged across all FATAL/MATERIAL findings in the critique
- Starting weights: `w_v = 0.60`, `w_f = 0.40`

Weight rationale: verdict is the primary signal (the system must reach the right answer), but finding calibration is substantive — a critic that correctly exonerates by raising only score-2 concerns should score higher than one that accidentally exonerates after raising score-8 concerns the adjudicator dismisses.

**Combined score range:**
- Perfect calibration (sound case, no FATAL/MATERIAL findings, defense_wins): +1.00 verdict + 0.00 finding = +1.00
- Worst calibration (sound case, score-9 findings, critique_wins): −0.50 verdict − 0.81 finding = −1.31 × 0.40 weight → lower floor than verdict-only
- Always-hedge coward (sound case, score-5 findings, empirical_test_agreed): −0.25 verdict − 0.25 finding

### Severity Clamp

Score 10 is reserved: a finding at severity 10 means the flaw has been *empirically observed* to cause wrong results — not inferred or hypothesized. This constraint belongs in the critic prompt, not just the scoring spec. Without it, severity-10 assignments on subtle theoretical concerns would face a log-loss-adjacent cliff that distorts calibration pressure.

**Prompt language (add to Intervention A):**
> "Severity 10 is reserved for flaws you can trace to an observed wrong result in the PoC output. Inferred or plausible flaws max out at severity 9."

### Interaction with Stability Weighting

Finding-level scores are computed per run (per model draw), then averaged before applying VS weighting:

```
weighted_case_score = mean(case_score across runs) × VS
```

This means unstable finding scores (high variance across model draws) get discounted the same way unstable verdicts do. A case where one model draws severity 8 and another draws severity 2 for the same finding will have high finding-score variance — that variance is absorbed by VS.

---

## Stability-Weighted Scoring

Raw scores are multiplied by verdict stability across model draws:

```
weighted_score(case) = raw_score(case) × VS(case)
```

Where VS = fraction of runs agreeing with majority verdict (3:0 → 1.0, 2:1 → 0.67, all different → 0.33).

**Effect:** A stable correct verdict gets full credit. A lucky correct verdict with high model-draw variance gets discounted. This prevents prompt changes that happen to get the right answer for the wrong reasons from appearing as improvements.

**DER with stability weighting:**
```
weighted_DER = mean(raw_score × VS) across defense cases
```

This is the primary metric for the iteration loop.

## v7 Comparability — Critical Prerequisite

The v7 scoring function (FVC) is not comparable to the penalty-aware function. Claiming "DER improved from 0.00" requires re-running the v7 prompts through the new scoring function first. Without this, the baseline is on a different scale.

**Pre-run step:** Before the first canary iteration, run v7 prompts (no changes) on the v7 benchmark cases under the new scoring function. Record the new baseline scores for DER, IDR, FHR, ARR. These become the v8 comparison points, not the v7 FVC-based results.

## Statistical Interpretation of DER 0.30

With 40 defense cases × 3 runs = 120 evaluations, at target DER 0.30:
- Point estimate: 36 defense_wins out of 120
- Standard error: `sqrt(0.30 × 0.70 / 120)` ≈ 0.042
- 95% CI: approximately [0.218, 0.382]

The lower bound of the confidence interval barely clears 0.22. This is a wide band.

**Open question:** Is DER > 0.30 (point estimate) the right target, or should the target be defined such that the lower CI bound clears a meaningful threshold (e.g., lower bound > 0.25)?

**Practical implication:** With n=120, a result of DER = 0.32 and DER = 0.28 are not distinguishable from each other. The iteration loop should treat canary-set differences of < 0.05 as noise, not signal. Define a minimum meaningful delta (MMD) of 0.05-0.10 before the loop starts.

## Minimum Meaningful Delta (MMD)

For the canary iteration loop (n=40 cases × 3 runs = 120 evaluations per condition):

| Metric | MMD |
|---|---|
| DER | 0.08 (approximately 2 SE) |
| IDR | 0.05 |
| FHR | 0.05 |
| ARR | 0.05 |

Changes smaller than the MMD are within noise and should not trigger acceptance or rejection. Require at least MMD improvement in the primary metric before accepting a prompt change.
