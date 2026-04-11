# Peer Review Round 1 — v5 Self-Debate Experiment Report

*Reviewer: research-reviewer (Opus). Conducted on REPORT.md prior to final revisions.*

---

## Summary

This report evaluates whether an adversarial self-debate protocol (critic vs. defender roles) produces better ML methodology verdicts than single-pass review, testing 110 synthetic benchmark cases across five conditions with three runs each. The primary hypothesis (H1: fair-comparison lift >= +0.10) fails, with observed lift of +0.0097 and a bootstrap CI spanning zero.

---

## Strengths

- **Honest negative result with pre-registration.** The report leads with H1 failure and reports fc_lift as the primary metric, consistent with its pre-registered design. The sensitivity analysis (Method A/B, bootstrap bounds, DC inclusion) demonstrates the verdict is robust to scoring variations.
- **Thorough contamination handling.** The answer-key leakage (Limitation 4) and batch contamination (Limitation 5) are documented with detection mechanism, remediation, and scope. This is exemplary provenance tracking for an LLM-based experiment.
- **Structured limitations section.** The (a) Threat / (b) Evidence / (c) Mitigation format is rigorous and goes well beyond the typical "future work" hand-wave. Each limitation is scoped with quantitative evidence.
- **Failure mode taxonomy.** The attribution breakdown (agent vs. protocol vs. ambiguous) with per-file counts adds genuine analytical value beyond aggregate scores.

---

## Critical Issues

**[MAJOR] The H1 threshold was structurally impossible to meet, undermining the "definitive" verdict.** Limitation 6 acknowledges that baseline performance (0.9452) leaves ~0.05 headroom on a [0,1] scale, yet the pre-registered threshold was +0.10. A test that cannot pass by construction is uninformative, not "definitive." The Conclusions paragraph 1 ("provides a definitive negative result") and the final sentence ("its operational value in less controlled settings is unlikely to be higher") both overclaim given this structural impossibility. The report must distinguish between "the protocol does not help" and "this benchmark could not detect whether the protocol helps."

**[MAJOR] Cross-vendor results are misinterpreted as partially mitigating the closed-loop confound.** An IDR delta of -0.7737 means gpt-4o-mini scores IDR near 0.12 where Claude scores 0.90. The report describes this as "model-specific threshold differences" (Phase 9 Interpretation) and claims cross-vendor scoring "partially mitigates" the closed-loop evaluation confound (Limitation 1c). A delta this large demonstrates the confound is *worse* than assumed: the absolute values in Tables A and B are evaluator-dependent to a degree that makes them unreliable as standalone numbers. The report should reframe Phase 9 as *revealing* the severity of the confound, not mitigating it.

**[MAJOR] "The protocol works" (Conclusions, para 1) lacks an external referent.** Claiming the protocol "works" based on a 0.9549 benchmark mean and 89.1% pass rate is circular when the scoring rubric, benchmark, and evaluator were all designed for this specific model and protocol. Without an external standard of what constitutes "working," this claim has no grounding.

---

## Minor Suggestions

**Related work section is thin and partially ungrounded.** Irving et al. (2018) studies safety-via-debate with a human judge; the connection to automated ML methodology review is not made explicit. The ChatEval reference lacks author and year. Missing entirely: LLM-as-judge reliability literature (directly relevant given the Phase 9 IDR delta) and prior work on automated code/methodology review. The related work does not discuss any prior evidence on whether LLM scorers agree with each other, which is the central confound the experiment discovered.

**Overclaimed generalization in final sentence of Conclusions.** "Its operational value in less controlled settings is unlikely to be higher" extrapolates from binary-verdict cases scored by a single model family to all operational settings. The report itself (Limitation 3) acknowledges mixed cases are the scenario most relevant to the mechanism claim, making this generalization unsupported.

---

## Prioritized Recommendations

1. Reframe the H1 verdict from "definitive negative" to "inconclusive due to ceiling effect." Add a paragraph in Conclusions distinguishing the two interpretations and stating that H1 cannot be meaningfully tested at the observed baseline performance level.
2. Revise Phase 9 Interpretation and Limitation 1c to characterize cross-vendor results as *evidence of confound severity*, not mitigation. State explicitly that the absolute dimension values in Tables A and B should not be treated as calibrated measurements.
3. Remove or qualify the "the protocol works" claim — scope it to rubric-relative performance only.
4. Strengthen related work: add LLM-as-judge reliability references; provide author and year for ChatEval; acknowledge the Irving et al. human-judge disanalogy.
5. Scope the final Conclusions sentence to the experimental conditions: binary-verdict cases, Claude-family models, ARCH-1 benchmark.

---

## Response

*All MAJOR and minor findings addressed. Summary of changes applied to REPORT.md:*

**M1 — Structural impossibility / "definitive negative":** The Conclusions opening paragraph was rewritten to characterize the result as "inconclusive, ceiling-limited" rather than "definitive negative." The distinction between "protocol does not help" and "benchmark could not detect whether the protocol helps" is now explicit. The H1 verdict section was updated with the qualifier "ceiling-limited" and an explanation that the +0.10 threshold exceeds the ~0.05 headroom available at the observed baseline level.

**M2 — Cross-vendor confound framing:** The Phase 9 Interpretation section was rewritten to lead with "Phase 9 does not mitigate the closed-loop confound --- it reveals its severity." Limitation 1c was relabeled from "Mitigation" to "Status" and reframed to state that the cross-vendor results demonstrate the confound is more severe than assumed. The reference to Panickssery et al. (2024) on self-enhancement bias was added to provide mechanism. Both Tables A and B are now flagged as Claude-evaluator-relative scores.

**M3 — Circular "works" claim:** The phrase "The protocol works" was replaced with qualified language scoped to rubric-relative performance: "The protocol produces outputs that pass the experiment's own rubric at a high rate (89.1% pass, benchmark mean 0.9549), but the rubric, benchmark, and evaluator were all designed for this specific model and condition --- this is necessary but not sufficient evidence of operational value."

**Minor — Related work:** ChatEval attributed to Chan et al. (2023). Panickssery et al. (2024) added as LLM-as-judge reliability reference. Irving et al. (2018) human-judge disanalogy made explicit with a note that this experiment departs from that setting by using a fully automated evaluator with no external epistemic anchor.

**Minor — Final sentence scope:** The final Conclusions sentence was replaced with a statement explicitly scoped to the tested conditions: binary-verdict cases, Claude-family models, ARCH-1 benchmark.

*Round 2 peer review not required — all MAJOR issues are structural framing corrections that do not require new data or analysis. The revised REPORT.md reflects all recommended changes.*
