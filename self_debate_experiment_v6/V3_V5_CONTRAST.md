# v3 vs v5: Result Contrast

## Top-Line Numbers

| Metric | v3 | v5 |
|---|---|---|
| Raw lift (isolated vs baseline) | **+0.341** ✅ CONFIRMED | **+0.0097** ❌ REFUTED |
| Fair-comparison lift | +0.0913 | +0.0113 |
| Isolated debate mean | 0.975 | 0.9549 |
| Baseline mean | 0.634 | 0.9452 |
| N cases | 49 | 110 |
| H1 verdict | PASS | FAIL |

The gap is enormous on the surface (+0.341 vs +0.0097), but the comparison requires unpacking three distinct sources of difference.

---

## Source 1: Structural penalties inflated v3 lift

In v3, the baseline condition was **definitionally penalized** on two dimensions:
- **DC = 0.0** (baseline doesn't produce a verdict label at all)
- **DRQ = 0.49** (no debate transcript to evaluate)

These aren't "baseline is bad at debate quality" — they're "baseline structurally can't produce the output that DC and DRQ measure." This contributed ~+0.25 of the raw v3 lift. The v5 design explicitly removed both: DC/DRQ are excluded from the fair-comparison set for baseline.

When you compute the v3 fair-comparison lift (IDR/IDP/ETD/FVC only, from the v3 sensitivity analysis): **+0.0913**. When you compute the same for v5 (IDR/IDP/DRQ/FVC): **+0.0113**. The gap narrows from 0.334 to 0.08.

---

## Source 2: ETD was the real signal in v3, and v5 eliminated it

This is the most important finding. Looking at v3 dimension-level data:

| Dim | v3 Isolated | v3 Baseline | Delta |
|---|---|---|---|
| IDR | 1.000 | **1.000** | 0.000 |
| IDP | 1.000 | **1.000** | 0.000 |
| ETD | 0.841 | **0.476** | **+0.365** |
| FVC | 0.980 | 0.980 | 0.000 |

In v3, **IDR/IDP/FVC showed zero debate advantage** — baseline was already ceiling or tied. Nearly all the fair-comparison lift (+0.0913) came from **ETD alone**: the debate protocol was better at specifying empirical tests when cases were genuinely contested.

v5 has **zero ETD signal** — ARCH-1 has no mixed cases, ETD is N/A for all 110 cases by design. The one dimension where debate demonstrably helped was designed out.

---

## Source 3: v5 baseline is near-ceiling on remaining dims

With structural penalties removed and ETD excluded, v5 is measuring debate advantage on IDR, IDP, DRQ, and FVC — and baseline scores very high on all four:

| Dim | v5 Isolated | v5 Baseline | Delta |
|---|---|---|---|
| IDR | 0.8969 | 0.8729 | +0.024 |
| IDP | 0.8549 | 0.8549 | **0.000** |
| DRQ | 1.0000 | 0.9894 | +0.011 |
| FVC | 1.0000 | 0.9894 | +0.011 |

Baseline DRQ/FVC: 324 of 330 runs score exactly 1.0. Baseline gets the verdict right almost every time. **The cases v5 selected as "hard" are not hard on the verdict dimensions** — only on the issue-identification dimensions (IDR), and even there the debate advantage is marginal (+0.024).

---

## Hypotheses for the Underlying Reason

**H1 (primary): The true debate advantage is narrow and ETD-specific.** The debate protocol helps models be more precise about *when something requires empirical resolution* — not about finding flaws or getting verdicts right. v3 showed this via ETD; v5 can't test it because there are no mixed cases. The -0.33 lift change between experiments is almost entirely explained by (a) removing structural penalties and (b) removing the one dimension where debate showed genuine signal.

**H2: The rubric dimensions (DRQ/FVC) are verdicts, and the model gets verdicts right.** DRQ and FVC are essentially "did you emit the correct verdict type." Sonnet correctly identifies `critique_wins` vs `defense_wins` with ~98.9% accuracy at single-pass. Debate can't improve a skill that's already near-ceiling.

**H3: IDR is sensitive to case construction, not just protocol.** v3 IDR = 1.0 for *both baseline and debate* — cases were too easy. v5 IDR = 0.87 for baseline, 0.90 for debate — cases are harder, but the ~0.024 advantage is structurally small. The hypothesis that "adversarial structure forces more thorough issue detection" is weakly supported at best.

**H4 (speculative): IDP is flat, which is the real surprise.** IDP (precision, false-alarm rate) should theoretically benefit from adversarial forcing — a Defender challenging every critique claim should suppress false alarms. But IDP is identical (0.8549) for both conditions in v5. Adversarial challenge is apparently not filtering spurious critique claims.

---

## Summary interpretation

v3's headline result (+0.341) was **not fraudulent but it was fragile** — it rested heavily on structural asymmetry in the scoring rubric. The corrected fair-comparison lift in v3 was ~+0.09, just below the +0.10 threshold even in the favorable case.

v5's result (+0.0097) represents what happens when you build a cleaner experiment: structural penalties removed, larger N, harder cases. The signal nearly vanishes. The most honest interpretation is that **the adversarial debate protocol's advantage, if any, is specific to ETD (empirical test quality)** — a dimension that requires genuine ambiguity in the case to trigger. On binary verdict tasks with planted flaws, single-pass Sonnet is already good enough that the protocol adds almost nothing.
