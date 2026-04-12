# v5 Experiment Report Addendum: Production Re-Evaluation

> This addendum is written by the experiment orchestrator and supplements REPORT.md.
> All quantitative claims are sourced from stats_results.json and REPORT.md; no values are paraphrased or independently rounded.

---

## Deployment Scenario

**What production use of this protocol would look like:**

A production deployment would operate as follows. An ML practitioner submits a methodology description (training setup, evaluation design, data pipeline, or experimental protocol) as a task prompt. The system routes it through the isolated_debate condition: a Critic agent independently reviews for methodological flaws, a Defender agent independently argues the design is sound, and an orchestrator adjudicates. The output is a typed verdict (critique_wins, defense_wins, or empirical_test_agreed) with supporting rationale.

**Operational parameters (based on v5 benchmark run):**
- Model: claude-sonnet-4-6
- Condition: isolated_debate (primary) or multiround (when extended exchange is warranted)
- Input: task prompt (~500–2000 tokens per case)
- Output: verdict + structured rationale (~800–1500 tokens)
- Latency: approximately 30–90 seconds per case depending on model load
- Cost per case: approximately $0.05–0.15 USD at current claude-sonnet-4-6 pricing (3 agents × ~1000 tokens output each)
- Concurrency: the Phase 6 pipeline ran up to 20 concurrent cases; this is the tested upper bound

**Conditions not recommended for production:**
- `forced_multiround`: hollow-round rate of 20.5% on defense_wins cases wastes tokens without adding signal; reserve for cases where initial verdict is borderline
- `ensemble`: suppresses IDR (0.7679 vs. 0.8969 for isolated_debate); appropriate only when false-positive control is the primary concern and recall is secondary

---

## Benchmark-to-Production Transfer

Which findings from REPORT.md generalize to production scenarios and which are benchmark-specific:

| Finding | Generalizes? | Notes |
|---|---|---|
| Protocol achieves 89.1% pass rate | Partially | Benchmark cases have unambiguous binary ground truth; real-world methodology questions are frequently ambiguous. Pass rate on mixed-verdict cases is unknown. |
| H1 FAILS: fc_lift = +0.0097 | Partially | The null result was obtained on binary-verdict cases selected to favor the protocol. If production cases are similarly unambiguous, the null result likely transfers. Mixed-verdict production cases remain untested. |
| Baseline performs near-ceiling (0.9452) | Likely | Single-pass critique at claude-sonnet-4-6 capability level is a strong baseline; this is a structural property of the model, not the benchmark. |
| DRQ and FVC at ceiling for all conditions | Likely | Both conditions reliably produce correctly-typed verdicts on clearcut cases; production benefit would come from precision on ambiguous cases, which were not tested. |
| Ensemble trades IDR for IDP | Likely | The majority-vote suppression mechanism is structural and will operate in production. Use ensemble when false-positive cost exceeds false-negative cost. |
| Forced multiround hollow rounds (20.5%) | Likely | Structural: defense_wins cases that resolve in round 1 have nothing to add in round 2. Production FM should gate round 2 on a substantive disagreement signal, not force it unconditionally. |
| Difficulty labels failed to stratify | Benchmark-specific | The proxy_mean filter was calibrated to this model version. Difficulty stratification in production would require a different operationalization. |
| Answer-key leakage (corrected) | Benchmark-specific | The leakage was a pipeline artifact of the evaluation harness. Not applicable to production deployment where no answer keys exist. |

---

## Unresolved Limitations at Scale

For each limitation named in REPORT.md §Limitations:

**1. Closed-Loop Evaluation Confound**
- Applies at production scale: Yes. If the same model family both generates and reviews outputs, model-specific bias cannot be ruled out.
- Mitigated: Partially. Cross-vendor validation (Phase 9) was conducted; IDR delta (-0.7737) is large. For production deployments where evaluation accuracy is critical, a different model family should score the outputs, or human spot-checks should be scheduled at regular intervals.

**2. Same-Model Benchmark Selection Bias**
- Applies at production scale: Yes. Benchmark-calibrated cases may not represent the distribution of real methodology questions.
- Mitigated: Not meaningfully. The v5 negative result is conservative (protocol failed on favorable cases), but the positive performance space (mixed-verdict cases, other models) is entirely uncharted. Production deployment on cases meaningfully different from ARCH-1 should be treated as extrapolation.

**3. No Mixed Cases in Benchmark**
- Applies at production scale: Yes. Real methodology review is dominated by mixed-verdict cases where some design choices are sound and others are flawed. The protocol's differential value is untested on this case type.
- Mitigated: No. This is the most significant unresolved gap. A production deployment without mixed-case validation is relying on an untested assumption that the protocol generalizes beyond binary-verdict cases.

**4. Answer-Key Leakage (Corrected)**
- Applies at production scale: Not applicable. No answer keys exist in production.

**5. Phase 6 Batch Contamination (Remediated)**
- Applies at production scale: Partially. The zero-variance detection mechanism is a useful production health check: if all runs of a condition on a case return identical outputs, the pipeline should flag the run as potentially contaminated.

**6. Small Effect Size Relative to Statistical Power**
- Applies at production scale: Yes. The +0.10 threshold was a pre-registered policy choice. At production scale, the relevant threshold is cost-benefit: does the incremental quality gain from the debate structure justify the 3× token cost vs. single-pass baseline? At fc_lift = +0.0097, the answer is no under any plausible quality-per-token metric.

**7. Forced Multiround Stub Misclassification (Corrected)**
- Applies at production scale: Not applicable. This was a benchmark pipeline artifact.

---

## Deployment Recommendation

**Verdict: Do not deploy the self-debate protocol as a general-purpose methodology reviewer in its current form.**

The evidence does not support production adoption for the following reasons:

1. **No demonstrated differential value over baseline.** fc_lift = +0.0097 [CI: -0.0013, +0.0217]. The protocol achieves 89.1% pass rate, but single-pass baseline achieves 94.52% benchmark mean on the same cases. The 3× token cost of the debate structure (Critic + Defender + adjudicator vs. single assessor) is not justified by a +0.0097 mean lift.

2. **Untested on the most relevant case type.** The mechanism claim requires mixed-verdict cases to demonstrate advantage; the benchmark contained none. Production deployment without mixed-case validation is extrapolation beyond the tested scope.

3. **Closed-loop evaluation confound unresolved.** The large IDR scorer disagreement between Claude (-0.7737 delta vs. gpt-4o-mini) means absolute quality estimates are evaluator-dependent. Production scoring should not rely on the same model family for both generation and evaluation.

**Qualified deployment conditions under which this recommendation could be revisited:**

- A new benchmark including >= 30% mixed-verdict cases shows fc_lift >= +0.10 with CI entirely above zero
- A cross-model evaluation design (generate with Model A, score with Model B) replicates the directional positive IDR lift
- The hollow-round rate in forced_multiround is reduced by gating round 2 on a substantive disagreement signal

Until those conditions are met, the isolated_debate protocol is appropriate as a research tool for understanding model debate behavior, not as a production methodology reviewer. The baseline (single-pass critique) achieves near-equivalent performance at one-third the token cost and should be preferred in production.
