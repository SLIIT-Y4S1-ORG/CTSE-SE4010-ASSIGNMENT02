from app.state import SupportState
from agents.escalation_decision_agent import escalation_decision_node

# Test Case: Your Custom Scenario
mock_state: SupportState = {
    "ticket_id": "TCK-CUSTOM-001",
    "customer_name": "John Fraud",  # This customer is flagged in data/customer_history.json
    "ticket_text": "I want a refund immediately!",
    "category": "refund_request",
    "urgency": "high",
    "sentiment": "negative",
    "missing_information": [],
    "policy_matches": ["Refund policy applies"]
}

print("Running custom test...")
result = escalation_decision_node(mock_state)

print(f"\nDecision: {result['decision']}")
print(f"Escalate To: {result['escalate_to']}")
print(f"Next Steps:")
for step in result['next_steps']:
    print(f"  • {step}")