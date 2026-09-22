from datetime import datetime
from threading import Lock
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import Field, JsonValue
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.auth import current_user_dependency
from app.core.security import decode_access_token
from app.db.dependencies import get_db_session
from app.db.memberships import (
    ProjectMembershipRecord,
    ProjectRole,
    get_membership,
    list_memberships,
)
from app.db.projects import (
    ProjectRecord,
    create_project,
    get_project,
    list_projects,
    update_project_if_revision,
)
from app.db.users import UserRecord, get_user_by_email, get_user_by_id
from app.domain.uml.command_bus import UmlCommandBus
from app.domain.uml.commands import UmlCommand, UmlCommandExecutionError
from app.domain.uml.models import DomainModel, ProjectDocument
from app.realtime.projects import project_connections

router = APIRouter(prefix="/projects", tags=["projects"])
database_session = Depends(get_db_session)
_project_buses: dict[UUID, UmlCommandBus] = {}
_project_locks: dict[UUID, Lock] = {}
_project_locks_lock = Lock()


class CreateProjectRequest(DomainModel):
    metadata: dict[str, JsonValue] = Field(default_factory=dict)


class ProjectSummary(DomainModel):
    id: UUID
    owner_id: UUID = Field(alias="ownerId")
    metadata: dict[str, JsonValue]
    revision: int
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    effective_role: ProjectRole = Field(alias="effectiveRole")


class CollaboratorRequest(DomainModel):
    email: str = Field(min_length=3, max_length=320)
    role: ProjectRole


class CollaboratorRoleRequest(DomainModel):
    role: ProjectRole


class CollaboratorResponse(DomainModel):
    user_id: UUID = Field(alias="userId")
    email: str
    role: ProjectRole


class ProjectAccess(DomainModel):
    document: ProjectDocument
    effective_role: ProjectRole = Field(alias="effectiveRole")

    @property
    def can_edit(self) -> bool:
        return self.effective_role == ProjectRole.EDITOR


class ExecuteProjectCommandRequest(DomainModel):
    base_revision: int = Field(alias="baseRevision", ge=0)
    command: UmlCommand


class ProjectRevisionRequest(DomainModel):
    base_revision: int = Field(alias="baseRevision", ge=0)


class ProjectEditorState(DomainModel):
    document: ProjectDocument
    can_undo: bool = Field(alias="canUndo")
    can_redo: bool = Field(alias="canRedo")


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "PROJECT_NOT_FOUND", "message": "Project was not found"},
    )


def _revision_conflict() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            "code": "PROJECT_REVISION_CONFLICT",
            "message": "Project revision does not match the persisted document",
        },
    )


def _forbidden() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "PROJECT_ACCESS_FORBIDDEN", "message": "Project access is not permitted"},
    )


def _command_error(error: UmlCommandExecutionError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={"code": error.code.value, "message": str(error)},
    )


def _project_lock(project_id: UUID) -> Lock:
    with _project_locks_lock:
        return _project_locks.setdefault(project_id, Lock())


def _invalidate_project_bus(project_id: UUID) -> None:
    _project_buses.pop(project_id, None)


def _clear_project_bus_cache() -> None:
    """Test helper that simulates losing process-local editor history on restart."""
    _project_buses.clear()


def _project_bus(project_id: UUID, document: ProjectDocument) -> UmlCommandBus:
    bus = _project_buses.get(project_id)
    if bus is None or bus.document.revision != document.revision:
        bus = UmlCommandBus(document)
        _project_buses[project_id] = bus
    return bus


def _project_access(session: Session, project_id: UUID, user: UserRecord) -> ProjectAccess:
    """Resolve every project permission from ownership or a persisted membership."""
    document = get_project(session, project_id)
    if document is None:
        raise _not_found()
    if document.owner_id == user.id:
        return ProjectAccess(document=document, effectiveRole=ProjectRole.EDITOR)
    membership = get_membership(session, project_id, user.id)
    if membership is None:
        raise _not_found()
    return ProjectAccess(document=document, effectiveRole=membership.role)


