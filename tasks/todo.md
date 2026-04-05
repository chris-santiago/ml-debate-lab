# Agent Development TODOs

---

## ~~ml-lab: Report mode selection prompt~~ ✓ DONE

**Before beginning the investigation**, ml-lab should ask the user whether they want:
- **Full report** — complete Step 8 writeup (`REPORT.md`) plus Step 10 peer review loop
- **Conclusions only** — stop after Step 7 (`CONCLUSIONS.md`) and Step 9 (production addendum); skip Step 8 and Step 10

This sets `report_mode` for the session. Default should be full report if the user doesn't specify.

After completing Steps 1–9 in full-report mode, ml-lab should ask the user whether they want to run the Step 10 peer review loop before kicking it off — don't start it automatically.

---

## ~~ml-lab: User-approved plans at key decision gates~~ ✓ DONE

At three points in the investigation, ml-lab should write a plan and surface it to the user for approval before proceeding. These are the highest-stakes transitions — each one commits significant compute and shapes everything that follows.

**Gate 1 — After debate phase (end of Step 5)**

Before entering Step 6, write a plan covering:
- The empirical test list extracted from `DEBATE.md` (each test, its pre-specified verdicts, and which side it favors)
- Conceded critique points that must be addressed in experiment design
- The proposed experimental conditions and baseline(s)
- Any subpopulations or stratifications identified in the debate

Present this as the experiment plan. Do not begin Step 6 until the user approves. This is already partially implied by the existing "present the debate summary and empirical test list to the user" instruction — this TODO formalizes it as an explicit written plan with approval required.

**Gate 2 — After macro-iteration decision (Outcome B or C)**

When a macro-iteration is triggered (return to adversarial review or return to hypothesis), write a plan covering:
- What triggered the re-opening (the specific finding or falsification)
- Which path is recommended (Outcome B or C) and why
- What the next cycle will test that the current cycle could not
- What artifacts will be updated and how

Present and wait for user confirmation before re-entering the loop. This replaces the current "wait for user confirmation" with a structured written plan rather than an inline description.

**Gate 3 — After first peer review round (Step 10, Round 1 only)**

After `PEER_REVIEW_R1.md` is written, before addressing any findings, write a plan covering:
- Each MAJOR issue: proposed action type (text fix / additional analysis / full experiment) and specific remediation
- Each MINOR issue: proposed action or deferral rationale
- Estimated scope of changes to `REPORT.md` and other artifacts

Present and wait for user approval before executing any fixes. Rounds 2–3 (Haiku verification) do not require a plan — only the deep Opus first pass does.

**Implementation notes:**
- Plans should be written as structured markdown, not inline prose
- Each gate plan is ephemeral — it does not need to be saved as an artifact unless the user asks
- The three gates are independent; none requires the others to exist

---

## ~~Update "An Example Run" in README after ml-lab edits are finalized~~ ✓ DONE

Once all changes to `agents/ml-lab.md` are complete, revisit the "An Example Run" section in the root README and update it to reflect the current workflow. Specifically check:
- Step count and naming (currently 9-step; ml-lab is now 10-step)
- Whether the fraud detection walkthrough accurately reflects the current agent behavior, prompts, and escalation logic
- Any new steps or behavioral changes (report mode selection, peer review loop, final synthesis report) that would change how the example run reads

The walkthrough is the primary "does this actually work?" demonstration for new users — it should always reflect the live agent, not an earlier version.

---

## README reorganization (post-plugin publish)

Once the ml-lab plugin is published, reorganize the root README into two distinct parts:

**Part 1 — ml-lab plugin** (primary audience: new users who want to use the tool)
- What ml-lab is and what it does
- Installation instructions
- How to invoke it and what to expect
- The complete fraud detection walkthrough (currently in "An Example Run")

**Part 2 — Experiment and results** (primary audience: readers interested in the evidence)
- Everything currently in "The Setup", "What We Found", "Should I Use ml-lab or Just Run an Ensemble?", "Why This Matters"
- External validation, limitations, artifact index

The motivation: right now the README leads with the experiment, which buries the tool. Once the plugin is live and people are finding it through the plugin registry, the first thing they need is how to install and use it — not a benchmark writeup.

---

## ~~ml-lab: Final synthesis report in "results mode"~~ ✓ DONE

After all steps complete, ml-lab should ask the user if they want a final technical report that synthesizes all conclusions, findings, and interim artifacts.

This report is distinct from the narrative `REPORT.md` written in Step 8. It is written in **results mode**:

- Findings are stated as known facts, not discoveries
- Limitations are described as structural properties of the design, not encountered surprises
- The narrative arc ("we found X, then Y surprised us") is replaced by a logical arc:
  *here is the question → here is the evidence → here is what it means*
- Multi-iteration arcs are explained by their logical necessity, not their chronological sequence

**Implementation notes:**
- This is an optional Step 11, triggered only on user confirmation
- It reads all artifacts (CONCLUSIONS.md, REPORT.md, REPORT_ADDENDUM.md, PEER_REVIEW_R*.md) and synthesizes into a single document
- Artifact: `REPORT_FINAL.md`
- The existing `REPORT.md` is preserved as the working document; `REPORT_FINAL.md` is the publication-ready version

