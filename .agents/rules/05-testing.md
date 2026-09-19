# Rule 05: Testing Conventions

1. **Current Status**: No test runner, test framework, or test suites currently exist in the repository.
2. **Targeted Testing First**: When testing is introduced, prefer fast, targeted test execution during active development.
3. **Milestone Validation**: Run full suites or regression sweeps only at milestone boundaries or before final delivery.
4. **No Test Tampering**: Never modify or weaken test assertions solely to make a failing test pass; address the root failure in code or verify requirements.
5. **Supported Commands Only**: Run only test commands and runners explicitly established in the project (to be documented in `FILE_MAP.md` and `DECISIONS.md`).
6. **Clean Test & Cache Artifacts**: Automatically clean up temporary test artifacts, test logs, and cache folders (`.pytest_cache/`, `__pycache__/`) generated during test runs.
