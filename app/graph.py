"""
Multi-agent workflow graph for customer support ticket processing.
Chains together Agents 1-4 in a state machine workflow.

Flow:
  Agent 1 (Classifier) → Agent 2 (Knowledge Retrieval) → 
  Agent 3 (Escalation Decision) → Agent 4 (Response Drafting)

Integration Pattern:
  - Agent 3 outputs (decision, escalate_to, next_steps) flow into SupportState
  - Agent 4 reads those outputs from SupportState
  - Both agents use the same state dictionary
"""

from typing import Dict, Any, Callable, Optional
from app.state import SupportState
from agents.response_drafting_agent import response_drafting_node

# Lazy import for Agent 3 (optional, with graceful fallback)
_escalation_decision_node: Optional[Callable] = None

def get_escalation_decision_node() -> Optional[Callable]:
    """
    Lazy-load Agent 3 (Escalation Decision Node).
    Returns None if dependencies are not available.
    This allows the integration to work even if Agent 3 can't be imported.
    """
    global _escalation_decision_node
    
    if _escalation_decision_node is not None:
        return _escalation_decision_node
    
    try:
        from agents.escalation_decision_agent import escalation_decision_node
        _escalation_decision_node = escalation_decision_node
        return _escalation_decision_node
    except ImportError as e:
        print(f"⚠ Warning: Could not import Agent 3: {e}")
        print("  Integration will use Agent 4 only.")
        return None


class SupportTicketWorkflow:
    """
    Multi-agent workflow orchestrator.
    
    Demonstrates Agent 3 → Agent 4 integration pattern:
    - State flows through agents left-to-right
    - Agent 3 outputs (decision, escalate_to, next_steps) get added to state
    - Agent 4 reads Agent 3 outputs from state to draft response
    
    Note: Agent 3 is lazy-loaded to gracefully handle missing dependencies.
          If Agent 3 unavailable, workflow runs Agent 4 only for demonstration.
    """
    
    def __init__(self):
        """Initialize the workflow."""
        self.escalation_node = get_escalation_decision_node()
    
    def process_ticket(
        self, 
        state: SupportState,
        run_agent_3: bool = True,
        run_agent_4: bool = True,
    ) -> SupportState:
        """
        Process a ticket through the workflow.
        
        Integration Demo:
        1. Agent 3 adds: decision, escalate_to, next_steps
        2. Agent 4 reads those fields and generates: draft_response
        
        Args:
            state: Initial SupportState with ticket data from Agents 1 & 2
            run_agent_3: Whether to run escalation decision (default: True)
            run_agent_4: Whether to run response drafting (default: True)
        
        Returns:
            Updated SupportState with all agent outputs
        """
        
        # AGENT 3: Escalation Decision
        if run_agent_3 and self.escalation_node:
            print("\n" + "="*70)
            print("AGENT 3: ESCALATION DECISION")
            print("="*70)
            
            agent_3_output = self.escalation_node(state)
            
            # Merge Agent 3 output into state
            state.update({
                "decision": agent_3_output.get("decision"),
                "escalate_to": agent_3_output.get("escalate_to"),
                "next_steps": agent_3_output.get("next_steps", []),
            })
            
            print(f"\n✓ Agent 3 Complete")
            print(f"  Decision: {state['decision']}")
            if state.get('escalate_to'):
                print(f"  Escalate To: {state['escalate_to']}")
        elif run_agent_3 and not self.escalation_node:
            print("\n[INFO] Agent 3 not available (dependency missing)")
            print("  Using mock decision for demonstration...")
            # Provide default decision for Agent 4 to work with
            state.update({
                "decision": "request_more_info",
                "escalate_to": None,
                "next_steps": ["Please provide more information"],
            })
        
        # AGENT 4: Response Drafting
        # This demonstrates Agent 4 reading Agent 3's outputs from state
        if run_agent_4:
            print("\n" + "="*70)
            print("AGENT 4: RESPONSE DRAFTING")
            print("="*70)
            print(f"\n[Agent 4 Reading from State]")
            print(f"  • decision: {state.get('decision', 'N/A')}")
            print(f"  • escalate_to: {state.get('escalate_to') or 'N/A'}")
            print(f"  • next_steps: {state.get('next_steps', [])}")
            print(f"\n[Agent 4 Processing...]")
            
            agent_4_output = response_drafting_node(state)
            
            # Merge Agent 4 output into state
            state.update({
                "draft_response": agent_4_output.get("draft_response"),
            })
            
            print(f"\n✓ Agent 4 Complete")
            print(f"  Response Preview: {state['draft_response'][:80]}...")
        
        return state


def process_support_ticket(
    ticket_id: str,
    customer_name: str,
    ticket_text: str,
    category: str = "general",
    urgency: str = "medium",
    sentiment: str = "neutral",
    missing_information: list = None,
    policy_matches: list = None,
) -> Dict[str, Any]:
    """
    Convenience function to process a ticket through the entire workflow.
    
    This simulates the output from Agents 1 & 2, then runs Agents 3 & 4.
    
    Args:
        ticket_id: Unique ticket identifier
        customer_name: Customer's name
        ticket_text: Full ticket text
        category: Ticket category (from Agent 1)
        urgency: Urgency level (from Agent 1)
        sentiment: Sentiment analysis (from Agent 1)
        missing_information: Missing info list (from Agent 1)
        policy_matches: Matched policies (from Agent 2)
    
    Returns:
        Complete SupportState with all agent outputs
    """
    
    # Build initial state (as if from Agents 1 & 2)
    state: SupportState = {
        "ticket_id": ticket_id,
        "customer_name": customer_name,
        "ticket_text": ticket_text,
        "category": category,
        "urgency": urgency,
        "sentiment": sentiment,
        "missing_information": missing_information or [],
        "policy_matches": policy_matches or [],
    }
    
    # Process through workflow
    workflow = SupportTicketWorkflow()
    final_state = workflow.process_ticket(state, run_agent_3=True, run_agent_4=True)
    
    return final_state


if __name__ == "__main__":
    # Example: Process a complete ticket through Agent 3 & 4
    
    result = process_support_ticket(
        ticket_id="DEMO-001",
        customer_name="Sarah Johnson",
        ticket_text="I received my order but the item is damaged. The box was completely crushed.",
        category="damaged_item",
        urgency="medium",
        sentiment="negative",
        missing_information=["photo"],  # Customer hasn't provided photo yet
        policy_matches=[
            "Damaged Item Refund Policy: Customers are eligible for a full refund or replacement "
            "for items damaged in transit within 7 days of delivery. A clear photo of the damaged "
            "item is strictly required before processing."
        ]
    )
    
    print("\n" + "="*70)
    print("FINAL RESULT")
    print("="*70)
    print(f"Decision: {result['decision']}")
    print(f"Escalate To: {result.get('escalate_to', 'N/A')}")
    print(f"Next Steps: {', '.join(result.get('next_steps', []))}")
    print(f"\nDraft Response:\n{result.get('draft_response', 'N/A')}")
