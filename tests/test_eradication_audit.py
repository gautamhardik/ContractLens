"""Tests ensuring that all hardcoded entities, document IDs, and static ontology mappings
are permanently eradicated from production source code (src/ and frontend/src/).
"""
import re
from pathlib import Path
import pytest

LEGACY_CONSTANTS = [
    "KNOWN_ENTITIES",
    "CONTRACT_PARTY_ROLES",
    "CONTRACT_ROLE_PROVENANCE",
    "KNOWN_PARENT_CHILD_PAIRS",
    "_DYNAMIC_ENTITIES",
]

PROD_DIRS = [
    Path("src"),
    Path("frontend/src"),
]


def test_no_legacy_constant_identifiers_in_production():
    """Verify that none of the legacy dictionary names exist in src/ or frontend/src/."""
    violations = []
    for prod_dir in PROD_DIRS:
        if not prod_dir.exists():
            continue
        for f in prod_dir.rglob("*"):
            if f.is_file() and f.suffix in {".py", ".js", ".jsx", ".ts", ".tsx"}:
                content = f.read_text(encoding="utf-8", errors="ignore")
                for const_name in LEGACY_CONSTANTS:
                    if const_name in content:
                        if re.search(rf"\b{const_name}\b\s*=", content):
                            violations.append(f"{f}: defines {const_name}")
                        elif f"import {const_name}" in content or (f"from " in content and const_name in content):
                            violations.append(f"{f}: references {const_name}")

    assert not violations, f"Legacy constants found in production code:\n" + "\n".join(violations)


def test_no_hardcoded_document_ids_in_runtime_logic():
    """Verify that no specific doc_01..doc_17 IDs are hardcoded in routing, understanding, or UI actions."""
    violations = []
    doc_id_pattern = re.compile(r"['\"]doc_(0[1-9]|1[0-7])['\"]")

    for prod_dir in PROD_DIRS:
        if not prod_dir.exists():
            continue
        for f in prod_dir.rglob("*"):
            if f.is_file() and f.suffix in {".py", ".js", ".jsx", ".ts", ".tsx"}:
                lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
                for line_no, line in enumerate(lines, start=1):
                    matches = doc_id_pattern.findall(line)
                    if matches:
                        stripped = line.strip()
                        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("*"):
                            continue
                        violations.append(f"{f}:{line_no} contains hardcoded '{matches[0]}': {line.strip()}")

    assert not violations, f"Hardcoded document IDs found in production code:\n" + "\n".join(violations)
