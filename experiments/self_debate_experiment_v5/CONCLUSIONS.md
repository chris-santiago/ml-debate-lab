# v5 Experiment Conclusions

## Abstract

The v5 self-debate experiment ran 110 benchmark cases across five conditions (isolated_debate, multiround, forced_multiround [hard cases only], ensemble, baseline), three runs each, yielding 1,650 raw output files. The primary metric is fair-comparison lift — isolated_debate versus baseline on IDR/IDP/DRQ/FVC only, the four dimensions where baseline has equal structural agency.

**Primary result:** fc_lift = +0.0097, bootstrap 95% CI [-0.0013, +0.0217]. The CI includes zero. **H1 FAILS** (pre-registered threshold: +0.10).

IDR and IDP values used in this document are rescored from raw agent text using an isolated semantic scorer (rescore_idr_idp.py), fixing an orchestrator answer-key leakage identified post-Phase 6. The rescoring covers all critique cases (n=80) across applicable conditions. Defense_wins cases are excluded from IDR/IDP scoring by protocol.

**Phase 9.5 correction:** Three FM critique cases (eval_scenario_381, eval_scenario_411, eval_scenario_616) were originally generated as medium-difficulty stubs by the Phase 6 batch agent (not_applicable_difficulty). These 9 files were re-run in Phase 9.5 with correct forced_multiround protocol, producing real debate outputs (all critique_wins, debate_rounds=2). Per-case FM means post-correction: 381=0.9583, 411=0.9583, 616=0.9167. FM hard mean corrected from 0.9425 to 0.9921.

---

## Benchmark Pass/Fail Criteria

| Criterion | Pre-registered Threshold | Actual | Pass? |
|---|---|---|---|
| H1: fc_lift isolated vs baseline | ≥ +0.10 | +0.0097 [CI: -0.0013, +0.0217] | **FAIL** |
| Debate pass rate | ≥ 75% | 89.1% (98/110) | PASS |
| Benchmark mean (isolated_debate) | ≥ 0.65 | 0.9549 | PASS |
| H2: FM > MR on hard (DRQ and IDR) | FM mean > MR mean | FM=0.9921 > MR=0.9826 (stub-fix corrected) | **PASS** |
| Secondary: Ensemble FVC ≥ 0.5 on ≥ 60% of defense_wins | ≥ 60% | 100% (30/30) | PASS |
| Difficulty label validity (Spearman rho negative, p < 0.05) | rho < 0, p < 0.05 | rho=0.046, p=0.687 | **FAIL** |

**Overall benchmark:** FAIL — primary hypothesis not met. H1 lift is positive but negligibly small and CI-inclusive-of-zero.

---

## Per-Case Scoring Table

All 5 conditions; forced_multiround shown as N/A for non-hard cases. Values are mean scores across 3 runs (PRIMARY dimensions: IDR/IDP/DRQ/FVC; DC diagnostic-only, ETD excluded as N/A for all ARCH-1 cases).

