"""
Test runner for Escalation Decision Agent (Agent 3)
Simulates the flow from Agent 1 and Agent 2 through Agent 3
"""

from app.state import SupportState
from agents.escalation_decision_agent import escalation_decision_node

# Test Case 1: TCK-1001 - Damaged item WITH photo (should APPROVE)
print("\n" + "="*70)
print("TEST CASE 1: Damaged Item WITH Photo Evidence")
print("="*70)

mock_state_1: SupportState = {
    "ticket_id": "TCK-1001",
    "customer_name": "Alice Smith",
    "ticket_text": "Hi, I received my coffee mug today but the handle is completely shattered. I have attached a picture of the broken mug and the box it came in. I would like my money back.",
    "category": "damaged_item",  # From Agent 1
    "urgency": "medium",  # From Agent 1
    "sentiment": "negative",  # From Agent 1
    "missing_information": [],  # No missing info - has photo
    "policy_matches": [  # From Agent 2
        "Damaged Item Refund Policy: Customers are eligible for a full refund or replacement for items damaged in transit within 7 days of delivery. A clear photo of the damaged item is strictly required before processing."
    ]
}

print("INPUT STATE:")
print(f"  Ticket ID: {mock_state_1['ticket_id']}")
print(f"  Category: {mock_state_1['category']}")
print(f"  Urgency: {mock_state_1['urgency']}")
print(f"  Missing Info: {mock_state_1['missing_information']}")

result_1 = escalation_decision_node(mock_state_1)

print("\nOUTPUT FROM AGENT 3:")
print(f"  Decision: {result_1['decision']}")
print(f"  Escalate To: {result_1['escalate_to']}")
print(f"  Next Steps:")
for step in result_1['next_steps']:
    print(f"    • {step}")

expected_1 = "approve"
status_1 = "✓ PASS" if result_1['decision'] == expected_1 else "✗ FAIL"
print(f"\n{status_1} - Expected 'approve', got '{result_1['decision']}'")

# Test Case 2: TCK-1002 - Damaged item WITHOUT photo (should REQUEST_MORE_INFO)
print("\n" + "="*70)
print("TEST CASE 2: Damaged Item WITHOUT Photo Evidence")
print("="*70)

mock_state_2: SupportState = {
    "ticket_id": "TCK-1002",
    "customer_name": "Bob Jones",
    "ticket_text": "My new headphones arrived broken. The left ear doesn't work at all. Please send me a new one immediately.",
    "category": "damaged_item",  # From Agent 1
    "urgency": "medium",
    "sentiment": "negative",
    "missing_information": ["photo", "attachment"],  # Missing photo!
    "policy_matches": [
        "Damaged Item Refund Policy: Customers are eligible for a full refund or replacement for items damaged in transit within 7 days of delivery. A clear photo of the damaged item is strictly required before processing."
    ]
}

print("INPUT STATE:")
print(f"  Ticket ID: {mock_state_2['ticket_id']}")
print(f"  Category: {mock_state_2['category']}")
print(f"  Urgency: {mock_state_2['urgency']}")
print(f"  Missing Info: {mock_state_2['missing_information']}")

result_2 = escalation_decision_node(mock_state_2)

print("\nOUTPUT FROM AGENT 3:")
print(f"  Decision: {result_2['decision']}")
print(f"  Escalate To: {result_2['escalate_to']}")
print(f"  Next Steps:")
for step in result_2['next_steps']:
    print(f"    • {step}")

expected_2 = "request_more_info"
status_2 = "✓ PASS" if result_2['decision'] == expected_2 else "✗ FAIL"
print(f"\n{status_2} - Expected 'request_more_info', got '{result_2['decision']}'")

# Test Case 3: TCK-1003 - Billing issue (should ESCALATE_TO_BILLING)
print("\n" + "="*70)
print("TEST CASE 3: Billing Issue - High Urgency")
print("="*70)

mock_state_3: SupportState = {
    "ticket_id": "TCK-1003",
    "customer_name": "Carol White",
    "ticket_text": "I checked my bank statement and you guys charged me $45 TWICE for the same order! This is ridiculous, fix it now!",
    "category": "billing_issue",  # From Agent 1
    "urgency": "high",
    "sentiment": "negative",
    "missing_information": [],
    "policy_matches": [
        "Double Charge Policy: If a customer claims they were charged twice, apologize and immediately escalate the ticket to the Billing Support Team for verification. Do not promise a refund until billing verifies."
    ]
}

print("INPUT STATE:")
print(f"  Ticket ID: {mock_state_3['ticket_id']}")
print(f"  Category: {mock_state_3['category']}")
print(f"  Urgency: {mock_state_3['urgency']}")
print(f"  Missing Info: {mock_state_3['missing_information']}")

result_3 = escalation_decision_node(mock_state_3)

print("\nOUTPUT FROM AGENT 3:")
print(f"  Decision: {result_3['decision']}")
print(f"  Escalate To: {result_3['escalate_to']}")
print(f"  Next Steps:")
for step in result_3['next_steps']:
    print(f"    • {step}")

expected_3 = "escalate_to_billing"
status_3 = "✓ PASS" if result_3['decision'] == expected_3 and result_3['escalate_to'] == "billing" else "✗ FAIL"
print(f"\n{status_3} - Expected 'escalate_to_billing' → 'billing', got '{result_3['decision']}' → '{result_3['escalate_to']}'")

# Summary
print("\n" + "="*70)
print("SUMMARY")
print("="*70)
test_results = [status_1.endswith("PASS"), status_2.endswith("PASS"), status_3.endswith("PASS")]
passed = sum(test_results)
total = len(test_results)
print(f"Passed: {passed}/{total}")
if passed == total:
    print("✓ ALL TESTS PASSED!")
else:
    print(f"✗ {total - passed} test(s) failed")
