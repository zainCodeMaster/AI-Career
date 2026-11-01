"""Gemini LLM provider for CareerOS.

Provides text generation capabilities using Google's Gemini API.
Uses the maintained `google-genai` SDK (not the deprecated `google-generativeai`).

Used for:
- Career Brain RAG answer generation
- Resume analysis and ATS recommendations
- Job analysis and matching explanations
- Cover letter generation
- Skill gap analysis
"""
from __future__ import annotations

import logging
import os
import re
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Sequence

from pydantic import BaseModel

logger = logging.getLogger("app.llm")


@dataclass(frozen=True)
class LLMResponse:
    """Response from an LLM provider."""

    text: str
    model: str
    usage: Optional[dict] = None
    metadata: Optional[dict] = None


class LLMProvider(ABC):
    """Abstract LLM provider for text generation."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text from a prompt."""

    @abstractmethod
    def generate_structured(self, prompt: str, schema: type[BaseModel], **kwargs) -> BaseModel:
        """Generate structured output matching a Pydantic schema."""


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider using the maintained `google-genai` SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-flash",
        temperature: float = 0.3,
        max_output_tokens: int = 4096,
    ) -> None:
        self._model = model
        self._temperature = temperature
        self._max_output_tokens = max_output_tokens
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self._client = None

        if not self._api_key:
            logger.warning("Gemini API key not configured. LLM features will be unavailable.")
            return

        try:
            from google import genai

            self._client = genai.Client(api_key=self._api_key)
            logger.info("Gemini provider initialized with model: %s", model)
        except ImportError:
            logger.error("google-genai package not installed. Run: pip install google-genai")
        except Exception as exc:
            logger.error("Failed to initialize Gemini provider: %s", exc)

    @property
    def model_name(self) -> str:
        return self._model

    def _is_available(self) -> bool:
        return self._client is not None

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text from a prompt."""
        if not self._is_available():
            return LLMResponse(
                text="LLM not configured. Please set GEMINI_API_KEY environment variable.",
                model=self._model,
                metadata={"error": "not_configured"},
            )

        try:
            from google.genai import types

            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=self._temperature,
                    max_output_tokens=self._max_output_tokens,
                ),
            )
            text = response.text if response.text else ""

            usage = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = {
                    "prompt_tokens": getattr(response.usage_metadata, "prompt_token_count", 0),
                    "completion_tokens": getattr(response.usage_metadata, "candidates_token_count", 0),
                    "total_tokens": getattr(response.usage_metadata, "total_token_count", 0),
                }

            finish_reason = None
            if response.candidates:
                finish_reason = getattr(response.candidates[0], "finish_reason", None)

            return LLMResponse(
                text=text,
                model=self._model,
                usage=usage,
                metadata={"finish_reason": finish_reason},
            )
        except Exception as exc:
            logger.error("Gemini generation failed: %s", exc)
            return LLMResponse(
                text=f"Generation failed: {exc}",
                model=self._model,
                metadata={"error": str(exc)},
            )

    def generate_structured(self, prompt: str, schema: type[BaseModel], **kwargs) -> BaseModel:
        """Generate structured output matching a Pydantic schema."""
        if not self._is_available():
            logger.warning("Gemini not configured, returning default schema instance")
            return schema()

        # Add JSON schema instruction to prompt
        schema_json = schema.model_json_schema()
        structured_prompt = (
            f"{prompt}\n\n"
            f"Return a valid JSON object matching this schema:\n"
            f"{schema_json}\n\n"
            f"Return ONLY the JSON object, no additional text."
        )

        try:
            from google.genai import types

            response = self._client.models.generate_content(
                model=self._model,
                contents=structured_prompt,
                config=types.GenerateContentConfig(
                    temperature=self._temperature,
                    max_output_tokens=self._max_output_tokens,
                    response_mime_type="application/json",
                ),
            )
            text = response.text if response.text else "{}"

            # Parse JSON from response
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
                if match:
                    data = json.loads(match.group(1))
                else:
                    raise

            return schema.model_validate(data)
        except Exception as exc:
            logger.error("Gemini structured generation failed: %s", exc)
            # Return default instance on failure
            return schema()


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing and when no API key is configured."""

    def __init__(self, model: str = "mock") -> None:
        self._model = model

    @property
    def model_name(self) -> str:
        return self._model

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        return LLMResponse(
            text=f"[Mock LLM] This is a mock response. Configure GEMINI_API_KEY for real AI responses.",
            model=self._model,
            metadata={"mock": True},
        )

    def generate_structured(self, prompt: str, schema: type[BaseModel], **kwargs) -> BaseModel:
        return schema()


# Provider factory
_provider_instance: Optional[LLMProvider] = None


def get_llm_provider() -> LLMProvider:
    """Get or create the configured LLM provider (singleton)."""
    global _provider_instance

    if _provider_instance is not None:
        return _provider_instance

    from app.core.config import get_settings

    settings = get_settings()
    llm_provider = getattr(settings, "llm_provider", "auto")

    if llm_provider == "mock":
        _provider_instance = MockLLMProvider()
    elif llm_provider == "gemini":
        _provider_instance = GeminiProvider()
    elif llm_provider == "auto":
        # Auto-detect: use Gemini if API key is available, else mock
        api_key = os.environ.get("GEMINI_API_KEY") or getattr(settings, "gemini_api_key", None)
        if api_key:
            _provider_instance = GeminiProvider(api_key=api_key)
        else:
            _provider_instance = MockLLMProvider()
    else:
        _provider_instance = MockLLMProvider()

    return _provider_instance


def reset_llm_provider() -> None:
    """Reset the provider (useful for testing)."""
    global _provider_instance
    _provider_instance = None