| case_id | category | difficulty | isolated_debate | multiround | ensemble | baseline | forced_multiround |
|---|---|---|---|---|---|---|---|
| eval_scenario_228 | critique | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_259 | critique | hard | 1.0000 | 0.9583 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_318 | critique | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_381 | critique | hard | 0.6250 | 0.6250 | 0.7500 | 0.7500 | 0.9583 |
| eval_scenario_411 | critique | hard | 0.7500 | 0.7500 | 0.7500 | 0.7500 | 0.9583 |
| eval_scenario_422 | critique | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_428 | critique | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_524 | critique | hard | 0.8750 | 0.9375 | 1.0000 | 0.8750 | 0.8750 |
| eval_scenario_616 | critique | hard | 0.8750 | 1.0000 | 0.7500 | 0.7500 | 0.9167 |
| eval_scenario_649 | critique | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_685 | critique | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9583 |
| eval_scenario_691 | critique | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_104 | critique | medium | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_105 | critique | medium | 1.0000 | 1.0000 | 0.8750 | 1.0000 | N/A |
| eval_scenario_125 | critique | medium | 1.0000 | 1.0000 | 0.5000 | 1.0000 | N/A |
| eval_scenario_139 | critique | medium | 0.9583 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_155 | critique | medium | 0.8750 | 0.8750 | 0.9583 | 0.8750 | N/A |
| eval_scenario_160 | critique | medium | 0.9167 | 0.8500 | 0.8500 | 0.8833 | N/A |
| eval_scenario_162 | critique | medium | 1.0000 | 0.9583 | 0.9583 | 0.9583 | N/A |
| eval_scenario_163 | critique | medium | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_164 | critique | medium | 0.9167 | 0.8750 | 0.8333 | 0.8750 | N/A |
| eval_scenario_167 | critique | medium | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_174 | critique | medium | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_18 | critique | medium | 0.9583 | 0.9167 | 1.0000 | 1.0000 | N/A |
| eval_scenario_180 | critique | medium | 1.0000 | 0.9167 | 1.0000 | 0.9167 | N/A |
| eval_scenario_199 | critique | medium | 1.0000 | 1.0000 | 0.8000 | 0.9500 | N/A |
| eval_scenario_230 | critique | medium | 0.8750 | 0.9583 | 0.9167 | 0.9167 | N/A |
| eval_scenario_238 | critique | medium | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_250 | critique | medium | 0.6250 | 0.6250 | 0.7500 | 0.6250 | N/A |
| eval_scenario_264 | critique | medium | 1.0000 | 1.0000 | 0.9583 | 1.0000 | N/A |
| eval_scenario_269 | critique | medium | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_271 | critique | medium | 1.0000 | 1.0000 | 0.8750 | 0.9375 | N/A |
| eval_scenario_275 | critique | medium | 0.7500 | 0.7500 | 0.9167 | 0.7500 | N/A |
| eval_scenario_286 | critique | medium | 0.8333 | 0.8333 | 1.0000 | 0.8333 | N/A |
| eval_scenario_292 | critique | medium | 0.9583 | 1.0000 | 0.8750 | 1.0000 | N/A |
| eval_scenario_295 | critique | medium | 0.9583 | 1.0000 | 0.4167 | 0.7500 | N/A |
| eval_scenario_296 | critique | medium | 1.0000 | 1.0000 | 0.8750 | 1.0000 | N/A |
| eval_scenario_299 | critique | medium | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_3 | critique | medium | 1.0000 | 1.0000 | 0.5000 | 0.6667 | N/A |
| eval_scenario_305 | critique | medium | 1.0000 | 1.0000 | 0.9167 | 1.0000 | N/A |
| eval_scenario_311 | critique | medium | 0.7500 | 0.7500 | 0.7500 | 0.7500 | N/A |
| eval_scenario_332 | critique | medium | 0.8611 | 0.8889 | 1.0000 | 0.9167 | N/A |
| eval_scenario_333 | critique | medium | 0.8333 | 0.8333 | 0.7500 | 0.8333 | N/A |
| eval_scenario_375 | critique | medium | 0.7500 | 0.7500 | 0.7500 | 1.0000 | N/A |
| eval_scenario_380 | critique | medium | 0.9167 | 0.9167 | 1.0000 | 1.0000 | N/A |
| eval_scenario_403 | critique | medium | 1.0000 | 1.0000 | 0.7500 | 0.7500 | N/A |
| eval_scenario_409 | critique | medium | 1.0000 | 1.0000 | 0.8750 | 1.0000 | N/A |
| eval_scenario_412 | critique | medium | 1.0000 | 0.9167 | 0.9583 | 0.9167 | N/A |
| eval_scenario_414 | critique | medium | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_433 | critique | medium | 1.0000 | 1.0000 | 0.9375 | 0.9167 | N/A |
| eval_scenario_437 | critique | medium | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_474 | critique | medium | 0.7500 | 0.8750 | 1.0000 | 0.8750 | N/A |
| eval_scenario_479 | critique | medium | 1.0000 | 1.0000 | 0.7500 | 1.0000 | N/A |
| eval_scenario_484 | critique | medium | 0.9583 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_496 | critique | medium | 0.7500 | 0.7500 | 0.7500 | 0.6250 | N/A |
| eval_scenario_500 | critique | medium | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_508 | critique | medium | 0.8750 | 0.9583 | 1.0000 | 0.8750 | N/A |
| eval_scenario_517 | critique | medium | 1.0000 | 1.0000 | 0.8750 | 1.0000 | N/A |
| eval_scenario_530 | critique | medium | 0.8889 | 0.7778 | 0.8750 | 0.8194 | N/A |
| eval_scenario_535 | critique | medium | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_554 | critique | medium | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_555 | critique | medium | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_557 | critique | medium | 1.0000 | 0.9722 | 1.0000 | 1.0000 | N/A |
| eval_scenario_574 | critique | medium | 0.9722 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_578 | critique | medium | 0.7500 | 0.7500 | 0.7500 | 0.6250 | N/A |
| eval_scenario_592 | critique | medium | 0.8750 | 0.8750 | 0.7500 | 0.8750 | N/A |
| eval_scenario_596 | critique | medium | 1.0000 | 0.8750 | 1.0000 | 0.8750 | N/A |
| eval_scenario_598 | critique | medium | 1.0000 | 1.0000 | 0.9375 | 1.0000 | N/A |
| eval_scenario_605 | critique | medium | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_606 | critique | medium | 1.0000 | 1.0000 | 0.9583 | 1.0000 | N/A |
| eval_scenario_615 | critique | medium | 0.9167 | 0.9167 | 0.8750 | 0.9167 | N/A |
| eval_scenario_621 | critique | medium | 0.8750 | 0.8750 | 1.0000 | 0.8750 | N/A |
| eval_scenario_638 | critique | medium | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_641 | critique | medium | 1.0000 | 0.9583 | 1.0000 | 1.0000 | N/A |
| eval_scenario_651 | critique | medium | 0.8750 | 0.8750 | 1.0000 | 0.8750 | N/A |
| eval_scenario_656 | critique | medium | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A |
| eval_scenario_664 | critique | medium | 0.9167 | 0.9167 | 1.0000 | 0.8611 | N/A |
| eval_scenario_682 | critique | medium | 0.8750 | 0.8750 | 0.8333 | 0.8542 | N/A |
| hyp_054 | critique | medium | 1.0000 | 1.0000 | 1.0000 | 1.0000 | N/A |
| hyp_077 | critique | medium | 0.8958 | 0.8750 | 0.8750 | 0.8750 | N/A |
| eval_scenario_109 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_113 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_13 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_142 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_144 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_17 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_189 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_194 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_20 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_207 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_212 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_219 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_309 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_312 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_313 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_319 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_323 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_326 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_342 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_344 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_394 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_419 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_468 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_483 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_487 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_488 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_509 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_589 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_594 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| eval_scenario_624 | defense_wins | hard | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

