# Evaluation

## The Reframe

The debate pipeline is a 3-class classifier.

- **Input:** hypothesis + PoC code
- **Output:** `defense_wins` / `empirical_test_agreed` / `critique_wins`
- **Ground truth:** SOUND / MIXED / FLAWED case label
- **Task:** multiclass classification

The critic, defender, and adjudicator are the model. They happen to be LLM agents, but from the outside the system takes an input and produces a class label. Every tool built for evaluating classifiers applies. The taxonomy in METRICS.md defines what to measure and how to structure agent outputs. This document defines how to compute those measurements using standard tools.

---

## Verdict → Numeric Mapping

```python
VERDICT_MAP = {
    "defense_wins":          0,   # predicted SOUND
    "empirical_test_agreed": 1,   # predicted AMBIGUOUS
    "critique_wins":         2,   # predicted FLAWED
}

LABEL_MAP = {
    "defense": 0,
    "mixed":   1,
    "regular": 2,
}
```

One mapping converts the full output stream to a standard integer array. All metrics derive from this.

---

## Existing Metrics Are Standard Metrics

Custom metric names are preserved for communication, but each maps to a standard sklearn call.

| Custom metric | Standard name | sklearn |
|---|---|---|
| DER (Defense Exoneration Rate) | Precision on class SOUND | `precision_score(y_true, y_pred, labels=[0], average=None)` |
| IDR (Issue Detection Rate) | Recall on class FLAWED | `recall_score(y_true, y_pred, labels=[2], average=None)` |
| FAR (False Alarm Rate) | FPR on class SOUND | `1 − precision[0]` from confusion matrix |
| FHR (False Hedge Rate) | Off-diagonal hedges on clear cases | derived from confusion matrix rows 0 and 2, column 1 |
| ARR (Ambiguity Recognition Rate) | Recall on class AMBIGUOUS | `recall_score(y_true, y_pred, labels=[1], average=None)` |
| VS (Verdict Stability) | Inter-rater agreement across 3 runs | `cohen_kappa_score(run_a, run_b)`, averaged over pairs |
| FCE (Finding Calibration Error) | Expected Calibration Error on severity scores | `calibration_curve(y_true_binary, severity/10, n_bins=4)` |
| wDCR (Severity-weighted Concession Rate) | Weighted false positive rate on findings | from taxonomy labels (see METRICS.md) |

All of DER, IDR, FAR, FHR, ARR fall out of a single `classification_report` call. No custom computation needed.

---

## Primary Metric: MCC

**Matthews Correlation Coefficient** replaces DER as the primary single-number summary for the iteration loop.

```python
from sklearn.metrics import matthews_corrcoef
mcc = matthews_corrcoef(y_true, y_pred)
```

**Why MCC over DER:**
- DER is precision on one class. A system that correctly exonerates defense cases but misses all regular flaws has DER = 1.0 and IDR = 0.0 — that's not a good system.
- MCC accounts for all cells of the confusion matrix simultaneously. It's equivalent to the geometric mean of precision and recall across all classes, corrected for chance agreement.
- MCC is bounded [−1, +1]. Random guessing gives MCC ≈ 0. A perfect classifier gives MCC = 1.0.
- MCC is robust to class imbalance — critical here, where defense cases are ~14% of the benchmark.

DER and IDR remain reported as secondary metrics (they tell you *where* performance comes from). MCC is what the acceptance criterion is applied to.

**MMD for MCC:** 0.06 (approximately 2 SE at n=120 canary evaluations, baseline MCC ≈ 0.0).

---

## Confusion Matrix as Phase 1 Diagnostic

The 3×3 confusion matrix replaces manual transcript reading for failure mode classification.

```python
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay

cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])
disp = ConfusionMatrixDisplay(cm, display_labels=["SOUND", "AMBIG", "FLAWED"])
disp.plot()
```

Each off-diagonal cell corresponds to a failure mode from PROTOCOL.md Phase 1:

| Cell | Failure mode |
|---|---|
| SOUND predicted as FLAWED (cm[0,2]) | False alarm — Intervention A/B target |
| SOUND predicted as AMBIGUOUS (cm[0,1]) | False hedge on clear case — FHR |
| FLAWED predicted as SOUND (cm[2,0]) | Missed flaw — IDR regression |
| FLAWED predicted as AMBIGUOUS (cm[2,1]) | Hedged on clear flaw — FHR |
| MIXED predicted as SOUND (cm[1,0]) | Over-exoneration — ARR regression |
| MIXED predicted as FLAWED (cm[1,2]) | Over-detection on ambiguous case — ARR regression |

