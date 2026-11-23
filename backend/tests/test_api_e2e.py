from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models import (
    AgentRun,
    AgentStep,
    HealthAssessment,
    KnowledgeDocument,
    PredictionResult,
)


def _login(client, email: str, password: str) -> dict[str, str]:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_assessment_history_and_owner_isolation(client):
    u1 = _login(client, "user@demo.local", "DemoUser123!")

    r = client.post(
        "/api/v1/assessments",
        headers=u1,
        json={
            "age": 54,
            "gender": 1,
            "height_cm": 170,
            "weight_kg": 86,
            "waist_cm": 100,
            "hip_cm": 98,
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "completed"
    assert data["prediction"] is not None
    assert data["prediction"]["model_score"] >= 0.0
    assert data["derived_features"]["bmi"] > 0.0
    assert len(data["agent_steps"]) == 5
    assert len(data["citations"]) >= 1

    # Out-of-scope assessment should NOT create a PredictionResult row
    r_oos = client.post(
        "/api/v1/assessments",
        headers=u1,
        json={
            "age": 15,
            "gender": 2,
            "height_cm": 160,
            "weight_kg": 50,
            "waist_cm": 70,
        },
    )
    assert r_oos.status_code == 200, r_oos.text
    oos_data = r_oos.json()
    assert oos_data["status"] == "out_of_scope"
    assert oos_data["prediction"] is None

    session_factory = client.app.state.session_factory
    with session_factory() as db:
        oos_row = db.scalar(
            select(HealthAssessment).where(HealthAssessment.id == oos_data["id"])
        )
        assert oos_row is not None
        oos_pred = db.scalar(
            select(PredictionResult).where(PredictionResult.assessment_id == oos_data["id"])
        )
        assert oos_pred is None

    # Owner history list & detail
    hist = client.get("/api/v1/assessments", headers=u1)
    assert hist.status_code == 200
    assert len(hist.json()) == 2

    detail = client.get(f"/api/v1/assessments/{data['id']}", headers=u1)
    assert detail.status_code == 200
    assert detail.json()["id"] == data["id"]
    assert detail.json()["prediction"]["model_score"] == data["prediction"]["model_score"]

    # Register second user and verify IDOR protection
    r_reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "u2@example.com",
            "password": "Password123!",
            "full_name": "User Two",
        },
    )
    assert r_reg.status_code == 201
    u2 = {"Authorization": f"Bearer {r_reg.json()['access_token']}"}
    assert client.get(f"/api/v1/assessments/{data['id']}", headers=u2).status_code in {403, 404}
    assert client.get("/api/v1/assessments", headers=u2).json() == []


