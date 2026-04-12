# DEBATE.md — Self-Debate Protocol v3 Experimental Design

**Initialized from:** CRITIQUE.md vs DEFENSE.md
**Protocol:** ml-critic (Mode 2) and ml-defender (Mode 2) alternate until all points resolve or Round 4 is exhausted. Unresolved points at Round 4 are force-resolved as `empirical_test_required`.

---

## Contested Points — Initial State

The following issues from CRITIQUE.md were not conceded or fully rebutted in DEFENSE.md. They carry forward as contested.

| Point | Issue | Critic Position | Defender Response | Status |
|-------|-------|-----------------|-------------------|--------|
| P1 | DC=FVC double-counting inflates case mean and threshold | Inflation is real; primary threshold overstates coverage | Conceded; inflation is real | **Resolved: critic wins** |
| P2 | Effective dimensionality is 3-4, not 6 | Threshold calibration reflects wrong dimensionality | Conceded | **Resolved: critic wins** |
| P3 | Isolated debate mechanism claim is imprecise | "Adversarial role separation" requires interaction; isolated = two parallel critics | Rebutted: asymmetric instructions are the mechanism, not interaction; but wording needs fix | **Contested** |
| P4 | No power analysis for +0.10 threshold | Threshold could be noise; no pre-specified test | Empirically open; substantive threshold is separate from statistical significance | **Contested** |
| P5 | DC=0.0 override suppresses baseline; primary threshold should be honest lift | Primary criterion should be stated against honest lift | Partial concede: honest_lift is right; primary hypothesis should reference honest lift | **Contested** |
| P6 | ETD constraint not operationally locked | ETD comparison confounded without verbatim instruction text | Conceded; must be in EXECUTION_PLAN.md | **Resolved: critic wins** |
| P7 | Generator fingerprinting could inflate IDR | Must_find vocabulary may correlate with task_prompt | Rebutted: affects all conditions equally; external_cases cross-check available | **Resolved: defender wins** |
| P8 | Category field leaks correct_position | High-severity leakage risk if category passed to agents | Conceded; must be confirmed before any run | **Resolved: critic wins** |
| P9 | DRQ filter not enforced in scoring engine | Stats_analysis.py is not committed; filter unspecified | Conceded; must be locked before execution | **Resolved: critic wins** |
| P10 | Convergence metric not implemented | Pre-registration gap | Conceded | **Resolved: critic wins** |

**Points carrying into debate rounds: P3, P4, P5**
**Pre-resolved (concede/critic wins): P1, P2, P6, P8, P9, P10**
**Pre-resolved (defender wins): P7**

---

### Critic — Round 1

Addressing contested points P3, P4, P5.

**P3 — Isolated debate mechanism:**

The defender's rebuttal replaces one mechanism with a different one. "Asymmetric role instructions" as the mechanism is a valid and more honest description, but it does not rescue the original claim. The original HYPOTHESIS.md states: "By requiring an independent defense of the presented work *before any critique is seen*, the protocol surfaces considerations that a single correlated assessor would suppress or conflate." This is explicitly framed as a structural forcing function — the Defender must defend *before seeing critique*. But in isolated_debate, the Defender is not responding to critique — the Defender does not know critique exists. It is producing a defense of a methodology it has not seen criticized. That is not "surfacing considerations that would be suppressed" — it is a blind assessment with a defend-oriented system prompt. The actual test is: does a defend-oriented prompt produce different outputs than a criticize-oriented prompt, and does the synthesized combination outperform either alone? That is a question about prompt ensemble effects, not adversarial role separation. The mechanism statement in HYPOTHESIS.md needs to be corrected in the execution plan, not just noted.

**P4 — Power analysis:**

The defender's response separates substantive and statistical significance, which is a valid distinction. But "substantive threshold" does not resolve the concern — it relocates it. The question is whether +0.10 is a threshold that the protocol has a reasonable probability of achieving given the expected variance. If the expected variance across 49 cases means the benchmark mean could plausibly swing ±0.08 between run batches, a +0.10 threshold is near the noise floor. The concrete resolution: pre-specify a bootstrap confidence interval (e.g., 95% CI on the lift must exclude 0.0) alongside the point-estimate threshold. This does not require a formal power calculation — it requires committing to a CI check in addition to the point estimate. Without it, a lift of +0.10 with a 95% CI of [-0.02, +0.22] would "pass" the pre-registered criterion while being statistically uninformative.

**P5 — Primary threshold vs. honest lift:**

