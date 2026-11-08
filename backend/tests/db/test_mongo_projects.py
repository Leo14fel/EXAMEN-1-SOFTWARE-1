from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from bson import BSON
from pymongo.errors import AutoReconnect, DuplicateKeyError
from pymongo.results import UpdateResult
from pymongo.write_concern import WriteConcern

from app.db.mongo_projects import MongoProjectStore, project_from_mongo, project_to_mongo
from app.domain.uml.command_bus import UmlCommandBus
from app.domain.uml.commands import AddUmlElementCommand
from app.domain.uml.models import (
    CanonicalUmlModel,
    DiagramLayout,
    DiagramNodeLayout,
    ProjectDocument,
    UmlAssociation,
    UmlAttribute,
    UmlClass,
    UmlMultiplicity,
)


def make_document() -> ProjectDocument:
    first = UmlClass(
        name="Cliente",
        visibility="public",
        attributes=[UmlAttribute(name="nombre", type="String", visibility="private")],
    )
    second = UmlClass(name="Pedido", visibility="public")
    return ProjectDocument(
        ownerId=uuid4(),
        metadata={"name": "Diseño", "nested": {"bool": True, "null": None, "float": 1.25}},
        createdAt=datetime(2026, 11, 6, 10, 0, 0, 123456, tzinfo=UTC),
        updatedAt=datetime(2026, 11, 6, 10, 0, 0, 123457, tzinfo=UTC),
        umlModel=CanonicalUmlModel(
            elements=[
                first,
                second,
                UmlAssociation(
                    sourceId=first.id,
                    targetId=second.id,
                    sourceMultiplicity=UmlMultiplicity(lower=1, upper=1),
                    targetMultiplicity=UmlMultiplicity(lower=0, upper="*"),
                ),
            ]
        ),
        diagramLayout=DiagramLayout(
            nodes={first.id: DiagramNodeLayout(x=12.5, y=-7, width=220, height=160)}
        ),
    )


def make_collection() -> MagicMock:
    collection = MagicMock()
    collection.write_concern = WriteConcern(w="majority")
    return collection


def next_document(document: ProjectDocument) -> ProjectDocument:
    bus = UmlCommandBus(document)
    bus.execute(AddUmlElementCommand(element=UmlClass(name="Producto", visibility="public")))
    return bus.document


def test_bson_round_trip_preserves_identity_semantics_layout_metadata_and_microseconds() -> None:
    document = make_document()
    payload = project_to_mongo(document)
    restored = project_from_mongo(BSON.encode(payload).decode())

    assert restored == document
    assert restored.created_at.microsecond == 123456
    assert "diagramLayout" not in payload["umlModel"]
    assert "umlModel" not in payload["diagramLayout"]


def test_mongo_payload_does_not_alias_the_original_document() -> None:
    document = make_document()
    payload = project_to_mongo(document)
    payload["metadata"]["nested"]["bool"] = False
    assert document.metadata["nested"]["bool"] is True


def test_corrupt_identity_is_not_silently_loaded() -> None:
    payload = project_to_mongo(make_document())
    payload["_id"] = str(uuid4())
    with pytest.raises(ValueError, match="identity"):
        project_from_mongo(payload)


def test_missing_mongo_identity_is_rejected() -> None:
    payload = make_document().model_dump(mode="json", by_alias=True)
    with pytest.raises(ValueError, match="identity"):
        project_from_mongo(payload)


def test_oversized_project_is_rejected_before_a_write() -> None:
    document = make_document()
    document.metadata["large"] = "a" * (16 * 1024 * 1024)
    collection = make_collection()
    with pytest.raises(ValueError, match="16 MiB"):
        MongoProjectStore(collection).create(document)
    collection.insert_one.assert_not_called()


def test_unacknowledged_writes_cannot_be_used_for_project_state() -> None:
    collection = make_collection()
    collection.write_concern = WriteConcern(w=0)
    with pytest.raises(ValueError, match="acknowledged"):
        MongoProjectStore(collection)


def test_create_does_not_replace_an_existing_project() -> None:
    collection = make_collection()
    collection.insert_one.side_effect = DuplicateKeyError("duplicate")
    with pytest.raises(DuplicateKeyError):
        MongoProjectStore(collection).create(make_document())
    collection.replace_one.assert_not_called()


def test_get_revalidates_the_document_and_handles_missing_projects() -> None:
    document = make_document()
    collection = make_collection()
    collection.find_one.side_effect = [project_to_mongo(document), None]
    store = MongoProjectStore(collection)
    assert store.get(document.id) == document
    assert store.get(uuid4()) is None


def test_cas_guards_revision_and_immutable_identity_without_upsert() -> None:
    document = make_document()
    updated = next_document(document)
    collection = make_collection()
    collection.update_one.return_value = UpdateResult({"n": 1, "nModified": 1}, True)
    assert MongoProjectStore(collection).update_if_revision(updated, document.revision)
    query, update = collection.update_one.call_args.args
    assert query == {
        "_id": str(document.id),
        "revision": document.revision,
        "ownerId": str(document.owner_id),
        "createdAt": document.created_at.isoformat().replace("+00:00", "Z"),
    }
    assert not {"_id", "id", "ownerId", "createdAt"} & update["$set"].keys()
    assert collection.update_one.call_args.kwargs == {"upsert": False}


def test_unmatched_cas_reports_conflict_instead_of_success() -> None:
    document = make_document()
    collection = make_collection()
    collection.update_one.return_value = UpdateResult({"n": 0, "nModified": 0}, True)
    assert not MongoProjectStore(collection).update_if_revision(next_document(document), 0)


@pytest.mark.parametrize("base_revision,new_revision", [(-1, 0), (0, 0), (0, 2), (2, 1)])
def test_invalid_revision_transition_does_not_reach_storage(
    base_revision: int, new_revision: int
) -> None:
    document = make_document().model_copy(update={"revision": new_revision})
    collection = make_collection()
    with pytest.raises(ValueError, match="revision"):
        MongoProjectStore(collection).update_if_revision(document, base_revision)
    collection.update_one.assert_not_called()


def test_storage_failure_propagates_and_does_not_mutate_the_caller_document() -> None:
    document = next_document(make_document())
    before = document.model_dump(mode="json")
    collection = make_collection()
    collection.update_one.side_effect = AutoReconnect("simulated unavailable storage")
    with pytest.raises(AutoReconnect):
        MongoProjectStore(collection).update_if_revision(document, 0)
    assert document.model_dump(mode="json") == before
