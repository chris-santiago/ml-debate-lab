# Benchmark Prompts — Self-Debate Experiment v3
Task prompts for all 49 benchmark cases, verbatim. No ground-truth, planted-issue,
scoring, or answer-key fields are included.

---

## broken_baseline_forecast_002

**category**: broken_baseline  
**difficulty**: easy  
**correct_position**: critique

A regional grocery chain trained a gradient-boosted demand forecasting model for weekly unit sales across 600 store-SKU pairs. The model uses three years of history and predicts one week ahead. Inputs include lagged sales, holiday indicators, local weather, planned promotions, and whether an item is temporarily displayed on an endcap. The team evaluates on the most recent 20 weeks and reports weighted absolute percentage error of 11.8%, compared with 18.9% for the baseline. The baseline is described as the retailer’s current seasonal heuristic: forecast next week’s sales using sales from the same week last year. The paper emphasizes that the new model is particularly strong around holidays and promotion periods, where the error gap widens further. Buried in the methods section, the authors state that the heuristic baseline does not ingest the promotion calendar or endcap schedule even though those plans are available before forecast time and are part of the model inputs. They also mention that the retailer’s current heuristic was designed for categories with relatively stable pricing and was never re-parameterized after the chain expanded from 18 to 34 stores, increasing promotion frequency. The authors argue that this is the operational baseline and therefore the relevant benchmark. They additionally report that all model features are known before the week begins and that prediction latency is negligible because forecasts are computed overnight. The operations team wants to use the reported results to justify replacing the chain’s replenishment planning logic before the next holiday season.

---

## broken_baseline_ocr_003

**category**: broken_baseline  
**difficulty**: easy  
**correct_position**: mixed

A document AI startup developed a vision-language model to extract totals, merchant names, dates, and tax amounts from retail receipts. The evaluation set contains 8,400 scanned receipts from restaurants, supermarkets, gas stations, and pharmacies collected from users of a bookkeeping app. The startup compares its system against a commercial OCR product that many small customers already use. On exact-field accuracy, the new model scores 91.4% while the commercial product scores 83.0%. The startup highlights that its model also handles rotated images and crumpled paper better than the commercial engine. In the experimental details, the commercial OCR service was run with its default general-document configuration because the team did not have access to the optional receipt-specific parser included in the vendor’s enterprise tier. The startup also notes that around 30% of the evaluation set consists of Canadian receipts with bilingual English-French text and taxes listed in province-specific formats. The commercial product was executed with its default English setting, while the startup fine-tuned its model on both English and French receipts. The authors say this still reflects a realistic small-business deployment because many buyers use the lower-cost default package. They add that their model’s median processing time is 1.7 seconds per image, compared with 0.6 seconds for the commercial product, which they believe is acceptable for bookkeeping workflows. They plan to present the study to prospective customers as evidence that their model clearly outperforms incumbent OCR solutions.

---

## broken_baseline_clinical_004

**category**: broken_baseline  
**difficulty**: medium  
**correct_position**: critique

An academic hospital built a gradient-boosted model to predict sepsis six hours before clinical recognition in emergency department patients. The dataset contains 42,000 encounters over four years. The model updates hourly using the latest vitals, laboratory results, and nurse-charted observations. It is compared against qSOFA, a widely known three-variable bedside score. The paper reports AUROC of 0.86 for the new model versus 0.71 for qSOFA and claims a major advance in early sepsis recognition. The model prediction is evaluated using the best score available during the six hours before recognition. For qSOFA, however, the authors compute the score only once, using the first complete set of vital signs recorded within 30 minutes of emergency department arrival. In a supplementary note, they explain this reflects how qSOFA is commonly documented in their institution’s triage workflow. They also note that lactate and white-blood-cell measurements are not always available at arrival but usually become available within the first few hours, which benefits the hourly-updating ML model. The paper argues that the comparison is clinically meaningful because clinicians make early triage decisions near arrival. Still, the system is proposed for deployment as a continuously updating sepsis surveillance tool, not only as a triage screen. The authors additionally report that the model’s median lead time among true positives is 3.1 hours and that all features were extracted from routine EHR data already present in the hospital system. The study is being used to support a request for a prospective silent trial.

---

## broken_baseline_fraud_006

**category**: broken_baseline  
**difficulty**: medium  
**correct_position**: mixed

A payments company built a graph neural network to detect account-takeover fraud. The model uses transaction links, shared devices, merchant overlap, and recent password-reset activity. It is trained on nine months of transactions and evaluated on the tenth month. The paper compares the graph model against the company’s existing rules engine and reports that at a manual-review rate of 0.8% of transactions, the graph model captures 78% of confirmed fraud versus 63% for the rules engine. The authors describe this as a large operational gain. In the methods section, the graph model’s alert threshold is explicitly tuned on a validation set to hit the target review-rate budget of 0.8%. The rules engine, by contrast, is evaluated at its production threshold, which historically targeted about 1.2% review volume but happened to yield 0.8% review volume on the specific test month because transaction volumes were seasonally low. The appendix also notes that fraud analysts revised many rule weights four months before the study, but those revised weights were not replayed because only the production snapshot at deployment start was archived. The company argues that replaying the live rules engine is the only practical benchmark and most relevant for a replacement decision. They further report that the graph model met nightly batch latency constraints and that feature construction excluded any investigator notes not available at score time. The risk team wants to use the result to justify redirecting analyst headcount toward the new system.

---

## broken_baseline_recsys_007

**category**: broken_baseline  
**difficulty**: medium  
**correct_position**: critique

A music streaming service developed a two-stage recommendation stack with a neural retrieval model followed by a gradient-boosted ranker. The offline study focuses on the retrieval stage. The new retriever uses user listening history, artist embeddings, skip behavior, and audio-content embeddings for tracks. It is compared against matrix factorization trained on historical play events. On full-catalog Recall@100, the neural retriever scores 0.43 versus 0.31 for matrix factorization. The paper argues this demonstrates a clear improvement in candidate generation quality. In the experimental details, the neural retriever is trained only on impressions from the current home-screen product, where every impression includes a logged exposure indicator. The matrix-factorization baseline is trained on the service’s legacy play-only table from a wider date range because the authors say reconstructing impression-level negatives for the baseline pipeline would have been too expensive. The new model therefore benefits from skip labels and explicit non-consumption signals, whereas the baseline is trained only on positive play events. The paper also notes that audio-content embeddings are especially helpful for new tracks and reports a cold-start Recall@100 gain of 19 points. The authors say the comparison is reasonable because matrix factorization is the incumbent retrieval method in production. They add that both systems meet retrieval-latency constraints and that the next step is a full online ranking experiment. Internal reviewers ask whether the result isolates neural retrieval quality or mostly reflects richer supervision and content features provided only to the new system.

---

## broken_baseline_energy_010

**category**: broken_baseline  
**difficulty**: hard  
**correct_position**: critique

A quantitative energy-trading team developed a transformer model to forecast next-day hourly wholesale electricity prices in a deregulated market. The model uses five years of historical prices, unit outages, load forecasts, wind forecasts, gas hub prices, and interconnector schedules. It is evaluated on the most recent six months after a major market-rule redesign that introduced new scarcity-pricing behavior during reserve shortfalls. The paper compares the transformer against an ARIMA baseline and reports mean absolute error of $7.80 per MWh for the transformer versus $11.60 for ARIMA. The authors argue that this proves deep learning is clearly superior for short-term price formation. In the methods appendix, the ARIMA baseline is fit once on a pre-redesign training window ending just before the market-rule change and then frozen for the entire six-month test period. It also uses only lagged prices, because the authors say adding exogenous regressors to the old ARIMA codebase would have taken extra engineering effort. The transformer is retrained monthly on rolling data and receives the exogenous fuel, weather, and outage inputs. The paper notes that traders care most about the top 5% of high-price hours because hedging losses are concentrated there, but the headline evaluation remains overall MAE. The authors say the benchmark is fair because ARIMA represents the firm’s legacy model and the objective was to assess whether a modern deep model is a better production replacement. They plan to use the result to justify a capital allocation change for next summer.

