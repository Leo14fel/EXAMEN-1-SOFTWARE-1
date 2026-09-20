from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Lock
from time import sleep
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api import projects
from app.domain.uml.models import ProjectDocument
from app.main import app

PROJECT_ID = UUID("11111111-1111-1111-1111-111111111111")
OWNER_ID = UUID("22222222-2222-2222-2222-222222222222")
FIRST_CLASS_ID = UUID("33333333-3333-3333-3333-333333333333")
SECOND_CLASS_ID = UUID("44444444-4444-4444-4444-444444444444")
RELATIONSHIP_ID = UUID("55555555-5555-5555-5555-555555555555")
CREATED_AT = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)


def add_class_payload(class_id: UUID, name: str) -> dict[str, object]:
    return {
        "commandType": "addElement",
        "element": {
            "id": str(class_id),
            "kind": "class",
            "name": name,
            "visibility": "public",
            "attributes": [],
            "operations": [],
        },
    }


class FakeSession:
    def __init__(self, store: "InMemoryProjectStore") -> None:
        self.store = store
        self.pending_document: ProjectDocument | None = None

    def commit(self) -> None:
        if self.store.fail_commit:
            raise SQLAlchemyError("simulated commit failure")
        if self.pending_document is not None:
            self.store.document = self.pending_document.model_copy(deep=True)
            self.pending_document = None

    def rollback(self) -> None:
        self.pending_document = None

    def close(self) -> None:
        pass


class InMemoryProjectStore:
    def __init__(self) -> None:
        self.document = ProjectDocument(
            id=PROJECT_ID,
            ownerId=OWNER_ID,
            createdAt=CREATED_AT,
            updatedAt=CREATED_AT,
        )
        self.fail_commit = False
        self.force_cas_conflict = False
        self.update_active = 0
        self.maximum_parallel_updates = 0
        self.update_lock = Lock()
        self.pause_updates = False

    def get(self, _: FakeSession, project_id: UUID) -> ProjectDocument | None:
        if project_id != PROJECT_ID:
            return None
        return self.document.model_copy(deep=True)

    def update(self, session: FakeSession, document: ProjectDocument, base_revision: int) -> bool:
        with self.update_lock:
            self.update_active += 1
            self.maximum_parallel_updates = max(self.maximum_parallel_updates, self.update_active)
        try:
            if self.pause_updates:
                sleep(0.05)
            if self.force_cas_conflict:
                return False
            if self.document.revision != base_revision:
                return False
            session.pending_document = document.model_copy(deep=True)
            return True
        finally:
            with self.update_lock:
                self.update_active -= 1


@pytest.fixture(autouse=True)
def clear_project_bus_cache() -> None:
    projects._clear_project_bus_cache()
    yield
    projects._clear_project_bus_cache()


@pytest.fixture
def store(monkeypatch: pytest.MonkeyPatch) -> InMemoryProjectStore:
    value = InMemoryProjectStore()
    monkeypatch.setattr(projects, "get_project", value.get)
    monkeypatch.setattr(projects, "update_project_if_revision", value.update)
    return value


@pytest.fixture
def client(store: InMemoryProjectStore) -> TestClient:
    app.dependency_overrides[projects.get_db_session] = lambda: FakeSession(store)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def execute(client: TestClient, revision: int, command: dict[str, object]) -> object:
    return client.post(
        f"/projects/{PROJECT_ID}/commands",
        json={"baseRevision": revision, "command": command},
    )


