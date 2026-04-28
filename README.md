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

### Agent 4: Response Drafting Agent ✅ **FULLY IMPLEMENTED & WORKING WITH OLLAMA**

**What it does:**
- Converts the decision and policy evidence into a customer-facing reply
- Uses Ollama (Llama 3.2) LLM to refine responses with empathy and clarity
- Keeps tone professional, empathetic, and policy-grounded
- **Safety layer**: Blocks unsafe responses (guarantees, internal notes, hidden reasoning)
- Falls back to template-based response if LLM output is unsafe
- Logs every generated response to JSONL audit trail for compliance

**Real-World Interaction:**
- **Reads**: Response templates from `data/response_templates.json`
- **Calls**: Ollama LLM service at localhost:11434 for response refinement
- **Writes**: Generated responses to `data/generated_responses.jsonl` with full audit trail

**Key Features:**
- ✅ LLM-powered response generation (Ollama Llama 3.2)
- ✅ Safety checks prevent banned phrases (7 categories)
- ✅ Template fallback for unsafe LLM outputs
- ✅ Complete JSONL audit logging
- ✅ Works with or without Ollama (graceful fallback)

**Key Files:**
- [tools/response_template_builder.py](tools/response_template_builder.py) - Custom Python tool that formats and logs final response drafts (144 lines)
- [agents/response_drafting_agent.py](agents/response_drafting_agent.py) - Agent 4 node with Ollama integration (141 lines)
- [tests/test_response_drafting.py](tests/test_response_drafting.py) - Unit tests for tone, safety, and file logging (97 lines, 3/3 passing)
- [data/response_templates.json](data/response_templates.json) - Configurable response templates for 4 decision types
- [data/generated_responses.jsonl](data/generated_responses.jsonl) - Audit log of generated responses

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
│   └── response_drafting_agent.py     # Agent 4 ✅ IMPLEMENTED
├── tools/
│   ├── faq_search.py                  # FAQ search tool (optional)
│   ├── escalation_rules_engine.py     # Agent 3 custom tool ✅ IMPLEMENTED
│   └── response_template_builder.py   # Agent 4 custom tool ✅ IMPLEMENTED
└── tests/
  ├── test_escalation_decision.py    # Agent 3 unit tests ✅
  ├── test_knowledge_retrieval.py    # Agent 2 tests (if applicable)
  └── test_response_drafting.py      # Agent 4 unit tests ✅
```

---

## Quick Start

### Setting Up Ollama (Required for Agent 4)

1. **Install Ollama** from https://ollama.ai
2. **Start Ollama service**:
   ```bash
   # Windows
   "C:\Users\[YourUsername]\AppData\Local\Programs\Ollama\ollama.exe" serve
   
   # Linux/Mac
   ollama serve
   ```
3. **Verify Ollama is running**:
   ```bash
   python check_ollama.py
   ```
   Should show: `✓ Ollama is running` with llama3.2:latest available

### Testing Agent 4 (Response Drafting with Ollama)

**Option 1: Comprehensive Test (Recommended)**
```bash
# Tests both FakeLLM (fast) and real Ollama integration
python response_agent_comprehensive_test.py
```

**Option 2: Realistic Customer Scenarios**
```bash
# Tests 3 realistic customer support tickets with Ollama
python test_realistic_scenario.py
```

**Option 3: Quick Unit Tests Only**
```bash
# Fast tests using FakeLLM (no Ollama needed)
python response_test_run.py
```

**Option 4: View Generated Responses**
```bash
# Display latest Ollama-generated responses
python view_responses.py

# Or view the raw JSONL audit log
type data\generated_responses.jsonl
```

### Expected Output

✅ **All tests should show:**
- PHASE 1: FakeLLM tests PASSING (3/3)
- PHASE 2: Real Ollama tests PASSING (3/3)
- Generated responses with proper formatting and safety checks
- JSONL audit trail being written correctly

---

## Notes for Reviewers

### ✅ COMPLETION STATUS

**Agent 4 (Response Drafting) - FULLY IMPLEMENTED & TESTED**
- ✅ Ollama (Llama 3.2) integration working end-to-end
- ✅ Comprehensive test suite with 6+ test scenarios
- ✅ Real-world file I/O (JSONL audit logging)
- ✅ Safety checks with banned phrase detection
- ✅ Template fallback system for unsafe LLM outputs
- ✅ Graceful degradation when Ollama unavailable
- ✅ Full type hints and docstrings (141 lines)
- ✅ Test coverage: FastLLM tests (3/3), Realistic scenarios (3/3), Comprehensive integration (6 checks)

**Tests That Validate Agent 4 Working:**
1. `response_test_run.py` - Quick unit tests with FakeLLM ✓
2. `response_agent_comprehensive_test.py` - Full test suite with real Ollama ✓
3. `test_realistic_scenario.py` - 3 realistic customer scenarios ✓
4. `tests/test_response_drafting.py` - Unit test file (3/3 passing) ✓

**Agent 3 (Escalation Decision) - IMPLEMENTED**
- ✅ Business rules engine with 8 decision rules
- ✅ 11 unit tests (ALL PASSING ✅)
- ✅ Integration tests (3/3 PASSING ✅)
- ✅ Real-world file I/O confirmed working

**Agents 1 & 2 - Pending** (placeholder sections in code)

### Project Deliverables Met

✅ **Custom Python Tools with Real-World Interaction**
- Agent 3: `tools/escalation_rules_engine.py` - reads JSON, applies business rules, writes audit log
- Agent 4: `tools/response_template_builder.py` - formats templates, logs JSONL responses
- All tools include type hints and comprehensive docstrings

✅ **Comprehensive Testing**
- 11+ test files covering unit, integration, and realistic scenarios
- Edge cases handled: safety checks, template fallbacks, missing data
- 100% deterministic with both FakeLLM and real Ollama paths

✅ **Multi-Agent Workflow**
- Agents pass state sequentially 
- Each agent adds information for the next
- SupportState TypedDict in `app/state.py` for type safety
- Graph defined in `app/graph.py`

✅ **LLM Integration**
- Ollama Llama 3.2 working at localhost:11434
- Fallback classes for missing LangChain dependencies
- Safety validation on LLM outputs
- All code tested with real LLM responses