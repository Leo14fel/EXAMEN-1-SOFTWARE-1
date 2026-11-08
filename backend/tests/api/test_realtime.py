from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

import pytest
from fastapi import HTTPException
from pymongo.errors import AutoReconnect
from starlette.websockets import WebSocketDisconnect

from app.api import realtime
from app.core.config import settings
from app.db.mongo_projects import project_to_mongo
from app.domain.uml.models import ProjectDocument, UmlClass
from tests.api.test_mongo_storage import command_payload, register

pytest_plugins = ["tests.api.test_mongo_storage"]


def connect(client, project, headers):
    socket = client.websocket_connect(f"/projects/{project}/sync")
    return socket


def authenticate(socket, headers):
    socket.send_json({"type": "authenticate", "token": headers["Authorization"].split()[1]})
    return socket.receive_json()


def setup_project(client):
    owner, _ = register(client, "owner")
    editor, editor_id = register(client, "editor")
    project = client.post("/projects", headers=owner, json={}).json()
    assert (
        client.post(
            f"/projects/{project['id']}/collaborators",
            headers=owner,
            json={"email": "editor@example.com", "role": "EDITOR"},
        ).status_code
        == 201
    )
    return owner, editor, editor_id, project


def test_two_clients_persisted_delta_stale_rejection_undo_and_reconnect(client, monkeypatch):
    monkeypatch.setattr(realtime, "POLL_SECONDS", 0.02)
    owner, editor, _, project = setup_project(client)
    url = f"/projects/{project['id']}"
    with connect(client, project["id"], owner) as a, connect(client, project["id"], editor) as b:
        assert authenticate(a, owner)["document"] == project
        assert authenticate(b, editor)["document"] == project
        saved = client.post(url + "/commands", headers=owner, json=command_payload()).json()
        for socket in (a, b):
            event = socket.receive_json()
            assert event["type"] == "patch"
            assert (event["baseRevision"], event["revision"]) == (0, 1)
            assert "document" not in event
            assert any(change["path"] == ["umlModel", "elements", 0] for change in event["changes"])
        b.send_json({"type": "resync"})
        assert b.receive_json()["document"] == saved["document"]
        assert (
            client.post(url + "/undo", headers=editor, json={"baseRevision": 1}).status_code == 200
        )
        assert b.receive_json()["revision"] == 2
        assert (
            client.post(url + "/commands", headers=editor, json=command_payload()).status_code
            == 409
        )
    with connect(client, project["id"], editor) as socket:
        recovered = authenticate(socket, editor)
        assert recovered["document"]["revision"] == 2
        assert recovered["document"]["umlModel"]["elements"] == []


def test_role_downgrade_and_revocation_are_seen_without_uml_edit(client, monkeypatch):
    monkeypatch.setattr(realtime, "POLL_SECONDS", 0.02)
    owner, editor, editor_id, project = setup_project(client)
    url = f"/projects/{project['id']}"
    with connect(client, project["id"], editor) as socket:
        authenticate(socket, editor)
        assert (
            client.patch(
                url + f"/collaborators/{editor_id}", headers=owner, json={"role": "VIEWER"}
            ).status_code
            == 200
        )
        event = socket.receive_json()
        assert event["effectiveRole"] == "VIEWER"
        assert event["changes"] == []
        assert (
            client.post(url + "/commands", headers=editor, json=command_payload()).status_code
            == 403
        )
        assert client.delete(url + f"/collaborators/{editor_id}", headers=owner).status_code == 204
        with pytest.raises(WebSocketDisconnect) as error:
            socket.receive_json()
        assert error.value.code == 4404


def test_auth_origin_and_project_isolation(client):
    owner, _, _, project = setup_project(client)
    outsider, _ = register(client, "outsider")
    for headers, code in (({"Authorization": "Bearer invalid"}, 4401), (outsider, 4404)):
        with connect(client, project["id"], headers) as socket:
            with pytest.raises(WebSocketDisconnect) as error:
                authenticate(socket, headers)
            assert error.value.code == code
    with pytest.raises(WebSocketDisconnect) as error:
        with client.websocket_connect(
            f"/projects/{project['id']}/sync", headers={"origin": "https://other.example"}
        ):
            pass
    assert error.value.code == 4403
    with client.websocket_connect(
        f"/projects/{project['id']}/sync", headers={"origin": settings.frontend_origin}
    ) as socket:
        assert authenticate(socket, owner)["type"] == "snapshot"
        socket.send_json({"type": "execute", "command": command_payload()})
        with pytest.raises(WebSocketDisconnect) as error:
            socket.receive_json()
        assert error.value.code == 4400


