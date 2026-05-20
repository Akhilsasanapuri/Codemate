from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from ..db import get_session
from ..models import Interaction
from ..schemas import InteractionDetail, InteractionOut

router = APIRouter()


@router.get("/history", response_model=List[InteractionOut])
def list_history(
    session: Session = Depends(get_session),
    limit: int = Query(default=20, ge=1, le=100),
    type: Optional[str] = Query(default=None, description="Filter by interaction type"),
) -> List[InteractionOut]:
    stmt = select(Interaction).order_by(Interaction.created_at.desc()).limit(limit)
    if type:
        stmt = select(Interaction).where(Interaction.type == type).order_by(Interaction.created_at.desc()).limit(limit)
    rows = session.exec(stmt).all()
    return [InteractionOut.model_validate(r, from_attributes=True) for r in rows]


@router.get("/history/{interaction_id}", response_model=InteractionDetail)
def get_history_item(interaction_id: int, session: Session = Depends(get_session)) -> InteractionDetail:
    row = session.get(Interaction, interaction_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found")
    return InteractionDetail.model_validate(row, from_attributes=True)
