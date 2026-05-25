"""Gemini embeddings via native REST.

The OpenAI-compat endpoint does NOT expose /embeddings for Gemini, so we call
the native v1beta `batchEmbedContents` endpoint directly. Returns 768-dim
vectors (configurable via EMBEDDING_DIM) using gemini-embedding-001 by default.
"""
import logging
import time
from typing import List, Literal

import httpx

from ..config import get_settings

logger = logging.getLogger(__name__)

TaskType = Literal["RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY", "SEMANTIC_SIMILARITY"]

# Gemini's batch endpoint accepts up to 100 requests per call.
_BATCH_SIZE = 100
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 2.0  # seconds


def embed_texts(texts: List[str], *, task_type: TaskType = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
    """Embed a list of strings, returning one vector per input (in order).

    Batches into groups of 100 and retries on 429 with exponential backoff.
    """
    if not texts:
        return []

    settings = get_settings()
    if not settings.llm_api_key:
        raise RuntimeError("LLM_API_KEY is not configured.")

    model_name = settings.embedding_model
    url = (
        f"{settings.embedding_base_url.rstrip('/')}"
        f"/models/{model_name}:batchEmbedContents"
        f"?key={settings.llm_api_key}"
    )

    all_vectors: List[List[float]] = []
    with httpx.Client(timeout=settings.llm_timeout_seconds) as client:
        for start in range(0, len(texts), _BATCH_SIZE):
            batch = texts[start : start + _BATCH_SIZE]
            payload = {
                "requests": [
                    {
                        "model": f"models/{model_name}",
                        "content": {"parts": [{"text": t}]},
                        "taskType": task_type,
                        "outputDimensionality": settings.embedding_dim,
                    }
                    for t in batch
                ]
            }
            vectors = _post_with_retries(client, url, payload)
            if len(vectors) != len(batch):
                raise RuntimeError(
                    f"Embedding count mismatch: expected {len(batch)}, got {len(vectors)}"
                )
            all_vectors.extend(vectors)

    return all_vectors


def embed_query(text: str) -> List[float]:
    """Convenience: embed a single search query."""
    vectors = embed_texts([text], task_type="RETRIEVAL_QUERY")
    return vectors[0]


def _post_with_retries(client: httpx.Client, url: str, payload: dict) -> List[List[float]]:
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            resp = client.post(url, json=payload)
            if resp.status_code == 429:
                delay = _RETRY_BASE_DELAY * (2**attempt)
                logger.warning("Embedding 429; sleeping %.1fs before retry", delay)
                time.sleep(delay)
                continue
            resp.raise_for_status()
            data = resp.json()
            return [e["values"] for e in data.get("embeddings", [])]
        except httpx.HTTPError as exc:
            last_exc = exc
            if attempt + 1 < _MAX_RETRIES:
                time.sleep(_RETRY_BASE_DELAY * (2**attempt))
                continue
            raise

    raise RuntimeError(f"Embedding failed after {_MAX_RETRIES} retries: {last_exc}")
