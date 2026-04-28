import json    # Used to parse the LLM's JSON response into a Python dictionary
import re    # Used to clean up the LLM response (e.g. remove markdown code fences)

from langchain_core.messages import HumanMessage, SystemMessage    # Two types of chat messages sent to the LLM
from langchain_ollama import ChatOllama    # Connects to Ollama running locally on your machine

from app.state import SupportState    # The shared state object that holds all ticket information and classification results
from tools.ticket_classifier_tool import read_ticket_from_file, log_classification_result    # Custom tools for reading tickets and logging results to terminal

# ── LLM setup ─────────────────────────────────────────────────────────────────
llm = ChatOllama(model="llama3.2", temperature=0)    # Using local Llama 3.2 with zero temperature for deterministic output


# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = SystemMessage(    
    content=(
        "You are an expert customer support ticket classifier.\n\n"

        "Analyze the given support ticket and return ONLY a valid JSON object with these exact keys:\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "1. category — PRIORITY ORDER (use the FIRST rule that matches):\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "   → 'refund_request'      if customer explicitly says 'refund', 'money back', 'return my money'\n"
        "   → 'billing_issue'       if customer mentions double charge, wrong charge, or billing error\n"
        "   → 'damaged_item'        if customer says item arrived broken, shattered, or damaged\n"
        "   → 'shipping_issue'      if customer asks where their package is or says it hasn't arrived\n"
        "   → 'account_issue'       if customer can't log in, account is locked, or needs access help\n"
        "   → 'technical_issue'     if customer reports an app crash, bug, or software error\n"
        "   → 'missing_information' if the ticket is too vague to understand (e.g. just 'Help')\n"
        "   → 'general_inquiry'     for anything else\n\n"
        "   IMPORTANT: 'refund_request' takes priority. Even if an item was damaged or wrong,\n"
        "   if the customer's primary ask is a refund, classify as 'refund_request'.\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "2. urgency — Choose ONE from [low, medium, high]:\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "   → 'high'   ONLY if the customer uses explicitly urgent language such as: 'immediately',\n"
        "               'right now', 'fix it now', 'urgent', 'ASAP', 'emergency'.\n"
        "               Also 'high' for: confirmed double charge, broken device preventing all use,\n"
        "               or account locked with active business impact.\n"
        "   → 'medium' for most real issues — including app crashes, refund requests, shipping delays,\n"
        "               wrong products, or complaints stated in a calm or factual tone.\n"
        "               Use 'medium' when the issue is legitimate but no urgent language is present.\n"
        "   → 'low'    only if the ticket is vague, speculative, or clearly non-urgent.\n\n"
        "   IMPORTANT: Do NOT upgrade urgency based on the severity of the issue alone.\n"
        "   Only upgrade to 'high' if the customer's OWN words express urgency.\n"
        "   A factual complaint (e.g. 'the app crashes', 'I want a refund') is 'medium', not 'high'.\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "3. sentiment — Choose ONE from [positive, neutral, negative]:\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "   → 'negative' ONLY if the customer uses emotionally charged language: 'frustrated',\n"
        "               'angry', 'terrible', 'horrible', 'unacceptable', 'disgusted', 'worst'.\n"
        "   → 'neutral'  if the tone is factual, matter-of-fact, or straightforwardly requesting help.\n"
        "               This includes complaints stated calmly without emotional language.\n"
        "               Examples: 'the app keeps crashing', 'I want a refund', 'the product was wrong'.\n"
        "   → 'positive' if the customer is polite, thankful, or complimentary.\n\n"
        "   IMPORTANT: Do NOT classify a ticket as 'negative' just because the situation is bad.\n"
        "   Only use 'negative' when the customer's TONE is emotionally charged or hostile.\n"
        "   A calm factual complaint is always 'neutral'.\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "4. missing_information — List absent but required fields:\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "   Choose from: [order_id, account_email, product_details, evidence_attachment]\n\n"
        "   → Add 'order_id'            ONLY if category is shipping_issue, billing_issue,\n"
        "                                refund_request, or damaged_item.\n"
        "                                Scan the ticket text for any order number pattern\n"
        "                                (e.g. ORD-1234, order #5678, #ORD-9988).\n"
        "                                If an order number IS found in the text, do NOT add 'order_id'.\n"
        "                                ONLY add 'order_id' if no order number is found.\n"
        "                                For all other categories (technical_issue, account_issue,\n"
        "                                general_inquiry, etc.), NEVER add 'order_id'.\n\n"
        "   → Add 'account_email'       ONLY if category is account_issue.\n"
        "                                Scan the ticket text for any email address (e.g. user@example.com).\n"
        "                                If an email IS found in the text, do NOT add 'account_email'.\n"
        "                                ONLY add 'account_email' if no email address is found.\n"
        "                                For all other categories, NEVER add 'account_email'.\n\n"
        "   → Add 'product_details'     if the ticket is so vague that you cannot identify what product\n"
        "                                or issue the customer is referring to (e.g. ticket just says 'Help').\n\n"
        "   → Add 'evidence_attachment' if category is damaged_item and the customer does NOT mention\n"
        "                                a photo, image, screenshot, or any attached proof.\n\n"
        "   → Return []                 when all required information is clearly present in the ticket text.\n\n"

        "Return ONLY the raw JSON object. No explanation, no markdown, no extra text."
    )
)


