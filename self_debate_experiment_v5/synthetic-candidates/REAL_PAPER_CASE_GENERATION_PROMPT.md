# Real-Paper Hard Case Generation Prompt

**Scope:** Hard cases only (difficulty=hard). Supplements `benchmark_case_generation_prompt.md` — use this prompt to generate cases grounded in documented real-world methodological failures rather than invented scenarios.

**For use with a non-Anthropic LLM (e.g., GPT-4o, GPT-5, Gemini, etc.)**

**Purpose:** Generate 12–15 hard benchmark cases by transposing documented methodological flaws from real published ML papers into anonymized, camouflaged scenarios. Cases generated this way are harder than invented cases because the flaws were missed by actual expert reviewers — they are genuine, not constructed to be tractable.

**How to use:**
1. Paste this entire document as the system/instruction prompt
2. Request 12–15 hard cases using the source paper library below
3. Request output as a JSON array matching the schema in the Output Format section
4. Run the v5 self-evaluation tests on each case before output
5. Run Phase 5.5 difficulty gate — acceptance criterion: ≥ 6 of 10 sampled cases score mean < 0.55 with `claude-haiku-4-5` as single-pass evaluator

---

## Why Start From Real Papers

Previous prompts asked the model to invent hard cases from scratch. This reliably produces cases that are too easy, for a structural reason: when you invent a flaw, you unconsciously include enough signal to make it findable. Real paper flaws were missed by peer reviewers, domain experts, and the research community — sometimes for years. They are hard because they were genuinely hard, not because they were designed to be solvable.

The external benchmark cases (Dacrema, Obermeyer, DeGrave) scored consistently below the invented hard cases for precisely this reason: the flaws were real, the confounds were genuine, and the methodology sections were written by researchers who believed the work was sound.

**The approach:** Take a real paper's methodology, extract the core flaw mechanism, transpose it to a structurally analogous domain that obscures the source, and write a case where the flaw is embedded in an otherwise-sound-looking methodology memo. The flaw type is preserved; the source paper is not recognizable.

---

## Source Paper Library

Each entry provides the flaw mechanism for use in case construction. **Do not reproduce the source paper domain or scenario verbatim** — transpose to a different domain as specified in the Transformation Instructions section. The source paper is never shown to agents; it is recorded only in the `source_paper` field for operator provenance tracking.

---

### Source 1 — Dacrema et al. (2019), RecSys

**Domain:** Recommendation systems

**Methodology:** Evaluated 18 neural recommender systems against simple baselines (ItemKNN, PureSVD, BPR) on standard datasets. Neural methods consistently outperformed baselines in the original papers.

**Core flaw:** The baselines were not tuned — hyperparameter search was applied to the neural models but not to the simple baselines. When baselines were properly tuned with the same budget, 7 of 9 neural methods were outperformed by at least one simple baseline. The claim of neural superiority rests on an asymmetric comparison.

**Flaw type:** `critical_omission` — omission of baseline tuning from the evaluation protocol, not stated as a limitation

**Transpose to:** Any model comparison domain where a new complex method is compared to a legacy baseline — churn prediction, fraud scoring, clinical risk stratification, document classification

---

### Source 2 — Obermeyer et al. (2019), Science

**Domain:** Clinical ML, population health management

**Methodology:** A commercial risk-stratification algorithm assigned patients to a "high-risk" care management program based on predicted healthcare cost. The algorithm achieved high accuracy (AUC 0.77 on cost prediction).

**Core flaw:** The algorithm uses cost as a proxy for health need, under the implicit assumption that cost and need are equally correlated across demographic groups. They are not: due to systemic unequal access to care, Black patients with the same disease burden generate lower healthcare costs than White patients, so the algorithm systematically underestimates their health need. At a given risk score, Black patients were significantly sicker than White patients.

**Flaw type:** `assumption_violation` — proxy variable assumed to be an unbiased measure of the target concept, but the proxy is itself biased by a systemic factor that correlates with the protected attribute

**Transpose to:** Any domain where an observable quantity is used as a proxy for an unobservable target, and where the proxy relationship may differ across subgroups — salary history as proxy for job performance in hiring, spending patterns as proxy for creditworthiness in lending, service call frequency as proxy for equipment health in predictive maintenance

---

### Source 3 — DeGrave et al. (2021), Nature Machine Intelligence

**Domain:** Medical imaging, COVID-19 detection

**Methodology:** Trained CNNs on chest radiographs from multiple hospital systems to detect COVID-19. Models achieved AUC > 0.90 on internal test sets drawn from the same hospitals.

**Core flaw:** The training data confounds hospital-specific imaging artifacts (positioning conventions, equipment signatures, metadata text burned into images) with disease labels. The model learned hospital membership as a shortcut to COVID-19 status — hospitals that treated more COVID patients in a given period had distinctive imaging characteristics. No out-of-hospital validation was performed, so the shortcut was not discovered until external deployment.

**Flaw type:** `critical_omission` — omission of external validation across sites; the evaluation protocol cannot distinguish genuine disease detection from hospital-membership detection

**Transpose to:** Any multi-site model trained on data where site membership is confounded with label prevalence — network intrusion detection trained across different enterprise environments, manufacturing defect detection across factories, fraud detection trained on data from specific merchant categories

---

### Source 4 — Lazer et al. (2014), Science

**Domain:** Public health surveillance, big data prediction

**Methodology:** Google Flu Trends (GFT) predicted influenza-like illness (ILI) prevalence by correlating search query volume against CDC surveillance data. The model used 50 million terms fit against 1,152 weekly ILI measurements.

**Core flaw:** Severe overfitting from extreme dimensionality (50M features, 1,152 labels) combined with a stationarity assumption — the model assumed the relationship between search queries and ILI incidence was stable. Google's search algorithm changed 86 times in a single month during one influenza season, altering query distributions independently of actual disease prevalence. GFT overestimated ILI by a factor of 2 during the 2012–2013 season.

**Flaw type:** `assumption_violation` — stationarity assumption violated by changes in the feature-generating process that are independent of the target variable

