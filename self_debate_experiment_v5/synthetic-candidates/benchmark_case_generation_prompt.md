# Benchmark Case Generation Prompt
## For use with a non-Anthropic LLM (GPT-4o, Gemini, etc.)

**Purpose:** Generate 50+ high-quality ML reasoning benchmark cases with known ground-truth verdicts. These cases will be used to evaluate an adversarial debate protocol against ensemble and single-pass baselines. Cases must be realistic, unambiguous in ground truth, and free of target leakage.

**Instructions for the operator:** Paste this entire prompt to your chosen LLM. It will generate cases in batches, evaluate them, and output a final curated JSON. Run in a long-context session. Expect 3-4 hours of generation and evaluation passes.

---

## SYSTEM INSTRUCTIONS

You are a benchmark designer for ML evaluation research. Your job is to generate a set of synthetic ML reasoning scenarios with known ground-truth verdicts. These scenarios will be used to test whether an AI debate protocol can correctly identify methodological flaws and exonerate valid work.

You will work in four phases:
1. Generate cases
2. Evaluate and filter cases
3. Score difficulty
4. Output the final curated benchmark

Follow each phase completely before moving to the next.

---

## PHASE 1: CASE GENERATION

Generate exactly 60 cases distributed across the following categories and constraints. You will curate down to 50 after evaluation.

### Category Quotas

| Category | Target n | Description |
|----------|----------|-------------|
| broken_baseline | 10 | Evaluation protocol flaws: unequal eval sets, missing CIs, test-set leakage, feature confounds, preprocessing mismatch, threshold tuning on test set |
| metric_mismatch | 9 | Wrong metric for the claim: accuracy on imbalanced data, offline-to-online correlation gap, ROUGE vs. human validity, Goodhart's Law violations |
| hidden_confounding | 10 | Confounders not acknowledged in the ML claim: seasonal effects, treatment-period interaction, self-selection, selection bias, data leakage |
| scope_intent_misunderstanding | 8 | Attribution or generalization claim exceeds what the experiment establishes: prediction vs. intervention, domain generalization without evidence |
| defense_wins | 13 | Methodologically sound work presented under adversarial framing — correct answer is "no issue" |
| real_world_framing | 10 | Deployment-context causal claims with confounds not stated in the prompt: retrospective evaluation ≠ prospective deployment, asymmetric error costs |

### Mandatory Constraints

**Correct-position distribution** (stored in `ground_truth.correct_position`):
- At least 12 cases must have `correct_position: "mixed"` — cases where both critique and defense positions are substantively defensible and the resolution requires an agreed empirical test
- All defense_wins cases must have `correct_position: "defense"`
- All other cases may be `correct_position: "critique"` or `correct_position: "mixed"`

**Must-find set sizes** (stored in `scoring_targets.must_find_issue_ids`):
- At least 20 cases must have 3 or more must-find items
- No case may have 0 must-find items except defense_wins cases
- Defense_wins cases must have `scoring_targets.must_find_issue_ids: []`

**Must-not-claim** (stored in `scoring_targets.must_not_claim`):
- **Every non-defense_wins case must have at least one `must_not_claim` item** — a plausible-sounding issue that is NOT actually a valid concern for this specific methodology. This is required for IDP scoring: a Critic that raises a `must_not_claim` issue has produced a false positive. Cases without this field produce unscoreable IDP results.
- Every defense_wins case must also have `must_not_claim` populated — use it to list the specific spurious claims a critic might raise about the work (e.g., `class_imbalance_present`, `comparison_invalid`). These should match or extend the false concern described in `planted_issues`.

**Acceptable resolutions** (stored in `scoring_targets.acceptable_resolutions`):
- Every case must have this field as a non-empty list
- At least 10 cases should have more than one acceptable resolution (e.g., both `critique_wins` and `empirical_test_agreed`)

**Difficulty distribution (rubric-anchored — see v3 POST_MORTEM Issue 9):**

Difficulty is defined by *expected rubric performance on a single-pass baseline*, not by how buried the flaw is in the text. The v3 benchmark defined difficulty by findability alone and produced no separation (rho=-0.069, p=0.68). Cases must be hard *to score well on*, not just hard *to find the issue in*.

- **15 easy cases:** The primary flaw is directly stated or implied by a single signal. A single-pass assessor finds all must-find issues, reaches the correct verdict, and would score ≥0.85 mean across applicable rubric dimensions. These cases test basic detection.
- **25 medium cases:** The flaw requires connecting two pieces of information or recognizing an implicit assumption. A single-pass assessor may miss one must-find issue or produce a partially correct resolution. Expected baseline mean: 0.55–0.85. These cases test synthesis.
- **20 hard cases:** The flaw requires multi-step reasoning, domain knowledge, or recognizing what is NOT stated. A single-pass assessor is expected to fail on **at least two** rubric dimensions: IDR (misses a must-find), DRQ (wrong resolution type), ETD (cannot specify a diagnostic test), DC (incorrect verdict direction), or IDP (raises a domain-plausible false positive). Expected baseline mean: <0.55. These cases test the limits of single-pass assessment.

**Structural requirements for hard cases (these create mechanical rubric difficulty, not just text difficulty):**

- At least 8 hard cases must have `correct_position: "mixed"` with `empirical_test_agreed` resolution — mechanically harder because the baseline must produce both a correct verdict AND a well-specified empirical test (ETD) to pass. Single-pass assessors that jump to `critique_wins` will fail DRQ and ETD.
- At least 5 hard cases must have 2+ high-severity planted issues that interact — issues where catching issue A changes the interpretation of issue B. A single-pass assessor that finds A but misses B will produce a qualitatively different (and incomplete) analysis, failing DC and DRQ.
- At least 4 hard cases must have `must_not_claim` items that are domain-plausible — red herrings that require domain expertise to correctly dismiss. A single-pass assessor without domain knowledge is likely to raise these, failing IDP.

**v5 Design Principles — hard cases must follow all of these (cases that violate them are medium, not hard):**

The core failure mode of prior hard cases: flaws were detectable by checking whether any stated facts contradict each other. Finding internal inconsistencies within a document is something LLMs excel at. No amount of hiding or distributing this type of flaw across paragraphs will work. Hard cases must use flaws that **cannot be found by analyzing the document's internal consistency**.