def test_execute_persists_class_layout_and_relationship(
    client: TestClient, store: InMemoryProjectStore
) -> None:
    first = execute(client, 0, add_class_payload(FIRST_CLASS_ID, "Customer"))
    second = execute(client, 1, add_class_payload(SECOND_CLASS_ID, "Order"))
    layout = execute(
        client,
        2,
        {
            "commandType": "setNodeLayout",
            "elementId": str(FIRST_CLASS_ID),
            "layout": {"x": 10, "y": 20, "width": 220, "height": 160},
        },
    )
    relationship = execute(
        client,
        3,
        {
            "commandType": "addElement",
            "element": {
                "id": str(RELATIONSHIP_ID),
                "kind": "association",
                "sourceId": str(FIRST_CLASS_ID),
                "targetId": str(SECOND_CLASS_ID),
                "sourceMultiplicity": {"lower": 1, "upper": 1},
                "targetMultiplicity": {"lower": 0, "upper": "*"},
            },
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert layout.status_code == 200
    assert relationship.status_code == 200
    payload = relationship.json()
    assert payload["document"]["revision"] == 4
    assert len(payload["document"]["umlModel"]["elements"]) == 3
    assert payload["document"]["diagramLayout"]["nodes"][str(FIRST_CLASS_ID)]["x"] == 10
    assert store.document.revision == 4
    assert store.document.updated_at > CREATED_AT


def test_undo_redo_persist_and_keep_monotonic_revision(
    client: TestClient, store: InMemoryProjectStore
) -> None:
    added = execute(client, 0, add_class_payload(FIRST_CLASS_ID, "Customer"))
    added_updated_at = store.document.updated_at

    undone = client.post(f"/projects/{PROJECT_ID}/undo", json={"baseRevision": 1})
    undone_updated_at = store.document.updated_at
    redone = client.post(f"/projects/{PROJECT_ID}/redo", json={"baseRevision": 2})

    assert added.status_code == 200
    assert undone.status_code == 200
    assert undone.json()["document"]["revision"] == 2
    assert undone.json()["document"]["umlModel"]["elements"] == []
    assert undone.json()["canRedo"] is True
    assert redone.status_code == 200
    assert redone.json()["document"]["revision"] == 3
    assert len(store.document.uml_model.elements) == 1
    assert added_updated_at < undone_updated_at < store.document.updated_at


def test_invalid_command_does_not_persist(client: TestClient, store: InMemoryProjectStore) -> None:
    assert execute(client, 0, add_class_payload(FIRST_CLASS_ID, "Customer")).status_code == 200

    response = execute(client, 1, add_class_payload(FIRST_CLASS_ID, "Customer"))

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "ELEMENT_ALREADY_EXISTS"
    assert store.document.revision == 1
    assert len(store.document.uml_model.elements) == 1


def test_stale_revision_returns_conflict_and_invalidates_bus(
    client: TestClient, store: InMemoryProjectStore
) -> None:
    assert execute(client, 0, add_class_payload(FIRST_CLASS_ID, "Customer")).status_code == 200
    assert PROJECT_ID in projects._project_buses

    response = execute(client, 0, add_class_payload(SECOND_CLASS_ID, "Order"))

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "PROJECT_REVISION_CONFLICT"
    assert PROJECT_ID not in projects._project_buses
    assert store.document.revision == 1


def test_compare_and_swap_conflict_invalidates_mutated_bus(
    client: TestClient, store: InMemoryProjectStore
) -> None:
    store.force_cas_conflict = True

    response = execute(client, 0, add_class_payload(FIRST_CLASS_ID, "Customer"))

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "PROJECT_REVISION_CONFLICT"
    assert PROJECT_ID not in projects._project_buses
    assert store.document.revision == 0
    assert store.document.uml_model.elements == []


def test_missing_project_returns_stable_not_found_error(client: TestClient) -> None:
    response = client.post(
        f"/projects/{UUID('99999999-9999-9999-9999-999999999999')}/undo",
        json={"baseRevision": 0},
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PROJECT_NOT_FOUND"


def test_cache_is_invalidated_after_persistence_error_and_rebuilt_from_store(
    client: TestClient, store: InMemoryProjectStore
) -> None:
    store.fail_commit = True

    failed = execute(client, 0, add_class_payload(FIRST_CLASS_ID, "Customer"))

    assert failed.status_code == 503
    assert failed.json()["detail"]["code"] == "PROJECT_PERSISTENCE_UNAVAILABLE"
    assert PROJECT_ID not in projects._project_buses
    assert store.document.revision == 0

    store.fail_commit = False
    recovered = execute(client, 0, add_class_payload(FIRST_CLASS_ID, "Customer"))

    assert recovered.status_code == 200
    assert store.document.revision == 1


def test_history_is_empty_after_cache_restart_and_undo_only_affects_new_commands(
    client: TestClient, store: InMemoryProjectStore
) -> None:
    assert execute(client, 0, add_class_payload(FIRST_CLASS_ID, "Customer")).status_code == 200
    projects._clear_project_bus_cache()

    unavailable_undo = client.post(f"/projects/{PROJECT_ID}/undo", json={"baseRevision": 1})
    added_after_restart = execute(client, 1, add_class_payload(SECOND_CLASS_ID, "Order"))
    undone_after_restart = client.post(f"/projects/{PROJECT_ID}/undo", json={"baseRevision": 2})

    assert unavailable_undo.status_code == 409
    assert unavailable_undo.json()["detail"]["code"] == "UNDO_NOT_AVAILABLE"
    assert added_after_restart.status_code == 200
    assert added_after_restart.json()["canUndo"] is True
    assert undone_after_restart.status_code == 200
    assert undone_after_restart.json()["document"]["revision"] == 3
    assert [element.id for element in store.document.uml_model.elements] == [FIRST_CLASS_ID]


def test_same_project_requests_are_serialized_and_one_conflicts(
    client: TestClient, store: InMemoryProjectStore
) -> None:
    store.pause_updates = True

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(execute, client, 0, add_class_payload(FIRST_CLASS_ID, "Customer"))
        second = executor.submit(execute, client, 0, add_class_payload(SECOND_CLASS_ID, "Order"))
        responses = [first.result(timeout=3), second.result(timeout=3)]

    assert sorted(response.status_code for response in responses) == [200, 409]
    assert store.maximum_parallel_updates == 1
    assert store.document.revision == 1
    assert len(store.document.uml_model.elements) == 1