**Transpose to:** Any model trained on user-generated behavioral signals that assumes the signal-to-target relationship is stable — app usage as proxy for customer health in SaaS, click-through rate as proxy for content quality in recommendation, support ticket volume as proxy for product defect rate

---

### Source 5 — Zech et al. (2018), PLOS Medicine

**Domain:** Clinical ML, radiology

**Methodology:** Trained a CNN on chest X-rays for pneumonia detection across multiple hospital datasets. Internal validation (same hospital system) achieved AUC 0.931. The paper reported this as strong generalization performance.

**Core flaw:** The model learned hospital-system-specific artifacts alongside pneumonia features. External validation at a different hospital yielded AUC 0.815. Further analysis showed the model could identify which hospital system an image came from with high accuracy — evidence that hospital membership was a confounding variable. The evaluation protocol used train/test splits within the same hospital system, making this confound invisible.

**Flaw type:** `assumption_violation` — i.i.d. assumption violated by unmeasured site-level confounders; internal validation is presented as evidence of generalization

**Transpose to:** Models trained on data from a single organization or region presented as generalizable — HR attrition models trained on one company's employees, credit default models trained on one lender's portfolio, product failure models trained on one factory's production line

---

### Source 6 — Recht et al. (2019), ICML

**Domain:** Computer vision, benchmark evaluation

**Methodology:** Evaluated ImageNet-trained classifiers on a new test set constructed by carefully replicating the original data collection procedure (same search terms, same annotation protocol, same filtering). Models trained on the original ImageNet training set were evaluated on both the original test set and the new test set.

**Core flaw:** Despite the nearly identical collection procedure, accuracy dropped 11–14% on the new test set for all evaluated models. The models had implicitly overfit to the idiosyncratic properties of the original test set over years of iterative improvement on it. The original test set was treated as representative of the distribution, but models had learned to exploit its specific quirks.

**Flaw type:** `critical_omission` — omission of temporal or distributional holdout; long-term iteration on a fixed test set causes implicit leakage even without direct access to test labels

**Transpose to:** Any domain with a long-lived benchmark that has been used for iterative model selection — leaderboard-driven ML competitions, clinical risk scores validated on the same population cohort over many years, NLP benchmarks used as primary selection criteria across multiple paper cycles

---

### Source 7 — Hooker et al. (2019), NeurIPS

**Domain:** ML interpretability evaluation

**Methodology:** Proposed ROAR (RemOve And Retrain) as an evaluation protocol for feature importance methods. The protocol removes features ranked as important by each method, retrains the model, and measures accuracy degradation. Methods producing larger accuracy degradation are judged better.

**Core flaw:** The retraining step changes the model being evaluated. A salience map describes how the *original* model uses features. ROAR evaluates what happens when a *different model* is trained without those features — a different question. Additionally, removing top-ranked features shifts the input distribution, making the retrained model's accuracy on the modified distribution incomparable to the original. The protocol conflates "explanatory faithfulness" with "feature usefulness for prediction."

**Flaw type:** `wrong_justification` — the evaluation protocol is justified as measuring salience map quality, but it measures a different quantity; the justification is plausible but technically wrong

**Transpose to:** Any evaluation where the measurement procedure modifies the system it is intended to evaluate — A/B test designs that change user behavior by exposure to the treatment condition, benchmark contamination where evaluation data is used for fine-tuning, calibration assessment that uses the calibration procedure to generate the ground-truth labels

---

### Source 8 — SMOTE Before Cross-Validation (Documented Pitfall)

**Domain:** Classification with class imbalance

**Methodology:** Applied SMOTE to generate synthetic minority class samples on the full dataset before performing k-fold cross-validation. Reported significantly improved minority class recall and F1. Justified as: "SMOTE was applied to the training data to address class imbalance."

**Core flaw:** SMOTE before CV creates data leakage. Synthetic samples are generated from all available instances, including those that will appear in validation folds. During CV, synthetic samples derived from a held-out instance may appear in the training fold, causing the model to have effectively seen information from the validation set. This inflates CV estimates by 0.1–0.2 AUC in documented cases. The justification ("applied to training data") describes the intent correctly but the implementation is wrong — the split must occur before SMOTE, not after.

**Flaw type:** `wrong_justification` — the justification describes correct practice but the implementation order violates it; the error is in the execution sequence, not the stated procedure

**Transpose to:** Any preprocessing step that generates new data from the training corpus before a split is applied — feature scaling fit on combined train+test data, data augmentation applied before train/test split, imputation using statistics computed on the full dataset

---

### Source 9 — Caruana et al. (2015), KDD

**Domain:** Clinical ML, pneumonia mortality prediction

**Methodology:** Trained rule-based models and neural networks to predict pneumonia mortality risk from structured clinical data. Discovered that both model types learned that having asthma lowers pneumonia mortality risk.

**Core flaw:** This is the opposite of the true causal relationship (asthma is a major risk factor for pneumonia mortality). The confounding arose from the clinical protocol: patients with asthma and pneumonia were triaged directly to the ICU and received intensive treatment, so their outcomes in the training data were better than average. The model learned the *treatment selection rule* rather than the underlying risk. The training data reflects observed outcomes under existing clinical protocols, not counterfactual outcomes under a neutral protocol.

**Flaw type:** `assumption_violation` — assumes training labels reflect unconfounded causal relationships; violated by treatment selection bias (high-risk patients receive differential treatment, improving their observed outcomes)

**Transpose to:** Any predictive model trained on historical data where the target outcome was affected by an existing intervention that was triggered by risk level — fraud detection trained on data where suspicious transactions were manually reviewed and blocked, predictive maintenance trained where high-risk equipment was proactively replaced, churn prediction trained where high-predicted-churn customers received retention offers

---

### Source 10 — Time Series Leakage via Pre-Generated Sequences

**Domain:** Time series forecasting

**Methodology:** Generated input-output sequence pairs from a time series dataset and then performed an 80/20 train-test split on the generated sequences. Reported strong generalization performance on the test set.

