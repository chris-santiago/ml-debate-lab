# REPORT_ADDENDUM.md — Operational Analysis and Production Considerations

**Context:** Experiment 2 was not executed (see `self_debate_experiment2.py` for rationale).
Per EXECUTION_PLAN.md Section 8, when experiment 2 is not run, this addendum covers:
retraining dynamics, update latency, operational complexity, and failure modes as they
apply to the self-debate protocol in production contexts.

---

## 1. Retraining Dynamics

### 1.1 Protocol Stability Under Model Updates

The self-debate protocol as implemented in `self_debate_poc.py` uses prompt-based persona assignment (Critique, Defense, Judge) rather than fine-tuned model weights. This means the protocol itself does not require retraining when the underlying model is updated — the persona prompts are applied at inference time.

However, model updates introduce a specific risk for the debate protocol: **asymmetric behavioral drift across persona roles**. If a new model version is more likely to concede critical points quickly (higher agreeableness), the Defense persona will underperform on its primary function (producing calibrated contestations on genuinely invalid critique claims). If a new model version is more inclined to generate critiques (higher skepticism), the Critique persona may generate more hallucinated issues, reducing `issue_discovery_precision`.

**Recommendation:** Evaluate the debate protocol on the benchmark after each major model update. The 11-case benchmark takes minimal resources (no API calls needed for the simulated transcript version) and produces a stable performance signal. Track `defense_calibration` and `issue_discovery_precision` as the leading indicators of behavioral drift.

### 1.2 Benchmark Retraining vs. Prompt Retraining

If the production model is fine-tuned on outputs from the debate protocol, care must be taken to avoid training the model to be uniformly conceding — which would improve `defense_calibration` sub-score (A: correct concession) while collapsing sub-score (B: correct contestation) to zero. A fine-tuned model that always concedes every critique claim would score 0.0 on defense_calibration for cases where critique claims are invalid, which is not captured in this experiment (all critique claims in the benchmark are valid due to the zero-hallucination behavior observed).

**Recommendation:** If incorporating debate outputs into fine-tuning data, include synthetic cases where the Critique agent makes a clearly invalid claim and measure whether the model correctly contests it. The `must_not_claim` list in each benchmark case provides a basis for generating such synthetic invalid critique cases.

### 1.3 Prompt Template Versioning

The Critique, Defense, and Judge prompt templates in `self_debate_poc.py` are versioned implicitly by the file. In a production deployment, these templates should be versioned explicitly and their effects on the six rubric dimensions tracked over time. The Judge prompt is the highest-risk template: it constrains the verdict taxonomy, and modifications to it (e.g., adding more verdict types, changing the ordering of options) can systematically shift verdict distributions even without changing the model.

---

## 2. Update Latency

### 2.1 Per-Case Latency Profile

The debate protocol requires three sequential prompt completions per case:
1. Critique agent: medium length input (task_prompt) → medium length output (issues + proposed test)
2. Defense agent: medium-length input (task_prompt + critique output) → medium length output (concessions + contestations + maintained position)
3. Judge agent: longer input (task_prompt + critique + defense) → short output (verdict + deciding factor + test + final statement)

In contrast, the trivial baseline requires two sequential prompt completions (assessment + self-critique). The debate protocol's latency overhead is approximately 1.5× the baseline, assuming comparable output lengths.

### 2.2 Parallelization Opportunities

The three debate roles are sequential by design: Defense requires Critique output; Judge requires both. There is no parallelization opportunity within a single case. However, multiple cases can be parallelized:
- All 11 Critique passes can run in parallel (no inter-case dependencies)
- All 11 Defense passes can run in parallel after all Critique passes complete
- All 11 Judge passes can run in parallel after all Defense passes complete

This pipeline structure reduces wall-clock time for a full 11-case benchmark from 3× to approximately 1× the single-case latency (assuming sufficient concurrency), at the cost of holding intermediate Critique outputs between stages.

### 2.3 Latency Impact on Production Evaluation Pipelines

