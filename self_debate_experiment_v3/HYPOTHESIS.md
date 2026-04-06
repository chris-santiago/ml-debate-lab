# Hypothesis — Self-Debate Experiment v3

## Primary Claim

The isolated self-debate protocol — ml-critic and ml-defender each receiving only the task
prompt, with the orchestrator adjudicating — will achieve a benchmark aggregate score at
least **+0.10 higher** than a single-pass baseline on synthetic ML reasoning tasks with
known ground-truth verdicts.

## Mechanism

Adversarial role separation forces engagement with both sides of each case. By requiring an
independent defense of the presented work before any critique is seen, the protocol surfaces
considerations that a single correlated assessor would suppress or conflate. This produces:

- Better-typed verdicts (correct identification of critique_wins vs. defense_wins vs. mixed)
- Higher false-positive catch rate on cases where the methodology is actually sound
- More structured point-by-point argumentation, elevating DC and DRQ scores
- Cleaner empirical test demands (ETD), because contested claims require resolution criteria

## Primary Metrics

| Dimension | Description |
|-----------|-------------|
| IDR | Issue Detection Rate — fractional recall of planted issues |
| IDP | Issue Detection Precision — with must_not_claim penalty |
| DC | Debate Coverage — fraction of contested points substantively addressed |
| DRQ | Debate Resolution Quality — quality of point-by-point adjudication |
| ETD | Empirical Test Demand — quality and specificity of required test specification |
| FVC | Final Verdict Correctness — alignment with ground-truth correct_position |

Scores are on a 0.0 / 0.5 / 1.0 scale per dimension (null = N/A, excluded from case mean).
A case passes if: mean over applicable dimensions >= 0.65 AND all applicable dimensions >= 0.5.

## Secondary Hypotheses

### H2 — Compute-Matched ETD Comparison

Debate outperforms a compute-matched ETD-constrained ensemble on mixed-position cases.
Rationale: the ETD advantage found in v2 was attributed to output-constraint prompt design
rather than adversarial structure. On mixed cases, where genuine disagreement exists,
adversarial role separation should produce more specific and discriminating empirical tests
than a single-pass synthesizer with an explicit ETD constraint.

### H3 — Defense Recall at Ensemble Compute Budget

Pre-specified criterion: ensemble DC >= 0.5 on >= 60% of defense_wins cases.

Rationale: v2 showed that ensemble exoneration precision was high (5/5 correct) but did not
test whether a compute-matched ensemble can achieve comparable point-level defense coverage.
This criterion establishes a minimum bar to assess whether the defense_wins advantage is
explained by compute budget alone or reflects a structural property of the debate protocol.

## Operationalization

- **Baseline**: single-pass ml-critic receiving task prompt only; no debate, no defender.
- **Debate condition**: ml-critic -> ml-defender (task prompt only, no critique seen) ->
  orchestrator adjudication of contested points.
- **Aggregate score**: mean case-level score across all 49 benchmark cases.
- **Success threshold**: debate aggregate - baseline aggregate >= 0.10.
- **Benchmark**: `benchmark_cases_verified.json` (49 cases across 7 categories and 3
  difficulty levels; ground-truth correct_position known).