**Core flaw:** When sequences overlap temporally (a sliding window of length L generates sequences starting at t, t+1, t+2, ...), splitting the sequence list randomly causes adjacent-window sequences to appear in both train and test sets. The model sees training sequences whose input windows overlap with test sequences' target windows — a form of temporal leakage. Splitting must occur on the *original time series* before sequence generation, not on the *generated sequence list*.

**Flaw type:** `critical_omission` — no disclosure of whether the split was performed on the original time series or on the generated sequences; omits the ordering of split vs. sequence generation

**Transpose to:** Any model trained on derived records from a time-ordered source — session-based models derived from user log data, image patch models derived from video frames, event prediction models derived from longitudinal records

---

### Source 11 — Offline-Online Gap in Recommendation Systems

**Domain:** Recommendation systems, offline evaluation

**Methodology:** Evaluated a new recommendation algorithm using Leave-One-Out Cross-Validation (LOOCV) on a static user interaction dataset. Reported 12% improvement in Precision@10 over the baseline. Proposed deployment based on this offline result.

**Core flaw:** LOOCV on a static dataset does not reflect the temporal dynamics of the deployment setting. The test items are drawn uniformly from each user's history regardless of recency, but in production the model must predict future interactions from past ones. The offline evaluation metric measures reconstruction of a static snapshot, not forecasting of future behavior. Algorithms that exploit popularity patterns perform well offline but poorly online because popularity distributions shift after deployment.

**Flaw type:** `assumption_violation` — offline evaluation assumes the test set reflects the same distribution as future deployment conditions; violated by temporal non-stationarity in user preferences and item popularity

**Transpose to:** Any system where a static offline evaluation is used to justify an online deployment decision — A/B test surrogates trained on historical data, predictive models for future market conditions calibrated on past data, anomaly detectors calibrated on historical baselines when the baseline is known to drift

---

### Source 12 — Ziegler et al. (RLHF Reward Model Overoptimization)

**Domain:** Language model fine-tuning, RLHF

**Methodology:** Trained a reward model from human preference data, then used PPO to optimize a language model against this reward model. Reported substantial gains on human preference evaluations (win rate vs. reference model).

**Core flaw:** The reward model is an imperfect proxy for human preferences. As the policy model is optimized against it, the policy learns to exploit gaps between the reward model's learned proxy and true human preferences — a form of Goodhart's Law. The human evaluation used to validate the result was conducted on the *same distribution of prompts* as the training reward model, making it likely that the evaluation captured reward hacking that happened to look good on familiar prompts. External evaluation on out-of-distribution prompts showed degraded performance.

**Flaw type:** `assumption_violation` — proxy optimization assumes the reward model is a sufficiently faithful proxy; violated by reward hacking that generalizes within the evaluation distribution but not beyond it

**Transpose to:** Any system where optimization against a surrogate metric is evaluated using the same surrogate — click-through rate optimization evaluated on click-through rate, safety classifiers fine-tuned to satisfy their own outputs, model compression evaluated on the benchmark it was compressed for

---

### Source 13 — Informative Censoring in Survival Analysis (Biostatistics Pitfall)

**Domain:** Clinical ML, time-to-event modeling

**Methodology:** Trained a Cox proportional hazards model or survival random forest on patient follow-up data to predict time to a clinical event (e.g., disease progression, readmission). Censored observations (patients who left the study without experiencing the event) were handled using standard right-censoring methods. Model performance was reported as concordance index on an internal holdout.

**Core flaw:** Censoring was informative — patients who were doing poorly were more likely to drop out of the study (lost to follow-up, transferred to palliative care) before experiencing the formally-recorded event. The standard right-censoring assumption (censoring is independent of the event) is violated: the censoring mechanism is correlated with the outcome. The concordance index on the holdout is optimistic because the holdout also contains informatively censored observations; the most difficult-to-predict patients are systematically underrepresented in both training and evaluation.

**Flaw type:** `assumption_violation` — the non-informative censoring assumption is violated by a clinical dropout mechanism correlated with disease severity

**Transpose to:** Equipment lifetime prediction where units that are failing subtly show different sensor patterns and are taken offline (informative removal before failure event); employee attrition models where the highest-risk employees are given retention packages and leave through a different mechanism than the modeled "unplanned departure"; subscription churn models where users who are about to cancel stop logging events days before cancellation (informative dropout before observed churn event).

---

### Source 14 — Aggregated Performance Masking Stratum-Specific Degradation

**Domain:** Multi-population ML deployment, clinical risk scoring

**Methodology:** A model was evaluated using a population-weighted aggregate metric (weighted AUC, macro-average F1, or pooled accuracy) across multiple sites or demographic groups. The aggregate metric was used to justify deployment "across all populations." Individual stratum metrics were computed but reported only in an appendix.

**Core flaw:** The aggregate metric is dominated by the majority stratum. The model achieves substantially lower performance on minority strata (lower-volume sites, smaller demographic subgroups, or rare clinical presentations). The deployment claim — that the model works "across all populations" — requires adequate performance on each stratum, but the reported metric does not surface stratum-level failures. The majority stratum inflates the aggregate to an acceptable level even when minority strata fall below any reasonable clinical or operational threshold.

**Flaw type:** `metric_mismatch` — the reported metric is not aligned with the deployment claim; a claim of "works across all populations" requires per-stratum evaluation, not population-weighted aggregation

**Transpose to:** Multi-warehouse demand forecasting reported as a single MAPE while small-volume SKUs have catastrophic MAPE; content moderation across language communities where high-resource languages inflate aggregate precision while low-resource languages fail; fraud detection across merchant categories where rare-category fraud is swamped by common-category volume in the aggregate.

---

### Source 15 — Calibration Circularity in Model Validation

**Domain:** Probabilistic prediction, clinical risk scoring, insurance pricing

**Methodology:** Trained a probabilistic classifier and assessed calibration using a dedicated calibration validation set. Observed poor initial calibration and applied Platt scaling or isotonic regression to recalibrate. Reported final calibration on the same validation set used to fit the recalibration, along with a calibration plot showing excellent agreement between predicted probabilities and observed rates.

