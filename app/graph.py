from __future__ import annotations

import os
import sys
from typing import Any, Callable, Dict, Optional

# Support direct script execution/imports from `python app/main.py`
if __package__ in (None, ""):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.state import SupportState
from agents.ticket_classifier_agent import ticket_classifier_node
from agents.knowledge_retrieval_agent import knowledge_retrieval_node
from agents.response_drafting_agent import response_drafting_node

_escalation_decision_node: Optional[Callable[[SupportState], Dict[str, Any]]] = None


def _merge_state(base_state: SupportState, updates: Dict[str, Any]) -> SupportState:
    """Return a new state with non-empty update values merged in."""
    merged: SupportState = dict(base_state)
    for key, value in updates.items():
        if value is not None:
            merged[key] = value
    return merged


def get_escalation_decision_node() -> Optional[Callable[[SupportState], Dict[str, Any]]]:
    """Lazy-load Agent 3 so the workflow can still run if it is unavailable."""
    global _escalation_decision_node

    if _escalation_decision_node is not None:
        return _escalation_decision_node

    try:
        from agents.escalation_decision_agent import escalation_decision_node

        _escalation_decision_node = escalation_decision_node
        return _escalation_decision_node
    except ImportError as exc:
        print(f"⚠ Warning: Could not import Agent 3: {exc}")
        print("  Workflow will continue without Agent 3.")
        return None


def run_knowledge_retrieval_workflow(state: SupportState) -> SupportState:
    """Run Agent 2 and merge its output into the shared state."""
    updated_state: SupportState = dict(state)
    retrieval_update = knowledge_retrieval_node(updated_state)
    return _merge_state(updated_state, retrieval_update)


class SupportTicketWorkflow:
    """Orchestrates the support ticket agents in order."""

    def __init__(self) -> None:
        self.escalation_node = get_escalation_decision_node()

    def process_ticket(
        self,
        state: SupportState,
        run_agent_1: bool = True,
        run_agent_2: bool = True,
        run_agent_3: bool = True,
        run_agent_4: bool = True,
    ) -> SupportState:
        """Process a ticket through Agents 1, 2, 3, and 4."""
        current_state: SupportState = dict(state)

        if run_agent_1:
            print("\n" + "=" * 70)
            print("AGENT 1: INTENT CLASSIFICATION")
            print("=" * 70)
            agent_1_output = ticket_classifier_node(current_state)
            current_state = _merge_state(current_state, agent_1_output)
            print("\n✓ Agent 1 Complete")
            print(f"  Category: {current_state.get('category', 'N/A')}")
            print(f"  Urgency: {current_state.get('urgency', 'N/A')}")
            print(f"  Sentiment: {current_state.get('sentiment', 'N/A')}")
            missing = current_state.get("missing_information", [])
            print(f"  Missing Information: {', '.join(missing) if missing else 'None'}")

        if run_agent_2:
            print("\n" + "=" * 70)
            print("AGENT 2: KNOWLEDGE RETRIEVAL")
            print("=" * 70)
            current_state = run_knowledge_retrieval_workflow(current_state)

        if run_agent_3 and self.escalation_node:
            print("\n" + "=" * 70)
            print("AGENT 3: ESCALATION DECISION")
            print("=" * 70)
            agent_3_output = self.escalation_node(current_state)
            current_state = _merge_state(current_state, agent_3_output)
            print("\n✓ Agent 3 Complete")
            print(f"  Decision: {current_state.get('decision', 'N/A')}")
            if current_state.get("escalate_to"):
                print(f"  Escalate To: {current_state['escalate_to']}")
        elif run_agent_3 and not self.escalation_node:
            print("\n[INFO] Agent 3 not available (dependency missing)")
            current_state = _merge_state(
                current_state,
                {
                    "decision": "request_more_info",
                    "escalate_to": None,
                    "next_steps": ["Please provide more information"],
                },
            )

        if run_agent_4:
            print("\n" + "=" * 70)
            print("AGENT 4: RESPONSE DRAFTING")
            print("=" * 70)
            print("\n[Agent 4 Reading from State]")
            print(f"  • decision: {current_state.get('decision', 'N/A')}")
            print(f"  • escalate_to: {current_state.get('escalate_to') or 'N/A'}")
            print(f"  • next_steps: {current_state.get('next_steps', [])}")
            print("\n[Agent 4 Processing...]")

            agent_4_output = response_drafting_node(current_state)
            current_state = _merge_state(current_state, agent_4_output)

            print("\n✓ Agent 4 Complete")
            draft_preview = str(current_state.get("draft_response", ""))[:80]
            print(f"  Response Preview: {draft_preview}...")

        return current_state


def run_workflow(state: SupportState) -> SupportState:
    """Run the combined workflow for the current project setup."""
    workflow = SupportTicketWorkflow()
    return workflow.process_ticket(state, run_agent_1=True, run_agent_2=True, run_agent_3=True, run_agent_4=True)


def process_support_ticket(
    ticket_id: str,
    customer_name: str,
    ticket_text: str,
    category: str = "general",
    urgency: str = "medium",
    sentiment: str = "neutral",
    missing_information: list | None = None,
    policy_matches: list | None = None,
) -> Dict[str, Any]:
    """Convenience wrapper to run the workflow from simple input fields."""
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
    return run_workflow(state)


__all__ = [
    "SupportTicketWorkflow",
    "get_escalation_decision_node",
    "process_support_ticket",
    "run_knowledge_retrieval_workflow",
    "run_workflow",
]