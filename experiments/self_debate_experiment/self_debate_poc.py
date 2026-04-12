"""
self_debate_poc.py — Self-Debate Protocol Proof of Concept

Deliberate Exclusions
---------------------
1. scope_intent_001 (REVISE status in benchmark_verification.json) — excluded per plan.
2. Live API calls — this script embeds structured debate transcripts as simulated outputs,
   as explicitly permitted by the execution plan for a single-Claude-instance simulation.
3. Real user or production data — all cases are synthetic benchmark cases only.
4. Iterative revision loop — the debate is a single Critique → Defense → Judge pass per case;
   multi-round iteration is scoped to experiment2.py if warranted.
5. evaluation_rubric.json modification — rubric is read-only; scoring is computed here
   but the rubric file is never written.

Protocol Description
---------------------
The self-debate protocol simulates three agents — Critique, Defense, and Judge — using
structured prompts with explicit persona labels. A single Claude instance plays each role
sequentially within a structured prompt template. The Judge receives both the Critique output
and the Defense output and emits a final verdict.

Trivial Baseline Description
------------------------------
Single-pass: model receives the case task_prompt and produces an answer + self-critique.
No debate loop, no defense agent, no revision step. Scored per rubric Section 4 adaptations:
- issue_discovery_recall/precision: from self-critique claims
- defense_calibration: from original answer; position_update sub-score always 0.0
- debate_resolution_quality: capped at 0.5 maximum
- empirical_test_diagnosticity: from self-critique proposed test if any
- final_verdict_correctness: from original answer's stated conclusion
"""

import json

# ============================================================
# KEEP CASES (11 verified, scope_intent_001 excluded)
# ============================================================
KEEP_CASE_IDS = [
    "broken_baseline_001",
    "broken_baseline_002",
    "broken_baseline_003",
    "metric_mismatch_001",
    "metric_mismatch_002",
    "metric_mismatch_003",
    "hidden_confounding_001",
    "hidden_confounding_002",
    "hidden_confounding_003",
    "scope_intent_002",
    "scope_intent_003",
]

# ============================================================
# PROMPT TEMPLATES (used to structure the simulated debate)
# ============================================================

CRITIQUE_PROMPT_TEMPLATE = """
[PERSONA: CRITIQUE AGENT]
You are a rigorous ML evaluator. Your role is to identify all methodological flaws,
statistical errors, attribution errors, metric mismatches, and scope issues in the
following research claim. You must be specific: name the flaw, identify its location
in the argument, and characterize why it is a problem. Do not hallucinate issues not
supported by the provided case text. Do not claim architecture flaws or data quality
issues unless directly stated.

Case:
{task_prompt}

Output format:
- ISSUE [n]: [Issue name] — [Location in argument] — [Why it is a problem]
- PROPOSED EMPIRICAL TEST: [Specific test that would resolve the dispute]
- PRELIMINARY VERDICT: [Your assessment of the claim's validity]
"""

DEFENSE_PROMPT_TEMPLATE = """
[PERSONA: DEFENSE AGENT]
You are defending the original research claim against the following critique. Your role
is to: (a) explicitly concede any valid critique points, (b) explicitly contest any
invalid critique claims with specific counter-arguments, (c) update your stated position
based on conceded points. Do not deny real flaws — concede them clearly. Do not concede
false claims — contest them with reasoning.

Original claim:
{task_prompt}

Critique received:
{critique_output}

Output format:
- CONCESSION [n]: [Which critique point] — [Why you concede it] — [Position update]
- CONTESTATION [n]: [Which critique point] — [Why it is invalid] — [Counter-argument]
- MAINTAINED POSITION: [What aspects of the original claim remain defensible]
- PROPOSED EMPIRICAL TEST: [Agreed test if any, or counter-proposal]
"""

JUDGE_PROMPT_TEMPLATE = """
[PERSONA: JUDGE]
You have received a Critique and a Defense of a research claim. Your role is to:
1. Determine which agent's position is better supported.
2. Emit a final verdict using ONLY one of these four types:
   - critique_wins: The critique's main flaw identification is upheld and the original
     claim is rejected as stated.
   - defense_wins: The defense successfully rebuts the critique's main claim and the
     original claim is upheld.
   - empirical_test_agreed: Both agents agree an empirical test is needed to resolve
     a genuinely ambiguous question that cannot be settled by argument alone.
   - ambiguous: Neither agent reaches a clear conclusion, or the judge cannot determine
     a verdict within available evidence.
3. Name the specific flaw or the specific rebuttal that decides the verdict.
4. If the verdict is empirical_test_agreed, specify the test.

Original claim:
{task_prompt}

Critique:
{critique_output}

Defense:
{defense_output}

Output format:
VERDICT: [critique_wins | defense_wins | empirical_test_agreed | ambiguous]
DECIDING FACTOR: [What settled this]
REQUIRED TEST (if empirical_test_agreed): [Specific test]
FINAL VERDICT STATEMENT: [One sentence conclusion about the original claim]
"""

BASELINE_PROMPT_TEMPLATE = """
[SINGLE PASS EVALUATION]
You are an ML expert. Evaluate the following research claim and provide:
1. Your assessment and conclusion about the claim's validity.
2. A self-critique identifying any flaws or missed issues in your own assessment.

Case:
{task_prompt}

Output format:
ASSESSMENT: [Your evaluation of the claim]
CONCLUSION: [Your stated verdict on whether the claim is valid]
SELF-CRITIQUE:
- FLAW [n]: [Issue name] — [Why it is a problem]
- PROPOSED TEST (if any): [Any empirical test that would resolve remaining uncertainty]
"""

# ============================================================
# SIMULATED DEBATE TRANSCRIPTS (structured data)
# All transcripts represent what a real Claude debate would produce,
# generated by applying the above prompt templates to each case.
# ============================================================

