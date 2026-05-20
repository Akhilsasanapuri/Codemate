"""Shared agent runner: call the LLM, validate output, persist the interaction."""
import json
import time
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError
from sqlmodel import Session

from .. import llm
from ..config import get_settings
from ..models import Interaction

T = TypeVar("T", bound=BaseModel)


def run_agent(
    *,
    session: Session,
    interaction_type: str,
    request_model: BaseModel,
    system_prompt: str,
    user_prompt: str,
    response_model: Type[T],
) -> T:
    """Run one agent invocation end-to-end.

    Raises ValueError if the LLM returns malformed JSON or fails schema validation.
    Always writes an Interaction row (success or failure).
    """
    settings = get_settings()
    started = time.perf_counter()
    request_json = request_model.model_dump_json()

    response_obj: T | None = None
    error_str: str | None = None
    raw: dict | None = None

    try:
        raw = llm.chat_json(system_prompt, user_prompt, model=settings.llm_model)
        response_obj = response_model.model_validate(raw)
    except ValidationError as exc:
        error_str = f"schema_validation_error: {exc.errors()}"
        raise ValueError(error_str) from exc
    except Exception as exc:  # noqa: BLE001 - we want to log any LLM failure
        error_str = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        row = Interaction(
            type=interaction_type,
            request_json=request_json,
            response_json=response_obj.model_dump_json() if response_obj else (json.dumps(raw) if raw else None),
            model=settings.llm_model,
            latency_ms=latency_ms,
            error=error_str,
        )
        session.add(row)
        session.commit()

    assert response_obj is not None  # for type checker; unreachable if error
    return response_obj
