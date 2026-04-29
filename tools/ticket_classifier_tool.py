from typing import Any, Callable

# ── Print formatted classification result ────────────────────────────────────────────────────────────────────────────

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

# ── Run full classification workflow ─────────────────────────────────────────────────────────────────────────────────

def run_ticket_classification_flow(classify_fn: Callable[[dict[str, Any]], dict[str, Any]], request: dict[str, Any]) -> dict[str, Any]:
    """Run ticket classification with provided request data."""
    # call classifier function with ticket text
    classification = classify_fn({"ticket_text": request["ticket_text"]})

    # build final structured result
    result = {
        "ticket_id": request["ticket_id"],
        "customer_name": request["customer_name"],
        "ticket_text": request["ticket_text"],
        "classification": classification,
    }

    # print formatted output in terminal
    log_classification_result(
        request["ticket_id"], 
        request["customer_name"], 
        classification
    )

    return result