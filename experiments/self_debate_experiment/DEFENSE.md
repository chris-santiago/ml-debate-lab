# DEFENSE.md — Defense Agent Structured Output

All 11 KEEP cases. Defense agent output produced by the Defense persona in `self_debate_poc.py`.
Persona label: [DEFENSE AGENT]. Format: explicit concessions, explicit contestations, maintained positions, proposed test.

---

## broken_baseline_001

**Category:** broken_baseline | **Difficulty:** easy

**CONCESSION 1: unequal_eval_set_size**
- Conceded in full. Evaluating the new model on 10% of the test set while the baseline was measured on the full set is a fundamental methodological asymmetry. The sampling variance at approximately n=1,000 is large enough that a 4-point accuracy gap could easily be attributable to noise. A 95% confidence interval on a 72% accuracy estimate from 1,000 samples is approximately [69.2%, 74.8%], which fully overlaps the baseline's 68%.
- Position update: The improvement claim cannot be asserted as valid under current evaluation conditions. The team must re-run the new model evaluation on the full test set before any comparison is made.

**CONCESSION 2: missing_confidence_intervals**
- Conceded. Even in a scenario with equal sample sizes, confidence intervals or a significance test are required for any quantitative performance claim in a published or business context.
- Position update: The reporting must include 95% CIs for both accuracy estimates. The current report form is insufficient regardless of the true performance difference.

**CONTESTATIONS:** None. Both critique claims are valid and conceded without reservation.

**MAINTAINED POSITION:** The new model may genuinely be better — there is directional evidence — but the claim of a valid improvement cannot be established from the current evaluation setup. The defense's only maintained position is that the underlying model architecture and training are not inherently flawed; only the evaluation and reporting are.

**PROPOSED EMPIRICAL TEST:** Full test set evaluation for both models with 95% confidence intervals, as proposed by the critique. This is the necessary and sufficient resolution.

---

## broken_baseline_002

**Category:** broken_baseline | **Difficulty:** medium

**CONCESSION 1: inappropriate_baseline_type**
- Conceded. The majority-class baseline is a degenerate classifier that scores 0% recall on the negative and neutral classes. Using it inflates the apparent improvement and provides no information about BERT's multi-class competence. The 18-point improvement claim is against a floor, not a meaningful reference.
- Position update: The 18-point improvement claim against the majority-class baseline should be retired. A proper baseline comparison is required (e.g., a frequency-weighted random classifier, a prior model, or a TF-IDF classifier).

**CONCESSION 2: accuracy_hides_class_failure**
- Conceded. Accuracy on an imbalanced 3-class problem masks per-class performance. Macro-F1, which weights each class equally regardless of prevalence, is the standard primary metric for this problem type.
- Position update: Macro-F1 and per-class precision/recall/F1 must be the primary reporting metrics for this evaluation.

**CONTESTATIONS:** None. Both critique claims are valid and conceded.

**MAINTAINED POSITION:** BERT almost certainly outperforms both a random baseline and a frequency-weighted baseline by a meaningful margin on a standard sentiment classification task — the critique does not dispute this directional claim. The prediction model's architecture and training are not under dispute; only the framing of the comparison and the metric choice are wrong.

**PROPOSED EMPIRICAL TEST:** Report macro-F1 and per-class recall/precision/F1 for BERT and a meaningful baseline. Retain the majority-class baseline metrics for reference purposes only.

---

## broken_baseline_003

**Category:** broken_baseline | **Difficulty:** hard

**CONCESSION 1: feature_set_confound**
- Conceded in full. The feature set difference (47 vs. 12 features) is a genuine confound. A fair architectural comparison requires that both models have access to the same features. The current experiment design cannot separate the contribution of architecture from the contribution of additional features, and the two are completely confounded in the reported comparison.
- Position update: The architectural superiority claim is retracted pending a controlled comparison with logistic regression trained on all 47 features.