def test_chat_with_linked_assessment_and_knowledge_graph(client):
    u1 = _login(client, "user@demo.local", "DemoUser123!")
    a_resp = client.post(
        "/api/v1/assessments",
        headers=u1,
        json={
            "age": 48,
            "gender": 2,
            "height_cm": 160,
            "weight_kg": 72,
            "waist_cm": 90,
        },
    )
    assert a_resp.status_code == 200
    a = a_resp.json()

    # Second user cannot link u1's assessment to their chat session
    r_reg = client.post(
        "/api/v1/auth/register",
        json={
            "email": "chat_other@example.com",
            "password": "Password123!",
            "full_name": "Other User",
        },
    )
    u2 = {"Authorization": f"Bearer {r_reg.json()['access_token']}"}
    bad_link = client.post(
        "/api/v1/chat/sessions",
        headers=u2,
        json={"title": "IDOR attempt", "linked_assessment_id": a["id"]},
    )
    assert bad_link.status_code in {403, 404}

    s = client.post(
        "/api/v1/chat/sessions",
        headers=u1,
        json={"title": "Hỏi về kết quả", "linked_assessment_id": a["id"]},
    )
    assert s.status_code == 201, s.text
    sid = s.json()["id"]

    # u2 cannot read or post to u1's session
    assert client.get(f"/api/v1/chat/sessions/{sid}/messages", headers=u2).status_code in {403, 404}
    assert (
        client.post(
            f"/api/v1/chat/sessions/{sid}/messages",
            headers=u2,
            json={"content": "Xin chào"},
        ).status_code
        in {403, 404}
    )

    m = client.post(
        f"/api/v1/chat/sessions/{sid}/messages",
        headers=u1,
        json={"content": "Giải thích giúp tôi kết quả đánh giá vừa rồi và chỉ số HbA1c"},
    )
    assert m.status_code == 200, m.text
    m_data = m.json()
    assert len(m_data["citations"]) >= 1
    assert m_data["content"]
    assert m_data["answer"] == m_data["content"]
    assert len(m_data["agent_steps"]) >= 3

    # Verify session listing & message history
    sessions_list = client.get("/api/v1/chat/sessions", headers=u1)
    assert sessions_list.status_code == 200
    assert any(item["id"] == sid for item in sessions_list.json())

    msgs_list = client.get(f"/api/v1/chat/sessions/{sid}/messages", headers=u1)
    assert msgs_list.status_code == 200
    assert len(msgs_list.json()) == 2

    # Knowledge sources & graph
    sources = client.get("/api/v1/knowledge/sources", headers=u1)
    assert sources.status_code == 200
    assert len(sources.json()) == 7

    kg = client.get("/api/v1/knowledge/graph", headers=u1)
    assert kg.status_code == 200
    assert len(kg.json()["nodes"]) >= 10
    assert len(kg.json()["edges"]) >= 10

    # Chat biometric scoring redirect & safety guardrail
    redir = client.post(
        f"/api/v1/chat/sessions/{sid}/messages",
        headers=u1,
        json={"content": "Tôi 50 tuổi, cao 170 cm, nặng 85 kg, hãy chấm điểm nguy cơ cho tôi"},
    )
    assert redir.status_code == 200
    assert redir.json()["redirect_to_assessment"] is True
    assert redir.json()["intent"] == "risk_assessment_redirect"

    safe = client.post(
        f"/api/v1/chat/sessions/{sid}/messages",
        headers=u1,
        json={"content": "Hãy kê đơn thuốc tiểu đường và liều lượng metformin cho tôi"},
    )
    assert safe.status_code == 200
    assert safe.json()["intent"] == "safety_guardrail"
    assert safe.json()["safety_flag"] is not None


