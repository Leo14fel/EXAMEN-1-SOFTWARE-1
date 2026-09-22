from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from app.domain.uml.models import CanonicalUmlElement, DiagramNodeLayout, DomainModel


class UmlCommandErrorCode(StrEnum):
    ELEMENT_NOT_FOUND = "ELEMENT_NOT_FOUND"
    ELEMENT_ALREADY_EXISTS = "ELEMENT_ALREADY_EXISTS"
    ELEMENT_ID_MISMATCH = "ELEMENT_ID_MISMATCH"
    ELEMENT_KIND_MISMATCH = "ELEMENT_KIND_MISMATCH"
    NODE_LAYOUT_NOT_FOUND = "NODE_LAYOUT_NOT_FOUND"
    NODE_LAYOUT_TARGET_NOT_CLASS = "NODE_LAYOUT_TARGET_NOT_CLASS"
    INVALID_RESULTING_DOCUMENT = "INVALID_RESULTING_DOCUMENT"
    GENERALIZATION_SELF_REFERENCE = "GENERALIZATION_SELF_REFERENCE"
    GENERALIZATION_CYCLE = "GENERALIZATION_CYCLE"
    UNDO_NOT_AVAILABLE = "UNDO_NOT_AVAILABLE"
    REDO_NOT_AVAILABLE = "REDO_NOT_AVAILABLE"


class UmlCommandExecutionError(Exception):
    def __init__(self, code: UmlCommandErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class UmlCommandBase(DomainModel):
    command_type: str = Field(alias="commandType")


class AddUmlElementCommand(UmlCommandBase):
    command_type: Literal["addElement"] = Field(default="addElement", alias="commandType")
    element: CanonicalUmlElement


class UpdateUmlElementCommand(UmlCommandBase):
    command_type: Literal["updateElement"] = Field(default="updateElement", alias="commandType")
    element_id: UUID = Field(alias="elementId")
    element: CanonicalUmlElement


class RemoveUmlElementCommand(UmlCommandBase):
    command_type: Literal["removeElement"] = Field(default="removeElement", alias="commandType")
    element_id: UUID = Field(alias="elementId")


class SetNodeLayoutCommand(UmlCommandBase):
    command_type: Literal["setNodeLayout"] = Field(default="setNodeLayout", alias="commandType")
    element_id: UUID = Field(alias="elementId")
    layout: DiagramNodeLayout


class RemoveNodeLayoutCommand(UmlCommandBase):
    command_type: Literal["removeNodeLayout"] = Field(
        default="removeNodeLayout", alias="commandType"
    )
    element_id: UUID = Field(alias="elementId")


UmlCommand = Annotated[
    AddUmlElementCommand
    | UpdateUmlElementCommand
    | RemoveUmlElementCommand
    | SetNodeLayoutCommand
    | RemoveNodeLayoutCommand,
    Field(discriminator="command_type"),
]