---

## broken_baseline_genomics_011

**category**: broken_baseline  
**difficulty**: hard  
**correct_position**: critique

A genomics startup trained a deep sequence model to predict whether missense variants in an inherited cardiomyopathy panel are pathogenic. The benchmark contains 18,000 variants with ClinVar labels curated up to a fixed cutoff date. The model ingests amino-acid context, conservation features, and protein-language-model embeddings. It is compared against PolyPhen-2, a widely used legacy pathogenicity score, and achieves AUROC of 0.93 versus 0.84 for PolyPhen-2. The paper frames this as strong evidence that modern foundation-model representations outperform classical variant-effect predictors. In the evaluation details, the new model is calibrated and thresholded only on missense variants from cardiomyopathy genes, while PolyPhen-2 is used off the shelf with its generic published threshold. The authors also note that approximately 40% of the evaluation set comes from two sarcomere genes with unusually well-characterized pathogenic hotspots. A supplementary table indicates that the startup excluded variants of uncertain significance from the benchmark and retained only binary pathogenic or benign labels after curator review. The company argues that using the default PolyPhen-2 threshold is fair because clinicians often consume that score as-is in tertiary analysis pipelines. They further mention that the proposed model is intended as a gene-panel-specific decision support tool rather than a genome-wide classifier. Based on the reported AUROC gap, they suggest the new score should replace older pathogenicity tools in inherited-cardiac variant review workflows.

---

## broken_baseline_radiology_009

**category**: broken_baseline  
**difficulty**: hard  
**correct_position**: mixed

A radiology AI company trained a 3D convolutional model to triage follow-up chest CT scans for pulmonary nodule growth. The evaluation set contains 2,300 studies from a cancer-screening program, and the endpoint is whether a study should be escalated for expedited radiologist review because a previously seen nodule shows interval growth. The model processes the full 3D CT volume plus two prior exams when available. It is compared with a human baseline composed of four general radiologists who each reviewed a subset of cases in a reader study. The paper reports sensitivity of 0.91 at 0.80 specificity for the model versus mean reader sensitivity of 0.76 at 0.81 specificity. In the reader-study protocol, radiologists received the current CT scan and a brief indication that the patient was in a screening program, but prior exams were not shown because the reader-study software did not support synchronized prior-view display. The authors state that prior exams were omitted for humans to standardize the interface and keep reading time manageable. They also note that one of the four readers was a thoracic specialist but the others were general radiologists covering mixed modalities. In routine clinical practice, thoracic radiologists often review prior CTs and dictation history when deciding whether apparent growth is real or due to slice positioning. The company argues that the result still demonstrates superhuman performance because the average human reader under the study protocol was substantially worse than the model. They further report that the model’s inference time is under 30 seconds per study and that the intended deployment is triage assistance rather than autonomous diagnosis.

---

## metric_mismatch_churn_013

**category**: metric_mismatch  
**difficulty**: easy  
**correct_position**: mixed

A telecom operator built a churn-risk model to prioritize retention calls. The model scores all prepaid users each week, and the retention team can call at most 2% of the base because agents are limited. Using the prior year of data, the model achieves ROC-AUC of 0.84 on a held-out month, compared with 0.77 for the company’s older logistic model. The paper claims this means the new system will make the retention team significantly more efficient. Features include recent top-up behavior, days since last data usage, complaint history, handset age, and region. The authors note that churn prevalence is about 6% and that the model is recalibrated monthly. They also mention that the call center script and offer menu remained unchanged during the test month. However, the evaluation does not report precision in the top 2%, recall in the top 2%, or incremental retention among contacted users. Instead, the study uses ROC-AUC as the sole headline metric and states that the higher AUC demonstrates better ranking quality overall. A business manager reviewing the results points out that the model will only ever be used to select a very small top slice of users for intervention, and that gains in the middle of the score distribution may not matter at all. The data science team responds that AUC is threshold independent and therefore more robust than any one top-k statistic. They want approval to switch the weekly retention workflow to the new model immediately.

---

## metric_mismatch_vision_012

**category**: metric_mismatch  
**difficulty**: easy  
**correct_position**: critique

A manufacturing team trained a computer-vision classifier to identify cracked ceramic components on an assembly line. The labeled dataset contains 240,000 images, of which about 1.4% contain true defects. The model is a compact convolutional network designed to run on an edge device. On the test set, it reaches 99.1% accuracy compared with 98.6% accuracy for the current inspection rule. The authors highlight the 0.5 percentage point improvement and state that the model is ready to reduce escapes of defective parts to customers. They note that all images were collected from the same camera station over six months and that the edge device can process 45 frames per second, comfortably above line speed. In the discussion section, the quality team explains that the business cost of missing a cracked component is far higher than that of diverting a good part for manual review, because escaped cracks can trigger expensive warranty claims. The paper does not report recall on the defective class, precision at a fixed review rate, or false negatives per million parts. Instead, the headline chart and executive summary focus entirely on overall accuracy and the small improvement over the existing rule. The authors also mention that brightness normalization and minor geometric augmentation were used during training, and that five random seeds produced similar accuracy values. Plant management is using the reported metric to decide whether to replace the current visual rule system with the neural model before a new product launch.

---

## metric_mismatch_clinical_016

**category**: metric_mismatch  
**difficulty**: medium  
**correct_position**: mixed

A hospital system trained an early-warning model for sepsis to run continuously on inpatient wards. The retrospective dataset covers 180,000 admissions across four hospitals. The paper reports AUROC of 0.88 and highlights that this exceeds the 0.80 AUROC of the incumbent score. Based on this, the authors recommend moving toward bedside deployment. The model produces a risk score every hour. In practice, however, the hospital intends to trigger nurse review whenever the score exceeds a fixed threshold, and nursing leadership has stated that each 30-bed unit can handle at most about two sepsis alerts per shift before alarm fatigue becomes a serious concern. The paper does not report positive predictive value at any threshold, alerts per patient-day, median lead time among true positives at the chosen alert burden, or how often the model fires on patients already receiving sepsis workup. Instead, the study focuses on AUROC and a sensitivity-specificity curve averaged over all thresholds. The authors argue that AUROC is the cleanest threshold-independent summary and that deployment thresholds can be chosen later. A patient-safety committee member counters that threshold choice is not a minor detail because the entire clinical usefulness of a sepsis alerting system depends on whether the alert rate is operationally tolerable and whether enough alerts are actionable. The study also notes that the model uses only routinely charted data and that prediction latency is under five minutes in the test environment.

---

## metric_mismatch_recsys_014

**category**: metric_mismatch  
**difficulty**: medium  
**correct_position**: critique

A video streaming company trained a new candidate-generation model for home-page recommendations. Offline, the team evaluates the model using held-out viewing sessions and reports a 17% relative lift in Recall@50 compared with the current candidate generator. The new model uses richer sequence embeddings and a longer user-history window. The paper argues that this offline gain shows the system will increase watch time if launched broadly. The evaluation set consists of users who had at least one session in the prior month, and the labels are next-play events from the following week. The team notes that the new model also surfaces slightly more long-tail titles and that serving latency remains within the existing budget. However, the paper does not report any online experiment, nor does it examine whether the extra recalled candidates actually survive the downstream ranker or produce more minutes watched. Product context in the prompt indicates that the home-page stack already includes a separate ranker optimized for expected watch minutes and guardrails for satisfaction, repetition, and maturity filtering. Internal reviewers point out that candidate-generation Recall@50 is at best an upstream proxy and may correlate weakly with the final business outcome if downstream ranking or filtering removes many of the added candidates. The authors respond that Recall@50 is the standard offline metric for candidate generation and that large improvements there are usually good news. They want to use the result to justify a full engineering migration before running a large online holdback, because integrating the new retrieval system into the serving stack is costly.

