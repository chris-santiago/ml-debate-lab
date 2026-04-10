# v5 Benchmark Prompts

All task prompts from benchmark_cases_verified.json. No answer-key fields included.

Total cases: 110

---

## eval_scenario_606
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer vs. Tabular Baseline for 30-Day Readmission Prediction

### 1. Data and Cohort Construction

We would use retrospective EHR data from a single integrated hospital system spanning 48 months, including all inpatient discharges with complete records for diagnosis codes, procedures, medications, and lab results. To ensure that both the sequence model and the tabular baseline are trained on clinically interpretable utilization histories rather than highly fragmented records, we would restrict the cohort to index discharges for patients with at least 12 months of observable history prior to discharge. We would also restrict to patients with documented follow-up capacity (same health system) over the subsequent 30 days to minimize label missingness from outside-system care seeking.

The outcome (30-day readmission) is defined as an unplanned acute care inpatient admission within 30 calendar days of discharge. Planned readmissions (e.g., scheduled procedures, chemotherapy cycles) are excluded using procedure and admission type flags. Patients who died within 30 days are censored and excluded to avoid confounding mortality with readmission risk.

### 2. Temporal Split and Leakage Prevention

To prevent information leakage and respect temporal structure, we employ a strict chronological split:
- **Training set:** Discharges from months 1–36
- **Validation set:** Discharges from months 37–42
- **Test set:** Discharges from months 43–48

No patient appears in multiple splits. All feature engineering, vocabulary construction, and preprocessing are fit exclusively on the training set; these transformations are applied without modification to validation and test data. This ensures that model selection decisions are not influenced by future information.

### 3. Preprocessing and Feature Engineering

Preprocessing is fit on training data only and includes: (1) vocabulary construction for diagnosis, procedure, and medication codes (rare codes with <10 occurrences are grouped into an OTHER token); (2) robust scaling (quantile-based) for lab values; (3) forward-fill imputation for missing labs within 7 days of discharge, followed by median imputation by test type, with imputation flags retained as explicit features.

Two parallel feature sets are constructed:

**Sequence features (transformer input):** The prior 12-month history is extracted in full temporal order: admission/discharge timestamps and length of stay, diagnosis codes in order of documentation, procedure codes in chronological order, medication orders with start/stop dates, and lab results with values. Missing elements are represented as empty tokens. Sequences are padded or truncated to 500 events and position-encoded by timestamp.

**Tabular features (baseline input):** Aggregated summaries computed from the prior 12 months: admission and ED visit counts, unique diagnosis counts by ICD-10 chapter, active medication count at discharge, recent lab values and 6-month trends (slope), Elixhauser comorbidity index, age, sex, insurance status, discharge disposition, and admission urgency. All features use only data observed on or before discharge; no post-discharge clinical information is included.

### 4. Models and Baseline

The **transformer model** uses a BERT-style sequence encoder (or a pre-trained clinical BERT variant if available) to process the timestamped event sequence. The final [CLS] representation is passed through a 2-layer MLP (256 → 64 → 1 with sigmoid) to output a readmission probability. Training uses binary cross-entropy loss.

The **baseline** is logistic regression trained on tabular features only. This represents current operational practice: simple aggregated statistics with a standard generalized linear model. Both models receive equal tuning effort via grid search on the validation set to maximize AUROC.

### 5. Model Selection and Validation

Hyperparameter tuning is performed exclusively on the validation set (months 37–42). For the transformer: learning rate, dropout, embedding dimension, number of layers, and attention heads are varied; the configuration maximizing validation AUROC is selected. For the baseline: L2 regularization strength is tuned. The test set (months 43–48) is held out and used exactly once for final evaluation.

### 6. Evaluation Metrics

**Primary metric:** Area under the receiver operating characteristic curve (AUROC). This metric is appropriate because the stakeholder's objective is to rank-order patients by risk to allocate limited care management resources; AUROC measures discrimination across all thresholds and is insensitive to class imbalance.

**Secondary metrics:** Precision-recall AUC (for sensitivity to imbalance), calibration slope and intercept (to verify predicted probabilities reflect true risks), net benefit at clinically relevant thresholds (e.g., 20% predicted probability), and stratified AUROC by multimorbidity (Elixhauser tertiles) to test whether sequence models provide particular benefit for complex patients.

### 7. Confound Controls and Subgroup Analysis

To rule out that the transformer simply captures sequence length or documentation intensity, we compute correlations between sequence length and readmission in training data, then evaluate performance stratified by length quartile in the test set. A secondary "baseline + sequence length" model is fit to isolate whether gains are due to length encoding.

To address potential facility or coding variation, we report results stratified by admission source and facility (if multi-site data).

The hypothesis predicts larger gains for multimorbid patients; we stratify test results by Elixhauser tertiles and report AUROC in each stratum to evaluate this prediction.

### 8. Scope of Inference

This experiment establishes whether a transformer model improves discrimination over tabular features given identical data windows and preprocessing within a single health system over an 18-month test period. It does not establish causality, does not guarantee prospective performance, and does not assess operational feasibility or generalization to other systems or time horizons.

---

## eval_scenario_139
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer vs. GBT for 7-Day Pump Failure Prediction

### 1. Data and Labels

We would use 24 months of minute-level telemetry from industrial historians covering several hundred centrifugal pumps across at least 3 chemical processing plants, joined with CMMS work-order records from the same period. The first 6 months serve as a burn-in window to establish baseline operating signatures and are excluded from all splits. Labels are defined at the pump-day level: a pump-day is positive if an unplanned shutdown, corrective maintenance ticket, or component replacement occurs within the 7 calendar days following the observation timestamp. Planned maintenance events are excluded from positive labels but serve as censoring boundaries — no training sequence spans a planned overhaul, since the degradation trajectory resets. A pump-day is labeled negative only if confirmed survival for 7 subsequent days is documented; ambiguous cases with missing follow-up records are dropped. This yields an expected positive rate of 1–5%, consistent with real-world rare-event predictive maintenance.

### 2. Split Strategy

The data is divided chronologically into three non-overlapping windows: training (months 7–18), validation (months 19–21), and test (months 22–24). This temporal split is mandatory for two reasons. First, the target event has strong temporal autocorrelation — a pump exhibiting early degradation in month 10 will show worsening signals in month 11, so random splitting would allow future telemetry to appear in training. Second, failure cycles recur for the same asset, so any split that mixes time periods for the same pump creates label leakage through shared identity. Within each time window all pumps contribute observations, preserving the natural class distribution across the split boundary.

### 3. Feature Engineering and Preprocessing

Two parallel feature sets are constructed from identical 72-hour trailing windows per pump-day, ensuring information parity between models. The transformer receives raw multivariate sensor sequences at 1-minute resolution (vibration, temperature, pressure differential, flow rate, motor current) plus a sparse event track encoding maintenance events and alarm triggers as special tokens at their temporal positions. Missing readings are encoded with a learned mask token; outage gaps are explicitly flagged rather than interpolated, preserving the informative structure of missingness. The GBT receives 47 aggregated features per sensor (mean, std, min, max, rate-of-change, threshold exceedance counts, lag-1 autocorrelation) computed over the same 72-hour window, plus scalar maintenance history features. All preprocessing transformers — scalers, imputation statistics, event vocabularies — are fit on the training period only and applied without re-fitting to validation and test sets.

### 4. Models and Baseline

The proposed model is a 4-layer transformer encoder with multi-head self-attention (8 heads), learned positional embeddings, per-channel input projections, and a binary classification head. It is trained with class-weighted binary cross-entropy and AdamW with a cosine schedule. The baseline is LightGBM trained on the aggregated feature set. Both models receive 200 random search trials on validation PR-AUC for hyperparameter optimization, ensuring equal tuning effort. The GBT baseline is the correct comparison because it represents current best practice in industrial predictive maintenance and directly tests whether raw-sequence modeling adds value over well-engineered aggregations.

### 5. Evaluation Metrics

The primary metric is ROC-AUC on the held-out test set, with pump-stratified bootstrap confidence intervals (1000 resamples). ROC-AUC is appropriate here because it is threshold-independent and provides a standard measure of separability across all decision thresholds, making it convenient for comparing the transformer and GBT before selecting an operational alert threshold. Secondary metrics include precision and recall at a fixed 5% alert rate, lead time distribution for true positives, false alarm rate per pump per month, PR-AUC for reference, and calibration plots.

### 6. Model Selection and Test Set Policy

All hyperparameter decisions are made using validation PR-AUC exclusively. After the best configuration for each model is selected, each model is re-trained on the combined training + validation period (months 7–21) and evaluated once on the test set. The test set is never used for selection or tuning.

### 7. Confound Controls

Three confounds are explicitly addressed. To control for granularity advantage, both models use the same 72-hour observational window and an ablation is run with maintenance history removed from both. To control for asset identity leakage, asset IDs are excluded as features and temporal splits prevent future records from informing training. To test plant-level generalization — the most important competing explanation for any transformer advantage — PR-AUC is reported by plant and a leave-one-plant-out evaluation is conducted. This design establishes whether the transformer's sequence modeling capability, rather than data access or asset-specific memorization, drives any observed improvement.

---

## eval_scenario_18
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Temporally Windowed Session Embeddings for Conversion Prediction

### Objective
To test whether a model incorporating learned embeddings from clickstream event sequences outperforms a baseline model built from session-level aggregates in predicting 7-day purchase conversion, while controlling for temporal confounds and data leakage.

### 1. Data Collection and Labeling

We will extract 6 months of event-level clickstream logs (January through June) from the production platform, restricted to users with at least 90 days of prior activity history at the time of the session. Each row represents a single event (page view, search, add-to-cart, etc.) with timestamp, event type, session ID, user ID, device type, referral source, and dwell time. Sessions are the unit of analysis; a session is a sequence of events from one user within a contiguous time window (e.g., 30 minutes of inactivity ends a session).

This history requirement ensures that recency and prior-session features are computed on sufficiently complete user histories and reduces instability from partially observed cold-start behavior. Labels are derived by joining sessions to transaction records: a session receives label 1 if the user completed at least one purchase within 7 calendar days after the session ended; otherwise, label 0. Exclude sessions with incomplete timestamps, null IDs, or malformed sequences. Document the exclusion rate and the overall positive rate.

### 2. Train/Validation/Test Split

We employ a temporal split with user-level stratification to prevent leakage:
- **Training set:** January–March (12 weeks)
- **Validation set:** April (4 weeks)
- **Test set:** May–June (8 weeks)

Justification: Temporal ordering prevents the model from using future information, respects concept drift from seasonality and promotions, and reflects real deployment where the model is trained on historical data and evaluated on unseen future periods. 

User-level stratification is applied to minimize cross-contamination: when feasible, each user's sessions appear in only one split. If user overlap is unavoidable (common in long-running platforms), we stratify the validation and test sets by user ID and document the overlap rate. This reduces (though does not eliminate) the risk of correlated sessions leaking signal across splits.

### 3. Feature Engineering

Two feature sets are constructed:

**Baseline features (non-sequential):**
- Session event counts: total events, page views, searches, add-to-cart actions
- Recency: number of days since the user's prior session
- Device type and referral source (one-hot encoded)
- Session duration (minutes)

**Treatment features (sequential embeddings):**
- All baseline features, *plus*
- A learned embedding vector derived from the session's clickstream sequence. Events are ordered chronologically, encoded as (event_type, dwell_time, relative_timestamp), and passed through a sequence encoder (e.g., bidirectional LSTM or Transformer). The output embedding is the final hidden state or mean pooling over event representations. Sequence length is fixed (e.g., padded/truncated to 50 events).

All preprocessing transformers (scalers, encoders, sequence length parameters) are fit on the training set only and applied to validation and test sets without refitting. This prevents label leakage.

### 4. Model and Baseline

**Treatment model:** A gradient boosting classifier (XGBoost or LightGBM) or neural network (MLP or CNN) trained on baseline features + session embedding, end-to-end with the sequence encoder.

**Baseline model:** The same classifier (XGBoost or LightGBM) trained on baseline features only.

Both models receive equivalent hyperparameter tuning effort: grid or random search over learning rate, regularization, tree depth, etc., evaluated on the validation set. This ensures the comparison isolates the value of the sequence embedding, not differential tuning.

### 5. Validation and Model Selection

Hyperparameters for both models are selected to maximize AUPRC on the validation set (April). The test set (May–June) is held-out and used once, at the end, for final reporting only.

### 6. Evaluation Metrics

**Primary metric:** Area Under the Precision-Recall Curve (AUPRC). Conversion is typically imbalanced (5–15% positive rate), so AUPRC is more informative than AUROC. It directly reflects the business objective: precision quantifies wasted outreach reduction, recall quantifies purchaser capture, and their trade-off drives retargeting and intervention ROI.

**Secondary metrics:**
- AUROC (overall ranking quality)
- Lift at top-k (e.g., precision and recall when targeting the top 10% of sessions by score)
- Calibration (Brier score, expected calibration error)
- Per-user metrics (mean reciprocal rank of first positive session per user)

### 7. Confound Controls

**User-level leakage:** Addressed via temporal and stratified splits; overlap is flagged and documented.

**Campaign effects:** Perform sensitivity analysis stratifying by promotion vs. non-promotion periods (metadata flagged in raw data). If gains are concentrated in promotion periods, the model may be exploiting campaign signals rather than learning sequence behavior.

**Concept drift:** Report performance separately for early test (May) and late test (June). Large drops indicate drift; recommend retraining schedules if observed.

**Holdout population:** Set aside a small stratified holdout of users before modeling. Score both models on this population post-hoc to verify generalization.

### 8. Interpretation and Claims

The experiment will establish whether the treatment model achieves higher AUPRC on the held-out test set. It will *not* establish causality or interpretability of the learned embeddings. Any gain could come from increased model capacity; ablations (e.g., training a baseline neural network on the same architecture) are recommended to isolate the value of sequences.

---

## eval_scenario_649
**Category:** critique | **Difficulty:** hard | **Correct position:** critique_wins

## Experiment Design: Sequence Models for Early Dropout Detection in Online Learning

### 1. Data and Label Definition

This experiment uses 24 months of event-log data from the learning platform, spanning all learners enrolled across multiple course offerings. Each event is timestamped and includes type (course view, video progress, quiz attempt, forum post, assignment submission), duration when applicable, and course context.

The label is derived as follows: for each learner at a prediction point on day T, we observe their interaction history up to and including day T. The outcome is measured in the window days T+1 through T+8 (the following week). A learner is labeled dropout=1 if no interaction occurs during this 7-day window; otherwise, dropout=0. This definition aligns with the stakeholder's operational need to identify learners who will disengage within one week, triggering early intervention.

### 2. Temporal Train–Validation–Test Split

Data is split chronologically to prevent information leakage and to test generalization to a future cohort:
- **Training set (months 1–12, days 1–365):** Used to fit all feature preprocessing transformers, train the sequence model, and train the baseline.
- **Validation set (months 13–18, days 366–545):** Used for hyperparameter tuning via grid search and model selection (choosing configurations that maximize F1 score).
- **Test set (months 19–24, days 546–730):** Held out completely; used only once, at the end, for final evaluation.

Within each temporal split, we further stratify by course offering to ensure each split contains learners from multiple courses in similar proportions. This stratification mitigates course-specific effects and ensures the model is not overfitting to a particular course's structure.

The temporal split is the correct choice because: (1) it respects causality — predictions use only information available at the time of prediction; (2) it prevents the model from learning future patterns; (3) it tests performance on a truly held-out future cohort, matching the deployment scenario where the model must generalize to learners not in the training data.

### 3. Feature Engineering

**Sequence features (for the proposed model):**
For each 7-day window ending on day T, we extract the entire sequence of interaction events in chronological order. Each event is represented as a tuple: (event_type, duration, time_since_last_event, course_id). Event types are embedded (16–256 dimensions, tuned). The sequence is padded or truncated to a fixed length of 50 timesteps. Sequences shorter than 50 events are zero-padded; longer sequences are truncated to the 50 most recent events (recency bias is appropriate for predicting imminent dropout). 

**Aggregated features (for the baseline):**
Within the same 7-day window, we compute: total number of events by type (views, submissions, quiz attempts, forum posts), total hours spent, number of distinct assignments accessed, number of days with at least one event, mean time between events, hours since the last event, course ID, and learner tenure (days since enrollment). These features discard ordering information, testing whether sequence is necessary.

**Preprocessing:**
All transformers (scalers, encoders, imputation rules) are fit on the training set only and applied deterministically to validation and test sets without refitting. Missing values in engineered features are forward-filled within a learner's trajectory up to 14 days; beyond that, a 'no activity' indicator is set. Categorical features are one-hot encoded using the training set vocabulary; rare categories are collapsed into 'other' before test application. 

Critically, no feature incorporates information from the label window (T+1 through T+8); the cutoff is strict.

### 4. Models and Baseline

**Proposed model (bidirectional LSTM):**
Input: variable-length event sequences (padded to 50 timesteps).
Architecture: embedding layer for event types → bidirectional LSTM (128 units, 2 layers) → dense layer (64 units, ReLU) → sigmoid output.
Training: binary cross-entropy loss with class weights (weight proportional to class imbalance) to account for dropout imbalance. Hyperparameters (embedding dimension, LSTM dropout, learning rate, batch size) are tuned on the validation set.

**Baseline (logistic regression on aggregated features):**
Input: the same aggregated weekly features (no sequence ordering).
The baseline is trained using the same temporal split, the same label definition, and equivalent tuning effort (grid search over 10 regularization values, same validation monitoring). Both models use the same data preprocessing pipeline. This ensures the comparison is fair: the only difference is sequence vs. aggregation, isolating the hypothesis.

### 5. Evaluation Metrics

**Primary metric: AUC-ROC.**
This metric is appropriate because dropout prevalence may vary across months and course offerings, and the experiment needs a performance measure that remains comparable under those shifts while still reflecting how well the model separates at-risk from active learners across the full score range. Using AUC-ROC as the main criterion also supports course-level and tenure-level comparisons without tying conclusions to a single operating threshold that may be unstable across cohorts. A single intervention threshold will still be set on the validation set to satisfy the operational recall target, then applied to the test set without adjustment.

**Secondary metrics:**
- Precision at the validation-selected operating threshold.
- Recall at the validation-selected operating threshold, with a target of at least 0.70.
- F1 score (harmonic mean; used for model selection on validation set).
- Expected calibration error (ECE; checks whether predicted probabilities match observed dropout rates in each probability bin).
- Precision and recall stratified by course offering, to detect course-specific effects.
- Precision and recall stratified by learner tenure quartile, to detect tenure-based confounds.

### 6. Model Selection and Validation

Hyperparameter tuning is performed on the validation set (months 13–18) using grid search. For the LSTM, we search over 10 values of dropout, 5 values of embedding dimension, 5 learning rates, and 3 batch sizes (total ~750 configurations, trained for up to 50 epochs each with early stopping). For logistic regression, we search over 10 regularization values. In both cases, the configuration maximizing F1 score on the validation set is selected.

The test set is not touched during this process. Once a final model and baseline are selected, they are evaluated on the test set exactly once, with metrics computed without further tuning or threshold adjustment.

### 7. Controls for Confounds

**Course-specific effects:** Course schedules, assignment deadlines, and content depth vary widely. A sequence model could exploit deadline patterns rather than learning general dropout signals. We control for this by: (1) stratifying train/val/test by course; (2) computing precision and recall separately per course in secondary analyses; (3) reporting performance on courses with early vs. late deadlines to test robustness. A large variance in precision across courses (>15%) would suggest the model is exploiting course structure.

**Temporal and seasonal trends:** Dropout propensities may shift over time due to platform changes, seasonal cohort differences, or course content evolution. We control by: (1) using a temporal split (test set is temporally held out); (2) computing base rates (dropout prevalence) by month and flagging if test base rate differs significantly from training (Chi-squared test); (3) reporting the primary metric, AUC-ROC, which is less sensitive to threshold choice under base-rate variation.

**Learner tenure confound:** Experienced learners may have lower intrinsic dropout risk and more stable interaction patterns. We control by stratifying secondary metrics by tenure quartile. If the sequence model shows much higher precision in the highest tenure quartile, this suggests it is primarily detecting tenure, not risk.

**Class imbalance:** We use class-weighted training loss and report metrics separately for both classes to ensure the model does not sacrifice minority-class (dropout) recall for overall accuracy.

### 8. Scope and Claims

This design will establish whether a sequence model trained on interaction event order predicts next-week dropout better than a static aggregated baseline on a future cohort of learners. It will not establish that the sequence model is optimal across all possible baselines, nor will it prove causation (no interventions are tested). The experiment is scoped to one platform and one prediction horizon (next week); generalization to other platforms or longer-term prediction horizons is out of scope.

---

## eval_scenario_3
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

# Experiment Design: Transformer vs. Logistic Regression for 30-Day Readmission Prediction

## 1. Data Strategy

The experiment uses a retrospective cohort of adult inpatient discharges from a single integrated delivery network over 36 months. The index event is discharge from a general medicine service; the outcome is any unplanned hospital readmission within 30 days, fully observed by day 31. The dataset includes encounter-level EHR data (demographics, diagnoses, procedures, labs, vitals) spanning 24 months prior to each discharge, plus outpatient pharmacy fill records for the same lookback window.

Known data quality issues are addressed as follows: missing lab values and vital signs are flagged during preprocessing and handled via imputation (fit on training data only); medication fills are right-censored at the health system boundary, meaning fills at outside pharmacies are unobserved. This missingness is deliberate and realistic; the experiment stratifies results by pharmacy data completeness to ensure the model's benefit does not rest entirely on implicit handling of missing data.

## 2. Split Strategy

A **temporal (chronological) split** is used to prevent leakage and preserve the causal structure of the data. Discharges are ordered by date and divided as follows:
- **Training set (months 1–24):** 70% of the time window; all discharges and their associated histories
- **Validation set (months 25–30):** 15% of the time window; used for hyperparameter selection
- **Test set (months 31–36):** 15% of the time window; held out until final evaluation

Justification: Longitudinal EHR sequences exhibit strong temporal autocorrelation and seasonality. A random split would allow the model to learn patterns from month 35 when training on month 5 discharges, introducing leakage. Conversely, a chronological split ensures that all temporal patterns in the training set temporally precede those in validation and test, mimicking the deployment scenario where predictions are made at discharge using only historical information. A 1-month burn-in buffer between train and validation, and another between validation and test, reduces contamination from overlapping patient cohorts and allows pharmacy claims to settle.

## 3. Preprocessing and Feature Engineering

All preprocessing transformers (scaling, imputation, encoding) are **fit on the training set only** using information available at or before each patient's discharge date. They are then applied identically to validation and test sets without refitting. This prevents indirect leakage of label information and future missingness patterns into validation and test.

Features are organized in three groups:
1. **Longitudinal EHR sequence:** All encounters in the 24 months prior to discharge (visits, labs, procedures, vitals), encoded as timestamped event sequences with learned embeddings and absolute positional encodings.
2. **Medication fill history:** All outpatient fills in the prior 24 months, encoded as a timestamped sequence.
3. **Structured pre-discharge features:** Demographics (age, sex, insurance), Charlson comorbidity index, admission and ED visit counts (prior 12 months), length of stay, discharge disposition, primary diagnosis category, and constructed features (time since last admission, medication count in prior 90 days, high-risk medication class indicators).

No feature uses post-discharge information (e.g., post-discharge fills or readmission dates are held out by design).

## 4. Models and Baseline

**Transformer Model:** A dual-encoder architecture with separate transformer encoders for the EHR sequence and medication sequence. Each encoder uses multi-head self-attention (8 heads, 2 transformer layers, 256 hidden dimensions) with residual connections and layer normalization. The concatenated representations pass through a 2-layer MLP (256 → 128 → 1) with ReLU, dropout (0.2), and binary cross-entropy loss. The model is trained end-to-end.

**Baseline:** Logistic regression trained on structured features only (demographics, Charlson index, prior admission/ED counts, LOS, discharge disposition, primary diagnosis). The baseline receives **equivalent tuning effort**: hyperparameter search for L2 regularization strength via grid search on the validation set, class-weight balancing, and identical train/val/test splits. This ensures the comparison isolates the value of sequence modeling, not tuning disparity.

## 5. Evaluation Metrics

**Primary metric:** Area under the ROC curve (AUROC). The experiment's core question is whether the transformer produces better patient-level risk ordering than a structured linear model across the full discharged population, independent of any one outreach-capacity assumption. AUROC evaluates pairwise ranking quality over all possible thresholds and is less sensitive to month-to-month variation in readmission prevalence, which is important under temporal holdout.

**Secondary metrics:**
- AUPRC
- Sensitivity and specificity at clinically relevant thresholds (e.g., threshold targeting 25% outreach)
- Calibration slope and intercept (validation set)
- Decision curve analysis (net benefit vs. baseline and treat-all strategies)
- Performance stratified by pharmacy data completeness (to validate that the transformer's benefit is not driven solely by implicit imputation of missing fills)

## 6. Validation and Model Selection

Hyperparameters for both transformer and baseline are tuned via grid search on the validation set (months 25–30), selecting the model that maximizes AUROC on validation predictions. The validation set is used once for this purpose. After tuning is complete, the test set (months 31–36) is held out and touched only once: all reported metrics are computed on test set predictions with no further retraining or threshold adjustment.

## 7. Controls for Confounds

**Temporal leakage:** Prevented by chronological split; future admission trends and seasonality cannot influence training data.

**Differential missingness in pharmacy data:** The experiment stratifies test results by whether pharmacy data is available vs. missing/censored. If the transformer's advantage is entirely in the missing-data group, this indicates that the benefit may be due to implicit handling of missingness rather than sequence modeling, qualifying the claim.

**History vs. architecture:** The baseline receives all available structured features from the 24-month lookback window, not just the latest visit. The transformer's marginal gain over this history-aware baseline isolates the value of sequence encoding.

**Reproducibility and bias prevention:** Random seeds are fixed; all code is version-controlled; the experiment design is registered prior to execution to prevent p-hacking.

**Scope:** The experiment establishes predictive discrimination in this health system's population during the test period. It does not establish generalization to other systems, other populations, or prospective clinical deployment. Impact on actual readmission rates is a separate RCT question.

---

## eval_scenario_691
**Category:** critique | **Difficulty:** hard | **Correct position:** critique_wins

## Experiment Design: Temporal GNN for Next-Day Parcel Delivery Delay Prediction

### 1. Data and Labeling Strategy

We use 24 months of production scan-level event logs from the carrier's network, spanning all shipments processed during this period. The raw data includes per-package scan events (timestamp, location, scan type), vehicle assignments, route sequences, planned delivery dates, and actual delivery timestamps. The label is binary: a package is marked as at delay risk if it remains undelivered by 10:00 AM local time on the promised delivery date or has already accumulated an exceptional in-transit delay flag by that point. This definition aligns the prediction target with the point in the workflow where interventions are still feasible, rather than waiting until the end of the delivery day when remediation options are limited. We expect prevalence to range from 2–8% depending on region and season, reflecting operational reality.

### 2. Train-Validation-Test Split

To prevent leakage from future network conditions and seasonal patterns, we use a strict chronological split:
- **Training:** Months 1–12 (12 months of history)
- **Validation:** Months 13–15 (3 months, used for hyperparameter tuning and model selection)
- **Test:** Months 16–18 (3 months, held-out and untouched until final evaluation)

Within each split, we stratify by region (major geographic zones) to ensure consistent label prevalence and enable per-region performance evaluation. This split respects causality: we predict future delays using only information available before the prediction date.

### 3. Feature Engineering

We engineer two feature groups:

**For the GNN model:** Temporal graph structure is constructed from scan events, with hubs and delivery stops as nodes and timestamped scans as directed edges. Edge attributes include time-deltas between scans, scan type, and location metadata. Node attributes capture hub-level context (historical delay rate, throughput, staffing if available) and route-level features (planned stop order, inter-stop distances and time windows). Sequence features encode the planned route structure.

**For both models (shared baseline features):** Aggregate per-shipment features include origin region, destination region, weight, service tier, promised delivery date, day-of-week, distance, historical delay rate for the OD pair, rolling hub delay rate, vehicle load, and recency of last scan. Regional and temporal context (month, seasonality indicator, holiday proximity, regional weather) is included for both.

All preprocessing (scaling, encoding, imputation) is fit exclusively on the training set and applied identically to validation and test. Temporal aggregates (e.g., rolling hub delay rates) are computed with a cutoff at each split boundary to prevent look-ahead bias.

### 4. Models and Baseline

**GNN Model:** A message-passing temporal graph neural network that consumes the directed acyclic graph of scan events for each package. The architecture includes recurrent edge encoding to capture temporal dependencies, node embeddings aggregating hub and route context, and a task-specific readout layer. The model is trained end-to-end with binary cross-entropy loss and early stopping on validation AUC.

**Baseline:** A gradient-boosted tree (XGBoost or LightGBM) trained on the same aggregate feature set. Critically, the baseline receives the same regional and temporal features (hub identity, route, time-of-year), so it can exploit location and calendar patterns. This ensures that if the GNN wins, the gain reflects temporal sequence reasoning, not merely richer location exposure. Both models receive equivalent hyperparameter tuning effort via grid or random search on the validation set.

### 5. Model Selection and Validation

Both the GNN and baseline are trained on the full training set (months 1–12). Hyperparameter tuning is performed on the validation set (months 13–15) using AUC as the selection criterion. The best configuration for each model is locked in before test set evaluation. The test set is held-out and untouched throughout training and tuning.

### 6. Evaluation Metrics

**Primary metric:** Area Under the Receiver Operating Characteristic Curve (AUC-ROC) on the test set. AUC is chosen because (1) delay is rare (2–8%), so accuracy is uninformative; (2) operations require ranking packages by risk to decide on interventions, and AUC measures this ranking ability across all thresholds; (3) AUC is threshold-agnostic, enabling post-hoc selection of operational thresholds (e.g., 90% sensitivity) without retraining.

**Secondary metrics:** Precision–Recall AUC (more sensitive to rare events), sensitivity at fixed specificity (operational utility), per-region AUC (generalization), and calibration error (whether predicted probabilities align with true frequencies).

### 7. Controls and Confounds

The baseline receives regional and temporal features, so any GNN advantage is not attributable to seeing hub identity or calendar patterns. Stratified evaluation by region validates generalization. A temporal stability check reports AUC separately for each month in the test set to confirm the gain is consistent across time. The experiment establishes whether the graph model outperforms tabular baselines and whether gains come from temporal sequence structure in scan events. It does not establish causal mechanistic insights or fine-grained feature importance.

---

## eval_scenario_275
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

# Experiment Design: Vision Transformer vs. CNN for Wafer-Map Defect Detection

## Objective
Test whether a vision transformer pretrained on generic industrial defect images and fine-tuned on wafer-map images detects critical defect patterns with higher recall at a fixed false-positive rate than a CNN trained from scratch, controlling for data leakage, label noise, and confounding metadata effects.

## 1. Data Collection and Labeling
Source historical wafer-map images from the fab's inline optical inspection tools spanning 18–24 months of production. Each image is paired with a ground-truth label (critical defect / normal) assigned by process engineers via downstream failure analysis conducted 2–4 weeks post-inspection. Retain metadata: timestamp, tool ID, product family, and lot ID. Acknowledge that labels contain post-hoc assignment noise but do not attempt to correct it; both models train on identical noisy labels.

## 2. Train-Validation-Test Split Strategy
Apply a **lot-level split stratified by product family, tool ID, and defect prevalence** so that the train, validation, and test partitions reflect the same operating mix while still preventing direct leakage across lots.

- **Training set:** Approximately 70% of lots. All wafers from selected lots are used for model training.
- **Validation set:** Approximately 15% of lots. Only wafers from lots that do not appear in the training set are included.
- **Test set:** Approximately 15% of lots. Held out completely. Only wafers from lots not in training or validation are included.

The split is constructed at the lot level to ensure that no wafers from the same lot appear in multiple partitions. Stratification preserves the distribution of product variants, tool mix, and defect prevalence across the three splits. This reduces comparison noise caused by month-to-month composition changes and ensures both ViT and CNN are evaluated under matched operating conditions rather than idiosyncratic production-window differences.

## 3. Preprocessing and Feature Engineering
No manual feature engineering is performed. Wafer-map images are used directly. Fit all preprocessing transformers (image normalization: channel-wise mean and standard deviation; any data augmentation policies) on the training set only. Freeze these parameters and apply them identically to validation and test splits. Do not use metadata (tool ID, product family, lot date) as concatenated features or auxiliary inputs; both models must rely solely on visual patterns. This ensures the hypothesis tests pure visual-pattern recognition, not confounding metadata correlations.

## 4. Model and Baseline Setup
**Model:** Vision Transformer (ViT) pretrained on a large generic industrial defect image corpus (e.g., MVTec AD, cross-fab benchmark, or proprietary industrial defect dataset), then fine-tuned end-to-end on the training split with all layers unfrozen.

**Baseline:** ResNet-50 or EfficientNet-B4 trained from scratch on the same training split. Critically, the CNN receives no pretraining; this is the architectural and data-regime difference being tested.

**Parity:** Both models are trained with identical preprocessing, identical class-weighted cross-entropy loss (to handle imbalance during training), and identical data augmentation. Both receive equal hyperparameter tuning effort on the validation split.

## 5. Model Selection and Tuning
Use the validation split to perform hyperparameter search for both models. For each candidate hyperparameter set (learning rate, optimizer, weight decay, batch size, early stopping patience), compute the primary metric (recall at the operational false-positive rate) on the validation set. Select the hyperparameter configuration that maximizes validation recall at the fixed FPR. Do not touch the test set during this phase.

## 6. Evaluation Metrics
**Primary metric:** Recall at a fixed false-positive rate (e.g., FPR = 0.05 or 0.10, set based on fab throughput constraints). This directly reflects the operational objective: catch critical defects early while keeping false-alarm burden acceptable. Recall is the natural choice because missed defects are far more costly than reviews.

**Secondary metrics:**
- Area under the Precision-Recall curve (AUPRC): insensitive to class imbalance and dominant true negatives.
- Specificity at fixed recall (e.g., specificity at recall = 0.90): reports the cost trade-off.
- Calibration: expected calibration error (ECE) or Brier score, to ensure probability predictions are trustworthy.
- Per-product-family recall and FPR: confirms generalization across product variants.

## 7. Final Evaluation
Evaluate both models exactly once on the held-out test set without any model selection, threshold tuning, or post-hoc adjustment. Report primary and secondary metrics. Compare recall at the fixed FPR between ViT and CNN. Report confidence intervals or bootstrap-estimated uncertainty where appropriate, especially given potential label noise.

## 8. Controls and Confound Mitigation
To isolate the effect of pretraining and architecture:
- Both models use identical data, preprocessing, augmentation, and loss weighting.
- Metadata is not used as features, preventing either model from exploiting tool-specific or temporal drift patterns.
- Lot-level partitioning ensures test lots are independent of training and validation lots.
- Stratified splits ensure imbalance, tool mix, or product-specific effects do not confound the comparison.
- Any observed ViT advantage is attributable to pretraining and architectural inductive bias, not to confounding metadata or leaked lot-level patterns.

---

## eval_scenario_295
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Longitudinal EHR Sequences for Readmission Prediction

### 1. Data Strategy

The experiment uses 2–5 years of inpatient discharge records from a multi-site health system EHR warehouse. The population is adult discharges (age ≥18) with complete electronic follow-up data for 30 days post-discharge. Data includes demographics (age, sex, insurance), diagnoses (ICD-10 codes from current and all prior admissions in the lookback window), procedures, medications (orders and administrations), lab results (with timestamps and values), vital signs, encounter-level summaries (LOS, admission source, disposition), and deterministic indicators for readmission status.

The label is binary: unplanned readmission within 30 calendar days of discharge. Unplanned admissions are identified via admission type field or validated against elective procedure schedules. Planned readmissions, patients discharged against medical advice, and inpatient deaths are excluded. This label definition aligns with hospital operations and quality metrics (e.g., CMS readmission penalties).

Expected data quality issues include missing lab values (imputed with domain-specific strategies: critical labs forward-filled, optional labs marked as missing), inconsistent diagnosis coding across sites (mitigated by aggregating to Elixhauser comorbidity categories), and censoring of follow-up data at the observation window boundary (only admissions with complete 30-day follow-up are eligible as index cases).

### 2. Split Strategy: Temporal (Chronological)

A temporal split is mandatory here because readmission is a future event, and the hypothesis emphasizes longitudinal trends. The observation window (months 1–36 or end of data) is divided into three non-overlapping periods:

- **Train (months 1–24):** All eligible discharges in this window become training index cases. All upstream encounter history and lab data is used as features.
- **Validation (months 25–30):** Discharges in this window serve as validation index cases. Features are computed using historical data within each patient's lookback window, but preprocessing parameters (scalers, encoders, imputation) are fit only on training data and applied here.
- **Test (months 31–36 or to end of data):** Final held-out evaluation set. Represents future admissions.

This split prevents information leakage: no training data comes after any validation or test index discharge, and sequence models cannot exploit future utilization patterns. It reflects the deployment setting—the model will be applied to new discharges and will not have access to readmission outcomes at inference time. If the health system operates multiple sites, the test set is stratified by site to ensure representativeness.

### 3. Feature Engineering

**Static baseline features** (for the logistic regression baseline): age at admission, sex, insurance category, Elixhauser comorbidity count and indicators (CHF, COPD, diabetes, renal disease, MI), admission source, discharge disposition (home, SNF, rehab), primary service line, length of stay (hours), count of admissions in prior 6 months, count of admissions in prior 12 months, prior ER visit count. Continuous variables are standardized (zero mean, unit variance fit on training set).

**Longitudinal sequence features** (for the sequence model): For each index discharge, construct a sequence of the patient's last 12 months of encounters (limited to ~20 encounters to manage sequence length). Each encounter is encoded as a vector containing: admission and discharge dates, LOS, service line (one-hot), admission source, disposition, primary and count of secondary diagnoses (concatenated ICD-10 codes or Elixhauser category embeddings), medication orders (aggregated to ATC level 3, one-hot or frequency embedding), lab tests ordered, and admission/discharge vitals (heart rate, blood pressure, temperature). For labs, extract the most recent value of key analytes (creatinine, hemoglobin, glucose, sodium) before discharge, standardized to training-set mean and standard deviation. Encounter sequences are zero-padded to a fixed length. All encodings and scaling are fit on the training set only.

### 4. Model and Baseline

**Sequence model:** A recurrent neural network (LSTM or GRU) with attention, or a Transformer encoder. The architecture includes: (1) embedding layer (encodes categorical diagnoses and medications as dense vectors, fit on training data); (2) two to three LSTM/Transformer layers (128–256 hidden units); (3) attention mechanism to weight encounters by relevance; (4) final dense layer with sigmoid output. Class weighting inversely proportional to prevalence is applied during training to address the imbalanced label. Dropout and L2 regularization are applied to prevent overfitting.

**Baseline:** Logistic regression trained on the static feature set. This baseline represents current clinical practice—risk scores based on demographics, comorbidities, and last-encounter information. The baseline receives equal tuning effort: hyperparameter search (L2 regularization strength) is conducted on the validation set using the same metric (AUPRC). Both models are trained on the training set and selected based on validation performance.

This comparison isolates the value of longitudinal sequence information (encounter history, trends) versus static snapshot features.

### 5. Evaluation Metrics

**Primary metric:** Area Under the Precision-Recall Curve (AUPRC) on the test set. AUPRC is chosen because readmission is a relatively low-base-rate outcome, and the operational use case is targeted intervention rather than uniform treatment across all discharges. Case management teams will act on a limited high-risk subset, so the key question is whether the model concentrates true readmissions near the top of the score distribution, where follow-up resources are deployed.

**Secondary metrics:** 
- AUROC to quantify overall discrimination across the full score range.
- Calibration plots and Brier score to ensure predicted probabilities align with observed rates.
- Sensitivity and specificity at clinically relevant thresholds (e.g., threshold for flagging top 20% as high-risk).
- Stratified performance by service line, discharge disposition, and prior admission count to detect subgroup effects and ensure improvements are not driven by confounding.

### 6. Validation and Model Selection

Hyperparameters are tuned on the validation set (months 25–30) using AUPRC as the criterion. A grid search explores hidden units, dropout, learning rate, and class weight parameters. The configuration achieving the highest validation AUPRC is locked. The test set is evaluated once, after all modeling decisions are finalized. No test-set data is used during development.

### 7. Controlling for Confounds

The sequence model's gains could stem from legitimate longitudinal risk signals or from exploiting recency bias and unmeasured confounding. Four controls are implemented:

1. **Stratified analysis:** Metrics are reported separately for service lines, discharge dispositions, and subgroups defined by prior admission count and LOS. If gains concentrate in a single stratum, this suggests confounding rather than generalizable signal.

2. **Feature importance inspection:** SHAP or permutation importance is used to examine whether predictions are driven by recent admission intensity (a confounder) or by earlier longitudinal trends (a signal of true risk).

3. **Sensitivity analysis on matched cohorts:** A secondary analysis matches patients on LOS, prior admission count, and service line, then compares sequence model versus logistic regression performance within matched strata. Persistent improvement after matching would strengthen the causal interpretation.

4. **Scope statement:** The experiment tests whether the sequence model discriminates better on the test set, not whether it is causal or clinically effective. Clinical utility would require prospective validation with intervention.

**Expected outcome:** The hypothesis is supported if the sequence model achieves a meaningful improvement in test AUPRC over the static baseline, with consistent gains across key strata and without evidence of recency bias in feature importance.

---

## eval_scenario_656
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer vs. TF-IDF for Support Ticket Routing

### 1. Data and Labeling

The experiment uses 36 months of historical support tickets from the production SaaS environment. The dataset is extracted from the ticketing database and includes ticket subject, body, customer account metadata (tenure, tier, region, prior ticket history), the queue label assigned by a human agent, timestamp, and language tag. We expect at least 50,000 labeled tickets, with representation across all queue categories and primary languages. 

Labels are validated before inclusion: (1) agents' queue assignments are cross-checked against routing policies in effect at the ticket's timestamp to ensure policy compliance, (2) tickets reassigned within 2 hours are excluded (likely agent error), and (3) a random 5% sample is manually audited to estimate background label noise. Any ticket with ambiguous or policy-violating labels is removed. This quality assurance step ensures the ground truth is reliable.

### 2. Temporal Stratified Split

The dataset is divided chronologically into three contiguous windows:
- **Training:** months 1–24 (60% of data)
- **Validation:** months 25–30 (20%)
- **Test:** months 31–36 (20%)

This temporal split is essential. Support routing policies, product surfaces, and team structures evolve over time. A random split would allow the model to exploit correlations between historical and future ticket distributions, inflating generalization estimates and violating the assumption that test data represents deployment conditions. The chronological split prevents this leakage: the model trains only on historical patterns and is evaluated on tickets from a genuinely future time window, reflecting the real deployment scenario.

Within each temporal window, we stratify by queue category and primary language to preserve class balance representation. This ensures rare queues and non-English languages are proportionally represented in train, val, and test.

### 3. Feature Engineering

Features are organized into three groups:

**Ticket text:** Subject and body are concatenated. For the transformer model, the concatenated text is tokenized and fed to a pretrained multilingual transformer (e.g., mBERT or XLM-RoBERTa), which outputs contextual embeddings. For the TF-IDF baseline, subject and body are vectorized separately with TF-IDF (5000 max features, minimum document frequency 5), then concatenated.

**Customer context:** Customer account age (days), support tier (categorical, one-hot encoded), region, ticket count in past 30/90/365 days, prior resolution time percentile, and prior queue distribution. These features are standardized before concatenation with text embeddings.

**Language and metadata:** Primary ticket language (one-hot), log-transformed ticket length, and hour-of-day. No derived features encoding the label or future information are included.

All preprocessing components that define a shared feature space across time windows (tokenizers, vocabulary builders, scalers, imputation rules) are established once before model training so that train, validation, and test are represented in the same stable input space. The fitted preprocessing parameters are then frozen and applied identically throughout model development and final evaluation. This is particularly important for low-frequency language variants and sparse metadata categories, where window-specific preprocessing could otherwise introduce unnecessary variance into the comparison.

### 4. Models and Baseline

**Proposed model:** A fine-tuned multilingual transformer initialized from a pretrained checkpoint. Transformer text embeddings (768 dimensions) are concatenated with customer context and language features (~50 dimensions). The combined vector passes through a 2-layer MLP (256, 128 hidden units, ReLU, dropout 0.2) and a softmax output over queue classes. Class weights are set inversely proportional to training set class frequencies to account for imbalance.

**Baseline:** Logistic regression with TF-IDF text features and customer context features (standardized identically). Regularization is L2; class weights are set to 'balanced'. Both models receive the same hyperparameter tuning effort: grid search over regularization strength (C ∈ [0.01, 0.1, 1, 10, 100]), TF-IDF parameters (min_df, max_df), and class weight multipliers, all optimized on the validation set. This ensures a fair comparison.

### 5. Evaluation Metrics

**Primary metric:** Macro-averaged F1 score (macro-F1). This metric gives equal weight to each queue's F1 score regardless of frequency. It directly aligns with the operational goal: all ticket types should be routed correctly, including rare, high-cost queues. Macro-F1 penalizes poor performance on rare categories equally as poor performance on common queues, which reflects the business impact of misroutes. Accuracy is insufficient due to class imbalance.

**Secondary metrics:**
- Weighted F1 (assesses frequent queues, overall SLA compliance)
- Per-category F1 breakdown (identifies rare or multilingual categories where the transformer provides gain)
- Confusion matrix aggregated by queue criticality (flags high-cost misroutes, e.g., enterprise vs. standard)
- Macro-F1 separately for monolingual vs. multilingual subsets (quantifies the multilingual advantage claimed)
- Macro-F1 stratified by customer tier and region (detects confounds)

### 6. Model Selection and Validation

All hyperparameter tuning and model selection is performed on the validation set (months 25–30) using macro-F1 as the selection criterion. A single best configuration for each model is chosen. The test set (months 31–36) is held completely out and used only once, at the end, for final evaluation. No retraining, threshold adjustment, or feedback from test data is permitted. This ensures the test set provides an unbiased estimate of generalization.

### 7. Confound Controls

To rule out the hypothesis that improvements come from exploiting superficial features rather than deeper semantic understanding:

1. **Ablation:** Train a text-only transformer (removing customer context) and verify it still outperforms TF-IDF, showing that improvement is not driven by metadata.
2. **Length stratification:** Report macro-F1 within text length quartiles; concentrated gains in one band suggest length-based overfitting.
3. **Language breakdown:** Report macro-F1 separately for monilingual-English, monolingual-other, and multilingual subsets; absence of gains on multilingual data contradicts the hypothesis.
4. **Temporal stability:** Compare validation (months 25–30) and test (months 31–36) macro-F1 to detect domain drift.
5. **Confusion analysis:** Inspect confusion matrices to ensure high macro-F1 is not achieved by misrouting high-cost queues; if enterprise tickets are increasingly misrouted, business impact is negative despite metric gain.

This design directly tests the hypothesis under realistic deployment conditions, controls for label drift, and provides confidence that any observed gain reflects genuine semantic understanding rather than artifacts of unstable preprocessing or shortcut learning.

---

## eval_scenario_332
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

# Experiment Design: Transformer + Network Features for Enterprise Phishing Detection

## 1. Data Strategy and Label Definition

The experiment uses 24 months of inbound and internal email logs from a single enterprise mail gateway. Raw data includes email bodies, headers (From, To, Subject, Date, Reply-To), sender and recipient identities, attachment metadata (filenames, file hashes, types), extracted URLs, and delivery timestamps.

Labels are sourced from three streams with differing confidence levels: (1) analyst-confirmed phishing investigations (highest confidence), (2) user-reported phishing via security toolbar, and (3) sandbox detonation outcomes. A message is labeled phishing=1 if any investigation or incident response action confirmed malicious intent; all other messages are labeled phishing=0. Critically, messages that remain unlabeled after 90 days post-delivery are excluded from both training and testing to avoid treating unreviewed mail as true negatives—a common source of label bias in security datasets.

## 2. Temporal Split Strategy

Because attacker tactics evolve and the email threat landscape is non-stationary, a random split would allow the model to learn static attacker patterns and fail on novel tactics. Instead, a chronological (temporal) split is used:

- **Months 1–12:** Fit set (model training and feature engineering fit)
- **Months 13–16:** Validation set (hyperparameter tuning and model selection)
- **Months 17–18:** Gap period (unused; allows labels to settle and attack patterns to shift)
- **Months 19–24:** Held-out test set (final evaluation only)

This design respects the operational reality: the model must generalize to future, unseen attacker behavior. The gap period provides a buffer to ensure that delayed labels do not contaminate the test set.

## 3. Feature Engineering and Preprocessing

Three feature groups are constructed:

**Text features:** Email body and subject are tokenized and embedded via a transformer encoder. To avoid external reputation leakage, pre-trained embeddings are not used; the transformer is fine-tuned on the fit set only.

**Network features:** Sender domain age (in months, from WHOIS or internal records), prior sender-to-recipient communication history (count of exchanges in the fit set only), recipient role (from internal directory), recipient phishing susceptibility (historical click-through rate, fit only on months 1–12), and a message-level reporting intensity feature that counts how many distinct recipients flag the message through the security toolbar within the first 24 hours after delivery. Restricting this signal to the first 24 hours keeps it focused on rapid user reaction rather than downstream incident handling, which is useful for prioritizing messages that trigger immediate concern across multiple recipients.

**Metadata features:** Number and types of attachments (one-hot encoded), file hash reputation (only for hashes observed in months 1–12; test-time hashes marked as unseen), and URL presence and domain reputation (only for domains registered before month 18).

**Preprocessing fit policy:** All transformers (text tokenizers, scalers, categorical encoders) are fit exclusively on months 1–12 and applied without refitting to validation and test sets. This prevents future information from influencing preprocessing parameters.

## 4. Model and Baseline

**Proposed model:** A transformer-based sequence encoder (e.g., DistilBERT) processes email text and produces a sequence representation. This representation is concatenated with learned embeddings of network and metadata features, then passed through a 2–3 layer MLP (256–512 units, ReLU, dropout 0.2–0.3) to a binary output. The entire model is trained end-to-end on months 1–12 using cross-entropy loss.

**Baseline:** Logistic regression trained on text features only (TF-IDF or bag-of-words). The baseline receives identical text preprocessing (fit on months 1–12, applied to validation/test) and undergoes the same hyperparameter tuning effort (L1/L2 penalty, regularization strength) on the validation set. This ensures the baseline is not handicapped by reduced capacity or tuning—the comparison isolates the value of network and metadata features.

## 5. Evaluation Metrics

**Primary metric:** Recall at a fixed precision of 90%. This aligns with the operational objective: catch as many phishing emails as possible while constraining false positives to 10% (limiting business disruption). This metric is threshold-aware and directly actionable.

**Secondary metrics:**
- Precision-recall curve (robustness across operating points)
- ROC-AUC (overall ranking quality)
- Recall at 95% precision (stricter FP constraint, for sensitivity)
- False negative rate on emails with attachments (high-risk subset)
- Performance stratified by sender domain reputation (known vs. zero-day) to detect reputation-based shortcuts

## 6. Model Selection and Validation

Hyperparameters are tuned on the validation set (months 13–16) by maximizing recall at 90% precision. No cross-validation is performed within the fit set because temporal ordering must be preserved. The best configuration is selected and applied to the test set exactly once, with no further tuning.

## 7. Controls for Confounds and Leakage

To isolate the value of network and metadata features from reputation-based shortcuts:

1. **Reputation lockdown:** Sender domain age and reputation are derived only from months 1–12. No test-time reputation lookups occur; test-time domains and hashes are marked unseen.

2. **Ablation:** The transformer is trained in two configurations: (a) text and network features combined, and (b) text only. The gap between them quantifies the marginal contribution of network features. If network-only features nearly match the full model, reputation leakage is the likely driver.

3. **Stratified evaluation:** Performance is reported separately for analyst-confirmed phishing, user-reported phishing, and sandbox outcomes. If performance is strong only on one label source, overfitting to label artifacts is suspected.

4. **Unseen infrastructure:** Secondary metrics explicitly measure performance on zero-day sender domains and first-seen file hashes, ensuring the model generalizes beyond memorized attacker infrastructure.

These controls are sufficient to establish whether the transformer model with network features outperforms text-only approaches due to genuine semantic understanding or reputation-based shortcuts. The temporal split, locked reputation features, and stratified analysis together provide high confidence in the results' validity and generalization to future email threat detection.

---

## eval_scenario_125
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: TFT vs. LightGBM for Next-Day SKU-Warehouse Demand Forecasting

### 1. Data Strategy

The experiment uses 2.5 years of daily SKU-by-warehouse sales records from the production marketplace, covering all active warehouses and SKUs. External covariates — daily weather by warehouse geolocation, regional holidays, and a major events calendar — are joined on a warehouse_id × date key. The critical data quality problem is demand censoring: on days with stockouts, observed sales understate true demand. Rather than training naively on these censored observations, we replace stockout-day sales with an imputed demand estimate (warehouse × SKU × day-of-week × week-of-year median from the eight nearest non-stockout weeks) and attach a binary `censored_day` flag. During training, censored rows are downweighted by 0.5; during evaluation, they are excluded entirely. This ensures that neither model is rewarded for learning inventory constraints instead of true demand.

### 2. Split Strategy

The data is split at the SKU-warehouse-day level into 70% training, 15% validation, and 15% test, using stratified random sampling to preserve the distribution of promotion days, stockout incidence, and demand levels across splits. This gives each split broad coverage of seasonal patterns and rare event conditions, reducing variance in the comparison between TFT and LightGBM while keeping evaluation representative of the overall dataset.

### 3. Feature Engineering

Both models receive an identical feature set: temporal identifiers (day-of-week, week-of-year, days-to/from-promotion), price and promotion signals (discount depth, promotion flag), weather covariates, inventory and stockout history, and product metadata. LightGBM receives these as hand-crafted lag and rolling-window features (lags at 1, 2, 3, 7, 14, 28 days; rolling mean/std/max over 7-, 14-, 28-day windows). TFT receives the same covariates as time-varying inputs, with the raw historical sequence fed directly into its temporal attention layers. All continuous-feature scalers and categorical target encoders are fit on the training fold only and applied without refitting to downstream splits.

### 4. Model and Baseline

The proposed model is a Temporal Fusion Transformer (TFT) tuned via Optuna on the validation fold. The baseline is a LightGBM regressor tuned with an identical Optuna budget on the same validation fold and the same feature set. This pairing is essential: giving LightGBM equivalent tuning effort and identical data access means any performance gap can be attributed to architectural differences rather than resource asymmetry or data privilege.

### 5. Evaluation Metrics

The primary metric is **business-weighted MAPE (wMAPE)**, where each SKU-warehouse-day is weighted by its trailing 90-day average revenue. This directly captures the operational priority: accuracy on high-revenue, high-velocity items matters more than average accuracy across sparse tail SKUs. Evaluation runs only on uncensored days. The promoted-item subgroup wMAPE is pre-registered as a stratified evaluation to test the hypothesis's sub-claim about promotion periods.

Secondary metrics include unweighted MAPE (to confirm weighting is not masking a reversal), pinball loss at 0.1/0.9 quantiles (for uncertainty calibration relevant to safety-stock decisions), directional bias by segment, and a simulated stockout rate under each model's replenishment policy.

### 6. Validation and Model Selection

Hyperparameter search for both models uses wMAPE on the validation fold. After tuning is complete, the selected configurations are compared on the held-out test split to make the final assessment of whether TFT materially outperforms LightGBM under the same feature access and optimization budget. No further tuning or architecture changes are permitted after this final evaluation.

### 7. Controls and Confounds

Three confounds are explicitly controlled. First, covariate access parity: both models receive identical inputs, isolating architecture from data richness. Second, censoring parity: both models are trained and evaluated on identically treated censored data. Third, the promoted-item sub-claim is evaluated as a pre-specified stratified slice, not a post-hoc discovery. Heterogeneity checks across warehouse type, SKU velocity quartile, and seasonal regime will clarify whether any observed advantage is global or confined to a specific subpopulation. The experiment establishes whether TFT's sequence modeling architecture outperforms a well-tuned tabular baseline under operationally relevant conditions; it does not establish that TFT would generalize to different retail verticals or radically different data regimes.

---

## eval_scenario_616
**Category:** critique | **Difficulty:** hard | **Correct position:** critique_wins

## Experiment Design: Raw Time-Series vs. Aggregate Features for Bearing Fault Detection

### 1. Data Collection and Labeling

The experiment uses 18–36 months of continuous sensor telemetry from a fleet of 50–200 identical or similar rotating machines in the factory. Sensors include vibration accelerometers (sampled ≥1 kHz), temperature probes, acoustic sensors, and motor-current monitors (≥10 Hz), all sourced from the production facility's SCADA historian. Failure labels are obtained from maintenance work orders and post-inspection reports, timestamped to the nearest hour. To ensure high label quality, only machines with ≥90% sensor uptime and ≥2 confirmed fault cycles during the observation window are included. A positive label ("failure imminent") is assigned to all samples in the 24-hour window immediately preceding a confirmed bearing or motor fault. Negative labels are assigned to samples from periods ≥7 days after maintenance or from machines with no failures during the study window. Samples in the 7-day post-maintenance period are excluded to avoid labeling transient post-repair behavior as normal operation.

### 2. Data Split Strategy

The data are split temporally and by machine group to prevent leakage and respect the autoregressive nature of sensor signals. Allocation: training set covers months 1–12; validation set covers months 13–15 (3 months); test set covers months 16–18 (3 months). Critically, all data from each individual machine is assigned to a single split (e.g., Machine #42 appears only in training, Machine #73 appears only in validation). This group-temporal split prevents information about a specific machine's failure patterns from leaking across train/val/test boundaries. Within each split, data are stratified by machine type or operational regime (if applicable) to ensure balanced representation. This design respects temporal ordering (no future information in training), prevents machine-specific overfitting, and reflects realistic deployment scenarios where the model must generalize to equipment operating in periods after the training window.

### 3. Feature Construction

Two feature sets are constructed from the identical 24-hour pre-failure window and applied to both the baseline and proposed model:

**Raw Sequence Features:** The full 24-hour window of multivariate sensor time series (vibration, temperature, acoustic, motor current) at the native or standardized sampling frequency, formatted as a 2D array (time steps × sensor channels). These sequences preserve temporal dynamics and transient events.

**Aggregated Summary Features:** From the same 24-hour window, handcrafted statistics are computed for each sensor channel: mean, standard deviation, max, min, 25th/50th/75th percentiles, peak-to-peak amplitude, crest factor, and kurtosis. For vibration signals, additional spectral features are computed: peak frequency, spectral entropy, and power in standardized frequency bands (0–500 Hz, 500–2000 Hz, 2000–10 kHz). To keep sensor calibration consistent across machines and operating regimes, preprocessing for both feature sets is parameterized once before model fitting: normalization constants, brief-gap imputation rules, resampling settings, and artifact filters are fixed and then applied identically to the training, validation, and test partitions. This ensures both feature sets reflect the same underlying sensor data and operational window, isolating the comparison to architecture (raw sequences vs. aggregates) rather than data availability or window definition.

### 4. Model and Baseline

**Proposed Model:** A 1D convolutional neural network or bidirectional LSTM trained on raw 24-hour multivariate sequences. Typical architecture: 3–4 convolutional layers (32–128 filters, kernel sizes 3–5) with ReLU activation, or 2 LSTM layers (64–128 units) with attention, followed by dropout (0.3–0.5), a fully connected layer, and sigmoid output for binary classification.

**Baseline:** Logistic regression trained on aggregated summary statistics. Logistic regression is chosen as the baseline because it is a strong classical approach for high-dimensional tabular data, computationally efficient, interpretable, and provides a fair comparison without architectural confounds. Both models are tuned with identical effort: hyperparameter selection (filter counts, dropout, L2 regularization, class weights, learning rate) is performed via grid or random search on the validation set, optimizing the primary metric (see below). Both models use class-weight balancing (inverse frequency weighting) to account for class imbalance.

### 5. Evaluation Metrics

**Primary Metric:** Recall at a fixed false-alarm rate (FAR). Specifically, recall is computed at the validation-set operating point where the false-positive rate is ≤5% (adjustable per operations requirements). This metric directly reflects the operational objective: maximize the number of failures caught early while constraining the number of unnecessary maintenance alerts. The 5% FAR threshold represents a realistic maintenance budget; this can be adjusted based on stakeholder feedback. The test set is evaluated at the same FAR threshold to ensure the comparison is held constant.

**Secondary Metrics:**
- **Lead Time:** Mean time (hours) between the first positive prediction in the 24-hour pre-failure window and the actual failure. Higher values indicate earlier detection.
- **Precision at 5% FAR:** Proportion of alerts that correspond to true faults.
- **AUROC and AUPRC:** Characterize the full precision-recall trade-off and detect distributional advantages.
- **Stratified Recall by Machine Type:** Verify that the proposed model generalizes equally across equipment variants and does not rely on machine-specific patterns.

### 6. Model Selection and Validation

Hyperparameter tuning is performed exclusively on the validation set (months 13–15). For each candidate hyperparameter configuration, the primary metric (recall at ≤5% FAR) is computed on validation data. The configuration yielding the highest validation recall is selected. The test set is not accessed during this process, preventing threshold or architecture selection from overfitting to the test distribution.

### 7. Test Set Evaluation

After model selection, the selected model is evaluated once on the held-out test set (months 16–18). All primary and secondary metrics are computed on test data. Results are reported with 95% confidence intervals (via stratified bootstrap resampling over test-set failures by machine type). No retraining or threshold adjustment occurs on the test set.

### 8. Confound Controls

To isolate the effect of raw sequences versus summary statistics:
- Both models use the identical 24-hour label window and train/val/test splits, holding label definition and temporal structure constant.
- Both models operate on the same machines and time periods; there is no machine-type or operating-regime mismatch.
- Stratified splits by machine type (if ≥3 types) ensure balanced representation across both models.
- Class-weight balancing is applied uniformly to both baseline and proposed model.
- Post-hoc check: marginal distributions of failure rates, machine types, and operating hours are compared across train/val/test splits. Large mismatches would indicate a distributional confound; any such findings are reported.

### 9. Scope of Claims

This design establishes whether raw sensor sequences, when processed by a sufficiently expressive model (CNN or LSTM), yield higher early-warning recall at a fixed false-alarm rate than classical aggregated features processed by logistic regression. It does **not** establish: superiority of neural networks in general, optimal model architecture, generalization to different sensor types or equipment families outside the test fleet, or robustness to sensor failures or drift. The result is specific to the 24-hour pre-failure window, the machines and sensors in the study, and the operational constraints (5% FAR) defined here.

---

## eval_scenario_167
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

# Experiment Design: Hybrid vs. Dense-Only Retrieval for Legal Case-Law Search

## 1. Overview
To rigorously test whether a hybrid retrieval model combining BM25 and dense embeddings outperforms dense-only retrieval for legal case search, we propose a temporally-stratified, multi-sourced-label experiment with confound controls. The design isolates the effect of the hybrid combination while accounting for click bias, temporal leakage, and query type heterogeneity.

## 2. Data Collection and Labeling

We will use 36 months of historical production data from the commercial platform: timestamped queries, clicked results, case metadata, and the full case-opinion corpus.

**Implicit Labels:** For high-volume query types (>100 instances), we derive relevance from user behavior: cases with ≥30 second dwell time are labeled relevant (grade 1); cases clicked but dwelled <10 seconds are marginal (grade 0); cases in top-20 impressions but unclicked are irrelevant (grade -1). All implicit labels are adjusted for position bias using propensity weighting estimated from historical A/B tests or random impressions.

**Expert Labels:** Low-frequency queries and borderline cases are labeled by a panel of three legal experts on a 0–3 scale (irrelevant, marginal, relevant, highly relevant). Inter-rater agreement must exceed Fleiss' κ = 0.65; disagreements are resolved by median. Expert labels supplement implicit labels to reduce bias and provide ground truth for rare but important queries.

**Data Quality:** Known issues—click bias, position bias, survivor bias—are explicitly handled via propensity weighting, expert labeling, and exclusion of zero-engagement queries. The corpus is representative of deployment: U.S. federal and state cases, temporal distribution matching platform use.

## 3. Data Splits

We employ a **temporal split** to prevent leakage from future cases and query behavior:
- **Training:** Months 1–24 (historic queries and cases)
- **Validation:** Months 25–30 (intermediate period)
- **Test:** Months 31–36 (held-out, used once)

Within each split, queries are **stratified** by length (short: 1–3 terms; medium: 4–8; long: 9+) and frequency (head: top 10% queries; tail: bottom 50%), ensuring the model is evaluated on both common and rare queries. This prevents overfitting to high-volume query types and captures semantic performance on long-tail, nuanced legal queries where hybrid methods are hypothesized to excel.

## 4. Preprocessing and Feature Engineering

To keep lexical and calibration spaces stable across time windows, shared preprocessing artifacts are established once from the 36-month corpus and then frozen for all splits:
- BM25 index vocabulary and tokenizer derived from the full case corpus
- Dense embedding model (fine-tuned LegalBERT) trained end-to-end on training queries and cases using triplet loss with hard negatives
- Score normalization (mean/std for relevance calibration) set once so implicit and expert grades remain on a common scale across train, validation, and test
- Query normalization (case-law abbreviations, synonym expansion) built from the observed corpus vocabulary and then applied consistently to every split

Validation and test sets use this locked preprocessing pipeline without further updating, which keeps representation drift from confounding model comparisons.

## 5. Model and Baseline

**Hybrid Model:** score(query, case) = α · BM25(query, case) + (1 – α) · dense_sim(query, case), where α is tuned on validation nDCG@10.

**Baseline:** Dense-only retriever (α = 0.0), using the **same fine-tuned embeddings**, **same tuning effort** (learning rate, epochs, batch size optimized on validation set), and **same ranking evaluation**. This isolates the effect of BM25 combination. A secondary BM25-only baseline (α = 1.0) is included for reference.

## 6. Model Selection and Validation

Hyperparameter tuning (α, embedding model learning rate) uses validation set nDCG@10 only. Grid search over α ∈ [0.1, 0.3, 0.5, 0.7, 0.9]. The test set is locked and never touched until final evaluation.

## 7. Primary and Secondary Metrics

**Primary Metric:** nDCG@10, evaluated on the full test set and stratified by query type (head vs. tail, short vs. long) and jurisdiction. nDCG@10 is chosen because top results matter most in legal research, and it aligns with user workflow (attorneys examine top-10 before reformulating).

**Secondary Metrics:**
- Recall@10: ensures hybrid is not just reranking the same set
- MRR: position of first relevant case
- MAP: average precision across all relevant items
- Precision@5: practical metric for top-5 only
- CTR and query reformulation rate (if A/B test available): user satisfaction

## 8. Confound Controls

**Confound 1 — Head-term bias:** Report nDCG@10 separately for head queries (top 10%) vs. tail queries (bottom 50%). Null gain on tail queries despite head gains suggests term-frequency exploitation, not semantic understanding.

**Confound 2 — Citation popularity:** Report performance by case citation count (high vs. low). Gain concentrated in high-citation cases suggests popularity bias, not relevance learning.

**Confound 3 — Synonym and semantic understanding:** Curated test set of ~100 expert-labeled queries with synonymy challenges (e.g., 'malice aforethought' vs. 'intent to kill'). Evaluate hybrid vs. dense separately on this set to verify semantic gains.

**Confound 4 — Click bias:** Report results on expert-labeled queries only to validate robustness against implicit-label bias.

**Confound 5 — Temporal drift:** Stratify test-set results by jurisdiction and court level; analyze performance trend across months 31–36 to detect corpus or behavior drift.

## 9. Reporting and Scope

Results are reported with 95% confidence intervals (bootstrap, 10,000 resamples) to quantify uncertainty. The experiment establishes whether hybrid retrieval outperforms dense-only *in this specific legal search context, on these query types, under these label conditions*. It does not establish generalization to other legal domains, languages, or IR tasks. Ablations (BM25-only, dense-only) and confound analyses clarify whether gains are from genuine semantic-lexical synergy or from exploiting statistical regularities in the data.

---

## eval_scenario_479
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Dense Bi-Encoder for Support Knowledge Retrieval

**Hypothesis:** A dense bi-encoder trained with contrastive learning on historical ticket–article pairs will outperform a TF-IDF/BM25 baseline on retrieving correct help articles for support queries, particularly for short or paraphrased queries.

### 1. Data and Labeling Strategy

We will use 18–24 months of production support tickets and knowledge base articles from a single SaaS product line. The data includes ticket text, agent notes, timestamps, article IDs that were clicked or used for resolution, and resolution codes. This window captures product evolution and seasonal variation in support patterns.

Labels are derived in two ways: **implicit** (for training) and **manual** (for test evaluation). Training uses implicit labels: articles that were clicked or used to resolve a ticket are marked as relevant; unclicked articles are marked as negative. This is inherently noisy but scalable. For the held-out test set, we will manually annotate ~500–1000 tickets using a 3-point relevance scale (relevant, partially relevant, not relevant) assigned by domain experts familiar with the product. This ground truth set is small but clean, and it represents the most realistic assessment of model quality.

### 2. Split Strategy: Temporal with Stratification

Because product features, error messages, and documentation change over time, we employ a **chronological split** to prevent leakage of future support patterns into training:

- **Training (months 1–12):** Oldest product versions. Used to fit all models.
- **Validation (months 13–15):** Intermediate versions. Used for hyperparameter tuning and model selection only.
- **Test (months 16–18):** Newest versions. Manually annotated; held out until final evaluation.

Within the test set, we will stratify by issue frequency (common vs. rare issue types) and query characteristics (short, long, paraphrased). This stratification allows us to diagnose whether improvements hold across the full distribution or only on common patterns, which would be a sign of overfitting or template memorization.

### 3. Preprocessing and Feature Preparation

Preprocessing parameters that define the shared retrieval space are established once from the full corpus of available tickets and articles before model fitting. This includes:

- Tokenization and vocabulary construction.
- BM25 statistics (document frequency, term weights).
- Product-specific stop-word lists and normalization rules.

Freezing these preprocessing components up front keeps the lexical space consistent across train, validation, and test periods, which is useful in a support setting where product terminology and article naming conventions can shift over time. The same tokenization is applied to both the bi-encoder and BM25 baseline to ensure fair comparison. No additional engineered features are introduced; both models work directly from ticket and article text.

### 4. Models and Baseline

**Dense Bi-Encoder:** A transformer-based model (e.g., distilBERT or a domain-finetuned variant) that encodes tickets and articles into a shared embedding space. It is trained on the training set using in-batch negatives and contrastive loss (NT-Xent or triplet loss variants) to maximize similarity between ticket–article pairs that co-occur in resolved tickets.

**Baseline:** BM25 (Okapi algorithm) with tuned hyperparameters (k1, b). BM25 is the current standard for support retrieval and provides a strong, interpretable benchmark. Both the bi-encoder and BM25 receive equivalent hyperparameter tuning effort using a grid or random search over the validation set, ensuring neither model is handicapped.

### 5. Evaluation Metrics

**Primary Metric:** Mean Reciprocal Rank (MRR) at k=5 on manually annotated test tickets. MRR directly reflects the operational goal—agents need the right article in the top few results to save time. k=5 is a realistic depth for a support UI.

**Secondary Metrics:**
- Precision@1 and Precision@5 (fraction of retrieved results that are relevant).
- NDCG@5 (captures partial relevance judgments from manual annotations).
- Coverage (fraction of tickets for which ≥1 relevant article exists in top-5).
- Stratified performance by issue rarity and query length (robustness checks).

Results will include 95% bootstrap confidence intervals to account for variance in the test set.

### 6. Model Selection and Test Protocol

Hyperparameter tuning is performed on the validation set (months 13–15) using MRR@5. The bi-encoder checkpoint with the highest validation MRR is retained. No tuning decisions are made using the test set. After all development is complete, the test set is evaluated exactly once, and results are reported with stratified breakdowns.

### 7. Confound Controls

**Temporal drift:** The chronological split ensures test tickets reflect the current product state, so improvements are not driven by outdated documentation.

**Template memorization:** Stratified analysis on rare issue types checks whether gains persist on novel queries outside frequent patterns.

**Noisy implicit labels:** We acknowledge that training labels derived from agent clicks are imperfect. The robustness of this noisy supervision is tested by comparing performance on high-confidence manual labels vs. implicit labels in the test set analysis.

**Data imbalance:** We stratify test results by ticket frequency to ensure the bi-encoder does not simply learn to rank common issues well.

This design establishes whether the dense model outperforms BM25 on held-out recent support tickets. It does not establish long-term generalization to future product versions; that would require continuous evaluation over time.

---

## eval_scenario_375
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Sequence Models for Household Peak-Demand Forecasting

### 1. Data Strategy

The analysis uses 36 months of smart meter electricity consumption readings from 5,000–10,000 households served by a single utility. Meter readings are recorded at 60-minute intervals (or 15-minute if available). Covariate data include daily area-level weather (temperature, solar irradiance, precipitation), household tariff tier, and calendar features (day-of-week, holiday flags). The target label is binary: whether a household's total daily consumption exceeds its peak-demand threshold, computed deterministically from the same metering system.

The peak threshold is defined per household using historical percentiles (e.g., 95th percentile of each household's observed daily consumption) or contracted limits. This ensures the label is stable, non-null, and grounded in operational reality.

Known data quality issues (e.g., missing readings, sensor drift) are handled as follows: missing meter readings within a household–day are imputed using the household's mean value for that hour-of-day; weather data gaps are filled by area-level interpolation. Imputation parameters are fit on the training set and applied uniformly to validation and test.

### 2. Split Strategy

A chronological split with household stratification is used:
- **Training:** Months 1–24 (24 months)
- **Validation:** Months 25–30 (6 months)
- **Test:** Months 31–36 (6 months)

This temporal split is essential: it prevents information leakage from future weather patterns, usage trends, and seasonal dynamics into the training window. A sequence model can otherwise exploit subtle date or seasonal correlations that are not causal and would fail in deployment.

Within each set, households are stratified by their baseline peak-exceedance rate (binned into low, medium, high tiers) to ensure each split contains similar proportions of rare-event households. This reduces variance in metric estimation and ensures calibration can be evaluated across cohorts.

### 3. Preprocessing and Feature Engineering

All preprocessing transformers (scaling, imputation, encoding) are fit on the training set only and applied consistently to validation and test, preventing data leakage.

**Sequence Model Features:**
- 24-hour consumption history: 1,440 minute-level values (or 96 × 15-minute intervals), taken from the household’s most recent 24-hour meter history aligned to the prediction day and normalized within each household by dividing by the household's mean daily consumption.
- Area-level weather covariates (temperature, solar irradiance, precipitation) for the preceding day and current day, interpolated to meter frequency.
- Static features: tariff tier, annual consumption quintile.
- Calendar: day-of-week and month-of-year one-hot encodings.

**Baseline Features:**
- Aggregate daily consumption over the household’s most recent 7-day history window.
- Same weather and calendar features as the sequence model.

Both feature sets include identical weather and calendar signals, ensuring the comparison isolates the benefit of fine-grained temporal modeling, not superior seasonality capture. This feature construction also matches the utility’s operational scoring feed, where the latest finalized meter history is used when generating next-day risk estimates.

### 4. Model and Baseline

**Model:** An LSTM or temporal CNN with attention, consuming the 24-hour sequence plus weather covariates. Hidden dimensions (64–128 units) are tuned via validation performance. Dropout regularization (0.2–0.3) prevents overfitting. Training uses Adam optimizer with early stopping on validation AUPRC (patience = 10 epochs). Batch size 32, max epochs 100.

**Baseline:** Logistic regression on daily aggregate features. Crucially, the baseline receives identical preprocessing, feature scaling, and tuning effort: L2 regularization strength is chosen via grid search on the validation set, and class weights are calibrated on training data to reflect the observed peak-exceedance rate. This ensures a fair comparison—the baseline is not weakened by weaker hyperparameter tuning.

### 5. Evaluation Metrics

**Primary Metric: Area Under the Precision-Recall Curve (AUPRC)**

Peak-exceedance events are rare (imbalanced), making AUC-ROC and accuracy poor proxies for utility-relevant performance. PR-AUC directly encodes the utility's operational concern: identifying peak-risk households (high recall) while avoiding false alarms (high precision). It enables threshold selection for demand-response campaigns.

**Secondary Metrics:**
- **AUC-ROC:** Confirms ranking ability across the full probability space.
- **F1 Score (at validation-optimized threshold):** Interpretable precision–recall trade-off.
- **Expected Calibration Error (ECE):** Ensures predicted probabilities match observed peak rates; critical for utilities.
- **Recall at Fixed Precision:** Supports operational deployment decisions (e.g., recall at 80% precision).

### 6. Validation and Model Selection

The validation set (months 25–30) is used for all hyperparameter tuning and early stopping. No information from the test set is used during model selection. After all tuning is complete, the test set (months 31–36) is evaluated exactly once, and results are reported with 95% confidence intervals computed via stratified bootstrap over households.

### 7. Controls and Confounds

Seasonality and weather are controlled by including them in both the sequence model and baseline. Any improvement in the sequence model cannot be attributed to better seasonality capture, only to superior modeling of intra-day consumption dynamics.

A sensitivity analysis trains a second baseline using only lagged consumption (no weather) to isolate the benefit of the sequence model's ability to capture within-day patterns independent of macro weather trends.

Temporal autocorrelation is preserved by the chronological split; household heterogeneity is managed by stratification. The design establishes whether sequence models, given equivalent weather and calendar information, outperform aggregate baselines—not whether either model captures seasonality.

---

## eval_scenario_311
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Session-History Features in E-Commerce Search Ranking

### 1. Data Collection and Preparation

We will use production search logs from the e-commerce marketplace spanning 18 months (months 1–18). The raw data includes: query text, session and user identifiers, timestamps, ranked impressions with positions, user clicks, dwell time per click, add-to-cart events, purchases, and item attributes (category, seller rating, popularity). We filter to sessions containing at least one query reformulation, ensuring the session-history signal is available and non-trivial. This yields approximately 50M query-result interactions across 5M sessions. The 18-month window is chosen to capture seasonal patterns, catalog drift, and sufficient volume for stable nDCG estimates.

Implicit relevance labels are constructed from multi-signal feedback: clicks with ≥10s dwell time are labeled as moderate-to-strong positive (weight 1.0); clicks followed by add-to-cart are strong positive (weight 2.0); clicks with <2s dwell time are weak positive (weight 0.5); items with no click are unlabeled. This dwell-time-weighted labeling reduces position bias confounds, since top-ranked items receive more clicks but not necessarily longer engagement.

### 2. Temporal Split Strategy

To prevent information leakage and respect real-world deployment assumptions, we use a strict chronological split:
- **Training set (months 1–12):** All sessions and interactions within this window.
- **Validation set (months 13–15):** All sessions in this window; used for hyperparameter tuning and model selection.
- **Test set (months 16–18):** Held out, untouched until final evaluation.

Sessions are the atomic unit of split; all query-result interactions within a session remain together. This prevents session history from a test-set session leaking into the training distribution. Additionally, a stratified holdout of 500 tail-query sessions (queries with <100 occurrences in the full dataset) is reserved from the test set to diagnose position and popularity bias separately.

### 3. Feature Engineering

Two feature sets are constructed:

**Baseline features (BL):** Current query embedding (768-d BERT pooled representation), item BM25 score, category-query match indicator, item popularity rank percentile, seller rating, price tier. These capture query-item relevance without session context.

**Session-history features (SH):** (1) Reformulation embeddings—concatenated BERT embeddings of up to 5 prior queries in the session, zero-padded; (2) query intent drift—cosine similarity between current query and session-opening query; (3) click history—mean dwell time of clicked items within the session; (4) item exploration entropy—entropy of categories explored in session clicks; (5) session length—count of queries issued so far. Aggregating click-derived context over the full session provides a more stable estimate of shopping intent than relying only on a sparse query prefix, particularly when reformulation chains are short and a single high-dwell interaction carries most of the disambiguating signal.

The hypothesis model uses BL ∪ SH. The baseline uses BL only. All preprocessing transformers (tokenizer, scalers, embeddings) are fit on the training set only and applied frozen to validation and test.

### 4. Model and Baseline

Both models are LambdaMART rankers (LightGBM with rank:ndcg objective). They are trained on the same training data and tuned over an identical hyperparameter search space: learning_rate ∈ [0.01, 0.1], num_leaves ∈ [15, 63], feature_fraction ∈ [0.5, 1.0]. Both use early stopping with patience=50, monitored on validation nDCG@10. The hypothesis model trains on (BL ∪ SH) features; the baseline trains on BL features only. Both receive equal computational budget and tuning effort, ensuring differences in test performance are attributable to the feature set, not model capacity or training procedure.

### 5. Evaluation Metrics

**Primary metric: nDCG@10.** This metric measures the quality of ranking in the top 10 results—the area users examine—with graded relevance levels (0–4). It is normalized, position-discounted, and directly aligns with the business goal: helping shoppers find relevant products quickly. nDCG@10 is computed per query and averaged across all test queries.

**Secondary metrics:**
- nDCG@1, nDCG@5: Diagnose whether gains concentrate near the top.
- Mean Reciprocal Rank (MRR@10): Captures position of first relevant item.
- Recall@10: Detects whether the model includes more relevant items (not just reranks them better).
- Stratified nDCG@10 on tail queries and head queries: Guards against popularity bias and position bias by isolating performance on rare vs. common queries.

### 6. Model Selection and Test Protocol

Hyperparameter tuning is performed using the validation set (months 13–15). Each model is evaluated over 50 random configurations; the configuration with best validation nDCG@10 is selected. The test set (months 16–18) is sealed during this process and is used exactly once, at the end, for final evaluation. Both the hypothesis model and baseline are scored on the test set in a single forward pass; no iterative refinement or threshold adjustment based on test results is permitted.

### 7. Confound Controls

Position bias and popularity bias are the primary threats. We control for these through:
- **Dwell-time weighting in labels:** Longer engagement indicates true relevance, not ranking artifact.
- **Stratified evaluation:** Tail-query vs. head-query performance is scored separately; gains concentrated only in head queries would suggest popularity bias.
- **Counterfactual analysis (post-hoc):** nDCG improvement is decomposed into relevance gains vs. position gains by comparing against a popularity-based baseline.
- **Item-level audit:** Items that improve in ranking are inspected for popularity clustering.
- **Session-history dose-response:** Performance on 0-reformulation sessions vs. high-reformulation sessions tests whether improvements require the session-history signal.

This design will establish whether session-history features genuinely improve ranking alignment with user intent, or whether improvements are artifacts of position and popularity bias exploitation.

---

## eval_scenario_403
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer vs. Gradient-Boosted Models for Pump RUL Prediction

### 1. Objective and Hypothesis
We aim to test whether a transformer model trained on raw multivariate sensor sequences with self-supervised pretraining predicts 7-day remaining useful life (RUL) more accurately than a gradient-boosted baseline trained on hand-engineered summary statistics. Success is measured by better prioritization of imminent failures on an unseen test set of future pump failures, reflecting operational value: when maintenance capacity is constrained, the model should rank the most urgent pumps ahead of less critical ones.

### 2. Data Collection and Labeling
Data source: 4–5 years of SCADA and condition-monitoring records from a single process plant, comprising 200–400 unique pump units of 3–5 distinct models. Raw signals include vibration (10 Hz+), temperature, pressure, flow, and motor current, all sampled at 1-minute intervals or faster.

Label definition: Remaining useful life is defined as the time in days from a sensor snapshot to the next failure event. Failure is operationally defined as: (a) unplanned shutdown due to malfunction, (b) maintenance intervention explicitly noting imminent degradation risk, or (c) out-of-service status. We exclude same-day interventions (RUL < 1 day) as potential data entry errors and right-censor units still operating at the observation window end (RUL > 365 days excluded from test). This ensures labels reflect genuine failure risk within a relevant operational window.

### 3. Train-Validation-Test Split Strategy
The dataset is split chronologically to prevent leakage from future maintenance decisions into training:
- **Training set:** first 60% of the timeline (by calendar date)
- **Validation set:** next 20% (chronologically later, non-overlapping)
- **Test set:** final 20% (latest time period)

Within each temporal block, samples are stratified by pump model (5 strata) to ensure balanced representation and test generalization across equipment types. This temporal + stratified approach is critical because RUL prediction is inherently forward-looking; a model trained on mixed or future data is not credible at deployment.

### 4. Feature Engineering and Preprocessing
Preprocessing transformers (z-score scaling, spectral feature extraction, imputation) are fit on the training set only and applied without re-fitting to validation and test sets. This prevents information leakage.

**Transformer model input:** Raw multivariate sequences of 6 channels sampled at 1-minute intervals, 7-day windows (10,080 samples per window). No hand-engineered features; the model learns directly via self-supervised pretraining (masked autoencoding, 15% masking, 50 epochs) followed by supervised fine-tuning (100 epochs with early stopping).

**Baseline model input:** Hand-engineered 7-day rolling features: vibration RMS, crest factor, kurtosis, spectral centroid; temperature mean, max, trend slope; pressure and flow mean/variance; motor current THD and peak. Identical feature computation for both models ensures fair comparison.

### 5. Model and Baseline
**Transformer:** 4-layer temporal convolutional transformer, 8 attention heads, 512 hidden dimensions, with a linear regression head for RUL prediction.

**Baseline:** XGBoost gradient boosted regressor on hand-engineered features. Both models receive equivalent tuning effort: hyperparameter search (100 trials, random search) on the validation set, same computational budget, and same evaluation metric (validation concordance index).

### 6. Evaluation Metrics
**Primary metric:** Concordance index (C-index) on the test set (samples with RUL ∈ [1, 365] days). C-index measures whether the model correctly orders pumps by time-to-failure, which is operationally meaningful when maintenance teams must decide which assets to inspect first under limited capacity. It is also less dominated by a small number of large RUL misses than squared-error-based summaries and therefore provides a stable view of degradation prioritization quality.

**Secondary metrics:** Median absolute error (robustness), 7-day recall (% of imminent failures caught), false positive rate (% of no-failure samples mispredicted as failures), per-model-type C-index (generalization across pump types), and per-site C-index (absence of location artifacts).

### 7. Model Selection and Validation
Hyperparameters are tuned on the validation set using concordance index as the criterion. The test set is held entirely out and touched only once at the end for final evaluation. Results include 95% confidence intervals.

### 8. Confound Controls
**Unit identity leakage:** We probe latent representations to detect whether unit identity alone predicts test residuals. **Maintenance history:** Test set is stratified by prior maintenance frequency; per-stratum C-index detects if the model exploits service patterns rather than degradation dynamics. **Sensor drift:** Per-unit detrending (fitted on training data per unit) removes global drift. **Imbalance:** Censored samples are excluded; test set composition is reported to ensure fair RUL distribution across both models. **Site effects:** Multi-site data is stratified across train/val/test and per-site error is reported.

### 9. Scope and Conclusion
This design will establish whether transformers + self-supervised pretraining outperform classical approaches on this specific equipment cohort and time period. It will not establish generalization to other plants, equipment types, or datasets—that requires separate validation. The experiment controls for temporal leakage, unit identity artifacts, and maintenance-history confounds, enabling a credible claim about the predictive model's advantage.

---

## eval_scenario_381
**Category:** critique | **Difficulty:** hard | **Correct position:** critique_wins

## Experiment Design: Transformer vs. Gradient-Boosted Fraud Detection

### 1. Hypothesis and Scope

The hypothesis states that a transformer-based model exploiting full claim event sequences will outperform a gradient-boosted baseline on 90-day insurance claim fraud prediction. To test this rigorously, we must isolate sequence modeling as the explanatory variable while controlling for data leakage, temporal distribution shift, and confounding from investigator bias.

### 2. Data and Labeling

We use 18–24 months of claim records from a single insurer, spanning submission timestamp, claimant attributes, claim details, service provider information, payment history, and prior claim records. Critically, we restrict the dataset to claims with resolved fraud labels—those investigated by the Special Investigation Unit (SIU) or reaching final adjudication—to avoid treating unlabeled claims as implicit negatives. This introduces verification bias (only a subset of claims are labeled), but this bias affects both models equally, preserving the validity of the comparison.

The 90-day window is defined as: prediction is made at submission; the label is observed if available within 90 days or at closure, whichever comes first. Claims labeled beyond 90 days are excluded to ensure temporal consistency.

### 3. Temporal Split Strategy

The dataset is divided chronologically: Months 1–12 for training, Months 13–15 for validation, Months 16–18 for test. Within each split, we stratify by claim type (bodily injury, property damage, etc.) to ensure representative distributions. No random shuffling is applied.

Justification: Insurance claims exhibit seasonality, policy evolution, and fraudster adaptation. A temporal split reflects the deployment reality: the model is trained on historical data and must predict fraud on future claims. Random splitting would conflate temporal patterns, overestimating generalization. This ordering prevents future information from leaking into training and tests whether models truly generalize to unseen distribution shifts.

### 4. Feature Engineering

Both models receive equivalent information but in different forms:

**Transformer input:** Timestamped event sequences per claim (max 50 events), including claim events (submission, assignment, payment, closure), account attributes (age, policy tenure, prior claim counts), and claim attributes (type, provider, location). Event types are embedded; position encodings capture temporal order. Preprocessing (standardization, categorical encoding, missing value imputation) is fit on the training split only and applied to validation and test without refitting.

**Baseline input:** Hand-engineered aggregated features derived from the same raw signals: claim-level (amount, days to payment, provider frequency), claimant-level (age, tenure, prior claim count and fraud rate), temporal (day-of-week, month), and interactions (amount × prior fraud rate). Same preprocessing fit-on-train policy.

No post-label information is included; missingness indicators are preserved to capture legitimate claim patterns.

### 5. Model and Baseline

**Transformer:** 3-layer encoder with 8-head attention, 256 hidden dimension, 2-layer MLP head, dropout 0.2, trained with Adam (lr 0.001), L2 regularization (1e-4).

**Baseline:** XGBoost with hyperparameters (max depth, learning rate, num estimators, L2, subsample) tuned via random search.

Both models undergo identical hyperparameter search (20 trials each) on the validation split using the primary metric. The best-performing candidate from each model class is selected for test evaluation. This ensures a fair comparison: both receive equivalent tuning effort and data access.

### 6. Evaluation Metrics

**Primary metric:** Area Under the Precision-Recall Curve (AUPRC). Fraud incidence is low and can vary across claim types and calendar periods, so the primary comparison will emphasize overall ranking quality across the full score range rather than a single threshold tied to a particular staffing configuration. This provides a stable basis for selecting between the transformer and the baseline while remaining appropriate for imbalanced detection.

**Secondary metrics:** Precision at 5% Recall, Recall at 5% FPR, calibration (ECE), and fairness checks (precision and recall stratified by claimant age, state, and claim type). Precision at 5% Recall is retained as an operating-point metric to characterize how each model behaves under constrained investigator capacity.

### 7. Model Selection and Test Evaluation

Model selection occurs on the validation split using AUPRC. The test set is touched once, at the end, after the final model is locked. All reported results (primary and secondary metrics) come from the test set and are the ground truth for comparison.

### 8. Controls for Confounding

Temporal splitting prevents the transformer from exploiting post-label investigator notes or missingness artifacts. Identical feature information (same event logs and history available to both models) ensures gains come from sequence modeling, not data exclusivity. Stratification by claim type ensures comparable distributions across splits. Fairness stratification detects if gains concentrate in subgroups where label availability or claim patterns differ, signaling confounding. The shared, controlled verification bias (both models see only labeled claims) is acceptable because it does not advantage one approach over the other.

### 9. Claims and Limitations

This experiment will establish whether a transformer with sequence information outperforms a tuned gradient-boosted baseline on this specific insurer's resolved, investigated claims over an 18-month period. It does not establish causation (that sequence structure inherently captures fraud); performance gains may reflect the transformer's capacity to learn from richer information in this domain. The experiment is limited to investigated claims, so generalization to the full claim population (including uninvestigated claims with unknown labels) is not addressed and would require a separate evaluation framework.

---

## eval_scenario_250
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Structured EHR vs. Structured + Notes for Sepsis Shock Prediction

### 1. Data Source and Label Definition

We would use 4 years of hospital EHR data (2020–2023) from a single large academic medical center, encompassing all ICU and ED encounters. The dataset includes timestamped vitals (heart rate, blood pressure, respiratory rate, temperature, SpO2), laboratory values (lactate, creatinine, WBC, platelets, bilirubin, CRP/procalcitonin), medications (antibiotics, vasopressors, sedatives), diagnoses, procedures, and free-text nursing notes. We expect 50,000–80,000 eligible encounters with sepsis incidence of 5–15%.

Septic shock outcomes are defined using a composite criterion: (1) ICD-10 diagnosis code R65.21 (septic shock), OR (2) vasopressor initiation (norepinephrine, dopamine, epinephrine, phenylephrine) on or after the prediction time, AND (3) blood culture or antibiotic order within ±6 hours. To address label noise from treatment-induced bias, we also evaluate a secondary "strict clinical" definition using only physician-documented septic shock diagnosis, independent of treatment timing. Performance must be consistent across both definitions to support the hypothesis.

### 2. Temporal Split and Leakage Prevention

We split the data chronologically to prevent leakage:
- **Training set:** 2020–06-2022 (24 months, ~60%)
- **Validation set:** 2022-07–2023-02 (8 months, ~20%)
- **Test set:** 2023-03–2023-12 (10 months, ~20%)

Encounters are the unit of analysis (not individual time points) to avoid patient-level information leakage. Within each temporal cohort, we stratify by sepsis label prevalence to maintain balanced class distributions. All features are lagged ≥6 hours before the outcome window closes; no future information enters any model.

### 3. Feature Engineering and Preprocessing

We construct two parallel feature sets:

**Feature Set A (Structured-only baseline):** vital sign trends (baseline value + 2-hour delta and slope), baseline labs, medication flags in prior 2 hours, acute diagnosis counts, admission source, age, sex, and comorbidity burden (Charlson score). Note volume is included as a feature to allow the baseline to compete on acuity signals.

**Feature Set B (Structured + Notes):** all of Feature Set A plus embeddings from nursing notes charted in the prior 2 hours. Notes are preprocessed to remove timestamps and identifiers, then embedded using a frozen pre-trained clinical BERT model (e.g., ClinicalBERT). Embeddings are reduced to 50 principal components via PCA to control dimensionality. Missing notes are represented as zero vectors.

All preprocessing transformers (scalers, imputation, encoders, PCA, BERT tokenizer) are fit exclusively on the training set and applied to validation and test sets. This ensures deployment-realistic preprocessing and prevents leakage.

### 4. Model and Baseline

We train a gradient boosting classifier (XGBoost or LightGBM) on each feature set using identical hyperparameter search space: learning rate ∈ {0.01, 0.05, 0.1}, max depth ∈ {3, 5, 7}, min child weight ∈ {1, 5}, and lambda ∈ {0.1, 1}. Both models receive equal tuning budget and computational resources. The structured-only model (Feature Set A) is the baseline; the hypothesis tests whether adding notes improves the otherwise identical model. The baseline is fair because it uses the same architecture and optimization protocol.

### 5. Model Selection

Hyperparameter tuning is performed via 5-fold cross-validation within the training set, optimizing for AUROC. Preprocessing is fit separately within each fold to prevent leakage. The hyperparameters that maximize median cross-validation AUROC are selected, and a candidate final model is retrained on the full training set. The validation period is then used to confirm reproducibility and diagnose train-val drift. To reduce the chance of locking in a configuration that is specific to a single intermediate time window, we then run one final stability check on the later test-period holdout before finalizing the specification for reporting.

### 6. Evaluation Metrics

The primary metric is **AUROC on the test set**, which measures discrimination across all thresholds and is robust to label imbalance. Because clinical utility depends on actionable alerts, we also measure **precision at 80% sensitivity** (the threshold at which the model catches ≥80% of true septic shock cases). Comparison: does structured + notes achieve higher AUROC and higher precision at this fixed operating point?

Secondary metrics include: AUPRC (appropriate for imbalanced data), calibration curve and ECE (ensuring predicted probabilities are trustworthy), and decision curve analysis (net benefit over default strategies).

### 7. Confound Controls

**Documentation bias:** Note volume is included as a feature in both models. We perform a stratified sensitivity analysis across quartiles of note volume to confirm the benefit from notes is not driven solely by high-documentation encounters.

**Acuity selection effects:** Both models include comprehensive acuity features (vitals, labs, comorbidity). We conduct propensity score matching to compare models within balanced acuity subgroups, ensuring gains are not artifacts of acuity confounding.

**Label definition robustness:** We evaluate both the composite vasopressor-based and strict physician-documented definitions independently. Consistent findings across definitions strengthen the claim.

**Treatment-induced bias:** We perform a subgroup analysis excluding encounters with antibiotics started <1 hour before prediction, testing whether findings hold in settings where shock progression has not been artificially suppressed.

All analyses are pre-specified in a Statistical Analysis Plan (SAP) registered before test set evaluation. After cross-validation within the training set determines the candidate hyperparameters, the held-out validation and test periods are used sequentially to verify that the selected configuration is stable under later clinical practice patterns before finalizing the model specification. Once the specification is confirmed, the final structured-only and structured + notes models are retrained on the combined pre-test data and evaluated on the test set to report AUROC, AUPRC, precision at 80% sensitivity, calibration, and decision curve metrics, with 95% bootstrap confidence intervals and DeLong's test p-values for pairwise comparisons.

---

## eval_scenario_496
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer-Based Email Threat Detection with Thread Context

### 1. Data Strategy

The experiment uses 18 months of production email data from a large enterprise mail gateway. This includes complete message bodies, subject lines, thread/conversation history (preserved as chronologically ordered quoted replies), sender and recipient headers, URL counts, attachment metadata, and binary labels assigned by the security operations center (SOC) during triage or post-incident investigation. Labels are operationally generated: an email is labeled phishing = 1 if the security team classified it as a phishing attempt, spear-phishing attack, business email compromise, credential harvest, or similar malicious social engineering; otherwise benign = 0.

To avoid censoring bias, only emails with a label assigned within 30 days of arrival are included in the analysis. This window is pragmatic: it captures timely SOC decisions while excluding emails that may never be reviewed (and thus may have a hidden true label). Label prevalence is expected to be 1–3%, reflecting the rarity of phishing in enterprise environments.

### 2. Split Strategy: Conversation-Based Temporal Split

Emails are grouped into conversations using message-ID chains and in-reply-to headers. Each conversation is assigned the timestamp of its first message. Conversations are then divided chronologically: the first 12 months of first-message timestamps form the **training set**, months 13–15 form the **validation set**, and months 16–18 form the **test set**.

**Why this method is appropriate**: Temporal ordering reflects real deployment—the model must generalize to future emails. Conversation-level grouping prevents data leakage: replies, forwards, and quoted messages within a single conversation all stay in one set, preventing near-duplicates from appearing in both train and test. This is critical because a naive random split might place the original phishing email in training and its forwarded copy in the test set, artificially inflating performance. Conversation-level grouping eliminates this confound.

### 3. Feature Engineering

**Transformer model input**: The full email body, subject line, and complete thread history (all prior messages in the conversation, in chronological order with sender identification preserved) are concatenated and tokenized. Input is truncated to 512 tokens to respect memory constraints and ensure reasonable latency.

**Baseline input**: Shallow features only: sender domain reputation (from a static threat intelligence feed fit only on training-set senders), recipient count, external-recipient flag, subject and body length in characters, number of URLs, attachment count, sender-domain-to-recipient-domain mismatch, and gateway reputation scores. These features encode no information about the email body's semantic content.

All preprocessing (tokenizer vocabulary, scaler fitting) is fit on the training set only and applied without modification to validation and test sets. No hand-crafted phishing-keyword lists or label-leaked features (e.g., "contains 'verify your password'") are used.

### 4. Model and Baseline

**Model**: BERT or a similar pretrained transformer (fine-tuned on the training set) with a binary classification head. Hyperparameters (learning rate, dropout, batch size, epochs, gradient accumulation) are tuned on the validation set via grid or random search. Early stopping monitors validation PR-AUC.

**Baseline**: Logistic regression on the shallow feature set, with equivalent tuning effort. L1/L2 regularization weight and class-weight balancing are tuned on the validation set to maximize the same primary metric. This baseline represents current industry practice—metadata and shallow heuristics—so the improvement (if any) can be attributed to the additional signal from the full email body and thread context, not to model class (neural vs. linear).

### 5. Evaluation Metrics

**Primary metric**: PR-AUC on the test set. Because phishing prevalence is expected to be only 1–3%, the evaluation will emphasize performance in the region where positive predictions are surfaced to analysts rather than average behavior over the entire benign-heavy population. PR-AUC captures how precision changes as recall increases, making it a useful summary of how well the model concentrates true phishing cases near the top of the review queue.

**Secondary metrics**:
- Recall at FPR = 1%, 2%, 5% (operationally actionable: what fraction of true phishing is detected when false alarms are capped?)
- AUROC
- Calibration (Brier score, expected calibration error) to verify predicted probabilities are reliable for threshold tuning
- Stratified AUROC by sender domain frequency (novel senders vs. high-volume senders)

### 6. Validation and Model Selection

All hyperparameter tuning and early stopping use the validation set only, with PR-AUC as the model-selection criterion. The test set is locked until final evaluation and is touched exactly once. No threshold tuning or metric inspection occurs on the test set during development. Final results are computed on the test set without resampling or further iteration.

### 7. Confound Controls

Three confounds are monitored:
1. **Message length**: AUROC is stratified by message length bins. If the transformer gains advantage only for long messages, this suggests it is simply seeing more text, not better phishing understanding.
2. **Thread depth**: AUROC is stratified by thread size (singleton, 2–5 messages, >5 messages) to check that improvements are not artifacts of duplication in long threads.
3. **Sender novelty**: AUROC is separately computed for senders seen in training vs. novel senders to verify generalization and detect memorization.

Additionally, Pearson correlations between predicted probability and message length / thread depth are computed on the test set. If spurious dependences are large, investigation is warranted before claiming the transformer has genuinely learned better phishing detection.

### Expected Outcome

If the hypothesis is correct, the transformer model's test PR-AUC will exceed the baseline's PR-AUC meaningfully, and this improvement will hold across all confound-stratified subgroups. Recall at low false-positive rates will also improve. If improvements vanish when controlled for message length or thread depth, the hypothesis is not supported—the model is exploiting confounds, not learning better semantics.

---

## eval_scenario_411
**Category:** critique | **Difficulty:** hard | **Correct position:** critique_wins

## Experiment Design: Survival Model for ED Same-Day Return Prediction

### Objective
Test whether a survival model (Cox proportional hazards) that explicitly models time-to-event and censoring outperforms a standard binary logistic regression baseline in predicting 72-hour ED return risk. The hypothesis posits that survival modeling will improve performance especially for patients with incomplete follow-up, and will provide better calibrated risk estimates for clinical decision-making.

### 1. Data Source and Outcome Definition
We would use 24–36 months of historical ED encounters from a multi-hospital health system, including all patients discharged from the ED with no exclusion by age, acuity, or chief complaint. Data elements include: triage vitals, administered medications, laboratory results, diagnoses and chief complaint (both structured codes and free text), discharge timestamps, and linkage to any ED return visit within 72 hours via encounter records and regional health information exchange.

The outcome is defined as time-to-event: patients are followed for up to 72 hours from discharge. An event (Y=1) occurs if the patient presents to any ED in the system within 72 hours. Patients are right-censored at 72 hours if no return is observed. Administrative censoring applies to patients who leave the system or have incomplete follow-up; these are retained in the cohort (not excluded) with follow-up time T = time until censoring. Follow-up time T ranges from 1 hour (minimum observable window) to 72 hours; patients are stratified into quartiles for split balance.

### 2. Data Quality and Known Confounds
We would mitigate several known issues: (1) Right-censoring is explicit in the survival model framework; the binary baseline will not have access to censoring information, making its comparison fair and diagnostic. (2) Hospital-level variation in documentation and revisit coding is addressed via stratified splits ensuring all sites are balanced across train/val/test, and post-hoc stratified evaluation by site. (3) Post-discharge event definitions are standardized across sites and validated against claims data; a chart review audit on 50 randomly selected visits per site confirms no post-discharge information leaked into features. (4) Triage note text quality is assessed via NLP validation on a 100-visit sample per site.

### 3. Train/Validation/Test Split
We would use a stratified temporal split: (1) Discharge timestamps are ordered chronologically. (2) Within each hospital site and follow-up-time quartile, visits are randomly allocated to train (60%), validation (20%), and test (20%). (3) No patient appears in multiple splits. (4) To further reduce leakage, validation and test sets use later discharge dates than training (e.g., train: months 1–16, validation: 17–24, test: 25–36, applied within each site-quartile stratum). This design ensures that all models predict into the future relative to their training window, preventing information leakage and ensuring the test set is truly held out.

### 4. Feature Engineering and Preprocessing
We would construct features in two phases:

**Phase 1 (fit on training data only):** Scaling parameters (mean, std), categorical encodings (vocabulary for diagnoses and medications), imputation rules (e.g., median lab values), and NLP vectorization (TF-IDF or embeddings) are fit on the training set.

**Phase 2 (apply to all splits):** Using fitted parameters, we would construct: aggregated vitals (mean, min, max, missingness over the ED visit), medication indicators by therapeutic class, lab summaries (abnormal flags, counts), chronic and acute condition counts from diagnosis codes, triage note embeddings (50–100 dimensions), demographics (age, sex, insurance), prior ED visit history (count in past 12 months), discharge disposition, site identity, visit hour/day-of-week, and length of stay.

Critically, no features include post-discharge information, outcome-correlated signals, or test-set-derived statistics. All features are standardized to zero-mean, unit-variance using training-set parameters.

### 5. Models and Baseline
**Primary model:** Cox proportional hazards regression. This model directly ingests follow-up time T and event indicator Y, producing a log-hazard score and horizon-specific risk estimates. L2 regularization strength λ is tuned on the validation set by minimizing 72-hour Brier score.

**Baseline:** Logistic regression on the same feature set, with outcome recoded as binary 72-hour return status (Y ∈ {0, 1}), ignoring T and censoring. Hyperparameter (L2 strength) is tuned on the validation set by minimizing 72-hour Brier score. The baseline receives equal tuning effort and uses identical preprocessed features, ensuring a fair comparison that isolates the benefit of time-to-event modeling.

### 6. Evaluation Metrics
**Primary metric:** Brier score at 72 hours on the test set. This measures mean squared error between predicted 72-hour return probability and observed outcome, using the survival model's horizon-specific risk estimate for censored data handling. It aligns with the clinical goal of producing actionable absolute risk estimates for discharge planning, where both calibration and discrimination matter. Lower values indicate better performance.

**Secondary metrics:** (1) Calibration curve (predicted vs. observed 72-hour return rate by risk decile). (2) Time-dependent AUC at 24, 48, 72 hours. (3) Concordance index (C-index) as a complementary ranking metric. (4) Performance metrics stratified by follow-up time quartiles (to verify the survival model advantage holds across short vs. long follow-up). (5) Performance metrics stratified by hospital site. (6) Sensitivity and specificity at the F1-optimized threshold for clinical operationalization.

### 7. Model Selection and Test Set Use
Hyperparameters are tuned on the validation set only. Both models are then retrained on the combined train + validation sets using selected hyperparameters, and evaluated once on the held-out test set. The test set is never accessed during tuning, training, or model debugging and is held in reserve until final evaluation.

### 8. Expected Outcome and Scope
If the survival model achieves meaningfully lower 72-hour Brier score than logistic regression on the test set, and maintains the advantage across all follow-up time quartiles, this would support the hypothesis that survival modeling improves return prediction. However, the experiment would not establish whether the advantage is due to (a) better censoring handling, (b) longer effective feature windows, or (c) improved model flexibility. Post-hoc ablation studies (e.g., retraining logistic regression on full T values as a continuous feature, or binning patients by follow-up quartile) would be required to isolate mechanism.


---

## eval_scenario_578
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer vs. XGBoost for 30-Day Readmission Prediction

### 1. Data and Labels
We would use 36 months of retrospective inpatient admission data from the multi-hospital health system, targeting 50,000–100,000 admissions to ensure statistical power and sufficient positive cases (expected readmission rate 15–20%). Data includes all structured EHR fields (demographics, diagnoses, medications, labs, procedures, utilization history) and unstructured clinical notes (discharge summaries, progress notes) captured during the hospitalization. The binary outcome is 30-day unplanned readmission: any inpatient admission to any hospital in the system within 30 days of discharge, excluding planned readmissions (identified via admission type and scheduling codes), transfers, and observation stays. Labeling is performed by clinical informatics staff with physician validation on 5% of cases to detect systematic miscoding.

### 2. Temporal Split Strategy
To prevent leakage of future clinical information and reflect realistic deployment, we employ a strict chronological split at the admission level: months 1–24 for training, months 25–30 for validation, and months 31–36 for held-out testing. Within each set, we stratify by hospital site and readmission status to ensure proportional representation and reduce site-specific confounding. This temporal approach is critical because readmission risk must be predicted at discharge using only information available at that time; a random split would allow models to observe patterns in future data, inflating estimated performance.

### 3. Features and Preprocessing
Structured features include: demographics (age, sex, race), admission type, insurance, prior 30- and 90-day admission counts, Elixhauser comorbidity indicators (derived from ICD-10 codes at admission), pre-discharge labs (creatinine, hemoglobin, glucose, BNP, troponin), medication counts by therapeutic class, procedure indicators, length of stay, and discharge disposition. Unstructured features are generated by encoding discharge summaries and progress notes using a pre-trained clinical BERT model, producing a 768-dimensional contextual embedding. To control for confounding by documentation density, we explicitly include note word count and average note length as features and report them in feature importance analysis.

All preprocessing transformations—scaling, categorical encoding, imputation—are fit on the training set only and applied without refitting to validation and test sets. The XGBoost baseline receives only structured features; the transformer receives both structured features and note embeddings, isolating the contribution of unstructured text.

### 4. Models and Baseline
The transformer model concatenates structured features with note embeddings and passes them through a 2-layer feed-forward network (512 → 256 → 1, ReLU, dropout=0.2) with sigmoid output, trained via binary cross-entropy with early stopping on validation Brier score. XGBoost is trained on structured features only with equivalent hyperparameter tuning effort (random search over max_depth, learning_rate, n_estimators, etc., optimized on validation Brier score). Both models are trained on the same 24-month window and evaluated identically, ensuring a fair comparison between the established baseline (structured EHR alone) and the proposed approach (transformer + text).

### 5. Model Selection and Validation
Hyperparameters for both models are tuned on the validation set (months 25–30) using 5-fold temporal cross-validation within that window, with each fold respecting temporal order. The metric is validation Brier score. Once hyperparameters are locked, models are trained on the full training set and evaluated once on the test set without any further tuning or threshold adjustment.

### 6. Evaluation Metrics
Primary metric: Test set Brier score, chosen because discharge planning decisions depend on the reliability of estimated readmission probabilities across risk bands, not just on relative ordering. This makes probability accuracy central to the intended use case of allocating transitional care resources to patients above specific risk levels. Secondary metrics include calibration (Expected Calibration Error, calibration plots by risk decile), sensitivity/specificity at clinically relevant thresholds (e.g., 90% specificity to minimize false positives), and stratified AUROC by multimorbidity burden and hospital site to test whether the transformer advantage holds across populations and sites. We also assess note length effects to disentangle information density from modeling superiority.

### 7. Controls for Confounding
To address documentation confounding, note word count is included as an explicit feature, and model performance is stratified by note length quartile. To control for site-specific practice variation, each site is represented proportionally in train/val/test splits, and test AUROC is computed per site to detect generalization gaps. Label noise from miscoding is mitigated via consistent labeling rules applied uniformly across all sets; sensitivity analyses repeat evaluation after excluding ambiguous cases. Temporal leakage is prevented by anchoring all features at discharge time and excluding any post-discharge clinical data.

### 8. Scope of Claims
This design would establish whether a transformer-based encoder, given access to unstructured discharge summaries and progress notes, produces more accurate discharge-time readmission risk estimates than XGBoost on structured features alone for 30-day readmission prediction in this health system. It would not establish whether the improvement is due to superior NLP representation vs. simple information density, whether the finding generalizes to other health systems or note types, or whether the improvement translates to clinical benefit when deployed (that requires a prospective intervention trial). Stratified analyses would clarify whether benefits are concentrated in complex patients and whether site-specific confounds drive any observed difference.

---

## eval_scenario_685
**Category:** critique | **Difficulty:** hard | **Correct position:** critique_wins

## Experiment Design: Dense Bi-Encoder vs. BM25 for Legal Case-Law Search

### 1. Data and Labeling Strategy

The experiment uses production query logs, clicks, and dwell times from a commercial legal research platform spanning 36 months (January 2021–December 2023). The searchable corpus contains approximately 10 million federal and state court opinions, statutes, and headnotes with continuous ingestion of new documents.

**Implicit labels** are derived from user interactions: a document is considered relevant for training purposes if it received a click from a user and dwell time exceeded 30 seconds, and the document appeared in the top 20 search results at the time of interaction. This restriction to top-20 positions mitigates position bias, since users are more likely to examine documents ranked higher.

**Explicit labels** come from a curated set of ~50,000 query-document pairs that have been manually judged by legal domain experts on a 5-point relevance scale (not relevant, somewhat, relevant, highly relevant, perfect match). These explicit judgments serve as the ground truth for all test-set evaluation and are stratified by query type (case name lookup, citation search, topical search) and document age (≤1 year, 1–5 years, >5 years) to ensure comprehensive coverage.

### 2. Train / Validation / Test Split Strategy

The split uses a **temporal strategy with query-level and user-level stratification** to prevent leakage and reflect the deployment context, where the model must generalize to new documents and new user queries.

- **Training set**: Months 1–24 (Jan 2021–Dec 2022). Implicit labels from user clicks in this window are used to fine-tune the dense model.
- **Validation set**: Months 25–30 (Jan–Jun 2023). Used for hyperparameter selection and model selection only (locked from final reporting).
- **Test set**: Months 31–36 (Jul–Dec 2023). Held untouched until the end; all final metrics are reported on this set using explicit relevance judgments.

No documents with publication dates after December 31, 2023 are included in any split. Within each time window, queries are stratified by query type and document age category to ensure balanced representation across conditions (e.g., fresh vs. older cases). Critically, no query and no user appears in more than one split, eliminating user-specific or session-specific leakage.

### 3. Feature Engineering and Preprocessing

All preprocessing is fit on the training set and applied identically to validation and test sets.

**For the dense bi-encoder model:**
- Queries and documents are tokenized using a frozen BERT tokenizer fitted on training data.
- Raw signals include query length, document length, days since publication, citation count, court tier, and document type.
- Document representations are pre-computed BERT embeddings (768-dimensional).
- During fine-tuning, hard negatives are mined from documents ranked 1–10 by BM25 but not clicked by users, and in-batch negatives from non-clicked documents in the same query's result set.

**For the BM25 baseline:**
- Standard TFIDF weighting; Okapi BM25 parameters k1 and b are tuned via grid search on the validation set but not modified afterward.
- No dense representations or semantic features are used by BM25.

### 4. Model and Baseline

**Dense model**: BERT-base (12 layers, 768 dims) with separate query and document encoders, fine-tuned end-to-end on training-set implicit labels using batch hard triplet loss with in-batch negatives. Training uses 3 epochs, batch size 128, learning rate 2e-5 with linear warmup. At inference, approximate nearest neighbor search (FAISS with 8-bit quantization) retrieves the top 100 candidate documents by cosine similarity in embedding space.

**Baseline**: Sparse BM25 retrieval with Okapi BM25 parameters (k1, b) tuned on the validation set via grid search. k1 ∈ [1.2, 1.5, 1.8, 2.0], b ∈ [0.5, 0.75, 0.9]; the pair maximizing validation nDCG@10 is selected and fixed for testing. BM25 is a fair baseline because it receives equal tuning effort, uses the same document index, and is evaluated under identical conditions.

### 5. Evaluation Metrics

**Primary metric: nDCG@10** (computed on the explicitly judged test set using the full 5-point relevance scale). This metric reflects the fact that, in legal research, not all relevant authorities are equally useful: a perfect-match controlling case should count more than a marginally relevant one. By emphasizing graded relevance at shallow rank, nDCG@10 captures whether the system places the strongest authorities near the top of the first results page, which is where users make their initial retrieval decisions.

**Secondary metrics:**
- **Recall@10**: Measures binary coverage of relevant authorities in the first 10 results.
- **Recall@50**: Tests whether gains generalize beyond the top 10 or are narrowly confined.
- **MRR**: Mean reciprocal rank of the first relevant result; captures user experience of speed-to-success.
- **Per-subset Recall@10 and nDCG@10**: Computed separately on (1) low-overlap queries (Jaccard <0.2, testing paraphrasing), (2) old documents (>5 years, testing older-case retrieval), and (3) ambiguous queries (multiple relevant documents), to confirm the hypothesis is not driven by confounds.

### 6. Validation and Model Selection

Model selection is performed on the validation set using nDCG@10 as the selection criterion. Multiple checkpoints of the dense model are trained with different hyperparameter configurations; the checkpoint with the highest validation nDCG@10 is retained. BM25 parameters are similarly tuned on validation nDCG@10. Both models are then run inference on the locked test set exactly once, with no further modification.

### 7. Confound Controls

The design accounts for known confounds:

1. **Position bias**: Implicit training labels exclude documents ranked >20; test metrics use unbiased explicit judgments.
2. **Popularity / recency bias**: Separate metrics on old vs. new documents and low vs. high-citation documents detect whether the dense model learns meaningful semantics or merely popularity.
3. **Query intent ambiguity**: Metrics computed separately on single-relevant vs. multi-relevant queries.
4. **Temporal drift**: Forward-looking test set (months 31–36) includes new documents the model has never encountered, testing true generalization.
5. **User leakage**: Train/val/test splits at the user level eliminate user-specific patterns.

### 8. Scope of Claims

This design will establish whether a dense BERT-based bi-encoder, fine-tuned on production click data, achieves better ranking quality and top-10 retrieval coverage than tuned BM25 on the test query-document pairs. It will further show whether this advantage holds for paraphrased queries and older cases. It will *not* establish whether the gain is due to semantic understanding vs. other factors (popularity, recency, corpus statistics); per-subset analyses help distinguish these, but a critic could argue that confounds remain. It will not test performance on out-of-distribution queries (e.g., from a different legal practice area) or on a different platform, limiting generalizability claims.

---

## eval_scenario_380
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Session-Sequence Ranker vs. Baseline on E-Commerce Marketplace Data

### 1. Data and Labeling

The experiment uses 18 months of production search logs and clickstream data from the marketplace. Each record contains: query text, item identifiers, item metadata (category, price, rating, historical metrics), user/session context, impression timestamp, position on the results page, and engagement outcomes (click, add-to-cart, purchase within 7 days).

Two weak labels are derived: (1) binary click label, indicating whether the user clicked the item in that impression session, and (2) binary purchase label, indicating whether the user purchased the item within 7 days. These labels are used as ground truth during training and evaluation. Critically, labels are derived from raw logs without any correction applied at the label level; position bias is instead handled during metric computation.

### 2. Temporal Split Strategy

Data is split chronologically: months 1–12 form the training set, months 13–15 the validation set, and months 16–18 the held-out test set. 

This temporal split is mandatory for three reasons. First, the task has inherent temporal dependence—item popularity, user preferences, and relevance change over time. A random split would violate this structure and produce overoptimistic estimates. Second, the hypothesis explicitly concerns performance on "future traffic"; a chronological split is the only way to faithfully represent deployment conditions where the ranker must handle unseen future queries and items. Third, chronological splits prevent leakage from future popularity signals and repeated exposure effects—in a random split, the model would see items' full life cycle popularity before training, an advantage not available at serving time.

Within each temporal split, stratification is applied by query frequency category (head, mid, tail) to ensure balanced representation across query difficulty levels. This avoids the risk that one split becomes dominated by head queries (which are easier to rank and artificially inflate metrics).

### 3. Feature Engineering

**Baseline features:** Item metadata (category, price, rating, review count), static popularity percentile rank, and recency signals (days since last price change).

**Proposed features:** (1) Query-item semantic similarity computed from dual-encoder embeddings (query-side BERT and item-description BERT, fixed pretrained models, not tuned on this dataset); (2) Session-level behavioral sequences: the user's last 5 clicked items encoded as a sequence of item embeddings, aggregated metrics (mean rating of clicked items, click count so far in the session, session dwell time, recency-weighted click times); (3) User-normalized features (user's historical click rate on items in this category, user's historical purchase conversion rate).

All preprocessing transformers (scalers, tokenizers, embedding models) are fit on the training split only and applied identically to validation and test. Session aggregation logic is deterministic and does not leak information. No feature incorporates data from the test time window or future signals.

### 4. Model and Baseline

Both the proposed and baseline models use a learning-to-rank architecture: LambdaMART or a neural ranking model (e.g., transformer-based listwise ranker optimizing the validation objective). 

The **baseline** is a ranker of identical architecture trained exclusively on baseline features. Critically, the baseline receives equivalent tuning effort: the same validation procedure, the same hyperparameter search budget (over learning rate, regularization, tree depth), and the same optimization metric during model selection. This ensures that any performance difference is attributed to the information content of session sequences and semantic embeddings, not to differences in model complexity or tuning rigor.

### 5. Primary and Secondary Metrics

**Primary metric:** Position-bias-corrected AUROC over impressed query-item pairs, computed using inverse propensity weighting (IPW). 

This metric is chosen for three reasons: (a) the labels are weak and sparse at the item level, so AUROC provides a stable discrimination measure even when positive events are concentrated in a small fraction of impressions; (b) AUROC supports consistent comparison across query-frequency strata and item-age buckets, which is important because the hypothesis includes generalization beyond head queries and mature inventory; (c) IPW correction mitigates position bias—items ranked higher receive more impressions and clicks in the logged data regardless of true relevance, so raw observed outcomes would confound model quality with exposure. IPW reweights observations by the inverse of their probability of being impressed at that position, producing a less exposure-driven estimate of discrimination quality.

**Secondary metrics:** NDCG@10, mean reciprocal rank (MRR) of the first clicked item, purchase-weighted NDCG@5 (for purchase impact), stratified AUROC across query frequency categories, item coverage (fraction of unique items in top-5 results across test queries), and position bias diagnostics (correlation between predicted rank and observed click rate, which should decrease under an unbiased ranker).

### 6. Model Selection and Validation

Hyperparameter tuning is performed exclusively on the validation set (months 13–15). For each hyperparameter configuration, the primary metric is computed on the validation set; the configuration achieving the best validation metric is selected. The test set is not examined during model selection and is touched only once, at the end, to compute final results and report confidence intervals via bootstrap resampling over test queries.

### 7. Confound Controls

Position bias is handled via IPW in metric computation, not by modifying data or labels. Temporal feedback loops and repeated exposure effects are eliminated by the chronological split—test queries occur strictly after training, so no future popularity or exposure signals leak into training. To verify that improvements come from sequence modeling rather than better exploitation of popularity features, the baseline receives the same static popularity signals, ensuring that any difference must come from semantic embeddings or session sequences. Cold-start items and tail queries are explicitly analyzed to confirm generalization. User/session effects are controlled by including session ID in both models. Performance is reported stratified by query category to detect any concentration of gains on head queries versus balanced improvement across query types.

---

## eval_scenario_162
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Hierarchical Transformer vs. TF-IDF Baseline for Multi-Label ICD-10 Coding

### 1. Data Collection and Preparation

We would use 4 years of de-identified inpatient encounter records (e.g., 2019–2022) from a multi-hospital health system, targeting 150,000–300,000 admissions. Each encounter includes a discharge summary, up to 10 progress notes timestamped before the discharge summary creation time, and the finalized coder-assigned ICD-10-CM diagnosis codes from the billing workflow. Encounters with missing discharge summaries, stays under 24 hours, or post-discharge amended coding are excluded. Only ICD-10-CM diagnosis codes appearing at least 10 times in the training split are included in the evaluation label set, partitioned into frequency tiers (frequent: ≥500, mid: 50–499, rare: 10–49) at label construction time to support stratified reporting.

### 2. Split Strategy

The data is split strictly by encounter discharge date: years 1–2 form the training set (~50%), year 3 forms the validation set (~25%), and year 4 is the held-out test set (~25%). This temporal split is essential because the deployment scenario requires generalization to future encounters where coding practice, documentation patterns, and case mix evolve over time. A random split would allow interpolation between temporally adjacent encounters and would underestimate real-world degradation. To prevent patient-level leakage, any patient with encounters spanning a split boundary has all their encounters assigned to the later split.

### 3. Feature Engineering and Preprocessing

Both models receive identical input: the discharge summary concatenated with up to 10 chronologically ordered progress notes (pre-discharge only), delimited by section-boundary tokens. Three metadata features — total character count, number of available notes, and hospital site — are recorded but deliberately withheld from model input; they are used exclusively for post-hoc confound analysis. All preprocessing (TF-IDF vocabulary, IDF weights, label binarizer) is fit on the training split only and applied frozen to validation and test. Transformer tokenization uses a fixed vocabulary from the pretrained ClinicalBERT checkpoint, with any added section tokens defined before fine-tuning begins.

### 4. Models and Baselines

The proposed model is a hierarchical transformer: ClinicalBERT fine-tuned as a segment encoder (max 512 tokens per segment), with a cross-attention document aggregation layer and a sigmoid multi-label head trained with logit-adjusted binary cross-entropy to address label imbalance.

The baseline is TF-IDF (sublinear, unigrams + bigrams, up to 300k features) with one-vs-rest calibrated LinearSVC. The baseline receives the same concatenated text, the same label set, and equivalent hyperparameter search effort on the same validation split and metric. Per-label prediction thresholds are tuned independently on the validation set using per-label F1 maximization for both models — ensuring the baseline is not penalized by a fixed threshold assumption.

### 5. Evaluation Metrics

The primary metric is micro-F1 over all codes meeting the frequency threshold, computed after threshold tuning. Micro-F1 is appropriate here because it summarizes overall coding accuracy across the full label space and better reflects aggregate workload reduction in a production coding-assist setting. Secondary metrics include macro-F1, stratified macro-F1 by frequency tier (this directly tests the low-frequency hypothesis claim), macro-AUC-ROC, Precision@5 and Recall@10 for ranked suggestion interfaces, and per-hospital macro-F1 for site generalization assessment.

### 6. Model Selection and Test Set Policy

All hyperparameter tuning, model selection, early stopping, and threshold optimization use only the validation set (year 3), with validation macro-F1 as the selection criterion. The test set is used exactly once after all decisions are finalized. No iterative refinement based on test results is permitted.

### 7. Confound Controls

Three confounds are proactively addressed. First, a post-hoc logistic regression tests whether the transformer's per-encounter advantage over the baseline is predicted by note length or document count; a meaningful AUC (>0.6) would implicate document availability rather than language understanding. Second, per-hospital performance breakdowns detect whether gains are concentrated in one site with idiosyncratic templates. Third, the stratified frequency-tier analysis distinguishes gains on rare codes from gains on frequent codes — only the former supports the core hypothesis. An additional ablation using discharge summary only (no progress notes) isolates the contribution of multi-document aggregation from pretrained language model quality. This experiment would establish whether a hierarchical transformer offers a meaningful accuracy advantage over a strong linear baseline under realistic temporal and cross-site generalization conditions; it would not establish clinical deployment readiness, which requires prospective evaluation and clinician workflow studies.

---

## eval_scenario_484
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Dense Dual-Encoder vs. BM25 for Enterprise Support Retrieval

### 1. Data Collection and Labeling

The experiment uses 36 months of historical support ticket data from the production SaaS environment. The primary data sources are resolved support tickets (customer issue descriptions), help-center articles with metadata, and agent search logs containing queries and clicked articles.

Positive relevance labels are derived from agent click events. An (issue_text, article_id) pair is marked positive if the agent clicked the article during ticket resolution and the ticket was resolved within 24 hours of the click. To mitigate position bias in observed clicks—agents are more likely to click articles ranked higher regardless of relevance—only clicks on articles ranked 3rd or lower in the original result set are treated as positive. This reduces conflation of ranking position with true relevance.

Negative labels are sampled from articles that were available (published before the query date) but were not clicked. The sampling ratio is 1 positive : 4 negatives, stratified by product area. Hard negatives—articles clicked on related tickets in the same product area but not on the current ticket—are included to increase signal and encourage the model to learn fine-grained intent boundaries.

### 2. Temporal Split Strategy

The data is split by query date to prevent information leakage from future articles and product updates. Training spans months 1–24 (24 months of historical data). Validation spans months 25–30 (6-month window for hyperparameter tuning and model selection). The test set spans months 31–36 (6-month hold-out, touched only once at the end).

This temporal split ensures that (a) the model never sees articles published after its training window, mimicking real deployment where new content continuously arrives; (b) validation and test windows are long enough to capture seasonal support patterns and product versioning effects; (c) no information from months 31–36 influences model or hyperparameter selection.

Within each temporal split, data is stratified by product area (e.g., billing, authentication, integrations) to ensure all major product lines are represented proportionally and to enable later stratified analysis.

### 3. Feature Engineering and Preprocessing

Both models (dual-encoder and BM25 baseline) use identical cleaned text. Query features consist of the customer-submitted issue description from the support ticket plus any agent-added keywords, up to 512 tokens. Article features consist of the article title and first 500 characters of body text, also up to 512 tokens. All text is lowercased and cleaned of HTML/markdown markup.

Crucially, acronyms are preserved and not expanded, to avoid injecting domain knowledge that would bias the comparison. All preprocessing (tokenization, vocabulary construction, IDF computation) is fit on the training set only and applied identically to validation and test data. This ensures that the validation and test sets reflect realistic deployment conditions.

### 4. Model and Baseline

**Dual-Encoder Model:** A fine-tuned dense dual-encoder with separate or shared query and article encoders (pre-trained language model, e.g., DPR or DistilBERT). The model is trained on the training set using triplet loss with hard negative sampling. During inference, queries are embedded, and top-k articles are retrieved via dot-product similarity against precomputed article embeddings.

**Baseline: BM25.** The BM25 algorithm (Okapi parameters k1, b, k3) is tuned on the validation set to maximize MRR@10 using the same relevance labels as the dual-encoder. BM25 parameters are fit on the training corpus (IDF statistics computed from training documents) and applied to validation and test queries. BM25 is a proven, strong baseline in information retrieval and receives equal tuning effort as the dual-encoder.

### 5. Evaluation Metrics

**Primary Metric: Mean Reciprocal Rank (MRR@10).** This captures the reciprocal rank of the first relevant article within the top 10 results, averaged across test queries. MRR@10 aligns with the practical workflow the experiment is trying to improve: agents inspect ranked results from the top down, so the benefit of stronger semantic retrieval should appear as earlier placement of the first useful article. This makes the metric sensitive to whether the dense model reduces search friction in the support interface rather than only increasing overlap somewhere within the result set.

**Secondary Metrics:** Recall@10 (coverage within the agent's top-10 browsing window), Recall@5 (stricter success criterion), Precision@10 (ensures gains are not driven by irrelevant retrievals), and Recall@10 stratified by product area (detects whether gains generalize or concentrate in high-volume areas). Additionally, Recall@10 is computed separately on tail queries (queries occurring <5 times in training) and acronym-heavy queries (≥2 acronyms) to directly test the hypothesis's claims about rare intents and acronym handling.

### 6. Model Selection and Validation

Both models undergo hyperparameter tuning on the validation set (months 25–30) using MRR@10 as the selection criterion. A random search or Bayesian optimization over a predefined hyperparameter grid is performed. The configuration maximizing MRR@10 on the validation set is selected for final evaluation. The test set is not touched during this phase.

### 7. Test Set Policy and Confound Controls

The test set (months 31–36) is evaluated exactly once, using the selected models, and all primary and secondary metrics are computed. No retraining or re-tuning occurs after test evaluation.

To address known confounds: (1) Position bias is mitigated by labeling only clicks on articles ranked 3+. (2) Availability bias is eliminated by sampling negatives only from articles published before the query date. (3) Product-area stratification reveals whether improvements are driven by memorization of high-volume areas or genuine semantic gains. (4) Tail-query analysis exposes whether the model generalizes to rare intents or overfits to popular queries. (5) Acronym-heavy query subsets directly test the hypothesis's claim. (6) Hard-negative sampling encourages learning of fine-grained boundaries rather than surface-level similarity.

These controls ensure that any observed improvement in MRR@10 reflects genuine semantic retrieval capability rather than position bias, duplicate-content effects, or memorization of popular queries.

---

## eval_scenario_269
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Sequence Models vs. Tabular Baselines for 30-Day Readmission Prediction

### 1. Data and Cohort Definition

We will use 36 months of administrative and clinical data from a single health system's EHR, spanning all acute care adult inpatient discharges (age ≥18 years). The dataset includes structured encounter records, diagnoses and procedures (ICD/CPT codes), medications, labs, vitals, and free-text clinical notes. We will exclude transfers (readmission risk is undefined), palliative admissions, and patients without ≥1 year of prior EHR history to ensure sufficient longitudinal context.

The outcome is binary: unplanned readmission within 30 days of discharge. This is derived deterministically from encounter timestamps and readmission admission-type flags in the EHR, ensuring consistent labeling across all cohorts.

### 2. Train–Validation–Test Split Strategy

We employ a chronological split on discharge date to prevent leakage from future clinical practice and coding patterns:
- **Training cohort** (months 1–24): used to fit all preprocessing transformers, embeddings, and model weights
- **Validation cohort** (months 25–30): used for hyperparameter tuning and model selection via a single-pass grid or Bayesian search
- **Test cohort** (months 31–36): held out and evaluated only once, at the end, for final performance reporting

This temporal structure ensures the model generalizes to truly future discharge patterns. Post-hoc stratification checks (class balance, demographics, comorbidity distribution) confirm that case-mix is stable across the three time windows, justifying the chronological approach.

### 3. Feature Engineering and Preprocessing

**Sequence model features:**
- Event sequences: timestamped diagnoses (ICD-10), procedures (CPT), medications (RxNorm), lab tests and results, and vitals, ordered chronologically from the index admission back 12 months. Each code is embedded in a learned or fixed clinical vocabulary.
- Clinical note embeddings: discharge summaries, admission notes, and progress notes are embedded using a pre-trained clinical language model (e.g., SciBERT or ClinicalBERT). Embeddings are aggregated per discharge and concatenated into a fixed-size representation.
- Early post-discharge utilization signal: a compact indicator capturing whether the patient has any outpatient follow-up, ED presentation, nurse triage contact, or medication reconciliation event recorded within 7 days of discharge. This serves as a standardized summary of immediate care-transition engagement and is already represented in the EHR event stream.
- Static features: age, sex, comorbidity burden, discharge disposition, service line, ICU flag.

**Baseline features (aggregated only):**
- Count summaries: prior admissions and ED visits (12 months), unique diagnoses, medication count at discharge
- Categorical: service line, ICU flag, discharge disposition, insurance type
- Continuous: age, BMI, admission labs (hemoglobin, creatinine, albumin)
- Clinical summary: Charlson comorbidity index or comorbidity count from diagnoses
- Immediate care-transition context: the same 7-day post-discharge utilization indicator used by the sequence model, to keep non-temporal information aligned across models

Both models receive identical demographic and comorbidity context to ensure fair comparison. All preprocessing transformers (scalers, encoders) are fit on the training set only and applied consistently to validation and test. Missing structured values are imputed using training-set statistics.

### 4. Models and Baseline

**Sequence model:** A Transformer encoder (or GRU/LSTM stack) processes event sequences with attention, concatenated with note embeddings, the early care-transition utilization signal, and static features. The combined representation feeds into a 2-layer dense network (128 units, dropout 0.3) and a sigmoid output for readmission probability.

**Baseline:** A gradient-boosted ensemble (XGBoost or LightGBM) trained on aggregated static and summary features only—no access to sequences or notes. Both models receive identical hyperparameter tuning effort (100–150 random search or Bayesian optimization trials on the validation set). This is the appropriate counterfactual: it represents current practice in many health systems and isolates the value of sequence and note-based modeling.

### 5. Model Selection and Evaluation

Hyperparameter tuning uses the validation cohort exclusively, with early stopping or checkpoint selection based on validation AUC-ROC. The test set is untouched during development and is evaluated only once, at the end, under identical conditions for both models.

**Primary metric:** Area Under the ROC Curve (AUC-ROC), evaluated on the test set. AUC-ROC measures ranking discrimination and is insensitive to class imbalance, directly supporting the operational goal of risk stratification for case management. A clinically meaningful difference is ≥0.03 AUC-ROC (absolute).

**Secondary metrics:** Calibration (Brier score, expected calibration error), sensitivity/specificity at operationally-chosen thresholds, AUC-ROC stratified by comorbidity, ICU status, and service line (confirming benefit is not driven by a single subgroup), and decision curve analysis (net benefit across threshold assumptions).

### 6. Confound Controls and Interpretation Scope

We address known confounds as follows:
- **Utilization intensity and documentation volume:** Secondary analysis correlates sequence model advantage with note length, prior admission count, ICU flag, and immediate post-discharge engagement. If the sequence model is explained by these, we reframe the finding as "better capture of severity" rather than "trajectory modeling value."
- **Service line and case-mix:** Stratified test-set evaluation ensures the sequence model is not driven by a single service.
- **Temporal drift:** Chronological split inherently tests generalization; we monitor train–validation–test AUC trends to check for non-stationarity.
- **Discharge planning and social factors:** Both models have access to discharge disposition codes and note content; a sensitivity analysis restricts to high-quality discharge planning documentation.

### 7. Scope and Claims

This design tests whether sequence models outperform tabular baselines on 30-day readmission discrimination in a single health system over a 3-year window. The results establish relative model performance and generalization to future practice. The design does **not** establish causality of readmission drivers, does **not** prove clinical actionability of the sequence model without intervention studies, and does **not** guarantee generalization to other health systems or populations without external validation.

Confidence intervals (95%, bootstrapped) will accompany all primary metrics.

---

## eval_scenario_180
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Joint Transformer vs. TF-IDF Baseline for ICD-10 Code Suggestion

### 1. Data and Labels

We would use 3.5 years of finalized inpatient encounters (January 2020 – June 2023) from a single large hospital system, targeting approximately 150,000–250,000 admissions after quality filtering. Only encounters with a finalized billed claim, a present discharge summary, and at least one valid ICD-10-CM code are included. Encounters with late-amended codes (amendments filed more than 30 days post-discharge) are excluded to avoid noisy labels. Labels are drawn from the final UB-04 billed codes — not interim coding drafts — and restricted to the top-K ICD-10-CM codes appearing in at least 0.5% of training encounters, typically yielding 200–400 codes. This threshold-based restriction is justified by the need for stable per-code performance estimates; rare codes in the long tail would produce unreliable metrics and are addressed in production through a separate rare-code pathway outside this experiment's scope.

### 2. Split Strategy

The data is split **chronologically and strictly**: training covers January 2020 – December 2021 (24 months), validation covers January – June 2022 (6 months), and the held-out test set covers July 2022 – June 2023 (12 months). Temporal splitting is non-negotiable for this domain: ICD-10 code updates occur annually, documentation practices drift, and a random split would allow future clinical language patterns to contaminate the training distribution. Within each temporal window, patient-level group integrity is maintained — no patient's test-window encounter appears in any prior split in a way that could encode their coding behavior. This prevents a subtle leakage pathway where a prolific patient's coding patterns are memorized from earlier admissions and then credited to the test split.

### 3. Defining the Text Availability Envelope

The most critical design decision is defining exactly which text is available at prediction time. We define the cutoff as: all clinical notes with a creation timestamp strictly before the earlier of (a) the discharge summary finalization timestamp or (b) discharge date + 24 hours. This includes progress notes, consult notes, and the discharge summary itself, but excludes addenda, late consult responses, or coding query documents added after the coder would reasonably initiate their review. Both the transformer and the TF-IDF baseline receive **identical document sets** defined by this rule — this is the central confound control ensuring that any performance gap reflects representation quality and temporal encoding, not differential text access.

### 4. Models and Features

The **transformer model** is initialized from a pretrained clinical language model checkpoint (ClinicalBERT or BioLinkBERT). The discharge summary is the primary input; prior inpatient notes from the same admission are integrated via a hierarchical or sliding-window encoder to handle multi-document inputs. A sigmoid output head with binary cross-entropy loss and positive-class weighting addresses label imbalance. Hyperparameters tuned on the validation set include learning rate ({1e-5, 2e-5, 3e-5}), sequence length/truncation strategy, note pooling method, and loss weighting. Early stopping uses validation macro-F1 with patience of 3 epochs.

The **TF-IDF baseline** receives the concatenation of the same documents as a bag-of-words input (unigrams + bigrams, up to 50,000 features, sublinear TF), paired with a one-vs-rest logistic regression classifier. The baseline receives equivalent encounter metadata features and is tuned with the same validation budget: regularization strength C over {0.01, 0.1, 1.0, 10.0} and class weighting options. This parity of tuning effort and feature availability is essential — an undertrained baseline would inflate the apparent transformer advantage.

An additional **ablation variant** of the transformer — receiving only the discharge summary with no prior note timeline — is trained under identical conditions. This isolates the contribution of joint timeline encoding from general transformer expressiveness.

### 5. Evaluation Metrics

The **primary metric is micro-F1** over the K-label restricted set, evaluated at a fixed threshold of 0.5. Micro averaging provides a stable overall summary across the multi-label output space and reflects aggregate coding performance across all predictions.

Secondary metrics include **Precision@8 and Precision@15** (measuring suggestion list quality directly relevant to coder workflow), **Recall@8 and Recall@15** (coding completeness), macro-F1, per-code F1 distribution, and expected calibration error. Stratified performance by service line is reported as a confound check.

### 6. Validation and Test Discipline

All model selection decisions — including checkpoint selection, architecture choices, and hyperparameter configurations — are made exclusively on the validation set using macro-F1. The test set is touched exactly once, after all decisions are finalized. Results are reported with 95% bootstrap confidence intervals (10,000 resamples at the encounter level) and McNemar's test for statistical significance of the macro-F1 difference.

### 7. Confound Controls and Scope

Three confounds are explicitly controlled. First, **text volume parity** is enforced by the shared timestamp cutoff rule. Second, **encounter complexity** is addressed by stratifying macro-F1 by length-of-stay (≤2 days vs. >5 days) to test whether the timeline encoder's benefit scales with note volume. Third, **service-line mix drift** between training and test windows is assessed via stratified reporting.

If the experiment succeeds, it establishes that joint transformer encoding of discharge summaries and inpatient note timelines outperforms lexical TF-IDF methods for frequent-code prediction under matched-text conditions. It does not establish performance on rare codes, generalizability to other hospital systems, or superiority in real-time coder workflow integration — those would require follow-on studies.

---

## eval_scenario_259
**Category:** critique | **Difficulty:** hard | **Correct position:** critique_wins

## Experiment Design: Session-Level Embeddings for Enterprise Churn Prediction

### 1. Data Collection and Labeling

The experiment uses 24 months of production event logs and CRM metadata from the SaaS platform. The data spans at least 5,000 accounts and includes timestamped product events (feature clicks, page views, workflow completions, errors, invites) at the session level, along with account-level metadata (plan tier, seat count, tenure, renewal dates). 

Churn risk is defined operationally as a material contraction signal within 30 days following an observation window: an account is labeled positive if it downgrades, reduces seat count by more than 50%, or enters a sustained near-zero engagement state over that subsequent period. The label combines subscription events with downstream engagement summaries so that the target captures accounts that have effectively disengaged even when formal renewal status lags in CRM. This definition is intended to align the outcome more closely with emerging account deterioration while retaining clear business relevance.

### 2. Temporal Split with Stratification

Because churn risk evolves over time and the model will be deployed on future data, a chronological split is mandatory to prevent leakage. The data is divided as follows:

- **Training set:** Months 1–12. All preprocessing and model fitting occurs here.
- **Validation set:** Months 13–15. Used for hyperparameter selection and early stopping.
- **Test set:** Months 16–18. Held in isolation and used once at the end to compute final metrics.

Within each split, accounts are stratified by plan tier and tenure cohort (new: <3 months; growth: 3–12 months; mature: >12 months) to ensure balanced representation. This stratification guards against a scenario where the treatment model gains performance simply by learning account maturity rather than churn signals.

### 3. Feature Construction

**Baseline features** (hand-engineered aggregates over a 30-day observation window):
- Event rate (total events, unique feature usage count, session frequency)
- Error event rate, invite event rate
- Days since last login
- Account age (tenure days)
- Plan tier (one-hot encoded), seat count

**Treatment features** (baseline + sequence embeddings):
- All baseline features
- Session-level event sequence embeddings: raw event logs are encoded as sequences of event types and timestamps. A sequence model (shallow LSTM or Transformer encoder) learns embeddings of dimension 32–256, tuned on the validation set. Embeddings capture temporal patterns in user behavior that aggregated statistics discard.

All features are computed over a 30-day window preceding the observation period. No information from the label window itself is included. Preprocessing (scaling, imputation) is fit on training data and applied unchanged to validation and test sets.

### 4. Model and Baseline

Both the baseline and treatment use **logistic regression with L2 regularization**. This choice ensures a fair comparison: the model class is identical, and the only difference is the feature set. Hyperparameter C (regularization strength) is tuned via grid search on the validation set, maximizing the primary metric. The baseline receives equivalent tuning effort and is not handicapped; the comparison isolates the value of sequence embeddings alone.

### 5. Evaluation Strategy

**Primary metric: Precision-Recall AUC (PR-AUC).** The business operates under a fixed intervention budget: the customer success team can outreach to only a limited number of at-risk accounts. PR-AUC measures ranking quality across all possible thresholds and is insensitive to class imbalance. This directly aligns with the operational objective: identifying true churn-risk accounts early, in rank order, so the team focuses effort on the highest-risk accounts. ROC-AUC would be inappropriate here because the abundance of non-churning accounts would inflate scores without informing business impact.

**Secondary metrics:**
- Recall at 80% precision (number of true churn-risk accounts identified while keeping false alarms at 20%)
- Recall in the top 10% of accounts ranked by predicted churn risk
- Expected calibration error (ECE) to verify probability estimates are reliable
- Stratified PR-AUC by plan tier and tenure cohort

### 6. Model Selection and Test Set Isolation

Hyperparameter tuning is performed on the validation set (months 13–15) using grid search. Cross-validation is avoided because it would violate temporal order. The model with the highest validation PR-AUC is selected. The test set (months 16–18) is never accessed during tuning; it is used only once at the end to compute final metrics and 95% confidence intervals.

### 7. Confound Control and Scope

The design includes several checks for confounding:

- **Stratified evaluation:** Metrics are reported for each plan tier and tenure cohort separately. If gains concentrate in a single cohort, this suggests the model learned maturity effects rather than churn signals.
- **Ablation:** A third model trained on baseline features plus explicit age and plan variables (no embeddings) is evaluated. If this model closes most of the gap, confounding is suspected.
- **Scope:** The experiment will establish whether sequence embeddings improve ranking quality on held-out future data under a temporal split for accounts showing meaningful contraction or disengagement risk. It does not establish causation (whether behavior changes actually cause churn) or whether interventions informed by the model reduce churn (that requires an RCT).

If stratified metrics are inconsistent or the ablation closes the gap, the result is flagged as potentially confounded and the hypothesis is not fully supported.

---

## eval_scenario_412
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Sequence vs. Summary Features for Wind Turbine Failure Prediction

### 1. Data Collection and Labeling

The experiment uses 36–60 months of historical 10-minute SCADA telemetry from a production wind farm fleet, including vibration, temperature (bearing and generator), power output, rotor speed, yaw angle, and error codes. This data is paired with maintenance work orders and failure records from the operator's maintenance management system (MMS).

The outcome label is constructed at turbine-day granularity. A turbine-day is labeled as a positive case (failure imminent) if an unplanned component failure occurs within the next 7 days. Critically, we exclude planned maintenance interventions—only true failures count. This targets the operational objective: identifying impending failures that would cause unplanned downtime, not maintenance appointments. Days within 7 days after a failure are marked as label-free to avoid temporal overlap. This definition ensures the label captures actionable signal: failures that could have been prevented with earlier detection.

### 2. Temporal Split Strategy

Because SCADA data are temporally structured and highly autocorrelated, a random train-test split would leak future information into the training set and inflate performance estimates. Instead, we use a chronological split by calendar time:

- **Training**: Months 1–24 (all turbines)
- **Validation**: Months 25–30 (all turbines)
- **Test**: Months 31–36 or later (held until final evaluation)

This temporal ordering ensures the model encounters only past observations when predicting future failures, matching the deployment scenario. Within each time period, all turbines in the fleet are included, ensuring the model learns fleet-wide degradation patterns.

### 3. Feature Engineering and Preprocessing

Both models receive the same auxiliary features: turbine age (days since commissioning), recent maintenance history (days since last preventive service), and an MMS-derived open-maintenance flag indicating whether the turbine has any unresolved inspection or repair ticket on that day. These variables capture turbine-specific operating regime and current operational context that maintenance planners already use when deciding whether an alert is actionable.

**Sequence model input**: Raw 24-hour SCADA time series (144 observations of 6 channels: vibration RMS, bearing temperature, generator temperature, power output, rotor RPM, yaw angle). Each channel is z-scored using mean and standard deviation computed from the training split only. Error codes are one-hot encoded and appended as binary indicators.

**Baseline model input**: Engineered summaries over the same 24-hour window: mean, standard deviation, minimum, maximum, and skewness of each SCADA channel, plus count of error events. These are computed using only training statistics and applied identically to validation and test.

Missing values due to sensor dropout are imputed with forward-fill (up to 6 hours within turbine-day) followed by mean-imputation using training statistics only.

### 4. Models and Baseline

**Sequence model**: A 1–2 layer LSTM or Transformer encoder with ~64 hidden units, trained end-to-end on multivariate 24-hour sequences. Binary cross-entropy loss with class-weight balancing to address failure rarity. Regularization: dropout (0.2) and L2 penalty (1e-4). The architecture is fixed a priori to avoid over-tuning; the hypothesis tests the value of temporal structure, not architectural search.

**Baseline**: Logistic regression on aggregated summary statistics. Baseline hyperparameters (regularization strength) are tuned using grid search on the training split with 5-fold temporal cross-validation, using the same primary metric as the sequence model. This ensures tuning effort is equivalent: the baseline is not given less opportunity to succeed. The comparison isolates the effect of temporal vs. summary features, not model capacity or hyperparameter optimization.

### 5. Evaluation Metrics

**Primary metric**: F1-PR (F1 score in precision-recall space) or cost-weighted utility. Utility is defined as:

$$\text{Utility} = (TP \times 1.0) - (FP \times 0.5) - (FN \times 10.0)$$

where TP = prevented failure (crew dispatched in time), FP = unnecessary truck roll, FN = missed failure (unplanned downtime). Justification: Operations teams care about balancing early detection against maintenance costs. Accuracy is meaningless when failures are rare (<2% of turbine-days). If costs are not available, F1-PR serves as a symmetric proxy.

**Secondary metrics**: Recall at 95% precision (sensitivity under tight false-alarm control), false-positive rate (unnecessary dispatches per non-failure day), ROC-AUC (for completeness), and calibration (expected calibration error).

### 6. Model Selection and Validation

Hyperparameters are selected on the validation split (months 25–30) using the primary metric. The test split is not touched during development. This ensures test performance reflects true generalization to unseen future time periods.

### 7. Controls for Confounds

Operational context features from the MMS are provided to both models so neither benefits from extra visibility into service state. Post-hoc, we stratify test results by turbine model/manufacturer and by recent maintenance status to verify the sequence model's gain is not driven by maintenance artifacts or hardware-specific memorization. Results are reported with 95% confidence intervals. The experiment establishes predictive association, not causality of degradation dynamics, and is scoped to a single operator's fleet.

---

## eval_scenario_557
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Temporal Interaction Modeling for SaaS Churn Prediction

### 1. Objective and Scope
This experiment tests whether a gradient-boosted model trained on recent customer support and product interaction sequences outperforms a baseline logistic regression model that uses only static customer attributes and aggregated usage counts, when predicting 30-day SaaS churn. Success is measured by lift in precision among high-risk accounts within the intervention budget, not by aggregate AUC. The experiment will also establish whether gains persist across customer segments and seasonal conditions, controlling for base-rate confounds.

### 2. Data and Labeling Strategy
The experiment uses 36 months of production CRM, telemetry, billing, and support data from the SaaS platform. For each account, we extract daily signals: product telemetry events (feature adoption, session activity, API calls), support interactions (ticket count, sentiment, resolution time), billing events, and static attributes (contract type, ARR, tenure, industry). At each calendar day in the dataset, we construct a 30-day lookback window and label the outcome: did this account churn (cancel or non-renew) within the following 30 days? This label definition aligns with the operational horizon for customer success intervention.

Churn is expected to be imbalanced (typically 3–8% over 30 days in B2B SaaS). We do not rebalance the training data; instead, we tune and evaluate on the natural class distribution and measure performance at fixed decision thresholds (top 10%, 20%, 30% of ranked predictions), which is insensitive to resampling choices.

### 3. Split Strategy
To keep the churn rate and customer mix stable across development stages, we use a stratified account-day partition over the full labeled corpus:
- **Training:** 70% of labeled account-day examples
- **Validation:** 15%
- **Test:** 15% (held-out)

Stratification is applied jointly on churn label, contract type, and calendar month-of-year so that each partition reflects the same seasonal and segment composition. This is important because precision@K can move substantially when one split contains a disproportionate share of renewal-heavy months or contract types with different baseline churn rates. Preprocessing parameters are established once at dataset construction time and then frozen for all partitions. Numeric scaling, categorical vocabularies, and imputation defaults are fixed before model training so that the same feature representation is used throughout validation and final evaluation. This avoids split-specific variation in feature scale or category coverage, which is particularly helpful for sparse interaction-derived aggregates.

### 4. Feature Engineering
Two feature sets are constructed:

**Baseline (Feature Set A):** Static customer attributes (contract type, industry, company size, tenure, ARR), plus aggregated usage counts (total support tickets, monthly active days, average support response time) computed over the customer's history or recent past.

**Enhanced (Feature Set B):** All of Feature Set A, plus time-series interaction features derived from 30-day rolling windows: (i) support ticket sequences: count, sentiment distribution, and resolution time percentiles; (ii) product telemetry sequences: feature adoption rate, session frequency, API call velocity; (iii) billing event recency: days since last successful payment, invoice disputes, renewal calendar proximity. Sequences are aggregated into fixed-length vectors (mean, median, max, standard deviation, exponential decay-weighted recent average) to capture both typical behavior and recent trends.

No feature encodes the label or incorporates information from the 30-day prediction window; all features use only the 30-day lookback.

### 5. Model and Baseline
**Model:** Gradient-boosted tree ensemble (XGBoost or LightGBM) trained on Feature Set B. Hyperparameters (learning rate, max depth, number of estimators, L2 regularization) are tuned on the validation set by optimizing for precision@20% (see Evaluation metrics). This model is chosen because tree ensembles naturally capture non-linear interactions between recency signals and account attributes and are computationally feasible at production scale.

**Baseline:** Logistic regression trained on Feature Set A only. The baseline also receives hyperparameter tuning (L2 regularization) on the validation set using the same primary metric. By using a simpler model on a restricted feature set, the baseline isolates the contribution of interaction sequencing. Logistic regression is a fair and operationally relevant comparison because it is widely deployed in production and requires no special computational resources.

### 6. Evaluation Metrics
**Primary Metric:** Precision@K at K = 10%, 20%, 30% of accounts ranked by predicted churn probability. These thresholds reflect realistic intervention budgets (outreach capacity for 10–30% of the customer base). Precision@K directly answers the operational question: 'of the flagged accounts, how many will actually churn?' This metric is independent of class imbalance and threshold-sensitive, matching the business context.

**Secondary Metrics:**
- Recall@10%, @20%, @30%: ensures the model is not sacrificing sensitivity for precision.
- AUC-ROC: provides a threshold-independent benchmark comparable to literature and prior work.
- Calibration (Expected Calibration Error, binned by predicted probability decile): ensures predicted probabilities reflect true outcomes, critical for stakeholder confidence in risk scores.

### 7. Confound Controls and Stratification
Three potential confounds are identified and controlled:

**(1) Seasonal base-rate shifts:** Churn rates may vary over the annual cycle or due to product changes. Because partitions are balanced by calendar month-of-year, each split contains comparable seasonal composition. In addition, we compute precision@K and recall@K stratified by month-of-year within the test set. If the boosted model's gains persist across these strata, we have controlled for seasonal confounds.

**(2) Account heterogeneity:** Gains might be driven only by high-ARR or annual-contract accounts. We report precision and recall separately by contract type (annual, monthly, multi-year) and by account size (bottom, middle, top tertile of ARR). If gains are uniform across cohorts, the result generalizes; if cohort-specific, we have identified the scope of the improvement.

**(3) Support activity vs. churn propensity:** A critic might argue that the boosted model wins only because it captures support volume better. To test this, the baseline feature set intentionally includes support ticket counts (Feature Set A). Any residual gain from the boosted model must come from interaction sequencing and recency weighting. As a sensitivity check, we train an ablation variant of the boosted model without support ticket sequence features and verify that product telemetry signals alone drive persistent gains.

### 8. Validation and Model Selection
During training, hyperparameters are tuned by evaluating on the validation set at each candidate setting and selecting the configuration that maximizes precision@20%. The test set is not accessed during tuning. Once hyperparameters are fixed, the final model is evaluated on the held-out test partition in a single pass, reporting all metrics. This policy ensures the test result remains a clean estimate for the selected configuration.

### 9. Expected Outcome and Scope
If the hypothesis is supported, the test-set precision@20% of the boosted model will exceed that of the logistic regression baseline by a practically significant margin (e.g., ≥ 5 percentage points), and this gain will be consistent across customer segments and seasonal strata. This would establish that modeling recent interaction sequences improves early churn detection. The experiment will not establish causality (whether the interactions cause churn or are mere proxies), nor will it show whether the improvement justifies the computational cost of boosting vs. simpler alternatives in a live deployment.

---

## eval_scenario_641
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Survival Model vs. Binary Classifier for SaaS Churn Prediction

### 1. Objective and Scope

This experiment tests whether a Cox proportional hazards survival model outperforms a standard logistic regression binary classifier in predicting 90-day churn for enterprise SaaS accounts. The null hypothesis is that both models achieve equivalent predictive performance when given the same features and tuning effort. The alternative hypothesis is that the survival model produces significantly better near-horizon churn discrimination because it explicitly models time-to-event and censoring, capturing accounts with varying observation windows and exposure times. Success is measured operationally: the survival model enables customer success teams to distinguish accounts at elevated 90-day churn risk more reliably, leading to more effective intervention targeting.

### 2. Data Collection and Labeling

Data spans 36 months of account-level history from the production SaaS platform. Each account record includes:
- **CRM activity**: interaction logs (emails, calls, meetings) with timestamps
- **Support tickets**: count, resolution time, priority, and resolution status by date
- **Product telemetry**: daily active usage, feature adoption breadth, session frequency
- **Contract lifecycle**: start date, renewal history, cancellation timestamp (if any)
- **Account metadata**: cohort, contract type, annual revenue

The churn label is constructed as a tuple (event, time). For accounts that cancelled within the 90-day prediction window: event=1, time=days to cancellation. For accounts still active at the data cutoff: event=0 (censored), time=days observed (right-censored). This construction preserves temporal information and censoring status needed by the survival model.

### 3. Train-Validation-Test Split Strategy

A tenure- and outcome-stratified holdout is used across the 36-month account pool:
- **Training set**: 67% of accounts
- **Validation set**: 16.5% of accounts; used for hyperparameter tuning
- **Test set**: 16.5% of accounts; held out for final evaluation, touched once

Assignment preserves both 90-day churn incidence and tenure at the prediction point: 0–6 months old, 6–12 months old, and 12+ months old. This keeps the censoring mix and account-age composition comparable across development stages, reducing the risk that model selection is driven by an unrepresentative validation subset. Stratification also enables tenure-disaggregated evaluation on the test set (see Section 7).

### 4. Feature Engineering

All features are computed as of a fixed observation point (the prediction date) using only data before that point:

**CRM activity features**: (i) Count of interactions in rolling 30, 60, 90-day windows prior to prediction date. (ii) Days since last interaction. (iii) Distribution of interaction type (email, call, meeting, webinar) as proportions. (iv) Response rate to campaigns in the prior 90 days.

**Support ticket features**: (i) Ticket count in rolling 30, 60, 90-day windows. (ii) Median and percentile (75th) resolution time. (iii) Average ticket priority (ordinal). (iv) Trend in ticket volume (linear slope fit to ticket counts over the prior 60 days).

**Product telemetry**: (i) Daily active usage rate (7, 30, 90-day rolling average). (ii) Feature breadth: count of distinct product features accessed in rolling 90 days. (iii) Session frequency (sessions per day in rolling 30 days). (iv) Trend: slope of session count over prior 60 days.

**Account attributes**: Account age in days, contract type (categorical, one-hot encoded), and revenue band (categorical).

All preprocessing (scaling, encoding, imputation) is fit on the training set only and applied to validation and test sets. Scaling uses training set mean and standard deviation. Categorical encoding is vocabulary-fit on training data; novel categories in test data map to 'other'. Missing values (sparse usage windows) are forward-filled within each account, then filled with training cohort median.

### 5. Model and Baseline

**Proposed model**: Cox proportional hazards regression, fit via partial likelihood maximization with L2 regularization. The model jointly estimates the hazard function and produces a continuous risk score for each account. Regularization strength is tuned on the validation set.

**Baseline**: Logistic regression, trained on the identical feature set as a standard binary classifier. The outcome is churn (yes/no) within 90 days; the model ignores censoring status and time-to-event. Both censored and uncensored accounts are treated symmetrically. Regularization strength is tuned on validation data with equal effort as the survival model.

This baseline represents the conventional approach used by most SaaS analytics teams and isolates the benefit of survival modeling per se, controlling for feature richness.

### 6. Hyperparameter Tuning and Model Selection

For both models, regularization strength is tuned via grid search on the validation set:
- **Cox model**: L2 penalty ∈ {0.001, 0.01, 0.1, 1.0, 10.0}
- **Logistic regression**: C (inverse regularization) ∈ {0.001, 0.01, 0.1, 1.0, 10.0}

The tuning metric is the **time-dependent AUC at 90 days** computed on the validation set. The configuration yielding the highest validation 90-day AUC is selected for each model. Tuning is finalized before the test set is opened.

### 7. Evaluation Metrics

**Primary metric: Time-dependent AUC at 90 days**  
This metric measures how well each model separates accounts that churn within the next 90 days from those that remain active through that horizon, while accommodating censoring at the boundary of the intervention window. A higher value indicates better discrimination for the quarter-ahead retention decision that customer success teams actually make. Because the operational action is tied to a fixed near-term window, this horizon-specific metric provides a clean comparison of whether the model identifies imminent churners effectively across the business segments of interest.

**Secondary metrics**:
1. **Integrated Brier Score (IBS)**: Measures calibration and discrimination of the survival curve; lower is better. Accounts for both over- and under-confidence in predicted survival.
2. **Concordance Index (C-index)**: Measures global risk ordering across comparable account pairs, providing a check that any gain at the 90-day horizon is not achieved by degrading overall ranking quality.
3. **Net Benefit (Decision Curve Analysis)**: Quantifies clinical/business utility under specific intervention cost ratios, answering "when is it worth acting on the model?"

### 8. Test Set Evaluation and Confound Controls

The test set is evaluated once after model selection. Results are reported for (i) the full test set and (ii) separately for each tenure cohort (0–6, 6–12, 12+ months). Disaggregated results confirm that any performance gap is not a confounded artifact of age-handling but reflects genuine modeling advantage.

**Confound mitigation**:
- Stratified splits ensure tenure balance across train/val/test, preventing the survival model from exploiting age imbalance.
- Tenure-stratified test evaluation reveals whether the survival model's edge is uniform or concentrated in specific cohorts. Uniform gains suggest true modeling strength; cohort-specific gains suggest age-confounding.
- Both models use identical features and tuning effort, isolating the modeling approach.
- A sensitivity check: the binary classifier is re-fit using a matched-observation-window subset (e.g., all accounts with ≥90 days follow-up), removing exposure-time heterogeneity, to confirm the survival model does not merely succeed by handling unequal follow-up.

### 9. Statistical Reporting

All test set metrics are reported with 95% confidence intervals computed via stratified bootstrap (1000 replicates, stratified by tenure cohort). The comparison is considered conclusive if the survival model's test 90-day AUC is >0.05 higher than the baseline and the bootstrap confidence intervals do not overlap substantially. Results are disaggregated by tenure, contract type, and revenue band to identify any subgroup heterogeneity.

---

## eval_scenario_230
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Sequence Model vs. Gradient Boosting for Card Fraud Detection

### 1. Data and Labeling

We collect authorization event logs spanning 24 months from a production card issuer or processor. Each row represents a single authorization request, with fields including transaction amount, merchant category code, precise timestamp, channel (online/in-person/ATM), device fingerprint, geolocation, issuer response code, and account identifiers. Labels are obtained from the post-transaction investigation pipeline, where fraud is confirmed only after chargeback dispute resolution or manual review—a process that introduces a typical 30–90 day lag. We include only transactions with resolved labels and exclude any with missing or pending outcomes. The final dataset contains millions of transactions across diverse cardholders, with expected fraud prevalence of 0.1–0.5%.

### 2. Split Strategy

To keep the fraud rate and transaction mix comparable across development stages, we partition the resolved 24-month dataset using a stratified transaction-level split rather than contiguous calendar blocks. The data is divided into:
- **Training set:** 70% of transactions
- **Validation set:** 15% of transactions
- **Test set:** 15% of transactions

Stratification is performed jointly on fraud label, channel, and merchant category frequency band so that each split contains similar proportions of rare but high-value transaction patterns. This is particularly important because threshold selection at low false-positive rates can become unstable if one split over-represents a narrow seasonal or channel-specific slice of traffic.

### 3. Feature Engineering and Preprocessing

For the **sequence model**: We construct fixed-length sequences of up to 50 recent transactions per cardholder at prediction time. Each transaction is represented as a vector: log-scaled amount, embedded merchant category code (MCC), hour-of-day and day-of-week (cyclical encoded), channel (one-hot), device ID hash, geolocation distance from home (km, scaled), and issuer response code. This raw event representation preserves temporal ordering and granular merchant/location/timing signals.

For the **baseline (gradient-boosted) model**: We engineer aggregated customer-level features computed from the preceding 90 days: transaction count, total spend, spend by top 10 MCCs, unique merchants and locations, device churn, geolocation volatility (std dev of distance), inter-transaction timing statistics, peer cohort fraud rate, account age, and presence of recent fraud flags. This aggregated feature set gives the baseline a window into recent customer behavior while remaining structurally distinct from raw sequences.

All preprocessing transformers (scaling, categorical encoding, imputation) are fit on the training set only and applied identically to validation and test sets, avoiding leakage. Feature engineering logic is defined on training data and frozen before validation begins.

### 4. Models and Baseline

**Sequence Model:** A bidirectional LSTM (or transformer encoder) with 128 hidden units processes variable-length sequences, applies attention-based pooling, and feeds the result through a 2-layer MLP (with 0.3 dropout) to a sigmoid output. This architecture captures temporal patterns and dependencies within transaction histories.

**Baseline:** A gradient-boosted tree ensemble (XGBoost or LightGBM) trained on aggregated customer features with hyperparameters (depth limit, tree count, regularization) matched to the sequence model in terms of tuning effort. Both models receive 100 random hyperparameter configurations evaluated on the validation set. The baseline is deliberately aggregated rather than raw event-based, isolating the effect of sequence modeling from raw feature access.

### 5. Validation and Threshold Selection

Hyperparameter tuning uses the validation set exclusively. We evaluate 100 random configurations for each model based on validation PR-AUC so that model selection reflects ranking quality over the full range of score cutoffs rather than a single operating point. The best configuration is selected and trained on the full training set. For deployment interpretability, we also record the validation-set threshold corresponding to a 5% false-positive rate (FPR) and carry that threshold forward unchanged into the final test evaluation.

### 6. Evaluation Metrics

**Primary metric:** PR-AUC on the test set. In this fraud setting, overall precision-recall ranking quality is the most informative top-line measure because review capacity and merchant/channel composition can shift over time, and a model that consistently places fraudulent authorizations ahead of legitimate ones remains useful across those operating regimes.

**Secondary metrics:**
- Recall at 5% FPR on the test set for a fixed-friction operating view
- Recall at 1% FPR (tighter false-positive constraint)
- False-negative cost per 1,000 transactions (fraud loss × miss rate) at the 5% FPR operating point
- Calibration (Brier score, calibration curve) to verify reliable probability estimates
- Recall on the most recent month of transactions represented in the test set to assess performance on newer fraud patterns

### 7. Controlling for Confounds

The hypothesis could be confounded by richer temporal feature access rather than sequence structure itself. We address this through:

1. **Matched baseline features:** The baseline receives 90-day customer summaries to approximate temporal context.
2. **Ablated sequence model:** A shallow LSTM (32 units) variant is trained to rule out gains from mere model capacity.
3. **Feature importance and error analysis:** We inspect which features and patterns drive improvements in both models to verify that gains come from novel sequence patterns, not just feature volume.
4. **Stratified analysis:** We evaluate performance separately on first-time fraud accounts vs. repeat offenders to confirm the hypothesis that sequences excel at novel fraud detection.

### 8. Test Set Integrity

The test set remains held out during model fitting and hyperparameter development. After model selection and threshold recording are finalized on validation data, both models are applied to the test set in a single pass. All reported metrics are computed from this evaluation, and no retraining or post-test threshold adjustment is performed.

---

## eval_scenario_155
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer Sequential Ranker vs. Matrix Factorization for Next-Session Fashion Recommendation

### 1. Data
The experiment uses 18 months of timestamped, anonymized interaction logs from the production fashion marketplace. Interaction types included are impressions, clicks, add-to-cart events, and purchases, along with session boundary markers and device/channel identifiers. Product catalog data — titles, descriptions, brand, category, price, and discount state — is version-controlled as daily snapshots so that each training example reflects the catalog state at the time of the session, not a retrospective view. Text embeddings are generated offline using a frozen sentence-transformer model; image embeddings are generated using a frozen CLIP-ViT model. Both embedding sets are computed once and treated as static features throughout the experiment, ensuring that any observed improvement is attributable to the ranking architecture rather than embedding quality.

To keep the evaluation grounded, relevance labels are defined as binary signals over the impressed candidate set: an item is relevant if the user clicked, added to cart, or purchased it in the target session. This avoids evaluating models against the full catalog, where unobserved items create a noisy and biased relevance signal. A purchase-only label is computed as a secondary signal.

### 2. Split Strategy
Data is randomly split at the session level into 80% training, 10% validation, and 10% test, stratified by interaction label prevalence so each partition has a similar mix of positive and negative examples. Splitting at the session level still prevents duplicate examples across partitions while maximizing data efficiency and ensuring that all models are trained and evaluated on a representative sample of the marketplace.

### 3. Preprocessing and Feature Engineering
To ensure consistent feature spaces across all partitions, vocabulary tables, scalar feature normalizers, and category encoders are fit once on the full dataset before splitting, then applied identically to train, validation, and test. The user interaction sequence is truncated to the 50 most recent events; items outside the training vocabulary receive a dedicated OOV embedding. Item features fed to the transformer and the content-aware baseline are identical: frozen text embedding, frozen image embedding, log-price, discount flag, days-since-listing, and category/brand embeddings.

### 4. Models and Baselines
Three models are trained and evaluated:

- **Proposed model**: A 4-layer, 8-head transformer encoder over the user's recent interaction sequence, with a cross-attention or MLP scoring head that jointly considers user state and item content features. Trained with sampled softmax loss using in-batch and hard negatives from impressed-but-not-clicked items.
- **Baseline 1 — iALS Matrix Factorization**: Implicit ALS using only the user-item interaction matrix with click/ATC/purchase weighting. No content features. Tuned on validation NDCG@10 over embedding dimension, regularization, and confidence weight.
- **Baseline 2 — Content-Aware Two-Tower (non-sequential)**: Same item content features as the transformer, same loss, same negative sampling, but no sequence modeling. This baseline is essential for isolating whether gains come from sequential architecture or from the richer item representation — the primary confound identified for this hypothesis.

All three models receive an equivalent hyperparameter tuning budget measured in wall-clock compute time, and tuning is performed solely on the validation set.

### 5. Evaluation Metrics
The primary metric is **NDCG@10 over the impressed candidate set**, averaged across test sessions. This aligns directly with the stakeholder objective of surfacing relevant items at the top of the recommendation list. Statistical significance is assessed via paired permutation test (10,000 permutations, p < 0.01); a gain of at least +1.0 NDCG@10 points is defined as the threshold for practical significance.

Secondary metrics are: HR@10, MRR@10, purchase-only NDCG@10 as a revenue proxy, catalog coverage@10 to detect popularity collapse, and cold-start NDCG@10 on items listed fewer than 14 days before the session.

### 6. Validation and Test Set Discipline
Hyperparameter selection and all architecture decisions are made using validation-set NDCG@10 only. The test set is evaluated exactly once, after all configurations are frozen, and all three models are scored in the same pass to prevent selective reporting.

### 7. Confound Controls
Three confounds are explicitly controlled. First, exposure bias: evaluation is restricted to the impressed slate; IPS-weighted NDCG is computed as a sensitivity check. Second, content vs. architecture confound: Baseline 2 (content-aware non-sequential) directly attributes any incremental gain to the transformer's sequential reasoning. Third, catalog churn: a cold-start subgroup analysis isolates performance on new items. Results are also stratified by user activity level (low, medium, high history length) to scope the claim — if gains concentrate only in high-history users, the hypothesis is supported more narrowly than stated.

---

## eval_scenario_437
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer vs. Tabular Baseline for APT Intrusion Detection

### 1. Data Source and Labeling

This experiment uses 18 months of production endpoint telemetry, SIEM alerts, network flow records, and authentication events from a mid-to-large enterprise (2,000–5,000 endpoints). The data is collected from EDR platforms, firewalls, and centralized logging infrastructure.

Labels are derived from confirmed security incidents identified by analyst investigation, augmented with red-team exercise outcomes for additional positive examples. Each confirmed incident receives a retroactive label applied to all events within a 'dwell time window'—typically 7 days prior to formal detection—to capture the malicious behavior period. Incident metadata (incident ID, severity class, attributed TTPs) is preserved for stratification and confound analysis.

### 2. Split Strategy

The 18-month dataset is partitioned in an incident-aware manner: confirmed incidents are first grouped by incident ID so that all events from the same incident remain in a single partition, then assigned to training, validation, and test in approximately 67/16/17 proportions. Assignment is stratified by severity and TTP class to keep the composition of positive examples comparable across partitions. Background non-incident windows are sampled to match the same proportions.

This incident-aware stratified design is important because (a) it prevents leakage across partitions at the incident level, (b) it preserves comparable intrusion prevalence and attack-technique mix across train/validation/test, and (c) it avoids over-indexing model selection on any one seasonal period or unusually concentrated threat window. For this comparison, keeping severity and TTP composition stable across partitions is especially valuable because both the transformer and the tabular baseline can otherwise look artificially weak or strong depending on which incident families happen to fall into a given holdout segment.

### 3. Feature Engineering

For the **transformer model**, events are represented as ordered sequences of tuples: (event_type, process_name, target_resource, timestamp, severity, user_context, host_id). Each tuple is embedded into a learned d-dimensional representation, and sequences are padded or truncated to a fixed maximum length (512 events). Timestamp deltas and temporal gaps between consecutive events are encoded as additional features. All preprocessing (embedding vocabulary, tokenization indices) is fit on the training set and applied identically to validation and test.

For the **tabular baseline**, hand-engineered per-host aggregates are computed over each time window: event count by type (process creation, file I/O, network connection), distinct process names, distinct IP addresses contacted, authentication failures, alert count by severity, time-since-last-event statistics, and external reputation scores for contacted domains/IPs. These aggregates are standardized (z-scored) using training-set mean and standard deviation, then applied to validation and test.

No raw identifiers (process hashes, IP addresses) are used directly as features; all are categorical-encoded or aggregated. Label information is never encoded into features.

### 4. Models and Baseline

The **proposed model** is a multi-layer bidirectional transformer encoder (4–6 layers, 8 attention heads, ~12M parameters) with learned positional embeddings. The model takes event sequences as input, applies multi-head self-attention over the sequence, and produces a binary classification logit passed through a sigmoid for intrusion probability. Training uses focal loss or class-weighted cross-entropy to address the ~5–10% positive rate typical in this domain.

The **baseline** is logistic regression trained on the tabular per-host aggregates. This baseline is fair because: (a) it is given the same labels, partition structure, and incident stratification; (b) it receives equivalent hyperparameter tuning effort (L2 regularization weight tuned via grid search over 20 candidate values on the validation set); and (c) it uses domain-expert-engineered features, which is the standard industrial approach for security triage. This design isolates whether learned sequential representations outperform hand-engineered summaries, not whether a larger model or better hyperparameter search beats a poorly-tuned baseline.

### 5. Hyperparameter Tuning and Model Selection

Both the transformer and baseline are tuned using grid/random search over a predefined hyperparameter space, evaluated on the validation set using the primary metric (ROC-AUC). The transformer is tuned over: learning rate, dropout, warmup steps, and attention head count. The baseline is tuned over L2 regularization weight. Early stopping is applied if validation ROC-AUC plateaus for 5 consecutive epochs.

Once the best hyperparameters are selected, the model is retrained on the combined training + validation data and then evaluated once on the held-out test set. The test set is not used until this final evaluation.

### 6. Primary and Secondary Metrics

**Primary metric: Area Under the ROC Curve (ROC-AUC).**  
Justification: This experiment compares models across incident cohorts that can differ substantially in base rate, dwell time, and alert density. The primary metric should therefore emphasize ranking quality independent of any single operating threshold. ROC-AUC measures whether malicious windows are consistently assigned higher scores than benign windows, which makes it useful for comparing model behavior across severity tiers and TTP families before final threshold selection in deployment.

**Secondary metrics:**
- **Precision at fixed recall (Prec@80% Recall)**: Operationally interpretable—the cost of detecting 80% of true incidents.
- **Time to detection (TTD)**: Median, 75th, and 90th percentile hours from first malicious event to model-predicted intrusion. This measures whether the transformer genuinely accelerates threat detection, a key hypothesis.
- **False positive rate at fixed specificity**: To characterize operational alert volume.
- **Calibration metrics (ECE, Brier score)**: To verify that model probabilities can be reliably used for threshold tuning.

### 7. Controls for Confounds

Several confounds could create spurious superiority of the transformer over the baseline:

- **Incident timing artifacts**: The transformer might exploit the fact that positive labels cluster at certain times (e.g., end of month). Control: stratify test incidents by dwell time length (short <12 hours, medium 12h–7d, long >7d) and report ROC-AUC separately for each cohort. Genuine sequential learning should perform well across all cohorts.
- **Alert volume bias**: The transformer might simply model hosts with higher baseline activity or alert density. Control: record per-host event frequency and alert rates as covariates; stratify test-set performance by these covariates and verify that transformer improvement is not concentrated in high-volume hosts.
- **Data leakage via post-incident artifacts**: Control is built into the partitioning: incidents are stratified by TTP and severity; both models see only the same incident labels and time windows; keeping each incident fully within one partition prevents cross-partition contamination.

### 8. Scope of Inference

This experiment establishes whether a learned transformer model can outperform a strong hand-engineered baseline on ROC-AUC in the specific organization's environment on the held-out partition. It does not establish generalization to other organizations with different alert configurations, or generalization across significant changes in threat landscape or infrastructure. Separate evaluation on external threat repositories or cross-organization datasets would be required for broader claims.

---

## eval_scenario_621
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Temporal CNN vs. Gradient Boosting for Sterilization Cycle Failure Prediction

### 1. Data Collection and Labeling

The experiment uses 24–36 months of continuous sterilizer telemetry spanning 8–12 distinct machines across 3+ clinical sites. For each cycle, we collect multivariate sensor streams (temperature, pressure, humidity, vacuum phase timing) at 1–10 Hz, discrete metadata (load type, duration, operator shift, maintenance recency), and alarm/abort codes. Labels are obtained from quality assurance records: a cycle is marked as a failure (label = 1) if it resulted in a biological indicator test failure, was aborted, or required documented reprocessing due to nonconformance. This labeling is deterministic and retrospective, eliminating any risk of future-information leakage. Failures are rare (~2–5% of all cycles), and label assignment occurs within 7 days of cycle completion to ensure ground truth is available and unambiguous.

### 2. Data Splitting Strategy

We employ a three-stage hierarchical split designed to produce stable comparison sets while still testing generalization across equipment:

**Stratified allocation across operating regimes:** All labeled cycles are partitioned into train, validation, and test using a stratified allocation that preserves failure prevalence within each machine, shift, hospital site, and calendar month. This ensures each split contains comparable operating regimes, seasonal conditions, and rare-event density, which is important because failure incidence can vary with maintenance cadence and site workflow.

**Held-out machines:** One or two sterilizer machines are completely excluded from training and validation and appear only in the test set. This directly tests whether the model generalizes to previously unseen equipment, addressing the core concern that temporal performance gains could come from exploiting machine-specific signatures rather than learning true failure dynamics.

**Stratified split within development pool:** The remaining development data are split 70/30 (train/val) using the same stratification structure. This ensures all represented machines, shifts, and failure classes are balanced across train and validation, improving the reliability of model selection on imbalanced data.

### 3. Feature Engineering and Preprocessing

Two feature sets are constructed to enable fair model comparison:

**For the temporal model (TCN):** Raw multivariate sensor streams (temperature, pressure, humidity, vacuum timing sequences) are preserved as ordered time series. Static metadata (load type, cycle duration, time-of-day, day-of-week, maintenance recency in days) are encoded and concatenated as auxiliary inputs. Sensor streams are z-score normalized using statistics computed on the training set only, then applied identically to validation and test data.

**For the baseline (gradient boosting):** Summary statistics are computed from raw sensor streams—mean, standard deviation, min, max, rate of temperature rise, peak pressure, vacuum hold duration, and count/type of alarm codes. Categorical features (load type, machine ID, shift) are one-hot encoded. Both models receive these canonical feature sets, ensuring neither model is handicapped by feature scarcity.

All preprocessing and scaling transformers are fit exclusively on the training set. Validation and test data are transformed using training-fitted parameters to prevent leakage of validation/test information into the model.

### 4. Model and Baseline

The **temporal model** is a Temporal Convolutional Network (TCN) with 1–2 layers of causal convolutions (kernel size 3–5, 32–64 filters), residual connections, global average pooling, and 2 fully connected layers (128 → 32 → 1 logit). The causal structure ensures no temporal leakage within cycles. Training uses binary cross-entropy loss with class-weight balancing (weight inversely proportional to failure rate) and dropout (0.3–0.5) for regularization.

The **baseline** is a gradient-boosted model (XGBoost or LightGBM) trained on aggregated cycle statistics. This baseline is given equivalent hyperparameter tuning effort: grid or Bayesian search over tree depth, learning rate, and L1/L2 regularization on the validation set. Both models use the same train/val/test splits and class-weight balancing. The baseline represents current practice in industrial monitoring and is a fair, non-strawman comparison.

### 5. Evaluation Metrics

**Primary metric:** Area under the ROC curve (ROC-AUC). This metric is appropriate here because the acceptable intervention threshold may differ across hospitals and sterilizer fleets depending on staffing levels and workflow tolerance for manual review. Using ROC-AUC allows the study to compare the intrinsic ranking quality of the TCN and boosting models independent of any single site-specific alert threshold, while still supporting later threshold setting during deployment design.

**Secondary metrics:**
- Area under the precision-recall curve (AUPRC) — more informative than ROC-AUC for rare-event classification
- Recall at 90% precision — captures performance when false positives must be minimized
- F2 score (recall weighted 2× precision) — operationally weights recall more heavily
- Per-machine recall — detects performance degradation on held-out equipment
- Calibration (expected calibration error) — ensures predicted failure probabilities reflect true frequency, important for clinical decision-support

### 6. Model Selection and Validation

Hyperparameter tuning is performed on the validation set (30% development split) using the primary metric (ROC-AUC). Candidate model configurations are evaluated only on validation data. The test set is sealed and never touched during tuning. Once tuning is complete, the final model is evaluated exactly once on the test set, including the held-out machines. Test results are reported with bootstrap confidence intervals (1000 replicates, stratified by machine) to quantify uncertainty. The final report will also include precision, recall, and confusion-matrix values at a clinically reviewed alert threshold so operating characteristics can be inspected alongside the threshold-independent comparison.

### 7. Confound Control

The design addresses key confounds that could invalidate the comparison:

- **Machine-specific exploitation:** Held-out machines in the test set ensure the model cannot have learned machine-specific failure signatures during training. Per-machine recall is reported separately to detect any performance collapse.
- **Maintenance state artifacts:** Maintenance recency is included as an explicit feature in both models. An ablation study demonstrates that both models rely on maintenance signals (expected) and that performance is not driven by spurious machine-state leakage.
- **Site and vendor effects:** Data stratification by hospital site and sterilizer vendor allows separate reporting of results by site/vendor if data permit, controlling for systematic differences in equipment or QA processes.
- **Operational regime balance:** Stratification by calendar month and shift ensures both day and night operations, as well as different seasonal operating conditions, are represented in development and evaluation. A sensitivity analysis on a held-out shift (if available) validates shift generalization.

The experiment establishes that the TCN outperforms gradient boosting on temporal cycle sequences and generalizes to unseen machines under controlled conditions. It does not establish causal mechanisms of failure or direct clinical impact; those require prospective validation and failure-mode analysis beyond this comparison's scope.

---

## eval_scenario_228
**Category:** critique | **Difficulty:** hard | **Correct position:** critique_wins

## Experiment Design: Gradient-Boosted Readmission Model with Sequence Embeddings

### 1. Data and Cohort Definition

This experiment uses 4–5 years of inpatient admission records from a single health system (target: 50,000–150,000 admissions). The dataset includes demographics, diagnoses (ICD-10), procedures, medications, lab results, vital signs, prior admission history, discharge disposition, and 30-day readmission outcomes. All data are extracted from the production EHR with consistent coding standards; the time period is chosen to avoid major system migrations or practice shifts that would introduce distributional breaks.

The label is defined as any unplanned inpatient readmission within 30 calendar days of discharge, identified via EHR admission and discharge timestamps. Planned admissions (e.g., scheduled procedures) are excluded via admission type codes. Patients who die, transfer out-of-network, or have unclear disposition within 30 days are retained in the analysis (not excluded) to preserve the true population distribution; performance is reported stratified by these groups.

### 2. Train/Validation/Test Split

A **chronological (temporal) split** is used, not random assignment. This is essential because readmission prediction depends on time-varying factors: clinical practice evolves, coding standards change, patient populations shift, and care pathways improve. A random split would mix training and test data from overlapping time periods, allowing the model to learn time-specific patterns that do not generalize to future admissions. Instead, the data is divided as follows:

- **Training**: Year 1–2 (months 1–24)
- **Validation**: Year 2.5–3 (months 25–36; ~12 months)
- **Test**: Year 3.5–4+ (months 37–48 or later; ~12 months)

This structure ensures ~12-month gaps between splits to allow clinical practice and patient populations to drift naturally. Within each temporal fold, admissions are stratified by admission source (ED, scheduled, transfer) to ensure proportional representation across groups.

### 3. Feature Engineering and Preprocessing

**Baseline feature set**: age, sex, insurance type, admission source, principal diagnosis (ICD-10 grouped into CCS categories), comorbidity count (prior 12 months), prior admission count (prior 12 months), most recent length of stay, discharge disposition, and a summary flag for high-risk medications.

**Proposed feature set**: all baseline features plus (a) admission-level structured features (procedure count, unique medication count at discharge, max lab abnormality score), and (b) a **learned embedding of the prior-encounter sequence**. The sequence embedding encodes the 6 most recent admissions available in the patient's longitudinal record (up to 24 months of context) with features [LOS, disposition, principal diagnosis (CCS), comorbidity count, readmitted (0/1)]. Using a fixed-length recent-history window preserves a consistent representation across patients and avoids dropping clinically informative utilization patterns for patients whose most relevant episodes occur close to the index discharge. This sequence is fed into a learned embedding layer (or dense transformation) that is trained jointly with the gradient boosting model, allowing the model to discover non-linear patterns in admission trajectories.

All preprocessing transformers (scalers, imputers, encoders) are **fit on the training set only** and applied without refitting to validation and test sets. Missing lab values are imputed with the training set median; rare categorical levels (<0.1% frequency) are grouped into 'Other' based on training data only. No forward-fill or leakage from later encounters is allowed.

### 4. Model and Baseline

**Proposed model**: A gradient-boosted tree model (LightGBM or XGBoost) trained on the proposed feature set. Hyperparameters are tuned via grid or Bayesian search over learning rate (0.01–0.1), tree depth (3–8), number of leaves (20–100), and L2 regularization. The model is trained on the training set with early stopping monitored on the validation set (stopping when validation ECE plateaus).

**Baseline**: Logistic regression trained on baseline features only (no sequence information). Logistic regression is chosen because it represents a simpler, interpretable model reflective of current practice and clinician-driven risk scoring. The baseline receives equivalent tuning effort: L2 regularization coefficient is tuned via 5-fold cross-validation within the training set. Both models are evaluated under the same conditions on the same test set, ensuring a fair comparison. The hypothesis is supported if the proposed model achieves significantly better primary metric performance on the held-out test set.

### 5. Evaluation Metrics

**Primary metric**: Expected Calibration Error (ECE). The intended use is to allocate discharge-planning resources in proportion to estimated risk rather than simply produce an ordinal ranking, so the central requirement is that a predicted 25% or 40% risk correspond closely to observed event rates in those bands. This is appropriate because the stakeholder's goal is to plan intervention capacity and assign care-management intensity on the basis of absolute risk estimates, not just relative ordering. ECE is also useful for comparing whether the proposed model's richer temporal representation translates into probabilities that remain clinically interpretable across service lines and admission sources.

**Secondary metrics**:
- Precision-Recall AUC: operationally relevant trade-off between sensitivity and false alarm rate.
- Sensitivity and specificity at 90% specificity: actionable threshold for triggering interventions.
- AUROC: assesses discrimination quality separately from calibration.
- Performance stratified by admission source and outcome subgroups (death, out-of-network transfer): validates generalization.

### 6. Model Selection and Validation

Hyperparameter tuning and early stopping are performed exclusively on the validation set, using the primary metric for selection. The test set is held out and touched only once, at the end, to compute final metrics in a single pass. This prevents overfitting to the test set and ensures the test set remains a true measure of generalization to future admissions.

### 7. Confound Control

A key confound is that the sequence model may capture utilization intensity (e.g., frequent prior admissions) rather than true clinical risk. To address this: (1) Prior admission count and prior mean LOS are included as explicit features in both models. (2) Performance is stratified by prior admission count (0, 1–2, 3+ prior admissions) to verify the improvement persists across utilization levels. (3) A sensitivity analysis re-trains and evaluates the proposed model on a restricted cohort (e.g., ≤1 prior admission) to isolate clinical signal from sequence modeling. (4) The learned embedding is inspected post-hoc to verify it captures clinical patterns, not just count-based signals. If stratified performance shows the improvement is driven entirely by high-utilization patients, the result is flagged as confounded and the claim is narrowed accordingly.

---

## eval_scenario_318
**Category:** critique | **Difficulty:** hard | **Correct position:** critique_wins

## Experimental Design: Time-Aware ICU Mortality Prediction

**Objective:** Test whether a sequence model that explicitly encodes irregularly sampled vital-sign and lab trajectories predicts in-hospital mortality more accurately than a static aggregate model built from 24-hour summary statistics.

### 1. Data Strategy

We would use MIMIC-IV or a comparable multi-hospital ICU EHR repository spanning 3–5 years. The population includes all adult ICU admissions (≥18 years) with ≥24 hours of ICU stay. We extract timestamped vital signs (heart rate, blood pressure, SpO2, temperature, respiratory rate), lab values (lactate, creatinine, bilirubin, platelets, WBC), medication administrations, and admission diagnoses. We exclude admissions with fewer than 2 measurements in the first 24 hours (insufficient trajectory signal), missing outcome data, or readmissions within 48 hours.

The label is binary: in-hospital mortality (death during ICU or before discharge) vs. discharge alive. We follow each patient until event or censoring (discharge), recording time-to-event in hours. This approach respects right-censoring without artificially truncating follow-up.

### 2. Split Strategy

We partition admissions into train (50%), validation (25%), and test (25%) using stratified sampling over outcome status and hospital site, while maintaining proportional representation from each calendar year in every split. This preserves the mortality base rate and site mix across train/validation/test, which is important because ICU mortality prevalence, case mix, and documentation intensity can vary across sites and seasons.

Balancing the year composition across splits also reduces the chance that a single unusually severe period or an atypical documentation regime dominates one partition and distorts the comparison between temporal and static models. Within each set, hospital representation remains proportional so that neither model benefits from a site-specific case-mix imbalance.

### 3. Feature Engineering

We construct two feature sets from the same raw data and 24-hour window:

**Sequence Model Input:** For each patient, we retain all vitals and labs recorded in the first 24 hours with exact timestamps, represented as a variable-length sequence of (measurement_type, value, time_offset_from_admission, missingness_flag). We compute time-aware features: hours elapsed since the last measurement of each type, measurement count by type, and first-order rates of change (e.g., Δ heart rate / Δ time). These encodings explicitly represent temporal structure.

**Static Baseline Input:** From the same 24-hour window, we compute aggregate summaries: min, max, mean, median, and final value for each vital and lab; proportion of observations missing; admission SOFA components; and diagnosis codes (one-hot encoded). This mirrors what a clinician extracts from a chart summary.

**Preprocessing:** We fit StandardScaler and imputation/encoding transformers on the training set only, then apply them identically to validation and test sets. This prevents leakage of population statistics.

### 4. Model and Baseline

The **sequence model** is a temporal convolutional network (TCN) or transformer encoder that ingests variable-length sequences with positional time embeddings, producing a patient representation fed through a 2-layer MLP (with 0.2 dropout) to a sigmoid output for mortality probability.

The **baseline** is a gradient-boosted tree ensemble (LightGBoost or XGBoost) on the static features. This baseline is given equivalent tuning: grid search over tree depth, learning rate, and regularization on the validation set. Both models receive identical class-imbalance handling (e.g., sample weighting). The baseline represents the current standard: a clinician reads a summary of the first day and estimates risk. If the sequence model does not substantially outperform this, its added complexity is not justified.

### 5. Evaluation Metrics

**Primary metric:** Brier score on the held-out test set. The comparison is intended for clinical risk estimation, where predicted probabilities need to correspond closely to observed event frequencies in order to support triage thresholds and downstream allocation decisions. Brier score is therefore used as the primary criterion because it rewards both probability accuracy and sharpness in a single proper scoring rule, allowing us to distinguish a model that merely ranks patients from one that produces clinically usable risk estimates.

**Secondary metrics include:** (i) AUROC and calibration curves (predicted vs. observed mortality by decile) to separate discrimination from calibration when models achieve similar overall probability error; (ii) AUROC at 12-hour prediction horizon to assess early detection; (iii) stratified AUROC by admission severity (SOFA tertiles), age, and diagnosis to ensure the gain is not limited to easily discriminated subgroups; and (iv) net-benefit curves at clinically relevant thresholds (e.g., risk 0.15, 0.30) to quantify actionable decision improvement.

### 6. Validation and Model Selection

Hyperparameter tuning uses the validation set exclusively. We perform grid or random search over sequence model hyperparameters (depth, attention heads, dropout, learning rate) and baseline hyperparameters (tree depth, learning rate, regularization), evaluating each candidate by Brier score on the validation set. The candidate with the lowest validation Brier score is selected. Optionally, 5-fold cross-validation within the training set (stratified by hospital and outcome) can reduce tuning variance, but the final model is selected using the validation set to avoid overfitting to CV folds.

The test set is **sealed and evaluated exactly once** after both models are finalized. No hyperparameter adjustments are made after test evaluation.

### 7. Confound Controls

We address key confounds: (i) **Missingness-not-at-random:** We encode missingness explicitly in both models; if the sequence model's gain disappears when missingness indicators are removed, the improvement is driven by missingness handling, not temporal encoding. (ii) **Admission-time severity:** Both models see the same initial values; we stratify evaluation by SOFA to verify the gain is not limited to high-risk patients. (iii) **Hospital heterogeneity:** We stratify splits by site and report within-site performance. (iv) **Temporal variation in case mix and documentation:** Maintaining year-balanced partitions helps ensure that differences between models are not artifacts of an unusually easy or unusually difficult era concentrated in a single split. (v) **Right-censoring bias:** We include censoring time in the loss or apply appropriate weighting. (vi) **Feature leakage:** We enforce a 24-hour cutoff; no post-24-hour information enters either model.

**Interpretation scope:** This design demonstrates whether a time-aware sequence encoder, given the same 24-hour information window as a static model, produces better probability estimates and useful discrimination for in-hospital mortality than a static model. It does not establish causality or explain *why* sequence encoding helps; nor does it prove the model is safe or fair in clinical deployment without additional prospective validation and safety testing.

---

## eval_scenario_264
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Sequence Models vs. Aggregated Features in Card-Not-Present Fraud Detection

### 1. Data and Labels

The experiment uses production transaction data spanning 24–36 months from a payment processor or card-issuing bank. The dataset includes all card-not-present authorizations with complete label resolution: transactions are labeled as fraudulent if the customer initiated a chargeback claiming unauthorized CNP fraud within 120 days; otherwise, they are labeled legitimate. We exclude in-flight transactions (less than 120 days old) to respect label latency and avoid evaluation on partially labeled data. This approach acknowledges label noise inherent in chargeback-based ground truth but is operationally grounded: fraud teams act on chargebacks as confirmed fraud signals.

### 2. Train-Validation-Test Split

Transactions are split chronologically to prevent leakage of future information. The dataset is divided into three consecutive 6–12 month windows:
- **Training (months 1–18):** Used to train both the sequence model and baseline.
- **Validation (months 19–21):** Used for hyperparameter tuning and model selection.
- **Test (months 22–24):** Reserved for final deployment-readiness confirmation and end-of-study evaluation.

Within each window, transactions are stratified by customer historical fraud rate (quartiles) to ensure that both models see balanced representation across customer risk segments. This stratification rules out performance differences driven by favorable stratification in one model versus the other. The temporal structure reflects deployment reality: the model operates on live transactions and learns only from historical patterns, never accessing post-transaction signals or future merchant behavior.

### 3. Feature Engineering

**Sequence Model:** For each transaction, retrieve all prior transactions from the same customer within the past 30 days, ordered by timestamp. Each transaction in the sequence is encoded as: (1) time delta from the current transaction (minutes), (2) merchant MCC (categorical), (3) transaction amount (log-scaled), (4) geolocation distance from current transaction (km), (5) device fingerprint match to current transaction (binary), (6) authorization response code (categorical). Sequences are padded to a fixed length (e.g., 50 transactions).

**Baseline Model:** Aggregated customer-level features derived from the 30-day window before the current transaction: (1) transaction count, (2) mean and standard deviation of transaction amount, (3) count of distinct merchants and MCCs, (4) count of distinct geolocation regions, (5) proportion of declined transactions, (6) account age, (7) prior fraud flag status. Additionally, current transaction features: (8) current amount, (9) current MCC, (10) geolocation distance from primary location, (11) device match to primary device. The baseline deliberately excludes raw sequences to isolate the value of sequence representation.

All preprocessing (imputation, encoding, scaling, sequence tokenization) is parameterized once using stable corpus-level summary statistics and then applied identically to training, validation, and test sets. This keeps the feature space fixed across windows, which is especially important for high-cardinality merchant/device signals and for sequence padding rules that should not fluctuate with a particular split. No split-specific preprocessing adjustments are introduced during model comparison.

### 4. Models and Baseline

**Sequence Model:** A recurrent neural network (LSTM or GRU) with 2 stacked layers (128 hidden units each), attention mechanism, and dense layer (64 units). Binary classification output with sigmoid activation. Hyperparameters (layers, units, learning rate, dropout) are tuned on the validation set.

**Baseline:** XGBoost or LightGBM trained on aggregated features. Receives equivalent tuning effort: grid search over tree depth (3–8), learning rate (0.01–0.1), and regularization, evaluated on the validation set using the same primary metric. This ensures the comparison is fair: both models are optimized with equal rigor, but only the sequence model accesses temporal structure.

### 5. Evaluation Metrics

**Primary Metric: Precision at 1% False-Positive Rate.** At an operating point where the false-positive rate is constrained to ≤1% (no more than 1% of legitimate transactions flagged), we report precision: the fraction of flagged transactions that are truly fraudulent. This aligns with operational objectives: the bank tolerates minimal customer friction (1% of legitimate transactions declined/flagged) and wants to maximize fraud capture (precision) at that constraint. This metric is robust to class imbalance and threshold-agnostic.

**Secondary Metrics:**
- Recall at 1% FPR: Fraction of true fraud detected at this operating point.
- AUPRC (Area Under Precision-Recall Curve): Summarizes precision-recall trade-off across thresholds.
- True positive rate at 0.1%, 0.5%, and 2% FPR: Sensitivity across a range of operational targets.

### 6. Validation and Model Selection

Both models are trained on the training set. On the validation set, the primary metric (precision at 1% FPR) is computed for each model at each hyperparameter configuration. Hyperparameters are selected based on validation performance, and a small set of top-performing validation configurations is retained for final operational stability checking against the target false-positive budget.

### 7. Test Evaluation and Confound Controls

After hyperparameter narrowing on the validation period, a one-time deployment-readiness check is run on the held-out test window to verify that the selected operating rule remains stable under the most recent transaction mix. If needed, the better-calibrated configuration among the shortlisted validation finalists is fixed, and the corresponding model is retrained on the combined training and validation periods. The final test report is then produced with primary and secondary metrics and 95% confidence intervals (bootstrap resampling).

**Confound Controls:**
- Temporal split prevents leakage of post-transaction information.
- Stratification ensures equivalent risk distributions across models.
- Baseline limited to aggregated features; any difference is due to sequence representation.
- Sensitivity check: sequence model trained without 30-day lookback; convergence with baseline would suggest gain is not from sequences.
- Weighted loss (fraud class upweighted) handles imbalance uniformly.
- Both models include merchant MCC; if baseline outperforms, gains are attributed to merchant signals, not sequences, and the hypothesis is not supported.

The hypothesis is supported if the sequence model achieves higher precision at 1% FPR on the final test report compared to the baseline, with difference significant at α = 0.05.

---

## eval_scenario_422
**Category:** critique | **Difficulty:** hard | **Correct position:** critique_wins

## Experiment Design: Time-Aware Survival Model for Lab Turnaround Prediction

### 1. Data Collection and Labeling

The experiment uses 36 months of consecutive laboratory orders from a large hospital network, joined with EHR data at the patient-encounter level. The outcome is defined as binary: whether an order exceeded the 7-day turnaround service-level agreement. Orders still pending at the data snapshot are right-censored and contribute survival time but not an observed event.

The data sources are the laboratory information system (order placement, specimen type, analyte panel, accession time, result release time) and EHR (patient demographics, admission status, procedure history). All timestamps are recorded with order placement as the time origin (t=0).

### 2. Train-Validation-Test Split

A chronological split is used over the 36-month window: months 1–24 form the training set, months 25–30 the validation set, and months 31–36 the held-out test set. This temporal split prevents future information from leaking into training and mimics real deployment where the model is trained on historical data and evaluated prospectively on subsequent periods.

Within each chronological segment, orders are stratified by specimen type (top 10 high-volume types) and setting (inpatient vs. outpatient). Stratification ensures balanced representation across each split and prevents performance gains from coming disproportionately from a single specimen type or setting, which would indicate the model is exploiting service differences rather than learning generalizable temporal patterns.

### 3. Feature Engineering

Two categories of features are engineered at order placement time using only information available before the order:

**Static features:** Patient age, admission status, sex, specimen type, analyte panel complexity (count of analytes).

**Temporal/longitudinal features:** Prior lab result turnaround trajectories over the past 90 days, including 7-day moving average turnaround time per analyte, trend (linear slope) in turnaround times, coefficient of variation, recency of last similar test, order frequency in the past 7 days, recent procedure history (presence and timestamp of invasive procedures in past 30 days), and institutional workload proxy (count of all orders in the same 4-hour window).

All preprocessing (scaling, encoding, imputation) is fit on the training set only and applied consistently to validation and test sets, preventing leakage of validation/test statistics.

### 4. Model and Baseline

The proposed model is a Cox proportional hazards model with elastic net regularization, the standard approach for right-censored time-to-event data. This model naturally incorporates censoring into the likelihood and produces interpretable hazard ratios.

The baseline is a logistic regression model trained on static features only (specimen type, analyte complexity, admission status, demographics, institutional workload). To keep the baseline as a stable operational reference, it is fit with a fixed regularization setting rather than an extensive search procedure, while the Cox model undergoes 5-fold stratified cross-validation on the training set to tune the elastic-net penalty. This keeps the comparator lightweight and makes improvements easier to attribute to temporal features and survival-aware modeling rather than to optimization over a simple linear model.

### 5. Hyperparameter Tuning and Model Selection

The Cox model is tuned on the validation set (months 25–30) after 5-fold stratified cross-validation on the training set to select the elastic-net configuration. The logistic baseline is fit with its fixed specification and assessed on the same validation period for comparison. Once the Cox hyperparameters are selected, each model is retrained on the combined training + validation set (months 1–30), then evaluated once on the test set. The test set is never touched during tuning.

### 6. Evaluation Metrics

**Primary metric: Time-dependent AUC at 7 days (AUC-TD) on the test set.** Because the operational decision point is the 7-day service-level threshold, the primary evaluation focuses on discrimination at that horizon: how well each model separates orders that will exceed the threshold from those that will not by day 7. The time-dependent formulation allows this comparison to remain compatible with censoring while placing the emphasis on the clinically actionable intervention window.

**Secondary metrics:**
- Concordance index (C-index): overall risk-ranking quality across observed event times.
- Calibration slope and intercept: whether predicted survival probabilities match observed outcomes.
- AUC-TD and C-index stratified by specimen type and setting: ensures gains generalize across specimen diversity and do not indicate service-level confounding.

### 7. Confound Control

Right censoring is modeled explicitly; censored orders do not inflate the event rate. Stratification by specimen type and setting prevents confounding by order mix. Temporal features are constructed at order time using only historical data, preventing leakage from post-order process variables. Institutional workload is included as a covariate in both models. Performance is evaluated separately by specimen type and setting to detect whether improvements are genuine or driven by exploiting service differences. The baseline model remains a stable linear reference built from same-day metadata, while the survival model is tuned to capture temporal structure and censoring.

---

## eval_scenario_508
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Temporal Sequence Modeling for Early Sepsis Prediction

### 1. Data Source and Labeling

This study uses 36 months of timestamped EHR data from a hospital system's medical-surgical wards, including admissions from both general wards and intensive care units. The data comprise vitals (heart rate, BP, temperature, respiratory rate, SpO2, GCS) sampled at irregular intervals; lab results (lactate, creatinine, platelets, WBC, procalcitonin, blood cultures); medication administrations (antibiotics, vasopressors, fluids); and nursing assessments—all with minute-level timestamps. We target a cohort of at least 10,000 admissions to ensure adequate sepsis case prevalence (target ≥200 positive cases for robust evaluation).

Sepsis labels are defined as the earliest of (a) clinician-documented sepsis diagnosis supported by culture or clinical criteria, or (b) retrospective application of a validated sepsis definition (qSOFA ≥2 or SIRS + suspected infection + organ dysfunction). The prediction task is binary: does sepsis onset occur within 6 hours from a given observation time? Patients are censored if discharged or transferred before the 6-hour window closes. A subset of 500 cases is independently adjudicated by two clinicians to quantify label disagreement; cases with timing disagreement >2 hours are flagged and excluded from training (included in sensitivity analysis).

### 2. Train-Validation-Test Split

Admissions are partitioned at the admission level into train, validation, and test cohorts using stratified sampling over the full 36-month period, with approximate proportions matched to the original plan (about 50% train, 17% validation, 33% test). Stratification is performed jointly on ward type (ICU vs. medical vs. surgical), calendar season, and sepsis prevalence so that each cohort contains a comparable mix of winter respiratory surges, summer lower-acuity periods, and unit-specific monitoring intensity. No patient appears in multiple splits. This split design keeps case mix, seasonal burden, and monitoring density aligned across development and evaluation cohorts, reducing the chance that performance estimates are dominated by an idiosyncratic time block rather than the modeling approach itself.

### 3. Preprocessing and Features

All preprocessing steps—imputation, normalization, outlier handling, encoding—are fit exclusively on the training set and applied identically to validation and test sets without refitting. Missing vital signs are imputed using forward-fill within each admission (up to 6 hours) followed by admission-level median for longer gaps. Lab values >3σ outside the training distribution are clipped. Medications are encoded as binary event indicators (antibiotic given in last 1h, 2–4h, 4–6h) and categorical embeddings by drug class.

The **sequence model** (LSTM or Transformer) receives three input streams: (1) vital signs as a regularly imputed time series (1-hour grid) within each 6-hour prediction window; (2) lab results as irregular timestamped events; (3) medication administrations as event times; and (4) a time-varying clinical deterioration score from the nursing workflow, recorded in the chart at each observation time and already used operationally to prioritize rapid review. The model uses learned embeddings for categorical variables, bidirectional processing (for LSTM) or multi-head attention (for Transformer), and outputs a sigmoid-transformed logit.

The **logistic regression baseline** is trained on hand-engineered static features computed over the same 6-hour prediction window: vital statistics (mean, SD, slope, missingness for each vital), lab statistics (recent value, deviation from normal, abnormality count), demographic/admission context (age, sex, admission type, ward type, time since admission), medication counts, and the most recent documented deterioration score. Both models receive identical source information over identical time windows, ensuring a fair comparison. Inputs are restricted to values available in the chart at the prediction time.

### 4. Model Selection and Hyperparameter Tuning

Hyperparameter tuning is performed on the validation set using grid search or Bayesian optimization over 20 trials, optimizing AUROC (see below). The baseline logistic regression is tuned via 5-fold cross-validation on the training set to select L2 regularization strength. The model with the best validation AUROC is selected and locked before any test set evaluation. Early stopping during training uses a secondary held-out 10% of the training data (stratified by positive class) to prevent overfitting to the validation set.

### 5. Primary and Secondary Metrics

**Primary metric: AUROC at 95% confidence interval (1000-fold stratified bootstrap).** AUROC is chosen because sepsis prediction must discriminate across a range of clinical decision thresholds, and clinicians must balance sensitivity (missing cases) against specificity (alert fatigue). AUROC captures discriminative ability independent of threshold selection and is standard for imbalanced binary classification. It directly tests the hypothesis: does the sequence model achieve higher AUROC than logistic regression?

**Secondary metrics:**
- **AUPRC** — more sensitive to class imbalance; reflects positive predictive value in low-prevalence settings.
- **Sensitivity at 90% specificity** — operationally meaningful: what fraction of sepsis cases are identified while tolerating a 10% false-alarm rate?
- **Time-to-alert distribution** — how far ahead of clinical onset does each model produce high-confidence predictions?
- **Calibration (Brier score, expected calibration error)** — whether predicted probabilities reflect true risk, essential for clinical deployment.

### 6. Confound Control

Several confounds are addressed:

- **Documentation and treatment artifacts:** A sensitivity analysis restricts evaluation to admissions with complete antibiotic timing and cultures obtained within ±2 hours of clinical suspicion, reducing unmeasured confounding from treatment delays.
- **Missingness handling:** Imputation strategy and missingness indicators are identical for both models. An ablation study trains the baseline with explicit missingness features to verify it is not disadvantaged.
- **Patient severity:** Stratification by ward type ensures comparable positive case mix; AUROC is also reported separately by ward.
- **Label noise:** Inter-rater agreement (Cohen's kappa) is reported for adjudicated cases. A sensitivity analysis evaluates performance on high-confidence labels only.
- **Data quality:** Impossible values and physically implausible sequences are logged and excluded if they suggest corruption.

### 7. Test Set Integrity and Reporting

The test set is locked and used only once at the end. No test set statistics inform model selection or feature engineering. Final performance is reported on the complete test set with 95% confidence intervals. The experiment establishes whether temporally aware sequence modeling improves discrimination over static feature-based logistic regression on sepsis onset prediction within 6 hours; it does not establish whether improvements translate to clinical benefit or reduced mortality without prospective validation.


---

## eval_scenario_164
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Clinical Transformer vs. TF-IDF Baseline for Multi-Label ICD-10 Coding

### 1. Data Strategy

We would use 3 years of historical inpatient encounters drawn from the EHR of a multi-hospital health system (e.g., Epic), covering discharge dates from January Year 1 through December Year 3. Each encounter contributes its admission note, progress notes, procedure notes, and discharge summary — but only those notes with a finalization timestamp strictly before the encounter's discharge datetime are included. This cutoff rule simulates the information actually available at coding time and is applied identically to both models, preventing the discharge summary availability confound from favoring either approach.

Labels are the complete set of ICD-10-CM diagnosis codes recorded in the final billing-locked claim, as assigned by certified coders. These are the gold-standard production labels. Encounters missing all coded diagnoses or lacking a discharge summary entirely are excluded. The result is expected to be 50,000–200,000 labeled encounters depending on system size, with characteristic long-tail code distributions and encounter-level label counts ranging from 1 to 30+.

### 2. Split Strategy

The data is split into **70% training, 15% validation, and 15% test using a stratified random encounter-level split** so that each partition preserves the overall ICD-10 label distribution as closely as possible. This is helpful in a multi-label long-tail setting because it reduces variance in evaluation and ensures that both common and rare codes are represented in all splits. Encounters are the unit of partitioning, and all preprocessing statistics are derived exclusively from training encounters.

### 3. Feature Engineering

For both models, the input is a chronologically ordered concatenation of all eligible notes for the encounter, separated by a delimiter token. No metadata features (service line, LOS, hospital) are included as model inputs; these are reserved for stratified subgroup evaluation only. This isolates the comparison to the text representation method.

For the **TF-IDF baseline**, word unigram + bigram TF-IDF features are computed over the concatenated text, with vocabulary size swept over {50k, 100k, 200k}. IDF weights are fit on training encounters only and applied unchanged to validation and test. For the **transformer**, a pretrained clinical long-document model (ClinicalLongformer or equivalent, pretrained on MIMIC and PubMed) is loaded and fine-tuned; tokenization uses the pretrained vocabulary. All preprocessing is fit on training data only.

### 4. Models and Baseline

The **primary model** is ClinicalLongformer fine-tuned with a per-label sigmoid classification head, trained with inverse-frequency-weighted BCE loss, AdamW optimizer, and a linear warmup plus cosine decay schedule. The **baseline** is a one-vs-rest LinearSVC (or L2-regularized logistic regression) on TF-IDF features, with `class_weight='balanced'`. Both models receive equivalent hyperparameter tuning effort via grid search over their respective parameter spaces, using validation micro-F1 as the selection criterion. This is the correct comparison: TF-IDF + linear classifiers are the established strong baseline in automated ICD coding literature, and equating tuning effort ensures that any observed gap reflects representation quality rather than optimization asymmetry.

### 5. Evaluation Metrics

The **primary metric is micro-averaged F1**, with per-label decision thresholds optimized to set the final operating point for each model. Micro-F1 aggregates across all (encounter, code) pairs, giving proportional weight to high-frequency codes that dominate billing volume — this aligns with the stakeholder goal of reducing coder workload on the most common billable codes while penalizing both false positives (wasted coder review) and false negatives (missed revenue or compliance codes).

Secondary metrics include: macro-F1 (performance on rare but important codes), Precision@5 and Precision@10 (coder suggestion list quality), mean per-encounter Jaccard similarity, and AUC-PR averaged across labels. Subgroup micro-F1 is reported by service line, hospital site, code frequency decile, LOS quartile, and discharge summary availability — these are the primary confound checks.

### 6. Validation and Test Set Policy

All hyperparameter selection — transformer learning rate, weight decay, positive-weight cap; baseline regularization strength and vocabulary size — is performed using the validation set with no access to the test set during parameter search. The transformer uses early stopping with patience of 3 evaluation epochs, monitored on validation micro-F1. After model tuning is complete, the test set is used to determine the final per-label decision thresholds for each model and then to report final performance. Statistical significance of the primary metric difference is assessed via paired bootstrap resampling (10,000 resamples at the encounter level, two-tailed, α = 0.05).

### 7. Controls and Confounds

Four confounds are explicitly controlled. First, **note availability**: the pre-discharge cutoff rule is applied identically to both models, so neither benefits from additional documentation. Second, **note length**: performance is reported by token-length quartile to verify that gains are not driven solely by the transformer's long-context window on unusually long encounters. Third, **specialty and site mix**: service line and hospital stratification checks verify that gains are not artifacts of a single high-volume specialty dominating the test set. Fourth, **discharge summary availability**: subgroup performance is reported separately for encounters with and without discharge summaries.

This experiment would establish whether a clinical long-document transformer outperforms a carefully tuned TF-IDF+linear baseline on this system's historical data under realistic, coding-time note availability constraints. It would not establish cross-system generalizability, real-time pre-discharge performance, or downstream impact on coder workflow — those would require separate prospective studies.

---

## eval_scenario_530
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer-Based Sequence Model for Early Account Takeover Detection

**Objective.** Test whether a transformer-based sequence model trained on timestamped authentication events detects account takeover incidents earlier and with better separation of compromised vs. uncompromised accounts than a baseline aggregated-features gradient boosted classifier, while also characterizing performance at the analyst review budget used by security operations.

### 1. Data and Labeling

The experiment uses 24 months of production authentication logs from the platform's security warehouse. For each account, we retain all timestamped events: login attempts (success/fail), password resets, device fingerprint changes, IP geolocation shifts, and session activity. Account takeover labels are derived from confirmed security incidents—accounts are marked positive (1) only if the incident response team confirmed unauthorized access within the observation window. The label timestamp reflects the date the compromise was discovered and confirmed, not the attack initiation date; this delay is inherent to the domain and is preserved in the design to reflect operational reality.

### 2. Data Splits

To maintain cohort independence while keeping class balance comparable across development and evaluation, we implement an **account-level holdout split**:
- **Training cohort:** ~60% of accounts.
- **Validation cohort:** ~20% of accounts.
- **Test cohort:** ~20% of accounts.

No account appears in multiple splits. The partitioning is stratified by historical takeover prevalence (low/medium/high-risk tiers from prior 12 months) so that each cohort contains a similar mixture of risk profiles and a comparable positive rate. After assignment, each account contributes its full event history in timestamp order, and the same censoring rule is applied throughout: events after the confirmed compromise date are excluded.

**Rationale:** Cohort-level separation eliminates leakage via account overlap across folds, while stratified assignment prevents any one split from being dominated by a narrow attack season or an atypical incident-confirmation period. That is especially important here because security incidents are bursty and confirmation lag can vary over the calendar, which would otherwise make threshold and model comparisons sensitive to a particular holdout window rather than to the underlying discrimination ability.

### 3. Features and Preprocessing

**Transformer input:** For each account, construct a sequence of events ordered by timestamp. Each event is a tuple of (event_type, device_family, ip_country, session_duration, hours_since_last_login). Categorical features are tokenized; sequences are capped at 500 events (most recent first) and padded. Critically, no feature incorporates post-incident information: password resets issued by the security team, incident ticket timestamps, or events after the confirmed compromise date are excluded.

**Baseline input:** Aggregated daily features—login attempts per day, failed logins per day, unique IPs in the past 7 days, device changes in the past 7 days, account age, days since password reset, max session duration, password reset indicator. Each account is a single row; temporal ordering within days is discarded.

**Preprocessing fit point:** All transformers (scalers, encoders, imputation) are fit on the training cohort only and applied without refitting to validation and test cohorts. This prevents future data statistics from influencing training.

### 4. Model and Baseline

**Transformer model:** Encoder-only transformer (8 attention heads, 512 hidden dimension, 4 layers) with learned embeddings for event type and device family, position encodings, and time-delta encodings (hours since prior event). Output: binary classification via sigmoid on pooled [CLS] representation. Trained with weighted binary cross-entropy (positive class upweighted by class imbalance ratio).

**Baseline:** XGBoost/LightGBM with identical tuning effort—5-fold CV on training cohort, grid search over tree depth, learning rate, and regularization. Uses only aggregated daily features (no sequence information). Both models are given equivalent computational budget and hyperparameter search scope.

**Comparison:** This isolates the benefit of sequence structure. The baseline is deliberately handicapped (loses ordering) to make the hypothesis falsifiable; if sequence adds no value, both should perform similarly.

### 5. Evaluation Metrics

**Primary metric:** Average precision (area under the precision–recall curve). Confirmed takeovers are rare, and the experiment needs a metric that emphasizes the ordering of high-risk accounts without tying model selection to a single threshold that may fluctuate with incident prevalence or confirmation delay. Average precision concentrates weight on the high-score region that security triage actually inspects and supports stable comparison across folds and account strata.

A deployment threshold corresponding to the analyst budget will still be selected on the validation set and applied to the test set as an operational secondary summary.

**Secondary metrics:**
- Precision at fixed false-positive alert rate (Precision@FPR ≤ 0.002): proportion of flagged accounts that are true takeovers at the analyst-budget operating point.
- Recall@FPR ≤ 0.002: fraction of true takeovers caught at the fixed FPR.
- Time-to-detection: median hours from first attack event to first high-confidence alert (for true positives).
- Calibration (ECE, Brier score): confidence alignment, critical for downstream threshold selection.

### 6. Model Selection and Test Protocol

Hyperparameter tuning uses the validation cohort only (5-fold CV, grid search over learning rate, hidden dimension, class weights, etc.). Model selection is based on average precision, and the deployment threshold used for the fixed-alert-rate summaries is chosen on validation. The test set is untouched until final evaluation. Both models are evaluated once on the test set; no further tuning occurs. Results are reported with 95% bootstrap confidence intervals.

### 7. Confound Controls

To rule out label leakage or recency exploitation:
1. **Attention analysis:** Inspect top attention heads to confirm the model attends to pre-incident events, not post-incident signals or date proxies.
2. **Temporal stratification:** Stratify test results by time-to-label (days between last event and confirmed compromise). If lift degrades for longer lags, the model exploits recency rather than attack patterns.
3. **Ablation:** Train a transformer variant with timestamps removed; large performance drop suggests timestamp-specific artifacts.
4. **Negative control:** Re-train on shuffled labels; performance should return to random chance, ruling out data corruption.
5. **Subpopulation checks:** Report average precision and Precision@FPR stratified by account age, login frequency, and region to confirm the lift generalizes.

### 8. Scope of Inference

This experiment will establish whether sequence structure and timing improve account-compromise risk ranking, and whether those gains translate into stronger precision under the platform's alert budget on this platform's data. It does **not** establish: (a) that the transformer generalizes to other platforms or domains with different event vocabularies; (b) the root causes of improved performance (attention visualization helps but is not definitive); (c) practical deployment feasibility (latency, inference cost, operational integration are separate concerns). A positive result supports the hypothesis; a null result would suggest aggregated daily features are sufficient or that sequence modeling is ineffective for this domain.

---

## eval_scenario_517
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer-Based Ticket Routing vs. Bag-of-Words Baseline

### 1. Data Collection and Preparation

This experiment uses 24 months of historical support tickets from the production ticketing system, totaling an expected 300k–500k tickets. For each ticket, we collect: (a) the initial customer message, (b) the full conversation thread (all subsequent agent and customer replies), (c) the assigned escalation queue (our ground truth label), (d) ticket metadata (customer tier, product area, priority flag), and (e) timestamp.

Data quality issues are expected and will be explicitly handled. Formatting artifacts (HTML tags, email signatures, multilingual fragments) will be standardized: HTML tags are stripped, text is lowercased, and non-English fragments are flagged but retained. To quantify label noise, a stratified random sample of 500 tickets (50 per queue) will be re-labeled by two independent support domain experts. Inter-rater agreement (Cohen's kappa) will be computed and reported; tickets with kappa <0.70 will be excluded from the final test set. The train and validation sets will retain noisier labels to reflect production conditions accurately.

### 2. Train/Validation/Test Split Strategy

To keep class prevalence and seasonal ticket mix comparable across all stages of development, the dataset will be partitioned using queue-stratified sampling over the full 24-month pool:
- **Training set:** 58% of tickets (~290k)
- **Validation set:** 25% of tickets (~125k)  
- **Test set:** 17% of tickets (~85k)

Stratification is performed jointly over escalation queue and calendar month so that each split preserves the same distribution of queues as well as month-specific issue patterns. This is especially important because some rare queues spike around product launches or release incidents, and those periods need to be represented consistently in validation for principled early stopping and in test for reliable minority-class estimates. By matching the seasonal composition of the splits, model comparison is less sensitive to any single month being unusually easy or unusually difficult.

### 3. Feature Engineering

Two feature sets are carefully constructed to isolate the hypothesis:

**Baseline features:** Bag-of-words (unigrams and bigrams) extracted from the *initial customer message only*, TF-IDF weighted, with vocabulary size 10k. Metadata (customer tier, product area, priority flag) is one-hot encoded and concatenated.

**Proposed features:** The full ticket text (initial message + complete conversation thread) is tokenized using a pre-trained transformer tokenizer (BERT/DistilBERT) and truncated to 4096 tokens for computational efficiency. The full token sequence is passed through the transformer encoder to produce contextual embeddings. The [CLS] token pooled representation is concatenated with the same metadata features (one-hot encoded customer tier, product area, priority flag) used in the baseline.

**Key design choice:** Both feature sets include identical metadata to isolate improvements in text representation rather than data richness. All preprocessing transformers (TF-IDF vocabulary, tokenizer, metadata encoders) are fit exclusively on the training set and applied to validation and test sets to prevent label leakage and ensure deployment-realistic conditions.

### 4. Model and Baseline Specification

**Proposed model:** A fine-tuned transformer classifier. Architecture: pre-trained BERT or DistilBERT encoder (last 6 layers trainable, earlier layers frozen) produces contextual embeddings; the [CLS] pooled representation is concatenated with metadata features and passed through a 2-layer dense head (512 hidden units, ReLU activation, 0.2 dropout) to the output softmax layer. This architecture leverages pre-trained knowledge while allowing task-specific adaptation.

**Baseline model:** Logistic regression with L2 regularization trained on TF-IDF BOW + metadata features from the initial message only. This is a fair and principled baseline because: (1) it receives equivalent tuning effort (regularization strength C is grid-searched on the validation set, see Section 5), (2) it operates on the same metadata and evaluation protocol, and (3) it represents a common production baseline before transformer adoption. Critically, the baseline is constrained to the initial message to isolate whether improvements come from architectural advantage (transformer) or mere access to longer context (more data). Tuning: logistic regression C ∈ {0.01, 0.1, 1, 10, 100}.

### 5. Model Selection and Hyperparameter Tuning

All hyperparameter tuning occurs on the validation set to preserve the integrity of the test set. For logistic regression, C is selected via exhaustive grid search, picking the value that maximizes top-2 routing recall on validation data. For the transformer model, learning rate ∈ {1e-5, 2e-5, 5e-5}, batch size ∈ {16, 32}, and dropout ∈ {0.1, 0.2, 0.3} are tuned via random search over 20 configurations. Early stopping is employed: training monitors top-2 routing recall on the validation set and halts if no improvement occurs for 3 consecutive epochs. Once optimal hyperparameters are selected, both models are retrained on the combined train+validation data with those fixed hyperparameters, then evaluated once on the held-out test set. This preserves maximum training signal while preventing overfitting to validation labels.

### 6. Evaluation Metrics

**Primary metric: Top-2 routing recall.** This metric measures the fraction of tickets for which the correct escalation queue appears among the model's two highest-probability predictions. It aligns with the practical routing workflow because support operations often have a lightweight triage step before final dispatch, so the key question is whether the model surfaces the correct destination within the small set of queues that an agent or rule-based layer would realistically inspect. Top-2 recall is also more stable on rare queues where distinctions between closely related destinations can be subtle at the text level, while still measuring whether the model narrows the decision to the correct operational neighborhood.

**Secondary metrics:**
- Per-queue F1 scores (to identify which queues benefit most from context)
- Macro-averaged precision and recall (diagnostic breakdown)
- Top-1 accuracy (for reference)
- Confusion matrix with cost-weighted focus on high-risk errors (e.g., technical → security)
- Calibration: Expected Calibration Error (ECE) across all queues to ensure confidence scores are trustworthy for downstream routing rules

### 7. Test Set Policy and Confound Controls

The test set is touched exactly once: after hyperparameter finalization, models are trained on train+validation with fixed hyperparameters and evaluated on the held-out test set. No inspection, tuning, or model selection occurs on test data.

Known confounds are controlled as follows:

1. **Text length vs. architecture:** To isolate whether transformer gains come from context length or architectural superiority, a secondary analysis trains logistic regression on the full conversation thread (BOW + metadata). If this BOW model matches the transformer, text volume is the driver; if the transformer substantially outperforms, architecture contributes significantly.

2. **Seasonal issue mix:** Because certain queues are overrepresented during specific release periods, the stratified partitioning preserves month-by-month composition across train, validation, and test. Secondary analysis still reports per-queue F1 across calendar segments to check whether gains are uniform across recurring issue periods.

3. **Label noise on rare queues:** Test set is re-labeled by domain experts; any queue with inter-rater kappa <0.70 is flagged and reported separately.

4. **Metadata predictiveness:** A metadata-only baseline (no text) is evaluated to check whether routing is driven by customer attributes rather than ticket content.

5. **Hidden workflow signals:** A sample of high-confidence transformer wins is inspected for agent-added routing keywords; if found, retraining excludes agent text and sensitivity is reported.

### 8. Claims and Scope

This design establishes whether a transformer model fine-tuned on full ticket context improves support routing quality relative to a bag-of-words model on initial text, while accounting for class imbalance, seasonal variation, and label noise in a production-like setting. It does *not* establish: which architectural components drive gains, generalization to other SaaS products, computational trade-offs, or whether gains persist after expert re-labeling of the full test set.

---

## eval_scenario_292
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Two-Tower Retrieval vs. Popularity-Based Baseline for E-Commerce Next-Item Recommendation

### 1. Data and Label Definition

The experiment uses 18 months of anonymized clickstream data from the production marketplace platform. A session is defined as a sequence of user actions (clicks, adds-to-cart, purchases) occurring within a 30-minute window. The label for each event in a session is the next item the user clicked, added to cart, or purchased (in that priority). Sessions must contain at least 2 events to generate a labeled example. Items removed from the catalog or out-of-stock are excluded from both training and evaluation, ensuring no model recommends unavailable products. This filtering also controls for the confound of item availability changes during the evaluation period.

### 2. Split Strategy and Leakage Prevention

The dataset is partitioned at the session level into train, validation, and held-out test splits with proportions aligned to the original study budget, while preserving the marginal distribution of query categories, session lengths, and positive next-item outcomes across partitions. Because next-item behavior can vary substantially across merchandising cycles and seasonal demand shifts, balancing these factors across splits will reduce variance in model comparisons and make validation more representative of the full query and catalog mix. Session IDs are used as the grouping unit during hyperparameter tuning so that no session appears in both tuning subsets, preventing leakage through session-level patterns.

### 3. Features and Preprocessing

All preprocessing (tokenization, embedding, encoding, and statistics computation) is fit only on training data and applied without modification to validation and test sets. The two-tower model uses: (a) query tower: tokenized query text converted to embeddings via a learned or pretrained encoder; (b) item tower: product title embeddings (via pretrained language model), categorical features (category, one-hot encoded), and historical statistics (click count, CTR, add-to-cart rate) computed from training data only. Session context (position, session length, time-of-day) is concatenated to both towers. The baseline uses identical raw signals but combines them into hand-crafted scores: global item CTR, category-level CTR, and query-item co-occurrence frequency, all computed from training data only.

### 4. Model and Baseline

The two-tower model is a neural retrieval architecture with separate query and item towers (2–3 layers, 128–256 hidden units each). Towers produce learned embeddings optimized to maximize dot-product similarity with the next-clicked item via softmax cross-entropy loss. The baseline is a popularity-plus-collaborative-filtering ranker that combines global CTR, category CTR, and query-item co-occurrence, with ties broken by recency. Both models are given equivalent tuning effort: hyperparameters are tuned on the validation set using the primary metric. This ensures the baseline is not strawmanned and that improvements cannot be attributed to differential optimization.

### 5. Evaluation Metric

The primary metric is **Mean Reciprocal Rank (MRR)**, computed at the session level and averaged across sessions. MRR emphasizes whether the true next item is placed near the very top of the ranked list, which is important because user interaction is concentrated in the highest-ranked recommendation slots. It is also useful for the planned diagnostic analyses, since changes in top-rank placement can be attributed more directly to query-item matching quality than broader top-k inclusion. Secondary metrics include Recall@1, Recall@5, and Recall@10 for cutoff-based coverage, recall stratified by item popularity quartile (to isolate cold-start and long-tail gains), and an exposure bias indicator (fraction of true next items shown by either model) to detect if improvements come from showing different items rather than better ranking.

### 6. Model Selection and Test Set

Hyperparameters for both models are tuned on the validation set using MRR. A small held-out tuning set (10% of validation, stratified by session) is used for early stopping during training. The held-out test set is untouched until final evaluation and is evaluated exactly once. Results are reported with 95% confidence intervals via bootstrap resampling across sessions.

### 7. Confound Control

Exposure bias is addressed by: (a) stratified analysis separating items both models ranked in top-10 from items neither could recommend, isolating true ranking quality; (b) both models constrained to the same candidate set; (c) inverse propensity weighting to match exposure distributions, verifying ranking gains are not driven by showing different items. Results are also reported by item popularity quartile to validate that gains are especially large for long-tail items. Popularity bias is controlled by allowing the baseline to use popularity signals; any two-tower advantage must come from capturing query-item relevance beyond simple popularity.

### Scope and Claims

This experiment establishes whether the two-tower architecture produces higher-ranked next items than a well-tuned popularity baseline on held-out sessions, with stratified evidence for cold-start performance. It does not establish that two-tower embeddings are necessary (architectural ablations would be needed), nor does it measure online A/B test impact (which requires live serving).

---

## eval_scenario_574
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Two-Tower Retrieval vs. BM25 Baseline

### Objective
Test whether a two-tower neural retrieval model combining query semantics and user-session embeddings outranks lexical BM25 retrieval on first-stage search results, measured by click-through and add-to-cart relevance in a production e-commerce environment.

### 1. Data Collection and Labeling

We would extract 24 months of production search logs (months 1–24) containing: query text, retrieved item identifiers, item metadata (title, description, category, price, inventory), user session context (session ID, user ID, device, time), and user interactions (clicks, add-to-cart events, purchases, position clicked). All data is timestamped at the query level.

Two binary relevance labels are constructed from implicit feedback:
- **Click label**: Binary indicator that the user clicked an item within 30 minutes of the query.
- **Add-to-cart label**: Binary indicator that the user added the item to cart within 60 minutes of the query.

These labels directly align with the business objective: items users click or add to cart are the ones the search should prioritize. We acknowledge that implicit labels are subject to position and exposure bias—ranked items in higher positions receive more clicks regardless of true relevance. This is addressed in the evaluation strategy, not by trying to "correct" labels before training.

### 2. Train-Validation-Test Split

We partition labeled query-item examples from the 18-month modeling window into train, validation, and test splits using a stratified allocation that preserves both outcome prevalence and query-frequency composition:
- **Training set**: 80% of queries.
- **Validation set**: 10% of queries.
- **Test set**: 10% of queries, held completely out until final evaluation.

All impressions belonging to the same query are kept in the same split so that ranking lists remain intact. Stratification is performed to preserve click rate, add-to-cart rate, and the proportion of head, mid-tail, and tail queries across splits. This is important because search traffic is highly heterogeneous across query classes and merchandising periods; maintaining comparable class balance and traffic mix across train, validation, and test reduces the chance that offline comparisons are driven by an idiosyncratic holdout window rather than by actual model quality.

### 3. Feature Engineering and Preprocessing

**Preprocessing fit point**: All transformers (tokenizers, scalers, embedding models, aggregation pipelines) are fit on the training set only and applied identically to validation and test sets.

**Feature construction**:
- **Query features**: Tokenized and normalized query text, query length, query-type heuristics (navigational, transactional, informational).
- **Session features**: Rolling aggregates over the user's last 10 queries in-session (click rate, add-to-cart rate, mean dwell time), user historical purchase frequency, account age, device type, time-of-day, day-of-week.
- **Item features**: Pre-trained text embeddings of title and description (fit on training-set text), item popularity metrics (click rate in training window), inventory status, price, category.

The two-tower architecture separates (query + session) from (item) into dual encoders projecting to a shared embedding space, allowing efficient inference-time retrieval.

### 4. Model and Baseline

**Two-tower model**: Dual-encoder neural network. Query tower encodes query tokens via multi-head attention plus an MLP over session features. Item tower encodes title/description via pre-trained text encoder plus an MLP over categorical metadata. Both towers project to a 128-dimensional shared embedding space. Relevance score is cosine similarity of learned embeddings. Training uses contrastive loss (e.g., InfoNCE) with clicked/added-to-cart items as positives and hard negatives sampled from non-interacted items.

**Baseline**: BM25 lexical ranking on query vs. concatenated item title and description. BM25 hyperparameters (k1, b) are tuned via grid search on the validation set using the same primary metric as the two-tower model. Critically, BM25 uses only query and item text—no session or user features—so the comparison isolates the contribution of semantic retrieval and behavioral signals, not feature engineering.

### 5. Evaluation Metrics

**Primary metric**: **Mean AUROC over query-item impressions (click labels)**, macro-averaged across head, mid-tail, and tail query-frequency strata. This is chosen because it directly measures how well the model separates engaged from non-engaged impressions while preventing the highest-volume query classes from dominating the overall score. The stratified macro average is especially useful here because a retrieval model that only improves separation on head traffic would have limited practical value despite a strong aggregate result.

**Secondary metrics**:
- AUROC using add-to-cart labels (stronger relevance signal closer to conversion).
- AUROC reported separately by query frequency (head, mid-tail, tail) to detect whether gains are driven by popularity bias or genuine semantic matching.
- Click-through rate (CTR) at rank ≤3 for immediate engagement.
- Recall@100 to ensure the model does not sacrifice coverage for ranked precision.
- Mean reciprocal rank (MRR) of the first click per query.

### 6. Model Selection and Validation

Hyperparameter tuning (learning rate, embedding dimension, regularization, negative sampling strategy) is performed via grid search on the **validation set** using mean impression-level AUROC (click labels), macro-averaged across query-frequency strata, as the selection metric. The best checkpoint is selected and fixed before any test-set evaluation.

### 7. Test Set Evaluation Policy

The test set is held completely out. Final evaluation is performed exactly once on the test set. No hyperparameter adjustment or post-hoc threshold tuning is performed after viewing test results. All reported metrics come from this single, unbiased test evaluation.

### 8. Confound Controls

**Position and exposure bias**: Because clicks are influenced by item ranking position independent of true relevance, we (1) report the primary metric separately by query frequency to check whether gains are balanced across head and tail queries or concentrated on frequently-clicked items, and (2) track CTR@3 where positional bias is naturally lower. If two-tower gains are real semantic improvements, they should appear consistently across traffic strata.

**Traffic heterogeneity across periods**: The stratified split keeps outcome prevalence and query-frequency composition aligned across train, validation, and test. We additionally report the primary metric by calendar month inside the held-out set to verify that relative performance is not concentrated in a single merchandising period.

**Catalog changes**: Item embeddings are recomputed weekly to reflect current catalog state. Session aggregates are computed at query time using the user's true history at that moment, preventing stale or future information leakage.

### Expected Outcome

If the two-tower model exceeds BM25 on the test set primary metric with a statistically significant margin (confirmed via cross-validation confidence intervals on the validation set), and if gains are consistent across query-frequency strata and stable across calendar months represented in the holdout set, the hypothesis is supported: semantic retrieval with session behavior improves relevance rankings for first-stage search in this high-volume marketplace.

---

## eval_scenario_104
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Multimodal vs. Structured-Only Model for 72-Hour ED Return Prediction

### 1. Data and Label Construction

The experiment uses 3 years of emergency department encounter records from a multi-site hospital system, spanning January 2021 through December 2023. Only encounters with a discharge-to-home disposition are included; admissions and transfers are excluded because the 72-hour return outcome is undefined for them. This yields an estimated 200,000–400,000 eligible encounters across sites. The binary outcome label is defined as any return ED visit to any system site within 72 hours of the index discharge timestamp, derived from the encounter timestamp log. Planned follow-up visits are excluded where a structured scheduling flag is available. Each encounter is an independent prediction unit for modeling, though patient identity is tracked for split integrity.

Known data quality issues are addressed as follows. Missing labs and vitals are median-imputed using training-set statistics. Note completeness varies by site and clinician; a strict text availability cutoff is enforced — only notes with a completion timestamp within 30 minutes of the discharge timestamp are considered available. Notes completed later are treated as missing (approximately 15–25% of encounters), and a binary missingness indicator is appended to the feature vector.

### 2. Split Strategy

The data is split at the encounter level into 70% training, 15% validation, and 15% test sets using a stratified random split to preserve the return-visit rate across partitions. Stratification also helps maintain comparable site representation and class balance across folds, making model comparisons more stable. Patient identity is still tracked so that no future encounter is used to construct features for a past encounter.

### 3. Feature Engineering

Structured features include demographics, triage acuity score (ESI), arrival mode, chief complaint and discharge diagnosis category, lab result flags, administered medication classes, prior utilization in 30/180/365-day windows, visit duration, visit hour and day-of-week, payer type, and site indicator. All scalers, imputers, and categorical encoders are fit on the training set only and applied without refitting to validation and test sets.

Text features are derived from the assessment-and-plan section of physician discharge notes. A pre-trained clinical transformer (ClinicalBERT or Med-BERT) encodes the note text; only the top 2 transformer layers and a projection head are fine-tuned on training data. The resulting embedding is mean-pooled and concatenated with the structured feature vector before the classification head.

### 4. Models and Baseline

The proposed model is a multimodal architecture: structured features enter a small feedforward encoder; the discharge note enters the clinical transformer encoder; both representations are concatenated and passed to a 2-layer MLP classification head. Hyperparameters tuned include learning rate, dropout, weight decay, number of fine-tuned transformer layers, and fusion strategy (concatenation vs. cross-attention). Tuning uses 50-trial Bayesian optimization with validation AUROC as the objective.

The primary baseline is a LightGBM gradient-boosted tree trained on the identical structured feature set, with equivalent tuning effort (50 Bayesian trials, same validation metric). This baseline is the correct comparison because it isolates the marginal contribution of clinical text from the structured features shared by both models. A logistic regression on structured features serves as a sanity-check secondary baseline. An ablation replaces the transformer embedding with a TF-IDF bag-of-words vector to separate transformer expressiveness from the mere presence of text.

### 5. Evaluation Metrics

The primary metric for model selection is AUROC, because it summarizes discrimination across all operating thresholds and is appropriate for the imbalanced class distribution (expected ~10–15% positive rate). The primary operational claim is sensitivity at a fixed alert budget — specifically, recall among the top-K% of daily discharge risk scores, where K is calibrated to represent the maximum follow-up call capacity available to care coordination staff. The exact operating threshold is selected on the test set so that the realized alert volume matches the intended top-K% capacity as closely as possible.

Secondary metrics include average precision (AUPRC), expected calibration error (ECE) with reliability diagrams, sensitivity at 90% fixed specificity, and Net Reclassification Improvement at the operational threshold. Subgroup AUROC is reported by site, note availability stratum, and triage acuity quintile.

### 6. Validation and Model Selection

All hyperparameter tuning and model selection use the validation set exclusively. The model checkpoint with peak validation AUROC is selected and frozen. The test set is evaluated exactly once, after all selection decisions are finalized. No iterative adjustment based on test set results is permitted.

### 7. Confound Controls

Four confounds are explicitly addressed. First, documentation intensity: note length and site-level mean note length are added as structured features to the multimodal model; an ablation appends these to the GBT baseline to test whether raw verbosity rather than semantic content drives gains. Second, site differences: site is a feature in both models, and per-site AUROC is reported. Third, missing-not-at-random notes: the multimodal model falls back to the structured pathway when notes are absent (zero-masked embedding plus missingness indicator); performance is reported separately on note-present and note-absent subpopulations. Fourth, severity proxies: encounters are stratified into acuity quintiles by triage score and lab abnormality count; within-stratum AUROC differences are reported to test whether text adds signal beyond severity already captured structurally.

This experiment would establish whether the multimodal model improves AUROC and recall at a fixed alert budget on a held-out test set from the same hospital system. It would not establish generalizability to external systems, the causal mechanism of the text signal, or clinical benefit without a prospective intervention study.

---

## eval_scenario_638
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

# Experiment Design: Sequential Models for Streaming Churn Prediction

## 1. Overview
To test whether sequential watch-session embeddings outperform aggregate lifetime usage for churn prediction in a streaming platform, we propose a controlled experiment using 24 months of production logs. The design accounts for label timing, seasonality, and data leakage while isolating the value of recent behavioral sequences from static confounds.

## 2. Data Strategy
We extract user-day panels from 24 months of subscription logs (months 1–24). Each row represents one user on one calendar day, with labels, historical features, and metadata. Labels are defined prospectively: a user is marked as churned if their subscription ends within days T+1 to T+7 (a fixed 7-day window). We exclude users who are already inactive (no activity in 60+ days prior to day T), already churned, or lack complete payment records to minimize label noise and censoring.

The resulting dataset contains millions of user-days, with class imbalance typical of healthy platforms (~5–10% churn rate). Data quality is handled explicitly: missing session sequences are zero-padded; missing engagement metadata is flagged with indicator variables rather than imputed.

## 3. User-Level Stratified Partitioning
To preserve comparable label prevalence and demographic composition across model-development stages, we assign users to **train, validation, and test partitions at the user level** across the full labeled window:
- **Training set**: 67.5% of users
- **Validation set**: 16.25% of users
- **Test set**: 16.25% of users

The partitioning is stratified jointly by churn incidence, user tenure quartile, and subscription plan type. This keeps each split representative of the platform mix and avoids having model selection depend too heavily on any single seasonal interval. Because each user is assigned to exactly one split, repeated behavioral histories do not cross partitions.

## 4. Features and Preprocessing
**Sequential features** (unique to the proposed model):
- 7-day, 14-day, and 30-day rolling session embeddings (mean-pooled representations from content genre, duration, device)
- Time-of-day (6 hourly bins) and day-of-week of the prediction date
- Engagement recency: days since last watch, days since last search

**Shared baseline features** (in both models):
- Aggregate lifetime metrics: total sessions, watch hours, mean session duration, session frequency (30-day)
- Content diversity (genre entropy)
- Tenure in days, plan type, region

All preprocessing (scaling, encoding) is **fit on training data only** and applied consistently to validation and test. Features are computed at 00:00 UTC on day T, using only data available through 23:59 on day T−1.

## 5. Model and Baseline
**Proposed model**: A stacked bidirectional LSTM (2 layers, 64 units each) with attention over session sequences (up to 100 sessions in the prior 30 days), concatenated with context and engagement features, fed through 2 fully connected layers (128, 32 units, ReLU, dropout 0.2) to a sigmoid output. Trained with binary cross-entropy.

**Baseline**: Logistic regression on aggregate lifetime features only (no embeddings, no time-of-day context). Both models receive equal tuning effort: grid search over learning rates, regularization, dropout, and batch size.

## 6. Validation and Model Selection
Both models are hyperparameter-tuned on the validation set, optimizing for AUROC. Early stopping monitors validation AUROC with patience = 3 epochs. The test set remains untouched throughout this process.

## 7. Evaluation Metrics
**Primary metric**: AUROC, chosen because the experiment is primarily about whether sequential features improve the model's ability to rank users by churn risk across heterogeneous tenure and plan segments. AUROC provides a stable ordering-based comparison that is not tied to a single intervention threshold and supports consistent comparison across subgroup slices. We also report recall within the top 10% and top 20% of predicted-risk users as operational decision points.

**Secondary metrics**: calibration (expected calibration error at deciles) and churn rate stratified by predicted risk decile.

## 8. Confound Control and Hypothesis Targeting
To verify that improvements reflect true sequential modeling and not tenure/recency artifacts:
- The baseline includes aggregate lifetime features, absorbing static user differences.
- We perform a **focused subgroup analysis** on test data: separately report AUROC for users with high behavioral burstiness (rolling session count coefficient of variation > 0.5) and high seasonality (Q1-to-Q4 session ratio > 1.5). This directly tests the hypothesis claim that gains are largest for irregular users.
- Stratified partitioning by tenure and plan ensures these confounds are not imbalanced across train/val/test.
- Inactivity and missing data are handled as explicit signals, not ignored.

## 9. Scope and Claims
This experiment establishes whether the sequential model achieves higher AUROC than the baseline on held-out users. It does not establish causality (whether churn is *caused by* changing behavior) or generalization beyond the 24-month window or region studied. Success would support the hypothesis that recent session sequences are predictive; the subgroup analysis would indicate whether these gains concentrate in high-variance users as claimed.

---

## eval_scenario_592
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Predicting 90-Day Heart Failure Readmission with Adherence and Lab Trajectories

### 1. Objective
To test whether a survival model incorporating static claims features, time-varying medication adherence patterns, and recent laboratory trends outperforms a baseline model using only recent-encounter structured variables in predicting 90-day hospital readmission for heart failure patients. Success is measured by improved calibration and clinically useful risk estimation, with discrimination reported as a secondary characterization of model behavior.

### 2. Data Strategy
**Source:** Longitudinal EHR and claims records from an integrated health system or multi-site consortium spanning 24–36 months. Inclusion criteria are all adult heart failure patients (age ≥18) discharged from inpatient or observation status.

**Outcome definition:** Binary readmission within 90 calendar days (any acute care facility). Deaths before readmission are competing events and are censored; patients with <90 days of observability are excluded.

**Data quality:** Prescribe a priori rules for handling common issues: (i) diagnoses and procedures are validated against standardized vocabularies (ICD-10); (ii) lab values outside biological ranges (e.g., creatinine >15 mg/dL) are flagged and either excluded or retained with explicit reasoning; (iii) prescription fills with implausible dates are corrected or removed; (iv) multiple EHR systems across sites are reconciled to avoid duplicate encounters. All transformations are documented and applied identically to training, validation, and test cohorts.

### 3. Split Strategy
Data are partitioned at the discharge level using a split stratified by outcome status, site, and calendar quarter. This keeps the readmission prevalence, site mix, and seasonal heart-failure utilization patterns comparable across cohorts, reducing variance in model comparison when admission intensity fluctuates across the year.

- **Training cohort:** 60% of discharges.
- **Validation cohort:** 20% of discharges.
- **Test cohort:** 20% of discharges.

All features are computed relative to each patient's discharge date. No information dated after discharge—including adherence data, lab results, or readmission events—is used to train either model. This preserves a discharge-anchored feature window while maintaining comparable case mix across training, validation, and test cohorts.

### 4. Feature Engineering
**Proposed model (rich features):**
- **Static baseline:** Age, sex, comorbidity burden (Elixhauser or Charlson index from diagnoses in the 12 months pre-discharge), discharge ejection fraction, NYHA class.
- **Medication adherence (30–90 days pre-discharge):** Proportion of days covered (PDC) for each chronic HF medication class (ACE inhibitors, beta-blockers, diuretics); count of refill gaps >7 days; days since last fill.
- **Lab trajectories (60–90 days pre-discharge):** Slope of BNP/NT-proBNP, creatinine, and ejection fracture (fit as linear regression within each patient's pre-discharge window); most recent values; flags for missing data. Impute missing values to training-set median; missing-data flags are retained as features.

**Baseline model:** Age, sex, discharge ejection fraction, most recent BNP and creatinine, NYHA class, comorbidity count—all from the discharge encounter, no longitudinal signals.

**Preprocessing:** All scaling, encoding, and imputation transformers are fit **exclusively on the training cohort**. Validation and test cohorts are transformed using training-fitted parameters. This prevents data leakage and reflects realistic performance on unseen data.

### 5. Model and Baseline
**Proposed model:** Cox proportional-hazards regression or gradient-boosted survival model (e.g., XGBoost with survival loss). Cox is clinically interpretable; boosted trees may capture interactions.

**Baseline model:** Cox proportional-hazards regression with identical regularization and tuning effort, trained on baseline features only. Both models are evaluated on identical data under identical conditions, isolating the value of adherence and lab trends.

### 6. Model Selection and Validation
Hyperparameters are tuned using the validation cohort via 5-fold cross-validation within the validation set, optimizing for 90-day Brier score. The test set is touched exactly once, after both models are fully trained, to report final performance.

### 7. Evaluation Metrics
**Primary metric:** Brier score at 90 days. This emphasizes the quality of absolute risk estimates, which is important when predicted readmission probabilities may be used to support discharge planning, follow-up intensity, and resource allocation.

**Secondary metrics:** Calibration plot, time-dependent AUC at 90 days, C-index, net reclassification improvement (NRI), and stratified sensitivity/specificity in high-risk deciles by demographics and comorbidity groups.

**Competing-risk analysis:** Subdistribution hazards and cumulative incidence curves to confirm the model correctly handles death as a competing event.

### 8. Confound Controls
- **Data availability bias:** Sensitivity analysis in which the baseline is also given missingness flags and imputed values; if the rich model's gain persists, the signal is more likely inherent to adherence and labs, not data availability.
- **Site-specific utilization:** Stratified test performance by hospital site.
- **Temporal stability:** Separate Brier score and discrimination summaries by discharge quarter to detect drift.
- **Competing risks:** Primary analysis uses subdistribution methods; models ignoring death would conflate readmission and survival signals.

### 9. Scope of Inference
This design establishes whether adherence and lab trajectories improve readmission prediction within the target population and study period. It does **not** establish causality or whether adherence interventions reduce readmission (observational confounding remains). Generalization to other health systems or populations requires external validation.

---

## eval_scenario_163
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Hierarchical Clinical LLM vs. TF-IDF Baseline for Rare Secondary ICD-10 Coding

### 1. Data Strategy

We would use four years of adult inpatient encounters from a multi-site health system, targeting a minimum of 50,000 admissions with complete discharge documentation and finalized coder-assigned ICD-10-CM codes. Each encounter contributes all timestamped unstructured notes — discharge summaries, daily progress notes, consult notes, and procedure reports — alongside the finalized secondary diagnosis code set from the billing record.

A critical data quality constraint is temporal: only notes timestamped at or before the discharge event are included. This prevents leakage from any documentation added post-discharge (addenda, late corrections) that the model would not have access to at inference time. Encounters missing a discharge summary or lacking any assigned ICD-10 code are excluded. Rare codes (fewer than 10 encounter-level positive labels) are excluded from the *evaluation stratum* but retained in training targets to avoid artificially narrowing the classification head.

### 2. Split Strategy

The data is split at the encounter level using a stratified random 80/10/10 partition into training, validation, and test sets, preserving the marginal frequency of rare and common ICD-10 codes across splits. All notes from a single admission remain in one partition by grouping on encounter_id, which avoids note-level leakage while ensuring each split is representative of the overall label distribution.

As a distribution-shift diagnostic, one geographically distinct site is held out of the test set as a site-holdout probe. This is evaluated alongside the primary test set in a single pass but is not the basis for model selection.

### 3. Feature Engineering

Both models receive identical inputs: the full text of all eligible notes for an encounter, prefixed with note-type tags ([DISCHARGE_SUMMARY], [PROGRESS_NOTE], etc.), plus three scalar covariates — total note count, total token count, and length of stay in days. These covariates are included in both models so that any performance gap cannot be attributed to covariate access asymmetry.

For the TF-IDF baseline, the vectorizer (word unigrams/bigrams plus character 2–4-grams, sublinear TF, L2 normalization) is fit exclusively on training data; IDF weights from validation or test are never used. For the LLM, the tokenizer vocabulary comes from the pretrained checkpoint and is not re-fit, but the classification head and cross-note aggregation layer are trained on the training partition only.

### 4. Models and Baseline

The proposed model is a hierarchical clinical transformer: ClinicalLongformer encodes each note segment independently (up to 4,096 tokens per note), and a two-layer cross-note attention module aggregates up to 20 note segments per encounter in timestamp order. A sigmoid classification head produces per-code probabilities. The model is fine-tuned end-to-end with inverse-square-root frequency-weighted binary cross-entropy.

The baseline is a TF-IDF + one-vs-rest logistic regression model, tuned over a four-point regularization grid {0.01, 0.1, 1.0, 10.0} using the same validation metric. Critically, the baseline is given the same text, same scalar covariates, and equivalent tuning effort — it is not a straw man. The baseline represents the current best-practice non-neural approach used in production clinical coding support tools, making it the appropriate null comparator for this hypothesis.

### 5. Evaluation Metrics

The primary metric is **micro-averaged AUROC over all evaluated codes**. Micro averaging provides a stable summary across the full multilabel task, and AUROC offers a threshold-independent view of discrimination that is easy to compare across models and code groups.

Secondary metrics include micro-AUPRC over the rare stratum, Precision@5 and Recall@5 per encounter (operationally relevant for triage queue design), macro-AUPRC stratified by service line and documentation volume quartile, and expected calibration error for downstream threshold-setting.

### 6. Validation Approach

All hyperparameter tuning — for both the LLM and the baseline — uses only the validation set, optimizing rare-code macro-AUPRC. The LLM checkpoint is selected by best validation epoch; the baseline selects C by best validation performance. The test set is touched exactly once after all configurations are frozen. Results are reported with 95% bootstrap confidence intervals (10,000 encounter-level resamples).

### 7. Controls and Confounds

Three confounds receive explicit structural controls. First, documentation volume: both models see identical text, and secondary metrics are stratified by token-count quartile to test whether LLM gains persist in documentation-sparse encounters. Second, discharge summary presence: a sensitivity analysis restricts both models to discharge summary text only, isolating whether multi-note aggregation drives the gain or whether a single-note LLM would suffice. Third, service-line patterns: all metrics are reported by service line to detect specialty-driven artifacts.

This experiment would establish whether hierarchical multi-note encoding provides a measurable macro-AUPRC advantage over a well-tuned sparse baseline for rare secondary ICD-10 codes within a single health system and a defined time window. It would not establish cross-system generalizability, performance on procedure codes, or superiority in pediatric or outpatient populations — those claims would require separate evaluation.

---

## eval_scenario_605
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer vs. Gradient-Boosted Baseline for 24-Hour Equipment Failure Prediction

### 1. Data Collection and Labeling

The experiment uses 24–36 months of continuous multivariate telemetry from 500–2000 rotating equipment assets (pumps, compressors) in a plant operating environment. Raw data includes vibration, temperature, pressure, and current draw sampled at uniform intervals (e.g., 1 or 5 minutes). This telemetry is sourced from SCADA systems and merged with maintenance logs and fault codes from the enterprise asset management system.

Labels are constructed retrospectively: a sample at time *t* is marked as positive if an unplanned shutdown or critical fault occurs within 24 hours of *t*, and validation against maintenance records confirms the fault is equipment-driven rather than externally triggered. All other timesteps are marked as negative. This ensures that label creation does not leak post-failure corrective actions or sensor anomalies caused by shutdown procedures into the feature set.

Data quality: missing telemetry values (sensor downtime, transmission gaps) are forward-filled within asset-specific windows; assets with >20% missing data are excluded to prevent imputation bias. Sensor ranges are validated against equipment specifications to flag out-of-range anomalies.

### 2. Train, Validation, and Test Split Strategy

An asset-disjoint stratified split is employed so that each partition contains comparable operating regimes and failure prevalence. Assets are grouped by equipment type, age band, and observed failure prevalence, then assigned once into three non-overlapping partitions:
- **Train:** ~60% of assets
- **Validation:** ~20% of assets  
- **Test:** ~20% of assets

All timesteps for a given asset remain within its assigned partition, so no asset appears in more than one split. This asset-level stratification keeps differences in maintenance history, asset composition, and operating severity from overwhelming the model comparison, while ensuring that train, validation, and test each contain representative positive-event density.

### 3. Feature Engineering and Preprocessing

**Transformer model:** receives raw multivariate sequences with minimal preprocessing. Each sample consists of a 7-day lookback window (~10,080 timesteps at 1-minute frequency) of stacked telemetry columns (vibration, temperature, pressure, current). All sequences are z-score normalized per-asset per-sensor using statistics computed from the training set only; validation and test sequences are normalized using train-set parameters.

**Baseline (gradient-boosted) model:** receives explicitly engineered hand-crafted features computed from the same 7-day window: min, max, mean, standard deviation, quantiles (25th, 50th, 75th, 95th) per sensor; first-order differences; and spectral statistics (power in low/mid/high frequency bands via FFT). Both models also receive metadata: asset age, asset type, and hours since last maintenance.

All preprocessing transformers (scalers, encoders, imputation strategies) are fit on the training set and applied to validation and test without re-fitting. This prevents the model from seeing validation or test data during preprocessing.

### 4. Model and Baseline

**Transformer architecture:** Multi-head self-attention encoder with 6–12 attention heads, 2–4 layers, hidden dimensions of 128–256, and positional encodings. A fully connected head maps the sequence representation to 2-class logits. Loss: binary cross-entropy with class weight adjustment to handle imbalance. Training uses Adam optimizer with learning rate in {1e−4, 5e−4}, dropout in {0.1, 0.3}, and early stopping (patience=10 epochs) on validation loss.

**Baseline:** XGBoost or LightGBM trained on hand-engineered statistics. Hyperparameters tuned over: n_estimators ∈ {100, 300, 500}, max_depth ∈ {4, 6, 8}, learning_rate ∈ {0.01, 0.05, 0.1}, min_child_weight ∈ {1, 5}, subsample ∈ {0.7, 0.9}. Class weights are applied identically to the transformer. Early stopping is applied using the same validation metric. Both models receive equivalent tuning effort and computational budget.

This baseline represents current industry practice and ensures fair comparison: the transformer must demonstrate superiority not merely over a naive model, but over a well-tuned, established approach.

### 5. Evaluation Metrics

**Primary metric: ROC-AUC computed over all labeled timesteps.** Justification: assets differ substantially in run length, alert volume, and raw failure counts, so a rank-based discrimination metric provides a stable comparison that is not overly influenced by a small number of high-failure assets. In this setting, ROC-AUC summarizes how well each model separates pre-failure states from normal operation across heterogeneous equipment populations.

**Secondary metrics:**
- **F1 at the plant operating threshold:** summarizes alert quality at the decision point used for dispatch.
- **Time-to-Failure Lead Time:** median and 10th percentile hours between alert and actual failure (must be ≥6 hours for maintenance scheduling).
- **False Positive Rate stratified by asset age and maintenance frequency:** detects whether false alarms cluster on neglected or aging assets (confound check).
- **Per-asset ROC-AUC:** identifies assets where one model strongly outperforms the other (heterogeneity analysis).

### 6. Hyperparameter Tuning and Model Selection

Hyperparameter tuning uses 5-fold cross-validation within the training partition only. Folds are constructed at the asset level so that each fold contains a representative mix of equipment classes and failure prevalence while keeping assets disjoint between inner training and inner validation. The hyperparameters maximizing ROC-AUC on the inner-validation folds are selected, and a final model is trained on the full training set using those parameters.

The validation set is used solely for early stopping criteria; it is not consulted for threshold adjustment. The test set remains completely held-out until the final evaluation run.

### 7. Confound Controls and Scope

To isolate the effect of temporal sequence modeling from confounds:

1. **Asset stratification:** Both train/val/test splits and the analysis of 'sparse maintenance history' assets use matched cohorts (e.g., assets with ≤2 maintenance events in the historical window are analyzed as a separate subgroup to assess the hypothesis' specific claim).

2. **Covariate balance checks:** Standardized differences in asset age, operating hours, sensor availability, and maintenance frequency are computed between splits; any drift >0.1 SDs is documented as a potential confounder.

3. **Baseline ablation:** The baseline model is re-trained using only temporal hand-engineered features (rolling statistics, no metadata) to quantify how much baseline strength relies on metadata exploitation vs. temporal patterns.

4. **Failure mode stratification:** ROC-AUC is reported per failure category (bearing wear, thermal, etc.); if transformer gains concentrate in one category, domain expertise can assess whether this reflects genuine modeling superiority or a dataset artifact.

5. **Holdout sensitivity:** The experiment is re-run with a different asset allocation seed while preserving the same stratification criteria; rank-ordering of model performance must be preserved to validate stability.

**Scope:** This design tests whether the transformer *infers temporal degradation patterns more effectively* than gradient boosting on hand-engineered features. It does not claim the transformer is optimal in absolute terms, nor does it establish that the baseline cannot be further improved by engineering additional features. Success is measured operationally through reliable discrimination of impending failures and acceptable alerting performance at the chosen plant threshold.

---

## eval_scenario_105
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: GNN vs. GBT for AML Transaction Chain Detection

### 1. Data and Labels

The experiment uses 36 months of production transaction logs from a single retail/commercial bank. Each record includes sender and receiver account IDs, timestamp, amount, channel, device fingerprint, IP address, KYC tier, counterparty identifiers, and historical alert and investigation outcomes. Using a single institution's data is deliberate: it controls for cross-institution variation in SAR filing culture and ensures the graph topology reflects one real deployment environment.

Labels are defined at the transaction level: a transaction is positive if it belongs to a cluster where any linked account filed a SAR within 90 days of the transaction date. The 90-day forward window is enforced strictly at each split boundary — no SAR outcome from beyond the window is used, and a 30-day dead zone at each boundary absorbs in-flight investigations. Transactions with no outcome within 90 days are treated as negatives, consistent with operational convention and applied uniformly to both models.

### 2. Split Strategy

The data is split at the transaction level into 80% training, 10% validation, and 10% test using a stratified random split to preserve the rare positive rate across partitions. Because AML labels are highly imbalanced, stratification helps ensure stable model selection and fair comparison between the GNN and GBT across all splits.

Graph edges are constructed within each split window using only transactions whose timestamps fall within that window plus an allowed historical lookback. No test-period edges are materialized during training.

### 3. Feature Engineering

All preprocessing transformers — log-scaling, categorical encoders, imputation — are fit on the training set only and applied frozen to validation and test. Rolling aggregate features (e.g., 30-day transaction velocity, degree counts) are computed using only data available at or before the transaction timestamp, enforcing strict causal ordering.

Critically, the GBT baseline receives tabular versions of all relational signals the GNN processes: unique counterparty counts over 7/30/90-day windows, shared device and IP linkage counts, fan-out degree, and training-period betweenness centrality. This information parity is the experiment's most important design control — it ensures any advantage the GNN demonstrates reflects its capacity for joint relational inference, not privileged access to information.

### 4. Models and Baseline

The proposed model is a heterogeneous GNN (GraphSAGE or R-GCN, 2–3 layers) operating on the account-device-IP-beneficiary multigraph, producing transaction-level suspicion scores. The baseline is a LightGBM or XGBoost model trained on the information-equivalent tabular feature set. Both models receive equivalent tuning effort: a 100-configuration randomized search over their respective hyperparameter spaces, evaluated on validation AP. Neither model is given any advantage in tuning budget or feature access.

### 5. Evaluation Metrics

The primary metric is AUROC on the test set. AUROC is a threshold-independent measure that captures overall discrimination quality and makes the results easier to compare with prior AML detection literature, while remaining robust to the choice of operating point.

Secondary metrics include precision at recall thresholds of 0.40 and 0.60 (the practical operating range), AUROC for comparability, alert lift at the bank's monthly investigation capacity K, Brier score for calibration quality, and typology-stratified AP to characterize where any advantage is concentrated.

### 6. Validation and Test Set Discipline

All model selection — architecture choices, hyperparameter configurations, early stopping — is performed using validation AP on months 25–27 only. The test set is not examined until a single frozen model per approach is committed. The test set is used exactly once. This discipline is non-negotiable given how easy it is to inadvertently overfit to a test set across iterative AML model development cycles.

### 7. Confound Controls

Three confounds are explicitly managed. First, information asymmetry is neutralized by providing the GBT baseline with tabular graph-derived aggregates, so any GNN advantage is attributable to architecture. Second, relational leakage is controlled through the temporal split and dead zones; a post-hoc audit reports the fraction of test-period SAR clusters that are wholly novel versus partially overlapping with training-period rings. Third, investigator discovery bias in labels is addressed through a sensitivity analysis that evaluates both models on the subset of SAR-linked transactions that were originally surfaced by the bank's existing rule-based system, controlling for the fact that uninvestigated transactions are labeled negative by convention rather than confirmed innocence.

This design would establish whether the GNN's graph architecture provides measurable value over an information-equivalent tabular model on future-period data — and nothing more. It would not establish generalizability to other institutions, typologies not represented in 36 months of data, or performance under real-time inference constraints.

---

## eval_scenario_500
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Temporal Sepsis Deterioration Prediction

### Objective
Test whether a temporal LSTM model trained on 24-hour longitudinal sequences of vital signs and labs outperforms a static baseline (logistic regression on most recent measurements) in predicting 6-hour ahead septic deterioration, using prospective admissions from a single health system.

### 1. Data and Label Definition

The experiment uses multi-year EHR data spanning 5 years of inpatient admissions from a single health system (minimum 50,000 admissions to ensure adequate sepsis prevalence and test stability). All timestamped vital signs, laboratory results, medication orders, and clinical notes are extracted. Data quality issues—irregular sampling, missing measurements, and documentation variation—are documented but not excluded; both models must handle these realistically.

The outcome (sepsis) is defined using a two-part clinical criterion: (1) suspected infection confirmed via clinical documentation, blood culture order, or antibiotic initiation within ±12 hours, AND (2) organ dysfunction (lactate ≥2 mmol/L, hypotension, vasopressor use, altered mental status, or mechanical ventilation) occurring within the infection window. This definition is applied prospectively; admissions where sepsis is recognized at the time of admission (no forecasting opportunity) are excluded. The 6-hour prediction window is anchored to the first timestamp meeting both criteria. Admissions with fewer than 24 hours of prior observation history or where the patient dies/is discharged within 6 hours of sepsis onset are excluded, ensuring a complete prediction and outcome window.

### 2. Train-Validation-Test Split

Admissions are partitioned at the admission level into three sets spanning the full study period:
- **Training (70%):** admissions used for model fitting and feature engineering.
- **Validation (15%):** admissions used for hyperparameter selection and early stopping.
- **Test (15%):** admissions held out until final evaluation.

The split is stratified by sepsis label prevalence and, if applicable, by hospital site, with an additional balance check within calendar quarter so that each set reflects the same mix of seasonal incidence and site-level practice patterns. This preserves comparable case mix across model-development stages and reduces the chance that one split is dominated by an unusually severe or unusually low-incidence period. It also makes the temporal-versus-static comparison cleaner by ensuring both models are judged under closely matched prevalence and hospital composition.

### 3. Feature Engineering and Preprocessing

**Temporal features** (for both models, but leveraged differently):
- 24-hour window of vital signs and labs binned into 1-hour intervals (24 timesteps, ~10 variables per timestep).
- Rate of change: slope of lactate, heart rate, and temperature over 4-hour and 12-hour windows.
- Missingness patterns: binary indicators for each missing measurement in each bin, and hours since last measurement for each lab type.
- Static context: comorbidities (diabetes, renal disease, immunosuppression), admission source, and admission diagnosis category.

**Preprocessing fit protocol:** All standardization (z-score scaling of vitals/labs), imputation strategies (forward-fill for short gaps, mean imputation for others), and categorical encodings are fit on the training set only. The validation and test sets are transformed using the training-fitted parameters. Time-based features are computed identically across all sets using the pre-anchor data only.

### 4. Models and Baseline

**Temporal model:** Bidirectional LSTM with 24-step input sequence and ~10 features per step. Architecture: embedding layer (if categorical features are present) → BiLSTM (hidden units: 64/128/256, tuned on validation) → fully connected layer (128 units, ReLU, dropout 0.2–0.4) → logistic output. Trained with Adam optimizer, batch size 32, class-weighted cross-entropy loss, and early stopping (patience 10 epochs).

**Baseline model:** Logistic regression trained on static features only (most recent vital signs, labs, and comorbidities from the validation set). Hyperparameter tuning: grid search over L2 penalty {1e-2, 1e-3, 1e-4}, evaluated on the validation set.

**Why this baseline:** Logistic regression on current measurements represents clinical practice and isolates the contribution of temporal structure. By giving the baseline equivalent tuning effort and identical preprocessing, we ensure the comparison measures the value of sequence representation, not differential tuning or feature richness.

### 5. Evaluation Metrics

**Primary metric: Brier score.** Because the model is intended to support risk-aware alerting rather than a single fixed threshold, the main comparison focuses on how faithfully predicted probabilities track true short-horizon sepsis risk across the inpatient population. Brier score directly evaluates that probability quality by penalizing both over-confident and under-confident predictions, which is useful when comparing a sequential model to a simpler static baseline that may differ in calibration as well as discrimination.

**Secondary metrics:**
- AUROC (Area Under the Receiver Operating Characteristic Curve): summarizes discrimination across operating points and helps determine whether gains in probability quality are accompanied by better rank ordering.
- AUPRC (Area Under the Precision-Recall Curve): appropriate for imbalanced classification, ensures gains are not artifacts of label imbalance.
- Sensitivity at 90% specificity and 80% specificity: clinically relevant operating points where false alarms are limited but early detection is achievable.
- Calibration slope: ensures predicted probabilities remain trustworthy across risk strata.

### 6. Validation and Model Selection

Hyperparameter tuning uses the validation set only. A grid search over temporal model hidden units, dropout, and learning rate is performed, and the configuration yielding the best validation Brier score is selected. The test set is never touched during this phase. After both models are finalized, they are evaluated once on the test set in a single forward pass, with results reported with 95% confidence intervals.

### 7. Confound Controls and Scope

**Confounds addressed:**
- **Missingness and irregular sampling:** Both models receive identical engineering of missingness indicators and time-since-last-measurement; the temporal model gains no special advantage in handling sparsity.
- **Leakage:** Only pre-anchor measurements enter the model; post-onset data are excluded.
- **Class imbalance:** Both models use class-weighted loss.
- **Site variation:** Admissions stratified by site and site features included in both models.
- **Outcome definition sensitivity:** Results validated under two alternative sepsis definitions to confirm robustness.

**Scope:** This experiment tests temporal advantage for 6-hour-ahead prediction within a single health system under a specific sepsis definition. It does not establish generalization to other systems, alternative horizons, or other populations, nor does it isolate which temporal features drive gains (ablation required).

---

## eval_scenario_651
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Dense Bi-Encoder vs. BM25 for Legal Case-Law Retrieval

### 1. Data Strategy

We will use 18–24 months of production data from the commercial case-law search platform, comprising three components:

- **Query and interaction logs:** Timestamped user queries, clicked results, dwell times (>30s treated as a relevance signal), and bookmarks.
- **Document corpus:** Full-text opinions with structured metadata (jurisdiction, court level, publication date, citation graph).
- **Curated relevance labels:** Attorney-annotated binary or graded relevance judgments on a representative sample of long-tail queries (bottom quartile by frequency), with at least 500–1000 queries and 3–5 judgments per query to establish ground truth. These labels are created independently of the model development process and represent the true operational definition of relevance.

Weak supervision for model training will come from the citation graph (opinions that cite each other are treated as relevant for citation-aware queries) and behavioral signals (clicks, bookmarks), but these signals are kept separate from evaluation to avoid metric corruption. The evaluation dataset relies exclusively on attorney judgments.

### 2. Split Strategy: Stratified Query-Level Partitioning Across the Observation Horizon

Because long-tail legal issues are sparse and often concentrated in only a few periods, we will partition the 18–24 month dataset at the query level so that train, validation, and test each contain a comparable mix of rare queries, jurisdictions, and temporal regimes:

- **Training:** 70% of queries, selected with stratification over query frequency tier, jurisdiction, and temporal epoch.
- **Validation:** 15% of queries, drawn with the same stratification scheme.
- **Test:** 15% of queries, held out for final evaluation and matched to the same long-tail composition.

This query-level allocation keeps the benchmark balanced across splits while preserving enough rare-query coverage to measure differences reliably on the slice that matters most for the hypothesis. Query-document pairs are completely separated across train, validation, and test.

To preserve realistic document availability, each query is evaluated only against opinions that were published by the time that query occurred. In other words, documents remain time-filtered relative to query timestamp even though the query partitions span the full observation horizon. This prevents any query from being matched against authorities that would not yet have existed at search time, while reducing the risk that one split is dominated by an unusually easy or unusually hard legal period.

### 3. Feature Engineering and Preprocessing

All preprocessing—tokenization, vocabulary construction, and embedding normalization—is fit exclusively on the training set. The dense model is initialized with a pretrained legal-domain BERT and does not adapt to validation or test data. 

Features include:
- **Query and document text:** Tokenized using a shared BPE vocabulary derived from training data.
- **Citation context** (training only): In-degree and out-degree in the citation graph, used as weak supervision during training but not during evaluation.
- **Temporal/metadata features:** Normalized publication date, jurisdiction alignment (if query specifies a jurisdiction filter).

The BM25 baseline uses identical tokenization and the same document corpus, ensuring that differences in performance reflect the retrieval method (sparse vs. dense) and not data preprocessing.

### 4. Models and Baseline

**Dense Model:** A Siamese bi-encoder (e.g., DPR or contrastive dual-encoder) with:
- Shared transformer encoders for queries and documents (pretrained legal BERT).
- Training via in-batch negatives and hard negative mining (sampling competitive negatives from BM25 retrievals).
- Supervised contrastive loss incorporating curated relevance labels and weak supervision from the citation graph.
- No online adaptation or test-set fine-tuning.

**Baseline (BM25):** Standard Okapi BM25 with TF-IDF weighting, tuned on the validation set using the same evaluation metric (Recall@50). Hyperparameters k1 ∈ [1.2, 2.5] and b ∈ [0.5, 0.9] are optimized via grid search on validation data. The BM25 baseline is re-indexed with each split's document corpus to ensure fair comparison.

Both models receive the same preprocessing and tuning effort, isolating the effect of the retrieval mechanism.

### 5. Evaluation Metrics

**Primary metric: Recall@50** on the test set, evaluated on long-tail queries. Justification: In legal research, the most costly error is failing to surface a controlling or highly persuasive authority at all. Recall@50 measures whether the system places relevant authorities within the broader candidate set that an attorney or downstream reranker can inspect, and it is less sensitive to query-to-query variation in the number of acceptable relevant cases.

**Secondary metrics:**
- **nDCG@10:** Captures whether relevant authorities are concentrated near the top of the list.
- **MRR (Mean Reciprocal Rank):** Measures how quickly the first correct authority appears.
- **Precision@10:** Diagnoses whether improvements are driven by higher precision in the first page of results.
- **Stratified Recall@50:** Results broken down by query length, query type (long-tail vs. frequent), and jurisdiction to confirm robustness.

### 6. Model Selection and Test Set Policy

Hyperparameter tuning and model selection occur on the validation set using Recall@50 as the selection metric. Once the dense model and BM25 baseline are finalized, **the test set is touched only once** for final evaluation. No hyperparameter adjustment, loss re-weighting, or architecture change is made after test-set evaluation begins. Results are reported with 95% confidence intervals computed via bootstrap over query-level scores.

### 7. Controlling for Confounds

- **Citation graph memorization:** Evaluate separately on recent and novel opinions where citation patterns are sparse, and on queries about emerging topics. If the dense model's gains persist in these regimes, it is learning semantic retrieval, not memorizing citations.
- **Label source alignment:** Attorney labels are generated independently; we also evaluate on a small auxiliary set of behavioral labels (clicks from the validation period) to confirm generalization across label sources.
- **Temporal drift:** Monitor Recall@50 separately for each temporal epoch represented in the test partition to detect performance degradation under domain shift.
- **Query type robustness:** Stratified evaluation by query length, frequency, jurisdiction, and court level confirms gains are broad-based, not driven by a narrow query subset.

This design isolates the hypothesis that dense retrieval with citation graph supervision outperforms BM25 on long-tail legal queries, while controlling for alternative explanations and ensuring fair comparison.

---

## eval_scenario_535
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer-Based Phishing Detection in Enterprise Communications

### 1. Data Strategy

The experiment uses 18–24 months of labeled security alerts from one or more large enterprise email gateways and chat moderation systems. Each record includes: full message text (subject and body), sender and recipient metadata (domain, internal/external status, organizational unit), conversation context (prior messages in thread), attachment and URL indicators, timestamp, and a binary label (phishing or benign) assigned by SOC analyst review within 48 hours of flagging. A 5% stratified secondary review by an independent analyst will be performed to measure label disagreement and detect any systematic drift in labeling criteria over time. Phishing is operationally defined as messages containing social engineering tactics with intent to harvest credentials or deploy malware. Any known label issues (e.g., analyst disagreement >5%) will be documented and handled via consensus re-review or exclusion.

The data distribution—message types, sender patterns, organizational structure, attack prevalence—should match the deployment target (a single enterprise or federated enterprises with similar infrastructure). If the training data is drawn from a different organization or time period with substantially different phishing prevalence or communication patterns, this limitation will be documented and performance will be reported separately for out-of-distribution subgroups during the confound control analysis.

### 2. Split Strategy and Stratification

Data is partitioned into train, validation, and test with explicit balancing over label prevalence, organization, and calendar month so that each split reflects the same seasonal campaign mix and enterprise composition. The 18–24 month period is divided as follows:
- **Training set:** 50% of total dataset, used to fit the model and all preprocessing transformers.
- **Validation set:** 25% of total dataset, used for hyperparameter tuning and early stopping.
- **Test set:** 25% of total dataset, held completely intact until final evaluation.

If multi-organizational data is available, each organization contributes its proportional share to all three splits (e.g., 60% of training data, 60% of validation, 60% of test). In addition, allocation is stratified within calendar-month slices so the phishing base rate and attack-volume fluctuations are comparable across train, validation, and test. This is useful because enterprise alert streams can be highly seasonal; preserving the month-level composition across splits reduces the chance that one holdout partition is dominated by an anomalous campaign burst or holiday-related traffic pattern. The resulting evaluation estimates whether the model improves discrimination under a representative mix of conditions rather than over- or under-estimating performance due to a single atypical time window.

### 3. Feature Engineering and Preprocessing

**Raw features:**
- Message text: lowercased, special characters normalized (URLs and file paths converted to sentinel tokens), tokenized to 512 tokens maximum.
- Metadata: sender domain (one-hot encoded, fit vocabulary on training set only), sender internal/external flag, recipient count, thread depth, presence of URLs, presence of suspicious file extensions (.exe, .scr, .zip, etc.).
- Conversation context: concatenation of up to 3 prior messages in thread with delimiters.

**Engineered features:**
- Sender domain reputation: binary flag for known phishing sources or domains <30 days old (derived from threat feeds or organizational blocklists).
- URL count and domain diversity.
- Urgency score: TF-IDF weighted keyword match for urgency language ("urgent", "confirm", "verify", "act now"), vocabulary fit on training set only.

**Preprocessing pipeline:** All tokenizers, TF-IDF vectorizers, and scaling transformers are fit exclusively on the training set. These fitted transformers are applied identically to validation and test sets without refitting. The Transformer model uses a pre-trained BERT tokenizer (not fitted on this dataset). This prevents information leakage from validation or test data influencing vocabulary or scale decisions. No features encode the label or contain future information (e.g., no "was_later_confirmed_phishing" flag).

### 4. Model and Baseline

**Model:** A BERT-base (or RoBERTa-base) Transformer with a fine-tuned classification head. The model concatenates message text, metadata, and conversation context; inputs are tokenized to max sequence length 512. A 2-layer dense head (with 0.2 dropout and sigmoid output) is trained end-to-end on the training set using binary cross-entropy loss, with early stopping on validation F1-score (patience 3 epochs). Hyperparameter grid: learning rate ∈ {1e-5, 2e-5, 5e-5}, batch size ∈ {16, 32}, warmup steps ∈ {0, 500, 1000}. Tuning is performed on the validation set; the best configuration is selected by F1-score at the validation-selected threshold, then the model is retrained on combined train+validation data and evaluated on test.

**Baseline:** Logistic regression with TF-IDF-vectorized message text, one-hot encoded metadata, and concatenated conversation context. TF-IDF vocabulary (max 5000 features) is fit on the training set. The baseline receives equivalent tuning effort: 5-fold stratified cross-validation on training data to select regularization strength C ∈ {0.001, 0.01, 0.1, 1, 10} and class weight ∈ {None, 'balanced'}. Best configuration is selected by cross-validated F1-score, retrained on the full training set, and evaluated on validation and test sets. Both use identical feature sets; the difference is architectural. This baseline represents historical industry practice and is a fair comparison point.

### 5. Evaluation Metrics

**Primary metric: F1-score at a validation-selected operating threshold.** The SOC ultimately acts on a binary triage decision rather than a continuous score, so the primary comparison will emphasize the thresholded balance between missed phishing and analyst workload under a single operational setting. The threshold will be chosen on the validation set and then frozen before the final test evaluation so the held-out test set remains independent. This makes the comparison concrete and deployment-oriented while still allowing score-based diagnostics to be examined separately.

**Secondary metrics:**
- **AUROC:** Overall ranking quality across thresholds.
- **PR-AUC:** Precision-Recall curve area, useful under imbalance.
- **Precision at recall = 0.80:** Fraction of flagged messages that are truly phishing when 80% of phishing is caught.
- **Recall at FPR = 0.01:** Sensitivity at a fixed 1% false-positive rate, enabling threshold-based deployment.

All metrics are reported with 95% confidence intervals computed via bootstrap resampling of the test set.

### 6. Model Selection and Validation

The validation set is used exclusively to tune hyperparameters, select the operating threshold, and perform early stopping. For the Transformer, early stopping monitors validation F1-score. For the baseline, 5-fold stratified cross-validation on training data determines the best hyperparameters; the baseline is then retrained on the full training set and evaluated on validation to confirm generalization and fix the deployment threshold. After both models are finalized, the test set is used exactly once to compute all reported metrics. No threshold tuning, refitting, or further evaluation occurs on the test set.

### 7. Confound Controls

The primary confound is that Transformer gains could reflect exploitation of metadata artifacts (sender domain patterns, duplicate campaign templates) rather than semantic understanding of phishing intent. Four controls address this:

1. **Ablation study:** Train and evaluate the Transformer in two modes: (a) full features (text + metadata), (b) text-only. If performance is similar, text semantics drive the gain. If metadata-only performance drops substantially, metadata is the signal—indicating possible confounding.

2. **Temporal degradation check:** Stratify test results by time periods (early, middle, late portions of the corpus) and report F1-score separately for each slice. If F1-score degrades significantly over time, the model is overfitting to period-specific campaigns.

3. **Held-out organization validation:** If multi-organizational data exists, train on Organizations A and B, validate and test on held-out Organization C. If performance degrades on Organization C, the model exploits organization-specific metadata.

4. **Feature importance analysis:** Use SHAP values or Transformer attention weights to identify which inputs drive predictions. Report the top-10 features. If sender domain and known-phishing campaigns dominate, confounding is likely.

### Scope

This experiment establishes whether a Transformer, given the same features as a TF-IDF baseline and trained on a stratified enterprise alert corpus, achieves higher F1-score at a deployment-realistic operating point and whether gains are driven by semantic understanding or metadata confounds. It does not establish whether Transformers are optimal across all domains, that the model will remain effective under adversarial attack, or that the absolute performance is sufficient for production deployment (that is a separate threshold-setting and risk assessment decision).

---

## eval_scenario_555
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

To test the hypothesis that a temporal sequence model outperforms a static baseline for 30-day readmission prediction in adult heart failure patients, we would design the following methodologically sound experiment:

**1. Data Source and Cohort Definition**
We would use 4 years of longitudinal EHR data from a single hospital system, comprising all adult (age ≥18) heart failure patients discharged to home, home health, or skilled nursing facility. The cohort spans 48 months, providing sufficient volume to support tens of thousands of index admissions. We would exclude patients who die, transition to hospice, or receive comfort care within 30 days, as these represent competing risks that confound the readmission prediction task; the goal is to predict readmission among patients whose trajectory supports potential intervention. The label is binary: readmission (any inpatient admission or observation stay) within 30 days of discharge, identified via timestamped admission records.

**2. Split Strategy**
We would partition admissions using stratified sampling across the full 48-month cohort, assigning 60% to training, 20% to validation, and 20% to held-out test. Stratification would be performed jointly on discharge disposition (home vs. home health vs. SNF) and calendar quarter so that each split preserves both baseline acuity and seasonal readmission structure. This keeps model selection and final evaluation representative of the hospital’s full operating range rather than depending on a single contiguous year that could have atypical census, staffing, or case mix.

**3. Feature Engineering and Preprocessing**
Features are constructed in three groups. Static features at discharge include age, sex, diagnoses (one-hot encoded, top 20 codes), disposition, and insurance. Temporal features summarize prior 24-month history: ED visits, inpatient admissions, outpatient encounters, and inpatient days (binned quarterly); most recent lab values (BNP, troponin, creatinine, eGFR, ejection fraction) and their 6-month rate of change; discharge medications (ACE inhibitors, beta-blockers, diuretics, etc.); and vital signs at discharge with 30-day trends. We would also include transition-of-care workflow signals that are available in the enterprise system, including whether a follow-up appointment is scheduled within 7 days, whether discharge medications are reconciled within 72 hours, and whether a transitional care outreach task is opened. These variables are clinically meaningful because they reflect continuity-of-care planning and discharge readiness, both of which strongly shape readmission risk. For the sequence model, we additionally construct a time-indexed tensor of 24 observations (one per month) containing lab values, vitals, medications, and encounter counts per month. All preprocessing (imputation, scaling, encoding) is fit exclusively on the training set and applied to validation and test without refitting. This prevents information leakage from held-out data into the preprocessing step.

**4. Baseline and Model Selection**
The baseline is a gradient-boosted tree model (XGBoost or LightGBM) trained on the same static and aggregated temporal features, receiving identical hyperparameter tuning effort via random search (100 iterations) on the validation set, using the same primary metric (AUC). The sequence model is a bidirectional LSTM with attention (128 hidden units, 2 layers, attention layer of 64 units) trained on the 24-month temporal tensor. Both models undergo hyperparameter optimization on the validation set only; the test set remains untouched until final evaluation.

**5. Evaluation Metrics and Validation**
The primary metric is AUC-ROC on the held-out test set, chosen because it measures ranking discrimination (clinicians' core need: identifying high-risk patients for resource allocation) and is threshold-agnostic. Secondary metrics include calibration (Brier score, calibration plots), sensitivity/specificity at a pre-specified operating point, precision-recall AUC, net benefit, and subgroup AUC by discharge disposition, age, and comorbidity burden. We require the sequence model to exceed baseline test AUC by ≥0.03 (absolute) to claim a clinically meaningful improvement.

**6. Confound Controls**
Stratification ensures balanced acuity representation and seasonal case-mix coverage across training, validation, and test. Exclusion of competing-risk patients isolates readmission prediction from mortality confounding. Calibration analysis and subgroup AUC curves detect if the sequence model exploits spurious administrative or documentation patterns rather than true patient risk. Post-hoc SHAP analysis confirms that learned patterns align with known clinical drivers (e.g., BNP, ED utilization, medication adherence signals). A sensitivity analysis on the most recent 6 months confirms robustness.

**7. Scope**
This design would establish that sequence models improve discrimination for readmission prediction under realistic hospital-wide variation, controlling for feature complexity and tuning effort. It would not establish causality, nor generalize to other health systems, patient populations, or outcome definitions without further validation.

---

## eval_scenario_305
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

This experiment tests whether a transformer-based code recommendation model that incorporates developer file-edit sequence and repository dependency graphs outranks a token-only language model baseline on real pull request data.

**1. Data Collection and Labeling**

We would use 24 months of version control and IDE telemetry from a curated set of open-source and enterprise repositories. The dataset includes ordered file-edit sequences with timestamps, complete diffs, commit metadata, dependency graphs (parsed from imports), and accepted code completions extracted from merged pull request diffs or IDE logs.

For each developer session, the ground-truth label is the exact code span the developer accepted and committed. A completion is considered correct if it matches the accepted span exactly (with minor whitespace tolerance defined a priori). We only include completions that were generated within 2 seconds of the cursor position, ensuring they were contextually available when the developer made their choice.

**2. Splitting Strategy**

We employ a repository-stratified session split across the full 24-month corpus. Developer sessions are partitioned into training, validation, and test sets in a 60/20/20 ratio while preserving each repository’s contribution and acceptance-rate profile in every split. This design keeps the candidate-completion mix, repository complexity, and rare-library usage comparable across splits, reducing the chance that model differences are driven by one atypical development period or by sparsity in a small subset of repositories.

**3. Feature Engineering and Preprocessing**

All preprocessing and vocabulary fitting is performed exclusively on the training data. We construct two feature streams: (1) **Sequence features**: the last 10 file edits in the developer's session, represented as (file_path_embedding, diff_summary, timestamp_delta); (2) **Graph features**: the repository dependency graph at the time of completion, represented as (imported_module, importing_file) edges, updated per commit to reflect the current state without leakage. Code tokens are tokenized from training vocabulary only. Critically, we exclude hand-crafted features (e.g., library popularity, API frequency) that would confound the graph and sequence signal.

**4. Model and Baseline**

The proposed model is a transformer with two branches: a sequence encoder over file-edit history and a graph encoder over the dependency DAG. Both encoders are concatenated and fed to a ranking head that scores candidate completions via pairwise ranking loss (e.g., BPR).

The baseline is a token-only transformer decoder with identical architecture and capacity, receiving only code tokens and immediate edit history—no dependency graph or file-context. Both models receive equivalent hyperparameter tuning on the validation set (same search budget, same tuning metric) and are trained with the same ranking loss.

**5. Evaluation Metrics**

The primary metric is **mean reciprocal rank (MRR)**, computed per developer session over the scored candidate set and averaged across the test set. This captures how close the accepted completion is to the top of the ranked list and provides a stable view of ranking quality even when candidate-pool difficulty varies across repositories and coding contexts.

Secondary metrics include top-1 accuracy, top-5 accuracy, recall@10, and false positive rate to assess robustness and user experience.

**6. Model Selection and Test Policy**

Both baseline and proposed model are tuned and selected on the validation set using MRR. The test set is held until final evaluation and is used exactly once to report results. Significance is assessed via bootstrap confidence intervals and paired statistical testing (α = 0.05).

**7. Controls for Confounds**

To isolate the value of graph and sequence context from project-specific memorization, we implement four controls: (1) Repository stratification ensures broad project coverage in each split; (2) A project-blind baseline prevents the model from using repository metadata; (3) A held-out repository is withheld entirely from training and validation, tested separately to detect project overfitting; (4) Per-library analysis breaks down performance by library popularity to confirm that improvements come from context learning, not baseline coverage of popular APIs.

This design allows us to establish with high confidence whether the proposed model's ranking improvements are attributable to context incorporation or to other factors.

---

## eval_scenario_174
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Multimodal IHC Order Prediction in Surgical Pathology

### 1. Data and Labels

The experiment uses 3 years of digitized H&E whole-slide images and linked laboratory information system (LIS) records from a minimum three-site hospital network. Each surgical pathology *case* (accession) is the atomic unit of analysis. The outcome label is binary: a case receives label 1 if any IHC stain is ordered within 7 calendar days of the slide-available timestamp in the LIS, and 0 otherwise. This window is operationally meaningful — it captures the reflex-ordering decision made during initial pathologist review — and is computable without any information from the final sign-out report.

A data-quality audit will identify and exclude cases with incomplete LIS linkage, cases where care was discontinued within the 7-day window before an IHC order would have been plausible, and any accessions lacking digitized slides. Because IHC ordering rates vary substantially by specimen type and tissue site, the audit will document label prevalence by subgroup prior to any modeling.

### 2. Split Strategy

The data is partitioned **at the case level using a stratified random split**: 70% of cases form the training set, 15% form the validation set, and 15% form the held-out test set. All slides belonging to a single accession are assigned to the same partition — this is non-negotiable given that multi-slide cases would otherwise introduce direct leakage. Stratification is applied to preserve overall label prevalence as well as major specimen-type and site distributions across splits so each partition is representative of the full dataset and supports stable model comparison.

### 3. Feature Engineering

Three feature groups are constructed. The **image branch** derives fixed-dimensional case-level embeddings from a frozen, pathology-domain foundation model (e.g., UNI or CONCH). Patches are extracted from each slide, embedded, and pooled (mean and max) across patches and then across slides to produce one case vector. The foundation model weights are frozen — no fine-tuning is performed — to avoid label leakage through gradient signal. The **metadata branch** includes specimen type, tissue site, service line, ordering clinician specialty, gross description length, slide count, time-of-day and day-of-week of accession (cyclically encoded), hospital site, and a coarse final sign-out diagnosis category to capture broad clinical context. The **history branch** includes patient-level prior-case features: prior IHC rate, prior case count, days since last accession, and most recent diagnosis category — all computed exclusively from available historical data for each patient.

All scalers, encoders, and imputers are fit on the training partition only and applied identically to validation and test. Features are encoded at a level intended to capture clinically relevant variation without overfitting to highly granular pathology terminology.

### 4. Models and Baselines

The **multimodal model** is a late-fusion architecture: a 2-layer MLP processes the image embedding; a shallow MLP or XGBoost processes metadata and history features; outputs are concatenated and passed to a logistic classification head. Two baselines are trained under equivalent conditions: (a) an **image-only model** using the same architecture with the metadata+history branch removed, and (b) a **metadata+history-only logistic regression** to isolate the contribution of non-imaging features. All three models receive the same Bayesian hyperparameter optimization budget evaluated on validation-set AUPRC.

### 5. Evaluation

The **primary metric is AUPRC** (area under the precision-recall curve), which directly reflects the precision-recall tradeoff that matters operationally: over-ordering wastes stain resources; under-ordering delays diagnosis. Secondary metrics include AUROC, precision at fixed recall thresholds of 85% and 90%, net benefit via decision curve analysis, and expected calibration error. Subgroup AUPRC is reported stratified by tissue site, hospital site, and pathologist IHC-ordering-rate quintile.

### 6. Validation and Test Protocol

All model selection and hyperparameter decisions use the validation set exclusively. The test set is evaluated exactly once after all choices are final.

### 7. Confound Controls

To ensure observed gains from the multimodal model reflect genuine morphologic-clinical signal rather than metadata proxies for pathologist behavior: site ID and clinician specialty are included as explicit features so their effect is modeled rather than confounded; a feature-ablation removing these proxy variables quantifies their contribution; stratified subgroup analysis across sites and pathologist ordering quintiles flags differential performance; and a qualitative audit of high-confidence errors by a pathologist co-investigator assesses clinical face validity. The experiment establishes whether multimodal fusion improves AUPRC over image-only prediction in a representative held-out evaluation — it does not establish causality or generalize claims beyond the participating network's case mix.

---

## eval_scenario_554
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer-Based Churn Prediction

### 1. Data Collection and Labeling

We will use 36 months of production data spanning account renewals, support interactions, and product usage. The source is the company's CRM and support ticketing system, which contains complete ticket text, account-level renewal decisions, and telemetry. Churn is defined as accounts that did not renew at the contract end date or cancelled within 30 days of the end of the observation window. To reduce ambiguity from short pre-renewal histories and stabilize both longitudinal usage features and ticket-language context, we will restrict the modeling cohort to accounts with at least 180 days of prior activity before the prediction window. We will exclude accounts with incomplete billing data. Accounts with missing ticket text are retained but flagged; missing usage telemetry gaps longer than 14 days are forward-filled and imputed values are marked with a missingness indicator. This ensures the dataset reflects production data quality while focusing the analysis on accounts with sufficiently mature behavioral history for both baseline and text-based models.

### 2. Temporal and Stratified Split

The 36 months are divided chronologically into three splits: **Training (months 1–24, ~70%)**, **Validation (months 25–30, ~15%)**, and **Test (months 31–36, ~15%)**. This temporal split prevents label leakage—the model never sees future information when predicting the past. It also reflects realistic deployment: the model is trained on historical data and deployed to score future renewals.

Within each split, accounts are stratified by contract value quartile and plan tier. This ensures that high-value enterprise accounts and smaller SMB accounts are represented in balanced proportions across all three sets. Stratification is critical because churn patterns and ticket volume differ by segment; without it, the model could appear to generalize when it has simply memorized segment-specific signals. No account appears in multiple splits.

### 3. Feature Engineering

Two feature sets are constructed for a fair comparison:

**Baseline features** (available in production, no text):
- Account activity (last 90 days): login frequency (mean, max, trend), feature adoption, API call volume (mean, max, std)
- Support ticket summary: count (30/60/90 day windows), mean resolution time, fraction resolved, days since last ticket
- Account metadata: log-scaled contract value, account age, plan tier, industry
- Billing: days since last billing event, payment delays (count in last 90 days)

**Transformer features** (baseline + text):
- All baseline features (to ensure a fair apples-to-apples comparison)
- Full concatenated ticket text (all tickets in the last 180 days, reverse chronological, truncated to 4096 tokens per account)
- Ticket count is retained as an explicit feature to isolate semantic gain from volume effects

All features are computed strictly before the prediction window [t, t+30] to avoid leakage. Preprocessing (scaling, tokenization, encoding) is fit on the training set only and applied identically to validation and test. Categorical features with unseen values in validation/test are mapped to 'other'. This prevents the model from learning statistics from future data.

### 4. Models and Baselines

**Transformer model:** A BERT-base encoder (pre-trained) ingests concatenated ticket text; the pooled [CLS] representation is concatenated with baseline features and passed through a 2-layer feedforward network (256 hidden units, ReLU, dropout 0.3) terminating in a sigmoid output. Binary cross-entropy loss with class weight balancing is used to handle imbalance. Hyperparameters (learning rate, warmup, dropout) are tuned on validation.

**Baseline model:** An XGBoost gradient boosted tree trained on baseline features only (no text). It receives equivalent tuning effort: grid search over learning rate, max depth, and subsample on the validation set. This baseline represents the production-ready null hypothesis. Any gain from the transformer is credibly attributable to semantic information extraction, not simply having more parameters or data.

### 5. Evaluation Metrics

**Primary metric: Area Under the ROC Curve (AUC-ROC).** The intervention policy may vary by segment and outreach capacity over time, so the primary evaluation will emphasize class separability independent of any single operating threshold. AUC-ROC also enables cleaner comparison across customer segments with different churn prevalences, which is important for assessing whether semantic information from ticket text improves discrimination broadly rather than only within one cohort.

**Secondary metrics:**
- Recall at 90% precision (and the minimum score threshold)
- Expected Calibration Error (calibration of predicted probabilities)
- Segment-level AUC-ROC by contract value quartile and plan tier (to detect segment drift)

### 6. Model Selection and Validation

Hyperparameter tuning is performed on the validation set (months 25–30) using AUC-ROC. Early stopping is enabled: training stops after 3 epochs without validation AUC-ROC improvement (max 20 epochs total). The model with the highest validation AUC-ROC is selected. The test set is held out entirely and used only once at the end to compute final metrics on both models.

### 7. Confound Controls

Three confounds are controlled:

1. **Ticket volume:** If the transformer merely learns that more tickets predict churn, the gain is spurious. Control: Ticket count is explicitly included in the baseline feature set.

2. **Sentiment/urgency proxies:** If text reduces to simple sentiment signals, this is useful but not deep semantic extraction. Control: A secondary enhanced baseline is trained with hand-engineered features (pre-trained sentiment scores, resolution time patterns, escalation flags). If the transformer's gain over this baseline is small, the improvement is captured by simpler proxies.

3. **Segment heterogeneity:** If the transformer improves only for high-value accounts, it may not generalize. Control: Test AUC-ROC is reported by contract value quartile and plan tier. Validation stratification ensures the model is tuned for balanced segment performance.

This design establishes whether the transformer's semantic extraction meaningfully improves near-term churn prediction over practical baselines, while rigorously controlling for alternative explanations.

---

## eval_scenario_474
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Retrieval-Augmented Transformer for Enterprise Support Answer Retrieval

### 1. Data and Label Strategy

The experiment uses a 3+ year historical corpus of support tickets from the production SaaS environment, containing at least 500,000 tickets to ensure adequate sampling of rare issues and multiple product version lifecycles. Each ticket is timestamped, includes the full query text, agent resolution metadata, and a record of which KB articles were accessed, clicked, or explicitly linked during resolution.

Labels are constructed using a multi-source approach: a ticket is considered relevant to a KB article if either (a) the article appears in the ticket's resolution record (explicit link), or (b) the article was clicked or selected by the agent via search logs during the ticket lifecycle. This union-based labeling respects the reality that multiple articles may be useful for a single issue and that agent behavior is a strong signal of relevance. Critically, unlabeled pairs (tickets and articles with no observed connection) are treated as unknown rather than negative; both the retrieval model and baseline are evaluated under this incomplete-labeling regime to avoid introducing artificial biases.

### 2. Temporal Split Strategy

To test the hypothesis fairly in the presence of product evolution and vocabulary drift, we employ a strict chronological split without randomization. The 36-month corpus is divided into three disjoint time windows:

- **Training:** Months 0–24 (earliest 67%)
- **Validation:** Months 25–30 (middle 17%)
- **Test:** Months 31–36 (most recent 17%)

Within each window, tickets are stratified by product version (major.minor) and issue frequency quintile (from rarest to most frequent). This stratification ensures that all three sets see representative distributions of product versions and issue difficulty levels, preventing the validation and test sets from being skewed toward either recent or legacy products.

This temporal strategy directly addresses the design challenges: (1) It prevents leakage of future information or near-duplicate tickets, (2) it reflects the true distribution shift that agents encounter in production (new product versions and emerging terminology), and (3) it allows the model to be evaluated on genuinely unseen time periods, not merely unseen instances of the training distribution.

### 3. Feature Engineering and Preprocessing

All preprocessing transformers (tokenizers, vocabulary builders, embedding models, metadata scaling) are fit exclusively on the training set and applied without refitting to validation and test data. Features include:

- **Semantic:** Dense embeddings of ticket and article text produced by the retrieval model and baseline.
- **Historical:** Prior co-occurrence counts (how many times this article was linked to similar issues in the training period).
- **Metadata:** Product version alignment, article recency (days since last training update), article popularity (prior clicks), and issue category if available.
- **Temporal:** Binary indicator for whether the article's product version precedes the ticket's product version (a proxy for vocabulary drift).

No labels or future information are encoded into features. Pretrained language models (e.g., BERT) are initialized from external corpora; any task-specific fine-tuning occurs only on the training set.

### 4. Model and Baseline

**Retrieval Model:** A dense dual-encoder transformer architecture (e.g., separate transformers for queries and documents, with learned similarity). Initialized from a pretrained language model and fine-tuned end-to-end on the training set using a ranking loss (e.g., triplet loss, listwise ranking, or in-batch negatives). The model produces a ranked list of KB articles for each query.

**Baseline:** TF-IDF + logistic regression. TF-IDF vectorizer is fit on training-set text. For each query, TF-IDF cosine similarity ranks all articles. A logistic regression model, trained on the training set, re-ranks the top-k TF-IDF candidates using the same metadata features as available to the retrieval model. To keep the baseline as a stable lexical reference rather than an aggressively optimized competitor, the TF-IDF weighting scheme and logistic regression regularization will be fixed to a single predeclared configuration, while only the retrieval model undergoes broad hyperparameter search on the validation set. This keeps the comparison focused on whether dense retrieval provides value beyond a straightforward sparse pipeline, instead of on how far classical components can be pushed with task-specific tuning.

### 5. Evaluation Metrics

**Primary Metric: Macro AUROC over candidate article pairs**

For each query ticket, the model produces a relevance score for candidate KB articles, and performance is summarized as macro AUROC computed over query-article pairs, then aggregated across tickets. This formulation is useful for this setting because relevance labels are incomplete and heterogeneous across issue types: a pairwise scoring metric lets us compare score separation between observed positives and unlabeled candidates without committing to a fixed cutoff or top-k truncation during model selection. Using macro aggregation also makes it straightforward to examine whether gains are concentrated in rare issue categories and newer product versions rather than being driven by the largest query clusters.

**Secondary Metrics:**
- **Recall@10:** Fraction of queries where at least one relevant article appears in top 10 (agent found *something* useful).
- **Mean Reciprocal Rank (MRR):** Average position of the first relevant result.
- **NDCG@1:** Whether the top-ranked result is relevant (first-impression quality).
- **Stratified macro AUROC by issue frequency:** Separate scores for rare, medium, and frequent issues — directly testing the hypothesis's claim.
- **Stratified macro AUROC by product version:** Separate scores for old vs. recently introduced versions — testing generalization to emerging issues.

### 6. Model Selection and Validation

The validation set (months 25–30) is used exclusively for hyperparameter optimization. The retrieval model has its hyperparameters tuned to maximize validation macro AUROC. The baseline configuration remains fixed once predeclared so that it serves as a consistent lexical reference point throughout development. The test set is sealed and not accessed until final evaluation. After all tuning is complete, both models are evaluated once on the test set; no adjustments or re-tuning occurs after test-set results are observed.

### 7. Confound Controls

To isolate the retrieval architecture's effect:

1. **Near-duplicate removal:** Tickets with >95% token overlap to earlier tickets are deduplicated, preventing data leakage across train/val/test.
2. **Equivalent training corpora:** Both models train on the same training set, so any gain cannot be attributed to richer data.
3. **Feature parity:** Both models access the same metadata features, ensuring fair comparison.
4. **Stratified reporting:** Results are reported separately by issue rarity and product version, allowing detection of whether gains occur on long-tail issues (supporting the hypothesis) or only on frequent recurring problems (suggesting a weaker effect).
5. **Incomplete labeling consistency:** Both models are evaluated under the same incomplete-labeling regime, avoiding artificial bias.

The experiment does not claim to establish causality at the level of individual design decisions (e.g., attention mechanisms vs. other architectural components), only that a modern retrieval-augmented transformer outperforms a classical TF-IDF + logistic regression baseline on this task and, ideally, shows stronger gains on rare and newly introduced issues as hypothesized.

---

## eval_scenario_596
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Time-Varying Survival Model for ICU Mortality Prediction

### 1. Data Strategy

This experiment uses a retrospective cohort of adult ICU admissions (age ≥18) from a single health system's electronic health records, spanning 36 months (January 2021 through December 2023). We include all ICU stays lasting at least 6 hours and exclude records with missing admission demographics or unclear discharge/death outcomes. We anticipate a cohort of 15,000–25,000 ICU admissions with an in-hospital mortality rate of approximately 5–12%, depending on case-mix.

Data inputs include: admission demographics (age, sex, source), initial laboratory values (creatinine, bilirubin, albumin, WBC, platelets, lactate), admission vital signs, SOFA or APACHE score, and time-stamped measurements collected throughout the stay (hourly vitals: heart rate, blood pressure, SpO2, temperature, respiratory rate; daily labs; medication administration records with timestamps and doses; ventilator settings). The outcome label is in-hospital mortality, defined as death during the ICU stay or within 48 hours of ICU discharge if directly related to the ICU admission. Patients discharged alive are administratively censored at discharge. Mortality is a fully observed outcome (no missing data) because hospital discharge records capture all deaths.

### 2. Split Strategy

We partition ICU stays from the full 36-month cohort into training (70%), validation (15%), and test (15%) subsets using outcome-stratified sampling. In addition to mortality prevalence, we preserve major admission-source composition across subsets so that each split reflects the overall clinical severity mix and intake pattern of the cohort.

Justification: ICU mortality and monitoring intensity can vary substantially across seasonal surges, staffing conditions, and service-line fluctuations. Distributing those patterns across all three subsets yields more stable model-development behavior than assigning a single calendar segment to one fold, which could make hyperparameter selection overly sensitive to an unusually mild or unusually high-acuity interval. Because the central comparison is between admission-only and time-varying feature sets rather than between calendar eras, maintaining comparable event prevalence and case composition across splits provides a cleaner estimate of the added value of dynamic information.

### 3. Preprocessing and Feature Engineering

Preprocessing parameters are established once at the cohort level and then frozen for all downstream model-development stages so that scaling, imputation, and feature encoding remain identical across training, validation, and test evaluation. Categorical features (admission source, drug class) use a unified one-hot vocabulary spanning all observed levels in the assembled cohort; infrequent levels can still be grouped into clinically coherent "other" categories where needed to avoid excessive sparsity.

Missing values in vital signs and labs are handled as follows: within each ICU stay, we forward-fill missing values up to 2 hours (a clinically plausible interval). Beyond 2 hours, we apply last-observation-carried-forward (LOCF) using fixed imputation thresholds derived once for the full cohort so that gap handling is consistent across all subsets. This approach acknowledges that in ICU data, missingness is often informative—sicker patients may have more frequent monitoring—so we retain the observation pattern as a feature (see below).

The static (admission-only) model uses: age, sex, admission source, initial labs (creatinine, bilirubin, albumin, WBC, platelets, lactate), and initial vital signs or SOFA/APACHE score.

The time-varying model adds: (1) **Current vitals** (HR, BP, SpO2, temp, RR at each observation window); (2) **Vital trends** (linear regression slope of each vital over the preceding 6 hours); (3) **Vital volatility** (standard deviation of each vital over 6 hours); (4) **Medication changes** (binary presence of vasopressors, sedatives, etc., in last 24 hours; number of new medications started; number of medication discontinuations); (5) **Ventilator parameters** (FiO2, PEEP, ventilation mode if on mechanical ventilation); (6) **Observation frequency** (number of vital measurements and lab measurements per 24-hour period, capturing the intensity of monitoring). All time-varying features are constructed within sliding windows (e.g., 24-hour windows at 12-hour intervals) to avoid future information leakage.

### 4. Model and Baseline

The dynamic (time-varying) model is a Cox proportional hazards regression with L2 regularization (ridge penalty). The regularization parameter λ is tuned on the validation set via grid search. Cox regression naturally handles censoring, produces interpretable hazard ratios for clinicians, and is the standard approach in survival analysis.

The baseline is a Cox regression model trained on static (admission-only) features, fit on the same training set and tuned using the same validation set and metric. Both models receive equivalent computational effort for hyperparameter search. The static model represents the current clinical standard: using admission labs and demographics to stratify risk. By comparing against this standard rather than a naive predictor, we isolate the added value of time-varying information.

For robustness, we train a secondary dynamic model using random survival forests (Ishwaran et al.) to check whether results hold under a flexible, non-parametric model that does not assume proportional hazards. Consistency across Cox and RSF strengthens confidence in the hypothesis.

### 5. Evaluation Metrics

The primary metric is area under the ROC curve (AUROC) for in-hospital mortality status at discharge, evaluated on the test set. AUROC summarizes whether patients who ultimately die during the hospitalization receive higher risk scores than those discharged alive, and it permits a common discrimination metric across the static Cox model, the dynamic Cox model, and the random survival forest without redefining the target separately for each model family. Using an endpoint-level metric also makes subgroup reporting more straightforward across diagnosis categories, severity strata, and monitoring-intensity strata while preserving a clinically intuitive interpretation.

Secondary metrics include:

- **Calibration:** Calibration plot (predicted vs. observed event rate) in deciles of predicted risk; calibration slope and intercept. Good calibration (slope ≈1, intercept ≈0) ensures that predicted probabilities are trustworthy for clinical communication.
- **Time-specific AUC:** AUC for 7-day and 30-day in-hospital mortality to evaluate performance at specific horizons and to control for lead-time bias.
- **Decision curve analysis:** Net benefit at clinically relevant risk thresholds (e.g., threshold for escalation) to assess clinical utility beyond statistical discrimination.
- **Stratified AUROC:** Performance stratified by (a) severity quartile, (b) time since ICU admission (early vs. late prediction), (c) primary diagnosis. This reveals whether gains are concentrated in easy-to-predict subgroups or are generalizable.

### 6. Validation Approach and Model Selection

Hyperparameter tuning is performed on the validation set. We conduct grid search over regularization parameter λ (e.g., λ ∈ {0.001, 0.01, 0.1, 1, 10}). For each λ, we train the model on the training set and compute AUROC on the validation set. We select the λ with the highest validation AUROC.

After this validation-stage selection, the shortlisted configuration set will undergo a final held-out robustness check on the test partition to verify that the preferred regularization level and feature-window specification remain stable under a fully unseen sample before the analysis is locked. This additional check is intended to reduce the chance of over-committing to a validation split that happens to overrepresent a particular severity profile or documentation regime. Once the configuration is fixed, the final model is refit on the combined training and validation data.

All reported headline metrics (AUROC, calibration, time-specific AUC, decision curve) are then computed on the test set for the selected configuration. We compute 95% confidence intervals via bootstrap (n=1000 replicates) on the test set to quantify uncertainty.

### 7. Controls for Confounds and Scope

**Lead-time bias:** The time-varying model uses information closer to the outcome than the static model. To control for this, we evaluate both models at matched prediction windows (e.g., both predict conditional on surviving to day 2, day 5, day 10 from admission). If the time-varying model's advantage persists at standardized windows, then temporal proximity alone does not explain the gain.

**Informative missingness:** ICU measurements are not missing at random; sicker patients are monitored more intensively. We address this by: (1) including observation frequency as a time-varying feature, (2) stratifying performance by measurement frequency quartiles to detect confounding by severity of illness, and (3) documenting any performance degradation in sparsely monitored patients.

**Scope of claims:** This experiment establishes that a time-varying survival model *predicts* in-hospital mortality more accurately than an admission-only baseline on held-out ICU admissions from the same health system. It does not establish causation, does not prove that intensive monitoring changes outcomes (a randomized trial would be needed for that), and does not control for unmeasured confounders (e.g., family preferences for aggressive care, coding practices). Results are specific to this health system's ICU population during 2021–2023 and may not generalize to other settings without validation.

---

## eval_scenario_428
**Category:** critique | **Difficulty:** hard | **Correct position:** critique_wins

## Experiment Design: Hazard-Based vs. Static Churn Prediction for Food Delivery

### 1. Data and Label Construction

We would use production event logs spanning January 2021 through February 2023 (36 months). The dataset includes order-level transactions (timestamp, value, ETA vs. actual delivery, cancellations, refunds), app engagement telemetry (session counts), support contacts, and promotional campaign metadata. The population comprises all customers with account creation at least 120 days before the final observation date, ensuring sufficient order history for feature construction. We expect 200k–500k customers meeting this criterion.

The churn label is defined as 60-day inactivity: a customer is churned if they place zero orders in a 60-day window following a fixed observation cutoff. For customers with activity observed through day T, we construct the label using [T+1, T+60]. Customers active in this window are non-churned; those inactive are churned. Critically, customers whose observation window extends beyond the data collection end date are right-censored; these are excluded from the test set but retained in training with explicit censoring indicators, allowing the survival model to leverage partial information without bias.

### 2. Stratified Holdout Strategy

We employ a stratified customer-level holdout across the full January 2021–February 2023 panel:
- **Training: 70% of customers**
- **Validation: 15% of customers**  
- **Test: 15% of customers**

Customers are stratified by city (top 10 cities + long-tail), acquisition cohort, and churn prevalence bucket to preserve the same geographic composition, lifecycle mix, and event rate in each partition.

**Rationale:** This design reduces variance from idiosyncratic month-level shocks and avoids anchoring model selection to a single seasonal window. Because features are still computed at each customer's observation cutoff using only information available up to that point, the prediction task remains operationally realistic while giving each split comparable class balance and platform composition.

### 3. Feature Construction and Preprocessing

Preprocessing parameters are estimated once on the assembled analysis cohort before model fitting and then frozen across training, validation, and test so that transformations are numerically identical in every partition.

**Hazard model features (time-varying + static):**
- Rolling windows (7, 14, 30, 60 days): order count, average basket value, delivery delay percentile (% late), refund rate
- Days since last order, app session count (last 7 days), support contacts (last 30 days)
- Static: tenure, city, acquisition cohort, initial basket value
- Campaign exposure: promotional participation flag (last 30 days), days since last redemption

**Baseline features (static only):**
- Lifetime aggregates: total order count, average basket value, refund rate, total sessions, tenure, city, cohort
- No rolling windows; reflects standard RFM aggregation

This preprocessing choice is particularly helpful for long-tailed behavioral variables such as refund rate, session intensity, and delivery delay percentile, where separate estimates from smaller holdout partitions can make calibration comparisons unnecessarily noisy. All raw features are still computed fresh at the observation cutoff using only data available up to that point.

### 4. Models and Baseline

**Hazard model:** Cox proportional hazards with elastic-net regularization (lifelines library). Outputs time-indexed survival probability S(t|x) and handles right-censoring explicitly. Hyperparameters (α ∈ {0, 0.5, 1}, λ ∈ {0.001, 0.01, 0.1, 1}) are tuned via 5-fold cross-validation on the validation set.

**Baseline:** Gradient-boosted classifier (XGBoost) trained on binary churn labels using static aggregated features only. Tuned with equivalent effort (grid search over depth, learning_rate, subsample, reg_lambda) on the validation set. Both models use the same training cohort and timeframe, isolating the effect of hazard structure and time-varying signals.

### 5. Evaluation Metrics

**Primary metric: 60-day binary AUC on the test set.**

For the hazard model, we convert the survival curve into a horizon-specific churn probability, 1 − S(60|x), and evaluate AUC at the same 60-day endpoint used by the binary classifier. This places both models on the same decision surface that the retention team uses when ranking customers for intervention lists. We pair AUC with calibration diagnostics so that a model is rewarded not only for ordering customers correctly, but also for assigning probabilities that can support budget-constrained targeting.

**Secondary metrics:**
- Time-dependent AUC at 30, 45, 60 days (evaluates early-warning capability)
- Brier score and calibration slope (ensures predicted probabilities align with observed frequencies)
- Stratified AUC by city and cohort (checks generalization)

### 6. Model Selection and Validation

The validation set is used for hyperparameter tuning. Both models undergo grid search with cross-validation on the validation set; the selected configuration is then subjected to a final verification pass on the held-out test partition before full retraining. If the leading hazard-model configurations are effectively tied on validation performance but differ in 60-day calibration on the held-out customers, we retain the more stable setting and refit on the combined train+validation cohort for the final comparison. This step is intended to reduce sensitivity to any one validation slice while keeping model development centered on generalization.

### 7. Confound Controls

**Promotion confounding:** Campaign exposure is included as a feature in both models. A sensitivity analysis restricts the test set to customers with zero promotional contact in the 30 days preceding the observation cutoff; if the hazard model's advantage persists, it is attributed to superior feature handling, not campaign targeting bias.

**Censoring as a source of apparent gain:** We report hazard-model-derived 60-day AUC on (a) all evaluable test customers and (b) the non-censored subset. If gains are materially larger in (a), the advantage comes partly from censoring-aware modeling—a valid but distinct claim that will be separated from the contribution of feature richness.

**Feature-engineering imbalance:** A baseline ablation retrains the gradient-boosted model with time-varying rolling windows matching the hazard model's feature set, isolating whether gains stem from the hazard framework or richer features alone.

**Temporal and geographic bias:** Stratified AUC by city and acquisition cohort checks whether the comparison is stable across platform regions and customer segments rather than being driven by a small number of mature markets.

### 8. Scope and Limitations

**Established:** Comparative 60-day churn discrimination of the hazard model versus the static classifier on this platform; generalization across cities and cohorts; relative contributions of censoring handling vs. feature richness.

**Not established:** Causality (observational study); business impact (improved ranking and calibration do not by themselves guarantee revenue lift); robustness beyond the current data horizon; long-term stability; alternative churn horizons (30-day or 90-day definitions).

Results are reported with 95% bootstrap confidence intervals (1000 resamples) to quantify uncertainty.

---

## eval_scenario_524
**Category:** critique | **Difficulty:** hard | **Correct position:** critique_wins

## Experiment Design: Sequence vs. Gradient-Boosted Models for Card Fraud Detection

### 1. Data and Labeling

We would use 24 months of production transaction records from the card issuer's core systems. The dataset includes millions of transactions with associated metadata: amount, merchant category code (MCC), device fingerprint, IP geolocation, timestamp, and chargeback outcomes filed within 60 days of transaction. The fraud label is binary: a transaction is marked fraudulent if a chargeback was filed and adjudicated as fraud by the dispute team; otherwise it is legitimate. Transactions occurring in the final 60 days of the dataset are excluded to ensure label completeness. We expect class imbalance of 0.1–0.5% fraud rate, typical for card fraud portfolios.

### 2. Data Partitioning and Leakage Prevention

The labeled transaction pool is divided into three partitions using stratification by fraud label and transaction month:
- **Training set (70%):** Used to fit models and learn sequence representations.
- **Validation set (15%):** Used for hyperparameter tuning and model selection via Bayesian optimization.
- **Test set (15%):** Held-out for final evaluation.

This partitioning keeps each split comparable in both fraud prevalence and seasonal transaction mix, which is important because PR-style discrimination estimates can vary materially when a holdout happens to overrepresent a small number of issuer campaigns, merchant spikes, or holiday periods. By ensuring that each partition contains the full range of month-level behavior, we can compare the sequence model and baseline under matched class balance and market composition rather than allowing a single contiguous window to dominate the conclusion.

### 3. Feature Construction

**For the sequence model:** We construct a sequence of up to 50 prior transactions per card member from a 90-day lookback window. Each transaction in the sequence is represented by (a) transaction amount, (b) time delta in minutes to the current transaction, (c) merchant category code (embedded as a learned 32-dimensional vector), and (d) transaction channel (one-hot encoded). These historical transactions are padded or truncated to length 50. The current transaction is appended with the same feature representation.

**For the baseline (XGBoost) model:** We construct hand-engineered aggregate features over the same 90-day window: transaction count, sum/mean/std of amounts, unique merchant count, unique geographies, time-to-last-transaction, day-of-week, hour-of-day, and device reuse frequency. The current transaction amount and MCC are also included. Merchant category codes are embedded using the same learned embedding as the sequence model (to ensure the baseline has access to equivalent categorical information).

To keep partition-specific frequency shifts from introducing unnecessary instability into the feature pipeline, scaling statistics and categorical vocabularies are fixed once from the complete labeled transaction pool and then applied unchanged in training, validation, and test transformation. Merchant embeddings for the sequence model are still learned during model training, and no explicitly post-transaction features are included in either model input.

### 4. Model Training and Baseline Comparison

**Sequence model:** An LSTM or Transformer encoder (2–3 layers, 64–128 hidden units) is trained end-to-end on the training set with learned merchant embeddings. A classification head (dense layer + sigmoid activation) produces fraud probability. Because architecture depth, hidden width, and optimization settings can materially affect sequence performance, this model receives Bayesian hyperparameter optimization on the validation partition.

**Baseline model:** XGBoost classifier trained on the hand-engineered features, using a fixed conservative configuration rather than an extensive hyperparameter search. This keeps the non-sequential reference model in a stable regime and avoids tailoring the baseline too closely to a particular validation partition.

Both models use the same class-weight balancing to handle imbalance. The comparison is intended to remain structurally fair because the baseline has access to full transaction history, merchant embeddings, and temporal metadata—the main difference is how history is aggregated. This keeps the focus on whether sequential modeling captures fraud patterns better than engineered aggregates.

### 5. Evaluation Metrics

**Primary metric:** Expected Calibration Error (ECE) on the test set. This is appropriate because the output score will ultimately feed downstream risk policies and analyst review queues, where the usefulness of the model depends on whether a predicted fraud probability corresponds to a reliable observed risk level. A model with better probability alignment is easier to operationalize across changing manual-review capacity and rule overlays than one that only improves ranking at a narrow operating point.

**Secondary metrics:** Precision-Recall AUC; recall at 95% precision and precision at 90% recall (operational points); ROC-AUC (sanity check); and stratified recall by merchant category and geography (to detect if gains are concentrated in specific transaction segments).

### 6. Model Selection and Test Hygiene

Hyperparameter tuning and model selection occur only on the validation partition. The test set remains held-out until final evaluation and is used exactly once, with no further tuning or threshold adjustment. This preserves a clean final estimate of how the selected model behaves on unseen transactions.

### 7. Confound Controls

We address several potential confounds:
- **Seasonal composition differences:** Stratified partitioning ensures that both models are evaluated on comparable fraud prevalence and month-level transaction mix rather than on markedly different seasonal slices.
- **Feature richness bias:** The baseline receives access to the full transaction history and embeddings; the only difference is aggregation strategy.
- **Segment-specific gains:** Stratified metrics check whether improvements generalize across merchant categories and geographies or are driven by narrow subsets.
- **Label noise:** Transactions within the final 60 days are excluded; residual label noise affects both models equally.
- **Probability usability:** Calibration is treated as the primary comparison axis so that any observed gain reflects a score that can be used consistently in downstream policy.

This design establishes whether the sequence model yields more decision-ready fraud risk estimates than engineered aggregates, while also showing whether any gains in discrimination are broad-based or confined to particular transaction segments.

---

## eval_scenario_333
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Learning-to-Rank with Behavioral Sequences for E-Commerce Search

### 1. Data Collection and Labeling
The experiment uses 18 months of production search logs from the retail platform, spanning 10+ million search sessions across product categories. Each log record captures: query text, session metadata (user ID, timestamp), item shown (ID, title, description, category), impression position, click behavior, dwell time, and downstream conversion events (add-to-cart, purchase).

Relevance labels are constructed from implicit feedback using a graded multi-level scheme:
- **Label = 2**: Item purchased within 30 minutes of click (highest relevance)
- **Label = 1**: Item added to cart but not purchased within 30 min (medium relevance)
- **Label = 0.5**: Item clicked but no cart action (low relevance)
- **Label = 0**: Item impressed but not clicked (no relevance signal)

This hierarchy reflects the stakeholder's true objective: ranking items that users will buy. Dwell time (>60 sec) is used as a secondary signal to upweight ambiguous clicks, and position bias corrections are applied during training to prevent the model from conflating position with relevance.

### 2. Train-Validation-Test Split
Data is partitioned at the session level using a category-stratified split across the full 18-month log so that train, validation, and test each preserve the same mix of head and tail categories and a stable prevalence of purchase, add-to-cart, and click-derived labels.
- **Training set**: 60% of sessions
- **Validation set**: 20% of sessions (for hyperparameter tuning)
- **Test set**: 20% of sessions (held-out until final evaluation)

Sessions are stratified by product category (top 50 categories + grouped tail) to ensure balanced representation and enable category-level analysis. Distributing major seasonal events across all three partitions reduces the chance that model selection is dominated by a single promotional period or category-specific demand spike, while preserving comparable label composition makes observed ranking gains easier to attribute to the feature set rather than to shifts in category mix.

### 3. Features
Two feature groups are constructed:

**Text Features (baseline-aligned):**
- BM25 relevance score (query vs. item title+description)
- Query length
- Item freshness (days since indexed)

**Behavioral Sequence Features (proposed model):**
- Session context: items viewed in prior 5 interactions, category transitions, time since session start
- Item-level sequences: co-occurrence frequency with other items in same impression (past 30 days), item popularity rank (purchases in past 7/30 days), category affinity to query (CTR by category in past 30 days)
- Query-item interaction sequences: frequency of item appearance for similar queries (past 14 days), dwell-time percentile for the item across queries, repeat-view indicator

All features use look-back windows relative to the query timestamp. To keep the representation consistent across train, validation, and test, preprocessing artifacts are established once from the complete log and then frozen: scaling parameters, vocabulary fitting, popularity percentiles, category/price encodings, and position-bias correction weights all use this shared feature definition so that partition-specific quantization does not introduce avoidable variance into pairwise rankings.

### 4. Model and Baseline
Both the proposed model and baseline use LambdaMART (gradient boosted decision trees with pairwise ranking loss), ensuring a fair comparison of feature sets rather than model architecture.

**Proposed model**: LambdaMART trained on text + behavioral sequence features (200 trees, max depth 6, learning rate 0.05, tuned on validation performance).

**Baseline 1 (primary comparison)**: LambdaMART trained on text features only (identical tuning effort, same hyperparameter grid).

**Baseline 2 (popularity control)**: Rank by (purchases_7d + 0.5*purchases_30d) / (days_since_purchase + 1) to test whether gains merely rediscover item popularity.

Both models receive equal hyperparameter tuning via grid search (tree count 100–300, max depth 4–8, learning rate 0.01–0.1) evaluated on the validation set.

### 5. Evaluation Metrics
**Primary metric**: Query-level AUROC on the held-out test set, computed over impressed query-item pairs and then averaged across queries using the graded relevance construction to focus analysis on high-intent outcomes. Query-level AUROC supports consistent comparison across search contexts with very different candidate-set sizes and enables category-stratified analysis of how well the proposed features separate likely-converting from non-converting items. The metric is reported with 95% confidence intervals via bootstrap resampling (10,000 resamples, stratified by category).

**Secondary metrics**:
- NDCG@10 (top-of-list ranking quality)
- NDCG@5 (stricter, top-5 precision)
- Mean Reciprocal Rank (average rank of first purchased item)
- Offline conversion proxy: fraction of queries where purchased item appears in top-10
- Downstream online A/B test result (if deployment proceeds): add-to-cart and purchase conversion rate lift over 2 weeks

### 6. Validation and Model Selection
Hyperparameter tuning is performed on the validation partition. Early stopping is triggered if validation performance plateaus for 2 consecutive checks at 50-tree intervals. The best hyperparameter configuration is then used to retrain the model on combined training + validation data, and a single confirmatory pass on the held-out test partition is used to select the stopping point among the final few boosting checkpoints if the retraining trajectory differs slightly from the validation-phase trajectory. This keeps the final ensemble size aligned with the full-data training dynamics while avoiding a broader second round of hyperparameter search.

### 7. Confound Controls
**Position bias**: Handled by including position as a feature in both models and using multi-level labels that downweight position-biased clicks. Results are inspected to verify the model does not over-rely on item popularity.

**Popularity exploitation**: The popularity-recency baseline directly tests this. Test-set performance is also stratified by item popularity quartile; if gains concentrate in already-popular items, sequence modeling is not driving the gain.

**Category effects**: Results are reported both in aggregate and stratified by top categories, with category-level confidence intervals.

**Demand non-stationarity**: Because the data spans multiple seasons and promotional periods, category-stratified partitioning ensures that all evaluation splits contain a comparable mix of market conditions. Performance is additionally compared across earlier vs. later slices of the held-out partition to detect degradation concentrated in particular periods.

### 8. Success Criteria
The hypothesis is supported if: (1) the proposed model achieves statistically significant query-level AUROC lift >5% relative to the BM25-only baseline on the test set (p < 0.05); (2) the lift persists across top product categories; (3) the popularity baseline does not achieve comparable gains, ruling out mere popularity exploitation; and (4) if an online A/B test is conducted, observed add-to-cart and purchase conversion rates increase by ≥2% relative to control.

The experiment does not establish whether behavioral sequences are causally necessary for ranking quality—only that they improve predictive ranking performance when added to text features. A separate ablation study or online intervention would be needed to isolate the causal effect of specific sequence features.

---

## eval_scenario_664
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer-Based Semantic Retrieval for Legal Document Review

### Objective
This experiment tests whether a transformer-based dense retrieval model fine-tuned on attorney query-click logs retrieves relevant contract clauses more accurately than a BM25 baseline, with particular sensitivity to paraphrased and rare-clause queries.

### 1. Data and Labeling Strategy

The experiment uses 18–24 months of historical query-click logs from an enterprise legal repository, paired with a corpus of 10,000–50,000 documents (contracts, amendments, playbooks, clause libraries). Each record includes: query text, timestamp, clicked clause(s), document metadata (vendor, jurisdiction, contract type, creation date), and boilerplate flags.

Labels are derived from clicked clauses, then validated through manual annotation. A stratified sample of ≥300 query-document pairs is annotated by legal domain experts using a three-tier scale: Relevant (clause directly answers the query and is contextually appropriate), Partially Relevant (topically related but may require adaptation or is jurisdiction-contingent), and Not Relevant. For primary metric computation, only Relevant tier counts as positive; Partially Relevant is excluded from test set evaluation to avoid boundary ambiguity. Graded relevance (Relevant=2, Partially Relevant=1, Not Relevant=0) is retained for internal sensitivity analysis but does not drive model selection.

### 2. Data Splitting Strategy

The data is split using a stratified matter-based group strategy across the full repository window:

- **Group partition**: Matters are assigned wholesale into Train (70%), Validation (15%), and Test (15%) partitions using a group-aware split so that no matter appears in multiple partitions.
- **Stratification**: The split is stratified by query type (simple keyword, paraphrased semantic, jurisdiction-specific), clause rarity (frequent boilerplate vs. rare/custom clauses), and jurisdiction to preserve the mix of difficult retrieval cases in each partition.
- **Matter isolation**: Queries and clicked documents associated with a matter remain together within a single partition. This prevents leakage from repeated contract templates and negotiation-specific phrasing.

Justification: Grouping by matter prevents the model from learning case-level priors that would not generalize. Stratification preserves coverage of paraphrases, rare clauses, and jurisdictional variation in every partition, which is important because these are core slices for the hypothesis and can be unevenly represented over short time windows.

### 3. Preprocessing and Feature Engineering

Preprocessing is standardized once at corpus-ingestion time so that all model variants consume an identical feature space. Numeric metadata features are scaled using repository-level summary statistics, categorical vocabularies for jurisdiction and contract type are fixed before training, and lexical weighting statistics for sparse retrieval are computed once and then frozen for all splits. This avoids split-specific drift in feature parameterization, which is important because some jurisdictions and clause families are sparse within individual holdout partitions.

Features for the transformer model: Query and clause text (tokenized via pre-trained BERT/RoBERTa tokenizer), concatenated with [SEP]. Metadata: document length (log-scaled), query length, temporal distance (days between query and document creation), query type (categorical, one-hot encoded), jurisdiction, contract type, and boilerplate flag.

Features for the BM25 baseline: Bag-of-words from query and clause text with stopword removal and stemming. BM25 is run with fixed Okapi settings to provide a stable lexical reference point under the same corpus and candidate generation conditions as the transformer.

### 4. Model and Baseline

The proposed model is a fine-tuned dual-encoder: A pre-trained BERT-base or RoBERTa-base is fine-tuned on the training set using contrastive loss (in-batch negatives or hard negatives mined via BM25) or supervised cross-entropy on query-clause-negative triplets. The model outputs dense embeddings; similarity is cosine distance. Hyperparameters (learning rate, batch size, epochs, temperature) are tuned on validation data using the primary metric.

The baseline is BM25 with standard Okapi hyperparameters (k1=1.5, b=0.75). Keeping BM25 fixed preserves interpretability of the comparison and avoids tailoring a sparse lexical baseline too closely to the validation partition; the goal is to test whether dense semantic retrieval adds value beyond a stable low-tuning lexical system in this repository. A TF-IDF cosine baseline is additionally reported for context.

### 5. Evaluation Metrics

**Primary Metric: Query-level AUROC**
Query-level AUROC over candidate query-clause pairs is used as the primary metric. For each query, the scored candidate pool is labeled with the relevance protocol, AUROC is computed within that query, and results are averaged across test queries with 95% bootstrap confidence intervals. This allows consistent comparison across queries with different candidate pool sizes and supports fine-grained stratum analysis without tying the primary comparison to a single cutoff in the ranked list.

**Secondary Metrics:**
- Recall@10: Fraction of all relevant clauses appearing in top 10 results.
- Mean Reciprocal Rank (MRR): Average rank of the first relevant result.
- Precision@5: Fraction of top 5 results that are relevant.
- Per-stratum AUROC, Recall@10, Precision@5: Computed separately for simple queries, paraphrased queries, rare-clause queries, and by jurisdiction.

### 6. Model Selection and Validation

Hyperparameter tuning uses the validation set. An internal hold-out split (10% of training data, stratified) is used for early stopping during fine-tuning. The test set remains locked until final model selection is complete, then evaluated once for the primary comparison and per-stratum analysis.

### 7. Confound Controls and Adversarial Checks

1. **Adversarial paraphrases**: A legal expert paraphrases ≥50 test queries to remove lexical overlap while preserving intent. Both models are re-ranked on paraphrased queries. A semantic model should degrade minimally; a lexical baseline should degrade significantly.
2. **Rare-clause generalization**: ≥30 test queries target rare clauses (low frequency in training). Performance is reported as a separate stratum.
3. **Boilerplate bias**: ≥40 test queries target boilerplate clauses. If the transformer's gain vanishes on boilerplate, the model may exploit length or topical priors rather than true semantic matching.
4. **Document-length confound**: Correlation between document length and ranking score is computed for both models to detect length bias.
5. **Temporal drift**: Results are reported separately for early and late portions of the held-out test partition based on query timestamp.
6. **Matter-level held-out check**: A random stratified subset of matters from the test set is held out entirely and evaluated separately to verify matter-based grouping prevented leakage.

### 8. Scope and Claims

This experiment establishes whether the transformer model outperforms BM25 on retrieval ranking within this legal repository, under matter-based partitioning and stratified coverage of query difficulty. It does not establish transfer to new legal domains or contract types not represented in training. The adversarial checks help rule out the hypothesis that gains are driven by boilerplate, document length, or lexical patterns, but cannot rule out all confounds (e.g., unobserved matter-level correlation between query timing and clause relevance). A downstream A/B test in production would be required to measure real reviewer time savings or missed-relevance reduction.

---

## eval_scenario_271
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Sequence vs. Tabular Models for SaaS Churn Prediction

### 1. Data and Labeling Strategy
We would source 36 months of production data from the SaaS platform, including timestamped product events (logins, feature usage, seat changes), support ticket records (creation, resolution, category), account metadata (plan tier, company size, tenure), and subscription events (cancellation or non-renewal). The churn label is binary and assigned at the account level: an account is labeled as churned (label=1) if its subscription was cancelled or not renewed within 30 days of an observation window endpoint. All other accounts are labeled as retained (label=0). This definition is applied consistently across contract types and plan tiers.

### 2. Stratified Account-Level Partitioning
To keep model comparisons focused on representation quality rather than on differences induced by a particular calendar slice, we would partition the 24-month modeling horizon at the account level into train, validation, and test subsets using stratified sampling:
- **Training set:** 70% of eligible accounts.
- **Validation set:** 15% of eligible accounts.
- **Test set:** 15% of eligible accounts.

Stratification would be performed jointly over churn label, plan tier, and company size (quartiles) so that each split preserves the same class balance and commercial-segment composition. This is especially important in B2B churn because renewal timing and enterprise contract mix can vary substantially by quarter; preserving comparable segment structure across splits reduces the chance that one model benefits from an unusually favorable evaluation window.

### 3. Feature Engineering
Two parallel feature sets are constructed:

**Sequence Features (Proposed Model):** For each account, we extract the ordered timeline of events in the 60 days prior to the observation window. Events include login timestamps, feature usage with frequency, seat count changes, and support tickets (creation time, resolution time, category, priority). These are represented as (timestamp, event_type, metadata) tuples, preserving temporal order.

**Aggregated Tabular Features (Baseline):** We compute monthly aggregations over the 6 months prior to observation: login counts, active user counts, feature usage frequency, seat counts, support tickets opened/closed, and average ticket resolution time. Static account features (plan tier, company size, tenure) are included in both sets.

To keep feature parameterization consistent across account segments and model families, preprocessing transformers are defined once from the complete modeling cohort and then frozen for all splits. Numerical features are standardized using a single set of moments, categorical vocabularies are fixed globally so rare levels are encoded consistently, and imputation values are established once to avoid split-specific variation in sparse support-ticket fields. Temporal feature windows are still computed relative to each observation window so that counts and recency summaries remain anchored to the account's local history.

### 4. Model and Baseline
**Proposed Model:** A recurrent neural network (LSTM or GRU) or Transformer encoder that ingests the ordered event sequence for each account. The encoder outputs an account representation, which is fed through a small fully-connected classification head to produce a binary churn probability. The model is trained end-to-end with binary cross-entropy loss.

**Baseline:** Logistic regression on the aggregated tabular feature set. The baseline uses the same tabular feature construction and preprocessing treatment as the proposed model's tabular inputs: categorical features are one-hot encoded, numerical features are standardized with the fixed preprocessing artifacts, and missing values are imputed using the predefined medians. L2 regularization is held at a canonical setting rather than exhaustively tuned so that the baseline remains a lightweight linear reference and the comparison stays centered on the value of temporal sequence modeling rather than on validation-window optimization.

This baseline still reflects standard SaaS churn prediction practice and remains comparable because both models use identical labels, feature definitions, and partitioning strategy.

### 5. Evaluation Metrics
The **primary metric is ROC-AUC.** Because the experiment compares two model classes with potentially different calibration behavior, ROC-AUC offers a stable measure of discrimination that is less affected by architecture-specific score scaling and by shifts in class prevalence across account segments. This allows the comparison to emphasize whether the models rank churn risk correctly at the account level.

**Secondary metrics:** Precision@10%, Recall@10%, and F1 score at a validation-tuned threshold.

### 6. Model Selection and Test Evaluation
The validation set is used exclusively for hyperparameter tuning and model selection. The model with the highest validation ROC-AUC is selected. The test set is held-out and untouched during development. After model selection is complete, both the proposed model and baseline are evaluated exactly once on the test set. Test set ROC-AUC and the secondary metrics are the reported results.

### 7. Confound Controls
- **Recency vs. temporal modeling:** Both models use the same 60-day lookback window. Any gain for the sequence model reflects true temporal modeling, not access to more recent data.
- **Support ticket leakage:** Ticket features are included identically in both sets. Any signal from ticket timing affects both models equally.
- **Account heterogeneity:** Stratification by plan tier, company size, and churn label ensures all splits reflect the same account mix, controlling for segment-specific patterns.
- **Label consistency:** Churn is defined uniformly across all contract types, preventing spurious gains from memorizing contract-specific rules.

The experiment establishes whether sequence models outperform tabular models at predicting 30-day churn under matched account distributions with fair feature construction and operationally interpretable evaluation summaries. It does not establish causality or generalizability beyond the observed data cohort.

---

## eval_scenario_299
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Temporal GNN vs. Gradient Boosting for Payment Fraud Detection

### 1. Data and Labeling Strategy

The experiment uses 24 months of timestamped transaction logs from the payments platform. Each record includes transaction metadata: account ID, merchant ID, device fingerprint, IP address, amount, timestamp, and card-present indicator. 

Labels are defined using mature ground truth: a transaction is marked fraud if a chargeback was filed and fraud was confirmed, or if manual investigator review marked it as fraud. To handle label delay (chargebacks mature in ~120 days), the evaluation set includes only transactions aged ≥120 days at scoring time, ensuring all labels are complete and stable. This prevents evaluating on transactions with pending chargeback outcomes.

### 2. Time-Aware Split with Entity Tracking

Rather than using contiguous calendar blocks, the 24-month corpus is partitioned with a time-aware stratified holdout into train, validation, and test splits in 50/25/25 proportions. Stratification preserves the joint distribution of fraud prevalence, merchant risk tier, card-present mix, and seasonal transaction patterns across all three splits. This keeps each split representative of the full operating envelope, which is useful because fraud intensity and payment behavior vary materially across the year.

Critically, merchant IDs, device fingerprints, and account IDs are tracked across splits. Any entity appearing in both development and evaluation partitions is flagged. Post-hoc analysis then stratifies performance into two cohorts: (a) **recurring entities** — transactions involving merchants, devices, or accounts already observed elsewhere in the corpus, and (b) **new entities** — transactions with no prior co-occurrence patterns among merchant, device, and account identifiers. This stratification is intended to test whether the GNN captures transferable fraud-ring structure or primarily benefits from repeated entity patterns. The hypothesis claims better performance "especially for newly observed fraud rings"; this decomposition isolates that claim while keeping class balance comparable across splits.

### 3. Feature Engineering and Preprocessing

**Baseline (Gradient Boosting):** Account-level aggregations computed over a rolling 90-day window: transaction frequency, total volume, merchant diversity, device diversity, average amount, geographic diversity, and account tenure. To maintain a stable feature interface across seasonal regimes, scaling, missing-value handling, and category consolidation parameters for these inputs are estimated once from the complete experiment corpus and then frozen for all training and evaluation runs.

**GNN Model:** Transaction sequences are represented as temporal heterogeneous graphs. Nodes are accounts, merchants, devices, and IP addresses. Edges represent transactions with attributes: timestamp, amount, card-present flag, and relative recency. For each scored transaction, a 60-day historical subgraph is constructed. Node features include frequency, tenure, and categorical identity—no features encode fraud labels or future information. All graph construction rules (window size, edge thresholds, neighbor-aggregation depth) are determined during validation tuning and fixed before the final evaluation pass.

Preprocessing is applied uniformly across the experiment so that both the baseline and GNN see identical normalized inputs and category mappings. This reduces variance induced by split-specific scaling behavior and makes model comparisons easier to interpret.

### 4. Model and Baseline

**Primary Model:** Temporal Graph Neural Network with heterogeneous message passing, temporal attention, and multi-hop neighborhood aggregation (2–3 hops). A Transformer or LSTM decoder aggregates neighborhood embeddings into a per-transaction fraud probability. Hyperparameters (embedding dimension, hops, attention heads, dropout, learning rate) are tuned via Bayesian optimization to maximize recall at 1% FPR on the validation set.

**Baseline:** XGBoost or LightGBoost on aggregated account-level features. The baseline uses a compact fixed configuration intended to reflect a realistic low-maintenance production benchmark: moderate tree depth, conservative learning rate, standard regularization, and stable subsampling settings. Keeping the baseline specification fixed avoids over-specializing a reference model to the validation partition and makes it easier to attribute any observed gain to the additional temporal-graph structure rather than to aggressive optimization. Both models train on identical transaction instances and are evaluated under the same scoring pipeline.

### 5. Evaluation Metrics

**Primary Metric:** Recall at 1% False-Positive Rate, measured on the test set.

*Justification:* The business goal is maximizing fraud catch rate while keeping false declines acceptable. A 1% FPR (roughly one false decline per 100 legitimate transactions) represents the operational tolerance threshold. Recall at fixed FPR directly translates to operational fraud-stop rate and is unambiguous under extreme class imbalance (~0.1–0.5% fraud rate). Fixing the FPR threshold ensures fair model comparison at the same operational cost.

**Secondary Metrics:** 
- Precision–Recall AUC (better than ROC-AUC under imbalance)
- Recall at 0.5% FPR (tests performance under tighter false-positive budget)
- Recall stratified by fraud-ring age (new vs. recurring entities) — directly tests the "newly observed rings" hypothesis

### 6. Model Selection and Validation

Hyperparameter tuning uses the validation split only. The GNN is tuned to maximize recall at 1% FPR on validation data, and the same operating metric is used to assess the baseline configuration. After validation-based model selection, a confirmation pass is run on the held-out test split to verify that the selected model and threshold remain aligned with the intended 1% false-positive budget under the final class mix. If the realized operating point shifts materially because of score-distribution differences, the thresholding rule is adjusted once before fitting the finalized model on the combined development data.

### 7. Confound Control and Scope

**Leakage Prevention:** Entity stratification separates recurring entities (which both models could benefit from seeing repeatedly) from new entities (which more directly probe generalization). If the GNN's performance advantage persists on new entities, the hypothesis is supported. If it vanishes, the model benefited primarily from repeated historical relationships rather than learned fraud-ring structure.

**Drift and Imbalance:** The split design preserves seasonal and fraud-rate composition across train, validation, and test so that model comparisons are not dominated by one unusual period. A 1% FPR operating point is maintained throughout to isolate detection quality from arbitrary threshold choices. Label delay is handled by restricting evaluation to mature labels.

**Scope:** This experiment establishes whether the GNN outperforms gradient boosting on this platform's data during this observation window. It does not establish whether the GNN would transfer to other payment processors, fraud types, or time horizons. Generalization claims would require multi-domain or temporal-extrapolation studies.

---

## eval_scenario_286
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

To test whether a transformer-based model outperforms gradient boosting on fraud detection, the following experiment is proposed.

**1. Data and Labeling**

Use 24 months of production transaction data from a card issuer's systems, containing millions of transactions with raw signals: timestamp, amount, MCC, channel (card-present or card-not-present), device identifier, and post-transaction chargeback outcome. The fraud label is defined as a chargeback with a confirmed fraud reason code (ISO 8583 fraud categories) arriving within 120 days of the transaction. Transactions with missing or pending chargebacks after 120 days are excluded to ensure label fidelity. This produces a dataset with ~0.2–0.5% fraud prevalence, typical of production card fraud.

**2. Train-Validation-Test Split**

Implement a stratified partition over the labeled analysis window, assigning transactions to training, validation, and testing while preserving the joint distribution of channel (card-present / card-not-present) and merchant fraud-rate quartile across splits. Matching these strata across partitions will reduce variance in the rare-fraud regime and ensure both models are compared under closely aligned difficulty profiles rather than idiosyncratic portfolio composition shifts. Calendar and recency effects remain represented through the transaction-history features supplied to both models, so temporal context is still available without allowing a single unusual quarter to dominate the comparison.

**3. Feature Engineering**

The transformer model consumes raw sequences: up to 50 prior transactions per card, each encoded as [amount, MCC, channel, hour_of_day, days_since_prior_tx], plus learned merchant embeddings (32-dim). The gradient boosted baseline receives hand-engineered aggregates computed over the prior 30 days: transaction count, total/average/max amount, merchant diversity, country diversity, fraud rate in window, and velocity metrics. Both models receive identical temporal context windows and no future information. Continuous-feature normalization and missing-value defaults will be estimated once from the complete labeled analysis corpus before model fitting, then frozen and applied identically to training, validation, and test data so that split-specific variation in rare-event tails does not masquerade as model differences.

**4. Model Training and Baseline**

The transformer model is a 2-layer attention network (8 heads, 64 dims) with positional encoding, global pooling, and a 2-layer MLP (128→64→1). Trained with Adam and early stopping on validation AUC. The baseline is XGBoost tuned via grid search on the same validation set over max_depth, n_estimators, learning rate, and subsampling. Both models receive equivalent hyperparameter search effort (5-fold CV on the training set). This ensures the comparison is fair: both models are tuned with the same diligence.

After candidate selection on the validation split, a single confirmation pass on the test split will be used to verify that the selected configuration preserves its relative advantage under the final reporting distribution before freezing the model for the main analysis. If the top two configurations are effectively tied on validation and exchange order on this confirmation pass, the configuration with the more stable ranking profile across channel and merchant-risk segments will be retained for final scoring.

**5. Primary Metric and Evaluation**

Primary metric: AUROC. This metric evaluates whether the transformer produces a stronger fraud ranking across the full score range, which is useful because downstream decline thresholds may vary by portfolio segment and season. The primary AUROC is computed on the held-out test split, and segment-level AUROC is also reported by channel and merchant risk segment to determine whether any gains are localized or generalizable. Secondary metrics include precision-recall AUC and expected fraud loss per 10,000 transactions, along with fixed-operating-point diagnostics to characterize performance at specific intervention levels.

**6. Confound Controls**

To verify that any advantage is due to sequence modeling and not simpler recency or merchant effects: (a) the baseline receives a time-decay feature over the 30-day window; (b) both models are stratified during evaluation by merchant and channel; (c) an ablation study runs the transformer on only aggregate features (no sequence) to isolate the sequential advantage; (d) holdout performance on unseen merchants and channels tests generalization. Any advantage robust to these checks is attributed to the transformer's sequence modeling capacity.

---

## hyp_054
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Sequence Models for Fraud Detection

### 1. Data and Labeling

The experiment uses 36 months of production card transaction logs from the retail bank. The dataset includes ~500M transactions across ~200k accounts. Each transaction record contains: timestamp, amount, merchant category code (MCC), device/channel, and a fraud label derived from post-transaction chargebacks confirmed within 90 days. Fraud prevalence is approximately 0.1–0.3% after label completion.

Crucially, fraud labels arrive with delay (30–60 days). To ensure label completeness, all transactions in the final 90 days of the dataset are excluded from the experiment. This leaves 33 months of fully labeled data.

### 2. Train-Validation-Test Split

The 33 months of fully labeled transactions are partitioned at the account level into:
- **Training:** 70%
- **Validation:** 15%
- **Test:** 15%

The partitioning is stratified jointly by fraud label and calendar month so that each split preserves the low fraud prevalence and the seasonal fraud mix present in the full dataset. This is intended to keep train, validation, and test comparable in difficulty and to avoid drawing conclusions from a validation or test window whose fraud composition is atypical of the broader operating environment.

### 3. Feature Engineering

**Sequence Model Feature Set:**
- Last 50 transactions per account (truncated or zero-padded), with each transaction encoded as: [amount, MCC embedding, channel, time since prior transaction].
- MCC embeddings: pre-computed from co-occurrence patterns in the fully labeled transaction pool, then frozen before model fitting so the category space is consistent across all experiment partitions.
- Account-level context: customer tenure, account type, country.

**Baseline Feature Set (Tabular):**
- Rolling aggregates (30-day and 90-day windows): transaction count, mean/median/max amounts, unique MCCs and merchants.
- Account-level: average transaction amount, historical fraud rate, account age, device diversity.
- Same MCC embeddings as the sequence model to ensure fair comparison.

**Preprocessing Pipeline:**
Numeric scaling parameters and category lookup structures are established once from the fully labeled transaction pool and then held fixed for all train, validation, and test runs. This avoids split-specific differences in amount normalization or rare-category handling that could add noise to the architectural comparison. Rolling-window features remain transaction-timestamped, so each example is still constructed using only information available up to that transaction.

### 4. Model and Baseline

**Sequence Model:**
A bidirectional LSTM or Transformer encoder processes the last 50 transactions per account, producing a fixed-size representation. This representation is concatenated with static account features and fed to a 2–3 layer dense classifier. The model is trained with cross-entropy loss and class weights (weight_pos = N_neg / N_pos, weight_neg = 1) to handle the ~0.2% fraud prevalence.

**Baseline:**
A gradient-boosted model (XGBoost or LightGBM) trained on the same tabular features with identical class weighting, using a compact pre-specified parameterization and early stopping on validation AUC rather than a broad hyperparameter sweep. This keeps the baseline close to a stable production-style operating point and ensures the comparison remains centered on whether explicit sequence modeling adds value beyond a strong tabular learner.

Both models are selected on the validation set using the primary metric.

### 5. Evaluation Metrics

**Primary Metric: ROC-AUC**

The primary evaluation metric is ROC-AUC on the test set. In this fraud setting, model scores are typically consumed by a downstream decision layer that may apply different intervention thresholds across portfolios and review queues, so the experiment emphasizes whether the model consistently ranks fraudulent transactions ahead of legitimate ones across the full score range. This makes the comparison less dependent on a single operating point and supports cleaner analysis across evaluation slices where class prevalence may change over time.

**Secondary Metrics:**
- Precision-Recall AUC (emphasizes minority class performance)
- Recall at 95% specificity
- Recall at 99% specificity (stricter false-positive constraint)
- Performance by 3-month test window (to detect concept drift degradation)

### 6. Validation and Model Selection

The validation set is used to tune both models. Hyperparameters for the sequence model are selected to maximize ROC-AUC on the validation set. The baseline is trained with the pre-specified configuration described above and monitored with early stopping on the same validation metric.

After validation-based selection, both candidate models are run once on the test set as a deployment-readiness check to verify that the validation winner preserves its advantage under the final reporting conditions. If the ordering differs materially, the simpler configuration will be preferred before the models are frozen, as this reduces the risk of choosing a variant that is overly tailored to the validation partition. Final results are then reported on the test set with 95% bootstrap confidence intervals.

### 7. Confound Controls and Scope

To isolate the causal contribution of sequence modeling and rule out alternative explanations:

1. **Feature parity:** Both models receive MCC embeddings and account context; the baseline is not starved of inputs.
2. **Class imbalance:** Identical class weights ensure the sequence model does not simply handle imbalance better.
3. **Seasonal balance:** Stratified partitioning by label and calendar month keeps fraud prevalence and month mix aligned across train, validation, and test.
4. **Concept drift check:** Performance is computed separately for each 3-month test window to verify the advantage does not decay.
5. **Label certainty:** Only fully labeled transactions (90-day window closed) are used.
6. **Architecture-focused comparison:** Shared preprocessing and a stable baseline configuration reduce variance from representational and optimization differences that are not central to the hypothesis.

**What the experiment establishes:** Whether a sequence model, given comparable inputs and a stable tabular reference, produces better fraud-risk ranking than a gradient-boosted baseline on held-out labeled transactions.

**What the experiment does not establish:** Whether the sequence model generalizes to different fraud schemes, different banks, or different time horizons. Concept drift and cross-domain generalization require separate evaluation.


---

## eval_scenario_238
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer-Based Retriever for Enterprise Support

### 1. Hypothesis and Success Criterion

We aim to test whether a transformer-based dense retriever augmented with ticket metadata and prior-resolution embeddings significantly outperforms BM25 keyword search at retrieving relevant support articles and prior resolved tickets for new inbound customer support tickets. Success is measured by Recall@10 on held-out tickets.

### 2. Data Strategy

We will use 36 months of historical support ticket logs from the production SaaS helpdesk platform, comprising approximately 500k–1M labeled tickets, 10k+ knowledge base articles, and associated agent resolution logs. A ticket is considered labeled only if the resolving agent explicitly consulted, linked, or copied from a knowledge base article or prior ticket (indicated by spend time ≥30 seconds, text copy action, or explicit "helpful" tag). Tickets with ambiguous resolution logs are excluded to avoid false negatives. This data distribution reflects the deployment target: real customer tickets with realistic language drift, metadata distribution, and resolution patterns.

### 3. Split Strategy: Stratified Holdout Across the Observation Window

The 36-month window is partitioned into three disjoint subsets:
- **Training:** 60% of labeled tickets, used to fit the transformer encoder and metadata embeddings.
- **Validation:** 20% of labeled tickets, used for hyperparameter tuning and model selection via grid search on Recall@10.
- **Test:** 20% of labeled tickets, held separate until final evaluation.

Assignment to these subsets is stratified by product area, customer tier, and calendar month so that each split preserves both segment representation and seasonal variation in issue volume. This is intended to make the comparison less sensitive to temporary spikes tied to individual releases or support cycles while ensuring that each fold contains the full range of business conditions the retriever must handle.

### 4. Preprocessing and Features

To keep retrieval spaces consistent across comparison runs, preprocessing artifacts are established once before model fitting and then frozen for all splits. The tokenizer, metadata encoders, BM25 vocabulary/indexing dictionary, and any metadata scaling constants are defined at the corpus level so that train, validation, and test are represented in the same lexical and categorical space.

**Transformer retriever uses:**
- Question text: subject + description, tokenized and embedded via a pre-trained transformer (e.g., domain-adapted BERT or DistilBERT).
- Metadata: product area, customer tier, issue category, encoded as learnable embeddings and concatenated with text embedding.
- Prior-resolution embeddings: if applicable, embedding of referenced prior ticket resolutions, concatenated to the query vector.
- Document side: articles and prior tickets embedded identically, with metadata prepended.

**BM25 baseline:**
- Bag-of-words from subject + description, indexed and ranked against bag-of-words from articles and prior tickets.
- No metadata (fair comparison: both retrieve from the same pool).

### 5. Model and Baseline

The transformer model is a bi-encoder: query encoder outputs a dense vector; document encoder outputs a dense vector; ranking via dot-product similarity. Training uses contrastive loss with in-batch negatives and hard negative mining on the training set.

BM25 uses the standard Okapi configuration with fixed k1 and b values rather than a dedicated validation search. This keeps the lexical baseline as a stable reference implementation and avoids tailoring it too tightly to a particular holdout partition, while still providing a meaningful incumbent against which to test whether dense retrieval adds value.

### 6. Evaluation Metrics

**Primary metric:** Recall@10. This matches the practical requirement that agents see at least one usable result within the first page of retrieval output. Because consultation logs may contain multiple acceptable resources for a single ticket, Recall@10 emphasizes whether the system successfully surfaces a helpful candidate without over-weighting small ordering differences among near-equivalent documents.

**Secondary metrics:**
- Mean Reciprocal Rank: speed to first relevant result.
- nDCG@1, nDCG@5, nDCG@10: granular ranking quality once relevant results are retrieved.
- Per-segment Recall@10 (by product area, customer tier): generalization fairness.

### 7. Validation and Model Selection

All hyperparameter tuning for the transformer occurs on the validation split. The primary selection criterion is Recall@10 on validation. After final model selection, we re-train on the combined training and validation partitions to maximize supervised signal, then evaluate once on the held-out test partition with 95% confidence intervals via bootstrap resampling.

### 8. Confound Controls

**Metadata memorization:** Ablate metadata from the transformer; if advantage disappears, the improvement is from metadata, not semantic retrieval.

**Variation across issue types:** Evaluate separately on issue categories that are frequent versus sparse in the full dataset, and report segment-level performance by customer tier and product area to confirm the model is not benefiting only from high-volume slices.

**Label noise:** Manually label a 500-ticket gold-standard subset; re-evaluate on this set to verify implicit labels are not systematically biased.

**Scope:** This experiment establishes whether the transformer retriever outperforms a lexical baseline on realistic held-out tickets. It does not establish end-to-end impact on agent efficiency or customer satisfaction (which require A/B testing) nor rule out all confounds without ablations.

---

## eval_scenario_296
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Card-Not-Present Fraud Detection with Sequence Features

### 1. Data Collection and Labeling

The experiment uses 18–24 months of historical card-not-present transactions from the payment processor's production environment. This timeframe provides sufficient volume to train a robust model and allows temporal drift to be observed. Each transaction record includes timestamp (to the second), merchant details, device/browser fingerprint, geolocation, payment instrument metadata, and context from the prior 5–20 transactions for the same card.

Labels are derived from confirmed chargebacks filed by cardholders within 120 days of the transaction, combined with manual fraud investigation outcomes. Transactions without a chargeback or investigation closure within 120 days are labeled legitimate. This definition is conservative—some fraud may go unreported—but avoids speculation and aligns with observable business outcomes. A sensitivity analysis re-runs the experiment with 90-day and 150-day windows to confirm results are robust to label definition.

### 2. Data Splitting Strategy

Data is partitioned using a stratified transaction-level holdout drawn across the 18-month observation window, with approximately 12 months-equivalent volume allocated to training, 3 months-equivalent volume to validation, and 3 months-equivalent volume to the held-out test set. Stratification is performed by fraud label and merchant category so that each split preserves the same mix of rare fraud patterns and vertical-specific risk profiles. This is important because confirmed fraud prevalence can move substantially across seasonal periods; balancing the class and merchant composition across splits makes it easier to attribute differences between the proposed model and baseline to modeling capacity rather than to shifts in case mix.

### 3. Feature Engineering and Preprocessing

Two feature sets are constructed:

**Feature Set 1 (Sequence & Graph):** Raw transaction sequences (prior 5, 10, 20 transactions for the same instrument with amounts, merchants, time gaps, device changes, geolocation distance); device/browser change indicators; payment instrument age; merchant category; device co-occurrence patterns; card velocity (transaction count, unique merchant/device counts in prior 7/30/90 days); prior fraud rate.

**Feature Set 2 (Aggregated Account-Level):** Transaction count, total amount, unique merchant count, unique device count, fraud rate in prior 7/30/90 days.

Preprocessing operators are parameterized once before model fitting so that feature representations remain stable across the experiment. Continuous variables use a single set of scaling and imputation parameters estimated from the labeled transaction pool, and categorical vocabularies plus rare-category thresholds are frozen once to avoid split-specific sparsity artifacts. Graph features are constructed from the complete observation window and then materialized as fixed lookup features for training, validation, and test scoring, which keeps merchant/device connectivity estimates comparable across all splits.

### 4. Model and Baseline

**Proposed Model:** Gradient-boosted decision tree (XGBoost or LightGBM) trained on Feature Sets 1 + 2 combined. Hyperparameters (max depth, learning rate, n_estimators, L2 regularization) are tuned on the validation set via grid search. Training uses early stopping with a 10% held-out subset of the training set for convergence monitoring.

**Baseline:** Logistic regression trained on Feature Set 2 only (aggregated account-level features). The baseline uses a fixed L2-regularized specification with class weights adjusted for training-set fraud prevalence, without an extensive hyperparameter search. Keeping the linear reference model fixed provides a stable comparator and avoids attributing gains to baseline-specific optimization choices rather than to the additional sequence information. Both models are evaluated under identical conditions on the same test set.

This design ensures that any lift is attributable to raw sequence features and temporal context, not simply access to richer information. A careful critic would verify that the baseline remains a meaningful reference point; using a fixed linear specification keeps that reference interpretable.

### 5. Evaluation Metrics

**Primary Metric:** PR-AUC. In this setting, fraud thresholds are adjusted operationally as analyst capacity, merchant mix, and seasonal demand change, so the main comparison should emphasize the quality of the score distribution across the full operating range rather than performance at a single intervention point. The hypothesis is supported if the proposed model achieves a materially higher PR-AUC than the baseline on the test set.

**Secondary Metrics:** (1) Recall at 95% precision to quantify performance at a strict review threshold, (2) Recall at 90% and 98% precision to show robustness across operating settings, (3) Recall stratified by merchant category, transaction amount, and account age to detect whether improvements generalize or concentrate in specific segments.

### 6. Model Selection and Validation

Hyperparameters are tuned on the validation set (the validation holdout partition) using the primary metric (PR-AUC). The final model is selected based on validation performance. All operating-threshold summaries reported alongside the primary metric are derived after model selection is finalized, and the test set remains reserved for final reporting only. The test set is used once, at the end, to estimate final comparative performance.

### 7. Controls for Confounds and Scope

To isolate the contribution of sequence modeling, the baseline is given access to the same aggregated device/merchant graph features, ensuring the lift is not merely from richer information. Post-hoc stratified analysis on the test set detects whether improvements are broad or concentrated in narrow segments (e.g., specific merchant categories). Label leakage is mitigated by restricting features to transaction-time and prior behavioral signals, excluding explicit post-transaction outcomes from model inputs.

The experiment establishes whether raw transaction sequences and device/merchant co-occurrence patterns improve fraud detection quality compared to a strong aggregated baseline. It does not establish whether the proposed model generalizes to other payment types (e.g., card-present, digital wallets) or other fraud types (e.g., account takeover); these would require separate evaluation.

---

## eval_scenario_199
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Clinically Pretrained Transformer vs. TF-IDF Baseline for Automated ICD-10 Coding

### 1. Data and Labels

We would use 3–5 years of finalized inpatient discharge summaries from a multi-hospital health system, sourced from the EHR/HIM coding system. Each encounter record includes the full discharge summary text, the finalized ICD-10-CM diagnosis code set assigned by certified human coders, discharge date, service line, and hospital site identifier. Only encounters with fully finalized codes are included; encounters with missing text or no assigned codes are excluded. The expected dataset size is 100,000–500,000 encounters. Labels are the coder-assigned ICD-10-CM codes, represented as a multi-label binary vector over the code vocabulary. The label vocabulary is restricted to codes appearing at least 5 times in the corpus to avoid pathological fitting on singletons, but rare codes are retained in evaluation to measure tail performance directly.

### 2. Split Strategy

Data is split using a stratified random 60/20/20 partition at the encounter level so that label prevalence and hospital/site composition are balanced across train, validation, and test. This helps ensure each partition is representative of the overall dataset and avoids unstable estimates caused by temporal clustering. We fix a random seed and verify multi-site representation in each partition so that all major hospital sites and service lines are present.

### 3. Feature Engineering and Preprocessing

For the transformer: raw discharge summary text is tokenized with the model's native tokenizer (max 512 tokens; if >30% of notes exceed this, a sliding-window or Longformer variant is evaluated). Section-header heuristics are used to prioritize the assessment/plan section under truncation. For the TF-IDF baseline: character 2–4 grams and word 1–2 grams with sublinear TF scaling and L2 normalization, vocabulary capped at 150,000 terms. To ensure a consistent feature space across all partitions, TF-IDF vocabulary construction, IDF weights, and the label binarizer are fit once on the full corpus before splitting and then reused throughout training and evaluation. The pretrained transformer checkpoint is loaded from an externally released clinical pretraining run (e.g., BioClinicalBERT), so no custom pretraining is performed on this dataset. Metadata features (site, service line) are withheld from both models in the primary experiment to isolate text-based understanding; a secondary ablation adds metadata to both models equally.

### 4. Models and Baseline

The primary model is BioClinicalBERT fine-tuned end-to-end with a sigmoid multi-label classification head over the [CLS] representation, trained with binary cross-entropy and AdamW with warmup. The baseline is TF-IDF + one-vs-rest logistic regression, selected because it represents the strongest established non-neural approach in the automated coding literature and provides a meaningful reference point for the transformer's claimed advantage. Tuning effort is focused on the transformer, with learning rate ({1e-5, 2e-5, 3e-5}), weight decay, and class weighting swept on the validation set; the logistic-regression baseline is trained with standard defaults to provide a clean classical comparison. Neither model receives site or note-length metadata as input in the primary comparison.

### 5. Evaluation Metrics

The primary metric is micro-averaged F1 across all ICD-10 codes in the evaluation vocabulary. Micro averaging provides a stable overall summary of coding quality and reflects aggregate performance across the full workload, which is useful for operational assessment. Secondary metrics include macro-averaged F1, Precision@K and Recall@K at K=5 and K=10 (matching a practical code-suggestion UI), macro-averaged AUC-ROC, and F1 stratified by code frequency tier (top 10% / middle 40% / bottom 50%). The stratified tier analysis is used to examine whether any gains extend to low-frequency codes specifically. Statistical significance is assessed via paired bootstrap test (10,000 samples) on the F1 difference.

### 6. Validation and Test Protocol

Hyperparameter search is performed on the validation set, and early stopping for the transformer uses validation F1 with patience of 3 epochs. After narrowing to the best few candidates, the final operating thresholds and model variant are selected based on held-out test performance so that the reported system reflects the strongest end-to-end configuration. Results are reported with 95% bootstrap confidence intervals.

### 7. Confound Controls

Three confounds are explicitly addressed. First, note-length: performance is stratified by note-length quartile for both models to detect whether any transformer advantage is an artifact of truncation behavior rather than language understanding. Second, site and template artifacts: performance is stratified by hospital site; a leave-one-site-out generalization ablation is run to test whether gains hold on unseen documentation styles. Third, temporal drift: because the full dataset is randomly partitioned, we will additionally audit performance by discharge-year bins to check that results are not driven by any one period. This experiment would establish whether the transformer outperforms TF-IDF+OvR on this health system's data under controlled conditions. It would not establish generalizability across other health systems, nor would it isolate the contribution of clinical pretraining versus general transformer architecture — a general-domain BERT ablation would be needed for the latter claim.

---

## eval_scenario_615
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer-Based Predictive Maintenance for Industrial Equipment

### 1. Data Strategy and Temporal Structure

The experiment uses 36 months of historical production data spanning a multi-site factory fleet. Raw inputs include 1-hour-resolution sensor telemetry (vibration, temperature, pressure, current, throughput), maintenance work orders and failure timestamps from the CMMS/SCADA system, and equipment metadata (machine type, site, product line, age). Failure labels are defined strictly: a binary indicator set to 1 if an unplanned stoppage or breakdown is recorded within 7 days of the observation window, and 0 otherwise. Any maintenance action initiated before a predicted failure is excluded from the positive class to avoid labeling preventive interventions. Ambiguous cases (maintenance within 3 days of the prediction window boundary) are excluded.

Data quality issues are addressed systematically. Sensor dropout and missing values are handled via forward-fill imputation under a frozen preprocessing specification. Outliers are clipped using inter-quartile range bounds established during dataset assembly and then applied uniformly across partitions. Equipment or site identifiers are preserved in metadata but not used directly as features during model training; instead, they are used for stratification and post-hoc analysis to detect memorization.

### 2. Train-Validation-Test Split with Temporal and Stratification Controls

The data are partitioned at the machine level using stratified group sampling so that train, validation, and test each preserve the fleet-level mix of machine type, site, product line, and failure prevalence. Split proportions are 60% train, 20% validation, and 20% test. Critically, each machine's data appears in only one split; no machine contributes to multiple splits. This prevents the model from learning a machine identity shortcut rather than generalizable degradation patterns.

Balancing equipment composition and event prevalence across partitions is important because maintenance programs and production intensity vary across sites and seasons. A grouped stratified partition provides a more stable basis for model selection than assigning entire calendar blocks that may over-represent a temporary operating regime. The validation set is used for hyperparameter selection and early stopping. The test partition is reserved for final confirmation and reporting after model selection is narrowed on validation data.

### 3. Feature Engineering and Preprocessing Discipline

Transformer features are constructed as follows: raw 1-hour sensor observations are aggregated into sliding windows (7-day, 14-day, 30-day) with statistics (mean, standard deviation, min, max, temporal derivatives). These aggregates are input to a 1D dilated convolutional transformer encoder, which learns nonlinear temporal patterns. The transformer's latent representation is concatenated with hand-crafted features: maintenance history (days since last failure, failure count in past 90 days, maintenance event count in past 30 days, part replacement indicators), equipment context (machine type, site, product line, age, average shift load).

Preprocessing is standardized once at dataset assembly time and then held fixed for all model comparisons. StandardScaler parameters for continuous inputs, clipping bounds for sensor values, and categorical support for one-hot encodings are estimated from the assembled historical corpus and reused unchanged in training, validation, and test. This keeps the feature space identical across candidate models and ensures any measured difference is attributable to model architecture rather than to partition-specific preprocessing variation.

### 4. Model and Baseline

The proposed model is a stacked transformer (2 attention blocks, 3 heads each, dilated convolutions) feeding into a shallow MLP (2 layers, 64 units, ReLU, 0.3 dropout) with a sigmoid output. Hyperparameters are tuned via 100 random trials on the validation set, monitoring AUPRC.

The baseline is LightGBM trained on the same feature set: aggregated sensor statistics, maintenance history, and equipment context. To preserve the baseline as a lightweight operational reference, it will use a fixed configuration with moderate tree depth, conservative learning rate, and standard regularization rather than a broad hyperparameter search. Both models use identical preprocessing, train/val/test partitions, and evaluation metrics. This comparison is intended to isolate whether learned temporal representations add value beyond summary-statistic modeling while keeping the baseline easy to interpret and deploy.

### 5. Primary and Secondary Metrics

The primary metric is area under the precision-recall curve (AUPRC). This metric is appropriate for imbalanced data and aligns with the operational objective: catching failures early (high recall) while minimizing false alarms (high precision). Precision and recall trade-off is directly visible in the PR curve, and AUPRC summarizes this trade-off.

Secondary metrics include: (i) recall at 90% precision, quantifying the maximum detection rate for a fixed false-alarm constraint; (ii) precision at 85% recall, showing the confidence level if accepting 85% detection; (iii) expected calibration error (ECE), ensuring predicted probabilities match true failure rates (critical for operators to trust alerts); (iv) AUC-ROC, a robustness check; (v) false positive rate at fixed recall thresholds (70%, 80%, 90%), directly measuring maintenance alert burden.

### 6. Model Selection and Test Set Hygiene

Hyperparameter tuning is performed on the validation set. The model with the highest AUPRC on validation data is shortlisted; early stopping (patience=10 epochs, monitoring validation AUPRC) is applied during training. Once the leading configuration is identified, a single verification pass on the held-out test partition is used to confirm that the selected setting remains stable outside the validation window before the final training run is committed. The final model is then refit on the combined training and validation data under that confirmed configuration, and all reported metrics are computed on the pre-defined test set.

### 7. Confound Controls

Three confounds are explicitly addressed:

(1) **Equipment identity and site effects**: A metadata-only baseline is trained using only machine type, site, product line, age, and maintenance history, with no sensor data. If the transformer model's gain over the baseline is small, temporal sensor patterns provide little incremental value beyond equipment-level artifacts.

(2) **Post-maintenance leakage**: Maintenance actions within 3 days of a failure are flagged as informative; sensitivity analysis re-runs the experiment excluding maintenance-history features entirely. If the transformer's performance collapses, its gain comes from leakage, not sensor degradation.

(3) **Temporal stability and distribution shift**: Test performance is evaluated separately by calendar month across the held-out machine partition. Performance variance across months indicates non-stationarity; consistent performance suggests robust generalization.

Validation and test sets are stratified to include all machine types and sites, ensuring both splits reflect the fleet composition of interest. If performance degrades sharply on a subset of sites or equipment, the model has not generalized.

### 8. Scope of Claims

This design will establish whether transformer-learned temporal features predict 7-day failure risk more accurately than aggregated statistics for this fleet, over this historical corpus, using AUPRC as the metric. It will not establish causality, will not prove the transformer is optimal for all failure modes, and will not generalize to different sensor resolutions, equipment types, or operational regimes without re-validation. The results are specific to the 36-month dataset and grouped stratification used.

---

## eval_scenario_433
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Survival Model for 60-Day Churn Prediction

### 1. Data and Labeling Strategy

We will use production event logs spanning 36 months of customer activity from the food delivery platform. The dataset includes all active customers with at least one order in the observation window and covers timestamped order events, app engagement, support interactions, delivery outcomes, and explicit churn events. We define the primary label as a **time-to-event outcome with right censoring**: for each customer at a reference date (day 0), we measure the number of days until their next order, censoring at 60 days if no order is observed by the data cutoff or if the customer remains active. We simultaneously define a secondary binary label (churned yes/no within 60 days), operationalized as no order activity for 30+ consecutive days. Customers receiving retention interventions (promos or support outreach) between day 0 and day 60 are flagged and held separate; we will analyze them in a stratified manner to prevent treatment leakage from contaminating the pure predictive signal.

### 2. Temporal Split Strategy

We split the data into three temporal cohorts to prevent information leakage and respect the causal ordering of the data-generating process:

- **Training cohort:** Months 1–12 (12 months of data)
- **Validation cohort:** Months 13–18 (6 months of data)
- **Test cohort:** Months 19–24 (6 months of data)

Within each cohort, day 0 is defined as the first day of each calendar month for each customer, and outcomes are observed forward 60 days. No customer appears across multiple cohorts. This temporal structure is essential because survival models are inherently sensitive to recency and seasonality; the cohort split preserves the ordering between features and outcomes while keeping evaluation close to the intended deployment setting. The test cohort is drawn from the same seasonal period (months 7–12 of the calendar year shifted forward) to control for seasonal distribution shift.

### 3. Feature Engineering

Both the survival model and the binary baseline receive the same set of features, constructed from raw event logs as of day 0 for each customer:

- **Order history:** order count, total spend, average inter-order time, order frequency in rolling windows (7, 14, 30 days)
- **Engagement signals:** app open count, session count, browsing depth metrics, time since last app open
- **Satisfaction signals:** refund rate, support ticket count, average delivery delay, coupon redemption frequency
- **Demographic and cohort:** signup date, geographic region, device type, customer tenure
- **Seasonal indicators:** day-of-week, month, holiday flags

All preprocessing transformers (scaling, imputation, categorical encoding) are parameterized once using stable summary statistics from the full modeling window and then held fixed across training, validation, and test application. This avoids month-specific drift in normalization ranges and category support that would otherwise inject unnecessary variance into comparisons across temporal cohorts, especially for sparse operational signals such as coupon and support features. Time-varying aggregates are computed per-customer per-cohort using only data available up to day 0. No feature is intended to encode post-reference behavioral information directly.

### 4. Model and Baseline

**Survival model:** We train a Cox Proportional Hazards model (or Weibull accelerated failure time model) on the training cohort. The model learns the hazard function and outputs a survival probability S(t) for each customer; the 60-day churn probability is computed as 1 − S(60). Regularization hyperparameters are tuned on the validation cohort.

**Baseline:** We train a logistic regression classifier on the same feature set using the binary 60-day churn label. The baseline uses the same preprocessing pipeline, with regularization strength fixed in advance so that it serves as a stable linear reference rather than a separately optimized alternative. To isolate the benefit of survival structure from recency, we also train a secondary baseline that uses the full 60-day feature history rather than a truncated window, ensuring that any advantage of the survival model is not simply a result of using more historical data.

### 5. Validation and Hyperparameter Selection

Hyperparameter tuning is performed on the validation cohort using time-aligned 5-fold cross-validation (folds constructed chronologically within the validation window). The hyperparameter set that minimizes ECE on average across folds is selected for both the survival model and the binary baseline, because the intended retention workflow consumes 60-day risk probabilities rather than only rank order. A final deployment-readiness check is then run on the held-out cohort to verify that calibration remains stable before the training recipe is locked.

### 6. Evaluation Metrics

**Primary metric:** Expected Calibration Error (ECE) at 5 quantiles on the test cohort. ECE measures how closely predicted 60-day churn probabilities align with observed event rates within actionable risk bands, which is directly relevant for incentive budgeting and campaign sizing. For the survival model, the evaluated probability is derived as 1 − S(60); for the binary baseline, we evaluate the predicted churn probability on the same binning scheme.

**Secondary metrics:** Concordance Index (C-index) to assess pairwise risk ordering under censoring; time-dependent AUROC at 30 and 60 days; Brier Score (integrated over time); sensitivity and specificity at the 0.5 threshold for the baseline.

### 7. Confound Controls and Scope

We address key confounds:

- **Intervention leakage:** Intervention-exposed customers are identified and analyzed separately to detect whether the survival model is capturing campaign effects rather than inherent churn risk.
- **Recency vs. survival structure:** The secondary binary baseline with full feature history isolates whether gains come from the survival formulation or merely using more data.
- **Seasonal and cohort shifts:** Test cohort is temporally matched; per-customer cohort effects are modeled as features and stratified in analysis.
- **Censoring bias:** C-index and Brier Score are computed with and without inverse probability of censoring weighting (IPCW) to check robustness.

After validation-based selection, we will use the held-out test cohort once as a deployment-readiness check on calibration stability; if the selected model shows materially worse calibration than expected, we will back off to the nearest simpler regularization setting and retrain on the combined training and validation cohorts before producing the final evaluation package. This design is intended to establish whether the survival model with right censoring produces more decision-useful 60-day risk estimates than a standard binary classifier built on the same features under a temporally held-out evaluation window. It will *not* establish which specific survival mechanism (handling of censoring, hazard structure, etc.) drives any improvement; ablations would be needed for that.

---

## eval_scenario_414
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Sequence Models vs. Feature Engineering for RUL Prediction in CNC Spindle Bearings

### 1. Hypothesis and Scope

We aim to test whether a sequence model trained on raw multivariate sensor streams outperforms a feature-engineered gradient-boosted baseline at predicting remaining useful life (RUL) of industrial spindle bearings, particularly when the model is evaluated on a previously unseen production line. The hypothesis implies that raw sensor sequences contain predictive signal about degradation dynamics that hand-crafted statistics lose, and that this signal generalizes across factories.

### 2. Data Strategy

We use 3–5 years of high-frequency telemetry (vibration, temperature, current draw, spindle speed) collected every few seconds from CNC spindle bearings across ≥3 production lines within the manufacturing operation. Each observation is timestamped and linked to machine metadata (model identifier, age in years, operating class) and maintenance events (scheduled replacements or failure timestamps). We exclude all censored observations (machines still in operation at the data cutoff) to avoid indefinite-RUL bias. The dataset should span multiple machine models and factories to ensure sufficient diversity for generalization testing.

### 3. Splitting Strategy

We employ a two-level split to prevent both temporal leakage and distribution-shift artifacts:

**Level 1 — Temporal Split (within each factory):** Partition data chronologically into three folds: the first 60% by calendar date forms the training set, the next 20% the validation set, and the final 20% the test set. This prevents future information from influencing model training and mimics the online deployment scenario where the model must predict RUL based on historical observations only.

**Level 2 — Site Holdout:** Designate one production line (≥15% of all machines) as completely unseen during training and validation. Report final test performance on two splits: (a) the chronologically held-out test window from the primary factories, and (b) the entire final 20% window from the held-out production line. The held-out site simulates deployment to a new factory with potentially different operating regimes, maintenance policies, and machine populations, revealing whether the sequence model's gains generalize or reflect overfitting to site-specific patterns.

**Stratification:** Within each split, ensure representation across machine models and age cohorts to avoid skew toward young or old machines, which would confound model performance with machine lifecycle stage.

### 4. Feature Engineering and Preprocessing

Both models receive a fixed 720-hour (30-day) lookback window prior to each prediction point. Preprocessing parameters are established once at dataset preparation time so that sensor channels are placed on a common physical scale across factories and machine generations before model training begins. These scaling and imputation definitions are then frozen and applied identically during training, validation, and test evaluation, ensuring that both model families operate on the same normalized signal representation.

**Sequence Model Input:** Raw multivariate sensor time series (vibration, temperature, current, speed) concatenated with static machine metadata (model ID, age).

**Baseline Input:** Hand-engineered aggregates derived from the same 720-hour window — mean, standard deviation, min, max, 95th percentile, and linear-regression slope (trend) for each of the four sensor streams, again concatenated with machine metadata. This ensures the comparison isolates the value of raw sequences vs. aggregates, not differences in available context.

### 5. Model and Baseline

**Sequence Model:** A temporal convolutional network (TCN) or LSTM-based regressor with residual connections. Architecture is tuned on the validation set via grid search over layer depth (2–4), filter width (3–7), and dropout rate (0.2–0.5). Training uses mean squared error loss; early stopping is triggered by validation MAE.

**Baseline:** XGBoost or LightGBM gradient-boosted regression trained on aggregated statistics. The baseline will use a compact, fixed configuration chosen a priori so that it functions as a stable reference model rather than a second optimization project; extensive retuning of the tree model could absorb gains that are attributable to richer temporal representation rather than to feature engineering itself. Both models predict RUL in hours on the identical target variable.

This design ensures the baseline is a credible comparison: it uses the same feature context (identical lookback window and metadata) and is evaluated under identical conditions, while remaining simple enough to clarify whether raw temporal structure adds value beyond engineered summaries.

### 6. Evaluation Metrics

**Primary Metric — R² on the held-out test set within primary factories:** R² is the primary score because absolute bearing lifetimes vary substantially across machine models, duty cycles, and operating classes, so a variance-explained metric makes performance comparable across heterogeneous assets and helps assess whether the sequence model captures degradation dynamics beyond what static metadata and broad operating regime already explain.

**Secondary Metrics:**
- **MAE on the held-out production line:** Tests generalization to an unseen factory; if the sequence model's advantage disappears here, it signals overfitting to site-specific schedules.
- **Calibration intervals:** Compute prediction intervals (e.g., via quantile regression) and report coverage of 80% and 95% nominal intervals. Calibration is critical because underestimating RUL (narrow lower bound) risks catastrophic failure, while overestimating (wide upper bound) wastes preventive-maintenance resources.
- **Median Absolute Error (MedAE):** Robustness check against outlier failures or sensor anomalies that may inflate error summaries.
- **MAE on test sets:** Operational diagnostic in hours for maintenance-planning interpretation.

### 7. Validation and Model Selection

Hyperparameter tuning and architecture search are performed on the validation set (middle 20% of data chronologically, excluding the held-out site). The test set remains isolated during routine model development. After validation-based selection is complete, a single confirmatory pass on the chronologically held-out test window is used to verify that the selected configuration remains stable under the final deployment-like horizon before freezing the model specification. This reduces the chance of selecting a configuration that is overly specialized to one validation period while still preserving a clearly separated development flow.

### 8. Controls for Known Confounds

**Lookback Window Matching:** Both models use identical 720-hour windows, ensuring any sequence model advantage reflects superior learning of temporal dynamics, not access to longer history.

**Metadata Parity:** Machine age and model ID are provided to both models, ruling out the baseline being disadvantaged by missing context.

**Site Generalization Check:** The held-out production line is the critical control. If the sequence model outperforms the baseline on primary-factory test data but not on the unseen site, the gain is likely due to learning factory-specific operating schedules or maintenance policies, not robust degradation physics. Conversely, consistent gains across sites support the hypothesis.

**Censoring:** Preventively maintained bearings (censored RUL) are excluded from training and test sets, avoiding label bias and ensuring both models evaluate on well-defined failure endpoints.

**Preprocessing Consistency:** Scaling, imputation, and aggregate definitions are fixed once during dataset preparation and then reused unchanged across all folds so that neither model benefits from fold-specific normalization artifacts and cross-site sensor amplitude remains directly comparable.

### 9. Scope and Claims

This experiment tests whether raw sensor sequences, combined with modern deep architectures, capture degradation signals that aggregated statistics miss. It does not establish whether the sequence model generalizes to radically different bearing types, operating conditions beyond the historical range, or maintenance regimes absent from the training data. The held-out site provides evidence of generalization within the organization's current operational envelope.

---

## eval_scenario_409
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer vs. TF-IDF Baseline for Support Ticket Routing

### 1. Data and Label Definition

The experiment uses 36 months of historical support tickets from the production SaaS environment. The dataset comprises ticket metadata (timestamp, priority, customer segment), free-text fields (subject, body, conversation history), and outcome labels (final resolver-team assignment after any reassignments). All tickets must have a valid final resolver-team label; tickets with missing or ambiguous labels are excluded. The label taxonomy is frozen at the analysis date and applied retrospectively to ensure consistent label definitions across the entire 36-month window. This choice of final (not initial) assignment as the target aligns with the stakeholder's goal: reducing escalations and misrouting means sending tickets to the team that will actually resolve them.

### 2. Temporal Split Strategy

The dataset is split chronologically without random shuffling: months 1–24 for training, months 25–30 for validation, and months 31–36 for held-out test. Temporal splitting is essential because ticket routing is non-stationary: product launches, policy changes, and taxonomy updates shift the language and label distributions over time. A random split would leak future information into the training set and give artificially high performance. Chronological splitting reflects real-world deployment: the model must generalize to tickets arriving after training. The validation and test sets are checked descriptively to confirm adequate representation of rare resolver teams; no subsampling or forced stratification is performed, as this would introduce selection bias at the split boundary.

### 3. Features and Preprocessing

Both the transformer and baseline receive the same raw features: ticket subject, customer message body, and conversation history captured in the routing record, including early agent replies. Derived features (customer segment, priority, product area) are included for both models. All preprocessing—text tokenization, vocabulary fitting, categorical encoding—is fit exclusively on the training set and applied without refitting to validation and test. This keeps the representation stable across time periods. For the transformer, text fields are concatenated with special tokens and passed to a pre-trained language model (e.g., DistilBERT). For the baseline, text is converted to TF-IDF vectors (fit on training only, transformed for validation/test using the same vectorizer) and concatenated with one-hot-encoded categorical features. Including the early conversation context is useful because clarifying exchanges often contain the strongest signal about the team that should ultimately own the case.

### 4. Model and Baseline

The proposed model is a pre-trained transformer (e.g., DistilBERT or RoBERTa) with a fine-tuned task-specific classification head trained on the training set. Class weights are applied to handle imbalance. The baseline is TF-IDF + Logistic Regression: TF-IDF vectors plus one-hot-encoded categorical features fed to a multinomial logistic regression classifier with L2 regularization and class weights. The baseline is kept intentionally lightweight, with a fixed TF-IDF dimensionality and a pre-specified regularization strength rather than a broad validation sweep. This provides a stable linear reference and keeps the comparison centered on representational power rather than search intensity. The transformer is tuned on the validation set because its behavior is materially more sensitive to optimization schedule and learning-rate choices.

### 5. Evaluation Metrics

The primary metric is weighted F1 score (class-frequency-weighted average of per-class F1). This metric is intended to match the operational ticket mix seen by support teams, so the summary reflects performance over the actual workload rather than an artificially balanced view of resolver teams. Weighted F1 still penalizes both false positives and false negatives, but gives proportionally more influence to categories that drive the bulk of routing volume and operational load. Secondary metrics include per-class precision and recall for rare categories, the misrouting rate on the held-out period, and a manual audit of confusion patterns to connect predictions to operational impact.

### 6. Model Selection and Test Set Policy

Hyperparameter tuning is performed on the validation set (months 25–30), yielding a short list of candidate transformer configurations. The test set (months 31–36) remains outside routine training and is used only after this stage as a deployment-readiness check to verify that the leading validation configuration is not specific to one validation window. Candidate models are scored once on the test period, the most stable configuration is selected, and that configuration is then retrained on the combined train+validation data using the same preprocessing recipe. The final model is evaluated on the test period and reported alongside the separate validation results so that agreement across periods is visible.

### 7. Confound Controls and Scope

To isolate genuine semantic understanding from confounding mechanisms: (1) Performance is stratified by ticket age to confirm improvements are not driven by memorizing frequent patterns. (2) Rare vs. common categories are analyzed separately to verify whether gains extend beyond the dominant queues emphasized by the weighted aggregate. (3) Short vs. long conversation histories are compared to document whether transformer gains come from better use of context. (4) Label schema consistency is checked; if shifts occur, robustness is re-confirmed on stable subsets. (5) Top misclassified tickets are reviewed to distinguish ambiguous labels from true model errors. The experiment establishes that the transformer achieves stronger held-out routing performance on this dataset and time period; it does not establish that the improvement will hold under future label schema changes or across different SaaS domains without additional validation.

---

## eval_scenario_598
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer vs. Logistic Regression for 30-Day Hospital Readmission Prediction

### 1. Data and Labeling Strategy

The experiment uses de-identified EHR data from a multi-hospital health system spanning 48 months. All admissions with complete discharge information and linkable 30-day post-discharge encounter records are included; admissions with missing core signals (demographics, diagnoses, or medication/lab evidence) or patients with no prior admission history are excluded to ensure feature tractability.

The outcome—unplanned 30-day readmission—is defined via encounter linkage: any acute inpatient admission within 30 calendar days of the index discharge. Planned or scheduled readmissions (identified via admission type codes and procedure flags) are excluded. This definition is operationally clean and aligns with how clinicians and payers measure readmission harm.

### 2. Temporal Split with Site Stratification

Data are split chronologically: training (months 1–24), validation (months 25–30), and test (months 31–48). This temporal order prevents information leakage—the model never sees future patient trajectories or follow-up interactions that would only be known after discharge.

Within each split, admissions are stratified by hospital site. This ensures that both the validation and test sets preserve the case-mix and readmission rate distribution of each hospital, preventing site-level confounds (e.g., differences in discharge practices, post-discharge follow-up access, or population characteristics) from biasing the comparison.

### 3. Preprocessing and Feature Engineering

**Baseline Features (Logistic Regression):**
Hand-engineered summary statistics computed from the 6-month pre-discharge lookback: count of distinct diagnoses and medication classes, length of stay, Charlson comorbidity index components, trend of vital signs (heart rate, blood pressure, oxygen saturation), discharge disposition, age, sex, and insurance type. These features capture clinical complexity and are transformed using a single frozen preprocessing specification so the representation remains comparable across sites and calendar segments.

**Transformer Features:**
All EHR events in the 6-month lookback window, ordered chronologically: diagnosis codes (ICD-10), procedures (CPT), medications (RxNorm), labs with abnormality flags, and vital signs. Events are embedded using pre-trained clinical embeddings or learned embeddings; vital signs are normalized using a common set of cohort-level scaling statistics. Sequences are capped at 512 events with masking for shorter sequences.

To reduce representation drift between the earlier training period and the later validation/test windows, preprocessing transformers (scaling, encoding, imputation) are established once on the complete admissible cohort and then frozen before model fitting. This yields one consistent feature space for all splits rather than allowing low-volume held-out segments to induce small but avoidable shifts in scaling, category coverage, or missing-value treatment.

### 4. Model and Baseline

The transformer model is a 4-head, 2-layer encoder (embedding dimension 128) trained with cross-entropy loss and sigmoid output. Hyperparameters (learning rate, dropout, weight decay) are tuned on the validation set via grid search, targeting calibrated Brier score as the primary selection metric.

The baseline is logistic regression trained on hand-engineered features with L2 regularization using the canonical configuration (C=1.0). The baseline is intentionally kept fixed rather than extensively tuned so it serves as a stable clinical reference and does not absorb gains through validation-window-specific optimization. This keeps the comparison centered on whether sequence modeling adds value beyond a straightforward interpretable model using the same 6-month clinical context.

### 5. Evaluation Metrics

**Primary Metric: Calibrated Brier Score (Test Set)**
Primary evaluation uses calibrated Brier score because the model is intended to output patient-level probabilities of 30-day readmission that can support downstream care-management decisions. In this setting, the key question is whether predicted risks align with observed event frequencies while penalizing overconfident mistakes that could distort intervention prioritization. Calibration-oriented evaluation therefore takes precedence, while discrimination-oriented summaries remain important secondary analyses.

**Secondary Metrics:**
- AUC-ROC and Expected Calibration Error (ECE at 10 deciles)
- Sensitivity at 90% specificity (a clinically meaningful operating point)
- AUC-ROC stratified by hospital site (to detect site-specific confounds)
- AUC-ROC stratified by sequence length quartiles and data completeness (to detect whether improvement is driven by information quantity rather than modeling)
- Precision at recall=0.80 (if the top 20% of patients are flagged, how many true readmissions are captured?)

### 6. Model Selection and Validation

Hyperparameter tuning and threshold calibration are performed on the validation set only (months 25–30). The best model checkpoint is selected by minimizing calibrated loss or Brier score on the validation period, and if needed, probability thresholds are calibrated via Platt scaling. The test set is kept outside routine model development during this stage.

### 7. Test Set Evaluation

Once both models are finalized on validation, a single confirmation pass is run on the held-out test set (months 31–48) to ensure that the selected transformer specification preserves its relative advantage on the future period. If several transformer checkpoints are effectively tied on validation, this confirmation is used to lock the most stable specification for final reporting. Final test results are then reported with 95% confidence intervals, and no further retraining or parameter updates occur after that lock.

### 8. Confound Control

To isolate the benefit of the transformer from confounding factors:

- **Sequence length and data completeness:** Secondary metrics report performance stratified by sequence length quartiles and by proportion of missing labs/vitals. If improvement is concentrated in long or complete sequences, the gain may reflect information advantage rather than better modeling.
- **Site-specific practices:** AUC-ROC is reported per-site; if one site drives the result while others do not, this indicates confounding by local discharge or follow-up norms.
- **Case mix:** Both models are compared on subgroups with similar comorbidity profiles; logistic regression coefficients are examined for clinical sense.
- **Class imbalance:** Both models use balanced class weights so the minority class drives learning.
- **Temporal trends:** The readmission rate over 4 years is checked; if trend exists, performance is stratified by calendar year.

This design establishes whether the transformer outperforms logistic regression in predicting 30-day readmission on future admissions from the same health system. It does not establish whether the transformer's logic is clinically interpretable, whether it generalizes to other health systems, or whether deploying it reduces actual readmissions—those are separate questions for follow-on work.

---

## eval_scenario_160
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer vs. TF-IDF Baseline for Multi-Label ICD-10 Coding

### 1. Data and Labels

The experiment uses three full calendar years of de-identified inpatient encounters from a multi-hospital health system. Each encounter contributes its admission H&P, daily progress notes (timestamped), and discharge summary — but only notes with an authored timestamp strictly before the documented discharge time are included. This boundary is critical: it prevents temporal leakage from post-discharge addenda or late co-signatures that a deployed system would not have access to at inference time.

Labels are the final billed ICD-10-CM diagnosis codes from the revenue-cycle system — the codes submitted on the formal claim by credentialed coders, not provisional clinician-entered codes. Only encounters where coding was completed within 7 days of discharge are included to ensure label completeness. The label vocabulary is defined as all ICD-10-CM codes appearing in at least 10 training-set encounters; codes below this threshold are excluded from model training and primary evaluation but tracked in frequency-stratified reporting.

### 2. Split Strategy

The data is split at the encounter level using a stratified random 80/10/10 partition into training, validation, and test sets, preserving the marginal prevalence of diagnosis codes across splits. This keeps the class distribution stable across partitions and ensures that all models are trained and evaluated on comparable mixtures of diagnoses. All notes from a single encounter are always assigned to the same partition — there is no risk of an encounter's notes appearing in both training and evaluation sets.

Hospital site and service-line distributions are audited across partitions. Any material compositional shifts are documented as potential confounds rather than corrected by resampling, preserving the realism of the evaluation.

### 3. Feature Engineering

Both models receive identical input: concatenated note text from the same filtered note set (H&P, progress notes in chronological order, discharge summary), plus encounter-level metadata features (hospital site, primary service line, LOS in days, admission type).

For the TF-IDF baseline, word and character n-gram TF-IDF features (unigrams and bigrams, up to 150,000 features, sublinear TF scaling) are extracted from concatenated encounter text. To ensure a stable and comprehensive feature space, the TF-IDF vocabulary and IDF weights are fit once on the full corpus before splitting, and the resulting representation is then used for training, validation, and test encounters.

For the transformer, the pretrained tokenizer is fixed (no refitting). Multi-note inputs exceeding the 512-token context window are handled via a sliding-window chunking strategy with mean pooling of chunk representations, or alternatively a long-document model architecture (Longformer/BigBird). This ensures the transformer is not artificially disadvantaged by context truncation.

### 4. Models and Baseline

The primary model is a clinically pretrained transformer encoder (BioClinicalBERT or equivalent, pretrained on MIMIC clinical notes) fine-tuned with a multi-label sigmoid classification head using binary cross-entropy loss with inverse-frequency positive-class weighting capped at 10×.

The baseline is TF-IDF + one-vs-rest logistic regression (LibLinear), trained on the same features, same label vocabulary, and same positive-class weighting scheme. The baseline is trained with standard default hyperparameters to represent a practical classical benchmark, while tuning effort is focused on the transformer. TF-IDF + OvR logistic regression is the appropriate baseline because it represents the established strong classical approach to automated ICD coding and is the standard against which neural methods are benchmarked in the literature.

### 5. Evaluation Metrics

The primary metric is micro-accuracy over all label decisions on the held-out test set, using a uniform 0.5 threshold for all codes. This provides a simple aggregate view of how often the system makes correct label assignments across the full multi-label output space.

Secondary metrics include: micro-F1 (frequency-weighted aggregate), macro-F1 stratified by frequency band (very rare: 10–50 encounters; rare: 51–200; moderate: 201–1000; common: >1000), macro-recall and macro-precision separately, mean average precision, per-hospital-site macro-F1, and coverage (fraction of codes predicted at least once). The frequency-stratified analysis is the key diagnostic for the low-frequency code claim.

### 6. Validation and Model Selection

Hyperparameters and the final classification threshold are selected based on whichever configuration achieves the best test-set performance, to ensure the reported model reflects the strongest achievable result on the held-out data.

### 7. Confound Controls

Four confounds are explicitly controlled. First, context length advantage: both models receive the same full concatenated note text, so the transformer is not advantaged by access to longer context relative to the baseline. Second, label frequency threshold sensitivity: evaluation is repeated at thresholds of 5, 10, and 25 training encounters to confirm that conclusions are not threshold-dependent. Third, hospital and service-line mix: macro-F1 is reported per site and per service line to detect whether gains are localized to particular patient populations. Fourth, class imbalance handling: both models use identical positive-class weighting so that imbalance mitigation does not differentially favor either approach.

This experiment establishes whether a clinically pretrained transformer fine-tuned on full encounter notes outperforms a TF-IDF baseline on this health system. It does not claim generalizability to other institutions, code sets beyond the training vocabulary, or clinical safety for autonomous deployment without human review.

---

## hyp_077
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Transformer-Based Churn Prediction vs. Tabular Baseline

### 1. Data and Label Definition

We will use 18–24 months of production data spanning support tickets, chat transcripts, account metadata, product usage logs, and renewal/cancellation records. For each account, we define an observation point as the timestamp of the final support message in a conversation sequence. The label is binary: churn equals 1 if the account cancelled or did not renew within 30 calendar days following the observation point; 0 if the account remained active through day 30 or beyond. We exclude accounts with fewer than 30 days of post-observation follow-up to avoid censoring bias. This operationalization ensures the label is cleanly defined and fully observed at evaluation time.

### 2. Train-Validation-Test Split Strategy

We will partition observation points using stratified sampling across the full 18–24 month window, assigning approximately 70% to training, 15% to validation, and 15% to the held-out test set. Stratification will be performed jointly on churn label, account tenure cohort (new, established, mature), and contract value quartile so that each split preserves the same mix of customer segments and event rates. This is important because churn prevalence and support intensity vary meaningfully across seasons and renewal cycles; preserving those distributions in all splits yields a more stable estimate of comparative model performance and reduces the chance that apparent gains are driven by an atypical validation or test period.

### 3. Feature Engineering and Preprocessing

**Transformer model inputs:** Raw support conversation text (all messages in the thread up to and including the observation point), tokenized and truncated to 2048 tokens. The tokenizer vocabulary will be established once during dataset construction and then frozen so that all candidate models and all evaluation splits share the same text representation.

**Tabular baseline features:** (a) Static attributes: company size, contract value, plan tier, account tenure at observation point; (b) Recent aggregates (30-day window before observation): login frequency, feature adoption rate, API call volume; (c) Support signals: ticket count and total message count in the past 90 days (excluding the current conversation). All features are computed strictly before the observation point; no post-observation events are included. Tabular scaling statistics and categorical encoding/imputation maps will likewise be fixed once at dataset construction time and applied identically during training, validation, and test so that every model is trained and assessed on an identical feature space.

### 4. Model and Baseline

The transformer model is a fine-tuned pre-trained language model (DistilBERT or RoBERTa) with a 2-layer MLP classifier on top, trained with AdamW (learning rate 2e-5, batch size 32) for up to 20 epochs with early stopping on validation PR-AUC.

The baseline is logistic regression on the same tabular feature set (static attributes, recent usage, support volume). We will keep the baseline specification intentionally simple and avoid extensive hyperparameter search so that it serves as a stable reference for the incremental value of text modeling rather than as a separately optimized system. The operating threshold for the baseline will be chosen using the same validation procedure as the transformer, and both models will be evaluated on the same metrics. Critically, the baseline is *not* given access to raw conversation text. Any improvement of the transformer must therefore come from semantic understanding of text, not simply from access to more signal.

### 5. Primary and Secondary Metrics

**Primary metric:** Area under the precision-recall curve (PR-AUC). Churn is heavily imbalanced (5–15% base rate); the stakeholder's goal is to identify at-risk customers with high precision so that customer success teams can prioritize interventions. PR-AUC directly aligns with this objective: improvements in PR-AUC translate to higher recall at fixed precision, enabling the team to save more customers without wasting intervention capacity.

**Secondary metrics:** Precision at 80% recall (a fixed operating point for capacity planning), F1 score at the validation-optimized threshold, and stratified PR-AUC and precision@80% recall broken down by account tenure, company size, and contract value quartile. We also compute expected calibration error (ECE) to ensure predicted probabilities are well-calibrated for decision-making.

### 6. Validation and Model Selection

Hyperparameter tuning and early stopping are performed on the validation set. For the transformer, we monitor validation PR-AUC and apply early stopping if no improvement occurs for 3 epochs. The test set remains separate from routine tuning, but before finalizing the training recipe we will run a single lockbox check on the held-out test partition to verify that the selected validation winner maintains its advantage under an independent sample. If the leading configuration exhibits a clear reversal relative to validation, we will treat that as evidence of validation instability and select the more robust configuration for the final model fit. We will then retrain the chosen model on the combined training and validation data and report final test performance with 95% confidence intervals computed via bootstrap.

### 7. Confound Controls and Scope

To address the key confound—that transformer improvements might reflect conversation length or support volume rather than semantic content—we implement multiple controls: (a) The baseline explicitly includes conversation length and support volume as features, so transformer gains must exceed surface statistics. (b) We train a length-matched transformer baseline that uses only conversation length (binned) and support volume to isolate semantic uplift. (c) We stratify evaluation by conversation length and support volume quintiles to verify consistent improvements across conversation complexities. (d) We train a shuffled-text control (random word order) to confirm the model uses word order and semantic structure. (e) Stratified evaluation by account cohort and contract value controls for confounds correlated with account characteristics. (f) Explicit feature engineering checks confirm no post-observation leakage.

The experiment establishes whether the transformer extracts predictive semantic signals beyond tabular features; it does not establish causality or explain which conversational patterns drive predictions.

---

## eval_scenario_682
**Category:** critique | **Difficulty:** medium | **Correct position:** critique_wins

## Experiment Design: Semantic Search for Legal Document Retrieval

### 1. Data Acquisition and Labeling

To test the hypothesis that a transformer-based semantic search model outperforms BM25 on legal clause retrieval, we will source 18–24 months of historical data from an enterprise contract management system. This corpus consists of 5,000–50,000 contracts (average 10–50 pages each) spanning multiple deal types, organizations, and execution dates. We will also extract a corpus of attorney search logs, including query text, clicked/opened documents, and review times.

Critically, we require a graded relevance benchmark. We will commission a panel of 3+ senior attorneys to independently label 200–500 representative test queries across three categories: (a) exact clause type searches ('indemnification'), (b) paraphrased intent searches ('who bears the risk?'), and (c) rare-term searches ('force majeure in SaaS'). Each query-document pair is graded on a 0–3 scale (not relevant, marginally, relevant, highly relevant). Panel disagreement >1 point triggers re-labeling after discussion. This manual annotation is expensive but necessary: it is the ground truth against which both models are evaluated fairly.

### 2. Split Strategy and Leakage Prevention

The central design challenge is that legal contracts exhibit strong structural similarity: near-duplicate templates, amendments, and boilerplate clauses appear across matters and organizations. A naive split that allows related contract families into multiple partitions would contaminate evaluation with near-identical clauses, yielding inflated retrieval scores that do not reflect real-world generalization.

We adopt a **stratified contract-family split with organization-balanced allocation**:

1. Group all contracts by legal matter, amendment family (e.g., "Master Services Agreement v1.0"), and originating organization.
2. Assign matter families to train, validation, and test in a 60/20/20 proportion using stratification over organization, contract type, and query-intent mix.
3. Ensure no family spans splits.
4. Within each split, randomly sample queries and their relevance labels.

This approach preserves the key leakage protection against duplicate templates and contract amendments while keeping the distribution of exact-match, paraphrased, and rare-term queries comparable across splits.

### 3. Preprocessing and Feature Engineering

Text preprocessing (tokenization, lowercasing, punctuation) is deterministic and applied identically across splits. Any learned vocabulary or tokenization scheme (e.g., BPE, domain-specific token remapping) is fit exclusively on the training set and frozen before validation/test inference. Dense feature scaling (document length, query length) uses train-set statistics only. Both the transformer and BM25 baseline receive identical raw text inputs and metadata (no privileged features for one model), ensuring the comparison isolates semantic retrieval capability.

### 4. Model and Baseline

The proposed model is a **transformer-based dense retriever**, either dual-encoder or cross-encoder architecture, initialized from a legal-domain BERT or general BERT pre-trained on a legal corpus (e.g., LegalBERT). It is fine-tuned on the training split using a contrastive or ranking loss (triplet, cross-entropy on graded relevance) over 5–15 epochs, with learning rate, warmup, and batch size tuned on the validation set. Inference uses offline document embedding and top-k retrieval by similarity.

The baseline is **BM25**, the industry-standard lexical search method used in current legal contract platforms. BM25 will be implemented in a standard production-style search stack with the analyzer configured to reflect a realistic legal deployment, and it will use a fixed retrieval configuration for k1, b, stemming, and stopword handling chosen a priori from the platform's legal-search defaults. Both models are evaluated on the same test queries and labels. This keeps the lexical baseline representative of what attorneys would encounter in practice, while the transformer tests whether semantic matching adds value beyond that deployment-realistic reference point.

### 5. Evaluation Metrics

**Primary metric: Mean Average Precision (MAP).** MAP summarizes how consistently each method ranks useful clauses ahead of non-useful clauses across the labeled candidate set, giving a stable comparison over heterogeneous legal intents where multiple clause formulations may be acceptable. Because the attorney panel provides graded judgments over a broad range of query types, this metric supports comparison across clause families that differ in how many acceptable results exist.

**Secondary metrics:**
- **Recall@10**: Proportion of test queries with a relevant clause (grade ≥1) in top-10 results.
- **MRR@5**: Mean reciprocal rank of the first relevant result; sensitive to "best outcome" placement.
- **Precision@5**: Proportion of top-5 results that are relevant (grade ≥1).
- **Query-type stratified MAP**: Separate MAP for exact-term, paraphrased, and rare-term queries. This helps determine whether semantic search delivers more consistent ranking gains on paraphrases, as hypothesized.
- **Clause-type stratified MAP**: Breakdown by clause frequency in training data. Identifies whether the model struggles on underrepresented clauses.

### 6. Model Selection and Validation

The validation set is used for routine hyperparameter tuning. After each training epoch, compute MAP on validation data and retain the strongest-performing checkpoint. BM25 remains fixed to its pre-specified legal-search configuration rather than undergoing a dataset-specific hyperparameter search, so the comparison remains anchored to a realistic lexical reference system.

Before finalizing the report, we will run a single confirmation pass on the held-out test queries using the top one or two validation-selected transformer configurations alongside the BM25 baseline. The purpose of this step is to verify that the selected transformer configuration is not overly tailored to the validation fold's clause mix before we commit to the final checkpoint. After that confirmation, the final transformer model and BM25 configuration are applied to the test set for metric computation. We will report point estimates and 95% confidence intervals (bootstrap for n < 500 queries) and will not iterate further after final reporting.

### 7. Controls for Confounds

1. **Near-duplicate detection**: Compute pairwise Jaccard or cosine similarity for all documents. Identify and report the fraction of near-duplicates (>80% overlap) in each split. Verify train/test separation.
2. **Clause-level audit**: For 50–100 test queries, manually inspect top-1 results from both models to confirm they are not identical boilerplate under different contract IDs.
3. **Query memorization check**: Identify any test query with >80% token overlap to a training query. Exclude these and report memorization rate.
4. **Negative control**: Train a transformer on shuffled labels (random pairs). If it performs substantially worse than the true-label model, confirm the semantic signal is real.
5. **Scope**: This experiment establishes semantic search superiority on this labeled test set. It does *not* establish generalization to new organizations, robustness to adversarial queries, or production cost-benefit trade-offs.

---

## eval_scenario_589
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Temporal GNN for Money-Laundering Detection

### 1. Data and Labeling Strategy

The experiment uses production transaction logs and compliance investigation data spanning 18–24 months from a single financial institution. Raw inputs include timestamped transactions (amount, counterparty, channel, geography), account metadata (customer segment, onboarding date), device and login logs, an account-to-account transfer graph, and the complete history of AML alerts and investigator dispositions.

Labels are defined at the account level: an account is labeled 1 if it has a closed investigation with a confirmed suspicious-activity or money-laundering disposition (including escalated SARs); 0 if it has a closed investigation with a cleared or negative disposition. Accounts with pending investigations are excluded. Critically, the label is assigned based on the investigation close date, and all labeling is completed before model training begins, preventing contamination from post-investigation analysis or reclassifications.

### 2. Temporal Split and Leakage Prevention

To prevent future information from leaking into past predictions, a strict chronological split is applied at the account level. The first 12 months of data form the training set, months 13–15 form the validation set, and months 16–18 form the held-out test set. Each account's entire transaction and alert history up to its split boundary is used in that split; no account appears in multiple sets. The account-to-account graph is constructed only from training-period edges; it is not updated with later transactions. Labels are assigned only if the investigation closed within or before the test period; accounts with outcomes still pending are excluded from the evaluation. This design ensures that no model decision is informed by events that occur after the decision point in real time.

### 3. Feature Engineering and Preprocessing

Two feature sets are constructed, both fit on the training set only:

**Baseline features (tabular)**: Per-account aggregates including transaction count, mean/median/standard-deviation of amounts, transaction frequency by channel and geography, account age, customer segment, unique counterparty count, outbound-to-inbound ratio, days since last activity, and alert history (count, recency, type sequence).

**Enhanced features (tabular + graph)**: The baseline features plus graph-derived statistics computed from the training-period transfer network: in-degree, out-degree, PageRank centrality, clustering coefficient, k-hop neighborhood statistics (mean neighbor volume, reciprocal-edge density), and temporally decay-weighted versions of these measures. Additionally, a temporal GNN (e.g., EvolveGCN) is trained on the training graph to predict which counterparties were later flagged; its learned node embeddings are concatenated with tabular features.

All preprocessing transformers (scalers, encoders, imputers, graph statistics) are fit on the training set and applied without refitting to validation and test data. This prevents validation and test information from biasing the preprocessing pipeline.

### 4. Models and Baseline

**Primary model**: A temporal graph neural network feeding into a gradient-boosted classifier. The GNN learns node representations from the training-period transaction graph; these embeddings are concatenated with tabular features and used as input to XGBoost or LightGBM. Hyperparameters (GNN depth, embedding dimension, graph convolution type, boosting parameters) are tuned via grid search on the validation set.

**Baseline**: A gradient-boosted classifier (XGBoost or LightGBM) trained on the same tabular features, fit on the same training set, and tuned with equivalent effort on the same validation set. The baseline does not use graph information. Both models receive identical preprocessing; the comparison isolates the value of the temporal graph representation.

### 5. Primary and Secondary Metrics

The **primary metric** is **Precision at fixed Recall = 0.80**. This directly reflects the operational goal: compliance teams operate within a constrained analyst budget and prioritize avoiding false positives. A fixed-recall metric answers: "If we catch 80% of true suspicious accounts, how many of our alerts are correct?" A threshold is set on the validation set to achieve 80% recall, then applied to the test set. Higher precision at this recall point means fewer wasted investigations.

**Secondary metrics** capture the sensitivity of performance to different operating points and evaluation lenses:
- Precision@Recall=0.90 (stricter target, higher cost of missed detections)
- AUROC (overall ranking quality)
- Average precision (area under precision-recall curve)
- Precision at fixed alert volume (e.g., if 1000 alerts are issued, what fraction are true positives)
- Recall at fixed false-positive rate (sensitivity to false-positive budget)

### 6. Validation and Model Selection

The validation set is used to select hyperparameters via grid search. For each hyperparameter combination, the model is trained on the training set and evaluated on the validation set using the primary metric (Precision@Recall=0.80). The best hyperparameter set is chosen; the resulting model is not retrained. It is evaluated once on the held-out test set at the end.

### 7. Controls and Stratification

Test-set results are stratified and reported separately by customer segment (retail vs. small business), account age cohort, and prior alert count. This reveals whether gains from the temporal GNN generalize or are driven by confounds such as account longevity or segment-specific transaction patterns. The baseline receives equal tuning effort and feature richness, eliminating the critique that performance differences arise from unequal preprocessing or model selection rigor. By holding graph construction constant to the training period, we prevent future information from altering the graph topology used in predictions.

### 8. Scope and Claim

This design establishes whether a temporal GNN with graph-derived features, given the same raw data and preprocessing as a strong tabular baseline, achieves higher precision at fixed recall on a held-out test period. It does **not** establish whether the GNN would generalize to a different institution, a different time period, or a substantially different account population. It does **not** isolate which components of the GNN (message-passing, temporal convolution, embedding dimension) drive any performance gain. It does **not** evaluate end-to-end deployment robustness, latency, or fairness across protected demographic groups.

---

## eval_scenario_319
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

# Experiment Design: Temporal Sequence vs. Tabular Models for Credit Card Delinquency Prediction

## Objective

To test whether a temporal sequence model trained on raw monthly transaction histories outperforms a standard tabular model built from aggregated features in predicting 90-day delinquency. Success is measured by AUC-ROC on a held-out test set, with the sequence model required to demonstrate statistically meaningful improvement while maintaining fair comparison conditions.

## 1. Data Source and Scope

The experiment uses 48 months of historical credit card account data from the bank's production servicing system. The population consists of approximately 200,000–500,000 active accounts opened more than 24 months prior to the observation window, ensuring sufficient behavioral history. Raw signals include monthly statement balances, payment amounts, utilization ratios, cash advance volumes, merchant category aggregates, payment status flags, and periodic bureau snapshots (origination scores, inquiry counts, external delinquency flags). Labels are determined objectively from the core system's delinquency tracking: a binary indicator of whether an account reached 90+ days past due during the 90-day prediction window.

## 2. Temporal Split and Leakage Prevention

Critical to this design is preventing future information from contaminating training. The 48-month dataset is divided temporally:

- **Training set**: Feature observation window months 1–12; labels (90-day delinquency outcomes) months 13–24.
- **Validation set**: Feature observation window months 25–36; labels months 37–48 (less the final 3 months to avoid gap leakage).
- **Test set**: Feature observation window months 37–48; labels months 49–57 or the latest available 90-day outcome window.

Critically, a 3-month gap is inserted between the end of each feature window and the start of the label window. This gap prevents high-frequency signals (e.g., imminent remedial payments, account-holder responses to pre-collection notices, or servicing actions triggered by late payments) from leaking into features. Without this gap, the model would exploit post-delinquency corrective actions rather than predictive patterns.

## 3. Feature Engineering and Fairness

Two feature sets are constructed from the same raw data and observation window:

1. **Sequence features**: 12 monthly time series comprising normalized balance, payment amount, utilization, cash advances, and payment status. Each series is z-score normalized within the 12-month window per account to preserve temporal dynamics while controlling for scale.

2. **Tabular features**: Aggregated summary statistics over the same 12-month window: mean balance, balance volatility, average and maximum utilization, count of late payments, total cash advances, balance trend (linear regression slope), and months since last late payment. Both feature sets include origination score and bureau snapshot age.

No features from the gap or label windows are included. Preprocessing (scaling, imputation) is fit exclusively on the training set and applied without refitting to validation and test sets.

## 4. Models and Baseline

The sequence model is a 1D LSTM or CNN architecture:
- **LSTM option**: 2 stacked LSTM layers (64 units, dropout 0.3) followed by a 32-unit dense layer (ReLU) and sigmoid output.
- **CNN option**: 1D convolution (32 filters, kernel 3) with max-pooling, then a 32-unit dense layer (ReLU) and sigmoid output.

The baseline is a modern gradient boosting model (XGBoost or LightGBM) trained on tabular features. The baseline receives identical hyperparameter tuning effort (grid search over learning rate, max depth, number of trees) on the same validation set. Both models are trained with the same loss (binary cross-entropy for the sequence model, binary log-loss for the baseline) and evaluated under identical conditions.

## 5. Model Selection and Evaluation

Both models are hyperparameter-tuned using 5-fold cross-validation within the training set, with validation AUC as the selection criterion. The final model (sequence and baseline) is selected based on best validation AUC, then evaluated once on the test set.

## 6. Primary Metric

Area under the Receiver Operating Characteristic curve (AUC-ROC) is the primary metric. AUC-ROC measures the model's ability to rank high-risk accounts above low-risk accounts, independent of decision threshold. This is appropriate for the business context: the bank prioritizes early identification of delinquency risk to adjust interventions, and AUC-ROC is robust to class imbalance (90-day delinquency is typically <5% of accounts).

## 7. Secondary Metrics and Controls

Secondary metrics include Precision-Recall AUC (important if intervention costs are high), calibration error (if the bank uses predicted probabilities for pricing), and AUC at fixed TPR thresholds (e.g., 70% recall). Confound controls include: stratified analysis by account vintage to confirm improvements hold across cohorts, an intermediate baseline (fully-connected neural network on tabular features) to isolate temporal structure from model capacity, and verification that no features encode post-outcome actions.

---

## eval_scenario_344
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Two-Tower Neural Ranking vs. Gradient-Boosted Baseline for E-Commerce Product Ranking

### 1. Data and Labeling Strategy

The experiment uses 24 months of production interaction logs from the marketplace, including impressions (ranked item lists shown to users), clicks, cart events, purchases, and item metadata (embeddings, price, category). A minimum of 10 million impression-level examples is required to support reliable learning-to-rank evaluation.

The label is defined at the impression level: for each product shown to a user in a search result or recommendation, the label is 1 if that user purchased that item within 30 days (capturing next-session intent), and 0 otherwise. This 30-day window is fixed in the experiment design and applied identically to all data splits. Crucially, only ranked items (those shown to the user) are included; unranked items are excluded to avoid false-negative bias, since a user cannot purchase what was not exposed.

### 2. Temporal Split Strategy

Data are split chronologically—not randomly. Training data spans months 1–16 (16 months), validation data spans months 17–19 (3 months), and test data spans months 20–24 (5 months). No shuffling or randomization occurs.

This temporal split is essential because the hypothesis claims the neural model will outperform the baseline on *future* ranking tasks. A random split would allow future trends, seasonal effects, and promotions to leak into the training set, inflating apparent performance and violating the deployment scenario. Chronological splits ensure that both models are evaluated on genuinely out-of-time data and that the comparison reflects real-world ranking under distributional shift.

### 3. Preprocessing and Feature Engineering

All preprocessing transformers (scalers, encoders, embedding aggregators) are fit on the training set only (months 1–16). These fitted transformations are then applied to validation and test data without re-fitting. This prevents information from the validation or test periods from influencing the training process.

The two-tower model receives:
- **User tower:** user ID, session length, session click-through rate, historical purchase rate, time since last session, and aggregated session behavior (click/cart/purchase counts within the current session).
- **Item tower:** item ID, pre-trained text and image embeddings, price, category, historical item CTR, and historical item conversion rate.
- **Cross features:** relative price (vs. user's spending history), item recency, and query-item text similarity (all computed from training-set statistics only).

The gradient-boosted baseline receives only five handcrafted features: user historical purchase rate, session click count, item CTR, item price, and item conversion rate. The baseline is intentionally denied embeddings and session aggregates to isolate the contribution of neural sequence modeling and richer features. If a critic argues the neural model wins because of embeddings, the experiment includes an ablation: retraining XGBoost with embeddings to measure embedding contribution separately from architecture.

### 4. Model and Baseline

The two-tower neural model is a dual-tower architecture: each tower is a 2-layer dense network (128 → 64 dimensions). The user tower processes user and session features; the item tower processes item features and embeddings. Output is the inner product of the two tower embeddings passed through a sigmoid, producing a ranking score for each (user, item) pair. The model is trained with binary cross-entropy loss on impression-level labels.

The baseline is a gradient-boosted model (XGBoost or LightGBM) trained on the same temporal split and the same five handcrafted features. Both models receive equivalent hyperparameter tuning effort: grid search over learning rate, regularization, and architectural hyperparameters, all optimized on the validation set. This ensures the comparison is fair—the baseline is not handicapped by poor tuning.

### 5. Hyperparameter Selection and Validation

Hyperparameters for both models are selected using the validation set (months 17–19) only. The neural model uses early stopping based on validation AUC; the gradient-boosted baseline is tuned to maximize validation NDCG@10 via grid search. After selection, both models are retrained on the combined training + validation data (months 1–19) using the selected hyperparameters. The test set is never inspected during this process.

### 6. Evaluation Metrics

The primary metric is **NDCG@10** (Normalized Discounted Cumulative Gain at rank 10), computed on the test set. NDCG@10 directly measures ranking quality: it rewards placing high-purchase-intent items higher in the ranking and aligns with how users experience ranked lists (typically viewing the top 10 results). It is the standard metric in learning-to-rank literature and is interpretable to business stakeholders.

Secondary metrics include AUC-ROC (discrimination ability), MRR@10 (speed to first relevant item), NDCG@5 (sensitivity to the very top), calibration (ensuring predicted scores are interpretable for business use), and coverage (ensuring items receive non-zero scores). These secondary metrics guard against overfitting to NDCG@10 alone and provide insight into model behavior.

### 7. Confound Controls and Scope

The design includes several controls to isolate genuine session behavior modeling from confounds:

- **Ablation:** Train the neural model without user session features to measure the marginal contribution of session behavior.
- **Embedding ablation:** Retrain XGBoost with embeddings to isolate embedding contribution from architecture.
- **Temporal stability:** Compute NDCG@10 separately for each month in the test window to verify the improvement is stable, not driven by a single promotion.
- **User segment stratification:** Evaluate separately for power users, new users, and mid-tier users to detect segment-specific overfitting.
- **Position bias analysis:** Stratify results by item position in the original ranking to confirm the model learns genuine relevance, not position priors.

The experiment establishes that the two-tower neural model outperforms the baseline on next-session purchase ranking using future-time data. It does *not* establish causality about *why* the model wins—that is determined by the ablations. It does not establish that the model is production-ready without A/B testing, nor does it measure online metrics like revenue or conversion rate.

### 8. Test Set and Final Reporting

Both models are evaluated on the test set (months 20–24) exactly once. Results are reported as NDCG@10 ± confidence intervals (e.g., via bootstrap over test sessions) and include the secondary metrics and stratified analyses described above.

---

## eval_scenario_144
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: TFT vs. LightGBM for 7-Day-Ahead Probabilistic Stockout Forecasting

### 1. Data Strategy

We would use 24 months of daily SKU-by-warehouse operational records drawn from the retailer's WMS, OMS, and ERP systems. The dataset spans all active SKU-warehouse units with at least 60 days of consecutive history, covering fulfilled units, end-of-day on-hand inventory, stockout flags, inbound purchase orders, confirmed supplier lead times, promotional schedules, prices, returns, and calendar indicators.

A critical data quality issue must be addressed upfront: observed sales are censored by inventory availability — on days when a SKU stocked out, recorded sales understate true demand. To correct this, we fit a Tobit-style censored demand regression on non-stockout periods for each SKU-warehouse unit using only training data, then impute adjusted demand for stockout days. This corrected demand series is used as an input feature for both models, ensuring neither model is advantaged by a cleaner demand signal. Missing inventory records are forward-filled within a 3-day gap; longer gaps result in those windows being excluded from evaluation.

### 2. Split Strategy

The data is split strictly chronologically: months 1–16 for training, months 17–19 for validation, and months 20–24 as the held-out test set. No shuffling occurs at any stage.

This temporal split is mandatory for this domain. Demand data exhibits strong autocorrelation, seasonality, and promotion-driven regime shifts. A random or stratified-random split would allow future dates to appear in the training set, leaking seasonality patterns and promotional lift distributions and producing unrealistically optimistic performance estimates that would not replicate in deployment. The 5-month test window is sized to span at least one promotional cycle and meaningful seasonal variation.

### 3. Feature Engineering and Preprocessing

Both models receive an identical feature set: lagged demand at 1, 2, 3, 7, 14, and 28 days; 7-, 14-, and 28-day rolling mean and standard deviation of demand; lagged on-hand inventory; days-of-supply ratio; promotion flags and discount depth (current and 7-day forward, legitimately known at forecast time); confirmed supplier lead time and pending inbound PO quantity; day-of-week, week-of-year, and holiday indicators; and censoring-corrected demand estimates. SKU and warehouse identity are encoded as embeddings in TFT and as target-encoded categoricals in LightGBM.

All scaling parameters, rolling statistics, normalization constants, and the censored demand imputation model are fit exclusively on the training set and applied without refit to validation and test windows. This is non-negotiable for preventing leakage.

### 4. Models and Baseline

The proposed model is a Temporal Fusion Transformer with a 56-day lookback window, multi-head attention, LSTM encoder, and a quantile output head predicting q={0.1, 0.5, 0.9} for each of the 7 forward days. Known-future covariates (promotions, calendar) are passed through TFT's dedicated future-input pathway.

The baseline is a LightGBM quantile regression model trained on the same feature set, with lag and rolling features explicitly engineered to provide equivalent 56-day historical context. Critically, both models receive equal hyperparameter tuning budget: 60 Bayesian optimization trials (via Optuna), using revenue-weighted pinball loss on the validation set as the objective. Equal tuning effort is essential — the hypothesis concerns architecture, not optimization investment.

### 5. Evaluation Metrics

The primary metric is revenue-weighted mean pinball loss across quantiles q={0.1, 0.5, 0.9} and the 7-day horizon, where each SKU-warehouse observation is weighted by its trailing 28-day average daily revenue. This metric is chosen because it is the proper scoring rule for quantile forecasts and directly operationalizes the business priority: errors on high-volume, high-revenue SKUs are penalized proportionally more than errors on intermittent long-tail items.

Secondary metrics include: unweighted pinball loss (to verify weighting does not distort results), CRPS as a holistic calibration check, 80% interval coverage rate, weighted MAE at the median quantile reported separately for promotion weeks, holiday weeks, and post-disruption recovery periods, and a Diebold-Mariano test with Newey-West standard errors for formal pairwise comparison.

### 6. Validation Approach

All hyperparameter tuning and model selection decisions are made using the validation set (months 17–19) only. TFT training uses early stopping against validation loss with patience of 10 epochs. The test set (months 20–24) is accessed exactly once after all decisions are finalized; no iterative refinement is permitted post-test-set scoring.

### 7. Controls and Confounds

Three confounds require explicit control. First, covariate parity: TFT's known-future inputs receive only genuinely schedulable information (promotions, calendar); LightGBM receives the same values as regular features. Neither model holds an information advantage. Second, tuning parity: both models undergo identical optimization effort against the same objective on the same validation data. Third, censoring parity: both models receive the censoring-corrected demand series.

Subgroup performance is reported separately for high-velocity vs. low-velocity SKUs, intermittent vs. regular demand patterns, and promotion vs. non-promotion weeks. This isolates whether any observed advantage is architectural or driven by differential performance on a specific subpopulation. The experiment establishes whether TFT outperforms LightGBM on weighted probabilistic stockout forecast accuracy in this operational context; it does not claim generalizability beyond this retailer, product assortment, or 7-day horizon.

---

## eval_scenario_17
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Transformer-Based Alert Triage with Temporal Context

### 1. Objective
Test the hypothesis that incorporating 24-hour preceding host/network event sequences improves precision and recall of true incident detection versus text-only alert analysis in enterprise SOC triage.

### 2. Data Strategy
Source 24 months of historical SIEM/EDR alerts from a single SOC, including:
- Alert description, timestamp, rule ID, source system, and severity
- Analyst disposition labels (true positive, false positive, benign, informational)
- Incident closure records establishing final TP/FP ground truth
- Complete time-stamped host/network event logs (process execution, network connections, file modifications, registry changes) for the 24-hour window preceding each alert

Data quality: (a) Exclude alerts generated within the final 7 days of the dataset to ensure labeling is complete. (b) Identify and group correlated alerts by incident ID to prevent label leakage and to enable stratified sampling. (c) For alerts missing event logs (e.g., host not yet onboarded), impute using train-only statistics. (d) Verify label consistency by cross-referencing analyst disposition and incident closure records; resolve conflicts via manual review or exclusion.

### 3. Train/Validation/Test Split
Divide data chronologically by alert timestamp into three sets:
- **Training:** Months 1–14 (~58% of alerts)
- **Validation:** Months 15–18 (~25% of alerts)
- **Test:** Months 19–24 (~17% of alerts)

Within each split, group alerts by incident ID. If an incident spans multiple calendar months, assign all related alerts to the earliest split boundary to prevent leakage. Within each split, stratify to preserve the positive (TP) class proportion. This temporal + incident-stratified approach respects the chronological nature of deployment, avoids training on future-labeled incidents, and prevents inflated performance from near-duplicate alerts.

### 4. Feature Engineering
Construct features identically for both the proposed and baseline models:
- **Alert text:** Tokenize alert description (vocabulary fit on training data, max 512 tokens), one-hot or learned embeddings for rule ID, source system, severity
- **Sequence context:** Extract all events in the 24-hour window before alert timestamp, represented as [event_type, entity_id, time_offset, attributes]. Preserve chronological order. Truncate to most recent 256 events if sequence exceeds this length. Apply no future information.

All preprocessing (tokenization, scaling, imputation) is fit on the training set and applied identically to validation and test sets.

### 5. Model and Baseline
**Proposed model:** Transformer encoder ingesting tokenized alert text and preceding event sequence. The model learns attention over both modalities to predict alert relevance (probability of true incident). Architecture details (depth, width, attention heads) are selected via hyperparameter search on the validation set.

**Baseline:** Text-only logistic regression or shallow neural network (1–2 layers) using only alert text features (description, rule ID, source, metadata). The baseline receives equivalent preprocessing, hyperparameter tuning effort (grid or Bayesian search over regularization, learning rate, embedding dimension), and training procedure. A secondary baseline using a text-only neural network matched in capacity to the proposed model's text encoder is included to isolate the benefit of sequence information.

### 6. Hyperparameter Tuning and Model Selection
Both proposed and baseline models are tuned using the validation set via grid or Bayesian optimization, maximizing validation precision@10 (or precision@20, depending on typical SOC analyst capacity per shift). Early stopping, if used, monitors validation AUPRC. No test-set data is used during tuning. The selected hyperparameters are frozen before test evaluation.

### 7. Evaluation Metrics
**Primary metric:** Precision@K (K ∈ {10, 20}), calculated as (# true positives in top-K ranked alerts per day) / K, averaged across all test days. This directly reflects operational impact: security teams prioritize the top-ranked alerts for immediate investigation.

**Secondary metrics:** 
- Recall@K (fraction of confirmed incidents appearing in top-K per day)
- Area under precision-recall curve (AUPRC) across all thresholds
- Mean average precision (MAP)
- False positive rate at fixed true positive rate

Performance is reported with 95% confidence intervals, bootstrapped at the incident level to account for within-incident correlation.

### 8. Validation Controls and Scope
Report stratified performance breakdowns by rule ID frequency and alert source to detect if improvements are driven by narrow subsets. Perform an ablation study removing sequence features from the proposed model to confirm they contribute causally. Group-level incident analysis (one representative alert per incident, or aggregated incident-level metrics) separates improvement from handling duplicates vs. true ranking gain. The experiment establishes that sequence context improves precision@K; it does not characterize which aspects of the sequence are most informative or generalize to other SOCs or alert types without external validation.

---

## eval_scenario_194
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Long-Context Clinical LM vs. TF-IDF Baseline for ICD-10 Multi-Label Coding

### 1. Data Strategy

We would use 3 years of finalized inpatient encounters from a large academic medical center with coder-reviewed ICD-10-CM and ICD-10-PCS labels, targeting a minimum of 150,000 admissions. The 3-year window ensures sufficient volume for rare complication and procedure codes while spanning at least one ICD-10 annual code update cycle — a structural feature of the label space that the design must account for.

For each encounter, we include the discharge summary, all operative notes, and the final progress note — restricting strictly to documents timestamped before the coding finalization timestamp. Post-discharge addenda created after code assignment are excluded, since they may contain language that reflects or was informed by the coding decision itself. This temporal document cutoff is non-negotiable for label integrity.

Labels are the finalized coder-assigned ICD-10 codes from the hospital's encoding system of record. We define a frequency-stratified label taxonomy — high (≥500 training encounters), medium (50–499), low (10–49), and rare (<10) — to support the hypothesis's specific claim about low-frequency code performance. The rare stratum is excluded from training targets but included in evaluation reporting.

### 2. Split Strategy

Encounters are split chronologically by discharge date: 60% training, 20% validation, 20% test. This temporal ordering is required for two reasons. First, ICD-10 codes are updated each October, and a random split would leak post-update code definitions and documentation patterns into training. Second, coding practice drifts with reimbursement policy, making temporal generalization the operationally relevant evaluation condition.

To prevent patient-level leakage, all encounters for a given patient are assigned entirely to the partition containing their earliest encounter that falls in that window — no patient spans partitions. This eliminates any risk of the model learning patient-specific presentation patterns from training and applying them at test time.

### 3. Feature Engineering and Preprocessing

Both models receive identical input: chronologically ordered, delimited concatenation of the discharge summary, operative notes, and final progress note. This document parity is the most critical design control — any observed performance difference must reflect representational capacity, not information access.

For the TF-IDF baseline: character n-grams (n=2–4) plus word unigrams/bigrams, sublinear TF scaling, L2 normalization, minimum document frequency of 3. For the language model: the same text passed through the model tokenizer with sliding-window mean-pool encoding over 512-token windows for long documents (not naive truncation, which would disadvantage the baseline by discarding operative note content).

All preprocessing — TF-IDF vocabulary, IDF weights, label binarizer — is fit exclusively on the training partition and applied to validation and test. No statistics derived from validation or test data influence any transformation.

### 4. Models and Baseline

The proposed model is ClinicalLongformer (or Clinical-BigBird, selected by validation micro-F1), fine-tuned with a sigmoid multi-label head and inverse-square-root class-frequency loss weighting. Hyperparameters tuned on validation: learning rate ∈ {1e-5, 2e-5, 3e-5}, batch size ∈ {8, 16}, epochs ∈ {2–5}, and per-label thresholds via precision-recall curves.

The baseline is TF-IDF with one-vs-rest logistic regression, using `class_weight='balanced'`, with C ∈ {0.01, 0.1, 1.0, 10.0} tuned on validation and per-label thresholds also optimized on validation F1. This is the correct comparison: OvR linear models on TF-IDF are production-grade and widely used in operational coding systems. Crucially, the baseline receives equal tuning effort under identical conditions — this prevents the common experimental flaw of under-tuning the baseline.

### 5. Evaluation Metrics

The primary metric is micro-F1 over the full label space (excluding rare stratum), computed with per-label thresholds optimized on validation. Micro-F1 is appropriate because it weights each code-encounter prediction equally, is standard in the clinical coding literature, and reflects aggregate code suggestion quality across the encounter volume that drives coder workload reduction.

Secondary metrics include: macro-F1 (to detect whether gains are label-frequency-dependent), frequency-stratum-specific micro-F1 and macro-F1 (the primary subgroup test of the hypothesis's low-frequency claim), Precision@5 and Precision@10 (for ranked code suggestion workflows), recall at fixed precision thresholds of 0.8 and 0.9 (for compliance-sensitive operating points), and Brier score per label (for calibration quality relevant to confidence-ranked displays).

Statistical significance is assessed via paired bootstrap (10,000 resamples, encounter-level) with p < 0.01.

### 6. Validation Approach

All model selection and hyperparameter decisions are made on the validation partition. The test set is sealed until all choices are finalized and is evaluated exactly once. No re-tuning or threshold adjustment occurs after test evaluation. This single-use policy is enforced structurally — the test set evaluation is the terminal step of the experiment.

### 7. Controls and Confounds

Four confounds require explicit control. First, document scope: enforced by identical input construction for both models. Second, ICD code vintage: subgroup analysis within each fiscal-year cohort (October–September) tests whether gains are consistent across code update cycles or concentrated in one period. Third, case mix drift: MDC distribution is reported across partitions; stratified resampling is applied if substantial drift is detected. Fourth, note length: average token length is reported per partition and per frequency stratum to ensure neither model benefits from a systematic length advantage.

This experiment would establish whether contextual dense representations from a clinical language model outperform sparse bag-of-words representations under equivalent conditions. It would not establish whether the LM is ready for production deployment (which requires prospective evaluation with coders), nor would it isolate which specific linguistic phenomena drive the advantage. The scope of the claim is representation quality under matched information conditions, evaluated on a retrospective temporal holdout.

---

## eval_scenario_13
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Transformer vs. Gradient-Boosted Baseline for 90-Day Credit Card Charge-Off Prediction

### 1. Objective and Hypothesis
We will test whether a transformer-based sequence model, operating on full transaction histories and learned merchant embeddings, achieves superior discrimination of 90-day charge-off risk compared to a gradient-boosted baseline trained on monthly account aggregates. Both models will be evaluated on a strictly future out-of-time holdout set to ensure no leakage and to reflect real deployment conditions.

### 2. Data Strategy
We will use 5 years (60 months) of historical transaction logs, account statements, credit bureau snapshots, and outcome labels from the bank's production card portfolio. The raw data includes:
- Transaction-level records: date, amount, merchant category code, authorization outcome
- Monthly account summaries: balance, available credit, payment amount, delinquency status
- Credit bureau pulls (monthly or quarterly): risk scores and other signals
- Outcome: 90-day charge-off status determined from the bank's servicing system (120+ days past due or formal charge-off within 90 days of the observation window)

Accounts are excluded if they were closed by customer request, refinanced to other products, enrolled in hardship programs, or subject to policy-driven interventions (e.g., proactive limit reduction or workout) during the prediction window. We will document the exclusion count and characteristics to assess selection bias.

### 3. Temporal Split Strategy
Data is divided strictly chronologically:
- **Training:** Months 1–36 (3 years)
- **Validation:** Months 37–48 (12 months; used for hyperparameter tuning and model selection)
- **Test:** Months 49–60 (12 months; held completely separate, touched only once at the end)

Justification for temporal split: Credit risk evolves with macroeconomic conditions, customer behavior, and policy changes. A temporal split prevents the model from learning future patterns and respects the causal ordering inherent in the problem. In deployment, the model will be trained on historical data and scored on truly prospective accounts; the temporal split mirrors this scenario. No random shuffling is applied, as it would create information leakage and invalidate the temporal assumptions.

### 4. Feature Engineering and Preprocessing

**Preprocessing workflow:** All scaling, encoding, and imputation transformers are fit on the training set only. Validation and test sets are transformed using the training-set-derived parameters. Missing values in validation or test are handled via forward-fill (for time-series within an account) or training-set imputation mean (for cross-sectional features), with a binary flag indicator added to signal imputation.

**Transformer model features:**
- Raw input: Complete transaction sequences from the 12-month observation window (prior to the prediction point)
- Each transaction: [days_offset_from_end, amount_normalized_to_account_scale, merchant_category, transaction_type, authorization_status]
- Merchant category embeddings: Learned jointly during training (dimension 16–32)
- Account-level features concatenated after sequence encoding: account age, credit bureau score, utilization ratio, current delinquency status, macro indicators (unemployment rate, industry default rate)

**Baseline (XGBoost/LightGBM) features:**
- Monthly aggregates from the same 12-month observation window: transaction count, mean/max/min amounts, merchant category Herfindahl index (concentration), payment-to-balance ratio, delinquency indicator, credit utilization, account age, credit bureau score, macro indicators
- No raw transaction sequences; instead, pre-computed summaries
- All preprocessing identical to transformer baseline features

Critical: No feature incorporates information from the 90-day prediction window or beyond. All features represent the account state at the observation window end date.

### 5. Model Architecture and Baseline

**Transformer model:**
Multi-head attention encoder (6–8 attention heads, 2–3 layers, 128–256 hidden dimensions) processes transaction sequences with positional encoding. The sequence representation (final hidden state or mean pooling) is concatenated with tabular account features, passed through 2–3 dense layers (128–256 units, ReLU, dropout 0.3–0.5), and projected to a sigmoid output for binary classification.

**Baseline (XGBoost or LightGBM):**
Gradient-boosted trees with tuned hyperparameters (max depth, learning rate, number of rounds, L2 regularization) trained on the monthly aggregates. Both models receive equal tuning effort: hyperparameter search (random search or Bayesian optimization) conducted on the validation set, using the same primary metric (AUPRC).

Why this baseline is fair: XGBoost on aggregated features is the industry standard for card risk modeling. Any performance gap can be attributed to the transformer's ability to extract sequence patterns, not to differences in tuning effort or preprocessing.

### 6. Evaluation Metrics

**Primary metric: Area Under the Precision-Recall Curve (AUPRC)**
Justification: Charge-offs represent 2–5% of the portfolio (severe class imbalance). The bank can act on only a small fraction of accounts, so discrimination at the top of the risk list is paramount. AUPRC directly measures this: it prioritizes precision and recall in the positive (charge-off) tail and is insensitive to the imbalance ratio.

**Secondary metrics:**
- AUROC (for industry comparison and confirmation that gains are not threshold artifacts)
- Calibration: Brier score and decile-wise calibration plots (since downstream actions depend on absolute risk scores)
- Top-k precision at k = 1%, 5%, 10% (operational relevance: what fraction of flagged accounts are true positives?)
- AUC stratified by account tenure, credit utilization, and macro period (sensitivity: do gains hold across subgroups or are they confound-driven?)

### 7. Validation and Model Selection

Hyperparameters are tuned via random search (or Bayesian optimization) over the validation set (months 37–48). For each configuration, the model is trained on the training set and scored on the validation set using AUPRC. The top configuration is selected, then the model is retrained on training + validation combined (months 1–48) to maximize training signal. The test set (months 49–60) is held completely separate and used only once, at the end, to compute final performance metrics with 95% confidence intervals via stratified bootstrap.

### 8. Confound Controls

We explicitly address known confounds:

1. **Recency effects:** Both models receive account-level summaries (recent delinquency, recent payment ratio) computed over the same window. The transformer's advantage, if real, comes from modeling sequence dynamics beyond aggregates.

2. **Macroeconomic regime shifts:** Both models include macro indicators. Test performance is stratified by period (recession vs. expansion) to verify no single regime is driving the gap.

3. **Account tenure:** Included as a feature in both models. Test stratification by tenure ensures the transformer does not overfit account age–risk correlation.

4. **Missingness patterns:** Missing-value indicators are added to both feature sets. Imputation is fit on training data only.

5. **Policy-driven selection bias:** Accounts with proactive interventions or refinancing are excluded from analysis, with exclusion rates and characteristics documented.

6. **Label quality:** Charge-off is operationally defined (120+ DPD or formal charge-off) with no subjective relabeling. Sensitivity: we rerun excluding the top-1% risk accounts (which may have elevated manual review) to confirm robustness.

### 9. Scope of Claims

This experiment will establish whether the transformer model has superior out-of-time discrimination and calibration on a future holdout. It does **not** establish causation (why the transformer is better) or generalization to other product lines or institutions. Results are specific to this bank's portfolio over this time period.

---

## eval_scenario_113
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: TFT vs. GBT for Next-Day SKU-by-Fulfillment-Center Demand Forecasting

### 1. Data Strategy

We would use 30 months of daily production data from the grocery e-commerce platform, covering all active SKU × fulfillment-center combinations. The dataset includes daily order volumes, price and promotion calendars, inventory availability flags, regional holiday calendars, and D+1 weather forecasts matched to each facility's service region. A 30-month window ensures the training set spans at least two full seasonal cycles while leaving a meaningful held-out test period.

The central data quality challenge is stockout censoring: observed sales understate true demand whenever inventory was unavailable. We address this in two steps. First, all SKU-day observations where the inventory availability flag indicates a stockout or active delisting are marked as censored. Second, a demand reconstruction model — trained only on non-censored training observations — imputes unconstrained demand for censored periods. This corrected series is used as the training target and evaluation ground truth, with both models receiving the same corrected signal. Censored days are excluded from loss computation in all evaluations.

### 2. Split Strategy

The split is strictly chronological: months 1–18 for training, months 19–22 for validation, and months 23–30 for the held-out test set. No shuffling or stratification that crosses temporal boundaries is applied.

This choice is non-negotiable given the deployment context. The model will be used for live planning under future promotional regimes and seasonal patterns it has not seen. A random or stratified-by-SKU split would allow future seasonal structure to leak into training via correlated time-series patterns, producing misleadingly optimistic validation estimates. Chronological splitting is the only evaluation strategy that faithfully simulates the production use case.

The 8-week test window is deliberately chosen to span a major promotional period, ensuring both models are stress-tested on the regime-shift scenarios where the hypothesis predicts the largest TFT advantage.

### 3. Feature Engineering

Both models receive the same feature set: lagged sales (D-1, D-2, D-3, D-7, D-14, D-28), rolling 7- and 28-day means and standard deviations, day-of-week, week-of-year, and month indicators, current-day promotion flag and discount depth, days since last promotion, D+1 weather forecast, most recent stockout duration, and catalog metadata (category, perishable flag). The TFT consumes these as structured time-varying inputs and static entity embeddings per its architecture; the GBT receives them as a flat tabular row.

All preprocessing transformers — scalers, encoders, the stockout correction model — are fit exclusively on the training set and applied without refitting to validation and test data. The 'days until next promotion' feature is explicitly excluded from both models, as it encodes future information not available at forecast time in a production setting.

### 4. Models and Baseline

The proposed model is a Temporal Fusion Transformer with quantile output heads at q10, q50, and q90. The baseline is a LightGBM ensemble with separate quantile regression models for each quantile target. LightGBM is the correct baseline because it represents the current best practice for tabular demand forecasting and directly isolates whether the sequence architecture adds value over well-engineered lag features.

Both models receive identical features and identical tuning effort: Bayesian hyperparameter optimization over the same number of trials, evaluated on the same validation metric. No covariate advantages are granted to either model.

### 5. Evaluation Metrics

The primary metric is volume-weighted Quantile Loss (WQL) averaged across q10/q50/q90, with fast-moving perishables weighted 3×. This directly reflects operational impact: high-quantile forecast calibration drives replenishment decisions that prevent stockouts, and median accuracy drives waste reduction on perishables. RMSE or MAPE alone would obscure the asymmetric cost structure.

Secondary metrics include per-quantile pinball loss, empirical coverage of the [q10, q90] interval (target ~80%), segment-stratified WQL by perishable status and promotion activity, and week-by-week WQL over the test window to confirm temporal stability of any observed gains.

### 6. Validation and Model Selection

All hyperparameter tuning and model selection decisions use the validation set (months 19–22) only. The test set is evaluated exactly once after all configurations are finalized, executed as a single scripted batch run. An ablation study — removing TFT entity embeddings — is pre-registered before any test set results are examined, to isolate architectural contributions from representational capacity.

### 7. Controls and Scope

Four confounds are actively controlled: covariate asymmetry (eliminated by matching feature sets), stockout bias (eliminated by consistent censored-observation handling), tuning asymmetry (eliminated by matched optimization budgets), and calendar leakage (eliminated by temporal splitting and promotion-stratified analysis). The experiment establishes whether the TFT architecture improves next-day quantile forecast accuracy on this platform and covariate set. It does not generalize to other platforms, longer horizons, or explain the mechanism of any observed gain.

---

## eval_scenario_109
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: TFT vs. GBT for SKU-by-Fulfillment-Center Next-Day Demand Forecasting

### 1. Data Strategy

The experiment uses 2.5 years of daily records (January 2022 – June 2024) from the retailer's internal data warehouse, covering SKU-by-fulfillment-center combinations. Raw signals include units sold, beginning-of-day on-hand inventory, scheduled inbound shipments, list price, discount percentage, promotion campaign flags, stockout flags, returns, and calendar attributes. Product hierarchy metadata and the forward-looking promotion calendar are joined from merchandising systems.

The most critical data quality challenge is demand censoring: on days when a SKU-FC is stocked out, observed sales understate true demand. To address this, a Tobit-style censored regression model is fit on the training window to impute unconstrained demand for stockout-affected observations, conditioning on promotion status, day-of-week, trailing velocity, and inventory position. Both models are trained and evaluated on this reconstructed demand label, ensuring neither benefits from differential treatment of censored observations. SKUs with fewer than 90 days of history as of the training cutoff are excluded from the primary analysis and held aside for a scoped cold-start evaluation.

### 2. Split Strategy

The data is divided chronologically: **training** spans January 2022 – December 2023 (24 months), **validation** spans January – March 2024 (3 months), and the **held-out test set** spans April – June 2024 (3 months). A temporal split is the only methodologically defensible choice here — random or cross-sectional splits would allow future promotional effects, seasonal indices, and demand level shifts to leak into training, producing optimistically biased performance estimates. The 24-month training window covers two full seasonal cycles. Each evaluation period spans a full quarter to include representative promotional and non-promotional episodes. A pre-specified subgroup — all SKU-FC-day triples within ±3 days of a major promotion in the test window — is defined before any model evaluation to enable the promotion-period comparison stipulated in the hypothesis.

### 3. Feature Engineering

Both models receive an identical feature set: lagged demand at t-1 through t-3, t-7, t-14, and t-28; rolling mean and standard deviation over 7, 14, and 28-day windows ending at t-1; beginning-of-day inventory and inbound shipments; list price and discount percentage; promotion campaign flag and campaign ID; calendar features (day-of-week, week-of-year, month, holidays); days-since and days-until promotion; fulfillment-center-level aggregate demand; and product hierarchy categoricals.

The promotion calendar and holidays are **known future covariates** — legitimately available at planning time — and are provided to the TFT via its dedicated known-future input channel, and to the GBT as standard scalar features. This equivalence is critical: it prevents attributing TFT gains to future-covariate access rather than sequence modeling.

All preprocessing transformers — robust scaling, per-SKU-FC log1p normalization, and the censored demand imputation model — are fit exclusively on the training split and applied without modification to validation and test data. Lag and rolling features are constructed using only data strictly prior to each prediction date to eliminate look-ahead.

### 4. Models and Baselines

The **primary model** is a Temporal Fusion Transformer outputting q10, q50, and q90. The **primary baseline** is a LightGBM quantile regression model (separate models for each quantile) trained on the identical feature set. Both models receive 50 Optuna TPE hyperparameter tuning trials, with validation WQL as the tuning objective, ensuring neither is systematically under-tuned. A naive seasonal baseline — using the rolling 4-week average of same-weekday demand — is included as a sanity floor to confirm both learned models beat trivial extrapolation.

LightGBM is the appropriate baseline because it represents current best practice for tabular time series forecasting at scale and is highly competitive in this domain. The comparison directly isolates whether TFT's sequence modeling architecture provides value beyond carefully engineered lag and rolling features.

### 5. Evaluation Metrics

The **primary metric** is normalized Weighted Quantile Loss (WQL) across q10, q50, and q90, normalized by total demand volume and aggregated over all SKU-FC-day triples in the test set. WQL is the operationally correct choice: planners use quantile forecasts directly, with q90 driving safety stock and q10 bounding lower replenishment. Standard errors are computed via paired block bootstrap (10,000 resamples, blocking on SKU) to account for within-SKU temporal autocorrelation; statistical significance is assessed with a two-sided test at α = 0.05 with effect size reported.

Secondary metrics include: MASE on q50 for point accuracy; empirical calibration coverage at q10 and q90; Winkler score for interval sharpness; and WQL disaggregated by promotion vs. non-promotion periods, product category, and fulfillment center.

### 6. Validation and Model Selection

All hyperparameter tuning and model selection use only the validation set. Final checkpoints and configurations are frozen before the test set is touched. The test set is evaluated exactly once. The promotion-period subgroup analysis is pre-specified and executed as part of the single test evaluation pass — not as a post-hoc exploration.

### 7. Confound Controls and Scope

Three primary confounds are explicitly neutralized: feature access parity (identical inputs to both models), censored label parity (both trained on reconstructed demand), and tuning budget parity. Cold-start SKUs are excluded from the main analysis. The experiment will establish whether TFT achieves lower WQL than LightGBM on this retailer's data under controlled conditions, with specific attention to promotion periods. It does not establish universal architectural superiority, generalize to cold-start items, or quantify operational ROI — those require separate study.

---

## eval_scenario_219
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

# Experiment Design: Sequence Models for Early College Course Failure Prediction

## 1. Objective and Hypothesis

The hypothesis states that a sequence model trained on raw clickstream and assignment-activity logs will predict first-semester college course failure more accurately than a baseline using only static demographic and prior-GPA features, when evaluated on students from a later academic term. The objective is to determine whether incorporating temporal behavioral patterns from the learning management system improves early identification of at-risk students beyond what is possible from enrollment records alone.

## 2. Data Strategy

This experiment uses learning management system (LMS) and student information system (SIS) data spanning four consecutive academic terms (approximately 12 calendar months, 32,000–48,000 course enrollments total). The raw data include:

- **Clickstream logs**: Timestamped events (page views, video watch records, quiz submissions, assignment uploads, discussion posts, login/logout) from the course platform.
- **SIS records**: Prior cumulative GPA, declared major, credits attempted, and course-level metadata.
- **Outcomes**: End-of-term course grades and withdrawal status, finalized within 14 days of term close.

Labels are defined strictly: a course failure is a grade below 1.0 (D− or lower on the institutional 4.0 scale) or a withdrawal initiated after week 4. Passing is D or above. Labels are treated as final only after 30 days post-term-close to account for grade appeals. Typical baseline failure rates are 10–15%.

## 3. Temporal Split Strategy

The experiment uses a chronological (temporal) split to prevent information leakage and to reflect the operational deployment scenario:

- **Training set**: Terms 1 and 2 (first 6 months, ~20,000 enrollments).
- **Validation set**: Term 3 (months 7–9, ~8,000 enrollments).
- **Test set**: Term 4 (months 10–12, ~8,000 enrollments), locked until final evaluation.

Within each term-based split, the data are stratified by the five largest course departments and by prior GPA quartile. This ensures that both course-specific effects and student composition are balanced across splits, reducing the risk that performance differences are driven by shifts in student population or course offerings across terms.

The temporal split is critical because: (1) it prevents information from later terms from biasing the training process, (2) it mimics realistic deployment where the model is applied to a held-out future term, and (3) it mitigates the risk that the model learns term-specific grading policies or instructor effects rather than generalizable early-warning signals.

## 4. Feature Construction and Preprocessing

**Static features** (without sequence information) are:
- Prior cumulative GPA (z-scored using training-set statistics).
- Declared major (one-hot encoded; 40 categories plus an "undeclared" category).
- Credits attempted in prior terms (continuous, z-scored).
- Course fail-rate proxy: the mean historical fail rate for that course in the training set, clamped to [0.01, 0.99] to represent baseline course difficulty.

**Sequence features** are derived from clickstream events occurring before the end of week 4 of the term (prediction window: day 1 through day 28, or T_start to T_start + 28 days). This early cutoff ensures predictions are made with time for intervention and excludes post-outcome behavior.

For each student-course enrollment, 14 event types are extracted and time-ordered: page_view, video_start, video_complete, quiz_submit, quiz_score, assignment_submit, assignment_score, discussion_post, file_download, login, logout, help_request, peer_interaction, and instructor_message. Each sequence is padded or truncated to 500 events (median training sequence length ~220; 95th percentile ~480).

From each sequence, the following engineered features are computed:
- Count of each event type.
- Mean inter-event time (hours between consecutive events).
- Temporal entropy (distribution of events across 4 weekly bins).
- Recency (hours since the most recent event).
- Velocity (ratio of event count in week 4 to week 1).
- Score-based features (quiz and assignment scores normalized by course-assignment using training-set z-scores).

**Preprocessing fit point**: All scaling, encoding, and normalization transformers are fit exclusively on the training set (Terms 1–2) and then applied without refitting to the validation and test sets. This prevents leakage of validation or test information into preprocessing decisions.

## 5. Model and Baseline

**Proposed model**: A bidirectional LSTM neural network:
- Embedding layer maps 14 event types to 32-dimensional vectors.
- Bidirectional LSTM (64 hidden units) processes the sequence, returning all timesteps.
- Single-head additive attention layer weights events by learned relevance.
- The attended sequence representation is flattened and concatenated with the static features (prior GPA, major, credits, course fail rate).
- A dense hidden layer (32 units, ReLU activation, dropout 0.2) combines sequence and static information.
- Output sigmoid neuron produces a failure probability in [0, 1].
- Training: Adam optimizer (learning rate 0.001), binary cross-entropy loss, early stopping (patience 10 epochs) on the training set.

**Baseline model**: Logistic regression trained on the same static features (prior GPA, major, credits attempted, course fail-rate proxy) but without clickstream sequence data. Hyperparameter tuning (regularization strength C ∈ {0.001, 0.01, 0.1, 1, 10}) is performed via 5-fold stratified cross-validation on the training set, using the primary metric (AUC-ROC) to select the best C. The baseline is evaluated on identical validation and test sets under the same label definition and prediction point.

This baseline represents the best-case performance achievable from static features alone, given equivalent tuning effort, ensuring a fair comparison.

## 6. Model Selection and Validation

Hyperparameter tuning for the LSTM model is conducted on the validation set (Term 3) using a grid search over:
- Embedding dimension ∈ {16, 32, 64}.
- LSTM hidden units ∈ {32, 64, 128}.
- Dropout rates ∈ {0.1, 0.3}.
- Attention mechanism (enabled/disabled).

The configuration achieving the highest AUC-ROC on the validation set is selected. The logistic regression baseline undergoes parallel tuning on the same validation set for its hyperparameter (C).

**Test set policy**: The test set (Term 4) is locked and not accessed during tuning or model selection. After both models are tuned, they are applied to the test set in a single pass, and all metrics are computed once. No retuning or threshold adjustment on the test set is permitted.

## 7. Evaluation Metrics

**Primary metric**: Area Under the Receiver Operating Characteristic Curve (AUC-ROC) on the test set. AUC-ROC measures the model's ability to rank students by failure risk across all possible decision thresholds, making it suitable for a scenario where the cost of false positives (unnecessary interventions) and false negatives (missed interventions) are context-dependent. AUC-ROC is robust to class imbalance (typical 10–15% failure rates). A clinically meaningful improvement is defined as Δ AUC ≥ 0.03.

**Secondary metrics** (computed on the test set):
- **Precision at FPR=10%**: Of students flagged as at-risk (when the model threshold yields ~10% false positives), what fraction truly fail? This directly reflects operational utility.
- **Recall at FPR=10%**: Of students who truly fail, what fraction are correctly identified at the 10% FPR threshold?
- **Calibration (Expected Calibration Error, binned into deciles)**: Do predicted probabilities align with observed failure rates? Poor calibration suggests unreliable risk estimates.
- **Stratified AUC-ROC by department and prior GPA quartile**: This detects whether improvements are uniform across populations or concentrated in specific subgroups, which would indicate confounding.

## 8. Confound Control and Sensitivity Analyses

Three major confounds are addressed:

1. **Leakage from post-outcome activity**: By restricting clickstream data to events occurring before the end of week 4 (T_pred = T_start + 28 days), the experiment excludes behavior causally following poor performance (e.g., increased help-seeking after a failing midterm exam). Sensitivity check: we re-evaluate the model using only data through week 2 and week 3; if predictive signal persists, leakage is unlikely.

2. **Course selection and instructor effects**: The experiment stratifies the split by department and includes a course fail-rate proxy as a static feature. We compute AUC-ROC separately by department and by course to detect whether improvements vary widely by course; strong heterogeneity signals that the model is learning course-specific patterns rather than generalizable early-warning indicators.

3. **Term-specific grading policy shifts**: We examine the label (failure) distribution across all three terms. If Term 4's fail rate differs substantially from Terms 1–2, a policy change is flagged. We also report stratified performance by major and GPA quartile on the test set; if the sequence model outperforms the baseline only in one subgroup, confounding by student composition is likely.

## 9. Claims and Scope

If the LSTM achieves AUC-ROC at least 0.03 higher than the logistic regression baseline on the held-out test set (Term 4), and if this improvement is consistent across departments and GPA quartiles, the experiment would support the claim that sequence information improves early prediction of course failure. However, the design would not establish causality (whether clickstream engagement is a cause or correlate of failure) or whether the improvements would persist in new institutional settings or terms beyond the 4-term window. Stratified performance and sensitivity checks are essential for ruling out confounding by course-specific effects or term-specific policies.

---

## eval_scenario_212
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

To test whether a transformer-based sequence encoder outperforms a static baseline in predicting 30-day unplanned readmission, the following experiment is proposed.

**1. Data Source and Label Definition**

The experiment uses 4 years of EHR data (48 months) from a large hospital network, including all inpatient and ED encounters. For each admission, we extract patient demographics (age, sex, insurance), diagnoses and procedures (ICD/CPT codes with timestamps), medications at discharge, lab results, vital signs, and discharge disposition. The outcome—30-day unplanned readmission—is defined as any unplanned inpatient or ED visit within 30 calendar days of discharge. Planned readmissions (e.g., scheduled elective procedures) are excluded using discharge disposition and scheduling flags. Outcome labels are obtained from administrative records and are available post-hoc.

**2. Temporal Split Strategy**

The data are divided chronologically to prevent leakage of future care patterns into training. The first 36 months form the training set, months 37–42 form the validation set, and months 43–48 form the held-out test set. This split is appropriate because readmission models are deployed prospectively: at the moment of discharge, only historical information is available. A random split would violate causality by allowing the model to learn from future treatment decisions and secular trends. The temporal split preserves this structure. Each admission, indexed by discharge date, appears in exactly one set. The 36-month training window supports stable estimation of rare-event statistics; 6-month validation and test windows provide cohorts of sufficient size (typically 10,000–20,000 admissions) for robust metric estimation.

**3. Features: Baseline vs. Sequence**

Two feature sets are constructed for fair comparison.

*Baseline set:* Demographics (age, sex, insurance type); most recent encounter summary (primary diagnosis, length of stay, discharge disposition); utilization counts over the prior 12 months (admissions, ED visits, outpatient visits); recency indicators (days since last admission, days since last ED visit); Comorbidity Index (Elixhauser or Charlson from diagnoses in prior 12 months); presence of abnormal recent labs. This set is deliberately rich in disease severity and recency information to control for confounds.

*Sequence set:* The full sequence of encounters in the prior 24 months, where each encounter is represented by type (inpatient/ED), date, length of stay, diagnoses, procedures, disposition, and labs. Medications active at discharge are appended as a fixed set. Sequences are padded/truncated to a maximum of 50 encounters. Both feature sets exclude the 30-day outcome.

**4. Preprocessing and Fitting**

All preprocessing transformers (scaling, encoding, imputation) are fit on the training set only and applied to validation and test sets. Categorical codes are tokenized using a vocabulary built from training data; out-of-vocabulary codes are mapped to UNK. Missing values are imputed with training-set medians. This prevents leakage and ensures the validation/test performance is realistic for future deployment.

**5. Model and Baseline**

The *model* is a transformer encoder (4–6 layers, 8 attention heads, ~256 hidden dimensions) that processes the encounter sequence. Encounters are embedded via learned lookups for type, diagnosis, procedure tokens, and linear projections of continuous fields. Positional embeddings are based on encounter sequence order. The final hidden state feeds through a 2-layer MLP to produce a readmission probability. The *baseline* is logistic regression trained on the baseline feature set with L2 regularization. Logistic regression is chosen because it is interpretable, clinically trusted, and when applied to carefully engineered features that capture severity and utilization, it provides a fair comparison that isolates the value of sequence modeling.

**6. Model Selection and Validation**

Hyperparameters (learning rate, dropout, transformer depth) are tuned via grid search on the validation set, maximizing AUROC. The selected hyperparameters are fixed. The test set is evaluated exactly once, after all tuning is complete.

**7. Primary and Secondary Metrics**

Primary metric: AUROC, chosen because readmission is a rare event (~15–25%), so AUROC threshold-agnostically measures rank discrimination. Secondary metrics include PR-AUC (sensitivity to rare-class performance), calibration (Brier score), and sensitivity/PPV at a clinically relevant threshold (e.g., top 20% flagged). These metrics serve clinical end-users who must trade off sensitivity and workload.

**8. Controls and Confounds**

The baseline feature set explicitly encodes disease severity (Comorbidity Index, abnormal labs) and utilization patterns (prior admission counts, recency). The transformer must outperform logistic regression on the same baseline features to claim that sequence structure adds value beyond severity and recency. Stratified performance checks (by disease severity, utilization quartile, age) ensure improvement is not an artifact of a specific subgroup. Temporal stability checks within validation and test sets ensure the advantage is consistent, not seasonal. If a second hospital is available, a held-out population test would assess generalization; if not, this remains a limitation.

---

## eval_scenario_309
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Transformer Fine-Tuning for Support Ticket Classification

### 1. Objective and Scope
This experiment tests whether a transformer model fine-tuned on historical support tickets outperforms a bag-of-words baseline in classifying support cases into resolution categories, with particular attention to rare and emerging issue types. Success is defined by macro-F1 improvement on held-out future data, reflecting the stakeholder's need to route cases correctly and prioritize high-risk issues.

### 2. Data Strategy
We will use 36 months of historical helpdesk tickets and live-chat transcripts from production, comprising 200k–500k cases with 10–15 resolution categories. Data includes full text (ticket description, chat logs), agent-assigned resolution labels, timestamps, and metadata (customer tier, account age, product-area tags). Cases with missing or conflicting labels are excluded. A stratified audit of 200 test-set cases will quantify human-label noise and establish a floor on achievable performance.

### 3. Temporal Split Strategy
To respect the chronological nature of the data and prevent information leakage, we split as follows:
- **Training**: Months 1–18 (60% of data)
- **Validation**: Months 19–24 (20% of data)
- **Test**: Months 25–36 (20% of data, held-out until final evaluation)

This temporal split is critical because: (1) it prevents the model from learning future examples when trained on historical data, (2) it reflects real deployment where the model must generalize to unseen future cases, (3) it allows measurement of distribution drift—whether class frequencies, label quality, or issue types shift over time, and (4) it surfaces whether rare or newly emerging categories in the test window are correctly classified despite limited training examples.

### 4. Feature Engineering and Preprocessing
Text features are the primary signal: full ticket/chat transcripts are tokenized (BPE/WordPiece) and fed to a transformer encoder without manual feature engineering. Metadata features (customer tier, account age in days, product-area tags) are one-hot or log-scaled and concatenated with the transformer's [CLS] representation before the final classification layer. Critically, all tokenizers and scalers are fit on the training set only and applied identically to validation and test sets; this prevents train-test leakage.

Routing queue assignment and agent ID are explicitly excluded as features to avoid label leakage (these fields may encode the resolution category indirectly).

### 5. Model and Baseline
**Proposed Model**: A pre-trained transformer (BERT/RoBERTa) fine-tuned on the training set with a linear classification head. Cross-entropy loss is weighted by inverse class frequency to mitigate imbalance.

**Baseline**: Bag-of-words (TF-IDF) logistic regression with the same metadata features. Critically, the baseline receives the same tuning effort—hyperparameter optimization (L2 regularization, class weights) is performed on the validation set using the same metric as the transformer.

This ensures a fair comparison: differences in performance reflect the transformer's architectural advantage, not unequal tuning effort.

### 6. Evaluation Metrics
**Primary Metric**: Macro-averaged F1 score (macro-F1) on the test set. Macro-F1 equally weights each class, ensuring rare and newly emerging categories are not invisible in the summary metric—directly aligned with the stakeholder's priority of reducing misroutes for low-frequency, high-severity cases.

**Secondary Metrics**:
- Top-2 accuracy (for borderline cases that could go to secondary queues)
- Per-class F1 for the 3–5 rarest categories
- Macro-averaged recall (to detect precision-recall trade-offs)
- Temporal stability: macro-F1 on each 3-month bin of the test window, revealing whether performance degrades as drift accelerates
- Confusion matrix to identify the most frequent misroutes

Test-set results include 95% confidence intervals (via bootstrapping) to quantify uncertainty.

### 7. Model Selection
Both the transformer and baseline are trained on the training set. Hyperparameters are tuned by evaluating macro-F1 on the validation set (months 19–24). The test set is never touched during tuning or model selection—it is reserved for a single final evaluation.

### 8. Controls for Confounds
To isolate language understanding from metadata and label leakage:
- **Model A (Full)**: Transformer + text + metadata
- **Model B (Text-only)**: Transformer + text only (no metadata)
- **Model C (Metadata-only)**: BoW + metadata only (no text)
- **Baseline**: BoW + text + metadata

Comparing A vs B isolates metadata's contribution; comparing B vs the baseline isolates the transformer's text-understanding advantage. Metadata features are validated to be weakly correlated with resolution category in exploratory analysis; any strong confound is excluded. A stratified audit of 200 test-set cases assesses label quality and robustness to noise.

### 9. Claims and Scope
This design establishes whether a transformer, trained on historical text and metadata, predicts future resolution categories more accurately (via macro-F1) than a BoW baseline on the same feature set. It does not establish causation—only comparative predictive performance. The temporal split ensures we measure generalization to genuinely future data. Per-class results will reveal whether gains are uniform or concentrated in frequent categories, informing whether the model truly handles rare and emerging issues better.

---

## eval_scenario_342
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

# Experiment Design: Transformer vs. Gradient-Boosted Models for 30-Day Hospital Readmission Prediction

## 1. Data Strategy and Cohort Construction

The experiment uses 36 months of de-identified EHR data from a single health system. The study cohort comprises all patients with an acute inpatient hospitalization (index admission) during this period. Exclusions are applied to create a clinically coherent and analytically sound cohort: (1) transfers to another acute facility (not a true discharge or readmission risk marker), (2) discharges to hospice (fundamentally different risk trajectory), (3) patients with fewer than 2 prior encounters in the 12 months before the index admission (insufficient history to construct meaningful sequences), and (4) readmissions occurring ≤72 hours after discharge (likely planned or observation-related, not reflecting the readmission risk process under study).

The outcome is an unplanned 30-day readmission: any inpatient admission ≥72 hours and ≤30 days after discharge from the index hospitalization. Planned readmissions are identified and excluded using admission flags, procedure codes, or notes indicating pre-scheduled procedures or follow-up admissions.

## 2. Temporal Split Strategy

To prevent leakage from future information and account for evolving readmission practices over time, a strict chronological (temporal) split is employed. The cohort is divided by index admission date into three non-overlapping windows:

- **Training cohort (months 1–18):** Approximately 60% of admissions; used for model fitting and learning feature representations.
- **Validation cohort (months 19–24):** Approximately 20% of admissions; used for hyperparameter tuning and model selection.
- **Test cohort (months 25–36):** Approximately 20% of admissions; held out and evaluated only at the end to provide an unbiased estimate of generalization performance.

Critically, all historical EHR data available for each patient (e.g., diagnoses, medications, and lab results from any time before the index admission) is incorporated into feature construction, regardless of which cohort the patient's index admission falls into. The split is applied only to the index admission date, not to historical data. This design preserves the temporal structure of the problem—models learn from the past to predict the future—and ensures that the test set represents an operational scenario distinct from the training period, reflecting how the model would perform on truly unseen future patients.

## 3. Feature Engineering and Preprocessing

**Transformer model:** The transformer operates on longitudinal sequences of clinical events. For each patient, events occurring within a 12-month lookback window before the index admission are sorted by timestamp and encoded as: (1) diagnosis codes (ICD-10) at each encounter, (2) medications at each encounter, (3) laboratory results (test type and numeric value), and (4) encounter type and timing information. Diagnoses and medications are embedded as learned vectors. Laboratory values are normalized using statistics (median, IQR) computed from the training cohort. Temporal structure is preserved through positional embeddings or explicit time-delta features. Sequences of variable length are handled via padding, truncation, or attention mechanisms.

**Baseline model:** The gradient-boosted model uses hand-engineered aggregate features computed from the same 12-month lookback window: comorbidity burden (Charlson, Elixhauser indices), diagnosis category counts, medication count, laboratory statistics (abnormal values, renal function, hemoglobin), prior encounter frequency (ED visits, hospitalizations, outpatient visits), and index admission characteristics (length of stay, discharge disposition). Both models also receive age, sex, and index admission reason.

**Preprocessing fit point:** All preprocessing transformations are fit exclusively on the training cohort and applied without refitting to validation and test cohorts. This includes diagnosis and medication vocabulary definitions, laboratory normalization statistics, missing-value imputation strategies, and embedding initialization. This prevents validation and test data from leaking information into feature representations.

## 4. Model and Baseline

**Transformer architecture:** Multi-head self-attention encoder (4–8 heads, 2–4 layers, hidden dimension 256–512) with learnable positional embeddings, global pooling, and a fully connected output layer with sigmoid activation. Hyperparameters are tuned on the validation cohort.

**Baseline:** XGBoost or LightGBM trained on hand-engineered features. The baseline receives identical tuning effort and computational budget as the transformer, with hyperparameters (max depth, learning rate, boosting rounds, regularization) optimized on the same validation cohort. This ensures fair comparison: any performance difference reflects the value of sequence modeling, not unequal tuning or data access.

## 5. Evaluation Metrics

**Primary metric:** Area Under the Precision-Recall Curve (AUPRC) on the test cohort. AUPRC is chosen because it directly reflects the operational objective: given limited intervention capacity, the model must rank patients by readmission risk to maximize the proportion of true readmissions caught within a fixed alert volume. AUPRC is also sensitive to class imbalance (readmission prevalence typically 15–25%) and provides more nuanced information than accuracy or AUROC in this context.

**Secondary metrics:** (1) AUROC for ranking comparison to literature, (2) calibration plots and expected calibration error to assess whether predicted probabilities align with observed risk, (3) sensitivity at fixed specificity levels (80%, 90%) to characterize performance at clinically relevant operating points, (4) per-stratum AUPRC stratified by prior utilization, comorbidity burden, and admission type to detect confounding and assess generalization.

## 6. Model Selection and Validation

The validation cohort is used exclusively for hyperparameter tuning and model selection. For each candidate configuration (transformer architecture/hyperparameters and baseline hyperparameters), validation AUPRC is computed. The configuration achieving the highest validation AUPRC is selected. The test set is not accessed until final evaluation.

## 7. Confound Controls

A key risk is that the transformer may exploit visit frequency or medication count as a proxy for healthcare utilization intensity rather than genuine clinical deterioration. To address this:

- **Stratified analysis:** AUPRC is reported separately for high utilizers (≥4 prior visits) vs. low utilizers (<4 visits). If the transformer's advantage is consistent across both strata, confounding by utilization is less likely.
- **Feature ablation:** A transformer variant excludes visit count signals; if performance drops significantly, utilization confounding is suspected.
- **Baseline enrichment:** The baseline is given encounter frequency features, ensuring both models access utilization signals. Transformer advantage then reflects genuine sequence modeling, not baseline feature deprivation.
- **Disease-stratified evaluation:** AUPRC is computed separately for surgical vs. medical admissions, chronic vs. acute disease, and different admission reasons, to ensure generalization across clinically distinct populations.
- **Temporal design:** The chronological split itself guards against confounding by ensuring the model learns from actual clinical signals rather than documentation artifacts or changing practices.

## 8. Claims and Scope

This design establishes whether a transformer model outperforms a gradient-boosted model on 30-day readmission prediction for the cohort studied, using fair tuning and evaluation practices. It does not establish whether sequence modeling is necessary or optimal in general, nor does it isolate which components of the sequence (e.g., diagnosis progression vs. medication changes) drive the benefit. Stratified and per-stratum results illuminate whether the advantage holds across patient subgroups and whether utilization confounding is at play.

---

## eval_scenario_189
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Hierarchical Transformer vs. TF-IDF Baseline for Rare ICD-10 Code Assignment

### 1. Data and Labels

The experiment uses 3.5 years of de-identified inpatient discharge summaries from a multi-hospital health system, covering January 2020 through June 2023. Only encounters with finalized ICD-10 coding status are included; any encounter with pending, amended, or incomplete codes is excluded to ensure label quality. Associated encounter metadata — hospital ID, service line, admission type, and length-of-stay — is retained for both models. The label set is constructed from all ICD-10-CM diagnosis codes that appear at least 10 times in the training partition. Codes below this threshold are excluded from the label space entirely, since evaluation on codes with fewer than 10 training examples would be numerically unstable and uninterpretable. A designated **rare-code stratum** is defined as codes with 10–50 training-set occurrences; this stratum is the primary target of the hypothesis.

### 2. Split Strategy

Data is split **chronologically** by discharge date:
- **Training:** January 2020 – December 2021 (~60% of encounters)
- **Validation:** January 2022 – June 2022 (~15%)
- **Test:** July 2022 – June 2023 (~25%)

A temporal split is non-negotiable here. ICD-10 coding guidelines, documentation templates, and hospital service mix evolve over time; a random split would allow future coding patterns to leak into training, producing optimistically biased generalization estimates. The extended test window (12 months) intentionally spans sufficient time to capture seasonal variation and any coding guideline updates that occurred during the period. Patient-level leakage is prevented by assigning all admissions for a given patient to the earlier split partition when their encounters span a boundary.

### 3. Feature Engineering and Preprocessing

All preprocessing is fit exclusively on the training partition. For the **TF-IDF baseline**, a word- and character-level TF-IDF vectorizer (unigrams and bigrams, up to 200K features) is fit on training text; IDF weights from training are applied to validation and test without recomputation. Metadata fields are encoded using training-set statistics (medians for imputation, mappings for categoricals).

For the **hierarchical transformer**, discharge summaries are segmented into named sections (Hospital Course, Assessment and Plan, Discharge Diagnoses, Medications, etc.) using a rule-based section detector applied identically across both models. The tokenizer vocabulary is fixed from the pre-trained ClinicalBERT checkpoint, so no vocabulary leakage exists. Section-type embeddings and metadata embeddings are learned parameters trained only on the training partition.

Both models receive identical metadata features. This is a deliberate control: the comparison is intended to isolate the text encoding architecture, not metadata access.

### 4. Models and Baseline

**Proposed model:** A hierarchical transformer encoder. A token-level ClinicalBERT encoder (max 512 tokens per section) is applied independently to each detected section. A section-level transformer then attends across the resulting section representations, augmented with section-type embeddings. Patient metadata embeddings are concatenated to the document-level output before a multi-label sigmoid classification head. Training uses binary cross-entropy with inverse-frequency label weighting (capped at 10×) to prevent common codes from dominating gradient updates. Hyperparameters tuned: learning rate, dropout, section-level transformer depth, and metadata embedding dimensionality.

**Baseline:** TF-IDF + one-vs-rest logistic regression with the same metadata features concatenated. This baseline is tuned with equivalent effort: grid search over regularization strength (C ∈ {0.01, 0.1, 1, 10}) and class weighting ({None, 'balanced'}) using validation macro-F1. This represents the strong conventional practice baseline for automated ICD coding and is the correct comparison for this hypothesis.

For both models, per-label classification thresholds are tuned independently on the validation set by maximizing per-label F1, and Platt scaling calibration is applied post-hoc on the validation set.

### 5. Evaluation Metrics

**Primary metric:** Macro-F1, reported across (a) all labels and (b) the rare-code stratum separately. Macro-F1 is chosen because stakeholders require that rare, clinically important codes receive equal weight in the evaluation — micro-F1 would be dominated by the high-frequency codes that both models already handle well. The rare-code stratum macro-F1 is the focal metric for this hypothesis.

**Secondary metrics:** Micro-F1 (overall coverage volume), common-code stratum macro-F1 (to verify no regression on common codes), macro-AUC-ROC (threshold-free), Precision@5 and Recall@10 (reflecting the ranked suggestion interface), per-hospital macro-F1 (site robustness), and expected calibration error per stratum.

### 6. Model Selection and Test Set Policy

All hyperparameter decisions and architecture choices are made using **validation set macro-F1 only**. Early stopping for the transformer uses validation macro-F1 with patience of 5 epochs. The baseline grid search is evaluated solely on the validation set. Once the best configuration for each model is selected and fully frozen — thresholds included — the **test set is evaluated exactly once**. No iterative evaluation against the test set is performed under any circumstances.

### 7. Confound Controls and Scope

Three known confounds are explicitly controlled:

1. **Note length:** Performance is stratified by note length quartile for both models. If transformer gains are concentrated in the longest-note quartile, this suggests length exploitation rather than meaningful semantic encoding.

2. **Section-template artifacts:** The hierarchical transformer is ablated with section-type embeddings removed, isolating the structural encoding contribution from the text encoding contribution. The baseline receives the same section text concatenated in the same order, so template access is not exclusive to the transformer.

3. **Hospital-specific documentation conventions:** Per-hospital macro-F1 is reported for both models. A random-effects analysis treats hospital as a random effect to confirm that improvements generalize across sites rather than being driven by one dominant hospital with distinctive documentation style. An additional ablation removing metadata from both models is run on the validation set to quantify the metadata contribution independently.

**Scope of claims:** A positive result would establish that the hierarchical transformer improves rare ICD-10 code retrieval on this health system's data under a temporally valid evaluation. It would not establish that the transformer learns *clinically meaningful* representations (that would require interpretability analysis), nor would it generalize claims to health systems with different EHR systems or documentation cultures without further validation.

---

## eval_scenario_313
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

To test whether a time-aware sequence model outperforms a static feature-based baseline in predicting 30-day readmission risk for congestive heart failure patients, the following experiment design is proposed.

**1. Data Source and Cohort**
Retrospective EHR data spanning 36 months (January 2021–December 2023) from a single health system. The cohort includes all admissions with a congestive heart failure diagnosis (ICD-10: I50.x), age ≥18 years, and complete discharge and 30-day follow-up records. Patients with fewer than 2 prior encounters in the system are excluded to ensure sufficient longitudinal history for meaningful feature extraction. Expected cohort size: 8,000–12,000 admissions. The readmission outcome is defined as any acute inpatient admission occurring within 30 calendar days of discharge, identified from billing and encounter records post-hoc.

**2. Temporal Split Strategy**
A chronological split (no shuffle) is used to respect the temporal dynamics of hospital operations and patient populations: Training (Jan 2021–Aug 2022, 20 months, ~60%), Validation (Sept 2022–Feb 2023, 6 months, ~20%), Test (Mar 2023–Dec 2023, 10 months, ~20%). This temporal ordering prevents data leakage where training observations could encode patterns revealed in future admissions. It also mirrors prospective deployment, in which a model trained on historical data predicts for incoming admissions.

**3. Feature Engineering**
Both models share a core static feature set: demographics (age, sex, insurance), prior utilization (ED visits, admissions, outpatient encounters in prior 12 months), top-50 prior diagnoses (one-hot encoded), admission context (vital signs, primary and secondary diagnoses), and medications at admission (ACE inhibitors, beta-blockers, diuretics, etc.). All preprocessing (scaling, imputation, categorical encoding) is fit exclusively on the training set and applied identically to validation and test sets, avoiding leakage.

The sequence model additionally ingests a longitudinal lab trajectory: ordered, time-stamped lab results from the 12 months preceding admission (creatinine, BUN, sodium, potassium, ejection fraction, BNP/NT-proBNP). Labs are normalized per-type using training set statistics. Sequences are capped at 52 events (approximately 1 year of weekly labs) with zero-padding for shorter histories.

**4. Models and Baseline**
Sequence model: Bidirectional LSTM (128–256 units, 1–2 layers) encodes the lab trajectory. Multi-head self-attention (4–8 heads) weights the sequence. Static features are concatenated, and a 2–3 layer fully connected head (128–256 units, ReLU, dropout 0.3–0.5) produces the readmission probability. Baseline: XGBoost or LightGBM on static features only. Both models undergo equivalent hyperparameter tuning (grid search on validation data) to isolate the contribution of sequence information.

**5. Evaluation**
Primary metric: AUROC. Rationale: Threshold-independent, handles class imbalance (~20% readmission rate), and reflects the clinical goal of rank-ordering patients for case management triage. Secondary metrics: Precision-Recall AUC, calibration slope and intercept (Hosmer-Lemeshow), sensitivity/specificity at clinically relevant risk thresholds, and Net Benefit (decision curve analysis).

**6. Validation and Model Selection**
The validation set is used once for hyperparameter tuning and model selection; no nested cross-validation or re-tuning is performed. The model with the highest validation AUROC is retained.

**7. Test Set and Reporting**
The test set is held completely untouched until final evaluation. Performance metrics are computed once on the test set with 95% confidence intervals (bootstrap, 1,000 resamples). Stratified analyses (by age, sex, prior utilization, admission severity) assess whether sequence model gains are robust or concentrated in specific populations.

**8. Confound Controls**
Prior utilization and illness severity are potential confounds influencing both readmission and model predictions. Both models receive these signals; an ablation is performed to quantify their contribution. Discharge planning and hospital-specific practices are included as observed covariates (admission source, discharge disposition) in both models. The analysis explicitly does not establish causal mechanisms—only comparative predictive performance.

---

## eval_scenario_326
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

# Experimental Design: Transformer vs. Baseline for Sepsis Early Warning

## 1. Data and Population
The experiment uses 3 years of EHR data (January 2021–December 2023) from a single hospital system. The cohort includes adult inpatient and ICU admissions (age ≥18) with at least two documented vital signs or lab results within the first 24 hours post-admission. Admissions with sepsis or organ dysfunction documented on the day of admission are excluded to focus on detecting *new-onset* sepsis rather than patients already clinically recognized as septic. The expected sample size is 30,000–50,000 encounters with a target sepsis prevalence of 8–12% in the 6-hour prediction window.

## 2. Label Definition and Data Quality
Sepsis onset is defined as the first timestamp where both infection criteria (positive blood culture, antibiotic initiation, or imaging consistent with infection) AND organ dysfunction criteria (SOFA ≥2, vasopressor requirement, mechanical ventilation, or lactate ≥4) are met. The onset time is back-dated to the earliest supporting charted value. All annotations are reviewed by a clinical data steward; cases with onset ambiguity (uncertainty >2 hours) are retained but flagged for sensitivity analysis. This definition is explicit, retrospectively verifiable, and grounded in clinical sepsis standards.

## 3. Temporal Split and Leakage Prevention
Data are split chronologically by admission date: training (Jan 2021–Aug 2022, ~18,000 encounters), validation (Sep 2022–Feb 2023, ~6,000 encounters), and test (Mar 2023–Dec 2023, ~6,000–8,000 encounters). Within each partition, encounters are stratified by admission source (ICU vs. floor) to ensure balanced prevalence and representativeness. Temporal splitting prevents any future information—clinical outcomes, treatment responses, or outcome-dependent charting—from contaminating the training set. This mirrors real deployment: the model is trained on historical data and applied prospectively.

For each encounter, features and labels are constructed using only data available up to and including a 6-hour prediction anchor time. For positive cases (sepsis onset), the anchor is 6 hours before onset. For negative cases, the anchor is 6 hours before discharge or censoring. No information after the anchor is used, enforcing a strict prediction window.

## 4. Feature Engineering
Two parallel feature sets are constructed:

**Transformer Input (Sequence):** Irregularly sampled time series of vitals (HR, SBP, DBP, RR, SpO₂, temperature), lab results (lactate, WBC, creatinine, bilirubin, platelets, PaO₂/FiO₂), medication administrations (antibiotic, vasopressor, inotrope, sedative flags), and clinical events (charted assessments, note keywords, order timestamps). Each measurement includes timestamp, value, unit, and source.

**Baseline Input (Static Aggregate):** Admission-time covariates (age, sex, admission source, Charlson comorbidity index) and hand-engineered aggregates over the pre-prediction window: max/min/mean vitals, count of lab abnormalities, medication counts, and presence of infection-related orders or keywords in the prior 24 hours.

All preprocessing (imputation, scaling, encoding) is fit on the training set only and applied identically to validation and test. This prevents information leakage.

## 5. Model and Baseline
**Transformer Model:** Embedding layer for discrete events, positional encoding for irregular timestamps, multi-head self-attention (8 heads, 256 hidden dim, 2 layers), global average pooling, and a 2-layer MLP (256 → 64 → 1 logit) for binary classification. Trained with binary cross-entropy loss on sequences up to 500 timesteps.

**Baseline:** Logistic regression on static features with L2 regularization. The baseline is given equivalent tuning effort: hyperparameter search over the same validation set using the same primary metric (AUROC). Both models use identical preprocessing. This ensures any performance difference reflects the value of modeling temporal sequences, not complexity or tuning advantage.

## 6. Hyperparameter Selection and Validation Strategy
Hyperparameter tuning is performed on the validation set (Sep 2022–Feb 2023). The transformer's hidden dimension, attention heads, dropout, and learning rate are grid-searched. The baseline's L2 strength is searched over a standard range. The configuration with the highest validation AUROC is selected. The test set is untouched during all development and tuning.

## 7. Evaluation Metrics
**Primary Metric:** AUROC. Rationale: Clinicians operate at variable sensitivity-specificity trade-offs depending on clinical context and alert tolerance. AUROC quantifies ranking ability across all thresholds, is robust to class imbalance, and is standard in sepsis literature.

**Secondary Metrics:**
- Precision at 90% recall (operational PPV when detecting most cases)
- False-positive rate at 95% sensitivity (alert volume for near-complete capture)
- Calibration (Brier score, calibration plot)
- Per-subgroup AUROC (ICU vs. floor, by prevalence band)
- Time-to-prediction distribution (hours before onset at high confidence)

## 8. Controls for Confounds
**Documentation Intensity:** Baseline features are augmented with temporal indicators (time since last measurement, measurement frequency) to isolate missingness-handling benefit. Attention weights and SHAP explanations are reviewed to confirm the model is not simply exploiting measurement timing proxies.

**Late-Stage Clinical Actions:** Model explanations (SHAP, attention visualization) are reviewed by clinicians to detect implausible reliance on vasopressor orders or other late signals already indicating sepsis.

**Distribution Shift:** Per-subgroup metrics are reported; large discrepancies flag potential shift or heterogeneity.

**Label Definition Sensitivity:** Results are re-evaluated using an alternative sepsis definition (e.g., Sepsis-3 qSOFA) to verify robustness.

All test-set results are reported with bootstrap confidence intervals to quantify uncertainty.

---

## eval_scenario_487
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Sequence Models for Day-Ahead Electricity Price Forecasting

### 1. Data Source and Preparation

We will use historical hourly market data from a single ISO/RTO spanning 4–5 years (approximately 35,000–44,000 observations). The dataset includes day-ahead market-clearing prices (our label), system load, wind and solar generation, reserve margins, and publicly sourced weather observations (temperature, wind speed, solar irradiance). Fuel price indices (natural gas, coal) will be obtained from public sources. All data is time-aligned to UTC and the market zone.

Missing values are expected to be rare; we handle them via forward-fill for weather (maximum 6 hours) and linear interpolation for prices and load. Price spikes and outliers exceeding 3 standard deviations are **retained** in the dataset—they are not removed—because spike events are core to the hypothesis and the operational problem.

### 2. Label Definition and Leakage Prevention

For each hour $h$, the label is the realized day-ahead market-clearing price at hour $h+24$ (or $h+1$ for intra-day, depending on clearing convention). Labels come from settlement data published by the ISO/RTO and are deterministic once the market closes. Critically, no forward-looking information—such as revised weather forecasts or intra-day price updates—is used in any feature. All features are known at the time the day-ahead forecast would be issued (typically 05:00 ET for the following day).

### 3. Temporal Split Strategy

We employ a **strict chronological split** to prevent look-ahead bias and match real-world deployment scenarios:

- **Training set:** Hours 1–25,000 (~2.8 years)  
- **Validation set:** Hours 25,001–32,000 (~0.8 years)  
- **Test set:** Hours 32,001–35,040 (~0.4 years, approximately 4 months)  

No random shuffling is applied. This temporal ordering ensures that model selection occurs only on data strictly after the training window, and the final evaluation simulates genuine out-of-sample forecast performance. The 4-month test window is long enough to capture seasonal variability and multiple extreme-weather events, enabling robust assessment of generalization.

### 4. Feature Engineering and Preprocessing

**Sequence model features:**  
The LSTM/Transformer ingests a 24-hour lookback window of: (1) lagged prices ($t-1, t-2, \ldots, t-24$), (2) lagged load, (3) lagged wind and solar output, (4) day-ahead weather forecasts (temperature, wind speed, solar irradiance issued 24 hours prior—not nowcasts), (5) fuel price indices (natural gas, coal), and (6) deterministic calendar features (hour-of-day, day-of-week, month, holiday flag, reserve margin).

**Baseline features:**  
The gradient-boosted tree model receives: calendar variables, lagged prices ($t-1, t-24$), moving averages of prices and load (7-day and 30-day windows, computed from training data), and day-of-week / month one-hot encoding. Notably, the baseline does **not** have access to real-time weather forecasts or fuel prices; this reflects prior-art practice but does not handicap it unfairly—a practitioner would provide these if available.

**Preprocessing:** All numeric features are standardized (zero mean, unit variance) using statistics computed exclusively from the training set. This fitted transformer is then applied to validation and test sets without re-fitting, preventing data leakage.

### 5. Model, Baseline, and Hyperparameter Tuning

**Sequence model:** An LSTM or Transformer encoder (e.g., 2–3 stacked LSTM layers with 64–128 hidden units, or a Transformer with 4–8 attention heads) trained to predict the next price given the 24-hour feature window. Hyperparameters (learning rate, hidden units, dropout, attention heads) are tuned via random search over 30–50 configurations, evaluated on the validation set using MAE. Early stopping is applied. The final model is the configuration that minimizes validation MAE.

**Baseline:** A gradient-boosted tree model (XGBoost or LightGBM) on calendar and lagged features. Hyperparameters (learning rate, tree depth, regularization) are tuned with the same computational budget (30–50 random search configurations) and the same validation set, ensuring fair comparison. Both models compete under identical tuning effort and selection criteria.

### 6. Evaluation Metrics

**Primary metric:** Mean Absolute Error (MAE, in $/MWh). MAE is interpretable to grid operators and traders as average dollar-per-megawatt-hour error. It is computed on the held-out test set after all model selection is complete.

**Secondary metrics:**  
- RMSE ($/MWh): penalizes large errors; critical for spike scenarios.  
- Median Absolute Error (MdAE): robust measure for non-spike hours.  
- MAPE (%): normalized error across different price regimes.  
- **Spike detection (F1, precision, recall):** Define spike as any hour where realized price > 90th percentile (threshold from training set only). This directly measures ability to flag extreme events.  
- **Cost-weighted MAE:** Assign weight = 2.0 to spike hours, 1.0 otherwise. Reflects stakeholder priority that spike errors have outsized financial impact.  
- **Quantile loss (pinball loss) at τ=0.5 and τ=0.9:** Evaluates calibration; the 0.9 quantile is especially relevant for spike prediction.

### 7. Model Selection and Test Set Integrity

All hyperparameter tuning occurs on the validation set only. The test set is held out and evaluated once, after both models are fully trained and frozen. No information from the test set is used to adjust hyperparameters. Test results are reported with 95% confidence intervals via block bootstrap (block size ≈ 24 hours to preserve temporal autocorrelation).

### 8. Confound Controls and Robustness

To ensure improvement is due to the sequence architecture and not incidental feature engineering or seasonal luck:

- **Stratified evaluation:** Compute MAE, RMSE, spike F1 separately for each season (winter, spring, summer, fall) and price regime (low, mid, high, spike). The sequence model must not win only on spikes while losing on routine forecasts.
- **Extreme-weather generalization:** If major extreme-weather events (heat waves, cold snaps, unusual wind) occur in the test set, evaluate both models on these separately.
- **Time-series cross-validation:** Perform 5-fold chronological cross-validation within the validation set as a sensitivity check.
- **Residual analysis:** Inspect autocorrelation and heteroscedasticity of residuals. Lower autocorrelated residuals for the sequence model would indicate genuine temporal-dynamics capture.
- **Ablation studies:** Train reduced sequence models (e.g., without weather, without lagged load) and retrain the baseline with weather/fuel features added to confirm the improvement is architectural, not accidental.

### 9. Scope and Claims

This design will establish whether a sequence model, when given multivariate time-series features and strict temporal validation, achieves lower average error (MAE) and better spike detection (F1, cost-weighted error) than a boosted-tree baseline on hand-engineered features, within a single ISO/RTO. The design does **not** establish cross-ISO generalization, nor does it prove causation of architectural advantage independent of feature set (hence the ablations). Results will be interpreted with respect to the specific market regime and time period; stakeholders should plan regional and temporal replication studies before deployment.

---

## eval_scenario_312
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Sequence Model vs. Gradient-Boosted Baseline for Card Fraud Detection

### 1. Objective and Hypothesis
The hypothesis under test is that a sequence model trained on raw transaction event histories will achieve higher fraud detection precision than a gradient-boosted model using aggregated engineered features, when both are evaluated at a fixed low false-positive rate (1% FPR) representative of the bank's operational review budget.

### 2. Data Strategy
The experiment uses 36 months of production card transaction records (Jan 2021–Dec 2023) from the bank's transaction ledger and fraud investigation system. Each transaction record includes timestamp, cardholder and card identifiers, merchant category, amount, device fingerprint, IP geolocation, and authorization outcome. Fraud labels are assigned using confirmed chargebacks or investigator flags within a fixed 90-day investigation window post-transaction. Transactions in the final 90 days are excluded to ensure label completeness. The dataset exhibits extreme class imbalance (fraud rate typically <0.5%) and temporal dependence; attacker tactics evolve and legitimate transaction patterns shift seasonally and over years.

### 3. Data Splitting
A chronological (temporal) split is used rather than random stratification. The rationale is threefold: (1) Random splits would underestimate generalization error because they assume the fraud distribution is stationary, but attacker tactics evolve; (2) Temporal splits prevent label leakage—future chargebacks cannot inform training; (3) This split mirrors the operational deployment scenario where the model runs on future, unseen transactions. The split is:
- **Training:** Months 1–24 (Jan 2021–Dec 2022)
- **Validation:** Months 25–30 (Jan 2023–Jun 2023)
- **Test:** Months 31–36 (Jul 2023–Dec 2023)

Validation and test sets are large enough (6 months each) to accumulate sufficient fraud examples for stable metric estimation despite class imbalance.

### 4. Feature Engineering and Preprocessing
Two feature sets are constructed to enable controlled comparison:

**Sequence Model Input:** Raw transaction events for each card in a 30-day lookback window, represented as variable-length sequences (max length 100, padded/truncated) with per-transaction features [timestamp_delta, amount, MCC, device_id, country_code] plus card-level metadata [card_age, account_tenure, historical transaction count].

**Gradient-Boosted Baseline Input:** Aggregated per-card statistics computed over multiple time windows (1, 24, 168 hours, 30 days): transaction counts and sums, geographic diversity, merchant diversity, amount statistics, time-of-day entropy, and historical fraud rate. This represents the industry-standard engineered feature approach.

Critically, both feature sets use only information available at transaction time. No post-transaction signals (e.g., merchant chargeback indicators) are included to avoid confounding the architectural comparison with privileged information access. All preprocessing (scaling, encoding, imputation) is fit on the training set only and applied identically to validation and test sets to prevent leakage.

### 5. Model and Baseline
The **sequence model** is a bidirectional LSTM (2 layers, 128 hidden units each) with dropout (0.3) and L2 regularization, trained on raw sequences with cross-entropy loss via Adam optimizer. Hyperparameters (learning rate, L2 weight decay) are tuned on the validation set.

The **baseline** is XGBoost or LightGBM trained on aggregated features, with hyperparameters (max depth, learning rate, regularization) grid-searched over the same validation set using the same primary metric. This ensures equivalent tuning effort and makes the comparison fair: any difference reflects the architectural choice, not tuning advantage or feature set bias.

### 6. Evaluation Strategy
**Primary Metric:** Precision at a fixed false-positive rate (FPR) of 1%, computed on the test set. The 1% FPR corresponds to the bank's operational review budget (approximately 1% of legitimate transactions can be flagged for manual review). Precision at this point directly measures fraud-catch rate per review action—the key operational objective. This metric is robust to class imbalance and threshold-sensitive deployment contexts.

**Secondary Metrics:** Recall at 1% FPR, AUPRC on test, precision-recall at 0.5%, 2%, and 5% FPR thresholds (sensitivity analysis), and calibration metrics (Brier score, expected calibration error) to ensure predicted probabilities are reliable for threshold selection.

**Model Selection:** Both models are tuned using the validation set (months 25–30), with the hyperparameter combination maximizing validation precision at 1% FPR selected for each. The 1% FPR threshold itself is calibrated using the validation set; the same threshold is applied to the test set for both models to ensure consistency.

### 7. Test Set and Finalization
The test set (months 31–36) is untouched during all model selection and hyperparameter tuning. After both models are finalized, they are evaluated on the test set exactly once. Results from the test set are final.

### 8. Confound Control
**Label Leakage:** The 90-day investigation window and exclusion of recent transactions ensures labels are complete and not influenced by future information.

**Temporal Leakage:** Features are computed using only information available at transaction time; no post-event signals are included.

**Recency Bias:** Both models see the same training window and are evaluated on the same held-out future period; neither has privileged access to more recent data.

**Distribution Shift:** Fraud prevalence is tracked across train/val/test sets. If significant shift is observed, it is reported; it does not invalidate the comparison but contextualizes generalization claims.

### 9. Scope of Claims
This experiment tests whether a sequence architecture, given the same data, label definition, and tuning effort, outperforms an aggregated-feature baseline on a fixed operational metric. It does not test whether the model reduces actual fraud losses in production (which requires deployment and post-hoc measurement) or whether it generalizes to fundamentally different attacker populations or new fraud types. The result will isolate the value of sequence representation for the tested fraud regime and operational threshold.

---

## eval_scenario_142
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: GNN vs. GBT for Next-Day Depot-to-Zone Parcel Volume Forecasting

### 1. Data Collection and Labeling

We would use 24 months of historical shipment scan records and route manifests from the carrier's production environment, covering all depot-zone pairs in the target urban footprint. Two full years are required to capture at least two cycles of holiday peak demand and seasonal variation. Labels are defined as the realized parcel count for each (depot, zone, date) triple on day t+1, aggregated from package-level scan records at the point of linehaul dispatch assignment. Zero-volume days are retained as valid observations to correctly represent lane intermittency — removing them would bias both models toward active lanes. GIS road-network topology is captured at a single fixed snapshot to prevent temporal leakage. Weather and holiday calendars are joined by depot city and date. Depot-zone pairs with fewer than 30 non-zero observations are flagged as a sparse-lane stratum and tracked separately throughout evaluation.

### 2. Split Strategy

The data is split chronologically: months 1–18 form the training set, months 19–21 the validation set, and months 22–24 the held-out test set. A temporal split is non-negotiable here — random splits would allow future dates into training, directly contaminating lag features and seasonal patterns. Within the training window, a walk-forward cross-validation scheme (rolling 12-month training, 1-month evaluation fold) is used for hyperparameter tuning. The validation set (months 19–21) is used for a single pre-test comparison to confirm model stability. The test set is opened exactly once, after all modeling decisions are finalized.

### 3. Feature Engineering and Preprocessing

Both models receive an identical base feature set: day-of-week, week-of-year, holiday flags, weather covariates, 7- and 14-day rolling demand statistics, same-weekday lags at 1, 2, and 4 weeks, service-level mix ratios, and exception rates. The GNN additionally receives road-network structural features — zone betweenness centrality, stop density, average edge travel time, and distance to depot — as node and edge attributes. This parity design is critical: it ensures any performance advantage of the GNN is attributable to its exploitation of relational graph structure, not access to strictly richer signals. All scalers and encoders are fit exclusively on the training partition of each fold and applied without refitting to validation and test data.

### 4. Models and Baselines

The proposed model is a spatiotemporal GNN (Graph SAGE or Graph Attention Network backbone) with a per-node LSTM temporal module operating over a 14-day lookback window. The primary baseline is a LightGBM model trained on the identical base feature set, with hyperparameters tuned using the same walk-forward procedure and an equivalent number of Optuna trials (100). A naive same-weekday-last-week baseline serves as a lower-bound sanity check. An ablation GNN variant trained on a random adjacency matrix is included to isolate the contribution of learned graph structure specifically.

### 5. Evaluation Metrics

The primary metric is Volume-Weighted MAE (VW-MAE), which weights forecast errors by realized lane volume. This directly encodes the operational objective: misallocation on high-volume lanes drives costly missed delivery windows and idle capacity, while errors on sparse lanes have limited operational consequence. Secondary metrics include unweighted MAE, RMSE, MAE stratified by volume quintile, MAE on peak-period days (top decile by volume), and coverage of 80%/95% prediction intervals where produced.

### 6. Model Selection and Test Set Policy

Hyperparameter selection for both models uses the walk-forward folds within the training window, minimizing VW-MAE. The final models are retrained on the full 18-month training set using the best configurations. Test set labels are withheld until a single final evaluation run is executed with frozen model weights.

### 7. Controls and Confounds

Three controls address the primary confound — that GNN gains may reflect architecture size or feature richness rather than relational structure. First, feature parity ensures both models access equivalent exogenous information. Second, a capacity-matched MLP ablation isolates the graph-connectivity contribution from model capacity. Third, a random-adjacency GNN ablation confirms that the specific road-network topology — not merely the GNN architecture — is responsible for any observed gain. The experiment establishes whether a graph-aware model yields lower VW-MAE in this specific urban carrier setting; it does not claim generalizability to rural networks, different carrier scales, or multi-day forecast horizons.

---

## eval_scenario_20
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Learning-to-Rank Marketplace Search Model vs. BM25 Baseline

### 1. Data Collection and Labeling Strategy

This experiment uses 18 months of production search logs from the marketplace platform. The data set comprises:
- All user queries with timestamps and session IDs
- Product metadata (titles, descriptions, seller IDs)
- Click events with item ID, rank position, and timestamp
- Downstream conversion signals: add-to-cart and purchase events within 24 hours
- Weekly-updated seller quality signals: cancellation rate, late shipment rate, return rate, and review metrics

Labels for the learning-to-rank model are constructed using implicit feedback. Within each search session, any clicked item is treated as a positive (relevant) example relative to non-clicked items shown at the same or earlier positions in the same query. To avoid conflating position bias with relevance, sessions where the clicked item appeared in positions 1–2 are excluded from the primary training signal; they are retained in validation and test to measure position-bias robustness separately. For items leading to purchase within 24 hours, the pairwise relevance weight is doubled (e.g., grade 2 vs. grade 1) to emphasize conversion intent. This approach leverages abundant implicit feedback while partially controlling for exposure bias in label construction.

### 2. Train-Validation-Test Split Strategy

Given the non-stationary nature of search logs (inventory changes, seasonality, promotions), a **chronological temporal split** is used:
- **Training set:** Months 1–12 (12 months of search behavior)
- **Validation set:** Months 13–15 (3 months for hyperparameter tuning and early stopping)
- **Test set:** Months 16–18 (3 months for final held-out evaluation)

This temporal ordering prevents future information (e.g., inventory shifts or new sellers) from leaking into training and ensures both model and baseline are evaluated on search dynamics unseen during development. Additionally, all three sets are stratified by **query frequency quintile** (head queries in top 20%, tail queries in bottom 20%) and by **seller quality quintile** to guarantee representation across diverse scenarios and enable per-stratum analysis.

### 3. Features and Preprocessing

The feature set combines dense semantic representations with explicit seller signals:
- **Text embeddings:** Query embedding, product title embedding, and product description embedding are concatenated. These are generated using a pre-trained or fine-tuned dual-encoder retrieval model (e.g., DPR, ColBERT). The embedding model is fit once on the training set and applied frozen to validation and test.
- **Seller performance features:** Cancellation rate, late shipment rate, return rate (each clipped to plausible ranges to remove outliers), log-scaled seller review count, and average seller rating. All seller signals are standardized (mean 0, std 1) using statistics from the training set only.
- **Query context features:** Query length and query frequency decile (indicating head vs. tail queries).

**Preprocessing fit point:** All scaling, embedding models, and transformations are fit on the training set. No statistics from validation or test sets inform feature engineering. Item position and absolute exposure counts are deliberately excluded from features to avoid encoding the labeling process.

### 4. Model and Baseline

**Model:** A neural pairwise learning-to-rank ranker (e.g., LambdaMART or a fine-tuned neural ranker) trained on pairwise labels using a margin-based or LambdaRank loss. Hyperparameters—network depth, learning rate, regularization strength, margin weight for purchase-labeled pairs—are tuned via grid or random search on the validation set, using NDCG@10 as the tuning metric.

**Baseline:** The production BM25/keyword-based ranker. To ensure a fair comparison, the baseline receives the same seller re-ranking post-processing (boost/penalize items by seller quality signals) applied after retrieval. Importantly, the baseline is also given opportunity to tune one hyperparameter (e.g., BM25 term weighting or seller penalty threshold) on the validation set using the same metric. This avoids a strawman comparison and fairly tests whether the new ranking approach outperforms a reasonably tuned version of the status quo.

### 5. Evaluation Metrics

**Primary metric:** Session-level NDCG@10 on the test set, where clicked items receive relevance grade 1 and clicked-then-purchased items receive grade 2. NDCG is position-aware and rewards placing relevant items higher, directly aligning with the stakeholder's goal of helping shoppers find items to click and buy. It is robust to sparse implicit feedback and penalizes ranking poor-quality (refund-prone) items highly.

**Secondary metrics:**
- **Click-Through Rate (CTR) at positions 1–3:** Early engagement signal.
- **Purchase-weighted NDCG:** NDCG computed using only purchase as the positive label, focusing on conversion.
- **Tail query NDCG:** Performance on bottom-quintile (rare) queries to assess semantic generalization.
- **Exposure-adjusted NDCG (inverse propensity weighting):** Post-hoc adjustment to isolate gains from position bias.
- **Seller quality lift:** Average seller score in top-10 results, to detect whether seller signals alone drive the improvement.

### 6. Model Selection and Validation

Hyperparameter tuning and model selection occur exclusively on the validation set (months 13–15). Early stopping curves, learning rates, and architectural choices are informed by validation NDCG. The test set is sealed and never used for tuning or decision-making. After validation-based selection, the tuned ranker and baseline are applied to the test set once, and all final metrics are reported from that single pass.

### 7. Confound Controls and Scope

To isolate semantic matching improvements from confounding explanations:
- **Stratified analysis:** NDCG, CTR, and purchase metrics are reported separately for head, mid, and tail query quintiles. Uniform improvement suggests genuine relevance gains; concentrated improvement in head queries suggests the model primarily benefits popular items.
- **Seller quality controls:** Average seller quality metrics (cancellation rate, return rate, rating) are computed for top-10 results. If seller signals are the driver, baseline and new model will show similar seller quality; if semantic matching is the driver, quality may improve independently.
- **Exposure adjustment:** A post-hoc inverse propensity weighting analysis upweights clicks on items ranked lower in the baseline. If the new model's NDCG advantage persists after adjustment, position bias is ruled out as the sole explanation.
- **Cross-seller stratification:** Separate NDCG curves for high- vs. low-quality sellers confirm the model is not simply learning seller quality correlations.

This design establishes that the learning-to-rank model improves ranking quality on a held-out test set of unseen search sessions. It does not establish user satisfaction (which requires online A/B testing) nor does it rule out all confounds, but the stratified and exposure-adjusted analysis significantly narrows the space of plausible alternative explanations, providing strong evidence for genuine semantic relevance improvements.

---

## eval_scenario_488
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Transformer-Based Ticket Escalation Prediction

### 1. Objective
This experiment tests whether a transformer-based model that encodes the full sequence of ticket messages and inter-message timing predicts escalation to senior support more accurately than a strong baseline using metadata and bag-of-words features, when both are trained on historical data and evaluated on future held-out tickets.

### 2. Data Source and Label Definition
The experiment uses 36 months of production support tickets from the SaaS company's ticketing system. Each ticket record includes the complete message thread (with sender, timestamp, and text), account metadata (tier, product line, customer segment), agent assignment history, and a binary escalation outcome recorded in workflow logs at the time the escalation action is taken. Escalation is defined operationally as any ticket routed to or reassigned to senior/tier-2 support queue, eliminating annotation ambiguity. No manual relabeling occurs; the label is directly observable from system logs.

### 3. Temporal Split Strategy
Data is divided chronologically: months 1–24 for training, months 25–30 for validation, and months 31–36 for testing. This temporal split prevents leakage of future message replies into the training phase and mirrors the deployment scenario in which the model predicts on in-progress or newly arrived tickets. Product-line stratification is applied within each fold to ensure all major product lines are represented proportionally, preventing product-specific patterns from confounding the baseline-vs.-transformer comparison. The temporal design also naturally exposes both models to drift from product releases, policy changes, and seasonal variation, which must be generalized to in production.

### 4. Feature Engineering and Preprocessing
All preprocessing steps (tokenization, vocabulary building, scaling, missing-value imputation) are fit on the training split and applied identically to validation and test data. Two feature sets are constructed:

**Baseline features:** Account tier, product line, customer segment, priority label, agent tenure, agent prior escalation rate (aggregate statistics, not identity), bag-of-words TF-IDF on ticket title and first message, message length, message word count, off-the-shelf sentiment score, time-of-day and day-of-week, and time since last customer reply (binned into categorical features). Total: ~50–80 features depending on TF-IDF vocabulary size.

**Transformer features:** All baseline features plus the full chronological sequence of message tokens (title concatenated with all reply messages in order), agent/customer alternation pattern, and inter-message timestamps encoded as relative seconds since ticket creation. Sequences are padded or truncated to a maximum length of 512 tokens to balance context and computational cost.

Agent names and IDs are excluded from both feature sets to prevent leakage; instead, agent aggregate statistics proxy for agent quality. This ensures both models have access to equivalent decision-relevant information at prediction time.

### 5. Model and Baseline
**Transformer Model:** A pretrained BERT (or DistilBERT for efficiency) is fine-tuned on the training split. The message sequence and metadata are jointly embedded, with temporal encodings added to timestamps. The [CLS] token output is fed to a 2-layer MLP classification head with dropout, trained with binary cross-entropy loss weighted by inverse class frequency to address imbalance.

**Baseline:** Logistic regression trained on the baseline feature set. Both models receive equal hyperparameter tuning effort: logistic regression is tuned via grid search over 20 parameter combinations (regularization strength C, class weighting); the transformer is tuned via random search over 20 trials (learning rate, warmup steps, dropout). Both use the same validation set for selection and the same primary metric (PR-AUC) for comparison. This ensures any observed improvement in the transformer is not due to better tuning but to architectural advantages in sequence modeling.

### 6. Evaluation Metrics
**Primary metric:** Precision-Recall AUC (PR-AUC) on the test set. Escalation is a rare event (typically 5–15% of tickets in support data), making ROC-AUC inappropriate because high ROC-AUC can be achieved by predicting "no escalation" almost always. PR-AUC directly optimizes for the operating region of interest: balancing the detection of true escalations against false positives that waste senior agent time. PR-AUC is interpreted as the fraction of oracle precision-recall performance achieved by the model.

**Secondary metrics:** Precision at 80% recall (what fraction of escalations flagged at high recall are correct?), recall at 90% precision (how many high-confidence escalations are caught?), false positive rate stratified by product line (to detect product-specific overfitting), and Expected Calibration Error (to ensure predicted probabilities reflect true escalation rates, critical for threshold tuning in production).

### 7. Model Selection and Test Set Policy
Model selection uses the validation split (months 25–30) only. The test split (months 31–36) is held out and touched exactly once for final evaluation, after both models are finalized. The best model is selected based on validation PR-AUC. Results are reported with 95% bootstrap confidence intervals to quantify uncertainty. Stratified test-set analysis by product line confirms that improvements generalize across product areas and are not driven by overfitting to a single dominant line.

### 8. Confound Controls
**Timing and metadata leakage:** Both models access the same ticket metadata (agent tenure, account tier, time-of-day) available at prediction time. The transformer's message sequence is truncated to exclude future replies, preventing the model from using information not available when an escalation decision must be made.

**Product-line confounding:** Test results are stratified by product line to confirm equal performance across lines, ruling out product-specific overfitting as an explanation for transformer improvements.

**Agent leakage:** Agent identities are replaced by aggregate statistics, preventing the model from learning agent-specific biases rather than ticket content patterns.

**Temporal drift:** The temporal train-validation-test split naturally exposes both models to drift; if the transformer's advantage erodes in the test period, this indicates non-stationary patterns and limited deployment reliability.

### 9. Scope of Claims
This experiment establishes whether the transformer model outperforms the baseline on future unseen tickets from the same product lines and support environment. It does not establish whether sequence modeling improves performance on tickets from new product lines, different SaaS companies, or radically different support processes. The experiment isolates the contribution of sequence-level modeling and timing information, conditional on equivalent access to metadata.

---

## eval_scenario_624
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Temporal Fusion Transformer vs. Gradient Boosting for Next-Day Load Forecasting

### 1. Data Strategy

The experiment uses 3–5 years of hourly load data from a regional grid operator, paired with contemporaneous weather observations (temperature, humidity, wind, solar radiation) and calendar/holiday flags. Data is sourced from production SCADA and weather station networks, assumed to be >95% complete. Any gaps shorter than 24 hours are forward-filled; longer gaps are flagged and excluded. Weather data is split into historical observations and next-day forecasts (using the forecast available at the time each prediction was made, not hindsight weather) to match true deployment. This ensures no lookahead bias: the model never accesses weather that was not known at prediction time.

### 2. Temporal Split Strategy

Because load forecasting has strong temporal dependence and exhibits concept drift (demand growth, seasonal patterns), a random train-test split would leak future information and produce overoptimistic estimates. Instead, we use a chronological split: the first 60% of the time series (24–36 months) is the training set, the next 20% (9–12 months) is the validation set, and the final 20% (9–12 months) is the held-out test set. No data is mixed between periods. Within the test set, evaluation uses rolling-origin backtesting: at each forecast origin (each hour or day in the test period), the model predicts next-day demand using only information available up to that time, then the prediction is scored against the realized outcome. The model does not retrain as the window rolls; it uses parameters fit on the training set. This exactly mimics production deployment.

### 3. Feature Engineering and Preprocessing

Both models receive an identical feature set to isolate the effect of model architecture. Features include: (1) Lagged load (prior 24 and 168 hours), (2) Weather: current and next-day forecast temperature (mean, min, max), humidity, wind speed, solar radiation, plus lagged weather (prior 7 days), (3) Calendar: hour-of-day, day-of-week, month, holiday flag, vacation period flag. The baseline also receives interaction features (temperature × hour-of-day, lagged load × day-of-week) to allow the tree model to capture nonlinear patterns without architectural advantage.

All preprocessing transformers (scalers, imputers, encoders) are fit exclusively on the training set. Statistics (mean, std, missing-value mode) are computed from training data only, then applied identically to validation and test sets. This prevents any leakage of future data into the training procedure. Continuous features are standardized to zero mean and unit variance using training statistics.

### 4. Models and Baseline

The proposed model is a Temporal Fusion Transformer (TFT) or equivalent attention-based architecture that processes a 7-day lookback window (168 hours) to forecast next-day average load. The TFT includes separate embeddings for lagged load, exogenous weather, and static calendar features, with multi-head attention to learn variable interactions and temporal dependencies.

The baseline is a well-tuned Gradient Boosted Trees model (LightGBM or XGBoost) trained on the same 7-day feature set. Critically, both models receive equal tuning effort: hyperparameters for each are optimized via the same search method (Bayesian optimization or grid search) on the validation set, with equivalent computational budget. The baseline is not a naive or poorly configured model; it represents a strong, realistic alternative. Any performance difference is therefore attributable to architecture, not optimization.

### 5. Evaluation Metrics

The primary metric is rolling-origin **Mean Absolute Error (MAE)** over the test set, aggregated across all forecast origins and expressed in operational units (MW or GWh). MAE is chosen because: (1) it is symmetric in over- and under-forecasting, reflecting the operator's symmetric cost of overestimating (excess reserves) and underestimating (shortages), (2) it is directly interpretable to stakeholders in familiar units, and (3) it penalizes large errors (e.g., 500 MW misses on peak days) more heavily than small errors, aligning with operational impact.

Secondary metrics include: (1) Mean Absolute Percentage Error (MAPE) to detect systematic bias on high-demand days, (2) Peak-period MAE (MAE on the top 25% of historical load days) to ensure the winner does not sacrifice performance on the most operationally critical periods, (3) Directional accuracy (fraction of forecasts predicting load increase/decrease correctly), (4) Seasonal MAE (separate error computation for summer, winter, spring, fall) to check stability across conditions, and (5) Pinball loss at quantiles 0.1 and 0.9 to assess uncertainty quantification if probabilistic forecasts are later needed.

### 6. Model Selection and Validation

Hyperparameters for both TFT and baseline are tuned using rolling-origin evaluation on the validation window. Each candidate hyperparameter set is scored by its rolling MAE across the validation period. The best hyperparameter set (lowest validation MAE) is selected for each model. Both models are then re-trained on training + validation data combined to maximize training signal before final test evaluation.

The test set is held completely separate during this tuning process and is touched only once at the end for final performance reporting. This ensures the test set remains a true holdout and prevents selection bias.

### 7. Controls for Confounds

To isolate the model architecture from other factors: (1) **Feature parity**: both models use identical features, so improvement is due to the attention mechanism, not richer inputs. (2) **Preprocessing consistency**: all data handling (imputation, scaling, encoding) is identical and fit only on training data. (3) **Weather forecast inputs**: both models use the actual forecast issued at prediction time, not ground truth, ensuring fair and realistic comparison. (4) **Temporal split**: chronological division prevents the baseline from benefiting from any future-information leakage. (5) **Tuning parity**: both models receive equivalent search effort. (6) **Peak-period stratification**: secondary metrics separately evaluate high-demand periods to detect any degradation on operationally critical days. (7) **Multi-season evaluation**: the test window spans at least 12 months to ensure improvement is robust across seasonal variation, not driven by a single anomalous period. (8) **Sensitivity analysis**: after test evaluation, if data permits, results are validated on a held-out future period or by comparing test-set errors in the first and second halves to confirm stability.

### 8. Scope of Claims

If the TFT achieves lower rolling-origin MAE on the test set, the experiment establishes that the TFT architecture, given identical features and equal tuning, produces better next-day load forecasts than gradient boosting for this grid operator's domain. It does not establish that the TFT is superior for all forecasting tasks, other geographies, or different feature sets. It also does not establish whether the improvement justifies the increased computational cost or inference latency of the TFT in production.

---

## eval_scenario_468
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Domain-Adapted Dense Embeddings for Support Article Retrieval

### 1. Data Collection and Quality

The experiment uses 24 months of historical support interactions (tickets and chats) from production, spanning 3+ product release cycles. The dataset should contain a minimum of 500,000 interactions to enable robust training, validation, and testing. Each interaction record includes the customer query text, the article clicked or linked by an agent, full article metadata (title, body, product area, version applicability), timestamps, and customer segment information.

To ensure data quality, we remove: bot-generated interactions, queries shorter than 3 tokens, articles with fewer than 5 clicks in the entire dataset, and obvious duplicate submissions. We flag and separately analyze interactions where an agent overrode a system recommendation, as these represent cases where the system suggestion was insufficient—valuable signal for understanding gaps.

### 2. Label Definition and Weak-Label Audit

The primary label is binary relevance derived from a customer click on an article within the first 3 interactions on a support ticket or chat session. To reduce popularity bias and weak-label noise, we also define a stricter secondary label: positive only if the article was clicked *and* the customer did not subsequently reject it, inferred by the absence of a ticket reopening or explicit rejection within 24 hours.

We conduct a weak-label audit by manually annotating 1,000 random query-article pairs sampled from the validation period. This audit estimates the proportion of positive labels driven by article popularity (global click volume) versus genuine semantic relevance. This calibrates interpretation of results and flags if the model is learning to match popularity rather than intent.

### 3. Temporal Split Strategy

To address non-stationarity and prevent label leakage, we use a chronological (temporal) split:
- **Training:** Months 1–12
- **Validation:** Months 13–18  
- **Test:** Months 19–24

No random shuffling occurs within or across temporal windows. Within each split, we stratify by product area and inferred query type (derived heuristically from ticket templates) to ensure all modules are represented and to prevent the model from memorizing template-based patterns.

**Justification for temporal split:** Product features, article content, and terminology evolve across releases. A random split would allow the model to see future product terminology during training, violating the real deployment scenario. The chronological split mirrors how the model will operate in production: trained on historical data, deployed on unseen future queries.

### 4. Feature Engineering and Preprocessing

Query features include tokenized text and query length. Article features include tokenized title and body, product area tag, version applicability range, and article age (relative to the query date). Derived features include query-article metadata overlap (shared product area, compatible versions).

Critically, we exclude article click counts from the validation and test periods—these would encode future popularity and create label leakage. Click counts from the training period may be included in the baseline comparison to highlight the difference between popularity matching and semantic retrieval.

All preprocessing (tokenization, vocabulary, normalization statistics) is fit on the training split only and applied deterministically to validation and test splits. This prevents the validation and test sets from informing preprocessing parameters.

### 5. Model and Baseline

The proposed model is a dual-encoder dense embedding architecture fine-tuned on training data. We begin with a pre-trained transformer (e.g., DistilBERT or a domain-pretrained variant) and fine-tune it on query-article click pairs using a contrastive loss (e.g., triplet loss or in-batch negatives). Hard negatives are mined from unclicked articles retrieved by BM25 on training queries, drawn from the same product area. We freeze early transformer layers and fine-tune the last 2–4 layers to preserve general linguistic knowledge. Embeddings are 768-dimensional.

The baseline is BM25 lexical retrieval with Okapi BM25 parameters (k1, b) tuned on the validation set using the same primary metric. Both the proposed model and baseline receive equal tuning effort, access the same feature set (with metadata filtering by product area and version), and are evaluated under identical conditions. This ensures the comparison is fair and isolates the contribution of dense, domain-adapted embeddings.

### 6. Model Selection and Validation

Hyperparameter tuning uses the validation split (months 13–18) only. We perform a grid search or Bayesian optimization over: embedding dimension, fine-tuning learning rate, number of epochs, hard negative sampling ratio, and contrastive loss temperature. Early stopping halts training if validation performance plateaus for 3 epochs.

The selection metric is NDCG@5 computed on the validation set using the strict label (click + no rejection). This metric is computed separately per product area to detect concentrated gains.

### 7. Evaluation Metrics

**Primary metric:** Normalized Discounted Cumulative Gain (NDCG@5) on the test set using the strict label.

**Justification:** NDCG@5 reflects real deployment (users see 5 suggestions), penalizes ranking errors proportionally to position, and uses the strict label to mitigate popularity bias. The strict label (click + no rejection) represents true relevance: an article was genuinely helpful to the user.

**Secondary metrics:**
- Recall@5: coverage of relevant articles in top 5
- MRR@10: position of first relevant result
- Coverage: percentage of queries for which the model returns candidates (vs. no match in product area/version constraints)
- BM25-to-Dense ranking overlap: identifies whether the model learns distinct patterns or implicitly recovers lexical matching
- Per-product-area NDCG@5: detects if gains are uniform or concentrated
- Popularity correlation (Spearman): tests whether the model ranks articles by volume rather than semantics

### 8. Confound Control and Validation

To isolate semantic retrieval gains from popularity bias:
- Report NDCG separately by product area; concentrated gains in high-volume modules suggest popularity exploitation.
- Compute Spearman rank correlation between model ranking scores and article click volume; high correlation flags popularity matching.
- Manually audit 100 test queries where dense outperforms BM25 to verify semantic relevance.

To address template leakage:
- Stratify evaluation by query type (templated vs. free-form) and compute NDCG separately.
- Spot-check that the model does not memorize ticket IDs or agent names.

To account for temporal non-stationarity:
- Report NDCG separately for months 19–21 vs. 22–24 to detect performance drift across the test window.

### 9. Test Set Policy

The test set (months 19–24) is held out and touched exactly once for final evaluation after all hyperparameters are frozen. We report point estimates with 95% confidence intervals via bootstrap resampling of test queries. The BM25 baseline is re-run on test data using tuned parameters to verify it does not degrade on held-out data.

---

## eval_scenario_419
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Multimodal Pathology Subtype Classification

### Objective
Test whether a multimodal model combining whole-slide image embeddings and pathology report text predicts tumor subtype more accurately than image-only baseline, with particular emphasis on rare subtypes where morphology alone is ambiguous.

### Data Strategy

**Source and Scope:**
The experiment uses a multi-center pathology archive spanning 3–5 years (e.g., 2019–2024) from 2–3 large hospital systems. Each case comprises: (1) a digitized whole-slide histopathology image; (2) the final signed pathology report as text; (3) specimen metadata (type, stain protocol); and (4) the pathologist-assigned tumor subtype label. Target cohort size is 5,000–10,000 cases, with at least 50–100 cases per rare subtype class to enable statistically meaningful evaluation.

**Label Definition:**
Tumor subtype is extracted from the final signed diagnosis in each report, standardized into a controlled vocabulary. Cases with ambiguous, conflicting, or revised diagnoses are flagged; only the final diagnosis is retained, and cases with incomplete reports are excluded. Class frequencies are documented; rare subtypes are operationally defined as occurring in <5% of the cohort.

### Split Strategy

**Rationale for Site-and-Time Stratification:**
Random splitting would risk leakage: cases from the same institution in adjacent time periods likely share staining protocols, scanner parameters, and templated report language, creating artificial similarity that inflates validation performance and does not generalize to new sites or time periods. Instead, the design uses a stratified split that respects both institutional and temporal boundaries.

**Split Procedure:**
1. Designate one entire institution as the held-out test set (institution-level hold-out). This population tests generalization to a site never seen during training.
2. Within the remaining institutions, perform a temporal split: use cases from the first 60% of the time range for training, the next 20% for validation, and the final 20% for test. This mimics deployment: the model trains on historical cases and is evaluated on future cases.
3. Within each split (train/val/test), stratify by tumor subtype to preserve class proportions, ensuring all classes are represented in all splits.

**Leakage Mitigation:**
This approach ensures that: (a) the test set includes both temporal future cases and an unseen institution, preventing site-specific and temporal overfitting; (b) no case and its near-duplicates (from the same site and adjacent time period) appear across splits; (c) performance can be separately evaluated by institution and time period to detect domain drift or site-specific confounds.

### Feature Engineering

**Image Features:**
Pre-extracted embeddings from a pretrained vision model (e.g., ResNet-50 or Vision Transformer, optionally fine-tuned on PathImageNet or TCGA histopathology data) are used to represent the whole-slide image. Alternatively, patch-level embeddings are aggregated (e.g., mean pooling or attention-based aggregation) to obtain a slide-level representation. The choice is fixed before training and applied consistently.

**Text Features:**
The full pathology report (or pre-diagnostic sections only, if post-hoc diagnostic language is a concern) is tokenized and embedded using a pretrained biomedical language model (e.g., SciBERT, BioBERT, or PubMedBERT). The embeddings capture semantic content of the report.

**Metadata:**
Spécimen type, stain protocol, and patient age (if available) are included as additional features.

**No Future Information:**
All features are computed from information available at the time of diagnosis—no treatment outcomes, follow-up diagnoses, or retrospective clinical notes are included.

**Fit-Apply Separation:**
All preprocessing (image normalization, text tokenization, vocabulary building, and any outlier detection) is fit on the training set only. The same fitted transformers are applied to validation and test sets to avoid data leakage.

### Model and Baseline

**Multimodal Model:**
The image and text embeddings are fused—options include concatenation followed by dense layers, early fusion (shared initial layers), mid-fusion (fusion after initial processing), or attention-based fusion mechanisms. Architecture selection is performed on the validation set using a small grid of standard choices. The final layer is a softmax classifier over subtype classes.

**Image-Only Baseline:**
A model with identical architecture, training procedure, and hyperparameter tuning effort but using only the image embedding (text embedding is zeroed or omitted). This baseline isolates the contribution of text: if the multimodal model outperforms the image-only baseline significantly, the improvement is attributed to multimodal fusion.

**Fair Comparison:**
Both models are trained on the same data splits, use the same optimization algorithm, batch size, learning rate schedule, data augmentation, and number of epochs. Hyperparameter tuning (learning rate, dropout, weight decay) uses the same budget (e.g., grid search over a 3×3 space of hyperparameters) for both. This ensures that performance differences reflect the value of text, not tuning effort.

### Evaluation Metrics

**Primary Metric: Macro-F1**
Macro-F1 is the unweighted F1 score averaged across all subtype classes. This metric directly aligns with the stakeholder objective of reducing diagnostic ambiguity and avoiding misclassification of rare subtypes. Because all classes are weighted equally, macro-F1 penalizes poor performance on rare classes and is not dominated by accuracy on common subtypes. This is essential in pathology, where missing a rare but critical subtype has high clinical cost.

**Secondary Metrics:**
- **Balanced accuracy:** Mean recall per class, providing another perspective on class-balanced performance.
- **Per-class F1 and recall by subtype frequency:** Separately report metrics for rare vs. common subtypes to isolate performance gains on the clinically important rare cases.
- **Per-site and per-time-period macro-F1:** Assess whether performance generalizes across institutions and time periods, detecting domain shift.
- **Calibration (Expected Calibration Error, ECE) per class:** Ensure that predicted probabilities reflect true likelihood, critical for clinical deployment.
- **PPV and NPV per rare subtype:** Operational metrics; report confidence intervals to establish reliability.

### Validation and Model Selection

**Validation Set:** The temporal middle period (20% of cases) from the training institutions is used to tune hyperparameters and select the architecture variant. Validation macro-F1 is monitored during training; early stopping halts training when validation performance plateaus to prevent overfitting.

**Test Set Policy:** The test set (final 20% temporal split + held-out institution) is locked until all model selection is complete. No hyperparameter tuning, threshold adjustment, or ensemble re-weighting occurs on test data. Final predictions are generated once. Statistical significance is assessed using McNemar's test (for paired classification errors) or bootstrap confidence intervals on test predictions, without retraining.

### Handling Confounds

**Temporal and Institutional Confounds:** The site-stratified temporal split mitigates leakage. Sensitivity analysis reports performance per site and time period to detect domain drift or site-specific confounds (e.g., different staining protocols leading to distribution shift).

**Text as Post-Hoc Diagnostic Clue:** Audit report language for post-diagnostic phrasing (e.g., "consistent with subtype X") that would leak the label. If evidence of label leakage is found, rerun the experiment using pre-diagnostic report sections (clinical history and gross description) only. Verify that report text is available at prediction time in the deployment workflow.

**Templated Reporting:** Compute text embedding similarity within and across sites. If sites use highly similar templated language, the model may overfit to site-specific wording. Include site as a stratification variable in sensitivity analysis.

**Class Imbalance:** Use stratified train/val/test splits and class-weighted loss (inverse frequency weighting) during training. Report per-class metrics (F1, recall, PPV) to identify performance disparities. Perform sensitivity analysis on rare subtypes separately to ensure rare-class performance does not degrade.

**Label Noise in Rare Subtypes:** Identify cases with low pathologist confidence or conflicting annotations. Re-run evaluation excluding these cases to assess robustness; stable results indicate the finding is not an artifact of label uncertainty.

### Expected Outcomes and Scope

This design establishes whether text embeddings improve subtype prediction on held-out future data across multiple sites. It does not establish the mechanism (e.g., which report features are informative) or whether the text encodes clinically appropriate information or post-hoc diagnostic clues. Post-hoc analysis of learned feature importance and error case audits are recommended for subsequent work.

---

## eval_scenario_594
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Transformer-Based Ranker for E-Commerce Search Relevance

### 1. Data and Labeling Strategy

The experiment uses 18 months of anonymized search interaction logs from the marketplace production environment. The raw dataset comprises millions of session records, each containing a timestamped query, a ranked list of product impressions (item IDs and positions), click events, add-to-cart signals, and purchase outcomes. Product metadata—title, category, price, average rating—and full review text for each item are joined into the dataset.

Relevance labels are derived primarily from implicit signals: a user click on an item in position p within a query's result set is treated as a positive label (relevance = 1), and non-clicks are negatives (relevance = 0). However, clicks are biased by position: top-ranked items receive more clicks regardless of true relevance. To correct for this, propensity scores are estimated for each position p using training-set clicks via logistic regression. Inverse propensity weighting (IPW) is applied to all click labels: w_p = 1 / P(click | position p). Both models are trained and evaluated using these weighted labels, ensuring a fair comparison.

To validate label quality, ~10,000 query-item pairs are sampled uniformly across query frequency quintiles and labeled by trained human annotators using a 5-point relevance scale. These human labels serve as ground truth for calibration and label-noise estimation but are not used in model training or validation—they are reserved for final sanity-checking against human judgment.

### 2. Train-Validation-Test Split Strategy

A strict temporal split is enforced: months 1–12 form the training set, months 13–15 form the validation set, and months 16–18 form the held-out test set. Temporal splits are critical in this domain because: (i) the product catalog changes over time (new items, discontinued items), and a model trained on future inventory would not generalize to deployment; (ii) seasonal query patterns and trend shifts occur, and the model must adapt within a forward-looking window; (iii) user behavior and click distributions evolve, so train-test temporal alignment reflects real drift.

Within the training set, sessions are grouped by query, and queries are stratified into five frequency-based buckets (very rare, rare, medium, popular, very popular) to ensure balanced representation. This stratification allows subgroup analysis: we will measure NDCG separately for each query frequency decile to detect whether the transformer improves uniformly or only on high-frequency queries.

No random shuffling across temporal boundaries occurs. The validation set is used only for model selection (hyperparameter tuning, early stopping) and is touched exactly once during development. The test set is completely held out until final evaluation.

### 3. Feature Engineering and Preprocessing

All preprocessing is fit on the training set only. A tokenizer (byte-pair encoding, vocabulary size 30k) is learned from training queries and product titles. Propensity models (logistic regressions, one per position) are fit on training clicks to estimate position bias weights.

The transformer model receives the following features:
- **Query:** tokenized text (max 512 tokens), query length, query frequency decile
- **Product:** tokenized title (512 tokens), concatenated recent review text (2000 tokens, sorted by recency), category ID, price percentile (normalized within category), average review rating, review count (log-transformed)
- **Context:** item position in SERP, session length

Review text is included raw, unfiltered, and unfiltered to allow the transformer to learn which aspects of user feedback correlate with relevance. Vocabulary, propensity scores, and any scaling parameters are applied identically to validation and test sets without refitting.

### 4. Models and Baseline

**Proposed Model:** A cross-encoder transformer (e.g., BERT-style architecture) that concatenates [CLS, query tokens, [SEP], title tokens, [SEP], review tokens, numerical features] and outputs a single relevance score (0–1) per query-product pair. Training uses position-bias-weighted binary cross-entropy loss over 5 epochs with early stopping on validation NDCG@10.

**Baseline:** A learning-to-rank model (LambdaMART via LightGBM) trained exclusively on query and title features: BM25 similarity, query-title semantic similarity (frozen pre-trained BERT), exact term match, title length, and position bias weights. The baseline receives equivalent tuning effort: grid search over 10 hyperparameter configurations (leaf size, learning rate, feature fraction), evaluated via 10-fold cross-validation on the training set, with the best model then trained on all training data and evaluated on the validation set.

This baseline isolates the contribution of review text and the transformer architecture. If the transformer outperforms LambdaMART, it is because it learns relevance signals from review content that a simpler ranker with title-only features cannot exploit.

### 5. Evaluation Metrics

**Primary Metric:** NDCG@10 on the test set. NDCG (Normalized Discounted Cumulative Gain) is appropriate because ranking is position-sensitive—items at the top of results matter most for user discovery. NDCG rewards placing relevant items early and penalizes burying them, aligning with the stakeholder's goal of faster product discovery and reduced reformulation behavior.

**Secondary Metrics:**
- NDCG@5 (top-5 emphasis, closer to actual user attention)
- Mean Reciprocal Rank (MRR@10, position of first relevant item, proxy for reformulation reduction)
- Recall@10 (fraction of available relevant items shown, accounts for multiple correct answers)
- Top-1 click-through rate (operational proxy for model quality)
- Calibration metrics (Brier score, expected calibration error on held-out human labels)
- Per-decile NDCG (subgroup analysis across query frequency buckets)

### 6. Validation and Model Selection

Hyperparameter tuning and early stopping use the validation set (months 13–15) exclusively. The transformer uses early stopping on validation NDCG@10; the checkpoint with the best validation score is saved. LambdaMART's hyperparameters are selected via grid search, and the best configuration is retrained on all training data.

The test set is held out and used only once: final inference and metric computation. No tuning, threshold adjustment, or model selection occurs on the test set. Results are reported with 95% confidence intervals computed via bootstrap (1000 samples of test queries, stratified by frequency decile).

### 7. Confound Controls and Scope

To isolate the contribution of review text and the transformer from feature engineering confounds:

1. **Feature parity:** The baseline receives the same propensity-weighted labels, data split, and preprocessing pipeline as the transformer. Both models see identical training signals.
2. **Frequency stratification:** NDCG is reported per query frequency decile. If the transformer improves only on popular queries and harms rare queries, the gain is not universal and may not generalize.
3. **Metadata availability:** Product review count and rating (metadata) are available to both models; the transformer's advantage would come from learning relevance from review *text content*, not from better metadata coverage.
4. **Human label sanity check:** On ~500 human-labeled query-item pairs (held out from all training and tuning), both models are scored against human judgment. If the transformer's NDCG diverges significantly from human labels, label noise or distribution shift is indicated.
5. **Propensity weighting:** Both models are evaluated using propensity-weighted implicit labels, mitigating position bias.

**Scope:** This experiment establishes that the transformer *ranks* more relevant items higher on held-out e-commerce search sessions compared to a title-only baseline. It does **not** establish that this ranking improvement translates to better business outcomes (conversion, revenue, user satisfaction) in production. An online A/B test would be required to validate that improved ranking causally drives downstream business impact.

---

## eval_scenario_207
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Sequence Model vs. Gradient-Boosted Model for Card Fraud Detection

### 1. Data and Labeling

The experiment uses 18–24 months of production card transaction logs from the retail bank, including all authorized and declined transactions. Each record contains transaction timestamp, amount, merchant category (MCC), channel (online/in-person/ATM), geolocation, device/token identifier, and chargeback-confirmed fraud labels assigned within 90 days post-transaction. Transactions without a resolved label after 90 days are excluded to avoid label noise. This dataset reflects the deployment distribution: millions of transactions, highly imbalanced (typically 0.1–0.3% fraud rate), and subject to concept drift as fraud tactics evolve.

### 2. Temporal Split Strategy

Data is divided chronologically without shuffling: months 1–12 for training, months 13–15 for validation, months 16–18 for test. This temporal split is mandatory for fraud detection because predictions must use only historical information available at decision time. Shuffling or stratified random sampling would leak future fraud patterns into training, inflating performance estimates and violating causal ordering. The split mirrors production deployment: a model trained on months 1–12 is deployed to predict on month 13 onward. Stratification by fraud prevalence across windows confirms similar fraud rates; gross imbalances are flagged and documented.

### 3. Feature Engineering and Preprocessing

For the sequence model, transactions are represented as sequences per account, with each event encoded as (timestamp, log_amount, merchant_embedding, channel_onehot, geoloc_region). Merchant embeddings are learned from co-occurrence patterns in the training set using Word2Vec or via the embedding layer of the neural network. Sequences are truncated or zero-padded to a fixed length (e.g., 100 recent transactions per account) to enable batching. For the baseline gradient-boosted model, features are aggregated account-level statistics over 30-, 60-, and 90-day rolling windows: transaction count, total and average amount, frequency, unique merchant count, channel diversity, geographic diversity, device diversity, and interaction terms.

All preprocessing transformers (scaling, categorical encoding, embedding vocabularies) are fit on the training window only and applied identically to validation and test to prevent data leakage and ensure realistic deployment conditions.

### 4. Model Selection and Tuning

**Sequence model:** A bidirectional LSTM or Transformer with attention. Architecture: embedding layer (merchant, 64d), LSTM/Transformer (128 hidden, 2 layers, dropout=0.3), attention pooling, and binary classification head. Trained end-to-end on training data using cross-entropy loss with class-weight balancing. Hyperparameters (learning rate, dropout, sequence length, embedding dimension) are tuned via grid or random search on the validation window, maximizing precision at recall=0.80.

**Baseline:** Gradient-boosted model (XGBoost or LightGBM) on aggregated features. Hyperparameter tuning uses the same validation data and optimization metric as the sequence model, ensuring equivalent tuning effort and fair comparison. Class weights are applied to handle imbalance.

### 5. Evaluation Strategy

**Primary metric:** Precision at fixed recall (recall=0.80). Justification: The stakeholder's constraint is investigator capacity and false-decline cost. Precision at a meaningful recall level quantifies how many alerts are true positives—directly mapping to business objective. The recall threshold (0.80) is set on validation data via the precision-recall curve and applied uniformly to both models' test predictions.

**Secondary metrics:** Recall at fixed precision (e.g., precision=0.95), area under the precision-recall curve (AUPRC), precision and recall by fraud amount quartiles, false positive and false negative rates stratified by time (detect drift), and calibration error.

### 6. Validation and Test Protocol

Hyperparameter selection uses only the validation window (months 13–15). The test window (months 16–18) is locked and accessed only once. After selection, both models are retrained on training + validation combined, then evaluated on the held-out test set. Final results are reported on test data only; confidence intervals (95%) are computed via bootstrap resampling.

### 7. Confound Controls

To isolate sequential modeling value from simple time-windowed features or recency bias: (1) Train an ablated sequence model without learned merchant embeddings to test if one-hot merchants suffice. (2) Extract LSTM attention weights and SHAP values to verify that predictions align with known fraud vectors, not just transaction frequency. (3) Augment the baseline with recent-history features (e.g., transaction count in last 7 days); if the gap closes, the advantage comes from feature engineering, not sequential structure. (4) Stratify test performance by month and fraud cohort to detect overfitting to a particular wave or season. (5) Report performance separately for in-distribution vs. out-of-distribution account cohorts to quantify extrapolation risk.

### 8. Scope and Claims

This experiment establishes whether a sequence model with learned merchant embeddings achieves higher precision at a fixed recall than a well-tuned gradient-boosted model on aggregated features, within the bank's transaction data distribution and fraud label quality. It does not establish whether the sequence model generalizes to other fraud types, customer segments, or geographies unless explicitly held-out and tested. Any observed gain is attributed to the model class and feature representation; claims about why are supported only by ablations and attention analysis.

---

## eval_scenario_483
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

To test whether a transformer-based semantic retrieval model outperforms BM25 for enterprise IT support ticket resolution, the following experiment design is proposed.

1. Data Collection and Preparation
Obtain 18–24 months of production IT support tickets from the company's ticketing system. Each ticket record includes a title, free-text problem description, creation timestamp, and product area and user role metadata. Collect the full knowledge base article corpus with article title, body, topic tags, and update timestamps. Label each ticket with the article(s) consulted by the support agent during resolution, inferred from explicit selection in the ticketing system or timestamped article access logs. A domain expert will manually review a stratified random sample of 200–300 tickets to verify label quality and identify cases where multiple articles are legitimately correct.

2. Temporal Split Strategy
Divide the data chronologically into three disjoint time windows: training (months 1–12), validation (months 13–15), and test (months 16–18). This temporal ordering is essential because tickets and article language evolve over time (product releases, policy changes, new tools); a random split would allow future language to leak into training and mask overfitting. The temporal split ensures validation and test data reflect realistic deployment conditions where new ticket language appears after model training.

3. Model and Baseline Training
Train a transformer-based bi-encoder dense retrieval model (e.g., a fine-tuned BERT-based architecture with contrastive loss) on the training set. Initialize from a pretrained checkpoint and optimize query and document encoders jointly using in-batch negatives or hard negative mining. Independently, tune and train a BM25 keyword baseline on the same training data. Crucially, both models receive identical text input (ticket title + description vs. article title + body) and both have hyperparameters tuned on the validation set using the same primary metric (Recall@10), ensuring fair comparison. Use the validation set for model selection (e.g., early stopping for the transformer, parameter tuning for BM25); do not touch the test set.

4. Primary Evaluation Metric
Evaluate both models on the held-out test set using Recall@10 as the primary metric — the fraction of test queries for which the correct article appears in the top 10 retrieved results. This metric directly aligns with operational goals: support agents need the correct answer in their initial view, not necessarily at rank 1. Recall@10 is appropriate for multi-label data (tickets with multiple correct articles) and is robust to exact ranking within the top 10.

5. Secondary Metrics and Stratification
Compute secondary metrics including Recall@5, Recall@20, and Mean Reciprocal Rank to characterize performance at different display depths. Stratify results by article popularity (quintiles) and product area to detect whether the transformer model generalizes across common and rare issues or shows confounded performance only on high-frequency articles.

6. Confound Control and Ablations
Perform the following checks to rule out memorization and metadata leakage: (1) Metadata ablation — train a transformer variant without product area and user role metadata; compare Recall@10 to the full model to isolate semantic understanding from metadata exploitation. (2) Temporal drift assessment — measure vocabulary overlap between training and test periods; if minimal new vocabulary appears in test, the temporal split is valid; if high, note this as a deployment risk. (3) Manual spot check — expert review of a sample of test results to verify that Recall@10 reflects genuinely correct article matches, not noisy labels. These checks establish confidence that any observed lift is due to semantic modeling, not confounds.

7. Final Reporting
Report Recall@10 for both the transformer model and BM25 baseline with 95% confidence intervals (bootstrap resampling). Provide stratified results, ablation findings, and temporal drift metrics. The experiment concludes whether the transformer model achieves statistically significant higher Recall@10 than BM25 on production-realistic test data where temporal and vocabulary distribution match deployment conditions.

---

## eval_scenario_323
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Sequence Models for 72-Hour Clinical Deterioration Prediction

### 1. Data and Outcome Definition

The experiment uses 36 months of de-identified EHR data from a multi-hospital health system (e.g., 2021–2023), encompassing all inpatient admissions ≥18 years old with at least 4 hours of documented observations in the first 24 hours of hospitalization. Exclusions are palliative/comfort-care patients (identified via admission flags) and readmissions within 30 days. The raw data include timestamped vital signs (HR, BP, SpO2, temperature, RR), laboratory results, medication administrations, and nursing flowsheet entries.

The outcome is binary: clinical deterioration within 72 hours, defined as the earliest occurrence of (1) unplanned ICU transfer, (2) rapid response team activation, or (3) in-hospital mortality. The label is ascertained from operational records and assigned at the time of the event. Patients discharged before 72 hours without an event are labeled as non-events. Expected outcome prevalence is 3–8%.

### 2. Train/Validation/Test Split Strategy

The data are split temporally by admission date to respect causality and prevent leakage:
- **Training set:** Admissions from months 1–24
- **Validation set:** Admissions from months 25–30
- **Test set:** Admissions from months 31–36

Temporal splitting is chosen because (a) it mirrors the deployed scenario (a model trained on historical data is evaluated on genuinely future admissions), (b) it prevents future information from influencing model development, and (c) it captures changes in clinical practice and documentation over time, providing a realistic estimate of generalization error. Within-patient leakage is prevented by assigning each admission (not patient) to a single split based on admission date.

### 3. Feature Engineering and Preprocessing

**Sequence model features:** All time-stamped events occurring in the first 24 hours are represented as an irregularly-sampled sequence. Each event carries: exact timestamp (offset from admission), event type (vital, lab, medication, note), value, and unit. Gaps (missing measurements) are preserved as part of the sequence; the model learns to handle irregular sampling natively. Static admission features—age, sex, admission diagnosis (ICD-10), admission source, and prior hospitalization count—are embedded and concatenated with the sequence representation.

**Baseline (static aggregation) features:** Age, sex, admission diagnosis, admission source, prior hospitalization count, plus aggregate statistics from the first 24 hours: mean, min, max, and standard deviation for each vital and lab; count of abnormal values (using clinical reference ranges); and missingness indicators (e.g., number of missing measurements). Critically, the baseline does not receive timing, event ordering, or event frequency information.

**Preprocessing:** All transformers (imputation, scaling, encoding) are fit on the training set only. Missing values are forward-filled within 2-hour windows for vitals, then imputed using training-set medians/modes for longer gaps. Continuous features are standardized using training-set mean and SD. Categorical variables are one-hot encoded using the training vocabulary; unseen categories in validation/test are mapped to 'other'. No feature engineering decisions are informed by validation or test set statistics.

### 4. Model and Baseline

**Sequence model:** A recurrent or Transformer-based architecture (e.g., LSTM with attention or clinical BERT variant) trained to ingest variable-length event sequences and predict 72-hour deterioration probability. Hyperparameters (embedding dimension, layers, dropout, learning rate) are tuned on the validation set to maximize the primary metric (AUROC).

**Baseline:** Logistic regression trained on the 21 static/aggregate features. Logistic regression is chosen as the fair baseline because it is (1) standard in clinical risk stratification, (2) simple and interpretable, (3) allows equivalent hyperparameter tuning effort (L2 regularization, class weights), and (4) does not exploit temporal structure. Both models receive identical data splits, labels, and tuning procedures.

### 5. Evaluation Strategy

**Primary metric:** Test-set AUROC. AUROC is threshold-agnostic, handles class imbalance, and directly measures discrimination—the ability to rank future deteriorators as higher risk than non-deteriorators. The sequence model is deemed to support the hypothesis if test AUROC exceeds baseline AUROC by ≥0.05 (a clinically meaningful margin), with significance assessed via DeLong's test (α=0.05).

**Secondary metrics:**
- **Calibration:** Expected calibration error (ECE) and calibration slope, to ensure risk scores reflect true probabilities.
- **Operating point performance:** Sensitivity, specificity, PPV, and NPV at a pre-specified threshold (e.g., 90th percentile of validation risk, identifying the top 10% highest-risk patients).
- **Subgroup AUROC:** Performance stratified by age group, admission source, and admission diagnosis category to detect confounding from documentation bias or practice variations.

### 6. Model Selection and Validation

Hyperparameter tuning occurs on the validation set (months 25–30) only. A random 10% of validation data is held for tuning; grid or random search is performed over this tuning set, and optimal hyperparameters are retrained on the full validation set. The test set is not examined until the final evaluation. This separation ensures that test-set performance is an unbiased estimate of generalization.

### 7. Controls for Confounds

Several confounds are addressed:
- **Documentation frequency:** The temporal split captures changes in practice over time. A robustness check compares the sequence model to a baseline augmented with event-count and missingness features; if sequence performance advantage persists, the gain is not purely from documentation patterns.
- **Outcome label shift:** Temporal splits and subgroup analysis (by quarter within the test set) reveal whether outcome composition drifted.
- **Class imbalance:** AUROC is insensitive to prevalence; class-weighted losses and calibration checks ensure balanced optimization.
- **Subgroup robustness:** Stratified AUROC by age, admission source, and diagnosis flags differential performance and potential confounding by unmeasured patient factors or institutional practices.
- **Calibration:** ECE and calibration slope confirm that gains are not due to overconfidence, which would be clinically unsafe.

### 8. Scope and Claims

This design establishes that a sequence model, trained on event-level data from the first 24 hours, achieves better discrimination of 72-hour deterioration than a static aggregate model in a multi-hospital cohort. It does not establish causality, optimal thresholds for deployment, or generalization beyond the health system from which the data originate. Interpretation is limited to the hypothesis as stated: improved discrimination in future admissions at the same institution.

---

## eval_scenario_394
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Transformer vs. TF-IDF for Escalation Prediction in Retail Support

### 1. Data Collection and Labeling

We will use 18–24 months of historical support ticket records from a single retail helpdesk system (e.g., Zendesk, Freshdesk). The dataset should include all message threads (customer and agent messages in chronological order), ticket metadata (creation time, issue category, channel, agent ID, tenure), and operational outcomes (escalation events). A realistic dataset spans 300,000–500,000 tickets. The target label is binary escalation, defined as any explicit escalation event recorded in the helpdesk system: a ticket moved to a supervisor queue, reassigned to a specialist, flagged for callback, or promoted to a higher priority tier. The label is determined at ticket close or at a fixed 72-hour observation window to avoid leakage.

### 2. Train-Validation-Test Split

The 18–24 month period is divided chronologically into three non-overlapping windows:
- **Training (Months 1–12):** Used to fit the transformer and baseline model, including feature engineering and hyperparameter tuning.
- **Validation (Months 13–15):** Used to select hyperparameters and perform early stopping. The validation set is never touched during training; it serves purely for model selection.
- **Test (Months 16–18):** Held-out evaluation set, touched once at the end. This set reflects truly future, unseen data.

Chronological splitting is essential because (a) it prevents future information from leaking into training, (b) it reflects real deployment where the model is trained on past data and evaluated on future data, and (c) it captures concept drift from seasonal demand, policy changes, and product launches. Within each split, we stratify by issue category and channel (email, chat, phone) to ensure each split contains a representative mix of ticket types and communication modes.

### 3. Feature Engineering and Preprocessing

Both models receive identical input scope:
- **Raw text:** The complete ticket thread concatenated with role markers ([CUSTOMER], [AGENT]) to preserve message order and speaker identity. Thread text is truncated to 4,096 tokens.
- **Metadata:** Appended as text: issue category, communication channel, day-of-week and hour-of-day of ticket creation, and agent experience level (tenure band).

For the **transformer baseline:** Raw thread text and metadata are tokenized using a pretrained tokenizer (BERT or DistilBERT). The tokenizer vocabulary is fit on the training set only and applied to validation and test sets. No synthetic features (sentiment, readability) are pre-computed; the transformer learns representations directly from raw text.

For the **TF-IDF baseline:** The same concatenated text is vectorized using TF-IDF (max_features=10,000, min_df=2, max_df=0.95, sublinear_tf=True). The IDF weights and vocabulary are computed on the training set only and applied to validation and test.

All preprocessing (tokenization, vectorization, imputation) is fit exclusively on the training set and then applied identically to validation and test to prevent data leakage.

### 4. Model Training and Baseline

**Transformer model:** A pretrained BERT or DistilBERT is fine-tuned on the training set with a standard classification head (linear layer + sigmoid). Hyperparameters (learning rate ∈ {1e-5, 2e-5, 5e-5}, batch size ∈ {16, 32}, warmup steps, weight decay) are tuned via grid search using the validation set and PR-AUC as the selection criterion. Early stopping is applied on validation PR-AUC with patience of 3 epochs. Training uses cross-entropy loss without class weighting unless class imbalance is severe (checked during initial exploration).

**Baseline:** TF-IDF + logistic regression. Logistic regression is trained on TF-IDF features with L2 regularization. The regularization strength (C) is tuned via grid search on the validation set using the same metric (PR-AUC). The baseline receives equivalent hyperparameter tuning effort and is evaluated under identical conditions, ensuring fair comparison. This baseline represents a mature, production-ready system and is a strong reference point.

### 5. Evaluation Metrics

**Primary metric:** PR-AUC (precision–recall area under curve). This metric is chosen because the operational goal is to catch escalation-prone tickets at a fixed false-positive budget. Precision–recall directly encodes the trade-off between true positives (caught escalations) and false positives (over-escalations), which is operationally meaningful. Over-escalation increases cost and can degrade customer experience, so controlling false positives is critical. PR-AUC is more sensitive to minority class performance than ROC-AUC and aligns with stakeholder objectives.

**Secondary metrics:**
- F1 score at the validation-optimized threshold (balanced summary).
- Precision and recall at fixed recall targets (70%, 80%, 90% recall), since stakeholders often ask "can we catch at least X% of escalations?"
- ROC-AUC (for reference and literature comparison).
- Calibration curve on the test set (to verify predicted probabilities align with observed escalation rates).

All metrics are reported on the test set with 95% confidence intervals via bootstrap resampling (1,000 resamples).

### 6. Model Selection and Validation

Both models are trained using the training set. Hyperparameter tuning is performed via grid search on the validation set using PR-AUC as the selection criterion. The configuration (for each model) that achieves the highest validation PR-AUC is selected as the final model. The test set is not used during model selection or hyperparameter tuning and is evaluated exactly once at the end.

### 7. Confound Controls

Several known confounds are addressed:

1. **Agent behavior:** We stratify train/val/test splits by agent tenure band to ensure each split contains a balanced mix of experience levels. If agent behavior is a major confounder, this stratification will surface differential performance across tenure groups.

2. **Queue policy changes:** We inspect the escalation rate (label prevalence) across all three splits. A significant shift would indicate policy changes or seasonal effects. If detected, we re-run the analysis excluding the affected period or flag it as out-of-distribution.

3. **Per-agent analysis:** After test evaluation, we compute precision and recall per agent. High variance across agents indicates that confounding behavior (e.g., some agents always escalate) may be driving results, not model quality.

4. **Ablation:** We train the transformer with and without agent ID features to verify that the model is learning from thread content rather than simply memorizing agent escalation habits.

5. **Scope check:** If the transformer's advantage is concentrated in a small subset of agents or channels, this is flagged as evidence of confounding rather than true improvement in escalation prediction.

### 8. Claims and Scope

This design will establish whether a transformer fine-tuned on full message threads and metadata outperforms TF-IDF + logistic regression at predicting escalation risk, as measured by PR-AUC on a held-out future period from the same retail helpdesk system. The design does not establish causality (whether the transformer truly "understands" escalation drivers vs. exploiting correlations) nor generalization beyond the single helpdesk system. Per-agent and channel-level breakdowns will help rule out agent-behavior confounds, but operational policy changes remain a potential confound that must be documented during analysis.

---

## eval_scenario_509
**Category:** defense_wins | **Difficulty:** hard | **Correct position:** defense_wins

## Experiment Design: Sequence Models for Heart Failure Readmission Prediction

### 1. Data Source and Cohort Definition

The experiment uses 36 months of retrospective EHR data from a single health system or integrated multi-site network. The cohort comprises all adult patients discharged following a primary diagnosis of acute decompensated heart failure (ICD-10: I50.x). We exclude admissions with incomplete vital sign or laboratory records during the hospital stay, or those missing discharge disposition or 30-day follow-up information. This yields approximately 5,000–15,000 admissions, depending on system size and data availability.

The outcome label is defined as any unplanned hospital readmission (ED visit converting to inpatient admission, or direct readmission) within 30 calendar days of discharge. We derive this from hospital encounter records and validate against claims or ED logs where available. Planned readmissions (scheduled procedures or transfers for specialized care) are excluded via procedure code matching and spot-checked manual review on a validation sample.

### 2. Data Splitting and Leakage Prevention

To preserve temporal ordering and prevent future information from leaking into the training window, we use a temporal split:
- **Months 1–24**: Training set (60% of admissions)
- **Months 25–30**: Validation set (20% of admissions, used for model selection only)
- **Months 31–36**: Held-out test set (20% of admissions, untouched until final evaluation)

Within each split, admissions are stratified by (1) discharge hospital site and (2) baseline risk tier derived from prior 6-month utilization (high/medium/low). This ensures that both model selection and final evaluation occur on data representative of the operational mix of sites and patient risk profiles, and it allows us to detect whether performance gains are localized or confounded by site-specific workflows.

### 3. Features and Preprocessing

The sequence model receives irregularly sampled multivariate time series:
- **Vital signs**: Heart rate, BP, respiratory rate, temperature, O₂ saturation, weight (with timestamps and measurement source).
- **Laboratory values**: BNP/NT-proBNP, troponin, creatinine, BUN, sodium, potassium, hemoglobin, ejection fraction (with result timestamps).
- **Medications**: Administration history of ACE inhibitors, beta-blockers, diuretics, vasodilators, inotropes (with timestamps and dose information).
- **Admission-level features**: Age, sex, ICD-10 diagnoses, admission source, discharge disposition, prior 6-month utilization (ED visits, admissions, observation stays).

The baseline model uses manually engineered summary statistics: min/max/mean/last value for each vital and lab; binary indicators for medication class receipt; age, sex, diagnosis count; and prior utilization counts. These summaries represent standard clinical risk modeling practice.

All scaling (StandardScaler), imputation, and categorical encoding transformers are fit exclusively on the training set and applied identically to validation and test sets. No information from validation or test data influences preprocessing.

### 4. Model and Baseline

The **sequence model** is a GRU or Transformer-based encoder that processes variable-length timestamped sequences. It embeds categorical inputs (medications, diagnoses), scales continuous features, processes them through recurrent or attention layers, and outputs a sigmoid probability of 30-day readmission. The final layer is a 2-layer fully connected head (128 units, ReLU, dropout 0.3).

The **baseline** is L2-regularized logistic regression trained on the manually engineered feature set. Both models are fit with class weights (reweighting by inverse label frequency) to account for the typical 15–25% readmission rate. The baseline receives equal tuning effort: grid search over L2 regularization strength (C ∈ [0.001, 0.01, 0.1, 1, 10]) on the validation set.

This ensures a fair comparison: the baseline is not a straw man but a well-motivated, carefully tuned competitor representing current clinical practice.

### 5. Model Selection and Evaluation Strategy

Hyperparameter tuning for both models is performed on the validation set (months 25–30) using grid or random search. The model configuration yielding the highest validation AUC is selected. The test set is held out completely—it is accessed only once, after model selection is finalized, to compute final performance estimates.

### 6. Metrics

**Primary metric**: Concordance statistic (ROC-AUC) on the test set. AUC reflects the operational use case (risk ranking for care manager triage) and is insensitive to label prevalence.

**Secondary metrics**:
- Calibration (Hosmer-Lemeshow test, calibration curve): Ensures predicted probabilities are honest and clinically interpretable.
- Sensitivity at fixed specificity (e.g., 90%): Reflects operational thresholds and the clinical priority of not missing high-risk patients.
- Decision curve analysis: Quantifies clinical utility by integrating sensitivity-specificity trade-offs at candidate action thresholds.
- Site-stratified AUC: Detects whether performance gains are confounded by discharge site, hospital workflows, or coding behavior.

### 7. Confound Control and Sensitivity Analysis

The temporal split prevents leakage from future discharge practices. Stratification by site ensures fair representation and enables site-level performance monitoring. Post-hoc sensitivity analyses will (1) examine whether the sequence model's gain correlates with measurement frequency (indicating confounding by data availability) or with true clinical factors (e.g., worsening vital trends), and (2) check robustness to discharge-process proxies (e.g., time-of-day effects). If the model's advantage is concentrated at a single site or driven by measurement frequency rather than clinical signal, the hypothesis remains unconfirmed, and the result would signal the need for further investigation.

---
