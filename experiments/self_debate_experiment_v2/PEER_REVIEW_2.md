# Peer Review #2: Self-Debate Protocol v2 — Technical Report

**Review date:** 2026-04-04
**Review depth:** Full
**Calibrated to:** Internal technical report / workshop paper submission
**Scope:** Issues not covered by the prior review (PEER_REVIEW.md)

---

## 1. Summary

This report evaluates a multi-agent LLM debate protocol (Critic + Defender + Judge) against a single-pass baseline on 20 synthetic ML reasoning tasks, scoring on six rubric dimensions. The headline finding (+0.586 lift) is qualified by the authors' own post-experiment analysis to +0.335–0.441. A follow-on ensemble experiment narrows the debate protocol's unique advantage to empirical test design forcing (ETD), while showing that compute-matched parallel assessors can replicate most other advantages.

---

## 2. Strengths

**Exemplary self-correction process.** The post-experiment adversarial review (SENSITIVITY_ANALYSIS.md) is genuinely commendable. The authors discovered that their own scoring code mechanically depressed baseline scores, quantified the effect across five scenarios, and revised their headline claims downward. This level of intellectual honesty is rare and substantially increases trust in the remaining findings.

**Clean decomposition of the ETD mechanism.** The ensemble follow-on experiment (ENSEMBLE_ANALYSIS.md) produced a genuinely informative result: the debate protocol's forcing function for empirical test design is a structurally distinct output that parallel assessors do not produce. The observation that ensemble cases scored ETD=0.0 because "parallel assessors stop at 'the critique is correct' rather than 'here is the test that would resolve it'" is a well-identified mechanistic finding that could generalize beyond this benchmark.

**Failure mode taxonomy is precise and actionable.** The three failure modes in Section 4.3 are specific, tied to individual cases, and accompanied by concrete remediation proposals. The reasoning/label disconnect (Failure Mode 1) is a genuinely novel observation about LLM agent behavior under role constraints.

---

## 3. Critical Issues

### Major Issues

**[MAJOR] Debate protocol scores are suspiciously near-ceiling across 20 diverse cases.**
The debate protocol scores 1.000 on 14 of 20 cases and never falls below 0.833. Four of six rubric dimensions (IDR, IDP, DRQ, FVC) are at a perfect 1.000 aggregate. This ceiling pattern makes it impossible to discriminate performance quality across cases — the rubric has no dynamic range for the treatment condition.

This matters because the report's analysis of "where the protocol adds the most value" (Section 4.1) and "where it adds limited value" (Section 4.2) relies entirely on variation in the *baseline* scores, not on variation in the debate scores. The debate protocol's own scores carry zero discriminative information. A rubric that cannot distinguish "protocol worked perfectly on an easy case" from "protocol worked perfectly on a hard case" is measuring below its resolution. Either the tasks are too easy for the protocol, the rubric granularity is too coarse (0.0/0.5/1.0), or the scoring is too lenient — but one of these must be true, and the report does not acknowledge or investigate which.

**[MAJOR] IDP=1.000 tied across debate and baseline is an anomalous non-finding that undermines rubric validity.**
Issue Discovery Precision is 1.000 for both the debate protocol and the single-pass baseline across all 15 non-defense_wins cases (Section 2.3). This means neither system ever raised a single invalid issue across 15 cases. For a dimension designed to measure precision of critique, this is diagnostically empty — it provides zero signal for any comparison.

The report notes this in passing ("IDP is tied at 1.000") but does not explore the implication: if IDP never fires, the rubric cannot detect false-positive issue generation, which is one of the most important failure modes in adversarial critique systems. The Critic agent is structurally incentivized to find issues; a rubric that never catches it raising spurious ones either measures the wrong thing or the benchmark cases are too clean. This is a construct validity concern that goes unaddressed.

**[MAJOR] The "ETD is the structural advantage" claim rests on a confound in how ETD is scored for the ensemble.**
The report's central surviving claim (Section 8, Conclusion) is that the debate protocol's advantage over the ensemble concentrates in ETD. But the ensemble's ETD=0.0 scores arise because the ensemble was not instructed to produce empirical test designs. ENSEMBLE_ANALYSIS.md acknowledges this: "This is not a reasoning quality failure. It's a missing output constraint."

This is a critical confound. The debate protocol's ETD advantage may reflect nothing more than the fact that the debate prompt explicitly requires a resolution step involving test design, while the ensemble prompt does not. The report treats this as evidence that the *debate architecture* (adversarial forcing function) produces ETD, but the simpler explanation — the debate prompt *asks for* ETD and the ensemble prompt does not — is not ruled out. ENSEMBLE_ANALYSIS.md even proposes the fix: "add an explicit output constraint to the synthesizer." Until this ablation is run, the ETD finding is confounded with prompt design.

**[MAJOR] Inconsistent handling of IDP across defense_wins cases between debate and ensemble conditions.**
For the debate protocol, IDP is scored N/A on all defense_wins cases (Section 1.2). But for the clean ensemble, IDP *is* scored on defense_wins cases (visible in `clean_ensemble_results.json`: defense_wins_001 gets IDP=0.5, defense_wins_002 gets IDP=0.5, etc.). These scores are included in the ensemble mean calculations.

This is an asymmetric rubric application across conditions. The debate protocol's defense_wins means are computed over 3 dimensions (DC, DRQ, FVC), while the ensemble's defense_wins means are computed over 4 dimensions (IDP, DC, DRQ, FVC). When the ensemble raises minor caveats on an exonerated case (IDP=0.5), it gets penalized in a way the debate protocol structurally cannot be. The comparison "debate achieves higher-precision exonerations" (Section 3.2 qualification) is partly an artifact of this asymmetric N/A treatment. To make the comparison fair, IDP must be scored for both conditions or excluded for both.

