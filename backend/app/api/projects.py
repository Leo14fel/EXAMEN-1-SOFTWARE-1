import re
from datetime import datetime
from threading import Lock
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import Field, JsonValue
from pymongo.errors import DuplicateKeyError, PyMongoError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.api.auth import current_user_dependency
from app.db.dependencies import (
    StorageSession,
    commit_sql_session,
    get_db_session,
    rollback_sql_session,
)
from app.db.memberships import (
    ProjectMembershipRecord,
    ProjectRole,
    create_membership,
    delete_membership,
    get_membership,
    list_memberships,
    update_membership,
)
from app.db.mongo_projects import ProjectTooLargeError
from app.db.mongo_store import MongoStore
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
from app.interoperability.xmi.exporter import export_project_document

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


def _project_access(session: StorageSession, project_id: UUID, user: UserRecord) -> ProjectAccess:
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


def _owner_access(session: StorageSession, project_id: UUID, user: UserRecord) -> ProjectAccess:
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
    session: StorageSession,
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
            # Mongo must check current edit permission in the same atomic write
            # as revision: a concurrent revocation cannot leave a stale editor authorized.
            options = {"actor_id": user.id} if isinstance(session, MongoStore) else {}
            if not update_project_if_revision(session, bus.document, base_revision, **options):
                rollback_sql_session(session)
                _invalidate_project_bus(project_id)
                raise _revision_conflict()
            commit_sql_session(session)
        except HTTPException:
            raise
        except ProjectTooLargeError as error:
            _invalidate_project_bus(project_id)
            raise HTTPException(
                status_code=413,
                detail={
                    "code": "PROJECT_DOCUMENT_TOO_LARGE",
                    "message": "Project exceeds storage limit",
                },
            ) from error
        except (SQLAlchemyError, PyMongoError) as error:
            rollback_sql_session(session)
            _invalidate_project_bus(project_id)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "PROJECT_PERSISTENCE_UNAVAILABLE",
                    "message": "Project storage is unavailable",
                },
            ) from error

        return _state(bus)


def _summary(
    record: ProjectRecord, user_id: UUID, session: StorageSession
) -> ProjectSummary | None:
    membership = None if record.owner_id == user_id else get_membership(session, record.id, user_id)
    if record.owner_id != user_id and membership is None:
        return None
    role = ProjectRole.EDITOR if record.owner_id == user_id else membership.role
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
    session: StorageSession = database_session,
) -> ProjectDocument:
    document = ProjectDocument(ownerId=user.id, metadata=request.metadata)
    try:
        return create_project(session, document)
    except (SQLAlchemyError, PyMongoError) as error:
        rollback_sql_session(session)
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
    session: StorageSession = database_session,
) -> list[ProjectSummary]:
    return [
        summary
        for record in list_projects(session, user.id)
        if (summary := _summary(record, user.id, session)) is not None
    ]


@router.get("/{project_id}/export/xmi")
def export_project_xmi(
    project_id: UUID,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> Response:
    document = _project_access(session, project_id, user).document
    filename = _xmi_filename(document)
    return Response(
        content=export_project_document(document),
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{project_id}", response_model=ProjectDocument)
def get_persisted_project(
    project_id: UUID,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> ProjectDocument:
    return _project_access(session, project_id, user).document


def _xmi_filename(document: ProjectDocument) -> str:
    name = document.metadata.get("name")
    safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", name.strip()) if isinstance(name, str) else ""
    return f"{safe_name.strip('._') or f'project_{document.id.hex[:8]}'}.xmi"


def _collaborator_response(
    membership: ProjectMembershipRecord, session: StorageSession
) -> CollaboratorResponse:
    user = get_user_by_id(session, membership.user_id)
    if user is None:
        raise _not_found()
    return CollaboratorResponse(userId=user.id, email=user.email, role=membership.role)


@router.get("/{project_id}/collaborators", response_model=list[CollaboratorResponse])
def get_collaborators(
    project_id: UUID,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
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
    session: StorageSession = database_session,
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
    try:
        create_membership(session, membership)
    except (IntegrityError, DuplicateKeyError) as error:
        rollback_sql_session(session)
        raise HTTPException(
            status_code=409,
            detail={
                "code": "PROJECT_MEMBERSHIP_EXISTS",
                "message": "User is already a collaborator",
            },
        ) from error
    return _collaborator_response(membership, session)


@router.patch("/{project_id}/collaborators/{collaborator_id}", response_model=CollaboratorResponse)
def update_collaborator(
    project_id: UUID,
    collaborator_id: UUID,
    request: CollaboratorRoleRequest,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> CollaboratorResponse:
    _owner_access(session, project_id, user)
    membership = get_membership(session, project_id, collaborator_id)
    if membership is None:
        raise _not_found()
    membership.role = request.role
    if not update_membership(session, membership):
        raise _not_found()
    return _collaborator_response(membership, session)


@router.delete(
    "/{project_id}/collaborators/{collaborator_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_collaborator(
    project_id: UUID,
    collaborator_id: UUID,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> None:
    _owner_access(session, project_id, user)
    membership = get_membership(session, project_id, collaborator_id)
    if membership is None:
        raise _not_found()
    if not delete_membership(session, membership):
        raise _not_found()


@router.post("/{project_id}/commands", response_model=ProjectEditorState)
def execute_project_command(
    project_id: UUID,
    request: ExecuteProjectCommandRequest,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> ProjectEditorState:
    return _mutate_project(
        project_id, request.base_revision, session, "execute", user, request.command
    )


@router.post("/{project_id}/undo", response_model=ProjectEditorState)
def undo_project(
    project_id: UUID,
    request: ProjectRevisionRequest,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> ProjectEditorState:
    return _mutate_project(project_id, request.base_revision, session, "undo", user)


@router.post("/{project_id}/redo", response_model=ProjectEditorState)
def redo_project(
    project_id: UUID,
    request: ProjectRevisionRequest,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> ProjectEditorState:
    return _mutate_project(project_id, request.base_revision, session, "redo", user)