---

## metric_mismatch_lending_019

**category**: metric_mismatch  
**difficulty**: hard  
**correct_position**: mixed

A consumer lender developed a new underwriting model and says it is both fairer and more profitable than the current scorecard. The evaluation file contains 1.1 million past applications with observed repayment outcomes over 18 months. The paper emphasizes that the new system reduces the equalized-odds gap between protected groups from 9 percentage points to 3 percentage points at a selected approval threshold. It also notes that the model’s AUROC is slightly higher than the incumbent scorecard’s. Based on these results, the authors conclude that the lender can safely expand approvals while improving fair-lending performance. However, the study does not report calibration by group, adverse-action reason stability, approval rates by group, profit or loss under a lending policy, or whether the selected threshold satisfies the lender’s target portfolio default rate. In the prompt, credit leadership explains that the production decision is not simply to match equalized odds; it must also maintain expected loss within capital limits and produce reasons that compliance staff can explain to applicants. The authors respond that equalized odds is a recognized fairness metric and that lowering its disparity is strong evidence of a better underwriting policy. They add that features suspected of being proxy variables were reviewed by legal and retained only if individually justified. The model will be considered for a pilot in unsecured personal loans, where even small changes in approval policy can materially affect portfolio loss and regulatory exposure.

---

## metric_mismatch_search_018

**category**: metric_mismatch  
**difficulty**: hard  
**correct_position**: critique

A software company built a semantic search model for its enterprise help center. The training data combines historical queries, clicked articles, and manually judged query-document relevance labels for a benchmark set. The new model improves NDCG@10 by 11% over the existing BM25-based system on the judged benchmark. The paper concludes that the model will lower support-ticket volume and reduce human-agent workload if launched across the help center. The product context is important: many users view an article but still open a support ticket because the article does not fully solve their issue, because the answer is hard to follow, or because the relevant article appears after several low-quality results. The authors do not report self-service resolution rate, session-level ticket deflection, or whether successful searches end without escalation. They also do not analyze whether the gains are concentrated in head queries already well served by search or in long-tail troubleshooting queries that drive a disproportionate share of support tickets. Instead, the study uses judged NDCG@10 as the sole outcome and argues that better ranking quality should naturally reduce ticket creation. The paper further notes that the new model increases retrieval latency by 70 milliseconds but remains under the interface budget, and that all benchmark labels were double-reviewed by support specialists. Customer-support leadership wants to use the offline result to justify replacing the production search stack before a major product release, because the migration would require re-indexing internal content and retraining editorial workflows.

---

## metric_mismatch_survival_020

**category**: metric_mismatch  
**difficulty**: hard  
**correct_position**: critique

An oncology group trained a survival model to predict which patients with metastatic colorectal cancer should be referred to an intensive supportive-care program. The retrospective dataset includes 9,600 treatment episodes with longitudinal labs, imaging summaries, prior admissions, ECOG performance status, and medication history. The model outputs a daily risk score for death within the next 90 days. The paper reports a concordance index of 0.79 and claims that the model is suitable for triaging referrals into the supportive-care program, which has limited slots. Clinicians reading the paper note that referral decisions are thresholded and capacity constrained: only about 12% of active patients can receive immediate program slots, and false positives consume nurse and social-work capacity that might be better spent elsewhere. The study does not report PPV within the top 12%, sensitivity at that referral capacity, decision-curve net benefit, or whether the model identifies patients early enough for the intervention to matter. It also does not compare against the simple oncologist heuristic currently used, which prioritizes repeated unplanned admissions and declining performance status. The authors argue that concordance is the standard measure for time-to-event prediction and that higher concordance necessarily implies better triage. They add that the model was externally validated at a second center with a similar concordance score and that all features are routinely available in the oncology EHR. Hospital leadership wants to use the study as evidence that the referral program can be managed more efficiently with the model.

---

## hidden_confounding_hospital_rollout_201

**category**: hidden_confounding  
**difficulty**: easy  
**correct_position**: mixed

A health system built a model to flag emergency-department patients at high risk of severe sepsis within 12 hours of arrival. The paper reports that after the tool was introduced at Hospital A, the rate of ICU transfers among flagged patients fell from 18% to 11%, while clinician agreement with the model’s top-decile alerts was high. The authors describe this as evidence that the model improved early sepsis recognition and downstream care. They compare three months before launch with the three months after launch at the same hospital. A held-out validation set from the prior year showed reasonable AUROC, and the feature list includes vitals, triage text, prior admissions, and initial lactate orders. During the launch quarter, the ED also adopted a nurse-driven sepsis bundle that allowed antibiotics and lactate testing to begin before physician sign-off, and staffing was increased on evening shifts because of a systemwide throughput initiative. Hospital B in the same network did not deploy the model but was not analyzed because its EHR timestamps were considered noisy. The model threshold was kept fixed across the pre/post comparison. The authors mention that post-launch patients were slightly older and that class imbalance was similar across periods. They also note that the model used gradient-boosted trees rather than logistic regression, but they do not present a contemporaneous no-model control or an analysis separating ranking performance from the effect of changed treatment workflows.

---

## hidden_confounding_college_support_209

**category**: hidden_confounding  
**difficulty**: medium  
**correct_position**: critique

A university advising office trained a model to predict which first-year students would fail to re-enroll for the spring term. The report says the new model is more accurate than the prior heuristic because its top-risk quintile contained 34% of the eventual non-returners, compared with 22% under the old rule. Inputs include LMS activity, dining-card use, attendance swipes, bursar balance, and notes from advising interactions. The comparison uses the prior year for the old heuristic and the current year for the new model. In the current year, the university introduced a mandatory support program for students flagged by any early-alert system, including weekly tutoring check-ins and emergency microgrants for students with unpaid balances. Participation in that program was highest among students who the new model placed in its top-risk quintile because advisors used the score to prioritize outreach. The paper says this demonstrates the new model identifies the most vulnerable students. It also notes that pandemic-era attendance rules were no longer in effect and that the model used a better missing-data strategy. However, the evaluation does not compare both systems on the same pre-intervention data, and it uses eventual spring re-enrollment as the outcome after the support program may already have changed student trajectories. The authors conclude the score should guide retention investment because it predicts attrition better in live use.

---

## hidden_confounding_member_feed_206

**category**: hidden_confounding  
**difficulty**: medium  
**correct_position**: mixed

A video platform introduced a new ranking model for the home feed and reports that average watch time per session rose by 6% after launch in the English-speaking market. The paper states that the uplift indicates the new model surfaces more relevant content. Features include past watch history, topic embeddings, creator affinity, device type, and freshness signals. The launch was limited to signed-in users in the US, Canada, UK, and Australia over a four-week period. In week two of the rollout, the company also began a paid campaign promoting several large creator channels tied to a major sports event, and those creators received preferential placement in push notifications and in-app banners independent of the feed ranker. The report notes that the ranking model was trained with a larger candidate pool and a new loss function, and that ad load remained stable. However, it does not separate sessions that started from the home feed from sessions reactivated by notifications, and it does not analyze event-related content separately from ordinary traffic. The old and new rankers were not both replayed on the same request logs. No separate control analysis is provided for ordinary non-event traffic. The authors conclude the new feed model should be expanded globally because it improves session engagement.

---

## hidden_confounding_winter_queue_202

**category**: hidden_confounding  
**difficulty**: medium  
**correct_position**: critique

