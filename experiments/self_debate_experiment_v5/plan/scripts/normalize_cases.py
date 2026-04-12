# normalize_cases.py
# /// script
# requires-python = ">=3.10"
# ///
"""
Transform ARCH-1 pipeline output schema → experiment schema.

The ARCH-1 pipeline (two-node design + corruption pipeline) produces a flat schema
that differs from what validate_cases.py, filter_verified_cases.py, and self_debate_poc.py
expect. This script normalizes those differences without modifying either the pipeline
output or the experiment scripts.

Key mappings:
  correct_verdict       → category (unchanged) + ground_truth.correct_position
  _pipeline.proxy_mean  → difficulty label (easy/medium/hard)
  must_find_issue_ids   → scoring_targets.must_find_issue_ids (unchanged)
  must_not_claim (dicts)→ scoring_targets.must_not_claim (synthetic IDs: mnc_001..N)
                          + scoring_targets.must_not_claim_details (full dicts w/ IDs)
  acceptable_resolutions→ scoring_targets.acceptable_resolutions (verdict-type strings)
                          + scoring_targets.resolution_descriptions (original dicts, kept)
  difficulty_justification → notes
  acceptable_resolutions[0] → ideal_debate_resolution (type + ETD fields)

Usage (from experiment root, e.g. self_debate_experiment_v5/):
    uv run plan/scripts/normalize_cases.py \\
        --input synthetic-candidates/selected_cases_all.json \\
        --output benchmark_cases.json

Defaults: --input synthetic-candidates/selected_cases_all.json
          --output benchmark_cases.json
"""

import argparse
import json
from pathlib import Path

# ---------------------------------------------------------------------------
# Difficulty derivation
# ---------------------------------------------------------------------------
# proxy_mean is the pipeline's single-pass Sonnet score (mean of IDR, IDP, FVC).
# Lower = harder (Sonnet struggles → debate protocol has more value to add).
# These thresholds align with validate_cases.py difficulty criteria:
#   easy:   proxy >= 0.85  (Sonnet mostly correct; baseline mean >= 0.85)
#   medium: 0.55 <= proxy < 0.85
#   hard:   proxy < 0.55   (Sonnet fails on multiple dimensions)
# Note: defense_wins cases have proxy_mean ≈ 0.0 (Sonnet invents flaws) → "hard".
EASY_THRESHOLD = 0.85
MEDIUM_THRESHOLD = 0.55


def derive_difficulty(proxy_mean: float | None) -> str:
    if proxy_mean is None:
        return "medium"  # unknown → conservative middle label
    if proxy_mean >= EASY_THRESHOLD:
        return "easy"
    if proxy_mean >= MEDIUM_THRESHOLD:
        return "medium"
    return "hard"


# ---------------------------------------------------------------------------
# Core normalizer
# ---------------------------------------------------------------------------

