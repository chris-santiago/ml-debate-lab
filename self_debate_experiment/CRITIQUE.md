# CRITIQUE.md — Critique Agent Structured Output

All 11 KEEP cases. Critique agent output produced by the Critique persona in `self_debate_poc.py`.
Persona label: [CRITIQUE AGENT]. Cases ordered by category then case number.

---

## broken_baseline_001

**Category:** broken_baseline | **Difficulty:** easy

**ISSUE 1: unequal_eval_set_size**
- Location: Comparison setup — new model evaluated on 10% sample vs. baseline on full test set
- Why it is a problem: A 4-point accuracy gap measured on approximately 1,000 examples (10% of a typical 10,000-item test set) carries a margin of error of roughly ±3 percentage points at 95% confidence under a binomial model. This means the reported gap of 4 points is statistically indistinguishable from zero. The comparison is not apples-to-apples: the baseline has the statistical stability of the full set, while the new model's number reflects high sampling variance. Even if the true gap is 4 points, it cannot be detected with reliability at this sample size.

**ISSUE 2: missing_confidence_intervals**
- Location: Results reporting — no CI or p-value accompanies the 72% vs. 68% comparison
- Why it is a problem: Without confidence intervals or a significance test, there is no way to determine whether the 4-point gap exceeds sampling noise. Reporting a raw point estimate as a definitive improvement violates basic statistical reporting standards for model evaluation. Confidence intervals are not optional when sample sizes differ and the claimed gap is small relative to the margin of error.

**Proposed Empirical Test:** Re-evaluate both models on the identical full test set and report accuracy with 95% confidence intervals. A statistically significant gap (CI lower bound > 0 for the difference) is required before any claim of improvement can be made.

**Preliminary Verdict:** The improvement claim is invalid as stated. Unequal evaluation conditions with missing uncertainty quantification render the comparison non-conclusive.

---

## broken_baseline_002

**Category:** broken_baseline | **Difficulty:** medium

**ISSUE 1: inappropriate_baseline_type**
- Location: Baseline selection — majority-class baseline that always predicts 'positive'
- Why it is a problem: The majority-class baseline is a degenerate classifier: it scores exactly 0% recall on the negative and neutral classes. Beating this baseline proves only that BERT is better than doing nothing on the positive class — not that it is useful for the task as a whole. In a 3-class problem where two of the three classes are entirely ignored by the baseline, the comparison is against the minimum possible competence threshold, not a meaningful reference point. A random baseline, a TF-IDF classifier, or a prior BERT model would all provide more informative comparisons.

**ISSUE 2: accuracy_hides_class_failure**
- Location: Metric selection — 78% accuracy on a 60/20/20 class split
- Why it is a problem: On a 60/20/20 distribution, accuracy is dominated by the majority class. A model that perfectly handles positives but fails entirely on negatives and neutrals would score 60% accuracy — still only 18 points below the reported 78%, but demonstrating no multi-class competence. Macro-F1 or per-class recall are the appropriate primary metrics for an imbalanced multi-class problem because they weight each class equally regardless of prevalence. The 18-point improvement claim is stated in a metric that obscures the actual question: does BERT handle minority classes?

**Proposed Empirical Test:** Report macro-F1, per-class precision, recall, F1, and confusion matrices for both the majority-class baseline and BERT. The improvement claim should be assessed on macro-F1, not accuracy.

**Preliminary Verdict:** The 18-point accuracy improvement claim is misleading. The baseline is inappropriate (degenerate on two of three classes) and accuracy is the wrong metric for this problem structure. BERT may still be substantially better than a meaningful baseline, but this cannot be determined from the current report.

---

## broken_baseline_003

**Category:** broken_baseline | **Difficulty:** hard

**ISSUE 1: feature_set_confound**
- Location: Experimental design — new model trained on 47 features vs. logistic regression baseline on 12 features
- Why it is a problem: The AUC gap of 0.07 (0.88 vs. 0.81) cannot be attributed to architectural differences when the two models have access to entirely different feature sets. The 35 additional features available to the new model may individually or collectively account for the entire gap. Feature richness and model architecture are completely confounded in this comparison: there is no experimental design choice that would allow separating the architectural contribution from the feature richness contribution given the current data.

