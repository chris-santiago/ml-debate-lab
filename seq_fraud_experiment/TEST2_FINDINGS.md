# Test 2 Findings: Sequence Fraud Hypothesis

## Hypothesis
"An LSTM on ordered transaction category sequences outperforms a bag-of-categories baseline because fraud exhibits characteristic temporal patterns."

## Pipeline Trace Summary

### Steps 1–2 (PoC + Review): ✅ No spec issues
- HYPOTHESIS.md template produced clean artifact
- PoC followed all rules (PEP 723, deliberately leaving out, visualization)
- AP = 0.96 vs 0.05 prevalence — initial result looks strong

### Steps 3–4 (Critic/Defender): ✅ No spec issues
- Critic produced 4 numbered issues with three-part structure
- Key critique: shuffled LSTM is wrong control, category distribution may explain signal
- Defender conceded 3 of 4, marked 1 as empirically open
- Counter-proposal on the empirically open point led to productive debate

### Step 5 (Debate): ✅ No spec issues
- One round resolved the contested point (three-condition experiment design)
- Conceded points correctly fed into experiment design (count-vector LR, trivial baseline)
- Empirical test list had clear pre-specified verdicts

### Steps 6–7 (Experiment): ✅ Spec handled a complex failure correctly
Results:
- Test 1 (randomized phases): AP drops 0.96 → 0.68. **Critique wins.** Phase position was significant signal.
- Test 2 (three conditions):
  - A (ordered LSTM): 0.96
  - B (count-vector LR): 0.12
  - C (equalized distribution): 1.00 ⚠️ SUSPICION TRIGGERED
  - Verdict: Defense wins on A vs B, but C is broken
- Test 3 (trivial baseline): Model beats threshold by 0.88. **Defense wins.**

The suspicion trigger (added from Test 1 trace) correctly fired on Condition C.
Agent would investigate → find that sort() makes sequences trivially detectable.
This is a micro-iteration trigger: "evaluation design flaw discovered."

Micro-iteration: Redesigned Condition C with soft-sort (Gaussian noise on ranks).
Result: AP = 0.996 — still suspiciously high.

**Key insight the spec helped surface:** The equalized-distribution test is fundamentally flawed for synthetic data. ANY imposed ordering is distinguishable from random sequences because LSTMs detect sequential structure. This isn't a fixable design flaw — it's a limitation of the experimental approach.

### Macro-iteration check: ✅ Spec correctly identifies Outcome C
The finding "any temporal ordering is trivially detectable" means the hypothesis is asking the wrong question. The mechanism needs reformulation:
- Original: "fraud exhibits temporal patterns that ordering captures"
- Revised: "fraud exhibits SPECIFIC temporal patterns (test→probe→extract) that add signal beyond what category frequency and general ordering capture"

The spec's Outcome C triggers correctly match:
- "Wrong observable" — we're measuring whether ordering exists, not whether fraud-specific ordering adds value
- "New hypothesis generated" — the experiment suggests the real question is about pattern specificity, not ordering existence

### HYPOTHESIS.md Cycle 2 (what would be written)
**Claim:** Fraud accounts exhibit a specific temporal signature (low-value test transactions → rapid category switching → high-value extraction) that is distinguishable from both random ordering and generic monotonic trends.
**Mechanism:** The fraud pattern is not just "ordered" but specifically shaped — the three-phase structure is the signal, not ordering per se.
**Signal:** Phase transition detection in category sequences.
**Expected observable:** An LSTM trained on fraud sequences outperforms both a bag-of-categories model AND an LSTM trained on generically-ordered (non-fraud) sequences.

---

## Spec Features That Proved Their Value

1. **Near-perfect metrics suspicion trigger** — caught Condition C immediately. Without this, the agent might have reported C = 1.0 as "defense wins conclusively."

2. **Micro-iteration cycle** — correctly identified the design flaw and triggered re-run. The fixed version ALSO triggered suspicion, leading to the deeper insight.

3. **Macro-iteration Outcome C** — correctly identified that the hypothesis needs reformulation, not just more experiments. The distinction between "return to debate" and "return to hypothesis" was load-bearing.

4. **Concession incorporation** — the count-vector LR (from conceded Point 2) was essential to the experiment. Without it, the only comparison would have been ordered vs shuffled LSTM, which the critique correctly identified as a weak control.

5. **Three-condition experiment design from debate** — the A/B/C structure surfaced the fundamental problem (C is trivially solvable) that a simpler A vs B comparison would have missed.

6. **Pre-specified verdicts** — prevented post-hoc rationalization. When C = 1.0, the agent couldn't claim "defense wins" because the pre-specified criterion required BOTH A > B and C > B, and C's result was flagged as suspicious before being counted.

## Spec Issues Found

**None new.** The two fixes from Test 1 (suspicion trigger + concession incorporation) were both validated here. The spec handled this significantly more complex scenario correctly, including:
- Mixed verdicts across tests
- A broken experimental condition requiring micro-iteration
- A fundamental design limitation requiring macro-iteration
- The distinction between fixable flaws and hypothesis-level problems
