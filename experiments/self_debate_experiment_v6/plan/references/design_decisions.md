# v6 Design Decisions

## 1. Case Source: RC Reports (Primary) + Synthetic Mixed (Supplement)

**Regular cases (critique/defense):** sourced from ML Reproducibility Challenge (RC) reports
via OpenReview API + ReScience C. RC reports contain post-hoc documented flaws from independent
reproducers — measuring *methodology review recall*, not planted corruption detection.

**Mixed cases:** generated via the synthetic pipeline (already built: `stage2_mixed_writer.md`,
`stage3_mixed_assembler.md`, `orchestrator.py --mixed`). RC reports may also yield natural
mixed cases ("paper mostly sound but X is overstated"), but the synthetic pipeline guarantees
sufficient volume and controlled ambiguity taxonomy.

**Decision gate — run after Phase 1, before Phase 2 commits:**

| RC yield | Action |
|---|---|
| regular >= 60 AND mixed >= 20 | Use RC exclusively |
| regular >= 60, mixed < 20 | Supplement mixed with synthetic pipeline |
| regular < 60 | Supplement regular cases with synthetic (lower proxy threshold) |
| RC total < 30 | Full synthetic fallback: v5 architecture + lower ceiling target + mixed cases |

**Critical-path risk:** RC extraction pipeline (`pipeline/rc_extractor.py`) does not yet exist.
Build and validate yield in Phase 1 before committing Phase 2.

---

## 2. Case Composition: Target N = 120

| Stratum | Source | Target N | % |
|---|---|---|---|
| Critique cases (flawed designs) | RC reports | 60 | 50% |
| Defense_wins (sound designs) | RC reports or synthetic | 20 | 17% |
| Mixed cases (empirically contingent) | Synthetic + RC natural | 40 | 33% |
| **Total** | | **120** | |

**Difficulty calibration:**
- Pilot Phase (Phase 3): run baseline on ~30 candidate cases
- **Hard gate:** discard cases where baseline FC mean > 0.80 (retain cases with genuine headroom)
- Use **cross-model proxy scoring** (GPT-4o) for difficulty filtering — not Claude
- Final N informed by pilot results; if pilot variance is high, increase N

---

## 3. Pipeline Architecture

Three pipelines converge at `normalize_cases.py` to produce unified Schema B, consumed by
`self_debate_poc.py`:

| Stage | RC Extraction | Synthetic Regular | Synthetic Mixed |
|---|---|---|---|
| 1 | RC-1: Fetch (OpenReview API, ReScience C) | Stage 1: Hypothesis gen | Stage 1: Hypothesis gen |
| 2 | RC-2: Flaw extraction (GPT-4o) | Stage 2: Corrupt design | Stage 2-mixed: Ambiguous design |
| 3 | RC-3: `must_not_claim` extraction (GPT-4o) | Stage 3: Ground truth assembly | Stage 3-mixed: Ground truth assembly |
| 4 | RC-4: Filtering + contamination gate | Stage 4: Case assembly | ↑ (3 stages only) |
| 5 | — | Stage 5: Smoke validation | — |
| ↓ | `rc_cases_raw.json` | `synthetic_regular_raw.json` | `synthetic_mixed_raw.json` |
| Normalize | `normalize_cases.py` (RC → Schema B) | `normalize_cases.py` (synth → Schema B) | `normalize_cases.py` (synth → Schema B) |
| Select | `select_cases.py` (stratified, difficulty-gated from Phase 3 pilot) | ← same | ← same |
| Output | `benchmark_cases_verified.json` (Schema B, all sources) | ← same | ← same |

**⚠ Blocking bug (fixed in Phase 0):** `stage3_mixed_assembler.md` as shipped set
`acceptable_resolutions = ["mixed", "empirical_test_agreed", "critique_wins", "defense_wins"]`.
This made `compute_fvc()` return 1.0 for every condition, collapsing H1b. Fixed to
`["empirical_test_agreed"]` only. PLAN.md, HYPOTHESIS.md, and MIXED_CASE_PLAN.md all agree
on this value — the prompt template was the outlier.

**Schema B fields consumed by `self_debate_poc.py`:**
- `ground_truth.correct_position` — read by `score_run()`
- `ideal_debate_resolution.type` — read by DRQ/FVC scoring
- `scoring_targets.acceptable_resolutions` — **flat string array** (line 168: `st.get('acceptable_resolutions', ...)`)
- `scoring_targets.must_find_issue_ids` — read by `compute_idr()`
- `scoring_targets.must_not_claim` — read by `compute_idp()`

---

## 4. Conditions (6)

| Condition | Description | Compute | Primary comparisons |
|---|---|---|---|
| `baseline` | Single-pass critique; no adversarial structure | 1x | Reference for all |
| `isolated_debate` | Critic + Defender isolated; orchestrator adjudicates | ~3x | Q1 (vs baseline), Q2 (vs ensemble) |
| `biased_debate` | Same as isolated_debate, but agents persona-primed (see below) | ~3x | Q4 (vs isolated_debate) |
| `multiround` | Defender sees Critic output; natural stopping up to 4 rounds | ~3–6x | Q3 reference |
| `conditional_fm` | Round 2 gated on unresolved disagreement (see gate below) | ~3–6x | Q3 (vs multiround) |
| `ensemble_3x` | 3 independent assessors; union-of-issues IDR | 3x | Q2 compute-matched |