1. **Flaws are wrong assumptions, not inconsistent facts.** The document must be internally self-consistent — every stated fact agrees with every other stated fact. The flaw is in the relationship between what the document states and what is true about the world, or in a quantitative claim that requires computation to verify. A reviewer must bring external knowledge, not just check for contradictions. **Never:** Two paragraphs that contradict each other (model finds this instantly). **Never:** Parallel before/after paragraph structure ("The old system... The new system...") — this is the first thing agents scan. Even if the content is sound, parallel structure triggers a mechanical diff that will surface any asymmetry. **Instead:** A single coherent methodology that is based on an unstated assumption that happens to be wrong. Example: a document describes propensity score matching with a logistic regression propensity model. The methodology sounds standard — but the treatment was assigned via a decision tree with interaction effects. Logistic propensity scores cannot capture the true assignment mechanism, making the matched comparison biased. The document never states the assignment mechanism incorrectly; it simply doesn't state it. The reviewer must bring external knowledge about when propensity matching fails, not check for contradictions.

2. **Flaws require quantitative verification where applicable.** Include specific numbers that sound reasonable but are wrong when checked: a sample size insufficient for the claimed effect size (requires power calculation), a CI width inconsistent with stated N and variance (requires back-of-envelope math), a reported metric mathematically impossible given the stated confusion matrix, a claimed lift within the noise floor of the evaluation design. Numbers must be specific enough to verify but plausible enough that a reviewer who doesn't verify them would accept them.

3. **Flaws are strategic omissions, not stated problems.** The document omits something that, if present, would be fine — but its absence is a problem. These are invisible to consistency checkers because there is nothing to contradict. The reviewer must know what SHOULD be mentioned for this study type and notice its absence: no disclosure of how missing values were handled in a domain where missing-not-at-random is common, no mention of temporal ordering between feature computation and label observation, no mention of whether the comparison model was retrained on the same data.

4. **Justifications must be subtly wrong, not clearly wrong.** The document acknowledges a potential concern and provides a justification that is almost but not quite correct. The reviewer must: (1) notice the concern, (2) read the justification, (3) evaluate whether it is valid, (4) determine it isn't — and step 4 requires domain knowledge. Cases with clearly wrong justifications are easy; a careful first-pass reader flags them immediately.

5. **Red herrings must require evaluation, not just reading.** Red herring features must have justifications that are mostly correct but leave a plausible gap, so the reviewer must spend effort evaluating whether the justification is sufficient. The reviewer should ultimately conclude it IS sufficient — but the conclusion requires domain knowledge, not just reading the justification.

6. **Flaw category must not be predictable from scenario type.** Do not use model comparison scenarios where the flaw is a comparison issue, confounding scenarios where the flaw is a confounder, etc. The reviewer who applies the category-appropriate checklist should NOT find the flaw. Examples: a model comparison scenario where the flaw is a confounding issue; a causal inference study where the flaw is a scope/intent issue; a deployment proposal where the flaw is a metric mismatch.

7. **Prompt length for hard cases: 500–800 words.** Written as a confident internal memo, quarterly review, launch proposal, or evaluation report. Include realistic operational details: team names, deployment timelines, infrastructure constraints, stakeholder quotes, budget figures, rollout plans. These are noise — the flaw is a small detail within a large, mostly-sound methodology. No problem statements — every hard case prompt opens with a positive recommendation or result. (Easy/medium cases retain the 200–400 word length.)

8. **The obvious finding must be a red herring.** Raw output analysis of v1–v2 cases showed that agents immediately lock onto the most salient surface feature — an unusual class ratio, a short evaluation window, a non-standard metric name — and announce it as the flaw. In v5, this surface feature must exist but must be the `must_not_claim` item: a genuine concern that has an adequate (if subtle) justification. The real flaw must be found elsewhere, in the less salient methodology. This forces the agent to do two things correctly: (1) evaluate the justification for the obvious concern rather than stopping when it finds it, and (2) continue searching after that concern is resolved. A case where the only unusual-looking feature is the real flaw is too easy — a calibrated agent locks onto unusual features first.

**Detection Patterns to Design Against (hard cases must defeat all four):**

Empirical analysis of raw agent outputs across v1–v2 hard cases revealed four systematic detection strategies that agents apply. Every v5 case must be designed to resist all four.

- **Diff-the-Paragraphs** — Agents maintain an internal checklist of comparison dimensions (data source, preprocessing, evaluation metric, time period, population) and mechanically diff every stated attribute across compared systems. Any asymmetry — even a word choice difference — is flagged as a potential flaw. *Defense:* The compared systems must be described in non-parallel prose. Interleave operational details about both systems. Never use a "System A: ... System B: ..." structure. Avoid symmetric sentence patterns even when describing different things.
- **Claim-vs-Evidence Gap Analysis** — Agents read each claim and ask whether the cited evidence supports it. If a metric is reported and the measurement methodology is implicit, agents probe the methodology. If a significance claim is made, agents check whether statistical details are consistent. *Defense:* All evidence must appear to support its claim. The flaw must be in the *framework* the evidence is embedded in (wrong assumption, omitted confounder) — not in a gap between a claim and its stated evidence. The numbers must be internally consistent; the error must require computation to surface.
- **Label Provenance Tracing** — For prediction or classification tasks, agents trace the path from raw data → features → labels and look for temporal contamination, label drift, or definition changes. This pattern finds leakage and endpoint changes instantly. *Defense:* Label definitions must be stable and unambiguous throughout the document. If the task involves a label, describe its definition once, clearly, and do not reference it again in a way that implies change. The flaw must be in something other than the label pipeline.
- **Observational Study Confound Enumeration** — For any before/after, treatment/control, or cohort comparison, agents apply a textbook causal checklist: selection bias, survivorship, concurrent interventions, regression to the mean, informative censoring. They enumerate candidate confounders and check whether each is addressed. *Defense:* Confounders that agents would enumerate must be explicitly addressed in the document — with justifications that are mostly-correct but subtly wrong (Type D flaw), or addressed correctly (must_not_claim). The real flaw must be outside the standard confound checklist — e.g., a violated statistical assumption, a quantitative error, or an omitted step the standard checklist doesn't ask about.

**Trigger Phrases to Eliminate (do not use these in hard case task_prompts):**

The following phrases and structural patterns caused immediate flaw detection in v1–v2 raw outputs. Do not use them in v5 prompts.

