"""Utilities for building customer-facing support responses.

This module provides a small, file-backed tool that turns structured support
state into a consistent customer response draft. It also writes generated
responses to a local JSONL log so the team can demonstrate real-world file I/O
for the assignment.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping


DEFAULT_TEMPLATES: Dict[str, str] = {
    "approval": (
        "Hello {customer_name},\n\n"
        "Thanks for contacting us about ticket {ticket_id}. Based on the policy review, {policy_summary}\n\n"
        "Next steps: {next_steps}\n\n"
        "Thank you for your patience."
    ),
    "request_more_info": (
        "Hello {customer_name},\n\n"
        "Thanks for reaching out about ticket {ticket_id}. We need a little more information before we can continue. {policy_summary}\n\n"
        "Please provide: {next_steps}\n\n"
        "Thank you."
    ),
    "escalation": (
        "Hello {customer_name},\n\n"
        "Thank you for your message about ticket {ticket_id}. We have reviewed the available details and will continue handling this through the appropriate support channel. {policy_summary}\n\n"
        "Next steps: {next_steps}\n\n"
        "Thank you for your patience."
    ),
    "rejection": (
        "Hello {customer_name},\n\n"
        "Thank you for contacting us about ticket {ticket_id}. Based on the current policy review, we cannot approve the request. {policy_summary}\n\n"
        "Next steps: {next_steps}\n\n"
        "Thank you."
    ),
    "default": (
        "Hello {customer_name},\n\n"
        "Thanks for contacting support about ticket {ticket_id}. {policy_summary}\n\n"
        "Next steps: {next_steps}\n\n"
        "Thank you."
    ),
}


def _load_template_overrides(template_path: str) -> Dict[str, str]:
    """Load template overrides from disk when a JSON file is available."""

    path = Path(template_path)
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)

    if not isinstance(loaded, Mapping):
        raise ValueError("Template file must contain a JSON object of string templates.")

    overrides: Dict[str, str] = {}
    for key, value in loaded.items():
        if isinstance(key, str) and isinstance(value, str):
            overrides[key] = value

    return overrides


def _normalize_next_steps(next_steps: Any) -> str:
    if isinstance(next_steps, list):
        cleaned = [str(item).strip() for item in next_steps if str(item).strip()]
        return "; ".join(cleaned) if cleaned else "follow the instructions provided by support"

    if isinstance(next_steps, str):
        cleaned = next_steps.strip()
        return cleaned or "follow the instructions provided by support"

    return "follow the instructions provided by support"


def build_response_template(
    response_data: Dict[str, Any],
    template_path: str = "data/response_templates.json",
    output_path: str = "data/generated_responses.jsonl",
) -> str:
    """Build a customer-facing support response from structured decision data.

    Args:
        response_data: Structured response inputs such as customer name, ticket
            id, decision, policy summary, and next steps.
        template_path: Optional JSON file that can override the default message
            templates.
        output_path: JSONL file that receives a local audit record of the final
            drafted response.

    Returns:
        A formatted customer-facing response string.
    """

    templates = DEFAULT_TEMPLATES | _load_template_overrides(template_path)

    customer_name = str(response_data.get("customer_name") or "Customer").strip() or "Customer"
    ticket_id = str(response_data.get("ticket_id") or "UNKNOWN").strip() or "UNKNOWN"
    decision = str(response_data.get("decision") or "default").strip().lower()
    decision_key = "default"
    if decision.startswith("approve"):
        decision_key = "approval"
    elif decision.startswith("request_more_info"):
        decision_key = "request_more_info"
    elif decision.startswith("escalate"):
        decision_key = "escalation"
    elif decision.startswith("reject"):
        decision_key = "rejection"

    policy_summary = str(response_data.get("policy_summary") or "We have reviewed the available policy guidance.").strip()
    if not policy_summary.endswith("."):
        policy_summary = f"{policy_summary}."

    next_steps = _normalize_next_steps(response_data.get("next_steps"))

    template = templates.get(decision_key, templates["default"])
    response_text = template.format(
        customer_name=customer_name,
        ticket_id=ticket_id,
        policy_summary=policy_summary,
        next_steps=next_steps,
    ).strip()

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ticket_id": ticket_id,
        "decision": decision,
        "customer_name": customer_name,
        "response": response_text,
    }
    with output_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    return response_text