"""
Integration test for register -> login -> me.

Uses the standard FastAPI testing pattern: build a fresh SQLite engine
per test and override the get_db dependency, rather than touching the
real DATABASE_URL / module-level engine. This keeps tests fully
isolated without any module-reload trickery.
"""
import os

os.environ.setdefault("OPENAI_API_KEY", "sk-test")
os.environ.setdefault("SECRET_KEY", "testsecret")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_current_user  # noqa: F401 (ensures module import order)
from app.db.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    # app.main's module-level `settings` object was already resolved at
    # import time (development -> lifespan tries create_all against the
    # real, unreachable-in-tests Postgres engine). Patch it directly so
    # lifespan skips that; our fixture manages its own isolated SQLite
    # schema via the get_db override below.
    import app.main as main_module

    main_module.settings.app_env = "test"

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def _override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_register_then_login_then_me(client):
    register_resp = client.post(
        "/api/auth/register", json={"email": "analyst@example.com", "password": "StrongPass123"}
    )
    assert register_resp.status_code == 201
    token = register_resp.json()["access_token"]

    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "analyst@example.com"

    login_resp = client.post(
        "/api/auth/login", json={"email": "analyst@example.com", "password": "StrongPass123"}
    )
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


def test_duplicate_registration_rejected(client):
    client.post("/api/auth/register", json={"email": "dup@example.com", "password": "pass1234"})
    second = client.post("/api/auth/register", json={"email": "dup@example.com", "password": "pass1234"})
    assert second.status_code == 400