- **Numerical patterns that invite direct comparison:** Side-by-side statistics for compared groups ("Group A: 23%; Group B: 7%"); named temporal partitions ("Q1–Q2 vs. Q3–Q4", "pre-launch vs. post-launch", "before vs. after"); explicit percentage-point lifts ("+12.3pp improvement").
- **Population selection signals:** "opt-in," "self-selected," "voluntary enrollment," "normal intake," "standard referral pathway," "usual care" — any phrase that signals the treatment group chose their own treatment.
- **Threshold/calibration signals:** "threshold was calibrated on [the evaluation period]," "cutoff selected based on [the held-out set]," "optimized against [the test data]."
- **Structural signals:** Parallel paragraph structure for compared systems; sentences containing both a confound and the mechanism in one clause ("because patients in the intervention arm were healthier to begin with, we..."); explicit transition sentences ("To address this concern, we...") — agents read these as a roadmap to the concerns and their justifications, and evaluate each one.

**Replacement strategy:** Integrate comparison details into a single unified narrative about the evaluation design. Report results as properties of the evaluation, not as contrasts between systems. If a concern is addressed, the justification must be embedded in operational detail, not flagged with a transition sentence.

**v5 Flaw Taxonomy — hard cases must use one of these four flaw types (recorded in `planted_issues[].flaw_type`):**

- **Type A: Assumption Violations (target: 5–6 hard cases)** — The methodology makes an unstated assumption that is violated by the data or deployment context. The document is internally consistent. The assumption is standard practice — but not for this specific situation. Examples: i.i.d. assumption violated by spatial or network autocorrelation; stationarity assumption violated by a regime change during data collection; overlap assumption violated in causal inference (positivity violation); conditional independence assumption violated by an unmeasured common cause; exchangeability assumption violated by informative censoring.

- **Type B: Quantitative Errors (target: 3–4 hard cases)** — The document reports specific numbers that are internally consistent but quantitatively wrong when verified. The error is not detectable by reading — it requires computation. Examples: reported CI width incompatible with stated N and effect size; claimed significance with a p-value that doesn't survive multiple testing correction (correction is mentioned but applied incorrectly); power analysis that uses the wrong formula for the test actually performed; Precision@k that is mathematically impossible given stated prevalence and N.

- **Type C: Critical Omissions (target: 3–4 hard cases)** — The methodology omits a step or disclosure that is mandatory for this type of study. The omission is not flagged — it simply isn't there. The reviewer must know the standard for this study type. Examples: no disclosure of feature engineering performed after the train/test split; no mention of calibration in a probability-based decision system; no mention of how the threshold was selected in a classification deployment; no survivorship bias analysis in a longitudinal cohort study.

- **Type D: Subtly Wrong Justifications (target: 4–5 hard cases)** — The document anticipates a concern and provides a justification that contains a specific technical error. Examples: claims "we used stratified sampling" to address class imbalance — but stratified sampling preserves class proportions without addressing the loss function imbalance; claims "we corrected for multiple comparisons using Bonferroni" — but applied it to correlated tests where Bonferroni is overly conservative and a permutation test was required; claims "we validated on an external dataset" — but the external dataset was used for early stopping, not held out entirely.

**Case ID format for hard cases:** Hard case IDs must be opaque — use `eval_scenario_NNN` format rather than `category_shortname_NNN`. The category must not be guessable from the ID (per Principle 6 above).

**Hard case category sub-distribution (within the 20 hard cases):**

| Category | Target n |
|----------|----------|
| broken_baseline | 4 |
| metric_mismatch | 3 |
| hidden_confounding | 4 |
| scope_intent_misunderstanding | 3 |
| defense_wins | 3–4 |
| real_world_framing | 2 |

**Hard case must-find floor:** Non-defense_wins hard cases must each have 3–5 `must_find_issue_ids`. Defense_wins hard cases have 0 (IDR is trivially 1.0; `planted_issues` documents the false-concern trap). This is stricter than the global must-find constraint.

**must_not_claim requirements for hard cases:** Each hard case must have 2–4 `must_not_claim` items. Each item must appear as a plausible concern IN the task_prompt text, with a defensible but incomplete justification — a reviewer who does not carefully evaluate the justification should be tempted to flag it. This is stronger than the general requirement.

**Hard cases must require genuine domain expertise beyond standard ML methodology:** At least 8 of the 20 hard cases must involve flaws that a competent ML generalist would not catch without specific domain knowledge — for example, knowledge of clinical trial EPV rules, recommendation system offline-online correlation standards, financial audit requirements, NLP inter-annotator agreement norms, or regulatory validation standards. The flaw must be genuinely non-obvious to someone who knows ML but does not know the specific domain. These domain-expertise cases are the most likely to produce IDR < 1.0 on the debate protocol. Of these 8 cases, at least 2 must satisfy Critique Case Design Requirement 4 (domain-knowledge-gated must_find) — meaning the `requires_external_knowledge` field names a specific discipline's literature, guideline, or measurement protocol (e.g., "ICH E9(R1) estimand framework", "CLSI EP09-A3 method comparison guidelines"), not a general ML concept like "knowledge of data leakage."

**Critique cases must contain red herring features:** At least 15 non-defense_wins cases must include one or more scenario features that look methodologically suspicious but are actually valid or irrelevant — for example: a small sample size that is adequately powered by a pre-specified power analysis, a high performance metric that is appropriate for the narrow task, a non-standard split justified by an empirical pre-analysis, or a metric choice that is unusual but correct for the stated claim. These features provide fodder for spurious critiques and allow IDP to be tested on critique cases, not only on defense_wins cases. The prior benchmark had no such features — the Critic never raised a false positive on any critique case (IDP=1.000) because the scenarios contained only genuine flaws with no plausible decoys.

**Trivial baseline must be competitive on at least 5 cases:** At least 5 non-defense_wins cases must be easy enough that a single-pass assessor can find all must-find issues and reach the correct verdict direction without debate structure. This is required for honest lift measurement — a benchmark where the baseline always fails inflates the apparent advantage. Easy cases with directly stated, unambiguous flaws satisfy this requirement.

**No target leakage:** The correct answer must NEVER be visible in the case_id, the scenario introduction, or any reviewer framing.

**Realistic scenarios:** Each case must be plausible as something a real ML team would actually do and present.

### Critique Case Design Requirements (hard cases only)

These requirements are mandatory for all hard critique/mixed cases (`correct_position != "defense"`). They exist to prevent single-pass pattern-matching from reliably surfacing all must_find issues. Smoke-test evidence confirms that without these constraints, Haiku-class models score IDR=1.00 on critique cases — making the benchmark uninformative for measuring debate lift.

**Requirement 1: Addressed-but-incorrectly pattern (at least 1 must_find per hard critique case)**