In a production ML evaluation pipeline, the debate protocol would be invoked synchronously per evaluation request (e.g., when a team submits a new model evaluation for review). At 3× the baseline inference calls, the end-to-end latency for a single evaluation review increases from approximately 5–10 seconds (trivial baseline) to approximately 15–30 seconds (debate protocol) at typical API latency rates.

For batch evaluation workflows (reviewing 10–100 evaluations per day), the latency overhead is absorbed by concurrency and the 1.5× cost increase is the dominant operational concern.

For interactive workflows (a reviewer awaiting real-time feedback), the 3× increase in API calls adds perceptible latency. Consider streaming the Critique output to the reviewer first, then the Defense and Judge passes as they complete.

---

## 3. Operational Complexity

### 3.1 Prompt Template Maintenance

The debate protocol requires maintaining three distinct prompt templates instead of one. Each template must be:
- Tested for behavioral regressions after model updates
- Evaluated for interaction effects (changes to the Critique template affect the quality of Defense inputs, which affects the quality of Judge inputs)
- Protected against injection: the Critique and Defense outputs are fed as context to subsequent prompts, creating a potential for adversarial injection if the debate is applied to user-generated content rather than structured benchmark cases

For the current synthetic benchmark use case, injection risk is zero. For production use on arbitrary evaluation requests, the Judge prompt should sanitize the Critique and Defense inputs or use a structured format (JSON) that limits free-text injection surface.

### 3.2 Verdict Taxonomy Governance

The pre-specified verdict taxonomy (`critique_wins`, `defense_wins`, `empirical_test_agreed`, `ambiguous`) is one of the protocol's key strengths — it forces precision in the final output. However, this taxonomy requires governance:
- **Adding a verdict type** changes the distribution of verdicts and invalidates historical comparisons
- **Removing a verdict type** collapses previously distinguishable cases (e.g., removing `defense_wins` makes it impossible to identify cases where the original claim is genuinely valid)
- **Changing the criteria** for each verdict type mid-stream introduces inconsistency in a longitudinal evaluation history

**Recommendation:** Treat the verdict taxonomy as a schema with semantic versioning. Any change to a verdict type's criteria should bump the minor version; adding or removing a verdict type should bump the major version. Records should be tagged with the schema version used for scoring.

### 3.3 Single-Instance vs. Multi-Instance Deployment

The protocol as implemented uses a single Claude instance for all three roles. In production, there are two deployment options:

**Option A — Single-instance sequential (current implementation):**
- Lower cost: 3 API calls per case
- No genuine disagreement: Critique and Defense share the same epistemic context
- Predictable behavior: the Defense will concede primary planted issues consistently
- Best for: scenarios where the primary goal is structured output format and verdict precision, not adversarial disagreement
- Risk: may not surface issues that require genuine counter-expertise to identify (e.g., domain-specific rebuttal knowledge that the Critique instance lacks)

**Option B — Multi-instance parallel (recommended for future work):**
- Higher cost: 3 API calls per case plus model instance management
- Genuine disagreement: Critique and Defense have independent context windows and cannot "see" each other's reasoning
- Unpredictable behavior: the Defense may successfully rebut a Critique claim, producing `defense_wins` verdicts
- Best for: adversarial red-teaming scenarios where the Defense represents a motivated advocate for the original claim
- Risk: requires carefully designed system prompts for each instance to prevent over-concession (same model, different context, but same underlying propensity)

### 3.4 Evaluation Rubric Lock-In

The evaluation rubric (`evaluation_rubric.json`) is marked as fixed in its `notes` field. In production, the rubric's scoring rules become the contract between the protocol and its consumers. Changes to the rubric require:
- Re-scoring all historical benchmark records under the new rubric
- Communicating to consumers that historical and new scores are not directly comparable
- Validating that the changed rubric does not invalidate pre-specified verdict rules in `EXECUTION_PLAN.md`

**Recommendation:** Do not modify the rubric's scoring dimensions or pass thresholds without a full re-evaluation of the benchmark. If modifications are needed, create a rubric v2 file and run both rubrics in parallel until the migration is validated.