def _owner_access(session: Session, project_id: UUID, user: UserRecord) -> ProjectAccess:
    access = _project_access(session, project_id, user)
    if access.document.owner_id != user.id:
        raise _forbidden()
    return access


def _state(bus: UmlCommandBus) -> ProjectEditorState:
    return ProjectEditorState(
        document=bus.document,
        canUndo=bus.can_undo,
        canRedo=bus.can_redo,
    )


def _mutate_project(
    project_id: UUID,
    base_revision: int,
    session: Session,
    action: str,
    user: UserRecord,
    command: UmlCommand | None = None,
) -> ProjectEditorState:
    with _project_lock(project_id):
        access = _project_access(session, project_id, user)
        document = access.document
        if not access.can_edit:
            raise _forbidden()
        if document.revision != base_revision:
            _invalidate_project_bus(project_id)
            raise _revision_conflict()

        bus = _project_bus(project_id, document)
        try:
            if action == "execute":
                if command is None:
                    raise AssertionError("command is required")
                bus.execute(command)
            elif action == "undo":
                bus.undo()
            elif action == "redo":
                bus.redo()
            else:
                raise AssertionError("unsupported project action")
        except UmlCommandExecutionError as error:
            raise _command_error(error) from error

        try:
            if not update_project_if_revision(session, bus.document, base_revision):
                session.rollback()
                _invalidate_project_bus(project_id)
                raise _revision_conflict()
            session.commit()
        except HTTPException:
            raise
        except SQLAlchemyError as error:
            session.rollback()
            _invalidate_project_bus(project_id)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "PROJECT_PERSISTENCE_UNAVAILABLE",
                    "message": "Project storage is unavailable",
                },
            ) from error

        return _state(bus)


async def _broadcast_project_updated(project_id: UUID, state: ProjectEditorState) -> None:
    await project_connections.broadcast_project_updated(project_id, state.document)


def _summary(record: ProjectRecord, user_id: UUID, session: Session) -> ProjectSummary:
    role = (
        ProjectRole.EDITOR
        if record.owner_id == user_id
        else get_membership(session, record.id, user_id).role
    )
    return ProjectSummary(
        id=record.id,
        ownerId=record.owner_id,
        metadata=record.project_metadata,
        revision=record.revision,
        createdAt=record.created_at,
        updatedAt=record.updated_at,
        effectiveRole=role,
    )


@router.post("", response_model=ProjectDocument, status_code=status.HTTP_201_CREATED)
def create_persisted_project(
    request: CreateProjectRequest,
    user: UserRecord = current_user_dependency,
    session: Session = database_session,
) -> ProjectDocument:
    document = ProjectDocument(ownerId=user.id, metadata=request.metadata)
    try:
        return create_project(session, document)
    except SQLAlchemyError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "PROJECT_PERSISTENCE_UNAVAILABLE",
                "message": "Project storage is unavailable",
            },
        ) from error


@router.get("", response_model=list[ProjectSummary])
def list_persisted_projects(
    user: UserRecord = current_user_dependency,
    session: Session = database_session,
) -> list[ProjectSummary]:
    return [_summary(record, user.id, session) for record in list_projects(session, user.id)]


@router.get("/{project_id}", response_model=ProjectDocument)
def get_persisted_project(
    project_id: UUID,
    user: UserRecord = current_user_dependency,
    session: Session = database_session,
) -> ProjectDocument:
    return _project_access(session, project_id, user).document


def _collaborator_response(
    membership: ProjectMembershipRecord, session: Session
) -> CollaboratorResponse:
    user = get_user_by_id(session, membership.user_id)
    if user is None:
        raise _not_found()
    return CollaboratorResponse(userId=user.id, email=user.email, role=membership.role)


@router.get("/{project_id}/collaborators", response_model=list[CollaboratorResponse])
def get_collaborators(
    project_id: UUID,
    user: UserRecord = current_user_dependency,
    session: Session = database_session,
) -> list[CollaboratorResponse]:
    _owner_access(session, project_id, user)
    return [
        _collaborator_response(membership, session)
        for membership in list_memberships(session, project_id)
    ]


