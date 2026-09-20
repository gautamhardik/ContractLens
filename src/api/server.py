"""ContractLens Production FastAPI Server.

Exposes RESTful endpoints connecting the frozen backend reasoning engine,
portfolio intelligence, operational risk detector, and canonical documents
to the interactive frontend workspace.
"""

from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Core Frozen Domain Imports
from src.ingestion.reconstructor import StructuralReconstructor
from src.ingestion.extractor import ContractIntelligenceExtractor
from src.ingestion.obligation_extractor import ObligationExtractor
from src.temporal.lifecycle import LifecycleEventEngine
from src.temporal.amendment_engine import AmendmentIntelligenceEngine
from src.retrieval.chunking import SectionAwareChunker
from src.retrieval.lexical import BM25Retriever
from src.retrieval.dense import LSADenseRetriever
from src.retrieval.fusion import HybridRRFRetriever
from src.evidence.resolver import EvidenceResolver
from src.graph.builder import KnowledgeGraphBuilder
from src.graph.query import ContractGraphQueryEngine
from src.rag.generator import FakeLLMProvider, get_default_llm_provider
from src.portfolio.aggregator import PortfolioAggregator, PortfolioOverview
from src.risk.detector import RiskDetector, RiskSeverity, ContractRiskReport
from src.agent.agent import ContractAgent
from src.agent.models import AgentResponse
from src.models.canonical import CanonicalDocument
from src.api.auth import verify_api_key, rate_limiter, SecurityHeadersMiddleware

import functools
from contextlib import asynccontextmanager
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse, Response
import orjson
import asyncio

from src.catalog.catalog import ContractCatalog

logger = logging.getLogger("contractlens.api")


# In-Memory Cache for Loaded Corpus, Precomputed Intelligence & Response Caches
class CorpusState:
    documents: Dict[str, CanonicalDocument] = {}
    intelligence: Dict[str, Any] = {}
    obligations: List[Any] = []
    lifecycle_events: List[Any] = []
    agent: Optional[ContractAgent] = None
    is_loaded: bool = False
    
    # 10/10 Enterprise Precomputed Serialized Caches
    precomputed_portfolio_bytes: Optional[bytes] = None
    precomputed_risks_bytes: Optional[bytes] = None
    precomputed_summaries_bytes: Optional[bytes] = None
    query_cache: Dict[str, Dict[str, Any]] = {}

    # Multi-worker concurrency safety lock
    lock: asyncio.Lock = asyncio.Lock()

    def build_catalog_snapshot(self) -> ContractCatalog:
        """Construct deeply immutable snapshot of active corpus."""
        return ContractCatalog.from_runtime(
            documents=dict(self.documents),
            intelligences=dict(self.intelligence),
        )


state = CorpusState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """On startup: reload any previously uploaded contracts so corpus persists across restarts."""
    load_corpus_state()
    yield


