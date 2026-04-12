# Benchmark Case Task Prompts — Self-Debate Protocol v2

Each task prompt below is self-contained and is given verbatim to the Critique agent
and to the Defense agent independently. Neither agent sees the other's output.
The Judge receives task_prompt + both outputs.
The Baseline receives task_prompt only and produces a single-pass assessment.

---

## broken_baseline_001
**Category:** broken_baseline | **Difficulty:** easy | **correct_position:** critique

**TASK PROMPT:**
A team reports that their new NLP model achieves 72% accuracy on a customer support ticket
classification task, up from the baseline's 68% accuracy — a 4-point improvement. The team
evaluated the new model on a random 10% sample of the test set (approximately 1,000 examples),
while the baseline was evaluated on the full test set (approximately 10,000 examples).
No confidence intervals or standard errors are reported. The team claims the 4-point improvement
demonstrates the new model is ready for deployment.

Assess whether this improvement claim is valid.

---

## broken_baseline_002
**Category:** broken_baseline | **Difficulty:** medium | **correct_position:** mixed

**TASK PROMPT:**
A team trains a BERT-based sentiment classifier on customer reviews (60% positive, 20% negative,
20% neutral) and compares it to a majority-class baseline that always predicts "positive."
BERT achieves 78% accuracy; the baseline achieves 60% accuracy — an 18-point gap. The team
concludes that BERT substantially outperforms the baseline and that the model is suitable for
production deployment to route customer feedback.

Assess whether this improvement claim is valid.

---

## broken_baseline_003
**Category:** broken_baseline | **Difficulty:** hard | **correct_position:** critique

**TASK PROMPT:**
A team compares a new gradient-boosted tree model (using 47 features including demographic,
behavioral, and contextual signals) against a logistic regression baseline (using 12 demographic
features only). The gradient-boosted model achieves AUC 0.84 vs. the baseline's AUC 0.77
on a held-out test set. The team attributes the 0.07 AUC improvement to the superior
architectural capacity of gradient-boosted trees and recommends replacing the logistic
regression model in production.

Assess whether this improvement claim is valid.

---

## broken_baseline_004
**Category:** broken_baseline | **Difficulty:** hard | **correct_position:** critique

**TASK PROMPT:**
A computer vision team compares a fine-tuned ResNet-50 (fine-tuned for 50 epochs on 10,000
domain-specific images) against a zero-shot YOLOv5 model (applied directly without any
domain-specific training). The fine-tuned ResNet achieves mAP 0.81; YOLOv5 zero-shot
achieves mAP 0.63 — an 18-point gap. The team concludes that ResNet-50 is architecturally
superior for this domain and recommends it for production.

Assess whether this improvement claim is valid.

---

## metric_mismatch_001
**Category:** metric_mismatch | **Difficulty:** easy | **correct_position:** critique

**TASK PROMPT:**
A team trains a binary fraud detection classifier on a dataset with 98% legitimate transactions
and 2% fraudulent transactions. The model achieves 97.5% accuracy on the held-out test set.
The team's logistic regression baseline also achieves 97.5% accuracy (by predicting "legitimate"
for every transaction). The team reports no difference between the two models and suggests
the new model adds no value.

Assess whether this conclusion is valid.

---

## metric_mismatch_002
**Category:** metric_mismatch | **Difficulty:** medium | **correct_position:** mixed

**TASK PROMPT:**
A team builds a recommendation model optimized for offline NDCG@10 on a static interaction
log. The model achieves NDCG@10 = 0.42 vs. the production baseline's NDCG@10 = 0.37 — a
relative improvement of 13.5%. The team argues the NDCG improvement justifies an A/B test,
but has not yet run one. An internal reviewer argues that offline NDCG improvements do not
reliably predict online engagement lift and that the model should not be A/B tested.

Assess whether the team's position (the offline improvement justifies A/B testing) or the
reviewer's position (offline NDCG is not a reliable predictor of online lift) is more valid.

---

## metric_mismatch_003
**Category:** metric_mismatch | **Difficulty:** hard | **correct_position:** critique

