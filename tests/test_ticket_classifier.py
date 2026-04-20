"""
test_ticket_classifier.py
--------------------------
Evaluation / unit-test script for the Intent Classification Agent tool.

Tests the rule-based ``classify_ticket()`` function directly — no Ollama
or LLM dependency required, so it runs offline and fast.

Run with:
    python tests/test_ticket_classifier.py

Exit code 0 = all tests passed.
Exit code 1 = one or more tests failed.
"""

from __future__ import annotations

import sys
import os
import traceback
from typing import Any, Callable, Dict, List, Optional

# ---------------------------------------------------------------------------
# Path setup — allow running from project root
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools.ticket_classifier_tool import classify_ticket  # noqa: E402


# ---------------------------------------------------------------------------
# Lightweight test framework
# ---------------------------------------------------------------------------

class _Result:
    def __init__(self, name: str, passed: bool, message: str) -> None:
        self.name = name
        self.passed = passed
        self.message = message


_results: List[_Result] = []


def _run_test(name: str, fn: Callable[[], None]) -> None:
    """Execute *fn* and record pass / fail."""
    try:
        fn()
        _results.append(_Result(name, True, "OK"))
        print(f"  [PASS] {name}")
    except AssertionError as exc:
        msg = str(exc) or "Assertion failed"
        _results.append(_Result(name, False, msg))
        print(f"  [FAIL] {name}  →  {msg}")
    except Exception as exc:  # noqa: BLE001
        msg = f"{type(exc).__name__}: {exc}"
        _results.append(_Result(name, False, msg))
        print(f"  [ERROR] {name}  →  {msg}")
        traceback.print_exc()


def _assert_field(
    result: Dict[str, Any],
    field: str,
    expected: Any,
    *,
    partial: bool = False,
) -> None:
    """Assert *result[field]* equals (or contains) *expected*."""
    actual = result.get(field)
    if partial and isinstance(expected, list):
        missing = [item for item in expected if item not in actual]
        assert not missing, (
            f"Field '{field}': expected {expected!r} to be present in {actual!r}; "
            f"missing: {missing}"
        )
    else:
        assert actual == expected, (
            f"Field '{field}': expected {expected!r}, got {actual!r}"
        )


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

def test_damaged_item_with_evidence() -> None:
    """Happy path: broken product with attachment — no missing info."""
    ticket = (
        "Hi, I received my coffee mug today but the handle is completely shattered. "
        "I have attached a picture of the broken mug and the box it came in. "
        "My order number is ORD-5592. I would like my money back."
    )
    result = classify_ticket(ticket)
    _assert_field(result, "category", "damaged_item")
    # Urgency can be medium or high (reasonable either way)
    assert result["urgency"] in {"medium", "high"}, (
        f"Expected urgency medium or high, got {result['urgency']!r}"
    )
    # Evidence + order_id present → missing list should NOT include them
    assert "evidence_attachment" not in result["missing_information"], (
        "Ticket has photo attachment — should NOT flag evidence_attachment"
    )
    assert "order_id" not in result["missing_information"], (
        "Ticket has order id — should NOT flag order_id"
    )


def test_billing_issue_double_charge() -> None:
    """Billing issue: double charge, angry customer → high urgency + negative sentiment."""
    ticket = (
        "I checked my bank statement and you charged me $45 TWICE for the same order! "
        "This is absolutely ridiculous, fix it NOW!"
    )
    result = classify_ticket(ticket)
    _assert_field(result, "category", "billing_issue")
    _assert_field(result, "urgency", "high")
    _assert_field(result, "sentiment", "negative")


def test_shipping_delayed_missing_order_id() -> None:
    """Shipping issue: ticket missing order ID — should be flagged."""
    ticket = (
        "My package has not arrived yet. It has been two weeks since I placed my order. "
        "Please tell me where my shipment is."
    )
    result = classify_ticket(ticket)
    _assert_field(result, "category", "shipping_issue")
    assert "order_id" in result["missing_information"], (
        "Ticket has no order id — expected 'order_id' in missing_information"
    )


def test_account_issue_locked() -> None:
    """Account issue: locked account, no email provided → missing account_email."""
    ticket = (
        "I cannot log in to my account. It says my account is locked or suspended. "
        "Please help me regain access."
    )
    result = classify_ticket(ticket)
    _assert_field(result, "category", "account_issue")
    assert "account_email" in result["missing_information"], (
        "No email in ticket — expected 'account_email' in missing_information"
    )


