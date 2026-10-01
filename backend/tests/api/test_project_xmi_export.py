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
    def close(self) -> None:
        pass


def make_user(user_id: UUID) -> UserRecord:
    return UserRecord(
        id=user_id,
        email=f"{user_id}@example.com",
        password_hash="unused",
        created_at=NOW,
        updated_at=NOW,
    )


@pytest.fixture(autouse=True)
def dependencies() -> None:
    app.dependency_overrides[projects.get_db_session] = lambda: FakeSession()
    yield
    app.dependency_overrides.clear()


@pytest.mark.parametrize("user_id", [OWNER_ID, EDITOR_ID, VIEWER_ID])
def test_all_read_roles_can_export_xmi(monkeypatch: pytest.MonkeyPatch, user_id: UUID) -> None:
    document = ProjectDocument(
        id=PROJECT_ID,
        ownerId=OWNER_ID,
        metadata={"name": 'Sales / Q3\r\n"model"'},
        createdAt=NOW,
        updatedAt=NOW,
    )
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
        lambda _, __, member_id: (
            editor if member_id == EDITOR_ID else viewer if member_id == VIEWER_ID else None
        ),
    )
    app.dependency_overrides[get_current_user] = lambda: make_user(user_id)

    with TestClient(app) as client:
        response = client.get(f"/projects/{PROJECT_ID}/export/xmi")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")
    assert response.headers["content-disposition"] == 'attachment; filename="Sales_Q3_model.xmi"'
    assert b"<xmi:XMI" in response.content


def test_unrelated_user_cannot_export_xmi(monkeypatch: pytest.MonkeyPatch) -> None:
    document = ProjectDocument(id=PROJECT_ID, ownerId=OWNER_ID, createdAt=NOW, updatedAt=NOW)
    monkeypatch.setattr(projects, "get_project", lambda _, __: document)
    monkeypatch.setattr(projects, "get_membership", lambda *_: None)
    app.dependency_overrides[get_current_user] = lambda: make_user(
        UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    )

    with TestClient(app) as client:
        response = client.get(f"/projects/{PROJECT_ID}/export/xmi")

    assert response.status_code == 404
