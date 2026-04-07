# V5 Calibration Diagnostic

**Date:** 2026-04-07
**Context:** Post-smoke-test analysis of real-paper case batch v2 (eval_scenario_201–214).
**Purpose:** Memorializes design decisions, rubric analysis, and option tradeoffs before Phase 0 commit.

---

## 1. Starting Point — Smoke Test V2 Results

After revising both generation prompts with Critique Case Design Requirements (addressed_but_incorrectly, decoy dominance, compound issues, domain-knowledge-gated) and Defense_Wins Case Design Requirements (multi-evidence false concern, external knowledge for exoneration, diversified flaw types, calibrated ideal_defense), the Haiku smoke test on the new 2xx batch returned:

| Stratum | Cases | Cases < 0.55 | Mean |
|---|:---:|:---:|:---:|
| Critique/mixed | 9 | 0 | 1.000 |
| Defense_wins | 5 | 4 | 0.467 |
| **All** | **14** | **4** | **0.810** |

**Phase 5.5 gate: FAIL** — criterion is ≥6/10 hard cases scoring < 0.55.

Defense_wins improvement was real: 4 of 5 defense_wins cases (206–209) scored 0.33, down from 0.78 mean in the original 1xx batch. Cases 206–209 all involved nested CV, worst-plant metrics, branch-only scope, or stability-based model selection — sound methodology patterns that Haiku incorrectly condemned.

Critique/mixed ceiling persisted at 1.00: all 9 cases found all must_find issues in a single pass despite addressed_but_incorrectly, compound, and decoy structure.

---

## 2. First Options Pass — What Could Move Critique Cases Below 0.55

Five options identified before examining the rubric:

**A — Tighten IDP (no generation round)**
Change IDP criterion for addressed_but_incorrectly cases to require the model to identify that the stated justification is wrong. Would require updating scoring infrastructure.

**B — Add a 4th dimension IDJ (justification evaluation)**
Introduce IDJ=1 if model correctly rejects the team's stated defense for an addressed_but_incorrectly issue. Separates "found concern" from "evaluated defense." Largest rubric change.

**C — FVC manipulation via must-not-claim verdicts**
Design critique cases where the only acceptable resolution is `empirical_test_agreed`, and Haiku incorrectly says `critique_wins` (overclaims). FVC=0 even when IDR=1.

**D — Stratum-specific gate**
Replace global ≥6/10 gate with separate gates for defense_wins and critique strata. Defense_wins already passes (4/5). Doesn't fix the fc_lift power problem on critique cases.

**E — Pre-register stratum separation, accept ceiling**
Don't change gates or rubric. Pre-register that real-paper cases are analyzed as two strata (critique vs. defense_wins) with the critique stratum expected to show ceiling effects. Defense_wins fc_lift is the primary signal.

---

## 3. IDP Definition Mismatch — Two Incompatible Definitions

Examining the scoring engine revealed that **the Phase 5.5 inline IDP definition and the actual experiment IDP are fundamentally different metrics.**

### Phase 5.5 inline definition (from `phase_05_5_difficulty_gate.md`)

> "Was at least one issue description substantively correct?"

Binary qualitative judgment. Measures mechanism quality.

### Actual experiment IDP (from `self_debate_poc.py:53–66`)

```python
def compute_idp(all_issues_raised, must_find_ids, must_not_claim):
    invalid = [i for i in all_issues_raised if i in must_not_claim]
    valid   = [i for i in all_issues_raised if i in must_find_ids]
    frac = len(valid) / (len(valid) + len(invalid))   # if denominator > 0
    # ≥0.9 → 1.0 | ≥0.5 → 0.5 | else → 0.0
```

**IDP is a false-alarm precision metric.** It answers: of the issues the model flagged that matched either `must_find_ids` or `must_not_claim`, what fraction were legitimate?

Issues that don't match either lookup list are invisible — denominator stays 0, IDP=1.0 free pass.

### Implications

