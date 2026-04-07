# Real-Paper Cases × Haiku Smoke Test

**Date:** 2026-04-07  
**Model:** claude-haiku-4-5 (single pass, no role, no structure)  
**Cases:** 14 real-paper hard cases (`eval_scenario_101`–`eval_scenario_114`)  
**Purpose:** Pre-experiment ceiling check — verify real-paper cases are not too easy for the acceptance-criterion model  
**Artifact type:** Ephemeral diagnostic — not a Phase 5.5 run; no INVESTIGATION_LOG entries written

---

## Method

Each case received a single Haiku dispatch with only the `task_prompt` and a generic methodology-review wrapper. No must_find_issue_ids, scoring_targets, ground_truth, or planted_issues were shown to the model.

Each response scored on three binary dimensions:

| Dimension | Criterion |
|-----------|-----------|
| **IDR** | Did the response surface ALL `must_find_issue_ids`? For defense_wins cases (must_find=[]), IDR=1 automatically. |
| **IDP** | Was at least one issue described with substantive correctness (correct mechanism, not just naming the concern)? For defense_wins cases, IDP=1 if the response correctly avoids inventing fatal flaws that aren't there. |
| **FVC** | Is the response's overall assessment consistent with `acceptable_resolutions`? |

Per-case mean = (IDR + IDP + FVC) / 3.

---

## Results

| Case ID | IDR | IDP | FVC | Mean | Category | Notes |
|---------|:---:|:---:|:---:|:----:|----------|-------|
| eval_scenario_101 | 1 | 1 | 1 | **1.00** | broken_baseline | All 3 must_find found; site-shortcut mechanism + pooled internal validation conflation both identified correctly |
| eval_scenario_102 | 1 | 1 | 1 | **1.00** | broken_baseline | All 4 must_find found; full-dataset feature-selection leakage and CV-tuning-loop optimism both identified explicitly |
| eval_scenario_103 | 1 | 1 | 1 | **1.00** | real_world_framing | Fold-level SE inflation identified; algorithm-average-vs-deployed-model distinction captured; staffing overreach flagged |
| eval_scenario_104 | 1 | 1 | 1 | **1.00** | hidden_confounding | Age confound, saliency consistent with aging shortcut, and confounded screening claim — all 3 found |
| eval_scenario_105 | 1 | 1 | 1 | **1.00** | scope_intent_misunderstanding | Pubertal confound identified; restricted-subgroup performance drop correctly flagged as diagnostic rather than noise |
| eval_scenario_106 | 1 | 1 | 1 | **1.00** | metric_mismatch | Global MAE masking subgroup error found; sex-as-input ≠ equity proof flagged; directional audit requirement identified |
| eval_scenario_107 | 1 | 1 | 1 | **1.00** | broken_baseline | Spatial autocorrelation in tile split identified; augmentation-cannot-fix-dependence-bias noted; reserve holdout needed |
| eval_scenario_108 | 1 | 1 | 1 | **1.00** | defense_wins | Correctly defended spatial block validation as sound; identified only one minor gap (seasonal variation) without overreaching |
| eval_scenario_109 | 1 | 1 | 1 | **1.00** | scope_intent_misunderstanding | Location-feature geographic memorization found; random CV as reproduction-not-transfer identified; capital-planning scope overreach flagged |
| eval_scenario_110 | 1 | 1 | 1 | **1.00** | metric_mismatch | Slide-level metric cannot validate region-level biology; subtype proxies as alternative explanation; cross-site ≠ mechanism — all 3 found |
| eval_scenario_111 | 1 | 1 | 1 | **1.00** | hidden_confounding | Single-draw layout leaving phenotype-plate correlation; batch correction cannot guarantee deconfounding; PCA cleanup circularity — all 3 found |
| **eval_scenario_112** | 1 | **0** | **0** | **0.33** | defense_wins | **FAIL**: Haiku misread sound pre-measurement layout optimization as "p-hacking risk" and recommended rejection. Correct verdict: defense_wins (prospective optimization to reduce confounding is legitimate methodology). |
| eval_scenario_113 | 1 | 1 | 1 | **1.00** | hidden_confounding | Complete phenotype-batch confound identified; missing concurrent references flagged; post-correction PCA and CV circularity both called out |
| eval_scenario_114 | 1 | 1 | 1 | **1.00** | scope_intent_misunderstanding | Ratio-based approach correctly defended as sound in principle; issued conditional approval with operational refinements; did not invent fatal flaws |

---

## Aggregate Statistics

| Metric | Value |
|--------|-------|
| Overall mean (14 cases) | **0.952** |
| Critique/mixed cases mean (101–111, 113; n=11) | **1.000** |
| Defense_wins cases mean (108, 112, 114; n=3) | **0.778** |
| Cases scoring mean ≥ 0.55 | **13 / 14 (93%)** |
| Cases scoring mean < 0.55 | **1 / 14 (7%)** |

---

## Phase 5.5 Gate Comparison

Phase 5.5 acceptance criterion: **≥6/10 hard cases must score mean < 0.55** for the case batch to be considered appropriately difficult.

Applied here (14 cases): only **1/14 (7%)** scored below the 0.55 ceiling.

**Gate result: FAIL** — The real-paper cases are too easy for Haiku.

---

## Observations

### 1. Critique cases were essentially trivial for Haiku
All 11 critique/mixed cases scored perfect (1.00). The flaw mechanisms — data leakage, confounding, metric mismatch, spatial autocorrelation — appear close enough to the surface that Haiku identifies them in a single unstructured pass. This is the same ceiling pattern that halted v4 after Phase 7.

### 2. Defense_wins cases are where difficulty concentrates
Case 112 is the only failure. Haiku could not resist flagging the optimized-layout design as suspicious ("p-hacking risk") when the correct reading is that prospective optimization before measurement, with documented seeds and locked-in design, is sound methodology. Cases 108 and 114 were handled correctly because their defenses are operationally more intuitive.

### 3. The real-paper supplement does not function as a hard tier
Despite being grounded in documented real-world failures and designed to resist single-pass review, all critique cases were cracked. If Haiku scores ~0.95 mean, Sonnet will likely approach 1.0 across all 14, making fc_lift on the real-paper supplement uninformative.

### 4. Root cause hypothesis
The flaw mechanisms in the real-paper cases are well-established ML pitfalls (data leakage, confounding, spatial autocorrelation, metric mismatch). Haiku has likely been trained on many descriptions of exactly these failure modes. The difficulty may require cases where the flaw is *not* a named, recognized pitfall but a more contextual or domain-specific reasoning failure — the 4 flaw types (assumption violations, quantitative errors, critical omissions, wrong justifications) do not appear to provide sufficient camouflage at this complexity level.

---

## Implications for v5 Experiment Design

1. **Phase 5.5 will likely trigger the calibration concern branch.** If Haiku scores 0.95+ on the real-paper supplement during the actual difficulty gate, the gate will flag ceiling effect before Phase 6 begins.

2. **fc_lift on real-paper cases may be near zero.** If baseline already scores near 1.0, there is no headroom for debate conditions to improve performance.

3. **Consider separating real-paper cases in analysis.** It may be worth pre-registering that real-paper cases (eval_scenario_1xx) are analyzed as a separate stratum in Phase 8, with the expectation that this stratum shows ceiling effects.

4. **Case revision may be needed before Phase 6.** If the Phase 5.5 gate confirms this ceiling, case revision or additional harder supplements should be prioritized before running the full benchmark.

---

*Smoke test run 2026-04-07. No INVESTIGATION_LOG entries written. No benchmark_cases.json or v5_raw_outputs/ artifacts created.*
