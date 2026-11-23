from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ai_services.orchestration.graph import MultiAgentOrchestrator
from backend.app.api.deps import get_current_user, get_db, get_orchestrator
from backend.app.db.models import User
from backend.app.schemas.assessment import AssessmentCreateRequest, AssessmentOut
from backend.app.services.assessment_service import (
    get_user_assessment_detail,
    list_user_assessments,
    run_and_persist_assessment,
)

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.post("", response_model=AssessmentOut)
def create_assessment(
    payload: AssessmentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    orchestrator: MultiAgentOrchestrator = Depends(get_orchestrator),
) -> AssessmentOut:
    """Run the 5-agent diabetes screening pipeline and persist the assessment."""
    return run_and_persist_assessment(
        db,
        current_user=current_user,
        payload=payload.model_dump(),
        orchestrator=orchestrator,
    )


@router.get("", response_model=list[AssessmentOut])
def list_assessments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    orchestrator: MultiAgentOrchestrator = Depends(get_orchestrator),
) -> list[AssessmentOut]:
    """List health assessments belonging to the authenticated user."""
    return list_user_assessments(
        db,
        user_id=current_user.id,
        predictor=orchestrator.predictor,
    )


@router.get("/{assessment_id}", response_model=AssessmentOut)
def get_assessment(
    assessment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    orchestrator: MultiAgentOrchestrator = Depends(get_orchestrator),
) -> AssessmentOut:
    """Return one assessment owned by the authenticated user."""
    return get_user_assessment_detail(
        db,
        assessment_id=assessment_id,
        user_id=current_user.id,
        predictor=orchestrator.predictor,
    )
