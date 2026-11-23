"""Local-only FastAPI wrapper for Step 5's strict research/synthetic LangGraph.

Do NOT expose this endpoint to public networks: no authentication, per-user authorization,
rate limits or production clinical validation. Default backend is mock.
"""
from __future__ import annotations

import argparse

from fastapi import FastAPI

from .step5_orchestrator import MEDICAL_GATE, Step5Request, Step5Response, invoke_step5
from .step5_runtime import build_runtime


def create_app(graph, *, mode: str = 'mock') -> FastAPI:
    app = FastAPI(title='Phase 5 Research-Only Multi-Agent Sandbox', version='0.5.0')
    @app.get('/health/live')
    def live():
        return {'status':'alive', 'mode':mode}
    @app.get('/health/ready')
    def ready():
        # readiness only means graph compiled, not all downstream services reachable.
        return {'status':'graph_compiled_backends_not_probed',
                'mode':mode, 'medical_gate': MEDICAL_GATE}
    @app.post('/api/v1/research/agents/run', response_model=Step5Response)
    def run_workflow(request: Step5Request):
        return invoke_step5(graph, request)
    return app


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=['mock','live'], default='mock')
    p.add_argument('--consultation', choices=['mock','ollama'], default='mock')
    p.add_argument('--model', default='qwen2.5:1.5b')
    p.add_argument('--port', type=int, default=8001)
    args = p.parse_args()
    if not (1024 <= args.port <= 65535):
        print('STOP: INVALID_LOCAL_PORT')
        return 2
    try:
        graph, backend = build_runtime(mode=args.mode, consultation_mode=args.consultation,
                                       model=args.model)
    except Exception:
        print('STOP: BACKEND_OR_GRAPH_NOT_READY')
        return 2
    try:
        import uvicorn
        print('LOCAL_RESEARCH_ONLY | NO PUBLIC HOST | MEDICAL GATE:', MEDICAL_GATE)
        uvicorn.run(create_app(graph, mode=args.mode), host='127.0.0.1', port=args.port,
                    access_log=False)
    finally:
        backend.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
