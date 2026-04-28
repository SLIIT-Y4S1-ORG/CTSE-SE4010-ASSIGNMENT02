"""
Demo: Agent 1 (Intent Classifier) running on sample tickets.

Run this to see the classifier in action with Ollama.
Make sure Ollama is running: ollama run llama3.2:3b
"""
from pathlib import Path
import sys
import json

# Add project root to path
_PROJECT_ROOT = Path(__file__).resolve().parent
if str(_PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(_PROJECT_ROOT))

from agents.ticket_classifier_agent import ticket_classifier_node
from app.state import SupportState


def demo_classify_tickets() -> None:
	"""Load sample tickets from data/tickets.json and classify each one."""
	tickets_file = _PROJECT_ROOT / "data" / "tickets.json"
	
	if not tickets_file.exists():
		print(f"Error: {tickets_file} not found")
		return
	
	with tickets_file.open("r") as f:
		tickets = json.load(f)
	
	print("=" * 70)
	print("AGENT 1 - INTENT CLASSIFICATION DEMO")
	print("=" * 70)
	
	for ticket in tickets:
		ticket_id = ticket.get("ticket_id", "UNKNOWN")
		customer_name = ticket.get("customer_name", "UNKNOWN")
		ticket_text = ticket.get("text", "")
		expected_behavior = ticket.get("expected_behavior", "")
		
		print(f"\n{'='*70}")
		print(f"Ticket: {ticket_id} | Customer: {customer_name}")
		print(f"Expected Behavior: {expected_behavior}")
		print(f"-" * 70)
		print(f"Text: {ticket_text[:100]}...")
		print(f"-" * 70)
		
		# Prepare state
		state: SupportState = {
			"ticket_id": ticket_id,
			"customer_name": customer_name,
			"ticket_text": ticket_text,
		}
		
		# Run classifier
		result = ticket_classifier_node(state)
		
		# Print result
		print(f"CLASSIFICATION RESULT:")
		print(f"  Category:              {result.get('category', 'N/A')}")
		print(f"  Urgency:               {result.get('urgency', 'N/A')}")
		print(f"  Sentiment:             {result.get('sentiment', 'N/A')}")
		missing = result.get('missing_information', [])
		print(f"  Missing Information:   {', '.join(missing) if missing else 'None'}")
	
	print(f"\n{'='*70}")
	print("DEMO COMPLETE")
	print(f"{'='*70}")


if __name__ == "__main__":
	try:
		demo_classify_tickets()
	except Exception as exc:
		print(f"Error running demo: {exc}")
		print("\nMake sure Ollama is running:")
		print("  ollama run llama3.2:3b")
		import traceback
		traceback.print_exc()
