# DEFENSE.md — Self-Debate Protocol v2

## Defense — Cycle 1

**Defender:** Original designer of the self-debate protocol PoC.
**Mode:** Initial defense (Mode 1) — point-by-point rebuttal of anticipated adversarial critique.

---

### Objection 1: The benchmark design is circular — you wrote the cases, defined the rubric, and scored the transcripts. The ground truth is whatever you decided it was.

**Verdict: Partially concede, partially rebut. The circularity risk is real but structurally contained.**

The circularity concern has two components that must be separated.

The first component — that the benchmark designer also controls the ground truth — is true and not deniable. The `must_find` issues and `correct_position` labels were assigned by the same investigator who designed the evaluation protocol. There is no independent third-party validation of the benchmark ground truth. This is a genuine limitation.

The second component — that the rubric scores are circular because they were assigned with knowledge of which system is being evaluated — is rebutted by the scoring architecture. The Scorer agent receives the ground truth rubric alongside all agent transcripts and is asked to evaluate each dimension independently. The scoring is not done by the investigator interpreting free-form outputs; it is done by a separate LLM call with explicit dimension criteria. The Scorer does not know it is being asked to validate a hypothesis — it is evaluating whether, for example, the `must_find` issues appear in the Critique output. This is not perfect independence, but it is not circular: the Scorer can and does assign 0.0 scores to the debate protocol (as in real_world_framing_001 DC=0.0).

The more pointed version of the circularity objection is whether the benchmark cases were constructed to favor the debate protocol. This is empirically addressable: the experiment included 5 defense_wins cases where the single-pass baseline structurally cannot score above 0.0 (DC is undefined for a system with no defense role, and DRQ/FVC require a correct verdict). If the benchmark were constructed to maximize debate scores, we would expect debate scores to be uniformly high. Instead, the debate protocol fails on real_world_framing_001 and shows partial failures on defense_wins_003 and _005 — cases that the protocol was specifically designed to handle. A rigged benchmark does not produce a failed case in a newly added category.

**What this does not address:** An independent, externally constructed benchmark with external ground truth validators would resolve the circularity concern definitively. That experiment has not been run. The current results are best interpreted as an internal validity check, not an externally validated claim.

---

### Objection 2: 20 cases is not a sufficient sample to support the stated conclusions. The +0.586 lift could be noise.

**Verdict: Empirically open. The argument for sufficiency is structural, not statistical.**

The statistical version of this objection would note that with n=20 and no reported confidence intervals, the +0.586 lift estimate has unknown uncertainty. This is correct. The paper does not report CIs, and no power calculation was performed. This is a real gap.

The design-intent rebuttal is that the benchmark is not a random sample from a population of ML reasoning tasks — it is a curated set of task types covering six distinct categories of methodological failure. The question the benchmark answers is not "what is the expected lift over random tasks?" but "does the protocol demonstrate structural advantages across the predefined failure categories?" On that narrower question, the 20-case result is informative: the protocol produces correct verdicts in 19 of 20 cases across all six categories, while the baseline fails in 18 of 20.

The concern about noise is most applicable to cases near the decision boundary. The debate mean of 0.970 is well above the 0.75 hypothesis threshold, and the baseline mean of 0.384 is well below the 0.60 expected ceiling. A result that reverses these findings with expanded n would require very large failures in new cases — which is possible but not suggested by the within-category consistency.

The strongest honest position: 20 cases is sufficient to confirm that the protocol's structural advantages exist and are large. It is not sufficient to estimate the expected lift across arbitrary real-world ML reasoning tasks, or to establish that the lift would hold on a randomly sampled benchmark.

**What would confirm the objection:** Adding 20 randomly sampled ML reasoning tasks (not curated by the protocol designer) and observing that the lift drops below +0.10. This test has not been run.

---

### Objection 3: The baseline is not a fair comparison. A more capable single-pass prompt, a chain-of-thought baseline, or a multi-turn self-critique baseline would close the gap.

**Verdict: Partially concede. The baseline is deliberately minimal. The gap to a stronger baseline is unknown.**

The single-pass baseline is explicitly described as "trivial" in the hypothesis. This was an intentional design choice: the hypothesis was framed as a claim about protocol structure (debate vs. no debate), not a claim about the best achievable single-pass performance. The trivial baseline provides a floor, not a ceiling.

The concession: a chain-of-thought baseline or a multi-turn self-critique baseline (where the model generates a critique and then revises its own answer) would likely perform better than the trivial baseline on several dimensions — particularly issue_discovery_recall and final_verdict_correctness on easy cases. The gap between the debate protocol and a well-engineered single-pass prompt is unknown. The experiment does not test this.

The rebuttal: the defense_wins cases represent the most important test of protocol structure, and no single-pass baseline — regardless of how it is prompted — can structurally produce a `defense_wins` verdict. This is not a promptability issue. A single-pass system that receives a task prompt has no mechanism to independently challenge an adversarial framing embedded in its own context. The DC=0.0 result for the baseline on all 20 cases is structural, not a prompting failure. The most important finding in this experiment — that the protocol exonerates valid work while the baseline condemns it — would survive a stronger baseline comparison.

