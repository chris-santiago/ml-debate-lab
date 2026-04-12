# v6 Hypotheses (Pre-Registered)

Pre-registration must be committed to git **before Phase 5 (benchmark run) begins**.
See `HYPOTHESIS.md` (repo root of v6 directory) for the full formal document.

---

## Co-Primary

**H1a — Regular case lift:**
```
fc_mean(isolated_debate, regular) - fc_mean(baseline, regular) >= threshold
```
- Fair-comparison dims: IDR, IDP, DRQ, FVC
- `threshold = max(0.03, min(0.10, (1.0 - baseline_pilot_fc_mean) * 0.5))` — set after Phase 3
- Bootstrap 95% CI; one-sided test

**H1b — Mixed case FVC lift:**
```
mean FVC(isolated_debate, mixed) > mean FVC(baseline, mixed)
```
- One-sided bootstrap test, CI excludes 0
- The cleanest structural test: debate should produce `empirical_test_agreed` where baseline commits to a side

---

## Secondary

**H2 — Debate vs compute-matched ensemble:**
```
fc_mean(isolated_debate) vs fc_mean(ensemble_union_idr)  [regular cases]
mean FVC(isolated_debate, mixed) vs mean FVC(ensemble, mixed)  [mixed cases]
```
- Two-sided. If ensemble >= debate on both, adversarial structure adds no value over
  independent redundancy at matched compute.

**H3 — Conditional FM vs natural multiround:**
```
FM hard mean > MR hard mean  [Wilcoxon signed-rank, hard cases only]
hollow round rate < 10%  [quality gate for conditional gate]
```

---

## Exploratory

**H4 — ETD quality by debate mode:**
Mean ETD across isolated_debate, multiround, conditional_fm, biased_debate on mixed cases.
Directional prediction (from v3 evidence and `V5_INSIGHTS_AND_AVENUES.md` Avenue 1):
`multiround > isolated_debate` on ETD specifically — the back-and-forth exchange is where
empirical test specification should emerge, not a single exchange round. Full credit (1.0)
rate and partial credit (0.5) rate reported separately per condition.

**H5 — Cross-model scorer agreement:**
Report IDR/IDP/ETD agreement between GPT-4o (primary) and Claude (secondary).
Quantify confound magnitude; flag if IDR delta > 0.50.

**H6 — Persona-biasing improves debate quality (Q4):**
```
fc_mean(biased_debate, regular) vs fc_mean(isolated_debate, regular)
mean FVC(biased_debate, mixed) vs mean FVC(isolated_debate, mixed)
mean ETD(biased_debate, mixed) vs mean ETD(isolated_debate, mixed)
```
- Two-sided bootstrap, 95% CI
- Prediction: biased_debate > isolated_debate on IDR (critic sensitivity) and IDP (defender
  selectivity); directional improvement on mixed FVC and ETD
- If biased_debate <= isolated_debate: persona framing has no measurable effect on debate
  quality beyond the structural protocol
