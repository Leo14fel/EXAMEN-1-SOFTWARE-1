from datetime import timedelta

from app.domain.uml.commands import (
    UmlCommand,
    UmlCommandErrorCode,
    UmlCommandExecutionError,
)
from app.domain.uml.executor import execute_uml_command
from app.domain.uml.models import ProjectDocument, utc_now

MAX_HISTORY_SIZE = 100


class UmlCommandBus:
    def __init__(self, document: ProjectDocument) -> None:
        self._document = document.model_copy(deep=True)
        self._undo_stack: list[ProjectDocument] = []
        self._redo_stack: list[ProjectDocument] = []

    @property
    def document(self) -> ProjectDocument:
        return self._document.model_copy(deep=True)

    @property
    def can_undo(self) -> bool:
        return bool(self._undo_stack)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_stack)

    def execute(self, command: UmlCommand) -> ProjectDocument:
        next_document = execute_uml_command(self._document, command)
        self._append_undo_snapshot(self._document)
        self._redo_stack.clear()
        self._document = self._version(next_document)
        return self.document

    def undo(self) -> ProjectDocument:
        if not self._undo_stack:
            raise UmlCommandExecutionError(
                UmlCommandErrorCode.UNDO_NOT_AVAILABLE, "Undo is not available"
            )
        self._redo_stack.append(self._document.model_copy(deep=True))
        self._document = self._version(self._undo_stack.pop())
        return self.document

    def redo(self) -> ProjectDocument:
        if not self._redo_stack:
            raise UmlCommandExecutionError(
                UmlCommandErrorCode.REDO_NOT_AVAILABLE, "Redo is not available"
            )
        self._append_undo_snapshot(self._document)
        self._document = self._version(self._redo_stack.pop())
        return self.document

    def _append_undo_snapshot(self, document: ProjectDocument) -> None:
        self._undo_stack.append(document.model_copy(deep=True))
        if len(self._undo_stack) > MAX_HISTORY_SIZE:
            del self._undo_stack[0]

    def _version(self, document: ProjectDocument) -> ProjectDocument:
        document = document.model_copy(deep=True)
        next_updated_at = max(utc_now(), self._document.updated_at + timedelta(microseconds=1))
        return ProjectDocument(
            id=document.id,
            metadata=document.metadata,
            ownerId=document.owner_id,
            revision=self._document.revision + 1,
            createdAt=document.created_at,
            updatedAt=next_updated_at,
            umlModel=document.uml_model,
            diagramLayout=document.diagram_layout,
        )