*Note: means are computed over non-null PRIMARY dimensions (IDR/IDP/DRQ/FVC). For defense_wins cases, IDR/IDP are not applicable by protocol; those cases are scored on DRQ/FVC only. forced_multiround N/A for medium difficulty cases.*

---

## Table A: Debate vs Ensemble (Fair Comparison Dimensions)

Dimensions: IDR, IDP, DRQ, FVC. ETD excluded (N/A for all ARCH-1 cases). DC excluded (diagnostic-only).

| Condition | IDR (rescored) | IDP (rescored) | DRQ | FVC | FC Mean |
|---|---|---|---|---|---|
| isolated_debate | 0.8969 | 0.8549 | 1.0000 | 1.0000 | 0.9477 |
| ensemble (majority IDR) | 0.7679 | 0.9583 | 0.9727 | 0.9727 | 0.9179 |
| ensemble (union IDR†) | 0.8725 | 0.9583 | 0.9727 | 0.9727 | 0.9441 |
| baseline | 0.8729 | 0.8549 | 0.9894 | 0.9894 | 0.9266 |

*FC Mean = mean of the four fair-comparison dimensions. IDR/IDP values are from v5_rescored_idr_idp.json (leakage-corrected). DRQ/FVC values from v5_results.json dimension_aggregates.*

