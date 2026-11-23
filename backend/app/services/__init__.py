from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ai_services.ml.predictor import NHANESPredictor, SCREENING_WARNING_VI
from backend.app.db.models import (
    AgentRun,
    AgentStep,
    HealthAssessment,
    KnowledgeDocument,
    PredictionResult,
)
from backend.app.schemas.assessment import AgentStepOut


def get_active_source_ids(db: Session) -> set[str]:
    """Return the set of `source_id` values whose status is currently `active`."""
    rows = db.scalars(
        select(KnowledgeDocument.source_id).where(KnowledgeDocument.status == "active")
    ).all()
    return set(rows)


def serialize_agent_steps(steps: list[AgentStep] | list[dict[str, Any]]) -> list[AgentStepOut]:
    """Convert ORM AgentStep rows or orchestrator step dicts into sorted AgentStepOut items."""
    out: list[AgentStepOut] = []
    for step in steps:
        if isinstance(step, dict):
            out.append(
                AgentStepOut(
                    step_order=int(step["step_order"]),
                    agent_name=str(step["agent_name"]),
                    status=str(step["status"]),
                    latency_ms=int(step.get("latency_ms", 0)),
                    summary=str(step.get("summary", "")),
                    error_code=step.get("error_code"),
                )
            )
        else:
            out.append(
                AgentStepOut(
                    step_order=step.step_order,
                    agent_name=step.agent_name,
                    status=step.status,
                    latency_ms=step.latency_ms,
                    summary=step.summary,
                    error_code=step.error_code,
                )
            )
    out.sort(key=lambda item: item.step_order)
    return out


def persist_agent_run(
    db: Session,
    *,
    request_id: str,
    user_id: str | None,
    task_type: str,
    result: dict[str, Any],
) -> AgentRun:
    """Persist sanitized AgentRun and AgentStep execution records and flush for ID."""
    run = AgentRun(
        request_id=request_id,
        user_id=user_id,
        task_type=task_type,
        status=str(result.get("status") or "completed"),
        total_latency_ms=int(result.get("total_latency_ms") or 0),
        llm_provider=str(result.get("llm_provider") or "ollama"),
        llm_model=str(result.get("llm_model") or ""),
        error_code=result.get("error_code"),
    )
    for raw_step in result.get("agent_steps") or []:
        run.steps.append(
            AgentStep(
                step_order=int(raw_step["step_order"]),
                agent_name=str(raw_step["agent_name"]),
                status=str(raw_step["status"]),
                latency_ms=int(raw_step.get("latency_ms") or 0),
                summary=str(raw_step.get("summary") or ""),
                error_code=raw_step.get("error_code"),
            )
        )
    db.add(run)
    db.flush()
    return run


def serialize_prediction_row(
    pred: PredictionResult | None,
    predictor: NHANESPredictor | None = None,
) -> dict[str, Any] | None:
    """Serialize a PredictionResult ORM row into the API prediction payload."""
    if pred is None:
        return None
    threshold_low = float(pred.threshold)
    threshold_high = threshold_low
    if predictor is not None:
        thresholds = predictor.manifest.get("thresholds") or {}
        if "high" in thresholds:
            threshold_high = float(thresholds["high"])

    return {
        "model_version": pred.model_version,
        "model_name": pred.model_name,
        "model_sha256": pred.model_sha256,
        "threshold": threshold_low,
        "threshold_low": threshold_low,
        "threshold_high": threshold_high,
        "model_score": pred.model_score,
        "predicted_label": pred.predicted_label,
        "risk_band": pred.risk_band,
        "feature_contributions": list(pred.factors_json or []),
        "warning": SCREENING_WARNING_VI,
    }


def get_owned_assessment(
    db: Session,
    assessment_id: str,
    user_id: str,
) -> HealthAssessment:
    """Fetch a HealthAssessment by ID and verify it belongs to `user_id`."""
    assessment = db.scalar(
        select(HealthAssessment)
        .options(joinedload(HealthAssessment.prediction_result))
        .where(HealthAssessment.id == assessment_id)
    )
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found",
        )
    if assessment.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this assessment",
        )
    return assessment