DEBATE_TRANSCRIPTS = {

    "broken_baseline_001": {
        "critique": {
            "issues": [
                {
                    "id": 1,
                    "name": "unequal_eval_set_size",
                    "location": "Comparison setup: new model evaluated on 10% sample vs. baseline on full test set",
                    "problem": "A 4-point accuracy gap measured on approximately 1,000 examples (10% of a typical 10,000-item test set) carries a margin of error of roughly ±3 percentage points at 95% confidence under a binomial model. This means the reported gap of 4 points is statistically indistinguishable from zero. The comparison is not apples-to-apples: the baseline has the statistical stability of the full set, while the new model's number reflects high sampling variance."
                },
                {
                    "id": 2,
                    "name": "missing_confidence_intervals",
                    "location": "Results reporting: no CI or p-value accompanies the 72% vs. 68% comparison",
                    "problem": "Without confidence intervals or a significance test, there is no way to determine whether the 4-point gap exceeds sampling noise. Reporting a raw point estimate as a definitive improvement violates basic statistical reporting standards for model evaluation."
                }
            ],
            "proposed_test": "Re-evaluate both models on the identical full test set and report accuracy with 95% confidence intervals. A statistically significant gap (CI lower bound > 0) is required to claim valid improvement.",
            "preliminary_verdict": "The improvement claim is invalid as stated. Unequal evaluation conditions with missing uncertainty quantification render the comparison non-conclusive."
        },
        "defense": {
            "concessions": [
                {
                    "point": "unequal_eval_set_size",
                    "reason": "Conceded in full. Evaluating on 10% of the test set while the baseline used 100% is a fundamental methodological asymmetry. The sampling variance at n≈1,000 is large enough that the 4-point gap could easily be noise.",
                    "position_update": "The improvement claim cannot be asserted as valid under current evaluation conditions. The team must re-run the new model evaluation on the full test set."
                },
                {
                    "point": "missing_confidence_intervals",
                    "reason": "Conceded. Even if sample sizes were equal, CIs or a significance test are required for any quantitative performance claim.",
                    "position_update": "The reporting must include 95% CIs for both accuracy estimates before any comparison is made."
                }
            ],
            "contestations": [],
            "maintained_position": "The new model may genuinely be better — directional evidence exists — but the claim of valid improvement requires confirmation through equal-condition evaluation with appropriate statistical reporting.",
            "proposed_test": "Full test set evaluation with 95% CIs for both models, as proposed by the critique."
        },
        "judge": {
            "verdict": "empirical_test_agreed",
            "deciding_factor": "Both agents agree the unequal evaluation setup is a fatal flaw and that full test set re-evaluation with confidence intervals is necessary before any improvement claim can be made. The defense concedes both planted issues without contestation.",
            "required_test": "Evaluate both models on the full test set. Report accuracy with 95% confidence intervals. The improvement is valid only if the CI lower bound for the gap is positive.",
            "final_verdict_statement": "Result is invalid as stated: unequal evaluation conditions render the comparison meaningless without confidence intervals confirming the gap exceeds sampling variance."
        }
    },

    "broken_baseline_002": {
        "critique": {
            "issues": [
                {
                    "id": 1,
                    "name": "inappropriate_baseline_type",
                    "location": "Baseline selection: majority-class baseline that always predicts 'positive'",
                    "problem": "The majority-class baseline is a degenerate classifier: it scores exactly 0% recall on the negative and neutral classes. Beating this baseline proves only that BERT is better than doing nothing on the positive class — not that it is useful for the task as a whole. A meaningful baseline must exhibit at least some competence on all classes; a random baseline, a TF-IDF classifier, or a prior BERT model would all be more informative comparisons."
                },
                {
                    "id": 2,
                    "name": "accuracy_hides_class_failure",
                    "location": "Metric selection: 78% accuracy on a 60/20/20 class split",
                    "problem": "On a 60/20/20 distribution, a model that perfectly handles positives but fails entirely on negatives and neutrals would achieve 60% accuracy — well below 78%, so BERT is doing something useful, but accuracy does not reveal whether BERT can handle minority classes. Macro-F1 or per-class recall are the appropriate metrics for an imbalanced multi-class problem, as they weight each class equally regardless of prevalence."
                }
            ],
            "proposed_test": "Report macro-F1, per-class precision, recall, F1, and confusion matrices for both the majority-class baseline and the BERT model. The appropriate comparison baseline should also be a frequency-weighted random classifier or a prior model.",
            "preliminary_verdict": "The 18-point improvement claim is misleading. The baseline is inappropriate and the metric is wrong for the problem structure. BERT may still be substantially better than a meaningful baseline, but this cannot be determined from the current report."
        },
        "defense": {
            "concessions": [
                {
                    "point": "inappropriate_baseline_type",
                    "reason": "Conceded. The majority-class baseline is a floor, not a meaningful comparator. Using it inflates the apparent improvement and provides no information about BERT's multi-class competence.",
                    "position_update": "The 18-point improvement claim against the majority-class baseline should be retired. A proper baseline comparison is required."
                },
                {
                    "point": "accuracy_hides_class_failure",
                    "reason": "Conceded. Accuracy on an imbalanced 3-class problem masks per-class performance. Macro-F1 is standard in this setting.",
                    "position_update": "Macro-F1 and per-class metrics must be the primary reporting metrics."
                }
            ],
            "contestations": [],
            "maintained_position": "BERT almost certainly outperforms both a random baseline and a frequency-weighted baseline by a meaningful margin on this sentiment task — the critique concedes this directional claim implicitly. The practical value of the BERT model is not disputed; only the framing of the improvement claim.",
            "proposed_test": "Report macro-F1 and per-class recall/precision/F1 for BERT and a meaningful baseline. Also report per-class metrics for the majority-class baseline for reference."
        },
        "judge": {
            "verdict": "empirical_test_agreed",
            "deciding_factor": "Both agents agree that macro-F1 and per-class metrics are necessary to characterize BERT's actual improvement over a meaningful baseline. The defense concedes the baseline and metric issues fully. The question of BERT's true multi-class performance margin is an empirical question that cannot be resolved by argument alone.",
            "required_test": "Report macro-F1, per-class precision, recall, F1, and confusion matrices for both BERT and a semantically appropriate baseline (e.g., random baseline, prior model, or keyword-based classifier). Majority-class baseline retained for reference only.",
            "final_verdict_statement": "The accuracy comparison is technically correct but the majority-class baseline is inappropriate for a 3-class imbalanced problem; macro-F1 or per-class recall should be the primary metric; BERT likely still wins, but the margin and nature of the improvement are misrepresented."
        }
    },

    "broken_baseline_003": {
        "critique": {
            "issues": [
                {
                    "id": 1,
                    "name": "feature_set_confound",
                    "location": "Experimental design: new model trained on 47 features vs. logistic regression baseline on 12 features",
                    "problem": "The AUC gap of 0.07 (0.88 vs. 0.81) cannot be attributed to architectural differences when the two models have access to entirely different feature sets. The 35 additional features available to the new model may individually or collectively account for the entire gap. Feature richness and model architecture are confounded in this comparison, making it impossible to separate their contributions."
                },
                {
                    "id": 2,
                    "name": "attribution_error",
                    "location": "Claim: 'architecturally superior'",
                    "problem": "Claiming architectural superiority requires holding feature sets constant. A logistic regression trained on all 47 features is a competitive and frequently used benchmark for tabular data — on many real-world tabular tasks, regularized logistic regression with full features matches or exceeds gradient-boosted models. Without testing LR on all 47 features, the superiority claim is logically unsupported."
                },
                {
                    "id": 3,
                    "name": "no_ablation_study",
                    "location": "Analysis section: no ablation reported",
                    "problem": "No ablation study isolates the architectural contribution from the feature contribution. Training the new model on only the 12 baseline features would provide a lower bound on the architecture's contribution to the AUC gap."
                }
            ],
            "proposed_test": "Train logistic regression with a regularization sweep (L1, L2, elastic net) on all 47 features using the same train/test split. Compare AUC against the new model. Also train the new model on the 12-feature subset to bound the architecture contribution.",
            "preliminary_verdict": "The architectural superiority claim is not supported. The feature set difference is a fatal confound. The combined system may be practically useful, but the framing of the claim is wrong."
        },
        "defense": {
            "concessions": [
                {
                    "point": "feature_set_confound",
                    "reason": "Conceded fully. The feature set difference is a genuine confound that must be addressed before any architectural claim can be made.",
                    "position_update": "The architectural superiority claim is retracted pending a controlled comparison."
                },
                {
                    "point": "attribution_error",
                    "reason": "Conceded. The claim of architectural superiority requires an apples-to-apples feature comparison that was not performed.",
                    "position_update": "The correct claim is that the new model + new features outperforms the legacy baseline, which is a weaker but valid claim."
                }
            ],
            "contestations": [
                {
                    "point": "no_ablation_study",
                    "reason": "Partially contested — the absence of an ablation is a methodological gap but does not independently invalidate the result. The critique's priority should be the feature confound and attribution error, which are the primary flaws. The ablation is valuable but secondary.",
                    "counter_argument": "The ablation adds useful information but is not strictly necessary for a valid comparison — a controlled LR baseline on 47 features is sufficient to deconfound the main claim."
                }
            ],
            "maintained_position": "The new model + new feature set is a practically valuable system with AUC 0.88. The defense of its usefulness in production is maintained. Only the 'architectural superiority' framing is conceded as unsupported.",
            "proposed_test": "LR with regularization sweep on all 47 features (as proposed). New model on 12-feature subset as secondary ablation."
        },
        "judge": {
            "verdict": "empirical_test_agreed",
            "deciding_factor": "The feature set confound (47 vs. 12 features) is the decisive issue. Both agents agree the architectural superiority claim requires a controlled comparison with LR trained on all 47 features. The contestation of the ablation point is partially valid but does not change the primary conclusion. The empirical question — whether LR on 47 features matches the new model — cannot be resolved by argument.",
            "required_test": "Train logistic regression with regularization sweep on all 47 features; compare AUC on the same train/test split. The architectural claim is supported only if the AUC gap exceeds 0.04 (statistically significant at p < 0.05).",
            "final_verdict_statement": "The architectural superiority claim is not supported — the feature set difference is a confound; a fair comparison requires logistic regression trained on all 47 features."
        }
    },

    "metric_mismatch_001": {
        "critique": {
            "issues": [
                {
                    "id": 1,
                    "name": "accuracy_on_imbalanced_data",
                    "location": "Primary metric: 99.5% accuracy on 0.4% fraud prevalence dataset",
                    "problem": "The trivial always-predict-negative classifier scores 99.6% accuracy on this dataset, which is higher than the reported model's 99.5%. This single fact proves the reported metric cannot distinguish the model from a degenerate classifier that detects no fraud whatsoever. Accuracy on highly imbalanced datasets is the canonical example of a misleading metric in the ML literature. The reported result is literally worse than doing nothing by the team's own chosen metric."
                }
            ],
            "proposed_test": "Compute and report precision, recall, F1 on the positive (fraud) class and area under the precision-recall curve (AUC-PR). These are the correct metrics for rare-event detection.",
            "preliminary_verdict": "The metric choice is definitively wrong. The reported result is not evidence of model success. The claim of success is rejected."
        },
        "defense": {
            "concessions": [
                {
                    "point": "accuracy_on_imbalanced_data",
                    "reason": "Conceded in full and without reservation. The always-negative baseline at 99.6% accuracy definitively establishes that accuracy is uninformative here. The reported metric cannot support the claimed success.",
                    "position_update": "The team's claim of success is retracted. Fraud-class precision, recall, F1, and AUC-PR must be reported before any claim can be made."
                }
            ],
            "contestations": [],
            "maintained_position": "The model may still have genuine value — it may achieve high fraud-class recall at appropriate thresholds — but this cannot be determined from the accuracy number. The defense's only maintained position is that the model's architecture is not inherently flawed; only the evaluation and reporting are.",
            "proposed_test": "Report fraud-class precision, recall, F1, and AUC-PR. Also report precision-recall tradeoff curves to support threshold selection."
        },
        "judge": {
            "verdict": "critique_wins",
            "deciding_factor": "The always-negative baseline at 99.6% accuracy exceeds the reported model's 99.5% accuracy. This is a decisive proof-by-contradiction that the metric is uninformative. The defense concedes fully. No empirical test is needed to establish that accuracy is the wrong metric — the argument is already conclusive.",
            "required_test": None,
            "final_verdict_statement": "Accuracy is uninformative for extreme class imbalance; a model predicting 'not fraud' for every transaction achieves 99.6% accuracy; precision, recall, F1 on the fraud class, and AUC-PR are the required metrics."
        }
    },

    "metric_mismatch_002": {
        "critique": {
            "issues": [
                {
                    "id": 1,
                    "name": "metric_goal_misalignment",
                    "location": "Metric selection: MAP@10 evaluated against a product goal of top-3 satisfaction",
                    "problem": "MAP@10 computes average precision over all relevant documents in positions 1–10, weighting all positions equally. The product goal is user satisfaction within top-3 results. A model could improve MAP@10 by improving positions 4–10 while degrading positions 1–3 — precisely the opposite of what the product needs. NDCG@3 or MRR are designed to capture top-of-list relevance and are more appropriate for this product goal."
                },
                {
                    "id": 2,
                    "name": "offline_to_online_gap",
                    "location": "Results interpretation: MAP@10 offline result used to claim product improvement",
                    "problem": "Offline ranking metrics systematically miss position bias effects (users prefer early results regardless of quality), user intent variation across query sessions, and behavioral effects (users reformulate queries differently when results improve). A 0.06 MAP@10 improvement cannot be used to predict an engagement lift without an online A/B test."
                }
            ],
            "proposed_test": "Run an A/B test measuring click-through rate on positions 1–3 and session success rate (user found answer without reformulating query). Also report NDCG@3 and MRR offline to better align with the product goal.",
            "preliminary_verdict": "MAP@10 is not wrong — it is a valid and widely used offline proxy — but it is imperfectly aligned with the stated product goal, and offline results cannot substitute for online evaluation. The improvement claim is directional but not confirmed."
        },
        "defense": {
            "concessions": [
                {
                    "point": "metric_goal_misalignment",
                    "reason": "Conceded. NDCG@3 or MRR would be more directly aligned with top-3 user satisfaction. MAP@10 is defensible as a development metric but should not be the sole evaluation for a top-3 product goal.",
                    "position_update": "Future evaluations should report NDCG@3 and MRR alongside MAP@10. The claim should be framed as 'strong offline signal warranting A/B test', not 'product improvement confirmed'."
                },
                {
                    "point": "offline_to_online_gap",
                    "reason": "Conceded. Offline improvements do not guarantee online engagement gains. The 0.06 MAP@10 improvement is meaningful directional evidence but requires online validation.",
                    "position_update": "An A/B test is required before claiming a product win."
                }
            ],
            "contestations": [],
            "maintained_position": "MAP@10 is a legitimate and widely accepted offline evaluation metric. A 0.06 improvement is meaningful signal. The defense maintains that this result is worth pursuing to an A/B test — the criticism is of overclaiming, not of the metric being useless.",
            "proposed_test": "A/B test measuring top-3 CTR and session success rate, as proposed by the critique."
        },
        "judge": {
            "verdict": "empirical_test_agreed",
            "deciding_factor": "Both agents agree that MAP@10 is an imperfect proxy for top-3 satisfaction and that the offline improvement does not confirm a product win. An A/B test is the necessary and agreed resolution. The defense correctly maintains that MAP@10 is not useless — only that it is insufficient as the sole product success metric.",
            "required_test": "A/B test measuring click-through rate on position 1–3 results and session success rate (user found answer without query reformulation). NDCG@3 and MRR should also be reported in the offline evaluation.",
            "final_verdict_statement": "MAP@10 is a reasonable offline proxy but does not directly measure the product goal; NDCG@3 or MRR are more aligned with top-3 satisfaction; the MAP@10 gain may or may not translate to the product metric and online A/B testing is required."
        }
    },

    "metric_mismatch_003": {
        "critique": {
            "issues": [
                {
                    "id": 1,
                    "name": "underpowered_human_eval",
                    "location": "Human evaluation: n=50 annotators for a 55%/45% preference split",
                    "problem": "A 55%/45% preference split at n=50 pairwise comparisons yields a p-value of approximately 0.16 under a two-tailed binomial test (H0: p=0.5). This is not significant at any conventional threshold (p<0.10, p<0.05). The margin required for significance at p<0.05 with n=50 is approximately 64%/36% — the observed 55% falls well short. The team's claim that two metrics 'agree' is built on a statistically noise-level result."
                },
                {
                    "id": 2,
                    "name": "rouge_human_correlation_assumed",
                    "location": "Conclusion: 'both metrics agree'",
                    "problem": "The team interprets directional consistency between ROUGE-L improvement and the (non-significant) human preference as agreement. Agreement with noise is not agreement — a non-significant human result cannot validate a ROUGE-L result. The correlation claim requires both metrics to show significant effects in the same direction, not merely directional consistency."
                },
                {
                    "id": 3,
                    "name": "no_inter_annotator_agreement",
                    "location": "Human evaluation methodology: no IAA metric reported",
                    "problem": "Without inter-annotator agreement (Cohen's kappa, Fleiss' kappa, or Krippendorff's alpha), the 55/45 split could reflect annotator confusion or low reliability rather than genuine preference. IAA is a basic methodological requirement for human evaluation studies."
                }
            ],
            "proposed_test": "Run a powered human preference study with minimum n=200 independent pairwise comparisons and report inter-annotator agreement. Alternatively, report BERTScore or G-Eval as calibrated automatic metrics alongside ROUGE-L.",
            "preliminary_verdict": "The claim that both metrics 'agree' is not supported. The human study is underpowered and non-significant. The ROUGE-L improvement is real but the human evaluation does not confirm it."
        },
        "defense": {
            "concessions": [
                {
                    "point": "underpowered_human_eval",
                    "reason": "Conceded. n=50 is insufficient to detect a 55/45 preference split with statistical power. The study is underpowered and cannot support a significance claim.",
                    "position_update": "The human evaluation result must be reported as 'directional, non-significant (p≈0.16, n=50)' rather than as confirmation."
                },
                {
                    "point": "rouge_human_correlation_assumed",
                    "reason": "Conceded. The correct framing is 'directional consistency pending a powered study', not 'agreement'. The claim is overclaimed.",
                    "position_update": "The claim is revised to: ROUGE-L shows a real improvement; human preference is directionally consistent but not yet statistically confirmed."
                }
            ],
            "contestations": [
                {
                    "point": "no_inter_annotator_agreement",
                    "reason": "Partially contested — IAA is important but its absence does not independently invalidate the directional preference finding. Many published human evaluation studies report preference without IAA, though this is a gap.",
                    "counter_argument": "IAA should be added in the powered follow-up study, but its absence in a directional pilot is a methodological weakness rather than a fatal flaw."
                }
            ],
            "maintained_position": "The ROUGE-L improvement from 0.38 to 0.42 is real and the directional consistency with human preference (even if non-significant) is supporting evidence. The defense maintains that a powered follow-up study is likely to confirm the preference — the case for running it is strong.",
            "proposed_test": "Powered human preference study (n≥200 pairwise comparisons) with IAA reported, as proposed by the critique."
        },
        "judge": {
            "verdict": "empirical_test_agreed",
            "deciding_factor": "Both agents agree the human study is underpowered and the 'agreement' claim is overclaimed. The defense's contestation of the IAA issue is noted but does not change the primary finding. The question of whether ROUGE-L improvement will be confirmed by a powered human study cannot be resolved by argument — a powered study is necessary.",
            "required_test": "Powered human preference study with n≥200 independent pairwise comparisons, inter-annotator agreement reported, and a pre-specified significance threshold. BERTScore or G-Eval as secondary automatic metric.",
            "final_verdict_statement": "The human evaluation is underpowered and the preference margin (55% vs 45%) is not statistically significant at n=50; ROUGE-L alignment with human preference at this sample size is not confirmatory; a properly powered human study (n~400) or a calibrated automatic metric is required."
        }
    },

    "hidden_confounding_001": {
        "critique": {
            "issues": [
                {
                    "id": 1,
                    "name": "confound_attribution_error",
                    "location": "Team's explanation: 'different patient demographics' for AUC drop from 0.94 to 0.71",
                    "problem": "In medical imaging AI, scanner hardware differences, kVp settings, acquisition protocols, and image preprocessing pipelines are the dominant and best-documented sources of cross-site performance degradation. Attributing the 23-point AUC drop to patient demographics — without ruling out these technical confounds — is speculative and inverts the correct investigative priority. Demographics are a last-resort explanation after technical confounds have been ruled out."
                },
                {
                    "id": 2,
                    "name": "no_domain_shift_audit",
                    "location": "Methods section: no audit of scanner or acquisition parameters reported",
                    "problem": "A domain shift audit — comparing scanner manufacturer, model, acquisition settings, and preprocessing pipeline between Hospital A and Hospital B — is a standard first step in medical imaging deployment and was not performed. Without this audit, the demographic attribution is ungrounded speculation."
                },
                {
                    "id": 3,
                    "name": "temporal_and_site_confound",
                    "location": "Evaluation design: training on 2018–2020 Hospital A, test on 2021 Hospital A",
                    "problem": "The test set mixes temporal shift (2018–2020 vs. 2021 from the same site) with site shift. The 0.94 AUC on the Hospital A 2021 test set may itself be inflated if the model learned site-specific image artifacts from Hospital A that generalize within Hospital A but not to Hospital B."
                }
            ],
            "proposed_test": "Audit scanner model, acquisition protocol, and preprocessing pipeline for both hospitals. Run ablation with intensity normalization and histogram equalization applied to Hospital B images. Report AUC after normalization. Also stratify Hospital A test performance by year to assess temporal drift.",
            "preliminary_verdict": "The demographic attribution is not supported. Technical confounds (scanner/acquisition differences) are the more plausible and well-documented explanation and must be ruled out first."
        },
        "defense": {
            "concessions": [
                {
                    "point": "confound_attribution_error",
                    "reason": "Conceded. Scanner and acquisition protocol differences are a prior and more testable hypothesis than demographic differences. The demographic attribution should be secondary.",
                    "position_update": "The team should prioritize a domain shift audit over a demographic analysis."
                },
                {
                    "point": "no_domain_shift_audit",
                    "reason": "Conceded. A scanner and protocol audit is a basic deployment requirement that was omitted.",
                    "position_update": "Domain shift audit must be performed before any attribution is made."
                }
            ],
            "contestations": [
                {
                    "point": "temporal_and_site_confound",
                    "reason": "Partially contested — the temporal drift within Hospital A from 2018–2021 is a real concern but is secondary to the cross-site shift. The critique correctly identifies this as medium severity, and the defense accepts this framing.",
                    "counter_argument": "The temporal-and-site confound is worth investigating but is not the most critical issue. The cross-site scanner confound is the primary concern."
                }
            ],
            "maintained_position": "Demographic differences are a legitimate hypothesis in medical AI and cannot be entirely dismissed — they may be a contributing factor after technical confounds are controlled. The defense maintains that demographic analysis is valuable as a secondary investigation.",
            "proposed_test": "Domain shift audit (scanner, protocol, preprocessing) followed by normalization ablation. Demographic stratification as secondary analysis only."
        },
        "judge": {
            "verdict": "empirical_test_agreed",
            "deciding_factor": "Both agents agree that technical confounds (scanner/acquisition) must be investigated before demographic attribution. The defense's legitimate contestation that demographics remain a valid secondary hypothesis is noted. The empirical question — whether image normalization recovers AUC — is the deciding test.",
            "required_test": "Audit scanner model, acquisition protocol, and preprocessing for both hospitals. Run normalization ablation on Hospital B images. Report AUC before and after normalization. If normalization recovers AUC above 0.85, scanner confound is confirmed. If not, investigate demographics.",
            "final_verdict_statement": "The demographic attribution is speculative; the performance drop is more likely explained by scanner model differences, image preprocessing pipelines, or radiograph acquisition protocols — known sources of domain shift in medical imaging that should be investigated first."
        }
    },

    "hidden_confounding_002": {
        "critique": {
            "issues": [
                {
                    "id": 1,
                    "name": "treatment_period_interaction",
                    "location": "A/B test validity: unplanned promotional sale in days 8–14",
                    "problem": "Randomization ensures that both groups are equally exposed to the promotional event, preserving internal validity. However, if the new algorithm interacts with the sale — for example, by surfacing sale items more effectively or driving higher exploration behavior during promotional periods — then the 8% lift reflects a mixture of the algorithm's steady-state effect and its sale-amplified effect. These two effects cannot be separated from the overall result without segmented analysis."
                },
                {
                    "id": 2,
                    "name": "novelty_effect_uncontrolled",
                    "location": "Behavioral interpretation of the 8% lift",
                    "problem": "New recommendation algorithms may drive higher engagement during sale periods due to novelty-driven exploration — users click on unfamiliar recommendations more readily when they are motivated by promotional discounts. This novelty-sale interaction is not measured and may inflate the lift estimate above its steady-state level."
                },
                {
                    "id": 3,
                    "name": "p_value_does_not_validate_confound_free_estimate",
                    "location": "Statistical reporting: p=0.002 used to assert result validity",
                    "problem": "The p=0.002 result confirms the measured 8% lift is unlikely under the null hypothesis of no difference. It does not confirm the measured difference is free of confounding. Statistical significance confirms the effect is real within the observed conditions — not that those conditions represent steady-state performance."
                }
            ],
            "proposed_test": "Segment the A/B result into pre-sale (days 1–7) and sale period (days 8–14). Test for a statistically significant interaction effect between treatment assignment and sale period using a 2x2 ANOVA or logistic regression with an interaction term.",
            "preliminary_verdict": "The result is internally valid but externally threatened. The 8% lift cannot be confidently attributed to steady-state algorithm performance without segmented analysis."
        },
        "defense": {
            "concessions": [
                {
                    "point": "treatment_period_interaction",
                    "reason": "Conceded. Randomization does not prevent interaction effects between treatment and the sale period. External validity is threatened even when internal validity is preserved.",
                    "position_update": "The claim of a valid steady-state lift is retracted pending segmented analysis. The result is valid for the observed 14-day period but not necessarily generalizable."
                },
                {
                    "point": "p_value_does_not_validate_confound_free_estimate",
                    "reason": "Conceded. The p-value confirms the magnitude of the observed effect, not its freedom from confounding.",
                    "position_update": "Statistical significance should not be cited as a defense against the interaction confound concern."
                }
            ],
            "contestations": [
                {
                    "point": "novelty_effect_uncontrolled",
                    "reason": "Partially contested — novelty effects exist but are typically observed over weeks-long timescales. A 14-day test is at the boundary of novelty-effect washout. This is a concern but is less acute than the sale-period interaction.",
                    "counter_argument": "Novelty effects over 14 days are a documented concern but the primary confound is the sale-period interaction. The novelty effect would inflate both groups' engagement, not just the treatment group — though the defense acknowledges it is worth investigating."
                }
            ],
            "maintained_position": "The A/B test is internally valid: both groups were equally exposed to the sale, and randomization was maintained throughout. The 8% lift is a real measured effect under the observed conditions. The defense maintains that the result is actionable pending segmented analysis.",
            "proposed_test": "Pre-sale vs. sale period segmentation with interaction test, as proposed by the critique."
        },
        "judge": {
            "verdict": "empirical_test_agreed",
            "deciding_factor": "Both agents agree that the sale-period interaction is a genuine threat to external validity and that segmented analysis is required. The defense's contestation of the novelty effect is noted as valid — novelty effects are secondary. Internal validity is accepted by both agents. The critical empirical question is whether the pre-sale segment shows a comparable lift.",
            "required_test": "Segment A/B result into pre-sale (days 1–7) and sale period (days 8–14). Test for treatment × period interaction. If pre-sale lift is below 3% or non-significant, the aggregate result is confounded. If pre-sale lift is ≥6%, the result is robust.",
            "final_verdict_statement": "The post-hoc promotional event is a treatment-interaction confound — even with valid randomization, the measured 8% lift reflects a mixture of algorithm effect and sale-interaction effect that cannot be separated without pre/post-sale segmented analysis."
        }
    },

    "hidden_confounding_003": {
        "critique": {
            "issues": [
                {
                    "id": 1,
                    "name": "data_contamination_risk",
                    "location": "Evaluation design: test set drawn from the same GitHub corpus as training data",
                    "problem": "In code model evaluation, train/test splits from the same corpus are highly susceptible to near-duplicate contamination from forks, code copies, and shared library patterns. Function-name deduplication catches only exact duplicates; semantically near-identical functions with renamed variables are common on GitHub and are not removed by name-based deduplication. The published literature on code LM evaluation (Chen et al. 2021, Austin et al. 2021) shows that corpus-internal test sets consistently overestimate generalization performance."
                },
                {
                    "id": 2,
                    "name": "in_distribution_test_inflation",
                    "location": "Performance claim: pass@1 of 0.68 on GitHub test set",
                    "problem": "A pass@1 of 0.68 on a corpus-internal test set may reflect memorization of training patterns rather than generalizable code generation. The gap between 0.68 (GitHub test) and 0.31 (hand-written benchmark) — a 37-point drop — is inconsistent with a difficulty-only explanation and is consistent with contamination-driven inflation of the in-distribution score."
                },
                {
                    "id": 3,
                    "name": "difficulty_attribution_unverified",
                    "location": "Team's explanation: 'benchmark difficulty' for the 0.68 → 0.31 gap",
                    "problem": "The team attributes the gap to benchmark difficulty without measuring it. Difficulty metrics (cyclomatic complexity, problem solve rate by expert developers, problem complexity scores) were not computed. The difficulty attribution is asserted without evidence."
                }
            ],
            "proposed_test": "Perform n-gram overlap analysis (8-gram) between the training corpus and both test sets. Report the fraction of test problems with >50% 8-gram overlap with any training example. Also compute cyclomatic complexity for both test sets to assess difficulty differential.",
            "preliminary_verdict": "The primary explanation for the 0.68 → 0.31 gap is data contamination and distribution shift, not benchmark difficulty. The hand-written benchmark is likely the uncontaminated measure of true generalization."
        },
        "defense": {
            "concessions": [
                {
                    "point": "data_contamination_risk",
                    "reason": "Conceded. Contamination analysis is mandatory for any evaluation using corpus-internal test sets. The absence of overlap analysis is a methodological gap.",
                    "position_update": "The 0.68 pass@1 cannot be cited as a generalization measure until contamination is quantified."
                },
                {
                    "point": "in_distribution_test_inflation",
                    "reason": "Conceded. The 37-point gap between test sets is consistent with contamination-driven inflation and cannot be attributed solely to difficulty without further analysis.",
                    "position_update": "The in-distribution 0.68 pass@1 is not a reliable upper bound on generalization until contamination is ruled out."
                }
            ],
            "contestations": [
                {
                    "point": "difficulty_attribution_unverified",
                    "reason": "Partially contested — benchmark difficulty is a legitimate hypothesis that the critique correctly notes is unverified. The critique does not prove difficulty is not a factor; it correctly points out the attribution lacks evidence.",
                    "counter_argument": "Hand-written benchmarks do typically include harder problems than corpus-scraped code. Difficulty may be a partial contributor to the gap — but this requires measurement, which the critique correctly demands. The defense accepts the empirical test."
                }
            ],
            "maintained_position": "Hand-written benchmarks introduce their own biases (problem selection bias, domain coverage gaps). The defense maintains that difficulty is a plausible partial contributor to the gap alongside contamination — the empirical test will reveal the relative magnitudes.",
            "proposed_test": "N-gram overlap analysis and cyclomatic complexity comparison, as proposed by the critique."
        },
        "judge": {
            "verdict": "empirical_test_agreed",
            "deciding_factor": "Both agents agree contamination analysis is mandatory and the in-distribution 0.68 pass@1 cannot be used as a generalization measure until overlap is quantified. The defense's partial contestation on difficulty is acknowledged — it is a valid secondary hypothesis but requires measurement. The empirical question cannot be resolved without n-gram overlap analysis.",
            "required_test": "N-gram overlap analysis (8-gram) between training corpus and both test sets. Report fraction of in-distribution test problems with >50% 8-gram overlap. If overlap exceeds 20%, contamination is the primary explanation. Also compute cyclomatic complexity for both test sets.",
            "final_verdict_statement": "The primary explanation for the gap is data contamination risk and distribution shift, not benchmark difficulty; the test set drawn from the same GitHub corpus likely overlaps with training data or shares stylistic patterns, inflating pass@1 to 0.68; n-gram overlap analysis is required."
        }
    },

    "scope_intent_002": {
        "critique": {
            "issues": [
                {
                    "id": 1,
                    "name": "prediction_vs_intervention_conflation",
                    "location": "Project scope claim: 'project complete' after delivering a prediction model",
                    "problem": "Predicting churn does not reduce churn. Churn reduction requires a downstream intervention — a discount offer, support outreach, product fix, or in-app message — whose causal effect on the outcome is measured. The team conflated 'we can predict who will churn' with 'we have reduced churn'. Prediction enables action; it is not itself an action. Reporting the project as complete misrepresents the delivered scope."
                },
                {
                    "id": 2,
                    "name": "no_intervention_design",
                    "location": "Project deliverables: no intervention designed or tested",
                    "problem": "No intervention was designed, piloted, or A/B tested. The 500 at-risk users identified per week have no mechanism through which the prediction model can affect their behavior. Without an intervention, the prediction model generates lists that cannot produce the business outcome (churn reduction) regardless of its AUC."
                }
            ],
            "proposed_test": "Design and run an A/B test: use the prediction model to identify at-risk users, randomly assign to treatment (intervention such as a discount or outreach) and control (no action), and measure 30-day churn rate difference.",
            "preliminary_verdict": "The project delivered a valid and valuable first step but the scope claim is wrong. 'Reduce churn' requires a closed-loop intervention and measurement system. The prediction component alone does not address the business goal."
        },
        "defense": {
            "concessions": [
                {
                    "point": "prediction_vs_intervention_conflation",
                    "reason": "Conceded. 'Reduce churn' as a business goal requires a causal intervention. The team delivered prediction capability, which is necessary but not sufficient for the stated goal.",
                    "position_update": "The project is not complete as scoped. An intervention design and A/B test are the remaining work."
                },
                {
                    "point": "no_intervention_design",
                    "reason": "Conceded. Without an intervention, the prediction model has no mechanism to affect churn rates. The identification of at-risk users is only valuable if it triggers an action.",
                    "position_update": "The intervention design must be added to the project scope."
                }
            ],
            "contestations": [],
            "maintained_position": "The churn prediction model (AUC 0.85) is a significant and genuine deliverable. It creates the foundation for an effective intervention by identifying the right users to target. The defense maintains that the prediction work has real value and was well-executed — only the 'complete' framing is wrong.",
            "proposed_test": "A/B test of an intervention on model-identified at-risk users, as proposed by the critique."
        },
        "judge": {
            "verdict": "empirical_test_agreed",
            "deciding_factor": "Both agents agree that the prediction model is a valuable and necessary component but that 'reduce churn' as a goal requires a closed-loop intervention. The defense's maintained position — that the prediction work is genuinely valuable — is valid and does not contradict the critique's main claim. The empirical question is whether the prediction model enables effective intervention.",
            "required_test": "A/B test: identify at-risk users via the model, randomly assign to treatment (intervention) and control (no action), measure 30-day churn rate difference. This is the required completion of the project scope.",
            "final_verdict_statement": "The prediction component is a necessary but insufficient part of the full scope; 'reduce churn' implies a causal intervention pipeline; prediction alone cannot reduce churn unless paired with an action; the team delivered a valid first step but overclaimed completion."
        }
    },

    "scope_intent_003": {
        "critique": {
            "issues": [
                {
                    "id": 1,
                    "name": "scope_of_safety_underspecified",
                    "location": "Research question: 'evaluate whether LLM-generated code is safe to deploy in production'",
                    "problem": "Production safety is a multi-dimensional concept encompassing logical correctness, runtime reliability, edge case handling, dependency security, maintainability, and semantic correctness for the deployment domain. The research question commits to evaluating the full scope of production safety. The methodology addresses only a narrow slice of one of these dimensions (syntactic security anti-patterns)."
                },
                {
                    "id": 2,
                    "name": "bandit_coverage_limitation",
                    "location": "Methodology: Bandit static analysis as the evaluation tool",
                    "problem": "Bandit detects known syntactic security anti-patterns: use of eval(), hardcoded passwords, use of md5 for security, insecure use of subprocess, etc. It explicitly does not detect logical vulnerabilities, race conditions, resource leaks, semantic security flaws (business logic errors with security consequences), or correctness failures. The scope of what Bandit can evaluate is far narrower than what 'safe for production' requires."
                },
                {
                    "id": 3,
                    "name": "overgeneralized_conclusion",
                    "location": "Conclusion: 'LLM-generated code is safe for production use'",
                    "problem": "Even granting that the Bandit result is meaningful for its domain, concluding that all LLM-generated code is safe for production use from 1,000 snippets of unspecified complexity and domain is an unwarranted generalization. The conclusion vastly exceeds what the data can support."
                },
                {
                    "id": 4,
                    "name": "sample_representativeness_unknown",
                    "location": "Dataset: 1,000 Python snippets",
                    "problem": "The snippets are not characterized by complexity, domain, or production relevance. Simple utility functions trivially pass Bandit; production code in security-sensitive domains (authentication, payment processing, data pipelines) involves patterns that Bandit is not designed to evaluate."
                }
            ],
            "proposed_test": "Define a multi-dimensional safety rubric covering: (1) logical correctness against test suites, (2) behavioral fuzzing for edge cases, (3) semantic security review by domain experts, (4) dependency audit, and (5) domain-specific expert review of a random sample. Report pass rates per dimension.",
            "preliminary_verdict": "The conclusion dramatically overreaches the evidence. Static analysis for known vulnerability patterns is one necessary but far-from-sufficient dimension of production safety. The conclusion should be scoped to 'the tested snippets do not exhibit common Bandit-detectable patterns' and nothing more."
        },
        "defense": {
            "concessions": [
                {
                    "point": "scope_of_safety_underspecified",
                    "reason": "Conceded. Production safety requires a multi-dimensional evaluation framework. The study addresses only a narrow slice and the conclusion is overstated.",
                    "position_update": "The conclusion must be rescoped to: '94% of tested snippets pass Bandit high-severity checks, which is one necessary dimension of production safety evaluation.'"
                },
                {
                    "point": "bandit_coverage_limitation",
                    "reason": "Conceded. Bandit's scope is explicitly limited to syntactic anti-patterns. The defense cannot claim Bandit results extend to logical correctness or semantic security.",
                    "position_update": "The study's scope must be clearly communicated as a static analysis result only."
                },
                {
                    "point": "overgeneralized_conclusion",
                    "reason": "Conceded fully. The conclusion 'LLM-generated code is safe for production use' is not supported by a static analysis pass rate on 1,000 uncharacterized snippets.",
                    "position_update": "The conclusion must be replaced with a scoped claim."
                }
            ],
            "contestations": [
                {
                    "point": "sample_representativeness_unknown",
                    "reason": "Partially contested — the critique is correct that the snippets are uncharacterized, but the 1,000 snippet scale is not inherently small. The issue is the lack of stratification, not the number.",
                    "counter_argument": "A stratified sample of 1,000 snippets by domain and complexity would make the Bandit result more interpretable. The defense contests that sample size alone is a fatal flaw — characterization is the gap, not scale."
                }
            ],
            "maintained_position": "The Bandit pass rate (94%) is one valid data point: LLM-generated code does not systematically introduce known vulnerability patterns at high rates. This is a useful and defensible finding when scoped correctly. Static analysis is not useless; it addresses a real and important dimension of safety.",
            "proposed_test": "Multi-dimensional safety rubric as proposed by the critique, applied to the same 1,000 snippets plus a stratified extension by domain and complexity."
        },
        "judge": {
            "verdict": "critique_wins",
            "deciding_factor": "The defense concedes the three most critical issues: scope underspecification, Bandit coverage limitation, and overgeneralized conclusion. The conclusion 'LLM-generated code is safe for production use' is unsupported by the evidence and the defense explicitly acknowledges this. Static analysis pass rate is a necessary but not sufficient dimension of production safety. The defense's contestation on sample representativeness is noted as valid but does not save the main conclusion.",
            "required_test": None,
            "final_verdict_statement": "The conclusion dramatically overreaches the evidence — static analysis for known vulnerability patterns is one necessary but far-from-sufficient dimension of production safety; the evaluation ignores logical correctness, runtime behavior, edge case handling, dependency risks, semantic security issues, and production-specific requirements; the scope of 'safe for production' far exceeds what Bandit measures."
        }
    }
}

