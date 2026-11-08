
from pymongo.errors import AutoReconnect

from app.api import xmi_import
from app.domain.uml.models import ProjectDocument
from app.interoperability.xmi.exporter import export_project_document
from app.interoperability.xmi.importer import import_xmi
from tests.api.test_mongo_storage import register
from tests.interoperability.test_xmi_importer import rich_document

pytest_plugins = ["tests.api.test_mongo_storage"]


def test_import_creates_new_owned_project_and_preserves_source_then_round_trips(client, store):
    owner, owner_id = register(client, "owner")
    original = client.post("/projects", headers=owner, json={"metadata": {"name": "Actual"}}).json()
    source = rich_document()
    response = client.post(
        "/projects/import/xmi",
        headers={**owner, "Content-Type": "application/xml"},
        content=export_project_document(source),
    )
    assert response.status_code == 201
    result = response.json()
    document = ProjectDocument.model_validate(result["document"])
    assert document.id != source.id and str(document.id) != original["id"]
    assert document.owner_id == owner_id and document.revision == 0
    assert document.uml_model == source.uml_model and document.diagram_layout.nodes == {}
    assert client.get(f"/projects/{original['id']}", headers=owner).json() == original
    exported = client.get(f"/projects/{document.id}/export/xmi", headers=owner)
    assert import_xmi(exported.content).model == source.uml_model
    assert len(client.get("/projects", headers=owner).json()) == 2


def test_authentication_payload_limits_and_unsupported_content_never_create_project(
    client, store, monkeypatch
):
    owner, _ = register(client, "owner")
    data = export_project_document(rich_document())
    assert client.post("/projects/import/xmi", content=data).status_code == 401
    assert (
        client.post(
            "/projects/import/xmi", headers={**owner, "Content-Type": "text/plain"}, content=data
        ).status_code
        == 415
    )
    assert client.post("/projects/import/xmi", headers=owner, content=b"not xml").status_code == 422
    monkeypatch.setattr(xmi_import, "MAX_XMI_BYTES", 8)
    assert client.post("/projects/import/xmi", headers=owner, content=data).status_code == 413
    assert store.projects.count_documents({}) == 0


def test_import_storage_failure_is_redacted_and_does_not_open_fake_project(
    client, store, monkeypatch
):
    owner, _ = register(client, "owner")
    monkeypatch.setattr(
        store, "create_project", lambda *a: (_ for _ in ()).throw(AutoReconnect("secret-uri"))
    )
    response = client.post(
        "/projects/import/xmi", headers=owner, content=export_project_document(rich_document())
    )
    assert response.status_code == 503 and "secret-uri" not in response.text
    assert store.projects.count_documents({}) == 0
