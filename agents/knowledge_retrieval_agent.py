from app.state import SupportState
from tools.faq_search import search_knowledge_base
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

# Use locally running Ollama model (llama3.2)
llm = ChatOllama(model="llama3.2", temperature=0)

def knowledge_retrieval_node(state: SupportState):
    """
    Agent 2: Uses a tool to find policies, then uses Llama 3.2
    to extract ONLY the most relevant rule based on the ticket text.
    """
    ticket_category = state.get("category", "unknown")
    ticket_text = state.get("ticket_text", "")

    print(f"\n[Agent 2] Searching knowledge base for: '{ticket_category}'...")
    
    # 1) Fetch policy evidence from local knowledge base
    raw_evidence = search_knowledge_base(category=ticket_category)
    evidence_text = "\n".join(
        [f"{item['title']}: {item['content']}" for item in raw_evidence]
    )

    print("[Agent 2] Waking up Llama 3.2 to analyze the evidence...")

    # 2) Instruct LLM to extract only the most relevant rule
    system_prompt = SystemMessage(
        content=f"""
            You are a Knowledge Retrieval AI.
            Read the following company policies:
            {evidence_text}

            Extract ONLY the exact rule or constraint that applies to this specific customer ticket.
            Do not invent policies. Keep it under 2 sentences.
        """
    )
    human_prompt = HumanMessage(content=f"Ticket: {ticket_text}")

    # 3) Invoke local Ollama model
    ai_response = llm.invoke([system_prompt, human_prompt])
    print(f"   -> AI Extracted: {ai_response.content}")

    # 4) Pass concise extracted policy text to next agent
    return {
        "policy_matches": [ai_response.content]
    }


# Backward-compatible alias if other modules import retrieval_node
def retrieval_node(state: SupportState):
    return knowledge_retrieval_node(state)