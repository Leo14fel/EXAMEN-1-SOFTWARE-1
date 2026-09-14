from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.domain.uml.models import (
    CanonicalUmlModel,
    DiagramLayout,
    DiagramNodeLayout,
    ProjectDocument,
    UmlAggregation,
    UmlAssociation,
    UmlAttribute,
    UmlClass,
    UmlComposition,
    UmlGeneralization,
    UmlMultiplicity,
    UmlOperation,
    UmlParameter,
)

OWNER_ID = UUID("b839adc0-64ae-4d66-9eb9-caa55d8918d8")
CLIENT_ID = UUID("4c745177-fec0-42d3-b12c-772b1a8cb11b")
ORDER_ID = UUID("3f72056c-8102-49e6-9977-c0c7f5334bd9")
RELATION_ID = UUID("d798684a-4f2a-4fae-b602-2429341a8b99")
TIMESTAMP = datetime(2026, 9, 13, 12, 0, tzinfo=UTC)


def uml_class(class_id: UUID, name: str) -> UmlClass:
    return UmlClass(id=class_id, name=name, visibility="public")


def multiplicity(lower: int, upper: int | str) -> UmlMultiplicity:
    return UmlMultiplicity(lower=lower, upper=upper)


def association(relation_id: UUID = RELATION_ID) -> UmlAssociation:
    return UmlAssociation(
        id=relation_id,
        sourceId=CLIENT_ID,
        targetId=ORDER_ID,
        sourceMultiplicity=multiplicity(1, 1),
        targetMultiplicity=multiplicity(0, "*"),
    )


@pytest.mark.parametrize(
    ("relationship_type", "kind"),
    [
        (UmlAssociation, "association"),
        (UmlAggregation, "aggregation"),
        (UmlComposition, "composition"),
    ],
)
def test_relationship_with_multiplicity_has_stable_kind(
    relationship_type: type[UmlAssociation | UmlAggregation | UmlComposition], kind: str
) -> None:
    relationship = relationship_type(
        sourceId=CLIENT_ID,
        targetId=ORDER_ID,
        sourceMultiplicity=multiplicity(1, 1),
        targetMultiplicity=multiplicity(0, "*"),
    )

    assert relationship.kind == kind


def test_generalization_has_stable_kind_and_child_to_parent_direction() -> None:
    relationship = UmlGeneralization(id=RELATION_ID, sourceId=CLIENT_ID, targetId=ORDER_ID)

    assert relationship.kind == "generalization"
    assert relationship.source_id == CLIENT_ID
    assert relationship.target_id == ORDER_ID


@pytest.mark.parametrize("relationship_type", [UmlAggregation, UmlComposition])
def test_aggregation_and_composition_use_source_whole_to_target_part_direction(
    relationship_type: type[UmlAggregation | UmlComposition],
) -> None:
    relationship = relationship_type(
        sourceId=ORDER_ID,
        targetId=CLIENT_ID,
        sourceMultiplicity=multiplicity(1, 1),
        targetMultiplicity=multiplicity(1, "*"),
    )

    assert relationship.source_id == ORDER_ID
    assert relationship.target_id == CLIENT_ID


@pytest.mark.parametrize(
    ("lower", "upper"), [(1, 1), (0, 1), (0, "*"), (1, "*")],
)
def test_accepts_structured_multiplicities(lower: int, upper: int | str) -> None:
    value = multiplicity(lower, upper)

    assert value.lower == lower
    assert value.upper == upper


