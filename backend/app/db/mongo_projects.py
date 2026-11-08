"""Canonical project storage for the CASE MongoDB adapter and isolated proofs."""

from typing import Any
from uuid import UUID

from bson import BSON
from pymongo.collection import Collection

from app.domain.uml.models import ProjectDocument

MAX_BSON_BYTES = 16 * 1024 * 1024


class ProjectTooLargeError(ValueError):
    pass


def project_to_mongo(document: ProjectDocument) -> dict[str, Any]:
    # JSON mode keeps UUIDs and timestamp precision independent of BSON datetime's
    # millisecond precision. Semantic UML and layout remain distinct fields.
    data = document.model_dump(mode="json", by_alias=True)
    data["_id"] = str(document.id)
    if len(BSON.encode(data)) > MAX_BSON_BYTES:
        raise ProjectTooLargeError("Project exceeds MongoDB's 16 MiB document limit")
    return data


def project_from_mongo(data: dict[str, Any]) -> ProjectDocument:
    payload = {
        key: value
        for key, value in data.items()
        if key not in {'_id', '_pendingActivity', '_pendingMessage', '_memberships'}
    }
    document = ProjectDocument.model_validate(payload)
    if data.get("_id") != str(document.id):
        raise ValueError("Stored project identity does not match its MongoDB key")
    return document


class MongoProjectStore:
    """One atomic document per project; errors propagate to the caller.

    API callers supply actor_id so the same write also checks current access;
    maintenance/proof callers operate below the HTTP authorization boundary.
    """

    def __init__(self, collection: Collection[dict[str, Any]]) -> None:
        if not collection.write_concern.acknowledged:
            raise ValueError("Project persistence requires acknowledged writes")
        self.collection = collection

    def create(self, document: ProjectDocument) -> None:
        self.collection.insert_one(project_to_mongo(document))

    def get(self, project_id: UUID) -> ProjectDocument | None:
        data = self.collection.find_one({"_id": str(project_id)})
        return None if data is None else project_from_mongo(data)

    def update_if_revision(
        self,
        document: ProjectDocument,
        base_revision: int,
        *,
        actor_id: UUID | None = None,
        activity: dict | None = None,
    ) -> bool:
        if base_revision < 0 or document.revision != base_revision + 1:
            raise ValueError("A persisted mutation must increment revision exactly once")
        data = project_to_mongo(document)
        query = {
            "_id": data["_id"],
            "revision": base_revision,
            "ownerId": data["ownerId"],
            "createdAt": data["createdAt"],
        }
        if actor_id is not None:
            query["$or"] = [
                {"ownerId": str(actor_id)},
                {f"_memberships.{actor_id}": "EDITOR"},
            ]
        updates = {
            key: data[key]
            for key in ("metadata", "revision", "updatedAt", "umlModel", "diagramLayout")
        }
        if activity is not None:
            query["_pendingActivity"] = {"$exists": False}
            updates["_pendingActivity"] = activity
            raw = self.collection.find_one({"_id": str(document.id)}) or {}
            if len(BSON.encode({**raw, **updates})) > MAX_BSON_BYTES:
                raise ProjectTooLargeError("Project activity reservation exceeds storage limit")
        result = self.collection.update_one(query, {"$set": updates}, upsert=False)
        return result.matched_count == 1
