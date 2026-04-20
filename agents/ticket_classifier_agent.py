"""
ticket_classifier_agent.py
---------------------------
Agent 1 — Intent Classification Agent

Responsibilities:
  • Classify the support ticket into a category
  • Detect urgency level
  • Identify sentiment
  • Detect missing information

Flow:
  1. Read  : state["ticket_text"]
  2. Call  : classify_ticket() tool (rule-based, no LLM)
  3. Verify: LLM reviews the tool result and must confirm or override with
             strict JSON output
  4. Write : category | urgency | sentiment | missing_information
             (also copies ticket_text → user_input)
"""

from __future__ import annotations

import json
import os
import re
import sys
import textwrap
from typing import Any, Dict

# Support direct script execution: `python agents/ticket_classifier_agent.py`
if __package__ in (None, ""):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage

from app.state import SupportState
from tools.ticket_classifier_tool import classify_ticket
from tracing.tracer import get_tracer

# ---------------------------------------------------------------------------
# LLM setup — local Ollama, llama3.2, deterministic
# ---------------------------------------------------------------------------
llm = ChatOllama(model="llama3.2", temperature=0)

# Module-level tracer
tracer = get_tracer("ticket_classifier_agent")

# ---------------------------------------------------------------------------
# System prompt — persona-driven, output-constrained
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are an expert Customer Support Triage Analyst.

Your ONLY job is to validate or correct a preliminary classification that was
produced by a deterministic rule-based tool.  You must NOT invent information.

You will receive:
  - The original ticket text
  - A JSON classification from the rule-based tool

Your task:
  1. Check whether the category, urgency, and sentiment are correct.
  2. Check whether the missing_information list is accurate.
  3. If everything is correct, return the classification unchanged.
  4. If something is wrong, correct ONLY the incorrect field(s).

STRICT OUTPUT RULES:
  - Respond with ONLY a valid JSON object — no prose, no markdown fences.
  - Use exactly these keys:
      "category", "urgency", "sentiment", "missing_information"
  - Allowed values:
      category  : damaged_item | refund_request | billing_issue |
                  shipping_issue | technical_issue | account_issue |
                  missing_information | other
      urgency   : low | medium | high
      sentiment : positive | neutral | negative
      missing_information : JSON array of strings (may be empty [])
  - Do NOT add any extra keys or commentary.
  - If unsure, keep the tool's value unchanged.
"""


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> Dict[str, Any]:
    """
    Robustly parse JSON from an LLM response that may contain markdown fences
    or surrounding prose.

    Raises
    ------
    ValueError
        If no valid JSON object can be extracted.
    """
    # Strip markdown fences
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Find the first {...} block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    raise ValueError(f"Could not extract JSON from LLM output:\n{text}")


def _validate_classification(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure required keys are present and values are within allowed sets.
    Falls back to sensible defaults for invalid values rather than crashing.
    """
    valid_categories = {
        "damaged_item", "refund_request", "billing_issue", "shipping_issue",
        "technical_issue", "account_issue", "missing_information", "other",
    }
    valid_urgency = {"low", "medium", "high"}
    valid_sentiment = {"positive", "neutral", "negative"}

    category = data.get("category", "other")
    urgency = data.get("urgency", "medium")
    sentiment = data.get("sentiment", "neutral")
    missing = data.get("missing_information", [])

    return {
        "category": category if category in valid_categories else "other",
        "urgency": urgency if urgency in valid_urgency else "medium",
        "sentiment": sentiment if sentiment in valid_sentiment else "neutral",
        "missing_information": missing if isinstance(missing, list) else [],
    }


def _print_section(title: str) -> None:
    """Render a compact section header."""
    print(f"\n{'=' * 72}")
    print(title)
    print(f"{'=' * 72}")


def _print_kv(label: str, value: Any) -> None:
    """Render key-value output with aligned labels."""
    print(f"  {label:<20}: {value}")


def _print_state_card(result: Dict[str, Any]) -> None:
    """Render a concise final state card for interactive runs."""
    card_lines = [
        f"Category            : {result.get('category')}",
        f"Urgency             : {result.get('urgency')}",
        f"Sentiment           : {result.get('sentiment')}",
        f"Missing Information : {result.get('missing_information')}",
    ]
    width = max(len(line) for line in card_lines) + 4
    print(f"\n+{'-' * width}+")
    for line in card_lines:
        print(f"| {line.ljust(width - 3)}|")
    print(f"+{'-' * width}+")


# ---------------------------------------------------------------------------
# Main agent node
# ---------------------------------------------------------------------------