Running the confusion matrix on v7 prompts under new scoring (Phase 0.5) gives the failure mode distribution without reading transcripts. Phase 1 transcript reading then focuses on the *why* for the largest off-diagonal cells, not on counting.

---

## 3 Runs = Ensemble → Soft Probabilities

Three runs with different model draws form an ensemble. Ensembles produce soft class probabilities:

```python
def soft_probs(run_verdicts: list[str]) -> dict:
    """run_verdicts: list of 3 verdict strings for one case."""
    counts = Counter(run_verdicts)
    total = len(run_verdicts)
    return {
        "p_sound": counts["defense_wins"] / total,
        "p_ambig": counts["empirical_test_agreed"] / total,
        "p_flawed": counts["critique_wins"] / total,
    }
```

With soft probabilities:

**Log loss** (proper scoring rule — penalizes confident wrong predictions):
```python
from sklearn.metrics import log_loss
# y_prob shape: (n_cases, 3) — [p_sound, p_ambig, p_flawed]
loss = log_loss(y_true_onehot, y_prob)
```

**Multiclass Brier score** (bounded, calibration-aware):
```python
# per class Brier score
brier_sound  = mean((y_true_binary_sound  - y_prob[:, 0]) ** 2)
brier_flawed = mean((y_true_binary_flawed - y_prob[:, 2]) ** 2)
```

**VS as ensemble agreement:** Cohen's Kappa across the 3 pairwise run combinations:
```python
from sklearn.metrics import cohen_kappa_score
pairs = [(0,1),(0,2),(1,2)]
vs = mean([cohen_kappa_score(runs[a], runs[b]) for a,b in pairs])
```

Kappa corrects for chance agreement, making VS comparable across case distributions with different base rates. Raw agreement (fraction matching majority) overestimates stability when one class dominates.

---

## Finding-Level Scoring: Multiple Instance Learning

Case labels are known; finding labels are not. This is Multiple Instance Learning (MIL):

- Each case is a **bag** containing N findings
- Bag label is known: SOUND (no genuine flaw) or FLAWED (≥1 genuine flaw)
- Instance label (is this specific finding a real flaw?) is unknown

**MIL-compatible loss (from SCORING.md Brier-like finding scores):**

```python
def finding_score(severity: int, stratum: str) -> float:
    p = severity / 10.0
    if stratum == "regular":
        return 1 - (1 - p) ** 2      # reward confident correct findings
    elif stratum == "defense":
        return -(p ** 2)              # penalize confident false alarms
    else:
        return 0.0                    # mixed: not scored at finding level
```

Average across all FATAL/MATERIAL findings per case, then combine with verdict score per SCORING.md.

**Finding calibration** via sklearn:
```python
from sklearn.calibration import calibration_curve

# severity/10 as probability estimate; y_binary = (stratum == "regular")
fraction_of_flaws, mean_predicted = calibration_curve(
    y_binary, severity_scores / 10, n_bins=4
)
# FCE = mean absolute deviation from diagonal
fce = mean(abs(fraction_of_flaws - mean_predicted))
```

A perfectly calibrated critic: score-8 findings appear on genuinely flawed cases 80% of the time. FCE = 0 means perfectly calibrated; FCE > 0.15 means the severity scores are misleading.

---

## Prompt Comparison: McNemar's Test

The MMD threshold (MCC ≥ 0.06) is a heuristic for the iteration loop. At the full benchmark, use McNemar's test for principled comparison between two prompt versions.

```python
from statsmodels.stats.contingency_tables import mcnemar

# contingency table: where do the two classifiers disagree?
# b = cases where version A correct, version B wrong
# c = cases where version A wrong, version B correct
table = [[n_both_correct, b], [c, n_both_wrong]]
result = mcnemar(table, exact=False)
print(result.pvalue)
```

McNemar's test is the standard non-parametric test for comparing two classifiers on the same test set (paired observations). It tests whether one classifier's error pattern is significantly different from the other's — not whether overall accuracy differs. This is the right test when the cases are fixed and the prompt is what changed.

