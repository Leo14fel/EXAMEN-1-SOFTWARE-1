from concurrent.futures import ThreadPoolExecutor
from threading import Event
from uuid import uuid4

import pytest
from fastapi import HTTPException
from pydantic import SecretStr
from pymongo.errors import AutoReconnect

from app.ai.gemini import ProviderError
from app.ai.intents import IntentResponse
from app.api import ai
from app.core.config import settings
from app.db import ai_requests
from tests.api.test_group_sessions import setup

pytest_plugins = ["tests.api.test_mongo_storage"]


@pytest.fixture
def provider(monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", SecretStr("CONTROLLED_TEST_KEY"))
    calls = []

    def controlled(context):
        calls.append(context)
        return IntentResponse(intent={"operation": "createClass", "name": "Producto"})

    monkeypatch.setattr(ai, "invoke_provider", controlled)
    return calls


def payload(project, text="Crea Producto", identity=None):
    return {"id": str(identity or uuid4()), "baseRevision": project["revision"], "text": text}


def test_ai_status_missing_configuration_and_unauthorized_access(client, store, monkeypatch):
    owner, _, peer, peer_id, outsider, project, route = setup(client)
    monkeypatch.setattr(settings, "gemini_api_key", None)
    assert client.get(route + "/ai/status", headers=owner).json()["configured"] is False
    assert client.get(route + "/ai/status", headers=outsider).status_code == 404
    assert client.get(route + "/ai/status").status_code == 401
    assert (
        client.post(route + "/ai/requests", headers=owner, json=payload(project)).status_code == 503
    )
    client.patch(route + f"/collaborators/{peer_id}", headers=owner, json={"role": "VIEWER"})
    assert (
        client.post(route + "/ai/requests", headers=peer, json=payload(project)).status_code == 403
    )
    assert "_aiRequest" not in store.projects.find_one({"_id": project["id"]})


def test_shared_proposal_is_durable_idempotent_and_never_modifies_uml(
    client, store, provider, monkeypatch
):
    owner, _, peer, _, outsider, project, route = setup(client)
    body = payload(project)
    result = client.post(route + "/ai/requests", headers=owner, json=body)
    assert result.status_code == 200, result.text
    saved = result.json()
    assert saved["result"]["status"] == "proposed"
    assert saved["result"]["canApply"] is False
    assert saved["request"]["actorId"] == project["ownerId"]
    assert saved["result"]["actorId"] == "ai:gemini"
    assert client.get(route, headers=owner).json() == project
    assert "_aiRequest" not in store.projects.find_one({"_id": project["id"]})
    assert client.get(route + "/session", headers=peer).json()["events"] == [
        saved["request"],
        saved["result"],
    ]
    assert client.get(route + "/ai/requests/" + body["id"], headers=outsider).status_code == 404
    assert client.post(route + "/ai/requests", headers=owner, json=body).json() == saved
    assert len(provider) == 1
    assert client.post(route + "/ai/requests", headers=peer, json=body).status_code == 409
    assert (
        client.post(
            route + "/ai/requests", headers=owner, json={**body, "text": "Otro"}
        ).status_code
        == 409
    )
    monkeypatch.setattr(settings, "gemini_api_key", None)
    assert client.post(route + "/ai/requests", headers=owner, json=body).json() == saved
    assert "CONTROLLED_TEST_KEY" not in str(saved)


def test_revision_and_context_are_checked_before_provider(client, provider):
    owner, _, _, _, outsider, project, route = setup(client)
    assert (
        client.post(
            route + "/ai/requests", headers=owner, json={**payload(project), "baseRevision": 9}
        ).status_code
        == 409
    )
    assert (
        client.post(route + "/ai/requests", headers=outsider, json=payload(project)).status_code
        == 404
    )
    other = client.post("/projects", headers=owner, json={}).json()
    client.post(
        f"/projects/{other['id']}/session/messages",
        headers=owner,
        json={"id": str(uuid4()), "text": "NEVER_OTHER_PROJECT"},
    )
    assert (
        client.post(route + "/ai/requests", headers=owner, json=payload(project)).status_code == 200
    )
    assert len(provider) == 1 and "NEVER_OTHER_PROJECT" not in str(provider[0])
    assert provider[0]["projectId"] == project["id"]


@pytest.mark.parametrize("kind", ["revision", "access", "token"])
def test_changes_during_inference_prevent_current_proposal(
    client, store, provider, monkeypatch, kind
):
    owner, _, peer, peer_id, _, project, route = setup(client)

    def delayed(_):
        if kind == "revision":
            store.projects.update_one({"_id": project["id"]}, {"$inc": {"revision": 1}})
        elif kind == "access":
            store.projects.update_one(
                {"_id": project["id"]}, {"$unset": {f"_memberships.{peer_id}": ""}}
            )
        else:

            def expired(*_):
                raise HTTPException(401)

            monkeypatch.setattr(ai, "get_current_user", expired)
        return IntentResponse(intent={"operation": "createClass", "name": "Producto"})

    monkeypatch.setattr(ai, "invoke_provider", delayed)
    body = payload(project)
    response = client.post(route + "/ai/requests", headers=peer, json=body)
    assert response.status_code == {"revision": 200, "access": 404, "token": 401}[kind]
    result = client.get(route + "/ai/requests/" + body["id"], headers=owner).json()["result"]
    assert result["status"] in {"stale", "failed"} and "intent" not in result
    assert client.get(route, headers=owner).json()["umlModel"] == project["umlModel"]


def test_provider_failure_and_invalid_proposal_are_shared_and_retry_never_calls_again(
    client, provider, monkeypatch
):
    owner, _, _, _, _, project, route = setup(client)
    for error in (ProviderError("AI_RATE_LIMIT"), ValueError("not safe to expose")):
        calls = []

        def failed(_, calls=calls, error=error):
            calls.append(1)
            raise error

        monkeypatch.setattr(ai, "invoke_provider", failed)
        body = payload(project)
        response = client.post(route + "/ai/requests", headers=owner, json=body)
        assert response.status_code == 200
        assert response.json()["result"]["status"] == "failed"
        assert "not safe" not in response.text
        assert (
            client.post(route + "/ai/requests", headers=owner, json=body).json() == response.json()
        )
        assert len(calls) == 1


def test_simultaneous_retry_and_other_request_do_not_duplicate_provider(
    client, provider, monkeypatch
):
    owner, _, _, _, _, project, route = setup(client)
    entered, release = Event(), Event()
    calls = []

    def delayed(_):
        calls.append(1)
        entered.set()
        assert release.wait(5)
        return IntentResponse(intent={"operation": "createClass", "name": "Producto"})

    monkeypatch.setattr(ai, "invoke_provider", delayed)
    body = payload(project)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(client.post, route + "/ai/requests", headers=owner, json=body)
        try:
            assert entered.wait(5)
            assert client.post(route + "/ai/requests", headers=owner, json=body).status_code == 202
            assert (
                client.post(
                    route + "/ai/requests", headers=owner, json=payload(project)
                ).status_code
                == 409
            )
            assert client.get(route, headers=owner).json() == project
        finally:
            release.set()
        assert future.result().status_code == 200
    assert len(calls) == 1


def test_completed_request_between_lookup_and_reservation_cannot_call_provider_twice(
    client, store, provider, monkeypatch
):
    owner, _, _, _, _, project, route = setup(client)
    body = payload(project)
    original = store.projects.update_one
    intercepted = False

    def racing_update(query, update, *args, **kwargs):
        nonlocal intercepted
        if query.get("_aiRequest") == {"$exists": False} and not intercepted:
            intercepted = True
            assert client.post(route + "/ai/requests", headers=owner, json=body).status_code == 200
        return original(query, update, *args, **kwargs)

    monkeypatch.setattr(store.projects, "update_one", racing_update)
    response = client.post(route + "/ai/requests", headers=owner, json=body)
    assert response.status_code == 200 and response.json()["result"]["status"] == "proposed"
    assert len(provider) == 1
    assert store.projects.find_one({"_id": project["id"]})["_aiSeen"][body["id"]]
    assert client.get(route, headers=owner).json() == project


def test_interrupted_lease_is_recovered_without_repeating_inference(
    client, store, provider, monkeypatch
):
    owner, _, _, _, _, project, route = setup(client)

    def interrupted(_):
        store.projects.update_one({"_id": project["id"]}, {"$set": {"_aiRequest.deadline": 0}})
        client.get(route + "/session", headers=owner)
        return IntentResponse(intent={"operation": "createClass", "name": "Producto"})

    monkeypatch.setattr(ai, "invoke_provider", interrupted)
    body = payload(project)
    result = client.post(route + "/ai/requests", headers=owner, json=body).json()
    assert result["result"]["code"] == "AI_REQUEST_INTERRUPTED"
    assert client.post(route + "/ai/requests", headers=owner, json=body).json() == result
    assert "_aiRequest" not in store.projects.find_one({"_id": project["id"]})


def test_saved_result_promotes_after_storage_interruption_without_second_inference(
    client, store, provider, monkeypatch
):
    owner, _, _, _, _, project, route = setup(client)
    original = ai_requests.append_event

    def unavailable(storage, project_id, event):
        if event["kind"] == "aiResult":
            raise AutoReconnect("controlled failure")
        return original(storage, project_id, event)

    monkeypatch.setattr(ai_requests, "append_event", unavailable)
    body = payload(project)
    assert client.post(route + "/ai/requests", headers=owner, json=body).status_code == 503
    assert (
        store.projects.find_one({"_id": project["id"]})["_aiRequest"]["result"]["status"]
        == "proposed"
    )
    monkeypatch.setattr(ai_requests, "append_event", original)
    result = client.post(route + "/ai/requests", headers=owner, json=body)
    assert result.json()["result"]["status"] == "proposed"
    assert (
        len(provider) == 1
        and len(client.get(route + "/session", headers=owner).json()["events"]) == 2
    )


@pytest.mark.parametrize(
    "change", [{"text": " "}, {"text": "x" * 2001}, {"actorId": "spoof"}, {"input": "voice"}]
)
def test_request_shape_cannot_spoof_actor_or_enable_voice_execution(client, provider, change):
    owner, _, _, _, _, project, route = setup(client)
    assert (
        client.post(
            route + "/ai/requests", headers=owner, json={**payload(project), **change}
        ).status_code
        == 422
    )
    assert not provider


def test_ai_events_reach_editor_and_viewer_websockets_and_survive_reconnection(
    client, provider, monkeypatch
):
    from app.api import realtime

    monkeypatch.setattr(realtime, "POLL_SECONDS", 0.02)
    owner, _, peer, peer_id, _, project, route = setup(client)
    client.patch(route + f"/collaborators/{peer_id}", headers=owner, json={"role": "VIEWER"})
    with (
        client.websocket_connect(route + "/sync") as first,
        client.websocket_connect(route + "/sync") as second,
    ):
        for socket, headers in ((first, owner), (second, peer)):
            socket.send_json(
                {
                    "type": "authenticate",
                    "token": headers["Authorization"].split()[1],
                    "conversation": True,
                }
            )
            assert socket.receive_json()["type"] == "snapshot"
            assert socket.receive_json()["type"] == "conversation"
        body = payload(project)
        assert client.post(route + "/ai/requests", headers=owner, json=body).status_code == 200
        for socket in (first, second):
            kinds = set()
            while kinds != {"aiRequest", "aiResult"}:
                frame = socket.receive_json()
                assert frame["type"] == "conversation"
                kinds.update(entry["kind"] for entry in frame["events"])
    with client.websocket_connect(route + "/sync") as later:
        later.send_json(
            {
                "type": "authenticate",
                "token": peer["Authorization"].split()[1],
                "conversation": True,
            }
        )
        assert later.receive_json()["document"] == project
        assert [event["kind"] for event in later.receive_json()["events"]] == [
            "aiRequest",
            "aiResult",
        ]
    assert len(provider) == 1 and client.get(route, headers=owner).json() == project


def test_ai_reservation_size_guard_prevents_provider_call(client, provider, monkeypatch):
    owner, _, _, _, _, project, route = setup(client)
    monkeypatch.setattr(ai_requests, "MAX_BSON_BYTES", 1)
    response = client.post(route + "/ai/requests", headers=owner, json=payload(project))
    assert response.status_code == 413 and not provider


def test_replayed_result_cannot_replace_the_first_intent_in_group_history(client, store, provider):
    from app.db.group_sessions import append_event

    owner, _, _, _, _, project, route = setup(client)
    saved = client.post(route + "/ai/requests", headers=owner, json=payload(project)).json()[
        "result"
    ]
    with pytest.raises(HTTPException) as conflict:
        append_event(
            store,
            project["id"],
            {**saved, "intent": {"intent": {"operation": "deleteClass", "target": "Otro"}}},
        )
    assert conflict.value.status_code == 409
