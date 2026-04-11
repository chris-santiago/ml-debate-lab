# v6 Experiment Conclusions

**Date:** 2026-04-11  
**Experiment:** self_debate_experiment_v6  
**Benchmark:** 120 cases (80 regular critique+defense, 40 mixed) × 6 conditions × 3 runs = 2,160 outputs  
**Primary scorer:** GPT-4o via OpenRouter (IDR, IDP, ETD)  
**Analysis:** Bootstrap 95% CI (n=10,000, seed=42); Wilcoxon signed-rank for H3

---

## Q1: Does ml-lab debate add value over single-pass baseline?

**Answer: No — not at the pre-registered threshold.**

H1a (regular cases): lift = −0.0026, 95% CI = [−0.1059, 0.2236], p = 0.5165 → **FAIL**  
H1b (mixed FVC): lift = +0.0083, 95% CI = [0.00, 0.05], p = 0.361 → **FAIL**

The adversarial debate protocol (isolated critic + defender + adjudicator) does not reliably outperform a single-pass critique on either regular or mixed cases. The fair-comparison lift is negative (−0.0026) and the bootstrap CI spans zero by a wide margin. The null result is robust across threshold sensitivity checks (±0.02).

**Dimension decomposition:** IDR is the primary failure mode — debate misses slightly more planted issues than baseline (0.6603 vs 0.6712). IDP_adj shows a small positive signal (+0.0167) from adjudicator filtering, but this is insufficient to offset the IDR deficit. DRQ and FVC are flat across conditions.

---

## Q2: Does adversarial structure add value over a compute-matched ensemble?

**Answer: Inconclusive — neither superior.**

H2 regular: isolated_debate − ensemble_3x = −0.0287, CI = [−0.1567, 0.0976] → **INCONCLUSIVE**  
H2 mixed FVC: isolated_debate − ensemble_3x = −0.0167, CI = [−0.075, 0.025] → **INCONCLUSIVE**

The two-sided CI spans zero in both dimensions. Three independent assessors (ensemble_3x) and one structured debate (isolated_debate) are statistically indistinguishable at this sample size.

**Descriptive observation:** ensemble_3x has the highest IDR (0.7717) and IDP (0.9861) of all conditions — 3 independent critics with union-of-issues pooling improve recall substantially. This suggests compute spent on redundancy (ensemble) may be more efficient than compute spent on adversarial structure (debate), but the difference is not formally significant.

---

## Q3: Is forced multiround superior to natural stopping?

**Answer: No.**

H3: CFM hard mean = 0.7049, MR hard mean = 0.6736, diff = +0.0313, W = 16.0, p = 0.3677, n_eff = 7 → **FAIL**

Conditional FM does not significantly outperform multiround on hard cases. The gate-fire rate of 94.7% (341/360 files) means the conditional gate almost never stops at round 1 — CFM is functionally equivalent to full multiround in practice. When nearly all cases require round 2, the "conditional" nature of the gate provides no efficiency benefit and no quality improvement.

**Secondary: hollow rate PASS.** Proxy hollow rate = 2.2% (< 10% threshold). When round 2 does fire, it is not hollow — PRR > 0 in the overwhelming majority of cases.

---

## Q4: Does persona-biasing improve debate quality?

**Answer: Partial — mixed FVC improves, but overall verdict is fail.**

H6: 1/3 tested dimensions has CI excluding 0 → **FAIL**  
- IDR: delta = +0.0352, CI = [−0.0907, 0.1614], p = 0.2892 — not significant
- IDP_adj: delta = −0.0389, CI = [−0.075, 0.000], p = 0.9782 — negative (precision hurt)
- FVC_mix: delta = +0.2417, CI = [0.1583, 0.3333], p = 0.00 — **significant improvement**

**FVC (mixed cases):** Biased debate achieves 0.25 vs isolated debate's 0.0083 on FVC_mixed. The combative-critic and selective-defender personas reliably produce `empirical_test_agreed` verdicts on mixed cases, where isolated debate almost never does. This is a real structural difference.

**IDP:** Persona-priming lowers IDP_raw (0.8917 vs 0.9472 baseline) — the aggressive critic generates more false claims. The defender does not fully filter these out (IDP_adj = 0.9250 vs 0.9639 isolated). Precision is hurt by the bias injection.

**IDR:** Nominally higher (0.6955 vs 0.6603 isolated) but not significant. The aggressive critic recalls slightly more issues but at a precision cost.

**Summary:** Biased debate is better at producing structured empirical conclusions on mixed cases but worse at precision. The tradeoff may be acceptable in contexts where FVC (correct verdict on empirically ambiguous cases) is the primary concern.

---

## Cross-Cutting Observations

**ETD ceiling (H4, exploratory):** All three debate conditions score ETD = 1.0 (full credit) on 100% of mixed cases. Every debate produced condition + supports_critique_if + supports_defense_if in the transcript. The ETD metric provides zero discrimination between debate conditions.

**Multiround FVC (mixed cases):** Multiround achieves FVC_mixed = 0.3667, the second highest after biased_debate (0.25). Multiple debate rounds help mixed cases more than regular cases — the iterative exchange surfaces empirical test designs that single-pass baseline (FVC = 0.0) never produces.

**Baseline ceiling on regular cases:** Baseline FC = 0.6785. Most regular cases (eval_scenario category) score near the ceiling under baseline, leaving little room for debate to add value. The RC (ReScience) cases score near the floor. This bimodal pattern compresses the effective range for H1a.

**Conditional FM gate saturation:** A 94.7% gate-fire rate means the FM gate is not functioning as a selective filter — it fires on almost all cases. The PRR after round 1 is rarely sufficient to stop (mean PRR = 0.418 across all CFM files). Redesigning the gate trigger (e.g., lower PRR threshold, different stopping criterion) is recommended for future runs.

---

## Phase 9 Outstanding

**H5 (cross-model scorer agreement)** is deferred to Phase 9. IDR/IDP/ETD agreement between GPT-4o (primary) and Claude (secondary) has not been quantified. The validity of all Q1–Q4 conclusions depends on GPT-4o scorer calibration.

---

## Verdict Table

| Question | Hypothesis | Result | Finding |
|---|---|---|---|
| Q1 | H1a: Debate > Baseline (regular) | **FAIL** | lift=−0.0026, CI far below threshold |
| Q1 | H1b: Debate > Baseline (mixed FVC) | **FAIL** | lift=+0.0083, CI includes 0 |
| Q2 | H2: Debate vs Ensemble | **INCONCLUSIVE** | CI spans zero in both dimensions |
| Q3 | H3: CFM > Multiround (hard cases) | **FAIL** | p=0.3677; gate fires 94.7% of cases |
| Q4 | H6: Biased > Isolated | **FAIL** | 1/3 dims significant; FVC_mix positive, IDP negative |
| — | H4: ETD by mode (exploratory) | **CEILING** | ETD=1.0 for all conditions; no discrimination |
| — | H5: Cross-model scorer agreement | **DEFERRED** | Phase 9 |
