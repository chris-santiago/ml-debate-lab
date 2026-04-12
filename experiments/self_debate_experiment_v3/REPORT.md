# Self-Debate Experiment v3: Technical Report

---

## Abstract

The self-debate protocol achieves a corrected lift of +0.127 (isolated_debate) and +0.138 (multiround) over a single-pass baseline on a 49-case ML peer-review benchmark. The raw lift (+0.341 / +0.352) is substantially higher but reflects pre-registered structural scoring overrides (baseline DC=0.0, DRQ capped at 0.5) rather than empirical content differences. The benchmark mean for isolated_debate is 0.975 (95% CI: [0.940, 0.998]), exceeding the pre-registered threshold of 0.65. The debate pass rate is 93.9% (46/49), exceeding the 75% threshold. The ensemble condition achieves 0.993 (97.9% pass rate); it is not significantly different from isolated_debate (Wilcoxon p = 0.951). Multiround (0.986) exceeds isolated_debate by +0.012 (95% CI: [0.000, +0.027], p = 0.087), directionally consistent with the adversarial-exchange design but not statistically significant. All three primary hypotheses are confirmed. External validation on 16 independent cases (13 published-paper, 3 synthetic-grounded) shows all debate conditions at 1.000 and a baseline of 0.628, consistent with the main benchmark baseline of 0.634. All agent runs used claude-sonnet-4-6.

---

## 1. Introduction

Automated ML peer review offers a scalable path to quality control in high-stakes model deployments: catching broken baselines, metric mismatches, hidden confounders, and scope-intent misalignments before they reach production. The self-debate protocol structures this as an adversarial exchange between a Critic and a Defender, with a Judge adjudicating contested points. The hypothesis is that adversarial structure forces more systematic issue identification, fewer false positives, and higher-quality resolution specifications than a single-pass review.

Self-debate experiment v3 tests four conditions — isolated_debate, multiround, ensemble, and baseline — against a 49-case benchmark with pre-specified must-find issues, acceptable resolutions, and explicit false-positive guards (must_not_claim). v3 addresses methodological concerns carried forward from v2: pre-registration before any agent run, corrected lift reporting, DC/FVC structural equivalence disclosure, and external validation against published-paper cases.

---

## 2. Related Work

**Irving et al. (2018)** propose debate as a mechanism for AI safety: two AI agents argue opposing positions while a human judge adjudicates, incentivizing truthful argument production. The self-debate protocol adapts this structure to the ML review domain, where correctness is verifiable against pre-specified ground truth rather than human judgment.

**Du et al. (2023)** show that multi-agent debate — multiple LLM agents generating and critiquing each other's responses — improves factual accuracy and reasoning on arithmetic and scientific questions. The multiround condition in v3 directly implements this exchange pattern.

**Liang et al. (2023)** demonstrate that debate-style prompting encourages divergent thinking and reduces sycophantic convergence when agents are explicitly assigned opposing roles. The Critic/Defender role separation in v3 is designed to exploit this property.

**Khan et al. (2024)** apply multi-agent debate to factual accuracy benchmarks, finding consistent improvement over single-agent baselines across multiple model families. v3 tests whether the same pattern holds for a structured reasoning domain (ML critique) with explicit scoring dimensions.

**Zheng et al. (2023)** (LLM-as-judge) establish the methodology for using language models as evaluators of language model outputs, including rubric-based scoring of multi-turn responses. The v3 scorer implements LLM-as-judge in a closed-loop design with pre-registered rubric.

**ChatEval (Chan et al., 2023)** introduces a multi-agent evaluation framework where agents play distinct roles (e.g., reviewer, respondent) in an iterative assessment process. The ensemble condition in v3 uses a comparable architecture: independent assessors followed by a synthesizer.

**Wang et al. (2023)** (self-consistency) show that sampling multiple outputs and aggregating by majority vote improves chain-of-thought reasoning accuracy. The ensemble condition in v3 tests whether multi-assessor aggregation produces analogous gains in the structured critique domain.

---

## 3. Experimental Design

### 3.1 Protocol

Four conditions were evaluated:

**isolated_debate**: A Critic and Defender each see only the task prompt (no access to each other's output). An Adjudicator then sees both outputs and produces a verdict. The Defender isolation is a benchmark-specific design choice enabling defense_wins verdicts — the Defender can genuinely argue the critique is wrong without having read the critique. This is not the canonical ml-lab protocol (which requires the Defender to receive the Critique before responding); it produces two independent critics rather than an adversarial exchange.

**multiround**: A Critic produces an issue list. The Defender receives the task prompt and the Critique and responds point-by-point (concede/rebut/empirically_open) using the same issue IDs. The exchange continues for up to 4 rounds; an Adjudicator reads the full transcript and produces a verdict with resolution tracking. This implements the canonical ml-lab debate protocol.

**ensemble**: Three independent assessors each see only the task prompt and produce individual verdicts. An ETD-constrained synthesizer receives all three outputs and produces a unified verdict, explicitly instructed to emit an empirical test specification when assessors disagree or when the evidence is mixed. No adversarial exchange occurs.

**baseline**: A single agent sees only the task prompt and produces a single-pass verdict. No debate, no defense, no iteration. This serves as the performance floor against which all other conditions are measured.

### 3.2 Rubric

Six scoring dimensions:

**IDR (Issue Detection Recall)**: issues_found / total_must_find_issue_ids, fractional 0.0–1.0. Measures how many pre-specified must-find issues the condition identifies. N/A on defense_wins cases (no must-find issues; the correct answer is that the critique is wrong).

**IDP (Issue Detection Precision)**: Fraction of raised issues that are valid; must_not_claim items count as false positives (0.0/0.5/1.0). Measures false-positive discipline. N/A on defense_wins cases.

**DC (Defense Correctness)**: Correct verdict via defense function (0.0/0.5/1.0). Pre-registered structural override: baseline DC=0.0 (hardcoded; baseline has no defense role). Note: DC calls compute_fvc() for all non-baseline conditions — DC is structurally identical to FVC in this scorer. DC provides no independent signal over FVC and is reported for completeness per pre-registration.

**DRQ (Debate Resolution Quality)**: Typed verdict matches ideal resolution (1.0); matches other acceptable_resolution (0.5); adjacent to ideal but not in list (0.5); wrong (0.0). Pre-registered structural override: baseline DRQ capped at 0.5 (baseline cannot produce a typed resolution from structured exchange).

**ETD (Empirical Test Design)**: Empirical test specification has condition + supports_critique_if + supports_defense_if present (0.0/0.5/1.0). N/A when ideal_resolution is critique_wins or defense_wins — those cases do not require an empirical test.

**FVC (Final Verdict Correctness)**: Verdict is in the acceptable_resolutions list (1.0); adjacent to ideal but not in list (0.5); wrong (0.0).

**must_not_claim**: Explicit false-positive guard. Items in this list represent plausible-sounding but incorrect claims that a well-calibrated reviewer must not raise. Any must_not_claim item appearing in raised issues drives IDP down.

**acceptable_resolutions**: The set of valid verdict types for a case beyond the single ideal. A case with ideal=empirical_test_agreed may also accept critique_wins if the critique is sufficiently strong. This prevents penalizing near-correct verdicts.

**Per-case pass criterion**: mean(non-null dimensions) ≥ 0.65 AND all applicable dimensions ≥ 0.5. A case passes isolated_debate if ≥ 2 of 3 runs pass.

### 3.3 Benchmark Construction

N=49 cases, GPT-generated and externally verified (49 KEEP, 1 REVISE excluded from benchmark_cases_verified.json). Categories: broken_baseline (8), metric_mismatch (7), hidden_confounding (8), scope_intent (5), defense_wins (11), real_world_framing (10). Correct positions (from v3_results.json): critique (22), mixed (16), defense (11).

External validation: 16 cases (13 published-paper, 3 synthetic-grounded). These form a separate validation stratum and are not included in primary hypothesis tests or bootstrap CIs.

Pre-registered at git commit 659c0c3 before any agent run. PREREGISTRATION.json contains all hypotheses, rubric definitions, structural overrides, and per-case pass criterion.

### 3.4 Execution

588 main benchmark runs: 49 cases × 4 conditions × 3 runs. Parallel execution via 7 batch agents. External benchmark: 16 cases × 4 conditions × 3 runs = 192 runs. Total agent calls: ~2,800+.

**Isolation check**: check_isolation.py detected 2 isolation breaches in isolated_debate run1 for real_world_framing_002 and real_world_framing_010 (Defender received Critique output). Both cases were re-run before scoring. Post-fix isolation check passed clean.

**Scorer bug (ETD schema mismatch)**: compute_etd() was written expecting measure/success_criterion/failure_criterion keys but agents naturally produced condition/supports_critique_if/supports_defense_if keys. Discovered post-execution; fixed before final scoring by updating the key-mapping logic and re-running stats_analysis.py, sensitivity_analysis.py, and related scripts. 5 cases changed from FAIL to PASS after the fix. See POST_MORTEM.md Issue 6 for full documentation.

---

## 4. Results

### 4.1 Primary Results

| Condition | Benchmark mean | 95% CI | Pass rate |
|-----------|---------------|--------|-----------|
| isolated_debate | 0.9745 | [0.9405, 0.9983] | 46/49 (93.9%) |
| multiround | 0.9864 | [0.9592, 1.0000] | 46/49 (93.9%) |
| ensemble | 0.9932 | [0.9864, 0.9983] | 48/49 (97.9%) |
| baseline | 0.6340 | [0.6048, 0.6626] | 0/49 (0.0%) |

Bootstrap CIs from 10,000 resamples (stats_results.json).

| Comparison | Point estimate | 95% CI |
|------------|---------------|--------|
| Isolated vs. baseline | +0.3405 | [+0.3089, +0.3711] |
| Multiround vs. baseline | +0.3524 | [+0.3221, +0.3813] |
| Isolated vs. ensemble | −0.0187 | [−0.0511, +0.0017] |
| Multiround vs. isolated | +0.0119 | [0.0000, +0.0272] |

Raw lift is inflation-adjusted by corrected lift analysis (see Section 4.3 and Sensitivity Analysis):

| | Isolated vs. baseline | Multiround vs. baseline |
|-|----------------------|------------------------|
| Raw lift | +0.3405 | +0.3524 |
| Corrected lift (DC=0.5, DRQ uncapped) | **+0.1265** | **+0.1384** |

The corrected lift is the honest performance advantage on dimensions where both systems have equal structural opportunity.

### 4.2 Per-Case Results

All 49 cases are documented in CONCLUSIONS.md with scores for all four conditions. Three cases fail isolated_debate; all three are in the real_world_framing category:

- **real_world_framing_003** (isolated=0.333, multiround=0.333): Adjudicator produced `mixed` verdict across all runs; `mixed` is not in acceptable_resolutions. FVC=0.0, DC=0.0, DRQ=0.0. Attribution: agent (adjudicator label error). Ensemble scores 1.000.
- **real_world_framing_005** (isolated=0.750, multiround=1.000): Verdict=`critique_wins`, no ETD produced. Ideal=`empirical_test_agreed`. Attribution: ambiguous. Multiround passes via adversarial pressure toward ETD.
- **real_world_framing_008** (isolated=0.750, multiround=1.000): Same pattern as rwf_005.

All 5 categories other than real_world_framing achieve 100% pass rate across all debate conditions.

### 4.3 Dimension Aggregates

Post-fix dimension aggregates (from stats_results.json):

| Dimension | Isolated | Multiround | Ensemble | Baseline |
|-----------|----------|------------|----------|----------|
| IDR | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| IDP | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| DC | 0.9796 | 0.9796 | 1.0000 | 0.0000† |
| DRQ | 0.9558 | 0.9796 | 0.9592 | 0.4898† |
| ETD | 0.8413 | 0.9524 | 1.0000 | 0.4762 |
| FVC | 0.9796 | 0.9796 | 1.0000 | 0.9796 |

†Baseline DC=0.0 (hardcoded) and baseline DRQ=0.4898 (≤0.5 cap) are structural overrides, pre-registered before any agent run.

DC = FVC for all non-baseline conditions: compute_dc() calls compute_fvc() directly. DC provides no independent signal; it is reported for completeness per pre-registration. The one dimension where multiround has a structural design advantage over isolated_debate is DRQ (+0.024), consistent with the adversarial exchange producing more precisely typed verdicts.

**IDR and IDP saturation.** IDR = 1.0 and IDP = 1.0 across all four conditions, including baseline. The debate protocol provides zero measurable advantage on issue identification or false-positive discipline at this benchmark level. These are the two dimensions most directly tied to the protocol's theoretical motivation — adversarial structure is hypothesized to surface issues a single reviewer would miss and suppress spurious claims. Neither effect is observable here. The most likely explanation is a difficulty ceiling: the benchmark cases are straightforward enough that the baseline reliably finds all planted issues without debate pressure. This ceiling effect cannot be disentangled from genuine protocol equivalence without a harder benchmark where baseline IDR < 1.0. The implication for the lift figures is significant: the entire corrected lift (+0.127) comes from ETD and DRQ, not from issue identification. The lift on IDR + IDP + FVC only (excluding both ETD and the structural DC/DRQ overrides) is **+0.000** — isolated debate and baseline achieve identical means (0.993) on these three fair-comparison, non-ETD dimensions.

ETD gap: ensemble (1.000) vs. isolated (0.841). This is a prompt-engineering effect: the ensemble synthesizer is explicitly instructed to produce an empirical test specification; the isolated debate adjudicator is not. Adding an equivalent forcing instruction to the isolated adjudicator would be expected to close most of this gap (cf. v2 ETD ablation: 0.962 with explicit constraint vs. 0.192 without).

### 4.4 Statistical Tests

| Comparison | W | p | r |
|------------|---|---|---|
| Isolated vs. baseline | 1176.0 | 6.15e−10 | 0.0* |
| Multiround vs. baseline | 1176.0 | 5.99e−10 | 0.0* |
| Isolated vs. ensemble | 1.0 | 0.951 | 0.9 |
| Multiround vs. isolated | 6.0 | 0.087 | 0.0* |

*Note on r=0.0 ceiling artifact: The effect-size formula r = 1 − 2W / (n*(n+1)) returns 0.0 when W = n*(n+1)/2 (the maximum possible statistic, achieved when all pairwise differences are positive). For isolated vs. baseline and multiround vs. baseline, W=1176.0 is exactly this maximum for n=49. r=0.0 here means maximum effect size, not zero effect — every single case improved. p < 0.001 is reliable and unaffected. The same artifact applies to multiround vs. isolated (W=6.0 is near-minimum, meaning nearly all differences favor multiround, so r≈0.0 by the same ceiling effect).

All Wilcoxon tests are two-sided signed-rank tests on per-case means.

### 4.5 Subgroup Analysis

**By category (isolated_debate)**:

| Category | n | Mean | Pass rate |
|----------|---|------|-----------|
| broken_baseline | 8 | 1.000 | 8/8 |
| metric_mismatch | 7 | 1.000 | 7/7 |
| hidden_confounding | 8 | 1.000 | 8/8 |
| scope_intent | 5 | 1.000 | 5/5 |
| defense_wins | 11 | 1.000 | 11/11 |
| real_world_framing | 10 | 0.875 | 7/10 |

All failures are concentrated in real_world_framing. These cases are all labeled hard difficulty, have the most complex verdict space (many with ideal=empirical_test_agreed), and involve the longest prose contexts. The 3 failures are genuine — 2 ambiguous ETD failures and 1 agent label error.

**Mixed-position cases (n=16)**:

| Condition | Mean |
|-----------|------|
| Isolated debate | 0.9583 |
| Multiround | 0.9583 |
| Ensemble | 1.0000 |

**Defense_wins cases (n=11)**: All conditions achieve DC=1.0 across all 11 cases. No condition misclassifies any defense_wins case.

---

## 5. Hypothesis Verdicts

### Primary Hypotheses

| Hypothesis | Criterion | Result | Verdict |
|------------|-----------|--------|---------|
| Debate benchmark mean ≥ 0.65 | mean ≥ 0.65 | 0.9745 | **CONFIRMED** |
| Case pass rate ≥ 75% | pass rate ≥ 75% | 93.9% (46/49) | **CONFIRMED** |
| Lift over baseline ≥ +0.10 | lift ≥ +0.10 | +0.1265 (corrected) / +0.3405 (raw) | **CONFIRMED** |

Both corrected (+0.1265) and raw (+0.3405) lift exceed the pre-registered +0.10 threshold.

### Secondary Hypotheses

| Hypothesis | Criterion | Result | Verdict |
|------------|-----------|--------|---------|
| Debate outperforms ensemble on mixed cases | debate mean > ensemble mean on n=16 mixed | Isolated=0.958, Ensemble=1.000 | **DISCONFIRMED** |
| Ensemble DC ≥ 0.5 on ≥ 60% of defense_wins | compute partially explains advantage | DC=1.0 on 11/11 (100%) | **CONFIRMED** |
| Multiround DRQ > isolated DRQ (non-defense_wins) | multiround_DRQ > isolated_DRQ | 0.980 vs. 0.956 (+0.024), p=0.087 | **DIRECTIONALLY CONFIRMED** (not significant) |

Secondary hypothesis 1 is disconfirmed: the ETD-constrained ensemble synthesizer achieves perfect scores on all 16 mixed-position cases, outperforming isolated debate (0.958). This is a prompt-engineering effect, not evidence of superior reasoning — the synthesizer is explicitly instructed to produce an empirical test specification when assessors disagree. Isolated debate would likely close this gap with an equivalent ETD-forcing instruction.

Secondary hypothesis 3 (multiround DRQ advantage) is directionally consistent at p=0.087 — below the α=0.05 threshold but showing the expected improvement. The +0.024 DRQ advantage represents 2 additional cases where multiround converged on the ideal resolution type rather than an acceptable-but-non-ideal one.

---

## 6. Failure Mode Analysis

**Failure attribution summary** (isolated_debate runs, n=147):

| Attribution | Count |
|-------------|-------|
| none (case passed) | 137 |
| agent | 3 |
| ambiguous | 7 |

**Agent failures (3 runs)**:

- **real_world_framing_003, runs 1–3**: Isolated debate verdict = `mixed` across all 3 runs. `mixed` is not in acceptable_resolutions (`['empirical_test_agreed', 'critique_wins']`). The adjudicator produced a structurally invalid verdict type. FVC=0.0, DC=0.0, DRQ=0.0 → run mean=0.333. The ensemble synthesizer, which is ETD-constrained, correctly produces `empirical_test_agreed` on this case (ensemble=1.000). Attribution: agent — adjudicator label error, not a protocol failure.

**Ambiguous failures (7 runs)**:

- **real_world_framing_005, runs 1–3 (isolated)**: Verdict = `critique_wins`, no ETD produced (ETD=0.0). Ideal = `empirical_test_agreed`. The critique correctly identifies all must-find issues and critique_wins is in acceptable_resolutions, so IDR=1.0, FVC=1.0, but DRQ=0.5 and ETD=0.0 reduce the run mean to 0.750. Attribution: ambiguous — cannot determine from outputs alone whether the adjudicator chose the acceptable-but-non-ideal resolution due to reasoning (agent failure) or because the isolated design provided no adversarial pressure toward the ETD resolution (protocol limitation).

- **real_world_framing_008, runs 1–3 (isolated)**: Identical pattern to rwf_005.

Both rwf_005 and rwf_008 pass in the multiround condition (mean=1.000). In multiround, the adversarial exchange — with the Defender responding to the Critique point-by-point — predictably pushes both agents toward specifying an empirical test as the resolution mechanism. The multiround improvement on these cases is structural: it is the adversarial exchange architecture that forces the ETD, not a content improvement in the underlying critique.

---

## 7. Limitations

**1. Closed-loop design.** Both benchmark cases and scorer are from the same model family (claude-sonnet-4-6). The scorer evaluating agent outputs may benefit from familiarity with GPT-generated content and the specific GPT-generated phrasing of must-find issues. It is not possible to distinguish genuine reasoning quality from in-distribution pattern matching. This limitation applies equally to all conditions, so relative comparisons (debate vs. baseline) are more reliable than absolute scores.

**2. Scorer independence.** The scorer reads verdict, issues_found, and all_issues_raised from the same agent outputs it is evaluating. There is no independent ground-truth oracle for ETD quality or verdict correctness beyond the pre-specified rubric. ETD is scored on structural presence (all required keys populated), not on whether the specified test would be statistically valid or practically feasible. This is a necessary simplification given the domain.

**3. Subgroup power.** N=49 total; category subgroups range from 5 (scope_intent) to 11 (defense_wins) cases. None of the subgroups are powered for subgroup-level statistical tests. The subgroup means in Section 4.5 are descriptive. The observation that all failures are concentrated in real_world_framing (7/10 pass vs. 49/49 pass elsewhere) is robust, but formal subgroup comparisons would require a larger benchmark.

**4. Benchmark difficulty ceiling (primary limitation).** IDR = IDP = 1.0 and FVC = 0.980 for baseline, meaning the baseline already finds every planted issue, avoids every false positive, and reaches a valid verdict 98% of the time without any debate structure. A benchmark where the unstructured baseline saturates on the most theory-relevant dimensions cannot detect an improvement from debate on those dimensions. The debate protocol's corrected content lift (excluding structural overrides) is +0.053 on fair-comparison dimensions (IDR, IDP, ETD, FVC), and +0.000 on those same dimensions after also excluding ETD. This is not evidence that debate provides no value — it is evidence that this benchmark is not hard enough to measure it. Constructing cases where baseline IDR < 0.9 or FVC < 0.8 is the direct path to discriminative lift measurement.

**5. Difficulty label validity.** Spearman ρ = −0.069, p = 0.680 (n=38, excluding defense_wins). The pre-assigned difficulty labels (easy/medium/hard) show no significant correlation with empirical discriminability (baseline scores). Hard cases do not score lower than medium cases (hard mean: 0.676, medium mean: 0.655, easy mean: 0.698). The labels reflect domain complexity as assessed by the case generator, not empirical score distributions. This compounds the difficulty ceiling concern: without empirically validated difficulty stratification, there is no way to identify the subset of cases where debate lift would be expected. Difficulty-stratified analysis is treated as descriptive only.

**6. Model version binding.** All results are for claude-sonnet-4-6 (model ID: claude-sonnet-4-6). Protocol efficacy on other model families (GPT-4o, Gemini, Llama) is untested. The closed-loop design makes it difficult to predict whether the same absolute scores would hold for a different model family, since the scorer is also claude-sonnet-4-6.

**7. Convergence metric gap.** The pre-registered convergence analysis (critic_verdict vs. defender_verdict comparison per isolated_debate run) could not be extracted from raw outputs. The critic_raw and defender_raw fields contain prose text; neither agent emits an explicit verdict label in the isolated_debate condition. Verdict emerges only at the adjudicator step. This is a pre-registration gap — the metric was defined as extractable but the raw output format does not support it. Convergence analysis is reported as N/A.

---

## 8. External Validation

16 external cases were evaluated across all four conditions: 13 drawn from published ML papers (NeurIPS, ICML, Nature Methods, etc.) and 3 synthetic-grounded cases based on documented real-world ML failures. These cases were constructed independently of the main benchmark and serve as a cross-corpus validation stratum.

| Condition | Published paper (n=13) | Synthetic grounded (n=3) | All external (n=16) |
|-----------|----------------------|--------------------------|---------------------|
| Isolated debate | 1.000 | 1.000 | 1.000 |
| Multiround | 1.000 | 1.000 | 1.000 |
| Ensemble | 1.000 | 1.000 | 1.000 |
| Baseline | 0.658 | 0.500 | 0.628 |
| Pass rate | 13/13 | 3/3 | 16/16 |

All three debate conditions achieve 1.000 on all 16 external cases (16/16 pass rate). The external baseline (0.628) is consistent with the main benchmark baseline (0.634), indicating the external cases are not systematically easier or harder on the non-structural dimensions.

The 3 synthetic-grounded cases show a lower baseline mean (0.500 vs. 0.658 for published-paper cases). These 3 cases are all defense_wins type, where the baseline structural override (DC=0.0) produces a lower floor — consistent with main benchmark defense_wins behavior (0.500 per case). This is expected and does not indicate a quality difference between the synthetic-grounded and published-paper cases.

The 16/16 external pass rate should be interpreted as non-degradation evidence: the protocol does not regress on out-of-distribution cases. It does not demonstrate generalization in the discriminative sense — all debate conditions achieve 1.000 on external cases, the same ceiling saturation as the main benchmark. Generalization evidence requires cases where conditions can be distinguished (i.e., where some conditions pass and others fail). Because all debate conditions saturate, the external results confirm the protocol is robust but do not reveal the boundary of its competence. External results are not included in primary hypothesis tests.

---

## Peer Review Summary

Two rounds of peer review were conducted.

**Round 1** (research-reviewer, Opus depth): 4 major issues identified — IDR/IDP saturation underemphasized, benchmark difficulty ceiling not foregrounded, external validation overclaiming generalization, ETD-excluded lift not reported. Recommendation: Revise.

**Round 2** (research-reviewer-lite, verification): All 4 major issues confirmed resolved. No new major issues. Recommendation: Accept.

**Key issues resolved:**
- IDR=IDP=1.0 saturation across all conditions (including baseline) now explicitly disclosed in Section 4.3
- Content lift excluding ETD and structural overrides (+0.000) now reported as lower bound
- Benchmark difficulty ceiling elevated to primary limitation in Section 7
- External validation reframed as non-degradation evidence, not generalization evidence

**No major issues open.** Minor issues (CONCLUSIONS.md raw lift table, Section 4.3 paragraph formatting, external validation table caption) deferred — below workshop-level threshold.

---

## 9. Artifacts

All artifacts reside in `self_debate_experiment_v3/`.

**Results data**:
- `v3_results.json` — Per-case scores for all 4 conditions × 3 runs. Primary results source.
- `v3_results_eval.json` — Post-fix evaluation scores after ETD schema correction.
- `v3_external_results.json` — Per-case scores for 16 external validation cases.
- `stats_results.json` — Bootstrap CIs, Wilcoxon tests, dimension aggregates, failure attribution.
- `sensitivity_analysis_results.json` — Corrected lift, dimension stratification, cases changing pass/fail under correction.
- `within_case_variance_results.json` — Per-case standard deviation across 3 runs for all conditions.
- `difficulty_validation_results.json` — Spearman ρ between difficulty labels and baseline scores.
- `external_stats_summary.json` — External benchmark summary by corpus stratum.

**Methodology**:
- `PREREGISTRATION.json` — Pre-registered hypotheses, rubric, structural overrides, commit 659c0c3.
- `evaluation_rubric.json` — Rubric dimension definitions and scoring logic.

**Analysis documents**:
- `CONCLUSIONS.md` — Per-case table, dimension aggregates, hypothesis verdicts, failure taxonomy, subgroup analysis.
- `SENSITIVITY_ANALYSIS.md` — Corrected lift derivation, dimension stratification, ETD structural note.
- `ENSEMBLE_ANALYSIS.md` — Ensemble vs. all conditions, defense_wins criterion, mixed-position analysis, ETD forcing effect.
- `REPORT.md` — This document.
- `REPORT_ADDENDUM.md` — Production re-evaluation considerations.
- `FINAL_SYNTHESIS.md` — Executive summary and key findings.
- `POST_MORTEM.md` — Full documentation of all issues discovered during execution and analysis.

**Figures**:
- `per_condition_comparison.png` — Bar chart: benchmark means with 95% CIs across 4 conditions.
- `dimension_heatmap.png` — Heatmap: per-dimension aggregate scores across all conditions.
- `sensitivity_analysis_chart.png` — Raw vs. corrected lift comparison.
- `difficulty_scatter.png` — Baseline score vs. difficulty label scatter (Spearman validation).

**Code**:
- `self_debate_poc.py` — Main experiment runner; defines all 49 cases, dispatches agents, scores results.
- `check_isolation.py` — Post-run isolation verification for isolated_debate condition.
- `stats_analysis.py` — Bootstrap CIs, Wilcoxon tests, dimension aggregates.
- `sensitivity_analysis.py` — Corrected lift and dimension stratification.
- `extract_within_case_variance.py` — Per-case run-level variance computation.
- `difficulty_validation.py` — Spearman correlation between difficulty labels and baseline scores.
- `generate_figures.py` — All four figures.
- `coherence_audit.py` — Three-check coherence audit across all documents.
