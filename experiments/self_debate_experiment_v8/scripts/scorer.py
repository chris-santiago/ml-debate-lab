# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "numpy>=2.0",
#   "scikit-learn>=1.5",
#   "statsmodels>=0.14",
# ]
# ///
"""
v8 scoring pipeline.

OBJECTIVE
---------
ml-lab produces zero defense_wins verdicts on sound methodology (v7 DER=0.00).
This script measures whether prompt interventions fix that — without breaking
flaw detection (IDR) or introducing over-exoneration (MCC, ARR).

The debate pipeline is treated as a 3-class classifier:
  Input:  hypothesis + PoC code
  Output: defense_wins | empirical_test_agreed | critique_wins
  Labels: SOUND (defense) | AMBIGUOUS (mixed) | FLAWED (regular)

PRIMARY METRIC: MCC (Matthews Correlation Coefficient). DER alone can be gamed
by exonerating everything; MCC accounts for all 9 cells of the confusion matrix.
MMD = 0.06 at canary scale (n=120). Changes below MMD are noise.

INTERVENTION DIAGNOSTIC CHAIN
------------------------------
Three interventions are tested in sequence (A → B → C). Each has a leading
indicator that should move *before* the primary metric (DER/MCC) improves.
If the leading indicator doesn't move, the mechanism didn't activate.

  Intervention A — Critic significance threshold (NIT filter):
    Leading:  CER_defense ↓  (fewer non-NIT findings on sound cases)
              critic_brier_defense → 0  (less severity overclaiming)
    Lagging:  DER ↑

  Intervention B — Defender exoneration path (anti-sycophancy):
    Leading:  wDCR ↓  (defender conceding less on defense cases)
              defender_brier_defense → 0  (defender dismissing false alarms)
    Lagging:  DER ↑

  Note — no Intervention C (adjudicator):
    Verdict derivation is deterministic (derive_verdict() in run_pipeline.py).
    AOR now measures defender self-consistency: how often the defender's claimed
    overall_verdict disagrees with the verdict derived from its own structured
    rebuttal fields. AOR > 0 after Intervention B means the defender is producing
    internally inconsistent output (e.g., claiming defense_wins while CONCEDEing
    a severity-7 finding) — a signal to tighten the defender's verdict calibration.

  Bottleneck diagnosis:
    wDCR drops but DER stays flat → check AOR.
      AOR > 0: defender claiming defense_wins but rebuttals don't support it
               → tighten defender verdict calibration (more Intervention B).
      AOR = 0: defender rebuttals not reaching defense_wins threshold
               → more Intervention B (confidence to use REBUT-IMMATERIAL).

REGRESSION FLOORS (must not be crossed by any accepted change)
--------------------------------------------------------------
  IDR ≥ 0.75   — flaw detection must not degrade
  FHR ≤ +0.05  — hedging on clear cases must not increase
  ARR ≥ 0.60   — ambiguity recognition on mixed cases must hold

Usage:
    uv run scripts/scorer.py --results-dir <dir> [--output scores.json] [--label name]
    uv run scripts/scorer.py --results-dir <candidate> --compare <baseline>  # McNemar's test

Input format (one JSON file per run, named arbitrarily):
    {
      "case_id":    str,
      "stratum":    "defense" | "regular" | "mixed",
      "flaw_category": str | null,   // regular cases only; matches critic finding
      "run_id":     int,
      "model_assignments": {"critic": str, "defender": str, "adjudicator": str},
      "critic_output": {
        "findings": [
          {
            "finding_id": str,
            "severity": int,          // 0-10
            "severity_label": str,    // FATAL|MATERIAL|MINOR|NIT
            "suppressed": bool,       // true if NIT
            "flaw_category": str | null
          }
        ],
        "no_material_findings": bool
      },
      "defender_output": {
        "rebuttals": [
          {
            "finding_id": str,
            "original_severity": int,
            "rebuttal_type": str,     // CONCEDE|REBUT-*|DEFER|EXONERATE
            "severity_adjustment": int,
            "adjusted_severity": int
          }
        ],
        "overall_verdict": str
      },
      "adjudicator_output": {           // populated by derive_verdict() — no LLM call
        "point_verdicts": [
          {
            "finding_id": str,
            "adjusted_severity": int,
            "rebuttal_type": str,
            "point_verdict": str,     // defense_wins|critique_wins|empirical_test_agreed
            "rule_applied": str       // which row of the verdict table was applied
          }
        ],
        "case_verdict": str           // defense_wins|empirical_test_agreed|critique_wins
      }
    }
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from statistics import mean

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    classification_report,
    cohen_kappa_score,
    confusion_matrix,
    log_loss,
    matthews_corrcoef,
)
from statsmodels.stats.contingency_tables import mcnemar

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VERDICT_MAP = {
    "defense_wins":          0,
    "empirical_test_agreed": 1,
    "critique_wins":         2,
}

LABEL_MAP = {
    "defense": 0,
    "mixed":   1,
    "regular": 2,
}

# Penalty-aware verdict scores per stratum (SCORING.md)
VERDICT_SCORES = {
    "defense": {
        "defense_wins":          +1.00,
        "empirical_test_agreed": -0.25,
        "critique_wins":         -0.50,
    },
    "regular": {
        "defense_wins":          -0.50,
        "empirical_test_agreed": -0.25,
        "critique_wins":         +1.00,
    },
    "mixed": {
        "defense_wins":          0.0,
        "empirical_test_agreed": 0.0,
        "critique_wins":         0.0,
    },
}

# ---------------------------------------------------------------------------
# Finding-level Brier scoring
# ---------------------------------------------------------------------------

def brier(p: float, y: int) -> float:
    """Asymmetric proper scoring rule. y ∈ {0, 1}.
    y=1 (real flaw): rewards confident high-severity; penalizes low severity.
    y=0 (false alarm): penalizes confident high-severity.
    """
    return 1 - (1 - p) ** 2 if y == 1 else -(p ** 2)


def get_finding_y(finding: dict, case_flaw_category: str | None, stratum: str) -> int:
    """Per-finding ground truth label.

    defense  → 0 (all findings are false alarms by definition)
    regular  → 1 if finding flaw_category matches case flaw_category, else 0
    mixed    → -1 (not scored at finding level)
    """
    if stratum == "defense":
        return 0
    if stratum == "regular":
        if case_flaw_category and finding.get("flaw_category"):
            return 1 if finding["flaw_category"] == case_flaw_category else 0
        return -1  # no category metadata — use MIL fallback
    return -1  # mixed


def aggregate_findings(
    findings: list[dict],
    rebuttals: list[dict],
    case_flaw_category: str | None,
    stratum: str,
) -> tuple[float, float]:
    """Returns (critic_brier, defender_brier) for the case.

    Primary path: finding-level ground truth via flaw_category match.
    MIL fallback: bag-level supervision when category metadata absent.
    """
    rebuttal_map = {r["finding_id"]: r for r in rebuttals}
    advancing = [f for f in findings if not f.get("suppressed", False)]

    if not advancing:
        return 0.0, 0.0

    # Decide path: primary if all advancing findings have flaw_category AND
    # case has flaw_category AND stratum is defense or regular
    use_primary = (
        stratum in ("defense", "regular")
        and (stratum == "defense" or case_flaw_category is not None)
    )

    cb_scores, db_scores = [], []

    for f in advancing:
        y = get_finding_y(f, case_flaw_category, stratum)
        if y == -1:
            use_primary = False
            break
        rb = rebuttal_map.get(f["finding_id"])
        adj_sev = rb["adjusted_severity"] if rb else f["severity"]

        cb_scores.append(brier(f["severity"] / 10.0, y))
        db_scores.append(brier(adj_sev / 10.0, y))

    if use_primary and cb_scores:
        return mean(cb_scores), mean(db_scores)

    # MIL fallback
    return _aggregate_mil(advancing, rebuttal_map, stratum)


def _aggregate_mil(
    advancing: list[dict],
    rebuttal_map: dict,
    stratum: str,
) -> tuple[float, float]:
    """Bag-level MIL fallback when per-finding ground truth unavailable."""
    if stratum == "defense":
        cb = mean([brier(f["severity"] / 10.0, 0) for f in advancing])
        db_vals = []
        for f in advancing:
            rb = rebuttal_map.get(f["finding_id"])
            adj = rb["adjusted_severity"] if rb else f["severity"]
            db_vals.append(brier(adj / 10.0, 0))
        return cb, mean(db_vals)

    if stratum == "regular":
        # critic: max pooling (reward finding ≥1 high-severity flaw)
        cb = max(brier(f["severity"] / 10.0, 1) for f in advancing)
        # defender: mean pooling (penalize over-reduction on any finding)
        db_vals = []
        for f in advancing:
            rb = rebuttal_map.get(f["finding_id"])
            adj = rb["adjusted_severity"] if rb else f["severity"]
            db_vals.append(brier(adj / 10.0, 1))
        return cb, mean(db_vals)

    return 0.0, 0.0


def combined_case_score(
    verdict: str,
    findings: list[dict],
    rebuttals: list[dict],
    case_flaw_category: str | None,
    stratum: str,
    w_v: float = 0.50,
    w_c: float = 0.25,
    w_d: float = 0.25,
) -> float:
    """Weighted combination of verdict score and finding-level Brier losses."""
    vs = VERDICT_SCORES[stratum][verdict]
    cb, db = aggregate_findings(findings, rebuttals, case_flaw_category, stratum)
    return w_v * vs + w_c * cb + w_d * db


# ---------------------------------------------------------------------------
# Verdict stability
# ---------------------------------------------------------------------------

def verdict_stability(run_verdicts: list[str]) -> float:
    """Per-case verdict stability: fraction of runs agreeing with the majority.

    3/3 agree → 1.00 | 2/3 agree → 0.67 | all differ → 0.33
    Used as a per-case stability weight on the combined case score.
    Cohen's Kappa (chance-corrected) is computed globally across all cases
    via compute_global_vs(), not per-case, because kappa requires n > 1.
    """
    if len(run_verdicts) < 2:
        return 1.0
    majority = max(set(run_verdicts), key=run_verdicts.count)
    return run_verdicts.count(majority) / len(run_verdicts)


def compute_global_vs(cases: list[dict]) -> float:
    """Global verdict stability via Cohen's Kappa averaged over run pairs.

    Compares run A verdicts vs run B verdicts across all cases — requires
    at least 2 labels to avoid divide-by-zero. Returns nan if insufficient
    cases or all runs agree perfectly.
    """
    n_runs = max((len(c["runs"]) for c in cases), default=0)
    if n_runs < 2:
        return float("nan")

    run_arrays: dict[int, list[int]] = defaultdict(list)
    for case in cases:
        for i, v in enumerate(case["runs"]):
            run_arrays[i].append(VERDICT_MAP[v])

    pairs = list(combinations(range(n_runs), 2))
    kappas = []
    for a, b in pairs:
        arr_a, arr_b = run_arrays[a], run_arrays[b]
        if len(set(arr_a)) < 2 and len(set(arr_b)) < 2:
            # All verdicts identical — perfect agreement, kappa undefined
            kappas.append(1.0)
            continue
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                k = cohen_kappa_score(arr_a, arr_b)
            kappas.append(k)
        except ValueError:
            kappas.append(1.0)

    return mean(kappas) if kappas else float("nan")


def soft_probs(run_verdicts: list[str]) -> list[float]:
    """[p_sound, p_ambig, p_flawed] from 3 run verdicts."""
    counts = Counter(run_verdicts)
    n = len(run_verdicts)
    return [counts["defense_wins"] / n, counts["empirical_test_agreed"] / n, counts["critique_wins"] / n]


# ---------------------------------------------------------------------------
# Secondary metrics
# ---------------------------------------------------------------------------

def compute_wdcr(cases: list[dict]) -> float:
    """Severity-weighted Defender Concession Rate on defense cases.

    wDCR = sum(original_severity × 1{CONCEDE}) / sum(original_severity)
    """
    numerator = denominator = 0.0
    for case in cases:
        if case["stratum"] != "defense":
            continue
        for run in case["runs_data"]:
            for rb in run.get("defender_output", {}).get("rebuttals", []):
                sev = rb.get("original_severity", 0)
                denominator += sev
                if rb.get("rebuttal_type") == "CONCEDE":
                    numerator += sev
    return numerator / denominator if denominator > 0 else 0.0


def compute_cer(cases: list[dict]) -> dict:
    """Critique Escalation Rate: fraction of non-NIT findings over all findings.

    Reported separately for defense and regular cases.
    """
    result = {}
    for stratum in ("defense", "regular"):
        total = non_nit = 0
        for case in cases:
            if case["stratum"] != stratum:
                continue
            for run in case["runs_data"]:
                for f in run.get("critic_output", {}).get("findings", []):
                    total += 1
                    if not f.get("suppressed", False):
                        non_nit += 1
        result[stratum] = non_nit / total if total > 0 else 0.0
    return result


def compute_adjudicator_override_rate(cases: list[dict]) -> float:
    """Fraction of defense-case runs where defender said defense_wins but
    adjudicator changed it to empirical_test_agreed or critique_wins.

    A non-zero AOR with flat DER after Intervention B confirms the adjudicator
    is the bottleneck — Intervention C is the next target.
    """
    total = overridden = 0
    for case in cases:
        if case["stratum"] != "defense":
            continue
        for run in case["runs_data"]:
            defender_verdict = run.get("defender_output", {}).get("overall_verdict")
            adjudicator_verdict = run.get("adjudicator_output", {}).get("case_verdict")
            if defender_verdict == "defense_wins":
                total += 1
                if adjudicator_verdict != "defense_wins":
                    overridden += 1
    return overridden / total if total > 0 else float("nan")


def compute_nit_suppression_rate(cases: list[dict]) -> float:
    """Fraction of findings classified NIT and suppressed over all findings."""
    total = suppressed = 0
    for case in cases:
        for run in case["runs_data"]:
            for f in run.get("critic_output", {}).get("findings", []):
                total += 1
                if f.get("suppressed", False):
                    suppressed += 1
    return suppressed / total if total > 0 else 0.0


def compute_fce(cases: list[dict]) -> float:
    """Finding Calibration Error: mean absolute deviation from diagonal.

    Uses severity/10 as the probability estimate and stratum (regular vs.
    defense) as the binary ground truth (1=regular, 0=defense).
    Mixed cases are excluded.
    """
    severities, labels = [], []
    for case in cases:
        if case["stratum"] == "mixed":
            continue
        y = 1 if case["stratum"] == "regular" else 0
        for run in case["runs_data"]:
            for f in run.get("critic_output", {}).get("findings", []):
                if not f.get("suppressed", False):
                    severities.append(f["severity"] / 10.0)
                    labels.append(y)

    if len(set(labels)) < 2 or not severities:
        return float("nan")

    fraction_pos, mean_pred = calibration_curve(
        labels, severities, n_bins=4, strategy="quantile"
    )
    return float(np.mean(np.abs(fraction_pos - mean_pred)))


# ---------------------------------------------------------------------------
# Main evaluate()
# ---------------------------------------------------------------------------

def _false_hedge_rate(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """FHR: proportion of clear cases (SOUND + FLAWED) predicted AMBIGUOUS."""
    clear_mask = (y_true == 0) | (y_true == 2)
    if not clear_mask.any():
        return 0.0
    return float(np.mean(y_pred[clear_mask] == 1))


def evaluate(cases: list[dict]) -> dict:
    """Compute all v8 evaluation metrics from aggregated case data.

    Each element of `cases` must have:
      case_id, stratum, flaw_category (or None), runs (list of verdict strings),
      runs_data (list of full per-run dicts for finding-level metrics)
    """
    y_true, y_pred, y_prob = [], [], []
    combined_scores_by_stratum = defaultdict(list)
    vs_scores = []

    critic_brier_by_stratum:   dict[str, list[float]] = defaultdict(list)
    defender_brier_by_stratum: dict[str, list[float]] = defaultdict(list)

    for case in cases:
        stratum = case["stratum"]
        run_verdicts = case["runs"]
        gt = LABEL_MAP[stratum]
        run_labels = [VERDICT_MAP[v] for v in run_verdicts]
        majority = max(set(run_labels), key=run_labels.count)

        y_true.append(gt)
        y_pred.append(majority)
        y_prob.append(soft_probs(run_verdicts))

        vs = verdict_stability(run_verdicts)
        vs_scores.append(vs)

        # Per-run: combined score + separate Brier components
        per_run_scores = []
        per_run_cb, per_run_db = [], []
        for run in case["runs_data"]:
            verdict = run["adjudicator_output"]["case_verdict"]
            findings = run.get("critic_output", {}).get("findings", [])
            rebuttals = run.get("defender_output", {}).get("rebuttals", [])
            cb, db = aggregate_findings(
                findings, rebuttals, case.get("flaw_category"), stratum
            )
            vs_score = VERDICT_SCORES[stratum][verdict]
            score = 0.50 * vs_score + 0.25 * cb + 0.25 * db
            per_run_scores.append(score)
            per_run_cb.append(cb)
            per_run_db.append(db)

        weighted_score = mean(per_run_scores) * vs
        combined_scores_by_stratum[stratum].append(weighted_score)

        # Case-mean Brier (not stability-weighted — raw signal per agent)
        if stratum != "mixed":
            critic_brier_by_stratum[stratum].append(mean(per_run_cb))
            defender_brier_by_stratum[stratum].append(mean(per_run_db))

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    y_prob = np.array(y_prob)

    report = classification_report(
        y_true, y_pred,
        labels=[0, 1, 2],
        target_names=["SOUND", "AMBIG", "FLAWED"],
        output_dict=True,
        zero_division=0,
    )

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2])

    # Avoid log_loss with missing classes
    present_classes = sorted(set(y_true))
    ll = log_loss(y_true, y_prob[:, present_classes], labels=present_classes) if len(present_classes) > 1 else float("nan")

    cer = compute_cer(cases)

    return {
        # Primary
        "mcc": float(matthews_corrcoef(y_true, y_pred)),

        # Verdict-level (all from classification report / confusion matrix)
        # DER = recall on SOUND: fraction of defense cases correctly exonerated
        # (METRICS.md: "count(defense_wins on defense cases) / total defense evaluations")
        # Note: EVALUATION.md erroneously maps this to precision — recall is correct.
        "DER":  float(report.get("SOUND", {}).get("recall", 0.0)),
        "IDR":  float(report.get("FLAWED", {}).get("recall", 0.0)),
        "FAR":  1.0 - float(report.get("SOUND", {}).get("recall", 0.0)),
        "FHR":  _false_hedge_rate(y_true, y_pred),
        "ARR":  float(report.get("AMBIG", {}).get("recall", 0.0)),

        # Stability — per-case majority fraction (mean), plus global kappa
        "VS_mean":   float(mean(vs_scores)) if vs_scores else float("nan"),
        "VS_kappa":  compute_global_vs(cases),

        # Combined weighted scores by stratum
        "weighted_score_defense": float(mean(combined_scores_by_stratum["defense"])) if combined_scores_by_stratum["defense"] else float("nan"),
        "weighted_score_regular": float(mean(combined_scores_by_stratum["regular"])) if combined_scores_by_stratum["regular"] else float("nan"),
        "weighted_score_mixed":   float(mean(combined_scores_by_stratum["mixed"]))   if combined_scores_by_stratum["mixed"]   else float("nan"),

        # Separate Brier losses per agent per stratum (raw, not stability-weighted)
        "critic_brier_defense":   float(mean(critic_brier_by_stratum["defense"]))   if critic_brier_by_stratum["defense"]   else float("nan"),
        "critic_brier_regular":   float(mean(critic_brier_by_stratum["regular"]))   if critic_brier_by_stratum["regular"]   else float("nan"),
        "defender_brier_defense": float(mean(defender_brier_by_stratum["defense"])) if defender_brier_by_stratum["defense"] else float("nan"),
        "defender_brier_regular": float(mean(defender_brier_by_stratum["regular"])) if defender_brier_by_stratum["regular"] else float("nan"),

        # Finding-level diagnostics
        "AOR":      compute_adjudicator_override_rate(cases),
        "wDCR":     compute_wdcr(cases),
        "CER_defense": cer.get("defense", float("nan")),
        "CER_regular": cer.get("regular", float("nan")),
        "NIT_suppression_rate": compute_nit_suppression_rate(cases),
        "FCE":      compute_fce(cases),

        # Log loss
        "log_loss": ll,

        # Raw structures for downstream use
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
        "n_cases": len(cases),
        "n_defense": int((y_true == 0).sum()),
        "n_mixed":   int((y_true == 1).sum()),
        "n_regular": int((y_true == 2).sum()),
    }


# ---------------------------------------------------------------------------
# McNemar's test (full benchmark comparison only)
# ---------------------------------------------------------------------------

def mcnemar_compare(
    cases_a: list[dict],
    cases_b: list[dict],
) -> dict:
    """McNemar's test comparing two prompt configurations on the same cases.

    Both lists must contain the same case_ids in the same order.
    Returns p-value and contingency table.
    """
    assert len(cases_a) == len(cases_b), "Case lists must be the same length"

    def is_correct(case: dict) -> bool:
        stratum = case["stratum"]
        majority_verdict = max(
            set(case["runs"]), key=case["runs"].count
        )
        correct_map = {
            "defense": "defense_wins",
            "regular": "critique_wins",
            "mixed":   "empirical_test_agreed",
        }
        return majority_verdict == correct_map[stratum]

    both_correct = a_only = b_only = both_wrong = 0
    for ca, cb in zip(cases_a, cases_b):
        a_ok, b_ok = is_correct(ca), is_correct(cb)
        if a_ok and b_ok:     both_correct += 1
        elif a_ok and not b_ok: a_only += 1
        elif b_ok and not a_ok: b_only += 1
        else:                 both_wrong += 1

    table = [[both_correct, a_only], [b_only, both_wrong]]
    result = mcnemar(table, exact=False)

    return {
        "p_value": float(result.pvalue),
        "statistic": float(result.statistic),
        "contingency": table,
        "b_vs_c": {"b": a_only, "c": b_only},
    }


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_runs(results_dir: Path) -> list[dict]:
    """Load all JSON run files from a directory."""
    runs = []
    for path in sorted(results_dir.glob("*.json")):
        with open(path) as f:
            runs.append(json.load(f))
    return runs


def group_by_case(runs: list[dict]) -> list[dict]:
    """Group individual run dicts into case-level dicts with 3 runs each."""
    by_case: dict[str, list[dict]] = defaultdict(list)
    for run in runs:
        by_case[run["case_id"]].append(run)

    cases = []
    for case_id, case_runs in by_case.items():
        case_runs.sort(key=lambda r: r.get("run_id", 0))
        first = case_runs[0]
        verdicts = [r["adjudicator_output"]["case_verdict"] for r in case_runs]
        cases.append({
            "case_id": case_id,
            "stratum": first["stratum"],
            "flaw_category": first.get("flaw_category"),
            "runs": verdicts,
            "runs_data": case_runs,
        })

    return cases


def print_report(metrics: dict, label: str = "") -> None:
    header = f"  v8 Scoring Report{' — ' + label if label else ''}  "
    print("=" * (len(header) + 4))
    print(f"  {header}")
    print("=" * (len(header) + 4))
    print(f"\n  Cases: {metrics['n_cases']}  (defense={metrics['n_defense']}, mixed={metrics['n_mixed']}, regular={metrics['n_regular']})\n")

    print("  ── Primary ─────────────────────────────────")
    print(f"  MCC                     {metrics['mcc']:+.4f}   (target: > baseline + 0.06 MMD)")
    print()
    print("  ── Verdict-Level ───────────────────────────")
    print(f"  DER  (recall SOUND)     {metrics['DER']:.4f}   (target: > 0.30)")
    print(f"  IDR  (recall FLAWED)    {metrics['IDR']:.4f}   (floor:  ≥ 0.75)")
    print(f"  FAR  (FPR SOUND)        {metrics['FAR']:.4f}")
    print(f"  FHR  (false hedge)      {metrics['FHR']:.4f}   (floor:  ≤ 0.05 increase)")
    print(f"  ARR  (recall AMBIG)     {metrics['ARR']:.4f}   (floor:  ≥ 0.60)")
    print()
    print("  ── Stability & Combined ────────────────────")
    vs_kappa = metrics.get('VS_kappa', float('nan'))
    print(f"  VS   (majority frac)    {metrics['VS_mean']:.4f}   kappa={vs_kappa:.4f}")
    print(f"  Weighted score defense  {metrics['weighted_score_defense']:+.4f}")
    print(f"  Weighted score regular  {metrics['weighted_score_regular']:+.4f}")
    print(f"  Weighted score mixed    {metrics['weighted_score_mixed']:+.4f}")
    print()
    print("  ── Brier Losses (raw, per agent) ───────────")
    print(f"  {'':25s}  defense        regular")
    cbd  = metrics.get('critic_brier_defense',   float('nan'))
    cbr  = metrics.get('critic_brier_regular',   float('nan'))
    dbd  = metrics.get('defender_brier_defense', float('nan'))
    dbr  = metrics.get('defender_brier_regular', float('nan'))
    print(f"  Critic   brier          {cbd:+.4f}         {cbr:+.4f}")
    print(f"  Defender brier          {dbd:+.4f}         {dbr:+.4f}")
    print(f"  (defense: negative = false alarms cost; regular: positive = correct flaws found)")
    print()
    print("  ── Finding-Level Diagnostics ───────────────")
    aor = metrics.get('AOR', float('nan'))
    aor_str = f"{aor:.4f}" if aor == aor else "  n/a "
    print(f"  AOR  (adjudicator override) {aor_str}   (defender said defense_wins; adj changed it)")
    print(f"  wDCR (sev-wtd concede)  {metrics['wDCR']:.4f}   (healthy: 0.30–0.50 defense)")
    print(f"  CER  defense            {metrics['CER_defense']:.4f}   (non-NIT findings / all)")
    print(f"  CER  regular            {metrics['CER_regular']:.4f}")
    print(f"  NIT suppression rate    {metrics['NIT_suppression_rate']:.4f}")
    print(f"  FCE  (calibration err)  {metrics['FCE']:.4f}   (target: < 0.15)")
    print()
    print("  ── Confusion Matrix ────────────────────────")
    print("          pred SOUND  pred AMBIG  pred FLAWED")
    labels = ["true SOUND ", "true AMBIG ", "true FLAWED"]
    for row_label, row in zip(labels, metrics["confusion_matrix"]):
        print(f"  {row_label}  {row[0]:>8d}   {row[1]:>9d}   {row[2]:>10d}")
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="v8 scoring pipeline")
    parser.add_argument("--results-dir", required=True, type=Path,
                        help="Directory containing per-run JSON files")
    parser.add_argument("--output", type=Path, default=None,
                        help="Save metrics JSON to this path")
    parser.add_argument("--label", default="",
                        help="Label for this run (e.g. 'defender-v2')")
    parser.add_argument("--compare", type=Path, default=None,
                        help="Results dir for baseline config — runs McNemar comparison")
    args = parser.parse_args()

    if not args.results_dir.exists():
        print(f"ERROR: results dir not found: {args.results_dir}", file=sys.stderr)
        sys.exit(1)

    runs = load_runs(args.results_dir)
    if not runs:
        print(f"ERROR: no JSON files found in {args.results_dir}", file=sys.stderr)
        sys.exit(1)

    cases = group_by_case(runs)
    metrics = evaluate(cases)
    print_report(metrics, label=args.label)

    if args.compare:
        baseline_runs = load_runs(args.compare)
        baseline_cases = group_by_case(baseline_runs)
        result = mcnemar_compare(baseline_cases, cases)
        print("  ── McNemar's Test (vs baseline) ────────────")
        print(f"  p-value:    {result['p_value']:.4f}")
        print(f"  statistic:  {result['statistic']:.4f}")
        print(f"  b (baseline only correct): {result['b_vs_c']['b']}")
        print(f"  c (candidate only correct): {result['b_vs_c']['c']}")
        print()

    if args.output:
        with open(args.output, "w") as f:
            json.dump({k: v for k, v in metrics.items() if k != "classification_report"}, f, indent=2)
        print(f"  Saved metrics → {args.output}")


if __name__ == "__main__":
    main()
