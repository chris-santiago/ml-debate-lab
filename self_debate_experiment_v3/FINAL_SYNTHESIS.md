# Final Synthesis — Self-Debate Experiment v3

---

## What the Benchmark Tested

v3 evaluated whether structuring automated ML peer review as an adversarial debate improves performance over a single-pass baseline. Four conditions were tested on 49 synthetic ML critique scenarios spanning broken baselines, metric mismatches, hidden confounders, scope-intent misalignments, defense_wins cases (correct defenses that should be exonerated), and real-world deployment framings.

The core question: does adversarial structure — a Critic producing an issue list, a Defender responding point-by-point, an Adjudicator resolving contested claims — produce better reviews than a single agent reviewing alone?

The benchmark used six scoring dimensions (IDR, IDP, DC, DRQ, ETD, FVC), pre-registered hypotheses and rubric before any agent run, and three independent runs per case to measure within-run stability.

---

## Whether the Protocol Worked

**On the pre-registered criteria: yes, clearly.**

All three primary hypotheses were confirmed:
- Benchmark mean: 0.975 (threshold: 0.65) ✓
- Case pass rate: 93.9% (threshold: 75%) ✓
- Lift over baseline: +0.341 raw / +0.127 corrected (threshold: +0.10) ✓

The failure attribution breakdown from isolated_debate runs (n=147) confirms the protocol is highly reliable: 137/147 runs (93.2%) have attribution=none (case passed). Only 3 runs carry agent attribution and 7 are ambiguous.

**On the substance of what was proven: more limited.**

The benchmark is too easy to discriminate between conditions on the dimensions most central to the protocol's theoretical justification. IDR = IDP = 1.0 for all four conditions including baseline — the baseline finds every planted issue and avoids every false positive as reliably as any debate condition. The debate protocol's content advantage over baseline on IDR + IDP + FVC (excluding ETD and structural overrides) is exactly +0.000.

The confirmed lift breaks down as:
- Structural overrides (DC=0.0, DRQ cap): +0.214 of the raw lift — definitional, not empirical
- ETD prompt-engineering effect: most of the remaining fair-comparison lift (+0.053 total on IDR/IDP/ETD/FVC, ~+0.040 attributable to ETD given the +0.000 on the non-ETD fair dims)
- DRQ adversarial exchange advantage: +0.024 (directional, p=0.087)
- IDR/IDP/FVC content advantage: +0.000

The protocol's empirical contribution at this benchmark level is narrow: it reliably produces more precise verdict typing (DRQ) and, where the adjudicator prompt includes ETD-forcing instructions (ensemble), better empirical test designs. Neither of these is the originally hypothesized advantage (catching issues a single reviewer would miss).

---

## Where It Failed and Why

Three cases fail isolated_debate (rwf_003, rwf_005, rwf_008 — all real_world_framing, all hard difficulty):

**rwf_003**: Adjudicator produced `mixed` verdict (not a valid verdict type) across all 3 runs. Agent label error — the adjudicator got the substance right but used an output format that the scorer correctly rejected. The ensemble synthesizer, constrained to emit a valid verdict type, scores 1.000 on this case. This is a prompt-engineering failure, addressable by adding explicit verdict-type validation to the adjudicator prompt.

**rwf_005, rwf_008**: Isolated debate adjudicator voted `critique_wins` without producing an empirical test on cases where the ideal resolution is `empirical_test_agreed`. Attribution: ambiguous. The critique was correct, the verdict was acceptable — but the adjudicator chose the second-best resolution and left no empirical test specification. Both cases pass in multiround (mean=1.000), where the adversarial exchange structure pushes agents toward specifying a test rather than declaring outright failure. The failure mode is not content error but missed resolution precision — addressable by adding the ETD-forcing instruction to the isolated debate adjudicator.

The absence of any IDR or IDP failures across 147 runs is itself a finding: no run failed because the protocol missed an issue or raised a false positive. Every failure was at the verdict/ETD layer, not the issue identification layer.

---

## Whether It Beat Both Baseline and Ensemble

**Versus baseline**: Yes, decisively, on pre-registered criteria. Lift is statistically significant (p < 0.001) and survives correction for structural overrides. The practical distinction: the baseline can identify issues and reach valid verdicts but cannot produce structured debate artifacts (typed resolution quality, empirical test designs). Whether that distinction matters depends on how the output is consumed.

**Versus the compute-matched ensemble**: No, not meaningfully. Ensemble mean = 0.993 vs. isolated = 0.975; the difference (−0.018) is not significant (p = 0.951). The ensemble outperforms isolated debate on ETD (1.000 vs. 0.841) and achieves a higher pass rate (97.9% vs. 93.9%), but these advantages are explained by the ETD-forcing instruction in the ensemble synthesizer, not by multi-agent consensus. The secondary hypothesis (debate outperforms ensemble on mixed cases) was disconfirmed — ensemble is better on mixed cases (1.000 vs. 0.958), driven by the same ETD forcing effect.

