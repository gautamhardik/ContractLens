# Rule 06: Workspace Hygiene & Transient File Cleanup

1. **Strict Directory Cleanliness**: The repository must always remain clean, uncluttered, and free of transient artifacts.
2. **Immediate Cleanup of Temporary Files**:
   - Any temporary script, scratch file, intermediate generator, or one-off conversion file created to produce a main deliverable must be deleted immediately after its job is done.
   - If a helper file is not intended to be a permanent, maintained part of the repository, do not leave it behind.
3. **Dead Code & Obsolete Artifacts**: Remove dead code, superseded test runs, and unused intermediary files immediately. Never leave orphaned files in the workspace.
4. **Cache & Test Artifacts Hygiene**:
   - Pytest cache (`.pytest_cache/`), Python bytecode caches (`__pycache__/`, `*.pyc`), and similar runtime directories generated during executions must be cleaned up if left un-ignored, and should never accumulate clutter deep within directories or at the root.
   - Any temporary build or test output files must be pruned once testing concludes.
5. **Preserve Immutable Assets**: This rule applies strictly to transient files and code artifacts. Never touch or remove raw contract assets in `Data/raw/`.
