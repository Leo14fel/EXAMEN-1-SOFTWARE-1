from datetime import datetime
from threading import Lock
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field, JsonValue
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.auth import current_user_dependency
from app.db.dependencies import get_db_session
from app.db.projects import (
    ProjectRecord,
    create_project,
    get_project,
    list_projects,
    update_project_if_revision,
)
from app.db.users import UserRecord
from app.domain.uml.command_bus import UmlCommandBus
from app.domain.uml.commands import UmlCommand, UmlCommandExecutionError
from app.domain.uml.models import DomainModel, ProjectDocument

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
        document = get_project(session, project_id)
        if document is None:
            raise _not_found()
        if document.owner_id != user.id:
            raise _not_found()
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


def _summary(record: ProjectRecord) -> ProjectSummary:
    return ProjectSummary(
        id=record.id,
        ownerId=record.owner_id,
        metadata=record.project_metadata,
        revision=record.revision,
        createdAt=record.created_at,
        updatedAt=record.updated_at,
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
    return [_summary(record) for record in list_projects(session, user.id)]


@router.get("/{project_id}", response_model=ProjectDocument)
def get_persisted_project(
    project_id: UUID,
    user: UserRecord = current_user_dependency,
    session: Session = database_session,
) -> ProjectDocument:
    document = get_project(session, project_id)
    if document is None:
        raise _not_found()
    if document.owner_id != user.id:
        raise _not_found()
    return document


@router.post("/{project_id}/commands", response_model=ProjectEditorState)
def execute_project_command(
    project_id: UUID,
    request: ExecuteProjectCommandRequest,
    user: UserRecord = current_user_dependency,
    session: Session = database_session,
) -> ProjectEditorState:
    return _mutate_project(
        project_id, request.base_revision, session, "execute", user, request.command
    )


@router.post("/{project_id}/undo", response_model=ProjectEditorState)
def undo_project(
    project_id: UUID,
    request: ProjectRevisionRequest,
    user: UserRecord = current_user_dependency,
    session: Session = database_session,
) -> ProjectEditorState:
    return _mutate_project(project_id, request.base_revision, session, "undo", user)


@router.post("/{project_id}/redo", response_model=ProjectEditorState)
def redo_project(
    project_id: UUID,
    request: ProjectRevisionRequest,
    user: UserRecord = current_user_dependency,
    session: Session = database_session,
) -> ProjectEditorState:
    return _mutate_project(project_id, request.base_revision, session, "redo", user)