**Compute accounting for Q2 (the structure test):**
The fairest test of whether debate *structure* adds value (not just additional compute) is
`isolated_debate` (~3x) vs `ensemble_3x` (3x) at matched compute. If ensemble >= debate,
adversarial structure adds no value over independent redundancy.

---

## 5. Conditional Forced Multiround Gate

Replaces unconditional `forced_multiround` from v5. Concrete gate:

```
After round 1 adjudication:
  IF point_resolution_rate == 1.0  → STOP (all points resolved)
  ELIF adjudicator verdict matches both agents' round 1 stated positions → STOP
  ELSE → force round 2
```

**Rationale from v5 data:** All 24 hollow rounds (20.5%) came from defense_wins cases where
there was no genuine disagreement. This gate would have prevented all 24. Target hollow rate < 10%.

---

## 6. Persona-Biased Debate

`biased_debate` is structurally identical to `isolated_debate` — same protocol, same compute,
same orchestrator. The only difference is asymmetric persona priming injected into each agent's
system prompt before dispatch:

**Critic priming:**
> "You are reviewing an experiment submitted by an inexperienced researcher. Be thorough and
> treat methodological gaps as real concerns until shown otherwise."

**Defender priming:**
> "You are responding to a combative reviewer who frequently focuses on insignificant issues
> and overstates concerns. Be selective about what you concede."

**Expected mechanism:** The biased critic is sensitized to real flaws (higher IDR); the biased
defender concedes less, forcing the critic to defend weaker claims under pressure.

**IDP note:** v5 IDP was flat at 0.8549 across all conditions on the synthetic benchmark.
v6 uses RC reports with a lower ceiling and different case structure — IDP behavior on genuine
RC flaws may differ. IDP is retained in H6 as a full prediction, not just a diagnostic probe.
If IDP remains flat under the new benchmark, that points to an orchestrator extraction issue
(see orchestrator audit in Phase 0 and `all_issues_adjudicated` field below).

**What this tests (Q4):** Does persona framing alone, without changing the protocol structure,
improve debate quality? Comparison is `biased_debate` vs `isolated_debate` — matched compute,
matched structure, prompt framing only.

**ETD applicability:** Same as `isolated_debate` — ETD fires on mixed cases.

---

## 7. Scoring Dimensions

DC is **dropped entirely** — it was fully redundant with FVC in v5
(mean_abs_delta = 0.0 across all conditions, all 330 comparable runs). Carrying it adds
no signal and introduces reporting confusion.

| Dimension | Regular cases | Mixed cases | Scorer |
|---|---|---|---|
| **IDR** (Issue Detection Rate) | Primary | N/A | GPT-4o (cross-model) |
| **IDP** (Issue Detection Precision) | Primary | N/A | GPT-4o (cross-model) |
| **DRQ** (Decision Resolution Quality) | Primary | Primary (vs `empirical_test_agreed`) | Rule-based |
| **FVC** (Final Verdict Correctness) | Primary | **Co-primary** (vs `empirical_test_agreed`) | Rule-based |
| **ETD** (Empirical Test Design) | N/A | Debate conditions only | GPT-4o (cross-model) |

**Cross-model scoring:** GPT-4o (primary) for IDR, IDP, ETD semantic scoring. Addresses the
closed-loop confound. Absolute scores are **not** comparable to v5 — only within-v6 lift
comparisons are valid.

**Union IDR for ensemble — split rule:** any-assessor-found credit for IDR; majority-vote
retained for the final verdict. The split is intentional: union recovers recall (v5: 0.8725
vs. majority 0.7679) while the conservative majority rule preserves precision on the verdict
itself. Do not union the verdict — that would inflate FVC by accepting minority verdicts.

---

## 8. Why Mixed-Case FVC Is the Primary Signal

On mixed cases, `acceptable_resolutions = ['empirical_test_agreed']`. Expected behavior
by condition:

| Condition | Expected verdict | FVC |
|---|---|---|
| `baseline` | Commits to `critique_wins` or `defense_wins` | 0.0–0.5 |
| `ensemble_3x` | Each assessor picks a side; no adversarial exchange | low |
| `isolated_debate` | Adversarial exchange surfaces ambiguity; `empirical_test_agreed` | high |
| `multiround` | Same as isolated, with more rounds | high |
| `conditional_fm` | Same + gated forcing | high |

Mixed-case FVC is comparable across **all 6 conditions** (unlike ETD, which is N/A for
baseline/ensemble). It directly tests the mechanism claim: adversarial structure should cause
agents to recognize ambiguity rather than commit to one side. This is the cleanest answer to
both Q1 and Q2 simultaneously. `biased_debate` should outperform `isolated_debate` here if
persona priming improves sensitivity to ambiguity.