- The `addressed_but_incorrectly` design pattern has zero effect on actual experiment IDP. The engine cannot measure justification quality — it only checks ID presence against lookup lists.
- IDP < 1.0 on critique cases requires the model to raise `must_not_claim` false alarms. Haiku currently resists all three decoys per case → IDP stays 1.0.
- The Phase 5.5 gate (using the qualitative binary IDP) is a **proxy rubric**, not the actual experiment rubric. The two are structurally different.
- For defense_wins cases: IDR=None, IDP=None — scoring uses only DRQ and FVC. The smoke test proxy (IDR=1 auto, IDP scored on "no fatal flaws invented") approximates but does not match the engine.

---

## 4. Scoring Engine Deep Dive — Actual Defense_Wins and Mixed Case Scores

### Defense_wins cases in the engine

For `correct_position == 'defense'`: IDR=None, IDP=None, DC=None, ETD=None (ETD also None because `ideal_resolution='defense_wins'` triggers early return). **Only DRQ and FVC contribute.**

| Model verdict | DRQ | FVC | Engine mean | Smoke test mean |
|---|:---:|:---:|:---:|:---:|
| `defense_wins` | 1.0 | 1.0 | **1.00** | 1.00 |
| `critique_wins` | 0.0 | 0.0 | **0.00** | 0.33 |
| `empirical_test_agreed` | 0.5 | 0.5 | **0.50** | ~0.67 |

The actual experiment is more punishing for incorrect defense_wins verdicts (0.00 vs. 0.33 in smoke test). Defense_wins cases 206–209 would score 0.00 at baseline, not 0.33.

### Mixed cases in the engine

Cases 202, 203, 210, 213, 214 have `ideal_type=empirical_test_agreed`, `acceptable=['empirical_test_agreed', 'critique_wins']`. Haiku said `critique_wins` on all five.

For baseline (ETD=None, DC=None):

| Dim | Value | Reason |
|---|:---:|---|
| IDR | 1.0 | All must_find found |
| IDP | 1.0 | No must_not_claim raised |
| DRQ | **0.5** | `critique_wins` in acceptable but ≠ ideal |
| ETD | None | N/A for baseline |
| FVC | 1.0 | `critique_wins` in acceptable |
| **Mean** | **0.875** | (1+1+0.5+1) / 4 |

**The smoke test showed 1.00 for mixed cases — the actual engine scores 0.875.** The DRQ penalty for a good-but-not-ideal verdict is invisible in the proxy rubric.

### Projected actual-engine baseline scores

| Case | Type | Engine mean | Smoke test mean |
|------|------|:---:|:---:|
| 201, 204, 211, 212 | Pure critique | 1.000 | 1.000 |
| 202, 203, 210, 213, 214 | Mixed | **0.875** | 1.000 |
| 205 | defense_wins (correct) | 1.000 | 1.000 |
| 206, 207, 208, 209 | defense_wins (fail) | **0.000** | 0.333 |
| **Real-paper batch mean** | | **0.634** | 0.810 |

Cases below 0.55 in actual engine: **4/14** (same count, but the failing cases score 0.00 not 0.33).

### fc_lift opportunity by stratum

| Stratum | Baseline | Ceiling | Max fc_lift | Mechanism |
|---|:---:|:---:|:---:|---|
| Defense_wins (206–209) | 0.00 | 1.00 | **+1.00/case** | Isolated debate: Defender argues sound methodology → orchestrator rules defense_wins |
| Mixed (5 cases) | 0.875 | 1.00 | +0.125/case | Debate reaches empirical_test_agreed verdict + correct ETD |
| Pure critique (4 cases) | 1.00 | 1.00 | **0** | Ceiling — no headroom |

Expected fc_lift if isolated_debate correctly handles 206–209 and pushes mixed cases to ideal verdict: (4 × 1.00 + 5 × 0.125) / 14 = **+0.33** per case — well above the +0.10 H1 threshold, and driven entirely by defense_wins.

---

## 5. Key Finding — Gate Failure vs. fc_lift Opportunity Are Separate Problems

The Phase 5.5 gate failing (4/14 below 0.55) is a calibration check that asks: "are these cases appropriately hard at baseline?" The answer for the real-paper supplement is: **hard in the defense_wins stratum, ceiling in the critique stratum.**