def test_angry_customer_urgent() -> None:
    """Edge case: furious customer with explicit urgency language."""
    ticket = (
        "This is the WORST service I have ever experienced! "
        "I need this resolved IMMEDIATELY or I am taking legal action. "
        "My product arrived completely broken and I have been waiting for a week!"
    )
    result = classify_ticket(ticket)
    # Should be damaged_item (broken product)
    _assert_field(result, "category", "damaged_item")
    _assert_field(result, "urgency", "high")
    _assert_field(result, "sentiment", "negative")


def test_incomplete_ticket_one_liner() -> None:
    """Edge case: extremely short ticket with no useful info."""
    ticket = "help"
    result = classify_ticket(ticket)
    # Should default to missing_information or other
    assert result["category"] in {"missing_information", "other"}, (
        f"Expected missing_information or other for one-word ticket, "
        f"got {result['category']!r}"
    )


def test_unclear_category_falls_to_other() -> None:
    """Edge case: ticket that doesn't match any specific category."""
    ticket = (
        "Hello, I just wanted to say thank you for the wonderful experience. "
        "Everything was handled professionally and I am very satisfied. "
        "Keep up the great work!"
    )
    result = classify_ticket(ticket)
    # No category keywords present — should be "other"
    _assert_field(result, "category", "other")
    _assert_field(result, "sentiment", "positive")
    _assert_field(result, "urgency", "medium")


def test_refund_request_detected() -> None:
    """Refund request should be identified even without damage keywords."""
    ticket = (
        "I want a full refund for my recent purchase. "
        "The product did not match the description on the website. "
        "Please process my refund to order ORD-9988."
    )
    result = classify_ticket(ticket)
    _assert_field(result, "category", "refund_request")
    assert "order_id" not in result["missing_information"], (
        "Ticket provides order id — should NOT flag order_id"
    )


def test_technical_issue_app_crash() -> None:
    """Technical issue: app crash with error mention."""
    ticket = (
        "Your mobile app keeps crashing every time I open it. "
        "I see an error message and then the app freezes. "
        "I have tried reinstalling but it still happens."
    )
    result = classify_ticket(ticket)
    _assert_field(result, "category", "technical_issue")


def test_missing_info_damaged_no_photo_no_order() -> None:
    """Damaged item ticket missing both order ID and photo evidence."""
    ticket = "My product is damaged and I want help."
    result = classify_ticket(ticket)
    _assert_field(result, "category", "damaged_item")
    assert "order_id" in result["missing_information"], (
        "Expected 'order_id' in missing_information"
    )
    assert "evidence_attachment" in result["missing_information"], (
        "Expected 'evidence_attachment' in missing_information"
    )


def test_invalid_input_raises_value_error() -> None:
    """Tool must raise ValueError for empty or non-string input."""
    try:
        classify_ticket("")  # type: ignore[arg-type]
        assert False, "Expected ValueError for empty string"
    except ValueError:
        pass  # expected

    try:
        classify_ticket(None)  # type: ignore[arg-type]
        assert False, "Expected ValueError for None input"
    except (ValueError, AttributeError):
        pass  # expected — either is acceptable


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("  Intent Classification Agent — Test Suite")
    print("=" * 60)

    tests = [
        ("TC-01  Damaged item + evidence present",           test_damaged_item_with_evidence),
        ("TC-02  Billing double-charge (high urgency)",      test_billing_issue_double_charge),
        ("TC-03  Shipping — missing order ID",               test_shipping_delayed_missing_order_id),
        ("TC-04  Account locked — missing email",            test_account_issue_locked),
        ("TC-05  Angry customer — urgent + negative",        test_angry_customer_urgent),
        ("TC-06  Incomplete one-liner ticket",               test_incomplete_ticket_one_liner),
        ("TC-07  Unclear category → other + positive",       test_unclear_category_falls_to_other),
        ("TC-08  Refund request with order ID",              test_refund_request_detected),
        ("TC-09  Technical issue (app crash)",               test_technical_issue_app_crash),
        ("TC-10  Damaged — missing photo AND order ID",      test_missing_info_damaged_no_photo_no_order),
        ("TC-11  Invalid input → ValueError",                test_invalid_input_raises_value_error),
    ]

    print()
    for name, fn in tests:
        _run_test(name, fn)

    # Summary
    total = len(_results)
    passed = sum(1 for r in _results if r.passed)
    failed = total - passed

    print()
    print("=" * 60)
    print(f"  Results: {passed}/{total} passed  |  {failed} failed")
    print("=" * 60)

    if failed:
        print("\nFailed tests:")
        for r in _results:
            if not r.passed:
                print(f"  • {r.name}: {r.message}")
        sys.exit(1)
    else:
        print("\n  All tests passed ✓")
        sys.exit(0)


if __name__ == "__main__":
    main()
