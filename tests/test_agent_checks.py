"""
Tests for the draft verifier. Run with:  py tests/test_agent_checks.py

These check the plain-code guardrails around the AI, not the AI itself.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent"))
from draft_exceptions import verify  # noqa: E402

SOURCES = {"S1": "rule", "S2": "hr", "S3": "accounts", "S4": "okta removed 74.5 hours after"}
ALLOWED = {24.0, 74.5}

GOOD = {
    "summary": "Okta access was removed 74.5 hours after termination [S4].",
    "criteria": "Access must be removed within 24 hours [S1].",
    "condition": "Removal took 74.5 hours [S4].",
    "cause": "Not determined from the evidence provided. Requested from the control owner.",
    "effect": "Access could have remained usable after termination.",
    "not_known": ["Was the account used after termination?"],
    "email_subject": "Control 7 exception",
    "email_body": "Please explain the delay of 74.5 hours [S4].",
}


def with_change(**changes):
    draft = dict(GOOD)
    draft.update(changes)
    return draft


def test_clean_draft_has_no_warnings():
    assert verify(GOOD, SOURCES, ALLOWED) == []


def test_wrong_number_is_flagged():
    warnings = verify(with_change(condition="Removal took 80 hours [S4]."), SOURCES, ALLOWED)
    assert any("80 hours" in w for w in warnings)


def test_invented_citation_is_flagged():
    warnings = verify(with_change(condition="Removal took 74.5 hours [S9]."), SOURCES, ALLOWED)
    assert any("S9" in w for w in warnings)


def test_missing_citations_are_flagged():
    warnings = verify(with_change(summary="Slow.", criteria="Rule.", condition="Late.",
                                  email_body="Please explain."), SOURCES, ALLOWED)
    assert any("no citations" in w for w in warnings)


def test_invented_cause_is_flagged():
    warnings = verify(with_change(cause="The IT queue was misrouted."), SOURCES, ALLOWED)
    assert any("cause" in w.lower() for w in warnings)


def test_unsupported_claim_is_flagged():
    warnings = verify(with_change(effect="The account was compromised."), SOURCES, ALLOWED)
    assert any("compromised" in w for w in warnings)


def test_gendered_pronoun_is_flagged():
    warnings = verify(with_change(condition="He held three accounts [S3]."), SOURCES, ALLOWED)
    assert any("pronoun" in w for w in warnings)


def test_questions_about_usage_are_allowed_in_not_known():
    draft = with_change(not_known=["Was the account logged in to after termination?"])
    assert verify(draft, SOURCES, ALLOWED) == []


if __name__ == "__main__":
    tests = [value for name, value in dict(globals()).items() if name.startswith("test_")]
    for test in tests:
        test()
        print(f"passed: {test.__name__}")
    print(f"\nAll {len(tests)} tests passed.")
