"""Forces a throwaway SQLite DB so tests can never touch your real Supabase
database, even if .env points there. Env vars MUST be set before importing app."""
import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-test-secret-key-1234567890"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app.database.connection import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

PASSWORD = "Passw0rd!x"


@pytest.fixture()
def client():
    # StaticPool: one shared in-memory DB across the TestClient's threads.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _record):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()


def register_and_login(client: TestClient, username: str) -> dict[str, str]:
    r = client.post("/auth/register", json={
        "username": username, "email": f"{username}@example.com", "password": PASSWORD,
    })
    assert r.status_code == 201, r.text
    r = client.post("/auth/login", data={"username": username, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture()
def auth_headers(client):
    return register_and_login(client, "somchai")


@pytest.fixture()
def other_headers(client):
    return register_and_login(client, "malee")



# ---- added in Step 6: freeze "today" so date-dependent tests are repeatable ----
from datetime import date  # noqa: E402

from app.core.clock import get_today  # noqa: E402

TODAY = date(2026, 11, 11)  # a Wednesday


@pytest.fixture()
def fixed_today(client):
    """Request this fixture in any test that relies on the default date."""
    app.dependency_overrides[get_today] = lambda: TODAY
    return TODAY