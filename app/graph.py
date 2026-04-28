from __future__ import annotations

import os
import sys
from typing import Dict, Any

# Support direct script execution/imports from `python app/main.py`
if __package__ in (None, ""):
	sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.state import SupportState
from agents.knowledge_retrieval_agent import knowledge_retrieval_node


def run_knowledge_retrieval_workflow(state: SupportState) -> SupportState:
		"""
		Run the Agent 2 knowledge retrieval step and merge its output into state.

		This is the part owned by the knowledge retrieval agent. It expects the
		incoming state to already contain at least:
			- ticket_text
			- category
		"""
		updated_state: SupportState = dict(state)
		retrieval_update: Dict[str, Any] = knowledge_retrieval_node(updated_state)
		updated_state.update(retrieval_update)
		return updated_state


def run_workflow(state: SupportState) -> SupportState:
		"""
		Current workflow entry point.

		For now, the repository only has the knowledge retrieval step wired up,
		so this simply runs Agent 2 and returns the merged state.
		"""
		return run_knowledge_retrieval_workflow(state)


__all__ = ["run_knowledge_retrieval_workflow", "run_workflow"]
