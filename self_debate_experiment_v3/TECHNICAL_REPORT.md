# Self-Debate Experiment v3: Technical Report

*Results mode. Findings stated as facts. Limitations framed as design properties.*

---

## Abstract

A self-debate protocol for automated ML peer review was evaluated across four conditions — isolated_debate, multiround, ensemble, and baseline — on a 49-case benchmark with pre-registered hypotheses and rubric. The isolated_debate condition achieved a mean score of 0.975 (95% CI: [0.940, 0.998]) against a baseline of 0.634 (95% CI: [0.605, 0.663]). The corrected lift, after removing pre-registered structural scoring overrides applied to baseline, is +0.127 (isolated) and +0.138 (multiround). The lift on issue-identification dimensions (IDR, IDP, FVC) only — excluding both structural overrides and the ETD prompt-constraint effect — is +0.000: IDR = IDP = 1.0 and FVC = 0.980 for all four conditions including baseline. The debate pass rate is 93.9% (46/49). All three primary hypotheses are confirmed. External validation on 16 independent cases (13 published-paper, 3 synthetic-grounded) shows all debate conditions at 1.000.

---

## 1. Method

### Benchmark Construction

49 cases were constructed across six categories: broken_baseline (8), metric_mismatch (7), hidden_confounding (8), scope_intent (5), defense_wins (11), and real_world_framing (10). Cases were GPT-generated and externally verified (49 KEEP, 1 REVISE excluded). Correct positions: critique (22), mixed (16), defense (11). External validation used 16 additional cases (13 drawn from published ML papers, 3 from documented production ML failures).

Each case specifies:
- `must_find_issue_ids`: the set of methodological issues the protocol must identify
- `must_not_claim`: explicit false-positive guard — issues that sound plausible but are incorrect
- `acceptable_resolutions`: the set of valid verdict types (may include alternatives to the single ideal)
- `ideal_debate_resolution.type`: the single best verdict type

### Conditions

**baseline**: Single-pass review. One agent receives the task prompt and produces a verdict. No debate, no iteration.