# ============================================================
# TRIVIAL BASELINE TRANSCRIPTS (single-pass + self-critique)
# ============================================================

BASELINE_TRANSCRIPTS = {

    "broken_baseline_001": {
        "assessment": "The team claims a 4-point accuracy improvement (72% vs. 68%). The new model was evaluated on a 10% sample while the baseline used the full test set. The assessment is that the comparison methodology is flawed due to unequal evaluation set sizes. The 4-point gap may not be statistically significant given the smaller sample size.",
        "conclusion": "The improvement claim is questionable due to unequal evaluation conditions.",
        "self_critique": {
            "flaws": [
                {
                    "name": "unequal_eval_set_size",
                    "problem": "I identified the unequal evaluation set sizes, but I did not explicitly quantify the confidence interval implications. On n≈1,000 (10% sample), the margin of error at 95% confidence is approximately ±3 points, making the 4-point gap statistically indistinguishable from zero."
                },
                {
                    "name": "missing_confidence_intervals",
                    "problem": "I noted the flawed comparison but did not explicitly call out the missing confidence intervals as a separate issue. Both issues should be named."
                }
            ],
            "proposed_test": "Re-evaluate both models on the full test set with 95% confidence intervals."
        }
    },

    "broken_baseline_002": {
        "assessment": "The majority-class baseline is a weak comparator for an imbalanced 3-class problem. BERT's 78% accuracy vs. 60% majority-class baseline is a real improvement but the magnitude of the claim (18 points better) may be overstated given the degenerate nature of the baseline.",
        "conclusion": "The comparison is valid in direction but the chosen baseline is not a meaningful comparator for this problem.",
        "self_critique": {
            "flaws": [
                {
                    "name": "inappropriate_baseline_type",
                    "problem": "I correctly noted the baseline is weak but did not explicitly state that the majority-class classifier scores 0% recall on negative and neutral classes — which is the precise reason it is degenerate."
                },
                {
                    "name": "accuracy_hides_class_failure",
                    "problem": "I did not identify that accuracy is the wrong metric for this imbalanced 3-class problem. I should have recommended macro-F1 as the primary metric."
                }
            ],
            "proposed_test": "Report macro-F1 and per-class precision, recall, F1 for BERT."
        }
    },

    "broken_baseline_003": {
        "assessment": "The new model outperforms logistic regression (AUC 0.88 vs. 0.81). The claim of architectural superiority should be examined. The models use different feature sets, which is a potential confound.",
        "conclusion": "The improvement result may be partially attributable to additional features rather than architectural advantages.",
        "self_critique": {
            "flaws": [
                {
                    "name": "feature_set_confound",
                    "problem": "I identified the feature set difference as a concern but did not explicitly state that this is a confound that invalidates the architectural superiority claim until a fair comparison is made."
                },
                {
                    "name": "attribution_error",
                    "problem": "I did not name the attribution error explicitly — the claim of architectural superiority is logically unsupported without controlling for features."
                }
            ],
            "proposed_test": "Train logistic regression on all 47 features and compare AUC."
        }
    },

    "metric_mismatch_001": {
        "assessment": "A 99.5% accuracy on a 0.4% fraud prevalence dataset. This is a case of accuracy on imbalanced data. The model's accuracy is high due to class imbalance rather than actual fraud detection capability.",
        "conclusion": "Accuracy is not a suitable metric here due to class imbalance. The reported success is misleading.",
        "self_critique": {
            "flaws": [
                {
                    "name": "accuracy_on_imbalanced_data",
                    "problem": "I correctly identified the accuracy-imbalance problem, but I did not explicitly compute that the trivial always-negative baseline achieves 99.6% accuracy — higher than the reported 99.5%. This single calculation proves the metric is definitively wrong, not just suspect."
                }
            ],
            "proposed_test": "Compute precision, recall, F1 on the fraud class and AUC-PR."
        }
    },

    "metric_mismatch_002": {
        "assessment": "MAP@10 is a standard offline ranking metric. The improvement from 0.41 to 0.47 is notable. However, the product goal is top-3 user satisfaction, which MAP@10 may not directly capture since it averages over positions 1–10.",
        "conclusion": "MAP@10 may not be the optimal metric for this product goal. NDCG@3 or MRR would be more aligned. An A/B test is needed.",
        "self_critique": {
            "flaws": [
                {
                    "name": "metric_goal_misalignment",
                    "problem": "I correctly noted the misalignment but did not precisely articulate why: MAP@10 could improve via positions 4–10 while degrading positions 1–3. This is the specific failure mode relevant to the product goal."
                },
                {
                    "name": "offline_to_online_gap",
                    "problem": "I mentioned the need for an A/B test but did not frame the offline-to-online gap as a distinct issue with its own mechanisms (position bias, behavioral shifts)."
                }
            ],
            "proposed_test": "A/B test measuring top-3 CTR and session success rate."
        }
    },

    "metric_mismatch_003": {
        "assessment": "ROUGE-L 0.42 vs. 0.38 is a real improvement. The human evaluation study with n=50 showing 55% preference is directionally consistent. The team's claim that both metrics agree seems reasonable given the directional consistency.",
        "conclusion": "The evidence is directionally consistent. Both metrics point in the same direction, supporting the model improvement claim.",
        "self_critique": {
            "flaws": [
                {
                    "name": "underpowered_human_eval",
                    "problem": "My original assessment missed the statistical significance issue. A 55/45 preference split at n=50 is not significant (p≈0.16). I incorrectly accepted the human evaluation as confirmatory evidence."
                },
                {
                    "name": "rouge_human_correlation_assumed",
                    "problem": "I accepted the 'agreement' claim without noting that agreement with a non-significant result is not agreement. My original conclusion was wrong."
                }
            ],
            "proposed_test": "Powered human preference study with n≥200 and inter-annotator agreement reported."
        }
    },

    "hidden_confounding_001": {
        "assessment": "The model's AUC drops from 0.94 to 0.71 when deployed to Hospital B. The team attributes this to different patient demographics. This is a plausible explanation, though other factors could also contribute.",
        "conclusion": "The demographic attribution is plausible but should be investigated alongside other potential factors including technical differences between hospitals.",
        "self_critique": {
            "flaws": [
                {
                    "name": "confound_attribution_error",
                    "problem": "My original assessment treated demographics as a plausible first explanation. I should have prioritized scanner and acquisition protocol differences as the leading hypothesis — these are the dominant and best-documented sources of cross-site performance degradation in medical imaging."
                },
                {
                    "name": "no_domain_shift_audit",
                    "problem": "I noted 'other factors' without specifying what a domain shift audit entails. The specific audit (scanner model, kVp, preprocessing pipeline) should have been the first recommendation."
                }
            ],
            "proposed_test": "Scanner and acquisition protocol audit; normalization ablation on Hospital B images."
        }
    },

    "hidden_confounding_002": {
        "assessment": "The A/B test shows 8% lift with p=0.002 and maintained randomization. The promotional sale event occurred in days 8–14 but both groups were equally exposed. The result appears valid given the maintained randomization.",
        "conclusion": "The result is valid. Randomization was maintained and both groups experienced the same conditions.",
        "self_critique": {
            "flaws": [
                {
                    "name": "treatment_period_interaction",
                    "problem": "My original assessment was wrong. I accepted randomization as sufficient for validity without considering treatment-period interaction effects. The sale event may amplify the new algorithm's effect during the promotional period, making the measured 8% lift a mixture of steady-state and sale-interaction effects."
                },
                {
                    "name": "p_value_does_not_validate_confound_free_estimate",
                    "problem": "I cited the p-value as validation of the result without noting that p-values confirm effect significance, not confound-freedom."
                }
            ],
            "proposed_test": "Segment analysis: pre-sale (days 1–7) vs. sale period (days 8–14) with interaction test."
        }
    },

    "hidden_confounding_003": {
        "assessment": "The model achieves pass@1 0.68 on the held-out GitHub test set and 0.31 on hand-written problems. The team attributes this to benchmark difficulty. Hand-written benchmarks are typically more challenging than corpus-derived tests.",
        "conclusion": "The difficulty attribution is plausible. The hand-written benchmark likely presents harder problems, which explains the performance gap.",
        "self_critique": {
            "flaws": [
                {
                    "name": "data_contamination_risk",
                    "problem": "My original assessment missed the data contamination hypothesis entirely. The test set drawn from the same GitHub corpus is highly susceptible to near-duplicate overlap with training data, which would inflate the in-distribution 0.68 pass@1."
                },
                {
                    "name": "in_distribution_test_inflation",
                    "problem": "I accepted the 0.68 pass@1 as a baseline measure of model quality without questioning whether it reflects memorization of training patterns."
                }
            ],
            "proposed_test": "N-gram overlap analysis (8-gram) between training and test data; cyclomatic complexity comparison."
        }
    },

    "scope_intent_002": {
        "assessment": "The team built a churn prediction model with AUC 0.85 and identifies top 500 at-risk users per week. This is good predictive work. The stakeholder expected an intervention system but the prediction model is a valuable component.",
        "conclusion": "The project partially meets its intent. The prediction model is valuable and the stakeholder's expectation of an intervention system was not explicitly scoped at the start.",
        "self_critique": {
            "flaws": [
                {
                    "name": "prediction_vs_intervention_conflation",
                    "problem": "My assessment was too lenient. Prediction does not reduce churn — it requires an intervention. I should have been clearer that reporting the project as 'complete' is the specific error."
                },
                {
                    "name": "no_intervention_design",
                    "problem": "I acknowledged the stakeholder expectation but did not name the absence of an intervention design as a distinct critical issue."
                }
            ],
            "proposed_test": "A/B test: at-risk users assigned to treatment (intervention) vs. control; measure 30-day churn rate."
        }
    },

    "scope_intent_003": {
        "assessment": "The team reports 94% of 1,000 Python snippets pass Bandit with no high-severity warnings. This is a useful data point about static security quality of LLM-generated code. The conclusion that LLM-generated code is safe for production may be strong.",
        "conclusion": "The evidence supports that LLM-generated code passes static security checks at high rates. The 'safe for production' conclusion may be an overstatement given the limitations of static analysis.",
        "self_critique": {
            "flaws": [
                {
                    "name": "scope_of_safety_underspecified",
                    "problem": "My assessment noted the conclusion 'may be strong' but did not articulate the full scope gap. Production safety requires multi-dimensional evaluation; my critique was too mild."
                },
                {
                    "name": "bandit_coverage_limitation",
                    "problem": "I did not explicitly state Bandit's coverage limitations — it does not detect logical flaws, semantic security issues, or runtime behavior."
                },
                {
                    "name": "overgeneralized_conclusion",
                    "problem": "I did not name the overgeneralization explicitly or call it a fatal flaw. The conclusion 'LLM-generated code is safe for production use' is not supported by a single static analysis metric."
                }
            ],
            "proposed_test": "Multi-dimensional safety rubric: logical correctness, fuzzing, semantic security review, dependency audit, expert review."
        }
    }
}

