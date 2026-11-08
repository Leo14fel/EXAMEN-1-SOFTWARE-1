from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import Field, field_validator

from app.ai.context import build_context
from app.ai.gemini import MODEL, ProviderError, interpret
from app.ai.intents import IntentResponse, ResolutionError, resolve_intent
from app.api.auth import bearer_credentials, current_user_dependency, get_current_user
from app.api.group_sessions import require_mongo
from app.api.projects import _forbidden, _project_access, _revision_conflict, database_session
from app.core.config import settings
from app.db.ai_requests import failure, find_events, finish, reserve
from app.db.dependencies import StorageSession
from app.db.group_sessions import join_session, recover_session, session_page
from app.db.users import UserRecord
from app.domain.uml.commands import UmlCommandExecutionError
from app.domain.uml.models import DomainModel

router = APIRouter(tags=["ai"])


class AiRequest(DomainModel):
    id: UUID
    base_revision: int = Field(alias="baseRevision", ge=0)
    text: str = Field(min_length=1, max_length=2000)

    @field_validator("text")
    @classmethod
    def meaningful_text(cls, value):
        if not value.strip():
            raise ValueError("Request must not be blank")
        return value.strip()


def configured() -> bool:
    return bool(settings.gemini_api_key and settings.gemini_api_key.get_secret_value().strip())


def invoke_provider(context: dict) -> IntentResponse:
    return interpret(context, settings.gemini_api_key.get_secret_value())


def describe_proposal(response: IntentResponse) -> str:
    item = response.intent.model_dump(by_alias=True)
    operation = item["operation"]
    if operation == "createClass":
        description = f"crear la clase «{item['name']}»"
    elif operation == "renameClass":
        description = f"renombrar «{item['target']}» como «{item['name']}»"
    elif operation == "deleteClass":
        description = f"eliminar la clase «{item['target']}»"
    elif operation == "addAttribute":
        description = f"agregar «{item['name']}: {item['type']}» a «{item['target']}»"
    elif operation == "addOperation":
        description = f"agregar el método «{item['name']}» sin parámetros a «{item['target']}»"
    else:
        description = (
            f"asociar «{item['source']}» ({item['sourceLower']}..{item['sourceUpper']}) "
            f"con «{item['target']}» ({item['targetLower']}..{item['targetUpper']})"
        )
    return f"Propuesta: {description}. No se aplicó ningún cambio al diagrama."


@router.get("/projects/{project_id}/ai/status")
def ai_status(
    project_id: UUID,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> dict:
    _project_access(session, project_id, user)
    require_mongo(session)
    return {"configured": configured(), "modelCandidate": MODEL, "mode": "proposalOnly"}


@router.get("/projects/{project_id}/ai/requests/{request_id}")
def get_ai_request(
    project_id: UUID,
    request_id: UUID,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> dict:
    _project_access(session, project_id, user)
    store = require_mongo(session)
    recover_session(store, project_id)
    return find_events(store, project_id, request_id)


@router.post("/projects/{project_id}/ai/requests")
def evaluate_ai_request(
    project_id: UUID,
    request: AiRequest,
    response: Response,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
    credentials: HTTPAuthorizationCredentials | None = bearer_credentials,
) -> dict:
    access = _project_access(session, project_id, user)
    if not access.can_edit:
        raise _forbidden()
    store = require_mongo(session)
    join_session(store, project_id, user)
    recover_session(store, project_id)
    try:
        previous = find_events(store, project_id, request.id)
    except HTTPException as error:
        if error.status_code != 404:
            raise
    else:
        saved = previous["request"]
        if (saved["actorId"], saved["baseRevision"], saved["text"]) != (
            str(user.id),
            request.base_revision,
            request.text,
        ):
            raise HTTPException(409, detail={"code": "AI_REQUEST_ID_CONFLICT"})
        if previous["pending"]:
            response.status_code = 202
        return previous
    if request.base_revision != access.document.revision:
        raise _revision_conflict()
    if not configured():
        raise HTTPException(503, detail={"code": "AI_NOT_CONFIGURED"})
    # Build the authorized snapshot before reserving. Never send other project history.
    history = session_page(store, project_id)["events"]
    try:
        context = build_context(access.document, user.id, request.text, history)
    except ProviderError as error:
        raise HTTPException(413, detail={"code": str(error)}) from None
    if not reserve(store, project_id, user, request.id, request.base_revision, request.text):
        result = find_events(store, project_id, request.id)
        if result["pending"]:
            response.status_code = 202
        return result
    saved = find_events(store, project_id, request.id)["request"]
    result = failure(saved, "AI_PROVIDER_ERROR")
    try:
        interpretation = invoke_provider(context)
        intent = interpretation.intent
        status = intent.operation if intent.operation in {"clarify", "unsupported"} else "proposed"
        if status == "proposed":
            resolve_intent(access.document, interpretation)
        result = {
            **result,
            "status": status,
            "code": "AI_PROPOSAL_ONLY",
            "text": intent.reason
            if status in {"clarify", "unsupported"}
            else describe_proposal(interpretation),
            "intent": interpretation.model_dump(mode="json", by_alias=True),
        }
    except ProviderError as error:
        result = failure(saved, str(error))
    except (ResolutionError, UmlCommandExecutionError, ValueError):
        result = failure(saved, "AI_PROPOSAL_INVALID")
    # Recheck token, account and access after external work, before returning anything.
    try:
        current = get_current_user(credentials, session)
        if not _project_access(session, project_id, current).can_edit:
            raise _forbidden()
    except HTTPException:
        finish(store, project_id, request.id, failure(saved, "AI_ACCESS_CHANGED"))
        raise
    result["createdAt"] = datetime.now(UTC).isoformat()
    finish(store, project_id, request.id, result)
    return find_events(store, project_id, request.id)
