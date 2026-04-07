# Real-Paper Cases × Haiku Smoke Test — V2

**Date:** 2026-04-07
**Model:** claude-haiku-4-5 (single pass, no role, no structure)
**Cases:** 14 revised real-paper cases (`eval_scenario_201`–`eval_scenario_214`)
**Source file:** `synthetic-candidates/real_paper_cases.json`
**Purpose:** Post-revision ceiling check — verify revised real-paper cases are harder for Haiku than the original 1xx batch
**Artifact type:** Ephemeral diagnostic — not a Phase 5.5 run; no INVESTIGATION_LOG entries written

---

## Context

The original smoke test (`REAL_PAPER_CASES_SMOKE_TEST.md`) ran against `eval_scenario_101`–`114` and found all 11 critique/mixed cases scored 1.00 mean (ceiling effect). Only 1/14 cases scored below the Phase 5.5 acceptance threshold of 0.55. Root cause: flaw mechanisms existed silently with no stated justification, decoys were not prominent, and all must_find issues were locatable to a single paragraph.

The `REAL_PAPER_CASE_GENERATION_PROMPT.md` was revised with four Critique Case Design Requirements and four Defense_Wins Case Design Requirements. `benchmark_case_generation_prompt.md` received matching updates. This smoke test verifies the revised 2xx cases are harder.

**Key structural changes in 2xx cases (verified from JSON):**
- All 9 critique/mixed cases: `addressed_but_incorrectly: 1`, `compound: 1` (design requirements satisfied)
- All 5 defense_wins cases: `must_not_claim` has 3 entries each (multi-evidence false concern structure)
- Distribution: 9 critique/mixed (broken_baseline ×2, metric_mismatch ×2, hidden_confounding ×2, scope_intent_misunderstanding ×2, real_world_framing ×1) + 5 defense_wins

---

## Method

Each case received a single Haiku dispatch with only the `task_prompt` and a generic methodology-review wrapper. No must_find_issue_ids, scoring_targets, ground_truth, or planted_issues were shown to the model.

Each response scored on three binary dimensions:

| Dimension | Criterion |
|-----------|-----------|
| **IDR** | Did the response surface ALL `scoring_targets.must_find_issue_ids`? For defense_wins cases (must_find=[]), IDR=1 automatically. |
| **IDP** | Was at least one issue described with substantive correctness (correct mechanism, not just naming the concern)? For defense_wins cases, IDP=1 if the response correctly avoids inventing fatal flaws that aren't there. |
| **FVC** | Is the response's overall assessment consistent with `scoring_targets.acceptable_resolutions`? |

Per-case mean = (IDR + IDP + FVC) / 3.

---

## Results

| Case ID | IDR | IDP | FVC | Mean | Category | Notes |
|---------|:---:|:---:|:---:|:----:|----------|-------|
| eval_scenario_201 | 1 | 1 | 1 | **1.00** | broken_baseline | Asymmetric tuning, threshold optimization asymmetry, and baseline freeze all identified with correct mechanisms |
| eval_scenario_202 | 1 | 1 | 1 | **1.00** | metric_mismatch | Traffic-weighted masking, category error in cross-population evidence, global launch overreach — all found |
| eval_scenario_203 | 1 | 1 | 1 | **1.00** | hidden_confounding | Informative censoring mechanism, right-censoring explanation error, holdout optimism — all three found with correct mechanisms |
| eval_scenario_204 | 1 | 1 | 1 | **1.00** | scope_intent_misunderstanding | Quality filter on both splits, label validity defense misstates what is measured, scope mismatch — all found |
| eval_scenario_205 | 1 | 1 | 1 | **1.00** | defense_wins | Correctly defended prospective holdout and tail-stability criterion; no false fatal flaws invented |
| **eval_scenario_206** | 1 | **0** | **0** | **0.33** | **defense_wins** | **FAIL**: Invented 8 flaws (dataset size, no held-out external test, no confidence intervals, no class-imbalance mitigation); verdict "insufficient evidence for deployment" — correct verdict is defense_wins (nested CV + stability criterion are sound for this dataset size and use case) |
| **eval_scenario_207** | 1 | **0** | **0** | **0.33** | **defense_wins** | **FAIL**: Invented 7 flaws (scope narrowed post-hoc, out-of-time validation absent, no disparate-impact test, monitoring lacks enforcement); verdict "does not support stated conclusion" — correct verdict is defense_wins (branch-only scope was pre-committed, exclusion is not opportunistic) |
| **eval_scenario_208** | 1 | **0** | **0** | **0.33** | **defense_wins** | **FAIL**: Invented 6 flaws (worst-plant metric suppresses performance artificially, holdout insufficient, pooled metric undermines governance claim); verdict "cannot be judged sound" — correct verdict is defense_wins (worst-plant criterion is the right statistic for cross-plant deployment claim) |
| **eval_scenario_209** | 1 | **0** | **0** | **0.33** | **defense_wins** | **FAIL**: Invented 8 flaws (no external test set, no CI on balanced accuracy, no class-imbalance specification, stability metric unquantified); verdict "material gaps between honest in-sample fit and deployment readiness" — correct verdict is defense_wins (nested CV + stability preference are correct for 410-coupon dataset) |
| eval_scenario_210 | 1 | 1 | 1 | **1.00** | broken_baseline | Baseline not reoptimized for current feature space, live-workflow argument overreaches, search and threshold asymmetry — all found |
| eval_scenario_211 | 1 | 1 | 1 | **1.00** | metric_mismatch | Calibration fit/eval share same block, held-out-from-base-model doesn't confer independence, best curve selected on its own grading sample — all found |
| eval_scenario_212 | 1 | 1 | 1 | **1.00** | hidden_confounding | Spend proxy varies by territory access, operational spend defense is wrong for need claim, division-wide claim exceeds proxy validity — all found |
| eval_scenario_213 | 1 | 1 | 1 | **1.00** | scope_intent_misunderstanding | Static leave-one-click-out measures reconstruction not future behavior, next-article simulation claim wrong, contact deflection claim exceeds offline evidence — all found |
| eval_scenario_214 | 1 | 1 | 1 | **1.00** | real_world_framing | Intervention-shaped labels, finance-cares defense circular, policy redesign claim exceeds residual-loss prediction evidence — all found |

