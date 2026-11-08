"""Run with `python -m app.db.mongo_probe`; only writes an isolated probe item."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier
from uuid import uuid4

from pydantic import ValidationError
from pymongo.errors import PyMongoError

from app.db.mongo_connection import MongoSettings, create_mongo_client
from app.db.mongo_projects import MongoProjectStore
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


def make_probe_document() -> ProjectDocument:
    first = UmlClass(
        name="Cliente",
        visibility="public",
        attributes=[UmlAttribute(name="nombre", type="String", visibility="private")],
    )
    second = UmlClass(name="Pedido", visibility="public")
    return ProjectDocument(
        ownerId=uuid4(),
        metadata={"purpose": "CU-25 probe", "nested": {"active": True, "optional": None}},
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
            nodes={
                first.id: DiagramNodeLayout(x=12.5, y=-7, width=220, height=160),
                second.id: DiagramNodeLayout(x=300, y=12, width=220, height=160),
            }
        ),
    )


def concurrent_update_probe(
    config: MongoSettings, collection_name: str, document: ProjectDocument
) -> ProjectDocument:
    """Exercise the server's CAS from two independent clients, not a local lock."""
    barrier = Barrier(2)

    def attempt(name: str) -> tuple[bool, ProjectDocument]:
        bus = UmlCommandBus(document)
        bus.execute(AddUmlElementCommand(element=UmlClass(name=name, visibility="public")))
        candidate = bus.document
        with create_mongo_client(config) as client:
            store = MongoProjectStore(client[config.mongodb_database][collection_name])
            barrier.wait(timeout=10)
            accepted = store.update_if_revision(candidate, document.revision)
        return accepted, candidate

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(attempt, name) for name in ("ConcurrentA", "ConcurrentB")]
        results = [future.result() for future in futures]
    winners = [candidate for accepted, candidate in results if accepted]
    if len(winners) != 1:
        raise RuntimeError("Concurrent revision writes must have exactly one winner")
    return winners[0]


def run_probe(config: MongoSettings) -> dict[str, str | int]:
    document = make_probe_document()
    collection_name = "cu25_storage_probe"
    # Only the generated UUID is removed; never drop a database/collection.
    with create_mongo_client(config) as client:
        collection = client[config.mongodb_database][collection_name]
        store = MongoProjectStore(collection)
        client.admin.command("ping")
        inserted = False
        try:
            store.create(document)
            inserted = True
            if store.get(document.id) != document:
                raise RuntimeError("Project round-trip did not preserve the document")
            bus = UmlCommandBus(document)
            bus.execute(AddUmlElementCommand(element=UmlClass(name="Probe", visibility="public")))
            updated = bus.document
            if not store.update_if_revision(updated, document.revision):
                raise RuntimeError("Valid revision was rejected")
            if store.update_if_revision(updated, document.revision):
                raise RuntimeError("Stale revision was accepted")
            updated = concurrent_update_probe(config, collection_name, updated)
            # A new client has no process-local document/history cache.
            with create_mongo_client(config) as reopened:
                recovered = MongoProjectStore(
                    reopened[config.mongodb_database][collection_name]
                ).get(document.id)
            if recovered != updated:
                raise RuntimeError("Recovery from a fresh client did not preserve the document")
            return {
                "status": "PASS",
                "timestamp": datetime.now(UTC).isoformat(),
                "projectId": str(document.id),
                "revision": updated.revision,
                "roundTrip": "PASS",
                "compareAndSwap": "PASS",
                "staleRevisionRejected": "PASS",
                "concurrentRevisionRejected": "PASS",
                "freshClientRecovery": "PASS",
            }
        finally:
            if inserted:
                collection.delete_one({"_id": str(document.id)})


def main() -> int:
    try:
        config = MongoSettings()
    except ValidationError:
        print("NOT RUN: configure MONGODB_URI and a MONGODB_DATABASE ending in _cu25_probe.")
        return 2
    try:
        print(json.dumps(run_probe(config), ensure_ascii=False))
    except (PyMongoError, ValueError, RuntimeError):
        # Driver exceptions can contain topology/connection details. No secrets
        # or server exception strings are printed to a shared terminal/report.
        print("FAIL: MongoDB probe failed; check access and test-database configuration.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
