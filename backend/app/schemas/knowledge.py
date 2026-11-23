from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class KnowledgeSourceOut(BaseModel):
    """Public metadata for an active diabetes knowledge document."""

    id: str
    source_id: str
    title: str
    publisher: str
    source_url: str | None = None
    language: str
    status: str
    chunk_count: int
    created_at: datetime
    updated_at: datetime


class KnowledgeGraphOut(BaseModel):
    """Diabetes Knowledge Graph nodes and edges filtered to active sources."""

    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    kg_source: str
