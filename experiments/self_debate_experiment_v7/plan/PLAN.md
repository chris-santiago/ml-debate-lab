# v7 Experimental Design: Prospective Validation of the Convergent/Divergent Framework

## Context

v6 produced three formally supported findings about multi-agent debate for LLM-based
methodology review:

1. **Ensemble > debate at matched compute** (3×): FC delta = +0.0287, CI [+0.0154, +0.0434]
2. **Debate ≈ baseline** (H1a FAIL): FC delta = −0.0026, CI [−0.0108, +0.0059]
3. **Multiround advantage on convergent tasks** (FVC_mixed=0.3667 vs baseline~0), but at
   ~5× compute, not 3×

**v6's three weaknesses identified in peer review:**

| Weakness | Impact | v7 Fix |
|---|---|---|
| Compute-matched multiround gap: FVC_mixed advantage at ~5×, not 3× | Central claim lacks matched-compute evidence for convergent task | Add `multiround_2r` (exactly 3×) |
| Convergent/divergent framework post-hoc | ACL/NLP reviewers treat post-hoc patterns as hypothesis not contribution | Pre-register directional predictions before Phase 5 |
| ETD ceiling: ETD=1.0 for 100% of outputs | Metric produces no signal, weakens battery | Remove ETD from primary battery |
| 40 mixed cases underpowered | FVC_mixed tests have wide CIs | Scale mixed 40→80 |
| H1a non-significance ≠ equivalence | TOST needed to formally claim debate≈baseline | Add TOST equivalence test |

v7 is designed to prospectively confirm the convergent/divergent framework and fix the
compute-matched gap, producing a substantially stronger paper.

---

## Submission Strategy

**Decision (2026-04-12):** Wait for v7. Single submission of the v7 paper to EMNLP ARR
May 2026 (deadline: May 25, 2026). No v6 submission in parallel.

**Timeline:** ~6 weeks from decision date to ARR deadline. Case generation + full experiment
run + analysis + paper rewrite is feasible with parallelization, but tight. Phases 0–4
should complete within 2 weeks to leave adequate time for the benchmark run and analysis.

---

## Pre-Registration (The Key Change)

The convergent/divergent framework must be committed to git as explicit directional
predictions **before Phase 5** (benchmark run). This converts a post-hoc pattern into a
prospective test.

**Pre-registered predictions (both must hold to confirm the framework):**

| Prediction | Metric | Direction | Threshold |
|---|---|---|---|
| P1 (divergent) | IDR: `ensemble_3x` vs `multiround_2r` | ensemble_3x > multiround_2r | CI lower bound > 0 |
| P2 (convergent) | FVC_mixed: `multiround_2r` vs `ensemble_3x` | multiround_2r > ensemble_3x | CI lower bound > 0 |

These two predictions are the minimum sufficient test of the framework: different aggregation
strategies should win on different task types, at matched compute.

---

## Conditions (4, down from 6)

| Condition | Description | Compute | Status |
|---|---|---|---|
| `baseline` | Single-pass critique | 1× | Retained from v6 |
| `isolated_debate` | Critic + Defender isolated; adjudicator synthesizes | 3× | Retained from v6 |
| `ensemble_3x` | 3 independent critics; union IDR / majority-vote verdicts | 3× | Retained from v6 |
| `multiround_2r` | Critic → Defender (sees critique) → Adjudicator; exactly 2 rounds | 3× | **New in v7** |

**Dropped from v6:**
- `biased_debate` — addressed bias sensitivity; sensitivity analysis sufficient
- `conditional_fm` — gated multiround; failed to isolate mechanism in v6; not a core claim

**`multiround_2r` design:**
- Round 1: Critic produces full critique
- Round 2: Defender sees critique and responds; Adjudicator synthesizes both
- Total: exactly 3 LLM calls = 3× compute — matched to `isolated_debate` and `ensemble_3x`
- This is a structural rearchitecting of v6's `multiround` (which was critic → debate loop
  up to 4 rounds, ~5× average)

---

## Phase 5 Architecture: API Dispatch

v7 Phase 5 runs via a standalone Python script (`pipeline/phase5_benchmark.py`) that calls
Claude directly via OpenRouter, replacing v6's Claude Code agent dispatch.

Full design: `plan/references/API_DISPATCH_PLAN.md` (status updated to ACTIVE for v7).

v7-specific adjustments:
- 4 conditions only: `baseline`, `isolated_debate`, `ensemble_3x`, `multiround_2r`
  (no `biased_debate` or `conditional_fm` handlers needed)
- `multiround_2r` is fixed 3 calls — critic → defender (critic visible) → adjudicator;
  no stop-detection loop required
- Verify OpenRouter model string for current claude-sonnet before Phase 5

Advantages: higher parallelism (20+ concurrent), programmatic resume, version-controlled
system prompts as constants in the script (not buried in conversation context).

---

## Case Design