### Minor Issues

**[MINOR] The "convergence" metric is operationally shallow and unreproducible.**
Beyond being undefined (flagged by the prior review), convergence values appear to be binary (0.5 or 1.0) for all 20 cases, suggesting they measure only whether the Critic and Defender reached the same verdict type — not any graded agreement on issues, severity, or proposed tests. If convergence is merely "did both agents output the same verdict label," it is redundant with a simple verdict-agreement indicator and should not be labeled "convergence," which implies something richer. Additionally, the values are not derivable from the scoring data in the results JSON; the mapping from transcript content to convergence score is never specified. Without a formal operationalization, this metric is unreproducible.

**[MINOR] The benchmark aggregate mean treats unequal-dimension cases as equal.**
Different cases have different numbers of applicable dimensions. Defense_wins cases are scored on 3 dimensions (DC, DRQ, FVC); critique_wins cases on 5 (IDR, IDP, DC, DRQ, FVC); empirical_test_agreed cases on 6 (all). A defense_wins case that scores 1.000 had to get only 3 things right; a hidden_confounding case scoring 1.000 had to get 6 things right. The benchmark aggregate implicitly overweights cases with fewer applicable dimensions, because they have less opportunity to lose points. Since defense_wins cases have the fewest dimensions AND the largest deltas (+1.000), this weighting systematically inflates the debate's aggregate advantage. A dimension-level aggregate (average each dimension separately across applicable cases, then average dimensions) would be more defensible.

**[MINOR] The report conflates "the protocol" with prompt-specific agent behavior.**
Throughout the report, findings about specific agent prompts are generalized to "the protocol." The reasoning/label disconnect (Section 4.3, Failure Mode 1) is attributed to "the Defender role" having structural label bias — but this could equally be a property of the specific Defender prompt wording, the model version, or the particular case framing. The two-pass fix (Section 6, Recommendation 1) is a prompt change, not a protocol change, yet the report frames it as resolving a protocol-level failure. This conflation obscures an important question: how sensitive are the results to prompt wording?

**[MINOR] The clean ensemble's metric_mismatch_002 all-zero result is unexplained.**
In `clean_ensemble_results.json`, metric_mismatch_002 scores 0.0 on every dimension. This is the only non-defense_wins case where the ensemble produced a completely incorrect verdict. This catastrophic failure mode for the ensemble is not discussed anywhere in ENSEMBLE_ANALYSIS.md or the main report. The ensemble's 0.754 mean is substantially affected by this single case, but the case-level failure is never analyzed. Was it a synthesis failure? Did all three assessors agree on defense_wins? This deserves the same failure mode analysis the report gives to the debate protocol's real_world_framing_001.

**[MINOR] No formal benchmark verdict re-evaluation against corrected baseline.**
The report states the benchmark passes all three criteria, but the formal pass/fail table (Section 2.1) uses uncorrected numbers. The sensitivity analysis shows that with corrected baseline scoring, the baseline mean rises to 0.529 and baseline pass count rises to 9/20. The report never re-evaluates the three benchmark criteria against the corrected baseline. While the debate protocol still clears all thresholds, the *margin* changes substantially (lift drops from +0.586 to +0.441), and the presentation should be explicit about which numbers the formal verdict is based on. Leading with a formal verdict on uncorrected numbers with a post-hoc qualification buried in the abstract is misleading.

---

## 4. Recommendations

1. **[Rubric Dynamic Range]** Investigate why the debate protocol scores at ceiling on 14/20 cases. Either increase rubric granularity (e.g., move from 0.0/0.5/1.0 to a finer scale), add harder benchmark cases that stress the protocol below 0.9, or introduce partial-credit scoring for IDR (fraction of must-find issues found with severity weighting). The current rubric cannot support claims about *where* the protocol excels because it cannot distinguish degrees of excellence.

2. **[ETD Ablation — Critical]** Run the ensemble with an explicit output constraint requiring empirical test proposals when issues are identified. If ensemble ETD scores rise to match the debate protocol's, the "adversarial forcing function" claim is falsified — the mechanism is simply the output instruction, not the adversarial architecture. This is the single most important missing ablation.

3. **[IDP Asymmetry]** Harmonize the IDP N/A treatment across debate and ensemble conditions for defense_wins cases. Recompute ensemble defense_wins means excluding IDP (to match the debate condition) and report both. If ensemble defense_wins means rise after this correction, revise the "cleaner exonerations" claim accordingly.

4. **[Formal Benchmark Verdict on Corrected Numbers]** Add a second pass/fail table evaluating all three benchmark criteria against the corrected baseline (DC=0.5, DRQ uncapped). State explicitly which numbers the formal verdict is based on.

5. **[Ensemble Failure Analysis]** Add a failure mode analysis for the clean ensemble's catastrophic failure on metric_mismatch_002. Determine whether this was a synthesis failure or assessor-level failure, and discuss what it implies about ensemble robustness on mixed-position cases.

6. **[Prompt Sensitivity]** Acknowledge that the protocol's performance is confounded with specific prompt wording and model version. If feasible, run a subset of cases with paraphrased prompts to estimate sensitivity. Frame fixes in Section 6 (Recommendations 1–3) as prompt modifications, not protocol changes.

7. **[Aggregate Weighting]** Report dimension-level aggregates (average each dimension across applicable cases, then average dimensions) as the primary comparison metric. This avoids implicit overweighting of cases with fewer applicable dimensions.

8. **[Convergence Operationalization]** Either formally define the convergence metric with a reproducible specification, or drop it from the report entirely.
