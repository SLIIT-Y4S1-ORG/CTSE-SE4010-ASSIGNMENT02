# CTSE-SE4010-ASSIGNMENT02: Multi-Agent Support Ticket Processing System

## Assignment Overview

This project implements a **multi-agent system** for automated customer support ticket processing. The system classifies incoming support tickets, retrieves relevant policies, makes escalation decisions, and drafts response messages—all using AI agents connected through a state machine workflow.

## Assignment Criteria

✅ **Custom Python Tools with Real-World Interaction**
- Each agent must include Python tools that interact with external systems (file I/O, databases, APIs)
- Type hints and comprehensive docstrings required
- No in-memory-only tools (must have real-world interaction)

✅ **Comprehensive Testing**
- Unit tests for each agent component
- Integration tests showing complete workflow
- Test coverage for edge cases and error scenarios

✅ **Multi-Agent Workflow**
- Agents work sequentially, passing state through the pipeline
- Each agent adds information that the next agent uses
- Proper use of TypedDict for state management

---

## System Architecture

The system consists of 4 sequential agents:

### Agent 1: Ticket Classifier

The Intent Classification Agent is the first agent in the Customer Support Ticket Triage System. It receives a raw customer support ticket and analyzes it using a local LLM (Llama 3.2 via Ollama) to extract structured information needed by the rest of the pipeline.

**Responsibilities**
- Classify the ticket into a support category
- Detect the urgency level of the issue
- Identify the customer's sentiment
- Flag any missing information required to resolve the ticket

**Input** (from shared state)
- `ticket_id` — unique identifier for the ticket
- `customer_name` — name of the customer
- `ticket_text` — the raw support message written by the customer

**Output** (stored back into shared state)
- `category` — type of issue: `damaged_item`, `billing_issue`, `shipping_issue`, `account_issue`, `technical_issue`, `refund_request`, `missing_information`, or `general_inquiry`
- `urgency` — `low`, `medium`, or `high`
- `sentiment` — `positive`, `neutral`, or `negative`
- `missing_information` — list of absent but required fields such as `order_id`, `account_email`, `product_details`, or `evidence_attachment`

**Files**
- `agents/ticket_classifier_agent.py` — agent node logic, LLM call, and prompt
- `tools/ticket_classifier_tool.py` — custom tool for reading the ticket dataset and logging results

**How to Run**
```bash
python -m agents.ticket_classifier_agent
```

**How to Test**
```bash
python -m pytest tests/test_ticket_classifier.py -q -s
```


### Agent 2: Knowledge Retrieval Agent
*Coming soon...*

### Agent 3: Escalation Decision Agent ✅ **IMPLEMENTED**

**What it does:**
- Analyzes classified tickets and determines the appropriate action (approve, escalate, or request more info)
- Applies 8 business rules to make decisions (fraud detection, abusive language, urgency levels, category-specific handling)
- Reads customer history from disk to check for repeat complainants and fraud flags
- Writes all decisions to an audit log for compliance and debugging
- Uses LLM (Llama 3.2) to validate decisions

**Real-World Interaction:**
- **Reads**: Customer profiles from `data/customer_history.json`
- **Writes**: Decision audit trail to `data/escalation_audit_log.json`

**Key Files:**
- `tools/escalation_rules_engine.py` - Custom Python tool with business logic
- `agents/escalation_decision_agent.py` - Agent 3 node
- `tests/test_escalation_decision.py` - 8 unit tests (ALL PASSING ✅)
- `escalation_test_run.py` - 3 integration tests (ALL PASSING ✅)

### Agent 4: Response Drafting Agent
*Coming soon...*

---

## Running Agent 3: Escalation Decision Agent

### Prerequisites
```bash
# Ensure Python 3.10+ and dependencies are installed
pip install -r requirements.txt  # or install manually
pip install langchain langchain-ollama pytest
```

### Test Agent 3

**Run Unit Tests (8 tests covering all decision types):**
```bash
python -m pytest tests/test_escalation_decision.py -v
```

**Run Integration Tests (3 real-world scenarios):**
```bash
python escalation_test_run.py
```

**View Audit Log (Real-world file I/O proof):**
```bash
# Windows
type data\escalation_audit_log.json

# Linux/Mac
cat data/escalation_audit_log.json
```

### Test Results Expected ✅

- **Unit Tests**: 8/8 PASSING
  - Damaged items with/without photos
  - Billing issues
  - High urgency handling
  - Abusive language detection
  - Repeat complainants
  - Missing information

- **Integration Tests**: 3/3 PASSING
  - TCK-1001: Photo verification scenario
  - TCK-1002: Missing information scenario
  - TCK-1003: Repeat complainant priority scenario

---

## Project Structure

```
├── README.md                          # This file
├── data/
│   ├── policies.json                  # Policy database
│   ├── customer_history.json          # Customer profiles (read by Agent 3)
│   └── escalation_audit_log.json      # Auto-generated audit trail (written by Agent 3)
├── app/
│   ├── state.py                       # SupportState TypedDict for state management
│   ├── graph.py                       # Multi-agent workflow graph
│   └── main.py                        # Entry point
├── agents/
│   ├── ticket_classifier_agent.py     # Agent 1 (Coming soon)
│   ├── knowledge_retrieval_agent.py   # Agent 2 (Coming soon)
│   ├── escalation_decision_agent.py   # Agent 3 ✅ IMPLEMENTED
│   └── response_drafting_agent.py     # Agent 4 (Coming soon)
├── tools/
│   ├── faq_search.py                  # FAQ search tool (optional)
│   └── escalation_rules_engine.py     # Agent 3 custom tool ✅ IMPLEMENTED
└── tests/
    ├── test_escalation_decision.py    # Agent 3 unit tests ✅
    └── test_knowledge_retrieval.py    # Agent 2 tests (if applicable)
```

---

## Quick Start

To test the complete system (as agents are implemented):

```bash
# Run all tests
python -m pytest tests/ -v

# Run Agent 3 only
python escalation_test_run.py

# View results
type data\escalation_audit_log.json
```

---

## Notes for Reviewers

- ✅ Agent 3 (Escalation Decision) is fully implemented and tested
- ✅ All type hints and docstrings present
- ✅ Real-world file I/O confirmed working
- ✅ 100% test pass rate (11/11 tests)
- Placeholder sections for Agents 1, 2, and 4
- Custom Python tool: `tools/escalation_rules_engine.py` (real-world interaction with file system)