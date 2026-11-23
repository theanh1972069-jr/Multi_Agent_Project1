"""Stage 5 Step 1: LOCAL, OFFLINE CONFIGURATION AUDIT.

This script never contacts FastAPI, Neo4j, ChromaDB or Ollama. It does not
import/load a model and does not read any clinical records. If a model path is
configured, it streams the file to compute SHA256 without deserializing it.
Only the generated JSON report is written to disk.

Run: python -m phase5.step1_environment_audit
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
from urllib.parse import urlparse

from .contracts import (
    EXPECTED_SHA256, THRESHOLD, CHROMA_COLLECTION, PREDICTION_PATH,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_EXAMPLE = PROJECT_ROOT / "config" / "phase5_step1_config.example.json"
CONFIG_LOCAL = PROJECT_ROOT / "config" / "phase5_step1_config.json"
OUTPUT_DEFAULT = PROJECT_ROOT / "data" / "outputs" / "phase5_step1" / "step1_environment_audit.json"
KNOWN_KEYS = {
    "model_artifact_path", "prediction_api_url", "chroma_persist_dir",
    "chroma_collection", "neo4j_uri", "neo4j_database", "ollama_url",
}
FORBIDDEN_KEY_PARTS = ("password", "secret", "api_key", "token", "credential", "private_key")


def _local_url_valid(url: str, expected_path: str | None = None) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        return False
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        return False
    if expected_path is not None and parsed.path != expected_path:
        return False
    return True


def _safe_config(data: object) -> dict:
    if not isinstance(data, dict):
        raise ValueError("CONFIG_MUST_BE_OBJECT")
    if any(any(bad in k.lower() for bad in FORBIDDEN_KEY_PARTS) for k in data if isinstance(k, str)):
        raise ValueError("SECRETS_ARE_FORBIDDEN_IN_CONFIG")
    if any(not isinstance(k, str) or k not in KNOWN_KEYS for k in data):
        raise ValueError("UNKNOWN_CONFIG_KEY")
    result = {k: data.get(k) for k in KNOWN_KEYS}
    for k, v in result.items():
        if v is not None and not isinstance(v, str):
            raise ValueError("CONFIG_VALUES_MUST_BE_STRINGS_OR_NULL")
    return result


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _path_from_config(value: str | None) -> Path | None:
    if not value or not value.strip():
        return None
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def audit(config: dict, *, config_is_example: bool) -> dict:
    result = {
        "experiment": "EXP-PHASE5-STEP1-LOCAL-001",
        "stage": "phase5_step1_integration_contracts_and_environment_audit",
        "configuration_mode": "example_not_connected" if config_is_example else "local_user_configuration",
        "python": {"version": platform.python_version(), "version_supported": sys.version_info >= (3, 11)},
        "packages": {p: _package_version(p) for p in (
            "pydantic", "langgraph", "fastapi", "requests", "chromadb", "neo4j", "scikit-learn"
        )},
        "locked_contract": {
            "model_name": "LogisticRegression",
            "model_sha256_expected": EXPECTED_SHA256,
            "threshold": THRESHOLD,
            "task": "classify_hba1c_ge_5_7_indicator",
            "chroma_collection": CHROMA_COLLECTION,
            "medical_knowledge_gate": "BLOCKED_RESEARCH_ONLY",
        },
        "local_checks": {},
        "next_actions": [],
        "network_calls": False,
        "llm_called": False,
        "database_reads": False,
        "database_writes": False,
        "ml_model_loaded": False,
        "ml_training": False,
    }
    checks = result["local_checks"]
    todo = result["next_actions"]

    # Read-only *hash*, NEVER unpickle/unserialize the model artifact.
    model_path = _path_from_config(config.get("model_artifact_path"))
    if model_path is None:
        checks["model_artifact"] = "NOT_CONFIGURED"
        todo.append("SET_MODEL_ARTIFACT_PATH")
    elif not model_path.is_file():
        checks["model_artifact"] = "FILE_NOT_FOUND"
        todo.append("FIX_MODEL_ARTIFACT_PATH")
    else:
        checks["model_artifact"] = (
            "SHA256_MATCH" if _file_sha256(model_path) == EXPECTED_SHA256 else "SHA256_MISMATCH"
        )
        if checks["model_artifact"] != "SHA256_MATCH":
            todo.append("CHECK_MODEL_ARTIFACT_VERSION_DO_NOT_OVERWRITE")

    prediction_url = config.get("prediction_api_url")
    checks["prediction_api_config"] = (
        "LOCAL_ROUTE_VALID_NOT_CONNECTED" if isinstance(prediction_url, str)
        and _local_url_valid(prediction_url, PREDICTION_PATH) else "INVALID_LOCAL_API_ROUTE"
    )
    if checks["prediction_api_config"] != "LOCAL_ROUTE_VALID_NOT_CONNECTED":
        todo.append("FIX_LOCAL_PREDICTION_API_URL")

    chroma_path = _path_from_config(config.get("chroma_persist_dir"))
    if chroma_path is None:
        checks["chroma_directory"] = "NOT_CONFIGURED"
        todo.append("SET_CHROMA_PERSIST_DIR")
    else:
        checks["chroma_directory"] = (
            "DIRECTORY_EXISTS_NOT_CONNECTED" if chroma_path.is_dir() else "DIRECTORY_NOT_FOUND"
        )
        if not chroma_path.is_dir():
            todo.append("FIX_CHROMA_PERSIST_DIR")
    checks["chroma_collection_config"] = (
        "EXPECTED_NAME" if config.get("chroma_collection") == CHROMA_COLLECTION else "COLLECTION_NAME_MISMATCH"
    )
    if checks["chroma_collection_config"] != "EXPECTED_NAME":
        todo.append("RESTORE_EXPECTED_CHROMA_COLLECTION")

    neo_uri = config.get("neo4j_uri")
    if not neo_uri:
        checks["neo4j_uri_config"] = "NOT_CONFIGURED"
        todo.append("SET_NEO4J_URI_WITHOUT_SECRETS")
    else:
        parsed = urlparse(neo_uri)
        # Aura should use TLS and not embed username/password in the URI.
        checks["neo4j_uri_config"] = (
            "TLS_URI_FORMAT_VALID_NOT_CONNECTED"
            if parsed.scheme in {"neo4j+s", "bolt+s"}
            and bool(parsed.hostname) and not parsed.username and not parsed.password
            and not parsed.path.strip("/") and not parsed.query and not parsed.fragment
            else "INVALID_OR_UNSAFE_NEO4J_URI"
        )
        if checks["neo4j_uri_config"] != "TLS_URI_FORMAT_VALID_NOT_CONNECTED":
            todo.append("FIX_NEO4J_TLS_URI_NO_EMBEDDED_PASSWORD")
    checks["neo4j_database_config"] = (
        "CONFIGURED_NOT_CONNECTED" if config.get("neo4j_database") else "NOT_CONFIGURED"
    )
    if checks["neo4j_database_config"] == "NOT_CONFIGURED":
        todo.append("SET_NEO4J_DATABASE")

    ollama_url = config.get("ollama_url")
    checks["ollama_config"] = (
        "OPTIONAL_LOCAL_FORMAT_VALID_NOT_CONNECTED" if isinstance(ollama_url, str)
        and _local_url_valid(ollama_url) else "OPTIONAL_NOT_CONFIGURED_OR_INVALID"
    )
    required = [
        "model_artifact", "prediction_api_config", "chroma_directory",
        "chroma_collection_config", "neo4j_uri_config", "neo4j_database_config",
    ]
    expected = {
        "model_artifact": "SHA256_MATCH",
        "prediction_api_config": "LOCAL_ROUTE_VALID_NOT_CONNECTED",
        "chroma_directory": "DIRECTORY_EXISTS_NOT_CONNECTED",
        "chroma_collection_config": "EXPECTED_NAME",
        "neo4j_uri_config": "TLS_URI_FORMAT_VALID_NOT_CONNECTED",
        "neo4j_database_config": "CONFIGURED_NOT_CONNECTED",
    }
    result["status"] = (
        "configured_not_connected" if all(checks[k] == expected[k] for k in required)
        else "local_setup_action_required"
    )
    result["warning"] = (
        "File/config inspection ONLY. No FastAPI/ChromaDB/Neo4j/Ollama connectivity, "
        "clinical validation, source rights, or medical approval has been tested."
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only local Phase 5 Step 1 environment audit")
    parser.add_argument("--config", type=Path, default=CONFIG_LOCAL)
    parser.add_argument("--output", type=Path, default=OUTPUT_DEFAULT)
    args = parser.parse_args()
    config_path = args.config
    is_example = False
    if not config_path.exists() and config_path.resolve() == CONFIG_LOCAL.resolve():
        config_path = CONFIG_EXAMPLE
        is_example = True
    try:
        config = _safe_config(json.loads(config_path.read_text(encoding="utf-8")))
        report = audit(config, config_is_example=is_example)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        # Do not echo exception text: absolute local paths and config values may be sensitive.
        print(f"Audit configuration error: {type(exc).__name__}; check config JSON and key names")
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("===== GIAI ĐOẠN 5 — BƯỚC 1: ENVIRONMENT AUDIT =====")
    print(f"Python: {report['python']['version']}")
    print("Contracts: LogisticRegression | threshold 0.225 | medical gate BLOCKED_RESEARCH_ONLY")
    for name, status in report["local_checks"].items():
        print(f"{name}: {status}")
    print("LLM: NO | Network: NO | DB writes: NO | ML training: NO")
    print("Status:", report["status"])
    print("Saved report:", args.output)
    print("===== SEND THIS OUTPUT AND JSON REPORT =====")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
