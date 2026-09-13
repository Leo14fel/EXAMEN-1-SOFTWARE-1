from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.domain.uml.models import (
    CanonicalUmlModel,
    DiagramLayout,
    DiagramNodeLayout,
    ProjectDocument,
    UmlClass,
    UmlElementBase,
    UmlVisibility,
)

OWNER_ID = UUID("b839adc0-64ae-4d66-9eb9-caa55d8918d8")
ELEMENT_ID = UUID("f2441b0f-5200-4ed3-bffa-a8a582c66b99")
CREATED_AT = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)
UPDATED_AT = datetime(2026, 9, 12, 12, 1, tzinfo=UTC)


def document_payload(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "ownerId": str(OWNER_ID),
        "createdAt": CREATED_AT.isoformat(),
        "updatedAt": UPDATED_AT.isoformat(),
    }
    payload.update(overrides)
    return payload


def test_creates_minimal_document_with_defaults() -> None:
    document = ProjectDocument.model_validate(document_payload())

    assert isinstance(document.id, UUID)
    assert document.owner_id == OWNER_ID
    assert document.metadata == {}
    assert document.revision == 0
    assert document.uml_model.elements == []
    assert document.diagram_layout.nodes == {}


@pytest.mark.parametrize("revision", [0, 4])
def test_accepts_non_negative_revision(revision: int) -> None:
    assert ProjectDocument.model_validate(document_payload(revision=revision)).revision == revision


def test_rejects_negative_revision() -> None:
    with pytest.raises(ValidationError):
        ProjectDocument.model_validate(document_payload(revision=-1))


@pytest.mark.parametrize("field_name", ["createdAt", "updatedAt"])
def test_rejects_naive_timestamps(field_name: str) -> None:
    with pytest.raises(ValidationError):
        ProjectDocument.model_validate(
            document_payload(**{field_name: datetime(2026, 9, 12, 12, 0)})
        )


def test_rejects_updated_at_before_created_at() -> None:
    with pytest.raises(ValidationError):
        ProjectDocument.model_validate(
            document_payload(updatedAt=datetime(2026, 9, 12, 11, 59, tzinfo=UTC))
        )


def test_accepts_json_safe_metadata_and_rejects_non_json_value() -> None:
    document = ProjectDocument.model_validate(
        document_payload(metadata={"nested": [True, None, {"count": 2}]})
    )

    assert document.metadata["nested"] == [True, None, {"count": 2}]
    with pytest.raises(ValidationError):
        ProjectDocument.model_validate(document_payload(metadata={"invalid": {1, 2}}))


def test_canonical_model_accepts_empty_elements_and_normalizes_kind() -> None:
    assert CanonicalUmlModel().elements == []
    assert UmlElementBase(kind="  future-kind  ").kind == "future-kind"


@pytest.mark.parametrize("kind", ["", "   "])
def test_rejects_blank_element_kind(kind: str) -> None:
    with pytest.raises(ValidationError):
        UmlElementBase(kind=kind)


def test_rejects_duplicate_uml_element_ids() -> None:
    element = UmlElementBase(id=ELEMENT_ID, kind="future-kind")

    with pytest.raises(ValidationError):
        CanonicalUmlModel(elements=[element, element])


def test_layout_allows_negative_coordinates_and_requires_positive_size() -> None:
    layout = DiagramNodeLayout(x=-10, y=-20, width=220, height=160)

    assert layout.x == -10
    assert layout.y == -20
    for invalid_size in ({"width": 0}, {"width": -1}, {"height": 0}, {"height": -1}):
        with pytest.raises(ValidationError):
            DiagramNodeLayout(**{"x": 0, "y": 0, "width": 100, "height": 100, **invalid_size})


def test_accepts_element_with_or_without_layout() -> None:
    element = UmlClass(id=ELEMENT_ID, name="FutureClass", visibility=UmlVisibility.PUBLIC)
    model = CanonicalUmlModel(elements=[element])
    layout = DiagramNodeLayout(x=100, y=200, width=220, height=160)

    assert ProjectDocument.model_validate(document_payload(umlModel=model))
    assert ProjectDocument.model_validate(
        document_payload(umlModel=model, diagramLayout=DiagramLayout(nodes={ELEMENT_ID: layout}))
    )


def test_rejects_orphan_layout() -> None:
    with pytest.raises(ValidationError):
        ProjectDocument.model_validate(
            document_payload(
                diagramLayout={str(ELEMENT_ID): {"x": 0, "y": 0, "width": 100, "height": 100}}
            )
        )


def test_rejects_unexpected_fields() -> None:
    with pytest.raises(ValidationError):
        ProjectDocument.model_validate(document_payload(inventedField=True))


def test_public_aliases_and_round_trip_json() -> None:
    document = ProjectDocument.model_validate(
        document_payload(
            id=str(uuid4()),
            metadata={"active": True},
            umlModel={
                "elements": [
                    {
                        "id": str(ELEMENT_ID),
                        "kind": "class",
                        "name": "FutureClass",
                        "visibility": "public",
                    }
                ]
            },
            diagramLayout={
                "nodes": {str(ELEMENT_ID): {"x": 100, "y": 200, "width": 220, "height": 160}}
            },
        )
    )

    public_json = document.model_dump_json(by_alias=True)
    public_data = document.model_dump(mode="json", by_alias=True)
    restored_document = ProjectDocument.model_validate_json(public_json)

    assert public_data["ownerId"] == str(OWNER_ID)
    assert public_data["id"] == str(document.id)
    assert public_data["createdAt"] == CREATED_AT.isoformat().replace("+00:00", "Z")
    assert public_data["umlModel"]["elements"][0]["id"] == str(ELEMENT_ID)
    assert str(ELEMENT_ID) in public_data["diagramLayout"]["nodes"]
    assert restored_document == document
