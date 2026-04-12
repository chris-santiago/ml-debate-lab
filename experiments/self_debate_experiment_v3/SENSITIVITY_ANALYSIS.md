# v3 Sensitivity Analysis

Addresses two structural scoring concerns carried forward from v2 peer review:
- **L3**: Raw lift is inflated by baseline DC=0.0 structural override
- **L4**: Dimension aggregation mixes fair-comparison and protocol-diagnostic dimensions

All corrected figures computed in `sensitivity_analysis.py` from `v3_results.json`.

---

## Corrected Lift

The pre-registered scoring applies two structural overrides to baseline:
1. **DC = 0.0** (hardcoded): Baseline has no defense role; the DC dimension is structurally inapplicable.
2. **DRQ capped at 0.5**: Baseline cannot produce a typed resolution from structured exchange.

These overrides are methodologically justified — they prevent crediting the baseline for capabilities it structurally cannot have. However, they inflate the raw lift figure. The corrected lift removes both overrides, giving baseline DC = 0.5 (partial credit) and uncapping DRQ.

| Metric | Isolated debate | Multiround |
|--------|----------------|------------|
| Raw lift vs. baseline | +0.341 | +0.352 |
| Corrected lift (DC=0.5, DRQ uncapped) | **+0.127** | **+0.138** |
| Raw baseline mean | 0.634 | — |
| Corrected baseline mean | 0.848 | — |

**Interpretation:** The corrected lift (+0.127 / +0.138) represents the performance advantage attributable to the debate protocol on dimensions where both systems have equal structural opportunity. This is the honest range. The raw lift (+0.341 / +0.352) includes 0.214 points of structural penalty that is definitional, not empirical.

Both corrected and raw lifts exceed the pre-registered threshold of +0.10, so the primary lift hypothesis holds under either accounting.

### Cases changing pass/fail under correction

48 of 49 baseline runs currently fail (passes=0). Under corrected scoring (DC=0.5, DRQ uncapped), 48 of those 49 baselines would reach mean ≥ 0.65 and pass. The only case where the baseline fails even under correction is `real_world_framing_003`, where the baseline returns verdict = `mixed` — structurally invalid — driving FVC=0.0 independently of the DC/DRQ overrides.

This finding confirms that nearly all baseline failures are attributable to the structural overrides, not to genuine content failure. The baseline produces correct verdicts (FVC=0.980) and finds issues (IDR=1.0, IDP=1.0) — it simply cannot be credited for the structural roles (debate, adversarial exchange) it does not perform.

---

## Dimension-Stratified Analysis

Two categories of dimensions:

**Fair-comparison dimensions** (IDR, IDP, ETD, FVC): Both baseline and debate have equal structural agency. The baseline can find issues, avoid false positives, produce empirical tests, and reach valid verdicts. Lift on these dimensions reflects genuine protocol contribution.

**Protocol-diagnostic dimensions** (DC, DRQ): The baseline is structurally penalized by design. DC=0.0 is hardcoded; DRQ is capped at 0.5. Lift on these dimensions is definitionally inflated.

| Condition | Fair-comparison mean | Protocol-diagnostic mean |
|-----------|---------------------|--------------------------|
| Isolated debate | 0.970 | 0.968 |
| Multiround | 0.986 | 0.980 |
| Ensemble | **1.000** | 0.980 |
| Baseline | 0.918 | 0.245 |

### Lift on fair-comparison dimensions only

| Comparison | Fair-dim lift |
|------------|--------------|
| Isolated vs. baseline | +0.053 |
| Multiround vs. baseline | +0.069 |
| Multiround vs. isolated | +0.016 |
| Isolated vs. ensemble | −0.030 |

**Interpretation:** On fair-comparison dimensions, the debate protocol achieves +0.053 lift over baseline (isolated) and +0.069 (multiround). This is substantially smaller than the raw lift (+0.341), confirming that most of the headline improvement is structural. The genuine content advantage — finding more of the right issues, avoiding false positives, producing well-specified empirical tests, reaching correct verdicts — is modest but consistent.

The ETD dimension drives most of the fair-comparison lift: baseline ETD = 0.476 vs. isolated ETD = 0.841 and multiround ETD = 0.952. The ETD advantage reflects a real protocol contribution: isolated debate and multiround consistently produce empirical test specifications when cases require them; the baseline does so less reliably.

IDR and IDP are 1.0 across all conditions including baseline, meaning the baseline finds all must-find issues and avoids all must-not-claim false positives as reliably as the debate conditions. These two dimensions contribute zero lift. The debate protocol's advantage on issue identification specifically (its originally hypothesized core benefit) is not observed at this benchmark level — all conditions saturate.

---

## ETD Structural Note

A post-hoc scorer bug was discovered and fixed before final scoring (see POST_MORTEM.md Issue 6): `compute_etd()` was written expecting `measure/success_criterion/failure_criterion` keys, but agents naturally produced `condition/supports_critique_if/supports_defense_if` keys in many outputs. After the fix, ETD scores for the affected `real_world_framing` cases improved substantially:

| | Pre-fix ETD (isolated) | Post-fix ETD (isolated) |
|--|----------------------|----------------------|
| real_world_framing_006 | 0.0 | 1.0 |
| real_world_framing_007 | 0.0 | 1.0 |
| real_world_framing_009 | 0.0 | 1.0 |
| real_world_framing_002 | mixed (0/0/1.0) | mixed (1.0/1.0/0.0) |
| real_world_framing_010 | mixed (1.0/0/0) | 1.0 all runs |

All ETD scores in this document and in CONCLUSIONS.md reflect the corrected scorer.

---

## Difficulty Label Validity

Spearman ρ = −0.069 between difficulty label (easy/medium/hard) and baseline mean score across 38 non-defense_wins cases. p = 0.680. No significant negative correlation.

| Difficulty | n | Baseline mean |
|------------|---|---------------|
| easy | — | 0.698 |
| medium | — | 0.655 |
| hard | — | 0.676 |

Hard cases do not score lower than medium cases on baseline. The ordering is non-monotonic (easy > hard > medium), contradicting the expected negative relationship. This indicates the difficulty labels reflect domain complexity as assessed by the case generator, not empirical discriminability for this scorer and model. Difficulty-stratified analysis should be treated as descriptive only.
