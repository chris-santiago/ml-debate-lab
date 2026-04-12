# Phase 0 — Setup

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - CWD: Bash tool CWD is always repo root (`ml-lab/`). Prefix all bash commands with `cd self_debate_experiment_v6 &&`.
> - Subagent context: authenticated Claude Code session. No direct API calls.

## Required Reading
- [design_decisions.md](../references/design_decisions.md) — conditions list (§4), persona-biased debate spec (§6), scoring dimensions (§7)
- [v5_mitigations.md](../references/v5_mitigations.md) — PM class note explains the `acceptable_resolutions` bug category
- [schema_b.md](../references/schema_b.md) — `acceptable_resolutions` flat-array constraint applies to the fixed prompt template

## Key Constraints
- `stage3_mixed_assembler.md` fix is already applied — grep to confirm before proceeding.
- DRQ ceiling of 0.5 for mixed cases is **intentional**: `ideal_debate_resolution.type = "mixed"` means no agent produces a literal `"mixed"` verdict. Do not "fix" this ceiling.
- `ETD_CONDITIONS` in `self_debate_poc.py` must include both `biased_debate` AND `conditional_fm`.

---

## Steps

### 0.1 Verify `acceptable_resolutions` fix
```bash
cd self_debate_experiment_v6 && grep "acceptable_resolutions" pipeline/prompts/stage3_mixed_assembler.md
```
Expected output: `"empirical_test_agreed"` only — not the four-value list. If incorrect, apply fix before proceeding.

### 0.2 Environment verification
- Confirm `uv` is installed: `uv --version`
- Confirm env vars are set: `OPENROUTER_API_KEY`, `CROSS_VENDOR_API_KEY`
- Confirm agents installed in `~/.claude/agents/`: `ml-critic`, `ml-defender`, `research-reviewer`, `report-writer`

### 0.3 Create v6 directory structure
```bash
cd self_debate_experiment_v6 && mkdir -p v6_raw_outputs rc_candidates
```

### 0.4 Update `self_debate_poc.py`
Make the following changes in order:

**a) Drop DC entirely:**
- Remove DC from `DIMENSIONS`, `CONDITIONS_MATRIX`, and all scoring/reporting code
- DC was fully redundant with FVC (mean_abs_delta = 0.0 across all v5 conditions)

**b) Union IDR for ensemble:**
- In `compute_idr()` ensemble path: credit any-assessor-found (union), not majority-found
- Per-assessor `found` booleans must be stored in every output JSON for post-hoc union computation
- Majority-vote retained for the final verdict field only

**c) Rename `forced_multiround` → `conditional_fm`:**
- Update `CONDITIONS` list, file naming, and all references in scoring/reporting

**d) Add `biased_debate` condition:**
- Add `biased_debate` to `CONDITIONS`
- Add `biased_debate` to `ETD_CONDITIONS` (ETD fires on mixed cases for this condition)
- Add `conditional_fm` to `ETD_CONDITIONS` (was missing)

**e) Add `all_issues_adjudicated` output field:**
- `all_issues_raised` — unchanged: issues from Critic raw output (used for IDP_raw)
- `all_issues_adjudicated` — NEW: issues from adjudicator synthesis after Defender exchange
- Both stored in every output JSON; both fed to the scorer
- Phase 6 and Phase 7 report IDP separately: `IDP_raw` (existing def) and `IDP_adj` (adjudicator-filtered)

### 0.5 Audit orchestrator prompt
- Review `pipeline/orchestrator.py` and its prompts for answer-key leakage vectors
- Confirm `all_issues_raised` is extracted from Critic raw output (not adjudicator synthesis)
- Confirm `all_issues_adjudicated` extraction path is added correctly
- This audit step is the "NEW from v5 lesson" in Phase 4 — front-loading it here catches structural issues before case generation

### 0.6 Commit RC scoring scope to `HYPOTHESIS.md`
RC scoring is **bidirectional**:
- `idr_documented` — recall against documented RC flaws (primary)
- `idr_novel` — novel valid concerns the debate surfaced that the reproducer missed (secondary)
Both score types saved separately in rescore JSON for independent analysis. Record this scope decision in `HYPOTHESIS.md` before Phase 5.

### 0.7 Create `biased_debate` agent prompt variants
Using the persona priming text from [design_decisions.md §6](../references/design_decisions.md#6-persona-biased-debate):

**Critic priming** (prepend to existing critic system prompt):
> "You are reviewing an experiment submitted by an inexperienced researcher. Be thorough and treat methodological gaps as real concerns until shown otherwise."

**Defender priming** (prepend to existing defender system prompt):
> "You are responding to a combative reviewer who frequently focuses on insignificant issues and overstates concerns. Be selective about what you concede."

Save as `biased_debate_critic.md` and `biased_debate_defender.md` in `pipeline/prompts/`.

### 0.8 Commit updated scoring engine and agent variants
Commit all changes before any runs begin.

---

## Verification
- [ ] `stage3_mixed_assembler.md` outputs `acceptable_resolutions = ["empirical_test_agreed"]` only — grep confirms
- [ ] `ETD_CONDITIONS` in `self_debate_poc.py` includes `biased_debate` and `conditional_fm`
- [ ] Orchestrator prompt audited: `all_issues_raised` extraction path verified (IDP mechanism)

## Outputs
- Updated `self_debate_poc.py`
- `pipeline/prompts/biased_debate_critic.md`
- `pipeline/prompts/biased_debate_defender.md`
- Committed to git

## Gate
All scoring engine changes and agent variants committed before Phase 1 begins.
