---
name: contract-agent
description: Guidelines for building the core ContractLens reasoning agent and deterministic tools.
---

# Contract Agent Skill

## When to Use
Use when implementing agent workflows, tool definitions, reasoning loops, prompt templates, or answer generation.

## Critical Constraints
1. **Deterministic Tools Over Generative Guessing**:
   - Use deterministic tools for date filtering, party lookup, obligation status, and amendment linking.
   - Do not ask the LLM to calculate renewal deadlines or sort dates in memory when a tool can do it deterministically.
2. **Grounded In Evidence**:
   - Every contractual assertion or answer MUST cite document name, section, and page number.
   - If a clause does not exist or is ambiguous, explicitly state that it is not found. Never invent missing terms.
3. **Structured Outputs**:
   - Return structured objects (JSON/Pydantic schemas) for obligations, risk flags, and timeline items to integrate smoothly with the UI.
4. **Fact vs. Interpretation**:
   - Clearly distinguish between explicit contract text and legal risk interpretations or advisory summaries.

## Typical Workflow
1. Define tool schemas and handler functions.
2. Implement agent loop (planning, tool call, synthesis).
3. Benchmark against sample queries (e.g., "What are the termination notice requirements in the Foxconn MSA?").
4. Verify citation correctness and output formatting.