**CONCESSION 2: attribution_error**
- Conceded. The claim of architectural superiority requires an apples-to-apples feature comparison that was not performed. Regularized logistic regression on all 47 features is a legitimate and competitive benchmark for tabular data, and its performance against the new model is an open empirical question.
- Position update: The correct defensible claim is: "The new model plus new features (47) outperforms the legacy logistic regression baseline (12 features). Whether this improvement is attributable to architecture or features requires a controlled experiment."

**CONTESTATION 1: no_ablation_study** (partial contestation)
- The absence of an ablation study is a methodological gap but does not independently invalidate the result. The primary confound — feature set difference — is already addressed by the proposed empirical test (LR on 47 features). The ablation (new model on 12 features) adds useful information about the architecture's contribution but is not strictly necessary for deconfounding the main claim. The critique correctly assigns this issue medium severity; the defense accepts this framing.
- Counter-argument: A controlled LR baseline on 47 features is sufficient to answer the key question. The ablation is valuable as a secondary experiment but should not be the primary requirement blocking publication of the main result.

**MAINTAINED POSITION:** The new model plus the expanded feature set (47 features) is a practically valuable system with AUC 0.88. Its production value is not disputed. The defense maintains only that the "architectural superiority" framing is the error — the combined value of the new model and new features is real.

**PROPOSED EMPIRICAL TEST:** LR with regularization sweep (L1, L2, elastic net) on all 47 features, same train/test split. New model on 12-feature subset as secondary ablation.

---

## metric_mismatch_001

**Category:** metric_mismatch | **Difficulty:** easy

**CONCESSION 1: accuracy_on_imbalanced_data**
- Conceded in full and without reservation. The always-negative baseline at 99.6% accuracy definitively and mathematically establishes that accuracy is uninformative here. The model is worse than doing nothing by its own chosen metric. The reported 99.5% accuracy cannot support any claim of model success.
- Position update: The team's claim of success is retracted. Fraud-class precision, recall, F1, and AUC-PR must be computed and reported before any statement about model usefulness can be made.

**CONTESTATIONS:** None. The critique's single claim is valid and decisive. There is no defensible position on the accuracy metric for this dataset.

**MAINTAINED POSITION:** The model's architecture is not inherently flawed — it may achieve high fraud-class recall at appropriate thresholds. The defense's only maintained position is that the model may have genuine value, but this cannot be determined from the accuracy number alone. The evaluation and reporting are wrong; the model may not be.

**PROPOSED EMPIRICAL TEST:** Report fraud-class precision, recall, F1, and AUC-PR. Include precision-recall tradeoff curves to support threshold selection for deployment.

---

## metric_mismatch_002

**Category:** metric_mismatch | **Difficulty:** medium

**CONCESSION 1: metric_goal_misalignment**
- Conceded. NDCG@3 or MRR would be more directly aligned with top-3 user satisfaction than MAP@10. MAP@10 is defensible as a development metric and a direction-of-improvement signal, but it should not be the sole evaluation metric for a product goal explicitly focused on top-3 result quality.
- Position update: Future evaluations should report NDCG@3 and MRR alongside MAP@10. The current claim should be framed as "strong offline signal warranting an A/B test" rather than "product improvement confirmed."

**CONCESSION 2: offline_to_online_gap**
- Conceded. Offline improvements do not guarantee online engagement gains. The 0.06 MAP@10 improvement is meaningful directional evidence but does not constitute a product win claim without online validation.
- Position update: An A/B test is required before claiming a product win. This is the accepted standard for search ranking changes.

**CONTESTATIONS:** None. Both critique claims are accurate and conceded.

**MAINTAINED POSITION:** MAP@10 is a legitimate and widely accepted offline evaluation metric in the information retrieval community. A 0.06 improvement is a meaningful and practically significant signal. The defense maintains that this result is worth pursuing to an A/B test — the critique is of overclaiming the result as a product win, not of the metric being useless or the improvement being noise.

**PROPOSED EMPIRICAL TEST:** A/B test measuring click-through rate on positions 1–3 and session success rate (user found answer without query reformulation), as proposed by the critique.

---

## metric_mismatch_003

**Category:** metric_mismatch | **Difficulty:** hard