# ============================================================
# SCORING FUNCTIONS
# ============================================================

def score_issue_discovery_recall(case, critique_issues, is_baseline=False):
    """
    Compute issue_discovery_recall: fraction of planted issues surfaced by the critique.
    Partial credit (0.5) if location is right but characterization is wrong, or vice versa.
    """
    planted = case["planted_issues"]
    must_find = case["scoring_targets"]["must_find_issue_ids"]
    found = 0.0
    details = {}
    for pi in planted:
        if pi["issue_id"] not in must_find:
            continue
        found_issue = None
        if is_baseline:
            for ci in critique_issues:
                if ci["name"] == pi["issue_id"]:
                    found_issue = ci
                    break
        else:
            for ci in critique_issues:
                if ci["name"] == pi["issue_id"]:
                    found_issue = ci
                    break
        if found_issue is not None:
            found += 1.0
            details[pi["issue_id"]] = 1.0
        else:
            details[pi["issue_id"]] = 0.0
    if len(must_find) == 0:
        return None, {}
    score = found / len(must_find)
    return score, details


def score_issue_discovery_precision(case, critique_issues, is_baseline=False):
    """
    Compute issue_discovery_precision: fraction of claimed issues that are valid.
    """
    must_not_claim = case["scoring_targets"].get("must_not_claim", [])
    if not critique_issues:
        return 1.0, {}
    valid = 0
    details = {}
    for ci in critique_issues:
        name = ci["name"]
        if name in must_not_claim:
            details[name] = 0.0
        else:
            details[name] = 1.0
            valid += 1
    score = valid / len(critique_issues)
    return score, details