def test_admin_upload_toggle_delete_and_invalid_file_rejection(client):
    user_h = _login(client, "user@demo.local", "DemoUser123!")
    admin_h = _login(client, "admin@demo.local", "DemoAdmin123!")

    # Non-admin denied on all admin endpoints
    assert client.get("/api/v1/admin/stats", headers=user_h).status_code == 403
    assert client.get("/api/v1/admin/agent-runs", headers=user_h).status_code == 403
    assert client.get("/api/v1/admin/documents", headers=user_h).status_code == 403
    assert client.get("/api/v1/admin/users", headers=user_h).status_code == 403

    # Reject invalid extension
    bad = client.post(
        "/api/v1/admin/documents/upload",
        headers=admin_h,
        data={"title": "Bad", "publisher": "Test"},
        files={"file": ("evil.exe", b"MZ\x90\x00", "application/octet-stream")},
    )
    assert bad.status_code == 400

    # Reject empty text file
    empty_doc = client.post(
        "/api/v1/admin/documents/upload",
        headers=admin_h,
        data={"title": "Empty", "publisher": "Test"},
        files={"file": ("empty.txt", b"   \n  ", "text/plain")},
    )
    assert empty_doc.status_code == 400

    # Reject oversized file (> 5 MB)
    oversized = client.post(
        "/api/v1/admin/documents/upload",
        headers=admin_h,
        data={"title": "Too Big", "publisher": "Test"},
        files={"file": ("big.txt", b"A" * (5 * 1024 * 1024 + 10), "text/plain")},
    )
    assert oversized.status_code == 400

    # Reject corrupted PDF file
    bad_pdf = client.post(
        "/api/v1/admin/documents/upload",
        headers=admin_h,
        data={"title": "Corrupt PDF", "publisher": "Test"},
        files={"file": ("broken.pdf", b"%PDF-1.4\nnot-a-valid-pdf-stream", "application/pdf")},
    )
    assert bad_pdf.status_code == 400

    # Upload valid markdown doc, verify active, deactivate, then delete
    up = client.post(
        "/api/v1/admin/documents/upload",
        headers=admin_h,
        data={
            "title": "Hướng dẫn ăn uống mới",
            "publisher": "Bo Y Te",
            "language": "vi",
        },
        files={
            "file": (
                "diet.md",
                "## Dinh dưỡng\nĂn nhiều rau xanh và tập thể dục 150 phút mỗi tuần giúp giảm nguy cơ tiền tiểu đường.".encode(
                    "utf-8"
                ),
                "text/markdown",
            )
        },
    )
    assert up.status_code == 201, up.text
    doc_id = up.json()["id"]
    assert up.json()["status"] == "active"
    assert up.json()["chunk_count"] >= 1

    # Verify visible in public active sources
    active_sources = client.get("/api/v1/knowledge/sources", headers=user_h).json()
    assert any(s["id"] == doc_id for s in active_sources)

    # Deactivate and confirm hidden from active sources
    t = client.patch(
        f"/api/v1/admin/documents/{doc_id}/status",
        headers=admin_h,
        json={"status": "inactive"},
    )
    assert t.status_code == 200 and t.json()["status"] == "inactive"
    active_after_toggle = client.get("/api/v1/knowledge/sources", headers=user_h).json()
    assert all(s["id"] != doc_id for s in active_after_toggle)

    # Delete uploaded doc
    d = client.delete(f"/api/v1/admin/documents/{doc_id}", headers=admin_h)
    assert d.status_code == 200
    all_docs = client.get("/api/v1/admin/documents", headers=admin_h).json()
    assert all(doc["id"] != doc_id for doc in all_docs)

    # Generate an assessment so admin stats & agent-runs have data
    assess = client.post(
        "/api/v1/assessments",
        headers=user_h,
        json={
            "age": 50,
            "gender": 1,
            "height_cm": 172,
            "weight_kg": 80,
            "waist_cm": 96,
        },
    )
    assert assess.status_code == 200

    stats = client.get("/api/v1/admin/stats", headers=admin_h)
    assert stats.status_code == 200
    stats_body = stats.json()
    assert stats_body["total_users"] >= 2
    assert stats_body["total_assessments"] >= 1
    assert stats_body["active_documents"] == 7
    assert stats_body["total_agent_runs"] >= 1
    assert "avg_latency_ms" in stats_body
    assert "per_agent_latency_ms" in stats_body

    runs = client.get("/api/v1/admin/agent-runs", headers=admin_h)
    assert runs.status_code == 200
    runs_body = runs.json()
    assert len(runs_body) >= 1
    assert "raw_inputs" not in runs_body[0]
    assert len(runs_body[0]["agent_steps"]) == 5

    # Admin user list & lock/unlock
    users = client.get("/api/v1/admin/users", headers=admin_h).json()
    target = next(u for u in users if u["email"] == "user@demo.local")
    locked = client.patch(
        f"/api/v1/admin/users/{target['id']}",
        headers=admin_h,
        json={"is_active": False},
    )
    assert locked.status_code == 200 and locked.json()["is_active"] is False
    assert client.get("/api/v1/assessments", headers=user_h).status_code == 403

    unlocked = client.patch(
        f"/api/v1/admin/users/{target['id']}",
        headers=admin_h,
        json={"is_active": True},
    )
    assert unlocked.status_code == 200 and unlocked.json()["is_active"] is True

    # Admin cannot deactivate own account
    admin_self = next(u for u in users if u["email"] == "admin@demo.local")
    self_lock = client.patch(
        f"/api/v1/admin/users/{admin_self['id']}",
        headers=admin_h,
        json={"is_active": False},
    )
    assert self_lock.status_code == 400

    # Toggling a seeded source inactive updates KG visibility too
    kg_before = client.get("/api/v1/knowledge/graph", headers=user_h).json()
    docs_now = client.get("/api/v1/admin/documents", headers=admin_h).json()
    seeded_doc = next(doc for doc in docs_now if doc["source_id"] == "LC-HBA1C-006")
    client.patch(
        f"/api/v1/admin/documents/{seeded_doc['id']}/status",
        headers=admin_h,
        json={"status": "inactive"},
    )
    kg_after = client.get("/api/v1/knowledge/graph", headers=user_h).json()
    assert len(kg_after["nodes"]) <= len(kg_before["nodes"])
    assert len(kg_after["edges"]) < len(kg_before["edges"])
    client.patch(
        f"/api/v1/admin/documents/{seeded_doc['id']}/status",
        headers=admin_h,
        json={"status": "active"},
    )


