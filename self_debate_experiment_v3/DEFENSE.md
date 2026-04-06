# DEFENSE.md — Self-Debate Protocol v3 Experimental Design

**Role:** ml-defender (Mode 1, initial defense)
**Inputs:** HYPOTHESIS.md, PREREGISTRATION.json, evaluation_rubric.json, CRITIQUE.md
**Structure:** Two-pass (Pass 1 full analysis, Pass 2 verdict selection)

---

## Pass 1 — Full Analysis

### Implementation Soundness Check

Before addressing individual critique points: the scoring engine (self_debate_poc.py) is sound for its intended purpose. The core functions `compute_idr`, `compute_idp`, `compute_fvc`, `compute_drq`, `compute_etd` all have distinct logic and do not share mutable state. The structural overrides (DC=0.0 for baseline, DRQ cap at 0.5 for baseline) are pre-registered and applied consistently in the code. The `score_run` function correctly reads from ground_truth and scoring_targets subfields per the v3 schema. No silent misconfiguration is present in the scoring engine itself.

The one implementation gap confirmed: convergence metric is defined in PREREGISTRATION.json but not implemented in self_debate_poc.py. This is a real omission, acknowledged below.

---

### Analysis of Each Critique Point

**On Issue 1 — DC=FVC double-counting:**

The critic correctly identifies that `compute_dc` calls `compute_fvc` for non-baseline conditions in isolated_debate and ensemble. This is not a defect — it was an explicit design choice documented in the dc_note. The reason DC was retained as a separate dimension even when structurally identical to FVC is: (a) it preserves rubric comparability with v1 which had a distinct DC definition, and (b) in the multiround condition, DC and FVC diverge (DC reflects the path of adversarial exchange, FVC reflects only the final verdict). Collapsing DC into FVC for isolated/ensemble would require condition-specific scoring rules that are harder to audit.

However, the critic's concern is valid: including two numerically identical values in a mean does inflate the apparent dimensionality without adding information. The honest_lift calculation partially addresses this, but the primary threshold (0.65 mean, 75% pass rate, +0.10 lift) is stated against the inflated metric. This is a real measurement integrity issue.

**On Issue 2 — Effective dimensionality 3-4 not 6:**

Correct in substance. For a critique_wins case in isolated_debate: IDR, IDP, DC (=FVC), DRQ, ETD=null, FVC gives 5 non-null values with one duplicate pair. Effective independent dimensions: IDR, IDP, DRQ, FVC = 4. For a mixed case: same structure. For a defense_wins case: DC (=FVC), DRQ, ETD, FVC = effectively DC, DRQ, ETD (FVC and DC are duplicate) = 3 distinct values. The six-dimension framing is aspirational, not operational. The critic is correct that the threshold calibration reflects assumed six-dimension coverage.

**On Issue 3 — Isolated debate is two parallel critics:**

This critique conflates the mechanism claim with the isolation design. The HYPOTHESIS.md mechanism statement is about what adversarial role separation forces — the Defender's system prompt is oriented toward defense (finding reasons the methodology is sound, looking for red herrings, checking that critique claims are not false positives). The Critic is oriented toward finding flaws. Two agents with asymmetric instructions applied to the same task are not structurally equivalent to running the same agent twice. The Defender's bias toward defense is the mechanism, not the interaction between the two agents' outputs.

However: the hypothesis statement says "forces engagement with both sides of each case" — that language implies the agents engage with each other, which they do not in the isolated condition. The mechanism as stated is imprecise. A more accurate statement: "Asymmetric role instructions produce complementary coverage — the Critic is biased toward flaw detection, the Defender toward exoneration — and the orchestrator synthesizes both biases." That is a defensible mechanism that does not require adversarial interaction.

**On Issue 4 — No power analysis for +0.10 threshold:**

The critic is right that no power calculation is pre-specified. The stats_analysis.py script is planned but its specific tests are not committed. However, the +0.10 threshold is a substantive criterion, not a statistical significance threshold. It represents "the debate protocol must beat baseline by a margin large enough to matter for deployment decisions." Whether that difference is statistically significant is a separate question. The experiment does commit to reporting confidence intervals in stats_analysis.py. The omission is the lack of a pre-specified alpha and test family before execution — not the choice of 0.10 as the effect size.

**On Issue 5 — DC=0.0 override suppresses baseline unfairly:**

The critic correctly identifies the asymmetry. The defense is that DC=0.0 is a structural fact: baseline has no Defender role, so "defense function correctly reached verdict type" is definitionally inapplicable. The honest_lift calculation corrects for this by applying DC=0.5 (the neutral midpoint) to baseline. The design commit is: primary hypothesis uses raw lift AND honest lift is reported. If honest lift >= 0.10, the conclusion holds even corrected. If raw lift >= 0.10 but honest lift < 0.10, the conclusion does not hold. The experiment is committed to reporting both — the honest lift is not a footnote.