**CONCESSION 1: underpowered_human_eval**
- Conceded. n=50 is insufficient to detect a 55/45 preference split with statistical power. The required sample size for significance at p<0.05 for this margin is approximately n=250 by power analysis. The study is underpowered and the result does not reach statistical significance.
- Position update: The human evaluation result must be reported as "directional, non-significant (p≈0.16, n=50)" rather than as confirmatory evidence.

**CONCESSION 2: rouge_human_correlation_assumed**
- Conceded. The correct framing is "directional consistency pending a powered study," not "agreement." The claim of metric agreement requires both metrics to show significant effects — agreement with a non-significant result is not agreement.
- Position update: The paper's claim is revised to: "ROUGE-L shows a real improvement; human preference is directionally consistent but not yet statistically confirmed."

**CONTESTATION 1: no_inter_annotator_agreement** (partial contestation)
- Partially contested. Inter-annotator agreement is an important methodological component that should be added in any follow-up study. However, its absence in a preliminary pilot evaluation does not rise to the level of a fatal flaw. Many published human evaluation studies in NLP report preference without IAA for initial experiments; IAA is more critical for annotation tasks where categories are ambiguous. Pairwise preference tasks have lower ambiguity than multi-category annotation.
- Counter-argument: The IAA gap should be remedied in the powered follow-up study, but its absence in a small-scale pilot is a methodological weakness rather than an independent grounds for rejection. The primary issue remains the underpowering.

**MAINTAINED POSITION:** The ROUGE-L improvement from 0.38 to 0.42 is a real and reproducible result. The directional consistency with human preference — even if non-significant — is supporting rather than conflicting evidence. The defense maintains that a powered follow-up study is well-motivated and likely to confirm the preference if the ROUGE-L improvement reflects genuine quality differences.

**PROPOSED EMPIRICAL TEST:** Powered human preference study with n≥200 independent pairwise comparisons, inter-annotator agreement reported (Cohen's kappa or Fleiss' kappa), and a pre-specified significance threshold.

---

## hidden_confounding_001

**Category:** hidden_confounding | **Difficulty:** medium

**CONCESSION 1: confound_attribution_error**
- Conceded. Scanner and acquisition protocol differences are a prior and more testable hypothesis than demographic differences for cross-site performance degradation in medical imaging. The demographic attribution should be secondary, not primary, in the investigation.
- Position update: The team should prioritize a domain shift audit (scanner, acquisition protocol, preprocessing pipeline) over demographic analysis.

**CONCESSION 2: no_domain_shift_audit**
- Conceded. A scanner and protocol audit is a basic deployment requirement in medical imaging AI. Its omission means the demographic attribution lacks any comparative basis.
- Position update: Domain shift audit must be performed before any attribution claim is made.

**CONTESTATION 1: temporal_and_site_confound** (partial contestation)
- Partially contested on priority grounds. The critique correctly assigns this issue medium severity. The temporal drift within Hospital A from 2018 to 2021 is a real concern, but the primary confound is the cross-site scanner/acquisition difference, not the within-site temporal shift. The defense accepts the issue as real but contests its priority relative to the other two issues.
- Counter-argument: Temporal within-site drift is worth investigating as part of a comprehensive domain shift analysis, but should not be the primary focus when the cross-site AUC gap of 23 points is the phenomenon under investigation.

**MAINTAINED POSITION:** Demographic differences are a legitimate hypothesis in medical AI and cannot be entirely dismissed — patient demographics (age distribution, disease severity distribution, comorbidity patterns) do affect imaging presentations. The defense maintains that demographic analysis is valuable as a secondary investigation after technical confounds are controlled.

**PROPOSED EMPIRICAL TEST:** Domain shift audit (scanner manufacturer, model, acquisition settings, preprocessing pipeline) followed by normalization ablation on Hospital B images. Demographic stratification as secondary analysis only, to be interpreted in light of post-normalization AUC results.

---

## hidden_confounding_002

**Category:** hidden_confounding | **Difficulty:** hard

