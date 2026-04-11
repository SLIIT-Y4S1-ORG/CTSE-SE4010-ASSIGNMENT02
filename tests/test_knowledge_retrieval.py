from app.state import SupportState
from agents.knowledge_retrieval_agent import knowledge_retrieval_node

def test_knowledge_retrieval_node_valid_category():
    """Test that the agent finds correct policies for known categories."""
    # Setup mock state
    mock_state: SupportState = {"category": "damaged_item"}
    
    # Run knowledge retrieval agent
    result = knowledge_retrieval_node(mock_state)
    
    # Assertions to prove it worked
    assert "policy_matches" in result
    assert len(result["policy_matches"]) == 2
    assert "Damaged Item Refund Policy" in result["policy_matches"][0]

def test_knowledge_retrieval_node_unknown_category():
    """Test that the agent handles weird or missing categories safely."""
    # Setup mock state with a category that doesn't exist in our JSON
    mock_state: SupportState = {"category": "weird_unknown_issue"}
    
    # Run knowledge retrieval agent
    result = knowledge_retrieval_node(mock_state)
    
    # Assertions to prove it didn't crash and returned the fallback
    assert "policy_matches" in result
    assert len(result["policy_matches"]) == 1
    assert "General Policy" in result["policy_matches"][0]