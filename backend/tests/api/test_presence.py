from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError
from starlette.websockets import WebSocketDisconnect

from app.api import realtime
from app.db.presence import PresenceUpdate, participants
from app.domain.uml.models import ProjectDocument
from tests.api.test_mongo_storage import command_payload, register

pytest_plugins = ["tests.api.test_mongo_storage"]


def presence(socket, predicate=lambda event: True):
    for _ in range(30):
        event = socket.receive_json()
        if event["type"] == "presence" and predicate(event):
            return event
    raise AssertionError("Expected presence not received")


def authenticate(socket, headers):
    socket.send_json(
        {"type": "authenticate", "token": headers["Authorization"].split()[1], "presence": True}
    )
    assert socket.receive_json()["type"] == "snapshot"
    return presence(socket)


def setup_project(client, role="EDITOR"):
    owner, owner_id = register(client, "owner")
    peer, peer_id = register(client, "peer")
    project = client.post("/projects", headers=owner, json={}).json()
    route = f"/projects/{project['id']}"
    assert (
        client.post(
            route + "/collaborators",
            headers=owner,
            json={"email": "peer@example.com", "role": role},
        ).status_code
        == 201
    )
    payload = command_payload()
    saved = client.post(route + "/commands", headers=owner, json=payload).json()["document"]
    return owner, owner_id, peer, peer_id, saved, route


def test_sessions_cursor_selection_editing_and_cleanup_do_not_mutate_project(
    client, store, monkeypatch
):
    monkeypatch.setattr(realtime, "POLL_SECONDS", 0.02)
    owner, owner_id, peer, peer_id, document, route = setup_project(client)
    element_id = document["umlModel"]["elements"][0]["id"]
    with client.websocket_connect(route + "/sync") as a:
        own = authenticate(a, owner)
        assert len(own["participants"]) == 1
        with client.websocket_connect(route + "/sync") as b:
            joined = authenticate(b, peer)
            assert len(joined["participants"]) == 2
            assert joined["sessionId"] != own["sessionId"]
            presence(a, lambda event: len(event["participants"]) == 2)
            b.send_json(
                {
                    "type": "presence",
                    "cursor": {"x": 12, "y": -5},
                    "selectedElementId": element_id,
                    "editingElementId": element_id,
                }
            )
            changed = presence(a, lambda event: any(p.get("cursor") for p in event["participants"]))
            row = next(p for p in changed["participants"] if p["userId"] == str(peer_id))
            assert row["cursor"] == {"x": 12, "y": -5}
            assert row["selectedElementId"] == row["editingElementId"] == element_id
            assert row["role"] == "EDITOR" and row["name"] == "peer"
            assert "expiresAt" not in row and "password_hash" not in row
            assert client.get(route, headers=owner).json() == document
        left = presence(a, lambda event: len(event["participants"]) == 1)
        assert left["participants"][0]["userId"] == str(owner_id)
    assert store.presence.count_documents({}) == 0


def test_viewer_cannot_claim_editing_or_spoof_identity(client, store, monkeypatch):
    monkeypatch.setattr(realtime, "POLL_SECONDS", 0.02)
    _, _, peer, peer_id, document, route = setup_project(client, "VIEWER")
    element_id = document["umlModel"]["elements"][0]["id"]
    with client.websocket_connect(route + "/sync") as socket:
        authenticate(socket, peer)
        socket.send_json(
            {
                "type": "presence",
                "selectedElementId": element_id,
                "editingElementId": element_id,
                "cursor": {"x": 1, "y": 2},
            }
        )
        event = presence(socket, lambda e: bool(e["participants"][0]["cursor"]))
        row = event["participants"][0]
        assert row["editingElementId"] is None
        assert row["selectedElementId"] == element_id and row["userId"] == str(peer_id)
        socket.send_json({"type": "presence", "userId": str(uuid4())})
        with pytest.raises(WebSocketDisconnect) as error:
            socket.receive_json()
        assert error.value.code == 4400
    assert store.presence.count_documents({}) == 0


def test_presence_filters_expired_other_projects_revoked_and_deleted_elements(
    client, store, monkeypatch
):
    monkeypatch.setattr(realtime, "POLL_SECONDS", 0.02)
    owner, owner_id, peer, peer_id, data, route = setup_project(client)
    document = ProjectDocument.model_validate(data)
    ids = [str(uuid4()) for _ in range(4)]
    future = datetime.now(UTC) + timedelta(seconds=30)
    common = {
        "projectId": str(document.id),
        "name": "peer",
        "role": "EDITOR",
        "expiresAt": future,
        "cursor": None,
        "lastActivity": datetime.now(UTC).isoformat(),
        "selectedElementId": str(uuid4()),
        "editingElementId": str(uuid4()),
    }
    store.presence.insert_many(
        [
            {**common, "_id": ids[0], "userId": str(owner_id)},
            {
                **common,
                "_id": ids[1],
                "userId": str(peer_id),
                "expiresAt": datetime.now(UTC) - timedelta(seconds=1),
            },
            {**common, "_id": ids[2], "userId": str(peer_id), "projectId": str(uuid4())},
            {**common, "_id": ids[3], "userId": str(uuid4())},
        ]
    )
    peers = participants(store, document)
    assert len(peers) == 1
    assert peers[0]["selectedElementId"] is peers[0]["editingElementId"] is None
    assert store.presence.count_documents({}) == 4  # Query excludes expiry even before TTL cleanup.


def test_two_tabs_same_identity_survive_one_disconnect_and_revocation_cleans_lease(
    client, store, monkeypatch
):
    monkeypatch.setattr(realtime, "POLL_SECONDS", 0.02)
    owner, _, peer, peer_id, _, route = setup_project(client)
    with client.websocket_connect(route + "/sync") as a:
        first = authenticate(a, peer)
        with client.websocket_connect(route + "/sync") as b:
            second = authenticate(b, peer)
            assert first["sessionId"] != second["sessionId"]
            assert len(second["participants"]) == 2
            presence(a, lambda event: len(event["participants"]) == 2)
        presence(a, lambda event: len(event["participants"]) == 1)
        assert client.delete(route + f"/collaborators/{peer_id}", headers=owner).status_code == 204
        with pytest.raises(WebSocketDisconnect) as error:
            a.receive_json()
        assert error.value.code == 4404
    assert store.presence.count_documents({}) == 0


def test_cursor_bounds_nan_and_unknown_fields_are_rejected():
    for cursor in ({"x": float("nan"), "y": 0}, {"x": 1_000_001, "y": 0}):
        with pytest.raises(ValidationError):
            PresenceUpdate(cursor=cursor)
    with pytest.raises(ValidationError):
        PresenceUpdate.model_validate({"type": "presence", "role": "EDITOR"})


def test_queued_cursor_positions_coalesce_to_latest_without_revision_changes(client, monkeypatch):
    monkeypatch.setattr(realtime, "POLL_SECONDS", 0.05)
    owner, _, _, _, document, route = setup_project(client)
    with client.websocket_connect(route + "/sync") as socket:
        authenticate(socket, owner)
        for index in range(10):
            socket.send_json({"type": "presence", "cursor": {"x": index, "y": 2}})
        event = presence(socket, lambda e: e["participants"][0]["cursor"] == {"x": 9, "y": 2})
        assert event["participants"][0]["selectedElementId"] is None
        assert client.get(route, headers=owner).json() == document
