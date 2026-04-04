# Peer Review: Self-Debate Protocol v2 — Technical Report

**Review date:** 2026-04-04
**Review depth:** Full
**Calibrated to:** Internal technical report / workshop paper submission

---

## 1. Summary

This report evaluates a multi-agent LLM debate protocol (Critic + Defender + Judge, operating under context isolation) against a single-pass baseline on 20 synthetic ML reasoning benchmark cases with known ground truth. Six rubric dimensions are scored per case. The headline finding is a +0.586 lift (debate mean 0.970 vs. baseline 0.384), subsequently qualified by the authors' own post-experiment analysis to an honest range of +0.335 to +0.441. A compute-matched ensemble follow-on partially refuted the isolation hypothesis for exoneration cases, narrowing the debate protocol's unique advantage to empirical test design forcing (ETD).

---

## 2. Strengths

**Self-critical post-experiment process.** The most unusual and commendable feature of this work is the adversarial self-review cycle documented in the sensitivity analysis and ensemble follow-on. The authors identified rubric inflation (DC=0.0 structural override, DRQ cap), ran a sensitivity analysis, quantified the honest lift range, and partially refuted one of their own secondary hypotheses via the clean ensemble test. This level of intellectual honesty is rare in internal reports and would be valued at any venue. The correction from +0.586 to +0.335–0.441 is transparently presented in the abstract itself, not buried in an appendix.

**Pre-specified decision criteria.** The ensemble follow-on had a pre-specified verdict criterion ("if ensemble scores DC>=0.5 on >=3/5 defense_wins cases, then compute budget partially explains defense_wins advantage"). This is good experimental hygiene and distinguishes the work from typical post-hoc rationalization.

**Failure mode taxonomy (Section 4.3).** The three failure modes (reasoning/label disconnect, under-confidence on defense_wins, genuine verdict divergence on mixed cases) are well-characterized, with specific case citations and clear scoring impact. The distinction between failure mode 3 (protocol working correctly) and modes 1–2 (genuine failures) is useful and well-argued.

**Artifact completeness.** Benchmark prompts, scoring code, full JSON results, and per-case justifications are all preserved and referenced. For a technical report, this is strong on reproducibility within the stated scope.

**Nuanced ETD finding.** The decomposition showing that the debate protocol's remaining structural advantage over the ensemble concentrates in empirical test design — not in issue detection or verdict calibration — is the most interesting mechanistic finding in the report. The insight that adversarial forcing functions generate test specifications that parallel assessors never produce is a genuinely useful observation for the multi-agent evaluation literature.

---

## 3. Critical Issues

### Major Issues

**[MAJOR] Single-entity benchmark design, scoring, and evaluation creates closed-loop validity threat.** The benchmark cases, ground truth labels (`must_find`, `correct_position`, `ideal_resolution`), rubric dimensions, scoring code, agent prompts, and scoring judgments all originate from the same entity. This is the report's fundamental validity limitation. The benchmark may be unconsciously calibrated to the protocol's strengths. The fact that 15/20 debate cases score exactly 1.000 across all applicable dimensions is extraordinary and should raise suspicion of ceiling effects or task-protocol co-adaptation. The sensitivity analysis partially addresses rubric inflation on the baseline side, but does not address the possibility that the debate protocol's near-perfect scores reflect benchmark cases that are too easy for the protocol. Section 6 (Recommendation 4) acknowledges the need for independent benchmark construction, but this is framed as a future enhancement rather than a fundamental limitation of the current results.

**[MAJOR] N=20 with no variance estimation, no confidence intervals, no significance testing.** The entire experiment runs each case exactly once with no repetition. The reported means (0.970, 0.384) are point estimates from single runs with no measure of variability. Given that LLMs are stochastic, the observed scores are samples from a distribution — the report treats them as fixed quantities. At minimum: (a) report bootstrap confidence intervals on the benchmark mean and lift by resampling over the 20 cases, (b) run a paired permutation test or Wilcoxon signed-rank test on the per-case deltas to establish that the lift is statistically distinguishable from zero, and (c) ideally re-run the full protocol 3–5 times to estimate within-case variance from LLM stochasticity. The convergence analysis (Section 2.4, 4.4) is particularly underpowered: the "easy" stratum has n=3 cases, making any convergence-by-difficulty conclusion uninterpretable.

