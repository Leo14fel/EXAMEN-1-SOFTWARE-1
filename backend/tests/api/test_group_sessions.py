from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from pymongo.errors import AutoReconnect

from app.db import group_sessions
from tests.api.test_mongo_storage import register

pytest_plugins = ["tests.api.test_mongo_storage"]


def setup(client):
    owner, owner_id = register(client, "owner")
    peer, peer_id = register(client, "peer")
    outsider, _ = register(client, "outsider")
    project = client.post("/projects", headers=owner, json={}).json()
    route = f"/projects/{project['id']}"
    client.post(
        route + "/collaborators",
        headers=owner,
        json={"email": "peer@example.com", "role": "EDITOR"},
    )
    return owner, owner_id, peer, peer_id, outsider, project, route


def message(text="Hola", identity=None):
    return {"id": str(identity or uuid4()), "text": text}


def test_group_history_identity_idempotence_and_original_diagram(client, store):
    owner, owner_id, peer, _, outsider, project, route = setup(client)
    path = route + "/session"
    assert client.post(path, headers=owner).json()["participants"][0]["userId"] == str(owner_id)
    assert len(client.post(path, headers=peer).json()["participants"]) == 2
    payload = message("  Hola grupo  ")
    saved = client.post(path + "/messages", headers=owner, json=payload)
    assert saved.status_code == 200
    event = saved.json()
    assert event["actorId"] == str(owner_id) and event["text"] == "Hola grupo"
    assert event["sequence"] == 1
    assert client.post(path + "/messages", headers=owner, json=payload).json() == event
    assert client.post(path + "/messages", headers=peer, json=payload).status_code == 409
    assert client.get(path, headers=peer).json()["events"] == [event]
    assert client.get(path, headers=outsider).status_code == 404
    assert client.get(route, headers=owner).json() == project
    assert "_pendingMessage" not in store.projects.find_one({"_id": project["id"]})


def test_viewer_can_read_but_not_send_or_spoof_and_input_is_bounded(client):
    owner, _, peer, peer_id, outsider, _, route = setup(client)
    path = route + "/session"
    client.patch(route + f"/collaborators/{peer_id}", headers=owner, json={"role": "VIEWER"})
    assert client.post(path, headers=peer).status_code == 200
    assert client.post(path + "/messages", headers=peer, json=message()).status_code == 403
    assert client.post(path + "/messages", headers=outsider, json=message()).status_code == 404
    for payload in (message("  "), message("x" * 4001), {**message(), "actorId": str(peer_id)}):
        assert client.post(path + "/messages", headers=owner, json=payload).status_code == 422


def test_concurrent_messages_have_unique_contiguous_sequence_and_pagination(client):
    owner, _, peer, _, _, _, route = setup(client)
    path = route + "/session"
    client.post(path, headers=owner)

    def send(index):
        return client.post(
            path + "/messages", headers=owner if index % 2 else peer, json=message(str(index))
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(send, range(6)))
    assert all(response.status_code == 200 for response in results)
    history = client.get(path, headers=owner).json()
    assert [event["sequence"] for event in history["events"]] == list(range(1, 7))
    older = client.get(path + "?before=4", headers=owner).json()
    assert [event["sequence"] for event in older["events"]] == [1, 2, 3]
    assert len({event["id"] for event in history["events"]}) == 6


def test_pending_message_recovers_after_append_failure_without_duplicate(
    client, store, monkeypatch
):
    owner, _, peer, _, _, project, route = setup(client)
    path = route + "/session"
    payload = message()
    with monkeypatch.context() as patch:
        patch.setattr(
            group_sessions,
            "append_event",
            lambda *a, **k: (_ for _ in ()).throw(AutoReconnect("secret")),
        )
        failed = client.post(path + "/messages", headers=owner, json=payload)
        assert failed.status_code == 503 and "secret" not in failed.text
    assert store.projects.find_one({"_id": project["id"]})["_pendingMessage"]["id"] == payload["id"]
    recovered = client.get(path, headers=peer).json()["events"]
    assert len(recovered) == 1
    assert client.post(path + "/messages", headers=owner, json=payload).json() == recovered[0]
    assert "_pendingMessage" not in store.projects.find_one({"_id": project["id"]})


def test_storage_limit_rejects_without_fake_success_and_keeps_recoverable_reservation(
    client, store, monkeypatch
):
    owner, _, _, _, _, project, route = setup(client)
    path = route + "/session"
    client.post(path, headers=owner)
    monkeypatch.setattr(group_sessions, "MAX_BSON_BYTES", 100)
    assert client.post(path + "/messages", headers=owner, json=message()).status_code == 413
    assert client.get(path, headers=owner).json()["events"] == []
    assert "_pendingMessage" not in store.projects.find_one({"_id": project["id"]})