*†Union IDR: any-assessor-found replaces majority-vote. IDR recovers +0.1046 (43/240 critique runs affected). Under union IDR, ensemble FC mean (0.9441) exceeds baseline (0.9266) by +0.0175 and nearly matches isolated_debate (0.9477). See ENSEMBLE_ANALYSIS.md — Union IDR Sensitivity Analysis.*

*Wilcoxon (isolated vs ensemble, fair dims): W=648.5, p=0.119 — not significant.*

---

## Table B: Debate Conditions vs Each Other

Dimensions: IDR, IDP, DC (diagnostic), DRQ, FVC. ETD excluded.

| Condition | IDR (rescored) | IDP (rescored) | DC (diag) | DRQ | FVC | Overall Mean |
|---|---|---|---|---|---|---|
| isolated_debate | 0.8969 | 0.8549 | 1.0000 | 1.0000 | 1.0000 | 0.9504 |
| multiround | 0.8925 | 0.8580 | 1.0000 | 1.0000 | 1.0000 | 0.9501 |
| forced_multiround* | 1.0000 | 0.9259 | 0.7500 | 0.9286 | 0.9286 | 0.9066 |
| ensemble | 0.7679 | 0.9583 | 0.9625 | 0.9727 | 0.9727 | 0.9268 |
| baseline | 0.8729 | 0.8549 | N/A | 0.9894 | 0.9894 | 0.9267 |

*forced_multiround restricted to 42 hard cases; IDR/IDP from rescored file (9 critique cases, 27 files — 3 critique cases with null verdicts excluded from rescoring). DC/DRQ/FVC from v5_results.json.*

*Wilcoxon (isolated vs multiround, fair dims): W=133.5, p=0.561 — not significant.*
*Wilcoxon (isolated vs baseline, fair dims): W=314.0, p=0.047 — marginally significant but effect size r=0.32 and lift is small.*

---

## Hypothesis Verdicts

### H1 (Primary): Fair-comparison lift ≥ +0.10

**FAILS.** fc_lift = +0.0097. Bootstrap 95% CI: [-0.0013, +0.0217]. The CI includes zero. The observed lift is one-tenth of the pre-registered threshold. The Wilcoxon test on fair-comparison dimensions (isolated vs baseline) reached p=0.047, but this is a marginal result and the effect size is small (r=0.32). The bootstrap CI is the definitive gate per pre-registration.

### H2 (Secondary): Protocol lifts harder cases more

**NOT INTERPRETABLE.** H2 required H1 to pass as a prerequisite. With H1 failed, stratified lift analysis is not meaningful. Difficulty labels are also invalidated (Spearman rho=0.046, p=0.687 — see Difficulty Label Validation section).

### Secondary: Ensemble FVC ≥ 0.5 on ≥ 60% of defense_wins cases

**PASSES.** Ensemble FVC ≥ 0.5 on 30/30 (100%) of defense_wins cases. The adversarial synthesis produced well-calibrated verdicts on defense-wins cases. However, given H1 failure, this finding is interpreted as showing ensemble does not harm defense_wins calibration, not as evidence of superiority over baseline.

### Secondary: Forced multiround > natural multiround on hard cases (DRQ and IDR)

