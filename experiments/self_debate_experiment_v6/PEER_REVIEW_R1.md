# Peer Review R1: v6 Investigation Report

**Reviewer:** Automated peer review (Claude Opus 4.6)  
**Date:** 2026-04-11  
**Document reviewed:** `self_debate_experiment_v6/REPORT.md`  
**Supporting materials consulted:** `HYPOTHESIS.md`, `CONCLUSIONS.md`, `SENSITIVITY_ANALYSIS.md`, `ENSEMBLE_ANALYSIS.md`, `v6_hypothesis_results.json`, `v6_results.json`, `v6_analysis.py`, `pilot_results.json`  
**Review depth:** Full  
**Focus areas:** (1) conclusion–data alignment, (2) null/positive result framing, (3) statistical methodology, (4) limitations completeness

---

## 1. Summary

This report evaluates whether an adversarial LLM debate protocol (critic + defender + adjudicator) improves ML methodology review quality over single-pass baseline critique, using 120 benchmark cases (80 regular, 40 mixed) scored across 6 conditions with 3 runs each (2,160 total outputs). Four pre-registered hypotheses are tested via bootstrap confidence intervals and Wilcoxon signed-rank, with GPT-4o as the cross-vendor scorer. All formal hypotheses fail or are inconclusive; the strongest descriptive finding is an ensemble IDR advantage (+0.1005 over baseline) from union-of-issues pooling across 3 independent assessors. The report recommends replacing adversarial debate with ensemble assessment.

---

## 2. Strengths

**2.1 Rigorous iterative design.** The v6 experiment directly addresses five documented failure modes from prior iterations (v3 ETD-driven lift, v5 baseline ceiling, closed-loop confound, majority-vote IDR suppression, hollow multiround rounds). The Related Work section (lines 20–26) provides clear traceability from each predecessor failure to the corresponding v6 design fix. This level of self-critical iteration is uncommon in applied ML evaluation research.

**2.2 Pre-registration with adaptive threshold.** The H1a threshold formula (`max(0.03, min(0.10, (1.0 - pilot_fc_mean) * 0.5))`) is a thoughtful solution to a real problem: setting a meaningful effect size threshold when baseline difficulty varies across benchmark versions. The formula prevents both trivially passable and structurally impossible thresholds. The pilot calibration step (Phase 3, n=30, 5 ceiling cases discarded) adds credibility.

**2.3 Cross-vendor scoring.** Using GPT-4o as the primary scorer for IDR, IDP, and ETD — when the debate agents are Claude — directly addresses the closed-loop confound that undermined v5 credibility. This is the right structural fix: within-evaluator comparisons are valid as long as scorer bias is condition-independent.

**2.4 Sensitivity analysis is thorough.** The Phase 8 checks (Method A vs B aggregation, threshold sensitivity, IDP extraction diagnostic, hollow-round rate) provide genuine robustness evidence. The Method A/B divergence check (Section 8.1) is especially useful: demonstrating zero divergence under the balanced design preempts a common aggregation concern.

**2.5 Honest null reporting.** The report does not attempt to rescue the failed hypotheses or reframe null results as positive. The abstract leads with the primary negative finding, and the failure mode analysis section provides a clear mechanistic account of why debate does not improve IDR. This intellectual honesty is a significant strength.

**2.6 Union/majority-vote split rule.** The `ENSEMBLE_ANALYSIS.md` provides a well-reasoned justification for using different aggregation rules for recall vs. verdict metrics in the ensemble condition. The asymmetry is principled (maximize recall for recall metrics, preserve precision for verdict metrics) and pre-registered.

---

## 3. Critical Issues

### MAJOR Issues

**3.1 [MAJOR] Unpaired bootstrap inflates confidence interval width by an order of magnitude.**

The `bootstrap_mean_diff()` function in `v6_analysis.py` (lines 39–68) independently resamples the two condition arrays:

```python
s_a = [a[random.randint(0, n_a-1)] for _ in range(n_a)]
s_b = [b[random.randint(0, n_b-1)] for _ in range(n_b)]
```

This is an unpaired (independent-sample) bootstrap. However, the experimental design is fully paired: each of the 80 regular cases is evaluated under every condition. A paired bootstrap should resample the *case-level differences* (or resample case indices and compute the difference within each resampled pair), preserving the within-case correlation that is the primary variance-reduction mechanism of a paired design.

**Empirical verification:** I implemented both approaches from the raw `v6_results.json` data. Results for H1a (isolated_debate minus baseline, regular cases):

| Method | CI | Width |
|---|---|---|
| Paired bootstrap (case-level differences) | [−0.0121, +0.0075] | ~0.020 |
| Unpaired bootstrap (case-level, as implemented) | [−0.1260, +0.1184] | ~0.244 |
| Reported CI (run-level unpaired, one-sided) | [−0.1059, +0.2236] | ~0.330 |

The paired CI is roughly 12–16x narrower than the reported CI. The unpaired resampling treats the two conditions as if they were drawn from independent populations, discarding the within-case pairing that the experimental design was built around.

**Impact on verdicts:** The consequences differ by hypothesis:

