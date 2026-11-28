"""Explicit runtime wiring; NEVER put secrets in JSON reports or app responses."""
from __future__ import annotations

import getpass
import json
import os
from pathlib import Path
from typing import Any

from .step1_environment_audit import CONFIG_LOCAL, _safe_config
from .step2_prediction_integration import LocalFastAPIClient, MockPredictionClient
from .step3_knowledge_integration import LiveKnowledgeBackend, MockKnowledgeBackend
from .step5_orchestrator import make_step5_graph


def build_runtime(*, mode: str, consultation_mode: str = 'mock',
                  model: str = 'qwen2.5:1.5b', config_path: Path = CONFIG_LOCAL):
    """Return compiled graph and owned backend; caller must backend.close().

    Explicit 'live' only: local prediction API, locally persisted Chroma, remote Neo4j.
    Never serialize/echo password. No automatic model retraining, DB modifications.
    """
    if mode == 'mock':
        backend = MockKnowledgeBackend()
        predictor = MockPredictionClient()
    elif mode == 'live':
        try:
            config = _safe_config(json.loads(config_path.read_text(encoding='utf-8')))
            predictor = LocalFastAPIClient(config['prediction_api_url'])
            chroma_dir = Path(config['chroma_persist_dir']).expanduser()
            if not chroma_dir.is_absolute():
                chroma_dir = Path(__file__).resolve().parents[1] / chroma_dir
            uri, db = config['neo4j_uri'], config['neo4j_database']
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise RuntimeError('CONFIG_NOT_READY') from None
        username = os.environ.get('NEO4J_USERNAME', 'neo4j')
        password = os.environ.get('NEO4J_PASSWORD') or getpass.getpass('Neo4j password (hidden): ')
        if not password:
            raise RuntimeError('MISSING_NEO4J_PASSWORD')
        backend = LiveKnowledgeBackend(chroma_dir=chroma_dir, uri=uri,
                    username=username, password=password, database=db)
    else:
        raise RuntimeError('INVALID_MODE')
    try:
        graph = make_step5_graph(prediction_client=predictor, knowledge_backend=backend,
                                consultation_mode=consultation_mode, model=model)
    except Exception:
        backend.close()
        raise
    return graph, backend