The gate was designed for a batch where difficult cases are hard because of subtlety in all categories. The 2xx batch has a bimodal distribution: critique cases all ceiling, defense_wins cases all floor. The gate threshold doesn't map cleanly to this distribution.

The fc_lift opportunity is **substantial** — concentrated in defense_wins and partially in mixed. The experiment has genuine signal even though the gate fails.

**The gate failure is a gate calibration problem, not an experiment validity problem.**

---

## 6. Open Decisions (as of 2026-04-07)

The following decisions remain open before Phase 0 commit:

1. **Gate adjustment:** Accept gate failure + proceed with documentation, adjust threshold to match bimodal distribution, or add stratum-specific sub-gates?

2. **Pre-registration:** Pre-register stratum-specific fc_lift analysis before Phase 6 to protect against post-hoc rationalization?

3. **Critique case redesign:** If harder critique cases are wanted, the target mechanism is IDP (Haiku must claim must_not_claim issues) or IDR (Haiku must miss must_find issues) — not justification quality. The `addressed_but_incorrectly` investment is misaligned with the scoring engine; must_not_claim decoy seductiveness is the actual lever.

4. **addressed_but_incorrectly fate:** The design requirement adds case complexity that the engine cannot measure. Options: (a) remove it from the generation prompt since it doesn't affect IDP, (b) keep it as a qualitative difficulty marker that may matter for Sonnet/Opus even if not measurable for Haiku, (c) add IDJ as a new scoring dimension that captures it.

---

## 7. Resolution — Rubric Track: Add IDJ Dimension

**Decision:** Add IDJ (Issue Defense Judgment) to the scoring engine and fair-comparison dimensions. IDJ captures whether the model correctly argued that the team's stated justification for an `addressed_but_incorrectly` issue is wrong — a qualitatively different skill from finding the concern (IDR).

**Why now, not later:** All 9 critique/mixed cases in the 2xx batch already have `addressed_but_incorrectly: 1` on one planted_issue each. The case investment is already made. Without IDJ, that structure is invisible to the engine.

**Impact:**
- Critique case baseline: 1.000 → **0.800** (IDJ=0 when Haiku accepts wrong justification)
- Critique case debate ceiling: 1.000 (if debate correctly rebuts justification, IDJ=1)
- fc_lift potential added: **+0.200 per critique case**

### IDJ Definition

```python
def compute_idj(must_find_ids, addressed_but_incorrectly_ids, justifications_challenged):
    """
    IDJ = fraction of addressed_but_incorrectly must_find issues where
    model correctly challenged the stated justification.
    N/A if no addressed_but_incorrectly issues in this case.
    """
    abi = [i for i in must_find_ids if i in addressed_but_incorrectly_ids]
    if not abi:
        return None
    challenged = [i for i in abi if i in justifications_challenged]
    frac = len(challenged) / len(abi)
    if frac >= 0.9: return 1.0
    elif frac >= 0.5: return 0.5
    return 0.0
```

**Output schema addition (Phase 6):**
```json
"justifications_challenged": ["issue_id_1", ...]
```
Populated by orchestrator: for each issue in `issues_found`, did the Critic specifically argue that the memo's stated reason/justification for this concern is wrong or insufficient? The orchestrator does NOT need to know which issues are `addressed_but_incorrectly` — that cross-reference happens in the scoring engine, not at dispatch time. No answer-key leakage.

### Implementation Steps (in order)

**Step 1 — `plan/scripts/self_debate_poc.py`**
- Add `compute_idj()` function (definition above)
- Add `'IDJ'` to `FAIR_COMPARISON_DIMS` and `PRIMARY_SCORING_DIMS`
- In `score_run()`:
  - Extract `addressed_but_incorrectly_ids` from case JSON: `[p['issue_id'] for p in case.get('planted_issues', []) if p.get('addressed_but_incorrectly')]`
  - Extract `justifications_challenged` from output: `output.get('justifications_challenged', [])`
  - Add: `scores['IDJ'] = compute_idj(must_find_ids, addressed_but_incorrectly_ids, justifications_challenged)`
  - Note: IDJ is computed for ALL correct_position types (defense_wins cases where must_find=[] will return None automatically)