**Where the objection has force:** On the IDR, FVC, and DRQ dimensions for non-defense_wins cases, a stronger baseline might close the gap significantly. The ETD gap is already minimal (0.067). A well-prompted chain-of-thought baseline might achieve IDR ≥ 0.80 on easy and medium cases, reducing the overall lift substantially. This has not been tested.

---

### Objection 4: The convergence result (easy=0.833, medium=0.944, hard=0.938) is post-hoc rationalization. The hypothesis predicted easy > hard. The result reversed. The authors' explanation — that difficulty reflects reasoning depth, not discoverability — was not pre-registered.

**Verdict: Concede that the explanation is post-hoc. Rebut the claim that this invalidates the result.**

The secondary hypothesis predicted that convergence would decrease with difficulty. The result does not support this prediction: hard cases show convergence 0.938, slightly below medium (0.944) but above easy (0.833). The authors' explanation — that the easy convergence decrement is driven by defense_wins_003 and _005 verdict calibration failures, not by issue discovery difficulty — is not wrong, but it was not stated in the pre-registered hypothesis.

The honest accounting: this is a secondary hypothesis that was not supported. The result should be recorded as "not supported" and the post-hoc explanation treated as a hypothesis to be tested in a follow-on experiment, not as a confirmed finding.

The rebuttal to the claim that this invalidates the primary result: the convergence finding is a secondary diagnostic, not a primary outcome. The primary hypothesis (lift ≥ +0.10) is supported by a different set of measurements (debate_mean, case_pass_fraction, lift). The convergence non-result does not bear on the primary outcome. A failed secondary hypothesis alongside a supported primary hypothesis is the normal output of a well-specified experiment.

The post-hoc explanation is also internally consistent with the data: when only non-defense_wins cases are examined, hard cases show convergence 1.0 across all 8 instances. The confound between difficulty tier and case category (defense_wins cases cluster in easy/medium) is real and the experimenters identified it correctly — even if they identified it after the fact.

**What would confirm the post-hoc explanation:** A follow-on experiment with difficulty tiers balanced across case categories (i.e., hard defense_wins cases and easy confounding cases) would test whether the easy-hard convergence gradient is genuine or a category artifact. defense_wins_004 (hard) already shows convergence 1.0, which is consistent with the post-hoc explanation.

---

### Objection 5: The lift could be explained by token count / extra compute rather than debate structure. The debate protocol uses 3-5x more tokens than the baseline. More tokens equals more reasoning, regardless of structure.

**Verdict: Empirically open. This is the most serious confound in the experiment and it is not addressed.**

This objection is structurally correct. The debate protocol generates: Critique output + Defense output + Judge output. The baseline generates: a single-pass assessment. The token count for the debate protocol is approximately 3-4x higher than the baseline. If reasoning quality scales with token count — a finding that is documented in the literature on chain-of-thought and extended thinking — then the lift could be partially or wholly explained by compute budget, not by the adversarial structure.

The defense can identify two structural arguments that are not fully explained by token count:

First, the defense_wins result. The baseline cannot produce correct `defense_wins` verdicts regardless of how many tokens it generates, because it has no mechanism to independently challenge an adversarial premise. The DC=0.0 result for the baseline is structural. However, a budget-matched chain-of-thought baseline that was prompted to explicitly consider whether the critique is valid would need to be tested to confirm this.

Second, the independent issue discovery finding. On hidden_confounding_002 and hidden_confounding_003, the baseline scored IDR=0.0 despite having access to the full task prompt. The issues (holiday season confound, document-level data leakage) are present in the task prompt text. A longer single-pass response would not necessarily identify issues that are invisible to shorter single-pass reasoning — but a budget-matched baseline could.