@pytest.mark.parametrize(
    "payload",
    [
        {"lower": -1, "upper": 1},
        {"lower": 0, "upper": -1},
        {"lower": 2, "upper": 1},
        {"lower": 0, "upper": "many"},
        {"lower": True, "upper": 1},
        {"lower": 0, "upper": False},
        {"lower": 0, "upper": 1, "unknown": True},
    ],
)
def test_rejects_invalid_multiplicity(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        UmlMultiplicity.model_validate(payload)


@pytest.mark.parametrize(
    ("relationship_type", "payload"),
    [
        (UmlAssociation, {"kind": "aggregation"}),
        (UmlGeneralization, {"kind": "association"}),
    ],
)
def test_rejects_incorrect_relationship_kind(
    relationship_type: type[UmlAssociation | UmlGeneralization], payload: dict[str, str]
) -> None:
    data = {"sourceId": CLIENT_ID, "targetId": ORDER_ID, **payload}
    if relationship_type is UmlAssociation:
        data.update(
            sourceMultiplicity={"lower": 1, "upper": 1},
            targetMultiplicity={"lower": 0, "upper": "*"},
        )
    with pytest.raises(ValidationError):
        relationship_type.model_validate(data)


def test_model_accepts_existing_references_and_self_relation() -> None:
    self_relation = UmlAssociation(
        id=RELATION_ID,
        sourceId=CLIENT_ID,
        targetId=CLIENT_ID,
        sourceMultiplicity=multiplicity(0, 1),
        targetMultiplicity=multiplicity(0, "*"),
    )

    model = CanonicalUmlModel(elements=[uml_class(CLIENT_ID, "Empleado"), self_relation])

    assert model.elements[-1] == self_relation


@pytest.mark.parametrize("field_name", ["sourceId", "targetId"])
def test_rejects_relationship_reference_to_missing_class(field_name: str) -> None:
    data = association().model_dump(by_alias=True)
    data[field_name] = str(RELATION_ID)

    with pytest.raises(ValidationError):
        CanonicalUmlModel(elements=[uml_class(CLIENT_ID, "Cliente"), data])


@pytest.mark.parametrize("field_name", ["sourceId", "targetId"])
def test_rejects_relationship_reference_to_another_relationship(field_name: str) -> None:
    other_relation = association(ORDER_ID)
    data = association().model_dump(by_alias=True)
    data[field_name] = str(ORDER_ID)

    with pytest.raises(ValidationError):
        CanonicalUmlModel(elements=[uml_class(CLIENT_ID, "Cliente"), other_relation, data])


@pytest.mark.parametrize(
    "duplicate_source", ["class", "attribute", "operation", "parameter", "relation"]
)
def test_rejects_relation_id_duplicated_with_any_semantic_element(duplicate_source: str) -> None:
    nested = UmlClass(
        id=CLIENT_ID,
        name="Cliente",
        visibility="public",
        attributes=[UmlAttribute(id=ORDER_ID, name="codigo", visibility="private", type="String")],
        operations=[
            UmlOperation(
                id=RELATION_ID,
                name="buscar",
                visibility="public",
                parameters=[UmlParameter(id=OWNER_ID, name="codigo", type="String")],
            )
        ],
    )
    duplicate_id = {
        "class": CLIENT_ID,
        "attribute": ORDER_ID,
        "operation": RELATION_ID,
        "parameter": OWNER_ID,
        "relation": UUID("8141de6e-4ca9-4d60-9a91-ff6c8443241a"),
    }[duplicate_source]
    valid_relation = UmlAssociation(
        id=duplicate_id,
        sourceId=CLIENT_ID,
        targetId=CLIENT_ID,
        sourceMultiplicity=multiplicity(1, 1),
        targetMultiplicity=multiplicity(1, 1),
    )
    elements = [nested, valid_relation]
    if duplicate_source == "relation":
        elements.append(
            UmlGeneralization(id=duplicate_id, sourceId=CLIENT_ID, targetId=CLIENT_ID)
        )

    with pytest.raises(ValidationError):
        CanonicalUmlModel(elements=elements)


def test_relationship_models_reject_unexpected_fields() -> None:
    with pytest.raises(ValidationError):
        UmlGeneralization(sourceId=CLIENT_ID, targetId=ORDER_ID, unknown=True)


def test_layout_accepts_class_and_rejects_relationship_or_orphan() -> None:
    relation = association()
    model = CanonicalUmlModel(
        elements=[uml_class(CLIENT_ID, "Cliente"), uml_class(ORDER_ID, "Pedido"), relation]
    )
    class_layout = DiagramLayout(
        nodes={CLIENT_ID: DiagramNodeLayout(x=0, y=0, width=100, height=80)}
    )

    assert ProjectDocument(
        owner_id=OWNER_ID,
        created_at=TIMESTAMP,
        updated_at=TIMESTAMP,
        uml_model=model,
        diagram_layout=class_layout,
    )
    for node_id in (RELATION_ID, OWNER_ID):
        with pytest.raises(ValidationError):
            ProjectDocument(
                owner_id=OWNER_ID,
                created_at=TIMESTAMP,
                updated_at=TIMESTAMP,
                uml_model=model,
                diagram_layout=DiagramLayout(
                    nodes={node_id: DiagramNodeLayout(x=0, y=0, width=100, height=80)}
                ),
            )


def test_project_document_round_trip_preserves_concrete_relationship_types() -> None:
    admin_id = UUID("8141de6e-4ca9-4d60-9a91-ff6c8443241a")
    document = ProjectDocument(
        owner_id=OWNER_ID,
        created_at=TIMESTAMP,
        updated_at=TIMESTAMP,
        uml_model=CanonicalUmlModel(
            elements=[
                UmlClass(
                    id=CLIENT_ID,
                    name="Cliente",
                    visibility="public",
                    attributes=[
                        UmlAttribute(id=ORDER_ID, name="email", visibility="private", type="String")
                    ],
                    operations=[
                        UmlOperation(
                            id=RELATION_ID,
                            name="crearPedido",
                            visibility="public",
                            parameters=[UmlParameter(id=OWNER_ID, name="total", type="Decimal")],
                        )
                    ],
                ),
                uml_class(admin_id, "Pedido"),
                UmlAssociation(
                    id=UUID("f2441b0f-5200-4ed3-bffa-a8a582c66b99"),
                    sourceId=CLIENT_ID,
                    targetId=admin_id,
                    sourceMultiplicity=multiplicity(1, 1),
                    targetMultiplicity=multiplicity(0, "*"),
                ),
                UmlAggregation(
                    id=UUID("a2441b0f-5200-4ed3-bffa-a8a582c66b99"),
                    sourceId=CLIENT_ID,
                    targetId=admin_id,
                    sourceMultiplicity=multiplicity(0, 1),
                    targetMultiplicity=multiplicity(1, "*"),
                ),
                UmlComposition(
                    id=UUID("c2441b0f-5200-4ed3-bffa-a8a582c66b99"),
                    sourceId=admin_id,
                    targetId=CLIENT_ID,
                    sourceMultiplicity=multiplicity(1, 1),
                    targetMultiplicity=multiplicity(1, "*"),
                ),
                UmlGeneralization(
                    id=UUID("e2441b0f-5200-4ed3-bffa-a8a582c66b99"),
                    sourceId=admin_id,
                    targetId=CLIENT_ID,
                ),
            ]
        ),
        diagram_layout=DiagramLayout(
            nodes={
                CLIENT_ID: DiagramNodeLayout(x=10, y=20, width=220, height=160),
                admin_id: DiagramNodeLayout(x=250, y=20, width=220, height=160),
            }
        ),
    )

    restored = ProjectDocument.model_validate_json(document.model_dump_json(by_alias=True))

    assert restored == document
    assert [type(element) for element in restored.uml_model.elements] == [
        UmlClass,
        UmlClass,
        UmlAssociation,
        UmlAggregation,
        UmlComposition,
        UmlGeneralization,
    ]
