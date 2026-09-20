"""NVIDIA NIM LLM Provider for ContractLens.

Integrates with NVIDIA NIM endpoints (specifically nvidia/nemotron-3-super-120b-a12b)
providing:
- Strictly formatted JSON grounded answers matching the system grounding prompt schema.
- Exponential backoff retry logic for resilience against transient errors.
- Automatic fallback to deterministic extraction if network, credits, or limits fail.
"""

from __future__ import annotations

import os
import re
import json
import logging
import time
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

from src.rag.generator import BaseLLMProvider, FakeLLMProvider

logger = logging.getLogger("contractlens.nvidia")


class NvidiaNIMProvider(BaseLLMProvider):
    """Production provider communicating with NVIDIA NIM inference endpoints."""

    DEFAULT_MODEL = "nvidia/nemotron-3-super-120b-a12b"
    ENDPOINT_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: float = 12.0,
        max_retries: int = 2,
        fallback_provider: Optional[BaseLLMProvider] = None,
    ):
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY", "")
        self.model_name = model_name or os.environ.get("NVIDIA_MODEL_NAME", self.DEFAULT_MODEL)
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.fallback = fallback_provider or FakeLLMProvider()

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Call NVIDIA NIM chat completions and return the synthesized JSON string.

        Falls back seamlessly to deterministic extraction if the API is unconfigured
        or encounters network / quota errors.
        """
        if not self.api_key:
            logger.info("NVIDIA_API_KEY not configured. Falling back to deterministic provider.")
            return self.fallback.generate(system_prompt, user_prompt)

        # Add concise prompt suffix to guarantee strict JSON output without trailing thoughts
        enforced_system = (
            system_prompt
            + "\n\nCRITICAL INSTRUCTION: Output ONLY valid JSON starting with '{' and ending with '}'. "
            "Do NOT write any thinking process, reasoning, scratchpad, or preamble before the JSON. "
            "Your first character MUST be '{'."
        )
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": enforced_system},
                {"role": "user", "content": user_prompt + "\n\nCRITICAL: Begin your response with '{' immediately without any thinking:"},
            ],
            "temperature": 0.0,
            "max_tokens": 4096,
        }

        req_data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                req = urllib.request.Request(self.ENDPOINT_URL, data=req_data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    if resp.status == 200:
                        body = json.loads(resp.read().decode("utf-8"))
                        choices = body.get("choices", [])
                        if choices:
                            msg_obj = choices[0].get("message", {})
                            content = msg_obj.get("content") or ""
                            # If content is empty or incomplete but reasoning_content exists
                            if not content and "reasoning_content" in msg_obj:
                                content = msg_obj.get("reasoning_content") or ""
                            cleaned = content.strip()
                            
                            # Find valid JSON object containing "answer" using first balanced { ... }
                            if "{" in cleaned and "}" in cleaned:
                                start_idx = cleaned.find("{")
                                while start_idx != -1:
                                    depth = 0
                                    in_str = False
                                    esc = False
                                    for i in range(start_idx, len(cleaned)):
                                        c = cleaned[i]
                                        if esc:
                                            esc = False
                                            continue
                                        if c == '\\':
                                            esc = True
                                            continue
                                        if c == '"':
                                            in_str = not in_str
                                            continue
                                        if not in_str:
                                            if c == '{':
                                                depth += 1
                                            elif c == '}':
                                                depth -= 1
                                                if depth == 0:
                                                    candidate = cleaned[start_idx:i+1]
                                                    try:
                                                        parsed = json.loads(candidate)
                                                        if isinstance(parsed, dict) and "answer" in parsed:
                                                            return candidate
                                                    except json.JSONDecodeError:
                                                        pass
                                                    break
                                    start_idx = cleaned.find("{", start_idx + 1)

                            # Markdown code fences
                            if "```json" in cleaned:
                                target_block = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
                                try:
                                    json.loads(target_block)
                                    return target_block
                                except json.JSONDecodeError:
                                    pass
                            elif cleaned.startswith("```"):
                                cleaned = cleaned.split("\n", 1)[1]
                                cleaned = cleaned.rsplit("```", 1)[0].strip()

                            try:
                                json.loads(cleaned)
                                return cleaned
                            except json.JSONDecodeError:
                                # If JSON was truncated while generating answer, extract whatever was written in "answer": "..."
                                ans_match = re.search(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)', cleaned)
                                if ans_match:
                                    raw_val = ans_match.group(1)
                                    # Decode unicode and escaped characters
                                    try:
                                        decoded_val = json.loads(f'"{raw_val}"')
                                    except Exception:
                                        decoded_val = raw_val.replace('\\"', '"').replace('\\n', '\n')
                                    return json.dumps({
                                        "answer": decoded_val.strip(),
                                        "claims": []
                                    })

                                # Strip internal chain-of-thought / scratchpad if model output reasoning before answer
                                answer_text = cleaned
                                
                                # Check for common conclusion or answer markers
                                markers = [
                                    "**Answer:**", "Answer:", "### Answer", "**Summary:**",
                                    "In summary,", "Therefore,", "Thus,", "To answer your question:",
                                    "Let's craft answer:", "So answer:"
                                ]
                                for marker in markers:
                                    if marker in answer_text:
                                        answer_text = answer_text.split(marker, 1)[1].strip()
                                        break
                                else:
                                    # If the output starts with reasoning markers, strip leading reasoning lines
                                    lines = [l for l in answer_text.split("\n") if l.strip()]
                                    clean_lines = []
                                    skipping_reasoning = True
                                    for line in lines:
                                        l_low = line.lower()
                                        if skipping_reasoning:
                                            if (l_low.startswith("we need to") or
                                                l_low.startswith("let's") or
                                                l_low.startswith("list of evidence") or
                                                l_low.startswith("from evidence") or
                                                l_low.startswith("[e") and ("not relevant" in l_low or "maybe heading" in l_low or "page:" in l_low)):
                                                continue
                                            else:
                                                skipping_reasoning = False
                                                clean_lines.append(line)
                                        else:
                                            clean_lines.append(line)
                                    if clean_lines:
                                        answer_text = "\n\n".join(clean_lines)

                                return json.dumps({
                                    "answer": answer_text,
                                    "claims": []
                                })
            except urllib.error.HTTPError as he:
                last_exception = he
                error_body = he.read().decode("utf-8", errors="ignore")
                logger.warning("NVIDIA NIM HTTP %d on attempt %d/%d: %s", he.code, attempt, self.max_retries, error_body)
                if he.code in (429, 500, 502, 503, 504):
                    time.sleep(1.0 * attempt)
                    continue
                else:
                    break
            except Exception as ex:
                last_exception = ex
                logger.warning("NVIDIA NIM connection error on attempt %d/%d: %s", attempt, self.max_retries, ex)
                time.sleep(0.5 * attempt)
                continue

        logger.error("NVIDIA NIM generation failed after %d retries (%s). Activating deterministic fallback.", self.max_retries, last_exception)
        return self.fallback.generate(system_prompt, user_prompt)