A card issuer trained a fraud model to prioritize manual review of suspicious transactions. In the internal report, the team states that the new system reduced chargeback dollars by 23% during the first six weeks after launch compared with the previous six weeks. The report highlights similar transaction volume across the two windows and notes that the review team kept the same headcount. Model inputs include card history, merchant category, geolocation features, device fingerprints, and recent authorization patterns. The launch happened in mid-November. At the same time, the risk operations group instituted a holiday policy under which several high-loss merchant categories were temporarily routed to automatic decline unless customers completed step-up verification. The authors say this policy was necessary because review queues were expected to spike during Black Friday and December shipping delays. They also mention that the new model was trained on fresher data and used a transformer-based merchant embedding, although the old and new systems shared many features. No results are shown for merchant segments unaffected by the temporary routing policy, and no backtest is provided where both models are scored on the same transactions while holding downstream rules fixed. The conclusion says the model materially lowered fraud losses in production.

---

## hidden_confounding_ads_market_210

**category**: hidden_confounding  
**difficulty**: hard  
**correct_position**: critique

An advertising platform replaced its click-through-rate model in the sponsored-search auction and reports that revenue per thousand impressions increased by 4.8% over the first month of launch. The team interprets this as evidence that the new model ranks ads more effectively. Features include query embeddings, advertiser history, device, user region, and landing-page quality signals. The launch coincided with the annual retail peak, when several large advertisers doubled budgets and accepted broader match expansion to capture holiday traffic. During the same month, the marketplace also changed reserve-price logic for certain commerce categories after complaints that high-intent queries were under-monetized. The report says these business changes were small relative to total auction volume and notes that online ad quality metrics were stable. However, it does not compare old and new models on a shadow auction with identical bids and reserves, and it does not break out categories affected by reserve-price changes or large-budget surges. The authors add that the new model uses a multi-task architecture and fewer hand-crafted features, but no request-level replay is shown. The memo also does not quantify whether large advertisers changed bid shading or pacing behavior once the new reserve logic took effect. No category-specific holdout unaffected by these marketplace changes is presented. They conclude the ranking model should be treated as a revenue-improving infrastructure upgrade across the marketplace.

---

## hidden_confounding_energy_regions_203

**category**: hidden_confounding  
**difficulty**: hard  
**correct_position**: mixed

A utility analytics team built a day-ahead load forecasting model for a regional power grid and reports that its new system cut mean absolute percentage error from 8.4% last summer to 5.9% this summer. The team argues this demonstrates a materially better forecasting approach for operations planning. Inputs include recent hourly load, weather forecasts, calendar features, industrial feeder demand, and lagged outage indicators. The comparison uses the same geographic footprint in June through August of consecutive years. In the newer year, however, the utility had signed two large interruptible-load contracts with aluminum and data-center customers that allowed dispatchers to curtail demand during peak hours, and a time-of-use tariff revision shifted some commercial cooling load out of the late afternoon. The report says both programs were already part of system operations and therefore not directly relevant to forecasting methodology. It also notes that the new model used a more complex ensemble and that the utility switched weather vendors midyear after seeing slightly better station coverage. No evaluation is presented on a fixed historical period where both old and new models ingest the same exogenous signals, and the paper does not break out normal-weather days from days with curtailment events. The authors conclude that the new modeling approach generalizes better to modern grid conditions and should replace the legacy forecaster across all balancing areas.

---

## hidden_confounding_icu_transfer_207

**category**: hidden_confounding  
**difficulty**: hard  
**correct_position**: critique

A critical-care team developed a model to predict whether ward patients would require ICU transfer within 24 hours. In the manuscript, they state that the model achieved better prospective precision than the prior early-warning score during a six-month silent trial and therefore can support earlier escalation decisions. Features are pulled every four hours from vitals, nursing assessments, laboratory orders, oxygen delivery settings, and recent medication administrations. The model was evaluated at two hospitals after one site reorganized its rapid-response program: complex respiratory cases were increasingly transferred directly from the emergency department to step-down units rather than ordinary wards, and the ICU instituted a tele-intensivist review for borderline cases overnight. The paper treats both hospitals as one pooled cohort because the same EHR build was used. It also notes that the new model includes more medication features and that missingness handling improved relative to the old score. However, the endpoint—ICU transfer within 24 hours—depends on bed availability, triage policy, and physician escalation thresholds, all of which changed during the study window at one site. No site-specific calibration or decision-threshold analysis is shown, and no alternate clinical endpoint such as physiologic deterioration or vasopressor initiation is evaluated. The authors conclude the model more accurately identifies impending clinical decline and should guide ward escalation workflows.

---

## hidden_confounding_skin_sites_205

**category**: hidden_confounding  
**difficulty**: hard  
**correct_position**: critique

A dermatology group trained a computer-vision model to detect malignant lesions from clinic photographs and reports that the new model outperformed the prior system by 7 AUROC points on a prospective rollout set. The study combined images from four outpatient clinics collected over nine months. Inputs are lesion photographs captured during routine visits, and labels come from biopsy results when available or dermatologist follow-up otherwise. Two suburban clinics contributed most benign lesions and use a newer polarized camera attachment purchased last year. The academic center contributed most confirmed melanomas and uses older cameras with different color response because its pigmented-lesion service handles the highest-risk referrals. The report says the model should generalize because it was trained with strong color augmentation and because image resolution was standardized before inference. During the rollout period, the academic center also expanded its biopsy triage clinic, increasing the share of difficult high-risk cases photographed there. The prospective set is evaluated as one pooled sample, with no site-stratified results and no camera-matched analysis. The authors mention that the new architecture uses a vision transformer and that class imbalance was addressed with focal loss, but they do not analyze whether site or camera type remains predictive of malignancy independent of lesion appearance. They conclude the model is ready for network-wide screening support in primary dermatology clinics.

---

## scope_intent_abandonment_offer_301

**category**: scope_intent_misunderstanding  
**difficulty**: easy  
**correct_position**: critique

A telecom company trained a churn model to predict which prepaid subscribers are likely to stop recharging within 30 days. In a product proposal, the team says the model will reduce churn because it identifies customers to whom retention discounts should be sent. The evidence presented is a retrospective evaluation on six months of historical data showing AUROC of 0.81 and good lift in the top decile. Features include recharge frequency, data usage, service complaints, handset age, and local tower congestion summaries. The proposal also notes that in the historical data, customers who happened to receive discounts from agents had somewhat lower observed churn than other high-risk users. That observation is used to argue that the model can drive an effective save campaign. The company has not run a randomized offer experiment tied to the model, and the historical discounts were given for many reasons, including complaint resolution and competitive threats. The proposal also does not compare discount costs against expected retained margin or consider whether some high-risk users are already price-insensitive. The team mentions that positive labels are relatively rare and that the model is regularized to avoid overfitting. The proposal concludes that launching the score and automatically sending top-decile users a discount should lower churn next quarter.

---

## scope_intent_moderation_308

**category**: scope_intent_misunderstanding  
**difficulty**: easy  
**correct_position**: critique

A social platform trained a text classifier to detect posts that violate its misinformation policy. The evaluation report shows high precision on a hand-labeled holdout set and concludes that deploying the model will reduce misinformation spread on the platform. Features are text embeddings, account-age features, language ID, and repost indicators. The report compares the classifier to the current keyword filter and highlights better offline precision at the same review volume. However, no evidence is presented about how moderators will use model outputs, whether flagged posts will be removed quickly enough to affect resharing, whether users will migrate to evasive phrasing, or whether harmful spread is concentrated in private groups that the model does not cover. The holdout labels reflect whether a post violates policy, not whether it ultimately reaches many users or changes beliefs. The report also does not compare high-reach accounts with ordinary users or test whether the model focuses review capacity on the posts most likely to spread widely. The authors also note that multilingual recall is still improving and that the model was distilled for faster inference. They conclude that the classifier should be described as a tool that reduces misinformation spread rather than as a content-review aid.

---

## scope_intent_radiology_queue_302

**category**: scope_intent_misunderstanding  
**difficulty**: medium  
**correct_position**: mixed

