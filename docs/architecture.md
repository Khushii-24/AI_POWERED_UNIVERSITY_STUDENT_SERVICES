# Architecture Decision Record: Single LangGraph Workflow vs Multi-Agent

## Decision
We have chosen to implement a **single, fixed deterministic LangGraph workflow** rather than a multi-agent system. 

## Rationale
In the context of the AI-Powered University Student Services platform, the system must adhere strictly to established university policies and procedures without deviation.

1. **Determinism over Autonomy**: Multi-agent systems tend to be non-deterministic as agents plan and adapt on the fly. In our domain (e.g., calculating exam eligibility, checking CGPA constraints), unpredictability is unacceptable. A fixed workflow guarantees that every request follows exactly the same path: `guard -> classify -> select tools -> retrieve+precedence -> execute tools -> synthesize -> verify -> finalize+audit`.
2. **Safety and Auditability**: With a strict workflow, we can enforce hard boundaries between retrieval, calculation, and synthesis. We can inject deterministic verification steps (e.g., ensuring numbers match tool outputs exactly) and ensure that LLM synthesis only receives safely retrieved and precedence-ordered data marked as "untrusted".
3. **Simplicity and Latency**: Agents communicating back and forth increases token usage and latency. A pipelined workflow is much more efficient and avoids issues where agents get stuck in conversational loops.

## The Workflow Pipeline
1. **Guard**: Input sanitization and injection detection.
2. **Classify**: Categorizes the intent and determines if clarification is needed.
3. **Select Tools**: Deterministic or Pydantic-validated LLM selection of tools.
4. **Retrieve & Precedence**: RAG retrieval followed by deterministic rule precedence checking.
5. **Execute Tools**: Calls to underlying databases.
6. **Synthesize**: LLM generates the response explicitly referencing untrusted `<doc>` sections and tool outputs.
7. **Verify**: Deterministic check that citations and numbers match source data.
8. **Finalize & Audit**: Structured output packaging and logging.
