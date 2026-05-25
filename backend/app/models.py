from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Interaction(SQLModel, table=True):
    """One row per agent invocation (success or failure)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    type: str = Field(index=True)  # explain_error | generate_code | review_code | ask_codebase
    request_json: str  # serialized request payload
    response_json: Optional[str] = None  # serialized response payload
    model: str
    created_at: datetime = Field(default_factory=_utcnow, index=True)
    latency_ms: Optional[int] = None
    error: Optional[str] = None


class Project(SQLModel, table=True):
    """One row per uploaded codebase (RAG)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    file_count: int = 0
    chunk_count: int = 0
    total_bytes: int = 0
    embedding_model: str = ""
    created_at: datetime = Field(default_factory=_utcnow, index=True)