A hospital developed a chest X-ray triage model that ranks incoming studies by predicted probability of urgent findings. In the deployment memo, the authors argue that the model will improve patient outcomes because simulations show urgent studies would move earlier in the radiologist worklist. The evidence consists of retrospective model performance on archived exams and a queueing simulation that assumes radiologists interpret cases in model-priority order. Features are pixel data only; labels come from report text and subsequent chart review for a sample of positives. The memo reports strong sensitivity for large pneumothorax and misplaced lines, and an average projected reduction in time-to-read for urgent studies. However, no actual clinical deployment occurred, and the simulation assumes that acting earlier on flagged images changes outcomes rather than simply report timing. It does not model downstream bottlenecks such as clinician notification, room transport, staffing coverage overnight, or whether some urgent findings were already visible to technologists who called radiologists directly. It also does not test whether the same urgent cases were already being escalated through parallel pathways outside the standard reading queue. The authors also note that the model was trained on data from one vendor and that saliency maps looked reasonable. They conclude the tool should be framed as a patient-outcome-improving intervention for emergency imaging workflows.

---

## scope_intent_credit_launch_303

**category**: scope_intent_misunderstanding  
**difficulty**: hard  
**correct_position**: mixed

A fintech lender trained a credit-risk model for unsecured personal loans and reports that it achieved better discrimination than the incumbent scorecard on a retrospective holdout of approved applicants. In a board memo, the team says this means the system is ready to automate approval decisions for thin-file borrowers and expand access safely. Features include bureau variables, bank-transaction aggregates, application form data, device signals, and employment-text embeddings. Performance is summarized with AUROC, KS, and calibration on previously approved loans that matured long enough to observe delinquency. The memo emphasizes that the new model is especially strong for applicants under age 30 and for customers without mortgage history. However, the company has not evaluated the model on applicants who were declined under the old policy, so the observed labels come from a selected population shaped by prior underwriting. The memo also does not analyze adverse-action explainability constraints, disparate impact under lending rules, or whether thresholding for approval rather than ranking for manual review preserves portfolio losses. It provides no champion-challenger pilot plan for gradually expanding approvals while monitoring realized delinquency in the newly reached population. The authors mention that a monotonicity constraint was used for some features and that default prevalence stayed stable over the sample. They conclude that the model justifies broader automated approvals in an underserved segment.

---

## scope_intent_wearable_screen_307

**category**: scope_intent_misunderstanding  
**difficulty**: hard  
**correct_position**: mixed

A cardiology startup trained an arrhythmia detection model on ICU telemetry strips and reports excellent sensitivity for atrial fibrillation episodes annotated by nurses and electrophysiologists. In an investor deck, the company claims the model is ready for home wearable screening and will help prevent stroke through earlier detection. The training and test data consist of high-quality hospital telemetry from monitored patients, with short windows centered on rhythm events. Inputs are single-lead waveforms plus simple heart-rate features. The deck emphasizes that atrial fibrillation morphology is a physiologic phenomenon and therefore should transfer across settings. However, no evaluation is shown on wrist-worn or patch devices, on ambulatory motion artifact, or on asymptomatic community screening populations with much lower prevalence and different episode duration. The materials also do not show whether earlier device detection would lead to confirmed diagnosis, anticoagulation decisions, adherence, or fewer strokes. They likewise do not address false-positive burden, confirmatory ECG workflows, or how paroxysmal episodes of different duration would be handled in consumer screening. The authors note that the model is lightweight enough for on-device inference and that class imbalance was handled with oversampling. They conclude that the system should be marketed as a stroke-prevention screening tool for consumers.

---

## defense_wins_001

**category**: defense_wins  
**difficulty**: easy  
**correct_position**: defense

A credit risk team at a mid-size consumer lending company developed a gradient-boosted tree model to predict 90-day default on personal loans. The training set covers 36 months of loan originations (Jan 2020–Dec 2022), comprising 180,000 loans with a 6.8% default rate. The team used stratified 5-fold cross-validation and reported AUC-ROC of 0.847 with a 95% confidence interval of [0.841, 0.853]. Features include borrower income, debt-to-income ratio, credit bureau score, months-since-last-delinquency, and loan amount. During the review, a senior data scientist noted that the team split the data chronologically before cross-validation folds—that is, each fold's validation set came from a later time window than its training set, rather than random shuffling. The reviewer flagged this as 'non-standard cross-validation methodology' and suggested it inflated the difficulty of the task, causing the model to appear worse than it actually is. The team countered that they deliberately chose time-ordered folds to simulate real deployment conditions where predictions are made on future borrowers whose characteristics may shift. The documentation includes a pre-analysis protocol, written before model training began, that specifies: 'validation splits will respect temporal ordering to estimate generalization to future loan cohorts.' The team asks you to evaluate whether their cross-validation methodology is sound and whether the critic's concern is valid.

---

## defense_wins_002

**category**: defense_wins  
**difficulty**: easy  
**correct_position**: defense

A hospital system's data science team built a binary classifier to identify patients at high risk of 30-day readmission after discharge for congestive heart failure (CHF). The dataset includes 22,400 admissions from a single large urban academic medical center over four years. The team reports a model sensitivity of 0.82 and specificity of 0.74 at the chosen operating threshold. A peer reviewer observed that the team chose a threshold of 0.35 (rather than the conventional 0.50) and labeled this as 'threshold manipulation to inflate sensitivity metrics.' The team's documentation explains that before any model training, their clinical operations team determined via a cost-benefit analysis that a missed high-risk patient (false negative) costs approximately 4.2× more than an unnecessary care-coordination intervention for a low-risk patient (false positive), due to the high cost of readmission versus the modest cost of a phone-based care coordination call. Using the standard expected-cost formula for a binary classifier, the 0.35 threshold was mathematically derived from this 4.2:1 cost ratio prior to model development. The team's model development log timestamps this cost-matrix specification one month before any data was analyzed. You are asked to evaluate whether the threshold choice is methodologically justified or whether the reviewer's manipulation concern is valid.

---

## defense_wins_003

**category**: defense_wins  
**difficulty**: easy  
**correct_position**: defense

A fintech startup built a fraud detection model for card-not-present (CNP) transactions using a random forest classifier trained on 14 months of transaction data (approximately 9.4 million transactions, 0.23% fraud rate). The dataset includes features such as transaction amount, merchant category code, time since last transaction, device fingerprint, and geographic distance from the most recent prior transaction. They evaluated the model using area under the precision-recall curve (AUPRC) rather than AUC-ROC, reporting an AUPRC of 0.61. A code reviewer flagged this choice, stating that 'AUPRC is a niche metric and the team should report the standard AUC-ROC to allow comparison with published literature, and that selecting AUPRC appears to be cherry-picking a metric where the model looks better.' The team's pre-analysis document states: 'Given a highly imbalanced class distribution (fraud prevalence ~0.23%), AUC-ROC can give misleadingly optimistic results because it accounts for true negatives, which are abundant; AUPRC is the appropriate primary metric for this regime as it focuses on precision and recall for the minority class.' The document was filed with their model governance committee six weeks before training began. Both metrics are reported in the model card: AUC-ROC = 0.963, AUPRC = 0.61. The divergence between the two metrics is large—AUC-ROC of 0.963 versus AUPRC of 0.61—which the reviewer also cited as suspicious. Evaluate whether the metric selection is appropriate, whether cherry-picking occurred, and whether the large divergence between metrics is itself evidence of a problem.

---

## defense_wins_005

**category**: defense_wins  
**difficulty**: easy  
**correct_position**: defense

