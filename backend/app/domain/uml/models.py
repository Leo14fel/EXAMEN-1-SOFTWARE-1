from datetime import UTC, datetime
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


class CanonicalUmlModel(DomainModel):
    elements: list[UmlElementBase] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_unique_element_ids(self) -> "CanonicalUmlModel":
        element_ids = [element.id for element in self.elements]
        if len(element_ids) != len(set(element_ids)):
            raise ValueError("elements must have unique ids")
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
