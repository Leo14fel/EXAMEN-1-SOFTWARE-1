import os
from uuid import UUID, uuid4

import mongomock
import pytest
from fastapi.testclient import TestClient
from pymongo.errors import AutoReconnect, DuplicateKeyError

from app.api import projects
from app.core.config import settings
from app.db import dependencies, mongo_store
from app.db.dependencies import get_db_session
from app.db.mongo_connection import MongoSettings, create_mongo_client
from app.db.mongo_store import MongoStore
from app.domain.uml.command_bus import UmlCommandBus
from app.domain.uml.commands import AddUmlElementCommand
from app.domain.uml.models import ProjectDocument, UmlClass
from app.main import app


@pytest.fixture
def store() -> MongoStore:
    live = os.getenv("CU25_LIVE_TESTS") == "1"
    config = MongoSettings() if live else None
    connection = create_mongo_client(config) if live else mongomock.MongoClient()
    database = connection[config.mongodb_database if live else "cu25_tests"]
    prefix = f"cu25_{uuid4().hex}_"
    storage = MongoStore(database, collection_prefix=prefix)
    projects._clear_project_bus_cache()
    app.dependency_overrides[get_db_session] = lambda: storage
    try:
        storage.ensure_indexes()
        yield storage
    finally:
        app.dependency_overrides.clear()
        projects._clear_project_bus_cache()
        if live:
            # Only collections created under this test's fresh UUID prefix.
            database.drop_collection(f"{prefix}users")
            database.drop_collection(f"{prefix}projects")
        connection.close()


@pytest.fixture
def client(store: MongoStore) -> TestClient:
    with TestClient(app) as client:
        yield client


def register(client: TestClient, name: str) -> tuple[dict[str, str], UUID]:
    response = client.post(
        "/auth/register",
        json={
            "email": f"{name}@example.com",
            "password": "local-test-password",
        },
    )
    assert response.status_code == 201, response.status_code
    payload = response.json()
    return {"Authorization": f"Bearer {payload['accessToken']}"}, UUID(payload["user"]["id"])


def command_payload(revision: int = 0) -> dict:
    return {
        "baseRevision": revision,
        "command": {
            "commandType": "addElement",
            "element": {
                "kind": "class",
                "id": str(uuid4()),
                "name": "Cliente",
                "visibility": "public",
            },
        },
    }


def test_mongo_register_login_and_duplicate_email_keep_credentials_private(
    client: TestClient,
    store: MongoStore,
) -> None:
    headers, user_id = register(client, "OWNER")
    assert client.get("/auth/me", headers=headers).json()["email"] == "owner@example.com"
    user = store.get_user_by_id(user_id)
    assert user["password_hash"] != "local-test-password"
    assert "password_hash" not in client.get("/auth/me", headers=headers).text
    assert (
        client.post(
            "/auth/register",
            json={
                "email": "owner@example.com",
                "password": "another-password",
            },
        ).status_code
        == 409
    )
    assert (
        client.post(
            "/auth/login",
            json={
                "email": "owner@example.com",
                "password": "wrong-password",
            },
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/auth/login",
            json={
                "email": " OWNER@example.com ",
                "password": "local-test-password",
            },
        ).status_code
        == 200
    )


def test_mongo_unique_index_covers_concurrent_registration_precheck_race(store: MongoStore) -> None:
    store.create_user(" User@example.com ", "hash-a")
    with pytest.raises(DuplicateKeyError):
        store.create_user("user@example.com", "hash-b")


