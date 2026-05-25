# Use Debate vs Ensemble Mode

ml-lab offers two review modes. Choose the one that matches your situation.

## Debate mode (default)

Use when you want a **deep, convergent review** that resolves every finding to a verdict.

```shell
/ml-lab
# When prompted for review_mode, choose: debate
```

**What happens:**

1. `ml-critic` produces initial findings with severity levels
2. `ml-defender` responds with structured rebuttals (7-type taxonomy: CONCEDE, REBUT-DESIGN, REBUT-SCOPE, REBUT-EVIDENCE, REBUT-IMMATERIAL, DEFER, EXONERATE)
3. Stage B runs 2–4 challenge/response rounds until `derive_verdict()` determines convergence
4. Each finding gets a deterministic verdict: `critique_wins`, `defense_wins`, or `empirical_test_agreed`

**Best for:** hypothesis-driven investigations where you want every issue resolved before experimenting.

## Ensemble mode (opt-in)

Use when you want a **high-recall sweep** and will triage precision manually.

```shell
/ml-lab
# When prompted for review_mode, choose: ensemble
```

**What happens:**

1. `ml-critic` is dispatched 3 times independently — no visibility between critics
2. Findings are clustered by root cause
3. Each issue gets a support count: 3/3, 2/3, or 1/3
4. `ENSEMBLE_REVIEW.md` is written with tier-weighted output

**Best for:** broad exploratory sweeps where missing a real issue is costlier than triaging false positives. 1/3 minority findings need explicit user confirmation before entering experiment design.

## Choosing between them

| Factor | Debate | Ensemble |
|--------|--------|----------|
| Issue resolution | Deterministic verdict per finding | Manual triage by support tier |
| Depth | Deep — multi-round convergence | Broad — independent perspectives |
| False positive rate | Low (defender filters) | Higher (union pooling) |
| False negative rate | Higher (single critic) | Low (3× independent critics) |
| When to use | Focused hypothesis testing | Exploratory audit, unknown risk surface |

!!! tip
    After v8 calibration fixes, debate mode is recommended for all standard investigations. Use ensemble when you're exploring a new codebase or problem domain and don't yet know what to worry about.