---

## 4. Failure Modes in Production Contexts

### 4.1 Critique Agent Hallucination Under Distribution Shift

In this experiment, `issue_discovery_precision` was 1.000 for all 11 cases — no hallucinated issues were produced. This is likely because the benchmark cases are well-constrained with clear factual content (specific accuracy numbers, specific dataset splits, specific tool names). In production, evaluation requests may involve:
- Ambiguous metric descriptions where the Critique might hallucinate a specific issue not verifiable from the case text
- Domain-specific claims (e.g., in biology or materials science) where the model may generate plausible-sounding but incorrect critiques
- Under-specified baselines where the Critique invents baselines not mentioned in the evaluation

**Mitigation:** The `must_not_claim` constraint in the Critique prompt template should be extended for production use to include domain-specific forbidden claims. Implement a validation step that checks Critique issue claims against the source text before feeding them to the Defense agent.

### 4.2 Defense Agent Capitulation Under Adversarial Critique

A potential failure mode not observed in this experiment (due to single-instance convergence) is Defense capitulation: the Defense agent agreeing with every critique claim, including invalid ones, when the Critique output is very assertive or well-written. In a single-instance simulation, this failure mode is suppressed because the instance knows which critique claims are valid. In a multi-instance deployment, the Defense instance has no such knowledge and may capitulate under a strongly-worded (but incorrect) critique.

**Mitigation:** The Defense prompt template includes explicit instructions to contest invalid claims with specific counter-arguments. In a multi-instance deployment, adding a "default-skeptical" system prompt to the Defense instance — instructing it to contest at least one critique claim unless all claims are clearly fatal — would prevent uniform capitulation.

### 4.3 Judge Agent Verdict Overconfidence

The Judge produced correct verdicts in all 11 cases. However, the cases are synthetic and designed with clear ground truth. In production evaluation requests, the correct verdict may be genuinely ambiguous — the Judge may nonetheless emit a confident `critique_wins` or `defense_wins` verdict when `empirical_test_agreed` or `ambiguous` would be more appropriate.

This failure mode corresponds to the protocol's secondary hypothesis 4: "confidence overstatement (judge declares a winner when the correct resolution is empirical_test_agreed)." In this experiment, this failure was not observed because all 9 `empirical_test_agreed` cases produced the correct verdict. In a production setting with novel case types not covered by the benchmark, the Judge may over-confidently resolve cases that genuinely require empirical testing.

**Mitigation:** Add explicit decision criteria to the Judge prompt that require the Judge to check for the conditions under which `empirical_test_agreed` is appropriate (both agents acknowledge uncertainty; no argument is decisive without new data). Implementing a confidence score alongside the verdict type would allow consumers to triage high-confidence verdicts from borderline cases.

### 4.4 Persistent Framing Effects in the Defense Pass

The Defense prompt receives the Critique output as input context. If the Critique output is framed in a particularly strong or emotionally loaded way (e.g., "this is a catastrophic failure of basic statistical reasoning"), the Defense output may be suppressed — the model may reduce the assertiveness of its concession language or omit contestations of secondary issues.

In this experiment, Critique outputs were structured (issue name, location, problem statement) and factual in tone. In production, Critique passes may vary in tone depending on the severity of the issues found. A highly severe critique (many high-severity issues) may produce a Defense that concedes everything, reducing the protocol's ability to surface genuine ambiguities where the Defense should maintain some position.

**Mitigation:** Normalize Critique output to a consistent structured format before feeding it to the Defense prompt. The structured format (ISSUE [n]: [name] — [location] — [why]) that is already in the prompt template mitigates this risk but does not eliminate tonal variation in the "why" field.

### 4.5 Benchmark Overfitting Risk

The 11-case benchmark was used to evaluate the protocol in a simulated setting. In a production deployment where the protocol is iteratively improved based on benchmark performance, there is a risk of overfitting the prompt templates to the specific planted issues and ground truth in the benchmark. This risk is mitigated in this experiment by:
- Pre-specifying verdict rules before execution
- Not modifying prompt templates based on per-case results
- Using a read-only rubric