**What would resolve this empirically:** A token-budget-matched baseline (single-pass, same token budget as the debate protocol's combined output) tested on the same 20 cases. If the lift survives budget-matching, the structural advantage claim is substantially stronger. If the lift disappears, the finding is compute-budget, not debate structure. This test has not been run.

This is the most important follow-on experiment the protocol needs.

---

### Objection 6: Claiming that the two observed failure modes are "tractable prompt-level fixes" is too optimistic. The reasoning/label disconnect in real_world_framing_001 and the under-confidence in defense_wins_003 and _005 could be fundamental limitations of single-model self-debate.

**Verdict: Rebut for failure mode 2. Partially concede for failure mode 1.**

**Failure mode 1 (real_world_framing_001: reasoning/label disconnect).** The authors' claim that this is fixable with a two-pass Defender design or more explicit verdict labeling guidance is plausible but not demonstrated. The defender correctly analyzed all the flaws in the text but then labeled `defense_wins` — contradicting its own analysis. This could reflect:

(a) A prompt ambiguity: the Defender role is associated with defending work, creating label bias. This is fixable with prompt revision.

(b) A deeper model limitation: the model cannot maintain consistency between extended analysis and a terminal verdict label, particularly when the role identity pulls in the opposite direction. This would not be fixable with prompt revision alone.

The report opts for interpretation (a) without testing (b). The proposed fix (a two-pass Defender) has not been tested. Calling this "tractable" before testing the fix is premature. The concession is that this failure mode could be more fundamental than the authors acknowledge.

**Failure mode 2 (defense_wins_003, _005: Defender under-confidence).** The claim that this is a prompt-level fix is better supported. The specific failure is: the Defender correctly identified the sound methodological aspects but stopped at `empirical_test_agreed` rather than `defense_wins`. The cases involved 5-fold stratified CV on 8,500 examples and same-system evaluation for same-system deployment. Both are cases where the distinction between "limitation that warrants more testing" and "limitation that does not falsify the claim" is codifiable in a prompt. The proposed fix — "If the methodology is sound for the stated scope and the limitations are real but not disqualifying, your verdict is defense_wins" — is specific and testable. Calling this tractable is reasonable, with the caveat that the fix has not been tested.

**The deeper concern:** Both failure modes occur in the Defender role. If the Defender is systematically biased — either toward defending (label bias in failure mode 1) or toward hedging (under-confidence in failure mode 2) — then the system has a role-level calibration problem that prompt changes may not fully resolve. A model that is simultaneously biased toward `defense_wins` in one context and biased away from it in another is exhibiting context-dependent calibration failure. Whether this pattern is systematic or case-specific requires more cases.

---

### Objection 7: The defense_wins result is a tautology. The protocol was designed to produce defense_wins verdicts. Of course it succeeds — the design guarantees it.

**Verdict: Rebut. The objection conflates design intent with experimental result.**

The objection is: the isolated protocol (Defense receives only task_prompt, never Critique output) was specifically designed to enable `defense_wins` verdicts. Therefore the result — that the protocol correctly produces `defense_wins` verdicts — is predetermined by design, not a discovery.

This confuses two distinct questions:

**Question 1:** Can the isolated protocol structurally produce `defense_wins` verdicts?  
**Answer:** Yes, by design. The isolation prevents the Defender from inheriting the Critic's premise, which is the necessary condition for genuine defense.

**Question 2:** Does the Defender, when independently evaluating the task prompt, correctly identify that the work is sound and commit to `defense_wins` against an adversarial framing?  
**Answer:** This is an empirical question that the design does not predetermine. The Defender receives the task prompt — which includes the claim being assessed — but does not receive the Critic's adversarial framing. The Defender must independently evaluate the methodology. It could fail by: (a) independently generating its own critique of sound work, (b) equivocating and stopping at `empirical_test_agreed`, or (c) correctly identifying soundness and reaching `defense_wins`.

Outcomes (a) and (b) both occurred in this experiment. defense_wins_003 and _005 produced outcome (b): the Defender correctly identified sound aspects but hedged, yielding DC=0.5. This would not happen in a tautological design — a tautological design would guarantee DC=1.0 on all defense_wins cases. The fact that DC was 0.5 on two of five cases, and that the baseline scored DC=0.0 on all five, is empirical, not structural.

The tautology objection is strongest for the FVC and DRQ dimensions on defense_wins cases: if the Defender says `defense_wins` and the Judge accepts it, those dimensions score 1.0. But this is not guaranteed — the Judge receives both the Critic's output and the Defender's output and must adjudicate. On cases where the Critic made a strong adversarial argument and the Defender equivocated, the Judge could side with the Critic. That it did not on defense_wins_003 and _005 (despite DC=0.5) is a result that required the Judge's adjudication to be evaluated.

The correct framing: the isolated protocol is a necessary condition for `defense_wins` verdicts. It is not a sufficient condition. The empirical contribution is demonstrating that the Defender can, in most cases, identify sound work without being misled by the adversarial framing.

---

## Summary Table

| Objection | Verdict | Summary |
|-----------|---------|---------|
| Benchmark circularity | Partially concede / Partially rebut | Ground truth is designer-controlled; scoring is not circular; no externally validated benchmark exists yet |
| N=20 insufficient | Empirically open | Structural advantages are large and consistent; lift to a random sample is unknown |
| Baseline too weak | Partially concede | Trivial baseline is intentional; defense_wins advantage is structural and survives any baseline; IDR gap to CoT baseline is unknown |
| Convergence result is post-hoc | Concede (secondary), rebut (primary impact) | Convergence explanation is post-hoc; it does not affect primary outcome |
| Token count confound | Empirically open | Most serious unaddressed confound; budget-matched baseline has not been run |
| Failure modes are tractable | Partially concede (FM1), rebut (FM2) | Two-pass fix for reasoning/label disconnect is untested; under-confidence fix is specific and plausible |
| Defense_wins is tautological | Rebut | Design enables defense_wins path; model achieving it is empirical; partial failures (DC=0.5 on two cases) confirm it is not predetermined |

---

**Most important unresolved questions, in order of impact on the primary claim:**

1. Token-budget-matched baseline (Objection 5) — would establish whether the lift is structural or compute.
2. Externally constructed benchmark (Objection 1) — would establish external validity.
3. Two-pass Defender fix tested on real_world_framing cases (Objection 6) — would confirm tractability of failure mode 1.
