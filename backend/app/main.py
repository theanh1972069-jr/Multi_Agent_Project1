from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_services.knowledge.service import HybridKnowledgeService
from ai_services.llm.factory import get_llm_provider
from ai_services.ml.predictor import NHANESPredictor
from ai_services.orchestration.graph import MultiAgentOrchestrator
from backend.app.api.v1 import api_v1_router
from backend.app.core.config import Settings, get_settings
from backend.app.core.logging_utils import get_logger
from backend.app.db.seed import seed_initial_data
from backend.app.db.session import build_engine, build_session_factory, init_db

logger = get_logger(__name__)


def create_app(
    settings: Settings | None = None,
    *,
    use_lightweight_embedder: bool = False,
) -> FastAPI:
    """Create and configure the FastAPI Modular Monolith application."""
    effective_settings = settings or get_settings()
    effective_settings.upload_dir.mkdir(parents=True, exist_ok=True)

    # Initialize DB, ChromaDB/KG, ML predictor, and LangGraph synchronously on the main
    # thread to avoid ChromaDB Rust/SQLite deadlocks inside AnyIO BlockingPortal threads.
    engine = build_engine(effective_settings.database_url)
    init_db(engine)
    session_factory = build_session_factory(engine)

    predictor = NHANESPredictor(
        artifact_path=effective_settings.model_artifact_path,
        manifest_path=effective_settings.model_manifest_path,
    )
    knowledge_service = HybridKnowledgeService(
        chroma_dir=effective_settings.chroma_persist_dir,
        kg_mirror_path=effective_settings.kg_mirror_path,
        use_lightweight_embedder=use_lightweight_embedder,
        neo4j_uri=effective_settings.neo4j_uri,
        neo4j_username=effective_settings.neo4j_username,
        neo4j_password=effective_settings.neo4j_password,
        neo4j_database=effective_settings.neo4j_database,
    )
    llm_provider = get_llm_provider(effective_settings)
    orchestrator = MultiAgentOrchestrator(
        predictor=predictor,
        knowledge_service=knowledge_service,
        llm_provider=llm_provider,
    )

    with session_factory() as db:
        seed_initial_data(db, knowledge_service)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(
        title="Diabetes Multi-Agent AI MVP",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.settings = effective_settings
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.predictor = predictor
    app.state.knowledge_service = knowledge_service
    app.state.llm_provider = llm_provider
    app.state.orchestrator = orchestrator

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(effective_settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_v1_router, prefix="/api/v1")

    logger.info(
        "Backend initialized (env=%s, llm_provider=%s)",
        effective_settings.app_env,
        effective_settings.llm_provider,
    )
    return app