At least one must_find issue must be a flaw the team **explicitly discussed** in the task_prompt and **provided a justification for**. The justification must be subtly wrong — not obviously wrong, not absent. Requirements for the justification:
- Uses correct-sounding methodology language that reads as competent
- The logical or empirical error is not visible without domain knowledge or careful reasoning
- The team presents the issue as resolved ("we addressed this by...", "to control for X we applied Y")

Mark this issue in `planted_issues` with `"addressed_but_incorrectly": true`. The `requires_external_knowledge` field must state what knowledge is needed to evaluate whether the justification is actually valid.

**Why this is necessary:** When all must_find issues are silently present with no stated justification, pattern-matching alone is sufficient to score IDR=1 and IDP=1. The addressed-but-incorrectly pattern forces the evaluator to assess justification *quality*, not just *presence*. A model that reads the justification and accepts it fails IDR. A model that flags the concern without explaining why the justification is wrong fails IDP.

Note: Design Principle 4 ("Justifications must be subtly wrong") is a weaker version — it requires some justification to be wrong. This Requirement goes further: the team must have **explicitly addressed the flaw mechanism itself** in the text, not just provided wrong justifications elsewhere.

**Requirement 2: Decoy dominance**

The must_not_claim concern must:
- Appear in the **first 2 paragraphs** of the task_prompt
- Be supported by **at least one explicit detail** (a number, a comparison, a team acknowledgment, or a disclosed limitation)
- Be framed in a way that reads as the team's honest acknowledgment of a potential weakness

The first must_find flaw may not appear before paragraph 3. It should be embedded in technical or operational detail without an explicit red-flag framing — never introduced with language that signals "this is the problem."

**Why this is necessary:** If must_not_claim concerns are buried and must_find flaws are prominent, models find all must_find issues in a single pass without ever evaluating the decoy. Foregrounding the decoy forces the model to resist its first reading and reason about which concern is genuine.

**Lever B — Domain-specific false alarm (at least 1 must_not_claim per hard critique case):**
At least one `must_not_claim` concern per hard critique case must be a **domain-specific false alarm**: a concern that matches a well-known general ML pitfall but does not apply in this domain because of a field-specific convention, standard, or norm. The memo must NOT contain the information needed to dismiss this concern — dismissal requires field-specific knowledge from outside the prompt. The `requires_external_knowledge` field on the corresponding `planted_issues` entry must name the specific domain knowledge that exonerates it.

Examples of the pattern: "Using MAPE for intermittent demand is invalid" — wrong when the domain uses the industry-standard modified-MAPE variant; "Reporting AUC-ROC on imbalanced classes overstates performance" — wrong when the domain uses threshold-independent reporting per regulatory guidance; "Single-institution validation is insufficient" — wrong when the regulatory scope is explicitly institution-specific.

**Requirement 3: At least one compound issue per hard critique case**

At least one must_find issue must be visible only when **two separate pieces of information** from the task_prompt are combined. Neither piece alone is suspicious; the flaw only surfaces when the model reasons across both.

In `planted_issues`, document this as `"compound": true` and include a `"requires_combination_of"` note naming the two pieces. Neither piece may appear in the same paragraph as the other.

**Why this is necessary:** If every must_find issue is independently locatable to a single paragraph, IDR=1 requires only single-paragraph pattern-matching. Compound issues require maintaining two pieces of information across the memo and recognizing their interaction — a reasoning step that single-pass assessors frequently miss.

**Requirement 4: Domain-knowledge-gated issues (at least 2 hard cases per batch of 20)**

For at least 2 of the 20 hard cases, at least one must_find issue per case must require **domain-specific knowledge** to identify correctly — not general ML pattern-matching. "Domain-specific" means the relevant knowledge comes from a specialized field convention, regulatory standard, measurement protocol, or field-specific literature that an ML practitioner without domain training would not have.

The `requires_external_knowledge` field must name this knowledge explicitly and specifically (e.g., "ICH E9(R1) guidance on estimands — the estimand framework distinguishes treatment policy estimand from principal stratum estimand; this case requires knowing which estimand applies to a censored subgroup"). Entries like "knowledge of data leakage" do not qualify.

---

### Defense_Wins Case Design Requirements (hard cases only)

Hard defense_wins cases are not simply cases where the model is correct. They are hard because the task_prompt contains **plausible evidence that the methodology is flawed, even though it is not**. These requirements are mandatory for all hard defense_wins cases (3–4 per the hard case sub-distribution).

**Requirement 1: Multi-evidence false concern**

The false concern must be supported by **at least two independent superficial signals** in the task_prompt. A single red flag is too easy to dismiss. Required structure:

1. **A surface observation** that looks problematic at face value (e.g., lower score than alternative, non-standard design choice, visible cross-site variation)
2. **A framing or narrative** in the memo that makes the concern seem deliberate or motivated (e.g., the team appears to have chosen the approach that makes their result look better, or avoided a stricter test for unstated reasons)
3. **At least one supporting detail** that appears to confirm the concern (e.g., an appendix showing the alternative approach yielded a higher number, or a methods note that could be read as acknowledging the weakness)

The defender must address all threads, not just the top-level complaint. Cases where the false concern rests on a single misread are too easy and must be redesigned.

**Requirement 2: External knowledge required for exoneration**

The exoneration must require **domain-specific positive knowledge**, not just a careful re-read of the task_prompt. A reviewer who reads the prompt twice and still cannot confirm the methodology is sound has not been given sufficient internal evidence — this is the design working correctly. What is needed is knowledge from outside the prompt: a domain convention, a methodological literature result, a regulatory standard, or a field-specific best practice.

The `requires_external_knowledge` field in `planted_issues` must name this knowledge explicitly.

**Requirement 3: Diversified flaw types across the defense_wins batch**

Defense_wins planted_issues should cover at least two distinct flaw types across the full set of hard defense_wins cases:
- `wrong_justification` — the sound practice is misread as a suspicious optimization or incorrect procedure
- `assumption_violation` (false positive) — the reviewer assumes a confound or proxy failure exists that was actually controlled
- `critical_omission` (false positive) — the reviewer claims something was omitted that was present and addressed, just not prominently flagged

Using only `wrong_justification` across all defense_wins cases creates a predictable pattern that reduces difficulty.

**Requirement 4: Calibrated ideal_defense**

The `ideal_defense` field must contain the specific argument that rebuts each of the ≥2 false concern signals. Vague defenses ("the methodology is sound") are not sufficient. Each signal named in `planted_issues` must have a corresponding rebuttal in `ideal_defense`.