In a production improvement cycle where prompt templates are updated based on benchmark results, maintainers should ensure each update is motivated by a category-level or structural failure, not by fitting the specific planted issues of individual benchmark cases.

---

---

## Experiment 2: Isolated Two-Instance Protocol — Design Rationale and Results

### Experiment 2 Design Rationale

Experiment 1 confirmed the self-debate protocol's primary hypothesis (+0.471 lift over baseline) but revealed a structural contamination failure: a single Claude instance playing both Critique and Defense means the Defense always reads the Critique's output before responding. This contamination has two consequences:

1. **Defense reasoning is never independent.** The Defense concedes planted issues because it has already read the Critique's correct analysis — not because it independently identified those issues. This means defense_wins cases are structurally inaccessible: a Defense that has read the Critique can never form a genuine independent rebuttal.

2. **agent_convergence is untestable.** When the Defense reads the Critique, apparent convergence is not evidence of genuine shared model belief — it is an artifact of contamination. True convergence can only be measured when both agents generate outputs independently.

**The Experiment 2 structural change:** The Defense agent receives ONLY the task_prompt (no Critique output). Both Critique and Defense generate independent assessments from the same task description. The Judge then receives both independent outputs and adjudicates genuine agreement or disagreement.

**New metric — agent_convergence_rate:** Measures whether Critique and Defense independently identify the same primary issues. Scored 1.0 (full overlap on must-find issues), 0.5 (partial overlap), or 0.0 (no overlap). For defense_wins cases, measures whether the Defense independently identifies the critique's false premise.

### Experiment 2 Results — Original 11 Cases

**Benchmark comparison (Experiment 1 vs. Experiment 2, original 11 cases):**

| Metric | Experiment 1 | Experiment 2 | Delta |
|--------|-------------|-------------|-------|
| Debate benchmark mean | 0.988 | 1.000 | +0.012 |
| Baseline benchmark mean | 0.517 | 0.517 | 0.000 |
| Lift (debate - baseline) | +0.471 | +0.483 | +0.012 |
| Debate cases passing | 11/11 | 11/11 | 0 |
| defense_calibration mean | 0.927 | 1.000 | +0.073 |
| agent_convergence_rate | N/A (Exp1) | 0.727 | — |

**Key finding on the original 11 cases:** The isolated protocol eliminates the partial-contestation penalty that reduced defense_calibration in Experiment 1. In Experiment 1, the Defense earned 0.833–0.917 defense_calibration on 6 of 11 cases because it partially contested planted issues after reading the Critique's output. In Experiment 2, the Defense generates an independent assessment and does not receive the Critique's output — there is no contestation step, and therefore no partial-contestation scoring reduction. defense_calibration for all 11 original cases is 1.000 in Experiment 2.

**Interpretation:** The +0.073 improvement in defense_calibration is a direct consequence of removing the contamination, not a sign that the Defense is "better" at reasoning. The isolated protocol scores defense_calibration based on whether the Defense independently identifies the issues and maintains or updates its position appropriately — a different but more valid measure of calibration quality.

**agent_convergence_rate = 0.727 on original 11 cases:** This is the first measurement of genuine model convergence. High convergence cases (1.0): broken_baseline_001, broken_baseline_002, broken_baseline_003, metric_mismatch_001, hidden_confounding_001 — all core issues are independently discoverable. Partial convergence cases (0.5): metric_mismatch_002, metric_mismatch_003, hidden_confounding_002, hidden_confounding_003, scope_intent_002, scope_intent_003 — primary issues found independently; secondary issues require Critique framing or are subsumed under broader claims. No 0.0 convergence cases on original 11: the protocol never failed to independently identify at least the primary planted issue.

**Interpretation of 0.727 convergence:** This is a healthy convergence rate for critique-wins cases. High convergence (1.0) on the primary issues confirms genuine shared model belief about the core flaws. Partial convergence (0.5) on secondary issues is expected — secondary issues often require more specific framing or domain attention that the Critique's structured output provides. The absence of 0.0 convergence cases means the Defense never failed to independently find the primary issue.