**Core flaw:** The recalibration method (and its hyperparameters) was selected because it produced the best-looking calibration on the validation set. The final calibration evaluation uses the same set on which the recalibration was fit. This is circular: the validation set both guided recalibration selection and now serves as the evaluation. The reported calibration is optimistic — it cannot detect whether the recalibration procedure has overfit the validation fold. An independent test set would show worse calibration than reported.

**Flaw type:** `wrong_justification` — the calibration procedure is described as validated by the calibration set, but the calibration set was used to fit the recalibration, making the evaluation circular

**Transpose to:** Any post-hoc adjustment fitted and evaluated on the same held-out set — threshold selection evaluated on the threshold-selection set, rank-order normalization of scores evaluated on the same sample used to set percentile bins, temperature scaling evaluated on the validation fold used to select the temperature parameter.

---

### Source 16 — Instance-Filtering Bias from Quality-Based Data Curation

**Domain:** Dataset curation, model training on structured data

**Methodology:** Training data was filtered for "high-quality" or "high-confidence" instances using an automated quality score (model confidence, annotation agreement score, or rule-based heuristic). The model was trained and evaluated on the filtered distribution. Performance was reported as strong on the curated test set.

**Core flaw:** The quality filter correlates with instance difficulty — easy, unambiguous cases receive high quality scores and are retained; hard, ambiguous, or distributional-tail cases are removed from both training and evaluation. The model is trained on the easy subset and evaluated on the same easy subset. The deployment distribution includes all incoming instances, including the difficult cases excluded by the filter. The model appears to generalize well within the filtered distribution but has unknown (likely poor) performance on the excluded tail — which comprises exactly the cases where accurate prediction matters most.

**Flaw type:** `assumption_violation` — the evaluation distribution is assumed to represent the deployment distribution; the curation step creates a systematic gap between the evaluated distribution and the actual deployment setting

**Transpose to:** NLP models trained on high-agreement annotation subsets evaluated on high-agreement test sets; medical imaging models trained on high-quality scans with no motion artifact evaluated on clinical-workflow images; sensor anomaly detection trained on "confirmed" anomaly labels (ignoring ambiguous cases) and evaluated on the same confirmed set while ambiguous borderline anomalies constitute the majority of production traffic.

---

## Defense_Wins Source Patterns (Sound Methods That Look Suspicious)

These patterns are used exclusively for `defense_wins` cases. Unlike the flawed-methodology sources above, these describe **correct methodology that is commonly misread as problematic**. The case is hard because the surface appearance is suspicious; the correct verdict requires positive domain knowledge to reach.

Use these patterns as design seeds. Each entry names the sound practice, describes why it looks suspicious to pattern-matching critics, and identifies the external knowledge required for exoneration.

---

### Defense Pattern A — Spatially Independent Validation (already used)

**Sound practice:** Using spatial-block or geographic holdouts that yield lower headline metrics than random splitting.

**Why it looks suspicious:** The headline score is worse than a simpler approach. Critics conflate "lower score" with "weaker methodology." The team appears to have chosen a method that makes their results look bad.

**External knowledge for exoneration:** Random tile or parcel splits within a spatially autocorrelated dataset inflate performance by violating train-test independence. Spatial blocking is the methodologically correct choice when the deployment claim involves generalization to new geographic locations. Lower score under correct validation is evidence of better calibration, not weakness.

**Difficulty mechanism:** The reviewer must distinguish a disclosed, design-appropriate limitation from an invalidating flaw. Pattern-matchers who stop at "lower F1" will assert a false critique.

---

### Defense Pattern B — Pre-Measurement Constrained Randomization with Optimization (already used)

**Sound practice:** Generating many candidate layouts and selecting the one that minimizes batch-phenotype correlation before any measurement occurs.

**Why it looks suspicious:** The process "searched until favorable" — multiple layouts were evaluated and the best one chosen. This structurally resembles p-hacking or outcome-seeking design, which are genuine methodological failures.

**External knowledge for exoneration:** Pre-measurement optimization on design variables (not on outcome data) is an established approach in multi-constraint experimental design (e.g., constrained randomization, covariate-adaptive allocation). The key distinction: the optimization objective was correlation between batch and design variables, not observed outcomes. No outcome data existed at optimization time. This approach reduces exactly the batch-phenotype confounds that undermine reproducibility.

**Difficulty mechanism:** Critics must distinguish layout optimization (prospective, on design metadata) from outcome-seeking tuning (retrospective, on results). This requires knowing the concept of constrained randomization — it cannot be resolved by reading the prompt more carefully.

---

### Defense Pattern C — Reference-Anchored Relative Quantification (already used)

**Sound practice:** Transforming absolute measurements into ratios relative to a concurrent common reference, rather than using raw cross-lab values directly.

**Why it looks suspicious:** Raw values differ visibly across labs when plotted. Critics treat raw disagreement as evidence of failure and demand absolute scale agreement before trusting the model.

**External knowledge for exoneration:** In multi-site omics programs, absolute values drift for technical reasons (instrument calibration, reagent lots, handling variation). Concurrent common references convert drifting absolute measurements into comparable relative quantities anchored to the same material. This is the correct approach for prospective multi-site data and is standard in validated multi-lab workflows (e.g., NIST reference material protocols).

**Difficulty mechanism:** The obvious finding — raw values differ — is a deliberate red herring. Exoneration requires knowing that the ratio design was built to accommodate exactly this property.

---

### Defense Pattern D — Conservative Evaluation That Produces Lower Headline Metrics

**Sound practice:** Using a more demanding evaluation protocol (stricter split, more challenging test set, harder baseline comparison) that intentionally yields lower scores than the easier alternative.

**Why it looks suspicious:** The published number is lower than what the team could have reported. Critics interpret this as underperformance, a methodological problem with the approach, or a sign that the model was unable to meet a more standard benchmark.

**External knowledge for exoneration:** Harder evaluation protocols are a mark of rigor, not weakness, when the claim is calibrated to match the evaluation scope. A model that scores 0.72 on a geographic holdout while the standard approach yields 0.89 is not underperforming — it is reporting honest performance. The correct verdict is to defend the evaluation design as appropriate for the deployment claim, while noting the disclosed gap between the conservative and naive estimates.