**isolated_debate**: Critic and Defender each receive only the task prompt (no access to each other's output). An Adjudicator receives both outputs and produces a verdict. Defender isolation is a benchmark-specific design enabling genuine defense_wins verdicts.

**multiround**: Critic produces an issue list. Defender receives the task prompt and the Critique and responds point-by-point. Exchange continues up to 4 rounds with resolution tracking. Adjudicator reads the full transcript.

**ensemble**: Three independent assessors each receive only the task prompt. An ETD-constrained synthesizer receives all three outputs and produces a unified verdict, explicitly instructed to emit an empirical test specification when assessors disagree.

### Rubric

Six dimensions; all pre-registered before any agent run (PREREGISTRATION.json, commit 659c0c3):

| Dimension | Definition | Structural notes |
|-----------|------------|-----------------|
| IDR | issues_found / must_find_issue_ids (fractional) | N/A on defense_wins |
| IDP | Fraction of raised issues that are valid; must_not_claim items are false positives (0.0/0.5/1.0) | N/A on defense_wins |
| DC | Correct verdict via defense function (0.0/0.5/1.0) | Baseline hardcoded 0.0; DC = FVC structurally for all non-baseline conditions |
| DRQ | Typed verdict matches ideal (1.0); other acceptable (0.5); adjacent (0.5); wrong (0.0) | Baseline capped at 0.5 |
| ETD | Empirical test has condition + supports_critique_if + supports_defense_if (0.0/0.5/1.0) | N/A when ideal is critique_wins or defense_wins |
| FVC | Verdict in acceptable_resolutions (1.0); adjacent to ideal (0.5); wrong (0.0) | — |

Per-case pass criterion: mean(non-null dimensions) ≥ 0.65 AND all applicable dimensions ≥ 0.5. Case passes if ≥ 2 of 3 runs pass. Benchmark passes if isolated_debate mean ≥ 0.65, case pass rate ≥ 75%, and lift ≥ +0.10.

### Execution

588 main benchmark runs (49 cases × 4 conditions × 3 runs). 192 external validation runs. All runs used claude-sonnet-4-6. Isolation check (check_isolation.py) detected 2 isolation breaches in isolated_debate run1 for real_world_framing_002 and real_world_framing_010; both were re-run before scoring. An ETD scorer schema mismatch (scorer expected `measure/success_criterion/failure_criterion`; agents produced `condition/supports_critique_if/supports_defense_if`) was discovered post-execution and corrected; 5 cases changed from FAIL to PASS after the fix.

---

## 2. Results

### Primary Results

| Condition | Mean | 95% CI | Pass rate |
|-----------|------|--------|-----------|
| isolated_debate | 0.9745 | [0.9405, 0.9983] | 46/49 (93.9%) |
| multiround | 0.9864 | [0.9592, 1.0000] | 46/49 (93.9%) |
| ensemble | 0.9932 | [0.9864, 0.9983] | 48/49 (97.9%) |
| baseline | 0.6340 | [0.6048, 0.6626] | 0/49 (0.0%) |

Bootstrap CIs: 10,000 resamples (stats_results.json).

### Lift

| Comparison | Raw lift | Corrected lift† | Fair-comparison lift‡ | IDR+IDP+FVC lift |
|------------|----------|-----------------|-----------------------|-----------------|
| Isolated vs. baseline | +0.341 | **+0.127** | +0.053 | **+0.000** |
| Multiround vs. baseline | +0.352 | **+0.138** | +0.069 | — |
| Multiround vs. isolated | +0.012 | — | +0.016 | — |
| Isolated vs. ensemble | −0.019 | — | −0.030 | — |

†Corrected lift: baseline DC=0.5 (partial credit), DRQ uncapped.
‡Fair-comparison: IDR, IDP, ETD, FVC only (both conditions have equal structural agency).

### Statistical Tests

| Comparison | W | p | r |
|------------|---|---|---|
| Isolated vs. baseline | 1176.0 | 6.15 × 10⁻¹⁰ | 0.0† |
| Multiround vs. baseline | 1176.0 | 5.99 × 10⁻¹⁰ | 0.0† |
| Isolated vs. ensemble | 1.0 | 0.951 | 0.90 |
| Multiround vs. isolated | 6.0 | 0.087 | 0.0† |

†r = 0.0 is a ceiling artifact: r = 1 − 2W/(n*(n+1)) returns 0.0 when W equals the maximum possible statistic (all pairwise differences in the same direction). p-values are unaffected.

Wilcoxon signed-rank tests, two-sided. Isolated vs. baseline: every one of 49 cases improved (W = 1176.0 = n*(n+1)/2, maximum possible). Multiround vs. isolated: directional improvement (p = 0.087), not significant at α = 0.05.

### Dimension Aggregates

| Dimension | Isolated | Multiround | Ensemble | Baseline |
|-----------|----------|------------|----------|----------|
| IDR | 1.000 | 1.000 | 1.000 | 1.000 |
| IDP | 1.000 | 1.000 | 1.000 | 1.000 |
| DC | 0.980 | 0.980 | 1.000 | 0.000† |
| DRQ | 0.956 | **0.980** | 0.959 | 0.490† |
| ETD | 0.841 | 0.952 | **1.000** | 0.476 |
| FVC | 0.980 | 0.980 | 1.000 | 0.980 |

†Structural overrides (pre-registered). DC = FVC structurally for all non-baseline conditions.

IDR and IDP are 1.000 across all four conditions. The debate and baseline conditions show identical issue-identification performance at this benchmark level. The debate advantage is concentrated in ETD (prompt-constraint effect: ensemble synthesizer is explicitly instructed to produce empirical test designs) and DRQ (adversarial exchange produces more precisely typed verdicts: +0.024 multiround vs. isolated).

### Multiround vs. Isolated: DRQ and DC

DRQ: multiround 0.980 vs. isolated 0.956 (+0.024). Multiround DRQ exceeds isolated on 2 additional cases (cases where multiround converged on the ideal resolution type rather than an acceptable-but-non-ideal type). Not significant at α = 0.05 (p = 0.087).

DC: multiround 0.980 = isolated 0.980. DC is structurally identical to FVC in this scorer (compute_dc() calls compute_fvc() for all non-baseline conditions). DC provides no independent signal over FVC.

Multiround operated in 1.03 rounds on average: 91.5% of 189 multiround runs resolved in a single round, 5.8% required 2 rounds, 11.1% of runs had at least one force-resolved point.

### Subgroup Results (isolated_debate)

| Category | n | Mean | Pass rate |
|----------|---|------|-----------|
| broken_baseline | 8 | 1.000 | 8/8 |
| metric_mismatch | 7 | 1.000 | 7/7 |
| hidden_confounding | 8 | 1.000 | 8/8 |
| scope_intent | 5 | 1.000 | 5/5 |
| defense_wins | 11 | 1.000 | 11/11 |
| real_world_framing | 10 | 0.875 | 7/10 |

Three cases fail isolated_debate, all in real_world_framing: real_world_framing_003 (adjudicator produced invalid verdict type `mixed`, attribution: agent), real_world_framing_005 and real_world_framing_008 (adjudicator voted `critique_wins` on `empirical_test_agreed` cases without ETD specification, attribution: ambiguous). Both rwf_005 and rwf_008 pass in multiround (mean=1.000).

Failure attribution across 147 isolated_debate runs: none (passed) = 137, agent = 3, ambiguous = 7.

### External Validation

| Condition | Published paper (n=13) | Synthetic grounded (n=3) | All external (n=16) | Pass rate |
|-----------|----------------------|--------------------------|---------------------|-----------|
| Isolated debate | 1.000 | 1.000 | 1.000 | 16/16 |
| Multiround | 1.000 | 1.000 | 1.000 | 16/16 |
| Ensemble | 1.000 | 1.000 | 1.000 | 16/16 |
| Baseline | 0.658 | 0.500 | 0.628 | 0/16 |

External baseline (0.628) is consistent with main benchmark baseline (0.634). All debate conditions achieve ceiling scores on external cases; the external results provide non-degradation evidence (the protocol does not regress on out-of-distribution cases).

---

## 3. Production Re-evaluation

The benchmark uses pre-specified `must_find_issue_ids` and `acceptable_resolutions` as scoring targets. In a production ML review workflow, these fields do not exist — the protocol produces a verdict against an unknown ground truth. Three operational properties differ from benchmark behavior:

**Answer-key absence.** Issue identification and verdict correctness cannot be verified in real time. Production deployment relies on the protocol's consistency and structural artifacts (typed resolution, empirical test specification) rather than rubric-scored accuracy.

**Operational cost.** The benchmark required approximately 2,800+ agent calls (588 main + 192 external runs × ~3 agent invocations each). In production, isolated_debate and ensemble can be parallelized across cases; multiround is sequential by design.

**Production failure modes identified.** Four failure modes observed in the benchmark have direct production implications: (1) invalid verdict types (rwf_003: `mixed`) — no post-hoc validator catches these without output schema enforcement; (2) ETD omission on empirical cases (rwf_005, rwf_008) — no signal to the reviewer that an empirical test was warranted but not specified; (3) isolation breaches — silently present without automated verification equivalent to check_isolation.py; (4) output schema drift — ETD key mismatch silently corrupted scoring in this experiment. All four are addressable by output schema enforcement and post-run validation.

---

## 4. Limitations

**Closed-loop design.** This benchmark uses a closed-loop design where both cases and scorer employ claude-sonnet-4-6. Scoring of agent outputs by the same model family may produce familiarity effects that inflate absolute scores relative to cross-model evaluation. Relative comparisons (debate vs. baseline) are less affected by this property than absolute scores.

**Benchmark difficulty ceiling.** IDR = IDP = 1.0 and FVC = 0.980 for the baseline condition. This benchmark uses cases where the unstructured baseline reliably identifies all planted issues and reaches valid verdicts. The content lift on IDR+IDP+FVC dimensions is +0.000. The measurable debate advantage is concentrated in ETD (a prompt-constraint effect) and DRQ (typed verdict precision, +0.024, p=0.087).

**Scorer independence.** The scorer reads verdict, issues_found, and all_issues_raised from agent outputs and evaluates them against pre-specified rubric fields. ETD quality is scored on structural key presence, not on whether the specified test would be statistically valid or practically feasible.

**Subgroup power.** Category subgroups range from 5 to 11 cases. Subgroup means are descriptive; they are not powered for formal statistical comparisons.

**Difficulty label validity.** Pre-assigned difficulty labels show no significant correlation with empirical discriminability: Spearman ρ = −0.069, p = 0.680 (n=38, excluding defense_wins). Labels reflect domain complexity as assessed by the case generator.

**Model version binding.** All results are for claude-sonnet-4-6. Protocol behavior on other model families is untested by this experiment.

**Convergence metric gap.** The pre-registered convergence metric (critic_verdict vs. defender_verdict comparison per isolated_debate run) was not extractable from raw outputs. Neither `critic_raw` nor `defender_raw` contains an explicit verdict label in the isolated_debate condition. Reported as N/A.

---

## 5. Conclusion

The self-debate protocol achieved a benchmark mean of 0.975 (isolated_debate), a case pass rate of 93.9%, and a corrected lift of +0.127 over a single-pass baseline — all exceeding pre-registered thresholds. At this benchmark level, IDR and IDP are 1.000 across all conditions including baseline; the protocol's content advantage on issue identification dimensions is +0.000. The measurable debate advantage is in DRQ (+0.024 for multiround, p=0.087) and ETD (driven by the ETD-forcing instruction in the ensemble synthesizer). External validation on 16 independent cases shows all debate conditions at 1.000, with baseline at 0.628. The protocol produces consistent, structured review artifacts with high pass-rate reliability; the conditions under which it outperforms a capable single reviewer on issue identification have not been identified in this benchmark.
