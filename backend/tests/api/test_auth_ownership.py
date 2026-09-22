from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
import pytest
from fastapi.testclient import TestClient

from app.api import auth, projects
from app.core.config import settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.users import UserRecord
from app.domain.uml.models import ProjectDocument
from app.main import app

OWNER_ID = UUID("11111111-1111-1111-1111-111111111111")
OTHER_ID = UUID("22222222-2222-2222-2222-222222222222")
PROJECT_ID = UUID("33333333-3333-3333-3333-333333333333")
NOW = datetime(2026, 9, 21, tzinfo=UTC)


class FakeSession:
    def commit(self) -> None:
        pass

    def refresh(self, _: object) -> None:
        pass

    def rollback(self) -> None:
        pass

    def close(self) -> None:
        pass


def user(user_id: UUID, email: str) -> UserRecord:
    return UserRecord(
        id=user_id,
        email=email,
        password_hash=hash_password("correct-password"),
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture(autouse=True)
def dependencies() -> None:
    app.dependency_overrides[auth.get_db_session] = lambda: FakeSession()
    yield
    app.dependency_overrides.clear()


def test_register_normalizes_email_hashes_password_and_rejects_duplicates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved: list[UserRecord] = []

    monkeypatch.setattr(auth, "get_user_by_email", lambda _, __: None)

    def create(_: FakeSession, email: str, password_hash: str) -> UserRecord:
        value = UserRecord(
            id=OWNER_ID, email=email, password_hash=password_hash, created_at=NOW, updated_at=NOW
        )
        saved.append(value)
        return value

    monkeypatch.setattr(auth, "create_user", create)
    with TestClient(app) as client:
        response = client.post(
            "/auth/register", json={"email": " User@Example.com ", "password": "correct-password"}
        )

    assert response.status_code == 201
    assert response.json()["user"] == {"id": str(OWNER_ID), "email": "user@example.com"}
    assert verify_password("correct-password", saved[0].password_hash)
    assert "correct-password" not in saved[0].password_hash

    monkeypatch.setattr(auth, "get_user_by_email", lambda _, __: saved[0])
    with TestClient(app) as client:
        duplicate = client.post(
            "/auth/register", json={"email": "user@example.com", "password": "correct-password"}
        )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "AUTH_EMAIL_ALREADY_REGISTERED"


def test_login_current_user_and_invalid_or_expired_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    owner = user(OWNER_ID, "owner@example.com")
    monkeypatch.setattr(auth, "get_user_by_email", lambda _, __: owner)
    monkeypatch.setattr(
        auth, "get_user_by_id", lambda _, user_id: owner if user_id == OWNER_ID else None
    )
    with TestClient(app) as client:
        login = client.post(
            "/auth/login", json={"email": owner.email, "password": "correct-password"}
        )
        invalid_login = client.post(
            "/auth/login", json={"email": owner.email, "password": "wrong-password"}
        )
        me = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {login.json()['accessToken']}"}
        )
        invalid = client.get("/auth/me", headers={"Authorization": "Bearer invalid"})
        expired_token = jwt.encode(
            {"sub": str(OWNER_ID), "exp": datetime.now(UTC) - timedelta(minutes=1)},
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        expired = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})

    assert login.status_code == 200
    assert invalid_login.status_code == 401
    assert invalid_login.json()["detail"]["code"] == "AUTH_INVALID_CREDENTIALS"
    assert me.json() == {"id": str(OWNER_ID), "email": owner.email}
    assert invalid.status_code == expired.status_code == 401
    assert create_access_token(OWNER_ID)


def test_projects_are_protected_and_hidden_from_other_users(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = ProjectDocument(id=PROJECT_ID, ownerId=OWNER_ID, createdAt=NOW, updatedAt=NOW)
    monkeypatch.setattr(
        projects,
        "get_project",
        lambda _, project_id: document if project_id == PROJECT_ID else None,
    )
    monkeypatch.setattr(
        projects, "list_projects", lambda _, owner_id: [] if owner_id == OTHER_ID else []
    )
    app.dependency_overrides[auth.get_current_user] = lambda: user(OTHER_ID, "other@example.com")

    with TestClient(app) as client:
        listed = client.get("/projects")
        hidden = client.get(f"/projects/{PROJECT_ID}")
        command = client.post(
            f"/projects/{PROJECT_ID}/commands",
            json={
                "baseRevision": 0,
                "command": {"commandType": "removeElement", "elementId": str(OWNER_ID)},
            },
        )
        undo = client.post(f"/projects/{PROJECT_ID}/undo", json={"baseRevision": 0})
        redo = client.post(f"/projects/{PROJECT_ID}/redo", json={"baseRevision": 0})

    assert listed.status_code == 200
    assert listed.json() == []
    assert hidden.status_code == command.status_code == undo.status_code == redo.status_code == 404
    assert hidden.json()["detail"]["code"] == "PROJECT_NOT_FOUND"


def test_projects_require_a_bearer_token() -> None:
    with TestClient(app) as client:
        response = client.get("/projects")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "AUTH_INVALID_TOKEN"
