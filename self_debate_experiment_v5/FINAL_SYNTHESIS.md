# v5 Final Synthesis

*Written by experiment orchestrator. Supplements REPORT.md and REPORT_ADDENDUM.md.*

---

## What the Benchmark Tested

The ARCH-1 benchmark tested whether assigning adversarial roles to LLM agents --- a Critic finding flaws, a Defender rebutting invalid critiques --- produces better ML methodology verdicts than single-pass critique. The test was scoped to 110 synthetic binary-verdict cases (80 critique with planted flaws, 30 defense_wins with sound designs), run across five conditions with three independent runs per case. The primary comparison was isolated_debate vs. baseline on four fair-comparison dimensions (IDR, IDP, DRQ, FVC) where both conditions have equal structural agency.

Critically, the benchmark was designed to favor the debate protocol: cases were filtered for cases where proxy_mean < 0.83 to retain headroom for protocol improvement. The difficulty filter was intended to ensure the benchmark was hard enough that the debate structure's additional deliberation could produce measurable signal.

---

## Whether the Protocol Worked

**The protocol performs well in absolute terms but does not demonstrate differential value over baseline.**

- Benchmark mean (isolated_debate): 0.9549
- Baseline mean: 0.9452
- Fair-comparison lift: +0.0097, CI [-0.0013, +0.0217]

The honest framing of the H1 result is not "the protocol fails" but "the benchmark could not resolve whether the protocol adds value." The +0.10 threshold exceeds the ~0.05 of headroom available at the observed baseline performance level. Both conditions score near-ceiling on DRQ and FVC (≥ 0.989), leaving IDR and IDP as the only dimensions with measurable cross-condition differences --- and even there, the lift is +0.0240 on IDR and 0.0000 on IDP.

The failure attribution data provides supporting evidence: 88.6% of isolated_debate runs are clean passes, 6.3% are agent-level failures, and 0.0% are protocol-level failures. The protocol structure itself did not cause any additional failures; the debate machinery works. What does not materialize is a consistent advantage in final output quality over single-pass critique.

**The failure is a benchmark design failure, not a protocol mechanism failure.** The cases were too easy for the baseline --- not hard enough to require the adversarial structure's additional deliberation.

---

## Where It Failed and Why

**Primary failure: ceiling effect.** Baseline performance (0.9452) is high enough that the entire dynamic range available for lift measurement is approximately 0.05. The difficulty labels intended to stratify hard and medium cases did not predict performance (Spearman rho = +0.046, p = 0.687). Despite the proxy_mean < 0.83 filter, the actual baseline aggregate was 0.94+ --- the filter was insufficiently aggressive or the distribution of cases does not produce sufficient hard-case concentration at the aggregate level.

**Secondary failure: no mixed cases.** The ARCH-1 benchmark has only binary-verdict cases. The adversarial structure's theoretical advantage is largest on mixed-verdict cases where both sides have substantive claims. Without mixed cases, the benchmark tests whether the protocol produces correct verdicts on easy-to-resolve cases, not whether it produces better-nuanced verdicts on genuinely ambiguous cases.

**Data integrity events (both remediated):**
- Answer-key leakage in original Phase 6 scoring collapsed IDR/IDP to ~1.0 for all conditions; detected and corrected via isolated rescore.
- Batch 2 contamination (165 files, zero variance) detected via within-case variance check; all files re-run clean.

Both remediations were applied before scoring and do not affect the final results. They do inform future pipeline design.

---

## Forced Multiround: Did the Mechanism Add Value on Hard Cases?

**Directional yes, statistically no.**

After Phase 9.5 correction (three Phase 6 stub-misclassified cases re-run), FM hard mean = 0.9921 vs. MR hard mean = 0.9826. FM is directionally higher. The Wilcoxon test is non-significant (W=12.5, p=0.376).

The hollow-round analysis (ENSEMBLE_ANALYSIS.md) identified a 20.5% hollow-round rate in forced_multiround --- 8 defense_wins cases where round 2 produced no new substantive exchange because all points resolved in round 1. These cases show FM does not improve DRQ or FVC beyond MR (both 0.9286 vs. 1.0000 for MR).

**Qualitative signal:** On critique cases, individual FM runs showed substantive adversarial exchanges (eval_scenario_691: clean concession arc; eval_scenario_649: consistent partial-concession; eval_scenario_428: progressive 2-round arc). The mechanism produces debate dynamics but not consistently better final scores. This qualitative signal is more informative for protocol design than the aggregate statistic.

**v6 implication:** Force round 2 only when the round 1 adjudication produces an unresolved point, not unconditionally. Gate FM on a substantive disagreement signal.

---

## Closed-Loop Confound: What Phase 9 Shows

Phase 9 cross-vendor validation (gpt-4o-mini via OpenRouter, 80/110 parse rate) does not mitigate the closed-loop confound --- it reveals its severity.

| Dimension | Delta (gpt-4o-mini minus Claude) |
|---|---|
| IDR | -0.7737 |
| IDP | +0.1181 |
| FVC | -0.1875 |

An IDR delta of -0.7737 means the two scorers disagree on issue detection for the same outputs at a magnitude that makes absolute IDR values evaluator-dependent. The absolute dimension values in Tables A and B of REPORT.md are Claude-evaluator-relative scores, not ground-truth quality measurements.

