from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import Field, field_validator

from app.api.auth import current_user_dependency
from app.api.projects import _forbidden, _project_access, database_session
from app.db.dependencies import StorageSession
from app.db.group_sessions import join_session, queue_message, recover_session, session_page
from app.db.mongo_store import MongoStore
from app.db.users import UserRecord
from app.domain.uml.models import DomainModel

router = APIRouter(tags=["sessions"])


class MessageRequest(DomainModel):
    id: UUID
    text: str = Field(min_length=1, max_length=4000)

    @field_validator("text")
    @classmethod
    def meaningful_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message must not be blank")
        return value


def require_mongo(session: StorageSession) -> MongoStore:
    if not isinstance(session, MongoStore):
        raise HTTPException(503, detail={"code": "SESSION_REQUIRES_NOSQL"})
    return session


@router.post("/projects/{project_id}/session")
def join_project_session(
    project_id: UUID,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> dict:
    _project_access(session, project_id, user)
    store = require_mongo(session)
    join_session(store, project_id, user)
    recover_session(store, project_id)
    return session_page(store, project_id)


@router.get("/projects/{project_id}/session")
def get_project_session(
    project_id: UUID,
    before: int | None = Query(default=None, ge=1),
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> dict:
    _project_access(session, project_id, user)
    store = require_mongo(session)
    recover_session(store, project_id)
    return session_page(store, project_id, before=before)


@router.post("/projects/{project_id}/session/messages")
def send_group_message(
    project_id: UUID,
    request: MessageRequest,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> dict:
    if not _project_access(session, project_id, user).can_edit:
        raise _forbidden()
    store = require_mongo(session)
    join_session(store, project_id, user)
    return queue_message(
        store,
        project_id,
        user.id,
        {
            "id": str(request.id),
            "kind": "message",
            "actorId": str(user.id),
            "actorName": user.email.partition("@")[0][:40],
            "createdAt": datetime.now(UTC).isoformat(),
            "text": request.text,
        },
    )
