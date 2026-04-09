# /// script
# requires-python = ">=3.10"
# dependencies = ["openai>=1.0", "rich>=13.0"]
# ///
"""
Temporary unit tests for smoke scoring logic.

Run with:
    uv run pipeline/test_scoring.py

Tests compute_smoke_scores() and recycle_action() without any LLM calls.

IDP semantics:
  must_not_claim present       → partial credit fraction: 1 - n_raised/len(must_not_claim)
  must_not_claim empty + 0 corruptions
                               → binary: 0.0 if Sonnet raised any issue, else 1.0
  must_not_claim empty + N>0 corruptions
                               → None (can't penalize without the protected-choice list)
IDR semantics:
  fraction of must_find_ids found; None if no must_find_ids
FVC semantics:
  1.0 if verdict correct, 0.0 otherwise; "approve" normalised to "defense_wins"
proxy_mean:
  mean of whichever of IDR/IDP/FVC are not None
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from orchestrator import compute_smoke_scores, recycle_action

# ---------------------------------------------------------------------------
# Minimal test harness
# ---------------------------------------------------------------------------

_passed = 0
_failed = 0


def check(label: str, actual, expected) -> None:
    global _passed, _failed
    if actual == expected:
        print(f"  PASS  {label}")
        _passed += 1
    else:
        print(f"  FAIL  {label}")
        print(f"        expected: {expected!r}")
        print(f"        actual:   {actual!r}")
        _failed += 1


def section(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def mnc_items(n: int) -> list:
    return [{"claim": f"claim_{i}", "why_wrong": "legitimate choice"} for i in range(n)]


def defense_wins_case(mnc_count: int = 3, task_prompt: str = "A valid design.") -> dict:
    return {
        "correct_verdict": "defense_wins",
        "must_find_issue_ids": [],
        "must_not_claim": mnc_items(mnc_count),
        "_pipeline": {"num_corruptions": 0},
        "task_prompt": task_prompt,
    }


def critique_case(
    num_corruptions: int = 1,
    must_find_ids: list | None = None,
    mnc_count: int = 0,
    task_prompt: str = "A flawed design.",
) -> dict:
    if must_find_ids is None:
        must_find_ids = [f"issue_{i:03d}" for i in range(1, num_corruptions + 1)]
    return {
        "correct_verdict": "critique",
        "must_find_issue_ids": must_find_ids,
        "must_not_claim": mnc_items(mnc_count),
        "_pipeline": {"num_corruptions": num_corruptions},
        "task_prompt": task_prompt,
    }


def smoke_out(verdict: str = "approve", issues: list | None = None) -> dict:
    """Raw Sonnet blind-eval output."""
    return {"verdict": verdict, "issues_found": issues or [], "reasoning": "..."}


def scorer_out(
    verdict: str = "approve",
    found: list | None = None,
    raised_bad: list | None = None,
) -> dict:
    """Scorer LLM output."""
    return {
        "verdict_given": verdict,
        "must_find_found": found or [],
        "must_not_claim_raised": raised_bad or [],
    }


# ---------------------------------------------------------------------------
# FVC normalization
# ---------------------------------------------------------------------------

section("FVC normalization — approve vs defense_wins")

scores = compute_smoke_scores(smoke_out("approve"), scorer_out("approve"), defense_wins_case(), "Valid design.")
check("approve + defense_wins → FVC=1.0", scores["FVC"], 1.0)

scores = compute_smoke_scores(smoke_out("critique"), scorer_out("critique", found=["issue_001"]), critique_case(1), "Flawed design.")
check("critique + critique correct_verdict → FVC=1.0", scores["FVC"], 1.0)

scores = compute_smoke_scores(smoke_out("approve"), scorer_out("approve"), critique_case(1), "Flawed design.")
check("approve + critique correct_verdict → FVC=0.0", scores["FVC"], 0.0)

scores = compute_smoke_scores(smoke_out("unclear"), scorer_out("unclear"), defense_wins_case(), "Valid design.")
check("unclear verdict → FVC=0.0", scores["FVC"], 0.0)

# ---------------------------------------------------------------------------
# IDR — partial credit
# ---------------------------------------------------------------------------

section("IDR — partial credit (fraction of must_find_ids found)")

scores = compute_smoke_scores(smoke_out("approve"), scorer_out("approve"), defense_wins_case(), "Valid design.")
check("0-corruption case → IDR=None", scores["IDR"], None)

scores = compute_smoke_scores(smoke_out(), scorer_out("critique", found=["issue_001", "issue_002"]), critique_case(2), "Flawed design.")
check("2/2 found → IDR=1.0", scores["IDR"], 1.0)

scores = compute_smoke_scores(smoke_out(), scorer_out("critique", found=["issue_001"]), critique_case(2), "Flawed design.")
check("1/2 found → IDR=0.5", scores["IDR"], 0.5)

scores = compute_smoke_scores(smoke_out(), scorer_out("critique", found=["issue_001", "issue_003"]), critique_case(5), "Flawed design.")
check("2/5 found → IDR=0.4", scores["IDR"], 0.4)

scores = compute_smoke_scores(smoke_out(), scorer_out("critique"), critique_case(1), "Flawed design.")
check("0/1 found → IDR=0.0", scores["IDR"], 0.0)

scores = compute_smoke_scores(smoke_out(), scorer_out("critique", found=["issue_999"]), critique_case(1, must_find_ids=["issue_001"]), "Flawed design.")
check("only non-required ID found → IDR=0.0", scores["IDR"], 0.0)

scores = compute_smoke_scores(smoke_out(), scorer_out("critique", found=["issue_001"]), critique_case(1), "Flawed design.")
check("1/1 found → IDR=1.0", scores["IDR"], 1.0)

# ---------------------------------------------------------------------------
# IDP — partial credit via must_not_claim
# ---------------------------------------------------------------------------

section("IDP — partial credit via must_not_claim")

scores = compute_smoke_scores(smoke_out("approve"), scorer_out("approve"), defense_wins_case(mnc_count=3), "Valid design.")
check("0/3 raised → IDP=1.0", scores["IDP"], 1.0)

scores = compute_smoke_scores(smoke_out("critique", issues=["x"]), scorer_out("critique", raised_bad=["claim_0"]), defense_wins_case(mnc_count=3), "Valid design.")
check("1/3 raised → IDP=0.6667", scores["IDP"], round(2/3, 4))

scores = compute_smoke_scores(smoke_out("critique", issues=["x","y"]), scorer_out("critique", raised_bad=["claim_0", "claim_1"]), defense_wins_case(mnc_count=3), "Valid design.")
check("2/3 raised → IDP=0.3333", scores["IDP"], round(1/3, 4))

scores = compute_smoke_scores(smoke_out("critique", issues=["x","y","z"]), scorer_out("critique", raised_bad=["claim_0", "claim_1", "claim_2"]), defense_wins_case(mnc_count=3), "Valid design.")
check("3/3 raised → IDP=0.0", scores["IDP"], 0.0)

scores = compute_smoke_scores(smoke_out("critique", issues=["x"]), scorer_out("critique", raised_bad=["claim_0"]), defense_wins_case(mnc_count=5), "Valid design.")
check("1/5 raised → IDP=0.8", scores["IDP"], 0.8)

scores = compute_smoke_scores(smoke_out("critique", issues=["x"]*4), scorer_out(raised_bad=["x", "x", "x", "x"]), defense_wins_case(mnc_count=2), "Valid design.")
check("raised_bad > must_not_claim → IDP clamped to 0.0", scores["IDP"], 0.0)

# ---------------------------------------------------------------------------
# IDP — defense_wins with no must_not_claim (OPEN-18 fix)
# ---------------------------------------------------------------------------

section("IDP — defense_wins, no must_not_claim: binary on n_issues_raised")

# 0-corruption, no must_not_claim, Sonnet raises nothing → IDP=1.0
scores = compute_smoke_scores(
    smoke_out("approve", issues=[]),
    scorer_out("approve"),
    defense_wins_case(mnc_count=0),
    "Valid design.",
)
check("0 corruptions, no MNC, 0 issues raised → IDP=1.0", scores["IDP"], 1.0)

# 0-corruption, no must_not_claim, Sonnet invents 4 novel issues → IDP=0.0
scores = compute_smoke_scores(
    smoke_out("critique", issues=["invented_1", "invented_2", "invented_3", "invented_4"]),
    scorer_out("critique", raised_bad=[]),  # none matched must_not_claim (empty)
    defense_wins_case(mnc_count=0),
    "Valid design.",
)
check("0 corruptions, no MNC, 4 invented issues raised → IDP=0.0", scores["IDP"], 0.0)

# 0-corruption, no must_not_claim, Sonnet invents 1 novel issue → IDP=0.0
scores = compute_smoke_scores(
    smoke_out("critique", issues=["invented_1"]),
    scorer_out("critique", raised_bad=[]),
    defense_wins_case(mnc_count=0),
    "Valid design.",
)
check("0 corruptions, no MNC, 1 invented issue raised → IDP=0.0", scores["IDP"], 0.0)

# critique case, no must_not_claim → IDP=None (can't penalize)
scores = compute_smoke_scores(
    smoke_out("critique", issues=["invented_1", "invented_2"]),
    scorer_out("critique", raised_bad=[]),
    critique_case(1, mnc_count=0),
    "Flawed design.",
)
check("N>0 corruptions, no MNC, issues raised → IDP=None", scores["IDP"], None)

# ---------------------------------------------------------------------------
# proxy_mean — None exclusion
# ---------------------------------------------------------------------------

section("proxy_mean — applicable metrics only (None excluded)")

# defense_wins, perfect, MNC present: IDR=None, IDP=1.0, FVC=1.0 → proxy=1.0
scores = compute_smoke_scores(smoke_out("approve"), scorer_out("approve"), defense_wins_case(mnc_count=2), "Valid design.")
check("defense_wins perfect → proxy=1.0", scores["proxy_mean"], 1.0)
check("defense_wins perfect → IDR=None excluded", scores["IDR"], None)

# defense_wins, no MNC, Sonnet raises 4 invented issues, wrong verdict:
# IDR=None, IDP=0.0, FVC=0.0 → proxy=0.0
scores = compute_smoke_scores(
    smoke_out("critique", issues=["i1","i2","i3","i4"]),
    scorer_out("critique", raised_bad=[]),
    defense_wins_case(mnc_count=0),
    "Valid design.",
)
check("defense_wins, no MNC, 4 invented issues, wrong verdict → proxy=0.0", scores["proxy_mean"], 0.0)

# defense_wins, no MNC, Sonnet raises 0 issues, correct verdict:
# IDR=None, IDP=1.0, FVC=1.0 → proxy=1.0
scores = compute_smoke_scores(
    smoke_out("approve", issues=[]),
    scorer_out("approve"),
    defense_wins_case(mnc_count=0),
    "Valid design.",
)
check("defense_wins, no MNC, 0 issues raised, correct verdict → proxy=1.0", scores["proxy_mean"], 1.0)

# critique, 2/5 found, no MNC, correct verdict: IDR=0.4, IDP=None, FVC=1.0 → proxy=0.7
scores = compute_smoke_scores(
    smoke_out("critique", issues=["i1","i2"]),
    scorer_out("critique", found=["issue_001", "issue_002"]),
    critique_case(5, mnc_count=0),
    "Flawed design.",
)
check("2/5 found, no MNC, correct verdict → proxy=(0.4+1.0)/2=0.7", scores["proxy_mean"], 0.7)

# critique, 1/2 found, 1/2 MNC raised, correct verdict: IDR=0.5, IDP=0.5, FVC=1.0 → proxy=0.6667
scores = compute_smoke_scores(
    smoke_out("critique", issues=["i1","claim_0"]),
    scorer_out("critique", found=["issue_001"], raised_bad=["claim_0"]),
    critique_case(2, mnc_count=2),
    "Flawed design.",
)
check("1/2 IDR, 1/2 IDP, correct verdict → proxy=0.6667", scores["proxy_mean"], round((0.5+0.5+1.0)/3, 4))

# ---------------------------------------------------------------------------
# gate_pass — structural gate
# ---------------------------------------------------------------------------

section("gate_pass — permissive structural gate")

scores = compute_smoke_scores(smoke_out("critique"), scorer_out("critique", raised_bad=["claim_0","claim_1","claim_2"]), defense_wins_case(mnc_count=3), "Valid design.")
check("defense_wins, all MNC raised → gate=True (debate candidate)", scores["gate_pass"], True)

scores = compute_smoke_scores(smoke_out("approve"), scorer_out("approve"), critique_case(1), "Flawed design.")
check("critique, Sonnet wrong verdict → gate=True", scores["gate_pass"], True)

scores = compute_smoke_scores(smoke_out(), scorer_out(), critique_case(1), "")
check("empty task_prompt → gate=False", scores["gate_pass"], False)

scores = compute_smoke_scores(smoke_out(), scorer_out(), critique_case(1, must_find_ids=[]), "Flawed design.")
check("corruptions=1, no must_find_ids → gate=False", scores["gate_pass"], False)

scores = compute_smoke_scores(smoke_out("approve"), scorer_out("approve"), defense_wins_case(), "Valid design.")
check("num_corruptions=0, no must_find_ids → gate=True", scores["gate_pass"], True)

# ---------------------------------------------------------------------------
# recycle_action
# ---------------------------------------------------------------------------

section("recycle_action — routing logic")

stage, reason, _ = recycle_action({"gate_pass": True}, num_corruptions=1)
check("gate_pass=True → accepted", stage, None)

stage, reason, _ = recycle_action({"gate_pass": False}, num_corruptions=1)
check("gate_pass=False → stage='stage4'", stage, "stage4")
check("gate_pass=False → structural_failure", reason, "structural_failure")

stage, reason, _ = recycle_action(None, num_corruptions=1)
check("smoke=None → accepted", stage, None)

stage, reason, _ = recycle_action({}, num_corruptions=0)
check("gate_pass missing → accepted (defaults True)", stage, None)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print(f"\n{'='*40}")
print(f"  {_passed} passed, {_failed} failed")
print(f"{'='*40}")
sys.exit(0 if _failed == 0 else 1)
