import json   # for parsing LLM output
import re     # for cleaning LLM output (removing markdown code blocks)
from langchain_core.messages import HumanMessage, SystemMessage  # for structured prompts
from langchain_ollama import ChatOllama  # for LLM interaction
from app.state import SupportState  # for shared state type
from tools.ticket_classifier_tool import run_ticket_classification_flow # for standalone testing and logging

# ── Initialize LLM model (Ollama Llama3.2) ──────────────────────────────────────────────────────────
llm = ChatOllama(model="llama3.2", temperature=0)

# ── System prompt (rules for ticket classification) ─────────────────────────────────────────────────
SYSTEM_PROMPT = SystemMessage(
    content=(
        "You are an expert customer support ticket classifier.\n\n"

        "Analyze the given support ticket and return ONLY a valid JSON object with these exact keys:\n"
        "category, urgency, sentiment, missing_information\n\n"

        "Use the ticket text itself as the source of truth. Do not invent missing fields when the text already contains them.\n"
        "Follow these rules exactly and apply the first matching category.\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "STEP 0 — VAGUE INPUT DETECTION (MANDATORY OVERRIDE):\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        "If the ticket is extremely short, vague, or unclear (examples: 'Help', 'Issue', 'Problem', 'Hi', 'Hello'):\n\n"

        "→ You MUST immediately return EXACTLY this JSON:\n"
        "{\n"
        "  \"category\": \"missing_information\",\n"
        "  \"urgency\": \"medium\",\n"
        "  \"sentiment\": \"neutral\",\n"
        "  \"missing_information\": [\"order_id\", \"product_details\"]\n"
        "}\n\n"

        "Do NOT continue to any other rules.\n"
        "This is a STRICT OVERRIDE.\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "1. category — PRIORITY ORDER (use the FIRST rule that matches):\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        "   → 'refund_request' if the customer asks for a refund, money back, return, or reimbursement.\n"
        "   → 'billing_issue' if the problem is about being charged twice, overcharged, payment, invoice, or a bank statement discrepancy.\n"
        "   → 'damaged_item' if the item is broken, damaged, shattered, cracked, defective, or not working as described.\n"
        "      If the ticket also mentions shipping words like arrived/package/shipment, damaged_item still wins.\n"
        "   → 'shipping_issue' if the issue is about late delivery, delayed shipment, missing package, tracking, or an item not arriving.\n"
        "      For every shipping_issue, check whether an explicit order number is visible in the text. If no order number is visible, missing_information MUST include 'order_id'.\n"
        "      Example: 'My package bag arrived yet. It has been two weeks since I ordered. Where is my shipment?' => category='shipping_issue', missing_information=['order_id'].\n"
        "   → 'account_issue' if the customer cannot log in, account is locked/suspended, or access is blocked.\n"
        "   → 'technical_issue' if the app/site/system crashes, freezes, shows errors, or fails to load.\n"
        "   → 'missing_information' only if the ticket is too vague to classify confidently.\n"
        "   → 'general_inquiry' only if none of the above apply.\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "2. urgency — Choose ONE from [low, medium, high]\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        "   → 'high' only if the ticket says immediately, urgently, ASAP, now, cannot wait, or describes a critical blocking issue.\n"
        "   → 'medium' is the default for normal support tickets.\n"
        "   → 'low' only if the ticket is clearly non-urgent.\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "3. sentiment — Choose ONE from [positive, neutral, negative]\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        "   → 'negative' only if the ticket contains strong emotional language, anger, frustration, or blame.\n"
        "   → 'neutral' is the default for ordinary complaints and requests.\n"
        "   → 'positive' only if the customer is clearly polite or thankful.\n\n"

        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "4. missing_information\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"

        "   → Add 'order_id' when the case is shipping_issue, billing_issue, refund_request, or damaged_item AND no order number is present.\n"
        "   → Treat phrases like 'I ordered it two weeks ago' or 'since I ordered' as NOT being an order_id.\n"
        "   → Only count a real order_id when the ticket contains an explicit order reference such as ORD-1234, order 1234, order number 1234, or a similar visible identifier.\n"
        "   → Example: 'My package has not arrived yet. It has been two weeks since I ordered. Where is my shipment?' MUST include missing_information: [\"order_id\"] because no order number is shown.\n"
        "   → If the ticket says 'my package arrived yet' or similar shipping language without an order number, still include 'order_id'.\n"
        "   → Do NOT add 'order_id' if the ticket already contains an order number like ORD-1234 or order 1234.\n"
        "   → Add 'account_email' only for account_issue when the email is missing.\n"
        "   → Add 'product_details' only when the ticket is vague and still needs clarification.\n"
        "   → Add 'evidence_attachment' for damaged_item when no photo, picture, screenshot, image, or proof is mentioned.\n"
        "   → For a damaged_item ticket, if a photo or proof is mentioned, do NOT add 'evidence_attachment'.\n"
        "   → Return missing_information as an empty list when nothing is missing.\n\n"

        "Important: do not over-label a ticket as missing_information when the message clearly describes a real issue.\n"

        "Return ONLY valid JSON."
    )
)

# ── Build user message for LLM ─────────────────────────────────────────────
def _build_human_prompt(ticket_text: str) -> HumanMessage:
    return HumanMessage(
        content=(
            f"Ticket Text: {ticket_text}\n\n"
            "Classify this ticket now."
        )
    )

# ── Clean + parse LLM output into JSON safely ──────────────────────────────
def _parse_llm_output(raw: str) -> dict:
    clean = raw.strip()

    # remove markdown code blocks (```json) if present
    clean = re.sub(r"^```(?:json)?", "", clean).strip()
    clean = re.sub(r"```$", "", clean).strip()

    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        # fallback: extract JSON object from text
        match = re.search(r"\{.*\}", clean, flags=re.DOTALL)
        if match:
            return json.loads(match.group(0))
        
        # fail if nothing valid found
        raise ValueError(f"Could not parse LLM output:\n{raw}")

# ── Main agent node (runs classification) ───────────────────────────────
def ticket_classifier_node(state: SupportState) -> dict:
    # extract ticket text from state
    ticket_text = state.get("ticket_text", "")

    print("\n[Agent 1] Llama 3.2 | Status: Classification started")
    # call LLM with system + user prompt
    response = llm.invoke([SYSTEM_PROMPT, _build_human_prompt(ticket_text)])
    # parse LLM response into structured JSON
    classification = _parse_llm_output(response.content)

    # ── Ensure missing_information is always a list ─────────────────────────────────────────────────────────────
    if not isinstance(classification.get("missing_information"), list):
        classification["missing_information"] = []

    # return structured output
    return {
        "category": classification.get("category"),
        "urgency": classification.get("urgency"),
        "sentiment": classification.get("sentiment"),
        "missing_information": classification.get("missing_information", []),
    }

# ── Run system standalone (for testing) ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_ticket_classification_flow(ticket_classifier_node)