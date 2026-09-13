from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.domain.uml.models import (
    CanonicalUmlModel,
    DiagramLayout,
    DiagramNodeLayout,
    ProjectDocument,
    UmlAttribute,
    UmlClass,
    UmlOperation,
    UmlParameter,
    UmlVisibility,
)

CLASS_ID = UUID("8141de6e-4ca9-4d60-9a91-ff6c8443241a")
ATTRIBUTE_ID = UUID("4c745177-fec0-42d3-b12c-772b1a8cb11b")
OPERATION_ID = UUID("3f72056c-8102-49e6-9977-c0c7f5334bd9")
PARAMETER_ID = UUID("d798684a-4f2a-4fae-b602-2429341a8b99")
OWNER_ID = UUID("b839adc0-64ae-4d66-9eb9-caa55d8918d8")
TIMESTAMP = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)


def valid_class() -> UmlClass:
    return UmlClass(
        id=CLASS_ID,
        name="  Usuario  ",
        visibility=UmlVisibility.PUBLIC,
        attributes=[
            UmlAttribute(
                id=ATTRIBUTE_ID,
                name="  email  ",
                visibility=UmlVisibility.PRIVATE,
                type="  String  ",
            )
        ],
        operations=[
            UmlOperation(
                id=OPERATION_ID,
                name="  login  ",
                visibility=UmlVisibility.PUBLIC,
                parameters=[UmlParameter(id=PARAMETER_ID, name="  password ", type=" String ")],
                returnType=" Boolean ",
            )
        ],
    )


def document_for(uml_class: UmlClass, layout: DiagramLayout | None = None) -> ProjectDocument:
    return ProjectDocument(
        owner_id=OWNER_ID,
        created_at=TIMESTAMP,
        updated_at=TIMESTAMP,
        uml_model=CanonicalUmlModel(elements=[uml_class]),
        diagram_layout=layout or DiagramLayout(),
    )


def test_uml_class_has_stable_kind_normalized_name_and_generated_id() -> None:
    uml_class = UmlClass(name="  Usuario  ", visibility="public")

    assert isinstance(uml_class.id, UUID)
    assert uml_class.kind == "class"
    assert uml_class.name == "Usuario"
    assert uml_class.visibility is UmlVisibility.PUBLIC


@pytest.mark.parametrize("name", ["", "   "])
def test_rejects_blank_class_name(name: str) -> None:
    with pytest.raises(ValidationError):
        UmlClass(name=name, visibility="public")


def test_rejects_invalid_visibility_and_class_kind() -> None:
    with pytest.raises(ValidationError):
        UmlClass(name="Usuario", visibility="internal")
    with pytest.raises(ValidationError):
        UmlClass(name="Usuario", visibility="public", kind="interface")


@pytest.mark.parametrize("field_name", ["name", "type"])
def test_attribute_rejects_blank_semantic_fields(field_name: str) -> None:
    attribute_data = {"name": "email", "visibility": "private", "type": "String", field_name: " "}
    with pytest.raises(ValidationError):
        UmlAttribute(**attribute_data)


def test_attribute_has_stable_kind_and_normalized_type() -> None:
    attribute = UmlAttribute(name=" email ", visibility="private", type=" String ")

    assert isinstance(attribute.id, UUID)
    assert attribute.kind == "attribute"
    assert attribute.name == "email"
    assert attribute.type == "String"


def test_operation_supports_empty_parameters_and_neutral_missing_return_type() -> None:
    operation = UmlOperation(name="logout", visibility="public")

    assert isinstance(operation.id, UUID)
    assert operation.kind == "operation"
    assert operation.parameters == []
    assert operation.return_type is None
    assert operation.model_dump(mode="json", by_alias=True)["returnType"] is None
    assert UmlOperation.model_validate_json(operation.model_dump_json(by_alias=True)) == operation


def test_operation_normalizes_explicit_return_type() -> None:
    operation = UmlOperation(name="login", visibility="public", returnType=" Boolean ")

    assert operation.return_type == "Boolean"


