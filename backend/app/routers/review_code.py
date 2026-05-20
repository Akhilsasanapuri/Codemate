from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ..db import get_session
from ..prompts import review_code_prompt
from ..schemas import ReviewCodeRequest, ReviewCodeResponse
from ..services.agent import run_agent

router = APIRouter()


@router.post("/review-code", response_model=ReviewCodeResponse)
def review_code(req: ReviewCodeRequest, session: Session = Depends(get_session)) -> ReviewCodeResponse:
    system, user = review_code_prompt(req)
    try:
        return run_agent(
            session=session,
            interaction_type="review_code",
            request_model=req,
            system_prompt=system,
            user_prompt=user,
            response_model=ReviewCodeResponse,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
