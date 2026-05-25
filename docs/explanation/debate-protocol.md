# Debate Protocol Design

## Why adversarial debate?

A single reviewer — human or LLM — tends to confirm the design it's reading. The critic-defender structure breaks this by giving two agents opposing mandates: one must find flaws, the other must defend the design. Neither can simply agree. This surfaces implicit assumptions that a single-pass review would accept at face value.

## The two-stage structure

### Stage A: Initial exchange

1. **ml-critic (R1)** reads the PoC and hypothesis, then produces findings tagged by severity (FATAL, MATERIAL, MINOR). The critic's mandate is exhaustive: find every implicit claim the PoC makes but hasn't tested.

2. **ml-defender (R1)** responds to each finding using a 7-type rebuttal taxonomy:

    | Type | Meaning |
    |------|---------|
    | CONCEDE | Finding is valid; will fix before main run |
    | REBUT-DESIGN | Design choice was intentional and correct |
    | REBUT-SCOPE | Finding is out of scope for this investigation |
    | REBUT-EVIDENCE | Evidence doesn't support the claimed severity |
    | REBUT-IMMATERIAL | Finding is real but doesn't affect conclusions |
    | DEFER | Will address as a pre-flight item |
    | EXONERATE | Finding is based on a misunderstanding |

    The taxonomy matters because it forces the defender to commit to a specific mode of disagreement rather than offering vague pushback.

### Stage B: Convergence loop

1. **ml-critic-r2** challenges each rebuttal with an ACCEPT / CHALLENGE / PARTIAL verdict
2. **ml-defender** responds to challenges
3. **`derive_verdict()`** — a pure Python function (no LLM) — computes a deterministic per-finding verdict based on final-round severity, rebuttal type, and acceptance status
4. Loop continues (min 2, max 4 rounds) until verdicts stabilize

## Why a deterministic verdict function?

The verdict could be computed by an LLM. It isn't, for two reasons:

1. **Reproducibility** — the same inputs always produce the same verdict. An LLM verdict would vary across runs, making it impossible to distinguish methodology changes from stochastic variation.

2. **Auditability** — the verdict logic is inspectable Python code with clear rules. When a verdict seems wrong, you can trace exactly which input caused it and adjust the rules. An LLM verdict is a black box that can only be debugged by prompt engineering.

The verdict function maps `(final_severity, rebuttal_type, acceptance_status)` → `{critique_wins, defense_wins, empirical_test_agreed}`. The mapping is explicit and testable.

## When ensemble mode is better

Ensemble mode (3× independent critics, no defender, union pooling by support tier) trades depth for breadth. It's better when:

- The risk surface is unknown and you want maximum recall
- You'll manually triage precision — false positives are acceptable
- The hypothesis is exploratory rather than focused

Debate mode is better when:

- You want every finding resolved to a deterministic verdict
- The hypothesis is specific and you need to know which issues are real
- You want the defender to filter low-quality findings before they enter experiment design

## Macro-iteration

When experimental results falsify a review assumption (e.g., the defender claimed a measurement was valid but the experiment revealed it wasn't), the entire review cycle reopens with results in hand. This is macro-iteration — up to 3 cycles of review → experiment → re-review.

Macro-iteration exists because some flaws are only visible after running the experiment. A pre-experiment review can't catch everything. The alternative — treating the first experiment's results as final — systematically underestimates methodology risk.