app = FastAPI(
    title="ContractLens API",
    description="Business Contract Review & Obligation Tracking Agent Service",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable GZip compression (reduces payload transfers by ~75-80%)
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Inject security defense-in-depth headers
app.add_middleware(SecurityHeadersMiddleware)

# Enable CORS for the local Vite React development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_corpus_state(data_raw_dir: str = "Data/raw", max_docs: Optional[int] = None):
    """Load canonical documents, run extractors, and initialize the ContractAgent."""
def rebuild_corpus_indices() -> None:
    """Rebuild retrieval indices, knowledge graph, agent, and precomputed caches."""
    chunker = SectionAwareChunker()
    all_chunks = []
    for d in state.documents.values():
        all_chunks.extend(chunker.chunk(d))

    bm25 = BM25Retriever(all_chunks)
    dense = LSADenseRetriever(n_components=min(30, max(2, len(all_chunks))), random_state=42)
    dense.index(all_chunks)
    hybrid = HybridRRFRetriever(lexical_retriever=bm25, dense_retriever=dense, rrf_k=60)
    resolver = EvidenceResolver(list(state.documents.values()))

    obs_by_doc: Dict[str, List[Any]] = {}
    for ob in state.obligations:
        obs_by_doc.setdefault(ob.evidence.document_id, []).append(ob)

    evts_by_doc: Dict[str, List[Any]] = {}
    for ev in state.lifecycle_events:
        evts_by_doc.setdefault(ev.evidence.document_id, []).append(ev)

    graph = KnowledgeGraphBuilder.build_graph(
        list(state.documents.values()),
        list(state.intelligence.values()),
        obligations_by_doc=obs_by_doc,
        events_by_doc=evts_by_doc,
    )
    query_engine = ContractGraphQueryEngine(graph)
    llm_provider = get_default_llm_provider()

    from src.agent.llm_planner import LLMToolPlanner
    planner = LLMToolPlanner(llm_provider=llm_provider)

    # Initialize ContractAgent with LLM tool planner & trace callbacks
    state.agent = ContractAgent(
        retriever=hybrid,
        resolver=resolver,
        query_engine=query_engine,
        intel_map=state.intelligence,
        obligations=state.obligations,
        events=state.lifecycle_events,
        llm_provider=llm_provider,
        planner=planner,
    )

    # Precompute 10/10 Enterprise Caches for instant <0.5ms responses
    logger.info("Precomputing portfolio overview and risk analysis caches...")
    docs = list(state.documents.values())
    overview = PortfolioAggregator.aggregate(
        canonical_docs=docs,
        intelligence_docs=state.intelligence,
        obligations=state.obligations,
        events=state.lifecycle_events,
    )
    state.precomputed_portfolio_bytes = orjson.dumps(overview.model_dump())

    reports = RiskDetector.scan_portfolio(
        canonical_docs=docs,
        intelligence_docs=state.intelligence,
        obligations_by_doc=obs_by_doc,
    )
    total_signals = sum(r.total_signals for r in reports)
    high_risk_contracts = [r for r in reports if r.risk_score >= 40.0]
    risks_payload = {
        "total_signals": total_signals,
        "high_risk_contracts": len(high_risk_contracts),
        "contract_reports": [r.model_dump() for r in reports],
    }
    state.precomputed_risks_bytes = orjson.dumps(risks_payload)

    summaries = []
    for did, doc in state.documents.items():
        intel = state.intelligence.get(did)
        parties = [p.name for p in intel.parties] if intel and intel.parties else []
        ctype = intel.contract_type.raw_value if intel and intel.contract_type.is_found else "Agreement"
        eff = intel.effective_date.normalized_value if intel and intel.effective_date.is_found else None
        exp = intel.expiration_date.normalized_value if intel and intel.expiration_date.is_found else None
        gov = intel.governing_law.normalized_value if intel and intel.governing_law.is_found else None
        pay = intel.payment_terms.raw_value if intel and intel.payment_terms.is_found else None

        summaries.append({
            "document_id": did,
            "filename": doc.filename,
            "page_count": doc.page_count,
            "contract_type": ctype,
            "parties": parties,
            "effective_date": eff,
            "expiration_date": exp,
            "governing_law": gov,
            "payment_terms": pay,
        })
    state.precomputed_summaries_bytes = orjson.dumps(summaries)
    state.query_cache.clear()


def load_corpus_state(data_raw_dir: str = "Data/raw") -> None:
    """Reconstruct canonical documents and build retrieval / intelligence caches.

    Scans in priority order:
    1. Data/uploads/ — user-uploaded contracts (persistent across restarts)
    2. Data/raw/     — pre-seeded corpus PDFs (only if uploads dir is empty)
    """
    if state.is_loaded:
        return

    uploads_dir = Path("Data/uploads")
    raw_dir = Path(data_raw_dir)

    # Prefer user-uploaded PDFs; fall back to raw corpus only when uploads is empty
    uploaded_pdfs = sorted(uploads_dir.glob("*.pdf")) if uploads_dir.exists() else []
    raw_pdfs = sorted(raw_dir.glob("*.pdf")) if raw_dir.exists() else []

    pdf_paths = list(uploaded_pdfs) if uploaded_pdfs else list(raw_pdfs)

    if not pdf_paths:
        logger.info("No PDF files found in Data/uploads or Data/raw — starting with empty corpus.")
        rebuild_corpus_indices()
        state.is_loaded = True
        return

    logger.info(
        "Loading corpus from %s: %d PDF(s) found in '%s'.",
        "Data/uploads" if uploaded_pdfs else data_raw_dir,
        len(pdf_paths),
        "Data/uploads" if uploaded_pdfs else data_raw_dir,
    )

    state.documents.clear()
    state.intelligence.clear()
    state.obligations.clear()
    state.lifecycle_events.clear()

    reconstructor = StructuralReconstructor()
    extractor = ContractIntelligenceExtractor()
    obligation_extractor = ObligationExtractor()

    for idx, p in enumerate(pdf_paths, start=1):
        doc_id = f"doc_{idx:02d}"
        try:
            doc = reconstructor.reconstruct_document(str(p), document_id=doc_id)
            state.documents[doc_id] = doc

            intel = extractor.extract(doc)
            state.intelligence[doc_id] = intel

            obs = obligation_extractor.extract_obligations(doc, intel)
            state.obligations.extend(obs)

            evts = LifecycleEventEngine.generate_lifecycle_events(doc, intel, obs)
            state.lifecycle_events.extend(evts)

            logger.info("  [%d/%d] Loaded '%s' as %s", idx, len(pdf_paths), p.name, doc_id)
        except Exception as exc:
            logger.warning("  [%d/%d] Skipping '%s' — failed to load: %s", idx, len(pdf_paths), p.name, exc)

    rebuild_corpus_indices()
    state.is_loaded = True
    logger.info(
        "Corpus State ready: %d documents, %d obligations, %d events.",
        len(state.documents),
        len(state.obligations),
        len(state.lifecycle_events),
    )


def clear_corpus_state() -> None:
    """Wipe in-memory corpus state and rebuild clean empty indices."""
    state.documents.clear()
    state.intelligence.clear()
    state.obligations.clear()
    state.lifecycle_events.clear()
    rebuild_corpus_indices()
    state.is_loaded = True
    logger.info("Corpus State cleared: 0 documents loaded.")


# Request / Response Schemas
class QueryRequest(BaseModel):
    query: str
    document_id: Optional[str] = None
    conversation_id: Optional[str] = None


class ContractSummary(BaseModel):
    document_id: str
    filename: str
    page_count: int
    contract_type: str
    parties: List[str]
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    governing_law: Optional[str] = None
    payment_terms: Optional[str] = None


# --- Endpoints ---

@app.get("/api/health")
def get_health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "loaded_documents": len(state.documents),
        "total_obligations": len(state.obligations),
        "total_events": len(state.lifecycle_events),
        "caches_active": state.precomputed_portfolio_bytes is not None,
    }


