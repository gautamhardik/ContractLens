---
name: testing
description: Guidelines for running targeted tests and validating changes across the codebase.
---

# Testing Skill

## When to Use
Use when validating changes, writing unit or integration tests, or running regression suites.

## Critical Constraints
1. **Targeted First**: Run fast, localized tests during feature development rather than broad sweeps.
2. **Never Weaken Tests**: If a test fails, investigate the implementation or verify requirement changes; never adjust assertions solely to make a test pass.
3. **Evidence Validation**: Specifically validate that retrieval and agent outputs include correct page and section references.
4. **Current Status**: No test framework is currently installed. When installed, record runner command in `DECISIONS.md` and `FILE_MAP.md`.

## Typical Workflow
1. Identify the minimal test command for modified components.
2. Run targeted validation.
3. If milestone is reached, run full project test suite.
