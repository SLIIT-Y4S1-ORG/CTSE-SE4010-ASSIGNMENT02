from app.state import SupportState
from agents.escalation_decision_agent import escalation_decision_node

def test_escalation_damaged_item_with_photo():
    """Test: Damaged item WITH photo evidence → should APPROVE"""
    mock_state: SupportState = {
        "ticket_id": "TCK-1001",
        "customer_name": "Alice Smith",
        "ticket_text": "My item arrived completely broken. I have photos attached.",
        "category": "damaged_item",
        "urgency": "medium",
        "sentiment": "negative",
        "missing_information": [],  # Photo is provided
        "policy_matches": ["Damaged items with photo evidence qualify for full refund within 7 days."]
    }

    result = escalation_decision_node(mock_state)

    assert "decision" in result
    assert result["decision"] == "approve"
    assert result["escalate_to"] is None
    assert "next_steps" in result
    assert len(result["next_steps"]) > 0
    print(f"✓ Test passed: Damaged item with photo → {result['decision']}")


def test_escalation_damaged_item_without_photo():
    """Test: Damaged item WITHOUT photo evidence → should REQUEST_MORE_INFO"""
    mock_state: SupportState = {
        "ticket_id": "TCK-1002",
        "customer_name": "Bob Jones",
        "ticket_text": "My headphones arrived broken. The left ear doesn't work.",
        "category": "damaged_item",
        "urgency": "medium",
        "sentiment": "negative",
        "missing_information": ["photo", "attachment"],  # Missing photo
        "policy_matches": ["Damaged items require photo evidence for refund eligibility."]
    }

    result = escalation_decision_node(mock_state)

    assert result["decision"] == "request_more_info"
    assert result["escalate_to"] is None
    assert len(result["next_steps"]) > 0
    print(f"✓ Test passed: Damaged item without photo → {result['decision']}")


def test_escalation_billing_high_urgency():
    """Test: Billing issue with HIGH urgency → should ESCALATE_TO_BILLING"""
    mock_state: SupportState = {
        "ticket_id": "TCK-1003",
        "customer_name": "Carol White",
        "ticket_text": "I was charged $45 TWICE for the same order! This is ridiculous!",
        "category": "billing_issue",
        "urgency": "high",
        "sentiment": "negative",
        "missing_information": [],
        "policy_matches": ["Double-charge policy: escalate immediately to Billing Team for verification."]
    }

    result = escalation_decision_node(mock_state)

    assert result["decision"] == "escalate_to_billing"
    assert result["escalate_to"] == "billing"
    assert len(result["next_steps"]) > 0
    print(f"✓ Test passed: Billing issue (high urgency) → {result['decision']} → {result['escalate_to']}")


def test_escalation_delayed_delivery():
    """Test: Delayed delivery (standard) → should APPROVE with compensation"""
    mock_state: SupportState = {
        "ticket_id": "TCK-1004",
        "customer_name": "Alice Smith",
        "ticket_text": "My order is 5 days late. Where is my package?",
        "category": "delayed_delivery",
        "urgency": "medium",
        "sentiment": "negative",
        "missing_information": [],
        "policy_matches": ["Late delivery by >3 days: offer 15% discount code."]
    }

    result = escalation_decision_node(mock_state)

    assert result["decision"] == "approve"
    assert result["escalate_to"] is None
    print(f"✓ Test passed: Delayed delivery (standard) → {result['decision']}")


def test_escalation_abusive_high_urgency():
    """Test: Abusive language + high urgency → should ESCALATE_TO_HUMAN_SUPPORT"""
    mock_state: SupportState = {
        "ticket_id": "TCK-1005",
        "customer_name": "Bob Jones",
        "ticket_text": "This is ridiculous! Your company is terrible and I'm disgusted with the service!",
        "category": "billing_issue",
        "urgency": "high",
        "sentiment": "negative",
        "missing_information": [],
        "policy_matches": []
    }

    result = escalation_decision_node(mock_state)

    assert result["decision"] == "escalate_to_human_support"
    assert result["escalate_to"] == "human_support"
    print(f"✓ Test passed: Abusive + high urgency → {result['decision']} → {result['escalate_to']}")


def test_escalation_critical_urgency():
    """Test: CRITICAL urgency → should escalate to HUMAN_SUPPORT regardless"""
    mock_state: SupportState = {
        "ticket_id": "TCK-1006",
        "customer_name": "Alice Smith",
        "ticket_text": "I need immediate help! System down!",
        "category": "damaged_item",
        "urgency": "critical",
        "sentiment": "negative",
        "missing_information": [],
        "policy_matches": []
    }

    result = escalation_decision_node(mock_state)

    assert result["decision"] == "escalate_to_human_support"
    assert result["escalate_to"] == "human_support"
    print(f"✓ Test passed: Critical urgency → {result['decision']}")


def test_escalation_refund_request():
    """Test: Standard refund request → should APPROVE"""
    mock_state: SupportState = {
        "ticket_id": "TCK-1007",
        "customer_name": "Bob Jones",
        "ticket_text": "I'd like to return the unopened item from my order.",
        "category": "refund_request",
        "urgency": "low",
        "sentiment": "neutral",
        "missing_information": [],
        "policy_matches": ["Unopened items: full refund within 30 days. Return shipping cost billed to customer."]
    }

    result = escalation_decision_node(mock_state)

    assert result["decision"] == "approve"
    assert result["escalate_to"] is None
    print(f"✓ Test passed: Refund request → {result['decision']}")


def test_escalation_missing_critical_info():
    """Test: Missing critical information → should REQUEST_MORE_INFO"""
    mock_state: SupportState = {
        "ticket_id": "TCK-1008",
        "customer_name": "Alice Smith",
        "ticket_text": "I want a refund but can't find my receipt.",
        "category": "refund_request",
        "urgency": "low",
        "sentiment": "neutral",
        "missing_information": ["order_id", "date_of_purchase"],
        "policy_matches": ["Refund requires order ID and purchase date verification."]
    }

    result = escalation_decision_node(mock_state)

    assert result["decision"] == "request_more_info"
    assert result["escalate_to"] is None
    print(f"✓ Test passed: Missing info → {result['decision']}")


if __name__ == "__main__":
    print("=" * 60)
    print("ESCALATION DECISION AGENT - TEST SUITE")
    print("=" * 60)
    
    test_escalation_damaged_item_with_photo()
    test_escalation_damaged_item_without_photo()
    test_escalation_billing_high_urgency()
    test_escalation_delayed_delivery()
    test_escalation_abusive_high_urgency()
    test_escalation_critical_urgency()
    test_escalation_refund_request()
    test_escalation_missing_critical_info()
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED! ✓")
    print("=" * 60)