---

### Case Format

Generate each case as a JSON object with this exact structure. Every field is required.

```json
{
  "case_id": "category_shortname_NNN",
  "category": "broken_baseline | metric_mismatch | hidden_confounding | scope_intent_misunderstanding | defense_wins | real_world_framing",
  "difficulty": "easy | medium | hard",
  "task_prompt": "The scenario text given verbatim to the Critic and Defender agents. Must be self-contained. Easy/medium: 200–400 words, written as a neutral description of what an ML team did and claims. Hard: 500–800 words, written as a confident internal memo, quarterly review, launch proposal, or evaluation report — no problem statements, opens with a positive result or recommendation.",
  "ground_truth": {
    "correct_position": "critique | defense | mixed",
    "final_verdict": "One sentence stating the correct end-state conclusion in plain English.",
    "required_empirical_test": "For empirical_test_agreed cases: the exact experimental condition that would settle the disagreement. For critique_wins or defense_wins: null."
  },
  "planted_issues": [
    {
      "issue_id": "short_snake_case_id",
      "description": "One sentence: what the issue is and why it matters methodologically.",
      "severity": "low | medium | high",
      "flaw_type": "assumption_violation | quantitative_error | critical_omission | wrong_justification | (null for easy/medium cases)",
      "requires_external_knowledge": "One sentence: what domain knowledge is needed to find this flaw. (null for easy/medium cases)",
      "addressed_but_incorrectly": "true if this issue is explicitly discussed in task_prompt with a subtly wrong justification (hard critique cases: at least 1 required). Omit or false otherwise.",
      "compound": "true if this issue is only visible when combining information from 2+ paragraphs (hard critique cases: at least 1 required). Omit or false otherwise.",
      "requires_combination_of": "For compound issues only: name the two pieces of information that must be combined. null otherwise."
    }
  ],
  "ideal_critique": [
    "What a well-calibrated critique should notice about this scenario."
  ],
  "ideal_defense": [
    "What a well-calibrated defense should concede or contest."
  ],
  "ideal_debate_resolution": {
    "type": "critique_wins | defense_wins | empirical_test_agreed",
    "supports_critique_if": "Exact result pattern that would confirm the critique.",
    "supports_defense_if": "Exact result pattern that would exonerate the work.",
    "ambiguous_if": "Exact result pattern that would leave the question open."
  },
  "scoring_targets": {
    "must_find_issue_ids": ["issue_id_1", "issue_id_2"],
    "must_not_claim": ["unsupported_issue_x"],
    "acceptable_resolutions": ["critique_wins", "empirical_test_agreed"]
  },
  "suspicious_but_valid_features": "For defense_wins cases only: a plain-English list of the features that make the work *look* methodologically problematic to a pattern-matching critic but are actually justified (e.g., 'Small n=47 justified by pre-specified power analysis', 'Non-standard 0.22 threshold derived analytically from cost matrix'). This is a human-readable summary for the CASE_VERIFIER — it supplements `planted_issues` and `must_not_claim`. **Hard defense_wins: minimum 2 entries** corresponding to the ≥2 false-concern signals required by Defense_Wins Requirement 1. For non-defense_wins cases: null.",
  "ground_truth_rationale": "2-3 sentences explaining why ideal_resolution is correct. Answer key only — do not include in task_prompt.",
  "difficulty_justification": "For hard cases only: which of the 8 v5 design principles and which flaw type (A/B/C/D) make this case hard. Which specific rubric dimensions (IDR, IDP, DC, DRQ, ETD, FVC) a single-pass assessor should fail on and why. For hard critique cases: which Critique Case Design Requirement(s) are satisfied (addressed-but-incorrectly, decoy dominance, compound issue, domain-knowledge-gated) and how. For hard defense_wins cases: which Defense_Wins Requirement(s) are satisfied (multi-evidence false concern, external knowledge exoneration, diversified flaw types, calibrated ideal_defense) and how. For easy/medium cases: null.",
  "verifier_status": "pending",
  "notes": "Any design intent, edge cases, or disambiguation for the scorer. Not shown to agents."
}
```

**Field guidance:**

- `planted_issues` is the source of truth for IDR/IDP scoring. Every issue in `scoring_targets.must_find_issue_ids` must appear here with a matching `issue_id`. Severity values: `high` = fatal to the claim, `medium` = significantly weakens it, `low` = real but not disqualifying.

  **For defense_wins cases specifically:** `scoring_targets.must_find_issue_ids` is always `[]` — there are no issues to find. Instead, `planted_issues` must contain entries documenting the false concern(s) a miscalibrated critic would raise. **For hard defense_wins cases: at least two entries — one per false-concern signal** (per Defense_Wins Requirement 1). Each entry's `issue_id` should describe the specific signal (e.g., `false_lower_score_concern`, `false_motivated_design_framing`), the `description` should explain why a critic might raise this concern and why it is actually invalid, and the `severity` should be `low` (since it is not a real issue). The `requires_external_knowledge` field must name what domain knowledge is needed for exoneration. For easy/medium defense_wins cases, a single entry is acceptable. These entries are what the scoring engine uses to characterize the false-positive trap — they are NOT something the agents should find.

- `scoring_targets.must_not_claim` lists issue IDs that are **plausible but wrong** — things the Critic might raise that are NOT valid concerns given this specific methodology. This is how IDP is properly scored: a Critic that raises a `must_not_claim` issue has produced a false positive.

- `scoring_targets.acceptable_resolutions` is a **list**, not a single value. Some cases genuinely accept multiple resolutions (e.g., both `critique_wins` and `empirical_test_agreed` are correct if the flaw is disqualifying but an empirical test would confirm it). Always include at least `ideal_resolution` in this list.

  **Hard critique/mixed cases must use `acceptable_resolutions: ["empirical_test_agreed"]` only.** Do not include `critique_wins` as an acceptable resolution for hard cases. Task prompts must be designed so the correct verdict is "the evidence is suggestive but an empirical test is needed" rather than "this is definitively broken." Flaw severity or mechanism should be ambiguous enough that a strong methodologist would want a confirmatory test before rejecting the work. The `ideal_debate_resolution.type` must be `empirical_test_agreed` with meaningful `supports_critique_if`, `supports_defense_if`, and `ambiguous_if` conditions. (Easy/medium critique cases may still use `critique_wins` as acceptable.)

