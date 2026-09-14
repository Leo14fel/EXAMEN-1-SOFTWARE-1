from collections.abc import Mapping
from enum import StrEnum
from uuid import UUID

from pydantic import Field, computed_field, model_validator

from app.domain.uml.models import (
    CanonicalUmlModel,
    DomainModel,
    UmlClass,
    UmlGeneralization,
    UmlParameter,
)


class UmlDiagnosticSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"


class UmlDiagnosticCode(StrEnum):
    DUPLICATE_CLASS_NAME = "DUPLICATE_CLASS_NAME"
    DUPLICATE_ATTRIBUTE_NAME = "DUPLICATE_ATTRIBUTE_NAME"
    DUPLICATE_PARAMETER_NAME = "DUPLICATE_PARAMETER_NAME"
    DUPLICATE_OPERATION_SIGNATURE = "DUPLICATE_OPERATION_SIGNATURE"
    GENERALIZATION_SELF_REFERENCE = "GENERALIZATION_SELF_REFERENCE"
    GENERALIZATION_CYCLE = "GENERALIZATION_CYCLE"
    DUPLICATE_GENERALIZATION = "DUPLICATE_GENERALIZATION"


class UmlDiagnostic(DomainModel):
    code: UmlDiagnosticCode
    severity: UmlDiagnosticSeverity
    message: str
    element_id: UUID = Field(alias="elementId")
    field: str | None = None


class UmlValidationResult(DomainModel):
    diagnostics: list[UmlDiagnostic] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def discard_computed_is_valid(cls, value: object) -> object:
        if isinstance(value, Mapping):
            return {key: item for key, item in value.items() if key not in {"isValid", "is_valid"}}
        return value

    @computed_field(alias="isValid")
    @property
    def is_valid(self) -> bool:
        return all(
            diagnostic.severity is not UmlDiagnosticSeverity.ERROR
            for diagnostic in self.diagnostics
        )


def validate_uml_model(model: CanonicalUmlModel) -> UmlValidationResult:
    diagnostics: list[UmlDiagnostic] = []
    classes = [element for element in model.elements if isinstance(element, UmlClass)]
    generalizations = [
        element for element in model.elements if isinstance(element, UmlGeneralization)
    ]

    _validate_duplicate_class_names(classes, diagnostics)
    for uml_class in classes:
        _validate_class_members(uml_class, diagnostics)
    _validate_generalizations(generalizations, diagnostics)

    return UmlValidationResult(diagnostics=diagnostics)


def _validate_duplicate_class_names(
    classes: list[UmlClass], diagnostics: list[UmlDiagnostic]
) -> None:
    seen_names: set[str] = set()
    for uml_class in classes:
        if uml_class.name in seen_names:
            diagnostics.append(
                _diagnostic(
                    UmlDiagnosticCode.DUPLICATE_CLASS_NAME,
                    "Duplicate class name",
                    uml_class.id,
                    "name",
                )
            )
        else:
            seen_names.add(uml_class.name)


def _validate_class_members(uml_class: UmlClass, diagnostics: list[UmlDiagnostic]) -> None:
    seen_attribute_names: set[str] = set()
    for attribute in uml_class.attributes:
        if attribute.name in seen_attribute_names:
            diagnostics.append(
                _diagnostic(
                    UmlDiagnosticCode.DUPLICATE_ATTRIBUTE_NAME,
                    "Duplicate attribute name in class",
                    attribute.id,
                    "name",
                )
            )
        else:
            seen_attribute_names.add(attribute.name)

    seen_signatures: set[tuple[str, tuple[str, ...]]] = set()
    for operation in uml_class.operations:
        _validate_duplicate_parameter_names(operation.parameters, diagnostics)
        signature = (operation.name, tuple(parameter.type for parameter in operation.parameters))
        if signature in seen_signatures:
            diagnostics.append(
                _diagnostic(
                    UmlDiagnosticCode.DUPLICATE_OPERATION_SIGNATURE,
                    "Duplicate operation signature in class",
                    operation.id,
                    "parameters",
                )
            )
        else:
            seen_signatures.add(signature)


def _validate_duplicate_parameter_names(
    parameters: list[UmlParameter], diagnostics: list[UmlDiagnostic]
) -> None:
    seen_parameter_names: set[str] = set()
    for parameter in parameters:
        if parameter.name in seen_parameter_names:
            diagnostics.append(
                _diagnostic(
                    UmlDiagnosticCode.DUPLICATE_PARAMETER_NAME,
                    "Duplicate parameter name in operation",
                    parameter.id,
                    "name",
                )
            )
        else:
            seen_parameter_names.add(parameter.name)


def _validate_generalizations(
    generalizations: list[UmlGeneralization], diagnostics: list[UmlDiagnostic]
) -> None:
    seen_pairs: set[tuple[UUID, UUID]] = set()
    adjacency: dict[UUID, list[UmlGeneralization]] = {}
    for generalization in generalizations:
        pair = (generalization.source_id, generalization.target_id)
        if pair in seen_pairs:
            diagnostics.append(
                _diagnostic(
                    UmlDiagnosticCode.DUPLICATE_GENERALIZATION,
                    "Duplicate generalization",
                    generalization.id,
                )
            )
        else:
            seen_pairs.add(pair)

        if generalization.source_id == generalization.target_id:
            diagnostics.append(
                _diagnostic(
                    UmlDiagnosticCode.GENERALIZATION_SELF_REFERENCE,
                    "Generalization cannot reference the same class",
                    generalization.id,
                )
            )
            continue
        adjacency.setdefault(generalization.source_id, []).append(generalization)

    visit_state: dict[UUID, int] = {}

    def visit(class_id: UUID) -> None:
        visit_state[class_id] = 1
        for generalization in adjacency.get(class_id, []):
            target_id = generalization.target_id
            state = visit_state.get(target_id, 0)
            if state == 1:
                diagnostics.append(
                    _diagnostic(
                        UmlDiagnosticCode.GENERALIZATION_CYCLE,
                        "Inheritance cycle detected",
                        generalization.id,
                    )
                )
            elif state == 0:
                visit(target_id)
        visit_state[class_id] = 2

    for class_id in adjacency:
        if visit_state.get(class_id, 0) == 0:
            visit(class_id)


def _diagnostic(
    code: UmlDiagnosticCode, message: str, element_id: UUID, field: str | None = None
) -> UmlDiagnostic:
    return UmlDiagnostic(
        code=code,
        severity=UmlDiagnosticSeverity.ERROR,
        message=message,
        elementId=element_id,
        field=field,
    )