**Step 2 — `plan/phases/phase_06_benchmark_run.md`**
- Add `"justifications_challenged": [...]` to the output schema block (the JSON template on line ~63)
- Add extraction instruction alongside `issues_found`/`all_issues_raised`:
  > "Extract `justifications_challenged`: for each issue in `issues_found`, did the Critic specifically argue that the memo's stated reason or justification for this concern is wrong or insufficient? If yes, include its issue_id. If the memo gave no stated justification for a found issue, omit it from this list (vacuously not challenged)."
- Add `justifications_challenged` to the POST-WRITE VALIDATION required keys list

**Step 3 — `plan/phases/phase_05_5_difficulty_gate.md`**
- Add IDJ as a 4th inline dimension to the per-case scoring:
  > "IDJ: For each issue in `issues_found` that has a stated justification in the memo — did the response specifically argue that justification is wrong? (For defense_wins cases: IDJ=N/A)"
- Update per-case mean formula: `(IDR + IDP + FVC + IDJ) / N_applicable`
- Update the gate criterion note to reflect 4-dim scoring for addressed_but_incorrectly cases

**Step 4 — `plan/scripts/write_preregistration.py`**
- Add `"IDJ"` to the `dimensions` list in `primary_fair_comparison_lift`
- Add IDJ entry to the `rubric` dict:
  > `"IDJ": "Fraction of addressed_but_incorrectly must_find issues where model correctly argued stated justification is wrong (0.0/0.5/1.0); N/A if no addressed_but_incorrectly issues in case"`
- Add IDJ entry to `rubric["scoring_dimensions"]`

**Step 5 — `plan/phases/phase_02_hypothesis.md`**
- Update fair-comparison dimensions list: `IDR, IDP, IDJ, DRQ, FVC`
- Update primary metric note to include IDJ

---

## 8. Resolution — Case Generation Track: Lever A + Lever B

**Decision:** Re-generate hard critique/mixed cases with two structural changes. Skip Lever C (domain-knowledge-gated IDR) for v5 — adds the most complexity for the least marginal gain once A+B are in place.

**Impact (with IDJ also active):**

| Condition | IDR | IDP | DRQ | IDJ | FVC | Mean |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|
| Baseline (current cases) | 1.0 | 1.0 | 1.0 | — | 1.0 | 1.000 |
| Baseline (A+B+IDJ) | 1.0 | 0.5 | 0.5 | 0 | 0.5 | **0.500** |
| Debate ceiling (A+B+IDJ) | 1.0 | 1.0 | 1.0 | 1 | 1.0 | **1.000** |
| fc_lift | | | | | | **+0.500** |

0.500 < 0.55 — **Phase 5.5 gate passes** for cases with all three active.

### Lever A — Verdict Constraint: `acceptable_resolutions = ['empirical_test_agreed']`

Remove `critique_wins` from `acceptable_resolutions` for hard critique/mixed cases. The ideal verdict becomes `empirical_test_agreed` only. Cases must be designed as genuinely uncertain: the flaw is real but its severity or mechanism needs an empirical test to confirm.

Effect: Haiku says `critique_wins` → DRQ=0.5 (adjacent), FVC=0.5 (adjacent). For mixed cases this is already partially in place (acceptable includes both); Lever A removes the `critique_wins` fallback entirely.

**Generation requirement:** Task prompts must be written so that the correct response is "the evidence is suggestive but an empirical test is needed" rather than "this is definitively broken." Flaw severity or mechanism should be ambiguous enough that a strong methodologist would want a confirmatory test before rejecting the work outright. The `ideal_debate_resolution` block must specify meaningful `supports_critique_if`, `supports_defense_if`, and `ambiguous_if` conditions.

**Case schema requirement:**
```json
"acceptable_resolutions": ["empirical_test_agreed"],
"ideal_debate_resolution": {
    "type": "empirical_test_agreed",
    "supports_critique_if": "...",
    "supports_defense_if": "...",
    "ambiguous_if": "..."
}
```