**TASK PROMPT:**
A team evaluates a text summarization model using ROUGE-L and a human evaluation study
with 20 annotators rating summary quality on a 1–5 scale. The model achieves ROUGE-L 0.42
(vs. baseline 0.38) and a human quality rating of 3.8 (vs. baseline 3.4). The human study
recruited annotators via a crowdsourcing platform and gave each annotator 5 summaries to
rate. The team claims the model significantly outperforms the baseline on both automated
and human evaluation.

Assess whether this conclusion is valid.

---

## hidden_confounding_001
**Category:** hidden_confounding | **Difficulty:** medium | **correct_position:** critique

**TASK PROMPT:**
A team trains a churn prediction model on customer data from January–June and evaluates it on
July–December of the same year. The model achieves AUC 0.79 on the test set. The team
attributes this performance to the model's ability to capture meaningful behavioral signals
related to churn risk, and recommends production deployment. An internal reviewer notes that
the product underwent a major UX redesign in August that changed engagement patterns
substantially, and that the model was trained entirely on pre-redesign behavior.

Assess whether the team's attribution of model performance to meaningful behavioral signals is valid.

---

## hidden_confounding_002
**Category:** hidden_confounding | **Difficulty:** hard | **correct_position:** critique

**TASK PROMPT:**
A team runs a quasi-experiment to estimate the effect of a new loyalty program on purchase
frequency. They compare purchase frequency 90 days before vs. 90 days after program launch
for program enrollees. Enrollees show a 22% increase in purchase frequency post-launch.
The team concludes that the loyalty program caused the 22% increase. A reviewer notes that
the loyalty program launched in November, so the pre-period is August–October and the
post-period is November–January, which includes Black Friday, Cyber Monday, and the holiday
season.

Assess whether the team's causal attribution is valid.

---

## hidden_confounding_003
**Category:** hidden_confounding | **Difficulty:** medium | **correct_position:** critique

**TASK PROMPT:**
A team fine-tunes a pre-trained language model on a proprietary legal document corpus and
evaluates it on a legal clause classification task. The fine-tuned model achieves F1 0.91
vs. the base model's F1 0.74. The training, validation, and test sets were all drawn from
the same proprietary corpus using an 80/10/10 random split. The team claims the fine-tuning
substantially improves legal clause classification.

Assess whether this improvement claim is valid.

---

## hidden_confounding_004
**Category:** hidden_confounding | **Difficulty:** hard | **correct_position:** critique

**TASK PROMPT:**
A credit risk team monitors a model trained on 2021 loan applications and deployed for
scoring 2022–2023 applications. They observe a 7-point increase in model-predicted default
probability (population average) from Q1 2022 to Q4 2023, and a corresponding increase in
actual default rates. The team attributes this to "economic uncertainty" and concludes the
model is working correctly by tracking macro conditions. They recommend no model updates.

Assess whether the team's conclusion is valid.

---

## scope_intent_002
**Category:** scope_intent_misunderstanding | **Difficulty:** medium | **correct_position:** mixed

**TASK PROMPT:**
A public health team builds a machine learning model that predicts which patients are at
highest risk of missing their follow-up appointments (AUC 0.77 on held-out data). The team
concludes that deploying the model to flag high-risk patients will reduce missed appointments.
A reviewer argues that predicting non-adherence does not mean any intervention will reduce it,
and that the team is conflating prediction with causal intervention efficacy.

Assess whether the team's conclusion (deployment will reduce missed appointments) or the
reviewer's objection (prediction ≠ intervention efficacy) is more valid.

---

## scope_intent_003
**Category:** scope_intent_misunderstanding | **Difficulty:** hard | **correct_position:** critique

**TASK PROMPT:**
A team trains a content moderation model using contextual bandits. The model selects which
of 4 intervention actions to apply to borderline content (warn user, reduce distribution,
remove, escalate to human review). In a 30-day online experiment, the contextual bandit
achieves 18% lower false positive rate and 12% higher true positive rate vs. the rule-based
baseline across all moderated content categories. The team concludes the bandit model is
ready to replace the rule-based system as the primary safety mechanism across all content
verticals.

Assess whether this conclusion is valid.

---

## defense_wins_001
**Category:** defense_wins | **Difficulty:** medium | **correct_position:** defense

