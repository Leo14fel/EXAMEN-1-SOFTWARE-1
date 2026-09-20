from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock
from time import monotonic, sleep
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import editor
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_editor_sessions() -> None:
    with editor._editor_sessions_lock:
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


def test_editor_sessions_are_bounded_and_evict_least_recently_used(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(editor, "_MAX_EDITOR_SESSIONS", 2)

    first = create_session()
    second = create_session()

    first_get = client.get(f'/editor/sessions/{first["sessionId"]}')
    assert first_get.status_code == 200

    third = create_session()

    evicted = client.get(f'/editor/sessions/{second["sessionId"]}')
    assert evicted.status_code == 404
    assert evicted.json()["detail"]["code"] == "EDITOR_SESSION_NOT_FOUND"

    assert client.get(f'/editor/sessions/{first["sessionId"]}').status_code == 200
    assert client.get(f'/editor/sessions/{third["sessionId"]}').status_code == 200

def test_active_session_is_pinned_and_same_session_access_is_serialized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(editor, "_MAX_EDITOR_SESSIONS", 1)
    created = create_session()
    session_id = UUID(str(created["sessionId"]))

    first_state_entered = Event()
    release_first_state = Event()
    state_calls: list[UUID] = []
    state_calls_lock = Lock()
    original_state = editor._state

    def blocking_state(current_session_id: UUID, bus: object):
        with state_calls_lock:
            state_calls.append(current_session_id)
            call_number = len(state_calls)

        if call_number == 1:
            first_state_entered.set()
            assert release_first_state.wait(timeout=3)

        return original_state(current_session_id, bus)

    monkeypatch.setattr(editor, "_state", blocking_state)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first_request = executor.submit(editor.get_editor_session, session_id)
        assert first_state_entered.wait(timeout=3)

        second_started = Event()

        def second_get():
            second_started.set()
            return editor.get_editor_session(session_id)

        second_request = executor.submit(second_get)
        assert second_started.wait(timeout=3)

        deadline = monotonic() + 3
        active_requests = 0
        while monotonic() < deadline:
            with editor._editor_sessions_lock:
                active_requests = editor._editor_sessions[session_id].active_requests
            if active_requests == 2:
                break
            sleep(0.01)

        assert active_requests == 2

        with state_calls_lock:
            assert len(state_calls) == 1

        capacity_response = client.post("/editor/sessions")
        assert capacity_response.status_code == 503
        assert capacity_response.json()["detail"]["code"] == "EDITOR_SESSION_CAPACITY_REACHED"

        release_first_state.set()

        assert first_request.result(timeout=3).session_id == session_id
        assert second_request.result(timeout=3).session_id == session_id

    assert client.get(f"/editor/sessions/{session_id}").status_code == 200
