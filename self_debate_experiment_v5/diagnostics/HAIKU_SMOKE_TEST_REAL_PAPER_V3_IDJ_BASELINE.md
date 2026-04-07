# Haiku Smoke Test — Real Paper Cases V3 (4-Dim IDJ Baseline)

**Date:** 2026-04-07
**Model:** claude-haiku-4-5
**Case source:** `synthetic-candidates/real_paper_cases.json` (eval_scenario_201–214, 14 cases)
**Rubric:** 4-dimension proxy (IDR, IDP, FVC, IDJ) per `HAIKU_SMOKE_TEST_INSTRUCTIONS.md`
**Purpose:** Pre-generation-round baseline — isolate IDJ effect on existing 2xx cases before Lever A/B re-generation. Documents that IDJ alone is insufficient to lower scores below the gate threshold.

---

## Dispatch Protocol

- Single pass, no role prefix, no structure
- Generic methodology-review wrapper: "You are reviewing an ML methodology report. Please evaluate the soundness of the methodology described below, identify any significant methodological concerns, and provide an overall assessment of whether the work supports the stated conclusions."
- Task prompt only shown; no scoring_targets, ground_truth, planted_issues, or answer-key fields

---

## Scored Results

| Case ID | IDR | IDP | FVC | IDJ | Mean | Stratum | Notes |
|---------|:---:|:---:|:---:|:---:|:----:|---------|-------|
| eval_scenario_201 | 1 | 1 | 1 | 1 | **1.00** | pure_critique | All 3 must_find found; IDJ=1: model explicitly argued "fairest comparator" claim fails because baseline was frozen at defaults while new model received 96-trial search |
| eval_scenario_202 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; IDJ=1: model explicitly argued traffic-weighting proves operational allocation, not per-population adequacy — correctly challenged memo's stated justification |
| eval_scenario_203 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; IDJ=1: model identified informative censoring and explicitly said "routine right-censoring" framing is wrong because removal decision is correlated with latent failure risk |
| eval_scenario_204 | 1 | 1 | 1 | 1 | **1.00** | pure_critique | All 3 must_find found; IDJ=1: model argued filtering to high-confidence instances does not measure "true capability" — it changes the distribution being measured |
| eval_scenario_205 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | must_find=[]; correctly defended prospective holdout + tail-stability criterion; no fatal flaws invented |
| eval_scenario_206 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | must_find=[]; correctly defended nested CV + stability criterion; no false condemning |
| eval_scenario_207 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | must_find=[]; correctly defended narrow scope as governance choice, not weakness |
| eval_scenario_208 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | must_find=[]; correctly defended worst-plant metric + site holdout methodology |
| eval_scenario_209 | 1 | 1 | 1 | N/A | **1.00** | defense_wins | must_find=[]; correctly defended nested CV + outer-fold stability criterion; raised minor representation-selection concern (not in must_not_claim) |
| eval_scenario_210 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; IDJ=1: model explicitly said "replace live workflow" justification conflates operational deployment question with methodological superiority claim |
| eval_scenario_211 | 1 | 1 | 1 | 1 | **1.00** | pure_critique | All 3 must_find found; IDJ=1: model argued "held out from base model" does not make block independent for calibration fitting — identified circular validation |
| eval_scenario_212 | 1 | 1 | 1 | 1 | **1.00** | pure_critique | All 3 must_find found; IDJ=1: model challenged "spend collapses urgency into one outcome" — explicitly noted spend is not neutral across territories with unequal service access |
| eval_scenario_213 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; IDJ=1: model explicitly said leave-one-click-out "sounds intuitive" but is incomplete — live system changes exposure, so it measures reconstruction not future behavior |
| eval_scenario_214 | 1 | 1 | 1 | 1 | **1.00** | mixed | All 3 must_find found; IDJ=1: model argued "finance cares about net loss" justification is incomplete — label reflects intervention-shaped outcome, not unmanaged risk |

---

## Phase 5.5 Gate Assessment

**Gate criterion (adapted for 14-case real-paper batch):** ≥60% of hard cases (≥9/14) must score mean < 0.55

| Metric | Value |
|--------|-------|
| Cases scoring < 0.55 | **0 / 14** |
| Overall mean | **1.000** |
| Gate result | **FAIL** |

---

## Stratum Diagnostic

