from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import anyio.to_thread
import httpx
import pytest
import starlette.concurrency
import starlette.routing
from fastapi import FastAPI

from backend.app.core.config import Settings
from backend.app.main import create_app


async def _run_sync_inline(func: Any, *args: Any, **kwargs: Any) -> Any:
    clean_kwargs = {
        k: v
        for k, v in kwargs.items()
        if k not in ("limiter", "abandon_on_cancel", "cancellable")
    }
    return func(*args, **clean_kwargs)


def _drive_coroutine(coro: Any) -> Any:
    try:
        while True:
            coro.send(None)
    except StopIteration as exc:
        return exc.value


class SyncASGITransport(httpx.BaseTransport):
    """Drive FastAPI's ASGI coroutine synchronously without asyncio self-pipes."""

    def __init__(self, app: FastAPI) -> None:
        self.app = app

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        body = request.read()
        raw_path = request.url.raw_path.split(b"?", 1)[0]
        query_string = request.url.query
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": request.method,
            "headers": [(k.lower(), v) for k, v in request.headers.raw],
            "path": unquote(raw_path.decode("ascii")),
            "raw_path": raw_path,
            "query_string": query_string,
            "scheme": request.url.scheme or "http",
            "server": (request.url.host or "testserver", request.url.port or 80),
            "client": ("127.0.0.1", 50000),
            "app": self.app,
        }
        sent_request = False
        status_code = 500
        response_headers: list[tuple[bytes, bytes]] = []
        body_chunks: list[bytes] = []

        async def receive() -> dict[str, Any]:
            nonlocal sent_request
            if not sent_request:
                sent_request = True
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.disconnect"}

        async def send(message: dict[str, Any]) -> None:
            nonlocal status_code, response_headers
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_headers = list(message.get("headers", []))
            elif message["type"] == "http.response.body":
                chunk = message.get("body", b"")
                if chunk:
                    body_chunks.append(chunk)

        _drive_coroutine(self.app(scope, receive, send))
        return httpx.Response(
            status_code=status_code,
            headers=[
                (k.decode("latin-1"), v.decode("latin-1"))
                for k, v in response_headers
            ],
            content=b"".join(body_chunks),
            request=request,
        )


class SandboxTestClient(httpx.Client):
    """httpx.Client backed by SyncASGITransport with `.app` reference."""

    def __init__(self, app: FastAPI) -> None:
        super().__init__(transport=SyncASGITransport(app), base_url="http://testserver")
        self.app = app


@pytest.fixture()
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        database_url=f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        chroma_persist_dir=tmp_path / "chroma",
        kg_mirror_path=tmp_path / "kg.json",
        upload_dir=tmp_path / "uploads",
        ollama_base_url="http://127.0.0.1:59999",
        ollama_timeout_seconds=1.0,
        neo4j_uri="",
    )


@pytest.fixture()
def client(
    test_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> Iterator[SandboxTestClient]:
    monkeypatch.setattr(anyio.to_thread, "run_sync", _run_sync_inline)
    monkeypatch.setattr(starlette.concurrency, "run_in_threadpool", _run_sync_inline)
    monkeypatch.setattr(starlette.routing, "run_in_threadpool", _run_sync_inline)

    app = create_app(test_settings, use_lightweight_embedder=True)
    app.state.llm_provider.health_check = lambda: False
    with SandboxTestClient(app) as test_client:
        try:
            yield test_client
        finally:
            app.state.engine.dispose()
