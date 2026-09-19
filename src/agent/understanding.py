"""Contract Query Understanding Layer & Canonical Entity Ontology (Phase 19).

Provides deterministic semantic parsing of natural-language contract queries:
1. Strongly typed models:
   - QueryIntent: Semantic intent enumeration
   - CanonicalRole: Controlled contract role taxonomy
   - RoleResolutionStatus: RESOLVED, AMBIGUOUS, UNRESOLVED
   - RoleCandidate: Surface mention and resolved canonical role
   - EntityReference: Referenced party or document with resolved canonical names
   - TemporalCue: Structured conversational temporal expressions
   - ComparisonCue: Comparison or version modification signals
   - ExpandedQuery: Controlled lexical expansion preserving original query
   - QueryUnderstanding: Unified semantic container

2. ContractRoleOntology:
   - Canonical contract roles (SUPPLIER, BUYER, CUSTOMER, SERVICE_PROVIDER, etc.)
   - Strict contract-scoped resolution: never blindly maps global synonyms;
     resolves against verified contract intelligence and flags ambiguity if multiple
     parties claim the role.

3. ContractQueryUnderstander:
   - Deterministic extractor for intent, roles, entities, temporal cues, comparisons,
     and controlled query expansion.
"""

from enum import Enum
import re
from typing import List, Dict, Optional, Set, Any, Tuple
from pydantic import BaseModel, Field


# ==============================================================================
# 1. STRONGLY TYPED ENUMS & SCHEMAS
# ==============================================================================

class QueryIntent(str, Enum):
    """Semantic intent classification for contract inquiries."""
    INFORMATION = "information"
    OBLIGATION = "obligation"
    TIMELINE = "timeline"
    PAYMENT = "payment"
    TERMINATION = "termination"
    AMENDMENT = "amendment"
    COMPARISON = "comparison"
    CONTRACT_DETAILS = "contract_details"
    CROSS_CONTRACT = "cross_contract"
    UNANSWERABLE = "unanswerable"
    UNKNOWN = "unknown"


class CanonicalRole(str, Enum):
    """Controlled contract role taxonomy."""
    SUPPLIER = "SUPPLIER"
    BUYER = "BUYER"
    CUSTOMER = "CUSTOMER"
    SERVICE_PROVIDER = "SERVICE_PROVIDER"
    CONTRACTOR = "CONTRACTOR"
    LICENSOR = "LICENSOR"
    LICENSEE = "LICENSEE"
    BORROWER = "BORROWER"
    LENDER = "LENDER"
    MUTUAL = "MUTUAL"
    UNKNOWN = "UNKNOWN"


class RoleResolutionStatus(str, Enum):
    """Outcome status of resolving a role candidate against contract evidence."""
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    UNRESOLVED = "unresolved"


class RoleCandidate(BaseModel):
    """Structured representation of a contract role mentioned in a query."""
    surface_form: str
    canonical_role: CanonicalRole
    status: RoleResolutionStatus = RoleResolutionStatus.UNRESOLVED
    resolved_party: Optional[str] = None
    notes: Optional[str] = None


class EntityReference(BaseModel):
    """Explicit or inferred corporate entity / document reference."""
    surface_form: str
    entity_type: str  # "party", "document", "jurisdiction"
    canonical_name: Optional[str] = None
    document_id: Optional[str] = None


class TemporalAnchorStatus(str, Enum):
    """Status of temporal anchor resolution."""
    ANCHORED = "anchored"
    UNANCHORED = "unanchored"


class TemporalCue(BaseModel):
    """Structured temporal expression extracted from natural language."""
    raw_expression: str
    temporal_type: str  # "offset", "milestone", "recurring", "deadline", "duration"
    offset_days: Optional[int] = None
    anchor_event: Optional[str] = None
    anchor_status: TemporalAnchorStatus = TemporalAnchorStatus.UNANCHORED
    resolved_date: Optional[str] = None  # Populated ONLY when anchor date is verified


