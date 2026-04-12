# Phase 10 — Reporting

> **Reminders:** `uv run` only. CWD: repo root.

---

## Steps

### 10.1 Run `/artifact-sync`
Per `CLAUDE.md`: run `/artifact-sync` before marking work complete. This updates all
artifacts, runs the three-check coherence audit (conflicts, staleness, completeness).

### 10.2 Dispatch `report-writer`
Agent prompt:
```
Write REPORT.md and TECHNICAL_REPORT.md for the v7 experiment.

Sources (numbers come ONLY from these):
- v7_results.json — all metrics, CIs, p-values, TOST result
- CONCLUSIONS.md — hypothesis verdicts and framework verdict
- SENSITIVITY_ANALYSIS.md — variance audit, bootstrap stability
- HYPOTHESIS.md — pre-registered predictions (P1, P2)
- benchmark_cases_v7_raw.json — case counts and stratum composition

Key findings to highlight:
1. Framework verdict (P1 + P2): CONFIRMED or NOT CONFIRMED
2. TOST H1a result: debate EQUIVALENT to baseline within ±{bounds} FC
3. ensemble_3x vs multiround_2r IDR delta (P1) with CI
4. multiround_2r vs ensemble_3x FVC_mixed delta (P2) with CI
5. Defense exoneration rate by condition
6. multiround_2r variance relative to other conditions

Do not source numbers from README, v6 artifacts, or pilot_results.json.
```

### 10.3 Rewrite paper

Update all three paper versions (`paper/arxiv/`, `paper/emnlp2026/`, `paper/neurips2026/`):

**New results section:**
- Update Table 1 (main results) with v7 condition means
- Update Table 2 (hypothesis verdicts) with P1, P2, H1a TOST
- Add Table for multiround_2r variance vs other conditions
- Update Abstract: lead with framework confirmation/non-confirmation

**Changed claims:**
- Replace v6's post-hoc framing with: "We pre-registered these predictions..."
- Replace "multiround advantage at ~5×" with v7 matched-compute result
- Add TOST result for H1a equivalence claim
- Remove ETD from primary results tables

**Paper structure additions:**
- §3.2 (Method): add pre-registration subsection (P1/P2, timing, commit hash)
- §3.3 (Method): add TOST subsection
- §4 (Results): add `multiround_2r` row to all tables

**Four required edits from v6_issues.md peer review (MUST DO):**

**a) Abstract: concept before numbers**
Current abstract leads with five specific deltas in the first three lines. Rewrite to lead
with the conceptual claim, then numbers:
> "Independent ensembles outperform adversarial debate at matched compute for divergent
> detection; task type moderates this advantage. [Then: ∆ IDR = ..., FC ∆ = ...]"

**b) IDR as co-primary metric throughout**
§5.2 makes the case that IDR is the signal metric for detection tasks and FC composites
dilute it. Apply consistently:
- Abstract: report IDR delta prominently, not buried after FC
- §1 (Introduction): state IDR alongside FC as co-primary
- §6 (Conclusion): lead conclusion with IDR advantage, not FC composite

**c) AI disclosure → title page footnote**
Current placement as a standalone section before References is unusual at ACL venues.
Move to `\thanks{}` footnote on title page (same approach as preprint `\thanks{Preprint.
Under review.}`). Keep the reflexive disclosure text — it's intellectually honest and
appropriate — just change placement.

**d) Benchmark as releasable artifact in Introduction**
The 260-case benchmark with ground-truth labels is a concrete contribution independent
of the experiment. Mention release in §1 (Introduction), not only in the reproducibility
section. One sentence is sufficient: "We release the benchmark and all experimental
artifacts at [repo URL]." ACL Findings reviewers weight released resources positively.

### 10.4 Final coherence audit

Run three checks manually:

**Conflicts:** Do any two documents contradict each other on the same number?
```bash
git log --format="%ci %s" -- experiments/self_debate_experiment_v7/*.md | sort -r | head -10
```

**Staleness:** Does any document reference a v6 number that should now be a v7 number?
```bash
grep -r "0\.6712\|0\.7717\|0\.6603\|0\.3667" experiments/self_debate_experiment_v7/ \
  paper/ --include="*.md" --include="*.tex" -l
```
(These are v6 IDR/FVC_mixed values. Flag any file that still contains them after paper rewrite.)

**Completeness:** Does README reflect the strongest current evidence?
Update `README.md` "What We Found" section with v7 framework verdict and key metrics.

### 10.5 Log and commit
Use `/log-commit` (ml-journal skill). Commit message should list:
- `REPORT.md`, `TECHNICAL_REPORT.md` created
- Paper files updated
- Artifact sync complete

---

## Outputs
- `REPORT.md`
- `TECHNICAL_REPORT.md`
- Updated `paper/arxiv/main.tex`, `paper/emnlp2026/main.tex`, `paper/neurips2026/main.tex`
- Updated `README.md`

## Gate
All artifacts updated. Coherence audit passes. Paper rewrite complete.