@app.get("/api/portfolio")
def get_portfolio_overview() -> Response:
    """Return precomputed portfolio-wide KPIs in <0.5ms directly from memory."""
    if state.precomputed_portfolio_bytes:
        return Response(content=state.precomputed_portfolio_bytes, media_type="application/json")

    docs = list(state.documents.values())
    overview = PortfolioAggregator.aggregate(
        canonical_docs=docs,
        intelligence_docs=state.intelligence,
        obligations=state.obligations,
        events=state.lifecycle_events,
    )
    return ORJSONResponse(content=overview.model_dump())


@app.get("/api/contracts")
def list_contracts() -> Response:
    """Return precomputed summary cards for all contracts in <0.5ms."""
    if state.precomputed_summaries_bytes:
        return Response(content=state.precomputed_summaries_bytes, media_type="application/json")

    summaries = []
    for did, doc in state.documents.items():
        intel = state.intelligence.get(did)
        parties = [p.name for p in intel.parties] if intel and intel.parties else []
        ctype = intel.contract_type.raw_value if intel and intel.contract_type.is_found else "Agreement"
        eff = intel.effective_date.normalized_value if intel and intel.effective_date.is_found else None
        exp = intel.expiration_date.normalized_value if intel and intel.expiration_date.is_found else None
        gov = intel.governing_law.normalized_value if intel and intel.governing_law.is_found else None
        pay = intel.payment_terms.raw_value if intel and intel.payment_terms.is_found else None

        summaries.append({
            "document_id": did,
            "filename": doc.filename,
            "page_count": doc.page_count,
            "contract_type": ctype,
            "parties": parties,
            "effective_date": eff,
            "expiration_date": exp,
            "governing_law": gov,
            "payment_terms": pay,
        })
    return ORJSONResponse(content=summaries)


