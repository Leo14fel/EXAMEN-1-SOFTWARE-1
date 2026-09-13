from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class UmlElementBase(DomainModel):
    id: UUID = Field(default_factory=uuid4)
    kind: str

    @field_validator("kind")
    @classmethod
    def normalize_kind(cls, value: str) -> str:
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError("kind must not be blank")
        return normalized_value


class UmlVisibility(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    PACKAGE = "package"


class UmlNamedElement(DomainModel):
    name: str

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return normalize_non_blank(value, "name")


class UmlTypedElement(UmlNamedElement):
    type: str

    @field_validator("type")
    @classmethod
    def normalize_type(cls, value: str) -> str:
        return normalize_non_blank(value, "type")


def normalize_non_blank(value: str, field_name: str) -> str:
    normalized_value = value.strip()
    if not normalized_value:
        raise ValueError(f"{field_name} must not be blank")
    return normalized_value


class UmlParameter(UmlTypedElement):
    id: UUID = Field(default_factory=uuid4)


class UmlAttribute(UmlElementBase, UmlTypedElement):
    kind: Literal["attribute"] = "attribute"
    visibility: UmlVisibility


class UmlOperation(UmlElementBase, UmlNamedElement):
    kind: Literal["operation"] = "operation"
    visibility: UmlVisibility
    parameters: list[UmlParameter] = Field(default_factory=list)
    return_type: str | None = Field(default=None, alias="returnType")

    @field_validator("return_type")
    @classmethod
    def normalize_return_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_non_blank(value, "return_type")


class UmlClass(UmlElementBase, UmlNamedElement):
    kind: Literal["class"] = "class"
    visibility: UmlVisibility
    attributes: list[UmlAttribute] = Field(default_factory=list)
    operations: list[UmlOperation] = Field(default_factory=list)


class CanonicalUmlModel(DomainModel):
    elements: list[UmlClass] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_unique_element_ids(self) -> "CanonicalUmlModel":
        semantic_ids: list[UUID] = []
        for uml_class in self.elements:
            semantic_ids.append(uml_class.id)
            for attribute in uml_class.attributes:
                semantic_ids.append(attribute.id)
            for operation in uml_class.operations:
                semantic_ids.append(operation.id)
                semantic_ids.extend(parameter.id for parameter in operation.parameters)

        if len(semantic_ids) != len(set(semantic_ids)):
            raise ValueError("semantic elements must have globally unique ids")
        return self


class DiagramNodeLayout(DomainModel):
    x: float
    y: float
    width: float = Field(gt=0)
    height: float = Field(gt=0)


class DiagramLayout(DomainModel):
    nodes: dict[UUID, DiagramNodeLayout] = Field(default_factory=dict)


def utc_now() -> datetime:
    return datetime.now(UTC)


class ProjectDocument(DomainModel):
    id: UUID = Field(default_factory=uuid4)
    metadata: dict[str, JsonValue] = Field(default_factory=dict)
    owner_id: UUID = Field(alias="ownerId")
    revision: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=utc_now, alias="createdAt")
    updated_at: datetime = Field(default_factory=utc_now, alias="updatedAt")
    uml_model: CanonicalUmlModel = Field(default_factory=CanonicalUmlModel, alias="umlModel")
    diagram_layout: DiagramLayout = Field(default_factory=DiagramLayout, alias="diagramLayout")

    @model_validator(mode="after")
    def validate_document_consistency(self) -> "ProjectDocument":
        for field_name in ("created_at", "updated_at"):
            timestamp = getattr(self, field_name)
            if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                raise ValueError(f"{field_name} must be timezone-aware")

        if self.updated_at < self.created_at:
            raise ValueError("updated_at must be greater than or equal to created_at")

        element_ids = {element.id for element in self.uml_model.elements}
        orphan_layout_ids = set(self.diagram_layout.nodes) - element_ids
        if orphan_layout_ids:
            raise ValueError("diagram_layout nodes must reference existing UML elements")

        return self
