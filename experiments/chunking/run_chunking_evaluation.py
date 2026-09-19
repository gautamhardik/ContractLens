"""Empirical Chunking and Benchmark Evaluation Harness (Phase 11 & 12).

Compares:
A. FixedSlidingWindowChunker (1000 chars, 200 char overlap)
B. SectionAwareChunker (contract section hierarchy + tables + exhibits)

Evaluates:
1. Evidence containment: Does a single chunk contain all required key phrases for a question?
2. Multi-chunk split rate: Is the evidence split across chunk boundaries?
3. Provenance retention: Are section numbers, titles, pages, and bboxes preserved?
4. Chunk size distribution: Mean, min, max, std deviation of character lengths.
5. Cross-page clause continuity.
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple
import statistics

from src.ingestion.reconstructor import StructuralReconstructor
from src.retrieval.chunking import FixedSlidingWindowChunker, SectionAwareChunker
from src.models.chunk import RetrievalChunk
from experiments.evaluation.benchmark_dataset import get_evaluation_dataset
from experiments.evaluation.benchmark_schema import BenchmarkQuestion


RAW_DIR = r"c:\Users\hiten\Downloads\ContractLens\Data\raw"
OUTPUT_DIR = Path("experiments/chunking")


def get_raw_path(needle: str) -> str:
    needle_clean = re.sub(r'[^a-zA-Z0-9]', '', needle).lower()
    for f in os.listdir(RAW_DIR):
        f_clean = re.sub(r'[^a-zA-Z0-9]', '', f).lower()
        if needle_clean in f_clean:
            return os.path.join(RAW_DIR, f)
    raise FileNotFoundError(f"File matching '{needle}' not found in {RAW_DIR}")


DOC_MAPPINGS = {
    "doc_01": "AMX–Best Circuit Boards Supply Agreement.pdf",
    "doc_02": "Access–E-TRADE Amendment.pdf",
    "doc_03": "Access–E-TRADE MSA.pdf",
    "doc_09": "SCYX – Data Processing Agreement provisions.pdf",
    "doc_10": "Sabre–DXC Amended & Restated MSA.pdf",
    "doc_13": "Spare Backup – Hewlett-Packard Standard Services Agreement + SOW.pdf",
    "doc_16": "The SEC filing for Square-Marqeta.pdf",
    "doc_17": "Turtle Beach–Foxconn MSA.pdf",
    "doc_18": "VIAC Non-Disclosure Agreement (2025).pdf",
}


def run_chunking_evaluation():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    reconstructor = StructuralReconstructor()
    benchmark_questions = get_evaluation_dataset()

    # Load canonical documents needed by benchmark
    target_doc_ids = set()
    for q in benchmark_questions:
        for d in q.target_documents:
            target_doc_ids.add(d)

    loaded_docs = {}
    for doc_id in target_doc_ids:
        needle = DOC_MAPPINGS[doc_id]
        path = get_raw_path(needle)
        loaded_docs[doc_id] = reconstructor.reconstruct_document(path, doc_id)

    # Chunk with both strategies
    sliding_chunker = FixedSlidingWindowChunker(target_chars=1000, overlap_chars=200)
    section_chunker = SectionAwareChunker(max_chars=2500, min_chars=150)

    sliding_chunks: Dict[str, List[RetrievalChunk]] = {}
    section_chunks: Dict[str, List[RetrievalChunk]] = {}

    for doc_id, doc in loaded_docs.items():
        sliding_chunks[doc_id] = sliding_chunker.chunk(doc)
        section_chunks[doc_id] = section_chunker.chunk(doc)

    # 1. Structural Chunk Statistics
    structural_stats = {}
    for strategy_name, chunk_map in [("fixed_sliding_window", sliding_chunks), ("section_aware", section_chunks)]:
        total_chunks = sum(len(c) for c in chunk_map.values())
        all_lengths = [c.char_count for c_list in chunk_map.values() for c in c_list]
        cross_page_count = sum(
            1 for c_list in chunk_map.values() for c in c_list if c.provenance.page_start != c.provenance.page_end
        )
        provenance_valid = all(
            len(c.provenance.block_ids) > 0 and len(c.provenance.bounding_boxes) > 0
            for c_list in chunk_map.values() for c in c_list
        )

        structural_stats[strategy_name] = {
            "total_chunks": total_chunks,
            "mean_char_length": round(statistics.mean(all_lengths), 1) if all_lengths else 0,
            "median_char_length": round(statistics.median(all_lengths), 1) if all_lengths else 0,
            "min_char_length": min(all_lengths) if all_lengths else 0,
            "max_char_length": max(all_lengths) if all_lengths else 0,
            "std_dev_char_length": round(statistics.stdev(all_lengths), 1) if len(all_lengths) > 1 else 0,
            "cross_page_chunks": cross_page_count,
            "provenance_retained_100_percent": provenance_valid
        }

    # 2. Benchmark Evidence Containment Evaluation
    benchmark_results = {
        "fixed_sliding_window": {"single_chunk_contained": 0, "multi_chunk_split": 0, "not_found": 0},
        "section_aware": {"single_chunk_contained": 0, "multi_chunk_split": 0, "not_found": 0}
    }

    per_question_breakdown = []

    for q in benchmark_questions:
        q_entry = {
            "question_id": q.question_id,
            "category": q.category.value,
            "is_answerable": q.is_answerable,
            "target_documents": q.target_documents,
            "strategies": {}
        }

        for strategy_name, chunk_map in [("fixed_sliding_window", sliding_chunks), ("section_aware", section_chunks)]:
            # Check containment across evidence requirements
            req_statuses = []
            for req in q.evidence_requirements:
                doc_id = req.document_id
                chunks = chunk_map.get(doc_id, [])

                def normalize_txt(s: str) -> str:
                    s = s.replace('\xa0', ' ').replace('\u00a0', ' ')
                    s = re.sub(r'[\r\n\t]+', ' ', s)
                    s = re.sub(r'[^a-zA-Z0-9\s]', '', s)
                    return re.sub(r'\s+', ' ', s).strip().lower()

                # Find which chunks contain each key phrase
                found_in_single = False
                for c in chunks:
                    c_norm = normalize_txt(c.text)
                    if all(normalize_txt(phrase) in c_norm for phrase in req.key_phrases):
                        found_in_single = True
                        break

                if found_in_single:
                    req_statuses.append("single_chunk")
                else:
                    # Check if phrases are scattered across multiple chunks
                    all_chunks_norm = [normalize_txt(c.text) for c in chunks]
                    scattered = all(
                        any(normalize_txt(phrase) in cn for cn in all_chunks_norm)
                        for phrase in req.key_phrases
                    )
                    req_statuses.append("multi_chunk_split" if scattered else "not_found")

            # Aggregate for question
            if all(s == "single_chunk" for s in req_statuses):
                benchmark_results[strategy_name]["single_chunk_contained"] += 1
                q_entry["strategies"][strategy_name] = "single_chunk_contained"
            elif any(s in ("single_chunk", "multi_chunk_split") for s in req_statuses):
                benchmark_results[strategy_name]["multi_chunk_split"] += 1
                q_entry["strategies"][strategy_name] = "multi_chunk_split"
            else:
                benchmark_results[strategy_name]["not_found"] += 1
                q_entry["strategies"][strategy_name] = "not_found"

        per_question_breakdown.append(q_entry)

    # Save output
    summary = {
        "benchmark_question_count": len(benchmark_questions),
        "target_documents_analyzed": list(target_doc_ids),
        "structural_statistics": structural_stats,
        "evidence_containment_summary": benchmark_results,
        "per_question_breakdown": per_question_breakdown
    }

    out_file = OUTPUT_DIR / "chunking_benchmark_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Chunking evaluation completed. Output saved to {out_file}")
    return summary


if __name__ == "__main__":
    run_chunking_evaluation()