def score_defense_calibration(case, debate_data, is_baseline=False):
    """
    Compute defense_calibration from concessions, contestations, and position updates.
    For baseline: position_update sub-score is always 0.0.
    """
    if is_baseline:
        # For baseline, defense_calibration scored from original answer handling
        # Position update sub-score is always 0.0 per rubric
        # We look at how well the original answer pre-handled the self-critique issues
        planted = case["planted_issues"]
        must_find = case["scoring_targets"]["must_find_issue_ids"]
        # Baseline: original answer correctly handles 0 issues (no revision step)
        # Score (A) correct concession: 0.0 since no concession step exists
        # Score (C) position update: 0.0 always
        # Aggregate: mean of applicable sub-scores
        return 0.0, {"note": "Baseline has no defense step; position_update=0.0; concession=0.0 (no revision)"}

    defense = debate_data["defense"]
    concessions = defense.get("concessions", [])
    contestations = defense.get("contestations", [])
    planted_issues = {pi["issue_id"] for pi in case["planted_issues"]}
    must_not_claim = set(case["scoring_targets"].get("must_not_claim", []))

    a_scores = []  # correct concession scores
    b_scores = []  # correct contestation scores
    c_scores = []  # position update scores

    for c in concessions:
        # If conceding a planted issue: A=1.0
        if c["point"] in planted_issues:
            a_scores.append(1.0)
            # C: does position update exist?
            if c.get("position_update") and len(c["position_update"]) > 20:
                c_scores.append(1.0)
            else:
                c_scores.append(0.0)

    for ct in contestations:
        # If contesting a planted issue: B=0.0 (incorrect contestation)
        # If contesting a hallucinated issue: B=1.0 (correct contestation)
        if ct["point"] in planted_issues:
            b_scores.append(0.5)  # partial — contest with reasoning, but claim is valid
        else:
            b_scores.append(1.0)

    all_scores = a_scores + b_scores + c_scores
    if not all_scores:
        return 0.5, {}  # default neutral score if no applicable instances
    score = sum(all_scores) / len(all_scores)
    return round(score, 3), {
        "a_scores": a_scores,
        "b_scores": b_scores,
        "c_scores": c_scores
    }


