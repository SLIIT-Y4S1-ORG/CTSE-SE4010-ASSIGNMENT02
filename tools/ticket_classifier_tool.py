import json    # Used for parsing JSON strings into Python dictionaries
import re    # Used for regular expressions to clean up LLM output
from pathlib import Path    # Used to construct file paths in a platform-independent way

# Path to the shared ticket dataset
TICKETS_FILE = Path(__file__).resolve().parents[1] / "data" / "tickets.json"


def read_ticket_from_file(ticket_id: str) -> dict | None:    # Reads the ticket dataset from a local JSON file and searches for a ticket with the given ID. Returns the ticket data as a dictionary if found, or None if not found or if the file doesn't exist.  

    if not TICKETS_FILE.exists():
        return None

    with TICKETS_FILE.open("r", encoding="utf-8") as f:
        tickets = json.load(f)

    # Search for the ticket with the matching ID
    for ticket in tickets:
        if ticket.get("ticket_id") == ticket_id:
            return ticket

    return None


def log_classification_result(ticket_id: str, customer_name: str, classification: dict) -> None:    # Logs the classification result to the terminal in a clean, readable format. This is a custom "tool" function that the agent can call to output results.

    missing = classification.get("missing_information", [])

    print("\n" + "=" * 50)
    print("  CLASSIFICATION RESULT")
    print("=" * 50)
    print(f"  Ticket ID            : {ticket_id}")
    print(f"  Customer             : {customer_name}")
    print(f"  Category             : {classification.get('category')}")
    print(f"  Urgency              : {classification.get('urgency')}")
    print(f"  Sentiment            : {classification.get('sentiment')}")
    print(f"  Missing Information  : {', '.join(missing) if missing else 'None'}")
    print("=" * 50 + "\n")