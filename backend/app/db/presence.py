"""Short-lived session leases, kept outside the canonical project document."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.db.memberships import ProjectRole
from app.db.mongo_store import MongoStore
from app.db.users import UserRecord
from app.domain.uml.models import ProjectDocument

LEASE_SECONDS = 15


class CursorPosition(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    x: float = Field(ge=-1_000_000, le=1_000_000)
    y: float = Field(ge=-1_000_000, le=1_000_000)


class PresenceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str = "presence"
    cursor: CursorPosition | None = None
    selectedElementId: UUID | None = None
    editingElementId: UUID | None = None


def heartbeat(
    store: MongoStore,
    session_id: UUID,
    document: ProjectDocument,
    user: UserRecord,
    role: ProjectRole,
    update: PresenceUpdate | None = None,
) -> None:
    now = datetime.now(UTC)
    collection = store.presence
    values = {
        "projectId": str(document.id),
        "userId": str(user.id),
        "name": user.email.partition("@")[0][:40],
        "role": role.value,
        "expiresAt": now + timedelta(seconds=LEASE_SECONDS),
    }
    initial = {
        "cursor": None,
        "selectedElementId": None,
        "editingElementId": None,
        "lastActivity": now.isoformat(),
    }
    if update is not None:
        ids = {element.id for element in document.uml_model.elements}
        values.update(
            cursor=update.cursor.model_dump() if update.cursor else None,
            selectedElementId=str(update.selectedElementId)
            if update.selectedElementId in ids
            else None,
            editingElementId=str(update.editingElementId)
            if role == ProjectRole.EDITOR and update.editingElementId in ids
            else None,
            lastActivity=now.isoformat(),
        )
        initial = {}
    if role == ProjectRole.VIEWER:
        values["editingElementId"] = None
        initial.pop("editingElementId", None)
    collection.update_one(
        {"_id": str(session_id)}, {"$set": values, "$setOnInsert": initial}, upsert=True
    )


def participants(store: MongoStore, document: ProjectDocument) -> list[dict]:
    rows = store.presence.find(
        {"projectId": str(document.id), "expiresAt": {"$gt": datetime.now(UTC)}},
        {"expiresAt": 0, "projectId": 0},
    ).sort("_id", 1)
    ids = {str(element.id) for element in document.uml_model.elements}
    result = []
    # One fresh membership map also prevents exposing a revoked peer during cleanup.
    memberships = store.list_memberships(document.id)
    for row in rows:
        role = (
            ProjectRole.EDITOR.value
            if row["userId"] == str(document.owner_id)
            else memberships.get(row["userId"])
        )
        if role is None:
            continue
        row["sessionId"] = row.pop("_id")
        row["role"] = role
        if row.get("selectedElementId") not in ids:
            row["selectedElementId"] = None
        if role != ProjectRole.EDITOR.value or row.get("editingElementId") not in ids:
            row["editingElementId"] = None
        result.append(row)
    return result
