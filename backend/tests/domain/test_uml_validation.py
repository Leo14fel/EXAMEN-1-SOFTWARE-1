from uuid import UUID

import pytest

from app.domain.uml.models import (
    CanonicalUmlModel,
    UmlAssociation,
    UmlAttribute,
    UmlClass,
    UmlGeneralization,
    UmlMultiplicity,
    UmlOperation,
    UmlParameter,
)
from app.domain.uml.validation import (
    UmlDiagnosticCode,
    UmlDiagnosticSeverity,
    UmlValidationResult,
    validate_uml_model,
)


def uml_class(name: str, **kwargs: object) -> UmlClass:
    return UmlClass(name=name, visibility="public", **kwargs)


def parameter(name: str, parameter_type: str) -> UmlParameter:
    return UmlParameter(name=name, type=parameter_type)


def email_attribute() -> UmlAttribute:
    return UmlAttribute(name="email", visibility="private", type="String")


def operation(
    name: str, parameters: list[UmlParameter] | None = None, return_type: str | None = None
) -> UmlOperation:
    return UmlOperation(
        name=name,
        visibility="public",
        parameters=parameters or [],
        returnType=return_type,
    )


def generalization(source: UmlClass, target: UmlClass) -> UmlGeneralization:
    return UmlGeneralization(sourceId=source.id, targetId=target.id)


def diagnostic_codes(model: CanonicalUmlModel) -> list[UmlDiagnosticCode]:
    return [diagnostic.code for diagnostic in validate_uml_model(model).diagnostics]


@pytest.mark.parametrize(
    "model",
    [
        CanonicalUmlModel(),
        CanonicalUmlModel(elements=[uml_class("Cliente")]),
        CanonicalUmlModel(elements=[uml_class("Cliente"), uml_class("Pedido")]),
    ],
)
def test_accepts_valid_models_without_diagnostics(model: CanonicalUmlModel) -> None:
    result = validate_uml_model(model)

    assert result.is_valid
    assert result.diagnostics == []


def test_accepts_model_with_valid_relationship() -> None:
    client = uml_class("Cliente")
    order = uml_class("Pedido")
    relationship = UmlAssociation(
        sourceId=client.id,
        targetId=order.id,
        sourceMultiplicity=UmlMultiplicity(lower=1, upper=1),
        targetMultiplicity=UmlMultiplicity(lower=0, upper="*"),
    )

    result = validate_uml_model(CanonicalUmlModel(elements=[client, order, relationship]))

    assert result.is_valid
    assert result.diagnostics == []


def test_detects_duplicate_class_name_for_each_subsequent_class() -> None:
    first = uml_class("Cliente")
    duplicate = uml_class("Cliente")

    result = validate_uml_model(CanonicalUmlModel(elements=[first, duplicate]))

    assert diagnostic_codes(CanonicalUmlModel(elements=[first, duplicate])) == [
        UmlDiagnosticCode.DUPLICATE_CLASS_NAME
    ]
    assert result.diagnostics[0].element_id == duplicate.id
    assert result.diagnostics[0].field == "name"


def test_class_names_are_case_sensitive() -> None:
    model = CanonicalUmlModel(elements=[uml_class("Cliente"), uml_class("cliente")])

    assert validate_uml_model(model).is_valid


def test_detects_duplicate_attribute_name_within_one_class() -> None:
    duplicate = UmlAttribute(name="email", visibility="private", type="String")
    model = CanonicalUmlModel(
        elements=[
            uml_class(
                "Cliente",
                attributes=[
                    UmlAttribute(name="email", visibility="private", type="String"),
                    duplicate,
                ],
            )
        ]
    )

    result = validate_uml_model(model)

    assert diagnostic_codes(model) == [UmlDiagnosticCode.DUPLICATE_ATTRIBUTE_NAME]
    assert result.diagnostics[0].element_id == duplicate.id


def test_allows_same_attribute_name_in_different_classes() -> None:
    model = CanonicalUmlModel(
        elements=[
            uml_class("Cliente", attributes=[email_attribute()]),
            uml_class("Usuario", attributes=[email_attribute()]),
        ]
    )

    assert validate_uml_model(model).is_valid


def test_detects_duplicate_parameter_name_within_operation() -> None:
    duplicate = parameter("id", "String")
    model = CanonicalUmlModel(
        elements=[
            uml_class(
                "Cliente",
                operations=[operation("buscar", [parameter("id", "UUID"), duplicate])],
            )
        ]
    )

    result = validate_uml_model(model)

    assert UmlDiagnosticCode.DUPLICATE_PARAMETER_NAME in diagnostic_codes(model)
    assert result.diagnostics[0].element_id == duplicate.id


def test_allows_same_parameter_name_in_different_operations() -> None:
    model = CanonicalUmlModel(
        elements=[
            uml_class(
                "Cliente",
                operations=[
                    operation("buscarPorId", [parameter("id", "UUID")]),
                    operation("eliminar", [parameter("id", "UUID")]),
                ],
            )
        ]
    )

    assert validate_uml_model(model).is_valid


