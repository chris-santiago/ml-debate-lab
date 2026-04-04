# Benchmark Cases 005 & 006 — Full Run Log

## Protocol: v2 Isolated Defender
- Critic sees task_prompt only
- Defender sees task_prompt only (never sees Critic output)
- Judge sees Critic + Defender outputs
- Baseline sees task_prompt only, single pass

---

# CASE 1: broken_baseline_005

## CRITIC

**C1 — Preprocessing Pipeline Mismatch**

The claim: The 7-point accuracy lift reflects the new model's superior architecture or learning, not preprocessing differences.

Why it might be wrong: The production model was trained on text that was never entity-normalized. Its token vocabulary, embedding weights, and decision boundaries were fitted to raw or minimally preprocessed text. When entity normalization is applied to the test set and that normalized text is fed into the production model, the input distribution has been changed relative to what the model was trained on. Entity normalization can merge tokens, split them, or replace surface forms entirely. If the production model's learned representations rely on specific surface-form tokens that normalization deletes or rewrites, its predictions degrade — not because the model is inferior, but because it has been given out-of-distribution inputs. The measured 74% may be lower than the production model's true capability on text preprocessed consistently with its training regime. This is a train/test preprocessing mismatch: the production model was evaluated under a covariate shift the evaluation team imposed on it. The new model, trained on entity-normalized text, matches the evaluation distribution perfectly. The comparison is "model tested on its own distribution" vs. "model tested on a foreign distribution."

Evidence to resolve: Re-evaluate the production model on test data preprocessed identically to its training data (without entity normalization). If it recovers substantially above 74%, the 7-point claim is at least partially attributable to pipeline mismatch. A clean comparison requires evaluating both models on data preprocessed consistently with the production model's training regime, or a full 2x2 factorial design.

**C2 — Attribution Error: Confounded Improvement Claim**

The claim: The superiority of the new model is a property of the model itself.

Why it might be wrong: Two things changed simultaneously — the model and the preprocessing. The team cannot decompose the 7-point lift into (a) fraction attributable to entity normalization and (b) fraction attributable to model architecture/training. The improvement claim is confounded. A logistic regression trained on entity-normalized text might outperform the production model evaluated on non-normalized text. The correct attribution requires a 2x2 factorial design: {old model, new model} x {old preprocessing, new preprocessing}.

Evidence to resolve: Train a model of equivalent complexity to the production model on entity-normalized data. Compare to the new model. If the gap collapses, entity normalization — not the new model — is responsible for the lift.

**C3 — No Statistical Significance Testing**

The claim: A 7-point absolute accuracy difference on 3,000 samples is a meaningful, stable difference.

Why it might be wrong: With 8 categories and potentially imbalanced class distribution, effective sample sizes for low-frequency classes are small. The 7-point difference should be tested with a McNemar test or bootstrap confidence interval. This is subsidiary to C1 and C2 — even a significant gap is invalid if caused by preprocessing mismatch — but it is a separate necessary condition.

---

## DEFENDER (isolated — never saw Critic output)

**Pass 1 — Full Reasoning**

Concern A (preprocessing mismatch): The production model was trained and served without the custom entity normalization step. The test set was evaluated with entity normalization applied. There is a clear mismatch between the production model's training distribution and its evaluation distribution. Entity normalization is described as "custom," meaning it involves non-trivial transformations that likely alter token-level features. Depending on the production model's architecture, entity normalization may invalidate a substantial fraction of its learned representations. The production model's 74% may understate its true capability under fair evaluation conditions. This is a fundamental flaw.

Concern B (confounded attribution): Two things changed simultaneously — the model and the preprocessing. The team cannot decompose the 7-point lift into the fraction attributable to entity normalization versus model architecture. Even if the preprocessing mismatch is small, the improvement claim is unidentified.

Concern C (statistical significance): 3,000 samples over 8 categories. If some categories are rare, per-class accuracy is noisy. The headline 7-point difference should be tested.

Concern D (test set integrity): The scenario says "shared held-out test set." No evidence of leakage is present, so this is not asserted — flagged only.

**Pass 2 — Verdict**

