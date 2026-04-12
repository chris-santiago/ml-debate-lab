---
marp: true
theme: default
paginate: true
style: |
  section {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    padding: 30px 52px;
    font-size: 1.0em;
  }
  h1 {
    font-size: 1.65em;
    color: #1a1a2e;
    border-bottom: 3px solid #e94560;
    padding-bottom: 6px;
    margin-bottom: 10px;
    margin-top: 0;
  }
  h3 { color: #444; margin: 2px 0 8px 0; }
  table {
    font-size: 0.8em;
    width: 100%;
    margin: 8px 0;
  }
  th {
    background: #1a1a2e;
    color: white;
    padding: 5px 8px;
  }
  td { padding: 4px 8px; }
  tr:nth-child(even) { background: #f4f4f4; }
  .hero {
    font-size: 0.9em;
    background: #f0f7ff;
    border-left: 4px solid #e94560;
    padding: 8px 14px;
    margin: 8px 0 0 0;
  }
  pre {
    font-size: 0.77em;
    margin: 6px 0;
  }
  p { margin: 5px 0; }
  ul { margin: 4px 0; padding-left: 1.4em; }
  blockquote { margin: 8px 0; }
---

# Does AI Debate Produce Better Verdicts?

### Benchmark Results — ml-lab

&nbsp;

**Adversarial debate between AI agents produces measurably more correct evaluations** than single-pass assessment — but not for all the reasons we expected.

&nbsp;

*20 benchmark cases · 3 conditions · known correct answers*

---

# The Research Question

Standard AI evaluation is single-pass: give a model some work, ask what it thinks, get an answer.

**When does this fail?**
- The flaw requires independently questioning the framing
- The work is actually valid but sounds questionable
- The correct answer is "run this specific test first" — not a binary verdict

**What we tested:** Does adding adversarial structure — a Critic and Defender in debate — produce *measurably more correct* verdicts on cases where we already know the right answer?

<div class="hero">
<strong>Key design choice:</strong> Known ground truth for every case. "Better" has a definite answer.
</div>

---

# Experimental Design

**20 synthetic ML reasoning scenarios** across 6 categories:

| Category | Description | n |
|----------|-------------|---|
| Broken baselines | Flawed comparison methodology | 4 |
| Metric mismatches | Wrong metric for the claim | 3 |
| Hidden confounders | Temporal, selection, or distribution bias | 4 |
| Scope misunderstandings | Conclusion doesn't follow from evidence | 4 |
| **False-positive traps** | Valid work, adversarial framing | 5 |

Three conditions run against every case. Pass criteria set before running anything: mean ≥ 0.65, ≥ 75% cases pass, lift ≥ +0.10 over baseline.

---

# The Three Conditions

| Condition | Design | What it isolates |
|-----------|--------|-----------------|
| **Single-pass baseline** | One agent, one call, no structure | The floor — unstructured LLM evaluation |
| **Compute-matched ensemble** | 3 independent assessors + synthesizer, no roles | What more compute and perspectives alone buy |
| **Debate protocol** | Critic → Defender → Judge, sequenced dispatch | What adversarial role structure adds on top |

The ensemble uses identical total compute to the debate. Any gap between them is attributable to role structure, not compute budget.

<div class="hero">
<strong>Why the ensemble condition?</strong> Without it, you can't separate "debate is better" from "more LLM calls are better."
</div>

---

# Results

All three pre-registered benchmark criteria passed.

| Condition | Mean Score | Cases Passed |
|-----------|:----------:|:------------:|
| Single-pass baseline | 0.38 | 12 / 20 |
| Compute-matched ensemble | 0.75 | 17 / 20 |
| **Debate protocol** | **0.97** | **19 / 20** |

Raw lift debate vs. baseline: **+0.586**. But two rubric dimensions score structurally differently — the baseline has no Defender (DC = 0.0 by design) and is capped on resolution quality (DRQ ≤ 0.5).

<div class="hero">
<strong>Honest corrected lift:</strong> +0.335 to +0.441 after neutralizing structural rubric penalties. Still 3–4× the pre-registered +0.10 threshold. Debate vs. ensemble: +0.216 (p = 0.004, r = 0.758).
</div>

---

# What Debate Does NOT Uniquely Provide

Two claimed advantages turned out to be wrong.

**Empirical test design (ETD)**
The debate protocol reliably produces well-specified empirical tests. We attributed this to adversarial forcing. An ablation falsified that: adding one explicit output instruction to the ensemble synthesizer achieves ETD mean **0.962** — nearly matching debate's 1.0.

*ETD is a prompt design effect. It's portable to any multi-agent configuration.*

**Exclusive exoneration of valid work**
A compute-matched ensemble correctly exonerated valid work in **4 of 5** false-positive trap cases without role isolation. Structural isolation is not uniquely necessary for reaching the right verdict.

<div class="hero">
<strong>Implication:</strong> You can get well-specified tests from an ensemble by adding one instruction. The debate's edge is elsewhere.
</div>

---

# What Debate DOES Provide

**Structured argumentation and contested-position resolution** *(confirmed)*

The Critic/Defender structure forces point-by-point rebuttal — every claim conceded, rebutted, or flagged as empirically open. More importantly, it forces engagement with both sides of a genuinely two-sided question.

**The clearest example (mm002):** An offline NDCG improvement challenged by a concern about offline-online correlation validity.
- Ensemble: all 3 assessors ignored the concern and agreed to run an A/B test → score **0.000**
- Debate: correctly identified that a calibration study was needed first → score **1.0**

This failure mode is **structural to parallel ensemble design**. Adding more assessors doesn't fix it — they all converge on the same intuitive answer because no one is required to argue the other side.

---

# The False-Positive Trap Finding

Five cases: valid work, sound methodology, presented under adversarial framing. The question is whether the protocol wrongly condemns it.

| Condition | Correct verdicts | Clean exonerations |
|-----------|:----------------:|:-----------------:|
| Single-pass baseline | **0 / 5** | 0 / 5 |
| Compute-matched ensemble | 4 / 5 | 2 / 4 correct |
| Debate protocol | **5 / 5** | 3 / 5 |

The baseline scored **0.000 on all five** — it accepted the adversarial framing entirely and condemned every piece of valid work it was shown.

The "clean exoneration" edge (3/5 no concerns vs. ensemble hedging on 2) is directional only — n=5 is below statistical threshold and the pattern did not replicate in the external exoneration benchmark.

---

# External Validation

The synthetic benchmark could have been too easy or too tailored. Two separate external benchmarks tested this.

**Fault detection — 10 cases from published ML failures**
Cases from Dacrema 2019, Obermeyer 2019, DeGrave 2021, and others. Ground truth from the published record — no designer involvement.

→ Debate protocol IDR = **0.95**, meeting the ≥ 0.85 pre-specified threshold.

**Exoneration — 3 cases from peer-reviewed ML work**
BERT/SQuAD 1.1, ResNet-152/ImageNet, clinical 5-fold CV — methodology is genuinely sound.

→ Debate protocol **3/3 pass** (mean 0.875). Baseline: 0/3 on rubric (DC = 0.0 structural rule), correct verdict label in all 3.

<div class="hero">
<strong>Note:</strong> Critics raised plausible-but-wrong concerns on all 3 external exoneration cases (IDP = 0.5). The "clean exoneration" tendency from the internal benchmark did not replicate externally.
</div>

---

# ⚠️ Remaining Limitations

Take the results at face value, but know what they can't yet tell you.

| Limitation | What it means |
|------------|---------------|
| **Synthetic benchmark** | 20 cases, author-designed. Expanding requires expensive ground-truth labeling. |
| **Same model family** | All agents used claude-sonnet-4-6. Cross-vendor validation (GPT-4o, Gemini) is pending. |
| **n=5 exoneration finding** | Below conventional statistical thresholds. Directional only. |
| **Author-assigned difficulty labels** | Difficulty calibration was not independently verified. |
| **No cross-vendor scorer** | Haiku validation confirmed no IDR bias within Anthropic family; external scorer pending. |

<div class="hero">
<strong>Bottom line:</strong> Results are specific to the claude-sonnet-4-6 capability tier. The honest corrected lift (+0.335 to +0.441) clears the pre-registered threshold by 3–4×, but replicate before treating as general.
</div>