def test_mongo_collaborators_permissions_undo_redo_export_and_revocation(
    client: TestClient,
    store: MongoStore,
) -> None:
    owner, _ = register(client, "owner")
    editor, editor_id = register(client, "editor")
    viewer, viewer_id = register(client, "viewer")
    outsider, _ = register(client, "outsider")
    created = client.post("/projects", headers=owner, json={"metadata": {"name": "Ventas"}})
    assert created.status_code == 201
    project_id = created.json()["id"]
    route = f"/projects/{project_id}"
    for name, role in [("editor", "EDITOR"), ("viewer", "VIEWER")]:
        assert (
            client.post(
                f"{route}/collaborators",
                headers=owner,
                json={
                    "email": f"{name}@example.com",
                    "role": role,
                },
            ).status_code
            == 201
        )
    assert (
        client.post(
            f"{route}/collaborators",
            headers=owner,
            json={
                "email": "editor@example.com",
                "role": "EDITOR",
            },
        ).status_code
        == 409
    )
    assert client.get(route, headers=outsider).status_code == 404
    assert client.get("/projects", headers=outsider).json() == []
    assert client.get("/projects", headers=viewer).json()[0]["effectiveRole"] == "VIEWER"
    assert client.get(f"{route}/collaborators", headers=editor).status_code == 403
    assert (
        client.post(f"{route}/commands", headers=viewer, json=command_payload()).status_code == 403
    )
    changed = client.post(f"{route}/commands", headers=editor, json=command_payload())
    assert changed.status_code == 200
    assert changed.json()["document"]["revision"] == 1
    assert "_memberships" not in changed.text
    undone = client.post(f"{route}/undo", headers=owner, json={"baseRevision": 1})
    assert undone.status_code == 200
    assert undone.json()["document"]["umlModel"]["elements"] == []
    redone = client.post(f"{route}/redo", headers=owner, json={"baseRevision": 2})
    assert redone.json()["document"]["revision"] == 3
    assert (
        client.post(f"{route}/commands", headers=editor, json=command_payload()).status_code == 409
    )
    exported = client.get(f"{route}/export/xmi", headers=viewer)
    assert exported.status_code == 200 and "Cliente" in exported.text
    assert (
        client.patch(
            f"{route}/collaborators/{editor_id}", headers=owner, json={"role": "VIEWER"}
        ).status_code
        == 200
    )
    assert (
        client.post(f"{route}/commands", headers=editor, json=command_payload(3)).status_code == 403
    )
    assert client.delete(f"{route}/collaborators/{viewer_id}", headers=owner).status_code == 204
    assert client.get(route, headers=viewer).status_code == 404
    assert client.get("/projects", headers=viewer).json() == []
    assert len(store.get_project(UUID(project_id)).uml_model.elements) == 1


def test_mongo_atomic_write_rejects_editor_revoked_after_access_check(store: MongoStore) -> None:
    owner_id, editor_id = uuid4(), uuid4()
    document = ProjectDocument(ownerId=owner_id)
    store.create_project(document)
    store.add_membership(document.id, editor_id, "EDITOR")
    bus = UmlCommandBus(store.get_project(document.id))
    bus.execute(AddUmlElementCommand(element=UmlClass(name="Pending", visibility="public")))
    store.delete_membership(document.id, editor_id)
    assert not store.project_store.update_if_revision(bus.document, 0, actor_id=editor_id)
    assert store.get_project(document.id).revision == 0
    assert store.project_store.update_if_revision(bus.document, 0, actor_id=owner_id)


def test_mongo_persistence_failure_discards_uncommitted_bus_state(
    client: TestClient,
    store: MongoStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner, _ = register(client, "owner")
    project_id = client.post("/projects", headers=owner, json={}).json()["id"]
    original_update = store.projects.update_one

    def failed_update(*args: object, **kwargs: object):
        raise AutoReconnect("simulated failure with a private credential")

    monkeypatch.setattr(store.projects, "update_one", failed_update)
    failed = client.post(f"/projects/{project_id}/commands", headers=owner, json=command_payload())
    assert failed.status_code == 503
    assert "private credential" not in failed.text
    monkeypatch.setattr(store.projects, "update_one", original_update)
    assert store.get_project(UUID(project_id)).revision == 0
    recovered = client.post(
        f"/projects/{project_id}/commands", headers=owner, json=command_payload()
    )
    assert recovered.status_code == 200
    assert len(recovered.json()["document"]["umlModel"]["elements"]) == 1


def test_mongo_read_failure_is_a_redacted_503(
    client: TestClient,
    store: MongoStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner, _ = register(client, "owner")

    def unavailable(*_: object):
        raise AutoReconnect("mongodb://secret:password@private-host")

    monkeypatch.setattr(store, "get_user_by_id", unavailable)
    response = client.get("/projects", headers=owner)
    assert response.status_code == 503
    assert "password" not in response.text
    assert "private-host" not in response.text


def test_runtime_can_select_mongo_without_a_sql_session(
    client: TestClient,
    store: MongoStore,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app.dependency_overrides.pop(get_db_session)
    monkeypatch.setattr(settings, "persistence_backend", "mongodb")
    monkeypatch.setattr(dependencies, "get_mongo_store", lambda: store)
    monkeypatch.setattr(mongo_store, "get_mongo_store", lambda: store)
    owner, _ = register(client, "owner")
    assert client.post("/projects", headers=owner, json={}).status_code == 201
    assert client.get("/health/db").json() == {"status": "ok", "database": "mongodb"}
