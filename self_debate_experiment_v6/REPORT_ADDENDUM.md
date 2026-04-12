# v6 Report Addendum: Production Deployment Recommendation

**Date:** 2026-04-11
**Experiment:** self_debate_experiment_v6

---

## Should the ml-lab Debate Protocol Be Used in Production?

### Recommendation Summary

**Do not deploy the adversarial debate protocol (isolated_debate) as the primary methodology review mechanism.** Replace it with ensemble assessment for all regular (critique/defense) cases. For mixed/ambiguous cases, multiround debate is the most promising variant, but requires stabilization before deployment.

---

## By Use Case

### Regular Methodology Review (critique/defense cases)

**Recommended: ensemble_3x with union-of-issues IDR**

The experiment provides no evidence that the critic-defender-adjudicator debate structure improves methodology review quality over a single-pass critique (H1a FAIL, lift = −0.0026). In contrast, three independent assessors with union-of-issues recall pooling achieve:

- IDR = 0.7717 vs. baseline 0.6712 (+0.1005, the largest effect observed in the experiment)
- IDP = 0.9861 vs. baseline 0.9472 (highest precision of all conditions)
- FC = 0.7046 vs. baseline 0.6785

At matched compute (3x baseline), independent redundancy outperforms adversarial structure on both recall and precision. The intuition is straightforward: three independent critics raise different issues from different analytical angles; union pooling recovers all of them. One critic trying to persuade another does not add a new analytical perspective — it routes the same perspective through a debate structure. *(Per-tier precision analysis, `v6_minority_precision.py`: minority-flagged issues precision = 0.946, unanimous = 0.929, diff = +0.017, CI [−0.028, +0.068] — no significant difference. ENSEMBLE_ANALYSIS.md §7.)*

**Compute cost:** 3× baseline per review. Suitable for any use case where baseline compute is acceptable and recall matters.

**Deployment note:** The majority-vote verdict in ensemble_3x is correct in 75% of regular cases — identical to baseline. The ensemble's advantage is entirely in issue detection recall and precision, not in final verdict accuracy. The ensemble should be deployed for issue identification, not verdict generation.

---

### Mixed / Empirically Ambiguous Cases

**Recommended: multiround debate (with stabilization work)**

Multiround debate achieves FVC_mixed = 0.3667, the highest of all conditions and far above baseline (0.0). The iterative exchange appears to help agents recognize when a verdict cannot be reached without additional empirical evidence, producing `empirical_test_agreed` outcomes in approximately one-third of cases.

However, multiround has the highest within-case variance of all conditions: 20 of 23 high-variance case-condition pairs are multiround, with several cases oscillating between FC = 0.0 and FC = 1.0 across three runs. The aggregate advantage is real but the per-case reliability is not.

**Recommended investment before deployment:**
1. Temperature reduction or fixed-seed inference for multiround to reduce path-dependent outcomes
2. Adjudicator prompt hardening on `empirical_test_agreed` criterion — when should it apply?
3. Explicit stopping criterion beyond "4 rounds or consensus": add a structured checklist for adjudicator to evaluate before round 2+

**Do not deploy multiround without stabilization.** The variance profile means one in five cases produces a qualitatively different outcome depending on stochastic variation.

---

### Persona-Biased Debate (biased_debate)

**Not recommended for regular cases. Conditionally useful for mixed cases.**

On regular cases, biased_debate has lower FC than baseline (0.6726 vs. 0.6785). The aggressive critic persona generates more claims at a precision cost (IDP = 0.8917, lowest of all conditions). The net effect is negative.

On mixed cases, biased_debate achieves FVC_mixed = 0.2500 (second only to multiround at 0.3667). If multiround is unavailable or too expensive, biased_debate is a viable alternative for mixed-case empirical test generation at 3× baseline compute (vs. 3–6× for multiround).

**Tradeoff:** Higher false-positive rate on claims is acceptable if the downstream consumer reviews the critic's output directly rather than relying on the adjudicator's synthesis. Not recommended for automated pipelines where precision matters.

---

### Conditional FM Gate

**Not ready for production.**

The gate fires on 94.7% of cases, providing no meaningful efficiency over full multiround. The gate's design assumes that many cases will resolve cleanly in round 1 (PRR = 1.0), but mean PRR after round 1 is only 0.418. The conditional gate was designed for a harder stopping criterion than the actual debate dynamics produce.

A redesigned gate with a lower PRR threshold (e.g., PRR ≥ 0.7 triggers stop rather than PRR = 1.0) would provide better efficiency. The current design should not be deployed as-is.

---

## Cost-Benefit Summary

| Protocol | Compute | IDR | FVC_regular | FVC_mixed | Recommendation |
|----------|---------|-----|-------------|-----------|----------------|
| baseline | 1× | 0.6712 | 0.75 | 0.00 | Minimum viable |
| isolated_debate | 3× | 0.6603 | 0.75 | 0.0083 | **Do not use** |
| biased_debate | 3× | 0.6955 | 0.75 | 0.25 | Mixed cases only |
| multiround | 3–6× | 0.6523 | 0.6917 | 0.3667 | Mixed cases (post-stabilization) |
| conditional_fm | 3–6× | 0.2153* | 0.9167* | N/A | Not ready |
| **ensemble_3x** | **3×** | **0.7717** | **0.75** | **0.025** | **Recommended for regular** |

*conditional_fm values computed on n=8 hard cases only; not comparable to other conditions.

---

## Investment Priorities for v7

1. **Stabilize multiround for mixed cases.** The FVC_mixed = 0.3667 signal is the most actionable positive finding. If reliable, it would justify multiround as the preferred protocol for empirically ambiguous reviews.

2. **Redesign the CFM gate trigger.** A PRR threshold of 0.7 or higher (instead of 1.0) would provide genuine selective deployment rather than near-universal round-2 firing.

3. **Redesign the ETD metric.** ETD = 1.0 for all debate conditions provides no discrimination. A sub-element quality rubric (specificity of condition, falsifiability of supports_critique_if, orthogonality of supports_defense_if) would restore discriminative power.

4. **Benchmark ensemble_3x against baseline formally.** H2 tested debate vs. ensemble, not ensemble vs. baseline. A direct formal test of whether union-IDR ensemble outperforms baseline would confirm the descriptive +0.1005 IDR advantage with statistical rigor.

5. **Expand hard case sample.** H3 ran on n=8 hard cases. Expanding to n=30+ would give the conditional FM gate test adequate statistical power and clarify whether the FM advantage is real or noise.