The H1 verdict is unaffected (the lift is too small to pass under any scorer), but this finding has architectural implications for future experiments: the IDR/IDP scoring pipeline must use either human evaluators or a cross-model scorer that is not in the same family as the generation model. Using Claude Haiku to rescore Claude Sonnet outputs is a partial fix; the self-enhancement bias is still present, just across model sizes rather than across model versions.

---

## What Changes for v6

Based on the v5 results, these are the minimum changes required for v6 to be informative:

1. **Lower-ceiling benchmark.** The proxy_mean filter must be set more aggressively. Aim for baseline aggregate < 0.75 rather than the v5 result of 0.9452. This may require a harder case generation prompt, a smaller proxy model, or both.

2. **Mixed-verdict cases.** Include at least 30% mixed-verdict cases in the benchmark (cases where the correct verdict is "significant flaw exists but design is not fatally compromised"). This is the case type where adversarial role structure has the clearest theoretical advantage.

3. **Cross-model scoring.** Use a different model family for IDR/IDP scoring. Do not use any Claude model to score Claude-generated outputs on IDR, given the Phase 9 evidence of large evaluator-model sensitivity.

4. **Conditional forced multiround.** Gate FM round 2 on a substantive disagreement signal from round 1 adjudication rather than forcing it unconditionally. Unconditional forcing produces 20.5% hollow rounds.

5. **Power analysis before threshold-setting.** Compute the expected dynamic range from baseline pilot runs before pre-registering the H1 threshold. A threshold of +0.10 on a benchmark with 0.05 of headroom is an uninformative test.

---

## Concrete Recommendation: When to Trust / Distrust the Protocol

**Trust the protocol for:**
- Binary-verdict cases with unambiguous planted flaws, when you want a second-opinion review mechanism and cost is not a constraint
- False-positive control scenarios: the ensemble condition produces higher IDP (0.9583) than isolated_debate (0.8549) by suppressing IDR; use ensemble when raising a false alarm is more costly than missing a real flaw

**Distrust the protocol for:**
- Cases where you need a calibrated absolute quality score: the closed-loop confound (IDR delta -0.7737) means scores are evaluator-relative, not objective
- Mixed-verdict cases: the protocol's behavior on genuinely ambiguous cases is untested
- Production deployment at current cost: 3× token overhead vs. baseline with no demonstrated differential value at fc_lift = +0.0097

**Do not deploy as a general-purpose methodology reviewer** until v6 demonstrates H1 lift on a lower-ceiling, mixed-case benchmark with cross-model scoring.

---

## Complete Artifact Inventory

| File | Phase | Description |
|---|---|---|
| `HYPOTHESIS.md` | 4 | Pre-registered hypothesis with conditions, dimensions, N/A rationale |
| `PREREGISTRATION.json` | 4 | Machine-readable pre-registration |
| `evaluation_rubric.json` | 4 | Scoring dimension definitions |
| `CRITIQUE.md` | 4 | Protocol self-review: 6 design risks |
| `DEFENSE.md` | 4 | Defense response with 7 pre-execution requirements |
| `benchmark_cases.json` | 0 | 110 cases from pipeline (pre-verification) |
| `benchmark_cases_verified.json` | 1 | 110 verified cases (CASE_VERIFIER output) |
| `benchmark_verification.json` | 1 | CASE_VERIFIER output: 110 keep, 0 revise, 0 reject |
| `v5_raw_outputs/` | 6 | 1,650 raw output files (all 5 conditions × 3 runs) |
| `v5_results.json` | 7 | Per-case scores, dimension aggregates, debate_pass_count |
| `v5_results_eval.json` | 7 | Per-case evaluation records with failure_attribution |
| `v5_rescored_idr_idp.json` | 7.5 | Leakage-corrected IDR/IDP (isolated Haiku scorer, 996 files) |
| `CONCLUSIONS.md` | 8 | Primary source of truth: hypothesis verdicts, per-case table |
| `SENSITIVITY_ANALYSIS.md` | 8 | Method A/B, lift decomposition, threshold sensitivity |
| `ENSEMBLE_ANALYSIS.md` | 8 | Ensemble tables, hollow-round, DC/FVC diagnostic |
| `stats_results.json` | 8 | Bootstrap CIs, Wilcoxon tests, variance, failure attribution |
| `sensitivity_analysis_results.json` | 8 | Sensitivity analysis data |
| `per_condition_comparison.png` | 8 | Fair-comparison dimension bar chart |
| `dimension_heatmap.png` | 8 | Dimension score heatmap across conditions |
| `sensitivity_analysis_chart.png` | 8 | Lift sensitivity visualization |
| `difficulty_scatter.png` | 8 | Difficulty labels vs. rubric performance |
| `forced_multiround_hard.png` | 8 | FM vs. MR on hard cases |
| `cross_vendor_scores_v5.json` | 9 | gpt-4o-mini cross-vendor scores: deltas, parse rate |
| `POST_MORTEM.md` | 9.5 | 4 anomalies: 1 high, 1 moderate, 2 low; all remediated |
| `REPORT.md` | 10 | Full experiment report (this document's primary companion) |
| `REPORT_ADDENDUM.md` | 10 | Production re-evaluation and deployment recommendation |
| `PEER_REVIEW_R1.md` | 10 | Round 1 peer review with response section |
| `FINAL_SYNTHESIS.md` | 10 | This document |
| `INVESTIGATION_LOG.jsonl` | all | Structured log of all experiment actions (seq 1–current) |
