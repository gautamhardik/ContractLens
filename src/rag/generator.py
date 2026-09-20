"""LLM Provider Abstraction and Generators for ContractLens (Phase 16).

Provides:
- BaseLLMProvider: Injectable interface for text/structured generation.
- FakeLLMProvider: Deterministic test provider returning programmed or grounded responses.
- GeminiLLMProvider: Optional live provider using Google GenAI SDK if credentials are present.
- GroundedAnswerGenerator: Formats EvidenceBundle, calls provider, and extracts structured claims.
"""

import os
import re
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple

from src.evidence.models import EvidenceBundle, EvidenceSpan
from src.rag.models import GroundedClaim, GroundedAnswer, ClaimVerificationStatus
from src.rag.prompts import SYSTEM_GROUNDING_PROMPT, format_evidence_for_prompt, build_rag_user_prompt


class BaseLLMProvider(ABC):
    """Abstract interface for LLM synthesis in ContractLens."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response string from system and user prompt."""
        pass


class FakeLLMProvider(BaseLLMProvider):
    """Deterministic, zero-cost fake provider for unit tests and offline evaluation."""

    def __init__(self, canned_responses: Optional[Dict[str, str]] = None, default_mode: str = "smart_mock"):
        self.canned_responses = canned_responses or {}
        self.default_mode = default_mode
        self.call_history: List[Dict[str, str]] = []

    def set_response_for_query(self, query: str, response_json: str):
        self.canned_responses[query.strip().lower()] = response_json

    GENERAL_DEFINITIONS: Dict[str, str] = {
        "msa": "A Master Services Agreement (MSA) is a contract that establishes the overarching terms, conditions, and legal framework governing future transactions, work orders, or Statements of Work (SOWs) between parties.",
        "master services agreement": "A Master Services Agreement (MSA) is a contract that establishes the overarching terms, conditions, and legal framework governing future transactions, work orders, or Statements of Work (SOWs) between parties.",
        "nda": "A Non-Disclosure Agreement (NDA) is a legally binding contract in which parties agree not to disclose confidential information shared during business negotiations or operational partnerships.",
        "non-disclosure agreement": "A Non-Disclosure Agreement (NDA) is a legally binding contract in which parties agree not to disclose confidential information shared during business negotiations or operational partnerships.",
        "sow": "A Statement of Work (SOW) is a transactional document under an MSA that details the specific project scope, deliverables, timelines, milestones, and fees.",
        "statement of work": "A Statement of Work (SOW) is a transactional document under an MSA that details the specific project scope, deliverables, timelines, milestones, and fees.",
        "indemnification": "Indemnification is a contractual commitment where one party agrees to compensate and protect the other party against specified losses, liabilities, damages, or third-party legal claims.",
        "governing law": "A governing law clause designates which jurisdiction's laws will interpret the contract and control in the event of any dispute.",
        "force majeure": "Force majeure frees both parties from liability or contractual obligations when an extraordinary event or circumstance beyond their control (e.g., war, natural disaster, strike) prevents performance.",
        "sla": "A Service Level Agreement (SLA) defines the expected quality, uptime, responsiveness, and performance metrics that a service provider must deliver.",
    }

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.call_history.append({"system": system_prompt, "user": user_prompt})

        # Check canned responses
        for query_key, resp in self.canned_responses.items():
            if query_key in user_prompt.lower():
                return resp

        # Check for general contractual acronyms/concepts/definitions
        q_text = user_prompt.split("USER QUESTION:")[-1].split("\n")[0].strip().lower() if "USER QUESTION:" in user_prompt else user_prompt.lower()
        is_definitional = any(w in q_text for w in ["what is a ", "what is an ", "what is ", "what does ", "define ", "meaning of ", "explain "])
        if is_definitional:
            for term, definition in self.GENERAL_DEFINITIONS.items():
                if re.search(rf"\b{re.escape(term)}\b", q_text):
                    return json.dumps({
                        "answer": definition,
                        "claims": []
                    })

        # Check for unanswerable signals or insufficient evidence
        if "no relevant contractual evidence found" in user_prompt.lower():
            return json.dumps({
                "answer": "The available contract evidence does not establish this.",
                "claims": []
            })

        # Smart mock: scans evidence blocks to formulate a grounded response referencing the matching evidence ID
        evidence_pattern = re.findall(r"\[(E\d+)\][^\n]*\n(.*?)(?=\n\[E\d+\]|\n===|$)", user_prompt, re.DOTALL)
        if evidence_pattern:
            question_part = user_prompt.split("QUESTION:")[-1].split("\n")[0].strip().lower() if "QUESTION:" in user_prompt else ""
            q_keywords = [w for w in re.findall(r"\b[a-zA-Z]{3,}\b", question_part) if w not in {"what", "which", "when", "where", "how", "the", "and", "for", "with", "this", "that", "does", "agreement", "contract"}]

            scored_matches = []
            for eid, ev_text in evidence_pattern:
                ev_lines = [l.strip() for l in ev_text.split("\n") if len(l.strip()) > 25]
                for line in ev_lines:
                    line_lower = line.lower()
                    score = sum(1 for kw in q_keywords if kw in line_lower)
                    if score > 0:
                        # Clean up punctuation
                        clean_line = line.strip().strip("-*• ")
                        if len(clean_line) > 30:
                            scored_matches.append((score, eid, clean_line))

            scored_matches.sort(key=lambda x: x[0], reverse=True)

            if scored_matches:
                selected_lines = []
                claims_list = []
                seen_texts = set()

                for score, eid, line in scored_matches[:4]:
                    # Extract complete meaningful clause statement, avoiding split on abbreviations like 'i.e.', 'e.g.', 'No.'
                    clean = line.strip().strip("-*• ")
                    # If line has multiple sentences, take the first complete one that is at least 30 chars
                    sentences = [s.strip() for s in re.split(r"(?<=[a-zA-Z0-9”\')\]])\.\s+", clean) if len(s.strip()) > 20]
                    sentence = sentences[0] if sentences else clean
                    if sentence and sentence not in seen_texts:
                        seen_texts.add(sentence)
                        if not sentence.endswith((".", ";", ":")):
                            sentence += "."
                        selected_lines.append(f"{sentence}")
                        claims_list.append({
                            "text": sentence,
                            "evidence_ids": [eid]
                        })

                if selected_lines:
                    answer_text = "\n\n".join(selected_lines)
                    return json.dumps({
                        "answer": answer_text,
                        "claims": claims_list
                    })

            # General / Conversational Overview fallback:
            # If user asks broad question ("what is the contract about", "summarize", "tell me about it")
            # and evidence spans exist, synthesize key identifying clauses rather than refusing.
            is_broad_overview = any(w in question_part for w in ["about", "summary", "summarize", "overview", "explain", "details", "scope", "cover", "tell me", "what is this"])
            if is_broad_overview or not q_keywords:
                top_overview_lines = []
                claims_list = []
                for eid, ev_text in evidence_pattern[:5]:
                    ev_lines = [l.strip().strip("-*• ") for l in ev_text.split("\n") if len(l.strip()) >= 25]
                    if ev_lines:
                        best_line = ev_lines[0]
                        sentences = [s.strip() for s in re.split(r"(?<=[a-zA-Z0-9”\')\]])\.\s+", best_line) if len(s.strip()) > 20]
                        sentence = sentences[0] if sentences else best_line
                        if not sentence.endswith((".", ";", ":")):
                            sentence += "."
                        top_overview_lines.append(f"{sentence}")
                        claims_list.append({"text": sentence, "evidence_ids": [eid]})

                if top_overview_lines:
                    intro = "Based on the contractual evidence, this agreement establishes the following core provisions and operational terms:"
                    answer_text = f"{intro}\n\n" + "\n\n".join(top_overview_lines)
                    return json.dumps({
                        "answer": answer_text,
                        "claims": claims_list
                    })

        return json.dumps({
            "answer": "The available contract evidence does not establish this.",
            "claims": []
        })