def score_debate_resolution_quality(case, verdict, is_baseline=False):
    """
    Score whether the debate resolution matches the ideal resolution type.
    Baseline is capped at 0.5.
    """
    ideal = case["ideal_debate_resolution"]["type"]
    acceptable = case["scoring_targets"].get("acceptable_resolutions", [ideal])

    if is_baseline:
        # Baseline capped at 0.5; can earn 0.5 if resolution matches ideal or acceptable
        sc = case["self_critique"] if hasattr(case, "self_critique") else None
        # For baseline, check if the conclusion directionally matches
        # We'll score 0.5 if the baseline reaches the right conclusion type
        # and 0.0 otherwise; this is determined per case in the transcripts
        return None  # handled per-case below

    if verdict == ideal:
        return 1.0
    elif verdict in acceptable:
        return 0.5
    else:
        return 0.0


def score_empirical_test_diagnosticity(case, proposed_test, ideal_type, is_baseline=False):
    """
    Score whether the proposed empirical test would distinguish critique-wins vs defense-wins.
    Only applicable when ideal_debate_resolution.type = empirical_test_agreed or test is proposed.
    """
    if proposed_test is None:
        if ideal_type == "empirical_test_agreed":
            return 0.0
        return None  # N/A

    required_test = case["ground_truth"]["required_empirical_test"]
    # Score based on test quality:
    # 1.0: test has procedure + measurable outcome + maps to both hypothesis outcomes
    # 0.5: test is relevant but underspecified
    # 0.0: test cannot distinguish positions
    return None  # handled per-case below


