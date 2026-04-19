# DEFENSE.md — Initial Defense (Cycle 1)

## Implementation Soundness Check

Before addressing individual critique points, the design was checked for configuration flaws that would silently invalidate results.

Three parameters are inherited from defaults rather than derived from corpus properties:

1. **512-token truncation** is the distilBERT/RoBERTa pre-training hard limit, not a number derived from the actual email body length distribution. If the median phishing email body is 150 tokens, this is harmless. If the corpus has a long-tail of verbose spear-phishing bodies, it matters. The design does not report this distribution.

2. **10 fine-tuning epochs** is unvalidated against convergence behavior on this corpus. No learning curve or early-stopping criterion is specified.

3. **Sender reputation cold-start imputation** is not specified. Novel sender domains receive some value — zero, mean, or a prior — and the choice affects F5's severity materially.

None of these flaws silently invalidate the primary PR-AUC comparison, but they constrain interpretation of component contributions and must be reported.

---

## Point-by-Point Defense

### F1 — DEFER (adj_sev: 8)

**Critic's claim:** The experiment conflates "text contains signal" with "transformers encode text better." The baseline has no text access, so a transformer win is consistent with multiple causal stories.

**Analysis:** This is structurally correct. The hypothesis as stated — that transformer learned text representations provide an advantage — requires a text-capable non-transformer baseline to isolate. A TF-IDF+GBM or BoW+GBM baseline receiving the same email text would break the modality-vs-encoding ambiguity. No such baseline is in the design. The within-transformer ablation (F2) does not substitute for it.

**Defense position:** DEFER. The correction is tractable: add a TF-IDF/BoW+GBM baseline with full email text access. This is a one-arm addition, not a redesign.

**Empirical test:** Add TF-IDF+GBM(text+metadata) as a third condition. If transformer PR-AUC > TF-IDF+GBM(text+metadata) > GBM(metadata-only), the encoding quality claim is supported. If TF-IDF+GBM(text+metadata) ≈ transformer, the advantage is modality access, not representation quality.

**Expected direction if valid:** The gap between transformer and baseline is partially or fully attributable to text modality access rather than representation quality. The transformer may still win, but the interpretation changes.

**Known accepted limitation:** Yes — many applied security papers compare to metadata-only baselines. The limitation is common but does not make it correct when the stated hypothesis is specifically about representation quality.

**If valid, does the primary conclusion hold:** A modified conclusion holds — "adding text access to a classifier improves phishing detection" — but the transformer-specific claim requires the additional baseline.

---

### F2 — DEFER (adj_sev: 6)

**Critic's claim:** The ablation is one-sided: metadata is removed from the transformer but text is never added to the baseline. Ablation symmetry is violated.

**Analysis:** Correct. The transformer ablation (with/without metadata) isolates metadata contribution within the transformer but says nothing about whether the baseline could recover with text access. A symmetric ablation would include: GBM(metadata-only), GBM(text+metadata), transformer(text-only), transformer(text+metadata). Only two of these four cells exist in the current design.

**Defense position:** DEFER. The fix is the same as F1 — adding the text-augmented GBM arm resolves both findings simultaneously.

**Empirical test:** Construct the full 2x2 ablation table. The crossed design resolves both the modality confound (F1) and the ablation asymmetry (F2) in one experiment.

**Expected direction if valid:** GBM(text+metadata) will likely outperform GBM(metadata-only), narrowing the apparent transformer advantage.

**Known accepted limitation:** Partially — ablation asymmetry is common in applied papers when the researcher is optimizing the focal model rather than the baseline. Not acceptable when the hypothesis is specifically about representation quality.

**If valid, does the primary conclusion hold:** Same as F1.

---

### F3 — DEFER (adj_sev: 7)

**Critic's claim:** Phishing campaigns spanning multiple quarters create data contamination. The transformer's full body text encoding provides more memorization surface than the metadata baseline.

**Analysis:** This is a genuine concern. Phishing campaigns reuse infrastructure, sender patterns, and templated body text for months. The transformer, encoding full body text, has more surface area to memorize campaign-specific signatures (exact phrasing, URL structures embedded in text) than the metadata-only baseline. The design acknowledges campaign autocorrelation for bootstrap stratification but does not treat it as contamination.

**Defense position:** DEFER. This is empirically resolvable: evaluate on a campaign-stratified test set where all emails from campaigns that appear in training are excluded, retaining only genuinely novel campaigns. If the transformer advantage persists on novel-campaign-only test cases, memorization is not driving the result.

**Empirical test:** Campaign-stratified evaluation: hold out all emails belonging to campaigns first observed in Q16 only. Compare PR-AUC on this novel-campaign subset vs. the full test set. A large drop in transformer advantage on novel campaigns would confirm memorization as a driver.

**Expected direction if valid:** Transformer advantage shrinks on novel-campaign-only evaluation, particularly for body-text-driven predictions.

**Known accepted limitation:** Yes — temporal splits are standard but imperfect defenses against campaign leakage in security ML. The limitation is domain-known.

**If valid, does the primary conclusion hold:** Partially — the transformer may still outperform on known-campaign patterns, which has operational value, but generalization to novel threats is the more important claim and would be weakened.

---

### F4 — REBUT-EVIDENCE (adj_sev: 4)

**Critic's claim:** 512-token truncation disadvantages the transformer on sophisticated spear-phishing where malicious payload is deep in the body. BM25 over full body would have an advantage incorrectly attributed to lexical vs. semantic differences.

**Rebuttal:** The causal chain requires two empirical assumptions that may not hold in this corpus:

1. That a substantial fraction of phishing emails in this dataset embed malicious payload past the 512-token boundary. Most phishing emails are short — credential harvesting lures, invoice fraud, and BEC pretexts are typically under 300 tokens. Verbose preambles are a specific spear-phishing subclass.

