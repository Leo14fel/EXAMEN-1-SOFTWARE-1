"""MongoDB persistence adapter for the existing CASE storage functions."""

import re
from datetime import UTC, datetime
from functools import lru_cache
from typing import Any
from uuid import UUID, uuid4

from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from app.db.mongo_connection import MongoConnectionSettings, create_mongo_client
from app.db.mongo_projects import MongoProjectStore, project_from_mongo, project_to_mongo
from app.domain.uml.models import ProjectDocument


class MongoStore:
    def __init__(self, database: Database, *, collection_prefix: str = "") -> None:
        if collection_prefix and not re.fullmatch(r"cu25_[0-9a-f]{32}_", collection_prefix):
            raise ValueError("Only isolated CU-25 collection prefixes are supported")
        self.database = database
        self.users = database[f"{collection_prefix}users"]
        self.projects = database[f"{collection_prefix}projects"]
        self.presence = database[f"{collection_prefix}presence"]
        self.project_store = MongoProjectStore(self.projects)

    def ensure_indexes(self) -> None:
        self.users.create_index("email", unique=True, name="unique_normalized_email")
        self.projects.create_index([("ownerId", 1), ("updatedAt", -1)])

    def get_user_by_id(self, user_id: UUID) -> dict[str, Any] | None:
        return self.users.find_one({"_id": str(user_id)})

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        return self.users.find_one({"email": email.strip().lower()})

    def create_user(self, email: str, password_hash: str) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        data = {
            "_id": str(uuid4()),
            "email": email.strip().lower(),
            "password_hash": password_hash,
            "created_at": now,
            "updated_at": now,
        }
        self.users.insert_one(data)
        return data

    def create_project(self, document: ProjectDocument) -> ProjectDocument:
        data = project_to_mongo(document)
        data["_memberships"] = {}
        self.projects.insert_one(data)
        return document.model_copy(deep=True)

    def get_project(self, project_id: UUID) -> ProjectDocument | None:
        return self.project_store.get(project_id)

    def list_projects(self, user_id: UUID) -> list[ProjectDocument]:
        query = {
            "$or": [
                {"ownerId": str(user_id)},
                {f"_memberships.{user_id}": {"$exists": True}},
            ]
        }
        return [
            project_from_mongo(data) for data in self.projects.find(query).sort("updatedAt", -1)
        ]

    def get_membership(self, project_id: UUID, user_id: UUID) -> str | None:
        data = self.projects.find_one({"_id": str(project_id)}, {"_memberships": 1})
        return None if data is None else data.get("_memberships", {}).get(str(user_id))

    def list_memberships(self, project_id: UUID) -> dict[str, str]:
        data = self.projects.find_one({"_id": str(project_id)}, {"_memberships": 1})
        return {} if data is None else data.get("_memberships", {})

    def add_membership(self, project_id: UUID, user_id: UUID, role: str) -> None:
        path = f"_memberships.{user_id}"
        result = self.projects.update_one(
            {"_id": str(project_id), path: {"$exists": False}}, {"$set": {path: role}}
        )
        if result.matched_count != 1:
            raise DuplicateKeyError("Membership already exists or project is missing")

    def update_membership(self, project_id: UUID, user_id: UUID, role: str) -> bool:
        path = f"_memberships.{user_id}"
        result = self.projects.update_one(
            {"_id": str(project_id), path: {"$exists": True}}, {"$set": {path: role}}
        )
        return result.matched_count == 1

    def delete_membership(self, project_id: UUID, user_id: UUID) -> bool:
        path = f"_memberships.{user_id}"
        result = self.projects.update_one(
            {"_id": str(project_id), path: {"$exists": True}}, {"$unset": {path: ""}}
        )
        return result.matched_count == 1


@lru_cache(maxsize=1)
def get_mongo_store() -> MongoStore:
    config = MongoConnectionSettings()
    client = create_mongo_client(config)
    try:
        store = MongoStore(client[config.mongodb_database])
        store.ensure_indexes()
    except Exception:
        client.close()
        raise
    return store


def close_mongo_store() -> None:
    if get_mongo_store.cache_info().currsize:
        get_mongo_store().database.client.close()
        get_mongo_store.cache_clear()
