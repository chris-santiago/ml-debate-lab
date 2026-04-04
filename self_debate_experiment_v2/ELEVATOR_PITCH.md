# Does Debate Between AI Agents Get Us Closer to the Truth?

## The Question

When an AI evaluates a piece of work — a model result, a statistical claim, a deployment decision — can it actually catch real problems? And does adding a second AI to argue the other side make it better, or is it just more words?

We built an experiment to find out.

---

## What We Did

We created 20 synthetic ML scenarios with *known correct answers* — cases like:

- A team claiming their model improved by 4 points, but evaluated on 1/10th the data with no confidence intervals
- A loyalty program showing a 22% sales lift that launched on November 1st (right before Black Friday)
- A fine-tuned model beating a zero-shot model, with the team concluding their architecture is superior
- Methodologically *sound* work, presented under adversarial conditions, to test whether the system would wrongly condemn it

Each case had a planted flaw (or deliberate absence of one), a ground-truth correct verdict, and specific issues the evaluation had to find.

We then ran two conditions against every case:

**Debate condition:** Two AI agents receive the same scenario with no shared context. One plays Critic, one plays Defender. Each produces an independent assessment. A Judge adjudicates and assigns a typed verdict: *critique wins*, *defense wins*, or *run an empirical test*.

**Baseline condition:** One AI agent, one pass, no debate structure.

---

## What We Found

The debate protocol scored **0.97 out of 1.0** on average. The single-pass baseline scored **0.38**.

A lift of **+0.59** on a 0-to-1 scale is large. The threshold we set in advance to call the experiment a success was +0.10. We exceeded it by nearly 6×.

19 of 20 cases passed.

---

## The Most Interesting Finding

Five of the 20 cases were *false-positive critique traps* — methodologically sound work deliberately presented under adversarial framing, to test whether the protocol would wrongly flag valid results.

The single-pass baseline scored **0.000** on all five. It accepted the adversarial framing, treated the planted critique as valid, and condemned work that was actually fine.

The debate protocol got all five correct.

This is the clearest result in the experiment: a single AI reasoning pass has no mechanism to push back on an adversarial premise. It inherits the framing. Adding an independent Defender — one that never saw the Critic's output — is the only way to exonerate valid work.

---

## Where It Failed

One case failed: a healthcare triage scenario where the Defender *correctly identified all the flaws in its own analysis text* but then labeled its verdict "the work is valid." The reasoning was right; the label was wrong. This is a calibration failure in the Defender's output structure, not a reasoning failure — and it's fixable.

Two cases showed the Defender being overly cautious: it correctly identified why the work was sound but hedged toward "needs more testing" rather than committing to "this is fine." Both cases still passed, but the under-confidence is a real pattern.

---

## Why This Matters

The standard approach to AI evaluation is single-pass: give a model some work, ask it what it thinks, get an answer. This works when the flaw is obvious. It fails when:

- The flaw requires independently questioning the framing
- The work is actually valid but sounds questionable
- The correct answer is "we need to test X first" rather than a yes/no

Debate adds something single-pass cannot: an independent second opinion with no access to the first. The context isolation is not a technicality — it's what makes the disagreement meaningful. When both agents independently find the same flaw, you have convergent evidence. When they disagree, you have a genuinely contested claim that requires an experiment to resolve.

---

## The Setup in Brief

- **20 benchmark cases**, 6 categories (broken baselines, metric mismatches, hidden confounders, scope misunderstandings, false-positive traps, real-world deployment framing)
- **Scoring rubric** defined before running the experiment: issue discovery, defense calibration, verdict quality, empirical test design, final verdict correctness
- **Full context isolation** between agents — no shared outputs before independent assessments
- **Known ground truth** for every case, so "better" has a definite answer
- **Benchmark pass criteria** set in advance: mean ≥ 0.65, ≥ 75% of cases pass, lift ≥ +0.10

All three criteria passed.

---

## Bottom Line

When AI agents debate with genuinely isolated context, the result is substantially better than a single-pass assessment — not because debate sounds more thorough, but because it produces measurably more correct verdicts on cases where we already know the right answer.

The biggest gains are exactly where you'd want them: catching hidden confounders, refusing to condemn valid work, and forcing contested claims into the right kind of empirical resolution rather than a confident-sounding guess.
