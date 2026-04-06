# Peer Review R1: Self-Debate Experiment v3 Technical Report

**Reviewer calibration:** Workshop paper, ML systems/evaluation venue (e.g., NeurIPS SysML, ICAIF workshop track). Full review depth.

---

## Summary

This report evaluates a self-debate protocol for automated ML peer review across four conditions (isolated_debate, multiround, ensemble, baseline) on a 49-case synthetic benchmark with pre-registered hypotheses, rubric dimensions, and structural scoring overrides. The corrected lift over baseline is +0.127 (isolated) / +0.138 (multiround) after removing rubric-inflation from structural overrides (DC=0.0, DRQ cap). All three primary hypotheses are confirmed, one secondary hypothesis is disconfirmed (ensemble outperforms debate on mixed cases), and external validation on 16 independent cases shows consistent results.

---

## Strengths

- **Pre-registration discipline is genuine and well-documented.** PREREGISTRATION.json was committed before any agent run (commit 659c0c3), contains all hypotheses, rubric definitions, structural overrides, and the per-case pass criterion. This is uncommon for workshop-level ML systems papers and substantially increases credibility. The report honestly reports a disconfirmed secondary hypothesis (ensemble > debate on mixed cases) rather than burying it.

- **Corrected lift is reported prominently.** The abstract leads with corrected lift (+0.127/+0.138), the raw lift is clearly labeled as inflated, and Section 4.1 presents both side-by-side with an explicit explanation of the inflation source. The sensitivity analysis (Section 4.3 and the dedicated SENSITIVITY_ANALYSIS.md) further decomposes lift into fair-comparison vs. protocol-diagnostic dimensions. This is a model of honest self-reporting that many papers fail to achieve.

- **DC=FVC structural equivalence is disclosed clearly.** Section 4.3 explicitly states that DC calls compute_fvc() for all non-baseline conditions and provides no independent signal. The pre-registration dc_note documents this upfront. A reader cannot be misled into treating DC as an independent measure.

- **The r=0.0 ceiling artifact is correctly explained.** Section 4.4 includes an inline note explaining that W=1176.0 is the maximum possible Wilcoxon statistic for n=49, meaning r=0.0 reflects maximum effect size (every case improved), not zero effect. The note extends to the multiround vs. isolated comparison. This prevents a serious misinterpretation.

- **Failure diagnosis is specific and actionable.** The three failing cases (rwf_003, rwf_005, rwf_008) are individually diagnosed in Section 4.2 and the failure mode taxonomy in Section 6, with clear attribution labels (agent vs. ambiguous) and identification of the specific scoring dimensions that failed. The comparison showing multiround passes on rwf_005 and rwf_008 provides useful structural insight.

- **Isolation breach handling is documented.** Section 3.4 discloses 2 isolation breaches detected by check_isolation.py, documents the re-run, and confirms the post-fix check passed clean. The ETD scorer bug (schema mismatch) is also transparently documented with before/after scoring impact.

- **Convergence metric gap is disclosed.** Section 7 (Limitation 6) and the multiround comparison section both acknowledge that the pre-registered convergence metric could not be extracted, explain why (raw outputs contain prose, not verdict labels), and correctly label this as a pre-registration gap.

---

## Major Issues

### 1. IDR=IDP=1.0 across all conditions (including baseline) is underemphasized

**Problem:** The dimension aggregate table (Section 4.3) shows IDR=1.0 and IDP=1.0 for every condition including baseline. The sensitivity analysis notes this means "the debate protocol's advantage on issue identification specifically -- its originally hypothesized core benefit -- is not observed at this benchmark level." However, this critical finding is confined to SENSITIVITY_ANALYSIS.md and a brief mention in Section 4.3. The main report body does not prominently surface the implication: the debate protocol shows zero advantage on the two dimensions most directly tied to its theoretical motivation.

**Why it matters:** A reader of the abstract and hypothesis verdicts would conclude the debate protocol provides a meaningful advantage. But the entire lift comes from ETD (a prompt-engineering effect acknowledged in the report), DRQ (a modest +0.024), and the structural overrides. The dimensions where debate is supposed to shine -- catching issues the baseline misses, or avoiding false positives the baseline raises -- show identical performance. This is a significant finding that deserves a dedicated paragraph in the main results section, not just a line in an appendix document.

**[MAJOR]**

**Proposed fix:** Add a paragraph to Section 4.1 or 4.3 in the main report explicitly stating: (a) IDR and IDP are saturated at 1.0 across all conditions including baseline, (b) the debate protocol provides no measurable advantage on issue identification at this benchmark difficulty level, and (c) this likely reflects a ceiling effect in benchmark difficulty rather than protocol equivalence -- but cannot be disentangled without harder cases. Frame this as both a limitation and a direction for future work.

