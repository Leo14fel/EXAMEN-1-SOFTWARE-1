from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import Field

from app.domain.uml.command_bus import UmlCommandBus
from app.domain.uml.commands import UmlCommand, UmlCommandExecutionError
from app.domain.uml.models import DomainModel, ProjectDocument

router = APIRouter(prefix="/editor/sessions", tags=["editor"])


class EditorSessionState(DomainModel):
    session_id: UUID = Field(alias="sessionId")
    document: ProjectDocument
    can_undo: bool = Field(alias="canUndo")
    can_redo: bool = Field(alias="canRedo")


_editor_sessions: dict[UUID, UmlCommandBus] = {}


def _get_bus(session_id: UUID) -> UmlCommandBus:
    bus = _editor_sessions.get(session_id)
    if bus is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "EDITOR_SESSION_NOT_FOUND",
                "message": "Editor session was not found",
            },
        )
    return bus


def _state(session_id: UUID, bus: UmlCommandBus) -> EditorSessionState:
    return EditorSessionState(
        sessionId=session_id,
        document=bus.document,
        canUndo=bus.can_undo,
        canRedo=bus.can_redo,
    )


def _execute_bus_action(
    session_id: UUID,
    action: str,
    command: UmlCommand | None = None,
) -> EditorSessionState:
    bus = _get_bus(session_id)
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
            raise AssertionError("unsupported editor action")
    except UmlCommandExecutionError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": error.code.value, "message": str(error)},
        ) from error
    return _state(session_id, bus)


@router.post("", response_model=EditorSessionState, status_code=status.HTTP_201_CREATED)
def create_editor_session() -> EditorSessionState:
    session_id = uuid4()
    bus = UmlCommandBus(ProjectDocument(ownerId=uuid4()))
    _editor_sessions[session_id] = bus
    return _state(session_id, bus)


@router.get("/{session_id}", response_model=EditorSessionState)
def get_editor_session(session_id: UUID) -> EditorSessionState:
    return _state(session_id, _get_bus(session_id))


@router.post("/{session_id}/commands", response_model=EditorSessionState)
def execute_editor_command(session_id: UUID, command: UmlCommand) -> EditorSessionState:
    return _execute_bus_action(session_id, "execute", command)


@router.post("/{session_id}/undo", response_model=EditorSessionState)
def undo_editor_session(session_id: UUID) -> EditorSessionState:
    return _execute_bus_action(session_id, "undo")


@router.post("/{session_id}/redo", response_model=EditorSessionState)
def redo_editor_session(session_id: UUID) -> EditorSessionState:
    return _execute_bus_action(session_id, "redo")