@pytest.mark.parametrize("field_name", ["name", "returnType"])
def test_operation_rejects_blank_semantic_fields(field_name: str) -> None:
    operation_data = {
        "name": "login",
        "visibility": "public",
        "returnType": "Boolean",
        field_name: " ",
    }
    with pytest.raises(ValidationError):
        UmlOperation(**operation_data)


@pytest.mark.parametrize("field_name", ["name", "type"])
def test_parameter_rejects_blank_semantic_fields(field_name: str) -> None:
    parameter_data = {"name": "password", "type": "String", field_name: " "}
    with pytest.raises(ValidationError):
        UmlParameter(**parameter_data)


def test_parameter_has_uuid_and_normalized_fields() -> None:
    parameter = UmlParameter(name=" password ", type=" String ")

    assert isinstance(parameter.id, UUID)
    assert parameter.name == "password"
    assert parameter.type == "String"


@pytest.mark.parametrize(
    "duplicate_level",
    ["class", "attribute", "operation", "parameter"],
)
def test_rejects_duplicate_ids_at_every_semantic_level(duplicate_level: str) -> None:
    uml_class = valid_class()
    duplicate_id = {
        "class": uml_class.id,
        "attribute": uml_class.attributes[0].id,
        "operation": uml_class.operations[0].id,
        "parameter": uml_class.operations[0].parameters[0].id,
    }[duplicate_level]

    with pytest.raises(ValidationError):
        CanonicalUmlModel(
            elements=[
                uml_class,
                UmlClass(id=duplicate_id, name="Otro", visibility="public"),
            ]
        )


def test_rejects_duplicate_ids_between_nested_members() -> None:
    with pytest.raises(ValidationError):
        CanonicalUmlModel(
            elements=[
                UmlClass(
                    id=CLASS_ID,
                    name="Usuario",
                    visibility="public",
                    attributes=[
                        UmlAttribute(
                            id=ATTRIBUTE_ID,
                            name="email",
                            visibility="private",
                            type="String",
                        )
                    ],
                    operations=[
                        UmlOperation(
                            id=ATTRIBUTE_ID,
                            name="login",
                            visibility="public",
                            parameters=[],
                        )
                    ],
                )
            ]
        )


@pytest.mark.parametrize(
    "factory, data",
    [
        (UmlClass, {"name": "Usuario", "visibility": "public", "unknown": True}),
        (
            UmlAttribute,
            {"name": "email", "visibility": "private", "type": "String", "unknown": True},
        ),
        (UmlOperation, {"name": "login", "visibility": "public", "unknown": True}),
        (UmlParameter, {"name": "password", "type": "String", "unknown": True}),
    ],
)
def test_rejects_unexpected_member_fields(factory: type[object], data: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        factory(**data)  # type: ignore[operator]


def test_project_document_round_trip_preserves_class_members_and_layout() -> None:
    uml_class = valid_class()
    document = document_for(
        uml_class,
        DiagramLayout(nodes={CLASS_ID: DiagramNodeLayout(x=10, y=20, width=220, height=160)}),
    )

    public_data = document.model_dump(mode="json", by_alias=True)
    restored = ProjectDocument.model_validate_json(document.model_dump_json(by_alias=True))
    class_data = public_data["umlModel"]["elements"][0]

    assert class_data["kind"] == "class"
    assert class_data["attributes"][0]["kind"] == "attribute"
    assert class_data["operations"][0]["parameters"][0]["name"] == "password"
    assert class_data["operations"][0]["returnType"] == "Boolean"
    assert str(CLASS_ID) in public_data["diagramLayout"]["nodes"]
    assert restored == document


def test_rejects_orphan_class_layout() -> None:
    with pytest.raises(ValidationError):
        ProjectDocument(
            owner_id=OWNER_ID,
            created_at=TIMESTAMP,
            updated_at=TIMESTAMP,
            uml_model=CanonicalUmlModel(),
            diagram_layout=DiagramLayout(
                nodes={CLASS_ID: DiagramNodeLayout(x=0, y=0, width=100, height=100)}
            ),
        )
