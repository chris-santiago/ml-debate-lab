# Working Paper

The full research paper documenting ml-lab's adversarial debate evaluation methodology. Covers the problem statement, related work, methodology design, experimental results across multiple versions, and conclusions.

!!! note "Source location"
    The working paper is maintained at [`WORKING_PAPER.md`](https://github.com/chris-santiago/ml-lab/blob/main/WORKING_PAPER.md) in the repository root. This page provides context; the canonical version lives there.

## Abstract

ml-lab uses an adversarial critic-defender debate protocol to evaluate ML methodology claims. This paper presents the protocol design, describes eight iterative experiments that calibrated the methodology, and reports detection and verdict accuracy on benchmark cases with known ground truth.

## Submission tracks

The paper is being prepared for:

| Venue | Track | Status |
|-------|-------|--------|
| arXiv | Preprint | In preparation |
| EMNLP 2026 | Conference | In preparation |
| NeurIPS 2026 | Conference | In preparation |

Submission-specific checklists and formatting are tracked in `paper/` subdirectories.

## Key results

- Detection performance: validated across v2–v7 with pre-registered hypotheses
- Ambiguity judgment: validated (system correctly identifies genuinely ambiguous cases)
- Defense-case calibration: pending (v8, active)
- Cross-vendor stability: evaluated in v6

For detailed per-version results, see the [Experiment Reports](reports/v1-v3.md).