def test_activity_atomic_with_project_recovers_after_promotion_failure(client, store, monkeypatch):
    from app.api import projects
    from tests.api.test_mongo_storage import command_payload

    owner, owner_id, peer, _, _, project, route = setup(client)
    with monkeypatch.context() as patch:
        patch.setattr(
            projects,
            "flush_pending",
            lambda *a, **k: (_ for _ in ()).throw(AutoReconnect("outage")),
        )
        response = client.post(route + "/commands", headers=owner, json=command_payload())
        assert response.status_code == 200
    raw = store.projects.find_one({"_id": project["id"]})
    assert raw["revision"] == 1 and raw["_pendingActivity"]["projectRevision"] == 1
    assert "_pendingActivity" not in client.get(route, headers=owner).json()
    recovered = client.get(route + "/session", headers=peer).json()["events"]
    assert len(recovered) == 1
    assert recovered[0]["actorId"] == str(owner_id) and recovered[0]["action"] == "addElement"
    assert "umlModel" not in recovered[0]
    assert recovered[0]["id"].startswith("activity:")
    assert (
        client.post(
            route + "/session/messages",
            headers=owner,
            json={"id": recovered[0]["id"], "text": "No puede suplantar actividad"},
        ).status_code
        == 422
    )
    assert "_pendingActivity" not in store.projects.find_one({"_id": project["id"]})
    assert client.get(route + "/session", headers=peer).json()["events"] == recovered


def test_rejected_mutation_has_no_activity_and_undo_redo_are_attributed(client):
    from tests.api.test_mongo_storage import command_payload

    owner, owner_id, peer, peer_id, _, _, route = setup(client)
    assert (
        client.post(route + "/commands", headers=owner, json=command_payload()).status_code == 200
    )
    assert client.post(route + "/commands", headers=peer, json=command_payload()).status_code == 409
    # A conflict clears ephemeral history; build a new accepted operation before undo.
    assert (
        client.post(route + "/commands", headers=peer, json=command_payload(1)).status_code == 200
    )
    assert client.post(route + "/undo", headers=peer, json={"baseRevision": 2}).status_code == 200
    assert client.post(route + "/redo", headers=owner, json={"baseRevision": 3}).status_code == 200
    events = client.get(route + "/session", headers=peer).json()["events"]
    assert [event["projectRevision"] for event in events] == [1, 2, 3, 4]
    assert [event["action"] for event in events] == ["addElement", "addElement", "undo", "redo"]
    assert events[2]["actorId"] == str(peer_id) and events[3]["actorId"] == str(owner_id)


def test_group_stream_shared_and_history_recovers_without_in_memory_bus(client, monkeypatch):
    from app.api import projects, realtime

    monkeypatch.setattr(realtime, "POLL_SECONDS", 0.02)
    owner, _, peer, _, outsider, project, route = setup(client)

    def authorize(socket, headers):
        socket.send_json(
            {
                "type": "authenticate",
                "token": headers["Authorization"].split()[1],
                "conversation": True,
            }
        )
        assert socket.receive_json()["type"] == "snapshot"
        return socket.receive_json()

    with (
        client.websocket_connect(route + "/sync") as a,
        client.websocket_connect(route + "/sync") as b,
    ):
        assert authorize(a, owner)["type"] == "conversation"
        assert authorize(b, peer)["type"] == "conversation"
        payload = message("Contexto compartido")
        saved = client.post(route + "/session/messages", headers=owner, json=payload).json()
        for socket in (a, b):
            for _ in range(10):
                event = socket.receive_json()
                if event["type"] == "conversation" and event["events"]:
                    assert event["events"] == [saved]
                    break
            else:
                raise AssertionError("Message missing")
    projects._clear_project_bus_cache()
    with client.websocket_connect(route + "/sync") as late:
        assert authorize(late, peer)["events"] == [saved]
    assert client.get(route + "/session", headers=outsider).status_code == 404


def test_atomic_message_reservation_rejects_concurrent_revocation(client, store, monkeypatch):
    owner, _, peer, peer_id, _, _, route = setup(client)
    original = store.projects.update_one

    def revoke_before_reservation(query, update, **kwargs):
        if "_pendingMessage" in update.get("$set", {}):
            original({"_id": query["_id"]}, {"$unset": {f"_memberships.{peer_id}": ""}})
        return original(query, update, **kwargs)

    monkeypatch.setattr(store.projects, "update_one", revoke_before_reservation)
    assert client.post(route + "/session/messages", headers=peer, json=message()).status_code == 403
    assert client.get(route + "/session", headers=owner).json()["events"] == []


def test_history_pages_do_not_skip_older_or_incremental_events(client, store):
    owner, owner_id, _, _, _, project, route = setup(client)
    client.post(route + "/session", headers=owner)
    from uuid import UUID

    for index in range(55):
        group_sessions.append_event(
            store,
            UUID(project["id"]),
            {
                "id": str(uuid4()),
                "kind": "message",
                "actorId": str(owner_id),
                "actorName": "owner",
                "createdAt": "2026-11-07T00:00:00+00:00",
                "text": str(index),
            },
        )
    latest = client.get(route + "/session", headers=owner).json()
    assert [event["sequence"] for event in latest["events"]] == list(range(6, 56))
    assert latest["hasEarlier"] and latest["cursor"] == 55
    older = client.get(route + "/session?before=6", headers=owner).json()
    assert [event["sequence"] for event in older["events"]] == list(range(1, 6))
    assert not older["hasEarlier"]
    forward = group_sessions.session_page(store, UUID(project["id"]), after=53, limit=2)
    assert [event["sequence"] for event in forward["events"]] == [54, 55]