def _build_human_prompt(customer_name: str, ticket_text: str) -> HumanMessage:    # Create the human message prompt with the customer's name and ticket text to send to the LLM
    
    return HumanMessage(
        content=(
            f"Customer Name: {customer_name}\n"
            f"Ticket Text: {ticket_text}\n\n"
            "Classify this ticket now."
        )
    )


def _parse_llm_output(raw: str) -> dict:    # Clean the raw LLM output to extract the JSON string, then parse it into a Python dictionary
    
    clean = raw.strip()
    clean = re.sub(r"^```(?:json)?", "", clean).strip()
    clean = re.sub(r"```$", "", clean).strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", clean, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError(f"Could not parse LLM output as JSON:\n{raw}")


def ticket_classifier_node(state: SupportState) -> dict:    # The main function for this agent node. It takes the shared SupportState as input and returns a dictionary with the classification results that this agent is responsible for.

    # ── Step 1: Read inputs from state ────────────────────────────────────────
    ticket_id     = state.get("ticket_id", "UNKNOWN")
    customer_name = state.get("customer_name", "Unknown Customer")
    ticket_text   = state.get("ticket_text", "")

    print(f"\n[Agent] Classification started")

    # ── Step 2: Use custom tool — read ticket from local file ─────────────────
    file_ticket = read_ticket_from_file(ticket_id)
    if file_ticket:
        print(f"[Tool] Ticket {ticket_id} found in local file.")
        print(f"[Tool] Ticket confirmed in local dataset.")
    else:
        print(f"[Tool] Ticket {ticket_id} NOT found in local file.")
        print(f"[Tool] Ticket not in dataset. Using state input directly.")

    # ── Step 3: Call LLM for classification ───────────────────────────────────
    print(f"[Agent] Sending to Llama 3.2 for classification...")

    human_prompt = _build_human_prompt(customer_name, ticket_text)
    response     = llm.invoke([SYSTEM_PROMPT, human_prompt])
    raw_output   = response.content

    # ── Step 4: Parse the LLM response ────────────────────────────────────────
    classification = _parse_llm_output(raw_output)

    # Ensure missing_information is always a list
    if not isinstance(classification.get("missing_information"), list):
        classification["missing_information"] = []

    # ── Step 5: Use custom tool — log result to terminal ──────────────────────
    log_classification_result(ticket_id, customer_name, classification)

    # ── Step 6: Return only the fields this agent owns ────────────────────────
    return {
        "category":            classification.get("category"),
        "urgency":             classification.get("urgency"),
        "sentiment":           classification.get("sentiment"),
        "missing_information": classification.get("missing_information", []),
    }

# ── Standalone run ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("    Agent 1: Intent Classification Agent")
    print("=" * 50 + "\n")

    ticket_id     = input("Enter Your Ticket ID       : ")
    customer_name = input("Enter Your Name            : ")
    ticket_text   = input("Enter Your Support Issue   : ")

    state = {
        "ticket_id":     ticket_id,
        "customer_name": customer_name,
        "ticket_text":   ticket_text,
    }

    ticket_classifier_node(state)