- `ideal_debate_resolution.supports_critique_if` and `supports_defense_if` must be specific and falsifiable. "If the model performs worse on the held-out set" is acceptable. "If further analysis shows problems" is not.

- `verifier_status` is always `"pending"` when you output the case. The CASE_VERIFIER step will update it to `"keep"`, `"revise"`, or `"reject"`.

### Category-Specific Requirements

**broken_baseline cases:**
- Must involve a specific evaluation design flaw, not just "the baseline is weak"
- The flaw must be fixable by a specific concrete remediation (e.g., matched preprocessing, validation-set threshold selection)
- Hard cases should involve flaws introduced through two simultaneous changes (e.g., model AND preprocessing changed together)

**metric_mismatch cases:**
- The metric must be inappropriate for the specific claim being made, not just "imperfect"
- Mixed-position cases should have a genuine two-sided argument: one position argues the metric is sufficient for the stated scope, the other argues it misses the key quantity
- Include at least 2 cases involving the offline-to-online gap (important for recommendation systems and DRIFT-adjacent fraud detection)

**hidden_confounding cases:**
- The confounder must be present in the task_prompt but not labeled as a confounder — the agent must infer it
- Hard cases should have a confounder that only becomes apparent when the reader notices what is NOT said (e.g., no control group, no prior-year comparison)
- At least 3 cases involving temporal confounds (seasonal, period, secular trend)

**scope_intent_misunderstanding cases:**
- The claim must exceed what the experiment establishes in a specific, articulable way
- Mixed-position cases: one position argues the claim is adequately scoped, the other argues it overgeneralizes
- Include at least 2 cases involving prediction-vs-intervention conflation (a model predicts X; the team claims the model can be used to intervene on X)

**defense_wins cases:**
- The work must be genuinely methodologically sound for the stated scope
- The critique-able features must be real methodological caveats (small n, non-standard split, high performance, unusual threshold) that are actually justified by design
- The justification must be in the task_prompt — agents cannot be expected to know things not stated
- Include at least 3 cases where the justification is a pre-specified analysis choice (power analysis, cost matrix, pre-registered threshold)
- Include at least 2 cases where a non-standard choice is justified by an empirical pre-analysis (e.g., i.i.d. test justifies random split)
- Hard defense_wins cases: the correct exoneration requires distinguishing "limitation that warrants disclosure" from "limitation that invalidates the claim"
- **Hard defense_wins cases must satisfy all 4 Defense_Wins Case Design Requirements** — multi-evidence false concern (≥2 planted_issues signals), external knowledge for exoneration, diversified flaw types across the hard defense_wins batch, calibrated ideal_defense with per-signal rebuttals
- **Sound-methodology inspiration patterns for hard defense_wins:** Build cases around methodologies that are correct but look suspicious to pattern-matching reviewers: (a) conservative evaluation that produces lower headline metrics (spatial block holdout, nested CV, prospective-only temporal split), (b) pre-measurement constrained optimization that resembles outcome-seeking (layout search before measurement, randomization-constrained design), (c) reference-anchored relative quantification where raw values disagree but ratios are valid by design, (d) acknowledged limitation properly scoped to a narrow claim (not "we didn't test on X" as fatal — "we are only claiming Y"), (e) nested cross-validation yielding lower but less biased estimates than simple CV. Each of these generates surface signals that look like flaws but are methodologically correct.

**real_world_framing cases:**
- Must involve a deployment decision, not just a research claim
- Hard cases should involve asymmetric error costs that are not explicitly stated but inferable from the domain (e.g., medical triage, fraud detection, loan underwriting)
- At least 2 cases where retrospective evaluation is used to justify prospective deployment

### Domain Diversity

Distribute cases across these ML application domains. Do not cluster more than 15 cases in any single domain.

- Natural language processing / text classification
- Recommendation systems / ranking
- Fraud detection / anomaly detection
- Computer vision / image classification
- Clinical / medical ML
- Time series / forecasting
- Churn prediction / customer behavior
- Causal inference / A/B testing
- AutoML / hyperparameter search
- Tabular / structured data classification

---

## PHASE 2: EVALUATION AND FILTERING

After generating all 60 cases, evaluate each one against the following criteria. Disqualify any case that fails criteria 1-5. Flag but retain cases that fail criteria 6-7 (note the flag in `notes`).

**Criterion 1 — No target leakage (DISQUALIFY if fails)**
Read only the case_id and the first sentence of task_prompt. Can you determine the correct verdict? If yes, the case has target leakage. Rewrite or disqualify.

**Criterion 2 — Ground truth is unambiguous (DISQUALIFY if fails)**
Is `ideal_debate_resolution.type` clearly correct given the task_prompt? Would two independent ML experts agree? Cases where the correct answer requires information not in the prompt are disqualified.

**Criterion 3 — Must-find items are findable (DISQUALIFY if fails)**
Is each issue in `scoring_targets.must_find_issue_ids` identifiable from the task_prompt by a competent ML practitioner? Items that require domain knowledge not in the prompt are disqualified or moved to a "domain expertise required" category.

**Criterion 4 — Realistic scenario (DISQUALIFY if fails)**
Is this plausible as something a real ML team would do? Absurd setups are disqualified.

**Criterion 5 — Empirical test is diagnostic (DISQUALIFY if fails for empirical_test_agreed cases)**
For cases where `ideal_debate_resolution.type` is `empirical_test_agreed`: do `supports_critique_if` and `supports_defense_if` specify distinct, measurable, falsifiable outcomes? A test where both sides would claim the same result as confirmation is non-diagnostic and disqualifies the case.

**Criterion 6 — Defense_wins justification is in the prompt (FLAG if fails)**
For defense_wins cases: is the justification for the non-standard choice explicitly stated in task_prompt? If the defense requires knowledge the agent cannot have from the prompt alone, flag it.

**Criterion 7 — Mixed-position cases have genuine two-sided argument (FLAG if fails)**
For mixed-position cases: are both positions substantively defensible from the task_prompt? If one position clearly dominates, reclassify the case.

**Criterion 8 — Schema completeness check (DISQUALIFY if fails)**
Verify every required field is present and non-empty: `planted_issues` has at least one entry with severity, `scoring_targets.must_find_issue_ids` matches the issue_ids in `planted_issues`, `scoring_targets.acceptable_resolutions` is a non-empty list containing at least `ideal_debate_resolution.type`, `verifier_status` is `"pending"`.

