# Dataset & Contract Corpus

## Overview
- **Location**: `Data/raw/`
- **Role**: Evaluation, retrieval-augmented generation (RAG), and demonstration corpus (NOT a model training dataset).
- **Document Count**: 18 commercial contract files (PDF format).
- **Immutability Principle**: `Data/raw/` is strictly read-only. Never modify, overwrite, or delete these raw files. Processed outputs belong in separate directories (e.g., `Data/processed/`).
- **Deduplication Rule**: Do not download duplicate documents without first checking this inventory.

---

## Corpus Inventory

| Filename | Approximate Size | Broad Classification / Known Relationship |
| :--- | :--- | :--- |
| `Access-E-TRADE Amendment.pdf` | ~163 KB | Amendment (Related to Access-E-TRADE MSA) |
| `Access-E-TRADE MSA.pdf` | ~213 KB | Master Services Agreement (MSA) |
| `AMX-Best Circuit Boards Supply Agreement.pdf` | ~158 KB | Supply Agreement / Manufacturing |
| `Colocation Master Services Agreement (2).pdf` | ~2.07 MB | Infrastructure / Colocation MSA |
| `GE Power & Water-TPI Supply Agreement.pdf` | ~936 KB | Industrial Supply Agreement |
| `Guidehouse Managed Services MSA.pdf` | ~604 KB | Professional Services / Managed Services MSA |
| `JPMorgan Supplier MSA Amendment.pdf` | ~269 KB | Financial Services Supplier MSA Amendment |
| `Karman Topco - First Amendment to Limited Partnership Agreement.pdf` | ~142 KB | Corporate Governance / LP Agreement Amendment |
| `Sabre-DXC Amended & Restated MSA.pdf` | ~2.19 MB | Technology Services Amended & Restated MSA |
| `SCYX - Data Processing Agreement provisions.pdf` | ~5.10 MB | Data Privacy / Data Processing Agreement (DPA) |
| `Software License Agreement - ACCESS.pdf` | ~1.29 MB | Software License Agreement (SLA / EULA) |
| `Software License Agreement - Robertson Technologies.pdf` | ~372 KB | Technology License Agreement |
| `Spare Backup - Hewlett-Packard Standard Services Agreement + SOW.pdf` | ~1.48 MB | IT Services Agreement + Statement of Work (SOW) |
| `Sun Microsystems Master Supply Agreement.pdf` | ~332 KB | Hardware / Supply Agreement |
| `The SEC filing for Square-Marqeta.pdf` | ~1.31 MB | Commercial Agreement (SEC Regulatory Filing) |
| `TNS Smart Network - ABM Processing Agreement.pdf` | ~265 KB | Financial Processing Agreement |
| `Turtle Beach-Foxconn MSA.pdf` | ~390 KB | Manufacturing Master Services Agreement |
| `VIAC Non-Disclosure Agreement (2025).pdf` | ~218 KB | Confidentiality / Non-Disclosure Agreement (NDA) |

---

## Notable Characteristics for Downstream Ingestion
- **Amendment Pairs**: Contains explicit base MSA and amendment relationships (e.g., `Access-E-TRADE MSA` + `Access-E-TRADE Amendment`, `JPMorgan Supplier MSA Amendment`, `Karman Topco First Amendment`).
- **Agreement Types**: Diverse coverage across MSAs, Supply Agreements, Software Licenses, DPAs, and NDAs.
- **Detailed Audit**: Comprehensive layout audit, scanned vs. digital text assessment, and page count indexing will be executed in a dedicated dataset audit task.