class GeminiLLMProvider(BaseLLMProvider):
    """Production provider using Google Gemini API if GEMINI_API_KEY is available."""

    def __init__(self, model_name: str = "gemini-1.5-flash", api_key: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment.")

        # Lazy import google.genai to avoid mandatory external dependency in tests
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=self.model_name,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    temperature=0.0,
                )
            )
            return response.text
        except ImportError:
            import google.generativeai as genai_legacy
            genai_legacy.configure(api_key=self.api_key)
            model = genai_legacy.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt,
                generation_config={"response_mime_type": "application/json", "temperature": 0.0}
            )
            resp = model.generate_content(user_prompt)
            return resp.text


def get_default_llm_provider() -> BaseLLMProvider:
    """Factory creating the best available production LLM provider.

    Precedence:
    1. NvidiaNIMProvider (if NVIDIA_API_KEY is present or LLM_PROVIDER=nvidia)
    2. GeminiLLMProvider (if GEMINI_API_KEY is present or LLM_PROVIDER=gemini)
    3. FakeLLMProvider (offline deterministic mode)
    """
    provider_type = os.environ.get("LLM_PROVIDER", "").strip().lower()
    
    if provider_type == "nvidia" or os.environ.get("NVIDIA_API_KEY"):
        try:
            from src.rag.nvidia_provider import NvidiaNIMProvider
            return NvidiaNIMProvider()
        except Exception:
            pass

    if provider_type == "gemini" or os.environ.get("GEMINI_API_KEY"):
        try:
            return GeminiLLMProvider()
        except Exception:
            pass

    return FakeLLMProvider()