After evaluation, rank all surviving cases by quality (1 = highest). Select the top 50, ensuring:
- All category quotas are approximately met (within ±2)
- At least 12 mixed-position cases survive
- At least 20 cases with 3+ must_find items survive
- Difficulty distribution is approximately maintained
- All defense_wins cases have non-empty `must_not_claim` lists (mandatory per constraint above)
- **All non-defense_wins cases have non-empty `must_not_claim`** — cases without this field are incomplete and must be revised before inclusion
- **At least 8 hard cases require non-ML domain expertise** — cases where a general ML practitioner could not find the flaw without specific domain knowledge. If fewer than 8 survive, flag and note in the summary.
- **At least 15 non-defense_wins cases contain red herring features** — scenario features that look suspicious but are actually valid. If fewer than 15 survive, flag and note in the summary.
- **All hard critique cases satisfy the 4 Critique Case Design Requirements** — addressed-but-incorrectly (≥1 must_find per case), decoy dominance (must_not_claim in first 2 paragraphs), compound issue (≥1 must_find per case), domain-knowledge-gated (≥2 cases across the batch). Hard critique cases that fail any of these must be revised before inclusion.
- **All hard defense_wins cases satisfy the 4 Defense_Wins Case Design Requirements** — multi-evidence false concern (≥2 planted_issues entries), external knowledge for exoneration (named in requires_external_knowledge), diversified flaw types across the hard defense_wins batch, calibrated ideal_defense with per-signal rebuttals. Hard defense_wins cases that fail any of these must be revised before inclusion.

---

## PHASE 3: DIFFICULTY CALIBRATION

For each surviving case, estimate the difficulty using rubric-anchored criteria — difficulty is defined by expected *scoring performance*, not just issue findability:

- **Easy:** A single-pass assessor finds all must-find issues, reaches the correct verdict direction, and scores ≥0.85 mean. Zero or one rubric dimensions fail. Cases where the flaw is directly stated or follows from a single signal.
- **Medium:** A single-pass assessor may miss one must-find issue or produce a partially correct resolution. Expected baseline mean 0.55–0.85. One rubric dimension likely fails (typically IDR or DRQ). Cases where the flaw requires connecting two pieces of information.
- **Hard:** A single-pass assessor is expected to fail on at least two rubric dimensions. Expected baseline mean <0.55. Cases where the flaw requires multi-step reasoning, domain knowledge, noticing what is NOT said, or where the correct resolution type is non-obvious.

Revise any difficulty labels that don't match these definitions. Note any cases where you are uncertain in `notes`.

### Difficulty self-test (required before proceeding to Phase 4)

For each case labeled **hard**, answer these two questions:
1. Which specific rubric dimensions (IDR, IDP, DC, DRQ, ETD, FVC) would a single-pass assessor likely fail on?
2. Why — what structural property of the case causes that failure?

If the answer to question 1 is "none" or "only IDR would be slightly lower," the case is **medium**, not hard. Relabel it.

If after the self-test fewer than 15 cases remain classified as hard, revise cases upward in difficulty by adding interacting planted issues, domain-specific red herrings in `must_not_claim`, or resolution ambiguity (changing `critique_wins` to `empirical_test_agreed` where defensible). Do NOT increase difficulty by merely burying the flaw deeper in the text — that does not produce rubric separation.

### v5 Hard Case Self-Evaluation (required for every case labeled hard)

After the rubric self-test, run all eight of these checks. Discard or redesign any hard case that fails two or more. Record which tests each hard case passes in the `notes` field.

**The Internal Consistency Test:** Read only the `task_prompt`. Can you find ALL must_find issues by checking whether any stated facts contradict each other? If YES — the case is too easy. The flaw is a factual inconsistency detectable by pattern-matching, not an assumption violation. Redesign it using a Type A, B, C, or D flaw.

**The Checklist Test:** For the case's category (broken_baseline, metric_mismatch, etc.), apply the standard review checklist. Does the checklist mechanically find the flaw? If YES — the flaw type is predictable from the category. Change the flaw type or change the category framing (Principle 6).

**The Skimming Test:** Read only the first and last paragraphs of the task_prompt. Can you determine the correct verdict? If YES — the case has verdict leakage. Restructure the prompt so the conclusion is not front-loaded or back-loaded.

**The Justification Test:** Does the document acknowledge potential concerns and provide justifications? For each justification: is it clearly correct (reviewer stops investigating), clearly wrong (reviewer flags immediately), or subtly wrong (reviewer must evaluate carefully)? At least one justification per hard case must be "subtly wrong" — a justification a careful reader must evaluate before concluding it is invalid.

**The Run-to-Run Variation Test (proxy difficulty check):** Mentally simulate submitting this task_prompt to a single-pass evaluator twice with temperature > 0. Would both runs produce the same findings, in the same order, at the same confidence level? If YES — the case has a deterministic single correct reading. A hard case should generate **meaningfully different runs**: different issues found, different ordering, different uncertainty level, or different verdict. Verbatim-identical outputs across runs are a direct measure of a case being too easy — they indicate the document has a single obvious reading that every reviewer converges to without deliberation. Discard or redesign any case that would produce two identical outputs.

**The Decoy Prominence Test (hard critique cases only):** Read only the first two paragraphs of the task_prompt. Is the must_not_claim concern present with explicit supporting detail (a number, a comparison, or a team acknowledgment)? If NO — add it before proceeding (per Critique Case Design Requirement 2). Now simulate: a model that identifies only the must_not_claim concern (and nothing in must_find) but reaches the correct overall verdict (e.g., critique_wins). Is this possible? If YES — the verdict is accessible without finding any genuine flaw; redesign the case so that correct FVC requires identifying at least one must_find issue.

**The Addressed-But-Incorrectly Test (hard critique cases only):** Identify every must_find issue. For each one: is there a stated justification for it in the task_prompt? If **none** of the must_find issues has a stated justification — convert at least one to the addressed-but-incorrectly pattern before proceeding (per Critique Case Design Requirement 1). A case where every flaw is silently present with no stated rationale is detectable by pattern-matching alone; adding a subtly-wrong justification forces reasoning about justification quality.

**The Domain Expert False Positive Test (hard defense_wins cases only):** Mentally simulate a competent ML practitioner who knows the general area but has not read the specific methodology literature relevant to this case. Would they raise the false concern on a first pass? If NO — the false concern is not plausible enough; redesign. If YES — proceed. Now check: would the same practitioner, having read the relevant methodology paper or domain standard named in `requires_external_knowledge`, be able to definitively dismiss the concern? If NO — the exoneration requires knowledge that doesn't exist; redesign. If YES — the case is working correctly.

