from app.state import SupportState
from tools.faq_search import search_knowledge_base
from typing import Any, Dict, List
from datetime import datetime
import json
import os

try:
    from langchain_core.messages import SystemMessage, HumanMessage     # type: ignore
except Exception:  # pragma: no cover - allow offline testing
    class _FallbackMessage:
        def __init__(self, content: str):
            self.content = content

    class SystemMessage(_FallbackMessage):
        pass

    class HumanMessage(_FallbackMessage):
        pass

try:
    from langchain_ollama import ChatOllama     # type: ignore
    llm = ChatOllama(model="llama3.2", temperature=0)
except Exception:  # pragma: no cover - allow offline testing
    llm = None  # type: ignore


def _format_evidence_text(evidence: List[Dict[str, Any]]) -> str:
    if not evidence:
        return ""
    return "\n".join([f"{item.get('title','')}: {item.get('content','')}" for item in evidence])


def _append_retrieval_audit_log(entry: Dict[str, Any], log_path: str = "data/retrieval_audit_log.jsonl") -> None:
    """Append one retrieval audit entry to disk as JSONL."""
    directory = os.path.dirname(log_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(log_path, "a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def knowledge_retrieval_node(state: SupportState, top_k: int = 3) -> Dict[str, Any]:
    """Agent 2: query local KB, call LLM to extract concise rule, and return structured evidence.

    Returns a dict containing:
    - `policy_matches`: legacy list[str] for downstream compatibility
    - `policy_match_details`: structured list[dict] with keys `id`, `title`, `content`, `source`, `extracted`
    - `faq_matches`: list[str] of titles returned by the tool
    - `logs`: appended structured log entry
    """
    ticket_category = state.get("category", "unknown")
    ticket_text = state.get("ticket_text", "")

    print("\n[Agent 2] Processing knowledge retrieval...")
    print(f"  Category: {ticket_category}")
    print(f"  Ticket Snippet: {str(ticket_text)[:120]}")
    print(f"[Agent 2] Searching knowledge base for: '{ticket_category}'...")

    # 1) Fetch policy evidence from local knowledge base
    kb_file = "data/policies.json"
    raw_evidence = []
    try:
        raw_evidence = search_knowledge_base(category=ticket_category, file_path=kb_file, top_k=top_k)
    except Exception as exc:
        raw_evidence = [{"title": "Error", "content": f"Knowledge base error: {exc}", "id": None}]

    print(f"[Agent 2] Tool returned {len(raw_evidence)} evidence item(s).")

    # Normalize evidence entries and add source metadata
    normalized: List[Dict[str, Any]] = []
    for idx, item in enumerate(raw_evidence):
        entry_id = item.get("id") or f"{ticket_category}_{idx}"
        normalized.append({
            "id": entry_id,
            "title": item.get("title", ""),
            "content": item.get("content", ""),
            "source": kb_file,
        })

    if normalized:
        print("[Agent 2] Top evidence titles:")
        for evidence in normalized:
            print(f"   - {evidence['title']}")

    evidence_text = _format_evidence_text(normalized)

    # 2) Prepare LLM prompt to extract the single most relevant rule (if LLM available)
    extracted_text = ""
    if llm is not None:
        print("[Agent 2] Consulting local LLM to extract concise policy guidance...")
        system_prompt = SystemMessage(
            content=(
                "You are a Knowledge Retrieval AI. Read the provided company policy excerpts and "
                "extract ONLY the single most relevant rule or constraint that applies to the given ticket. "
                "Cite the rule as a short sentence and do not invent policies. Keep under 2 sentences.\n\n"
                f"Policies:\n{evidence_text}"
            )
        )
        human_prompt = HumanMessage(content=f"Ticket: {ticket_text}")

        try:
            ai_response = llm.invoke([system_prompt, human_prompt])
            extracted_text = getattr(ai_response, "content", "").strip()
            print(f"   -> AI Extracted: {extracted_text}")
        except Exception as exc:
            print(f"   -> LLM invocation failed: {exc}")
            extracted_text = ""  # will fallback below
    else:
        print("[Agent 2] LLM is not available; skipping LLM extraction.")

    # 3) Build structured policy matches and a legacy string list for downstream agents
    policy_match_details: List[Dict[str, Any]] = []
    policy_matches: List[str] = []
    for entry in normalized:
        # If LLM produced text, associate it with the top evidence entry only
        extracted = extracted_text if extracted_text else entry.get("content", "").strip()
        policy_match_details.append({
            "id": entry["id"],
            "title": entry["title"],
            "content": entry["content"],
            "source": entry["source"],
            "extracted": extracted,
        })
        policy_matches.append(extracted)

    faq_matches = [e["title"] for e in normalized]

    # 4) Append structured log entry into state['logs']
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent": "knowledge_retrieval_agent",
        "ticket_id": state.get("ticket_id", "UNKNOWN"),
        "customer_name": state.get("customer_name", "UNKNOWN"),
        "input": {
            "category": ticket_category,
            "ticket_text_snippet": ticket_text[:200],
        },
        "tool_call": "search_knowledge_base",
        "tool_output_count": len(normalized),
        "policy_matches_count": len(policy_matches),
        "faq_matches": faq_matches,
    }

    print(f"[Tool] Writing retrieval audit log for ticket {log_entry['ticket_id']}...")
    try:
        _append_retrieval_audit_log(log_entry)
        print(f"[Tool] Retrieval audit logged for {log_entry['ticket_id']}")
    except Exception as exc:
        print(f"[Tool] Retrieval audit logging failed: {exc}")

    print("✓ Agent 2 Complete")
    print(f"  Policy matches: {len(policy_matches)}")
    print(f"  FAQ matches: {len(faq_matches)}")

    existing_logs = state.get("logs", [])
    if isinstance(existing_logs, list):
        updated_logs = [*existing_logs, log_entry]
    else:
        updated_logs = [log_entry]

    # 5) Return structured update (do not mutate unrelated keys)
    return {
        "policy_matches": policy_matches,
        "policy_match_details": policy_match_details,
        "faq_matches": faq_matches,
        "logs": updated_logs,
    }


# Backward-compatible alias if other modules import retrieval_node
def retrieval_node(state: SupportState):
    return knowledge_retrieval_node(state)