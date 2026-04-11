# v6 Experimental Design: Does the ml-lab Debate Protocol Add Value?

## Context

v5 tested whether adversarial debate (critic + defender) outperforms single-pass critique on
110 synthetic binary-verdict cases. The primary hypothesis **failed**: fc_lift = +0.0097
(threshold +0.10, CI [-0.0013, +0.0217]). But v5 was structurally unable to answer the question:

1. **Ceiling effect** — baseline scored 0.9452, leaving only ~0.05 headroom. The threshold was uninformative.
2. **No mixed cases** — ETD (the one dimension where v3 showed genuine debate advantage: +0.365 lift) was N/A for all 110 cases.
3. **Closed-loop confound** — Claude scored Claude outputs. Cross-vendor IDR delta = -0.7737.
4. **Majority-vote artifact** — ensemble IDR suppressed from 0.8725 (union) to 0.7679 (majority-vote).
5. **Hollow forced rounds** — 20.5% of forced_multiround rounds were vacuous (no new points resolved).

v3 retrospective revealed the debate protocol's only clear advantage was **ETD-specific**:
helping models specify empirical tests for genuinely ambiguous cases. IDR/IDP/FVC showed zero
debate advantage even in v3 (all lift from ETD: +0.365; IDR/IDP/FVC delta = 0.0).

v6 is designed to definitively answer three questions:
- **Q1:** Does ml-lab debate add value over single-pass baseline?
- **Q2:** Does it add value over a compute-matched ensemble?
- **Q3:** Is forced multiround superior to natural stopping?

---

## Execution Rules

> These rules apply to every phase without exception.

1. **Script invocations:** All Python scripts must use `uv run`. Never `python` or `python3` directly. For inline one-liners: `uv run python -c '...'`. For multi-line inline scripts, use heredoc style.
2. **Agent invocation:** Agents (`ml-critic`, `ml-defender`, `research-reviewer`, `report-writer`) invoked by name via the Agent tool only. Do not read any file from `agents/` during execution.
3. **Working directory:** The Bash tool CWD is always the repo root (`ml-debate-lab/`). All bash commands must `cd self_debate_experiment_v6 &&` first, or use repo-root-relative paths.
4. **Subagent context:** All agents run inside an authenticated Claude Code session. Do not call the Anthropic API directly or locate API keys.
5. **Log entries:** Always use `uv run log_entry.py`. Never write JSONL manually via echo or direct append.

---

## Reference Documents

| Document | Description | Used by phases |
|---|---|---|
| [design_decisions.md](references/design_decisions.md) | Case source, composition, pipeline architecture, conditions, FM gate, persona-biased debate, scoring dimensions, mixed-case FVC rationale | 0, 1, 2, 3, 4, 5, 6 |
| [hypotheses.md](references/hypotheses.md) | H1a, H1b, H2, H3, H4, H5, H6 definitions + pre-registration timing | 3, 4, 5, 7, 8, 9 |
| [rc_pipeline_spec.md](references/rc_pipeline_spec.md) | RC-1–RC-4 stage definitions, flaw schema, contamination prevention | 1, 2 |
| [schema_b.md](references/schema_b.md) | Schema B field table + critical format constraints | 0, 2, 6 |
| [v5_mitigations.md](references/v5_mitigations.md) | PM1–PM5 mapping + proxy_mean constraint + PM class note | 0, 1, 2, 5 |

---

## Phase Index

