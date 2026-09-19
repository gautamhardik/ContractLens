# Rule 03: Python Conventions

1. **Current Status**: No Python code or environment has been established yet in the repository.
2. **Virtual Environment**: When initialized, ensure dependencies and scripts run within a designated local virtual environment (e.g., `.venv`).
3. **Targeted Execution**: Execute Python scripts or modules using explicit virtual environment interpreter paths.
4. **Clean Dependencies**: Specify dependencies strictly via explicit dependency configuration (e.g., `pyproject.toml` or `requirements.txt`) without installing unvetted global packages.
5. **No Fabricated Patterns**: Do not introduce unvetted formatting, linting, or packaging tools until decided and documented in `DECISIONS.md`.
