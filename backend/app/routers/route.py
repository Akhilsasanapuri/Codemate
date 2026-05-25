"""Phase 4: Intent-routing agent.

One endpoint: `POST /api/route` takes free-form user text (plus an optional
project_id) and:
  1) Calls the LLM as a classifier to pick one of {explain_error,
     generate_code, review_code, ask_codebase} and extract the inputs.
  2) Dispatches to the matching agent/service.
  3) Returns a unified RouteResponse with `routed_to`, `reason`, and the
     populated result for the chosen tool.

Logs ONE Interaction row of type "route" wrapping the whole exchange.
"""
import json
import logging
import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlmodel import Session

from .. import llm
from ..config import get_settings
from ..db import get_session
from ..models import Interaction, Project
from ..prompts import (
    explain_error_prompt,
    generate_code_prompt,
    review_code_prompt,
    route_prompt,
)
from ..schemas import (
    ExplainErrorRequest,
    ExplainErrorResponse,
    GenerateCodeRequest,
    GenerateCodeResponse,
    ReviewCodeRequest,
    ReviewCodeResponse,
    RouteRequest,
    RouteResponse,
)
from ..services import rag
from ..services.agent import run_agent

logger = logging.getLogger(__name__)
router = APIRouter()

_ALLOWED_TOOLS = {"explain_error", "generate_code", "review_code", "ask_codebase"}


@router.post("/route", response_model=RouteResponse, tags=["router"])
def route(req: RouteRequest, session: Session = Depends(get_session)) -> RouteResponse:
    settings = get_settings()

    started = time.perf_counter()
    request_json = req.model_dump_json()
    response_obj: RouteResponse | None = None
    error_str: str | None = None
    classifier_raw: dict | None = None

    try:
        # Look up the project (if any) so the classifier knows about it.
        project: Project | None = None
        if req.project_id is not None:
            project = session.get(Project, req.project_id)
            if project is None:
                raise HTTPException(
                    status_code=404, detail=f"project_id {req.project_id} not found"
                )

        # --- Step 1: classify ----------------------------------------------
        sys_p, user_p = route_prompt(
            req.text,
            has_project=project is not None,
            project_name=project.name if project else None,
        )
        classifier_raw = llm.chat_json(sys_p, user_p, model=settings.llm_model, temperature=0.0)
        tool = str(classifier_raw.get("tool", "")).strip()
        reason = str(classifier_raw.get("reason", "")).strip() or "(no reason given)"
        extracted = classifier_raw.get("extracted") or {}
        if tool not in _ALLOWED_TOOLS:
            raise HTTPException(status_code=502, detail=f"router returned invalid tool: {tool!r}")
        if tool == "ask_codebase" and project is None:
            raise HTTPException(
                status_code=400,
                detail="router chose ask_codebase but no project_id was provided",
            )

        # --- Step 2: dispatch ----------------------------------------------
        response_obj = _dispatch(
            tool=tool,
            reason=reason,
            extracted=extracted,
            req=req,
            session=session,
        )
        return response_obj

    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        error_str = f"{type(exc).__name__}: {exc}"
        logger.exception("route failed")
        raise HTTPException(status_code=500, detail=error_str) from exc
    finally:
        latency_ms = int((time.perf_counter() - started) * 1000)
        row = Interaction(
            type="route",
            request_json=request_json,
            response_json=response_obj.model_dump_json() if response_obj else (json.dumps(classifier_raw) if classifier_raw else None),
            model=settings.llm_model,
            latency_ms=latency_ms,
            error=error_str,
        )
        session.add(row)
        session.commit()


def _dispatch(
    *,
    tool: str,
    reason: str,
    extracted: dict,
    req: RouteRequest,
    session: Session,
) -> RouteResponse:
    if tool == "explain_error":
        try:
            inner_req = ExplainErrorRequest(
                error_message=str(extracted.get("error_message") or req.text),
                code=extracted.get("code") or None,
                language=extracted.get("language") or None,
            )
        except ValidationError as exc:
            raise HTTPException(status_code=502, detail=f"router-extracted invalid: {exc}") from exc
        sys_p, user_p = explain_error_prompt(inner_req)
        result = run_agent(
            session=session,
            interaction_type="explain_error",
            request_model=inner_req,
            system_prompt=sys_p,
            user_prompt=user_p,
            response_model=ExplainErrorResponse,
        )
        return RouteResponse(routed_to="explain_error", reason=reason, explain_error=result)

    if tool == "generate_code":
        try:
            inner_req = GenerateCodeRequest(
                prompt=str(extracted.get("prompt") or req.text),
                language=extracted.get("language") or None,
            )
        except ValidationError as exc:
            raise HTTPException(status_code=502, detail=f"router-extracted invalid: {exc}") from exc
        sys_p, user_p = generate_code_prompt(inner_req)
        result = run_agent(
            session=session,
            interaction_type="generate_code",
            request_model=inner_req,
            system_prompt=sys_p,
            user_prompt=user_p,
            response_model=GenerateCodeResponse,
        )
        return RouteResponse(routed_to="generate_code", reason=reason, generate_code=result)

    if tool == "review_code":
        code = str(extracted.get("code") or req.text)
        try:
            inner_req = ReviewCodeRequest(code=code, language=extracted.get("language") or None)
        except ValidationError as exc:
            raise HTTPException(status_code=502, detail=f"router-extracted invalid: {exc}") from exc
        sys_p, user_p = review_code_prompt(inner_req)
        result = run_agent(
            session=session,
            interaction_type="review_code",
            request_model=inner_req,
            system_prompt=sys_p,
            user_prompt=user_p,
            response_model=ReviewCodeResponse,
        )
        return RouteResponse(routed_to="review_code", reason=reason, review_code=result)

    # ask_codebase (project_id checked already in caller)
    question = str(extracted.get("question") or req.text)
    try:
        ask_resp, _raw = rag.answer_question(project_id=req.project_id, question=question)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RouteResponse(routed_to="ask_codebase", reason=reason, ask_codebase=ask_resp)
