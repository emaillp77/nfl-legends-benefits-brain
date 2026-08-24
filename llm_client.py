#!/usr/bin/env python3
"""
Optional LLM client for natural-language explanations.

Supports:
  - Mock mode (always available, deterministic templates)
  - xAI Grok (via XAI_API_KEY or GROK_API_KEY)
  - OpenAI-compatible endpoints (OPENAI_API_KEY + optional OPENAI_BASE_URL)

Usage:
    from llm_client import get_llm_client
    client = get_llm_client()          # auto-detects
    text = client.complete(system=..., user=...)
"""

from __future__ import annotations
import os
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod


class LLMClient(ABC):
    @abstractmethod
    def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.3,
        max_tokens: int = 800,
    ) -> str:
        ...

    @property
    def name(self) -> str:
        return self.__class__.__name__


class MockLLMClient(LLMClient):
    """Deterministic, no-network explanations for demos and offline use."""

    def complete(self, system: str, user: str, temperature: float = 0.3, max_tokens: int = 800) -> str:
        # Extract JSON payload even if wrapped in markdown / prose
        payload = {}
        try:
            if "```json" in user:
                start = user.index("```json") + 7
                end = user.index("```", start)
                payload = json.loads(user[start:end].strip())
            elif user.strip().startswith("{"):
                payload = json.loads(user)
            else:
                # last-ditch: find first { ... }
                start = user.find("{")
                end = user.rfind("}") + 1
                if start >= 0 and end > start:
                    payload = json.loads(user[start:end])
        except Exception:
            payload = {}

        player = payload.get("player", {})
        name = player.get("name", "the Legend")
        cs = player.get("credited_seasons", "?")
        age = player.get("age", "?")
        eligible = payload.get("eligible_count")
        if eligible is None:
            eligible = len(payload.get("eligible_benefits", [])) or "?"
        actions = payload.get("priority_actions", [])
        cautions = payload.get("cautions", [])
        benefits = payload.get("eligible_benefits", [])

        lines = [
            f"Here's a clear summary for {name} "
            f"(Credited Seasons: {cs}, age {age}):",
            "",
            f"Based on the current profile, approximately {eligible} benefits appear eligible.",
        ]

        if benefits:
            lines.append("")
            lines.append("Eligible benefits include:")
            for b in benefits[:6]:
                val = f" — {b['value']}" if b.get("value") else ""
                lines.append(f"  • {b.get('name', 'Benefit')}{val}")

        if actions:
            lines.append("")
            lines.append("Recommended next steps (in priority order):")
            for a in actions[:5]:
                step = a.get("step", "")
                benefit = a.get("benefit", "Benefit")
                action = a.get("action", "")
                lines.append(f"  {step}. {benefit} — {action}")

        if cautions:
            lines.append("")
            lines.append("Important cautions to review carefully:")
            for c in cautions[:5]:
                sev = c.get("severity", "info").upper()
                msg = c.get("message", "")
                lines.append(f"  [{sev}] {msg}")

        lines.extend([
            "",
            "This is an automated plain-language summary generated in Mock mode "
            "(no live LLM API key detected).",
            "Always confirm eligibility, amounts, and deadlines with official NFL Player Benefits "
            "resources (NFLPlayerBenefits.com) and the current plan documents before taking action.",
        ])
        return "\n".join(lines)


class OpenAICompatibleClient(LLMClient):
    """
    Works with OpenAI, xAI Grok, or any OpenAI-compatible chat completions endpoint.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        provider_name: str = "OpenAI-Compatible",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._provider_name = provider_name

    @property
    def name(self) -> str:
        return f"{self._provider_name}({self.model})"

    def complete(
        self,
        system: str,
        user: str,
        temperature: float = 0.3,
        max_tokens: int = 800,
    ) -> str:
        url = f"{self.base_url}/chat/completions"
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM API error {e.code}: {err_body}") from e
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {e}") from e


def get_llm_client(prefer: Optional[str] = None) -> LLMClient:
    """
    Auto-select a client.

    Priority:
      1. Explicit prefer="mock" | "xai" | "openai"
      2. XAI_API_KEY / GROK_API_KEY → xAI Grok
      3. OPENAI_API_KEY → OpenAI (or OPENAI_BASE_URL)
      4. Fallback to Mock
    """
    prefer = (prefer or os.getenv("LLM_PROVIDER", "")).lower().strip()

    xai_key = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    openai_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    xai_model = os.getenv("XAI_MODEL", "grok-2-latest")

    if prefer == "mock":
        return MockLLMClient()

    if prefer in ("xai", "grok") or (not prefer and xai_key):
        if not xai_key:
            print("[llm_client] XAI/GROK key requested but not found → Mock")
            return MockLLMClient()
        return OpenAICompatibleClient(
            api_key=xai_key,
            base_url="https://api.x.ai/v1",
            model=xai_model,
            provider_name="xAI-Grok",
        )

    if prefer == "openai" or (not prefer and openai_key):
        if not openai_key:
            print("[llm_client] OPENAI_API_KEY requested but not found → Mock")
            return MockLLMClient()
        return OpenAICompatibleClient(
            api_key=openai_key,
            base_url=openai_base,
            model=openai_model,
            provider_name="OpenAI",
        )

    # Default: try xAI then OpenAI then Mock
    if xai_key:
        return OpenAICompatibleClient(
            api_key=xai_key,
            base_url="https://api.x.ai/v1",
            model=xai_model,
            provider_name="xAI-Grok",
        )
    if openai_key:
        return OpenAICompatibleClient(
            api_key=openai_key,
            base_url=openai_base,
            model=openai_model,
            provider_name="OpenAI",
        )

    return MockLLMClient()


# Convenience system prompt for benefits explanations
BENEFITS_EXPLANATION_SYSTEM = """You are a clear, empathetic benefits counselor for NFL Legends (former NFL players).
Your job is to turn structured eligibility and coordination data into plain-language explanations.

Rules:
- Be accurate. Never invent eligibility, dollar amounts, or deadlines that are not in the provided data.
- Use warm but professional tone. Avoid jargon where possible; when you must use a term (e.g. "Credited Seasons", "Vested"), briefly explain it.
- Highlight the highest-priority next actions first.
- Call out any HIGH or MEDIUM cautions prominently.
- Always end with a short reminder that the player should verify details on NFLPlayerBenefits.com or with the plan administrator before acting.
- Keep the response concise (roughly 250-450 words) unless the user asks for more detail.
- Do not mention that you are an AI unless asked.
"""