---

## Aggregate Statistics

| Metric | Value |
|--------|-------|
| Overall mean (14 cases) | **0.810** |
| Critique/mixed cases mean (201–204, 210–214; n=9) | **1.000** |
| Defense_wins cases mean (205–209; n=5) | **0.467** |
| Cases scoring mean < 0.55 | **4 / 14 (29%)** |
| Cases scoring mean ≥ 0.55 | **10 / 14 (71%)** |

---

## Comparison to Original 1xx Batch

| Metric | V1 (101–114) | V2 (201–214) | Delta |
|--------|:---:|:---:|:---:|
| Overall mean | 0.952 | 0.810 | −0.142 |
| Critique/mixed mean | 1.000 | 1.000 | 0 |
| Defense_wins mean | 0.778 | **0.467** | **−0.311** |
| Cases scoring < 0.55 | 1/14 (7%) | **4/14 (29%)** | +3 cases |

---

## Phase 5.5 Gate Comparison

Phase 5.5 acceptance criterion: **≥6/10 hard cases must score mean < 0.55** for the case batch to be considered appropriately difficult.

Applied here (14 cases, all hard): only **4/14 (29%)** scored below the 0.55 ceiling.

**Gate result: FAIL** — Real-paper cases are still too easy for Haiku as a batch. However, the failure mode has shifted compared to V1.

---

## Observations

### 1. Defense_wins cases are now effective — 4/5 below ceiling

Cases 206–209 all scored 0.33. The new Defense_Wins Case Design Requirements (multi-evidence false concern, external knowledge required for exoneration, diversified flaw types) successfully induced false critique from Haiku. Haiku invented novel governance and validation concerns not present in the memos — exactly the failure mode the requirements were designed to produce.

Case 205 was the only defense_wins pass (1.00). Haiku correctly recognized the prospective temporal holdout as methodologically sound without inventing false flaws — suggesting case 205 may be insufficiently challenging or that its defense is more operationally intuitive than 206–209.

### 2. Critique/mixed cases remain at perfect ceiling — 0/9 below threshold

All 9 critique/mixed cases scored IDR=1.00 despite the addressed_but_incorrectly and compound requirements. Haiku reads the full task_prompt and still locates all must_find mechanisms in a single pass. The structural improvements (one issue explicitly discussed with a wrong justification, one issue requiring cross-paragraph combination) do not prevent surface-level pattern matching from surfacing all flaws.

**Why the addressed_but_incorrectly pattern did not help:** Haiku identifies the must_find mechanism correctly regardless of whether the memo's justification for it is right or wrong. IDR scores presence of the concern, not evaluation of the justification quality. The addressed_but_incorrectly design requirement was intended to make IDP harder (requiring evaluation of justification correctness), but since IDR=1 across all critique cases, IDP is also 1 automatically — the IDP criterion only penalizes missed or wrong mechanisms, not insufficient justification critique.

**Why compound issues did not help:** The task_prompts are short enough (4 paragraphs) that Haiku reads the whole document in one pass. Compound issues requiring combination of paragraphs 1 and 3 do not meaningfully impede a full-document reader.

### 3. Gate failure is entirely driven by the critique/mixed stratum

If the gate were applied only to defense_wins cases: **4/5 (80%)** pass. If applied only to critique/mixed: **0/9 (0%)** pass. The ceiling effect is category-specific, not a uniform property of the case batch.

### 4. Root cause hypothesis for critique ceiling

The flaw mechanisms in the critique/mixed cases (asymmetric tuning, informative censoring, calibration circularity, proxy validity, static reconstruction) are well-established ML pitfalls that Haiku has likely encountered in training. The compound and addressed_but_incorrectly structures add friction at the IDP level (justification evaluation) but do not block IDR. Haiku's IDR=1 on critique cases likely reflects broad flaw-type recognition, not careful per-paragraph reasoning.

---

## Implications

1. **Phase 5.5 will trigger gate failure on critique/mixed cases.** If Haiku scores 1.00 on all critique/mixed cases during the formal gate, Phase 5.5 will flag ceiling effect before Phase 6.

2. **Defense_wins improvement is real and should be preserved.** The 4 new defense_wins failures represent a genuine difficulty improvement. The defense_wins stratum is now calibrated well for Haiku.

3. **fc_lift on critique/mixed real-paper cases may still be near zero.** If baseline already scores 1.00, there is no headroom for debate to improve performance in that stratum.

4. **Consider stratum-specific analysis pre-registration.** The clean separation (critique=ceiling, defense_wins=hard) suggests pre-registering separate fc_lift estimates for critique vs. defense_wins strata in Phase 8 CONCLUSIONS.md.

5. **Critique case hardening may require domain-obscurity, not structural complexity.** The domain-knowledge-gated requirement (Critique Requirement 4, ≥2 cases per batch) may be the highest-leverage remaining lever — cases where the flaw requires external literature knowledge, not just reading the memo. None of the 2xx critique cases were explicitly gated on domain knowledge in a way that blocked Haiku; future generation should prioritize this requirement more aggressively.

---

*Smoke test run 2026-04-07. No INVESTIGATION_LOG entries written. No benchmark_cases.json or v5_raw_outputs/ artifacts created.*
