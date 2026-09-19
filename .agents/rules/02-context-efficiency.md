# Rule 02: Context Efficiency & Memory System

1. **Read Memory First**: Read project-context documents in `docs/agent-context/` before exploring source code.
2. **No Repository Scanning**: Do not scan the entire repository or recursively list directories for routine tasks.
3. **Use the Memory Map**:
   - Locate files via `FILE_MAP.md`.
   - Understand system architecture via `ARCHITECTURE.md`.
   - Verify completed work via `STATUS.md`.
   - Check technical decisions via `DECISIONS.md`.
   - Review corpus structure via `DATASET.md`.
4. **Targeted Inspection**: Inspect only files directly relevant to the current task. Prefer targeted grep/line-range reads over whole-file inspection.
5. **No Repeated Rediscovery**: Never rediscover facts, decisions, or structures already documented in memory.
6. **Maintain Stale Memory**: If a documented fact becomes stale, update the corresponding context file immediately after verifying the change. Never compensate for stale memory by re-scanning the repo.
7. **Brevity & Conciseness**: Keep persistent context files concise, structured, and free of redundancy.
8. **No Code/Data Dumps**: Never dump source code, large text blobs, or PDF contents into context documents or always-loaded rules.
