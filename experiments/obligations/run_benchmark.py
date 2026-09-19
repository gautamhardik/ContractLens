"""Empirical Obligation, Temporal & Lifecycle Benchmark Runner (Phase 7–9).

Evaluates obligation extraction, actor resolution, temporal type classification,
relative offset preservation, and lifecycle event generation across key contracts:
1. Access-E*TRADE MSA (doc_03)
2. Access-E*TRADE Amendment (doc_02)
3. Turtle Beach-Foxconn MSA (doc_13)
4. AMX Supply Agreement (doc_01)
5. Spare Backup HP MSA (doc_15)
6. Square-Marqeta (doc_16)
"""

import os
import re
import json
from pathlib import Path
from collections import Counter
from typing import Dict, Any

from src.ingestion.reconstructor import StructuralReconstructor
from src.ingestion.extractor import ContractIntelligenceExtractor
from src.ingestion.obligation_extractor import ObligationExtractor
from src.temporal.lifecycle import LifecycleEventEngine
from src.models.obligation import ObligationStatus, TemporalType


RAW_DIR = r"c:\Users\hiten\Downloads\ContractLens\Data\raw"
OUTPUT_DIR = Path("experiments/obligations")


def get_raw_path(needle: str) -> str:
    needle_clean = re.sub(r'[^a-zA-Z0-9]', '', needle).lower()
    for f in os.listdir(RAW_DIR):
        f_clean = re.sub(r'[^a-zA-Z0-9]', '', f).lower()
        if needle_clean in f_clean:
            return os.path.join(RAW_DIR, f)
    raise FileNotFoundError(f"File matching '{needle}' not found in {RAW_DIR}")


def run_benchmark():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    reconstructor = StructuralReconstructor()
    intel_extractor = ContractIntelligenceExtractor()
    ob_extractor = ObligationExtractor()

    targets = [
        ("doc_03", "Access-E-TRADE MSA"),
        ("doc_02", "Access-E-TRADE Amendment"),
        ("doc_13", "Turtle Beach-Foxconn MSA"),
        ("doc_01", "AMX"),
        ("doc_15", "Spare Backup"),
        ("doc_16", "Square-Marqeta"),
    ]

    results = []

    for doc_id, needle in targets:
        path = get_raw_path(needle)
        filename = os.path.basename(path)
        print(f"Processing {doc_id}: {filename}...")

        doc = reconstructor.reconstruct_document(path, doc_id)
        intel = intel_extractor.extract(doc)
        obligations = ob_extractor.extract_obligations(doc, intel)
        events = LifecycleEventEngine.generate_lifecycle_events(doc, intel, obligations)

        temporal_dist = Counter(ob.temporal.temporal_type.value for ob in obligations)
        actor_dist = Counter(ob.actor for ob in obligations)

        # Verification metrics
        all_have_evidence = all(ob.evidence is not None and ob.evidence.bbox.x1 > ob.evidence.bbox.x0 for ob in obligations)
        all_unknown_status = all(ob.status == ObligationStatus.UNKNOWN for ob in obligations)
        unresolved_anchors_intact = all(
            ob.temporal.is_resolved is False
            for ob in obligations
            if ob.temporal.temporal_type in (TemporalType.RELATIVE_OFFSET, TemporalType.EVENT_RELATIVE)
        )

        doc_summary = {
            "document_id": doc_id,
            "filename": filename,
            "page_count": doc.page_count,
            "total_obligations_extracted": len(obligations),
            "total_lifecycle_events": len(events),
            "temporal_distribution": dict(temporal_dist),
            "top_actors": dict(actor_dist.most_common(5)),
            "guarantees": {
                "all_have_evidence_provenance": all_have_evidence,
                "zero_fabricated_completion_status": all_unknown_status,
                "unresolved_relative_anchors_intact": unresolved_anchors_intact
            },
            "sample_obligations": [
                {
                    "id": ob.obligation_id,
                    "actor": ob.actor,
                    "action": ob.action,
                    "temporal_type": ob.temporal.temporal_type.value,
                    "raw_expression": ob.temporal.raw_expression,
                    "page": ob.evidence.page_number,
                    "bbox": ob.evidence.bbox.as_tuple()
                }
                for ob in obligations[:5]
            ],
            "lifecycle_events_sample": [
                {
                    "event_id": ev.event_id,
                    "event_type": ev.event_type.value,
                    "title": ev.title,
                    "trigger_or_date": ev.date_or_trigger,
                    "page": ev.evidence.page_number
                }
                for ev in events[:5]
            ]
        }
        results.append(doc_summary)

    out_file = OUTPUT_DIR / "benchmark_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Benchmark completed. Output written to {out_file}")


if __name__ == "__main__":
    run_benchmark()
