# Phase 9 — Cross-Vendor Validation

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - CWD: Bash tool CWD is always repo root (`ml-debate-lab/`). Prefix all bash commands with `cd self_debate_experiment_v6 &&`.
> - Subagent context: authenticated Claude Code session. No direct API calls.

## Required Reading
- [hypotheses.md](../references/hypotheses.md) — H5 cross-model scorer agreement definition

## Key Constraints
- Frame results as **confound quantification**, not mitigation. GPT-4o is the primary scorer; Claude secondary results characterize the magnitude of the closed-loop confound.
- Flag if IDR delta (GPT-4o vs Claude) > 0.50.
- Requires `CROSS_VENDOR_API_KEY`, `CROSS_VENDOR_BASE_URL`, `CROSS_VENDOR_MODEL` env vars.

---

## Steps

### 9.1 Run Claude secondary scorer on all 2,160 files
Claude re-scores IDR, IDP, and ETD on the same outputs GPT-4o scored in Phase 6.
Uses the same scoring prompts; different model.

```bash
cd self_debate_experiment_v6 && uv run cross_vendor_scorer.py \
  --scores v6_rescored_idr_idp.json \
  --output v6_cross_vendor_scores.json
```

### 9.2 Compute GPT-4o vs Claude deltas
For each dimension (IDR, IDP, ETD) and each condition:
- Compute mean absolute delta between GPT-4o and Claude scores
- Compute Spearman ρ between rankings

### 9.3 Report confound magnitude
- IDR delta across conditions: does the closed-loop confound inflate debate conditions more than baseline?
- IDP delta: similar analysis
- ETD delta on mixed-case debate conditions

### 9.4 Flag threshold
If IDR delta > 0.50 for any condition, record as a critical finding in `CROSS_VENDOR_VALIDATION.md` — indicates the cross-scorer confound is large enough to materially affect interpretation.

---

## Verification
(none — cross-scorer delta check is the output of this phase)

## Outputs
- `CROSS_VENDOR_VALIDATION.md` — GPT-4o vs Claude deltas on IDR/IDP/ETD, confound framing, flag if delta > 0.50

## Gate
`CROSS_VENDOR_VALIDATION.md` written. H5 data ready for inclusion in Phase 7 results if not already reported.
