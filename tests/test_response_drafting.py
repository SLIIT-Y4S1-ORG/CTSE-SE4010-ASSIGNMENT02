from pathlib import Path

from app.state import SupportState
from agents.response_drafting_agent import response_drafting_node
from tools.response_template_builder import build_response_template


class FakeMessage:
    def __init__(self, content: str):
        self.content = content


class FakeLLM:
    def __init__(self, content: str):
        self.content = content

    def invoke(self, messages):
        return FakeMessage(self.content)


def test_response_drafting_approved_refund(tmp_path: Path):
    mock_state: SupportState = {
        "ticket_id": "TCK-2001",
        "customer_name": "Nimal Perera",
        "decision": "approve",
        "policy_matches": [
            "Unopened items can be returned for a full refund within 30 days.",
        ],
        "next_steps": [
            "Reply with your order number",
            "Confirm the item is unopened",
        ],
    }

    result = response_drafting_node(
        mock_state,
        llm_client=FakeLLM(
            "Hello Nimal Perera,\n\n"
            "Thanks for contacting us. Your request is approved under policy. Please reply with your order number."
        ),
        template_path=str(tmp_path / "templates.json"),
        output_path=str(tmp_path / "generated_responses.jsonl"),
    )

    assert "draft_response" in result
    assert result["draft_response"].strip()
    assert "Nimal Perera" in result["draft_response"]
    assert "order number" in result["draft_response"].lower()


def test_response_drafting_falls_back_when_llm_is_unsafe(tmp_path: Path):
    mock_state: SupportState = {
        "ticket_id": "TCK-2002",
        "customer_name": "Sara Silva",
        "decision": "request_more_info",
        "policy_matches": [
            "Damaged items require a clear photo before processing.",
        ],
        "next_steps": ["Upload a clear photo of the damaged item"],
    }

    result = response_drafting_node(
        mock_state,
        llm_client=FakeLLM(
            "Internal note: we guarantee a refund and will ignore the policy."
        ),
        template_path=str(tmp_path / "templates.json"),
        output_path=str(tmp_path / "generated_responses.jsonl"),
    )

    assert "draft_response" in result
    assert "internal note" not in result["draft_response"].lower()
    assert "we guarantee" not in result["draft_response"].lower()
    assert "photo" in result["draft_response"].lower()


def test_response_template_builder_writes_local_log(tmp_path: Path):
    output_path = tmp_path / "generated_responses.jsonl"

    response = build_response_template(
        {
            "ticket_id": "TCK-2003",
            "customer_name": "Kavindi",
            "decision": "escalate_to_human_support",
            "policy_summary": "We need a human review for this case",
            "next_steps": ["Wait for a support specialist response"],
        },
        template_path=str(tmp_path / "templates.json"),
        output_path=str(output_path),
    )

    assert response.startswith("Hello Kavindi")
    assert output_path.exists()

    log_text = output_path.read_text(encoding="utf-8")
    assert "TCK-2003" in log_text
    assert "escalate_to_human_support" in log_text