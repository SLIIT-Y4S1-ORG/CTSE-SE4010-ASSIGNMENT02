from app.state import SupportState
from agents.knowledge_retrieval_agent import knowledge_retrieval_node

def test_knowledge_retrieval_node_valid_category():
    # Setup mock state
    mock_state: SupportState = {
        "ticket_text": "My item arrived completely smashed, I want my money back.",
        "category": "damaged_item"
    }

    # Run agent
    result = knowledge_retrieval_node(mock_state)

    # Assertions
    assert "policy_matches" in result
    assert len(result["policy_matches"]) == 1

    # Validate key policy ideas from the AI summary
    ai_summary = result["policy_matches"][0].lower()
    assert "refund" in ai_summary
    assert "photo" in ai_summary or "proof" in ai_summary

def test_knowledge_retrieval_node_unknown_category():
    mock_state: SupportState = {
        "ticket_text": "Do you guys sell hotdogs?",
        "category": "weird_unknown_issue"
    }

    result = knowledge_retrieval_node(mock_state)

    assert "policy_matches" in result
    assert len(result["policy_matches"]) == 1

    ai_summary = result["policy_matches"][0].lower()
    assert "terms" in ai_summary or "escalate" in ai_summary or "policy" in ai_summary