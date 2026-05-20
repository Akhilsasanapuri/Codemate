"""Thin wrapper around any OpenAI-compatible chat completions API.

Default config targets Google Gemini's OpenAI-compatible endpoint, but the
same code works for OpenAI, Groq, OpenRouter, Ollama, etc. — just change
LLM_BASE_URL / LLM_MODEL / LLM_API_KEY.
"""
import json
import logging
from typing import Any

from openai import OpenAI

from .config import get_settings

logger = logging.getLogger(__name__)

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.llm_api_key:
            raise RuntimeError(
                "LLM_API_KEY is not configured. Set it in your .env file. "
                "For Gemini, create one at https://aistudio.google.com/apikey"
            )
        _client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=settings.llm_timeout_seconds,
        )
    return _client


def chat_json(system: str, user: str, *, model: str | None = None, temperature: float = 0.2) -> dict[str, Any]:
    """Call the LLM and parse a JSON object from the response.

    Raises ValueError if the model returns invalid JSON.
    """
    settings = get_settings()
    chosen_model = model or settings.llm_model
    client = _get_client()

    completion = client.chat.completions.create(
        model=chosen_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        temperature=temperature,
    )

    content = completion.choices[0].message.content or "{}"
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        logger.error("LLM returned invalid JSON: %s", content[:500])
        raise ValueError(f"LLM returned invalid JSON: {exc}") from exc