If the isolated debate adjudicator received the same ETD-forcing instruction as the ensemble synthesizer, the ETD gap would likely close and the conditions would become statistically indistinguishable. The ensemble is not a better architecture — it has a better-specified prompt for ETD production.

---

## Multiround vs. Isolated: Which Architecture, Which Dimensions

**Multiround is better, but barely.**

Multiround mean = 0.986 vs. isolated = 0.975 (+0.012, 95% CI: [0.000, +0.027], p = 0.087). Not statistically significant at α = 0.05.

The advantage is structurally concentrated:
- **DRQ**: +0.024 (0.980 vs. 0.956) — the adversarial exchange produces more precisely typed verdicts
- **ETD**: +0.111 (0.952 vs. 0.841) — the multiround condition's adversarial structure predictably pushes agents toward empirical test resolution on borderline cases

The DRQ advantage is the theoretically meaningful one: it reflects the adversarial exchange architecture actually doing what it's designed to do — forcing convergence on the most precise resolution type, not just any acceptable resolution. The ETD advantage partially reflects the same mechanism (adversarial pressure toward "let's test this" rather than "critique wins") but is also confounded by prompt differences.

Multiround operated with remarkable efficiency: 91.5% of runs resolved in a single debate round (mean = 1.03 rounds). This means multiround is functionally close to isolated debate plus better adjudication — the multi-round capability was rarely exercised because most cases resolved immediately.

**Limitation on this comparison**: Multiround uses orchestrator adjudication rather than ml-lab's canonical agent-consensus adjudication. If agent-consensus is a genuine performance feature, the measured multiround advantage is a lower bound.

---

## What Changes for v4

The core protocol is validated. These are the concrete improvements warranted by the evidence:

1. **Harder benchmark**: The most important change. IDR=IDP=1.0 at baseline means the current cases are too easy to measure debate's hypothesized advantage. v4 needs cases where baseline IDR < 0.9 or FVC < 0.8. Target at least 20 "discriminative" cases where baseline fails on issue identification.

2. **ETD-forcing instruction on isolated debate adjudicator**: Closes the ETD gap between isolated and ensemble with a single prompt change. Expected to bring isolated debate ETD from 0.841 to ~0.950+, closing most of the ensemble advantage.

3. **Explicit verdict-type validation**: The rwf_003 failure (verdict=`mixed`) is preventable by requiring the adjudicator to emit only one of the defined verdict types. Add an output schema constraint or structured output specification.

4. **Canonicalize ETD output schema**: The scorer bug (two incompatible ETD key schemas across runs) cost 5 cases before detection. Enforce structured output for ETD specifications in agent prompts with an explicit schema.

5. **Log entry script**: Replace ad-hoc INVESTIGATION_LOG entries with a `log_entry.py` script (Issue 4 in POST_MORTEM.md). All 6 batch formats were non-compliant with the ml-lab logging spec.

6. **Agent-consensus adjudication for multiround**: To test the canonical ml-lab multiround protocol rather than orchestrator adjudication. This would make the multiround advantage estimate more interpretable.

7. **Commit raw outputs before scoring**: The isolation breach re-runs (Issue 3) left no git record of what was overwritten. A post-Phase-6 commit creates a tamper-evident checkpoint.

---

## Concrete Recommendation: When to Trust / Distrust the Protocol

**Trust the protocol for:**
- Cases involving defense_wins detection (correct exoneration): 11/11 perfect, all conditions
- Issue identification on well-posed critique scenarios: IDR=1.0 everywhere, zero false positives
- Producing structured verdict artifacts (typed resolution, ETD specification) when the adjudicator/synthesizer is explicitly instructed to do so
- Stability: within-run std = 0.0024 (isolated), 0.0000 (multiround, ensemble, baseline) — results are highly reproducible

**Distrust the protocol (or verify separately) for:**
- Detecting subtle issues a capable single reviewer would miss: no evidence this happens on current benchmark difficulty; the baseline matches debate on IDR/IDP
- Verdict-type precision in isolated debate: two cases failed by choosing an acceptable but non-ideal resolution (critique_wins instead of empirical_test_agreed) — fixable with ETD-forcing instruction
- Cases requiring unusual verdict types: the adjudicator can produce `mixed` (an invalid type) — add output validation
- Claims of generalization: the external validation establishes non-degradation, not a performance boundary

