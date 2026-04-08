# Stage 3 — Corruption Node

**Role:** You are an expert ML practitioner who deeply understands how experiment designs fail in practice. You have been given a methodologically sound experiment design. Your task is to corrupt exactly **{{NUM_CORRUPTIONS}}** design choices, replacing each with a plausible-but-wrong alternative.

**If {{NUM_CORRUPTIONS}} is 0:** Return the design unchanged. The ground truth is that this design is sound. Do not introduce any corruptions.

---

## The Target for Your Corruptions

You are simulating the output of a capable but less careful LLM — one that produced a reasonable-looking experiment design without reasoning carefully about a specific choice. Your corruptions must:

1. **Look like natural LLM output** — the corrupted choice should be the kind of thing a capable model would write if it didn't think carefully about this particular decision. Not obviously wrong. Plausible on first read.

2. **Require methodology expertise to detect** — a non-expert or a fast reader should not notice the problem. The error should only become visible to someone who reasons carefully about the specific domain, data structure, or evaluation context.

3. **Be a genuine methodological error** — not a style preference or a legitimate alternative approach. The corruption must actually invalidate or weaken the experiment in a way that matters.

4. **Target a single design choice** — each corruption replaces exactly one decision. Do not conflate multiple errors into one corruption entry.

---

## Flaw Taxonomy

Choose corruptions from this taxonomy. For each corruption, the flaw type must be one of the following:

### `temporal_leakage`
Replace a chronological or group-based split with a random split on time-ordered or group-structured data. The corrupted choice uses random sampling where temporal or group ordering is essential — allowing future information or correlated observations to appear in training.

*Example corruption:* "The dataset is randomly split 80/10/10 into train, validation, and test sets, stratified by label" — replacing a temporal split in a setting where user behavior or market conditions evolve over time.

### `preprocessing_leakage`
Fit a preprocessing transformer (scaler, encoder, imputer, feature selector, dimensionality reducer) on the full dataset before the train/test split, rather than fitting only on the training set and applying to validation/test.

*Example corruption:* "Features are standardized using z-score normalization across the full dataset before splitting" — instead of fitting the scaler on training data only.

### `metric_mismatch`
Use an evaluation metric that does not align with the operational objective or the data structure. Common cases: accuracy on heavily imbalanced data; AUC when the model's calibrated probability output matters; MSE when rank ordering is what drives decisions; a threshold-dependent metric when the threshold is unknown at design time.

*Example corruption:* "Model performance is evaluated using accuracy on the held-out test set" — replacing F1 or precision@k in a setting where the positive class is rare.

### `broken_baseline`
Use a baseline that is not given equivalent treatment: untuned while the proposed model is tuned, uses a different or smaller feature set without justification, evaluated on different data, or is a fundamentally weaker model class chosen to make the new model look good.

*Example corruption:* "The baseline logistic regression is trained on default hyperparameters" — replacing a properly tuned baseline with equitable optimization effort.

### `evaluation_contamination`
Use the test set during model development — for hyperparameter tuning, model selection, threshold setting, or any other decision that should be made on the validation set only. Or use the same data for both feature selection and model evaluation.

*Example corruption:* "Final hyperparameters are selected by evaluating candidate configurations on the test set and choosing the best-performing one" — instead of using the validation set for selection.

### `target_leakage`
Include a feature in the model that directly or indirectly encodes the label — computed using the outcome, derived from a post-outcome signal, or available only because the outcome occurred.

*Example corruption:* "Features include the number of customer support tickets filed in the 7 days following account creation" — in a churn prediction setting where this ticket count post-dates the label window.

### `scope_mismatch`
The experiment tests something adjacent to the stated hypothesis rather than the hypothesis itself — a confounded proxy, a different population, a different time horizon, or a different formulation of the outcome.

*Example corruption:* "The model is trained to predict whether a user clicks on a recommended item, used as a proxy for purchase conversion" — when the hypothesis is about purchase conversion rate and click-through rate is a weak proxy with known divergence.

### `distribution_shift`
Train on a population or time period that does not represent the intended deployment distribution, without acknowledging or controlling for the shift. The experiment would produce results that do not generalize.

*Example corruption:* "Training data is drawn from the top 10% of users by activity, as they have the most complete behavioral records" — when the model will be deployed on all users including low-activity ones.

### `confound_conflation`
Attribute an observed improvement to the proposed mechanism when the experiment cannot isolate it from a known confound — a correlated variable, a concurrent intervention, or a selection effect that changes at the same time as the treatment.

*Example corruption:* "The graph embedding model is evaluated against the baseline over the same period, where the graph embedding also incorporates more recent data due to implementation timing" — confounding the feature type with the data recency.

---

## Selection Rules

When choosing which choices to corrupt:

1. **Prefer choices that are non-obvious** — corrupting the split strategy is more interesting than corrupting a secondary metric
2. **For {{NUM_CORRUPTIONS}} = 2:** The two corruptions may be independent or may interact (two choices that are each fine individually but wrong in combination). If they interact, note this in `compound_note`
3. **For {{NUM_CORRUPTIONS}} = "many":** Select 3–5 corruptions from at least 3 different flaw types. Include at least one that is more obvious (calibration anchor) and at least one that is subtle
4. **Never corrupt the hypothesis statement** — only corrupt design choices

---

## Output Format

Return a JSON object.

```json
{
  "hypothesis_id": "{{HYPOTHESIS_ID}}",
  "num_corruptions": {{NUM_CORRUPTIONS}},
  "corruptions": [
    {
      "corruption_id": "c001",
      "flaw_type": "one of the flaw taxonomy types above",
      "targeted_choice": "Which structured_choice field this corruption targets (e.g., split_method, primary_metric, baseline)",
      "original_text": "The exact text from the sound design that is being replaced",
      "corrupted_text": "The replacement text — plausible, sounds reasonable, is wrong",
      "why_wrong": "1-2 sentences: why this corrupted choice is methodologically incorrect for this specific hypothesis and data structure",
      "detectability": "subtle | moderate | obvious",
      "compound_note": "If this corruption only reveals a problem in combination with another corruption, describe the interaction. Otherwise null."
    }
  ],
  "corrupted_narrative": "The full design_narrative from Stage 2 with corrupted choices substituted in. Must be self-consistent — rewrite surrounding sentences as needed so the corrupted version reads naturally and does not call attention to itself. The reader should not be able to tell where substitutions occurred. Same length and structure as original."
}
```

---

## Critical Requirements

- The `corrupted_narrative` must read as a coherent, confident experiment plan. It should not feel patched or awkward around the corrupted choices.
- Each `corrupted_text` must sound like something a real LLM would write — not like a deliberately bad answer.
- The `original_text` must be a verbatim or near-verbatim extract from the Stage 2 `design_narrative`.
- Do not corrupt the same design dimension twice (e.g., two different metric corruptions).

---

## Your Input

**Sound design from Stage 2:**
```json
{{SOUND_DESIGN}}
```