@router.post(
    "/{project_id}/collaborators",
    response_model=CollaboratorResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_collaborator(
    project_id: UUID,
    request: CollaboratorRequest,
    user: UserRecord = current_user_dependency,
    session: Session = database_session,
) -> CollaboratorResponse:
    _owner_access(session, project_id, user)
    collaborator = get_user_by_email(session, request.email.strip().lower())
    if collaborator is None:
        raise HTTPException(
            status_code=404, detail={"code": "USER_NOT_FOUND", "message": "User was not found"}
        )
    if collaborator.id == user.id:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "PROJECT_OWNER_CANNOT_BE_MEMBER",
                "message": "Owner is not a collaborator",
            },
        )
    membership = ProjectMembershipRecord(
        project_id=project_id, user_id=collaborator.id, role=request.role
    )
    session.add(membership)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail={
                "code": "PROJECT_MEMBERSHIP_EXISTS",
                "message": "User is already a collaborator",
            },
        ) from error
    session.refresh(membership)
    return _collaborator_response(membership, session)


@router.patch("/{project_id}/collaborators/{collaborator_id}", response_model=CollaboratorResponse)
def update_collaborator(
    project_id: UUID,
    collaborator_id: UUID,
    request: CollaboratorRoleRequest,
    user: UserRecord = current_user_dependency,
    session: Session = database_session,
) -> CollaboratorResponse:
    _owner_access(session, project_id, user)
    membership = get_membership(session, project_id, collaborator_id)
    if membership is None:
        raise _not_found()
    membership.role = request.role
    session.commit()
    session.refresh(membership)
    return _collaborator_response(membership, session)


@router.delete(
    "/{project_id}/collaborators/{collaborator_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_collaborator(
    project_id: UUID,
    collaborator_id: UUID,
    user: UserRecord = current_user_dependency,
    session: Session = database_session,
) -> None:
    _owner_access(session, project_id, user)
    membership = get_membership(session, project_id, collaborator_id)
    if membership is None:
        raise _not_found()
    session.delete(membership)
    session.commit()
    await project_connections.disconnect_user(project_id, collaborator_id)


@router.post("/{project_id}/commands", response_model=ProjectEditorState)
async def execute_project_command(
    project_id: UUID,
    request: ExecuteProjectCommandRequest,
    user: UserRecord = current_user_dependency,
    session: Session = database_session,
) -> ProjectEditorState:
    state = _mutate_project(
        project_id, request.base_revision, session, "execute", user, request.command
    )
    await _broadcast_project_updated(project_id, state)
    return state


@router.post("/{project_id}/undo", response_model=ProjectEditorState)
async def undo_project(
    project_id: UUID,
    request: ProjectRevisionRequest,
    user: UserRecord = current_user_dependency,
    session: Session = database_session,
) -> ProjectEditorState:
    state = _mutate_project(project_id, request.base_revision, session, "undo", user)
    await _broadcast_project_updated(project_id, state)
    return state


@router.post("/{project_id}/redo", response_model=ProjectEditorState)
async def redo_project(
    project_id: UUID,
    request: ProjectRevisionRequest,
    user: UserRecord = current_user_dependency,
    session: Session = database_session,
) -> ProjectEditorState:
    state = _mutate_project(project_id, request.base_revision, session, "redo", user)
    await _broadcast_project_updated(project_id, state)
    return state


@router.websocket("/{project_id}/realtime")
async def project_realtime(
    project_id: UUID, websocket: WebSocket, token: str | None = None
) -> None:
    if token is None:
        await websocket.close(code=1008)
        return
    session_dependency = get_db_session()
    session = next(session_dependency)
    try:
        user = get_user_by_id(session, decode_access_token(token))
        if user is None:
            await websocket.close(code=1008)
            return
        _project_access(session, project_id, user)
    except HTTPException:
        await websocket.close(code=1008)
        return
    finally:
        session_dependency.close()

    await project_connections.connect(project_id, user.id, websocket)
    try:
        while True:
            await websocket.receive()
    except WebSocketDisconnect:
        pass
    finally:
        await project_connections.disconnect(project_id, user.id, websocket)