**New transposition targets:** Any setting where a team voluntarily chose the harder test: leaving out one full site from a multi-site study (lower score but honest generalization claim), using a strictly prospective temporal holdout rather than random split on a time-ordered dataset, reporting worst-case subgroup performance as the headline rather than pooled average.

---

### Defense Pattern E — Nested Cross-Validation Yielding Lower Performance Than Simple CV

**Sound practice:** Using nested CV (inner loop for hyperparameter selection, outer loop for performance estimation) which produces a lower, less biased estimate than single-loop CV used for both tuning and reporting.

**Why it looks suspicious:** The reported performance is lower than a simpler approach would produce. The team appears to have found a worse model, or to have used an unnecessarily complex validation scheme that penalizes them for no apparent reason.

**External knowledge for exoneration:** Nested CV is the methodologically correct approach when the same dataset is used for both model selection and performance reporting. Single-loop CV — using the same folds for both hyperparameter tuning and final evaluation — produces an optimistic estimate because the selected model was chosen for performing well on those specific folds. The lower nested CV score is a more honest estimate of out-of-sample performance. This is not a limitation; it is the design working correctly.

**Difficulty mechanism:** The critic must know that nested CV is not a more pessimistic version of simple CV — it is the correct version, and simple CV is the biased one. Most practitioners have used simple CV and may not immediately recognize nested CV's advantage.

---

### Defense Pattern F — Acknowledged Limitation Properly Scoped to a Narrow Claim

**Sound practice:** A methodology section that explicitly identifies a constraint on generalizability and correctly limits the deployment claim to within the validated scope.

**Why it looks suspicious:** The team acknowledges a limitation — external validity, sample representativeness, distributional scope. Critics treat disclosed limitations as admissions of fatal flaws. The team appears to be defending a weak result by narrowing the goalposts post-hoc.

**External knowledge for exoneration:** In rigorous applied science and regulatory work, explicitly scoped claims are stronger, not weaker, than vague claims of generalizability. A model validated for use in one hospital's patient population that is deployed only at that hospital is correctly scoped. A team that acknowledges "we do not claim generalizability to other institutions" is being honest; the correct critique is to assess whether the claim matches the evidence, not to penalize them for not claiming more than they validated. The debate resolution is defense_wins when the claim is genuinely narrow and the limitation is genuinely disclosed.

**Difficulty mechanism:** The critic has to resist the reflex that a limitation + a defense = weakness. The correct reading is that the limitation is honest and the claim was never broader.

---

## Transformation Instructions

For each case, select one source and perform the following transformation. For flawed-methodology sources (Sources 1–12), extract the flaw and transpose it. For defense_wins cases, select a Defense Pattern (A–F) or derive a novel sound-methodology pattern and transpose it to a new domain.

### Step 1: Extract the flaw mechanism (critique cases) or sound-practice mechanism (defense_wins cases)

**Critique cases:** Write a one-sentence description of the flaw at the level of **abstract mechanism**, not domain-specific instance.
- NOT "cost is used as proxy for health need, which is biased for Black patients"
- YES "a proxy variable is used to measure an unobservable target quantity, under the assumption that the proxy-target correlation is uniform across subgroups; the assumption fails because a systemic factor affects the proxy but not the target differently across subgroups"

**Defense_wins cases:** Write a one-sentence description of the sound practice being misread, and separately, the surface appearance that generates the false concern.
- Sound practice: "Constrained randomization selects the layout that minimizes batch-phenotype correlation before measurement"
- False concern surface: "The team searched over many candidate layouts and selected the one that looked best"

### Step 2: Select a target domain

Choose a domain that:
- Preserves the abstract mechanism
- Is structurally analogous but surficially different from the source
- Does not share key vocabulary with the source paper (different disease, different model type, different industry)
- Belongs to a domain not used by more than 2 other cases in the batch
- Includes at least one **domain-specific detail** — a regulatory constraint, measurement protocol, data collection convention, or field-specific norm — that affects how the flaw manifests in that domain

Generic industry labels without domain-specific texture are insufficient. "Fraud detection" is not a domain — "real-time card transaction fraud scoring under PCI-DSS reporting requirements with a 3-second SLA" is a domain. The domain-specific detail must be embedded in the task_prompt and must be necessary context for understanding (or for missing) the flaw.

Suggested transpositions by source:

| Source domain | Suggested transpositions |
|---|---|
| Clinical ML, radiology | Fraud detection, HR analytics, manufacturing QC |
| Recommendation systems | Search ranking, content moderation, financial scoring |
| Public health surveillance | Ops monitoring, demand forecasting, IoT anomaly detection |
| NLP/text | Tabular classification, time series, vision |
| Computer vision | Sensor data, genomics, document processing |

### Step 3: Write the case prompt

Write a 500–800 word internal memo, evaluation report, or launch proposal. Requirements:
- Opens with a positive result or deployment recommendation — no problem statements
- Every stated fact must be consistent with every other stated fact (the flaw is not a factual inconsistency)
- For critique cases: the flaw is present as an assumption violation, critical omission, or wrong justification — NOT as an explicit statement of a problem. Additionally follow all 4 requirements in **Critique Case Design Requirements** below.
- For defense_wins cases: the false concern must be supported by **≥2 independent signals** in the prompt — converging circumstantial evidence, a plausible narrative, and at least one detail that looks like confirmation (see Defense_Wins Case Design Requirements below)
- Apply all v5 trigger phrase prohibitions: no contrast signals, no compensation language, no parallel before/after structure
- Include at least one plausible concern with a defensible but incomplete justification (the `must_not_claim` item); for critique cases this must appear in the **first 2 paragraphs** with explicit supporting detail (see Critique Requirement 2)
- Include realistic operational detail: team names, timelines, infrastructure, deployment numbers

### Step 4: Verify the mechanism is not source-recognizable

