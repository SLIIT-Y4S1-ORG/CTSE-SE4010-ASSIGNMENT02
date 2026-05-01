from __future__ import annotations

import os
import sys
from typing import Any, Dict, Optional

# Ensure package imports work when running as a script
if __package__ in (None, ""):
	sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.state import SupportState

# LangGraph is an optional dependency; import lazily to avoid hard failure
try:
	from langgraph.graph import StateGraph, START, END  # type: ignore
except Exception:  # pragma: no cover - optional import
	StateGraph = None  # type: ignore
	START = None
	END = None


def _get_ticket_classifier_node():
	try:
		from agents.ticket_classifier_agent import ticket_classifier_node

		return ticket_classifier_node
	except Exception:
		return None


def _get_knowledge_retrieval_node():
	from agents.knowledge_retrieval_agent import knowledge_retrieval_node

	return knowledge_retrieval_node


def _get_escalation_node():
	try:
		from agents.escalation_decision_agent import escalation_decision_node

		return escalation_decision_node
	except Exception:
		return None


def _get_response_drafting_node():
	from agents.response_drafting_agent import response_drafting_node

	return response_drafting_node


_compiled_app: Optional[Any] = None


def build_langraph_app():
	"""Build and compile a LangGraph StateGraph for Agents 1→4.

	Returns a compiled workflow app when `langgraph` is available, otherwise raises ImportError.
	"""
	if StateGraph is None:
		raise ImportError("langgraph is not available in this environment")

	graph = StateGraph(SupportState)

	graph.add_node("agent_1", _get_ticket_classifier_node())
	graph.add_node("agent_2", _get_knowledge_retrieval_node())
	graph.add_node("agent_3", _get_escalation_node())
	graph.add_node("agent_4", _get_response_drafting_node())

	graph.add_edge(START, "agent_1")
	graph.add_edge("agent_1", "agent_2")
	graph.add_edge("agent_2", "agent_3")
	graph.add_edge("agent_3", "agent_4")
	graph.add_edge("agent_4", END)

	return graph.compile()


def get_langraph_app():
	global _compiled_app
	if _compiled_app is None:
		_compiled_app = build_langraph_app()
	return _compiled_app


def run_langraph_workflow(state: SupportState) -> Dict[str, Any]:
	"""Invoke the compiled LangGraph workflow and return the resulting state dict.

	This function is safe to call even when some agents are missing — LangGraph will
	execute None nodes as no-ops if the node function is `None`.
	"""
	app = get_langraph_app()
	result = app.invoke(state)
	return dict(result)


__all__ = ["build_langraph_app", "get_langraph_app", "run_langraph_workflow"]