class GroundedAnswerGenerator:
    """Orchestrates structured LLM answer generation from an EvidenceBundle."""

    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    def generate_candidate_answer(
        self,
        query: str,
        bundle: EvidenceBundle,
    ) -> Tuple[str, List[GroundedClaim], Dict[str, EvidenceSpan], float]:
        """Synthesize candidate answer and proposed claims.

        Returns:
            (answer_text, proposed_claims, evidence_map, latency_ms)
        """
        start_time = time.perf_counter()

        formatted_evidence, evidence_map = format_evidence_for_prompt(bundle, query=query)
        user_prompt = build_rag_user_prompt(query, formatted_evidence)

        # Generate response from provider
        raw_output = self.provider.generate(
            system_prompt=SYSTEM_GROUNDING_PROMPT,
            user_prompt=user_prompt
        )

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        # Parse structured output safely
        answer_text = ""
        claims: List[GroundedClaim] = []

        try:
            # Handle potential markdown fencing
            cleaned_json = raw_output.strip()
            if cleaned_json.startswith("```"):
                cleaned_json = cleaned_json.split("\n", 1)[1]
                cleaned_json = cleaned_json.rsplit("```", 1)[0]
            parsed = json.loads(cleaned_json)

            answer_text = parsed.get("answer", "").strip()
            raw_claims = parsed.get("claims", [])

            for idx, c in enumerate(raw_claims, start=1):
                if isinstance(c, dict):
                    text = c.get("text", "").strip()
                    eids = c.get("evidence_ids", [])
                elif isinstance(c, str):
                    text = c.strip()
                    eids = re.findall(r"\[(E\d+)\]", text)
                else:
                    continue

                if text:
                    # Clean brackets if user passed raw E1 or [E1]
                    clean_eids = [e.replace("[", "").replace("]", "").upper() for e in eids]
                    claims.append(
                        GroundedClaim(
                            claim_id=f"claim_{idx}",
                            text=text,
                            evidence_ids=clean_eids,
                        )
                    )

            # If LLM generated answer citing [E...] inline but returned empty or sparse claims array,
            # automatically derive claims from sentences containing evidence tags
            if not claims and answer_text:
                sentences = re.split(r"(?<=[.!?])\s+", answer_text)
                for s_idx, sent in enumerate(sentences, start=1):
                    inline_eids = re.findall(r"\[(E\d+)\]", sent)
                    if inline_eids:
                        claims.append(
                            GroundedClaim(
                                claim_id=f"claim_{s_idx}",
                                text=sent.strip(),
                                evidence_ids=[e.upper() for e in set(inline_eids)],
                            )
                        )
        except Exception as e:
            # Fallback if model output is malformed or unclosed JSON
            raw = raw_output.strip()
            ans_match = re.search(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)', raw)
            if ans_match:
                try:
                    answer_text = json.loads(f'"{ans_match.group(1)}"')
                except Exception:
                    answer_text = ans_match.group(1).replace('\\"', '"').replace('\\n', '\n')
            else:
                answer_text = raw

            # Derive claims from sentences containing evidence tags
            if answer_text:
                sentences = re.split(r"(?<=[.!?])\s+", answer_text)
                for s_idx, sent in enumerate(sentences, start=1):
                    inline_eids = re.findall(r"\[(E\d+)\]", sent)
                    if inline_eids:
                        claims.append(
                            GroundedClaim(
                                claim_id=f"claim_{s_idx}",
                                text=sent.strip(),
                                evidence_ids=[e.upper() for e in set(inline_eids)],
                            )
                        )

        # Clean dangling prompt tags like [E1] or [E12] from the final answer text so it reads naturally
        # The frontend renders exact interactive verified citation pills (§ Clause · p.X) directly beneath the message
        if answer_text:
            answer_text = re.sub(r"\s*\[E\d+\]", "", answer_text).strip()

        return answer_text, claims, evidence_map, latency_ms
