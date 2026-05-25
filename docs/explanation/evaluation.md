# Evaluation Methodology

## Pre-registration

Every ml-lab investigation locks its hypothesis, metrics, and pass criteria before any experiment code runs. This isn't bureaucracy — it's a response to a specific failure mode observed in v4: specification drift, where implementation changes silently violated the original experimental design.

Pre-registration is enforced by `/intent-watch`, which monitors the experiment directory for changes that conflict with the source-of-truth document (typically `HYPOTHESIS.md`). Any HIGH or CRITICAL conflict blocks the experiment.

Amendments are allowed — pre-registration doesn't mean the spec can never change. But amendments must be logged with their trigger and rationale, creating an auditable trail of why the design evolved.

## Metrics

ml-lab investigations use pre-specified metrics agreed before the PoC is built. The specific metrics depend on the hypothesis, but the structure is always:

1. **Primary metric** — the main measurement that will determine the verdict
2. **Pass criteria** — what value or outcome would support or falsify the claim
3. **Secondary metrics** — additional measurements that provide context

Metrics are chosen during the hypothesis-sharpening phase (before Step 1) and locked at pre-registration.

## Scoring

The self-evaluation experiments (v1–v8) use benchmark cases with ground-truth metadata:

- **`must_find`** — planted flaws the critic must detect for a case to count as "detected"
- **`correct_position`** — the ground-truth verdict (critic_wins, defense_wins, or empirical_test_agreed)
- **`acceptable_resolutions`** — valid ways to resolve the finding
- **`ideal_resolution`** — the best possible resolution

Scoring is deterministic: `derive_verdict()` maps debate outputs to case-level verdicts, which are compared against ground truth.

## Cross-vendor evaluation

v6 introduced cross-vendor scoring — running the same evaluation protocol with different LLM providers to test whether results are provider-dependent. This requires separate API credentials (`CROSS_VENDOR_API_KEY`, `CROSS_VENDOR_BASE_URL`, `CROSS_VENDOR_MODEL`).

Cross-vendor results are reported alongside primary results, not averaged with them, because provider-specific biases are a finding, not noise.

## Statistical methods

The methodology uses non-parametric tests by default:

- **Kruskal-Wallis** for multi-group comparisons (score distributions are typically non-normal)
- **Sensitivity analysis** across scoring schemes, weighting functions, and case orderings
- **Mixed-effects models** when modeling nested structure (e.g., cases within tasks within model tiers)

Multiple comparison corrections are applied when testing individual dimensions.

## Quality gates

Several gates protect against false conclusions:

1. **PoC gate** — confirms the measurement works before investing in review
2. **Gate 1** — all pre-flight items closed before experiment execution
3. **Intent-watch** — continuous drift monitoring during experiment scripting
4. **Micro-iteration** — evaluation design flaws trigger a re-run, not a conclusion
5. **Macro-iteration** — surprising results reopen the full review cycle
6. **Peer review** — optional multi-round review loop (Steps 10–11)
7. **Coherence audit** — cross-document consistency check (Step 12)
