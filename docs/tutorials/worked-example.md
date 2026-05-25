# Worked Example: LLM Preambles

This tutorial walks through a real investigation that used ml-lab to test whether coding-agent preambles measurably change code quality. The investigation was run in the [llm-preamble](https://github.com/chris-santiago/llm-preamble) repository and produced a statistically significant result (p = 9.2 x 10^-18^) with a refined mechanism explanation.

Every artifact referenced below is real — nothing was fabricated for this tutorial.

## The hypothesis

The investigation started with a question: *do coding-agent preambles affect the quality of generated code?* The initial hypothesis was sharpened through conversation into a falsifiable claim:

> Production-realistic preambles (including reasoning-inclusive models) move craft-quality dimensions but not capability dimensions, as measured by an LLM-judge rubric.

## Step 1: Build a proof-of-concept

ml-lab's first step is always a minimal PoC — just enough code to prove the measurement is possible. The preamble investigation's PoC generated 6 code samples across 3 preamble conditions and judged them with 18 LLM judge calls. Total cost: ~$0.01.

```
preamble_quality_v2_poc.py
├── 3 preamble conditions (none, expert_coder, long_directive)
├── 2 tasks × 1 rep per condition = 6 generations
└── 3 judges per generation = 18 judge calls
```

The PoC confirmed that (a) models produce measurably different code under different preambles, and (b) the LLM judge rubric can detect the difference. That's enough to proceed.

## Step 2: Adversarial review

With the PoC in hand, ml-lab dispatched `ml-critic` for a Stage A round-1 critique. The critic found 7 issues:

| ID | Severity | Finding |
|----|----------|---------|
| F1 | FATAL | Score clamping bug — rubric dimension scores were silently clamped to \[0, 5\] before validation |
| F2 | FATAL | No trap task — baseline smell rate could be 0%, making severity scores meaningless |
| F3 | MATERIAL | Subject pool too narrow — 7 non-reasoning models only |
| F4 | MATERIAL | Single-judge scoring lacks reliability estimate |
| F5 | MATERIAL | Rubric dimensions not validated against actual prevalence |
| F6 | MINOR | No explicit reasoning parameter logging |
| F7 | MINOR | Missing provider metadata in generation records |

`ml-defender` responded with structured rebuttals using the 7-type taxonomy:

- **F1: CONCEDE** — the clamping bug was real and had to be fixed before the main run
- **F2: DEFER** — agreed to add a trap task as a pre-flight check
- **F3: REBUT-SCOPE** → eventually CONCEDE — pool was expanded from 7 to 10 models (adding 3 reasoning models)
- **F4: REBUT-DESIGN** → eventually CONCEDE — restored 10-judge cross-judge panel
- **F5: DEFER** — added rubric prevalence audit to pre-flight
- **F6–F7: CONCEDE** — minor instrumentation fixes

Three rounds of Stage B debate (`ml-critic-r2` challenging each rebuttal, `ml-defender` responding) converged on all 7 findings resolved.

!!! tip "The value of adversarial review"
    The F1 finding (clamping bug) was a genuine show-stopper that would have invalidated the entire experiment. The PoC appeared to work — the bug was silent. Without structured adversarial review, it would have shipped to the main run.

## Step 3: Pre-flight and pre-registration

The debate produced a Gate 1 plan with 13 captured decisions and a pre-flight checklist:

1. Fix the clamping bug (F1)
2. Add a trap task with 0% baseline smell verification (F2)
3. Expand the model pool to include reasoning models (F3)
4. Restore multi-judge panel (F4)
5. Run rubric prevalence audit (F5)
6. Add reasoning parameter and provider logging (F6–F7)

Each pre-flight item was executed as a separate phase (A through D2) with pass/fail gates. The pre-registration spec (SPEC_V2.md) was written with 12 sections including an amendment log.

Five amendments were logged during pre-flight as the spec drifted:

| Amendment | Trigger | Change |
|-----------|---------|--------|
| A1 | Phase D prevalence audit | Rubric redesigned: 14 → 11 algorithmic-code dimensions |
| A2 | Baseline analysis | Task dropped: modeflag_sort had 0% baseline smell rate |
| A3 | Pool expansion | Model pool grew from 7 to 10 (3 reasoning models added) |
| A4 | Reasoning model inclusion | Explicit reasoning parameter + provider logging |
| A5 | Judge reliability concern | Multi-judge panel + calibration anchor restored |

## Step 4: Main experiment run

With all pre-flight items closed and `/intent-watch` confirming no spec drift, the main run executed:

- **1,260 generations** (10 models × 9 preambles × 7 tasks × 2 reps)
- **22,680 judge calls** (10-judge panel per generation)
- **Cost: ~$32**
- **Valid data: 1,215/1,260 generations, 22,028/24,300 judge calls parsed**

## Step 5: Results and mechanism discovery

The primary result was unambiguous: **p = 9.2 × 10^-18^** on pooled CQS-craft (Kruskal-Wallis test across preamble conditions). Seven of nine always-on rubric dimensions were individually significant.

But the investigation didn't stop at "preambles matter." ml-lab's Step 9 (production re-evaluation) prompted three confound probes to discriminate *why* preambles matter:

| Probe | Condition | Result | Rules out |
|-------|-----------|--------|-----------|
| A | Non-rubric expert preamble | -0.155 CQS vs none | — |
| B | Bare rubric (no persona) | +0.015 CQS vs none (recovers 70% of long_directive lift) | Judge-priming hypothesis |
| C | Anti-rubric expert preamble | -0.154 CQS vs none (symmetric with A) | Persona-halo hypothesis |

The refined mechanism: preambles direct the model's **attention-allocation budget** toward enumerated dimensions. CQS-craft is real but rubric-dependent — lift is proportional to overlap between preamble-enumerated dimensions and rubric-measured dimensions.

## Step 6: Investigation log

The full investigation generated 53 sequenced entries in `INVESTIGATION_LOG.jsonl`:

```
Entries  1–7:   PoC + hypothesis correction
Entries  8–25:  Three-round debate (critic/defender)
Entries 26–28:  Gate 1 plan approval
Entries 29–38:  Pre-flight phases A–D2
Entries 39–41:  Main run execution
Entries 42–53:  Analysis + confound probes
```

Every decision, amendment, and finding is traceable through this log.

## Key takeaways

1. **The PoC is cheap.** $0.01 and 30 seconds to confirm the measurement works before investing in review.
2. **Adversarial review finds real bugs.** The clamping bug (F1) would have invalidated the experiment. It was silent — the PoC appeared to work.
3. **Pre-registration drift is normal.** Five amendments were logged and justified. The point isn't to prevent drift — it's to make drift visible and auditable.
4. **Confound probes refine mechanisms.** The main result said "preambles matter." The probes said *why* — attention allocation, not judge priming or persona halo.
5. **The investigation log is the audit trail.** 53 entries trace the full path from hypothesis to mechanism.

Next: [Setting Up ml-journal](journal-setup.md) — initialize the audit trail that makes this kind of traceability possible.