2. That BM25 is in the experimental design as a comparison point. It is not. The comparison is transformer vs. metadata-only GBM. The critic introduces a hypothetical BM25 baseline to argue the transformer is being disadvantaged — but that baseline does not exist in the experiment.

The relevant question is whether the 512-token cutoff biases the transformer-vs.-baseline comparison. Since the baseline has no text access at all, text truncation only affects the transformer, and only for emails longer than 512 tokens. If such emails are rare or if the malicious signals appear early in the body (as is common in most phishing types), the truncation effect is small.

**Residual concern:** The design should report the body length distribution and the fraction of emails exceeding 512 tokens. If more than 20% of the corpus is truncated, revisit.

---

### F5 — REBUT-EVIDENCE (adj_sev: 3)

**Critic's claim:** Sender reputation degrades on novel sender domains in the test quarter, systematically disadvantaging the baseline on exactly the novel threats the temporal split is designed to surface.

**Rebuttal:** The critic frames a realistic deployment property as a confound, but it is not. If novel phishing campaigns use previously unseen infrastructure — and they do, as a matter of operational security — then the baseline's inability to classify those senders is a real limitation in deployment, not an artifact of experimental design. The temporal split is precisely calibrated to surface this gap.

The transformer's ability to classify a novel-domain sender as malicious using body text and subject line, where the baseline has no reputation signal, is the claimed advantage made concrete. This is not the experiment disadvantaging the baseline unfairly — this is the experiment measuring exactly the scenario where the hypothesis predicts a transformer advantage.

The cold-start imputation strategy matters here (see implementation soundness check above), but the underlying asymmetry is a feature of the evaluation, not a bug.

**Residual concern:** The design should specify the cold-start imputation value for novel sender domains and test sensitivity to that choice. If the baseline is imputed to "benign" for unknown senders, that is a conservative imputation that if anything understates baseline performance on known domains and overstates it on novel ones (depending on the phishing base rate).

---

### F6 — DEFER (adj_sev: 4)

**Critic's claim:** The 1–7 day analyst review lag creates a label boundary effect where the hardest cases near split boundaries may be excluded, biasing toward easier classification.

**Analysis:** This is a real concern of limited magnitude. It affects only emails in the final 7 days of Q12 and Q15. Whether it matters depends on the exclusion rule: if emails without complete review labels are excluded, the hardest ambiguous cases near boundaries are dropped. If they are included with provisional labels, the bias runs the other direction.

**Defense position:** DEFER. The design should specify the handling rule and report the number of emails affected at each boundary.

**Empirical test:** Report the count of emails excluded at each split boundary and their class distribution. Compare model performance with and without the boundary-7-day exclusion zone.

**Expected direction if valid:** Both models benefit equally from boundary exclusion (since both use the same labels), so any bias in PR-AUC is shared rather than differential. The relative comparison may be less affected than the absolute PR-AUC values.

**Known accepted limitation:** Yes — temporal label lag at split boundaries is a known issue in security ML evaluation. Typically handled by a holdout buffer zone.

**If valid, does the primary conclusion hold:** Yes, if both models are affected equally. The relative advantage claim is more robust to this flaw than absolute performance claims.

---

### F7 — REBUT-EVIDENCE (adj_sev: 2)

**Critic's claim:** Domain-agnostic BERT/RoBERTa pre-training distribution mismatch with enterprise phishing language may prevent optimal convergence on security-specific tokens.

**Rebuttal:** The concern is real in principle but weak in magnitude for this use case. Fine-tuning provides 10 epochs of gradient updates on the target distribution, which is sufficient for the model to adapt token representations toward phishing-specific patterns. Security-specific tokens (DMARC strings, IP literals, file extensions) appear repeatedly in the fine-tuning corpus and will develop useful representations through exposure.

The stronger form of this concern applies to specialized domains like clinical NLP or legal text where terminology is opaque and pre-training exposure is near-zero. Enterprise phishing language — financial urgency framing, credential harvest lures, display name spoofing phrases — is abundant in pre-training data. The concern is within scope but not severe.

**Residual concern:** If a domain-adapted model (e.g., SecBERT or email-specific pre-training) is available, it would be a stronger baseline for the transformer arm. This is an improvement path, not a flaw that invalidates the current result.

---

### F8 — CONCEDE (adj_sev: 2)

**Critic's claim:** Attention weights are not feature importance scores; integrated gradients would be more appropriate for sender vs. body token attribution.

**Concession:** This is factually correct. Jain & Wallace (2019) and subsequent work established that attention weights do not reliably indicate feature importance and can be manipulated independently of model predictions. Using attention weights to attribute classification decisions to sender vs. body tokens overstates the interpretability of the analysis.

**Scope:** This concession applies to the SHAP/attention interpretability analysis only. The primary PR-AUC comparison between transformer and baseline is not affected by the choice of attribution method. The fix is straightforward — replace or supplement attention-based attribution with integrated gradients or input-perturbation methods.

---

## Overall Defense Assessment

The two FATAL findings (F1, F3) are deferred rather than rebutted because their corrections are tractable and empirically testable: adding a TF-IDF+GBM baseline arm resolves the modality confound and ablation asymmetry (F1, F2 simultaneously), while campaign-stratified evaluation resolves the memorization concern (F3). The experiment as designed can determine that combining a transformer with email text outperforms a metadata-only baseline, but cannot yet attribute that advantage to representation quality specifically — a meaningful distinction when the hypothesis explicitly claims transformer encoding is the source of the advantage. The strongest findings against the defender are F1/F2 (structural) and F3 (domain-specific contamination risk); F5 is affirmatively rebutted as the critic mischaracterizes a realistic evaluation property as a confound.
