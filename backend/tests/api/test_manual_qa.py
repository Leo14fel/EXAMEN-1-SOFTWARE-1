import mongomock
from fastapi.testclient import TestClient

from app.db import dependencies, mongo_store
from app.main import app as production_app
from tests.manual.qa_server import QA_EMAILS, QA_PASSWORD, create_qa_app


def test_manual_harness_is_isolated_and_reuses_current_routes(monkeypatch):
    def fail_cloud():
        raise AssertionError("Manual QA must never connect to Atlas")

    monkeypatch.setattr(dependencies, "get_mongo_store", fail_cloud)
    monkeypatch.setattr(mongo_store, "get_mongo_store", fail_cloud)
    app = create_qa_app()
    assert isinstance(app.state.qa_store.database.client, mongomock.MongoClient)
    qa_paths = set(app.openapi()["paths"])
    assert set(production_app.openapi()["paths"]) <= qa_paths
    with TestClient(app) as client:
        health = client.get("/health/db").json()
        assert health == {
            "status": "ok",
            "database": "mongomock",
            "temporary": True,
            "atlas": False,
        }
        users = []
        for email in QA_EMAILS:
            response = client.post("/auth/login", json={"email": email, "password": QA_PASSWORD})
            assert response.status_code == 200
            users.append({"Authorization": "Bearer " + response.json()["accessToken"]})
        owner, editor, viewer = users
        projects = client.get("/projects", headers=owner).json()
        assert len(projects) == 1
        route = f"/projects/{projects[0]['id']}"
        assert client.get("/projects", headers=editor).json()[0]["effectiveRole"] == "EDITOR"
        assert client.get("/projects", headers=viewer).json()[0]["effectiveRole"] == "VIEWER"
        document = client.get(route, headers=owner).json()
        assert len(document["umlModel"]["elements"]) == 3
        assert (
            client.post(route + "/undo", headers=viewer, json={"baseRevision": 0}).status_code
            == 403
        )
        assert client.get(route + "/relational-model", headers=viewer).json()["model"]
        xml = client.get(route + "/export/xmi", headers=owner).content
        response = client.post("/projects/import/xmi", headers=owner, content=xml)
        assert response.status_code == 201
        assert response.json()["document"]["id"] != document["id"]
        assert client.get(route, headers=owner).json() == document
        assert app.state.qa_store.projects.count_documents({}) == 2


def test_restart_of_manual_harness_resets_only_its_temporary_fixtures():
    first = create_qa_app()
    second = create_qa_app()
    assert first.state.qa_project_id != second.state.qa_project_id
    assert first.state.qa_store.database.client is not second.state.qa_store.database.client
    assert second.state.qa_store.projects.count_documents({}) == 1
    assert second.state.qa_store.users.count_documents({}) == 3
