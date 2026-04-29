"""Agent 4: Response drafting for the support workflow."""

from __future__ import annotations

from typing import Any, Dict, List

try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError:  # pragma: no cover - fallback for environments without LangChain
    class _FallbackMessage:
        def __init__(self, content: str):
            self.content = content

    class SystemMessage(_FallbackMessage):
        pass

    class HumanMessage(_FallbackMessage):
        pass

try:
    from langchain_ollama import ChatOllama
except ImportError:  # pragma: no cover - fallback for environments without Ollama bindings
    class ChatOllama:  # type: ignore[override]
        def __init__(self, *args: Any, **kwargs: Any):
            pass

        def invoke(self, messages: Any):
            return type("_FallbackResponse", (), {"content": ""})()

from app.state import SupportState
from tools.response_template_builder import build_response_template


llm = ChatOllama(model="llama3.2", temperature=0)

BANNED_PHRASES: List[str] = [
    "we guarantee",
    "internal note",
    "internal notes",
    "as an ai",
    "policy engine",
    "escalation decision",
    "unsupported promise",
]


def _format_policy_summary(policy_matches: List[str]) -> str:
    if not policy_matches:
        return "We have reviewed the available policy guidance."

    useful_matches = [match.strip() for match in policy_matches if str(match).strip()]
    if not useful_matches:
        return "We have reviewed the available policy guidance."

    if len(useful_matches) == 1:
        return useful_matches[0]

    return "; ".join(useful_matches[:2])


def _is_safe_customer_response(text: str) -> bool:
    lowered = text.lower()
    if not lowered.strip():
        return False

    return not any(phrase in lowered for phrase in BANNED_PHRASES)


def response_drafting_node(
    state: SupportState,
    llm_client: Any | None = None,
    template_path: str = "data/response_templates.json",
    output_path: str = "data/generated_responses.jsonl",
) -> Dict[str, Any]:
    """Draft the final customer-facing response for the ticket.

    The agent uses structured support state, a local response template builder,
    and a local Ollama model to produce a polished customer response without
    exposing internal reasoning or unsupported promises.
    """

    ticket_id = str(state.get("ticket_id", "UNKNOWN"))
    customer_name = str(state.get("customer_name", "Customer"))
    decision = str(state.get("decision", "default"))
    escalate_to = str(state.get("escalate_to") or "").strip()
    next_steps = state.get("next_steps", [])
    policy_matches = state.get("policy_matches", [])

    print(f"\n[Agent 4] Drafting customer response for ticket {ticket_id}...")
    print(f"  Decision: {decision}")
    if escalate_to:
        print(f"  Escalate To: {escalate_to}")

    policy_summary = _format_policy_summary(policy_matches)
    base_response = build_response_template(
        {
            "ticket_id": ticket_id,
            "customer_name": customer_name,
            "decision": decision,
            "policy_summary": policy_summary,
            "next_steps": next_steps,
        },
        template_path=template_path,
        output_path=output_path,
    )

    llm_client = llm_client or llm

    system_prompt = SystemMessage(
        content=(
            "You are a customer support response writer. Draft empathetic, concise, "
            "policy-grounded replies. Do not include internal notes or unsupported "
            "promises. Do not mention hidden decision logic. Use only the provided "
            "ticket details, policy summary, and next steps."
        )
    )
    human_prompt = HumanMessage(
        content=(
            f"Ticket ID: {ticket_id}\n"
            f"Customer Name: {customer_name}\n"
            f"Decision: {decision}\n"
            f"Escalate To: {escalate_to or 'None'}\n"
            f"Policy Summary: {policy_summary}\n"
            f"Next Steps: {', '.join(next_steps) if isinstance(next_steps, list) and next_steps else 'Follow support instructions'}\n\n"
            f"Base Draft:\n{base_response}\n\n"
            "Return only the final customer-facing response."
        )
    )

    ai_response = llm_client.invoke([system_prompt, human_prompt])
    draft_text = getattr(ai_response, "content", str(ai_response)).strip()

    final_response = draft_text if _is_safe_customer_response(draft_text) else base_response

    return {"draft_response": final_response}


def response_node(state: SupportState):
    """Backward-compatible alias for the response drafting agent."""

    return response_drafting_node(state)