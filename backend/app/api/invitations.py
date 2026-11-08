import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from bson import BSON
from fastapi import APIRouter, HTTPException
from pydantic import Field, field_validator

from app.api.auth import CredentialsRequest, current_user_dependency
from app.api.projects import _owner_access, database_session
from app.db.dependencies import StorageSession
from app.db.memberships import ProjectRole
from app.db.mongo_projects import MAX_BSON_BYTES, ProjectTooLargeError
from app.db.mongo_store import MongoStore
from app.db.users import UserRecord, get_user_by_email
from app.domain.uml.models import DomainModel

router = APIRouter(tags=["invitations"])


class CreateInvitationRequest(DomainModel):
    email: str = Field(min_length=3, max_length=320)
    role: ProjectRole
    expires_hours: int = Field(default=24, alias="expiresHours", ge=1, le=168)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return CredentialsRequest.normalize_email(value)


class AcceptInvitationRequest(DomainModel):
    token: str = Field(min_length=50, max_length=256)


def _mongo(session: StorageSession) -> MongoStore:
    if not isinstance(session, MongoStore):
        raise HTTPException(503, detail={"code": "INVITATIONS_REQUIRE_NOSQL"})
    return session


def _public(identity: str, row: dict) -> dict:
    return {
        "id": identity,
        "email": row["email"],
        "role": row["role"],
        "expiresAt": row["expiresAt"],
        "createdAt": row["createdAt"],
    }


@router.post("/projects/{project_id}/invitations", status_code=201)
def create_invitation(
    project_id: UUID,
    request: CreateInvitationRequest,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> dict:
    _owner_access(session, project_id, user)
    store = _mongo(session)
    email = request.email
    if email == user.email:
        raise HTTPException(409, detail={"code": "INVITATION_OWNER"})
    target = get_user_by_email(store, email)
    if target and store.get_membership(project_id, target.id) is not None:
        raise HTTPException(409, detail={"code": "PROJECT_MEMBERSHIP_EXISTS"})
    identity = str(uuid4())
    secret = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    row = {
        "email": email,
        "role": request.role.value,
        "secretHash": hashlib.sha256(secret.encode()).hexdigest(),
        "createdAt": now.isoformat(),
        "expiresAt": (now + timedelta(hours=request.expires_hours)).isoformat(),
    }
    raw = store.projects.find_one({"_id": str(project_id)})
    invitations = {**raw.get("_invitations", {}), identity: row}
    if len(BSON.encode({**raw, "_invitations": invitations})) > MAX_BSON_BYTES:
        raise ProjectTooLargeError("Invitation exceeds storage limit")
    result = store.projects.update_one(
        {"_id": str(project_id), "ownerId": str(user.id)},
        {"$set": {f"_invitations.{identity}": row}},
    )
    if not result.matched_count:
        raise HTTPException(404, detail={"code": "PROJECT_NOT_FOUND"})
    return {**_public(identity, row), "token": f"{project_id}.{identity}.{secret}"}


@router.get("/projects/{project_id}/invitations")
def list_invitations(
    project_id: UUID,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> list[dict]:
    _owner_access(session, project_id, user)
    raw = _mongo(session).projects.find_one({"_id": str(project_id)}, {"_invitations": 1})
    now = datetime.now(UTC).isoformat()
    return [
        _public(identity, row)
        for identity, row in raw.get("_invitations", {}).items()
        if row["expiresAt"] > now
    ]


@router.delete("/projects/{project_id}/invitations/{invitation_id}", status_code=204)
def cancel_invitation(
    project_id: UUID,
    invitation_id: UUID,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> None:
    _owner_access(session, project_id, user)
    path = f"_invitations.{invitation_id}"
    result = _mongo(session).projects.update_one(
        {"_id": str(project_id), "ownerId": str(user.id), path: {"$exists": True}},
        {"$unset": {path: ""}},
    )
    if not result.matched_count:
        raise HTTPException(404, detail={"code": "INVITATION_NOT_FOUND"})


@router.post("/project-invitations/accept")
def accept_invitation(
    request: AcceptInvitationRequest,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> dict:
    store = _mongo(session)
    try:
        project, identity, secret = request.token.split(".")
        project_id, invitation_id = UUID(project), UUID(identity)
    except ValueError as error:
        raise HTTPException(404, detail={"code": "INVITATION_NOT_FOUND"}) from error
    path = f"_invitations.{invitation_id}"
    raw = store.projects.find_one({"_id": str(project_id)}, {"_invitations": 1, "ownerId": 1})
    row = raw.get("_invitations", {}).get(str(invitation_id)) if raw else None
    digest = hashlib.sha256(secret.encode()).hexdigest()
    if (
        row is None
        or not secrets.compare_digest(row["secretHash"], digest)
        or row["email"] != user.email
    ):
        raise HTTPException(404, detail={"code": "INVITATION_NOT_FOUND"})
    now = datetime.now(UTC).isoformat()
    if row["expiresAt"] <= now:
        raise HTTPException(410, detail={"code": "INVITATION_EXPIRED"})
    if raw["ownerId"] == str(user.id):
        raise HTTPException(409, detail={"code": "INVITATION_OWNER"})
    result = store.projects.update_one(
        {
            "_id": str(project_id),
            f"{path}.secretHash": digest,
            f"{path}.email": user.email,
            f"{path}.expiresAt": {"$gt": now},
            f"{path}.role": row["role"],
            f"_memberships.{user.id}": {"$exists": False},
        },
        {"$set": {f"_memberships.{user.id}": row["role"]}, "$unset": {path: ""}},
    )
    if not result.matched_count:
        raise HTTPException(409, detail={"code": "INVITATION_UNAVAILABLE"})
    return {"projectId": str(project_id), "effectiveRole": row["role"]}
