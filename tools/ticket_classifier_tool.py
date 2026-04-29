import random
from typing import Any, Callable


def _next_ticket_id() -> str:
    return f"TCK-{random.randint(1, 9999):04d}"


def collect_ticket_input() -> dict[str, str]:
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


def log_classification_result(ticket_id: str, customer_name: str, classification: dict[str, Any]) -> None:
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


def run_ticket_classification_flow(classify_fn: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    print("\n" + "=" * 50)
    print("    Agent 1: Intent Classification Agent")
    print("=" * 50 + "\n")

    request = collect_ticket_input()
    classification = classify_fn({"ticket_text": request["ticket_text"]})

    result = {
        "ticket_id": request["ticket_id"],
        "customer_name": request["customer_name"],
        "ticket_text": request["ticket_text"],
        "classification": classification,
    }

    log_classification_result(request["ticket_id"], request["customer_name"], classification)
    return result