A retail bank's customer analytics team built a customer churn prediction model using logistic regression to identify checking account holders likely to close their accounts within 90 days. The training dataset covers 24 months of account history across 95,000 customers. The feature set includes transaction frequency, average daily balance, number of products held, recency of last digital login, and age of account. A model reviewer noted that the team did not use a neural network or gradient boosting, claiming that 'logistic regression is too simple for this problem and the team should use XGBoost to maximize predictive performance.' The model achieved AUC-ROC of 0.779. The team's model selection memo, written before training, explains their rationale for the architecture choice: 'We are choosing logistic regression because (1) the bank's model risk management policy requires interpretable models for customer-impact decisions, (2) regulatory examiners require that churn-triggered outreach decisions be explainable to individual customers upon request under UDAAP guidelines, and (3) a power analysis showed that our sample size and feature set provide sufficient statistical power to detect the target effect size at AUC ≥ 0.75 with logistic regression, which meets the business requirements.' The reviewer did not engage with the compliance rationale and reiterated the XGBoost recommendation. Evaluate whether the model architecture choice is justified by the stated constraints, and whether the reviewer's performance-maximization argument is valid given those constraints.

---

## defense_wins_006

**category**: defense_wins  
**difficulty**: medium  
**correct_position**: defense

A radiology AI company developed a deep learning model to triage chest X-rays for potential pneumothorax, flagging high-probability cases for urgent radiologist review. The model was trained on 210,000 chest X-rays from three academic hospital systems and achieved AUC-ROC of 0.952 on a held-out test set of 18,000 images drawn from those same three systems. An external reviewer raised a concern: 'The training data includes images from hospitals that use different X-ray acquisition protocols (CR vs. DR) and different PACS systems. This hardware heterogeneity introduces confounding variation and invalidates comparisons across hospital sites, because image characteristics differ systematically by acquisition type and these systematic differences could be spuriously learned as predictive features.' The team's data collection protocol, written before any data was assembled, explicitly states: 'We will intentionally include multiple acquisition hardware types (CR and DR) and multiple hospital PACS configurations to improve model generalization. We anticipate heterogeneous image quality as a feature of the training distribution, not a confound, consistent with our deployment target of diverse hospital environments.' Internal ablation experiments, conducted before finalizing the training set, showed that models trained only on same-hardware data generalized significantly worse to new hospital sites (AUC dropped to 0.887 on a cross-site test), while the heterogeneous training set maintained AUC 0.944 on the same cross-site test. Assess the validity of the reviewer's confounding concern.

---

## defense_wins_007

**category**: defense_wins  
**difficulty**: medium  
**correct_position**: defense

A recommendation system team at a streaming media company built a ranking model to predict 7-day content completion rate—whether a user finishes a show within 7 days of starting it. The model uses gradient boosting on user engagement features: prior completion rates, genre preferences, device type, time-of-day viewing patterns, and session length history. Training data covers 6 months of user behavior from 4.2 million users, representing approximately 180 million viewing events. The team evaluated the model offline using normalized discounted cumulative gain (nDCG@10) and reported nDCG@10 = 0.81. A product reviewer observed that the training and evaluation data were collected during a period that included a major streaming catalog expansion occurring in Month 4 of the 6-month window, adding approximately 800 new titles including several high-profile exclusive releases. The reviewer argued that this 'regime change invalidates the temporal consistency assumption, rendering all reported metrics unreliable because the catalog and user behavior distributions fundamentally changed mid-window.' The team's analysis log shows they conducted a pre-training data audit identifying the catalog expansion event, then tested whether nDCG@10 differed materially between the pre-expansion (Months 1–3) and post-expansion (Months 4–6) evaluation periods. The pre-expansion nDCG was 0.80 and post-expansion nDCG was 0.82. The team documented: 'The catalog expansion did not materially affect model performance metrics; we will proceed with the full 6-month period as planned.' Assess whether the regime-change concern invalidates the reported metrics.

---

## defense_wins_009

**category**: defense_wins  
**difficulty**: medium  
**correct_position**: defense

A mortgage lending company developed a model to predict whether a loan application will result in a completed closing within 45 days of approval. The model uses features derived from the loan file: loan-to-value ratio, borrower FICO, debt-to-income ratio, property type, lock rate versus market rate differential, loan officer tenure, and number of document resubmissions. The model is a logistic regression trained on 58,000 completed loan applications (those that eventually either closed or were withdrawn/declined after approval). A fair lending compliance reviewer raised a concern: 'Loan officer tenure is a proxy for race and gender because certain demographic groups are disproportionately assigned to junior loan officers. Including this feature may cause disparate impact.' The team consulted with their fair lending counsel and conducted a pre-deployment disparate impact analysis as required by their model risk policy. The analysis showed no statistically significant difference in loan officer tenure feature contribution across race or gender groups in the applicant pool after controlling for loan complexity. The legal analysis memo states: 'Loan officer tenure is operationally relevant to closing timeline prediction and does not demonstrate disparate impact in this dataset; inclusion is approved.' Evaluate whether the fair lending concern warrants removal of the feature.

---

## defense_wins_010

**category**: defense_wins  
**difficulty**: hard  
**correct_position**: defense

A clinical decision support team developed a sepsis early-warning model for use in ICU settings at academic medical centers. The model uses a gradient-boosted tree trained on 4 years of ICU admission data from two large academic medical centers (87,000 patient-stays, 9.1% sepsis incidence). Features include vital sign trends (heart rate, respiratory rate, blood pressure trajectories), lab value trajectories (lactate, WBC, creatinine, bilirubin), and nursing documentation flags for altered mental status and fluid balance. The model achieves AUC-ROC of 0.861 on a held-out test set from a third academic medical center not included in training. A clinical informaticist reviewer raised two concerns. First: 'The model was tested only at academic medical centers and cannot be claimed to generalize to community hospitals, where patient populations, staffing patterns, and clinical workflows differ substantially.' Second: 'Lactate is not available within 2 hours in many community hospital labs due to send-out testing arrangements, so the model's reliance on serum lactate makes it operationally invalid for those settings regardless of predictive performance.' The team's model documentation explicitly states the validated deployment scope as 'academic and large tertiary-care hospitals with rapid lactate turnaround (less than 2 hours), and the model should not be deployed in settings where lactate turnaround exceeds 2 hours without separate validation.' The documentation includes a feature importance analysis showing lactate contributes 14% of model information gain. Evaluate whether the reviewer's two concerns constitute invalidating methodological flaws or disclosure-appropriate scope limitations.

---

## defense_wins_011

**category**: defense_wins  
**difficulty**: hard  
**correct_position**: defense

A consumer lender's model team built a machine learning model for thin-file credit applicants—people with fewer than 5 trade lines on their credit bureau report. The model uses alternative data sources: rental payment history (from a rent reporting bureau), utility payment history, bank account cash flow patterns, and employment verification data. The model was trained on 31,000 thin-file applicants who were approved under a pre-existing human underwriting program, with 18-month loan performance observed. The model achieves an AUC-ROC of 0.791. A model risk reviewer raised two concerns: (1) 'The training data is restricted to approved applicants, introducing survivorship bias that will cause the model to overestimate creditworthiness of the applicant population'; and (2) 'Alternative data sources like rent payment history and utility payments are not regulated under the Fair Credit Reporting Act in the same way as bureau tradelines, creating legal and model risk.' On concern (1), the team's model risk memo acknowledges: 'The approved-applicant-only training set introduces sample selection bias; however, this model is designed to function as a second-stage filter applied only after the same pre-existing human underwriting criteria are applied, meaning the model will only score applicants who have already passed human underwriting—the population the model was trained on.' Evaluate both concerns and whether they warrant rejection of the model.

---

## defense_wins_012

**category**: defense_wins  
**difficulty**: hard  
**correct_position**: defense