def normalize_case(case: dict) -> dict:
    correct_verdict = case["correct_verdict"]  # "critique" | "defense_wins"
    pipeline_meta = case.get("_pipeline", {})
    proxy_mean = pipeline_meta.get("proxy_mean")

    # ---- ground_truth -------------------------------------------------------
    # correct_position uses 'defense' not 'defense_wins' (matches scorer branch:
    # `if correct_position == 'defense'`)
    correct_position = "defense" if correct_verdict == "defense_wins" else correct_verdict
    final_verdict = (
        "Defense wins — design is sound"
        if correct_verdict == "defense_wins"
        else "Critique wins — design has methodological flaw(s)"
    )
    ground_truth = {
        "correct_position": correct_position,
        "final_verdict": final_verdict,
        "required_empirical_test": None,
    }

    # ---- ideal_debate_resolution --------------------------------------------
    # type strings match the scorer's RESOLUTION_EQUIVALENT_PAIRS vocabulary:
    # "critique_wins" | "defense_wins" | "empirical_test_agreed"
    idr_type = "critique_wins" if correct_verdict == "critique" else "defense_wins"
    ar_list = case.get("acceptable_resolutions", [])
    first_ar = ar_list[0] if ar_list else {}
    ideal_debate_resolution = {
        "type": idr_type,
        # ETD fields from the first resolution description; may be None for defense_wins
        "supports_critique_if": first_ar.get("supports_critique_if"),
        "supports_defense_if": first_ar.get("supports_defense_if"),
        "ambiguous_if": None,
    }

    # ---- scoring_targets ----------------------------------------------------
    # must_not_claim: pipeline provides narrative dicts; scorer needs ID strings
    # for set-membership testing (`if i in must_not_claim`).
    # Assign synthetic IDs mnc_001..N so IDP scoring can function.
    # Agents must reference these IDs when raising must_not_claim concerns.
    raw_mnc = case.get("must_not_claim", [])
    if isinstance(raw_mnc, list) and raw_mnc and isinstance(raw_mnc[0], dict):
        mnc_ids = [f"mnc_{i + 1:03d}" for i in range(len(raw_mnc))]
        mnc_details = [
            {
                "id": mnc_ids[i],
                "claim": item.get("claim", ""),
                "why_wrong": item.get("why_wrong", ""),
            }
            for i, item in enumerate(raw_mnc)
        ]
    elif isinstance(raw_mnc, list) and raw_mnc and isinstance(raw_mnc[0], str):
        # Already ID strings (old schema) — pass through
        mnc_ids = raw_mnc
        mnc_details = [{"id": m, "claim": m, "why_wrong": ""} for m in raw_mnc]
    else:
        mnc_ids = []
        mnc_details = []

    # acceptable_resolutions: scorer expects verdict-type strings, not dicts.
    # Pipeline "acceptable_resolutions" are descriptive dicts → preserve as
    # resolution_descriptions; generate verdict-type list for the scorer.
    acceptable_verdicts = [idr_type]  # critique_wins or defense_wins

    scoring_targets = {
        "must_find_issue_ids": case.get("must_find_issue_ids", []),
        "must_not_claim": mnc_ids,
        "must_not_claim_details": mnc_details,
        "acceptable_resolutions": acceptable_verdicts,
        "resolution_descriptions": ar_list,  # full pipeline data, for agent context
    }

    # ---- assemble normalized case ------------------------------------------
    normalized = {
        # --- Identity & provenance ---
        "case_id": case["case_id"],
        "hypothesis": case.get("hypothesis", ""),
        "domain": case.get("domain", ""),
        "ml_task_type": case.get("ml_task_type", ""),
        # --- Required by experiment scripts ---
        "category": correct_verdict,           # "critique" | "defense_wins"
        "difficulty": derive_difficulty(proxy_mean),
        "task_prompt": case["task_prompt"],
        "ground_truth": ground_truth,
        "planted_issues": case.get("planted_issues", []),
        "ideal_debate_resolution": ideal_debate_resolution,
        "scoring_targets": scoring_targets,
        "verifier_status": case.get("verifier_status", "pending"),
        "notes": case.get("difficulty_justification", ""),
        # --- Not generated by ARCH-1 pipeline; set to empty ---
        "ideal_critique": [],
        "ideal_defense": [],
        # --- Supplementary pipeline fields (preserved for context) ---
        "num_corruptions": (
            pipeline_meta.get("num_corruptions")
            or case.get("num_corruptions")
        ),
        "sound_design_reference": case.get("sound_design_reference", ""),
        "_pipeline": pipeline_meta,
        # Explicitly mark as synthetic so validate_cases.py source_paper check is skipped
        "is_real_paper_case": False,
    }

    return normalized


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        default="synthetic-candidates/selected_cases_all.json",
        help="Path to pipeline output JSON (default: synthetic-candidates/selected_cases_all.json)",
    )
    parser.add_argument(
        "--output",
        default="benchmark_cases.json",
        help="Output path for normalized cases (default: benchmark_cases.json)",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    with input_path.open() as f:
        cases = json.load(f)

    print(f"Normalizing {len(cases)} cases from {input_path} ...")
    normalized = [normalize_case(c) for c in cases]

    # Summary statistics
    from collections import Counter
    cats = Counter(n["category"] for n in normalized)
    diffs = Counter(n["difficulty"] for n in normalized)
    mixed_count = sum(1 for n in normalized if n["ground_truth"]["correct_position"] == "mixed")
    print(f"  category:   {dict(cats)}")
    print(f"  difficulty: {dict(diffs)}")
    print(f"  mixed:      {mixed_count} (ARCH-1 has no mixed cases by design)")

    with output_path.open("w") as f:
        json.dump(normalized, f, indent=2)

    print(f"Written → {output_path} ({len(normalized)} cases)")
    print()
    print("Next: uv run plan/scripts/validate_cases.py benchmark_cases.json")


if __name__ == "__main__":
    main()