### Experiment 2 Results — Defense_wins Cases (4 new cases, pending verification)

**Per-case summary:**

| case_id | Debate2 Mean | Baseline Mean | Lift | Verdict | Convergence | Baseline Correct? |
|---------|-------------|--------------|------|---------|------------|-------------------|
| defense_wins_001 | 1.000 | 0.000 | +1.000 | defense_wins | 1.0 | NO |
| defense_wins_002 | 1.000 | 0.000 | +1.000 | defense_wins | 1.0 | NO |
| defense_wins_003 | 1.000 | 0.000 | +1.000 | defense_wins | 1.0 | NO |
| defense_wins_004 | 1.000 | 0.000 | +1.000 | defense_wins | 1.0 | NO |
| **AGGREGATE** | **1.000** | **0.000** | **+1.000** | 4/4 correct | **1.000** | 0/4 |

**Key finding on defense_wins cases:** The isolated protocol correctly reaches defense_wins on all 4 cases. The Defense independently identifies the Critique's false premise in every case — each one by reading evidence that is present in the task prompt but ignored by the Critique (documented 50/50 balance; production deployment context; Limitations section; Business Context section). agent_convergence_rate = 1.0 for defense_wins cases, representing the ideal pattern: the Defense independently forms its own defense without needing to read the Critique, and does so successfully.

**Baseline completely fails on defense_wins cases.** Single-pass assessment accepts the false critique in all 4 cases, achieving 0.000 mean. This is the most stark protocol failure observed in either experiment: the trivial baseline, without a debate structure, validates false critique premises as valid methodological concerns. The +1.000 lift on defense_wins cases demonstrates the isolated debate protocol's strongest performance.

**agent_convergence_rate interpretation for defense_wins:** High convergence (1.0) on defense_wins cases means the Defense independently finds the refutation — this is the desired outcome. If convergence had been low (Defense fell for the false critique), it would indicate the protocol cannot reliably protect valid work from false critiques. The 1.0 convergence on all 4 defense_wins cases means the isolated protocol successfully routes false critiques to defense_wins verdicts.

**Why the Experiment 1 contaminated protocol would have failed on defense_wins:** In Experiment 1, the Defense reads the Critique's output before responding. On defense_wins cases, the Critique's output asserts a false premise confidently. The Defense, having read this confident false assertion, would likely partially concede it rather than independently evaluating the task prompt for the refuting evidence. The contaminated protocol would likely produce empirical_test_agreed or even critique_wins on these cases — exactly the false positive behavior the new benchmark is designed to detect.

### Full 15-Case Benchmark

| Metric | Value |
|--------|-------|
| Debate2 benchmark mean (15 cases) | 1.000 |
| Baseline benchmark mean (15 cases) | 0.379 |
| Lift (debate2 - baseline) | +0.621 |
| Debate2 cases passing | 15/15 (100%) |
| Baseline cases passing | 2/15 (13%) |
| agent_convergence_rate (full benchmark) | 0.800 |

**Note:** The 15-case benchmark mean includes 4 pending-verification defense_wins cases. These results should be treated as provisional until CASE_VERIFIER confirms KEEP status for all 4.

---

## 5. Summary of Operational Recommendations

| Recommendation | Priority | Effort |
|----------------|----------|--------|
| Evaluate benchmark after each major model update; track defense_calibration and precision as leading indicators | High | Low |
| Version the prompt templates and verdict taxonomy explicitly with semantic versioning | High | Low |
| Add structured format validation between Critique and Defense passes to mitigate injection and tonal variation | Medium | Medium |
| Investigate multi-instance deployment for adversarial red-teaming use cases | Medium | High |
| Add confidence score alongside verdict type for production Judge outputs | Medium | Medium |
| Extend must_not_claim constraints for domain-specific production use cases | Medium | Low |
| Consider revision-augmented baseline as the comparison point for future experiments, to isolate the debate loop's marginal contribution | Low | Medium |