### Lever B — Seductive Domain-Specific Decoys

Current `must_not_claim` decoys are too obviously wrong — they match generic false alarms that a careful general reviewer would correctly avoid. Haiku correctly avoids all of them in the 2xx batch.

A seductive decoy must look like a real flaw under general ML knowledge but be wrong due to domain-specific context the memo takes for granted. Examples of the pattern:
- "Using MAPE for intermittent demand is invalid" — wrong when the domain uses the industry-standard modified-MAPE variant
- "Reporting AUC-ROC on imbalanced classes overstates performance" — wrong when the domain uses threshold-independent reporting as per regulatory guidance
- "Single-institution validation is insufficient" — wrong when the regulatory scope is explicitly institution-specific

The decoy concern must be:
1. Plausible to a general ML reviewer without domain context
2. Wrong because of a field-specific convention, standard, or norm not stated in the memo
3. Stated in the must_not_claim list by ID, with `requires_external_knowledge` noting what domain context exonerates it

**Generation prompt change required:** Add to `must_not_claim` design guidance:
> "At least one `must_not_claim` concern per hard critique case must be a domain-specific false alarm: a concern that matches a well-known general ML pitfall but does not apply in this domain because of a field-specific convention, standard, or norm. The memo should NOT explain why the concern doesn't apply — that knowledge must be brought from outside. The `requires_external_knowledge` field on the `planted_issues` entry for this decoy must name the specific domain knowledge that exonerates it."

### Implementation Steps (in order)

**Step 1 — `synthetic-candidates/benchmark_case_generation_prompt.md`**
- In the **Critique Case Design Requirements** section, add under Requirement 2 (Decoy Dominance):
  > "At least one `must_not_claim` concern per hard critique case must be a domain-specific false alarm (see Lever B guidance above). The memo must NOT contain the information needed to dismiss this concern — dismissal requires field-specific knowledge from outside."
- In the **Case Format** section, for `acceptable_resolutions` on hard critique/mixed cases:
  > "Hard critique/mixed cases must use `acceptable_resolutions: ['empirical_test_agreed']` only. Do not include `critique_wins` as an acceptable resolution. The case should be designed so the correct verdict is 'we need to test this' not 'this is definitively broken.'"
- In the **Phase 4 Summary Table**, add tracking rows:
  - Hard critique/mixed cases with `acceptable_resolutions = ['empirical_test_agreed']` only: N (target: all hard critique/mixed)
  - Hard critique cases with ≥1 domain-specific false-alarm `must_not_claim`: N (target: all hard critique)

**Step 2 — `synthetic-candidates/REAL_PAPER_CASE_GENERATION_PROMPT.md`**
- Apply the same `acceptable_resolutions` constraint and domain-specific decoy requirement to the real-paper prompt (parallel update)

**Step 3 — Re-generate `synthetic-candidates/openai_benchmark_cases.json`**
- Run revised `benchmark_case_generation_prompt.md` through a non-Anthropic LLM (GPT-4o or Gemini)
- Target: 50 cases as before; hard critique/mixed cases use `acceptable_resolutions: ['empirical_test_agreed']` with domain-specific decoys
- Verify generation with `validate_cases.py --lenient` before merging

**Step 4 — Re-generate `synthetic-candidates/real_paper_cases.json`**
- Run revised `REAL_PAPER_CASE_GENERATION_PROMPT.md` through a non-Anthropic LLM
- Target: 14 cases as before

**Step 5 — Re-run Haiku smoke test on new real-paper cases**
- Use the updated proxy rubric (Phase 5.5 inline including IDJ)
- Gate criterion unchanged: ≥6/10 hard cases score mean < 0.55
- With Lever A + Lever B + IDJ active, expect critique/mixed baseline ~0.5 → gate should pass

---

## 9. What Is NOT Changing