A reviewer who knows the source paper must not be able to identify it from the task_prompt. Check:
- Domain is different from source paper domain
- Model type / algorithm type is different
- No shared vocabulary with the source paper title or abstract
- The mechanism is present at the abstract level, not the surface level

### Step 5: Complete the schema

Populate all required fields. The `source_paper` field is operator-only metadata — never include it in `task_prompt`, `ideal_critique`, or `ideal_defense`.

---

## Defense_Wins Case Design Requirements

Defense_wins cases are not simply cases where the model is correct. They are hard because the prompt contains **plausible evidence that the methodology is flawed, even though it is not**. These requirements are mandatory in addition to the general Transformation Instructions above.

### Requirement 1: Multi-evidence false concern

The false concern must be supported by **at least two independent superficial signals** in the prompt. A single red flag is too easy to dismiss. Required structure:

1. **A surface observation** that looks problematic at face value (e.g., lower score than alternative, non-standard design choice, visible cross-site variation)
2. **A framing or narrative** in the memo that makes the concern seem deliberate or motivated (e.g., the team appears to have chosen the approach that makes their result look better, or avoided a stricter test for unstated reasons)
3. **At least one supporting detail** that appears to confirm the concern (e.g., an appendix showing the alternative approach yielded a higher number, or a methods note that could be read as acknowledging the weakness)

The defender must address all three threads, not just the top-level complaint. Cases where the false concern rests on a single misread are too easy and must be redesigned.

### Requirement 2: External knowledge required for exoneration

The exoneration must require **domain-specific positive knowledge**, not just a careful re-read of the prompt. The reviewer who reads the prompt twice and still cannot confirm the methodology is sound has not been given sufficient internal evidence — this is the design working correctly. What is needed is knowledge from outside the prompt: a domain convention, a methodological literature result, a regulatory standard, or a field-specific best practice.

The `requires_external_knowledge` field in `planted_issues` must name this knowledge explicitly.

### Requirement 3: Diversified flaw types across the defense_wins batch

Defense_wins planted issues should cover at least two distinct flaw types across the full set of defense_wins cases generated:
- `wrong_justification` — the sound practice is misread as a suspicious optimization or incorrect procedure
- `assumption_violation` (false positive) — the reviewer assumes a confound or proxy failure exists that was actually controlled
- `critical_omission` (false positive) — the reviewer claims something was omitted that was present and addressed, just not prominently flagged

Using only `wrong_justification` across all defense_wins cases creates a predictable pattern that reduces difficulty.

### Requirement 4: Calibrated ideal_defense

The `ideal_defense` field must contain the specific argument that rebuts each of the ≥2 false concern signals. Vague defenses ("the methodology is sound") are not sufficient. Each signal named in `planted_issues` must have a corresponding rebuttal in `ideal_defense`.

---

## Critique Case Design Requirements

These requirements are mandatory for all critique/mixed cases (correct_position ≠ defense_wins). They exist to prevent single-pass pattern-matching from reliably surfacing all must_find issues. Failing these requirements produces cases that score IDR=1 with Haiku — which the smoke-test evidence confirms is the default outcome without these constraints.

### Requirement 1: Addressed-but-incorrectly pattern (at least 1 must_find per case)

At least one must_find issue must be a flaw the team **explicitly discussed** in the memo and **provided a justification for**. The justification must be subtly wrong — not obviously wrong, not absent. Requirements for the justification:
- Uses correct-sounding methodology language that reads as competent
- The logical or empirical error is not visible without domain knowledge or careful reasoning
- The team presents the issue as resolved ("we addressed this by...", "to control for X, we Y")

Mark this issue in planted_issues as the primary `addressed_but_incorrectly` issue. The `requires_external_knowledge` field must state what knowledge is needed to evaluate whether the justification is actually correct.

**Why this is necessary:** When all must_find issues are silently present (no stated justification), pattern-matching is sufficient to score IDR=1 and IDP=1. The addressed-but-incorrectly pattern forces the evaluator to assess justification *quality*, not just *presence*. A model that reads the justification and accepts it fails IDR (missed the issue). A model that flags the concern without explaining why the justification is wrong fails IDP.

### Requirement 2: Decoy dominance

The must_not_claim concern must:
- Appear in the **first 2 paragraphs** of the task_prompt
- Be supported by **at least one explicit detail** (a number, a comparison, a team acknowledgment, or a disclosed limitation)
- Be framed in a way that reads as the team's honest acknowledgment of a potential weakness

The first must_find flaw may not appear before paragraph 3. It should be embedded in technical or operational detail without an explicit red-flag framing — never introduced with language that signals "this is the problem."

**Why this is necessary:** If the must_not_claim concern is buried and must_find flaws are prominent, models find all must_find issues in a single pass and never evaluate the decoy. Foregrounding the decoy forces the model to resist its first reading and reason about which concern is genuine.

**Lever B — Domain-specific false alarm (at least 1 must_not_claim per critique/mixed case):**
At least one `must_not_claim` concern per critique/mixed case must be a **domain-specific false alarm**: a concern that matches a well-known general ML pitfall but does not apply in this domain because of a field-specific convention, standard, or norm. The memo must NOT contain the information needed to dismiss this concern — dismissal requires field-specific knowledge from outside the prompt. The `requires_external_knowledge` field on the corresponding `planted_issues` entry must name the specific domain knowledge that exonerates it.

Examples of the pattern: "Using MAPE for intermittent demand is invalid" — wrong when the domain uses the industry-standard modified-MAPE variant; "Reporting AUC-ROC on imbalanced classes overstates performance" — wrong when the domain uses threshold-independent reporting per regulatory guidance; "Single-institution validation is insufficient" — wrong when the regulatory scope is explicitly institution-specific.

### Requirement 3: At least one compound issue per case

At least one must_find issue must be visible only when **two separate pieces of information** from the memo are combined. Neither piece alone is suspicious; the flaw only surfaces when the model reasons across both. 

In planted_issues, document this as: `"compound": true` and include a `"requires_combination_of"` note naming the two pieces. Neither piece should appear in the same paragraph as the other.