def ticket_classifier_node(state: SupportState) -> Dict[str, Any]:
    """
    LangGraph node for the Intent Classification Agent.

    Reads
    -----
    state["ticket_text"]

    Writes
    ------
    user_input, category, urgency, sentiment, missing_information

    Parameters
    ----------
    state : SupportState
        The shared graph state dict.

    Returns
    -------
    dict
        Partial state update consumed by LangGraph.
    """
    ticket_id = state.get("ticket_id", "UNKNOWN")
    ticket_text = state.get("ticket_text", "")

    # ------------------------------------------------------------------
    # Step 0 — Log agent input
    # ------------------------------------------------------------------
    tracer.info(
        "AGENT_INPUT",
        extra={
            "ticket_id": ticket_id,
            "ticket_text": ticket_text,
        },
    )
    _print_section(f"Agent 1 - Intent Classification (Ticket: {ticket_id})")
    _print_kv("Input text", textwrap.shorten(ticket_text, width=120, placeholder="..."))

    # ------------------------------------------------------------------
    # Step 1 — Call the custom rule-based tool
    # ------------------------------------------------------------------
    print("[Step 1/3] Running rule-based classifier tool")
    tracer.info("TOOL_CALL", extra={"tool": "classify_ticket", "input": ticket_text})

    try:
        tool_result = classify_ticket(ticket_text)
    except (ValueError, Exception) as exc:
        tracer.error("TOOL_ERROR", extra={"error": str(exc)})
        # Graceful degradation — fill with safe defaults
        tool_result = {
            "category": "other",
            "urgency": "medium",
            "sentiment": "neutral",
            "missing_information": [],
            "confidence": "low",
        }

    tracer.info("TOOL_OUTPUT", extra={"tool_result": tool_result})
    _print_kv("Tool result", tool_result)

    # ------------------------------------------------------------------
    # Step 2 — LLM validation / correction pass
    # ------------------------------------------------------------------
    print("[Step 2/3] Validating with Llama 3.2")

    human_message = HumanMessage(
        content=(
            f"Ticket Text:\n\"\"\"\n{ticket_text}\n\"\"\"\n\n"
            f"Rule-Based Tool Classification (JSON):\n"
            f"{json.dumps(tool_result, indent=2)}\n\n"
            "Validate and return the final classification as a strict JSON object."
        )
    )

    try:
        llm_response = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), human_message])
        final_data = _extract_json(llm_response.content)
        tracer.info("LLM_OUTPUT", extra={"raw": llm_response.content})
    except Exception as exc:
        # LLM failure — fall back to tool output
        tracer.warning(
            "LLM_FALLBACK",
            extra={"reason": str(exc), "fallback": "tool_result"},
        )
        print(f"  [Warning] LLM validation failed ({exc}). Using tool result.")
        final_data = tool_result

    # ------------------------------------------------------------------
    # Step 3 — Validate and sanitise the final output
    # ------------------------------------------------------------------
    validated = _validate_classification(final_data)

    # ------------------------------------------------------------------
    # Step 4 — Build state update
    # ------------------------------------------------------------------
    state_update: Dict[str, Any] = {
        # user_input is a copy of ticket_text (as per spec)
        "user_input": ticket_text,
        "category": validated["category"],
        "urgency": validated["urgency"],
        "sentiment": validated["sentiment"],
        "missing_information": validated["missing_information"],
    }

    # ------------------------------------------------------------------
    # Step 5 — Log final classification and state update
    # ------------------------------------------------------------------
    tracer.info(
        "FINAL_CLASSIFICATION",
        extra={
            "ticket_id": ticket_id,
            "classification": validated,
            "state_keys_written": list(state_update.keys()),
        },
    )

    print("[Step 3/3] Final classification")
    _print_kv("Category", validated["category"])
    _print_kv("Urgency", validated["urgency"])
    _print_kv("Sentiment", validated["sentiment"])
    _print_kv("Missing information", validated["missing_information"])
    _print_kv("State keys written", list(state_update.keys()))

    return state_update


# Backward-compatible alias (in case other modules import under this name)
classify_ticket_node = ticket_classifier_node


def _run_interactive() -> int:
    """Interactive command-line runner for manual Agent 1 checks."""
    _print_section("Agent 1 Interactive Runner")
    print("Describe your support issue")
    user_ticket = input("Enter ticket text: ").strip()

    if not user_ticket:
        print("No ticket text provided. Exiting.")
        return 1

    state: SupportState = {
        "ticket_id": "MANUAL-001",
        "customer_name": "Manual User",
        "ticket_text": user_ticket,
    }

    result = ticket_classifier_node(state)
    _print_state_card(result)
    print("\nJSON output:")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_run_interactive())
