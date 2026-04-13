# Model Assignments — v7

> **Status:** Frozen. All model slugs verified against OpenRouter availability
> (cached `openrouter_models.json`).
>
> **Anti-bias constraint** [→ decision b117d517]: no two adjacent stages in the
> data chain share a vendor family. Chain: OpenAI → Anthropic → OpenAI → Qwen → Google.

---

## Case Generation Pipeline (orchestrator.py)

| Stage | Role | Model | Vendor |
|---|---|---|---|
| stage1 | Hypothesis generator | `openai/gpt-5.4-mini` | OpenAI |
| stage2 | Sound design writer | `anthropic/claude-haiku-4.5` | Anthropic |
| stage3 | Corruption node | `openai/gpt-5.4` | OpenAI |
| stage4 | Ground truth assembler | `qwen/qwen3-235b-a22b` | Qwen |
| stage2m | Mixed design writer | `openai/gpt-5.4` | OpenAI |
| stage3m | Mixed assembler | `qwen/qwen3-235b-a22b` | Qwen |
| smoke | Smoke test (structural gate) | `google/gemini-3-flash-preview` | Google |
| scorer | Smoke scorer | `openai/gpt-5.4-mini` | OpenAI |

## RC Extraction Pipeline (rc_extractor.py)

| Stage | Role | Model | Vendor |
|---|---|---|---|
| rc2 | Flaw extraction | `openai/gpt-5.4` | OpenAI |
| rc3 | must_not_claim generation | `openai/gpt-5.4` | OpenAI |

## Benchmark + Scoring (Phase 5–6)

| Script | Role | Model | Vendor |
|---|---|---|---|
| phase5_benchmark.py | Debate LLM (critic/defender/adjudicator) | `anthropic/claude-sonnet-4.6` | Anthropic |
| v7_scoring.py | Cross-vendor IDR/IDP scorer | `openai/gpt-5.4-mini` | OpenAI |

## Changes from v6

| Stage | v6 | v7 | Reason |
|---|---|---|---|
| stage1 | `openai/gpt-4o-mini` | `openai/gpt-5.4-mini` | Generation upgrade |
| stage2 | `anthropic/claude-haiku-4-5` | `anthropic/claude-haiku-4.5` | Slug fix (dash→dot) |
| stage3 | `openai/gpt-4o` | `openai/gpt-5.4` | Generation upgrade |
| stage4 | `qwen/qwen3-235b-a22b-2507` | `qwen/qwen3-235b-a22b` | Drop date suffix |
| stage2m | `openai/gpt-4o` | `openai/gpt-5.4` | Generation upgrade |
| stage3m | `qwen/qwen3-235b-a22b-2507` | `qwen/qwen3-235b-a22b` | Drop date suffix |
| smoke | `google/gemini-2.5-flash` | `google/gemini-3-flash-preview` | Generation upgrade |
| scorer | `openai/gpt-4o-mini` | `openai/gpt-5.4-mini` | Generation upgrade |
| rc2 | `openai/gpt-4o` | `openai/gpt-5.4` | Generation upgrade |
| rc3 | `openai/gpt-4o` | `openai/gpt-5.4` | Generation upgrade |
| benchmark | `anthropic/claude-sonnet-4-20250514` | `anthropic/claude-sonnet-4.6` | Slug fix [→ decision 8d7dba6b] |
| scoring | — (new in v7) | `openai/gpt-5.4-mini` | Cross-vendor [→ decision 4d49b663] |

## Notes

- All models route through OpenRouter (`OPENROUTER_API_KEY`)
- Benchmark model is configurable via `--model` flag; default is the table value
- Scoring model is configurable via `--model` flag; default is the table value
- The anti-bias constraint applies to the generation pipeline only; benchmark (Phase 5)
  is intentionally all-Claude, mitigated by cross-vendor scoring in Phase 6