- **H1a:** A paired CI of [−0.012, +0.008] still spans zero and the observed lift (−0.0026) is still far below threshold (0.10). The FAIL verdict is *strengthened* — the null result is more precise, not less certain.

- **H2:** The reported CI [−0.1567, +0.0976] is INCONCLUSIVE. A paired bootstrap could narrow this substantially. If the paired CI excluded zero in the ensemble-favored direction, H2 would flip from INCONCLUSIVE to FAIL-for-debate (ensemble statistically superior). This would change the paper's central recommendation from "descriptive suggestion" to "formally supported conclusion."

- **H6:** The FVC_mixed dimension already shows CI excluding zero; paired resampling would tighten the other two dimensions and could change the 1/3 result.

The report's entire statistical apparatus uses the wrong bootstrap variant for a paired design. All CIs, p-values, and verdict determinations are affected.

Additionally, the H1a one-sided CI upper bound (+0.2236) is computed as `diffs[-1]` — the maximum bootstrap sample, not a confidence bound. Reporting the maximum of 10,000 bootstrap draws as a CI endpoint is misleading. A one-sided test should report only the lower bound; if both bounds are desired, use a two-sided CI.

---

**3.2 [MAJOR] FC metric heterogeneity across case types is undisclosed and produces misleading summary statistics.**

The report states that FC = mean(IDR, IDP, DRQ, FVC) and that DRQ/FVC are "flat at 0.7500" across conditions (Section: DRQ/FVC Compression, lines 243–246). Both statements are misleading.

**Defense cases (20/80 regular) have IDR=None and IDP=None.** For these cases, FC = mean(DRQ, FVC) — a 2-dimension composite. For critique cases (60/80), FC = mean(IDR, IDP, DRQ, FVC) — the full 4-dimension composite. The FC metric means different things for different case types, and the report does not disclose this.

**DRQ and FVC are not "flat at 0.7500."** They are bimodally distributed: 1.0 on all critique cases and 0.0 on all defense cases (for baseline, isolated_debate, biased_debate, and ensemble_3x). The 0.75 grand mean is an artifact of the 60/20 composition (60×1.0 + 20×0.0 = 60, divided by 80 = 0.75). Reporting 0.75 as a flat score obscures the fact that no condition correctly resolves any defense case (FC = 0.0 for all 20 defense cases × 3 runs = 60 observations of complete failure).

**Why this matters:** The 20 defense cases contribute FC = 0.0 identically across conditions (except multiround, where 12/60 runs score FC ≈ 0.2). These cases contribute zero discriminative signal while dragging all FC means downward uniformly. A reader cannot assess the IDR/IDP signal quality without knowing that 25% of the "regular" cases are scored on a completely different scale and contribute no between-condition variation.

This does not bias the *between-condition difference* (the zeros cancel in the subtraction), so H1a and H2 verdict directions are preserved. But it does mean:
- The absolute FC values (e.g., baseline = 0.6785) are uninterpretable without knowing the case composition
- The effective sample providing discriminative signal is n=60 critique cases, not n=80 regular cases
- The "DRQ/FVC flat" characterization obscures a complete inability to correctly assess defense cases

---

**3.3 [MAJOR] The recommendation to adopt ensembles is based on an untested comparison and overclaims the evidence.**

The abstract recommends: "replace the adversarial debate protocol with ensemble assessment for methodology review" (line 12). The report acknowledges (line 182) that "This finding was not formally tested against baseline (the pre-registered H2 tests ensemble vs. isolated_debate)."

The chain of reasoning is: ensemble IDR (0.7717) > baseline IDR (0.6712), a descriptive gap of +0.1005. But this comparison has no confidence interval, no formal test, and no pre-registered hypothesis. The formal test that *was* run (H2: ensemble vs. debate) was INCONCLUSIVE. The recommendation to "replace" the debate protocol with ensembles thus rests on a descriptive observation from an untested comparison, presented in the same report whose formal tests are all null or inconclusive.

This is overclaiming. The appropriate framing is: "ensemble shows a promising descriptive IDR advantage over baseline that warrants formal testing in a future experiment," not a recommendation to replace the debate protocol. The strength of the recommendation language in the abstract exceeds what the statistical evidence supports.

---

### MINOR Issues

**3.4 [MINOR] Pre-registration audit trail is incomplete.**

`HYPOTHESIS.md` (lines 249–250) contains two unfilled fields:

```
| Committed to git before Phase 5 | TBD |
| Phase 5 start date | TBD |
```

These fields exist specifically to provide verifiable evidence that hypotheses were locked before data collection began. Leaving them as "TBD" undermines the pre-registration's evidentiary value. A reviewer has no way to verify that the thresholds, scoring rules, and pass criteria were not modified after observing results.

**3.5 [MINOR] H5 status inconsistency between REPORT.md and CONCLUSIONS.md.**

`REPORT.md` (line 144) lists H5 as "N/A" with the justification that the experimental design (GPT-4o as primary scorer) eliminated the closed-loop confound that H5 was designed to measure. `CONCLUSIONS.md` (line 82) lists H5 as "DEFERRED to Phase 9" with the statement that "IDR/IDP/ETD agreement between GPT-4o (primary) and Claude (secondary) has not been quantified."

