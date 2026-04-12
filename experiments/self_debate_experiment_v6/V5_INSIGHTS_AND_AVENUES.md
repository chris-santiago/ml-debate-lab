# v5 Insights & Investigation Avenues

*Synthesized from REPORT.md, FINAL_SYNTHESIS.md, REPORT_ADDENDUM.md, PEER_REVIEW_R1.md, and V3_V5_CONTRAST.md.*

---

> **Before synthesizing:** the most structurally interesting thing about this entire body of work is that it's a *recursive validity experiment* — you built infrastructure to evaluate the evaluator, discovered the evaluator was biased, discovered the benchmark was measuring the wrong thing, and now v6 is correcting for all of that. The experiment's failure modes are more informative than its results.

---

## The Most Interesting Insights from v5

### 1. ETD was the only real signal — and v5 eliminated it by design

This is the deepest finding in the project. Looking at the v3/v5 contrast:

| Dim | v3 Isolated | v3 Baseline | Delta |
|---|---|---|---|
| IDR | 1.000 | 1.000 | **0.000** |
| IDP | 1.000 | 1.000 | **0.000** |
| ETD | 0.841 | 0.476 | **+0.365** |
| FVC | 0.980 | 0.980 | **0.000** |

The entire v3 fair-comparison lift came from ETD — the debate protocol was better at specifying *empirical tests for ambiguous choices*, not at finding flaws or getting verdicts right. When v5 was built to fix v3's methodological problems, the case generation pipeline structurally produced only binary-verdict cases (planted flaws or sound designs). Zero mixed cases → ETD always N/A → the one dimension where debate demonstrably helped was designed out. The experiment measured the wrong thing.

**This isn't a mistake, it's the core finding:** the debate protocol's advantage, if any, is specific to genuinely contestable cases, not clearcut ones.

---

### 2. The "hard" benchmark was near-ceiling for baseline

The proxy_mean < 0.83 filter was supposed to create discriminative headroom. It didn't. Baseline aggregate came in at **0.9452**, leaving ~0.05 of dynamic range on a [0,1] scale. The pre-registered H1 threshold of +0.10 exceeded the total available headroom. The test was structurally impossible to pass regardless of protocol quality.

What's revealing: **Spearman rho = +0.046 (p=0.687)** between difficulty labels and actual performance. The direction is positive when it should be negative. The proxy scoring model (Claude Haiku smoke test) created a difficulty gradient that doesn't transfer to actual rubric performance — the benchmark was calibrated for the smoke test model's failure modes, not the evaluation model's. This is a closed-loop calibration problem nested inside the main experiment's closed-loop evaluation problem.

---

### 3. IDP is completely flat across conditions — and that's surprising

| Condition | IDP |
|---|---|
| isolated_debate | 0.8549 |
| multiround | 0.8580 |
| baseline | **0.8549** |

The adversarial structure was theoretically supposed to improve precision: a Defender explicitly challenging every critique claim should suppress false alarms. But IDP is essentially identical for isolated_debate and baseline. This isn't explained by the ceiling effect — IDP has room to vary (it's not at 1.0). The adversarial exchange isn't changing what claims get raised or credited. Either the orchestrator isn't using the Defender's challenges to filter critique claims, or the Defender's challenges aren't landing on the false positives.

---

### 4. Ensemble IDR suppression is a majority-vote artifact, not a recall deficit

| Aggregation | Ensemble IDR |
|---|---|
| Majority vote | 0.7679 |
| Union-of-issues | **0.8725** |

The individual assessors are finding the issues (union IDR ≈ isolated IDR). Majority-vote synthesis discards recall. When 2/3 assessors agree on the verdict but identify *different specific issues*, the conservative rule may not surface the planted issue even though it was found. The IDP advantage (0.9583 vs. 0.8549) is real and preserved under union IDR — the ensemble is genuinely better at not raising false positives. So the correct v6 aggregation rule is: **union-of-issues for IDR, majority-vote for verdict** — take the recall from any assessor while using the conservative rule for the final verdict.

---

### 5. The closed-loop confound is far worse than assumed

Cross-vendor validation (gpt-4o-mini) returned an IDR delta of **-0.7737**. That means gpt-4o-mini scored IDR ≈ 0.12 where Claude's rescorer scored 0.90 on the same outputs. These are not just calibration differences — they're evaluating different things. What Claude considers "identified the planted issue," gpt-4o-mini mostly does not credit.

The key nuance: **the lift calculation is still valid** because bias cancels when both conditions are scored by the same evaluator. But the absolute values in every table (IDR = 0.8969 for isolated_debate, etc.) are "Claude-evaluator-relative numbers," not objective quality measurements. This has a direct implication: any v6 result that reports a positive H1 is only as trustworthy as the evaluator family.

---

### 6. Zero-variance contamination detection is a practical diagnostic