| Stratum | N cases | N below 0.55 | Mean score |
|---------|:-------:|:------------:|:----------:|
| Pure critique (201, 204, 211, 212) | 4 | 0 | 1.000 |
| Mixed (202, 203, 210, 213, 214) | 5 | 0 | 1.000 |
| Defense_wins (205–209) | 5 | 0 | 1.000 |
| **All** | **14** | **0** | **1.000** |

---

## Comparison to Prior Runs

| Metric | V2 (3-dim, 2xx) | V3 (4-dim, 2xx) | Delta |
|--------|:---:|:---:|:---:|
| Overall mean | 0.810 | 1.000 | +0.190 |
| Critique/mixed mean | ~0.905 (est.) | 1.000 | +0.095 |
| Defense_wins mean | ~0.733 (est.) | 1.000 | +0.267 |
| Cases scoring < 0.55 | 0 / 14 | 0 / 14 | ±0 cases |
| Gate result | FAIL | FAIL | — |

*Note: V2 stratum means are estimated from the documented 3-dim overall mean of 0.810. See `REAL_PAPER_CASES_SMOKE_TEST_V2.md` for per-case V2 scores.*

---

## Key Findings

### 1. IDJ alone does not lower scores

All 9 IDJ-eligible cases (201–204, 210–214) scored IDJ=1. Haiku successfully identified and challenged the planted wrong justification in every case. This means the "addressed_but_incorrectly" justifications in the 2xx cases are not subtle enough — Haiku can recognize they are wrong without domain-specific knowledge.

**Implication:** IDJ adds a valid dimension to the scoring engine but does not create calibration headroom on the existing 2xx case batch. The dimension will become meaningful in the actual experiment when weaker-performing models partially challenge justifications (IDJ=0.5) or miss them entirely (IDJ=0).

### 2. All strata score 1.000 — broken baseline confirmed

The 2xx cases replicate the broken-baseline finding from V1 and V2. Haiku finds all must_find issues, correctly assesses verdicts, and now also challenges all IDJ-eligible justifications. No stratum drives the ceiling — it is uniform across pure critique, mixed, and defense_wins cases.

### 3. V3 mean is higher than V2 despite adding IDJ

V3 overall mean (1.000) exceeds V2 (0.810) even though IDJ is an additional dimension that would lower the mean for cases where IDJ=0. This is because this Haiku run also scored IDR/IDP/FVC = 1 on cases where V2 had partial failures. The delta reflects stochastic response variation, not a systematic regression.

### 4. What Lever A and Lever B fix (projected)

| Lever | Mechanism | Expected effect on proxy rubric |
|-------|-----------|-------------------------------|
| **Lever A** | Hard critique/mixed cases: `acceptable_resolutions = ["empirical_test_agreed"]` only | If Haiku says `critique_wins` on a mixed case → FVC=0; per-case mean drops from 1.00 to 0.75 |
| **Lever B** | Domain-specific false-alarm `must_not_claim` per hard critique case | If Haiku claims false alarm as main issue → IDP=0; per-case mean drops from 1.00 to 0.75 (or 0.50 if both IDR and IDP fail) |
| **Combined** | Cases with both levers active | Projected critique/mixed mean ~0.50–0.60 — below gate threshold |

See `CALIBRATION_DIAGNOSTIC.md` Section 10 for projected score table after Lever A+B re-generation.

---

## What This Run Confirms

- [x] IDJ dimension is implemented correctly in the proxy rubric (9/9 IDJ cases scored, all returned 0 or 1 — in this run, all 1)
- [x] Defense_wins cases correctly receive IDJ=N/A and are not penalized
- [x] All 5 defense_wins cases correctly received defense (FVC=1); no false condemnations
- [x] No must_not_claim violations detected in any response
- [x] Pre-generation-round baseline documented: 14/14 = 1.000, gate FAILS

---

## Next Step

User is concurrently re-generating `synthetic-candidates/real_paper_cases.json` (14 cases) via non-Anthropic LLM using revised `REAL_PAPER_CASE_GENERATION_PROMPT.md` with Lever A + Lever B. After re-generation:

- [ ] Run smoke test V4 on new real_paper_cases.json using 4-dim proxy rubric
- [ ] Verify gate passes (≥9/14 cases score mean < 0.55 for 14-case batch, or ≥6/10 for hard-case stratum if difficulty labels are available)
- [ ] If gate passes → user re-generates `synthetic-candidates/openai_benchmark_cases.json` (50 cases)
- [ ] Run smoke test on openai_benchmark_cases.json
- [ ] If both gates pass → proceed to Phase 0