**TASK PROMPT:**
A team evaluates a machine translation model on the WMT22 English–German test set using
BLEU and chrF. The model achieves BLEU 32.4 and chrF 61.8. The team compares it to three
prior published systems on the same benchmark: System A (BLEU 31.1, chrF 60.2), System B
(BLEU 31.9, chrF 61.0), System C (BLEU 32.1, chrF 61.5). All comparisons are on the
identical WMT22 test set using identical tokenization and evaluation scripts. The team claims
their model sets a new state-of-the-art on this benchmark.

Assess whether this state-of-the-art claim is valid.

---

## defense_wins_002
**Category:** defense_wins | **Difficulty:** medium | **correct_position:** defense

**TASK PROMPT:**
A team trains a tree-based anomaly detection model and reports precision 0.91 and recall
0.87 at a decision threshold of 0.5 on a balanced held-out test set (50% anomalies, 50%
normal). They compare to three baselines evaluated at the same threshold on the same data:
Isolation Forest (precision 0.83, recall 0.79), One-Class SVM (precision 0.80, recall 0.75),
Local Outlier Factor (precision 0.82, recall 0.81). All models used the same features and
the same train/test split. The team claims their model substantially outperforms all baselines.

Assess whether this claim is valid.

---

## defense_wins_003
**Category:** defense_wins | **Difficulty:** easy | **correct_position:** defense

**TASK PROMPT:**
A team evaluates a tabular classification model using 5-fold stratified cross-validation
on a dataset of 8,500 examples (maintaining class proportions across folds). They report
mean AUC 0.84 ± 0.02 (standard deviation across folds). The team concludes that 5-fold
stratified cross-validation provides a reliable estimate of generalization performance for
this dataset size.

Assess whether this conclusion about the reliability of the cross-validation estimate is valid.

---

## defense_wins_004
**Category:** defense_wins | **Difficulty:** hard | **correct_position:** defense

**TASK PROMPT:**
A research team proposes a new neural architecture for time-series forecasting. They evaluate
it on 7 standard benchmarks (ETT-h1, ETT-h2, ETT-m1, ETT-m2, Exchange, Weather, ILI) and
report improvements on all 7 benchmarks vs. PatchTST, TimesNet, and DLinear using the
standard long-term forecasting protocol (input length 96, prediction horizons 96/192/336/720).
All baselines are reimplemented using the original authors' published code and hyperparameters.
The team claims their architecture achieves state-of-the-art results on the standard long-term
forecasting benchmark suite.

Assess whether this claim is valid.

---

## defense_wins_005
**Category:** defense_wins | **Difficulty:** medium | **correct_position:** defense

**TASK PROMPT:**
A team deploys a named entity recognition (NER) model to extract drug names, dosage amounts,
and administration routes from clinical notes at a single hospital system. They evaluate
the model exclusively on 500 held-out clinical notes from the same hospital system, sampled
from the same time period as training data. The team achieves F1 0.93 and reports the model
is suitable for deployment at this specific hospital system for this specific extraction task.

Assess whether the team's suitability claim is valid given the intended deployment scope.

---

## real_world_framing_001
**Category:** real_world_framing | **Difficulty:** medium | **correct_position:** critique

**TASK PROMPT:**
A healthcare AI company builds a symptom triage system that recommends one of three actions:
"schedule urgent appointment," "schedule routine appointment," or "self-care at home." The
system is validated retrospectively on 5,000 de-identified patient records: the AI's triage
recommendation agrees with the treating physician's actual triage decision 87% of the time.
The company concludes that the 87% agreement rate demonstrates clinical readiness and begins
marketing the system to hospital systems as a decision-support tool.

Assess whether the company's conclusion (87% retrospective agreement demonstrates clinical readiness) is valid.

---

## real_world_framing_002
**Category:** real_world_framing | **Difficulty:** hard | **correct_position:** critique

**TASK PROMPT:**
An e-commerce team deploys a dynamic pricing model in Q4 2023. They compare total revenue
in Q4 2023 to Q4 2022 and observe a 14% year-over-year revenue increase. During Q4 2023,
they also expanded their product catalog from 12,000 SKUs to 18,000 SKUs, adding a new
premium accessories category with average order value 2.3x higher than existing categories.
The team attributes the 14% revenue lift to the dynamic pricing model and considers the
deployment a success.

Assess whether the team's attribution of the 14% revenue lift to the dynamic pricing model is valid.

---