### 2. Benchmark difficulty ceiling undermines the central claim

**Problem:** When the baseline achieves IDR=1.0, IDP=1.0, and FVC=0.980 -- meaning it finds every issue, avoids every false positive, and reaches the correct verdict 98% of the time -- the benchmark is not discriminating between conditions on the dimensions that matter most. The remaining lift is almost entirely ETD (a prompt-design effect) and the structural overrides (DC, DRQ). The corrected fair-comparison-only lift is just +0.053 (isolated) and +0.069 (multiround), and this is driven almost entirely by ETD.

**Why it matters:** The benchmark is too easy for the model being evaluated. A baseline that already achieves near-perfect issue detection and verdict accuracy cannot be meaningfully improved upon by any protocol. The report frames this as "the protocol generalizes" via external validation, but the external validation shows the same pattern: all debate conditions at 1.000, baseline at 0.628 (with the same structural override inflation). This is a construct validity concern: the experiment cannot distinguish "debate helps" from "this model doesn't need debate for these cases."

**[MAJOR]**

**Proposed fix:** Acknowledge the ceiling effect as a first-order limitation, not just a passing note. The difficulty label invalidity (rho=-0.069, p=0.68) compounds this: the benchmark lacks empirically validated difficulty stratification, so there is no way to identify the subset of cases where debate might actually be needed. Recommend constructing harder cases where baseline FVC < 0.8 or IDR < 0.9 to test whether debate provides lift in the regime where it would matter.

### 3. External validation does not demonstrate generalization

**Problem:** Section 8 claims the 16/16 external pass rate "provides cross-corpus evidence that the protocol generalizes beyond the GPT-generated synthetic benchmark." But all debate conditions achieve 1.000 on external cases -- the same ceiling saturation as the main benchmark. The external baseline (0.628) is consistent with the main benchmark baseline (0.634), but this consistency is expected since the structural overrides (DC=0.0, DRQ cap) are the dominant factor in both.

**Why it matters:** An external validation that shows 100% performance across all conditions tells you nothing about where the protocol's performance boundary lies. Generalization evidence requires cases where the protocol is challenged. The 16 external cases appear to be in the same difficulty regime as the main benchmark. A reviewer at a venue like NeurIPS SysML would note that this validation adds no discriminative information.

**[MAJOR]**

**Proposed fix:** Reframe external validation honestly: it confirms the protocol does not degrade on out-of-distribution cases, but does not demonstrate generalization to harder review tasks. Note that meaningful external validation would require cases where baseline performance is substantially lower (e.g., FVC < 0.7) so that debate lift can be measured on content-discriminative dimensions.

### 4. Absence of a non-structural baseline for ETD comparison

**Problem:** The ETD gap (baseline 0.476 vs. isolated 0.841 vs. ensemble 1.000) drives most of the fair-comparison lift. The report correctly notes that the ensemble ETD advantage is a "prompt-engineering effect" (the synthesizer is explicitly instructed to produce an ETD). However, the same logic applies to the isolated debate condition: the adjudicator prompt may implicitly encourage ETD production in ways the baseline prompt does not. No ablation is provided where the baseline receives an equivalent ETD-forcing instruction.

**Why it matters:** Without a baseline+ETD-forcing ablation, it is impossible to determine whether the debate protocol's ETD advantage reflects adversarial structure or simply the fact that the debate condition's adjudicator prompt mentions empirical tests. The report acknowledges v2 showed ETD=0.962 with explicit constraint vs. 0.192 without, which strongly suggests the advantage is prompt-driven. This makes the fair-comparison lift of +0.053/+0.069 potentially attributable entirely to prompt differences rather than protocol architecture.

**[MAJOR]**

**Proposed fix:** Either (a) run an ablation where the baseline receives an ETD-forcing instruction equivalent to what the adjudicator sees, or (b) report the fair-comparison lift excluding ETD (which would be approximately +0.000 given IDR/IDP/FVC saturation) as a lower bound. Option (b) is straightforward and would give readers the honest picture: the protocol's content advantage over baseline, after removing both structural overrides and prompt-design effects, is approximately zero on this benchmark.

---

## Minor Issues

### 5. CONCLUSIONS.md lift table reports raw lift without corrected figure

**[MINOR]** The pass/fail criteria table at the top of CONCLUSIONS.md shows "Lift over baseline: +0.341" without the corrected figure. A reader entering through CONCLUSIONS.md rather than REPORT.md would see the inflated number first. Add the corrected lift (+0.127) to this table or add a cross-reference.

### 6. Defense_wins baseline score explanation could be clearer