The critic's concern that the primary threshold is stated against raw lift is valid: the primary success criterion should be stated against honest lift to be unambiguous. This is a pre-registration gap.

**On Issue 6 — ETD constraint not operationally locked:**

Valid concern. PREREGISTRATION.json specifies that the ensemble synthesizer receives a measure/success_criterion/failure_criterion instruction, but the exact text is not committed. This is a real gap — the EXECUTION_PLAN.md must include the verbatim ETD instruction before any agent runs. Without it, the ETD comparison between debate and ensemble cannot be cleanly attributed to structural vs. prompt-design differences.

**On Issue 7 — Single-source generator fingerprinting:**

Partially valid. The external_cases_v3.json set provides a partial cross-source control. The case verifier checked for target leakage in case_id and first task_prompt sentence but did not run vocabulary correlation analysis. The critic's concern is plausible but speculative — generator fingerprinting requires a specific mechanism (e.g., must_find_issue_ids share unusual vocabulary with task_prompt). The defense: this is a valid concern for the external validity of the benchmark, but it does not invalidate the within-benchmark comparison between debate and baseline conditions. Both conditions receive the same cases from the same source — if there is systematic vocabulary correlation, it affects all conditions equally, not the lift calculation.

**On Issue 8 — category field leaks correct_position:**

This is the highest-severity issue in the critique and the defense cannot fully rebut it. For 11 cases in the defense_wins category, the category field directly signals the correct_position. If category is included in agent context, IDR and FVC on those cases are invalidated. The execution plan must specify that only task_prompt is passed to agents. The case verifier focused on case_id and first-sentence leakage but did not verify that category is stripped from agent context. This must be confirmed before any agent run.

**On Issue 9 — DRQ filter not enforced in scoring engine:**

Valid. The secondary hypothesis criterion specifies "non-defense_wins cases" but the scoring engine aggregates over all 49 cases. The stats_analysis.py script is planned to handle filtered comparisons, but it is not pre-specified whether it implements the correct filter for the DRQ hypothesis. This needs to be locked before execution.

**On Issue 10 — Convergence metric not implemented:**

Conceded. The convergence metric is defined in PREREGISTRATION.json but absent from self_debate_poc.py. It should either be added to the scoring engine before execution begins or explicitly deferred to a post-processing script with a locked schema.

---

## Pass 2 — Verdict Selection

| Issue | Verdict | Rationale |
|-------|---------|-----------|
| 1 — DC=FVC double-counting | **Concede** | Inflation is real; primary threshold overstates independent coverage |
| 2 — Effective dimensionality | **Concede** | Six-dimension framing is aspirational; threshold calibration should reflect effective dims |
| 3 — Isolated debate mechanism | **Rebut** | Asymmetric role instructions are the mechanism; interaction is not required; but mechanism statement should be reworded |
| 4 — No power analysis | **Empirically open** | +0.10 is a substantive threshold; statistical significance is separate; needs pre-specified test before execution |
| 5 — DC override suppresses baseline | **Rebut (partial concede)** | DC=0.0 is structural; honest_lift corrects; but primary hypothesis should be stated against honest lift |
| 6 — ETD constraint not locked | **Concede** | ETD instruction text must appear in EXECUTION_PLAN.md before any agent run |
| 7 — Generator fingerprinting | **Rebut** | Fingerprinting affects all conditions equally; lift comparison is still valid; external_cases_v3.json provides cross-source check |
| 8 — Category field leakage | **Concede** | This must be confirmed closed before any agent run; high-severity |
| 9 — DRQ filter not in scoring | **Concede** | Filter must be pre-specified before execution |
| 10 — Convergence not implemented | **Concede** | Add to scoring engine or lock a post-processing schema |

### Overall Verdict

The experimental design is sound in its core scoring logic. Four issues require action before execution begins (Issues 1, 6, 8, 9 — measurement inflation, unlocked ETD constraint, category leakage, and missing DRQ filter). Two issues require acknowledgment in reporting but do not block execution (Issues 3, 5 — mechanism restatement and honest lift primacy). Issues 4, 7, 10 are lower severity and can be addressed in the execution plan with locked specifications.

Overall design position: **empirical_test_agreed** — the design can produce interpretable results if the four pre-execution gaps are closed, and the primary hypothesis can be evaluated, but the test is not clean until the ETD constraint is locked, the category leakage is confirmed closed, and the DRQ filter is pre-specified.
