"""Deterministic Rule-First Intent Router for ContractLens (Phase 18).

Categorizes user questions into constrained routes:
- DIRECT_GRAPH: Structured entity and cross-contract relationship questions
- DIRECT_RETRIEVAL: Clause-specific, semantic, or section-level text queries
- CONTRACT_DETAILS: Metadata, parties, governing law, and general overview
- OBLIGATION_QUERY: Operational commitments, actions, and covenants
- TIMELINE_QUERY: Lifecycle milestones, renewals, and expiration dates
- AMENDMENT_QUERY: Clause changes, additions, replacements, and parent linkage
- HYBRID_REASONING: Multi-condition questions combining graph filtering and clause evidence
- UNANSWERABLE: Safety route for questions outside contractual scope
"""

import re
from typing import Tuple, Dict, Any, Optional

from src.agent.models import AgentRouteCategory


class AgentRouter:
    """Deterministic, rule-first intent router."""

    # Lexical triggers
    GRAPH_PARTY_TRIGGERS = [
        r'\bwhich contracts involve\b',
        r'\bcontracts with\b',
        r'\bwho are the parties\b',
        r'\bparties to\b',
        r'\bcounterparties?\b',
        r'\bcontracts involving\b',
    ]

    GRAPH_TERM_TRIGGERS = [
        r'\bwhich contracts have net\b',
        r'\bwhich contracts have \d+-day\b',
        r'\bcontracts with payment terms?\b',
        r'\bwhich agreements have renewal\b',
        r'\bwhich contracts contain renewal\b',
        r'\bwhich contracts specify termination notice\b',
        r'\bwhich contracts have termination notice\b',
    ]

    OBLIGATION_TRIGGERS = [
        r'\bwhat obligations?\b',
        r'\bwhat duties\b',
        r'\bwhat must the (?:vendor|supplier|client|party)\b',
        r'\bwhat does the (?:vendor|supplier|client|party) have to\b',
        r'\breporting obligations?\b',
        r'\bcompliance obligations?\b',
        r'\bongoing covenant\b',
    ]

    TIMELINE_TRIGGERS = [
        r'\bwhen does (?:[a-zA-Z0-9\*\.\'\-]+\s+)*(?:agreement|contract|msa)?\s*expire\b',
        r'\bexpiration date\b',
        r'\beffective date\b',
        r'\bupcoming (?:contract )?events?\b',
        r'\bupcoming deadlines?\b',
        r'\btimeline\b',
        r'\bcalendar\b',
        r'\bwhat should i (?:review|worry about) (?:first|this month)\b',
    ]

    AMENDMENT_TRIGGERS = [
        r'\bwhat changed in (?:the|an)?\s*(?:[a-zA-Z0-9\*\.\'\-]+\s+)*amendment\b',
        r'\bhow did the amendment change\b',
        r'\bamendment modifications?\b',
        r'\bamends?\b',
        r'\bwhich amendments?\b',
    ]

    UNANSWERABLE_TRIGGERS = [
        r'\btell me something not contained\b',
        r'\bceo personal salary\b',
        r'\bstock ticker\b',
        r'\bweather\b',
        r'\bwho is the president\b',
        r'\bnot mentioned in the contracts\b',
    ]

    @classmethod
    def route_query(cls, query: str) -> Tuple[AgentRouteCategory, Dict[str, Any]]:
        """Determine route category and extract parameters deterministically."""
        q = query.strip()
        q_lower = q.lower()

        # 1. Check Unanswerable / Safety triggers
        for pat in cls.UNANSWERABLE_TRIGGERS:
            if re.search(pat, q_lower):
                return AgentRouteCategory.UNANSWERABLE, {}

        # 2. Check Hybrid Multi-Condition queries (e.g. "Which contracts involving E*TRADE have Net 30?")
        if ("involving" in q_lower or "with" in q_lower) and ("net" in q_lower or "payment" in q_lower) and "which contracts" in q_lower:
            party = cls._extract_party_candidate(q)
            term = cls._extract_payment_term_candidate(q)
            return AgentRouteCategory.HYBRID_REASONING, {"party": party, "payment_term": term}

        # 3. Check Amendment queries
        for pat in cls.AMENDMENT_TRIGGERS:
            if re.search(pat, q_lower):
                doc_id = cls._extract_doc_candidate(q)
                return AgentRouteCategory.AMENDMENT_QUERY, {"document_id": doc_id}

        # 4. Check Timeline / Lifecycle queries
        for pat in cls.TIMELINE_TRIGGERS:
            if re.search(pat, q_lower):
                doc_id = cls._extract_doc_candidate(q)
                return AgentRouteCategory.TIMELINE_QUERY, {"document_id": doc_id}

        # 5. Check Obligation queries
        for pat in cls.OBLIGATION_TRIGGERS:
            if re.search(pat, q_lower):
                doc_id = cls._extract_doc_candidate(q)
                party = cls._extract_party_candidate(q)
                return AgentRouteCategory.OBLIGATION_QUERY, {"document_id": doc_id, "party": party}

        # 6. Check Direct Graph Relational queries
        for pat in cls.GRAPH_PARTY_TRIGGERS:
            if re.search(pat, q_lower):
                party = cls._extract_party_candidate(q)
                return AgentRouteCategory.DIRECT_GRAPH, {"query_type": "contracts_for_party", "param": party}

        for pat in cls.GRAPH_TERM_TRIGGERS:
            if re.search(pat, q_lower):
                if "renewal" in q_lower:
                    return AgentRouteCategory.DIRECT_GRAPH, {"query_type": "contracts_with_renewal", "param": None}
                elif "termination" in q_lower:
                    days = cls._extract_number(q)
                    return AgentRouteCategory.DIRECT_GRAPH, {"query_type": "contracts_with_termination_notice", "param": str(days) if days else None}
                else:
                    term = cls._extract_payment_term_candidate(q)
                    return AgentRouteCategory.DIRECT_GRAPH, {"query_type": "contracts_with_payment_term", "param": term}

        # 7. Check Contract Details / Overview
        if (("payment terms in" in q_lower or "governing law of" in q_lower or "details of" in q_lower) 
            and ("agreement" in q_lower or "contract" in q_lower or "msa" in q_lower)):
            doc_id = cls._extract_doc_candidate(q)
            return AgentRouteCategory.CONTRACT_DETAILS, {"document_id": doc_id}

        # 8. Default fallback: Unstructured Clause-Level Retrieval
        return AgentRouteCategory.DIRECT_RETRIEVAL, {"top_k": 5}

    @classmethod
    def _extract_party_candidate(cls, query: str) -> Optional[str]:
        """Extract referenced party name from question."""
        known_parties = [
            "E*TRADE", "AMX", "Best Circuit Boards", "Foxconn", "Turtle Beach",
            "Marqeta", "Square", "Sabre", "DXC", "JPMorgan", "Guidehouse",
            "Spare Backup", "Hewlett-Packard", "Sun Microsystems", "TNS Smart Network",
            "Access Worldwide", "Access"
        ]
        for p in known_parties:
            if p.lower() in query.lower():
                return p
        return None

    @classmethod
    def _extract_doc_candidate(cls, query: str) -> Optional[str]:
        """Extract referenced contract or document from question."""
        q_lower = query.lower()
        if "access" in q_lower and "amendment" in q_lower:
            return "doc_02"
        elif "access" in q_lower:
            return "doc_03"
        elif "amx" in q_lower or "circuit board" in q_lower:
            return "doc_01"
        elif "foxconn" in q_lower or "turtle beach" in q_lower:
            return "doc_17"
        elif "square" in q_lower or "marqeta" in q_lower:
            return "doc_16"
        elif "sabre" in q_lower or "dxc" in q_lower:
            return "doc_10"
        return None

    @classmethod
    def _extract_payment_term_candidate(cls, query: str) -> Optional[str]:
        """Extract Net day requirement (e.g. '30' or 'Net 30')."""
        m = re.search(r'\b(?:net\s*)?(\d{2,3})\b', query, re.IGNORECASE)
        if m:
            return m.group(1)
        return "30"

    @classmethod
    def _extract_number(cls, query: str) -> Optional[int]:
        m = re.search(r'\b(\d{1,3})\b', query)
        return int(m.group(1)) if m else None