**CONCESSION 1: treatment_period_interaction**
- Conceded. Randomization does not prevent interaction effects between treatment assignment and the sale period. Even with perfect randomization, if the new algorithm has a differential effect during sale conditions, the aggregate measured lift reflects a mixture of steady-state and sale-amplified effects. External validity — generalizability to steady-state conditions — is genuinely threatened.
- Position update: The claim of a valid steady-state lift is retracted pending segmented analysis. The measured result is valid for the observed 14-day period including a sale event, but cannot be generalized to steady-state deployment without additional analysis.

**CONCESSION 2: p_value_does_not_validate_confound_free_estimate**
- Conceded. The p=0.002 result confirms the measured 8% lift is statistically significant — it does not confirm the lift is free of interaction confounds or generalizable to non-sale conditions.
- Position update: Statistical significance should not be cited as a defense against the interaction confound concern. These are orthogonal properties.

**CONTESTATION 1: novelty_effect_uncontrolled** (partial contestation)
- Partially contested on magnitude grounds. Novelty effects in recommendation systems are a real phenomenon, but they are typically most pronounced in the first few days of deployment and wash out over 1–3 weeks. A 14-day test may be at the boundary of novelty effect washout, and the effect would inflate engagement in the treatment group broadly, not just during the sale period. This is a secondary concern relative to the sale-period interaction.
- Counter-argument: The novelty effect concern is worth controlling for by examining daily or weekly trends within the test period, but the primary confound requiring analysis is the pre-sale vs. sale-period segmentation.

**MAINTAINED POSITION:** The A/B test is internally valid: both groups were equally exposed to the promotional sale, and randomization was maintained throughout the test period. The 8% lift is a real measured effect under the observed conditions. The defense maintains that the result is actionable directional evidence pending segmented analysis — it should be treated as a strong signal to investigate further rather than a clean causal estimate of steady-state performance.

**PROPOSED EMPIRICAL TEST:** Pre-sale (days 1–7) vs. sale period (days 8–14) segmentation with a treatment × period interaction test (logistic regression with interaction term), as proposed by the critique.

---

## hidden_confounding_003

**Category:** hidden_confounding | **Difficulty:** medium

**CONCESSION 1: data_contamination_risk**
- Conceded. Contamination analysis is mandatory for any evaluation that uses a corpus-internal test set. The absence of n-gram overlap analysis between training and test data is a methodological gap that must be remedied before the in-distribution pass@1 of 0.68 can be cited as a measure of generalization.
- Position update: The 0.68 pass@1 on the GitHub test set cannot be presented as a generalization performance measure until contamination is quantified and found to be low.

**CONCESSION 2: in_distribution_test_inflation**
- Conceded. A 37-point gap between in-distribution (0.68) and out-of-distribution (0.31) test performance is inconsistent with a difficulty-only explanation at face value. This gap is consistent with contamination-driven inflation of the in-distribution score and requires investigation.
- Position update: The in-distribution 0.68 pass@1 is not a reliable upper bound on generalization performance until contamination is ruled out.

**CONTESTATION 1: difficulty_attribution_unverified** (partial contestation)
- Partially contested on the grounds that difficulty is a legitimate and plausible hypothesis, not a baseless claim. Hand-written coding problems designed for human evaluation purposes are typically more complex than code scraped from public repositories, which includes many simple utility functions. The critique is correct that this hypothesis is unverified — the defense accepts that difficulty measurement is required — but the critique does not prove difficulty is not a factor.
- Counter-argument: The defense accepts the empirical test (cyclomatic complexity comparison) as the correct resolution. Difficulty may be a partial contributor to the gap alongside contamination, and the test will reveal the relative magnitudes.

**MAINTAINED POSITION:** Hand-written benchmarks introduce their own biases including problem selection bias, domain coverage gaps, and solver demographic effects. The defense maintains that difficulty is a plausible partial contributor to the performance gap alongside contamination — the correct framing is that both hypotheses need to be tested, not that contamination is definitely the sole explanation.

**PROPOSED EMPIRICAL TEST:** N-gram overlap analysis (8-gram) between training corpus and both test sets, reporting fraction with >50% overlap. Cyclomatic complexity computation for both test sets. Both tests together will quantify the relative contributions of contamination and difficulty.

