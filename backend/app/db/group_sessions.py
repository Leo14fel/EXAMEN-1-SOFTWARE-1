"""One bounded, ordered session ledger per project; never another UML model."""

from datetime import UTC, datetime
from uuid import UUID

from bson import BSON
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from app.db.mongo_projects import MAX_BSON_BYTES, ProjectTooLargeError
from app.db.mongo_store import MongoStore
from app.db.users import UserRecord


def join_session(store: MongoStore, project_id: UUID, user: UserRecord) -> None:
    now = datetime.now(UTC).isoformat()
    try:
        store.sessions.update_one(
            {"_id": str(project_id)},
            {
                "$setOnInsert": {
                    "projectId": str(project_id),
                    "createdAt": now,
                    "version": 0,
                    "events": [],
                    "participants": {},
                }
            },
            upsert=True,
        )
    except DuplicateKeyError:
        pass
    store.sessions.update_one(
        {"_id": str(project_id), f"participants.{user.id}": {"$exists": False}},
        {
            "$set": {
                f"participants.{user.id}": {
                    "userId": str(user.id),
                    "name": user.email.partition("@")[0][:40],
                    "joinedAt": now,
                }
            }
        },
    )


def append_event(store: MongoStore, project_id: UUID, event: dict) -> dict:
    for _ in range(8):
        session = store.sessions.find_one({"_id": str(project_id)})
        if session is None:
            raise ValueError("Session must be joined before appending")
        for existing in session["events"]:
            if existing["id"] == event["id"]:
                # Retries keep the first accepted server time/name/sequence.
                keys = ("actorId", "kind", "text", "action", "projectRevision", "elementId")
                if any(existing.get(key) != event.get(key) for key in keys):
                    raise HTTPException(409, detail={"code": "SESSION_EVENT_ID_CONFLICT"})
                return existing
        entry = {**event, "sequence": session["version"] + 1}
        candidate = {**session, "version": entry["sequence"], "events": [*session["events"], entry]}
        if len(BSON.encode(candidate)) > MAX_BSON_BYTES:
            raise ProjectTooLargeError("Session exceeds storage limit")
        result = store.sessions.update_one(
            {"_id": str(project_id), "version": session["version"]},
            {"$push": {"events": entry}, "$inc": {"version": 1}},
        )
        if result.matched_count == 1:
            return entry
    raise HTTPException(409, detail={"code": "SESSION_BUSY", "message": "Retry the same event"})


def session_page(
    store: MongoStore,
    project_id: UUID,
    *,
    after: int | None = None,
    before: int | None = None,
    limit: int = 50,
) -> dict:
    data = store.sessions.find_one({"_id": str(project_id)}, {"events": 0})
    if data is None:
        return {
            "projectId": str(project_id),
            "events": [],
            "participants": [],
            "cursor": 0,
            "version": 0,
            "hasEarlier": False,
            "hasMore": False,
        }
    version = data["version"]
    if after is not None:
        start = min(after, version)
        end = min(start + limit, version)
    else:
        end = min(version, before - 1) if before is not None else version
        start = max(0, end - limit)
    page = (
        store.sessions.find_one(
            {"_id": str(project_id)}, {"events": {"$slice": [start, end - start]}}
        )
        if end > start
        else {"events": []}
    )
    return {
        "projectId": str(project_id),
        "events": page["events"],
        "participants": list(data["participants"].values()),
        "cursor": end,
        "version": version,
        "hasEarlier": start > 0,
        "hasMore": end < version,
    }


def flush_pending(
    store: MongoStore, project_id: UUID, field: str = "_pendingMessage"
) -> dict | None:
    raw = store.projects.find_one({"_id": str(project_id)}, {field: 1})
    event = raw.get(field) if raw else None
    if event is None:
        return None
    saved = append_event(store, project_id, event)
    store.projects.update_one(
        {"_id": str(project_id), f"{field}.id": event["id"]}, {"$unset": {field: ""}}
    )
    return saved


def recover_session(store: MongoStore, project_id: UUID) -> None:
    flush_pending(store, project_id, "_pendingActivity")
    flush_pending(store, project_id)


def queue_message(store: MongoStore, project_id: UUID, user_id: UUID, event: dict) -> dict:
    for _ in range(8):
        flush_pending(store, project_id)
        session = store.sessions.find_one({"_id": str(project_id)})
        if any(item["id"] == event["id"] for item in session["events"]):
            return append_event(store, project_id, event)
        raw = store.projects.find_one({"_id": str(project_id)})
        if raw is None:
            raise HTTPException(404, detail={"code": "PROJECT_NOT_FOUND"})
        if len(BSON.encode({**raw, "_pendingMessage": event})) > MAX_BSON_BYTES:
            raise ProjectTooLargeError("Project message reservation exceeds storage limit")
        result = store.projects.update_one(
            {
                "_id": str(project_id),
                "_pendingMessage": {"$exists": False},
                "$or": [{"ownerId": str(user_id)}, {f"_memberships.{user_id}": "EDITOR"}],
            },
            {"$set": {"_pendingMessage": event}},
        )
        if result.matched_count:
            return flush_pending(store, project_id) or append_event(store, project_id, event)
        membership = store.get_membership(project_id, user_id)
        if raw["ownerId"] != str(user_id) and membership != "EDITOR":
            raise HTTPException(403, detail={"code": "PROJECT_ACCESS_FORBIDDEN"})
    raise HTTPException(409, detail={"code": "SESSION_BUSY"})
