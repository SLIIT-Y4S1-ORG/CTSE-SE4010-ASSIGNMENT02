from typing import TypedDict, List, Annotated, Optional
import operator

class SupportState(TypedDict, total=False):
    # Initial Input
    ticket_id: str
    customer_name: str
    ticket_text: str
    
    # Agent 1 (Classification) Fills These
    category: str
    urgency: str
    sentiment: str
    missing_information: List[str]
    
    # Agent 2 (Retrieval) Fills This
    policy_matches: Annotated[List[str], operator.add]
    
    # Agent 3 (Escalation) Fills These
    decision: str
    escalate_to: Optional[str]
    next_steps: List[str]
    
    # Agent 4 (Response) Fills This
    draft_response: str