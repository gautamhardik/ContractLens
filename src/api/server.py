"""ContractLens Production FastAPI Server.

Exposes RESTful endpoints connecting the frozen backend reasoning engine,
portfolio intelligence, operational risk detector, and canonical documents
to the interactive frontend workspace.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query
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
from src.rag.generator import FakeLLMProvider
from src.portfolio.aggregator import PortfolioAggregator, PortfolioOverview
from src.risk.detector import RiskDetector, RiskSeverity, ContractRiskReport
from src.agent.agent import ContractAgent
from src.agent.models import AgentResponse
from src.models.canonical import CanonicalDocument

logger = logging.getLogger("contractlens.api")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="ContractLens API",
    description="Business Contract Review & Obligation Tracking Agent Service",
    version="1.0.0",
)

# Enable CORS for the local Vite React development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-Memory Cache for Loaded Corpus & Precomputed Intelligence
class CorpusState:
    documents: Dict[str, CanonicalDocument] = {}
    intelligence: Dict[str, Any] = {}
    obligations: List[Any] = []
    lifecycle_events: List[Any] = []
    agent: Optional[ContractAgent] = None
    is_loaded: bool = False


state = CorpusState()


def load_corpus_state(data_raw_dir: str = "Data/raw", max_docs: Optional[int] = None):
    """Load canonical documents, run extractors, and initialize the ContractAgent."""
    if state.is_loaded:
        return

    logger.info("Initializing ContractLens Corpus State from %s...", data_raw_dir)
    pdf_paths = sorted(list(Path(data_raw_dir).glob("*.pdf")))
    if max_docs:
        pdf_paths = pdf_paths[:max_docs]

    state.documents.clear()
    state.intelligence.clear()
    state.obligations.clear()
    state.lifecycle_events.clear()

    reconstructor = StructuralReconstructor()
    extractor = ContractIntelligenceExtractor()
    obligation_extractor = ObligationExtractor()
    lifecycle_engine = LifecycleEventEngine()

    for idx, p in enumerate(pdf_paths, 1):
        doc_id = f"doc_{idx:02d}"
        doc = reconstructor.reconstruct_document(str(p), document_id=doc_id)
        state.documents[doc_id] = doc

        # Extract Intelligence
        intel = extractor.extract(doc)
        state.intelligence[doc_id] = intel

        # Extract Obligations
        obs = obligation_extractor.extract_obligations(doc, intel)
        state.obligations.extend(obs)

        # Extract Lifecycle Events
        evts = LifecycleEventEngine.generate_lifecycle_events(doc, intel, obs)
        state.lifecycle_events.extend(evts)

    # Build retrieval, graph, and agent components
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
    fake_llm = FakeLLMProvider()

    # Initialize frozen ContractAgent
    state.agent = ContractAgent(
        retriever=hybrid,
        resolver=resolver,
        query_engine=query_engine,
        intel_map=state.intelligence,
        obligations=state.obligations,
        events=state.lifecycle_events,
        llm_provider=fake_llm,
    )
    state.is_loaded = True
    logger.info(
        "Corpus State loaded successfully: %d documents, %d obligations, %d events.",
        len(state.documents),
        len(state.obligations),
        len(state.lifecycle_events),
    )


@app.on_event("startup")
def startup_event():
    load_corpus_state()


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
    }


@app.get("/api/portfolio")
def get_portfolio_overview() -> Dict[str, Any]:
    """Compute portfolio-wide KPIs, party matrices, governing laws, and payment terms."""
    docs = list(state.documents.values())
    overview = PortfolioAggregator.aggregate(
        canonical_docs=docs,
        intelligence_docs=state.intelligence,
        obligations=state.obligations,
        events=state.lifecycle_events,
    )
    return overview.model_dump()


@app.get("/api/contracts", response_model=List[ContractSummary])
def list_contracts() -> List[ContractSummary]:
    """List summary cards for all contracts in the active corpus."""
    summaries = []
    for did, doc in state.documents.items():
        intel = state.intelligence.get(did)
        parties = [p.name for p in intel.parties] if intel and intel.parties else []
        ctype = intel.contract_type.raw_value if intel and intel.contract_type.is_found else "Agreement"
        eff = intel.effective_date.normalized_value if intel and intel.effective_date.is_found else None
        exp = intel.expiration_date.normalized_value if intel and intel.expiration_date.is_found else None
        gov = intel.governing_law.normalized_value if intel and intel.governing_law.is_found else None
        pay = intel.payment_terms.raw_value if intel and intel.payment_terms.is_found else None

        summaries.append(ContractSummary(
            document_id=did,
            filename=doc.filename,
            page_count=doc.page_count,
            contract_type=ctype,
            parties=parties,
            effective_date=eff,
            expiration_date=exp,
            governing_law=gov,
            payment_terms=pay,
        ))
    return summaries


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


@app.get("/api/risks")
def get_portfolio_risks() -> Dict[str, Any]:
    """Scan all contracts and return portfolio-wide risk flags and high-impact warnings."""
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

    return {
        "total_signals": total_signals,
        "high_risk_contracts": len(high_risk_contracts),
        "contract_reports": [r.model_dump() for r in reports],
    }


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

    parent_doc = None
    target_amend_doc = None

    # Check if requested doc is amendment or parent
    if "amendment" in doc.filename.lower() or "amend" in doc.filename.lower():
        target_amend_doc = doc
        # Find parent
        for other_id, other_doc in state.documents.items():
            if "msa" in other_doc.filename.lower() or "agreement" in other_doc.filename.lower():
                if "access" in doc.filename.lower() and "access" in other_doc.filename.lower() and "amend" not in other_doc.filename.lower():
                    parent_doc = other_doc
                    break
    else:
        parent_doc = doc
        # Find amendment
        for other_id, other_doc in state.documents.items():
            if ("amendment" in other_doc.filename.lower() or "amend" in other_doc.filename.lower()):
                if "access" in doc.filename.lower() and "access" in other_doc.filename.lower():
                    target_amend_doc = other_doc
                    break

    if not parent_doc or not target_amend_doc:
        raise HTTPException(
            status_code=400,
            detail=f"No associated parent/amendment counterpart found for document {document_id}."
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
def process_agent_query(req: QueryRequest) -> Dict[str, Any]:
    """Execute grounded conversational agent query with tool invocation trace and citations."""
    if not state.agent:
        raise HTTPException(status_code=503, detail="Agent service is not initialized.")

    response: AgentResponse = state.agent.process_query(
        query=req.query,
    )
    return response.model_dump()
