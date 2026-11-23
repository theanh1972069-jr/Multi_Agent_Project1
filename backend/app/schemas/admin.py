from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from backend.app.schemas.assessment import AgentStepOut


class AdminStatsOut(BaseModel):
    """Aggregated system statistics for the admin dashboard."""

    total_users: int
    total_assessments: int
    active_documents: int
    total_documents: int
    total_chunks: int
    total_agent_runs: int
    agent_status_counts: dict[str, int] = Field(default_factory=dict)
    avg_latency_ms: float
    per_agent_latency_ms: dict[str, float] = Field(default_factory=dict)


class AdminAgentRunOut(BaseModel):
    """Sanitized multi-agent execution run record without raw health inputs."""

    id: str
    request_id: str
    user_id: str | None = None
    task_type: str
    status: str
    total_latency_ms: int
    llm_provider: str
    llm_model: str
    error_code: str | None = None
    created_at: datetime
    agent_steps: list[AgentStepOut] = Field(default_factory=list)


class AdminDocumentOut(BaseModel):
    """Knowledge document record visible to administrators."""

    id: str
    source_id: str
    title: str
    publisher: str
    source_url: str | None = None
    language: str
    status: str
    chunk_count: int
    uploaded_by: str | None = None
    created_at: datetime
    updated_at: datetime


class AdminDocumentStatusUpdateRequest(BaseModel):
    """Toggle knowledge document active/inactive visibility."""

    status: Literal["active", "inactive"]


class AdminDocumentDeleteOut(BaseModel):
    """Confirmation payload after deleting a knowledge document."""

    deleted: bool = True
    id: str
    source_id: str


class AdminUserUpdateRequest(BaseModel):
    """Admin update payload for toggling user activation or role."""

    is_active: bool | None = None
    role: Literal["user", "admin"] | None = None