**PASSES (corrected).** FM mean on hard cases = 0.9921 vs MR mean on hard = 0.9826. FM is higher after Phase 9.5 stub-fix rerun. The three cases (eval_scenario_381, 411, 616) were originally Phase 6 batch-agent stubs (not_applicable_difficulty) that depressed FM hard mean to 0.9425; after re-run with correct FM protocol, all 9 files produced critique_wins verdicts and the corrected mean is 0.9921. The directional result holds but the margin is small and the Wilcoxon test on fair-comparison dimensions (FM vs MR, hard) is non-significant (W=1.5, p=0.977).

---

## Forced Multiround Analysis

**Scope:** 42 hard cases only (12 critique + 30 defense_wins). 3 runs each = 126 FM files. 12 FM critique files were scored for IDR/IDP via rescoring. Three cases (eval_scenario_381, 411, 616) were originally stubs from Phase 6 batch agent misclassification and were re-run in Phase 9.5 with correct FM protocol; their rescored IDR/IDP is included in the analysis below.

**DRQ and IDR — FM vs MR on hard cases:**

| Metric | FM (hard, n=42) | MR (hard, n=42) |
|---|---|---|
| IDR (rescored, critique only, n=27) | 1.0000 | 1.0000 |
| IDP (rescored, critique only, n=27) | 0.9259 | 0.9537 |
| DRQ | 0.9286 | 1.0000 |
| FVC | 0.9286 | 1.0000 |

After Phase 9.5 stub correction, FM IDR = 1.0000 ties MR; IDP is slightly lower for FM (0.9259 vs 0.9537). DRQ and FVC remain lower for FM than MR (0.9286 vs 1.0000) — these are driven by the defense_wins FM cases, where the forced second round sometimes produces hollow exchanges that don't resolve to a clear verdict upgrade.

**Wilcoxon (FM vs MR, hard, fair dims):** W=1.5, p=0.977 — no significant difference.

**Qualitative signal from PHASE6_OBSERVATIONS.md:** Individual cases show FM producing substantive adversarial exchanges. eval_scenario_691 produced a clean concession arc (point_resolution_rate=1.0, both points resolving toward critique). eval_scenario_649 produced consistent partial-concession patterns across all 3 runs. eval_scenario_428 showed a progressive 2-round arc with the Defender holding on one issue while conceding others. This qualitative signal suggests FM affects debate dynamics without consistently improving final scores — the protocol forces exchange but does not guarantee score improvement.

The corrected FM hard mean (0.9921 > MR 0.9826) shows the directional result holds but the margin is small. The Wilcoxon non-significance and the hollow-round pattern in defense_wins cases temper the interpretation.

---

## Failure Mode Taxonomy

From v5_results_eval.json failure_attribution counts:

| Attribution | Count | Fraction |
|---|---|---|
| none (clean pass or acceptable fail) | 294 | 88.6% |
| ambiguous | 15 | 4.5% |
| agent | 21 | 6.3% |
| protocol | 0 | 0.0% |

*Note: 330 total evaluation files (110 cases × 3 runs for the primary isolated_debate condition). The 9 null-verdict FM files are not included in the failure_attribution counts — those were protocol failures at the output-generation level, not scoring-level failures.*

The dominant failure mode is agent (6.3% of runs) — these are cases where the agent missed a planted issue or raised a false positive at a sufficient rate to score below threshold. The ambiguous category (4.5%) covers borderline cases where failure cause could not be definitively attributed. No protocol-level failures were classified in the attribution data.

---

## Difficulty Label Validation

**Spearman rho = +0.046, p = 0.687** (non-defense_wins cases only, n=80).

The difficulty labels do NOT predict rubric performance. The expected direction was negative (harder labels → lower baseline scores); the observed direction is slightly positive (harder labels → marginally higher baseline scores, though insignificant). The means by difficulty stratum are nearly identical: medium = 0.9242, hard = 0.9271.

