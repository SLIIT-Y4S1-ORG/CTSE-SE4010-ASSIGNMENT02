from app.state import SupportState
from tools.escalation_rules_engine import apply_escalation_rules
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Dict, Any, List

# Use locally running Ollama model (llama3.2)
llm = ChatOllama(model="llama3.2", temperature=0)

def escalation_decision_node(state: SupportState) -> Dict[str, Any]:
    """
    Agent 3: Escalation Decision Agent
    
    Analyzes ticket classification, retrieved policies, and applies escalation rules
    to decide whether to approve, request more info, escalate, or reject.
    
    Takes input from:
    - Agent 1 (Classifier): category, urgency, sentiment, missing_information
    - Agent 2 (Knowledge Retrieval): policy_matches
    
    Outputs:
    - decision: One of ['approve', 'request_more_info', 'escalate_to_X', 'reject', 'escalate_to_human_support']
    - escalate_to: Team name if escalating (e.g., 'billing', 'logistics', 'human_support')
    - next_steps: List of recommended actions
    """
    
    # Extract relevant state information
    ticket_id = state.get("ticket_id", "UNKNOWN")
    customer_name = state.get("customer_name", "UNKNOWN")
    category = state.get("category", "unknown")
    urgency = state.get("urgency", "medium").lower()
    sentiment = state.get("sentiment", "neutral").lower()
    missing_information = state.get("missing_information", [])
    policy_matches = state.get("policy_matches", [])
    ticket_text = state.get("ticket_text", "")
    
    print(f"\n[Agent 3] Processing escalation for ticket {ticket_id}...")
    print(f"  Customer: {customer_name}")
    print(f"  Category: {category}")
    print(f"  Urgency: {urgency}")
    print(f"  Sentiment: {sentiment}")
    print(f"  Missing Info: {missing_information}")
    
    # 1) Apply escalation rules engine to get initial decision
    print("[Agent 3] Applying business rules engine...")
    rule_result = apply_escalation_rules(
        ticket_id=ticket_id,
        customer_name=customer_name,
        category=category,
        urgency=urgency,
        sentiment=sentiment,
        missing_information=missing_information,
        policy_matches=policy_matches,
        ticket_text=ticket_text
    )
    
    print(f"  -> Initial Decision: {rule_result['decision']}")
    print(f"  -> Reason: {rule_result['reason']}")
    
    # 2) Use LLM to validate and refine the decision with reasoning
    print("[Agent 3] Consulting Llama 3.2 for validation...")
    
    system_prompt = SystemMessage(
        content="""
You are a Support Operations Decision Agent. Your job is to validate escalation decisions
and ensure they are justified and consistent with company policy.

You will receive:
1. An initial decision from our rules engine
2. The ticket classification details
3. Retrieved policies

Your task:
- Validate if the INITIAL CLASSIFICATION makes sense for the user's issue.
- If the ticket explicitly mentions fraud, scams, fake goods, or severe pricing complaints, DO NOT ACCEPT an 'approve' decision meant for transit damage. You MUST override it to 'escalate_to_human_support'.
- Validate the decision is correct
- If the rules were misapplied, correct it
- Provide a clear, concise reason for the decision
- List concrete next steps (2-4 items max)

IMPORTANT:
- Only approve decisions backed by policy
- Escalate conservatively when uncertain or when severe issues like scams are alleged
- Never invent rules
- Keep reasoning concise and actionable

Available decisions:
- 'approve' (auto-resolve with policy support)
- 'request_more_info' (ask customer for missing data)
- 'escalate_to_billing' (route to billing team)
- 'escalate_to_logistics' (route to logistics/shipping)
- 'escalate_to_human_support' (route to human supervisor)
- 'reject' (deny per policy)

Return ONLY a valid JSON object containing exactly these keys:
- "decision": The final decision string from the available options
- "reason": A short string explaining why
- "next_steps": A list of short strings describing next actions
"""
    )
    
    policy_context = "\n".join([f"- {p}" for p in policy_matches]) if policy_matches else "No matching policies found"
    
    human_prompt = HumanMessage(
        content=f"""
Ticket ID: {ticket_id}
Category: {category}
Urgency: {urgency}
Sentiment: {sentiment}
Missing Info: {missing_information if missing_information else "None"}

Retrieved Policies:
{policy_context}

Ticket Text: "{ticket_text}"

Initial Decision from Rules Engine:
Decision: {rule_result['decision']}
Reason: {rule_result['reason']}

Please validate this decision and provide your final recommendation.
"""
    )
    
    # 3) Invoke LLM for validation
    ai_response = llm.invoke([system_prompt, human_prompt])
    
    print(f"   -> AI Validation: {ai_response.content}")
    
    # 4) Parse and structure the final decision
    decision_text = rule_result['decision']
    escalate_to = rule_result['escalate_to']
    next_steps = rule_result['next_steps']
    reason = rule_result['reason']

    import json
    import re
    # Try to extract JSON from LLM response
    try:
        clean_content = ai_response.content.strip()
        # Remove markdown formatting if present
        clean_content = re.sub(r"^```(?:json)?", "", clean_content).strip()
        clean_content = re.sub(r"```$", "", clean_content).strip()
        
        parsed_llm = None
        try:
            parsed_llm = json.loads(clean_content)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", clean_content, flags=re.DOTALL)
            if match:
                parsed_llm = json.loads(match.group(0))

        if parsed_llm:
            # Override rules engine if LLM provided valid response
            if 'decision' in parsed_llm and parsed_llm['decision'] in [
                'approve', 'request_more_info', 'escalate_to_billing', 
                'escalate_to_logistics', 'escalate_to_human_support', 'reject'
            ]:
                decision_text = parsed_llm['decision']
                
                # Map specific escalations
                if decision_text in ['escalate_to_billing', 'escalate_to_logistics', 'escalate_to_human_support']:
                    escalate_to = decision_text.replace('escalate_to_', '')
                elif decision_text in ['approve', 'reject', 'request_more_info']:
                    escalate_to = None

            if 'next_steps' in parsed_llm and isinstance(parsed_llm['next_steps'], list):
                next_steps = parsed_llm['next_steps']
            if 'reason' in parsed_llm:
                reason = parsed_llm['reason']

    except Exception as e:
        print(f"   -> Could not parse LLM validation JSON (falling back to initial decision). Error: {e}")
    
    # Validate escalate_to field has correct team name
    valid_escalations = ['billing', 'logistics', 'human_support', 'human_supervisor']
    if escalate_to and escalate_to not in valid_escalations:
        escalate_to = 'human_support'  # Default fallback
    
    # Return the decision in the expected format
    return {
        "decision": decision_text,
        "escalate_to": escalate_to,
        "next_steps": next_steps
    }


# Backward-compatible alias if other modules import this differently
escalation_node = escalation_decision_node