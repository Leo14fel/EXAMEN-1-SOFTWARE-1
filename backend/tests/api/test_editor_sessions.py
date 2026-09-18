from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import editor
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_editor_sessions() -> None:
    editor._editor_sessions.clear()


def create_session() -> dict[str, object]:
    response = client.post("/editor/sessions")
    assert response.status_code == 201
    return response.json()


def test_create_editor_session_returns_empty_document_and_history_state() -> None:
    payload = create_session()

    assert UUID(str(payload["sessionId"]))
    document = payload["document"]
    assert isinstance(document, dict)
    assert document["revision"] == 0
    assert document["umlModel"] == {"elements": []}
    assert document["diagramLayout"] == {"nodes": {}}
    assert payload["canUndo"] is False
    assert payload["canRedo"] is False


def test_get_editor_session_returns_current_state() -> None:
    created = create_session()

    response = client.get(f'/editor/sessions/{created["sessionId"]}')

    assert response.status_code == 200
    assert response.json() == created


def test_command_endpoint_executes_real_command_bus_and_supports_undo_redo() -> None:
    created = create_session()
    session_id = created["sessionId"]
    class_id = str(uuid4())

    command_response = client.post(
        f"/editor/sessions/{session_id}/commands",
        json={
            "commandType": "addElement",
            "element": {
                "id": class_id,
                "kind": "class",
                "name": "Cliente",
                "visibility": "public",
                "attributes": [],
                "operations": [],
            },
        },
    )

    assert command_response.status_code == 200
    command_state = command_response.json()
    assert command_state["document"]["revision"] == 1
    assert command_state["document"]["umlModel"]["elements"][0]["id"] == class_id
    assert command_state["canUndo"] is True
    assert command_state["canRedo"] is False

    undo_response = client.post(f"/editor/sessions/{session_id}/undo")
    assert undo_response.status_code == 200
    undo_state = undo_response.json()
    assert undo_state["document"]["umlModel"]["elements"] == []
    assert undo_state["document"]["revision"] == 2
    assert undo_state["canRedo"] is True

    redo_response = client.post(f"/editor/sessions/{session_id}/redo")
    assert redo_response.status_code == 200
    redo_state = redo_response.json()
    assert redo_state["document"]["umlModel"]["elements"][0]["id"] == class_id
    assert redo_state["document"]["revision"] == 3
    assert redo_state["canUndo"] is True
    assert redo_state["canRedo"] is False


def test_unknown_editor_session_returns_stable_not_found_error() -> None:
    response = client.get(f"/editor/sessions/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "EDITOR_SESSION_NOT_FOUND"


def test_command_error_is_exposed_as_stable_conflict() -> None:
    created = create_session()
    session_id = created["sessionId"]
    class_id = str(uuid4())
    command = {
        "commandType": "addElement",
        "element": {
            "id": class_id,
            "kind": "class",
            "name": "Cliente",
            "visibility": "public",
            "attributes": [],
            "operations": [],
        },
    }

    first_response = client.post(f"/editor/sessions/{session_id}/commands", json=command)
    assert first_response.status_code == 200

    response = client.post(f"/editor/sessions/{session_id}/commands", json=command)

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "ELEMENT_ALREADY_EXISTS"