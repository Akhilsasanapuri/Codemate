from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ---------- Explain Error ----------
class ExplainErrorRequest(BaseModel):
    error_message: str = Field(..., min_length=1, description="The error/stack trace to explain")
    code: Optional[str] = Field(default=None, description="Optional related code snippet")
    language: Optional[str] = Field(default=None, description="Programming language hint, e.g. 'python'")


class ExplainErrorResponse(BaseModel):
    explanation: str
    root_cause: str
    suggested_fix: str
    corrected_code: Optional[str] = None
    language: Optional[str] = None


# ---------- Generate Code ----------
class GenerateCodeRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Natural language description of the task")
    language: Optional[str] = Field(default=None, description="Target language, e.g. 'python'")
    framework: Optional[str] = Field(default=None, description="Optional framework, e.g. 'fastapi'")


class GenerateCodeResponse(BaseModel):
    code: str
    language: str
    explanation: str
    assumptions: List[str] = Field(default_factory=list)


# ---------- Review Code ----------
Severity = Literal["info", "warning", "error"]
IssueType = Literal["bug", "inefficiency", "style", "security", "other"]


class ReviewIssue(BaseModel):
    type: IssueType
    severity: Severity
    description: str
    line: Optional[int] = None


class ReviewCodeRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: Optional[str] = None


class ReviewCodeResponse(BaseModel):
    summary: str
    issues: List[ReviewIssue] = Field(default_factory=list)
    improved_code: Optional[str] = None
    language: Optional[str] = None


# ---------- History ----------
class InteractionOut(BaseModel):
    id: int
    type: str
    model: str
    created_at: datetime
    latency_ms: Optional[int]
    error: Optional[str]


class InteractionDetail(InteractionOut):
    request_json: str
    response_json: Optional[str]


# ---------- Codebase / RAG ----------
class ProjectOut(BaseModel):
    id: int
    name: str
    file_count: int
    chunk_count: int
    total_bytes: int
    embedding_model: str
    created_at: datetime


class CodebaseSource(BaseModel):
    file_path: str
    line_start: int
    line_end: int
    score: float = 0.0  # similarity score (lower = closer for L2/cosine distance)
    snippet: str


class AskCodebaseRequest(BaseModel):
    project_id: int
    question: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(default=None, ge=1, le=20)


class AskCodebaseResponse(BaseModel):
    answer: str
    used_sources: List[str] = Field(default_factory=list)
    sources: List[CodebaseSource] = Field(default_factory=list)


# ---------- Intent Router (Phase 4) ----------
RoutedTool = Literal["explain_error", "generate_code", "review_code", "ask_codebase"]


class RouteRequest(BaseModel):
    text: str = Field(..., min_length=1, description="What the user typed")
    project_id: Optional[int] = Field(
        default=None, description="If set, ask_codebase is available as a routing target"
    )


class RouteResponse(BaseModel):
    routed_to: RoutedTool
    reason: str
    # exactly one of these will be populated based on routed_to
    explain_error: Optional[ExplainErrorResponse] = None
    generate_code: Optional[GenerateCodeResponse] = None
    review_code: Optional[ReviewCodeResponse] = None
    ask_codebase: Optional[AskCodebaseResponse] = None
