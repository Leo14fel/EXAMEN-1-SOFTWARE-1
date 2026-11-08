"""Model output is data. Only this resolver can build canonical commands."""

from typing import Annotated, Literal
from uuid import uuid4

from pydantic import Field, field_validator

from app.domain.uml.commands import (
    AddUmlElementCommand,
    RemoveUmlElementCommand,
    UmlCommand,
    UpdateUmlElementCommand,
)
from app.domain.uml.executor import execute_uml_command
from app.domain.uml.models import (
    DomainModel,
    ProjectDocument,
    UmlAssociation,
    UmlAttribute,
    UmlClass,
    UmlMultiplicity,
    UmlOperation,
)
from app.domain.uml.validation import validate_uml_model

Name = Annotated[str, Field(min_length=1, max_length=100, pattern=r"^\S(?:.*\S)?$")]


class CreateClass(DomainModel):
    operation: Literal["createClass"]
    name: Name


class RenameClass(DomainModel):
    operation: Literal["renameClass"]
    target: Name
    name: Name


class DeleteClass(DomainModel):
    operation: Literal["deleteClass"]
    target: Name


class AddAttribute(DomainModel):
    operation: Literal["addAttribute"]
    target: Name
    name: Name
    type: Literal["String", "Integer", "Long", "Decimal", "Boolean", "Date", "DateTime", "UUID"]


class AddOperation(DomainModel):
    operation: Literal["addOperation"]
    target: Name
    name: Name


class CreateAssociation(DomainModel):
    operation: Literal["createAssociation"]
    source: Name
    target: Name
    source_lower: Literal[0, 1] = Field(alias="sourceLower")
    source_upper: Literal[1, "*"] = Field(alias="sourceUpper")
    target_lower: Literal[0, 1] = Field(alias="targetLower")
    target_upper: Literal[1, "*"] = Field(alias="targetUpper")

    @field_validator("source_lower", "source_upper", "target_lower", "target_upper", mode="before")
    @classmethod
    def no_boolean_bound(cls, value):
        if isinstance(value, bool):
            raise ValueError("Multiplicity must not be boolean")
        return value


class Clarify(DomainModel):
    operation: Literal["clarify", "unsupported"]
    reason: str = Field(min_length=1, max_length=500)


class IntentResponse(DomainModel):
    intent: Annotated[
        CreateClass
        | RenameClass
        | DeleteClass
        | AddAttribute
        | AddOperation
        | CreateAssociation
        | Clarify,
        Field(discriminator="operation"),
    ]


class ResolutionError(ValueError):
    pass


def resolve_intent(document: ProjectDocument, response: IntentResponse) -> UmlCommand:
    """Build and validate a single command on a copy, never persist/apply it."""
    intent = IntentResponse.model_validate(response.model_dump(by_alias=True)).intent
    classes = [item for item in document.uml_model.elements if isinstance(item, UmlClass)]

    def find(name: str) -> UmlClass:
        matches = [item for item in classes if item.name.casefold() == name.casefold()]
        if len(matches) != 1:
            raise ResolutionError("Target is missing or ambiguous; request clarification")
        return matches[0]

    if isinstance(intent, Clarify):
        raise ResolutionError("Clarification or an unsupported request cannot become a command")
    if isinstance(intent, CreateClass):
        if any(item.name.casefold() == intent.name.casefold() for item in classes):
            raise ResolutionError("Class name already exists")
        command = AddUmlElementCommand(element=UmlClass(name=intent.name, visibility="public"))
    elif isinstance(intent, CreateAssociation):
        command = AddUmlElementCommand(
            element=UmlAssociation(
                sourceId=find(intent.source).id,
                targetId=find(intent.target).id,
                sourceMultiplicity=UmlMultiplicity(
                    lower=intent.source_lower, upper=intent.source_upper
                ),
                targetMultiplicity=UmlMultiplicity(
                    lower=intent.target_lower, upper=intent.target_upper
                ),
            )
        )
    elif isinstance(intent, DeleteClass):
        command = RemoveUmlElementCommand(elementId=find(intent.target).id)
    else:
        target = find(intent.target).model_copy(deep=True)
        if isinstance(intent, RenameClass):
            target.name = intent.name
        elif isinstance(intent, AddAttribute):
            target.attributes.append(
                UmlAttribute(id=uuid4(), name=intent.name, type=intent.type, visibility="private")
            )
        elif isinstance(intent, AddOperation):
            target.operations.append(UmlOperation(name=intent.name, visibility="public"))
        command = UpdateUmlElementCommand(elementId=target.id, element=target)
    candidate = execute_uml_command(document.model_copy(deep=True), command)
    if not validate_uml_model(candidate.uml_model).is_valid:
        raise ResolutionError("Proposal violates UML validation")
    return command