Concern A is a critical flaw. The production model is evaluated on out-of-distribution inputs relative to its training. This alone invalidates the 7-point claim as stated. Concern B is a separate critical flaw. Concern C is real but subsidiary. Concern D is speculative.

**Verdict: The improvement claim is not valid as stated. The preprocessing mismatch is disqualifying without additional evidence. The claim could be rescued by a clean comparison study.**

---

## JUDGE

Both agents independently identified the same two core flaws without seeing each other's work:
- Preprocessing pipeline mismatch: Critic C1 = Defender Concern A. Exact agreement.
- Attribution error / confounding: Critic C2 = Defender Concern B. Exact agreement.
- Statistical significance: Both raised it as subsidiary.

No contested points.

**Empirical test specification (agreed):** Evaluate the production model on two test conditions — normalized preprocessing (as done originally) and non-normalized preprocessing (matching its training). The difference in accuracy between these two conditions for the production model isolates the preprocessing effect. A complete resolution is a 2x2 factorial: {old model, new model} x {old preprocessing, new preprocessing}. If the production model's accuracy under its native preprocessing substantially closes the gap (e.g., recovers to 78%+), the original claim is falsified as a model quality claim. If the gap persists under matched preprocessing, the new model's superiority holds.

**Final verdict: empirical_test_agreed**

---

## BASELINE (single pass, no roles)

The 7-point improvement claim is not valid as stated.

The core problem is that the production model is evaluated under a preprocessing pipeline it was never trained with. Custom entity normalization was introduced as part of the new model's development. The production model's learned representations were fitted to text without this normalization. Evaluating it on normalized text is a covariate shift applied by the evaluation team — it degrades the production model's measured performance for reasons unrelated to model quality.

The 74% figure likely understates the production model's true capability under fair evaluation conditions. The 7-point gap is partially or fully an artifact of pipeline mismatch, not model superiority. Additionally, because both the model and the preprocessing changed simultaneously, even a corrected comparison cannot isolate which factor drives the improvement without explicit controls.

**Conclusion: The comparison is broken. A 2x2 ablation is required before the improvement claim can be accepted.**

---

---

# CASE 2: broken_baseline_006

## CRITIC

**C1 — Post-Hoc Threshold Tuning on the Test Set (test-set overfitting)**

The claim: The reported precision 0.88 and recall 0.82 are generalizable performance metrics.

Why it might be wrong: The team swept 17 threshold values (0.1 to 0.9 in increments of 0.05) and selected the one that maximized F1 on the test set. This is optimization on the test set. The test set is supposed to be a held-out estimate of generalization performance. The moment any performance criterion on the test set is used to make a configuration decision, the test set is no longer a held-out estimate — it becomes a validation set. The reported metrics are biased upward because the threshold was chosen to maximize them. With 17 threshold candidates, there is a meaningful probability that the selected threshold over-fits to the noise structure of the 5,000-sample test set.

Mechanism: maximum-over-candidates bias. If you measure F1 at 17 thresholds and pick the maximum, the expected value of the maximum is higher than the true best threshold's F1 on a fresh sample. With 5,000 samples and 17 candidates, this bias is real; its magnitude depends on the sharpness of the F1 curve (0.5–5 points of inflation is plausible).

Evidence to resolve: Commit to a threshold using a held-out validation set, then evaluate at that pre-committed threshold on the test set. Comparing the F1 at the validation-selected threshold versus the F1 at the test-optimized threshold gives a direct estimate of the inflation.

**C2 — Comparison Against Baseline at Mismatched Threshold**

The claim: The comparison to the production baseline (precision 0.80, recall 0.76) is fair.

Why it might be wrong: The production baseline operates at its "deployed threshold" — not threshold-optimized. The new model's threshold was chosen to maximize F1 on the test set. The comparison gives the new model a tuning advantage the baseline did not receive. If the same threshold optimization procedure were applied to the baseline on the test set, the baseline's F1 might also increase. We do not know whether the new model's advantage is real or whether the baseline would close the gap under equivalent treatment.

Evidence to resolve: Compare both models' AUROC or PR-AUC (threshold-independent). Alternatively, apply an identical threshold selection procedure to the baseline using a validation set, then compare at matched thresholds on the test set.

**C3 — Production Readiness Claim Without Deployment-Relevant Metrics**

