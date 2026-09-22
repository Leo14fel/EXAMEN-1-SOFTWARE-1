from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api import projects
from app.api.auth import get_current_user
from app.db.memberships import ProjectMembershipRecord, ProjectRole
from app.db.users import UserRecord
from app.domain.uml.models import ProjectDocument
from app.main import app

OWNER_ID = UUID("11111111-1111-1111-1111-111111111111")
EDITOR_ID = UUID("22222222-2222-2222-2222-222222222222")
VIEWER_ID = UUID("33333333-3333-3333-3333-333333333333")
PROJECT_ID = UUID("44444444-4444-4444-4444-444444444444")
NOW = datetime(2026, 9, 22, tzinfo=UTC)


class FakeSession:
    def add(self, _: object) -> None:
        pass

    def delete(self, _: object) -> None:
        pass

    def commit(self) -> None:
        pass

    def refresh(self, _: object) -> None:
        pass

    def rollback(self) -> None:
        pass

    def close(self) -> None:
        pass


def make_user(user_id: UUID, email: str) -> UserRecord:
    return UserRecord(
        id=user_id, email=email, password_hash="unused", created_at=NOW, updated_at=NOW
    )


@pytest.fixture(autouse=True)
def dependencies() -> None:
    app.dependency_overrides[projects.get_db_session] = lambda: FakeSession()
    yield
    app.dependency_overrides.clear()


def test_editor_can_read_and_mutate_but_viewer_is_read_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = ProjectDocument(id=PROJECT_ID, ownerId=OWNER_ID, createdAt=NOW, updatedAt=NOW)
    editor = ProjectMembershipRecord(
        project_id=PROJECT_ID, user_id=EDITOR_ID, role=ProjectRole.EDITOR
    )
    viewer = ProjectMembershipRecord(
        project_id=PROJECT_ID, user_id=VIEWER_ID, role=ProjectRole.VIEWER
    )
    monkeypatch.setattr(projects, "get_project", lambda _, __: document)
    monkeypatch.setattr(
        projects,
        "get_membership",
        lambda _, __, user_id: (
            editor if user_id == EDITOR_ID else viewer if user_id == VIEWER_ID else None
        ),
    )
    monkeypatch.setattr(projects, "update_project_if_revision", lambda *_: True)

    app.dependency_overrides[get_current_user] = lambda: make_user(EDITOR_ID, "editor@example.com")
    with TestClient(app) as client:
        assert client.get(f"/projects/{PROJECT_ID}").status_code == 200
        assert (
            client.post(
                f"/projects/{PROJECT_ID}/commands",
                json={
                    "baseRevision": 0,
                    "command": {"commandType": "removeElement", "elementId": str(OWNER_ID)},
                },
            ).status_code
            == 409
        )

    app.dependency_overrides[get_current_user] = lambda: make_user(VIEWER_ID, "viewer@example.com")
    with TestClient(app) as client:
        response = client.post(
            f"/projects/{PROJECT_ID}/commands",
            json={
                "baseRevision": 0,
                "command": {"commandType": "removeElement", "elementId": str(OWNER_ID)},
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "PROJECT_ACCESS_FORBIDDEN"


def test_only_owner_can_manage_collaborators(monkeypatch: pytest.MonkeyPatch) -> None:
    document = ProjectDocument(id=PROJECT_ID, ownerId=OWNER_ID, createdAt=NOW, updatedAt=NOW)
    collaborator = make_user(EDITOR_ID, "editor@example.com")
    membership = ProjectMembershipRecord(
        project_id=PROJECT_ID, user_id=EDITOR_ID, role=ProjectRole.EDITOR
    )
    monkeypatch.setattr(projects, "get_project", lambda _, __: document)
    monkeypatch.setattr(projects, "get_user_by_email", lambda _, __: collaborator)
    monkeypatch.setattr(projects, "get_user_by_id", lambda _, __: collaborator)
    monkeypatch.setattr(projects, "list_memberships", lambda _, __: [membership])
    monkeypatch.setattr(projects, "get_membership", lambda _, __, ___: membership)

    app.dependency_overrides[get_current_user] = lambda: make_user(OWNER_ID, "owner@example.com")
    with TestClient(app) as client:
        listed = client.get(f"/projects/{PROJECT_ID}/collaborators")
        changed = client.patch(
            f"/projects/{PROJECT_ID}/collaborators/{EDITOR_ID}", json={"role": "VIEWER"}
        )

    assert listed.status_code == changed.status_code == 200
    assert listed.json()[0]["email"] == "editor@example.com"
    assert changed.json()["role"] == "VIEWER"

    app.dependency_overrides[get_current_user] = lambda: collaborator
    with TestClient(app) as client:
        denied = client.get(f"/projects/{PROJECT_ID}/collaborators")

    assert denied.status_code == 403