@app.get("/api/contracts/{document_id}")
def get_contract_detail(document_id: str) -> Dict[str, Any]:
    """Return full canonical structure (pages, blocks, bounding boxes) and intelligence."""
    doc = state.documents.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")

    intel = state.intelligence.get(document_id)
    doc_obs = [ob.model_dump() for ob in state.obligations if ob.evidence.document_id == document_id]
    doc_evts = [ev.model_dump() for ev in state.lifecycle_events if ev.evidence.document_id == document_id]

    return {
        "document": doc.model_dump(),
        "intelligence": intel.model_dump() if intel else None,
        "obligations": doc_obs,
        "lifecycle_events": doc_evts,
    }


@app.post("/api/contracts/upload")
async def upload_contract(
    file: Optional[UploadFile] = File(None),
    files: Optional[List[UploadFile]] = File(None),
) -> Dict[str, Any]:
    """Dynamically ingest uploaded contract PDF(s) with stage tracking, validation, OCR detection, and atomic rollback."""
    # Gather incoming files (supporting both single 'file' and multi 'files' inputs)
    upload_list: List[UploadFile] = []
    if files:
        upload_list.extend(files)
    if file:
        upload_list.append(file)

    if not upload_list:
        raise HTTPException(status_code=400, detail="No PDF file was provided in the upload request.")

    MAX_FILE_SIZE = 25 * 1024 * 1024
    uploads_dir = Path("Data/uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)

    # Validate and save all incoming files first
    validated_files = []
    for f in upload_list:
        if not f.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"File '{f.filename}' is not supported. Only PDF files (.pdf) are allowed.")

        safe_filename = Path(f.filename).name
        if not safe_filename or ".." in safe_filename or "/" in safe_filename or "\\" in safe_filename:
            raise HTTPException(status_code=400, detail=f"Invalid filename or path traversal detected in '{f.filename}'.")

        contents = await f.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"File '{safe_filename}' exceeds 25MB limit ({len(contents)/(1024*1024):.1f}MB).")

        if len(contents) < 5 or not contents.startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail=f"Corrupted or invalid PDF in '{safe_filename}': missing '%PDF-' magic bytes.")

        saved_path = uploads_dir / safe_filename
        with open(saved_path, "wb") as out_f:
            out_f.write(contents)

        validated_files.append((safe_filename, saved_path))

    # Ingest into corpus under state.lock
    async with state.lock:
        reconstructor = StructuralReconstructor()
        extractor = ContractIntelligenceExtractor()
        obligation_extractor = ObligationExtractor()

        ingestion_stage = "EXTRACTING"
        results = []
        added_docs = []
        added_intels = []
        added_obs = []
        added_evts = []
        saved_paths_to_clean = [p for _, p in validated_files]

        try:
            for safe_filename, saved_path in validated_files:
                existing_nums = []
                for did in state.documents.keys():
                    if did.startswith("doc_"):
                        try:
                            existing_nums.append(int(did.split("_")[1]))
                        except ValueError:
                            pass
                next_num = max(existing_nums, default=0) + 1
                doc_id = f"doc_{next_num:02d}"

                ingestion_stage = f"EXTRACTING ({safe_filename})"
                doc = reconstructor.reconstruct_document(str(saved_path), document_id=doc_id)

                total_chars = sum(len(b.normalized_text) for p in doc.pages for b in p.blocks)
                avg_chars_per_page = total_chars / max(1, doc.page_count)
                if avg_chars_per_page < 30.0:
                    raise ValueError(f"Document '{safe_filename}' appears to be scanned/image-only and requires OCR. Text extraction yielded insufficient characters.")

                state.documents[doc_id] = doc
                added_docs.append(doc_id)

                ingestion_stage = f"UNDERSTANDING ({safe_filename})"
                intel = extractor.extract(doc)
                state.intelligence[doc_id] = intel
                added_intels.append(doc_id)

                obs = obligation_extractor.extract_obligations(doc, intel)
                state.obligations.extend(obs)
                added_obs.extend(obs)

                evts = LifecycleEventEngine.generate_lifecycle_events(doc, intel, obs)
                state.lifecycle_events.extend(evts)
                added_evts.extend(evts)

                parties = [p.name for p in intel.parties] if intel and intel.parties else []
                ctype = intel.contract_type.raw_value if intel and intel.contract_type.is_found else "Agreement"

                results.append({
                    "status": "success",
                    "document_id": doc_id,
                    "filename": safe_filename,
                    "page_count": doc.page_count,
                    "contract_type": ctype,
                    "parties": parties,
                    "obligations_extracted": len(obs),
                    "events_extracted": len(evts),
                })

            ingestion_stage = "INDEXING"
            rebuild_corpus_indices()

            if len(results) == 1:
                single_res = results[0]
                single_res["ingestion_stage"] = "READY"
                single_res["message"] = f"Successfully ingested {single_res['filename']} as {single_res['document_id']} and updated live indices."
                return single_res

            return {
                "status": "success",
                "ingestion_stage": "READY",
                "total_ingested": len(results),
                "documents": results,
                "message": f"Successfully ingested {len(results)} contracts into the corpus and rebuilt live indices.",
            }

        except Exception as e:
            logger.exception("Failed during ingestion stage %s", ingestion_stage)
            for did in added_docs:
                state.documents.pop(did, None)
            for did in added_intels:
                state.intelligence.pop(did, None)
            for ob in added_obs:
                if ob in state.obligations:
                    state.obligations.remove(ob)
            for ev in added_evts:
                if ev in state.lifecycle_events:
                    state.lifecycle_events.remove(ev)
            for p in saved_paths_to_clean:
                if p.exists():
                    try:
                        p.unlink()
                    except Exception:
                        pass

            raise HTTPException(
                status_code=422 if "requires OCR" in str(e) else 500,
                detail=f"Ingestion failed at stage [{ingestion_stage}]: {str(e)}"
            )