---

## scope_intent_002

**Category:** scope_intent_misunderstanding | **Difficulty:** medium

**CONCESSION 1: prediction_vs_intervention_conflation**
- Conceded. "Reduce churn" as a business goal requires a causal intervention — a treatment applied to at-risk users whose effect is measured through a controlled comparison. The team delivered prediction capability, which is a necessary but not sufficient component of a churn reduction system. Reporting the project as complete misrepresents the remaining scope.
- Position update: The project is not complete as scoped. An intervention design and A/B test are the remaining required work to meet the stated business goal.

**CONCESSION 2: no_intervention_design**
- Conceded. Without an intervention (a discount, support outreach, in-app message, or any treatment applied to the identified at-risk users), the prediction model generates lists that cannot by itself affect churn rates. The mechanism linking prediction to outcome is missing.
- Position update: The intervention design must be added to the project scope.

**CONTESTATIONS:** None. Both critique claims are accurate and conceded without reservation.

**MAINTAINED POSITION:** The churn prediction model (AUC 0.85) is a significant and genuine deliverable. Identifying the top 500 at-risk users per week with this accuracy is a valuable foundation for an intervention system — it is necessary for the intervention to be efficient rather than applied randomly. The defense maintains that the prediction work has real practical value and was well-executed; only the "project complete" framing is wrong.

**PROPOSED EMPIRICAL TEST:** A/B test: use the prediction model to identify at-risk users, randomly assign to treatment (intervention) and control (no action), measure 30-day churn rate difference between groups.

---

## scope_intent_003

**Category:** scope_intent_misunderstanding | **Difficulty:** hard

**CONCESSION 1: scope_of_safety_underspecified**
- Conceded. Production safety requires a multi-dimensional evaluation framework. The study addresses only a narrow slice of the safety landscape, and the conclusion overstates what the evidence can support.
- Position update: The conclusion must be rescoped to: "94% of tested snippets pass Bandit high-severity checks, which is one necessary dimension of a production safety evaluation. Comprehensive safety assessment requires additional dimensions."

**CONCESSION 2: bandit_coverage_limitation**
- Conceded. Bandit's scope is explicitly limited to syntactic anti-patterns. It does not and cannot detect logical vulnerabilities, race conditions, resource leaks, semantic security flaws, or correctness failures. The defense cannot claim Bandit results extend beyond the narrow scope for which the tool was designed.
- Position update: The study's scope must be clearly communicated as a static analysis result. Any claim about production safety must be qualified accordingly.

**CONCESSION 3: overgeneralized_conclusion**
- Conceded in full. The conclusion "LLM-generated code is safe for production use" is not supported by a static analysis pass rate on 1,000 uncharacterized snippets. This is an extraordinary claim that requires extraordinary evidence across multiple safety dimensions.
- Position update: The conclusion must be replaced with a scoped, qualified claim that accurately reflects the scope of the measurement.

**CONTESTATION 1: sample_representativeness_unknown** (partial contestation)
- Partially contested on scale grounds. The critique correctly identifies that the snippets are uncharacterized by complexity and domain, which is a genuine methodological gap. However, the defense contests the implication that the sample size itself is the primary problem — a well-characterized stratified sample of 1,000 is a reasonable scale for a study of this type. The issue is the lack of stratification and characterization, not the number 1,000.
- Counter-argument: A stratified sample of 1,000 snippets by domain (authentication, data processing, algorithm implementations, utilities) and complexity level would make the Bandit result substantially more interpretable and defensible. The study's gap is in characterization, not in scale.

**MAINTAINED POSITION:** The Bandit pass rate (94%) is one valid and useful data point: LLM-generated code does not systematically introduce common syntactic security anti-patterns at high rates. This is a useful finding when scoped correctly. The defense maintains that static analysis is not useless — it is a necessary (if insufficient) dimension of safety evaluation, and the 94% pass rate is a positive signal for that specific dimension.

**PROPOSED EMPIRICAL TEST:** Multi-dimensional safety rubric as proposed by the critique, applied to the same 1,000 snippets plus a stratified extension by domain and complexity level.