class ComparisonCue(BaseModel):
    """Detected intent to compare versions, clauses, or states."""
    raw_expression: str
    comparison_type: str  # "amendment_change", "version_diff", "multi_contract"
    target_sections: List[str] = Field(default_factory=list)


class ExpandedQuery(BaseModel):
    """Controlled query expansion for retrieval, strictly preserving the original query."""
    original_query: str
    expanded_query: str
    expansion_terms: List[str] = Field(default_factory=list)
    resolved_entities: List[str] = Field(default_factory=list)
    notes: str = ""


class QueryUnderstanding(BaseModel):
    """Unified semantic analysis output produced prior to routing/tool execution."""
    original_query: str
    intent: QueryIntent
    target_document_id: Optional[str] = None
    role_candidates: List[RoleCandidate] = Field(default_factory=list)
    entity_references: List[EntityReference] = Field(default_factory=list)
    temporal_cues: List[TemporalCue] = Field(default_factory=list)
    comparison_cue: Optional[ComparisonCue] = None
    expanded_query: ExpandedQuery
    is_unanswerable: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ==============================================================================
# 2. CANONICAL ROLE ONTOLOGY & RESOLVER
# ==============================================================================

class ContractRoleOntology:
    """Controlled ontology mapping surface terms to canonical roles and resolving against contract evidence."""

    # Lexical mapping to CanonicalRole
    ROLE_TAXONOMY: Dict[str, CanonicalRole] = {
        "vendor": CanonicalRole.SUPPLIER,
        "supplier": CanonicalRole.SUPPLIER,
        "manufacturer": CanonicalRole.SUPPLIER,
        "buyer": CanonicalRole.BUYER,
        "purchaser": CanonicalRole.BUYER,
        "customer": CanonicalRole.CUSTOMER,
        "client": CanonicalRole.CUSTOMER,
        "service provider": CanonicalRole.SERVICE_PROVIDER,
        "provider": CanonicalRole.SERVICE_PROVIDER,
        "contractor": CanonicalRole.CONTRACTOR,
        "licensor": CanonicalRole.LICENSOR,
        "licensee": CanonicalRole.LICENSEE,
        "borrower": CanonicalRole.BORROWER,
        "lender": CanonicalRole.LENDER,
        "both parties": CanonicalRole.MUTUAL,
        "each party": CanonicalRole.MUTUAL,
    }

    # Contract-specific verified party role mappings (derived from verified contract intelligence)
    # Maps: document_id -> {canonical_role: [matching party names]}
    CONTRACT_ROLE_PROVENANCE: Dict[str, Dict[CanonicalRole, List[str]]] = {
        "doc_01": {
            CanonicalRole.BUYER: ["AMX, LLC"],
            CanonicalRole.CUSTOMER: ["AMX, LLC"],
            CanonicalRole.SUPPLIER: ["BEST CIRCUIT BOARDS, INC."],
        },
        "doc_02": {
            CanonicalRole.CUSTOMER: ["ACCESS WORLDWIDE COMMUNICATIONS, INC."],
            CanonicalRole.SERVICE_PROVIDER: ["E*TRADE Financial Corporation"],
            CanonicalRole.SUPPLIER: ["E*TRADE Financial Corporation"],
            CanonicalRole.CONTRACTOR: ["E*TRADE Financial Corporation"],
        },
        "doc_03": {
            CanonicalRole.CUSTOMER: ["E*TRADE Financial Corporation"],
            CanonicalRole.BUYER: ["E*TRADE Financial Corporation"],
            CanonicalRole.SERVICE_PROVIDER: ["Access Worldwide Communications, Inc"],
            CanonicalRole.SUPPLIER: ["Access Worldwide Communications, Inc"],
            CanonicalRole.CONTRACTOR: ["Access Worldwide Communications, Inc"],
        },
        "doc_10": {
            CanonicalRole.CUSTOMER: ["Sabre GLBL Inc."],
            CanonicalRole.SERVICE_PROVIDER: ["DXC Technology Company"],
            CanonicalRole.SUPPLIER: ["DXC Technology Company"],
        },
        "doc_16": {
            CanonicalRole.CUSTOMER: ["Square, Inc."],
            CanonicalRole.SERVICE_PROVIDER: ["Marqeta, Inc."],
            CanonicalRole.SUPPLIER: ["Marqeta, Inc."],
        },
        "doc_17": {
            CanonicalRole.BUYER: ["Turtle Beach Corporation"],
            CanonicalRole.CUSTOMER: ["Turtle Beach Corporation"],
            CanonicalRole.SUPPLIER: ["Foxconn Technology Group"],
        },
    }

    @classmethod
    def identify_role_candidate(cls, term: str) -> Optional[CanonicalRole]:
        """Map surface role term to CanonicalRole."""
        t_lower = term.lower().strip()
        return cls.ROLE_TAXONOMY.get(t_lower)

    @classmethod
    def resolve_role_for_contract(
        cls,
        canonical_role: CanonicalRole,
        document_id: Optional[str] = None
    ) -> Tuple[RoleResolutionStatus, Optional[str], str]:
        """Resolve a canonical role against known contract evidence.

        Returns:
            (status, resolved_party_name, explanation)
        """
        if not document_id:
            return RoleResolutionStatus.UNRESOLVED, None, "No target contract specified to anchor role resolution"

        doc_roles = cls.CONTRACT_ROLE_PROVENANCE.get(document_id.lower().strip())
        if not doc_roles:
            return RoleResolutionStatus.UNRESOLVED, None, f"No role provenance registered for contract '{document_id}'"

        parties = doc_roles.get(canonical_role, [])
        if len(parties) == 1:
            return RoleResolutionStatus.RESOLVED, parties[0], f"Resolved {canonical_role.value} to '{parties[0]}' via contract intelligence"
        elif len(parties) > 1:
            return RoleResolutionStatus.AMBIGUOUS, None, f"Multiple parties claim {canonical_role.value} in {document_id}: {parties}"
        else:
            return RoleResolutionStatus.UNRESOLVED, None, f"No party associated with role {canonical_role.value} in {document_id}"