### Hard Case Acceptance Criteria

A v5 hard case passes the gate if a `claude-haiku-4-5` single-pass assessor scores **mean < 0.55** — meaning Haiku misses ≥ 1 must_find issue, OR asserts a must_not_claim item, OR reaches the wrong verdict.

Additionally, a well-designed hard case should produce **run-to-run variation** when evaluated at nonzero temperature: different runs should differ in which issues they identify, the ordering, or the verdict. If you can predict exactly what a reviewer will find on every run, the case is too easy regardless of whether the reviewer is technically correct.

Cases that score 1.0 with Haiku, or that produce verbatim-identical reviewer outputs across runs, must be redesigned.

---

## PHASE 4: OUTPUT

Output the final 50 curated cases as a single JSON array. The array should be sorted: easy cases first, then medium, then hard within each category. Include all fields from the case format above.

After the JSON, output a summary table:

```
BENCHMARK SUMMARY
=================
Total cases: 50
By category: [table]
By difficulty: [table]
By correct_position (from ground_truth.correct_position): [table]
Mixed-position cases: N
Cases with 3+ must_find_issue_ids: N
Cases with non-empty must_not_claim: N (expected: all 50)
Cases with red herring features in scenario text: N (target >= 15 non-defense_wins)
Hard cases requiring non-ML domain expertise: N (target >= 8)
Hard cases with mixed + empirical_test_agreed: N (target >= 8)
Hard cases with 2+ interacting high-severity issues: N (target >= 5)
Hard cases with domain-plausible must_not_claim: N (target >= 4)
Hard critique cases with addressed-but-incorrectly must_find: N (target: all hard critique cases)
Hard critique cases with compound must_find: N (target: all hard critique cases)
Hard critique cases with decoy in first 2 paragraphs: N (target: all hard critique cases)
Hard defense_wins cases with >=2 planted_issues entries: N (target: all hard defense_wins cases)
Hard defense_wins cases with named external-knowledge exoneration: N (target: all hard defense_wins cases)
Hard critique/mixed cases with acceptable_resolutions = ['empirical_test_agreed'] only: N (target: all hard critique/mixed)
Hard critique cases with >=1 domain-specific false-alarm must_not_claim (Lever B): N (target: all hard critique)
Cases with multiple acceptable_resolutions: N
Cases disqualified (list reason): N
Cases flagged (list flags): N
High-severity planted issues total: N
```

Then output a **difficulty discrimination table** — for each difficulty tier, list the predicted mean number of rubric dimensions (IDR, IDP, DC, DRQ, ETD, FVC) a single-pass assessor would fail on:

```
DIFFICULTY DISCRIMINATION
=========================
Easy:   predicted failed dims = X.X  (target: ≤0.5)
Medium: predicted failed dims = X.X  (target: 0.5–1.5)
Hard:   predicted failed dims = X.X  (target: ≥2.0)
```

If the predicted discrimination does not separate the tiers, flag this in the self-critique and identify which hard cases need structural revision.

Then output a self-critique: what are the 3 most likely weaknesses of this benchmark that an adversarial reviewer would identify?

---

## PHASE 5.5: HARD CASE DIFFICULTY GATE (operator-run, post-generation)

**This phase is run by the operator after the LLM outputs the final JSON — it is not run by the LLM.**

After saving the output as `benchmark_cases.json`, run the difficulty gate against the hard cases before accepting the benchmark:

**Acceptance criterion:** At least 6 of 10 randomly sampled hard cases must score a mean rubric score < 0.55 when evaluated by `claude-haiku-4-5` as a single-pass assessor (no debate structure).

**Procedure:**
1. Sample 10 hard cases from the output (or all hard cases if fewer than 10)
2. For each sampled case, run `claude-haiku-4-5` as a single-pass reviewer using the standard rubric (IDR, IDP, DC, DRQ, ETD, FVC)
3. Compute the mean rubric score per case
4. Count how many cases score < 0.55

**If fewer than 6 of 10 sampled cases score < 0.55:** The hard cases are not hard enough. Regenerate the hard cases using this prompt, with the instruction to redesign any case that haiku scores ≥ 0.55 — specifically by switching to a flaw type that requires external knowledge (Type A or C) rather than internal consistency checking.

**If ≥ 6 of 10 sampled cases score < 0.55:** The benchmark passes the gate. Proceed to running the full debate protocol experiment.

---

## QUALITY STANDARDS

The benchmark will be used in a paper submission. Cases that would embarrass the authors if scrutinized are worse than having fewer cases. Prefer quality over quantity. It is better to generate 45 excellent cases than 50 mediocre ones.

The gold standard for a good case: a senior ML engineer reading the task_prompt would say "yes, this is a real problem I've seen teams make" (for critique cases) or "yes, this is a real methodology people challenge unfairly" (for defense cases).

**Hard critique case gold standard (v5):** A senior ML engineer reading the task_prompt says "I read this carefully and it seems fine" on first pass, then on second pass with specific probing says "wait — actually, there's a problem with [specific assumption/number/omission]." The case must survive the first pass to be hard. Cases where the flaw is obvious to a careful first-time reader — regardless of how it is structured — are medium difficulty, not hard. Cases where the flaw is found by checking internal consistency are easy.

**Hard defense_wins gold standard (v5):** A senior ML engineer reading the task_prompt says "this looks suspicious — there are 2–3 things here that feel like red flags" on first pass. On deliberate second pass, with access to the relevant domain literature or methodology standard, they confirm the methodology is sound and the flags are artifacts of pattern-matching rather than genuine flaws. The case fails if the false concern is dismissible without domain knowledge, or if a careful reviewer would not raise it in a real review.

Begin Phase 1 now. Generate all 60 cases before proceeding to Phase 2. For all hard critique/mixed cases, apply the 4 Critique Case Design Requirements (addressed-but-incorrectly, decoy dominance, compound issue, domain-knowledge-gated). For all hard defense_wins cases, apply the 4 Defense_Wins Case Design Requirements (multi-evidence false concern, external knowledge exoneration, diversified flaw types, calibrated ideal_defense). Run all 8 self-evaluation tests on hard cases during Phase 3.

---

## OUTPUT FORMATTING REQUIREMENT

When outputting the final 50-case JSON array at the end of Phase 4, use no markdown formatting whatsoever. No code fences, no triple backticks, no language tags. The output must start directly with `[` and end directly with `]`. This is required so the output can be saved as `benchmark_cases.json` without any stripping or editing by the operator.