**ISSUE 2: attribution_error**
- Location: The claim "architecturally superior"
- Why it is a problem: Claiming architectural superiority requires holding feature sets constant and varying only the architecture. A logistic regression trained on all 47 features is a competitive benchmark for tabular data — on many real-world tabular tasks, regularized logistic regression with full feature access matches or exceeds gradient-boosted models. Without testing LR on all 47 features, the claim of architectural superiority is logically unsupported by the experimental evidence. Performance could improve from 0.81 to 0.88 purely due to additional feature information, with architecture contributing nothing.

**ISSUE 3: no_ablation_study**
- Location: Analysis section — no ablation reported
- Why it is a problem: No ablation study isolates the architectural contribution from the feature contribution. Training the new model on only the 12 baseline features would provide a lower bound on the architecture's contribution to the AUC gap. This is a methodological gap, though secondary to the feature confound and attribution error.

**Proposed Empirical Test:** Train logistic regression with a regularization sweep (L1, L2, elastic net) on all 47 features using the same train/test split. Compare AUC against the new model. Also train the new model on the 12-feature subset to bound the architecture contribution.

**Preliminary Verdict:** The architectural superiority claim is not supported. The feature set difference is a fatal confound. The combined system may be practically useful, but the framing of the superiority claim is wrong.

---

## metric_mismatch_001

**Category:** metric_mismatch | **Difficulty:** easy

**ISSUE 1: accuracy_on_imbalanced_data**
- Location: Primary metric — 99.5% accuracy on a 0.4% fraud prevalence dataset
- Why it is a problem: The trivial always-predict-negative classifier scores 99.6% accuracy on this dataset, which is higher than the reported model's 99.5%. This single calculation proves the reported metric cannot distinguish the model from a degenerate classifier that detects no fraud whatsoever. The model is literally underperforming the do-nothing baseline by 0.1 percentage points on the team's own chosen metric. Accuracy on highly imbalanced datasets is the canonical example of a misleading metric in the ML literature, and this case is a textbook instance: with 0.4% fraud prevalence, almost any classifier will achieve >99% accuracy regardless of its actual fraud detection ability.

**Proposed Empirical Test:** Compute and report precision, recall, F1 on the positive (fraud) class and area under the precision-recall curve (AUC-PR). These are the correct metrics for rare-event detection and will reveal whether the model has any actual fraud detection capability.

**Preliminary Verdict:** The metric choice is definitively wrong. The reported result is not evidence of model success. The claim of success is rejected on the basis of the trivial baseline argument alone, without needing any additional data.

---

## metric_mismatch_002

**Category:** metric_mismatch | **Difficulty:** medium

**ISSUE 1: metric_goal_misalignment**
- Location: Metric selection — MAP@10 evaluated against a product goal of top-3 user satisfaction
- Why it is a problem: MAP@10 computes average precision over all relevant documents in positions 1 through 10, weighting improvements at position 8 equally with improvements at position 1. The product goal is user satisfaction within the top 3 results. A model could improve MAP@10 by substantially improving positions 4–10 while simultaneously degrading positions 1–3 — and this would register as a model improvement in the offline evaluation while being a regression in the product metric. NDCG@3 or MRR are designed specifically to capture top-of-list relevance and are the appropriate metrics for this product goal.

**ISSUE 2: offline_to_online_gap**
- Location: Results interpretation — MAP@10 offline result used to claim product improvement
- Why it is a problem: Offline ranking metrics systematically miss position bias effects (users prefer early results regardless of quality), user intent variation across query sessions, and behavioral effects such as query reformulation rate. A 0.06 MAP@10 improvement in an offline evaluation cannot be used to predict an engagement lift without an online A/B test. The gap between offline and online performance is a well-documented phenomenon in search ranking research.

**Proposed Empirical Test:** Run an A/B test measuring click-through rate on positions 1–3 and session success rate (user found answer without reformulating query). Also report NDCG@3 and MRR offline to better align the development metric with the product goal.

**Preliminary Verdict:** MAP@10 is not wrong — it is a valid and widely used offline proxy — but it is imperfectly aligned with the stated product goal, and offline results cannot substitute for online evaluation. The improvement claim is directional evidence warranting an A/B test, not confirmed product improvement.

---

## metric_mismatch_003

**Category:** metric_mismatch | **Difficulty:** hard

