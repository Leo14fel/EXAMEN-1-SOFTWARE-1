from collections.abc import Generator
from datetime import UTC, datetime
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.api import projects
from app.api.auth import get_current_user
from app.db.projects import ProjectRecord
from app.db.users import UserRecord
from app.domain.uml.models import ProjectDocument
from app.main import app

client = TestClient(app)
PROJECT_ID = UUID("11111111-1111-1111-1111-111111111111")
OWNER_ID = UUID("22222222-2222-2222-2222-222222222222")
CREATED_AT = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
UPDATED_AT = datetime(2026, 9, 20, 12, 1, tzinfo=UTC)


class FakeSession:
    def rollback(self) -> None:
        pass

    def close(self) -> None:
        pass


@pytest.fixture(autouse=True)
def override_database_session() -> Generator[None]:
    app.dependency_overrides[projects.get_db_session] = lambda: FakeSession()
    app.dependency_overrides[get_current_user] = lambda: UserRecord(
        id=OWNER_ID,
        email="owner@example.com",
        password_hash="not-used",
        created_at=CREATED_AT,
        updated_at=UPDATED_AT,
    )
    yield
    app.dependency_overrides.clear()


def make_document() -> ProjectDocument:
    return ProjectDocument(
        id=PROJECT_ID,
        ownerId=OWNER_ID,
        metadata={"name": "Sales"},
        createdAt=CREATED_AT,
        updatedAt=UPDATED_AT,
    )


def test_create_project_uses_authenticated_owner_and_returns_empty_valid_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_documents: list[ProjectDocument] = []

    def create(_: FakeSession, document: ProjectDocument) -> ProjectDocument:
        created_documents.append(document)
        return document

    monkeypatch.setattr(projects, "create_project", create)

    response = client.post("/projects", json={"metadata": {"name": "New project"}})

    assert response.status_code == 201
    payload = response.json()
    assert UUID(payload["ownerId"])
    assert payload["revision"] == 0
    assert payload["umlModel"] == {"elements": []}
    assert payload["diagramLayout"] == {"nodes": {}}
    assert payload["createdAt"] <= payload["updatedAt"]
    assert created_documents[0].owner_id == OWNER_ID


def test_create_project_rejects_client_supplied_owner_id() -> None:
    response = client.post("/projects", json={"ownerId": str(OWNER_ID)})

    assert response.status_code == 422


def test_list_projects_returns_summaries_in_repository_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    newer = ProjectRecord(
        id=PROJECT_ID,
        owner_id=OWNER_ID,
        project_metadata={"name": "Newer"},
        revision=3,
        created_at=CREATED_AT,
        updated_at=UPDATED_AT,
        uml_model={"elements": []},
        diagram_layout={"nodes": {}},
    )
    older = ProjectRecord(
        id=UUID("33333333-3333-3333-3333-333333333333"),
        owner_id=OWNER_ID,
        project_metadata={"name": "Older"},
        revision=1,
        created_at=CREATED_AT,
        updated_at=CREATED_AT,
        uml_model={"elements": []},
        diagram_layout={"nodes": {}},
    )
    monkeypatch.setattr(
        projects,
        "list_projects",
        lambda _, owner_id: [newer, older] if owner_id == OWNER_ID else [],
    )

    response = client.get("/projects")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(PROJECT_ID),
            "ownerId": str(OWNER_ID),
            "metadata": {"name": "Newer"},
            "revision": 3,
            "createdAt": "2026-09-20T12:00:00Z",
            "updatedAt": "2026-09-20T12:01:00Z",
        },
        {
            "id": "33333333-3333-3333-3333-333333333333",
            "ownerId": str(OWNER_ID),
            "metadata": {"name": "Older"},
            "revision": 1,
            "createdAt": "2026-09-20T12:00:00Z",
            "updatedAt": "2026-09-20T12:00:00Z",
        },
    ]


def test_get_project_returns_validated_complete_document(monkeypatch: pytest.MonkeyPatch) -> None:
    document = make_document()
    monkeypatch.setattr(projects, "get_project", lambda _, __: document)

    response = client.get(f"/projects/{PROJECT_ID}")

    assert response.status_code == 200
    assert ProjectDocument.model_validate(response.json()) == document


def test_unknown_project_returns_stable_not_found_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(projects, "get_project", lambda _, __: None)

    response = client.get(f"/projects/{PROJECT_ID}")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PROJECT_NOT_FOUND"