The defender partially concedes but argues that reporting both raw and honest lift satisfies the requirement. This is insufficient. A pre-registration specifies the primary success criterion in advance. If the primary criterion is the raw lift (+0.10 including DC suppression), the experiment can "pass" the primary hypothesis even if the honest lift is +0.04. That outcome would be presented as a positive result but would not survive a read that accounts for the structural override. The fix is simple: state the primary hypothesis as requiring both raw lift >= +0.10 AND honest lift >= +0.10. This costs nothing if the debate protocol genuinely works and prevents a false positive if the lift is entirely attributable to baseline suppression.

---

### Defender — Round 1

**P3 — Mechanism restatement:**

The critic's restatement is accurate and I adopt it. The correct mechanism is: asymmetric role instructions produce complementary coverage biases that the synthesizer combines. The "independent defense before critique is seen" framing in HYPOTHESIS.md does not describe the isolated_debate condition correctly — it describes the multiround condition's setup. HYPOTHESIS.md should be understood as describing the mechanism for the full experimental design (which includes multiround), not exclusively the isolated condition. The isolated condition tests whether role-assignment alone (without exchange) produces better coverage than a single-pass Critic. The multiround condition tests whether adversarial exchange on top of role-assignment adds further value. Both are measured, and the mechanism for each is distinct. The EXECUTION_PLAN.md should clarify this distinction.

**P4 — CI requirement:**

The critic's proposed resolution is operationally sound and I accept it: pre-specify a 95% bootstrap CI on the lift, requiring CI lower bound > 0.0 as a secondary condition alongside the point-estimate threshold. This should be locked in EXECUTION_PLAN.md as: "Lift is considered meaningful if: (a) point estimate >= +0.10 AND (b) 95% bootstrap CI lower bound > 0.0." Adding (b) costs nothing if the lift is real.

**P5 — Honest lift as co-primary:**

The critic's proposed fix is correct and I adopt it. The primary success criterion should require both raw lift >= +0.10 AND honest lift >= +0.10 (where honest lift applies DC=0.5 and uncapped DRQ to baseline). This closes the loophole where the hypothesis "passes" on structural suppression alone. Adding this requirement to EXECUTION_PLAN.md is the right resolution.

---

### Resolution After Round 1

| Point | Resolution |
|-------|-----------|
| P3 | **Resolved: empirical_test_agreed** — Mechanism is prompt ensemble effect (asymmetric roles); EXECUTION_PLAN.md must clarify isolated vs. multiround mechanism separately. The empirical test: if isolated_debate and a second-Critic run with same inputs produce statistically indistinguishable aggregate means, the mechanism is prompt bias not adversarial structure. |
| P4 | **Resolved: defender concedes** — Pre-specify 95% bootstrap CI lower bound > 0.0 as co-condition alongside +0.10 point estimate. Lock in EXECUTION_PLAN.md. |
| P5 | **Resolved: defender concedes** — Primary success criterion requires both raw lift >= +0.10 AND honest lift >= +0.10. Lock in EXECUTION_PLAN.md. |

---

## Final Resolution Summary

| Point | Issue | Final Status | Action Required |
|-------|-------|-------------|-----------------|
| P1 | DC=FVC double-counting | Critic wins | Report corrected mean (4 independent dims) alongside 6-dim mean |
| P2 | Effective dimensionality 3-4 | Critic wins | Note effective dim count per case type in EXECUTION_PLAN.md |
| P3 | Isolated debate mechanism | Empirical_test_agreed | EXECUTION_PLAN.md: clarify isolated=role-bias, multiround=adversarial exchange; add isolated vs. second-Critic comparison as diagnostic |
| P4 | Power analysis | Defender concedes | Add 95% bootstrap CI lower bound > 0.0 as co-condition in EXECUTION_PLAN.md |
| P5 | Primary threshold vs. honest lift | Defender concedes | Primary criterion = raw lift >= +0.10 AND honest lift >= +0.10 |
| P6 | ETD constraint not locked | Critic wins | Verbatim ETD instruction in EXECUTION_PLAN.md before any run |
| P7 | Generator fingerprinting | Defender wins | External cases cross-check; report IDR comparison in CONCLUSIONS.md |
| P8 | Category field leakage | Critic wins | Confirm agent dispatch passes task_prompt only; document in EXECUTION_PLAN.md |
| P9 | DRQ filter not in scoring | Critic wins | Lock non-defense_wins filter in stats_analysis.py spec before execution |
| P10 | Convergence not implemented | Critic wins | Add to scoring engine or specify post-processing schema in EXECUTION_PLAN.md |

All 10 points resolved within 1 full debate round. No force-resolution required.