**[MAJOR] Rubric dimensions are structurally confounded with the treatment condition.** Two of six rubric dimensions (DC and DRQ) are defined in ways that the baseline *cannot* perform well on by construction:
- DC (defense calibration) is hardcoded to 0.0 for the baseline because the baseline has no defense role. This is the widest-gap dimension (+0.867).
- DRQ (debate resolution quality) is capped at 0.5 for the baseline because a single-pass system cannot produce a "debate resolution."

The authors identified this and ran the sensitivity analysis, which is good. However, the main report's Section 2.1 still leads with the +0.586 headline number and only qualifies it in the abstract's post-experiment addendum and Section 8. For a workshop paper, the corrected range (+0.335 to +0.441) should be the primary reported number. More fundamentally, including DC and DRQ in the aggregate when comparing debate vs. baseline is like comparing a basketball player to a swimmer and including "free throws made" as a scoring dimension. The report should present dimension-stratified results as the primary comparison: debate vs. baseline on IDR, IDP, ETD, and FVC (dimensions where both systems have agency), with DC and DRQ reported separately as protocol-specific diagnostics.

**[MAJOR] Scorer is not independent from the protocol under evaluation.** The scoring rubric is applied by the same model family that generates the debate transcripts. The scorer has access to `must_find` labels (ground truth) during scoring, and the model doing the scoring is likely the same model that generated the Critic/Defender/Judge outputs. This creates a self-grading confound: the model may systematically rate its own outputs more favorably than an independent scorer would. The sensitivity analysis recommends cross-model scorer validation but this has not been executed.

**[MAJOR] Baseline is a strawman by design.** The single-pass baseline receives the same task prompt but operates with 3–4x fewer LLM calls and no structural role prompting. The clean ensemble follow-on demonstrated that a compute-matched ensemble without role differentiation scored 0.754 overall and matched or exceeded the debate protocol on issue detection for non-defense_wins cases. This is the correct comparison condition, and it substantially deflates the protocol's claimed advantage. The main report should present the debate vs. clean ensemble comparison as the primary result, with the single-pass baseline relegated to a reference condition. As currently structured, the report's headline claims are anchored to the weakest possible comparison.

### Minor Issues

**[MINOR] Per-case results table (Section 2.2) reports baseline passes inconsistently.** The table shows baseline passes for broken_baseline_001 and metric_mismatch_002 as "YES" (inferred from scores), but the correction note in CONCLUSIONS.md Section 3 states these are incorrect (baseline pass count should be 0/20 after DC=0.0 enforcement). The main report table still shows 2/20 in its text ("10% (2/20)"). This inconsistency should be resolved.

**[MINOR] "Convergence" metric is undefined in the main report.** Section 2.2 includes a "Conv" column and Section 2.4 discusses convergence by difficulty, but the report never formally defines what convergence measures or how it is computed. From context it appears to be agreement between Critic and Defender on verdict type, but this should be stated explicitly with the computation formula.

**[MINOR] Section numbering gap: Section 3.2 is referenced but does not exist.** The abstract references "the Section 3.2 'isolation is the only mechanism' finding" but the report's Section 3 jumps from 3.1 to 3.3 (no Section 3.2 exists). The secondary hypothesis about defense_wins (currently unnumbered between 3.1 and 3.3) should be labeled 3.2.

**[MINOR] Defense_wins baseline scoring creates an artificial floor.** For defense_wins cases, IDR and IDP are set to N/A for both systems, leaving only DC, DRQ, and FVC as applicable dimensions. With DC=0.0, DRQ=0.0, and FVC=0.0 for the baseline, the baseline mean is mechanically 0.000 on these cases. The report should quantify what the lift would be if defense_wins cases were excluded entirely from the aggregate.

**[MINOR] Difficulty labels are author-assigned and unvalidated.** Difficulty labels (easy/medium/hard) are used in analysis but there is no independent calibration. The convergence analysis and Section 4.4 interpretation depend on these labels, but they may not reflect actual difficulty for the protocol.

**[MINOR] No related work section.** The report does not reference any prior work on LLM debate protocols, multi-agent evaluation, adversarial prompting for reasoning quality, or structured argument generation. For a workshop paper, at minimum cite: Irving et al. (2018) on AI safety via debate, Du et al. (2023) on multi-agent debate for mathematical reasoning, Liang et al. (2023) on encouraging divergent thinking in LLM debates, and Khan et al. (2024) on debate as verification. The absence of related work makes it impossible to assess novelty or position the contribution.