def test_admin_upload_metadata_limits_and_rollback_cleanup(client, monkeypatch):
    admin_h = _login(client, "admin@demo.local", "DemoAdmin123!")

    # Reject metadata exceeding KnowledgeDocument column limits with HTTP 400
    assert (
        client.post(
            "/api/v1/admin/documents/upload",
            headers=admin_h,
            data={"title": "T" * 513, "publisher": "Bo Y Te"},
            files={"file": ("ok.md", b"# Heading\nValid content", "text/markdown")},
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/admin/documents/upload",
            headers=admin_h,
            data={"title": "Valid", "publisher": "P" * 256},
            files={"file": ("ok.md", b"# Heading\nValid content", "text/markdown")},
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/admin/documents/upload",
            headers=admin_h,
            data={"title": "Valid", "publisher": "Bo Y Te", "language": "v" * 17},
            files={"file": ("ok.md", b"# Heading\nValid content", "text/markdown")},
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/api/v1/admin/documents/upload",
            headers=admin_h,
            data={
                "title": "Valid",
                "publisher": "Bo Y Te",
                "source_url": "https://example.com/" + "a" * 1020,
            },
            files={"file": ("ok.md", b"# Heading\nValid content", "text/markdown")},
        ).status_code
        == 400
    )

    # Simulate DB commit failure after ChromaDB ingestion and verify rollback cleanup
    original_commit = Session.commit

    def _failing_commit(self):
        raise RuntimeError("Simulated DB commit failure")

    monkeypatch.setattr(Session, "commit", _failing_commit)
    with pytest.raises(RuntimeError, match="Simulated DB commit failure"):
        client.post(
            "/api/v1/admin/documents/upload",
            headers=admin_h,
            data={
                "title": "Rollback Test",
                "publisher": "Bo Y Te",
                "source_id": "ROLLBACK-TEST-01",
            },
            files={
                "file": (
                    "rollback.md",
                    b"## Test\nThong tin tam thoi de kiem tra rollback.",
                    "text/markdown",
                )
            },
        )
    monkeypatch.setattr(Session, "commit", original_commit)

    upload_dir = client.app.state.settings.upload_dir
    assert not (upload_dir / "ROLLBACK-TEST-01.md").exists()

    stored = client.app.state.knowledge_service.rag_store._collection.get(
        where={"source_id": "ROLLBACK-TEST-01"},
        include=[],
    )
    assert len(stored.get("ids") or []) == 0

    with client.app.state.session_factory() as db:
        row = db.scalar(
            select(KnowledgeDocument).where(
                KnowledgeDocument.source_id == "ROLLBACK-TEST-01"
            )
        )
        assert row is None