- **Lever C (domain-knowledge-gated IDR):** Skipped for v5. Hardest to implement, least marginal gain with A+B+IDJ active. Document for v6.
- **Defense_wins case design:** Already effective (4/5 below 0.55 in smoke test, 0.00 in actual engine). No changes.
- **Easy/medium case requirements:** All new requirements scoped to hard cases only.
- **Existing 8 design principles:** Unchanged.
- **Overall category quotas:** Defense_wins stays at 13/60 synthetic + 5 real-paper.
- **DC dimension:** Remains diagnostic-only, excluded from fair-comparison lift.
- **ETD dimension:** Unchanged. Applies to debate conditions on cases with `ideal_type=empirical_test_agreed` (which will now be all hard critique/mixed cases under Lever A).

---

## 10. Projected Scores After Full Resolution

### Real-paper batch (eval_scenario_201–214) after Lever A + B + IDJ

| Case | Type | Old baseline | New baseline | New debate ceiling | fc_lift |
|------|------|:---:|:---:|:---:|:---:|
| 201, 204, 211, 212 | Pure critique | 1.000 | ~0.500 | ~1.000 | ~+0.500 |
| 202, 203, 210, 213, 214 | Mixed | 0.875 | ~0.500 | ~1.000 | ~+0.500 |
| 205 | defense_wins (pass) | 1.000 | 1.000 | 1.000 | 0 |
| 206–209 | defense_wins (fail) | 0.000 | 0.000 | 1.000 | +1.000 |
| **Batch mean** | | 0.634 | **~0.393** | **~1.000** | **~+0.607** |

### Phase 5.5 gate (projected)
- Critique/mixed cases scoring < 0.55: **~9/9** (all hard critique/mixed)
- Defense_wins scoring < 0.55: **4/5** (206–209)
- Total < 0.55: **~13/14 (93%)** — gate passes comfortably

---

## 11. Resolution — Options D and E: Gate Reporting and Pre-Registration

### Option D — Stratum-specific gate

**Original motivation:** Global gate was failing because critique cases ceiling at 1.0 while defense_wins cases sat below 0.55. A stratum-specific gate would pass defense_wins while flagging the critique ceiling separately.

**Status after Sections 7–8:** With IDJ + Lever A + Lever B implemented, projected gate scores are ~13/14 below 0.55. Global gate passes comfortably. **A stratum-specific blocking gate is no longer needed.**

**What remains useful:** Stratum-level reporting in Phase 5.5 as a non-blocking diagnostic. If something goes wrong in re-generation, a global FAIL gives no information about which stratum broke. A stratum table makes the gate diagnostic actionable.

**Resolution:** Add a non-blocking stratum breakdown table to Phase 5.5 output. No new gate logic. One additional logging step.

#### Implementation Step

**`plan/phases/phase_05_5_difficulty_gate.md`** — after the hard-case ceiling check, add:

> **Stratum diagnostic (non-blocking — informational only):**
> Report mean scores broken down by stratum:
>
> | Stratum | N cases | N below 0.55 | Mean score |
> |---|---|---|---|
> | Pure critique | N | N | X.XX |
> | Mixed | N | N | X.XX |
> | Defense_wins | N | N | X.XX |
>
> This table does not affect the gate decision. It identifies which stratum drives any gate failure and informs Phase 8 analysis planning.

Log the stratum breakdown alongside the existing gate outcome entry:
```bash
cd self_debate_experiment_v5 && uv run log_entry.py --step 5.5 --cat gate \
  --action stratum_diagnostic \
  --detail "Stratum breakdown: critique mean=X.XX (N/N below 0.55); mixed mean=X.XX (N/N); defense_wins mean=X.XX (N/N)"
```

---

### Option E — Pre-register stratum separation

**Status:** Still needed and now enhanced. The original motivation (critique ceiling → rely on defense_wins) is partially addressed by the rubric + generation changes, but stratum pre-registration remains valuable for three independent reasons:

1. **Different fc_lift mechanisms by stratum.** Critique/mixed lift comes from IDJ improvement (justification evaluation) + DRQ/FVC improvement (reaching empirical_test_agreed instead of overclaiming). Defense_wins lift comes from FVC/DRQ improvement (preventing false condemnation). Collapsing these into one aggregate obscures the mechanism.

