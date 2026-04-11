from app.state import SupportState
from tools.faq_search import search_knowledge_base

def knowledge_retrieval_node(state: SupportState):
    """
    Agent 2: Reads the category from Agent 1, searches the local DB, 
    and appends the findings to the state.
    """
    # 1. Read what Agent 1 wrote in the state
    ticket_category = state.get("category", "unknown")
    print(f"\n[Agent 2] Searching knowledge base for category: '{ticket_category}'...")
    
    # 2. Calls FAQ search Python tool
    evidence = search_knowledge_base(category=ticket_category)
    
    # 3. Format the results into a clean list of strings
    formatted_policies = []
    for item in evidence:
        formatted_policies.append(f"{item['title']}: {item['content']}")
        print(f"   -> Found: {item['title']}")
        
    # 4. Return the new state update with the retrieved policies
    return {
        "policy_matches": formatted_policies
    }