def test_failed_persistence_never_publishes_uncommitted_bus(client, store, monkeypatch):
    monkeypatch.setattr(realtime, "POLL_SECONDS", 0.02)
    owner, _, _, project = setup_project(client)
    with connect(client, project["id"], owner) as socket:
        authenticate(socket, owner)
        with monkeypatch.context() as patch:
            patch.setattr(
                store.project_store,
                "update_if_revision",
                lambda *a, **k: (_ for _ in ()).throw(AutoReconnect("private")),
            )
            assert (
                client.post(
                    f"/projects/{project['id']}/commands", headers=owner, json=command_payload()
                ).status_code
                == 503
            )
        socket.send_json({"type": "resync"})
        assert socket.receive_json()["document"] == project
        monkeypatch.setattr(
            realtime,
            "subscription_state",
            lambda *a: (_ for _ in ()).throw(AutoReconnect("secret-uri")),
        )
        with pytest.raises(WebSocketDisconnect) as error:
            socket.receive_json()
        assert error.value.code == 1013
        assert "secret" not in error.value.reason


def test_external_writer_and_expired_session(client, store, monkeypatch):
    monkeypatch.setattr(realtime, "POLL_SECONDS", 0.02)
    owner, _, _, project = setup_project(client)
    with connect(client, project["id"], owner) as socket:
        authenticate(socket, owner)
        document = ProjectDocument.model_validate(project)
        document.revision = 1
        document.uml_model.elements.append(UmlClass(name="Otro proceso", visibility="public"))
        # Write to persistence without using this worker's HTTP API or event bus.
        store.projects.replace_one({"_id": project["id"]}, project_to_mongo(document))
        assert socket.receive_json()["revision"] == 1
        monkeypatch.setattr(
            realtime,
            "decode_access_token",
            lambda *a: (_ for _ in ()).throw(HTTPException(status_code=401)),
        )
        with pytest.raises(WebSocketDisconnect) as error:
            socket.receive_json()
        assert error.value.code == 4401


def test_structural_delta_handles_nested_add_delete_layout_and_lists():
    before = {
        "items": [{"id": "a", "name": "A"}, {"id": "b"}],
        "layout": {"a": {"x": 1}},
        "obsolete": True,
    }
    after = {"items": [{"id": "a", "name": "Changed"}], "layout": {"a": {"x": 5}, "b": {"x": 2}}}
    result = deepcopy(before)
    for change in realtime.document_delta(before, after):
        parent = result
        for segment in change["path"][:-1]:
            parent = parent[segment]
        key = change["path"][-1]
        if change["op"] == "remove":
            del parent[key]
        else:
            parent[key] = change["value"]
    assert result == after
    assert realtime.document_delta(after, after) == []
    assert realtime.document_delta([], [1]) == [{"op": "set", "path": [0], "value": 1}]


def test_two_editors_racing_from_same_revision_publish_one_winner(client, monkeypatch):
    monkeypatch.setattr(realtime, "POLL_SECONDS", 0.02)
    owner, editor, _, project = setup_project(client)
    with connect(client, project["id"], owner) as a, connect(client, project["id"], editor) as b:
        authenticate(a, owner)
        authenticate(b, editor)

        def write(headers):
            return client.post(
                f"/projects/{project['id']}/commands", headers=headers, json=command_payload()
            ).status_code

        with ThreadPoolExecutor(max_workers=2) as pool:
            codes = list(pool.map(write, [owner, editor]))
        assert sorted(codes) == [200, 409]
        for socket in (a, b):
            event = socket.receive_json()
            assert event["revision"] == 1
        saved = client.get(f"/projects/{project['id']}", headers=owner).json()
        assert len(saved["umlModel"]["elements"]) == 1
