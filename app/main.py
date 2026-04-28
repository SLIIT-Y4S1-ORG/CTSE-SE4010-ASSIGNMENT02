from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict

# Support direct script execution: `python app/main.py`
if __package__ in (None, ""):
	sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.graph import run_workflow
from app.state import SupportState


def main() -> int:
	"""Run the common support workflow demo."""
	sample_state: SupportState = {
		"ticket_id": "TCK-2001",
		"customer_name": "Alice Smith",
		"ticket_text": (
			"Hi, I received my coffee mug today but the handle is completely "
			"shattered. I have attached a picture of the broken mug and the box "
			"it came in. My order number is ORD-5592. I would like my money back."
		),
		"category": "damaged_item",
		"urgency": "medium",
		"sentiment": "neutral",
		"missing_information": [],
	}

	print("Starting support ticket workflow...\n")
	final_state: Dict[str, Any] = run_workflow(sample_state)

	print("\nFinal state:")
	print(json.dumps(final_state, indent=2))
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
