from app.state import SupportState
from agents.knowledge_retrieval_agent import knowledge_retrieval_node

# 1. MOCK STATE: Pretend Agent 1 just finished and passed this to you
mock_state: SupportState = {
    "ticket_id": "TCK-1001",
    "customer_name": "Alice Smith",
    "ticket_text": "My item is broken!",
    "category": "damaged_item", # <--- Agent 1 categorized it!
    "urgency": "medium",
    "sentiment": "negative",
    "missing_information": ["order_id"],
    # Notice we don't have to fill in your part or Agent 3/4's part yet
}

# 2. Run YOUR agent
print("--- STARTING AGENT 2 ---")
new_state_update = knowledge_retrieval_node(mock_state)

# 3. Print the results
print("\n--- WHAT AGENT 2 IS PASSING TO AGENT 3 ---")
print(new_state_update)