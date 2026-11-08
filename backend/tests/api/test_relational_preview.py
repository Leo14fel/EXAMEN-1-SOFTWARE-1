from uuid import uuid4

from tests.api.test_mongo_storage import register

pytest_plugins = ["tests.api.test_mongo_storage"]


def test_authenticated_roles_can_preview_without_mutating_project_or_revision(client, store):
    owner, _ = register(client, "owner")
    viewer, _ = register(client, "viewer")
    outsider, _ = register(client, "outsider")
    document = client.post("/projects", headers=owner, json={}).json()
    route = f"/projects/{document['id']}"
    client.post(
        route + "/collaborators",
        headers=owner,
        json={"email": "viewer@example.com", "role": "VIEWER"},
    )
    payload = {
        "baseRevision": 0,
        "command": {
            "commandType": "addElement",
            "element": {
                "id": str(uuid4()),
                "kind": "class",
                "name": "Cliente",
                "visibility": "public",
                "attributes": [
                    {
                        "id": str(uuid4()),
                        "name": "nombre",
                        "type": "String",
                        "visibility": "private",
                    }
                ],
            },
        },
    }
    assert client.post(route + "/commands", headers=owner, json=payload).status_code == 200
    before = client.get(route, headers=owner).json()
    raw_before = store.projects.find_one({"_id": document["id"]})
    for headers in (owner, viewer):
        response = client.get(route + "/relational-model", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["sourceRevision"] == 1 and data["projectId"] == document["id"]
        assert data["model"]["dialect"] == "postgresql" and len(data["model"]["tables"]) == 1
    assert client.get(route + "/relational-model", headers=outsider).status_code == 404
    assert client.get(route + "/relational-model").status_code == 401
    assert client.get(route, headers=owner).json() == before
    assert store.projects.find_one({"_id": document["id"]}) == raw_before


def test_bad_profile_and_unknown_type_show_diagnostics_without_partial_schema(client):
    owner, _ = register(client, "owner")
    document = client.post(
        "/projects", headers=owner, json={"metadata": {"generation": {"version": 999}}}
    ).json()
    response = client.get(f"/projects/{document['id']}/relational-model", headers=owner)
    assert response.status_code == 200 and response.json()["model"] is None
    assert response.json()["diagnostics"][0]["code"] == "GENERATION_PROFILE_INVALID"
    document = client.post("/projects", headers=owner, json={}).json()
    route = f"/projects/{document['id']}"
    payload = {
        "baseRevision": 0,
        "command": {
            "commandType": "addElement",
            "element": {
                "id": str(uuid4()),
                "kind": "class",
                "name": "Pedido",
                "visibility": "public",
                "attributes": [
                    {
                        "id": str(uuid4()),
                        "name": "dato",
                        "type": "UnsupportedType",
                        "visibility": "private",
                    }
                ],
            },
        },
    }
    assert client.post(route + "/commands", headers=owner, json=payload).status_code == 200
    result = client.get(route + "/relational-model", headers=owner).json()
    assert result["model"] is None and result["diagnostics"][0]["code"] == "TYPE_UNSUPPORTED"


def test_metadata_profile_overrides_technical_defaults_and_empty_document_is_valid(client):
    owner, _ = register(client, "owner")
    cls_id, attr_id = uuid4(), uuid4()
    profile = {
        "classes": {str(cls_id): {"tableName": "clientes", "primaryKeyAttributeId": str(attr_id)}}
    }
    document = client.post(
        "/projects", headers=owner, json={"metadata": {"generation": profile}}
    ).json()
    route = f"/projects/{document['id']}"
    payload = {
        "baseRevision": 0,
        "command": {
            "commandType": "addElement",
            "element": {
                "id": str(cls_id),
                "kind": "class",
                "name": "Cliente",
                "visibility": "public",
                "attributes": [
                    {"id": str(attr_id), "name": "codigo", "type": "Long", "visibility": "public"}
                ],
            },
        },
    }
    assert client.post(route + "/commands", headers=owner, json=payload).status_code == 200
    table = client.get(route + "/relational-model", headers=owner).json()["model"]["tables"][0]
    assert table["name"] == "clientes" and table["columns"][0]["sqlType"] == "bigint"
    assert table["columns"][0]["generated"] is None
    empty = client.post("/projects", headers=owner, json={}).json()
    assert (
        client.get(f"/projects/{empty['id']}/relational-model", headers=owner).json()["model"][
            "tables"
        ]
        == []
    )
