# Rule 01: Core Agent Behavior

1. **Focused, Bounded Tasks**: Work strictly on the assigned task. Never expand scope or introduce unrequested refactors without explicit justification and user approval.
2. **Minimum Touchpoint**: Identify the exact, minimum set of files required to complete the task before making edits.
3. **Memory Over Rediscovery**: Consult persistent project memory (`docs/agent-context/`) before scanning or re-exploring the repository.
4. **Preserve Architecture**: Adhere strictly to established conventions and architecture. Never introduce speculative abstractions or modify untouched components.
5. **No Unnecessary Dependencies**: Do not install external libraries, packages, or tools unless explicitly required by the task.
6. **Smallest Correct Change**: Implement the minimal, robust change that satisfies requirements.
7. **Targeted Validation**: Validate changes using focused tests or checks relevant only to modified code.
8. **Clear Stop Condition**: Stop immediately once the acceptance criteria of the task are satisfied.
9. **Transient Artifact Cleanup**: Always remove temporary helper scripts, dead code, intermediate scratch files, and execution caches (`__pycache__`, `.pytest_cache`) after their work is done to keep directories clean.
