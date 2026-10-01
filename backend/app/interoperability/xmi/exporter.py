from hashlib import sha256
from typing import Final
from uuid import UUID

from lxml import etree

from app.domain.uml.models import (
    ProjectDocument,
    UmlAggregation,
    UmlAssociation,
    UmlClass,
    UmlComposition,
    UmlGeneralization,
    UmlMultiplicity,
)

XMI_NAMESPACE: Final = "http://schema.omg.org/spec/XMI/2.1"
UML_NAMESPACE: Final = "http://www.omg.org/spec/UML/20161101"
NSMAP: Final = {"xmi": XMI_NAMESPACE, "uml": UML_NAMESPACE}


def export_project_document(document: ProjectDocument) -> bytes:
    """Serialize only the canonical UML semantics of a project as XMI 2.1."""
    root = etree.Element(_xmi("XMI"), nsmap=NSMAP)
    root.set(_xmi("version"), "2.1")
    model = etree.SubElement(
        root,
        _uml("Model"),
        {_xmi("id"): _id(document.id), "name": _project_name(document)},
    )

    classes = [element for element in document.uml_model.elements if isinstance(element, UmlClass)]
    class_ids_by_name = {uml_class.name: _id(uml_class.id) for uml_class in classes}
    primitive_types = sorted(
        {
            type_name
            for uml_class in classes
            for type_name in _class_type_names(uml_class)
            if type_name not in class_ids_by_name
        }
    )
    primitive_ids = {type_name: _primitive_id(type_name) for type_name in primitive_types}

    for type_name in primitive_types:
        etree.SubElement(
            model,
            _uml("packagedElement"),
            {
                _xmi("type"): "uml:PrimitiveType",
                _xmi("id"): primitive_ids[type_name],
                "name": _xml_name(type_name),
            },
        )

    for uml_class in classes:
        _export_class(model, uml_class, class_ids_by_name, primitive_ids)

    for relationship in document.uml_model.elements:
        if isinstance(relationship, (UmlAssociation, UmlAggregation, UmlComposition)):
            _export_association(model, relationship)
        elif isinstance(relationship, UmlGeneralization):
            etree.SubElement(
                model,
                _uml("packagedElement"),
                {
                    _xmi("type"): "uml:Generalization",
                    _xmi("id"): _id(relationship.id),
                    "specific": _id(relationship.source_id),
                    "general": _id(relationship.target_id),
                },
            )

    return etree.tostring(root, encoding="UTF-8", xml_declaration=True, pretty_print=True)


def _export_class(
    model: etree._Element,
    uml_class: UmlClass,
    class_ids_by_name: dict[str, str],
    primitive_ids: dict[str, str],
) -> None:
    class_element = etree.SubElement(
        model,
        _uml("packagedElement"),
        {
            _xmi("type"): "uml:Class",
            _xmi("id"): _id(uml_class.id),
            "name": _xml_name(uml_class.name),
            "visibility": uml_class.visibility.value,
        },
    )
    for attribute in uml_class.attributes:
        etree.SubElement(
            class_element,
            _uml("ownedAttribute"),
            {
                _xmi("id"): _id(attribute.id),
                "name": _xml_name(attribute.name),
                "visibility": attribute.visibility.value,
                "type": _type_id(attribute.type, class_ids_by_name, primitive_ids),
            },
        )
    for operation in uml_class.operations:
        operation_element = etree.SubElement(
            class_element,
            _uml("ownedOperation"),
            {
                _xmi("id"): _id(operation.id),
                "name": _xml_name(operation.name),
                "visibility": operation.visibility.value,
            },
        )
        for parameter in operation.parameters:
            _export_parameter(
                operation_element,
                _id(parameter.id),
                _xml_name(parameter.name),
                parameter.type,
                "in",
                class_ids_by_name,
                primitive_ids,
            )
        if operation.return_type is not None:
            _export_parameter(
                operation_element,
                f"{_id(operation.id)}_return",
                "return",
                operation.return_type,
                "return",
                class_ids_by_name,
                primitive_ids,
            )


def _export_parameter(
    operation: etree._Element,
    parameter_id: str,
    name: str,
    type_name: str,
    direction: str,
    class_ids_by_name: dict[str, str],
    primitive_ids: dict[str, str],
) -> None:
    etree.SubElement(
        operation,
        _uml("ownedParameter"),
        {
            _xmi("id"): parameter_id,
            "name": _xml_name(name),
            "type": _type_id(type_name, class_ids_by_name, primitive_ids),
            "direction": direction,
        },
    )


def _export_association(
    model: etree._Element, relationship: UmlAssociation | UmlAggregation | UmlComposition
) -> None:
    association = etree.SubElement(
        model,
        _uml("packagedElement"),
        {_xmi("type"): "uml:Association", _xmi("id"): _id(relationship.id)},
    )
    source_end_id = f"{_id(relationship.id)}_source_end"
    target_end_id = f"{_id(relationship.id)}_target_end"
    association.set("memberEnd", f"{source_end_id} {target_end_id}")
    _export_association_end(
        association, source_end_id, relationship.source_id, relationship.source_multiplicity, "none"
    )
    aggregation = (
        "shared"
        if isinstance(relationship, UmlAggregation)
        else "composite" if isinstance(relationship, UmlComposition) else "none"
    )
    _export_association_end(
        association,
        target_end_id,
        relationship.target_id,
        relationship.target_multiplicity,
        aggregation,
    )


def _export_association_end(
    association: etree._Element,
    end_id: str,
    type_id: UUID,
    multiplicity: UmlMultiplicity,
    aggregation: str,
) -> None:
    etree.SubElement(
        association,
        _uml("ownedEnd"),
        {
            _xmi("id"): end_id,
            "type": _id(type_id),
            "lower": str(multiplicity.lower),
            "upper": str(multiplicity.upper),
            "aggregation": aggregation,
        },
    )


def _class_type_names(uml_class: UmlClass) -> set[str]:
    return {
        *(attribute.type for attribute in uml_class.attributes),
        *(
            parameter.type
            for operation in uml_class.operations
            for parameter in operation.parameters
        ),
        *(
            operation.return_type
            for operation in uml_class.operations
            if operation.return_type is not None
        ),
    }


def _type_id(
    type_name: str, class_ids_by_name: dict[str, str], primitive_ids: dict[str, str]
) -> str:
    return class_ids_by_name.get(type_name, primitive_ids[type_name])


def _project_name(document: ProjectDocument) -> str:
    name = document.metadata.get("name")
    if isinstance(name, str) and name.strip():
        return _xml_name(name.strip())
    return f"Project_{document.id.hex[:8]}"


def _id(value: UUID) -> str:
    return f"id_{value.hex}"


def _primitive_id(type_name: str) -> str:
    return f"primitive_{sha256(type_name.encode('utf-8')).hexdigest()[:24]}"


def _xml_name(value: str) -> str:
    return "".join(
        character
        for character in value
        if character in "\t\n\r" or ord(character) >= 0x20
    ) or "Unnamed"


def _xmi(name: str) -> str:
    return f"{{{XMI_NAMESPACE}}}{name}"


def _uml(name: str) -> str:
    return f"{{{UML_NAMESPACE}}}{name}"