def test_detects_duplicate_operation_signature_ignoring_parameter_names_and_return_type() -> None:
    duplicate = operation("buscar", [parameter("codigo", "UUID")], "String")
    model = CanonicalUmlModel(
        elements=[
            uml_class(
                "Cliente",
                operations=[operation("buscar", [parameter("id", "UUID")], "Boolean"), duplicate],
            )
        ]
    )

    result = validate_uml_model(model)

    assert diagnostic_codes(model) == [UmlDiagnosticCode.DUPLICATE_OPERATION_SIGNATURE]
    assert result.diagnostics[0].element_id == duplicate.id


def test_allows_operation_overloads_with_different_ordered_parameter_types() -> None:
    model = CanonicalUmlModel(
        elements=[
            uml_class(
                "Cliente",
                operations=[
                    operation("buscar", [parameter("id", "UUID")]),
                    operation("buscar", [parameter("nombre", "String")]),
                    operation("buscar", [parameter("id", "UUID"), parameter("codigo", "String")]),
                    operation("buscar", [parameter("codigo", "String"), parameter("id", "UUID")]),
                ],
            )
        ]
    )

    assert validate_uml_model(model).is_valid


def test_detects_self_generalization() -> None:
    class_a = uml_class("A")
    model = CanonicalUmlModel(elements=[class_a, generalization(class_a, class_a)])

    assert diagnostic_codes(model) == [UmlDiagnosticCode.GENERALIZATION_SELF_REFERENCE]


def test_detects_simple_generalization_cycle() -> None:
    class_a = uml_class("A")
    class_b = uml_class("B")
    model = CanonicalUmlModel(
        elements=[
            class_a,
            class_b,
            generalization(class_a, class_b),
            generalization(class_b, class_a),
        ]
    )

    assert diagnostic_codes(model) == [UmlDiagnosticCode.GENERALIZATION_CYCLE]


def test_detects_indirect_generalization_cycle() -> None:
    class_a = uml_class("A")
    class_b = uml_class("B")
    class_c = uml_class("C")
    model = CanonicalUmlModel(
        elements=[
            class_a,
            class_b,
            class_c,
            generalization(class_a, class_b),
            generalization(class_b, class_c),
            generalization(class_c, class_a),
        ]
    )

    assert diagnostic_codes(model) == [UmlDiagnosticCode.GENERALIZATION_CYCLE]


def test_allows_acyclic_generalization_chain() -> None:
    class_a = uml_class("A")
    class_b = uml_class("B")
    class_c = uml_class("C")
    model = CanonicalUmlModel(
        elements=[
            class_a,
            class_b,
            class_c,
            generalization(class_c, class_b),
            generalization(class_b, class_a),
        ]
    )

    assert validate_uml_model(model).is_valid


def test_detects_duplicate_generalization() -> None:
    child = uml_class("Administrador")
    parent = uml_class("Usuario")
    model = CanonicalUmlModel(
        elements=[child, parent, generalization(child, parent), generalization(child, parent)]
    )

    assert diagnostic_codes(model) == [UmlDiagnosticCode.DUPLICATE_GENERALIZATION]


def test_collects_multiple_errors_without_mutating_model() -> None:
    first = uml_class("Cliente")
    duplicate = uml_class("Cliente")
    self_generalization = generalization(first, first)
    model = CanonicalUmlModel(elements=[first, duplicate, self_generalization])
    before = model.model_copy(deep=True)

    result = validate_uml_model(model)

    assert [diagnostic.code for diagnostic in result.diagnostics] == [
        UmlDiagnosticCode.DUPLICATE_CLASS_NAME,
        UmlDiagnosticCode.GENERALIZATION_SELF_REFERENCE,
    ]
    assert not result.is_valid
    assert model == before


def test_validation_is_deterministic() -> None:
    first = uml_class("Cliente")
    duplicate = uml_class("Cliente")
    model = CanonicalUmlModel(elements=[first, duplicate, generalization(first, first)])

    assert validate_uml_model(model) == validate_uml_model(model)


def test_validation_result_serializes_with_public_aliases_and_round_trips() -> None:
    element_id = UUID("8141de6e-4ca9-4d60-9a91-ff6c8443241a")
    result = UmlValidationResult(
        diagnostics=[
            {
                "code": "DUPLICATE_CLASS_NAME",
                "severity": "error",
                "message": "Duplicate class name",
                "elementId": str(element_id),
                "field": "name",
            }
        ]
    )

    public_data = result.model_dump(mode="json", by_alias=True)
    restored = UmlValidationResult.model_validate_json(result.model_dump_json(by_alias=True))

    assert public_data["isValid"] is False
    assert public_data["diagnostics"][0]["elementId"] == str(element_id)
    assert restored == result
    assert restored.diagnostics[0].severity is UmlDiagnosticSeverity.ERROR