| Case type | v6 count | v7 target | Rationale |
|---|---|---|---|
| Regular (planted flaws) | 80 | 120 | More statistical power for primary IDR/FC test |
| Mixed (ambiguous) | 40 | 80 | Double convergent task evidence; FVC_mixed tests underpowered |
| Defense (valid work) | 0 | 20 | Reintroduce; needed for exoneration rate analysis |
| **Total** | **120** | **220** | |

**Case sourcing:** All fresh generation. v6 cases are not reused (independent replication
requires independent cases). v5 synthetic-candidate pool (728 cases, type: unknown) is not
used directly — category labels (regular/mixed/defense) must come from the v7 generation
pipeline, not retroactive classification.

**Case generation:**
- Regular cases: new synthetic cases with planted methodology flaws; same Schema B format
- Mixed cases: empirically ambiguous designs where correct position is contestable
- Defense cases: valid work that should receive clean exoneration (rare in real ML papers)
- RC papers: aim for 30–40 real ReScience C papers (vs 25 in v6) for ecological validity

---

## Scoring Changes

### Removed from primary battery
- **ETD (Empirical Test Design)**: ETD=1.0 for 100% of outputs in v6 — metric is at ceiling
  and produces zero signal. Reported in appendix as a structural observation, not in tables.

### Primary battery (v7)
| Dimension | Regular cases | Mixed cases | Scorer |
|---|---|---|---|
| IDR (Issue Detection Recall) | Primary | N/A | GPT-4o cross-vendor |
| IDP (Issue Detection Precision) | Primary | N/A | GPT-4o cross-vendor |
| DRQ (Decision Resolution Quality) | Primary | Primary | Rule-based |
| FVC (Final Verdict Correctness) | Primary | **Co-primary** | Rule-based |

### New statistical tests
- **TOST for H1a**: two one-sided tests (equivalence bounds ±0.05) to formally claim
  debate ≈ baseline, not just non-significance. Requires pre-specifying bounds before Phase 5.
- **Bootstrap CIs**: retain paired bootstrap (n=10,000, seed=42) for all condition comparisons

### Primary composite
- **FC** = mean(IDR, IDP, DRQ, FVC) — same as v6, ETD removed
- **FVC_mixed** = FVC on mixed cases only — co-primary for convergent task test

---

## Phase Structure

| Phase | Title | Key gate |
|---|---|---|
| 0 | Setup | `multiround_2r` agent + scoring engine updated; committed |
| 1 | RC Data Acquisition | `rc_cases_raw.json` with ≥30 ReScience C papers |
| 2 | Case Library Assembly | `benchmark_cases_v7_raw.json` passes Schema B validation; 220 cases |
| 3 | Pilot & Calibration | `baseline_fc_mean < 0.80`; ≥120 regular + ≥60 mixed pass filter |
| **4** | **Pre-Experiment Self-Review** | **`HYPOTHESIS.md` committed with P1 + P2 predictions; TOST bounds committed; coherence audit passes as named gate (→ issue 5273d436)** |
| 5 | Benchmark Run | All output files pass schema + zero-variance check |
| 6 | Cross-Model Scoring | `v7_rescored_idr_idp.json` complete |
| 7 | Analysis | `v7_results.json` with all hypothesis tests + TOST |
| 8 | Sensitivity & Robustness | `SENSITIVITY_ANALYSIS.md`; variance audit on `multiround_2r` |
| 9 | Cross-Vendor Validation | Spot-check 10% of cases |
| 10 | Reporting | All artifacts + `/artifact-sync` + coherence audit |

**Phase 4 gate (critical):** HYPOTHESIS.md must contain P1 and P2 as explicit directional
predictions with bootstrap CI thresholds, committed to git. Coherence audit (spec vs plan
vs scoring code alignment) is a mandatory named step — not ad-hoc (resolves issue 5273d436).

---

## Open Questions Before Starting

1. ~~**Dual-track vs wait?**~~ **Decided (2026-04-12):** Wait for v7. Single ARR May 2026 submission.
2. **Defense case sourcing:** Where to find 20 valid methodology cases that should be
   exonerated? Options: (a) sample real ReScience C replications that succeeded, (b) generate
   synthetic cases with no planted flaws and manually validate
3. **`multiround_2r` stopping rule:** Is adjudicator always called after exactly 1 round,
   or should there be a divergence gate (call adjudicator only if Defender disputes)?
   Recommendation: always call adjudicator (clean 3× compute matching; no conditional
   branching confound)
4. **TOST equivalence bounds:** ±0.05 FC is the natural choice (5pp difference = meaningful
   in context); confirm before pre-registering

---

## Authoritative Sources (v7)

After the experiment:
- `v7_hypothesis_results.json` — all metrics, CIs, p-values (primary)
- `HYPOTHESIS.md` (committed pre-Phase-5) — pre-registered predictions (ground truth)
- `ENSEMBLE_ANALYSIS.md` — minority precision + RC subgroup
- `SENSITIVITY_ANALYSIS.md` — variance, subgroup robustness

**Never source numbers from:** README prose, pre-Phase-5 drafts, or v6 artifacts.