**[MINOR] No explicit limitations section.** The post-experiment qualifications are scattered across the abstract, Section 3 hypothesis verdicts, Section 4 analysis, and a separate `SENSITIVITY_ANALYSIS.md` file. A consolidated limitations section would improve readability and signal intellectual honesty to reviewers. Key limitations to consolidate: (a) closed-loop benchmark design, (b) single-run results, (c) rubric-inflated headline lift, (d) strawman baseline, (e) same-model scoring confound.

---

## 4. Recommendations

1. **[Baseline Comparison]** Restructure the report to present the clean ensemble (0.754) as the primary comparison condition and the single-pass baseline (0.384) as a reference floor. The headline finding should be "debate protocol scores 0.970 vs. 0.754 for a compute-matched ensemble without role differentiation" — a lift of +0.216 attributable to the adversarial role structure itself.

2. **[Statistical Rigor]** Add bootstrap confidence intervals (10,000 resamples over the 20 cases) for the benchmark mean, lift, and per-category means. Run a paired Wilcoxon signed-rank test on the 20 per-case deltas (debate minus baseline, and debate minus ensemble). Report p-values and effect sizes. If feasible, re-run the full protocol 3–5 times to estimate within-case variance from LLM stochasticity.

3. **[Dimension-Stratified Reporting]** Report debate vs. baseline lift separately for "fair comparison dimensions" (IDR, IDP, ETD, FVC — where both systems have agency) and "protocol-diagnostic dimensions" (DC, DRQ — where the baseline is structurally disadvantaged). Make the fair-comparison lift the primary number.

4. **[Cross-Model Scorer Validation]** Execute the report's own Recommendation 3 from `SENSITIVITY_ANALYSIS.md`: have a different model family score the embedded transcripts against the same rubric without access to `must_find` labels. Report inter-scorer agreement (Cohen's kappa or ICC) and whether debate-favorable scoring bias is detectable.

5. **[Independent Benchmark]** Construct a parallel benchmark from externally-grounded cases (published ML paper retractions, NeurIPS reproducibility failures, Kaggle post-mortems) where ground truth is established by domain consensus rather than the protocol designer. Even 10 such cases would provide an external validity anchor.

6. **[Convergence Definition and Analysis]** Formally define the convergence metric in Section 1 or a methods subsection. Drop or heavily qualify the convergence-by-difficulty analysis given n=3 for the easy stratum. If the finding is retained, present it as "exploratory, underpowered."

7. **[Related Work]** Add a related work section covering: (a) debate as an AI alignment mechanism (Irving et al. 2018), (b) multi-agent debate for LLM reasoning (Du et al. 2023), (c) LLM-as-judge and self-evaluation pitfalls (Zheng et al. 2023 on MT-Bench), (d) multi-agent collaboration frameworks (ChatEval, MAD).

8. **[Consolidated Limitations Section]** Add a dedicated limitations section consolidating: closed-loop benchmark design, single-run per case, rubric-inflated headline numbers, same-model scoring confound, N=20 sample size, unvalidated difficulty labels, and absence of external benchmark validation.

9. **[Section Numbering]** Fix the missing Section 3.2 — the defense_wins secondary hypothesis between 3.1 and 3.3 should be numbered 3.2. Update the abstract's reference accordingly.

10. **[Corrected Headline Numbers]** Replace the +0.586 headline in Section 2.1, the abstract, and Section 8 with the corrected range (+0.335 to +0.441) as the primary figure. The uncorrected number can be retained with explanation, but leading with a number the authors themselves have shown to be inflated undermines credibility.

---

## 5. Overall Assessment

The work demonstrates genuine intellectual rigor in its self-correction cycle, and the ETD forcing-function finding is a real contribution to understanding when structured debate adds value over parallel assessment. However, the report's presentation still leads with inflated numbers, compares primarily against a strawman baseline, lacks variance estimation, and suffers from a closed-loop design where the same entity controls benchmark, scoring, and evaluation.

For a workshop paper, the most important revisions are: (1) reframing around the ensemble comparison, (2) adding statistical tests, (3) cross-model scorer validation, and (4) a consolidated limitations section. The underlying findings are interesting enough to survive honest reporting — the authors should trust their corrected numbers and lead with them.