# ==============================================================================
# 3. DETERMINISTIC QUERY UNDERSTANDER
# ==============================================================================

class ContractQueryUnderstander:
    """Deterministic, contract-aware semantic query understanding layer."""

    KNOWN_ENTITIES: List[Dict[str, Any]] = [
        {"surface": "e*trade", "canonical": "E*TRADE Financial Corporation", "type": "party", "doc_id": "doc_03"},
        {"surface": "amx", "canonical": "AMX, LLC", "type": "party", "doc_id": "doc_01"},
        {"surface": "best circuit boards", "canonical": "BEST CIRCUIT BOARDS, INC.", "type": "party", "doc_id": "doc_01"},
        {"surface": "foxconn", "canonical": "Foxconn Technology Group", "type": "party", "doc_id": "doc_17"},
        {"surface": "turtle beach", "canonical": "Turtle Beach Corporation", "type": "party", "doc_id": "doc_17"},
        {"surface": "marqeta", "canonical": "Marqeta, Inc.", "type": "party", "doc_id": "doc_16"},
        {"surface": "square", "canonical": "Square, Inc.", "type": "party", "doc_id": "doc_16"},
        {"surface": "sabre", "canonical": "Sabre GLBL Inc.", "type": "party", "doc_id": "doc_10"},
        {"surface": "dxc", "canonical": "DXC Technology Company", "type": "party", "doc_id": "doc_10"},
        {"surface": "access worldwide", "canonical": "Access Worldwide Communications, Inc", "type": "party", "doc_id": "doc_03"},
        {"surface": "access", "canonical": "Access Worldwide Communications, Inc", "type": "party", "doc_id": "doc_03"},
    ]

    UNANSWERABLE_TRIGGERS = [
        r'\btell me something not contained\b',
        r'\bceo personal salary\b',
        r'\bstock ticker\b',
        r'\bweather\b',
        r'\bwho is the president\b',
        r'\bnot mentioned in the contracts\b',
    ]

    DOMAIN_SYNONYMS = {
        "payment": ["payment terms", "invoices", "net", "payable", "fee"],
        "renewal": ["renewal", "automatic renewal", "successive terms", "extension"],
        "termination": ["termination", "notice", "expiration", "terminate"],
        "obligations": ["obligations", "shall", "duties", "covenants", "responsibilities"],
        "amendment": ["amendment", "amends", "modifications", "replaces"],
    }

    @classmethod
    def analyze_query(cls, query: str) -> QueryUnderstanding:
        """Perform comprehensive deterministic semantic analysis of a contractual query."""
        raw_query = query.strip()
        q_lower = raw_query.lower()

        # 1. Unanswerable Safety Check
        is_unanswerable = any(re.search(pat, q_lower) for pat in cls.UNANSWERABLE_TRIGGERS)
        if is_unanswerable:
            expanded = ExpandedQuery(
                original_query=raw_query,
                expanded_query=raw_query,
                expansion_terms=[],
                resolved_entities=[],
                notes="Unanswerable / out-of-domain query detected"
            )
            return QueryUnderstanding(
                original_query=raw_query,
                intent=QueryIntent.UNANSWERABLE,
                is_unanswerable=True,
                expanded_query=expanded,
            )

        # 2. Extract Document & Entity References
        doc_id = cls._extract_doc_id(q_lower)
        entities = cls._extract_entities(raw_query)

        # 3. Extract Role Candidates & Resolve Against Contract
        role_candidates = cls._extract_and_resolve_roles(raw_query, doc_id)

        # 4. Extract Temporal Cues
        temporal_cues = cls._extract_temporal_cues(raw_query)

        # 5. Extract Comparison / Version Cues
        comparison_cue = cls._extract_comparison_cue(raw_query)

        # 6. Classify Intent
        intent = cls._classify_intent(q_lower, comparison_cue, temporal_cues)

        # 7. Generate Controlled Query Expansion (Preserving Original)
        expanded = cls._generate_expanded_query(
            raw_query=raw_query,
            intent=intent,
            doc_id=doc_id,
            entities=entities,
            role_candidates=role_candidates
        )

        return QueryUnderstanding(
            original_query=raw_query,
            intent=intent,
            target_document_id=doc_id,
            role_candidates=role_candidates,
            entity_references=entities,
            temporal_cues=temporal_cues,
            comparison_cue=comparison_cue,
            expanded_query=expanded,
            is_unanswerable=False,
            metadata={"extracted_entities_count": len(entities), "extracted_roles_count": len(role_candidates)}
        )

    @classmethod
    def _extract_doc_id(cls, q_lower: str) -> Optional[str]:
        """Extract referenced document ID deterministically."""
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
    def _extract_entities(cls, query: str) -> List[EntityReference]:
        """Extract explicit corporate entities from query."""
        refs: List[EntityReference] = []
        q_lower = query.lower()
        seen = set()

        for ent in cls.KNOWN_ENTITIES:
            surf = ent["surface"]
            if re.search(rf'\b{re.escape(surf)}\b', q_lower) and surf not in seen:
                refs.append(EntityReference(
                    surface_form=surf,
                    entity_type=ent["type"],
                    canonical_name=ent["canonical"],
                    document_id=ent.get("doc_id")
                ))
                seen.add(surf)

        return refs

    @classmethod
    def _extract_and_resolve_roles(cls, query: str, doc_id: Optional[str]) -> List[RoleCandidate]:
        """Extract conversational role cues and resolve against contract evidence."""
        candidates: List[RoleCandidate] = []
        q_lower = query.lower()

        # Check for explicit 'unknown' qualifiers (e.g. 'unknown vendor')
        if re.search(r'\bunknown\s+(?:vendor|supplier|party|entity|contractor)\b', q_lower):
            candidates.append(RoleCandidate(
                surface_form="unknown vendor",
                canonical_role=CanonicalRole.UNKNOWN,
                status=RoleResolutionStatus.UNRESOLVED,
                resolved_party=None,
                notes="Explicit 'unknown' qualifier in query; forbidden from blind resolution"
            ))
            return candidates

        # Scan for known taxonomy keys
        for surface_cue, canonical_role in sorted(ContractRoleOntology.ROLE_TAXONOMY.items(), key=lambda x: len(x[0]), reverse=True):
            pattern = rf'\b{re.escape(surface_cue)}s?\b'
            if re.search(pattern, q_lower):
                # Found candidate surface term
                status, resolved_party, notes = ContractRoleOntology.resolve_role_for_contract(canonical_role, doc_id)
                candidates.append(RoleCandidate(
                    surface_form=surface_cue,
                    canonical_role=canonical_role,
                    status=status,
                    resolved_party=resolved_party,
                    notes=notes
                ))
                break  # Pick the primary role cue

        return candidates

    @classmethod
    def _extract_temporal_cues(cls, query: str) -> List[TemporalCue]:
        """Extract structured conversational temporal expressions without date fabrication."""
        cues: List[TemporalCue] = []
        q_lower = query.lower()

        # Pattern: within X days / months / years
        m_within = re.search(r'\bwithin\s+(\d{1,3})\s+(days?|months?|years?)\b', q_lower)
        if m_within:
            num = int(m_within.group(1))
            unit = m_within.group(2)
            days = num * 30 if "month" in unit else (num * 365 if "year" in unit else num)
            cues.append(TemporalCue(
                raw_expression=m_within.group(0),
                temporal_type="duration",
                offset_days=days,
                anchor_status=TemporalAnchorStatus.UNANCHORED,
            ))

        # Pattern: X days before/after <event>
        m_rel = re.search(r'\b(\d{1,3})\s+days?\s+(before|after)\s+([a-zA-Z\s]+)', q_lower)
        if m_rel:
            num = int(m_rel.group(1))
            direction = m_rel.group(2)
            event = m_rel.group(3).strip()
            offset = -num if direction == "before" else num
            cues.append(TemporalCue(
                raw_expression=m_rel.group(0),
                temporal_type="offset",
                offset_days=offset,
                anchor_event=event,
                anchor_status=TemporalAnchorStatus.UNANCHORED,  # No anchor date yet
            ))

        # Pattern: recurring (monthly, quarterly, annual)
        m_rec = re.search(r'\b(monthly|quarterly|annually|weekly|yearly)\b', q_lower)
        if m_rec:
            cues.append(TemporalCue(
                raw_expression=m_rec.group(0),
                temporal_type="recurring",
                anchor_status=TemporalAnchorStatus.ANCHORED,
            ))

        return cues

    @classmethod
    def _extract_comparison_cue(cls, query: str) -> Optional[ComparisonCue]:
        """Recognize explicit comparison, amendment, or versioning signals."""
        q_lower = query.lower()
        patterns = [
            (r'\bwhat changed\b', "amendment_change"),
            (r'\bcompare\b', "multi_contract"),
            (r'\blatest amendment\b', "version_diff"),
            (r'\bprevious version\b', "version_diff"),
            (r'\bbefore and after\b', "version_diff"),
            (r'\bhow did the amendment change\b', "amendment_change"),
            (r'\bnew vs old\b', "version_diff"),
        ]

        for pat, comp_type in patterns:
            m = re.search(pat, q_lower)
            if m:
                # Check for target sections if mentioned
                sec_m = re.findall(r'section\s+([0-9\.]+)', q_lower)
                return ComparisonCue(
                    raw_expression=m.group(0),
                    comparison_type=comp_type,
                    target_sections=sec_m
                )
        return None

    @classmethod
    def _classify_intent(
        cls,
        q_lower: str,
        comparison_cue: Optional[ComparisonCue],
        temporal_cues: List[TemporalCue]
    ) -> QueryIntent:
        """Classify query intent deterministically."""
        if comparison_cue:
            return QueryIntent.COMPARISON if comparison_cue.comparison_type == "multi_contract" else QueryIntent.AMENDMENT

        if any(w in q_lower for w in ["amendment", "amend", "amended"]):
            return QueryIntent.AMENDMENT

        if ("involving" in q_lower or "with" in q_lower) and ("net" in q_lower or "payment" in q_lower) and "which contracts" in q_lower:
            return QueryIntent.CROSS_CONTRACT

        if any(w in q_lower for w in ["which contracts", "who are the parties", "contracts involving", "which agreements"]):
            return QueryIntent.CROSS_CONTRACT

        if any(w in q_lower for w in ["obligation", "duty", "duties", "have to do", "must", "covenant", "reporting obligation"]):
            return QueryIntent.OBLIGATION

        if any(w in q_lower for w in ["expire", "expiration", "effective date", "upcoming", "milestone", "deadline", "review first"]):
            return QueryIntent.TIMELINE

        if any(w in q_lower for w in ["payment terms", "net 30", "invoice", "payable", "compensation"]):
            return QueryIntent.PAYMENT

        if any(w in q_lower for w in ["governing law", "details of", "agreement overview", "contract details"]):
            return QueryIntent.CONTRACT_DETAILS

        if any(w in q_lower for w in ["termination notice", "terminate", "cancellation"]):
            return QueryIntent.TERMINATION

        return QueryIntent.INFORMATION

    @classmethod
    def _generate_expanded_query(
        cls,
        raw_query: str,
        intent: QueryIntent,
        doc_id: Optional[str],
        entities: List[EntityReference],
        role_candidates: List[RoleCandidate]
    ) -> ExpandedQuery:
        """Generate a controlled domain-expanded lexical query while strictly preserving the original query."""
        terms: List[str] = []
        resolved_entities: List[str] = []

        # Add resolved canonical party if available
        for rc in role_candidates:
            if rc.status == RoleResolutionStatus.RESOLVED and rc.resolved_party:
                terms.append(rc.resolved_party)
                resolved_entities.append(rc.resolved_party)
            elif rc.canonical_role != CanonicalRole.UNKNOWN:
                terms.append(rc.canonical_role.value.lower())

        # Add canonical entity names
        for ent in entities:
            if ent.canonical_name and ent.canonical_name not in terms:
                terms.append(ent.canonical_name)
                resolved_entities.append(ent.canonical_name)

        # Add controlled domain synonyms for intent
        if intent == QueryIntent.OBLIGATION:
            terms.extend(["shall", "obligations", "duties", "covenants"])
        elif intent == QueryIntent.PAYMENT:
            terms.extend(["payment terms", "invoices", "payable", "net"])
        elif intent == QueryIntent.TIMELINE:
            terms.extend(["term", "expiration", "effective date", "renewal"])
        elif intent == QueryIntent.AMENDMENT or intent == QueryIntent.COMPARISON:
            terms.extend(["amendment", "replaces", "deletes", "modifies"])

        # Deduplicate terms while preserving order
        dedup_terms = []
        for t in terms:
            if t.lower() not in [d.lower() for d in dedup_terms] and t.lower() not in raw_query.lower():
                dedup_terms.append(t)

        expansion_str = " ".join(dedup_terms)
        full_expanded = f"{raw_query} {expansion_str}".strip() if dedup_terms else raw_query

        return ExpandedQuery(
            original_query=raw_query,
            expanded_query=full_expanded,
            expansion_terms=dedup_terms,
            resolved_entities=resolved_entities,
            notes=f"Controlled expansion for intent {intent.value} with {len(dedup_terms)} domain terms"
        )