The REPORT.md justification is reasonable: if Claude was never used as a scorer, the cross-model comparison cannot be performed. However, the two documents disagree on both the status label and the rationale. An outside reader encountering CONCLUSIONS.md first would believe Phase 9 work remains; encountering REPORT.md first would believe H5 was structurally resolved. Reconcile to a single status with a single justification.

**3.6 [MINOR] No multiple comparison correction across 8 hypothesis tests.**

The experiment tests 8 distinct comparisons (H1a, H1b, H2-regular, H2-mixed, H3, H4, H6-IDR, H6-IDP_adj, H6-FVC_mixed). No family-wise error rate correction (Bonferroni, Holm-Bonferroni, or FDR) is applied. Because all primary results are null, this does not inflate the false positive rate for *this* experiment — but it would matter if any test had been significant. The H6 FVC_mixed result (p=0.0000) would survive any reasonable correction, but the practice of running 8 uncorrected tests should be acknowledged.

**3.7 [MINOR] IDR_novel data exists but is not reported.**

`HYPOTHESIS.md` (lines 44–48) specifies that `idr_novel` (novel valid concerns the debate raised beyond the documented ground truth) should be "reported separately." The `v6_results.json` contains `idr_novel_means` data per condition. The report does not mention these results. This is a pre-registration commitment to report a specific analysis that has not been honored.

**3.8 [MINOR] Within-case variance count discrepancy.**

The report (line 203) states "Twenty-three case-condition pairs exceed the within-case variance threshold of 0.05." The `v6_hypothesis_results.json` lists `n_high_variance: 23` but the accompanying `high_variance_cases` array contains only 20 entries (all multiround). The 3 non-multiround high-variance cases mentioned in the report table (line 211: "Other Conditions: 3") are not enumerated in the JSON artifact. Either the JSON is missing entries or the count is wrong.

---

## 4. Recommendations

1. **[Bootstrap Methodology — Issue 3.1]** Reimplement `bootstrap_mean_diff()` as a paired bootstrap: resample case indices (with replacement), compute the within-case difference for each resampled pair, then take the mean of differences. Rerun all hypothesis tests (H1a, H1b, H2, H6) with the corrected implementation. Report both the corrected CIs and note the change from the draft analysis. For H1a, also fix the one-sided CI reporting to present only the lower bound (or switch to a two-sided CI if both endpoints are desired). *Priority: blocks all quantitative conclusions.*

2. **[FC Heterogeneity Disclosure — Issue 3.2]** Add a subsection to the Experimental Design or Results section explicitly documenting that FC is computed over 2 dimensions (DRQ, FVC) for defense cases and 4 dimensions for critique cases. Report the critique-only FC separately from the all-regular FC. Replace "DRQ and FVC are flat at 0.7500" with the actual distribution: DRQ = FVC = 1.0 on all critique cases, 0.0 on all defense cases, with the 0.75 mean being a composition artifact. Report the n=60 critique-case lift alongside the n=80 all-regular lift.

3. **[Ensemble Recommendation — Issue 3.3]** Downgrade the abstract recommendation from "replace the adversarial debate protocol with ensemble assessment" to a descriptive finding that motivates future work: e.g., "ensemble union-of-issues pooling shows the largest descriptive IDR advantage of any condition; formal testing of ensemble vs. baseline is recommended for v7." Alternatively, run the formal bootstrap test of ensemble vs. baseline (this is straightforward with the existing data) and report it as a post-hoc comparison with appropriate caveats.

4. **[Pre-Registration Completion — Issue 3.4]** Fill in the two TBD fields in `HYPOTHESIS.md` with the actual git commit hash and Phase 5 start date. If these cannot be verified from git history, note this gap explicitly.

5. **[H5 Status Reconciliation — Issue 3.5]** Align `REPORT.md` and `CONCLUSIONS.md` on a single H5 status and rationale. If H5 is N/A because Claude was not used as a scorer, update CONCLUSIONS.md to match. If Phase 9 cross-vendor validation is still planned (e.g., scoring a subset with Claude for comparison), keep DEFERRED and update REPORT.md.

6. **[IDR_novel Reporting — Issue 3.7]** Add a subsection or table reporting the `idr_novel` means per condition, as committed in `HYPOTHESIS.md`. If the data shows no meaningful signal, a brief statement is sufficient. The pre-registration commits to reporting the analysis, not to finding a significant result.

7. **[Multiple Comparisons — Issue 3.6]** Add a sentence to the Statistical Methods section acknowledging the number of tests performed and noting that no family-wise correction was applied. State that all primary results are null and the single significant sub-test (H6 FVC_mixed) survives Bonferroni correction at the 8-test level (0.0000 < 0.05/8 = 0.00625).

8. **[Variance Count — Issue 3.8]** Reconcile the `n_high_variance` count in `v6_hypothesis_results.json` with the enumerated list. Either add the 3 missing non-multiround entries to the JSON or correct the count.
