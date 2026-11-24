from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ai_services.ml.predictor import NHANESPredictor
from ai_services.orchestration.graph import MultiAgentOrchestrator
from backend.app.core.logging_utils import get_logger, sanitize_log_context
from backend.app.db.models import AgentRun, HealthAssessment, PredictionResult, User
from backend.app.schemas.assessment import AssessmentOut
from backend.app.services import (
    get_active_source_ids,
    get_owned_assessment,
    infer_run_flags_from_steps,
    persist_agent_run,
    serialize_agent_steps,
    serialize_prediction_row,
)

logger = get_logger(__name__)


def _to_assessment_out(
    assessment: HealthAssessment,
    *,
    agent_run: AgentRun | None = None,
    predictor: NHANESPredictor | None = None,
    prediction_override: dict[str, Any] | None = None,
    kg_relations: list[dict[str, Any]] | None = None,
    llm_used: bool | None = None,
    llm_fallback: bool | None = None,
) -> AssessmentOut:
    prediction_payload = (
        prediction_override
        if prediction_override is not None
        else serialize_prediction_row(assessment.prediction_result, predictor=predictor)
    )
    steps = serialize_agent_steps(list(agent_run.steps)) if agent_run is not None else []
    _inferred_kg, inferred_llm_used, inferred_llm_fallback = infer_run_flags_from_steps(steps)
    return AssessmentOut(
        id=assessment.id,
        request_id=assessment.request_id,
        status=assessment.status,
        raw_inputs=dict(assessment.raw_inputs_json or {}),
        derived_features=assessment.derived_features_json,
        prediction=prediction_payload,
        summary_text=assessment.summary_text,
        recommendations=list(assessment.recommendations_json or []),
        citations=list(assessment.citations_json or []),
        kg_relations=list(kg_relations or []),
        limitations=list(assessment.limitations_json or []),
        llm_used=llm_used if llm_used is not None else inferred_llm_used,
        llm_fallback=llm_fallback if llm_fallback is not None else inferred_llm_fallback,
        agent_steps=steps,
        total_latency_ms=agent_run.total_latency_ms if agent_run is not None else 0,
        error_code=agent_run.error_code if agent_run is not None else None,
        created_at=assessment.created_at,
    )


def run_and_persist_assessment(
    db: Session,
    *,
    current_user: User,
    payload: dict[str, Any],
    orchestrator: MultiAgentOrchestrator,
) -> AssessmentOut:
    """Execute the 5-agent assessment graph, persist results & trace, and return AssessmentOut."""
    request_id = f"assess_{uuid4().hex[:16]}"
    active_source_ids = get_active_source_ids(db)

    result = orchestrator.run_assessment(
        request_id=request_id,
        payload=payload,
        active_source_ids=active_source_ids,
    )

    assessment = HealthAssessment(
        user_id=current_user.id,
        request_id=request_id,
        status=str(result.get("status") or "failed"),
        raw_inputs_json=dict(payload),
        derived_features_json=result.get("derived_features"),
        summary_text=str(result.get("summary_text") or ""),
        recommendations_json=list(result.get("recommendations") or []),
        citations_json=list(result.get("citations") or []),
        limitations_json=list(result.get("limitations") or []),
    )

    prediction = result.get("prediction")
    if assessment.status == "completed" and prediction is not None:
        assessment.prediction_result = PredictionResult(
            model_version=str(prediction["model_version"]),
            model_name=str(prediction["model_name"]),
            model_sha256=str(prediction["model_sha256"]),
            threshold=float(prediction["threshold_low"]),
            model_score=float(prediction["model_score"]),
            predicted_label=int(prediction["predicted_label"]),
            risk_band=str(prediction["risk_band"]),
            factors_json=list(prediction.get("feature_contributions") or []),
        )

    db.add(assessment)
    agent_run = persist_agent_run(
        db,
        request_id=request_id,
        user_id=current_user.id,
        task_type="assessment",
        result=result,
    )
    db.commit()
    db.refresh(assessment)
    db.refresh(agent_run)

    logger.info(
        "Assessment processed: %s",
        sanitize_log_context(
            {
                "request_id": request_id,
                "user_id": current_user.id,
                "status": assessment.status,
                "total_latency_ms": agent_run.total_latency_ms,
                "error_code": agent_run.error_code,
            }
        ),
    )

    return _to_assessment_out(
        assessment,
        agent_run=agent_run,
        prediction_override=prediction if assessment.status == "completed" else None,
        kg_relations=list(result.get("kg_relations") or []),
        llm_used=bool(result.get("llm_used", False)),
        llm_fallback=bool(result.get("llm_fallback", False)),
    )


def list_user_assessments(
    db: Session,
    *,
    user_id: str,
    predictor: NHANESPredictor | None = None,
) -> list[AssessmentOut]:
    """List all health assessments owned by `user_id` ordered newest-first."""
    assessments = list(
        db.scalars(
            select(HealthAssessment)
            .options(joinedload(HealthAssessment.prediction_result))
            .where(HealthAssessment.user_id == user_id)
            .order_by(HealthAssessment.created_at.desc())
        ).all()
    )
    if not assessments:
        return []

    req_ids = [item.request_id for item in assessments]
    runs = list(
        db.scalars(
            select(AgentRun)
            .options(joinedload(AgentRun.steps))
            .where(AgentRun.request_id.in_(req_ids))
        )
        .unique()
        .all()
    )
    runs_by_req = {run.request_id: run for run in runs}

    return [
        _to_assessment_out(
            item,
            agent_run=runs_by_req.get(item.request_id),
            predictor=predictor,
        )
        for item in assessments
    ]


def get_user_assessment_detail(
    db: Session,
    *,
    assessment_id: str,
    user_id: str,
    predictor: NHANESPredictor | None = None,
) -> AssessmentOut:
    """Return full details for one assessment after verifying ownership."""
    assessment = get_owned_assessment(db, assessment_id, user_id)
    agent_run = db.scalar(
        select(AgentRun)
        .options(joinedload(AgentRun.steps))
        .where(AgentRun.request_id == assessment.request_id)
    )
    return _to_assessment_out(
        assessment,
        agent_run=agent_run,
        predictor=predictor,
    )