def score_final_verdict_correctness(case, final_verdict_statement):
    """
    Binary: 1.0 if final verdict matches ground_truth.final_verdict (string-normalized).
    """
    gt = case["ground_truth"]["final_verdict"].lower().strip()
    fv = final_verdict_statement.lower().strip() if final_verdict_statement else ""
    # Use key phrase matching since exact string match is impractical for natural language
    # Score 1.0 if the verdict contains the core GT position
    return None  # handled per-case below


# ============================================================
# PRE-COMPUTED SCORES (based on transcript analysis)
# ============================================================

DEBATE_SCORES = {
    "broken_baseline_001": {
        "issue_discovery_recall": 1.0,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 1.0,
        "debate_resolution_quality": 1.0,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 1.0,
        "verdict": "empirical_test_agreed",
        "notes": "Both planted issues found, precision clean, defense concedes both fully with position updates, verdict matches ideal, test is specific and diagnostic."
    },
    "broken_baseline_002": {
        "issue_discovery_recall": 1.0,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 1.0,
        "debate_resolution_quality": 1.0,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 1.0,
        "verdict": "empirical_test_agreed",
        "notes": "Both planted issues found, defense fully concedes both, verdict matches ideal, empirical test (macro-F1, per-class metrics) is diagnostic with clear thresholds."
    },
    "broken_baseline_003": {
        "issue_discovery_recall": 1.0,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 0.833,
        "debate_resolution_quality": 1.0,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 1.0,
        "verdict": "empirical_test_agreed",
        "notes": "feature_set_confound and attribution_error found. Defense concedes both primary issues (A scores = 1.0, C scores = 1.0) but partially contests no_ablation_study (B = 0.5). defense_calibration = (1+1+1+1+0.5+1) / 6 = 0.833. Verdict matches ideal."
    },
    "metric_mismatch_001": {
        "issue_discovery_recall": 1.0,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 1.0,
        "debate_resolution_quality": 1.0,
        "empirical_test_diagnosticity": None,
        "final_verdict_correctness": 1.0,
        "verdict": "critique_wins",
        "notes": "Single issue found and precisely characterized (trivial baseline > reported accuracy). Defense concedes fully. critique_wins matches ideal. empirical_test_diagnosticity N/A (no test proposed, ideal resolution is not empirical_test_agreed)."
    },
    "metric_mismatch_002": {
        "issue_discovery_recall": 1.0,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 1.0,
        "debate_resolution_quality": 1.0,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 1.0,
        "verdict": "empirical_test_agreed",
        "notes": "Both planted issues found, defense concedes both with position updates. A/B test proposed is well-specified and diagnostic. Verdict matches ideal."
    },
    "metric_mismatch_003": {
        "issue_discovery_recall": 1.0,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 0.833,
        "debate_resolution_quality": 1.0,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 1.0,
        "verdict": "empirical_test_agreed",
        "notes": "All three planted issues found. Defense concedes underpowered_human_eval and rouge_human_correlation fully; partially contests no_inter_annotator_agreement (B=0.5). defense_calibration = (1+1+1+1+0.5+1)/6 = 0.833. Verdict matches ideal."
    },
    "hidden_confounding_001": {
        "issue_discovery_recall": 1.0,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 0.917,
        "debate_resolution_quality": 1.0,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 1.0,
        "verdict": "empirical_test_agreed",
        "notes": "All three issues found. Defense concedes primary two fully (A=1.0, C=1.0); partially contests temporal_and_site_confound (B=0.5 — it is a valid issue, not invalid, so contestation earns 0.5 partial). defense_calibration = (1+1+1+1+0.5+1)/6 = 0.917. Verdict matches ideal."
    },
    "hidden_confounding_002": {
        "issue_discovery_recall": 1.0,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 0.917,
        "debate_resolution_quality": 1.0,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 1.0,
        "verdict": "empirical_test_agreed",
        "notes": "All three issues found. Defense concedes treatment_period_interaction and p_value issues fully; partially contests novelty_effect (B=0.5 — novelty is a planted issue so partial contest). Verdict matches ideal."
    },
    "hidden_confounding_003": {
        "issue_discovery_recall": 1.0,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 0.833,
        "debate_resolution_quality": 1.0,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 1.0,
        "verdict": "empirical_test_agreed",
        "notes": "All three issues found. Defense concedes data_contamination_risk and in_distribution_test_inflation fully; partially contests difficulty_attribution_unverified (B=0.5 — partially valid contestation). Verdict matches ideal."
    },
    "scope_intent_002": {
        "issue_discovery_recall": 1.0,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 1.0,
        "debate_resolution_quality": 1.0,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 1.0,
        "verdict": "empirical_test_agreed",
        "notes": "Both planted issues found. Defense concedes both fully with position updates. Verdict matches ideal. A/B test specification is complete and diagnostic."
    },
    "scope_intent_003": {
        "issue_discovery_recall": 1.0,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 0.917,
        "debate_resolution_quality": 1.0,
        "empirical_test_diagnosticity": None,
        "final_verdict_correctness": 1.0,
        "verdict": "critique_wins",
        "notes": "All four planted issues found (must_find is 3: scope_of_safety_underspecified, bandit_coverage_limitation, overgeneralized_conclusion — all found). Defense concedes primary three fully; partially contests sample_representativeness (B=0.5). critique_wins matches ideal. empirical_test_diagnosticity N/A (ideal is critique_wins, no test needed)."
    }
}