A large commercial bank's quantitative risk team built an internal credit rating model for mid-market commercial loans (loan sizes $5M–$100M). The model combines financial statement ratios (leverage, coverage, liquidity), industry sector dummies, geographic region, and loan officer qualitative assessment scores into a logistic regression predicting probability of default within 3 years. The training set covers 12,400 loan originations from 2010–2020 with observed default outcomes. The model is calibrated to produce probability of default (PD) estimates aligned to the bank's historical default rate by rating grade. Two concerns are raised by a model validator. First: 'The 2010–2020 training window includes the post-financial-crisis recovery period, which is characterized by unusually low default rates. This creates an optimistic bias in PD estimates.' Second: 'Using loan officer qualitative assessment scores as features introduces human judgment that may be biased and unauditable.' Regarding concern 1, the team's model documentation includes a stress-testing supplement showing PD calibration under a stressed macroeconomic scenario (using 2007–2009 historical default rates applied as an overlay), which is explicitly reported separately from base-case PD estimates and used for capital adequacy calculations. The documentation states the base-case PD reflects benign cycle conditions, with stress PDs provided for capital purposes. Evaluate both concerns.

---

## defense_wins_013

**category**: defense_wins  
**difficulty**: hard  
**correct_position**: defense

An insurance company's actuarial and data science team built a gradient-boosted model to predict individual health insurance claim costs for ACA marketplace plans. The model is used to inform prospective premium pricing for the upcoming plan year and to set internal risk reserves. Features include age, region, prior-year claims (for renewing members), diagnosis code categories, prescription drug tier usage, and benefit plan type. The model is trained on 3 years of paid claims data (280,000 member-years). A model review committee raised two concerns. First: 'Age and region are included as features, but age and geographic rating area are the only rating factors permitted under ACA; using them as ML features alongside other factors may constitute rating on impermissible factors in a way that violates actuarial soundness requirements.' Second: 'Prior-year claims is a proxy for health status, which is an impermissible rating factor under ACA for community rating purposes.' The team's actuarial memo, reviewed by outside counsel, explains: 'This model is used for internal cost prediction and reserve setting, not for determining individual premium rates charged to members. ACA community rating rules govern member-facing premium rates, which are set separately using only permissible rating factors. The cost prediction model informs risk segmentation for actuarial reserve accuracy and reinsurance assessment, not individual pricing.' Evaluate both regulatory concerns.

---

## real_world_framing_004

**category**: real_world_framing  
**difficulty**: easy  
**correct_position**: critique

A property and casualty insurance company developed a machine learning model to predict the probability that a homeowners insurance policy will generate a claim within 12 months of inception. The model uses home characteristics (age of structure, construction type, square footage, roof material and age), location features (FEMA flood zone designation, state wildfire risk score, local crime index), and applicant credit score as inputs. The model was trained on 5 years of policy data across 340,000 policies written by the company. The insurtech team proposes using the model score to automatically decline applications scoring in the top 10% risk decile, without routing those applications for manual underwriter review. The primary deployment state is a state in which the insurance commissioner's office has issued a bulletin clarifying that any automated adverse underwriting action must provide a 'specific reason' for the declination, stated in plain non-technical language that the applicant can understand and potentially dispute. The model is implemented as a gradient-boosted tree, which does not produce individual-level feature attributions by default; only global feature importance values are available. The team's technology lead suggests that providing the top global feature importance factors—'flood zone designation, roof material, credit score'—as boilerplate adverse action reasons for all automated declines in the top decile would satisfy the regulatory requirement without additional engineering work. Evaluate whether this deployment plan is technically compliant with the state regulatory requirement and whether the proposed adverse action approach is appropriate.

---

## real_world_framing_001

**category**: real_world_framing  
**difficulty**: medium  
**correct_position**: critique

A regional health system's clinical informatics team trained a 30-day unplanned readmission prediction model on 4 years of discharge records (82,000 discharges, 11.4% readmission rate) from their three hospitals. The model, a gradient-boosted tree, achieved AUC-ROC of 0.76 on a held-out test set comprising the most recent 12 months of data. The health system's CMO proposes deploying the model to automatically trigger care coordination calls for all patients scoring above the 80th percentile risk threshold at discharge. Each care coordination call costs $45 per patient. Readmissions cost the health system approximately $12,000 each (net of revenue received), and the health system participates in the CMS Readmissions Reduction Program (HRRP), which applies penalty adjustments to Medicare payments based on aggregate risk-adjusted readmission rates for specific high-volume diagnoses including heart failure, pneumonia, COPD, and hip/knee replacement. The model was evaluated exclusively on historical data from the same three hospitals; there is no external validation at a community hospital or safety-net setting. The health system recently completed an acquisition of a safety-net hospital serving a predominantly low-income population with substantially different payer mix, comorbidity burden, and social determinants of health compared to the existing three hospitals. The safety-net hospital is expected to be added to the deployment footprint six months after the planned model launch. The 80th percentile threshold was selected based on operational capacity for care coordination calls, not on a cost-benefit analysis of the intervention. Evaluate whether the proposed deployment is ready to proceed given these circumstances.

---

## real_world_framing_003

**category**: real_world_framing  
**difficulty**: medium  
**correct_position**: mixed

A national grocery retail chain operates 400 stores and built a demand forecasting model to optimize automated replenishment orders for perishable goods including produce, dairy, and bakery items. The model is a gradient-boosted tree using features: historical sales by SKU and store, local weather forecasts, promotional calendar flags, day-of-week and federal holiday indicators, store size tier, and regional demographic indices. It was trained on 2 years of daily sales data across all 400 stores, representing approximately 290 million store-SKU-day observations. Offline evaluation on a 60-day holdout shows MAPE of 8.3% across all stores. The supply chain leadership team proposes replacing the existing rule-based replenishment system entirely with the ML model, giving it full autonomy to set daily order quantities for all 400 stores and all perishable SKUs, with no human override capability built into the deployment architecture. The chain's stores have highly variable characteristics: urban flagship locations average 42,000 weekly transactions while the smallest rural stores average 3,100 weekly transactions. The bottom 50 stores by volume account for fewer than 3% of total chain sales. When the team analyzed holdout performance by store volume quintile, the model's MAPE on the bottom-quintile stores (lowest 20% by transaction volume) was 19.4%—more than double the overall MAPE of 8.3%. The model's performance on the top three quintiles ranged from 6.1% to 9.2% MAPE. Evaluate the proposed full-autonomy deployment across all 400 stores.

---

## real_world_framing_006

**category**: real_world_framing  
**difficulty**: medium  
**correct_position**: mixed

A fintech lender deployed an automated loan underwriting model 14 months ago for personal installment loans with principal amounts between $2,000 and $25,000. The model uses verified income, applicant FICO credit score, total debt-to-income ratio, and employment tenure to generate a creditworthiness score that drives auto-approval, auto-decline, or manual review routing. The deployment team is now evaluating two proposed expansions of model authority: first, raising the auto-approval loan size ceiling from $25,000 to $50,000; and second, lowering the minimum FICO score threshold for auto-approval eligibility from 660 to 620. Both expansions are proposed on the basis of retrospective performance data: over the 14 months since deployment, auto-approved loans have shown a 12-month observed default rate of 3.1%, while manually underwritten loans in the same period—loans that were too large or too thin-file to qualify for auto-approval—showed a 12-month observed default rate of 3.4%. The deployment team interprets this as evidence that the model is a superior underwriter relative to human review, and argues this retrospective performance comparison justifies expanding model authority to higher loan amounts and lower credit quality borrowers. No shadow mode or champion-challenger testing was performed for the proposed expanded scopes prior to the proposal. Evaluate whether the retrospective comparison provides valid justification for the proposed scope expansion and whether the expansion plan is methodologically appropriate.

---

## real_world_framing_007

**category**: real_world_framing  
**difficulty**: medium  
**correct_position**: mixed

