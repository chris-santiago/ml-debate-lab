# Peer Review #3: Self-Debate Protocol v2 — Technical Report

**Reviewer:** research-reviewer agent  
**Date:** 2026-04-04  
**Target:** `self_debate_experiment_v2/REPORT.md`

---

## 1. Summary

The report evaluates an isolated self-debate multi-agent architecture (Critic + Defender + Judge) against a single-pass baseline and a compute-matched ensemble on a 20-case synthetic benchmark. Primary claim: structured adversarial debate produces better hypothesis evaluation (+0.335 to +0.441 corrected lift). The work includes post-experiment adversarial review, sensitivity analysis, ensemble ablation, and ETD ablation that progressively narrow and honest-up the original claims.

---

## 2. Strengths

**S1 — Exceptional intellectual honesty.** Revised headline lift from +0.586 down to +0.335–0.441 after self-critique. Rare and credibility-building.

**S2 — Well-designed ablation structure.** Three-condition comparison with ETD ablation provides genuine causal decomposition. The ETD=0.962 ensemble-with-constraint result is a clean, falsifiable finding.

**S3 — Pre-registered thresholds and typed verdicts.** Pass criteria specified before execution. The `defense_wins` false-positive trap cases are a creative, underexplored test of over-critique.

**S4 — Thorough failure mode taxonomy.** Three distinct failure modes are correctly characterized and distinguished.

**S5 — Comprehensive limitations section.** L1–L8 are specific, candid, and correctly calibrated.

---

## 3. Critical Issues

### Major

**[M1] Residual advantage after ablations is thin and underspecified.** After the ETD ablation, the confirmed advantages reduce to (a) exoneration precision and (b) structured argumentation — but (b) is partly tautological since DC/DRQ are *defined* to measure debate-specific outputs. The debate-vs-ensemble "fair comparison" lift is never reported; it is likely near zero on IDR/IDP/ETD/FVC.

**[M2] Exoneration claim rests on n=5.** The entire "structural isolation produces cleaner exonerations" finding is one case difference (5/5 vs. 4/5) in a 5-case stratum. Not statistically distinguishable from noise at any conventional threshold.

**[M3] Harmonized scoring undermines the quantitative exoneration advantage.** `ENSEMBLE_ANALYSIS.md` explicitly states the mean-score advantage disappears under harmonized scoring (IDP excluded for both conditions on defense_wins cases). The headline gap is largely explained by methodological artifacts, not genuine performance differences.

**[M4] Single-run results with no within-case variance.** `within_case_variance.py` was never executed. Bootstrap CIs estimate *sampling variance across cases*, not *execution variance within cases*. For a stochastic system, every reported score could shift materially on a second run. P-values and CIs carry no caveat about this.

**[M5] Closed-loop benchmark design.** Same entity designed cases, wrote ground-truth labels, designed rubric, implemented scoring, designed prompts, and scored outputs. The most distinctive findings (exoneration precision, structured argumentation) are exclusively demonstrated on designer-authored cases with no external validation path.

### Minor

**[M6]** "Convergence does not decrease with difficulty" is a non-result presented as a finding. A single sentence suffices.

**[M7]** CONCLUSIONS.md reports baseline passes as "2/20" in its table but "0/20" in a correction note. Inconsistency is confusing.

**[M8]** Related Work missing key references: computational argumentation quality (Wachsmuth et al.) and LLM ensemble evaluation literature (Wang et al., 2023 self-consistency).

**[M9]** Abstract leads with the inflated +0.586 before the corrected range — wrong prioritization for a report that has already revised this.

**[M10]** "Difficulty" labels are author-assigned with no inter-rater agreement, yet used as a stratification variable.

---

## 4. Prioritized Recommendations

1. **Compute and report debate-vs-ensemble fair comparison lift** (IDR/IDP/ETD/FVC only). If near zero, state this explicitly in the abstract.
2. **Execute `within_case_variance.py`** on at least the 5 defense_wins cases and 5 cross-range cases. Report mean ± SD across 5–10 runs before claiming any advantage on those cases.
3. **Reframe exoneration precision** as a "directional observation on n=5" rather than an established finding, OR expand the stratum to n≥15.
4. **Restructure abstract** to lead with the corrected lift range and the ensemble comparison as the primary result, not the inflated +0.586.
5. **Bring harmonized scoring into main REPORT.md results tables**, not just supplementary documents.
6. **Add explicit statistical caveat** wherever p-values appear: bootstrap CIs do not account for within-case LLM stochasticity.
7. **Compress the convergence section** to a single null-result paragraph.
8. **Fix CONCLUSIONS.md baseline pass count** (2/20 vs. 0/20 inconsistency).
9. **Run cross-vendor scorer** (GPT-4o or Gemini) on full benchmark to test same-model-family bias beyond the Haiku check.
10. **Construct externally-grounded exoneration cases** from well-replicated peer-reviewed ML work to address the closed-loop limitation for defense_wins.