The batch contamination was caught because affected files showed zero stochastic variance across 3 runs — identical outputs every run. This is a reliable signal that the agent had the answer key in context. This is worth keeping as a standard pipeline health check in any future multi-run LLM evaluation setup.

---

## Avenues for Further Investigation

### Avenue 1 (v6 — highest priority): Test ETD directly with mixed-verdict cases

The v6 `MIXED_CASE_PLAN.md` is already designed around this. The core question to answer: *Does the debate protocol produce better empirical test specifications on genuinely ambiguous cases?*

The key design constraint from `MIXED_CASE_PLAN.md`: the `condition` field in `ideal_debate_resolution` must be concretely measurable — not "it depends on the data" but "compute autocorrelation at lag 1 week; if > 0.4, temporal split is required." The quality of that constraint determines whether mixed cases are actually testing real ETD vs. trivial ambiguity.

**Watch for:** with 20 mixed cases × 3 debate conditions × 3 runs = 180 ETD observations, you have enough for per-condition ETD comparison. The hypothesis to test isn't H1 (aggregate lift) — it's specifically whether `multiround > isolated_debate` on ETD, because the back-and-forth exchange is where empirical test specification should emerge.

---

### Avenue 2: Break the closed loop — cross-model IDR scoring as the design target

The -0.7737 IDR delta is too large to ignore. v6 needs a non-Claude scorer for IDR/IDP to produce trustworthy absolute values. But there's a deeper question: **why is the delta so large?**

Three hypotheses worth probing:
- **Threshold calibration**: Claude's semantic scorer was trained to be permissive about "mentioning" an issue vs. "identifying" it; gpt-4o-mini requires more specific identification
- **Self-enhancement bias** (Panickssery et al.): Claude systematically credits Claude-generated text more
- **Issue description mismatch**: the planted issue descriptions were written in a Claude-idiomatic style that Claude recognizes more readily than gpt-4o-mini

You can probe H3 directly: take 10 cases, rewrite the `planted_issues` descriptions in neutral language vs. Claude-idiomatic language, rescore with both models, see if the delta shrinks. This is a low-cost experiment that could distinguish evaluator-family bias from description-format bias.

---

### Avenue 3 (RC reports): Replace synthetic benchmarks entirely

`DATA_ACQUISITION.md` describes using ML Reproducibility Challenge reports as ground truth. This is a qualitative leap in validity — real documented post-hoc flaws vs. LLM-generated planted corruptions.

The interesting methodological question: **does the debate protocol find flaws that human reproducers found, or does it find different flaws?** This opens up a bidirectional scoring question: you can score recall against documented flaws *and* score whether the debate surfaces novel valid concerns the reproducer missed. If the debate consistently finds things the reproducer missed on "mostly-sound" papers, that would be the strongest possible evidence for the protocol's value — and it's a form of ETD that can't be measured on a synthetic benchmark.

The complication flagged in the doc: RC reports skew toward definitive flaws, not mixed cases. You'd need to specifically find the "mostly sound but X is overstated" reports to get the mixed-case distribution needed for ETD testing.

---

### Avenue 4: Fix the IDP mystery

IDP flat at 0.8549 across isolated_debate, multiround, and baseline is underexplained. Two diagnostic experiments:

1. **Trace the Defender's challenges**: In multiround cases where the Defender explicitly challenged a critique claim that was a false positive, did the orchestrator's final verdict credit or discard that claim? If the orchestrator ignores the Defender's precision-raising challenges, that's an orchestrator design bug, not a protocol limitation.

2. **Check whether false positives are clustered**: Are the 15% of IDP-reducing false positive claims concentrated in specific case types, or distributed? If clustered, there may be a specific flaw category where the Critic systematically hallucinates issues that the Defender can't suppress.

---

### Avenue 5: Conditional forced multiround

The 20.5% hollow-round rate in FM is structural — defense_wins cases resolve in round 1, leaving nothing for round 2. The fix: *gate FM round 2 on a substantive disagreement signal from round 1 adjudication.*

The interesting implementation question: what constitutes a "substantive disagreement signal"? Options:
- Adjudicator explicitly marks one or more points as "unresolved"
- Round 1 verdict confidence is below a threshold
- The Defender's round 1 response length exceeds a threshold (proxy for substantive rebuttal)

This is testable with the existing v5 forced_multiround outputs: look at the 8 defense_wins cases with hollow rounds and check what their round 1 adjudicator outputs look like. If the adjudicator already signals "all points resolved" in round 1, you have the detection signal for free.

---

> **The most underappreciated finding:** the protocol never failed at the protocol level (0.0% protocol-level failure attribution). Every failure was agent-level. The debate machinery runs correctly; what's uncertain is whether *correct execution of the debate* is sufficient to produce better outcomes than no debate at all. That's a much more interesting question than "does the protocol fail" — it's asking whether the architecture is wrong, not whether the implementation is broken.