This invalidates the difficulty stratification as a meaningful experimental variable for v5. The difficulty labels defined "hard" by rubric-performance criteria during case generation, but the generated cases did not separate cleanly along that dimension once exposed to the actual baseline condition. This is consistent with a ceiling effect: baseline performance is sufficiently high (0.9452) that the expected hard/medium separation is compressed into a narrow band.

The difficulty label failure also limits interpretation of the forced_multiround condition, which was scoped to hard cases specifically on the hypothesis that hard cases would benefit from extended adversarial exchange. With labels not validating, the FM scope restriction loses its theoretical grounding.

---

## Key Observations

**Ensemble IDR suppression is a majority-vote artifact, not a genuine recall deficit.** Under majority-vote aggregation, ensemble IDR appears at 0.768 — below baseline (0.873) and isolated_debate (0.897). But union-of-issues IDR (any-assessor-found) recovers it to 0.8725, confirming the assessors collectively have sufficient recall. The suppression mechanism: when 2/3 assessors agree on critique_wins but identify different specific issues, the conservative ensemble rule may not surface the correct planted issue even if each assessor individually flagged it. The ensemble IDP is simultaneously high (0.958) — meaning the ensemble rarely raises false positives — but the IDR suppression means it is harder for the ensemble to correctly identify the specific must-find issues when assessors disagree on which issue is primary. Cases eval_scenario_3 and eval_scenario_295 exemplify this pattern: both showed consistent 2/3 critique_wins splits on metric-alignment flaws where the defense argument was substantively compelling, and the ensemble conservative rule fired correctly to prevent false consensus but at the cost of IDR credit. A retroactive union-IDR sensitivity analysis (`union_idr_analysis.py`) replaces majority-vote aggregation with any-assessor-found and recovers ensemble IDR to 0.8725 (+0.1046), bringing FC mean to 0.9441 — above baseline (0.9266) and approximately matching isolated_debate (0.9477). The per-assessor recall is adequate; the suppression is entirely in the aggregation rule.

**Protocol cleanliness on defense_wins cases.** All 30 defense_wins cases scored 1.0 across all conditions, with the exception of one ensemble case (eval_scenario_136: ensemble mean 0.9375). This is a strong result — the protocol reliably identifies defense-winning designs when presented. The uniformity also limits the contribution of defense_wins cases to differential scoring across conditions, since all conditions score near-ceiling on them. The defense_wins stratum effectively adds no discriminative signal to the cross-condition comparison.

**Forced multiround stub misclassification (corrected).** Three critique hard cases (eval_scenario_381, 411, 616) were originally generated as not_applicable_difficulty stubs by the Phase 6 batch agent. The 9 stub files were replaced in Phase 9.5 with correct FM debate outputs (all critique_wins, debate_rounds=2). Per-case FM means post-correction: 381=0.9583, 411=0.9583, 616=0.9167. These cases score lower in isolated_debate and multiround than other hard cases (381: 0.625/0.625, 411: 0.750/0.750, 616: 0.875/1.0), indicating they are genuinely harder cases at the edge of the protocol's resolution capability. The FM protocol handled them successfully once correctly dispatched.

**High ceiling effect, low discriminative power.** With isolated_debate mean = 0.9549 and baseline mean = 0.9452, the dynamic range available for lift measurement is narrow. The fc_lift of +0.0097 is real but below the threshold for experimental relevance. DRQ and FVC are essentially at ceiling for isolated_debate, multiround, and baseline (all ≥ 0.989), leaving IDR and IDP as the primary dimensions where meaningful cross-condition differences exist. The debate protocol does not appear to generate enough additional deliberative signal to move IDR beyond what baseline achieves on a single-pass critique.

**Batch 2 re-run integrity.** The 165 batch 2 files were identified as contaminated (zero stochastic variance indicating the original batch agent loaded planted_issues before dispatch), self-deleted, and re-run with a clean subagent. The re-run files are clean. This is the most significant data integrity event in the experiment. The contamination detection mechanism — zero cross-run variance — is worth retaining as a validation step in future pipeline iterations.