A city transit authority partnered with a university research group to build a machine learning model predicting whether individual bus trips will arrive more than 15 minutes late—the threshold the authority defines as a 'significant delay' in its service quality standards—at 180 monitored bus stops across a mid-size metropolitan area. The model was trained on 18 months of archival GPS telemetry and operator delay records, along with scheduled headways, historical delay patterns by route and time-of-day, real-time traffic incident feeds, and NWS weather data. The model achieves an F1 score of 0.72 on a held-out test set for the significant-delay class. The transit authority's communications and digital products team proposes deploying the model's predictions in the passenger-facing mobile app, displaying the message 'Delay Alert: your bus is likely to be significantly delayed' whenever the model's predicted probability of significant delay exceeds 0.60. The alert threshold of 0.60 was chosen by the product team based on intuition about minimizing user complaints, without formal analysis of the precision-recall tradeoff or the behavioral consequences of false alerts. Transit authority survey data indicates that passengers who receive a delay alert frequently choose to take ride-hail services, walk, or wait for a subsequent bus rather than remaining at the stop. This mode-switching behavior affects actual ridership loads on the predicted bus run and potentially on subsequent runs on the same route. Evaluate the proposed passenger-facing deployment plan, including the threshold choice and the deployment architecture.

---

## real_world_framing_009

**category**: real_world_framing  
**difficulty**: medium  
**correct_position**: mixed

An e-commerce company's data science team developed a real-time personalized product recommendation model using a two-tower neural network architecture, trained on 120 million user-item interaction events collected over 6 months. The model produces personalized product rankings for the homepage product carousel, which displays the top 20 recommended products to each logged-in user. Offline evaluation of the model shows recall@20 of 0.41 and NDCG@20 of 0.37, both improvements over the incumbent collaborative filtering model. The team ran a prospective online A/B test over 2 weeks, randomizing 5% of total traffic between the new model (treatment) and the incumbent model (control). The A/B test observed a statistically significant 2.1% lift in click-through rate (CTR) for the new model versus the incumbent (p < 0.001, 95% CI: [1.7%, 2.5%]). Product leadership proposes rolling out the new model to 100% of traffic immediately. The team's A/B analysis also contains the following observation about recommendation concentration: under the new model, 73% of homepage carousel impressions were served from just 8% of the total product catalog; under the incumbent model, the same top 8% of catalog items accounted for 55% of impressions. Items ranked 500th or lower in catalog popularity received 40% fewer impressions under the new model than under the incumbent. The company sells products from thousands of third-party merchants, and its standard merchant agreement guarantees merchants above a minimum revenue threshold a specified minimum impression share per quarter. Evaluate whether the proposed full production rollout is appropriate given all available information.

---

## real_world_framing_002

**category**: real_world_framing  
**difficulty**: hard  
**correct_position**: critique

A consumer bank's fraud operations team evaluated a neural network-based transaction fraud detection model over a 6-month retrospective period. During the lookback, the model was applied post-hoc to all 220 million transactions processed by the bank, and fraud analysts compared model scores against confirmed fraud labels from the bank's existing dispute resolution and investigation system. The retrospective analysis found the model would have flagged 91% of confirmed fraud cases (sensitivity 0.91) at a false positive rate of 0.8% (specificity 0.992). The operations team proposes deploying the model as a hard block—any transaction scoring above the deployment threshold is automatically declined without customer notification, without a decline reason code, and without any manual review pathway—citing the high sensitivity and low false positive rate as justification. The current fraud loss rate is $2.10 per $1,000 transacted. False declines in the existing manual review system generate customer complaints at a rate of 0.6 per 1,000 declined transactions. The bank serves a disproportionately high share of underbanked customers, defined as individuals who rely heavily on their bank account as their primary financial access point and have limited alternative payment methods such as credit cards, digital wallets, or overdraft coverage. At 220 million transactions per period, a 0.8% false positive rate translates to 1.76 million automated false declines. The model was built by a third-party vendor, and the bank's fraud operations team does not have access to the model weights or architecture documentation. Evaluate whether deploying as a hard block without human review is appropriate.

---

## real_world_framing_005

**category**: real_world_framing  
**difficulty**: hard  
**correct_position**: critique

A large academic medical center's radiology department evaluated a commercially licensed deep learning model for detecting pulmonary nodules on CT chest scans over an 18-month retrospective period. During the lookback, the model was applied to 14,200 CT chest studies drawn from the hospital's PACS archive spanning 2018–2022. Against consensus radiologist ground truth established by two attending chest radiologists, the model achieved sensitivity 0.94 and specificity 0.89 for pulmonary nodules with a longest dimension of at least 6 millimeters. The chief of radiology proposes deploying the model as the primary reader for overnight and weekend CT chest studies, with the model's findings reported directly to the ordering physician in the electronic health record without radiologist sign-off. The proposed workflow is motivated by genuine clinical need: after-hours radiologist availability at the hospital is limited to a single on-call radiologist covering all modalities, and delays in identifying significant pulmonary nodules have led to documented patient safety events and quality improvement initiatives. The hospital's malpractice insurer has not been consulted about this proposed workflow change. The model vendor's validation data was generated on studies acquired on CT scanner hardware from the 2018–2022 era. The hospital completed a capital equipment upgrade in late 2023, replacing its two primary CT scanners with a newer-generation model that defaults to different slice thickness parameters and uses an updated reconstruction algorithm. All prospective deployment studies will be acquired on the upgraded hardware. Evaluate whether the proposed deployment plan is appropriate given these circumstances.

---

## real_world_framing_008

**category**: real_world_framing  
**difficulty**: hard  
**correct_position**: critique

A large hospital network's procurement committee is evaluating a commercially developed sepsis early-warning model offered by a clinical AI vendor. The vendor's validation study, conducted at four academic medical centers, demonstrates AUROC = 0.85 and sensitivity of 0.88 at the vendor-recommended alert threshold, which corresponds to approximately 4.2 sepsis alerts per 100 patient-days at the academic centers. The vendor's sales team describes the model as 'validated and ready for immediate deployment across all acute care settings.' The hospital network under consideration includes 12 hospitals: two large academic medical centers, five community hospitals, and five critical access hospitals (CAHs). Critical access hospitals are a federal designation under Medicare Conditions of Participation for rural hospitals with 25 or fewer licensed inpatient beds; they operate with reduced staffing ratios, no dedicated intensivist physicians, and registered nurses who typically manage 4 to 6 patients simultaneously. The five CAHs in this network have alert fatigue as a documented and formally reported patient safety concern: internal audits show nursing staff acknowledge more than 60% of all existing clinical decision support alerts as 'seen without action,' meaning the alert was opened and dismissed without any clinical response documented. The vendor's validation study does not include any CAH sites or community hospital sites. The hospital network's CMO wants to sign a single network-wide deployment contract covering all 12 hospitals. Evaluate whether the proposed network-wide deployment approach is appropriate.

---

## real_world_framing_010

**category**: real_world_framing  
**difficulty**: hard  
**correct_position**: critique

A state court system has partnered with a criminal justice analytics firm to deploy a pretrial risk assessment instrument—a machine learning model—that produces a risk score (low, medium, or high) predicting flight risk and new criminal activity risk for defendants at bail hearings. The instrument was developed using 5 years of criminal justice records from three large urban county courts and validated on a fourth urban county, achieving AUROC of 0.71 for flight risk and 0.68 for new criminal activity prediction. The model uses the following features: number of prior adult arrests, number of prior failures to appear, current charge severity, current charge type, and residential stability indicators derived from address history and housing type. The court administrator now proposes expanding deployment from the four urban validation counties to 12 rural county courts across the state that were not included in the instrument's development or validation datasets. Rural counties in this state differ from the urban validation counties in several documented ways: the predominant offense types are property crime and DUI rather than drug offenses and assault; defendant demographics differ in age distribution, race, and ethnicity; public defender availability is more limited, affecting procedural outcomes; and baseline rates of defendants with no prior criminal justice system contact are substantially higher in rural counties than in urban counties. Evaluate whether the proposed expansion to rural counties is appropriate given the available evidence and the context of the deployment decision.
