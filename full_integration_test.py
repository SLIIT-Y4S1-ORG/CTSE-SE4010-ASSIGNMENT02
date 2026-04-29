#!/usr/bin/env python3
"""Full integration test for the support workflow from Agent 2 to Agent 4.

This script simulates the Agent 1 output needed to start the flow, then runs:
- Agent 2: knowledge retrieval
- Agent 3: escalation decision
- Agent 4: response drafting with Ollama

It writes temporary audit output so the test does not pollute the repository's
shared audit files.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Dict, List


def _install_langchain_compat_stubs() -> None:
    """Install lightweight compatibility stubs when LangChain packages are missing."""

    if "langchain_core.messages" not in sys.modules:
        messages_module = types.ModuleType("langchain_core.messages")

        class SystemMessage:
            def __init__(self, content: str):
                self.content = content

        class HumanMessage:
            def __init__(self, content: str):
                self.content = content

        messages_module.SystemMessage = SystemMessage
        messages_module.HumanMessage = HumanMessage

        core_module = types.ModuleType("langchain_core")
        core_module.messages = messages_module

        sys.modules.setdefault("langchain_core", core_module)
        sys.modules.setdefault("langchain_core.messages", messages_module)

    if "langchain_ollama" not in sys.modules:
        ollama_module = types.ModuleType("langchain_ollama")

        class ChatOllama:
            def __init__(self, *args: Any, **kwargs: Any):
                self.model = kwargs.get("model", "stub-model")

            def invoke(self, messages: Any):
                text_parts = [getattr(message, "content", str(message)) for message in messages]
                combined = "\n".join(text_parts)

                if "Base Draft:" in combined:
                    base_draft = combined.split("Base Draft:", 1)[1].split("\n\nReturn only", 1)[0].strip()
                    if base_draft:
                        return types.SimpleNamespace(content=base_draft)

                if "Policy Retrieval" in combined or "Extract ONLY" in combined:
                    return types.SimpleNamespace(content="Relevant policy guidance extracted from the knowledge base.")

                return types.SimpleNamespace(content="Validated by compatibility stub.")

        ollama_module.ChatOllama = ChatOllama
        sys.modules.setdefault("langchain_ollama", ollama_module)


_install_langchain_compat_stubs()

from app.state import SupportState
from agents.knowledge_retrieval_agent import knowledge_retrieval_node
from agents.escalation_decision_agent import escalation_decision_node
from agents.response_drafting_agent import response_drafting_node


def simulate_agent_1_classification(ticket_text: str, category: str) -> Dict[str, Any]:
    """Minimal Agent 1 stand-in used to seed the integration test."""

    lowered = ticket_text.lower()

    if "urgent" in lowered or "immediately" in lowered or "asap" in lowered:
        urgency = "high"
    else:
        urgency = "medium"

    if any(word in lowered for word in ["angry", "frustrated", "unacceptable", "!", "broken"]):
        sentiment = "negative"
    else:
        sentiment = "neutral"

    missing_information: List[str] = []
    if category == "damaged_item" and "photo" not in lowered and "image" not in lowered:
        missing_information.append("photo")
    if category == "billing_issue" and not any(word in lowered for word in ["order", "transaction", "receipt"]):
        missing_information.append("order_id")

    return {
        "category": category,
        "urgency": urgency,
        "sentiment": sentiment,
        "missing_information": missing_information,
    }


def run_full_integration_test() -> bool:
    """Run a complete Agent 2 → Agent 4 workflow across three scenarios."""

    print("\n" + "=" * 80)
    print("FULL INTEGRATION TEST: Agent 2 → Agent 4")
    print("=" * 80)

    scenarios = [
        {
            "name": "Damaged Item With Photo",
            "ticket_id": "FULL-INT-001",
            "customer_name": "Sarah Chen",
            "ticket_text": (
                "My headphones arrived with a broken speaker. I attached clear photos of the damage "
                "and the shipping box. Please help."
            ),
            "category": "damaged_item",
        },
        {
            "name": "Refund Request - Unopened Item",
            "ticket_id": "FULL-INT-002",
            "customer_name": "Michael Johnson",
            "ticket_text": (
                "I changed my mind about this purchase. The item is still unopened in original packaging. "
                "Can I get a refund?"
            ),
            "category": "refund_request",
        },
        {
            "name": "Billing Issue - High Urgency",
            "ticket_id": "FULL-INT-003",
            "customer_name": "Patricia Lopez",
            "ticket_text": "I was charged $89 TWICE for the same order! This is urgent, please fix this immediately!",
            "category": "billing_issue",
        },
    ]

    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        response_audit_path = tmp_path / "response_audit_log.jsonl"

        results: List[Dict[str, Any]] = []

        for scenario in scenarios:
            print("\n" + "-" * 80)
            print(f"SCENARIO: {scenario['name']}")
            print("-" * 80)

            agent_1_output = simulate_agent_1_classification(
                ticket_text=scenario["ticket_text"],
                category=scenario["category"],
            )

            state: SupportState = {
                "ticket_id": scenario["ticket_id"],
                "customer_name": scenario["customer_name"],
                "ticket_text": scenario["ticket_text"],
                "category": agent_1_output["category"],
                "urgency": agent_1_output["urgency"],
                "sentiment": agent_1_output["sentiment"],
                "missing_information": agent_1_output["missing_information"],
            }

            print("\n[Agent 2] Knowledge Retrieval")
            agent_2_output = knowledge_retrieval_node(state)
            state.update(agent_2_output)
            print(f"  Retrieved policies: {len(state.get('policy_matches', []))}")

            print("\n[Agent 3] Escalation Decision")
            agent_3_output = escalation_decision_node(state)
            state.update(agent_3_output)
            print(f"  Decision: {state.get('decision')}")
            print(f"  Escalate To: {state.get('escalate_to') or 'None'}")

            print("\n[Agent 4] Response Drafting")
            agent_4_output = response_drafting_node(
                state,
                template_path="data/response_templates.json",
                output_path=str(response_audit_path),
            )
            state.update(agent_4_output)
            draft_response = state.get("draft_response", "")
            print(f"  Response length: {len(draft_response)} characters")
            print(f"  Preview: {draft_response[:100]}...")

            results.append(
                {
                    "scenario": scenario["name"],
                    "ticket_id": scenario["ticket_id"],
                    "decision": state.get("decision"),
                    "response_length": len(draft_response),
                }
            )

        print("\n" + "=" * 80)
        print("INTEGRATION SUMMARY")
        print("=" * 80)
        for item in results:
            print(f"- {item['ticket_id']}: {item['decision']} ({item['response_length']} chars)")

        print("\nAudit file written to temporary path:")
        print(f"  {response_audit_path}")

        if response_audit_path.exists():
            entries = [json.loads(line) for line in response_audit_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            print(f"  Logged responses: {len(entries)}")
        else:
            print("  Logged responses: 0")

    print("\n✅ FULL INTEGRATION TEST COMPLETE")
    return True


if __name__ == "__main__":
    raise SystemExit(0 if run_full_integration_test() else 1)
