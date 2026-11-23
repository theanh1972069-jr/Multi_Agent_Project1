from pathlib import Path

from backend.app.core.config import Settings, get_settings
from backend.app.core.logging_utils import sanitize_log_context


def test_default_settings_use_relative_paths_and_ollama():
    s = Settings(_env_file=None)
    assert s.llm_provider == "ollama"
    assert s.ollama_model == "qwen2.5:1.5b"
    assert s.ollama_timeout_seconds == 45.0
    assert "sqlite" in s.database_url
    assert not str(s.model_artifact_path).startswith("C:/Users/")
    assert Path(s.model_artifact_path).name == "nhanes_hba1c_v2.joblib"


def test_settings_exposes_all_required_fields_and_defaults():
    s = Settings(_env_file=None)
    assert s.app_env == "development"
    assert s.database_url.startswith("sqlite:///")
    assert s.database_url.endswith("/data/diabetes_app.db")
    assert s.cors_origins == ["http://localhost:5173", "http://127.0.0.1:5173"]
    assert s.neo4j_uri is None
    assert s.neo4j_username is None
    assert s.neo4j_password is None
    assert s.neo4j_database is None
    assert s.gemini_api_key is None
    assert s.openai_api_key is None
    assert s.openai_base_url is None
    assert Path(s.model_manifest_path).name == "model_manifest.json"
    assert Path(s.chroma_persist_dir).name == "chroma_kb"
    assert Path(s.kg_mirror_path).name == "diabetes_kg.json"
    assert Path(s.upload_dir).name == "uploads"
    assert isinstance(get_settings(), Settings)


def test_sanitize_log_context_redacts_health_and_secret_keys():
    cleaned = sanitize_log_context({
        "request_id": "req-1",
        "age": 50,
        "bmi": 31.2,
        "waist_cm": 98,
        "password": "secret",
        "status": "ok",
    })
    assert cleaned == {"request_id": "req-1", "status": "ok"}


def test_sanitize_log_context_redacts_all_sensitive_and_nested_fields():
    cleaned = sanitize_log_context({
        "request_id": "req-2",
        "gender": 1,
        "height_cm": 170,
        "weight_kg": 75,
        "hip_cm": 96,
        "token": "abc",
        "api_key": "xyz",
        "raw_inputs": {"age": 40, "bmi": 24.5},
        "nested": {"request_id": "sub-1", "gemini_api_key": "secret", "agent": "orchestrator"},
    })
    assert cleaned == {
        "request_id": "req-2",
        "nested": {"request_id": "sub-1", "agent": "orchestrator"},
    }
