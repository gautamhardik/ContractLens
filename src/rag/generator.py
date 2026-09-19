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

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        self.call_history.append({"system": system_prompt, "user": user_prompt})

        # Check canned responses
        for query_key, resp in self.canned_responses.items():
            if query_key in user_prompt.lower():
                return resp

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

            best_eid = "E1"
            best_line = ""
            best_score = -1

            for eid, ev_text in evidence_pattern:
                ev_lines = [l.strip() for l in ev_text.split("\n") if l.strip()]
                for line in ev_lines:
                    line_lower = line.lower()
                    score = sum(1 for kw in q_keywords if kw in line_lower)
                    if score > best_score:
                        best_score = score
                        best_eid = eid
                        best_line = line

            if best_score > 0 and best_line:
                # Truncate clean sentence
                answer_sent = best_line.split(". ")[0].strip()
                if not answer_sent.endswith("."):
                    answer_sent += "."
                return json.dumps({
                    "answer": f"{answer_sent} [{best_eid}].",
                    "claims": [
                        {
                            "text": answer_sent,
                            "evidence_ids": [best_eid]
                        }
                    ]
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

        formatted_evidence, evidence_map = format_evidence_for_prompt(bundle)
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
                text = c.get("text", "").strip()
                eids = c.get("evidence_ids", [])
                if text:
                    claims.append(
                        GroundedClaim(
                            claim_id=f"claim_{idx}",
                            text=text,
                            evidence_ids=[str(e).strip().upper() for e in eids],
                        )
                    )
        except Exception as e:
            # Fallback if model output is malformed
            answer_text = raw_output.strip()
            claims = []

        return answer_text, claims, evidence_map, latency_ms
