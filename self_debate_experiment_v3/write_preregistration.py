# write_preregistration.py
# /// script
# requires-python = ">=3.10"
# ///
import json
from datetime import datetime

preregistration = {
    "date": datetime.now().isoformat(),
    "experiment": "self_debate_experiment_v3",
    "model": "claude-sonnet-4-6",
    "hypotheses": {
        "primary": {"claim": "Debate benchmark mean >= 0.65", "threshold": 0.65},
        "primary_passrate": {"claim": "Debate case pass rate >= 75%", "threshold": 0.75},
        "primary_lift": {"claim": "Debate corrected lift over baseline >= +0.10", "threshold": 0.10},
        "secondary_ensemble_mixed": {
            "claim": "Debate outperforms ETD-constrained ensemble on mixed-position cases",
            "criterion": "Debate mean on mixed cases > ensemble mean on same cases"
        },
        "secondary_defense_wins": {
            "claim": "Compute budget partially explains defense_wins advantage",
            "criterion": "Ensemble DC >= 0.5 on >= 60% of defense_wins cases -> compute partially explains"
        },
        "secondary_multiround_debate": {
            "claim": "Multi-round adversarial exchange outperforms single-pass isolated debate on DRQ (DC is structurally identical to FVC in this scorer — see dc_note)",
            "criterion": "multiround_mean(DRQ) > isolated_debate_mean(DRQ) across non-defense_wins cases; DC reported for completeness but not independently informative"
        }
    },
    "rubric": {
        "IDR": "issues_found / total_must_find_issue_ids (fractional 0.0-1.0); N/A on defense_wins",
        "IDP": "fraction of valid raised issues; must_not_claim items count as false positives (0.0/0.5/1.0); N/A on defense_wins",
        "DC": "correct verdict via defense function (0.0/0.5/1.0); baseline hardcoded 0.0",
        "DRQ": "typed verdict matches ideal (1.0); matches other acceptable_resolution (0.5); adjacent to ideal but not in list (0.5); wrong (0.0); baseline capped at 0.5",
        "ETD": "empirical test has measure + success_criterion + failure_criterion (0.0/0.5/1.0); N/A when ideal is critique_wins or defense_wins",
        "FVC": "verdict in acceptable_resolutions list (1.0); adjacent to ideal not in list (0.5); wrong (0.0)"
    },
    "dc_note": "DC in this experiment measures verdict-match, not defense agent behavior quality (v1's rich concession/contestation metric). The single-pass isolation design makes concession/contestation scoring inapplicable — the Defender never sees the Critique to concede or contest. In isolated_debate and ensemble conditions, DC is structurally identical to FVC for non-baseline. In multiround condition, DC reflects the final verdict after adversarial exchange.",
    "convergence_metric": {
        "definition": "1.0 if critic_verdict == defender_verdict; 0.5 if they diverge",
        "source_fields": "critic_raw verdict vs defender_raw verdict extracted from v3_raw_outputs/",
        "note": "Diagnostic only — not used in pass/fail determination. Reported in CONCLUSIONS.md for isolated_debate condition."
    },
    "structural_overrides": {
        "baseline_DC": 0.0,
        "baseline_DC_rationale": "Baseline has no defense role. Structural, not a reasoning penalty.",
        "baseline_DRQ_cap": 0.5,
        "baseline_DRQ_cap_rationale": "Baseline cannot produce typed resolution from structured exchange.",
        "honest_lift": "Corrected lift uses DC=0.5 and DRQ uncapped for baseline. Report both raw and corrected."
    },
    "failure_attribution_values": {
        "agent": "Traceable to specific agent output (Critic missed issue; Defender reasoning/label disconnect)",
        "protocol": "In debate structure (correct resolution not reached despite agents performing roles)",
        "ambiguous": "Cannot distinguish agent vs protocol from outputs alone",
        "none": "Case passed — no failure to attribute"
    },
    "per_case_pass_criterion": "mean(non-null dimensions) >= 0.65 AND all applicable dimensions >= 0.5",
    "n_runs_per_case": 3
}

with open('PREREGISTRATION.json', 'w') as f:
    json.dump(preregistration, f, indent=2)

rubric = {
    "scoring_dimensions": {
        "IDR": "Fraction of scoring_targets.must_find_issue_ids correctly identified (fractional). N/A on defense_wins.",
        "IDP": "Fraction of claimed issues that are valid; must_not_claim items are explicit false positives (0.0/0.5/1.0). N/A on defense_wins.",
        "DC": "Whether defense correctly reached verdict type (0.0/0.5/1.0). Baseline hardcoded 0.0.",
        "DRQ": "Whether typed verdict matches expected resolution (0.0/0.5/1.0). Baseline capped 0.5.",
        "ETD": "Empirical test has pre-specified measure, success criterion, failure criterion (0.0/0.5/1.0). N/A when ideal is critique_wins or defense_wins.",
        "FVC": "Verdict in scoring_targets.acceptable_resolutions (1.0); adjacent to ideal (0.5); wrong (0.0)."
    },
    "pass_fail_rule": "mean(non-null dimensions) >= 0.65 AND all applicable dimensions >= 0.5",
    "notes": "Rubric fixed before any agent run. Do not modify after execution begins."
}

with open('evaluation_rubric.json', 'w') as f:
    json.dump(rubric, f, indent=2)

print("Pre-registration and rubric written and locked.")