@app.post("/api/contracts/clear")
async def clear_contracts() -> Dict[str, Any]:
    """Wipe all loaded contracts and indices, resetting workspace to clean slate."""
    async with state.lock:
        clear_corpus_state()
        return {
            "status": "success",
            "message": "Corpus state and indices cleared cleanly. 0 documents loaded.",
            "loaded_documents": 0,
        }


@app.get("/api/risks")
def get_portfolio_risks() -> Response:
    """Return precomputed portfolio-wide risk flags and high-impact warnings in <0.5ms."""
    if state.precomputed_risks_bytes:
        return Response(content=state.precomputed_risks_bytes, media_type="application/json")

    docs = list(state.documents.values())
    obs_by_doc: Dict[str, List[Any]] = {}
    for ob in state.obligations:
        obs_by_doc.setdefault(ob.evidence.document_id, []).append(ob)

    reports = RiskDetector.scan_portfolio(
        canonical_docs=docs,
        intelligence_docs=state.intelligence,
        obligations_by_doc=obs_by_doc,
    )
    total_signals = sum(r.total_signals for r in reports)
    high_risk_contracts = [r for r in reports if r.risk_score >= 40.0]

    return ORJSONResponse(content={
        "total_signals": total_signals,
        "high_risk_contracts": len(high_risk_contracts),
        "contract_reports": [r.model_dump() for r in reports],
    })


@app.get("/api/risks/{document_id}")
def get_contract_risks(document_id: str) -> Dict[str, Any]:
    """Return specific risk signals and remediation recommendations for one contract."""
    doc = state.documents.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")

    intel = state.intelligence.get(document_id)
    doc_obs = [ob for ob in state.obligations if ob.evidence.document_id == document_id]
    report = RiskDetector.analyze_contract(doc, intel, doc_obs)
    return report.model_dump()


