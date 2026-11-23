from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from backend.app.schemas.assessment import AgentStepOut


class ChatSessionCreateRequest(BaseModel):
    """Request payload to create a new chat session."""

    title: str = Field(default="Cuộc trò chuyện mới", max_length=255)
    linked_assessment_id: str | None = None

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        cleaned = value.strip()
        return cleaned or "Cuộc trò chuyện mới"


class ChatSessionOut(BaseModel):
    """Chat session metadata returned to its owner."""

    id: str
    title: str
    linked_assessment_id: str | None = None
    created_at: datetime
    updated_at: datetime


class ChatMessageCreateRequest(BaseModel):
    """Request payload for posting a user message in a chat session."""

    content: str = Field(min_length=1, max_length=4000)
    linked_assessment_id: str | None = None

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("content cannot be blank")
        return cleaned


class ChatMessageOut(BaseModel):
    """Serialized chat message including evidence, safety metadata, and agent trace."""

    id: str
    session_id: str
    role: str
    content: str
    answer: str | None = None
    intent: str | None = None
    citations: list[dict[str, Any]] = Field(default_factory=list)
    kg_relations: list[dict[str, Any]] = Field(default_factory=list)
    kg_source: str | None = None
    redirect_to_assessment: bool = False
    safety_flag: str | None = None
    llm_used: bool = False
    llm_fallback: bool = False
    agent_steps: list[AgentStepOut] = Field(default_factory=list)
    total_latency_ms: int = 0
    created_at: datetime
