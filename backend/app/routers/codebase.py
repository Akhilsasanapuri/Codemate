"""Codebase (RAG) endpoints: upload a zip, ask questions, list/delete projects."""
import json
import time
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form
from sqlmodel import Session

from .. import llm
from ..config import get_settings
from ..db import get_session
from ..models import Interaction
from ..prompts import ask_codebase_prompt
from ..schemas import (
    AskCodebaseRequest,
    AskCodebaseResponse,
    CodebaseSource,
    ProjectOut,
)
from ..services import rag

router = APIRouter()


@router.post("/codebase/upload", response_model=ProjectOut, tags=["codebase"])
async def upload_codebase(
    file: UploadFile = File(...),
    name: str = Form(...),
    session: Session = Depends(get_session),
) -> ProjectOut:
    if not name.strip():
        raise HTTPException(status_code=400, detail="name is required")
    if not (file.filename or "").lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip uploads are supported")

    data = await file.read()
    try:
        project = rag.ingest_zip(session=session, name=name.strip(), zip_bytes=data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"ingest_failed: {exc}") from exc

    return ProjectOut.model_validate(project, from_attributes=True)


@router.post("/codebase/ask", response_model=AskCodebaseResponse, tags=["codebase"])
def ask_codebase(req: AskCodebaseRequest, session: Session = Depends(get_session)) -> AskCodebaseResponse:
    settings = get_settings()

    started = time.perf_counter()
    request_json = req.model_dump_json()
    response_obj: AskCodebaseResponse | None = None
    error_str: str | None = None
    raw: dict | None = None

    try:
        retrieved = rag.query(project_id=req.project_id, question=req.question, top_k=req.top_k)
        if not retrieved:
            raise HTTPException(
                status_code=404,
                detail=f"No indexed chunks found for project_id={req.project_id}",
            )

        system, user = ask_codebase_prompt(req.question, retrieved)
        raw = llm.chat_json(system, user, model=settings.llm_model)
        answer = str(raw.get("answer", "")).strip()
        used_sources = [str(s) for s in raw.get("used_sources", []) if isinstance(s, str)]

        sources = [
            CodebaseSource(
                file_path=r["file_path"],
                line_start=r["line_start"],
                line_end=r["line_end"],
                score=r["score"],
                snippet=r["text"][:600],
            )
            for r in retrieved
        ]
        response_obj = AskCodebaseResponse(answer=answer, used_sources=used_sources, sources=sources)
        return response_obj
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        error_str = f"{type(exc).__name__}: {exc}"
        raise HTTPException(status_code=500, detail=error_str) from exc
    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        row = Interaction(
            type="ask_codebase",
            request_json=request_json,
            response_json=response_obj.model_dump_json() if response_obj else (json.dumps(raw) if raw else None),
            model=settings.llm_model,
            latency_ms=latency_ms,
            error=error_str,
        )
        session.add(row)
        session.commit()


@router.get("/codebase/projects", response_model=List[ProjectOut], tags=["codebase"])
def list_projects(session: Session = Depends(get_session)) -> List[ProjectOut]:
    rows = rag.list_projects(session)
    return [ProjectOut.model_validate(p, from_attributes=True) for p in rows]


@router.delete("/codebase/projects/{project_id}", tags=["codebase"])
def delete_project(project_id: int, session: Session = Depends(get_session)) -> dict:
    ok = rag.delete_project(session=session, project_id=project_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"project {project_id} not found")
    return {"deleted": project_id}
