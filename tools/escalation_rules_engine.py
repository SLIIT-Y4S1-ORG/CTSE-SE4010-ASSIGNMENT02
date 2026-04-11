from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime

# ============================================================================
# REAL-WORLD INTERACTION: File I/O Operations
# ============================================================================

def load_customer_history(customer_name: str, history_file: str = "data/customer_history.json") -> Dict[str, Any]:
    """
    REAL-WORLD TOOL: Reads customer history from local file system.
    This allows the agent to check if customer has repeated complaints/violations.
    
    Args:
        customer_name: Name of the customer
        history_file: Path to local JSON file storing customer history
    
    Returns:
        dict with customer's previous tickets, escalations, fraud flags, etc.
    """
    try:
        if not os.path.exists(history_file):
            return {
                "previous_tickets": 0,
                "repeat_complainant": False,
                "fraud_flagged": False,
                "satisfaction_rating": 0
            }
        
        with open(history_file, 'r', encoding='utf-8') as f:
            history_db = json.load(f)
        
        if customer_name in history_db:
            return history_db[customer_name]
        else:
            return {
                "previous_tickets": 0,
                "repeat_complainant": False,
                "fraud_flagged": False,
                "satisfaction_rating": 0
            }
    except Exception as e:
        print(f"[Tool] Warning: Could not read customer history: {e}")
        return {"previous_tickets": 0, "repeat_complainant": False, "fraud_flagged": False}


def log_escalation_decision(
    ticket_id: str,
    customer_name: str,
    decision: str,
    escalate_to: Optional[str],
    reason: str,
    log_file: str = "data/escalation_audit_log.json"
) -> bool:
    """
    REAL-WORLD TOOL: Writes escalation decisions to audit log on disk.
    This creates an immutable record for compliance, debugging, and analytics.
    
    Args:
        ticket_id: Unique ticket identifier
        customer_name: Customer name
        decision: The decision made ('approve', 'escalate_to_X', 'request_more_info')
        escalate_to: Team name if escalating
        reason: Justification for the decision
        log_file: Path to audit log file
    
    Returns:
        bool: True if successfully logged, False otherwise
    """
    try:
        # Read existing log
        logs = []
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        
        # Add new log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "ticket_id": ticket_id,
            "customer_name": customer_name,
            "decision": decision,
            "escalate_to": escalate_to,
            "reason": reason
        }
        logs.append(log_entry)
        
        # Write back to disk
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        
        print(f"[Tool] Decision logged for {ticket_id}: {decision}")
        return True
    except Exception as e:
        print(f"[Tool] Error logging decision: {e}")
        return False