The honest summary: the protocol is a validated evaluation framework that reliably produces structured, consistent reviews. Its demonstrated advantage over baseline is in verdict precision (DRQ) and structured empirical test design (ETD) — both prompt-engineering effects at this benchmark level. It does not demonstrably catch more issues than a careful single reviewer on these cases. The value proposition in production is the structured output format and adversarial pressure toward empirical resolution, not superior issue detection.

---

## Complete Artifact Inventory

### Raw data
| File | Description |
|------|-------------|
| `v3_raw_outputs/` (588 files) | Per-run agent outputs for main benchmark (critic_raw, defender_raw, adjudication_raw, verdict, issues_found, empirical_test) |
| `v3_raw_outputs/ext_*.json` (192 files) | Per-run agent outputs for external validation cases |
| `INVESTIGATION_LOG.jsonl` | Merged execution log from all 7 batches (324 entries) |

### Scored results
| File | Description |
|------|-------------|
| `v3_results.json` | Per-case scores: all 4 conditions × 3 runs. Primary results source. |
| `v3_results_eval.json` | Evaluation-format scores (pass/fail, found/missed issues per case) |
| `v3_external_results.json` | Per-case scores for 16 external validation cases |

### Computed statistics
| File | Description |
|------|-------------|
| `stats_results.json` | Bootstrap CIs (10k resamples), Wilcoxon tests, dimension aggregates, failure attribution |
| `sensitivity_analysis_results.json` | Corrected lift (DC=0.5, DRQ uncapped), fair-comparison vs. protocol-diagnostic stratification |
| `within_case_variance_results.json` | Per-case std across 3 runs, all conditions |
| `difficulty_validation_results.json` | Spearman ρ between difficulty labels and baseline scores |
| `external_stats_summary.json` | External benchmark summary by corpus stratum (published-paper vs. synthetic-grounded) |

### Methodology
| File | Description |
|------|-------------|
| `PREREGISTRATION.json` | Pre-registered hypotheses, rubric, structural overrides. Locked at commit 659c0c3. |
| `evaluation_rubric.json` | Rubric dimension definitions and scoring logic |
| `benchmark_cases_verified.json` | 49 verified benchmark cases |
| `external_cases_v3.json` | 16 external validation cases with provenance metadata |
| `benchmark_verification.json` | External verification decisions (49 KEEP, 1 REVISE) |

### Analysis documents
| File | Description |
|------|-------------|
| `CONCLUSIONS.md` | Per-case table, dimension aggregates, hypothesis verdicts, failure taxonomy, subgroup analysis |
| `SENSITIVITY_ANALYSIS.md` | Corrected lift, dimension stratification, ETD structural note, difficulty label validity |
| `ENSEMBLE_ANALYSIS.md` | Ensemble results, defense_wins criterion, mixed-position analysis, ETD forcing effect |
| `REPORT.md` | Complete technical report (peer reviewed, 2 rounds) |
| `REPORT_ADDENDUM.md` | Production re-evaluation: deployment considerations, operational complexity, failure modes |
| `PEER_REVIEW_R1.md` | Round 1 peer review + response |
| `PEER_REVIEW_R2.md` | Round 2 verification review |
| `FINAL_SYNTHESIS.md` | This document |
| `POST_MORTEM.md` | All execution issues documented (7 issues, scope: active and future) |

### Figures
| File | Description |
|------|-------------|
| `per_condition_comparison.png` | Bar chart: benchmark means with 95% CIs, all 4 conditions |
| `dimension_heatmap.png` | Heatmap: per-dimension aggregate scores across all conditions |
| `sensitivity_analysis_chart.png` | Raw vs. corrected lift comparison |
| `difficulty_scatter.png` | Baseline score vs. difficulty label scatter with Spearman annotation |

### Code
| File | Description |
|------|-------------|
| `self_debate_poc.py` | Scoring engine: all rubric functions, case aggregation, benchmark summary |
| `check_isolation.py` | Post-run isolation breach detector for isolated_debate condition |
| `stats_analysis.py` | Bootstrap CIs, Wilcoxon tests, dimension aggregates, external stratum summaries |
| `sensitivity_analysis.py` | Corrected lift and dimension stratification |
| `extract_within_case_variance.py` | Per-case run-level variance |
| `difficulty_validation.py` | Spearman correlation between difficulty labels and baseline scores |
| `generate_figures.py` | All four figures |
| `coherence_audit.py` | Pre-report numerical consistency check |
| `write_preregistration.py` | Pre-registration artifact generator (run before any agent invocation) |
| `filter_verified_cases.py` | Filters benchmark_cases.json to verified KEEP decisions |
| `validate_cases.py` | Schema and composition validation for benchmark case files |
