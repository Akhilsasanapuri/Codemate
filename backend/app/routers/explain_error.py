from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ..db import get_session
from ..prompts import explain_error_prompt
from ..schemas import ExplainErrorRequest, ExplainErrorResponse
from ..services.agent import run_agent

router = APIRouter()


@router.post("/explain-error", response_model=ExplainErrorResponse)
def explain_error(req: ExplainErrorRequest, session: Session = Depends(get_session)) -> ExplainErrorResponse:
    system, user = explain_error_prompt(req)
    try:
        return run_agent(
            session=session,
            interaction_type="explain_error",
            request_model=req,
            system_prompt=system,
            user_prompt=user,
            response_model=ExplainErrorResponse,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
