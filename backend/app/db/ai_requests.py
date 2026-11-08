"""One leased AI request per project, recoverable without repeating inference."""

import time
from datetime import UTC, datetime
from uuid import UUID

from bson import BSON
from fastapi import HTTPException

from app.db.group_sessions import append_event
from app.db.mongo_projects import MAX_BSON_BYTES, ProjectTooLargeError
from app.db.mongo_store import MongoStore
from app.db.users import UserRecord


def event_id(request_id: UUID, phase: str) -> str:
    return f"ai:{phase}:{request_id}"


def find_events(store: MongoStore, project_id: UUID, request_id: UUID) -> dict:
    data = store.sessions.find_one({"_id": str(project_id)}, {"events": 1}) or {}
    events = {event["id"]: event for event in data.get("events", [])}
    request = events.get(event_id(request_id, "request"))
    if request is None:
        raise HTTPException(404, detail={"code": "AI_REQUEST_NOT_FOUND"})
    result = events.get(event_id(request_id, "result"))
    return {"request": request, "result": result, "pending": result is None}


def failure(request: dict, code: str, *, status: str = "failed") -> dict:
    return {
        "id": event_id(UUID(request["requestId"]), "result"),
        "kind": "aiResult",
        "requestId": request["requestId"],
        "requestedBy": request["actorId"],
        "actorId": "ai:gemini",
        "actorName": "IA · Gemini",
        "createdAt": datetime.now(UTC).isoformat(),
        "baseRevision": request["baseRevision"],
        "status": status,
        "code": code,
        "canApply": False,
        "text": "La evaluación no produjo una propuesta vigente. No se modificó el diagrama.",
    }


def recover_ai(store: MongoStore, project_id: UUID) -> None:
    raw = store.projects.find_one({"_id": str(project_id)}, {"_aiRequest": 1}) or {}
    record = raw.get("_aiRequest")
    if record is None:
        return
    request = record["request"]
    append_event(store, project_id, request)
    if "result" not in record and record["deadline"] <= time.time():
        store.projects.update_one(
            {
                "_id": str(project_id),
                "_aiRequest.request.id": request["id"],
                "_aiRequest.result": {"$exists": False},
            },
            {"$set": {"_aiRequest.result": failure(request, "AI_REQUEST_INTERRUPTED")}},
        )
        raw = store.projects.find_one({"_id": str(project_id)}, {"_aiRequest": 1}) or {}
        record = raw.get("_aiRequest")
        if record is None or record["request"]["id"] != request["id"]:
            return
    if "result" in record:
        append_event(store, project_id, record["result"])
        store.projects.update_one(
            {
                "_id": str(project_id),
                "_aiRequest.request.id": request["id"],
                "_aiRequest.result.id": record["result"]["id"],
            },
            {"$unset": {"_aiRequest": ""}},
        )


def reserve(
    store: MongoStore, project_id: UUID, user: UserRecord, identity: UUID, revision: int, text: str
) -> bool:
    recover_ai(store, project_id)
    try:
        previous = find_events(store, project_id, identity)
    except HTTPException as error:
        if error.status_code != 404:
            raise
    else:
        event = previous["request"]
        if (event["actorId"], event["baseRevision"], event["text"]) != (
            str(user.id),
            revision,
            text,
        ):
            raise HTTPException(409, detail={"code": "AI_REQUEST_ID_CONFLICT"})
        return False
    request = {
        "id": event_id(identity, "request"),
        "requestId": str(identity),
        "kind": "aiRequest",
        "actorId": str(user.id),
        "actorName": user.email.partition("@")[0][:40],
        "createdAt": datetime.now(UTC).isoformat(),
        "baseRevision": revision,
        "text": text,
    }
    record = {"request": request, "deadline": time.time() + 30}
    raw = store.projects.find_one({"_id": str(project_id)}) or {}
    seen = {**raw.get("_aiSeen", {}), str(identity): True}
    if len(BSON.encode({**raw, "_aiRequest": record, "_aiSeen": seen})) > MAX_BSON_BYTES:
        raise ProjectTooLargeError("AI reservation exceeds project limit")
    result = store.projects.update_one(
        {
            "_id": str(project_id),
            "revision": revision,
            "_aiRequest": {"$exists": False},
            f"_aiSeen.{identity}": {"$exists": False},
            "$or": [{"ownerId": str(user.id)}, {f"_memberships.{user.id}": "EDITOR"}],
        },
        {"$set": {"_aiRequest": record, f"_aiSeen.{identity}": True}},
    )
    if not result.matched_count:
        # Another process may have reserved the same ID. Recover and deduplicate it.
        recover_ai(store, project_id)
        try:
            previous = find_events(store, project_id, identity)
        except HTTPException as error:
            if error.status_code != 404:
                raise
        else:
            archived = previous["request"]
            if (archived["actorId"], archived["baseRevision"], archived["text"]) != (
                str(user.id),
                revision,
                text,
            ):
                raise HTTPException(409, detail={"code": "AI_REQUEST_ID_CONFLICT"})
            return False
        raw = store.projects.find_one({"_id": str(project_id)}) or {}
        active = raw.get("_aiRequest", {}).get("request", {})
        if active.get("requestId") == str(identity):
            if (active["actorId"], active["baseRevision"], active["text"]) != (
                str(user.id),
                revision,
                text,
            ):
                raise HTTPException(409, detail={"code": "AI_REQUEST_ID_CONFLICT"})
            return False
        raise HTTPException(409, detail={"code": "AI_BUSY_OR_PROJECT_CHANGED"})
    recover_ai(store, project_id)
    return True


def finish(store: MongoStore, project_id: UUID, identity: UUID, event: dict) -> None:
    query = {
        "_id": str(project_id),
        "_aiRequest.request.requestId": str(identity),
        "_aiRequest.result": {"$exists": False},
        "_aiRequest.deadline": {"$gt": time.time()},
    }
    raw = store.projects.find_one({"_id": str(project_id)}) or {}
    record = raw.get("_aiRequest")
    if not record or record["request"]["requestId"] != str(identity):
        return
    if len(BSON.encode({**raw, "_aiRequest": {**record, "result": event}})) > MAX_BSON_BYTES:
        raise ProjectTooLargeError("AI result exceeds project limit")
    if event["status"] != "failed":
        request = record["request"]
        query["revision"] = request["baseRevision"]
        query["$or"] = [
            {"ownerId": request["actorId"]},
            {f"_memberships.{request['actorId']}": "EDITOR"},
        ]
    changed = store.projects.update_one(query, {"$set": {"_aiRequest.result": event}})
    if not changed.matched_count:
        store.projects.update_one(
            {
                "_id": str(project_id),
                "_aiRequest.request.requestId": str(identity),
                "_aiRequest.result": {"$exists": False},
            },
            {
                "$set": {
                    "_aiRequest.result": failure(
                        record["request"], "AI_CONTEXT_CHANGED", status="stale"
                    )
                }
            },
        )
    recover_ai(store, project_id)
