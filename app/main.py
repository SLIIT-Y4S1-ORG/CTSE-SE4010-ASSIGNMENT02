from __future__ import annotations

import json
import os
import sys
import random
from typing import Any, Dict

# Support direct script execution: `python app/main.py`
if __package__ in (None, ""):
	sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.graph import run_workflow
from app.state import SupportState

def _next_ticket_id() -> str:
	"""Generate a unique ticket ID."""
	return f"TCK-{random.randint(1, 9999):04d}"

def collect_user_input() -> dict:
	"""Collect user input for ticket creation."""
	customer_name = ""
	while not customer_name:
		customer_name = input("Enter Your Name            : ").strip()

	ticket_text = ""
	while not ticket_text:
		ticket_text = input("Enter Your Support Issue   : ").strip()

	ticket_id = _next_ticket_id()
	return {
		"ticket_id": ticket_id,
		"customer_name": customer_name,
		"ticket_text": ticket_text,
	}

def main() -> int:
	"""Run the support workflow with user input."""
	print("\n" + "*" * 70)
	print("\nWelcome to Multi-Agent Customer Support System\n")
	print("*" * 70 + "\n")

	# Collect user input at runtime
	user_input = collect_user_input()

	# Create initial state with user input
	initial_state: SupportState = {
		"ticket_id": user_input["ticket_id"],
		"customer_name": user_input["customer_name"],
		"ticket_text": user_input["ticket_text"],
	}

	print("\nStarting support ticket workflow...\n")
	final_state: Dict[str, Any] = run_workflow(initial_state)

	print("\nFinal state:")
	print(json.dumps(final_state, indent=2))
	return 0

if __name__ == "__main__":
	raise SystemExit(main())