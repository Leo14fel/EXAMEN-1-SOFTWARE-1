"""Temporary CU-06 editor-session bridge.

This bridge is intentionally process-local and supported with a single FastAPI
worker. Sessions are bounded in memory and serialize access per session. CU-07
will replace this temporary storage with persistent project recovery.
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from threading import Lock
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import Field

from app.domain.uml.command_bus import UmlCommandBus
from app.domain.uml.commands import UmlCommand, UmlCommandExecutionError
from app.domain.uml.models import DomainModel, ProjectDocument

router = APIRouter(prefix="/editor/sessions", tags=["editor"])

_MAX_EDITOR_SESSIONS = 64


class EditorSessionState(DomainModel):
    session_id: UUID = Field(alias="sessionId")
    document: ProjectDocument
    can_undo: bool = Field(alias="canUndo")
    can_redo: bool = Field(alias="canRedo")


@dataclass(slots=True)
class _EditorSession:
    bus: UmlCommandBus
    lock: Lock = field(default_factory=Lock)


_editor_sessions: OrderedDict[UUID, _EditorSession] = OrderedDict()
_editor_sessions_lock = Lock()


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={
            "code": "EDITOR_SESSION_NOT_FOUND",
            "message": "Editor session was not found",
        },
    )


def _get_session(session_id: UUID) -> _EditorSession:
    with _editor_sessions_lock:
        session = _editor_sessions.get(session_id)
        if session is None:
            raise _not_found()
        _editor_sessions.move_to_end(session_id)
        return session


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
    session = _get_session(session_id)

    with session.lock:
        try:
            if action == "execute":
                if command is None:
                    raise AssertionError("command is required")
                session.bus.execute(command)
            elif action == "undo":
                session.bus.undo()
            elif action == "redo":
                session.bus.redo()
            else:
                raise AssertionError("unsupported editor action")
        except UmlCommandExecutionError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": error.code.value, "message": str(error)},
            ) from error

        return _state(session_id, session.bus)


@router.post("", response_model=EditorSessionState, status_code=status.HTTP_201_CREATED)
def create_editor_session() -> EditorSessionState:
    session_id = uuid4()
    session = _EditorSession(UmlCommandBus(ProjectDocument(ownerId=uuid4())))

    with _editor_sessions_lock:
        _editor_sessions[session_id] = session
        _editor_sessions.move_to_end(session_id)

        while len(_editor_sessions) > _MAX_EDITOR_SESSIONS:
            _editor_sessions.popitem(last=False)

    with session.lock:
        return _state(session_id, session.bus)


@router.get("/{session_id}", response_model=EditorSessionState)
def get_editor_session(session_id: UUID) -> EditorSessionState:
    session = _get_session(session_id)
    with session.lock:
        return _state(session_id, session.bus)


@router.post("/{session_id}/commands", response_model=EditorSessionState)
def execute_editor_command(session_id: UUID, command: UmlCommand) -> EditorSessionState:
    return _execute_bus_action(session_id, "execute", command)


@router.post("/{session_id}/undo", response_model=EditorSessionState)
def undo_editor_session(session_id: UUID) -> EditorSessionState:
    return _execute_bus_action(session_id, "undo")


@router.post("/{session_id}/redo", response_model=EditorSessionState)
def redo_editor_session(session_id: UUID) -> EditorSessionState:
    return _execute_bus_action(session_id, "redo")