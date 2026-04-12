# v7 Design Decisions

## 1. Conditions (4)

| Condition | Description | Compute | vs v6 |
|---|---|---|---|
| `baseline` | Single-pass critique | 1× | Retained |
| `isolated_debate` | Critic + Defender (no cross-visibility); Adjudicator synthesizes | 3× | Retained |
| `ensemble_3x` | 3 independent critics; union IDR / majority-vote verdicts | 3× | Retained |
| `multiround_2r` | Critic → Defender (sees critic) → Adjudicator; exactly 2 rounds | 3× | **New** |

**Dropped from v6:**
- `biased_debate` — bias sensitivity addressed; not a primary claim. Report as footnote if needed.
- `conditional_fm` — gate logic failed to isolate mechanism; not a core claim.

**`multiround_2r` design rationale:**
v6's `multiround` averaged ~5× compute (up to 4 rounds + adjudicator). The FVC_mixed advantage
at 5× was the central weakness in peer review — it confounds compute budget with debate structure.
`multiround_2r` is fixed at exactly 3 API calls: critic → defender (sees critic output) →
adjudicator. No stop-detection. No conditional branching. Clean 3× matching against
`isolated_debate` and `ensemble_3x`.

---

## 2. Case Composition: Target N = 260

| Stratum | v6 count | v7 target | Source | Rationale |
|---|---|---|---|---|
| Regular (planted flaws) | 80 | 160 | RC reports + synthetic | ≥160 required; n=80 is desk-reject risk at ACL Findings (v6_issues.md) |
| Mixed (ambiguous) | 40 | 80 | Synthetic + RC natural | Double convergent task evidence |
| Defense (valid work) | 0 | 20 | RC successful replications or synthetic no-flaw | Exoneration rate analysis |
| **Total** | **120** | **260** | | |

**Defense case sourcing (open question):**
Options: (a) sample ReScience C replications that succeeded without raised concerns,
(b) generate synthetic cases with no planted flaws and validate manually. Resolve in Phase 1
based on RC yield.

**Difficulty calibration gate (Phase 3):**
- Run baseline on ~40 candidate cases per stratum
- Discard cases where `baseline_fc_mean > 0.80` (insufficient headroom)
- Final N may exceed 260 targets if pilot yield is high

**Case sourcing:** All freshly generated. No reuse of v5 or v6 cases. v5 candidate pool
(728 cases) is available as a supplement but all items have `type: unknown` — require
manual categorization before use; fresh generation is preferred.

---

## 3. Scoring Battery

### Primary (4 dimensions)

| Dimension | Regular cases | Mixed cases | Scorer |
|---|---|---|---|
| IDR (Issue Detection Recall) | Primary | N/A | GPT-4o cross-vendor |
| IDP (Issue Detection Precision) | Primary | N/A | GPT-4o cross-vendor |
| DRQ (Decision Resolution Quality) | Primary | Primary | Rule-based |
| FVC (Final Verdict Correctness) | Primary | **Co-primary** | Rule-based |

**FC composite** = mean(IDR, IDP, DRQ, FVC) — same as v6 definition.
**FVC_mixed** = FVC on mixed cases only — co-primary for the convergent task test (P2).

### Removed: ETD (Empirical Test Design)
ETD=1.0 for 100% of debate outputs in v6 — ceiling effect, no signal. Dropped from primary
battery. Include a one-paragraph appendix note explaining the ceiling observation.

### IDR scoring — bidirectional (retained from v6)
- `idr_documented` — recall against documented RC flaws (primary, used in FC)
- `idr_novel` — novel valid concerns not in RC report (secondary, reported separately)

### IDP scoring — dual field (retained from v6)
- `idp_raw` — precision from `all_issues_raised` (Critic raw output; primary)
- `idp_adj` — precision from `all_issues_adjudicated` (post-Adjudicator; secondary)

---

## 4. Statistical Tests

### Bootstrap CIs
- Paired bootstrap, n=10,000, seed=42 for all condition comparisons
- 95% CI on all primary metrics

### TOST for H1a
Two one-sided tests (equivalence bounds: ±0.05 FC) to formally claim debate ≈ baseline.

**Equivalence bounds:** ±0.05 FC (5 percentage points). This represents a practically
meaningful difference threshold in the evaluation context. Confirm and commit before Phase 5.

**TOST passes (equivalence confirmed)** if both:
- Upper bound test: upper CI < +0.05
- Lower bound test: lower CI > −0.05

### Pre-registered thresholds
H1a TOST bounds must be specified in `HYPOTHESIS.md` before Phase 5 (same pre-registration
timing requirement as hypotheses). Set to ±0.05 unless pilot data suggests revision.

---

## 5. Open Questions

| Question | Recommended resolution | Decide by |
|---|---|---|
| Defense case sourcing | RC successful replications preferred; fall back to synthetic | Phase 1 |
| TOST equivalence bounds | ±0.05 FC; confirm after pilot (bounds must not change post-Phase-5) | Phase 4 |
