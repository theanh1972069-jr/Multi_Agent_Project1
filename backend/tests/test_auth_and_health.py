from __future__ import annotations

from sqlalchemy import inspect, select

from backend.app.db.models import KnowledgeChunk, KnowledgeDocument, User


def test_health_and_seeded_demo_accounts(client):
    h = client.get("/api/v1/health")
    assert h.status_code == 200
    body = h.json()
    assert body["status"] == "ok"
    assert body["database"]["connected"] is True
    assert body["ml_model"]["loaded"] is True
    assert body["ml_model"]["model_version"]
    assert body["ml_model"]["model_name"]
    assert len(body["ml_model"]["model_sha256"]) == 64
    assert body["knowledge_base"]["active_documents"] == 7
    assert body["knowledge_base"]["total_chunks"] > 0
    assert body["knowledge_base"]["kg_source"] == "local_mirror"
    assert body["llm"]["provider"] == "ollama"
    assert body["llm"]["model"] == "qwen2.5:1.5b"
    assert body["llm"]["reachable"] is False

    login = client.post(
        "/api/v1/auth/login",
        json={"email": "user@demo.local", "password": "DemoUser123!"},
    )
    assert login.status_code == 200
    login_data = login.json()
    assert login_data["token_type"] == "bearer"
    assert login_data["user"]["role"] == "user"
    token = login_data["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    me_data = me.json()
    assert me_data["email"] == "user@demo.local"
    assert me_data["role"] == "user"
    assert me_data["is_active"] is True
    assert me_data["preferred_language"] == "vi"

    admin_login = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@demo.local", "password": "DemoAdmin123!"},
    )
    assert admin_login.status_code == 200
    assert admin_login.json()["user"]["role"] == "admin"


def test_register_duplicate_email_and_profile_update(client):
    r1 = client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "password": "Password123!",
            "full_name": "Nguyen Van A",
        },
    )
    assert r1.status_code == 201
    reg_body = r1.json()
    assert reg_body["token_type"] == "bearer"
    assert reg_body["user"]["email"] == "new@example.com"
    assert reg_body["user"]["role"] == "user"
    assert reg_body["user"]["full_name"] == "Nguyen Van A"

    r2 = client.post(
        "/api/v1/auth/register",
        json={"email": "new@example.com", "password": "Password123!", "full_name": "Dup"},
    )
    assert r2.status_code == 409

    token = reg_body["access_token"]
    upd = client.put(
        "/api/v1/auth/me",
        json={
            "full_name": "Nguyen B",
            "birth_year": 1985,
            "gender": 1,
            "preferred_language": "vi",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert upd.status_code == 200
    upd_body = upd.json()
    assert upd_body["full_name"] == "Nguyen B"
    assert upd_body["birth_year"] == 1985
    assert upd_body["gender"] == 1
    assert upd_body["preferred_language"] == "vi"


def test_auth_error_cases_and_inactive_user(client):
    assert client.get("/api/v1/auth/me").status_code == 401

    bad_pw = client.post(
        "/api/v1/auth/login",
        json={"email": "user@demo.local", "password": "WrongPassword!"},
    )
    assert bad_pw.status_code == 401

    unknown = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@demo.local", "password": "DemoUser123!"},
    )
    assert unknown.status_code == 401

    # Deactivate user in DB and confirm login returns 403 and existing token is rejected
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "user@demo.local", "password": "DemoUser123!"},
    )
    token = login.json()["access_token"]

    session_factory = client.app.state.session_factory
    with session_factory() as db:
        user = db.scalar(select(User).where(User.email == "user@demo.local"))
        assert user is not None
        user.is_active = False
        db.commit()

    locked_login = client.post(
        "/api/v1/auth/login",
        json={"email": "user@demo.local", "password": "DemoUser123!"},
    )
    assert locked_login.status_code == 403

    locked_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert locked_me.status_code == 403


def test_schema_creates_all_10_tables_and_knowledge_chunks(client):
    engine = client.app.state.engine
    table_names = set(inspect(engine).get_table_names())
    expected_tables = {
        "users",
        "user_profiles",
        "health_assessments",
        "prediction_results",
        "chat_sessions",
        "chat_messages",
        "knowledge_documents",
        "knowledge_chunks",
        "agent_runs",
        "agent_steps",
    }
    assert expected_tables.issubset(table_names)

    session_factory = client.app.state.session_factory
    with session_factory() as db:
        docs = db.scalars(select(KnowledgeDocument)).all()
        chunks = db.scalars(select(KnowledgeChunk)).all()
        assert len(docs) == 7
        assert all(doc.status == "active" and doc.chunk_count > 0 for doc in docs)
        assert len(chunks) == sum(doc.chunk_count for doc in docs)