2. **Expected magnitude differs.** Defense_wins baseline: 0.0 → ceiling +1.0 per case. Critique/mixed baseline: ~0.5 → ceiling +0.5. Without stratum-level pre-registration, a large defense_wins effect could swamp a small critique effect or mask a zero result in one stratum.

3. **Prevents post-hoc rationalization.** Pre-registering expected directional patterns before Phase 6 means the stratum interpretation is committed before seeing data.

**Resolution:** Add stratum fc_lift analysis to Phase 2 hypothesis file and `write_preregistration.py` as a pre-registered secondary analysis — not a new primary hypothesis, but a committed interpretive structure.

#### Implementation Steps

**`plan/phases/phase_02_hypothesis.md`** — add after the existing secondary hypotheses:

> **Pre-registered stratum analysis (Phase 8):**
> fc_lift will be reported separately for three strata: pure critique, mixed, and defense_wins.
> Expected directional patterns:
> - Defense_wins stratum: primary driver of DRQ/FVC lift (isolated debate Defender prevents false condemnation)
> - Critique/mixed stratum: primary driver of IDJ lift (debate forces justification quality evaluation)
> - Mixed stratum: additional DRQ lift from reaching `empirical_test_agreed` verdict + ETD quality improvement
>
> Global fc_lift (H1 primary criterion) remains the hypothesis test. Stratum breakdown is the interpretive structure for understanding mechanism, pre-registered to prevent post-hoc selection of favorable stratum framing.

**`plan/scripts/write_preregistration.py`** — add to the hypotheses dict:

```python
"stratum_fc_lift": {
    "claim": "Pre-registered stratum breakdown for Phase 8 interpretation",
    "strata": ["pure_critique", "mixed", "defense_wins"],
    "expected_primary_lift_driver": "defense_wins (DRQ/FVC); critique/mixed (IDJ)",
    "note": "Not a hypothesis test — a pre-committed interpretive structure. Prevents post-hoc stratum selection."
}
```

---

## 12. Complete Implementation Checklist

All changes from Sections 7–11, sequenced by dependency:

### Before Phase 0 (no generation round required)

- [ ] **`plan/scripts/self_debate_poc.py`** — add `compute_idj()`, add `'IDJ'` to `FAIR_COMPARISON_DIMS` and `PRIMARY_SCORING_DIMS`, update `score_run()` to extract `addressed_but_incorrectly_ids` and `justifications_challenged`
- [ ] **`plan/phases/phase_06_benchmark_run.md`** — add `justifications_challenged` to output schema, add extraction instruction, add to POST-WRITE VALIDATION keys
- [ ] **`plan/phases/phase_05_5_difficulty_gate.md`** — add IDJ as 4th inline proxy dimension, update per-case mean formula, add non-blocking stratum diagnostic table + logging step
- [ ] **`plan/phases/phase_02_hypothesis.md`** — add stratum fc_lift pre-registration block, add IDJ to fair-comparison dimensions list
- [ ] **`plan/scripts/write_preregistration.py`** — add IDJ to dimensions and rubric dict, add `stratum_fc_lift` entry to hypotheses dict

### Before Phase 0 (generation round required first)

- [ ] **`synthetic-candidates/benchmark_case_generation_prompt.md`** — add Lever A constraint (`acceptable_resolutions: ['empirical_test_agreed']` for hard critique/mixed) and Lever B guidance (domain-specific false-alarm decoys) to Critique Case Design Requirements and Case Format sections; update Phase 4 tracking table
- [ ] **`synthetic-candidates/REAL_PAPER_CASE_GENERATION_PROMPT.md`** — parallel Lever A + B updates
- [ ] **Re-generate `synthetic-candidates/openai_benchmark_cases.json`** via non-Anthropic LLM using revised prompt
- [ ] **Re-generate `synthetic-candidates/real_paper_cases.json`** via non-Anthropic LLM using revised prompt
- [ ] **Re-run Haiku smoke test** on new real-paper cases using updated proxy rubric (4-dim including IDJ); verify gate passes (≥6/10 hard cases < 0.55)

### After generation round validates

- [ ] Proceed to Phase 0: merge sources, validate, log

---

*Document complete as of 2026-04-07.*
