from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from ..db import get_session
from ..prompts import generate_code_prompt
from ..schemas import GenerateCodeRequest, GenerateCodeResponse
from ..services.agent import run_agent

router = APIRouter()


@router.post("/generate-code", response_model=GenerateCodeResponse)
def generate_code(req: GenerateCodeRequest, session: Session = Depends(get_session)) -> GenerateCodeResponse:
    system, user = generate_code_prompt(req)
    try:
        return run_agent(
            session=session,
            interaction_type="generate_code",
            request_model=req,
            system_prompt=system,
            user_prompt=user,
            response_model=GenerateCodeResponse,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