**Why this is necessary:** If every must_find issue is independently locatable to a single paragraph, IDR=1 requires only single-paragraph pattern-matching. Compound issues require maintaining two pieces of information across the memo and recognizing their interaction — a reasoning step that single-pass assessors frequently skip.

### Requirement 4: Domain-knowledge-gated issues (at least 2 cases per batch)

For at least 2 cases in the batch, at least one must_find issue per case must require **domain-specific knowledge** to identify correctly — not general ML pattern-matching. "Domain-specific" means the relevant knowledge comes from a specialized field convention, regulatory standard, measurement protocol, or field-specific literature that a pure ML practitioner without domain training would not have.

The `requires_external_knowledge` field must name this knowledge explicitly and specifically (e.g., "ICH E9(R1) guidance on estimands — the estimand framework distinguishes treatment policy estimand from principal stratum estimand; this case requires understanding which estimand applies to a censored subgroup"). Entries like "knowledge of data leakage" do not qualify.

---

## Constraints

### Category distribution (across all 12–15 generated cases)

| Category | Target n |
|---|---|
| broken_baseline | 2–3 |
| metric_mismatch | 2–3 |
| hidden_confounding | 2–3 |
| scope_intent_misunderstanding | 2–3 |
| **defense_wins** | **5–6** |
| real_world_framing | 1–2 |

> **Rationale for defense_wins increase:** Evaluation shows that critique/mixed cases are near-ceiling for single-pass strong models. Defense_wins cases are where the debate protocol generates the clearest fair-comparison lift signal: the baseline has no defender (false positive stands), isolated debate has a Defender responding without seeing the specific false concern, and multiround has a Defender who can address each false-concern thread explicitly. A 35–40% defense_wins proportion is required to measure this signal reliably.

### Position and must-find
- At least 4 cases must have `correct_position: "mixed"` with `empirical_test_agreed` resolution
- Non-defense_wins cases: 3–5 `must_find_issue_ids` each
- Defense_wins cases: 0 `must_find`; `planted_issues` documents the false concern trap with ≥1 entry per false-concern signal (minimum 2 entries total per case)
- Every case: 2–4 `must_not_claim` items, each grounded in a plausible prompt-internal concern with incomplete justification
- Critique/mixed cases: at least 1 must_find per case must be marked `"addressed_but_incorrectly": true` in planted_issues (see Critique Requirement 1)
- Critique/mixed cases: at least 1 must_find per case must be marked `"compound": true` in planted_issues (see Critique Requirement 3)
- Across the batch: at least 2 critique/mixed cases must include a domain-knowledge-gated must_find whose `requires_external_knowledge` names specific field literature or standards (see Critique Requirement 4)
- **Hard critique/mixed cases must use `acceptable_resolutions: ["empirical_test_agreed"]` only.** Do not include `critique_wins` as an acceptable resolution. Task prompts must be designed so the correct verdict is "the evidence is suggestive but an empirical test is needed." The `ideal_debate_resolution.type` must be `empirical_test_agreed` with meaningful `supports_critique_if`, `supports_defense_if`, and `ambiguous_if` conditions.
- Every critique/mixed case must have at least 1 domain-specific false-alarm `must_not_claim` item (see Critique Requirement 2, Lever B)

### Source paper diversity
- No source paper or defense pattern may be used more than twice
- At least 8 different sources must be represented across the batch
- The same abstract mechanism may appear in at most 2 cases (even from different sources)
- Defense Patterns A, B, C (already used in existing real-paper supplement) may be reused at most once in a new batch; prefer Patterns D, E, F or novel patterns

### Domain diversity
- No domain (clinical, recommendation, fraud, NLP, etc.) may be used more than 3 times
- The target domain must differ from the source domain for all cases

---

## Output Format

Return a JSON array. No markdown formatting. Output starts with `[` and ends with `]`.

Each case object uses the v5 schema with one additional field:

```json
{
  "case_id": "eval_scenario_NNN",
  "category": "broken_baseline | metric_mismatch | hidden_confounding | scope_intent_misunderstanding | defense_wins | real_world_framing",
  "difficulty": "hard",
  "task_prompt": "500–800 word memo/report. Internally consistent. Opens with positive result. For defense_wins: contains ≥2 independent false-concern signals.",
  "ground_truth": {
    "correct_position": "critique | defense | mixed",
    "final_verdict": "One sentence stating the correct conclusion.",
    "required_empirical_test": "For empirical_test_agreed cases: the exact experiment. For others: null."
  },
  "planted_issues": [
    {
      "issue_id": "opaque_snake_case_id",
      "description": "What the issue is and why it matters. For defense_wins: one entry per false-concern signal (minimum 2 entries).",
      "severity": "low | medium | high",
      "flaw_type": "assumption_violation | quantitative_error | critical_omission | wrong_justification",
      "requires_external_knowledge": "One sentence: what domain knowledge is needed to identify this as a false concern (defense_wins) or genuine flaw (critique)."
    }
  ],
  "ideal_critique": ["What a well-calibrated critique should find."],
  "ideal_defense": ["For defense_wins: one rebuttal per planted_issue signal. For critique cases: what a well-calibrated defense should concede or contest."],
  "ideal_debate_resolution": {
    "type": "critique_wins | defense_wins | empirical_test_agreed",
    "supports_critique_if": "Specific, falsifiable result pattern.",
    "supports_defense_if": "Specific, falsifiable result pattern.",
    "ambiguous_if": "Specific, falsifiable result pattern."
  },
  "scoring_targets": {
    "must_find_issue_ids": ["issue_id_1"],
    "must_not_claim": ["plausible_but_wrong_concern_1"],
    "acceptable_resolutions": ["empirical_test_agreed"]
  },
  "suspicious_but_valid_features": "For defense_wins cases only: a plain-English list of the features that make the work *look* methodologically problematic to a pattern-matching critic but are actually justified. Minimum 2 entries corresponding to the ≥2 false-concern signals. For non-defense_wins cases: null.",
  "ground_truth_rationale": "2-3 sentences. Answer key only.",
  "difficulty_justification": "Which v5 principles make this case hard. Which specific rubric dimensions (IDR, IDP, DC, DRQ, ETD, FVC) a single-pass assessor should fail on and why. For defense_wins: which false-concern signals will trip pattern-matching models, and what external knowledge is required to dismiss each one.",
  "source_paper": "Author (year), Venue — or Defense Pattern letter — operator provenance only, never shown to agents.",
  "verifier_status": "pending",
  "notes": "Which v5 self-evaluation tests each case passes."
}
```

