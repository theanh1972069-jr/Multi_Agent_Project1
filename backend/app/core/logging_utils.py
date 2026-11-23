import logging
from typing import Any

REDACTED_LOG_KEYS: frozenset[str] = frozenset(
    {
        "age",
        "gender",
        "height_cm",
        "weight_kg",
        "bmi",
        "waist_cm",
        "hip_cm",
        "whtr",
        "whr",
        "previously_diagnosed_diabetes",
        "is_pregnant",
        "password",
        "password_hash",
        "token",
        "access_token",
        "api_key",
        "secret",
        "jwt_secret_key",
        "raw_inputs",
        "raw_inputs_json",
        "derived_features_json",
    }
)

_SENSITIVE_SUFFIXES: tuple[str, ...] = ("_password", "_token", "_api_key", "_secret")


def _is_sensitive_key(key: str) -> bool:
    normalized = str(key).strip().lower()
    if normalized in REDACTED_LOG_KEYS:
        return True
    return normalized.endswith(_SENSITIVE_SUFFIXES)


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return sanitize_log_context(value)
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    return value


def sanitize_log_context(payload: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of payload with raw health measurements and secret keys removed."""
    cleaned: dict[str, Any] = {}
    for key, value in payload.items():
        if _is_sensitive_key(key):
            continue
        cleaned[key] = _sanitize_value(value)
    return cleaned


def get_logger(name: str) -> logging.Logger:
    """Return a standard library logger for the given module name."""
    return logging.getLogger(name)