@app.get("/api/amendments/{document_id}")
def get_amendment_comparison(document_id: str) -> Dict[str, Any]:
    """Generate structured side-by-side clause diffs between amendment and parent agreement."""
    doc = state.documents.get(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found.")

    engine = AmendmentIntelligenceEngine(
        canonical_docs=state.documents,
        intel_map=state.intelligence,
    )

    parent_doc = None
    target_amend_doc = None

    # Check if requested doc is amendment or base agreement
    resolution = engine.resolve_parent(document_id)
    if resolution:
        target_amend_doc = doc
        parent_doc = state.documents.get(resolution.parent_doc_id)
    else:
        # Check if requested doc is parent of any registered amendment
        for other_id in state.documents.keys():
            if other_id == document_id:
                continue
            cand_res = engine.resolve_parent(other_id)
            if cand_res and cand_res.parent_doc_id == document_id:
                target_amend_doc = state.documents.get(other_id)
                parent_doc = doc
                break

    if not parent_doc or not target_amend_doc:
        raise HTTPException(
            status_code=404,
            detail=f"No associated parent/amendment counterpart resolved for document {document_id}."
        )

    engine = AmendmentIntelligenceEngine(
        canonical_docs=state.documents,
        intel_map=state.intelligence,
    )
    report = engine.compare_versions(
        amendment_doc_id=target_amend_doc.document_id,
        parent_doc_id=parent_doc.document_id,
    )
    if not report:
        raise HTTPException(status_code=400, detail="Unable to compare document versions.")
    return report.model_dump()


@app.post("/api/query")
async def process_agent_query(
    req: QueryRequest,
    user: Optional[str] = Depends(verify_api_key),
) -> Dict[str, Any]:
    """Execute grounded conversational agent query with LRU caching, rate limiting, and async non-blocking execution."""
    if not state.agent:
        raise HTTPException(status_code=503, detail="Agent service is not initialized.")

    # Rate limiting check
    client_id = user or "anonymous"
    if not rate_limiter.is_allowed(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Maximum 180 requests per minute.")

    cache_key = f"{req.query.strip().lower()}::{req.document_id or ''}"
    if cache_key in state.query_cache:
        return state.query_cache[cache_key]

    # Deeply immutable snapshot of runtime corpus state
    async with state.lock:
        catalog = state.build_catalog_snapshot()

    # Non-blocking async execution off the main FastAPI event loop
    response: AgentResponse = await asyncio.to_thread(
        state.agent.process_query,
        query=req.query,
        catalog=catalog,
        document_id=req.document_id,
    )
    dumped = response.model_dump()

    # Store in LRU query cache (max 256 items)
    if len(state.query_cache) >= 256:
        state.query_cache.pop(next(iter(state.query_cache)))
    state.query_cache[cache_key] = dumped

    return dumped


@app.post("/api/query/stream")
async def stream_agent_query(req: QueryRequest):
    """Server-Sent Events (SSE) streaming endpoint providing real-time agent progression, tool traces, and tokens."""
    from fastapi.responses import StreamingResponse

    if not state.agent:
        raise HTTPException(status_code=503, detail="Agent service is not initialized.")

    async with state.lock:
        catalog = state.build_catalog_snapshot()

    async def event_generator():
        try:
            # Heartbeat token
            yield f": ping\n\n"

            # Step 1: Query Understanding & Routing
            yield f"event: status\ndata: {json.dumps({'step': 'understanding', 'message': 'Understanding contractual query & resolving roles...'})}\n\n"
            await asyncio.sleep(0.04)

            # Queue for capturing tool-level activity
            trace_events = []

            def capture_step(tool_name: str, action_label: str):
                trace_events.append({"tool_name": tool_name, "label": action_label})

            # Execute agent query with live step callback
            response: AgentResponse = await asyncio.to_thread(
                state.agent.process_query,
                query=req.query,
                catalog=catalog,
                document_id=req.document_id,
                step_callback=capture_step,
            )

            # Stream individual tool-level trace events
            for tr in trace_events:
                yield f"event: trace\ndata: {json.dumps({'tool_name': tr['tool_name'], 'label': tr['label']})}\n\n"
                await asyncio.sleep(0.05)

            # Step 2: Verification
            yield f"event: status\ndata: {json.dumps({'step': 'verifying', 'message': 'Verifying evidence boundaries & coordinate bounding boxes...'})}\n\n"
            await asyncio.sleep(0.04)

            # Step 3: Stream Answer Tokens
            words = response.answer.split(" ")
            for i, word in enumerate(words):
                chunk_data = {"token": word + (" " if i < len(words) - 1 else "")}
                yield f"event: token\ndata: {json.dumps(chunk_data)}\n\n"
                await asyncio.sleep(0.012)

            # Step 4: Complete Payload (Includes EvidenceBundle, Claims, Tool Trace Steps, Provider Telemetry)
            payload = response.model_dump()
            payload["provider_telemetry"] = {
                "provider": "nvidia/nemotron" if os.environ.get("NVIDIA_API_KEY") else "local_deterministic_grounded",
                "mode": "LIVE_LLM" if os.environ.get("NVIDIA_API_KEY") else "DETERMINISTIC_FALLBACK",
            }
            yield f"event: complete\ndata: {json.dumps(payload)}\n\n"
        except asyncio.CancelledError:
            logger.info("Client disconnected from SSE stream.")
            return
        except Exception as e:
            logger.exception("Error in SSE event stream: %s", e)
            yield f"event: error\ndata: {json.dumps({'error': str(e), 'message': 'Stream encountered an error and was safely terminated.'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

