import json
from typing import List, Dict, Any

def search_knowledge_base(category: str, file_path: str = "data/policies.json", top_k: int = 2) -> List[Dict[str, str]]:
    """Searches local JSON knowledge base for policies relevant to the ticket category."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            knowledge_base: Dict[str, Any] = json.load(f)
            
        # If the category exists in our database, return the rules
        if category in knowledge_base:
            return knowledge_base[category][:top_k]
        else:
            # Fallback if Agent 1 gives us a weird category
            return [{"title": "General Policy", "content": "Refer to standard terms and conditions. Escalate to human if unsure."}]
            
    except FileNotFoundError:
        return [{"title": "Error", "content": f"Knowledge base file not found at {file_path}"}]