**ISSUE 1: underpowered_human_eval**
- Location: Human evaluation — n=50 annotators for a 55%/45% preference split
- Why it is a problem: A 55%/45% preference split at n=50 pairwise comparisons yields a p-value of approximately 0.16 under a two-tailed binomial test (null hypothesis: p=0.5). This is not significant at any conventional threshold (0.10, 0.05, or 0.01). To achieve significance at p<0.05 with n=50, the preference margin would need to be approximately 64%/36% — the observed 55% falls substantially short. The team's claim that two metrics "agree" is built on a statistically noise-level human evaluation result.

**ISSUE 2: rouge_human_correlation_assumed**
- Location: Conclusion: "both metrics agree"
- Why it is a problem: The team interprets directional consistency between ROUGE-L improvement and the (non-significant) human preference as agreement between the two metrics. But agreement with noise is not agreement. A non-significant human result cannot validate, confirm, or corroborate a ROUGE-L result. For two metrics to be said to "agree," both must show significant effects in the same direction. The non-significant human result is consistent with both the model being better and the model being equivalent — it provides no distinguishing information.

**ISSUE 3: no_inter_annotator_agreement**
- Location: Human evaluation methodology — no IAA metric reported
- Why it is a problem: Without inter-annotator agreement statistics (Cohen's kappa, Fleiss' kappa, or Krippendorff's alpha), the 55/45 split could reflect annotator confusion, task ambiguity, or annotation inconsistency rather than a genuine preference signal. Inter-annotator agreement is a basic methodological requirement for any human evaluation study intended to support a scientific claim.

**Proposed Empirical Test:** Run a powered human preference study with minimum n=200 independent pairwise comparisons and report inter-annotator agreement. Alternatively, report BERTScore or G-Eval as calibrated automatic metrics alongside ROUGE-L.

**Preliminary Verdict:** The claim that both metrics "agree" is not supported. The human study is underpowered and the result is not statistically significant. The ROUGE-L improvement is real but the human evaluation does not confirm it; claiming agreement misrepresents the statistical state of the evidence.

---

## hidden_confounding_001

**Category:** hidden_confounding | **Difficulty:** medium

**ISSUE 1: confound_attribution_error**
- Location: Team's explanation — "different patient demographics" for the AUC drop from 0.94 to 0.71
- Why it is a problem: In medical imaging AI, scanner hardware differences, kVp settings, acquisition protocols, and image preprocessing pipelines are the dominant and best-documented sources of cross-site performance degradation — not patient demographics. The medical imaging literature (e.g., Zech et al. 2018, Pooch et al. 2020) consistently identifies acquisition-related domain shift as the primary cause of cross-site failures in radiology AI. Attributing a 23-point AUC drop to patient demographics — without ruling out these technical confounds — is speculative and inverts the correct investigative priority. Demographics are a last-resort explanation after technical confounds have been ruled out.

**ISSUE 2: no_domain_shift_audit**
- Location: Methods section — no audit of scanner or acquisition parameters reported
- Why it is a problem: A domain shift audit — comparing scanner manufacturer, model, acquisition settings, and preprocessing pipeline between Hospital A and Hospital B — is a standard first step in any medical imaging deployment and was not performed. Without this audit, the demographic attribution lacks any comparative basis. It is not possible to rule out technical confounds without examining the technical parameters.

**ISSUE 3: temporal_and_site_confound**
- Location: Evaluation design — training on 2018–2020 Hospital A, testing on 2021 Hospital A
- Why it is a problem: The evaluation mixes temporal shift (2018–2020 training vs. 2021 test from the same site) with site shift. The 0.94 AUC on the Hospital A 2021 test set may itself be inflated if the model learned site-specific image artifacts from Hospital A that generalize within Hospital A but not to Hospital B. This means the reference AUC of 0.94 may be an optimistic upper bound.

**Proposed Empirical Test:** Audit scanner model, acquisition protocol, and preprocessing pipeline for both hospitals. Run an ablation with intensity normalization and histogram equalization applied to Hospital B images. Report AUC before and after normalization. Also stratify Hospital A test performance by year to assess temporal drift.

**Preliminary Verdict:** The demographic attribution is not supported by the evidence. Technical confounds (scanner/acquisition differences) are the more plausible and well-documented explanation and must be ruled out first.

---

## hidden_confounding_002

**Category:** hidden_confounding | **Difficulty:** hard

**ISSUE 1: treatment_period_interaction**
- Location: A/B test validity — unplanned promotional sale in days 8–14 of a 14-day test
- Why it is a problem: Randomization ensures that both treatment and control groups are equally exposed to the promotional event, preserving internal validity. However, if the new recommendation algorithm interacts with the sale conditions — for example, by surfacing sale items more effectively, or by driving higher recommendation-driven clicks when users are already motivated by discounts — then the measured 8% lift reflects a mixture of the algorithm's steady-state effect and its sale-amplified effect. These two contributions cannot be disentangled from the aggregate result without segmented analysis. Internal validity is preserved; external validity (generalizability to non-sale conditions) is threatened.

**ISSUE 2: novelty_effect_uncontrolled**
- Location: Behavioral interpretation of the 8% lift
- Why it is a problem: New recommendation algorithms may drive higher engagement during promotional periods due to novelty-driven exploration — users who are actively browsing sale items may be more likely to click on unfamiliar recommendations than users in their typical browsing mode. This novelty-sale interaction is not measured and may inflate the lift estimate above its steady-state level.

**ISSUE 3: p_value_does_not_validate_confound_free_estimate**
- Location: Statistical reporting — p=0.002 cited to assert result validity
- Why it is a problem: The p=0.002 result confirms the measured 8% lift is unlikely under the null hypothesis of no effect. It does not confirm the measured difference is free of confounding. Statistical significance confirms the effect is real within the observed conditions — it does not confirm those conditions are representative of the intended deployment scenario.

**Proposed Empirical Test:** Segment the A/B result into pre-sale (days 1–7) and sale period (days 8–14). Test for a statistically significant interaction effect between treatment assignment and sale period using a 2×2 interaction model (logistic regression with treatment × period interaction term or ANOVA).

**Preliminary Verdict:** The result is internally valid but externally threatened. The 8% lift cannot be confidently attributed to steady-state algorithm performance without segmented period analysis revealing whether the lift is consistent across non-sale conditions.

---

## hidden_confounding_003

**Category:** hidden_confounding | **Difficulty:** medium

**ISSUE 1: data_contamination_risk**
- Location: Evaluation design — test set drawn from the same GitHub corpus as training data (2015–2022)
- Why it is a problem: In code model evaluation, train/test splits from the same corpus are highly susceptible to near-duplicate contamination from forks, code copies, and shared library patterns common on GitHub. Function-name deduplication catches only exact name matches; semantically near-identical functions with renamed variables, reordered parameters, or minor cosmetic differences are not removed. The published literature on code LM evaluation demonstrates that corpus-internal test sets consistently overestimate generalization performance due to this contamination.

**ISSUE 2: in_distribution_test_inflation**
- Location: Performance claim — pass@1 of 0.68 cited as the in-distribution baseline
- Why it is a problem: A pass@1 of 0.68 on a corpus-internal test set may primarily reflect memorization of training patterns rather than generalizable code generation. The gap between 0.68 (GitHub test) and 0.31 (hand-written benchmark) — a 37-point drop — is inconsistent with a difficulty-only explanation and is highly consistent with contamination-driven inflation. A 37-point gap from difficulty alone would imply the hand-written problems are dramatically harder across the board, which is an extraordinary claim requiring evidence.

**ISSUE 3: difficulty_attribution_unverified**
- Location: Team's explanation — "benchmark difficulty" for the 0.68 → 0.31 gap
- Why it is a problem: The team attributes the performance gap to benchmark difficulty without measuring it. Difficulty metrics such as cyclomatic complexity, expert human solve rates, or problem complexity scores were not computed. The difficulty attribution is asserted without any supporting evidence and is not the most parsimonious explanation given the evaluation design.

**Proposed Empirical Test:** Perform n-gram overlap analysis (8-gram) between the training corpus and both test sets. Report the fraction of test problems with >50% 8-gram overlap with any training example. Also compute cyclomatic complexity for both test sets to assess the difficulty differential hypothesis.

**Preliminary Verdict:** The primary explanation for the 0.68 → 0.31 gap is data contamination and distribution shift, not benchmark difficulty. The hand-written benchmark is likely the uncontaminated measure of true generalization performance.

---

## scope_intent_002

**Category:** scope_intent_misunderstanding | **Difficulty:** medium

**ISSUE 1: prediction_vs_intervention_conflation**
- Location: Project scope claim — "project complete" after delivering a prediction model
- Why it is a problem: Predicting churn does not reduce churn. Churn reduction requires a downstream intervention — a discount offer, support outreach, product fix, or in-app message — whose causal effect on the outcome is measured through a controlled experiment. The team conflated "we can predict who will churn" with "we have reduced churn." A prediction model generates a ranked list of at-risk users; it is a targeting mechanism, not a treatment. Without an intervention, the prediction model has no mechanism through which it can affect churn rates.

**ISSUE 2: no_intervention_design**
- Location: Project deliverables — no intervention designed or tested
- Why it is a problem: No intervention was designed, piloted, or A/B tested. The 500 at-risk users identified per week are identified but then receive no treatment. Without an intervention, the prediction model generates lists that cannot produce the business outcome regardless of its AUC quality. The absence of intervention design is not a minor gap — it is the entire missing second half of the stated project goal.

**Proposed Empirical Test:** Design and run an A/B test: use the prediction model to identify at-risk users, randomly assign to treatment (intervention such as a discount, support outreach, or in-app message) and control (no action), and measure 30-day churn rate difference between groups.

**Preliminary Verdict:** The project delivered a valid and valuable first step (prediction infrastructure) but the scope claim is wrong. "Reduce churn" requires a closed-loop intervention and measurement system. The prediction component alone does not address the business goal and reporting the project as complete misrepresents the remaining work.

---

## scope_intent_003

**Category:** scope_intent_misunderstanding | **Difficulty:** hard

**ISSUE 1: scope_of_safety_underspecified**
- Location: Research question — "evaluate whether LLM-generated code is safe to deploy in production"
- Why it is a problem: Production safety is a multi-dimensional concept encompassing at minimum: logical correctness, runtime reliability, edge case handling, dependency security, maintainability, semantic correctness for the deployment domain, and resistance to adversarial inputs. The research question commits to evaluating the full scope of production safety. The methodology addresses only a narrow subset of one security-related dimension (syntactic security anti-patterns detectable by static analysis). The scope gap between the question asked and the methodology deployed is enormous.

**ISSUE 2: bandit_coverage_limitation**
- Location: Methodology — Bandit static analysis as the sole evaluation tool
- Why it is a problem: Bandit is a static analysis tool that detects known syntactic security anti-patterns in Python: use of eval(), hardcoded credentials, insecure hashing, unsafe subprocess calls, and similar patterns. Its scope is explicitly limited by design. Bandit does not detect: logical vulnerabilities, race conditions, resource leaks, integer overflows, semantic security flaws (business logic errors with security consequences), or correctness failures of any kind. The conclusion that code is "safe for production" requires evidence on all of these dimensions, not just the subset Bandit covers.

**ISSUE 3: overgeneralized_conclusion**
- Location: Conclusion — "LLM-generated code is safe for production use"
- Why it is a problem: Even granting that the Bandit result is meaningful for what it measures, concluding that all LLM-generated code is safe for production use from 1,000 snippets of unspecified complexity and domain is an unwarranted generalization on at least three axes: (a) from the tested snippets to all LLM-generated code; (b) from Bandit-passing to all dimensions of safety; (c) from the tested domains to all production deployment contexts.

**ISSUE 4: sample_representativeness_unknown**
- Location: Dataset — 1,000 Python snippets with unspecified characteristics
- Why it is a problem: The 1,000 snippets are not characterized by complexity, domain, or production relevance. Simple utility functions (string operations, list manipulations) trivially pass Bandit static analysis; production code in security-sensitive domains (authentication systems, payment processing, medical data pipelines) involves patterns, libraries, and integration contexts that Bandit is not designed to evaluate in isolation.

**Proposed Empirical Test:** Define a multi-dimensional safety rubric covering: (1) logical correctness against test suites, (2) behavioral fuzzing for edge cases, (3) semantic security review by domain experts (business logic vulnerabilities), (4) dependency audit, and (5) domain-specific expert review of a random sample. Report pass rates per dimension on the same 1,000 snippets.

**Preliminary Verdict:** The conclusion dramatically overreaches the evidence. Static analysis for known vulnerability patterns is one necessary but far-from-sufficient dimension of production safety. The conclusion should be scoped to "the tested snippets do not exhibit common Bandit-detectable syntactic security patterns" and nothing broader.