**When to use:** Full benchmark comparison only (n ≥ 280 cases). With n=40 canary cases, McNemar's has low power. Use MMD at canary scale; McNemar's at full benchmark.

---

## Prompt Iteration as Hyperparameter Search

| Experiment protocol element | ML equivalent |
|---|---|
| Canary set (40 cases, fixed) | Validation set (held constant across trials) |
| Full benchmark (280 cases) | Test set (evaluated once per candidate configuration) |
| Prompt iteration loop | Hyperparameter search |
| MMD threshold | Minimum improvement to accept a trial |
| 15-iteration budget cap | Max trials |
| 3 consecutive accepts → full benchmark | Early stopping + final test evaluation |
| Fixed model seeds during iteration | Fixed validation fold across trials |
| Fully random seeds at full benchmark | No fold-overfitting: full generalization estimate |
| Max 2 full benchmark runs | No test set reuse: prevents threshold overfitting |

The canonical ML failure: evaluating on the test set repeatedly until a configuration passes. Max 2 full benchmark runs is the enforcement mechanism. The canary is the validation set — iterate on it freely, never mistake it for the final score.

---

## Evaluation Script Skeleton

```python
import numpy as np
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    matthews_corrcoef,
    cohen_kappa_score,
    log_loss,
)
from sklearn.calibration import calibration_curve

VERDICT_MAP = {"defense_wins": 0, "empirical_test_agreed": 1, "critique_wins": 2}
LABEL_MAP   = {"defense": 0, "mixed": 1, "regular": 2}

def evaluate(results: list[dict]) -> dict:
    """
    results: list of dicts with keys:
      case_id, stratum, ground_truth, runs (list of 3 verdict strings),
      findings (list of dicts with severity, finding_score per run)
    """
    y_true, y_pred, y_prob = [], [], []

    for r in results:
        gt  = LABEL_MAP[r["stratum"]]
        run_labels = [VERDICT_MAP[v] for v in r["runs"]]
        majority   = max(set(run_labels), key=run_labels.count)

        probs = [
            run_labels.count(0) / 3,   # p_sound
            run_labels.count(1) / 3,   # p_ambig
            run_labels.count(2) / 3,   # p_flawed
        ]

        y_true.append(gt)
        y_pred.append(majority)
        y_prob.append(probs)

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    y_prob = np.array(y_prob)

    report = classification_report(
        y_true, y_pred,
        labels=[0, 1, 2],
        target_names=["SOUND", "AMBIG", "FLAWED"],
        output_dict=True,
    )

    return {
        "mcc":        matthews_corrcoef(y_true, y_pred),
        "log_loss":   log_loss(y_true, y_prob),
        "DER":        report["SOUND"]["precision"],
        "IDR":        report["FLAWED"]["recall"],
        "ARR":        report["AMBIG"]["recall"],
        "FHR":        _false_hedge_rate(y_true, y_pred),
        "confusion":  confusion_matrix(y_true, y_pred, labels=[0,1,2]).tolist(),
        "report":     report,
    }

def _false_hedge_rate(y_true, y_pred):
    """FHR: proportion of clear cases (SOUND + FLAWED) predicted as AMBIGUOUS."""
    clear_mask = (y_true == 0) | (y_true == 2)
    return np.mean(y_pred[clear_mask] == 1)
```

---

## Relationship to METRICS.md

METRICS.md defines the **taxonomy** (finding → rebuttal → adjudication structure, severity scale, DCR, FCE formulas). This document defines the **evaluation pipeline** (how taxonomy outputs become numpy arrays and sklearn metric calls).

The taxonomy is upstream: it specifies what structured fields the pipeline must emit. The evaluation script is downstream: it consumes those fields and produces the final metric table. Neither replaces the other.

**Data flow:**
```
Case + PoC
  → Critic (CRITIQUE.md: finding_id, severity, severity_label per finding)
  → Defender (DEFENSE.md: finding_id, rebuttal_type, severity_adjustment per rebuttal)
  → Adjudicator (ADJUDICATION.md: point_verdict per rebuttal, case_verdict)
  → evaluate() → MCC, DER, IDR, FHR, ARR, confusion matrix, log loss
```
