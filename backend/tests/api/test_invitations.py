from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

from tests.api.test_mongo_storage import register

pytest_plugins = ["tests.api.test_mongo_storage"]


def setup(client):
    owner, _ = register(client, "owner")
    peer, peer_id = register(client, "peer")
    other, _ = register(client, "other")
    document = client.post("/projects", headers=owner, json={}).json()
    return owner, peer, peer_id, other, document, f"/projects/{document['id']}"


def invite(client, owner, route, role="VIEWER", email="peer@example.com"):
    response = client.post(
        route + "/invitations",
        headers=owner,
        json={"email": email, "role": role, "expiresHours": 1},
    )
    assert response.status_code == 201
    return response.json()


def test_invitation_hash_one_time_email_scope_role_and_unchanged_uml(client, store):
    owner, peer, peer_id, other, document, route = setup(client)
    issued = invite(client, owner, route)
    raw = store.projects.find_one({"_id": document["id"]})
    row = raw["_invitations"][issued["id"]]
    assert issued["token"] not in str(raw)
    assert issued["token"].split(".")[-1] != row["secretHash"]
    listed = client.get(route + "/invitations", headers=owner)
    assert "secretHash" not in listed.text and "token" not in listed.text
    assert client.get(route, headers=owner).json() == document
    assert (
        client.post(
            "/project-invitations/accept", headers=other, json={"token": issued["token"]}
        ).status_code
        == 404
    )
    accepted = client.post(
        "/project-invitations/accept", headers=peer, json={"token": issued["token"]}
    )
    assert accepted.status_code == 200 and accepted.json()["effectiveRole"] == "VIEWER"
    assert store.get_membership(document["id"], peer_id) == "VIEWER"
    assert client.get(route, headers=peer).json() == document
    assert (
        client.post(
            "/project-invitations/accept", headers=peer, json={"token": issued["token"]}
        ).status_code
        == 404
    )
    assert client.get(route + "/invitations", headers=owner).json() == []


def test_only_owner_can_create_list_cancel_and_input_is_validated(client):
    owner, peer, _, other, _, route = setup(client)
    for headers in (peer, other):
        assert client.get(route + "/invitations", headers=headers).status_code == 404
        assert (
            client.post(
                route + "/invitations",
                headers=headers,
                json={"email": "x@example.com", "role": "EDITOR"},
            ).status_code
            == 404
        )
    for payload in (
        {"email": "invalid", "role": "EDITOR"},
        {"email": "peer@example.com", "role": "EDITOR", "expiresHours": 169},
    ):
        assert client.post(route + "/invitations", headers=owner, json=payload).status_code == 422
    assert (
        client.post(
            route + "/invitations",
            headers=owner,
            json={"email": "owner@example.com", "role": "EDITOR"},
        ).status_code
        == 409
    )


def test_expiry_cancel_and_wrong_secret_do_not_grant_membership(client, store):
    owner, peer, peer_id, _, document, route = setup(client)
    expired = invite(client, owner, route)
    store.projects.update_one(
        {"_id": document["id"]},
        {
            "$set": {
                f"_invitations.{expired['id']}.expiresAt": (
                    datetime.now(UTC) - timedelta(seconds=1)
                ).isoformat()
            }
        },
    )
    assert (
        client.post(
            "/project-invitations/accept", headers=peer, json={"token": expired["token"]}
        ).status_code
        == 410
    )
    assert client.get(route + "/invitations", headers=owner).json() == []
    fresh = invite(client, owner, route)
    bad = fresh["token"][:-1] + ("A" if fresh["token"][-1] != "A" else "B")
    assert (
        client.post("/project-invitations/accept", headers=peer, json={"token": bad}).status_code
        == 404
    )
    assert client.delete(route + f"/invitations/{fresh['id']}", headers=owner).status_code == 204
    assert (
        client.post(
            "/project-invitations/accept", headers=peer, json={"token": fresh["token"]}
        ).status_code
        == 404
    )
    assert store.get_membership(document["id"], peer_id) is None


def test_concurrent_acceptance_has_one_winner_and_cannot_overwrite_role(client, store):
    owner, peer, peer_id, _, document, route = setup(client)
    issued = invite(client, owner, route, "EDITOR")
    with ThreadPoolExecutor(max_workers=2) as pool:
        codes = list(
            pool.map(
                lambda _: (
                    client.post(
                        "/project-invitations/accept", headers=peer, json={"token": issued["token"]}
                    ).status_code
                ),
                range(2),
            )
        )
    assert codes.count(200) == 1 and all(code in (200, 404, 409) for code in codes)
    assert store.get_membership(document["id"], peer_id) == "EDITOR"
    assert (
        client.post(
            route + "/invitations",
            headers=owner,
            json={"email": "peer@example.com", "role": "VIEWER"},
        ).status_code
        == 409
    )


def test_registration_after_invitation_and_atomic_cancellation_before_accept(
    client, store, monkeypatch
):
    owner, peer, peer_id, _, document, route = setup(client)
    later = invite(client, owner, route, "EDITOR", "later@example.com")
    new_user, _ = register(client, "later")
    assert (
        client.post(
            "/project-invitations/accept", headers=new_user, json={"token": later["token"]}
        ).status_code
        == 200
    )
    issued = invite(client, owner, route)
    original = store.projects.update_one

    def cancel_before_write(query, update, **kwargs):
        if f"_memberships.{peer_id}" in update.get("$set", {}):
            original({"_id": document["id"]}, {"$unset": {f"_invitations.{issued['id']}": ""}})
        return original(query, update, **kwargs)

    monkeypatch.setattr(store.projects, "update_one", cancel_before_write)
    assert (
        client.post(
            "/project-invitations/accept", headers=peer, json={"token": issued["token"]}
        ).status_code
        == 409
    )
    assert store.get_membership(document["id"], peer_id) is None