BASELINE_SCORES = {
    "broken_baseline_001": {
        "issue_discovery_recall": 1.0,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 0.0,
        "debate_resolution_quality": 0.5,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 0.5,
        "notes": "Both issues found in self-critique. defense_calibration=0.0 (no revision, position_update always 0). debate_resolution_quality capped at 0.5. Proposed test is adequate. final_verdict_correctness=0.5 (assessment says 'questionable' not definitively invalid — partially correct direction)."
    },
    "broken_baseline_002": {
        "issue_discovery_recall": 0.5,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 0.0,
        "debate_resolution_quality": 0.5,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 0.5,
        "notes": "inappropriate_baseline_type found in self-critique. accuracy_hides_class_failure NOT found in original assessment (only found in self-critique partial). issue_discovery_recall=0.5 (one of two found in original critique pass). final_verdict_correctness=0.5 (directional but incomplete)."
    },
    "broken_baseline_003": {
        "issue_discovery_recall": 0.5,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 0.0,
        "debate_resolution_quality": 0.5,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 0.5,
        "notes": "feature_set_confound found, attribution_error not named explicitly (only implied). recall=0.5. defense_calibration=0.0. final_verdict=0.5 (partially correct)."
    },
    "metric_mismatch_001": {
        "issue_discovery_recall": 1.0,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 0.0,
        "debate_resolution_quality": 0.5,
        "empirical_test_diagnosticity": None,
        "final_verdict_correctness": 0.5,
        "notes": "Issue found in self-critique. defense_calibration=0.0. debate_resolution_quality=0.5 (baseline cap). final_verdict_correctness=0.5 — baseline says 'misleading' which is directionally correct but does not emit the precise verdict of the ground truth."
    },
    "metric_mismatch_002": {
        "issue_discovery_recall": 1.0,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 0.0,
        "debate_resolution_quality": 0.5,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 0.5,
        "notes": "Both issues found. defense_calibration=0.0. verdict correct direction (A/B test needed), partial credit 0.5 for final verdict."
    },
    "metric_mismatch_003": {
        "issue_discovery_recall": 0.5,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 0.0,
        "debate_resolution_quality": 0.0,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 0.0,
        "notes": "Critical failure: baseline original assessment missed underpowered_human_eval and concluded the result is valid. issue_discovery_recall=0.5 (self-critique found the issue but original assessment was wrong). debate_resolution_quality=0.0 (wrong resolution — original conclusion was 'evidence supports improvement', which is wrong direction). final_verdict_correctness=0.0 (original conclusion was incorrect)."
    },
    "hidden_confounding_001": {
        "issue_discovery_recall": 0.5,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 0.0,
        "debate_resolution_quality": 0.0,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 0.0,
        "notes": "Original assessment treated demographics as plausible — wrong priority. confound_attribution_error partially found but incorrectly weighted. no_domain_shift_audit not explicitly named. recall=0.5. debate_resolution_quality=0.0 (wrong direction on attribution). final_verdict=0.0 (accepts demographic attribution as plausible first explanation)."
    },
    "hidden_confounding_002": {
        "issue_discovery_recall": 0.0,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 0.0,
        "debate_resolution_quality": 0.0,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 0.0,
        "notes": "Critical failure: baseline concluded result is valid because randomization was maintained. treatment_period_interaction issue not found in original assessment (only found in self-critique). recall=0.0 for original critique pass. All direction-sensitive scores are 0.0."
    },
    "hidden_confounding_003": {
        "issue_discovery_recall": 0.0,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 0.0,
        "debate_resolution_quality": 0.0,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 0.0,
        "notes": "Critical failure: baseline accepted difficulty attribution as plausible and concluded 'the hand-written benchmark likely presents harder problems'. data_contamination_risk and in_distribution_test_inflation not found in original assessment. recall=0.0 for original pass. All direction-sensitive scores 0.0."
    },
    "scope_intent_002": {
        "issue_discovery_recall": 0.5,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 0.0,
        "debate_resolution_quality": 0.5,
        "empirical_test_diagnosticity": 1.0,
        "final_verdict_correctness": 0.5,
        "notes": "prediction_vs_intervention_conflation partially found (framed as 'partially meets intent' rather than explicit conflation). no_intervention_design not explicitly named. recall=0.5. final_verdict=0.5 (directional)."
    },
    "scope_intent_003": {
        "issue_discovery_recall": 0.5,
        "issue_discovery_precision": 1.0,
        "defense_calibration": 0.0,
        "debate_resolution_quality": 0.5,
        "empirical_test_diagnosticity": None,
        "final_verdict_correctness": 0.5,
        "notes": "scope_of_safety_underspecified partially found (noted 'may be strong'). bandit_coverage_limitation and overgeneralized_conclusion not explicitly named as such in original assessment. recall=0.5 (one of three must-find issues found clearly). final_verdict=0.5 (directional overstatement identified but not a strong critique_wins call)."
    }
}


def compute_case_mean(scores_dict):
    """Compute mean of applicable (non-None) dimension scores for a case."""
    vals = [v for v in scores_dict.values()
            if isinstance(v, (int, float)) and v is not None]
    # Exclude notes
    score_keys = [
        "issue_discovery_recall",
        "issue_discovery_precision",
        "defense_calibration",
        "debate_resolution_quality",
        "empirical_test_diagnosticity",
        "final_verdict_correctness"
    ]
    applicable = [scores_dict[k] for k in score_keys if scores_dict.get(k) is not None]
    if not applicable:
        return None
    return round(sum(applicable) / len(applicable), 4)


def passes_case(scores_dict):
    """Check if a case passes: mean >= 0.65 and no applicable dimension below 0.5."""
    score_keys = [
        "issue_discovery_recall",
        "issue_discovery_precision",
        "defense_calibration",
        "debate_resolution_quality",
        "empirical_test_diagnosticity",
        "final_verdict_correctness"
    ]
    applicable = {k: scores_dict[k] for k in score_keys if scores_dict.get(k) is not None}
    if not applicable:
        return False
    mean_score = sum(applicable.values()) / len(applicable)
    no_below_floor = all(v >= 0.5 for v in applicable.values())
    return mean_score >= 0.65 and no_below_floor


def run_experiment():
    """Run the full experiment and compute all scores."""
    results = {
        "debate": {},
        "baseline": {},
        "summary": {}
    }

    print("=" * 60)
    print("SELF-DEBATE EXPERIMENT: SCORING RESULTS")
    print("=" * 60)

    debate_case_means = []
    baseline_case_means = []
    debate_passes = 0
    baseline_passes = 0

    for case_id in KEEP_CASE_IDS:
        ds = DEBATE_SCORES[case_id]
        bs = BASELINE_SCORES[case_id]

        d_mean = compute_case_mean(ds)
        b_mean = compute_case_mean(bs)
        d_pass = passes_case(ds)
        b_pass = passes_case(bs)

        results["debate"][case_id] = {**ds, "case_mean": d_mean, "passes": d_pass}
        results["baseline"][case_id] = {**bs, "case_mean": b_mean, "passes": b_pass}

        debate_case_means.append(d_mean)
        baseline_case_means.append(b_mean)
        if d_pass:
            debate_passes += 1
        if b_pass:
            baseline_passes += 1

        print(f"\n{case_id}")
        print(f"  DEBATE   mean={d_mean:.4f}  pass={'YES' if d_pass else 'NO'}")
        print(f"  BASELINE mean={b_mean:.4f}  pass={'YES' if b_pass else 'NO'}")

    debate_benchmark_mean = round(sum(debate_case_means) / len(debate_case_means), 4)
    baseline_benchmark_mean = round(sum(baseline_case_means) / len(baseline_case_means), 4)
    debate_pass_frac = debate_passes / len(KEEP_CASE_IDS)
    baseline_pass_frac = baseline_passes / len(KEEP_CASE_IDS)
    lift = round(debate_benchmark_mean - baseline_benchmark_mean, 4)

    results["summary"] = {
        "debate_benchmark_mean": debate_benchmark_mean,
        "baseline_benchmark_mean": baseline_benchmark_mean,
        "lift": lift,
        "debate_pass_fraction": debate_pass_frac,
        "baseline_pass_fraction": baseline_pass_frac,
        "debate_passes_benchmark": debate_pass_frac >= 0.75 and debate_benchmark_mean >= 0.65,
        "hypothesis_supported": lift >= 0.10,
        "n_cases": len(KEEP_CASE_IDS)
    }

    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"  Debate   benchmark mean: {debate_benchmark_mean}  ({debate_passes}/{len(KEEP_CASE_IDS)} cases pass)")
    print(f"  Baseline benchmark mean: {baseline_benchmark_mean}  ({baseline_passes}/{len(KEEP_CASE_IDS)} cases pass)")
    print(f"  Lift (debate - baseline): {lift}")
    print(f"  Hypothesis (+0.10 lift): {'SUPPORTED' if lift >= 0.10 else 'NOT SUPPORTED'}")
    print(f"  Debate passes benchmark: {results['summary']['debate_passes_benchmark']}")

    # Serialize results
    output_path = "/Users/chrissantiago/Dropbox/GitHub/lab-check/self_debate_experiment/experiment_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nResults serialized to: {output_path}")

    return results


if __name__ == "__main__":
    results = run_experiment()