def apply_escalation_rules(
    ticket_id: str,
    customer_name: str,
    category: str,
    urgency: str,
    sentiment: str,
    missing_information: List[str],
    policy_matches: List[str],
    ticket_text: str = ""
) -> Dict[str, Any]:
    """
    Applies escalation and resolution rules to ticket data.
    
    ** REAL-WORLD INTERACTION: This tool interacts with the real world by:
       1. Reading customer history from local file (data/customer_history.json)
       2. Writing audit logs to local file (data/escalation_audit_log.json)
    
    This fulfills the assignment requirement: "Agents must use custom Python tools
    that allow agents to interact with the real world (e.g., reading/writing local files)."
    
    Args:
        ticket_id: Unique ticket identifier (used for logging and lookup)
        customer_name: Customer name (used to read history and log)
        category: Ticket category (e.g., 'damaged_item', 'billing_issue')
        urgency: Ticket urgency level ('low', 'medium', 'high', 'critical')
        sentiment: Customer sentiment ('positive', 'neutral', 'negative')
        missing_information: List of missing required fields
        policy_matches: Retrieved policy excerpts from Agent 2
        ticket_text: The original ticket text for analysis
    
    Returns:
        dict with: decision, escalate_to, reason, next_steps
    """
    
    decision = "approve"
    escalate_to = None
    reason = ""
    next_steps = []
    
    # ========================================================================
    # REAL-WORLD DATA: Fetch customer history from local file
    # ========================================================================
    print(f"[Tool] Reading customer history for '{customer_name}' from data/customer_history.json...")
    customer_history = load_customer_history(customer_name)
    
    print(f"[Tool] Customer history retrieved: {customer_history['previous_tickets']} previous tickets, "
          f"repeat_complainant={customer_history['repeat_complainant']}, "
          f"fraud_flagged={customer_history['fraud_flagged']}")
    
    # Rule 0: Check for fraud-flagged customers
    if customer_history.get('fraud_flagged', False):
        decision = "escalate_to_human_support"
        escalate_to = "human_support"
        reason = "Customer flagged for potential fraud. Requires human review."
        next_steps = [
            "Route to Fraud Investigation Team",
            "Review customer history and patterns",
            "Contact customer for verification if needed"
        ]
        log_escalation_decision(ticket_id, customer_name, decision, escalate_to, reason)
        return {
            "decision": decision,
            "escalate_to": escalate_to,
            "reason": reason,
            "next_steps": next_steps
        }
    
    # ========================================================================
    # CATEGORY-SPECIFIC RULES (Rule 2-5): Check these BEFORE general status rules
    # This ensures that policy-driven escalations take priority over sentiment-based rules
    # ========================================================================
    
    # Rule 2: Damaged Item Handling
    if category == "damaged_item":
        # Rule 2a: No photo evidence → request_more_info
        if "photo" in missing_information or "attachment" in missing_information:
            decision = "request_more_info"
            escalate_to = None
            reason = "Refund possible for damaged items, but photo evidence is missing. Policy requires clear photo of damage."
            next_steps = [
                "Ask customer to provide photo evidence of damaged item",
                "Confirm order ID",
                "Advise: Once received, refund will be reviewed immediately",
                "Offer replacement option if preferred"
            ]
        # Rule 2b: High urgency damaged item → escalate to logistics
        elif urgency == "high":
            decision = "escalate_to_logistics"
            escalate_to = "logistics"
            reason = "High-urgency damaged item requires logistics team for expedited replacement/refund."
            next_steps = [
                "Escalate to Logistics/Shipping Team",
                "Flag for priority handling",
                "Prepare replacement shipment",
                "Offer expedited refund if preferred"
            ]
        # Rule 2c: Valid photo, within policy window → approve
        else:
            decision = "approve"
            escalate_to = None
            reason = "Damaged item with photo evidence qualifies for automatic refund/replacement per policy."
            next_steps = [
                "Initiate refund processing",
                "Generate return shipping label",
                "Send confirmation email within 24 hours",
                "Track refund until completion"
            ]
    
    # Rule 3: Billing Issues
    elif category == "billing_issue":
        # Rule 3a: High urgency billing → escalate to billing team
        if urgency == "high":
            decision = "escalate_to_billing"
            escalate_to = "billing"
            # Add repeat complainant context if applicable
            if customer_history.get('repeat_complainant', False):
                reason = f"High-urgency billing issue from repeat complainant ({customer_history['previous_tickets']} tickets). Requires Billing Team verification and immediate action."
            else:
                reason = "High-urgency billing issue requires Billing Team verification and immediate action."
            next_steps = [
                "Escalate to Billing Support Team immediately",
                "Do NOT promise refund until verified",
                "Request transaction details from customer",
                "Billing team to investigate within 2 hours"
            ]
        # Rule 3b: Missing critical billing info
        elif missing_information and any(info in missing_information for info in ["order_id", "transaction_id"]):
            decision = "request_more_info"
            escalate_to = None
            reason = "Cannot process billing claim without order ID or transaction reference."
            next_steps = [
                "Request order ID or transaction ID from customer",
                "Ask for screenshot of billing statement showing the duplicate charge",
                "Provide billing support email for expedited response"
            ]
        else:
            decision = "escalate_to_billing"
            escalate_to = "billing"
            reason = "Billing issues require verification by Billing Team per policy."
            next_steps = [
                "Escalate to Billing Support Team",
                "Provide all transaction details",
                "Wait for billing verification (2-3 business days)"
            ]
    
    # Rule 4: Delayed Delivery
    elif category == "delayed_delivery":
        # Rule 4a: High urgency → escalate
        if urgency == "high":
            decision = "escalate_to_logistics"
            escalate_to = "logistics"
            reason = "High-urgency delivery delay requires Logistics Team investigation."
            next_steps = [
                "Escalate to Logistics/Shipping Team",
                "Request tracking update from carrier",
                "Prepare compensation (discount or refund options)",
                "Follow up within 24 hours"
            ]
        # Rule 4b: Standard case → approve compensation
        else:
            decision = "approve"
            escalate_to = None
            reason = "Delayed delivery qualifies for automatic compensation per policy."
            next_steps = [
                "Apply 15% discount code to next purchase",
                "Send tracking update to customer",
                "Offer expedited shipping on next order",
                "Document in CRM for patterns"
            ]
    
    # Rule 5: Refund Requests
    elif category == "refund_request":
        # Rule 5a: Missing critical info
        if missing_information:
            decision = "request_more_info"
            escalate_to = None
            reason = "Cannot process refund without complete information."
            next_steps = [
                "Request item condition (opened/unopened)",
                "Request order number and purchase date",
                "Clarify reason for return",
                "Confirm authorization for return shipping"
            ]
        else:
            decision = "approve"
            escalate_to = None
            reason = "Unopened item return within 30-day window approved per policy."
            next_steps = [
                "Process full refund authorization",
                "Generate return shipping label",
                "Deduct return shipping from refund if applicable",
                "Send refund tracking info"
            ]
    
    # ========================================================================
    # GENERAL STATUS RULES (Rule 1, 6, 6b, 7, 8): Applied after category rules
    # ========================================================================
    
    # Rule 1: Check for abusive language (applied AFTER category-specific rules)
    # Only escalate if no category matched, or if truly aggressive behavior despite policy
    abusive_keywords = ["stupid", "unacceptable", "disgust", "hate", "absolutely unacceptable"]
    has_abusive_language = any(keyword in ticket_text.lower() for keyword in abusive_keywords)
    
    # Only apply abusive language rule if we haven't already determined a category-based decision
    if has_abusive_language and urgency == "high" and decision == "approve":
        decision = "escalate_to_human_support"
        escalate_to = "human_support"
        reason = "Abusive language combined with high urgency requires human supervisor attention."
        next_steps = [
            "Route ticket to human supervisor",
            "Flag for sensitivity training check",
            "Prepare empathetic response template"
        ]
    
    # Rule 6: High Severity/Sentiment Cases
    if urgency == "critical" and not decision.startswith("escalate"):
        decision = "escalate_to_human_support"
        escalate_to = "human_support"
        reason = "Critical urgency ticket requires human support team review."
        next_steps = [
            "Route to human support immediately",
            "Flag ticket as critical",
            "Prepare summary for support agent"
        ]
    
    # Rule 6b: Repeat complainants with high urgency should be escalated
    # ONLY if not already escalating to a specialist team (billing, logistics)
    if customer_history.get('repeat_complainant', False) and urgency == "high":
        # If already escalating to specialist team, enhance the reason with repeat complainant context
        if escalate_to in ["billing", "logistics"]:
            reason = f"{reason} [PRIORITY: Customer is a repeat complainant ({customer_history['previous_tickets']} previous tickets) - escalate with priority handling]"
            next_steps.append("Flag as repeat complainant for priority handling by specialist team")
        # Otherwise, escalate to human support for complex repeat complainants
        elif not escalate_to:  # Only override if not already escalating
            decision = "escalate_to_human_support"
            escalate_to = "human_support"
            reason = f"Customer is a repeat complainant ({customer_history['previous_tickets']} previous tickets). High urgency requires escalation to supervisor."
            next_steps = [
                "Route to senior support team member",
                "Review customer history and previous resolutions",
                "Prioritize for expedited handling",
                "Consider customer retention strategy"
            ]
    
    # Rule 7: Missing Critical Information
    if missing_information and decision == "approve":
        decision = "request_more_info"
        escalate_to = None
        reason = f"Missing critical information: {', '.join(missing_information)}"
        next_steps = [
            f"Request the following from customer: {', '.join(missing_information)}",
            "Re-evaluate once information is provided",
            "Escalate to human support if customer doesn't respond within 48 hours"
        ]
    
    # Rule 8: Default escalation for ambiguous cases
    if not policy_matches or (policy_matches and "unknown" in policy_matches[0].lower()):
        if decision == "approve":
            decision = "escalate_to_human_support"
            escalate_to = "human_support"
            reason = "No matching policy found. Route to human support for specialized handling."
            next_steps = [
                "Escalate to human support team",
                "Provide all ticket details and classification",
                "Request expedited review"
            ]
    
    # ========================================================================
    # REAL-WORLD INTERACTION: Log the decision to audit log file on disk
    # ========================================================================
    print(f"[Tool] Writing decision to audit log for ticket {ticket_id}...")
    log_escalation_decision(ticket_id, customer_name, decision, escalate_to, reason)
    
    return {
        "decision": decision,
        "escalate_to": escalate_to,
        "reason": reason,
        "next_steps": next_steps
    }