| Phase | Title | File | Gate summary |
|---|---|---|---|
| 0 | Setup | [phase_00_setup.md](phases/phase_00_setup.md) | Updated scoring engine + biased_debate agents committed |
| 1 | RC Data Acquisition | [phase_01_rc_acquisition.md](phases/phase_01_rc_acquisition.md) | `rc_cases_raw.json` exists; decision table applied |
| 2 | Case Library Assembly | [phase_02_case_assembly.md](phases/phase_02_case_assembly.md) | `benchmark_cases_raw.json` passes Schema B validation |
| 3 | Pilot & Calibration | [phase_03_pilot.md](phases/phase_03_pilot.md) | `baseline_fc_mean < 0.80`; >= 80 regular + 30 mixed pass filter |
| 4 | Pre-Experiment Self-Review | [phase_04_self_review.md](phases/phase_04_self_review.md) | `HYPOTHESIS.md` committed; PRE-N requirements addressed |
| 5 | Benchmark Run | [phase_05_benchmark.md](phases/phase_05_benchmark.md) | All output files pass schema + zero-variance check |
| 6 | Cross-Model Scoring | [phase_06_scoring.md](phases/phase_06_scoring.md) | `v6_rescored_idr_idp.json` complete |
| 7 | Analysis | [phase_07_analysis.md](phases/phase_07_analysis.md) | `v6_results.json` with all 6 hypothesis tests |
| 8 | Sensitivity & Robustness | [phase_08_sensitivity.md](phases/phase_08_sensitivity.md) | `SENSITIVITY_ANALYSIS.md` + `CONCLUSIONS.md` |
| 9 | Cross-Vendor Validation | [phase_09_cross_vendor.md](phases/phase_09_cross_vendor.md) | `CROSS_VENDOR_VALIDATION.md` |
| 10 | Reporting | [phase_10_reporting.md](phases/phase_10_reporting.md) | All artifacts + `/artifact-sync` + coherence audit |

---

## Files

### Create (new)
| File | Purpose |
|---|---|
| `plan/PLAN.md` | This document |
| `HYPOTHESIS.md` | Pre-registered hypotheses (commit before Phase 5) |
| `pipeline/rc_extractor.py` | OpenReview API + ReScience C extraction |
| `pipeline/select_cases.py` | Case selection: mixed stratum + difficulty gate |
| `pipeline/normalize_cases.py` | Unify RC + synthetic schemas to benchmark format |

### Modify (existing v6)
| File | Change |
|---|---|
| `self_debate_poc.py` | Drop DC entirely; union IDR in ensemble scoring; `conditional_fm` condition |
| `pipeline/orchestrator.py` | `--rc-cases` input path for RC-sourced cases; conditional FM gate logic |
| `pipeline/prompts/stage3_mixed_assembler.md` | Fixed `acceptable_resolutions` bug (was all four verdicts; now `["empirical_test_agreed"]` only) |

### Reuse (no changes needed)
| File | Status |
|---|---|
| `pipeline/prompts/stage2_mixed_writer.md` | Ready |
| `V3_V5_CONTRAST.md` | Reference |
| `DATA_ACQUISITION.md` | Reference → implemented in `rc_extractor.py` |
| `MIXED_CASE_PLAN.md` | Reference → already implemented in `orchestrator.py` |

---

## Key Differences from v5

| Aspect | v5 | v6 |
|---|---|---|
| Case source | Synthetic planted corruptions | RC reports + synthetic mixed |
| Mixed cases | 0 (ETD always N/A) | 40 (33% of benchmark) |
| Baseline ceiling | 0.9452 | Target < 0.75 |
| IDR/IDP scorer | Claude (closed-loop) | GPT-4o (cross-model) |
| Ensemble IDR | Majority-vote (0.7679) | Union-of-issues |
| Forced multiround | Unconditional (20.5% hollow) | Conditional on unresolved disagreement |
| H1 threshold | +0.10 (fixed, no power analysis) | Set after pilot, <= 50% of headroom |
| DC dimension | Diagnostic-only | Dropped entirely |
| Primary signal | fc_lift on regular cases only | fc_lift (regular) + FVC lift (mixed) — co-primary |
| Compute matching | Implicit | Explicit: isolated ~3x = ensemble 3x |
| Conditions | 5 | 6 (adds biased_debate) |
| Ensemble aggregation | Majority IDR + majority verdict | Union IDR + majority verdict (split rule) |
| H4 (ETD) | Not tested | Directional: multiround > isolated on ETD |
| IDP mechanism | Unaudited (flat in v5) | Orchestrator extraction path audited before Phase 5 |
| Contamination detection | Post-hoc | Zero-variance check after each batch |