**[MINOR]** The defense_wins cases all show baseline=0.500, which is entirely due to DC=0.0 (structural override). The report explains this in several places but a consolidated one-sentence note in the per-case table header (Section 4.2 or CONCLUSIONS.md table) would prevent confusion, since 0.500 could be misread as the baseline getting the verdict half-right.

### 7. Within-case variance is near-zero but interpretation is missing

**[MINOR]** The within-case variance section in CONCLUSIONS.md reports mean std of 0.0024 (isolated) and 0.0000 (all others). This extreme stability across 3 runs per case suggests either (a) the model is highly deterministic at the temperature used, or (b) the scoring rubric is too coarse (0.0/0.5/1.0) to capture run-level variation. The report does not discuss which interpretation applies. If temperature=0 was used, this should be stated; if not, the near-zero variance is a finding worth interpreting.

### 8. Related work section lacks self-critique/debate-for-review references

**[MINOR]** The related work cites general multi-agent debate papers (Irving et al., Du et al., Khan et al.) but does not cite work specifically on LLM-based code or paper review (e.g., automated scientific reviewing, LLM-based code review systems). If such systems exist in the literature, they would be the most relevant comparisons. The omission makes it harder to position this work's contribution relative to existing automated review systems.

### 9. Multiround round-count distribution deserves more analysis

**[MINOR]** Section on multiround comparison reports mean rounds=1.03 with 91.5% resolving in round 1. This means the multiround condition barely exercises its multi-round capability. If nearly all cases resolve in one round, the multiround condition is functionally equivalent to isolated debate plus a different adjudication prompt. This should be discussed as a limitation of the benchmark difficulty (cases are too easy to require extended debate) rather than evidence that single-round resolution is sufficient.

### 10. No code release or reproducibility statement

**[MINOR]** The report lists code files (self_debate_poc.py, stats_analysis.py, etc.) but does not include a reproducibility statement about whether code, data, and agent prompts will be released. For a workshop paper, a brief statement about artifact availability would strengthen the contribution.

---

## Recommendation

**Revise.**

The report demonstrates strong methodological discipline -- pre-registration, honest corrected-lift reporting, transparent disclosure of structural equivalences and scorer bugs. These are genuine strengths. However, the central empirical finding is substantially weaker than the framing suggests: the benchmark is too easy to discriminate between conditions on content-relevant dimensions (IDR, IDP, FVC all saturated), the remaining lift is driven by ETD (a prompt-design effect) and structural overrides, and the fair-comparison content lift excluding ETD is approximately zero. A revision should (1) foreground the ceiling effect as a primary finding rather than a footnote, (2) add the ETD-excluded lift figure as a lower bound, (3) reframe external validation as non-degradation evidence rather than generalization evidence, and (4) position the contribution as a validated evaluation framework ready for harder benchmarks rather than evidence that debate improves ML review quality.

---

## Response

All four major issues were addressed in REPORT.md. No additional analysis scripts were required — all figures are derivable from existing computed data.

**Major Issue 1 — IDR/IDP saturation underemphasized**: Added a dedicated paragraph to Section 4.3 immediately after the DC=FVC note. The paragraph explicitly states: IDR=IDP=1.0 across all conditions including baseline; the protocol provides zero measurable advantage on issue identification at this benchmark level; the lift on IDR+IDP+FVC only (excluding ETD and structural overrides) is +0.000.

**Major Issue 2 — Benchmark difficulty ceiling**: Expanded Section 7 (Limitations) to treat the difficulty ceiling as the primary limitation (now listed as item 4, before model-version binding). The revised text leads with the specific saturation numbers (FVC=0.980, IDR=IDP=1.0 for baseline), states the corrected content lift excluding ETD is +0.000, and explicitly frames the benchmark as not hard enough to measure debate lift on its theoretically motivated dimensions. The difficulty-label invalidity (rho=-0.069) note immediately follows as a compounding factor.

**Major Issue 3 — External validation overclaims generalization**: Section 8 closing sentence changed from "provides cross-corpus evidence that the protocol generalizes" to explicit non-degradation framing: the 16/16 pass rate confirms the protocol does not regress on out-of-distribution cases but does not reveal the boundary of its competence, since all conditions saturate at 1.000.

**Major Issue 4 — ETD-excluded lift not reported**: The IDR/IDP saturation paragraph added in Section 4.3 explicitly states the lift on IDR+IDP+FVC (excluding both ETD and DC/DRQ structural overrides) is +0.000. This is the lower bound — content lift after removing both structural and prompt-design effects.

**Minor issues**: Not addressed in this revision. Issues 5–10 are presentation notes that do not affect validity. Issue 5 (CONCLUSIONS.md table) is noted for v4. Issues 7, 9 (variance interpretation, round-count discussion) are reasonable future additions but not validity threats at the workshop level. Issue 10 (reproducibility statement) applies to a public release context outside the scope of this internal benchmark.