The claim: The model is "ready for production" based on F1-optimized precision and recall.

Why it might be wrong: Loan default prediction has asymmetric costs. False negatives (granting loans that default) and false positives (rejecting loans that would not default) have different financial costs. F1 treats them as equal. If the operational context requires a specific precision floor or recall floor, the F1-optimized threshold may not satisfy it. The team has not demonstrated that F1 optimization aligns with the business constraint.

Evidence to resolve: Specify the cost matrix or operational precision/recall constraints. Confirm the threshold meets them.

---

## DEFENDER (isolated — never saw Critic output)

**Pass 1 — Full Reasoning**

Concern A (threshold selection on test set): The scenario is explicit: threshold was swept 0.1 to 0.9 in increments of 0.05 and chosen to maximize F1 on the test set. This is the core issue. The test set served two purposes: (1) final model evaluation and (2) threshold optimization. Once the threshold is selected by optimizing on the test set, the performance estimate is no longer unbiased. The reported precision and recall correspond to the threshold that maximized F1 on this particular 5,000-sample draw. This is a fundamental evaluation error. The magnitude of the bias depends on the shape of the F1-threshold curve and the sample size, but does not disappear with 5,000 samples when 17 candidates are swept.

Concern B (comparability to baseline): The baseline operates at its deployed threshold; the new model operates at the test-optimized threshold. These are not equivalent conditions. Even a model identical to the production baseline might appear superior under this protocol.

Concern C (class imbalance amplifies C1): Loan default prediction typically has skewed class distribution — perhaps 5–20% default rate. At 10% default rate, 5,000 samples yields ~500 positives. Precision and recall estimates on 500 positives are noisy; this amplifies the optimization bias from Concern A.

Concern D (no significance testing): 8-point precision and 6-point recall improvements are not tested for significance. May or may not matter given C1.

Concern E (production readiness): Loan default prediction has asymmetric costs; F1 optimization may not align with the business constraint. The claim of "ready for production" is premature.

**Pass 2 — Verdict**

Concern A is critical and disqualifying. Concern B compounds it. Concerns C, D, E are real but subsidiary.

**Verdict: The improvement claim is not valid. Post-hoc threshold optimization on the test set invalidates the reported metrics as unbiased performance estimates. A proper evaluation protocol requires validation-set-based threshold selection followed by a single held-out test-set evaluation at the pre-committed threshold.**

---

## JUDGE

Both agents independently identified the same primary flaw:
- Post-hoc threshold tuning on test set: Critic C1 = Defender Concern A. Exact agreement on mechanism, violation, and remedy.
- Mismatched comparison to baseline: Critic C2 = Defender Concern B. Exact agreement.
- Class imbalance / noise: convergent across both agents.

No contested points.

**Empirical test specification (agreed):**
1. Using only the validation set (or a held-out split of training data), sweep threshold values and select the F1-maximizing threshold.
2. Evaluate both the new model and the baseline at those pre-committed thresholds on the test set.
3. Compare precision/recall at the validation-selected threshold to the original test-optimized figures.
If the new model's F1 at the validation-selected threshold still substantially exceeds the baseline under comparable selection procedures, the improvement claim is rescued. If the gap narrows substantially (more than 0.03–0.05 F1 points), the original claim was inflated. AUROC comparison on the same test set provides a threshold-independent sanity check.

**Final verdict: empirical_test_agreed**

---

## BASELINE (single pass, no roles)

The improvement claim is not valid as stated.

The critical error is that the team selected their decision threshold by optimizing F1 directly on the test set. A held-out test set's purpose is to provide an unbiased estimate of generalization performance. By using the test set to select among 17 threshold candidates, the team turned the test set into a validation set. The resulting precision and recall figures are biased upward.

The secondary problem: the production baseline is evaluated at its fixed deployed threshold, not a test-set-optimized threshold. The new model benefits from threshold search that the baseline did not receive. Even a model not genuinely better than the baseline might appear superior under this protocol.

**Conclusion: The evaluation is methodologically invalid due to post-hoc threshold selection on the test set. The team must select the threshold on a validation set and report test-set performance at that pre-committed threshold. AUROC comparison provides an additional threshold-independent check.**