---

## Self-Evaluation (Required Before Output)

Run all nine tests on every case. Discard or redesign any case that fails two or more. Record pass/fail for each test in `notes`.

**The Internal Consistency Test:** Read only the `task_prompt`. Can you find ALL must_find issues (critique cases) or identify the false concern as definitively false (defense_wins cases) by checking whether any stated facts contradict each other? If YES for critique — the flaw is a factual inconsistency detectable by pattern-matching. Redesign. If YES for defense_wins — the false concern can be dismissed purely from internal evidence, meaning the case is too easy. Redesign.

**The Checklist Test:** For the case's category, apply the standard review checklist. Does the checklist mechanically find the flaw (critique) or mechanically dismiss the false concern (defense_wins)? If YES — the mechanism is predictable from the category. Change the category assignment or change the surface presentation.

**The Skimming Test:** Read only the first and last paragraphs. Can you determine the correct verdict? If YES — verdict leakage is present. Restructure so the conclusion is not front-loaded or back-loaded.

**The Justification Test:** Does the document acknowledge any concern and provide a justification? For each justification: is it clearly correct, clearly wrong, or subtly wrong? Critique cases: at least one justification must be subtly wrong. Defense_wins cases: at least one justification must be subtly right but look suspicious on surface.

**The Run-to-Run Variation Test (proxy difficulty check):** Mentally simulate submitting this task_prompt to a single-pass evaluator twice with temperature > 0. Would both runs produce the same findings, in the same order? If YES — the case has a deterministic single reading. Redesign to introduce genuine ambiguity.

**The Source Recognition Test:** Mentally simulate a reviewer who has read the source paper or knows the defense pattern. Can they identify the source from the task_prompt? If YES — the transposition is insufficient. Change the domain, model type, or core vocabulary.

**The Domain Expert False Positive Test (defense_wins cases only):** Mentally simulate a competent ML practitioner who knows the general area but has not read the specific methodology literature relevant to this case. Would they raise the false concern on a first pass? If NO — the false concern is not plausible enough; redesign. If YES — proceed. Now check: would the same practitioner, if they had read the relevant methodology paper or domain standard, be able to definitively dismiss the concern? If NO — the exoneration requires knowledge that doesn't exist; redesign. If YES — the case is working correctly.

**The Decoy Prominence Test (critique cases only):** Read only the first two paragraphs of the task_prompt. Is the must_not_claim concern present with explicit supporting detail (a number, a comparison, or a team acknowledgment)? If NO — add it before proceeding. Now simulate: a model that identifies only the must_not_claim concern (and nothing in must_find) but reaches the correct overall verdict (critique_wins or mixed) — is this possible? If YES — the verdict is accessible without finding any genuine flaw; redesign the case so that correct FVC requires identifying at least one must_find issue.

**The Addressed-But-Incorrectly Test (critique cases only):** Identify every must_find issue. For each one: is there a stated justification in the task_prompt? If **none** of the must_find issues has a stated justification — convert at least one to the addressed-but-incorrectly pattern before proceeding. A case where every flaw is silently present with no stated rationale is detectable by pattern-matching alone; adding a subtly-wrong justification forces reasoning about justification quality.

---

## Difficulty Acceptance Criteria

A case passes the gate if a `claude-haiku-4-5` single-pass assessor scores **mean < 0.55** — meaning Haiku misses ≥1 must_find issue (critique cases), OR asserts a must_not_claim item, OR reaches the wrong verdict (including falsely critiquing a defense_wins case).

Additionally, the case should produce **run-to-run variation** when evaluated at nonzero temperature. Verbatim-identical outputs across runs indicate the flaw or false concern is too deterministically findable.

Cases that score 1.0 with Haiku, or that produce verbatim-identical outputs, must be redesigned — typically by:
- Critique cases: making the transposition deeper (more domain-specific operational noise, more distance from source paper vocabulary)
- Defense_wins cases: adding a second or third false-concern signal, or replacing the false concern with one that requires harder external knowledge to dismiss

---

## Quality Standard

**Critique cases:** A senior ML engineer who has NOT read the source paper reads the task_prompt and says "this looks fine" on first pass, then on second pass with specific probing identifies "wait — there's a problem with [the mechanism]."

**Defense_wins cases:** A senior ML engineer reads the task_prompt and says "this looks suspicious" on first pass — there are 2–3 things that feel like red flags. On second pass, with deliberate probing, they confirm the methodology is sound. A senior ML engineer who has read the relevant methodology literature dismisses the concern quickly; one who has not may remain uncertain even after a careful read.

The quality bar for defense_wins is: the false concern must be plausible enough that a competent reviewer would raise it in a real review, and hard enough to dismiss that they would need to either consult the literature or have prior domain knowledge. Cases where the false concern is obviously dismissible (e.g., "they disclosed the limitation so it's fine") are too easy and must be redesigned.

Cases where the transposition is superficial are rejected. Cases where the mechanism has been distorted are also rejected — the mechanism must be structurally identical to the source.

Begin generation now. Generate all 12–15 cases with 5–6 defense_wins cases using Defense Patterns D, E, F (and at most one reuse each of Patterns A, B, C), and prefer Sources 13–16 for at least 4 of the critique/mixed cases. Apply all 4 Critique Case Design Requirements and all 4 Defense_Wins Case Design Requirements. Run all nine self-evaluation tests, then output the final set.

---

## OUTPUT FORMATTING REQUIREMENT

No markdown formatting in the final JSON output. No code fences, no triple backticks, no language tags. Output starts directly with `[` and ends directly with `]`.
